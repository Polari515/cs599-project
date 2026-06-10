import os
import sys

# 将 src 目录添加到 Python 路径
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from dotenv import load_dotenv
from agents.main_controller import MainController
import streamlit as st

# 页面配置
st.set_page_config(
    page_title="智能穿搭助手",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义 CSS 样式 - 参考 DeepSeek 设计风格
st.markdown("""
<style>
/* 主容器样式 */
.main-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 1rem;
}

/* 输入区域 */
.input-area {
    display: flex;
    gap: 0.75rem;
    padding: 0.5rem;
    background-color: white;
    border-radius: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* 输入框 */
.input-area input {
    flex: 1;
    border: none;
    outline: none;
    padding: 0.75rem 1rem;
    font-size: 0.95rem;
    background-color: #f5f5f5;
    border-radius: 0.75rem;
}

/* 发送按钮 */
.send-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.75rem;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s ease;
}

.send-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.send-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

/* 欢迎消息 */
.welcome-message {
    text-align: center;
    padding: 2rem;
    color: #666;
}

.welcome-message h3 {
    color: #333;
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# 初始化 session state
if "controller" not in st.session_state:
    st.session_state.controller = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def init_controller():
    """初始化控制器"""
    load_dotenv()
    st.session_state.controller = MainController()

# 初始化控制器
if st.session_state.controller is None:
    with st.spinner("正在初始化..."):
        init_controller()

# 主界面
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# 头部
st.markdown("""
<div style="text-align: center; margin-bottom: 1rem;">
    <h1 style="color: #333; margin-bottom: 0.25rem;">👔 智能穿搭助手</h1>
    <p style="color: #666; font-size: 0.9rem;">基于 AI 的智能穿搭推荐系统</p>
</div>
""", unsafe_allow_html=True)

# 欢迎消息
if not st.session_state.chat_history:
    st.markdown("""
    <div class="welcome-message">
        <h3>👋 欢迎使用智能穿搭助手</h3>
        <p>我可以根据天气和您的衣橱为您推荐穿搭</p>
        <p style="font-size: 0.85rem; margin-top: 1rem; color: #999;">
            试试这些问题：<br>
            "今天天气怎么样"<br>
            "今天穿什么"<br>
            "添加白衬衫，上衣，白色，棉"
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    for message in st.session_state.chat_history:
        role = message.get("role", "assistant")
        content = message.get("content", "")
        with st.chat_message("user" if role == "user" else "assistant"):
            st.markdown(content)

# 输入区域
st.markdown('<div class="input-area">', unsafe_allow_html=True)

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "",
        key="user_input",
        placeholder="输入您的问题或需求...",
        label_visibility="collapsed",
        max_chars=500
    )
    submitted = st.form_submit_button("发送")

if submitted:
    if user_input.strip():
        # 1. 记录用户输入
        st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
        # 2. 追加一个"思考中"的占位消息
        st.session_state.chat_history.append({"role": "assistant", "content": "🤔 思考中..."})
        # 3. 立即 rerun，让页面先渲染出"思考中"提示
        st.rerun()
    else:
        st.warning("请输入内容")

# 4. 每次页面渲染时，检测最后一条是否为占位消息（即是否需要调用大模型）
if st.session_state.chat_history and st.session_state.chat_history[-1]["content"] == "🤔 思考中...":
    # 获取用户的真实输入（倒数第二条）
    real_input = st.session_state.chat_history[-2]["content"]
    try:
        result = st.session_state.controller.invoke(
            real_input,
            st.session_state.chat_history[:-2]  # 传给大模型的历史记录，排除占位和当前输入
        )
        assistant_reply = result.get("final_output", "抱歉，暂时没有生成回复。")
    except Exception as e:
        assistant_reply = f"抱歉，发生了错误：{str(e)}"
    # 5. 将占位消息替换为真正的回复
    st.session_state.chat_history[-1] = {"role": "assistant", "content": assistant_reply}
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
