import os
import glob
import subprocess
import shutil
import imageio_ffmpeg

# 获取底层的 FFmpeg 路径
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

INPUT_FOLDER = "./meme_org" 
OUTPUT_BASE = "./meme"

name_map = {
    "哀求": "imploring", "崩溃": "broken", "吃惊": "surprised", "大笑": "laughing",
    "呆滞": "blank", "得瑟": "showoff", "得意": "proud", "烦躁": "irritable",
    "害羞": "shy", "坏笑": "smirk", "任性": "willful", "欢呼": "cheering",
    "饥饿": "hungry", "焦急": "anxious", "教训": "scolding", "惊讶": "astonished",
    "可怜": "pitiful", "蔑视": "disdain", "努力": "striving", "其他": "others",
    "傻笑": "giggle", "痛苦": "painful", "威严": "majestic", "无辜": "innocent",
    "无奈": "frustrated", "无助": "helpless", "兴奋": "excited", "勇敢": "brave",
    "愉快": "happy", "震惊": "shocked",
    "吃饭": "eating", "尴尬": "awkward", "绝望": "despair"
}

def process_videos():
    if not os.path.exists(INPUT_FOLDER):
        print(f"❌ 错误：找不到输入文件夹 {INPUT_FOLDER}")
        return

    os.makedirs(OUTPUT_BASE, exist_ok=True)
    green_videos = glob.glob(os.path.join(INPUT_FOLDER, "*.mp4"))

    if not green_videos:
        print("⚠️ 输入文件夹中没有找到任何 mp4 文件！")
        return

    success_count = 0
    
    # 🎯 核心参数设定
    REAL_GREEN = "0x00FF4B" 
    SIMILARITY = "0.25" 
    BLEND = "0.02"      

    # 🔥 兼容性最强的高级滤镜：colorkey 负责基础抠图，despill 负责吸干猫咪身上反光的绿光
    ADVANCED_FILTER = f"colorkey={REAL_GREEN}:{SIMILARITY}:{BLEND},despill=green"

    for video_path in green_videos:
        filename = os.path.basename(video_path)
        zh_name, _ = os.path.splitext(filename)
        
        en_name = name_map.get(zh_name, zh_name)
        
        out_folder = os.path.join(OUTPUT_BASE, en_name)
        frames_folder = os.path.join(out_folder, "frames")
        
        # ⚠️ 关键动作：执行前，先把里面的旧废料全都扬了，防止旧文件干扰视线！
        if os.path.exists(frames_folder):
            shutil.rmtree(frames_folder)
        os.makedirs(frames_folder, exist_ok=True)
        
        png_pattern = os.path.join(frames_folder, "%04d.png")
        audio_path = os.path.join(out_folder, "audio.mp3")
        
        print(f"⚡ 正在执行强力去绿光: {zh_name} -> /{en_name}/frames/ ...")
        
        cmd_png = [
            ffmpeg_path, "-y", "-i", video_path,
            "-vf", ADVANCED_FILTER, 
            "-r", "30", 
            png_pattern
        ]
        
        cmd_audio = [
            ffmpeg_path, "-y", "-i", video_path,
            "-q:a", "0", "-map", "a",
            audio_path
        ]
        
        # ⚠️ 关键动作：捕获报错信息。如果有错，直接贴脸输出！
        res_png = subprocess.run(cmd_png, capture_output=True, text=True)
        if res_png.returncode != 0:
            print(f"❌ [{zh_name}] FFmpeg 罢工了！错误详情如下：\n{res_png.stderr}\n")
            continue # 如果报错了，直接跳过当前视频，不打印成功
            
        subprocess.run(cmd_audio, capture_output=True)
        
        print(f"✅ [{zh_name}] 处理完成！")
        success_count += 1

    print(f"\n🎉 处理完毕！本次真正成功输出了 {success_count} 个素材包。")

if __name__ == "__main__":
    process_videos()
