import time
import json
import secrets
import string
import redis
from flask import Flask, request, jsonify
from flask_cors import CORS
from waitress import serve

from core.config import REDIS_HOST, REDIS_PORT, OUTPUT_FOLDER
from core.models import StoryAnalysis
from utils.logger import initialize_csv, log_submission
from services.video_service import create_video
from google import genai
from core.config import GEMINI_API_KEY

app = Flask(__name__)
CORS(app)

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.ping()
except redis.ConnectionError:
    print("警告: 无法连接到 Redis 服务器，限流功能暂时停用。")

def generate_password(length=6):
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def process_request(data_json, client_ip):
    story = data_json.get('story', '')
    
    # 获取前端传来的配置，如果前端没传或为空，则回退到代码里导入的默认配置
    user_api_key = data_json.get('api_key') or GEMINI_API_KEY
    model_name = data_json.get('model', 'gemini-2.5-flash')
    
    try:
        # 使用提取到的 API KEY 初始化客户端
        client = genai.Client(api_key=user_api_key)
        prompt_text = f"分析以下故事，将其拆分为连续的镜头.故事：{story}"

        # 使用前端传过来的模型名字
        response = client.models.generate_content(
            model=model_name, 
            contents=[prompt_text],
            config={
                "response_mime_type": "application/json",
                "response_schema": StoryAnalysis.model_json_schema(), 
                "temperature": 0.7,
            },
        )

        parsed_json = json.loads(response.text)
        generated_data = parsed_json.get("scenes", [])
        user_id = generate_password()
        output_path = f"{OUTPUT_FOLDER}/{user_id}.mp4"

        print(f"AI导播脚本: {json.dumps(generated_data, ensure_ascii=False, indent=2)}")
        
        # 调用分离出去的视频生成服务
        video_result = create_video(generated_data, output_path)

        if not video_result:
            return {"message": "视频生成失败，请检查素材(背景和情感)是否齐全"}, 500
        
        return {"message": f"生成成功，专属ID：{user_id}", "file_path": output_path}, 200

    except Exception as e:
        return {"message": str(e)}, 500

@app.route('/generate_video', methods=['POST'])
def generate_video_endpoint():
    result, status_code = process_request(request.json or {}, request.remote_addr)
    return jsonify(result), status_code

@app.route('/generate_video_debug', methods=['POST'])
def generate_video_debug():
    data = request.json
    scenes_data = data.get("scenes", data) if isinstance(data, dict) else data
    user_id = generate_password()
    output_path = f"{OUTPUT_FOLDER}/debug_{user_id}.mp4"

    try:
        video_result = create_video(scenes_data, output_path)
        if not video_result:
            return jsonify({"message": "视频生成失败，请检查素材是否齐全"}), 500
            
        return jsonify({"message": f"调试生成成功！ID: {user_id}", "file_path": output_path}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

if __name__ == '__main__':
    initialize_csv()
    print("猫Meme视频制作服务已启动...")
    serve(app, host="0.0.0.0", port=5000)