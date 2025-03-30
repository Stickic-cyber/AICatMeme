import os
import cv2
from moviepy.editor import *
from moviepy.config import change_settings

# 重要的写在最前面，本脚需指定magick.exe路径
# 需自行下载 imagemagick.exe

# 设置主路径
main_path = "D:/AICatmeme"

# 确保“成品”文件夹存在
output_folder = f"{main_path}/成品"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def BgVideo(text, place, num):
    change_settings({"IMAGEMAGICK_BINARY": r"D:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})  # 设置 imagemagick 路径

    # 创建一个空白视频，时长为10秒，分辨率为1080x1080
    width, height = 1080, 1080
    duration = 10
    blank_clip = ColorClip((width, height), color=(0, 0, 0), duration=duration)

    # 在指定时间点添加图片
    image_clip = ImageClip(f"{main_path}/backgrounds/{place}.jpg").resize(width=1080)  # 调整图片大小
    image_clip = image_clip.set_position(('center', 'top')).set_start(0).set_end(10)

    # 在指定时间点添加文本
    txt_clip = TextClip(text, fontsize=60, color='black', font='华文细黑', stroke_color='black', stroke_width=3, bg_color='white')
    txt_clip = txt_clip.set_position((50, 50)).set_start(0).set_end(10)

    # 合成视频
    final_clip = CompositeVideoClip([blank_clip, image_clip, txt_clip])

    # 保存最终视频
    final_clip.write_videofile(f'{output_folder}/backgrounds{num}.mp4', codec='libx264', fps=24)

def AddMeme(emo, num):
    # 加载绿幕视频和替换视频
    green_screen_video_path = f'{main_path}/meme/{emo}.mp4'
    replacement_video_path = f'{output_folder}/backgrounds{num}.mp4'
    output_video_path = f'{output_folder}/{num}.mp4'
    
    cap_green = cv2.VideoCapture(green_screen_video_path)
    cap_replacement = cv2.VideoCapture(replacement_video_path)

    fps = int(cap_green.get(cv2.CAP_PROP_FPS))
    width = int(cap_green.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap_green.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 输出视频对象
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # 处理每一帧
    while cap_green.isOpened():
        ret_green, frame_green = cap_green.read()
        ret_replacement, frame_replacement = cap_replacement.read()

        if not ret_green or not ret_replacement:
            break

        # 调整替换视频的大小
        frame_replacement = cv2.resize(frame_replacement, (width, height))

        # 设置绿色屏幕的范围
        lower_green = (0, 90, 0)
        upper_green = (100, 255, 100)
        mask = cv2.inRange(frame_green, lower_green, upper_green)

        # 替换绿幕区域
        frame_green[mask != 0] = frame_replacement[mask != 0]

        # 写入输出视频
        out.write(frame_green)

    cap_green.release()
    cap_replacement.release()
    out.release()
    cv2.destroyAllWindows()

def AddNewline(text):
    punctuations = ['，', '。', '！', '？', '；', '：', ',', '.', '?', '!', ';', ':']
    result = ''
    buffer = ''
    for char in text:
        buffer += char
        if char in punctuations:
            if len(buffer.strip()) > 7:
                result += buffer + '\n'
                buffer = ''
    result += buffer  # 添加最后一部分文本
    if result[-1] == '\n':
        return result[:-1]
    else:
        return result

def concatenate_videos(folder_path, video_names, output_file):
    video_clips = []
    for video_name in video_names:
        video_path = os.path.join(folder_path, video_name)
        video_clip = VideoFileClip(video_path)
        video_clips.append(video_clip)

    final_clip = concatenate_videoclips(video_clips)
    final_clip.write_videofile(output_file)

def add_audio_to_video(video_file, audio_file, output_file):
    video = VideoFileClip(video_file)
    audio = AudioFileClip(audio_file)
    
    # 将音频设置到视频
    video_with_audio = video.set_audio(audio)
    
    # 写入输出文件
    video_with_audio.write_videofile(output_file, codec='libx264', audio_codec='aac')

# 示例故事
'''
地点严格从以下选择：["concert", "fantacy", "others", "rooftop", "stage", "airport", "amusementpark", "bank", "cinema", "classroom", "grassland", "gym", "home", "hospital", "kitchen", "library", "museum", "park", "playground", "pool", "restaurant", "school", "shop", "station", "theater", "village"]；
情感严格从以下选择：["哀求", "崩溃", "吃惊", "大笑", "呆滞", "得瑟", "得意", "烦躁", "害羞", "坏笑", "欢呼", "饥饿", "焦急", "教训", "惊讶", "可怜", "蔑视", "努力", "其他", "傻笑", "痛苦", "威严", "无辜", "无奈", "无助", "兴奋", "勇敢", "愉快", "震惊","愉快"]
'''

story = [
    ["library", "同学，某某学院的某教室怎么走？", "得瑟"],
    ["playground", "她老乡某某回家了，让她过来替上课的。", "得意"],
    ["classroom", "然后抬头看见了站在讲台上准备上课的老师——我。", "震惊"],
    ["classroom", "打了一个电话之后默默的离开了教室……", "尴尬"]
]

# 根据故事自动生成视频文件名
video_names = []

# 处理每个故事片段
for i in range(len(story)):
    place = story[i][0]
    text = story[i][1]
    emo = story[i][2]
    processed_text = AddNewline(text)
    
    BgVideo(processed_text, place, i)
    AddMeme(emo, i)
    
    # 添加音频到视频
    audio_file = f"{main_path}/meme_audio/{emo}.mp3"
    video_file = f"{output_folder}/{i}.mp4"
    output_video_file = f"{output_folder}/out{i}.mp4"
    
    add_audio_to_video(video_file, audio_file, output_video_file)
    
    # 将输出视频文件名添加到视频列表中
    video_names.append(f"out{i}.mp4")

# 合成视频文件
folder_path = f"{main_path}/成品"
output_file = f"{main_path}/Final.mp4"

# 合并视频
concatenate_videos(folder_path, video_names, output_file)
