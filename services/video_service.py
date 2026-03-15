import os
import glob
import tempfile
import concurrent.futures
import subprocess
from utils.draw_utils import wrap_text
from core.config import EMOTION_FOLDER, BG_FOLDER, FONT_PATH
import imageio_ffmpeg

# 动态获取当前 Python 环境自带的 ffmpeg 绝对路径
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

def ff_path(path):
    """把 Windows 路径转换为 FFmpeg 滤镜能识别的安全格式（转义冒号和反斜杠）"""
    return path.replace('\\', '/').replace(':', '\\:')

def write_text_file(temp_dir, filename, text):
    """FFmpeg drawtext 传长文本容易引发引号冲突，最稳妥的做法是把台词写进临时 txt 文件"""
    filepath = os.path.join(temp_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    return ff_path(filepath)

def create_image_concat_file(png_list, temp_dir, prefix, fps=30):
    """生成 FFmpeg 专用的图片序列 concat 文本，完美规避 Windows 下 glob 支持不稳定的坑"""
    txt_path = os.path.join(temp_dir, f"{prefix}_concat.txt")
    dur = 1.0 / fps
    with open(txt_path, 'w', encoding='utf-8') as f:
        for png in png_list:
            safe_path = png.replace('\\', '/')
            f.write(f"file '{safe_path}'\n")
            f.write(f"duration {dur}\n")
        if png_list:
            safe_last_png = png_list[-1].replace('\\', '/')
            f.write(f"file '{safe_last_png}'\n")
    return txt_path

def process_single_scene_ffmpeg(index, scene, temp_dir):
    """
    独立构建并执行纯 FFmpeg 命令行，极速渲染单个场景
    """
    temp_output = os.path.join(temp_dir, f"scene_{index}.mp4")
    print(f"🔄 [FFmpeg] 正在全速处理场景 {index+1}: {scene['title']}")

    # 1. 获取背景
    bg_files = glob.glob(os.path.join(BG_FOLDER, f"{scene['place']}.*"))
    if not bg_files:
        raise FileNotFoundError(f"找不到背景素材: {scene['place']}")
    bg_path = bg_files[0]
    bg_is_image = bg_path.lower().endswith(('.png', '.jpg', '.jpeg'))

    # 字幕和字体配置
    font_safe = ff_path(FONT_PATH)
    title_txt = write_text_file(temp_dir, f"title_{index}.txt", scene['title'])
    
    chars = scene['characters']
    stype = scene['scene_type']

    def get_emo_assets(emo_name):
        base = os.path.join(EMOTION_FOLDER, emo_name)
        frames = sorted(glob.glob(os.path.join(base, "frames", "*.png")))
        if not frames: raise FileNotFoundError(f"找不到帧: {emo_name}")
        audio = os.path.join(base, "audio.mp3")
        has_audio = os.path.exists(audio) and os.path.getsize(audio) > 2048
        return frames, (audio if has_audio else None)

    # --- 开始构建 FFmpeg 指令 ---
    cmd = [FFMPEG_EXE, "-y"]

    # 输入 0: 背景
    if bg_is_image:
        cmd.extend(["-loop", "1", "-framerate", "24", "-i", bg_path])
    else:
        cmd.extend(["-stream_loop", "-1", "-i", bg_path])

    filters = []
    texts = []
    
    # 基础文字滤镜参数（去掉了背景框，加上黑色描边）
    title_filter = f"drawtext=fontfile='{font_safe}':textfile='{title_txt}':x=(w-text_w)/2:y=50:fontsize=75:fontcolor=yellow:borderw=4:bordercolor=black"
    
    if stype == 'single' and len(chars) > 0:
        frames, audio = get_emo_assets(chars[0]['emotion'])
        dur = len(frames) / 30.0
        concat_txt = create_image_concat_file(frames, temp_dir, f"single_{index}")
        
        # 输入 1 & 2: 序列与音频
        cmd.extend(["-f", "concat", "-safe", "0", "-i", concat_txt])
        cmd.extend(["-i", audio] if audio else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"])

        # 构建滤镜链
        filters.append(f"[0:v]scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,setsar=1,trim=duration={dur}[bg]")
        filters.append(f"[1:v]scale=750:-1,setsar=1[anim]")
        filters.append(f"[bg][anim]overlay=(W-w)/2:(H-h)/2[v1]")
        
        # 构建文字
        name_txt = write_text_file(temp_dir, f"name_{index}.txt", chars[0]['name'])
        dialogue = wrap_text(f"*{chars[0]['text']}", 20)  # 修改为 20 字符换行
        dialogue_txt = write_text_file(temp_dir, f"dial_{index}.txt", dialogue)
        
        texts.append(title_filter)
        # 单人场景：名字悬浮于头顶 (y=260)，台词保留在底部
        texts.append(f"drawtext=fontfile='{font_safe}':textfile='{name_txt}':x=(w-text_w)/2:y=260:fontsize=52:fontcolor=yellow:borderw=3:bordercolor=black")
        texts.append(f"drawtext=fontfile='{font_safe}':textfile='{dialogue_txt}':x=(w-text_w)/2:y=1080-220:fontsize=52:fontcolor=white:borderw=3:bordercolor=black:line_spacing=-30")
        
        filters.append(f"[v1]{','.join(texts)}[vout]")
        filters.append(f"[2:a]atrim=duration={dur}[aout]")
        total_dur = dur

    elif stype == 'dialogue' and len(chars) >= 2:
        l_frames, l_audio = get_emo_assets(chars[0]['emotion'])
        r_frames, r_audio = get_emo_assets(chars[1]['emotion'])
        
        dur_l = len(l_frames) / 30.0
        dur_r = len(r_frames) / 30.0
        total_dur = dur_l + dur_r
        
        l_concat = create_image_concat_file(l_frames, temp_dir, f"l_anim_{index}")
        r_concat = create_image_concat_file(r_frames, temp_dir, f"r_anim_{index}")
        
        # 输入 1:左侧动图 2:右侧动图 3:右侧静止首帧 4:左侧静止尾帧
        cmd.extend(["-f", "concat", "-safe", "0", "-i", l_concat])
        cmd.extend(["-f", "concat", "-safe", "0", "-i", r_concat])
        cmd.extend(["-loop", "1", "-i", r_frames[0]])
        cmd.extend(["-loop", "1", "-i", l_frames[-1]])
        
        # 输入 5:左音频 6:右音频
        cmd.extend(["-i", l_audio] if l_audio else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"])
        cmd.extend(["-i", r_audio] if r_audio else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"])

        # 视频合成链 (利用 enable 滤镜实现极速帧切换)
        filters.append(f"[0:v]scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,setsar=1,trim=duration={total_dur}[bg]")
        filters.append("[1:v]scale=520:-1,setsar=1[la]")
        filters.append(f"[2:v]scale=520:-1,setsar=1,setpts=PTS-STARTPTS+{dur_l}/TB[ra]")
        filters.append("[3:v]scale=520:-1,setsar=1[r_first]")
        filters.append("[4:v]scale=520:-1,setsar=1[l_last]")
        
        filters.append(f"[bg][r_first]overlay=x=530:y=(H-h)/2:enable='lt(t,{dur_l})'[v1]")
        filters.append(f"[v1][la]overlay=x=30:y=(H-h)/2:enable='lt(t,{dur_l})'[v2]")
        filters.append(f"[v2][l_last]overlay=x=30:y=(H-h)/2:enable='gte(t,{dur_l})'[v3]")
        filters.append(f"[v3][ra]overlay=x=530:y=(H-h)/2:enable='gte(t,{dur_l})'[v4]")

        # 文本生成
        ln_txt = write_text_file(temp_dir, f"ln_{index}.txt", chars[0]['name'])
        rn_txt = write_text_file(temp_dir, f"rn_{index}.txt", chars[1]['name'])
        ld_txt = write_text_file(temp_dir, f"ld_{index}.txt", wrap_text(f"*{chars[0]['text']}", 10))  # 修改为 10 字符换行
        rd_txt = write_text_file(temp_dir, f"rd_{index}.txt", wrap_text(f"*{chars[1]['text']}", 10))  # 修改为 10 字符换行

        texts.append(title_filter)
        # 双人场景：名字悬浮于头顶 (y=260)，并修正了左侧猫咪中心对齐 (x=290)
        texts.append(f"drawtext=fontfile='{font_safe}':textfile='{ln_txt}':x=290-text_w/2:y=260:fontsize=52:fontcolor=yellow:borderw=3:bordercolor=black")
        texts.append(f"drawtext=fontfile='{font_safe}':textfile='{rn_txt}':x=790-text_w/2:y=260:fontsize=52:fontcolor=yellow:borderw=3:bordercolor=black")
        
        # 台词留在底部，同步修正左侧台词中心对齐 (x=290)
        texts.append(f"drawtext=fontfile='{font_safe}':textfile='{ld_txt}':enable='lt(t,{dur_l})':x=290-text_w/2:y=1080-260:fontsize=52:fontcolor=white:borderw=3:bordercolor=black:line_spacing=-30")
        texts.append(f"drawtext=fontfile='{font_safe}':textfile='{rd_txt}':enable='gte(t,{dur_l})':x=790-text_w/2:y=1080-260:fontsize=52:fontcolor=white:borderw=3:bordercolor=black:line_spacing=-30")
        
        filters.append(f"[v4]{','.join(texts)}[vout]")

        # 音频混合 (右侧音频延后 dur_l 毫秒)
        delay_ms = int(dur_l * 1000)
        filters.append(f"[5:a]atrim=duration={dur_l},asetpts=PTS-STARTPTS[a1]")
        filters.append(f"[6:a]atrim=duration={dur_r},adelay={delay_ms}|{delay_ms},asetpts=PTS-STARTPTS[a2]")
        filters.append("[a1][a2]amix=inputs=2:duration=longest:normalize=0[aout]")

    filter_complex = ";".join(filters)
    cmd.extend(["-filter_complex", filter_complex])
    
    # 输出配置 (硬编码最高效的 x264 参数，速度起飞)
    cmd.extend([
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-r", "24", "-t", str(total_dur),
        temp_output
    ])

    # 执行命令
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"❌ FFmpeg 错误日志:\n{result.stderr}")
        raise RuntimeError(f"FFmpeg 渲染失败，场景: {scene['title']}")

    return temp_output


def create_video(data, output_path):
    """主控入口：并行调度 FFmpeg 渲染，并使用极速 Copy 模式拼接最终视频"""
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"🚀 [FFmpeg引擎] 开启并发渲染，共 {len(data)} 个场景...")
        
        results = [None] * len(data)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(process_single_scene_ffmpeg, i, scene, temp_dir): i 
                for i, scene in enumerate(data)
            }
            for future in concurrent.futures.as_completed(futures):
                i = futures[future]
                try:
                    results[i] = future.result()
                    print(f"✅ 场景 {i+1} 压制完成！")
                except Exception as e:
                    print(f"❌ 场景 {i+1} 压制失败: {str(e)}")
                    return None

        if any(res is None for res in results):
            return None

        # 🎬 秒级无损拼接
        print("🎬 正在无损秒级拼接最终视频...")
        concat_list_path = os.path.join(temp_dir, "final_concat.txt")
        with open(concat_list_path, 'w', encoding='utf-8') as f:
            for mp4 in results:
                safe_mp4 = mp4.replace('\\', '/')
                f.write(f"file '{safe_mp4}'\n")

        # 使用 -c copy 直接复制视频流，无需重新编码，1秒内完成！
        concat_cmd = [
            FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0", 
            "-i", concat_list_path, "-c", "copy", output_path
        ]
        
        res = subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            print("🎉 FFmpeg 渲染引擎全流程完成！速度遥遥领先。")
            return output_path
        else:
            print(f"❌ 最终拼接失败:\n{res.stderr.decode('utf-8')}")
            return None
