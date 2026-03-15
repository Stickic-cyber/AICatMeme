import os
from dotenv import load_dotenv

load_dotenv()

# --- 基础配置 ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# --- 路径配置 ---
BASE_DIR = "D:/Project/AImeme/TheNewMeme"
EMOTION_FOLDER = "D:/Project/AImeme/TheNewMeme/meme"
BG_FOLDER = os.path.join(BASE_DIR, "backgrounds")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
FONT_PATH = "C:/Windows/Fonts/simhei.ttf"
LOG_CSV_FILE = 'D:/Project/AImeme/user_submissions.csv'

# 确保输出目录存在
os.makedirs(OUTPUT_FOLDER, exist_ok=True)