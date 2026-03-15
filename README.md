# 🐈 AICatMeme: AI 驱动的猫 Meme 视频全自动生成流水线 (V2.0)

欢迎来到 **AICatMeme**！这是一个利用大模型（Gemini/OpenAI/DeepSeek 等）自动拆分剧本，并结合猫片素材库自动合成“猫片”视频的开源项目。

---

### 🎥 效果示例 / Example Preview

**Fan-submitted video 来自粉丝的投稿视频：**

[https://github.com/user-attachments/assets/69a448a4-8dea-4ee9-b8b9-a2b8b231f84b](https://github.com/user-attachments/assets/69a448a4-8dea-4ee9-b8b9-a2b8b231f84b)

🖼️ *The background image will also change according to the prompt.*
📌 *背景图也会根据 prompt 自动更换！*

---

### 🚀 重磅更新 / Big Update!

微信小程序已正式上线！📱 打开微信，搜索：**AI视频生成猫meme** 即可体验！或直接扫描二维码进入👇

![gh\_d8d6e3fde1de\_430](https://github.com/user-attachments/assets/4d2ec73b-c029-4d11-beb4-95c45fd2d9fc)
---

### 🛠️ 环境准备与安装 / Installation

#### 1. 克隆仓库到本地

打开终端，执行以下命令：

```bash
git clone https://github.com/Stickic-cyber/AICatMeme.git
cd AICatMeme

```

#### 2. 安装 Python 依赖

建议使用虚拟环境（如 Conda 或 venv）：

```bash
pip install -r requirements.txt

```

---

### 📖 快速运行指南 (V2.0 架构)

项目采用了**预处理 + 后端 + 前端**的分离架构，请按顺序执行：

#### 第一步：素材库预处理 (Pre-Process)

在正式生成前，你需要将原始绿幕素材转化为干净的透明 PNG 序列。

1. 将你的 `.mp4` 绿幕素材放入 `meme_org` 文件夹。
2. 运行预处理脚本：
```bash
python PreProcessVideo.py

```


*该脚本会执行强力去绿光算法，并将素材拆解为带透明通道的 PNG 序列和音频。*

#### 第二步：启动后端服务 (Backend)

后端负责接收任务、调用 AI API 以及执行视频渲染逻辑。

1. 确保 Redis 运行中（可选，用于请求限流）。
2. 运行 Flask 后端：
```bash
python app.py

```


*服务默认运行在 `5000` 端口。*

#### 第三步：启动交互面板 (Dashboard)

1. 启动前端 Web 界面：
```bash
streamlit run dashboard.py

```


2. 浏览器访问 `http://localhost:8501`。
3. **配置：** 在侧边栏配置 AI 厂商（Gemini/OpenAI/DeepSeek 等）及 API Key，即可开始生成！

---

### 📂 核心文件职能说明

| 文件名 | 职能 | 说明 |
| --- | --- | --- |
| **`PreProcessVideo.py`** | **素材加工** | 绿幕抠图核心。采用 `colorkey` + `despill` 滤镜，保证素材边缘丝滑。 |
| **`app.py`** | **后端核心** | 生产级 Flask 服务，支持 AI 脚本分析与视频合成调度。 |
| **`dashboard.py`** | **前端 UI** | 基于 Streamlit。支持多语言切换、多模型配置及左右分栏视频预览。 |

---

### 📜 路径配置提醒 (Path Configuration)

为了保证程序运行，请确保：

* ✅ **ImageMagick 路径** 已在 `core/config.py` 中正确指向其 `magick.exe` 位置。
* ✅ **素材路径** 建议使用相对路径，以便项目在不同环境下都能直接跑通。

