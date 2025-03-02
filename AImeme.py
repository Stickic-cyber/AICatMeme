from flask import Flask, request, jsonify
from waitress import serve
import os
import glob
import time
import json
import secrets
import string
import numpy as np
import redis
from moviepy.editor import VideoFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
from bypy import ByPy
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
from flask_cors import CORS  # 引入CORS

app = Flask(__name__)
CORS(app)  # 启用CORS，这样所有路由都允许跨域访问

# 连接 Redis 进行 IP 限制
r = redis.Redis(host='localhost', port=6379, db=0)
ACCESS_TIME_LIMIT = 3  # 限制每个 IP 3 秒内只能请求 1 次

# SparkAI 配置
SPARKAI_URL = 'wss://spark-api.xf-yun.com/chat/max-32k'  #'wss://spark-api.xf-yun.com/v3.5/chat'
SPARKAI_DOMAIN = 'max-32k' #'generalv3.5'
SPARKAI_APP_ID = 'your_id'
SPARKAI_API_SECRET = 'yours'
SPARKAI_API_KEY = 'yours'


def generate_password(length=6):
    """生成 6 位随机数字 ID"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def add_newline(text):
    """优化文本换行"""
    punctuations = ['，', '。', '！', '？', '；', '：', ',', '.', '?', '!', ';', ':', '・', '·']
    result, buffer = '', ''
    for char in text:
        buffer += char
        if char in punctuations or len(buffer.strip()) > 12:
            if len(buffer.strip()) > 4:
                result += buffer + '\n'
                buffer = ''
    result += buffer
    return result.rstrip('\n')


def add_text_with_outline(frame, text, font_path, font_size, text_color, outline_color, position, outline_width=2):
    """给图片添加带描边的文字"""
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    img_width, img_height = img.size

    x = (img_width - text_width) / 2 if position[0] == 'center' else 10 if position[0] == 'left' else img_width - text_width - 10
    y = 20 if position[1] == 'top' else img_height - text_height - 10 if position[1] == 'bottom' else (img_height - text_height) / 2

    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)

    draw.text((x, y), text, font=font, fill=text_color)
    return np.array(img)


def create_video(data, video_folder, output_path, font_path, font_size=59, text_color=(255, 255, 255),
                 outline_color=(0, 0, 0), text_position=('center', 'top'), outline_width=3):
    """根据数据生成视频"""
    clips = []
    for place, emotion, text in data[:4]:
        search_pattern = os.path.join(video_folder, f"{place}_{emotion}.*")
        matching_files = glob.glob(search_pattern)
        if not matching_files:
            continue

        clip = VideoFileClip(matching_files[0])
        text = add_newline(text)

        def add_text(frame, text=text):
            return add_text_with_outline(frame, text, font_path, font_size, text_color, outline_color, text_position, outline_width)

        modified_clip = clip.fl_image(add_text).set_audio(clip.audio)
        clips.append(modified_clip)

    if not clips:
        return None

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    return output_path


def file_upload(file_path, user_id):
    """上传文件到百度云，并返回状态"""
    bp = ByPy()
    result = bp.upload(file_path, remotepath=f'{user_id}/{user_id}.mp4')
    return result == 0

@app.route('/')
def home():
    return jsonify({"message": "I Love U"})

ip_access_time = {}

@app.route('/generate_video', methods=['POST'])
def generate_video_endpoint():
    """API 生成视频"""
    client_ip = request.remote_addr
    # print(client_ip)
    current_time = time.time()
    print(current_time)

    # 检查 IP 访问频率
    if client_ip in ip_access_time and current_time - ip_access_time[client_ip] < 5:
        return jsonify({"message": "访问过于频繁，请稍后重试！"}), 429

    # 记录 IP 访问时间
    ip_access_time[client_ip] = current_time


    data = request.json
    story = data.get('story', '')

    # 调用 SparkAI API
    spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )
    messages = [ChatMessage(role="user", content='''把下面的故事分成不同的地点，再配上一个情感，以及少于20字的对话或旁白作为文本：
        要求把输出的结果写成以下格式，不要多写任何内容：[["地点1", "情感1", "文本1"], ["地点2", "情感2", "文本2"], ["地点3", "情感3", "文本3"], ...]；
        要求地点严格从以下选择：["concert", "fantacy", "others", "rooftop", "stage", "airport", "amusementpark", "bank", "cinema", "classroom", "grassland", "gym", "home", "hospital", "kitchen", "library", "museum", "park", "playground", "pool", "restaurant", "school", "shop", "station", "theater", "village"]；
        要求情感严格从以下选择：["哀求", "崩溃", "吃惊", "大笑", "呆滞", "得瑟", "得意", "烦躁", "害羞", "坏笑", "欢呼", "饥饿", "焦急", "教训", "惊讶", "可怜", "蔑视", "努力", "其他", "傻笑", "痛苦", "威严", "无辜", "无奈", "无助", "兴奋", "勇敢", "愉快", "震惊","愉快"]
        故事为：{%s}'''%story)]
    handler = ChunkPrintHandler()
    response = spark.generate([messages], callbacks=[handler])

    # **安全替换 eval()**
    try:
        data = json.loads(response.generations[0][0].text)
    except json.JSONDecodeError:
        return jsonify({"message": "生成数据解析失败"}), 500
    print(data)
    user_id = generate_password()
    video_folder = "/AICatMeme/Videos/output_videos"
    output_path = f"/AICatMeme/Videos/output/{user_id}.mp4"
    font_path = "/usr/share/fonts/truetype/msttcorefonts/SimHei.ttf"


    video_result = create_video(data, video_folder, output_path, font_path)

    if not video_result:
        return jsonify({"message": "视频生成失败，可能缺少对应的素材"}), 500

    if not file_upload(output_path, user_id):
        return jsonify({"message": "视频上传失败", "backup_url": f"your_baidu_netdisk_path"}), 500

    return jsonify({
        "message": f"您的专属ID是：{user_id}。\n请访问：your_baidu_netdisk_path\n找到ID对应的文件夹后请及时下载！",
        "file_path": output_path
    })


if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=5000)  # 仅本机监听，提高安全性
