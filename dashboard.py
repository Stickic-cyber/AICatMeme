import streamlit as st
import requests
import json
import os

# --- 核心修改点 1：配置你新的阿里云服务器子域名 ---
# 注意：如果你后续在 Nginx 配置了 SSL 证书，这里记得把 http 改成 https
API_BASE_URL = "http://localhost:5000"

st.set_page_config(page_title="Cat Meme Generator", page_icon="🐈", layout="wide")

# --- 注入自定义 CSS ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem; 
            padding-bottom: 1rem;
        }
        header {
            visibility: hidden; 
        }
    </style>
""", unsafe_allow_html=True)

# --- 1. 语言包配置 ---
translations = {
    "zh": {
        "title": "🐈 猫Meme视频生成器 Dashboard",
        "desc": "通过AI自动分析故事脚本，生成对应的猫Meme视频。",
        "sidebar_title": "⚙️ 全局配置",
        "provider_label": "🤖 AI 厂商",
        "api_key_label": "🔑 API Key",
        "api_key_ph": "输入对应的 API Key",
        "base_url_label": "🌐 Base URL (可选)",
        "base_url_ph": "例如: https://api.deepseek.com/v1",
        "model_label": "🧠 选择/输入模型",
        "tab_story": "📖 故事一键生成",
        "tab_debug": "🛠️ JSON 调试模式",
        "story_header": "输入故事自动拆分并生成",
        "story_label": "请输入你的故事大纲：",
        "story_placeholder": "从前有只小猫，今天去上班被老板骂了，非常委屈...",
        "btn_gen_story": "🚀 生成视频",
        "warn_no_story": "请先输入故事内容！",
        "spin_story": "AI正在拆分镜头并渲染视频，请耐心等待...",
        "debug_header": "使用场景 JSON 数据直接生成",
        "debug_label": "输入合法的 JSON 数据：",
        "btn_gen_debug": "🛠️ 调试生成",
        "warn_no_json": "请先输入JSON数据！",
        "spin_debug": "正在读取场景数据并渲染视频...",
        "err_json": "⚠️ 输入的 JSON 格式不正确，请检查语法！",
        "msg_success": "🎉 {msg}",
        "msg_saved": "📁 视频已保存至服务器: {path}",
        "err_gen": "❌ 生成失败: {msg}",
        "err_conn": "🔌 无法连接到后端服务，请检查网络或确认服务端已启动。错误: {err}"
    },
    "en": {
        "title": "🐈 Cat Meme Video Generator",
        "desc": "Automatically analyze story scripts via AI to generate cat meme videos.",
        "sidebar_title": "⚙️ Settings",
        "provider_label": "🤖 AI Provider",
        "api_key_label": "🔑 API Key",
        "api_key_ph": "Enter API Key",
        "base_url_label": "🌐 Base URL (Optional)",
        "base_url_ph": "e.g., https://api.deepseek.com/v1",
        "model_label": "🧠 Model",
        "tab_story": "📖 Story to Video",
        "tab_debug": "🛠️ JSON Debug Mode",
        "story_header": "Enter a story to auto-split and generate",
        "story_label": "Please enter your story outline:",
        "story_placeholder": "Once upon a time, a little cat...",
        "btn_gen_story": "🚀 Generate Video",
        "warn_no_story": "Please enter the story content first!",
        "spin_story": "AI is processing and rendering...",
        "debug_header": "Generate directly using JSON",
        "debug_label": "Enter valid JSON data:",
        "btn_gen_debug": "🛠️ Debug Generation",
        "warn_no_json": "Please enter JSON data first!",
        "spin_debug": "Rendering video...",
        "err_json": "⚠️ Invalid JSON format!",
        "msg_success": "🎉 {msg}",
        "msg_saved": "📁 Video saved on server at: {path}",
        "err_gen": "❌ Generation failed: {msg}",
        "err_conn": "🔌 Cannot connect to backend service. Error: {err}"
    }
}

if 'lang' not in st.session_state:
    st.session_state.lang = 'zh'

# --- 2. 顶部布局 ---
header_col1, header_col2 = st.columns([8, 2])
with header_col2:
    st.write("") 
    lang_choice = st.radio(
        "Language", ("中文", "English"),
        index=0 if st.session_state.lang == 'zh' else 1,
        horizontal=True, label_visibility="collapsed"
    )
    st.session_state.lang = 'zh' if lang_choice == "中文" else 'en'

t = translations[st.session_state.lang]

with header_col1:
    st.title(t["title"])
    st.markdown(t["desc"])

# --- 3. 侧边栏多模型配置 ---
PROVIDER_MODELS = {
    "Google Gemini": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
    "OpenAI": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    "DeepSeek": ["deepseek-chat", "deepseek-reasoner"],
    "Anthropic": ["claude-3-5-sonnet-latest", "claude-3-haiku-20240307"],
    "Custom (OpenAI Compatible)": ["自定义模型名称请在下方输入"]
}

with st.sidebar:
    st.header(t["sidebar_title"])
    
    provider_choice = st.selectbox(t["provider_label"], list(PROVIDER_MODELS.keys()))
    
    if provider_choice == "Custom (OpenAI Compatible)":
        model_choice = st.text_input(t["model_label"], placeholder="例如: qwen-plus")
    else:
        model_choice = st.selectbox(t["model_label"], PROVIDER_MODELS[provider_choice])
    
    api_key_input = st.text_input(t["api_key_label"], type="password", placeholder=t["api_key_ph"])
    
    base_url_input = ""
    if provider_choice in ["OpenAI", "DeepSeek", "Custom (OpenAI Compatible)"]:
        default_base = "https://api.deepseek.com" if provider_choice == "DeepSeek" else ""
        base_url_input = st.text_input(t["base_url_label"], value=default_base, placeholder=t["base_url_ph"])
    
    st.divider()
    if st.session_state.lang == 'zh':
        st.caption("提示：如需使用默认后端配置，保持 Key 为空即可。部分 API（如 DeepSeek 或代理服务）需确认 Base URL 正确。")
    else:
        st.caption("Tip: Leave Key blank to use backend defaults. Ensure Base URL is correct for custom proxies.")

st.divider() 

# --- 4. 页面主体 (Tabs) ---
tab1, tab2 = st.tabs([t["tab_story"], t["tab_debug"]])

# --- 标签页 1: 故事一键生成 ---
with tab1:
    st.subheader(t["story_header"])
    col1_left, col1_right = st.columns(2)
    video_to_play_story = None 
    
    with col1_left:
        story_input = st.text_area(t["story_label"], height=400, placeholder=t["story_placeholder"])
        submit_story = st.button(t["btn_gen_story"], type="primary", key="generate_story", use_container_width=True)
        
        if submit_story:
            if not story_input.strip():
                st.warning(t["warn_no_story"])
            elif provider_choice == "Custom (OpenAI Compatible)" and not model_choice.strip():
                st.warning("请输入自定义模型名称！" if st.session_state.lang == 'zh' else "Please enter a model name!")
            else:
                with st.spinner(t["spin_story"]):
                    try:
                        payload = {
                            "story": story_input,
                            "provider": provider_choice,
                            "model": model_choice,
                            "api_key": api_key_input.strip(),
                            "base_url": base_url_input.strip()
                        }
                        response = requests.post(
                            f"{API_BASE_URL}/generate_video", 
                            json=payload,
                            timeout=300 
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success(t["msg_success"].format(msg=result.get('message')))
                            
                            # --- 核心修改点 2：改为网络 URL 播放模式 ---
                            file_path = result.get('file_path')
                            if file_path:
                                file_name = os.path.basename(file_path)
                                video_url = f"{API_BASE_URL}/outputs/{file_name}"
                                video_to_play_story = video_url
                                # 同时保留一条文件路径的提示，方便查阅
                                st.info(t["msg_saved"].format(path=file_path))
                            else:
                                st.error("未获取到视频路径")
                        else:
                            st.error(t["err_gen"].format(msg=response.json().get('message', 'Unknown Error')))
                    except requests.exceptions.RequestException as e:
                        st.error(t["err_conn"].format(err=str(e)))

    with col1_right:
        if video_to_play_story:
            vid_col, spacer = st.columns([8, 2])
            with vid_col:
                st.video(video_to_play_story)

# --- 标签页 2: JSON 调试模式 ---
with tab2:
    st.subheader(t["debug_header"])
    col2_left, col2_right = st.columns(2)
    
    default_json = """{
  "scenes": [
    {
      "title": "特工潜入",
      "place": "office",
      "scene_type": "single",
      "characters": [
        {
          "name": "特工·大橘",
          "emotion": "majestic",
          "text": "目标已经锁定。那个白色的保险箱（冰箱）里，一定藏着改变世界的终极武器。"
        }
      ]
    },
    {
      "title": "风险评估",
      "place": "lab",
      "scene_type": "dialogue",
      "characters": [
        {
          "name": "总部辅助",
          "emotion": "scolding",
          "text": "大橘！冷静点！如果你被人类的‘红外线’（走廊灯）扫到，今晚就彻底暴露了！"
        },
        {
          "name": "特工·大橘",
          "emotion": "smirk",
          "text": "呵，这些所谓的‘激光’，只是我平时玩剩下的玩具罢了。看我闪现！"
        }
      ]
    },
    {
      "title": "最后的冲击",
      "place": "lab",
      "scene_type": "single",
      "characters": [
        {
          "name": "特工·大橘",
          "emotion": "striving",
          "text": "保险箱的大门正在开启！白色的光芒... 我看见它了！是神圣的冻干！"
        }
      ]
    },
    {
      "title": "真相大白",
      "place": "home",
      "scene_type": "single",
      "characters": [
        {
          "name": "大橘",
          "emotion": "awkward",
          "text": "呃，妈？你听我解释... 我只是半夜起来帮冰箱检查一下制冷效果，绝对不是在偷吃。"
        }
      ]
    }
  ]
}"""
    video_to_play_debug = None 
    
    with col2_left:
        json_input = st.text_area(t["debug_label"], value=default_json, height=400)
        submit_debug = st.button(t["btn_gen_debug"], key="generate_debug", use_container_width=True)
        
        if submit_debug:
            if not json_input.strip():
                st.warning(t["warn_no_json"])
            else:
                try:
                    parsed_json = json.loads(json_input)
                    with st.spinner(t["spin_debug"]):
                        parsed_json["provider"] = provider_choice
                        parsed_json["model"] = model_choice
                        parsed_json["api_key"] = api_key_input.strip()
                        parsed_json["base_url"] = base_url_input.strip()
                        
                        response = requests.post(
                            f"{API_BASE_URL}/generate_video_debug", 
                            json=parsed_json,
                            timeout=300
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success(t["msg_success"].format(msg=result.get('message')))
                            
                            # --- 核心修改点 3：改为网络 URL 播放模式 ---
                            file_path = result.get('file_path')
                            if file_path:
                                file_name = os.path.basename(file_path)
                                video_url = f"{API_BASE_URL}/outputs/{file_name}"
                                video_to_play_debug = video_url
                                st.info(t["msg_saved"].format(path=file_path))
                            else:
                                st.error("未获取到视频路径")
                        else:
                            st.error(t["err_gen"].format(msg=response.json().get('message', 'Unknown Error')))
                            
                except json.JSONDecodeError:
                    st.error(t["err_json"])
                except requests.exceptions.RequestException as e:
                    st.error(t["err_conn"].format(err=str(e)))
                    
    with col2_right:
        if video_to_play_debug:
            vid_col, spacer = st.columns([8, 2])
            with vid_col:
                st.video(video_to_play_debug)
