import cv2,os,subprocess
from moviepy.editor import *
from moviepy.config import change_settings
from moviepy.editor import VideoFileClip, concatenate_videoclips

# 重要的写在最前面，本脚需指定magick.exe路径，以及设置主路径

# 比如：
main_path="D:/AI猫meme"


def BgVideo (text, place, num):
    change_settings({"IMAGEMAGICK_BINARY": r"D:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})# 你的magick.exe所在路径，没有需自行下载

    # 创建一个空白视频，时长为10秒，分辨率为1280x720
    width, height = 1080, 1080
    duration = 10
    blank_clip = ColorClip((width, height), color=(0, 0, 0), duration=duration)

    # 在指定时间点添加图片
    image_clip = ImageClip("%s/background/%s.jpg" % (main_path, place)).resize(width=1080)  # 调整图片大小
    image_start_time = 0  # 图片出现的时间（秒）
    image_end_time = 10  # 图片消失的时间（秒）
    image_clip = image_clip.set_position(('center', 'top')).set_start(image_start_time).set_end(image_end_time)

    # 在指定时间点添加文本
    txt_clip = TextClip(text, fontsize=60, color='black', font='华文细黑',
                        stroke_color='black', stroke_width=3, bg_color='white')
    txt_start_time = 0  # 文本出现的时间（秒）
    txt_end_time = 10  # 文本消失的时间（秒）
    txt_clip = txt_clip.set_position((50, 50)).set_start(txt_start_time).set_end(txt_end_time)

    # 将所有元素合成为一个视频
    final_clip = CompositeVideoClip([blank_clip, image_clip, txt_clip])#, additional_video_clip])

    # 保存最终视频
    final_clip.write_videofile('%s/成品/background%s.mp4'%(main_path, num), codec='libx264', fps=24)

def AddMeme(emo, num):
    # 绿幕视频文件路径
    green_screen_video_path ='%s/meme/%s.mp4'%(main_path,emo)
    # 替换视频文件路径
    replacement_video_path = '%s/成品/background%s.mp4'%(main_path,num)
    # 输出路径
    output_video_path = '%s/成品/%s.mp4'%(main_path,num)
    # 加载绿幕视频
    cap_green = cv2.VideoCapture(green_screen_video_path)
    fps = int(cap_green.get(cv2.CAP_PROP_FPS))
    width = int(cap_green.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap_green.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 加载替换视频
    cap_replacement = cv2.VideoCapture(replacement_video_path)

    # 创建输出视频的写入对象
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # 处理视频帧
    while cap_green.isOpened():
        ret_green, frame_green = cap_green.read()
        ret_replacement, frame_replacement = cap_replacement.read()
        
        if not ret_green or not ret_replacement:
            break
        # 调整替换视频的大小以匹配绿幕视频
        frame_replacement = cv2.resize(frame_replacement, (width, height))

        # 调整颜色阈值以增加抠出绿色的强度
        lower_green = (0, 90, 0)  # 调整了绿色范围的下界
        upper_green = (100, 255, 100)  # 调整了绿色范围的上界
        mask = cv2.inRange(frame_green, lower_green, upper_green)

        # 使用替换视频的对应帧替换绿幕区域
        frame_green[mask != 0] = frame_replacement[mask != 0]

        # 写入输出视频
        out.write(frame_green)

    cap_green.release()
    cap_replacement.release()
    out.release()
    cv2.destroyAllWindows()
    
def AddNewline(text):
    punctuations = ['，','。','！','？','；','：',',', '.', '?', '!', ';', ':']
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

def add_audio_to_video(emo, num):
    # 指定音频文件、视频文件和输出文件
    audio_file = '%s/meme_audio/%s.mp3'%(main_path,emo)
    video_file = '%s/成品/%s.mp4'%(main_path,num)
    output_file = '%s/成品/out%s.mp4'%(main_path,num)
    # 使用FFmpeg将音频添加到视频
    subprocess.run(['ffmpeg', '-i', video_file, '-i', audio_file, '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental', output_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def concatenate_videos(folder_path, video_names, output_file):
    video_clips = []
    for video_name in video_names:
        video_path = os.path.join(folder_path, video_name)
        video_clip = VideoFileClip(video_path)
        video_clips.append(video_clip)

    final_clip = concatenate_videoclips(video_clips)
    final_clip.write_videofile(output_file)

emotions = ['哀求', '崩溃', '吃惊', '得瑟', '得意', '发呆', '烦躁', '害羞', '欢呼', '教训', '惊讶', '绝望', '可怜', '努力', '尴尬', '傻笑', '威严', '无辜', '无助', '兴奋', '勇敢', '愉快']
places = ["医院", "车站", "学校", "餐厅", "厨房", "公园", "图书馆", "银行", "商店", "电影院", "体育馆", "游泳池", "机场", "博物馆", "剧院", "游乐园", "草原", "家里", "村子", "教室", "操场"]

# one example
story = [
  [
    "图书馆",
    "同学，某某学院的某教室怎么走？",
    "得瑟"
  ],
  [
    "操场",
    "她老乡某某回家了，让她过来替上课的。",
    "得意"
  ],
  [
    "教室",
    "然后抬头看见了站在讲台上准备上课的老师——我。",
    "震惊"
  ],
  [
    "教室",
    "打了一个电话之后默默的离开了教室……",
    "尴尬"
  ]
 ]

for i in range(len(story)):
    place = story[i][0]
    text = story[i][1]
    emo = story[i][2]
    processed_text=AddNewline(text)
    # print(processed_text)
    BgVideo (processed_text, place, i)
    AddMeme(emo, i)
    add_audio_to_video(emo, i)

folder_path = "%s/成品"% main_path # 自动创建一个成品所在文件夹，需指定路径
video_names = ["out0.mp4","out1.mp4", "out2.mp4", "out3.mp4"]  # 需要合成的视频文件名列表（倒数第二步）
output_file = "%s/Final.mp4"% main_path  # 合成后的输出最终文件名（最后一步）

concatenate_videos(folder_path, video_names, output_file)

'''把下面的故事分成不同的场景，配上一个情感，以及合适的对话或旁白（少于30字）
要求地点从下面选择：["医院", "车站", "学校", "餐厅", "厨房", "公园", "图书馆", "银行", "商店", "电影院", "体育馆", "游泳池", "机场", "博物馆", "剧院", "游乐园", "草原", "家里", "村子", "教室", "操场"]
要求情感从下面选择：['哀求', '崩溃', '吃惊', '得瑟', '得意', '发呆', '烦躁', '害羞', '欢呼', '教训', '惊讶', '绝望', '可怜', '努力', '其他', '傻笑', '威严', '无辜', '无助', '兴奋', '勇敢', '愉快']
把输出的结果写成以下格式：[[地点1, 文本1, 情感1], [地点2, 文本2, 情感2],...]
故事为：'''




# ["公园", "在公园里，莉莉发现了一只受伤的小鸟", "吃惊"],
#          ["家里", "莉莉小心翼翼地把小鸟带回家", "可怜"],
#          ["家里", "细心给小鸟包扎好伤口", "哀求"],
#          ["村子", "突然火灾爆发，小鸟化身鸟人冲进火场，救出老人", "勇敢"],
#          ["村子", "村民感激鸟人，也感谢莉莉，称她们为村子的英雄", "兴奋"]