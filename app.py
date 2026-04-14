import os
import time
import json
import secrets
import string
import redis
from flask import Flask, request, jsonify
from flask_cors import CORS
from waitress import serve
from openai import OpenAI  # 修改：引入 OpenAI 客户端以兼容通义千问

# 注意：请确保 core.config 中已将 GEMINI_API_KEY 替换为 DASHSCOPE_API_KEY
from core.config import REDIS_HOST, REDIS_PORT, OUTPUT_FOLDER, DASHSCOPE_API_KEY
from core.models import StoryAnalysis
from utils.logger import initialize_csv, log_submission
from services.video_service import create_video

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
    
    # 获取前端传来的配置，如果为空则回退到默认的通义千问配置
    user_api_key = data_json.get('api_key') or DASHSCOPE_API_KEY
    model_name = data_json.get('model', 'qwen-plus')  # 修改：默认模型改为 qwen-plus
    
    try:
        # 修改：使用 OpenAI 客户端和阿里云的 base_url 初始化
        client = OpenAI(
            api_key=user_api_key,
            base_url="[https://dashscope.aliyuncs.com/compatible-mode/v1](https://dashscope.aliyuncs.com/compatible-mode/v1)"
        )
        
        prompt_text = f"分析以下故事，将其拆分为连续的镜头。故事：{story}"
        
        # 将 Pydantic 模型的 Schema 转换为字符串，用于告诉大模型我们要什么格式
        schema_str = json.dumps(StoryAnalysis.model_json_schema(), ensure_ascii=False)

        # 构造系统提示词，强化 JSON 输出并规范画面中的文本语言
        system_instruction = (
            "你是一个专业的AI视频导播。请根据用户提供的故事生成连续的镜头脚本。\n"
            f"必须严格按照以下 JSON Schema 格式返回结果（只返回合法的 JSON 对象，不要包含 markdown 标记）：\n{schema_str}\n"
            "重要要求：写脚本生成图像时，图像的所有文本都用英文。"
        )

        # 发起 API 请求
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt_text}
            ],
            response_format={"type": "json_object"}, # 开启 JSON 模式
            temperature=0.7,
        )

        # 提取返回文本
        result_text = response.choices[0].message.content
        
        # 容错清理：防止模型依然输出 ```json 标记
        if result_text.startswith("```"):
            result_text = result_text.strip("`").removeprefix("json").strip()

        parsed_json = json.loads(result_text)
        
        # 提取 scenes 数组
        generated_data = parsed_json.get("scenes", [])
        if not generated_data and isinstance(parsed_json, list):
            generated_data = parsed_json
            
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
    print("猫Meme视频制作服务已启动 (Powered by Qwen)...")
    serve(app, host="0.0.0.0", port=5000)
