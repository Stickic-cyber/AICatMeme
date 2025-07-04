import cv2
import numpy as np
import os
import glob
from moviepy.editor import VideoFileClip, AudioFileClip

def remove_green_screen_and_replace_background(
    input_folder, 
    background_folder, 
    audio_folder, 
    output_folder, 
    temp_folder, 
    green_lower=(35, 85, 70), 
    green_upper=(85, 255, 255),
    image_extensions=['*.jpg', '*.jpeg', '*.png', '*.bmp']
):
    """
    处理输入文件夹中的所有视频，去除绿幕并替换为指定背景图片，同时合并对应的音频文件。
    对于每个背景图片，生成一个对应的视频，并命名为“图片名称视频名称”。

    :param input_folder: 存放绿幕视频的文件夹路径
    :param background_folder: 存放背景图片的文件夹路径
    :param audio_folder: 存放音频文件的文件夹路径
    :param output_folder: 处理后视频的输出文件夹路径
    :param temp_folder: 存放临时视频文件的文件夹路径
    :param green_lower: HSV颜色空间中绿色的下界
    :param green_upper: HSV颜色空间中绿色的上界
    :param image_extensions: 支持的背景图片格式列表
    """
    # 确保输出和临时文件夹存在
    for folder in [output_folder, temp_folder]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"创建文件夹: {folder}")

    # 获取所有背景图片文件
    background_files = []
    for ext in image_extensions:
        background_files.extend(glob.glob(os.path.join(background_folder, ext)))
    
    if not background_files:
        print("未找到背景图片文件。")
        return
    else:
        print(f"找到 {len(background_files)} 张背景图片。")

    # 获取所有视频文件（支持常见视频格式）
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv']
    video_files = []
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(input_folder, ext)))

    if not video_files:
        print("未找到视频文件。")
        return
    else:
        print(f"找到 {len(video_files)} 个视频文件。")

    # 遍历每一张背景图片
    for bg_idx, background_image_path in enumerate(background_files, 1):
        bg_filename = os.path.basename(background_image_path)
        bg_name, bg_ext = os.path.splitext(bg_filename)
        print(f"\n[{bg_idx}/{len(background_files)}] 处理背景图片: {bg_filename}")

        # 读取背景图片
        background = cv2.imread(background_image_path)
        if background is None:
            print(f"无法读取背景图片: {background_image_path}")
            continue
        else:
            print(f"成功读取背景图片: {background_image_path}")

        # 遍历每一个视频文件
        for vid_idx, video_path in enumerate(video_files, 1):
            video_filename = os.path.basename(video_path)
            video_name, video_ext = os.path.splitext(video_filename)
            print(f"  [{vid_idx}/{len(video_files)}] 处理视频: {video_filename}")

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"  无法打开视频: {video_path}")
                continue

            # 获取视频属性
            fps = cap.get(cv2.CAP_PROP_FPS)
            width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用MP4编码

            # 调整背景图片大小以匹配视频分辨率
            bg_resized = cv2.resize(background, (width, height))

            # 准备临时输出视频路径（无音频）
            temp_output_filename = f"temp_{bg_name}_{video_filename}"
            temp_output_path = os.path.join(temp_folder, temp_output_filename)
            out = cv2.VideoWriter(temp_output_path, fourcc, fps, (width, height))
            if not out.isOpened():
                print(f"  无法创建临时视频文件: {temp_output_path}")
                cap.release()
                continue

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            current_frame = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 转换为HSV颜色空间
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                # 创建绿色掩码
                mask = cv2.inRange(hsv, green_lower, green_upper)

                # 进行一些形态学操作以减少噪点
                kernel = np.ones((3,3), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel)

                # 反转掩码，得到前景
                mask_inv = cv2.bitwise_not(mask)

                # 提取前景
                foreground = cv2.bitwise_and(frame, frame, mask=mask_inv)

                # 提取背景
                background_part = cv2.bitwise_and(bg_resized, bg_resized, mask=mask)

                # 合并前景和背景
                combined = cv2.add(foreground, background_part)

                # 写入临时输出视频
                out.write(combined)

                current_frame += 1
                if current_frame % 100 == 0 or current_frame == frame_count:
                    print(f"    已处理 {current_frame}/{frame_count} 帧")

            # 释放视频捕捉和写入对象
            cap.release()
            out.release()
            print(f"  完成视频帧处理: {temp_output_path}")

            # 合并音频
            try:
                # 音频文件路径
                audio_path = os.path.join(audio_folder, f"{video_name}.mp3")
                if not os.path.exists(audio_path):
                    print(f"  对应的音频文件不存在: {audio_path}")
                    # 如果没有音频，直接将临时文件移动到输出文件夹
                    final_output_filename = f"{bg_name}_{video_name}{video_ext}"
                    final_output_path = os.path.join(output_folder, final_output_filename)
                    if os.path.exists(final_output_path):
                        print(f"  最终输出文件已存在，跳过: {final_output_path}")
                    else:
                        os.rename(temp_output_path, final_output_path)
                        print(f"  已移动临时文件到: {final_output_path}")
                    continue

                # 加载处理后的视频（无音频）
                with VideoFileClip(temp_output_path) as processed_clip:
                    # 加载音频文件
                    with AudioFileClip(audio_path) as audio_clip:
                        # 设置音频到处理后的视频
                        final_clip = processed_clip.set_audio(audio_clip)

                        # 准备最终输出路径
                        final_output_filename = f"{bg_name}_{video_name}{video_ext}"
                        final_output_path = os.path.join(output_folder, final_output_filename)

                        # 写入最终视频
                        final_clip.write_videofile(final_output_path, codec='libx264', audio_codec='aac', verbose=False, logger=None)

                print(f"  完成最终视频处理（包含音频）: {final_output_path}")

            except Exception as e:
                print(f"  音频合并失败: {e}")
                # 如果合并失败，保留临时视频文件以便后续检查
                continue

            finally:
                # 删除临时无音频的视频文件
                if os.path.exists(temp_output_path):
                    try:
                        os.remove(temp_output_path)
                        print(f"  已删除临时文件: {temp_output_path}")
                    except PermissionError as pe:
                        print(f"  无法删除临时文件 {temp_output_path}: {pe}")

    print("\n所有视频和背景图片处理完成。")

if __name__ == "__main__":
    # 示例用法
    input_folder = "D:/Project/AImeme/meme"  # 替换为您的输入视频文件夹路径
    audio_folder = "D:/Project/AImeme/meme_audio"  # 替换为您的音频文件夹路径
    background_folder = "D:/Project/AImeme/backgrounds"  # 替换为您的背景图片文件夹路径
    output_folder = "D:/Project/AImeme/output_videos"  # 替换为您的输出文件夹路径
    temp_folder = "D:/Project/AImeme/temp_videos"             # 替换为您的临时文件夹路径

    remove_green_screen_and_replace_background(
        input_folder, 
        background_folder, 
        audio_folder, 
        output_folder,
        temp_folder
    )
