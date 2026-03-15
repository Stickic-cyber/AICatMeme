import os
from dotenv import load_dotenv

load_dotenv()

# --- 动态获取项目根目录 ---
# __file__ 是当前 config.py 的绝对路径
# os.path.dirname(__file__) 是 core 文件夹路径
# 再取一次 dirname 就是项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- 基础配置 ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# --- 路径配置 (全部切换为基于 ROOT_DIR 的相对路径) ---

# 素材包目录 (PreProcessVideo.py 生成的带透明通道的帧目录)
EMOTION_FOLDER = os.path.join(ROOT_DIR, "meme_frames")

# 背景图目录
BG_FOLDER = os.path.join(ROOT_DIR, "backgrounds")

# 视频输出目录
OUTPUT_FOLDER = os.path.join(ROOT_DIR, "output")

# 日志 CSV 文件
LOG_CSV_FILE = os.path.join(ROOT_DIR, "user_submissions.csv")

# 字体配置
# 提示：如果是 Windows 跑，可以用系统字体；如果是开源，建议在项目里放一个 font 文件夹存一个 .ttf 文件
FONT_PATH = os.getenv("FONT_PATH", "C:/Windows/Fonts/simhei.ttf")

# --- 自动创建必要文件夹 ---
# 这样别人克隆代码后，不用手动建文件夹也能跑
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(BG_FOLDER, exist_ok=True)
os.makedirs(EMOTION_FOLDER, exist_ok=True)
