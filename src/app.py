"""
毕设论文写作 Agent 系统 - Streamlit Web UI (优化版)

运行: streamlit run src/app.py
"""

import os
os.environ.setdefault('PYTHONUTF8', '1')

import streamlit as st
import sys
import time
import re
from datetime import datetime

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (OSError, AttributeError):
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, AIMessage
from src.graph import create_thesis_workflow
from src.llm_config import (
    MODEL_REGISTRY, create_llm, auto_select_llm,
    get_providers, get_models_by_provider, get_recommended_models,
)

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI 论文写作 Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Theme
# ──────────────────────────────────────────────
THEME = {
    "primary": "#6366f1",
    "primary_dark": "#4f46e5",
    "secondary": "#a855f7",
    "accent": "#06b6d4",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "bg": "#0f1117",
    "bg_card": "#1a1d29",
    "bg_hover": "#232738",
    "text": "#e2e8f0",
    "text_muted": "#94a3b8",
    "border": "#2d3142",
    "gradient_1": "linear-gradient(135deg, #6366f1, #a855f7)",
    "gradient_2": "linear-gradient(135deg, #06b6d4, #6366f1)",
    "gradient_3": "linear-gradient(135deg, #f59e0b, #ef4444)",
    "gradient_4": "linear-gradient(135deg, #22c55e, #06b6d4)",
}

# ──────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }}

    .stApp {{
        background: {THEME["bg"]};
        color: {THEME["text"]};
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] > div:first-child {{
        background: {THEME["bg_card"]};
        border-right: 1px solid {THEME["border"]};
    }}
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stTextInput label {{
        color: {THEME["text_muted"]} !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    /* Remove default padding/margins */
    .block-container {{
        padding: 2rem 3rem !important;
        max-width: 1400px !important;
    }}

    /* Main header */
    .app-header {{
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.25rem;
    }}
    .app-header h1 {{
        font-size: 2rem;
        font-weight: 700;
        background: {THEME["gradient_1"]};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }}
    .app-header .badge {{
        font-size: 0.7rem;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        background: {THEME["primary"]}22;
        color: {THEME["primary"]};
        font-weight: 600;
        border: 1px solid {THEME["primary"]}44;
    }}
    .app-subtitle {{
        color: {THEME["text_muted"]};
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }}

    /* Stat cards */
    .stat-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 0.75rem;
        margin-bottom: 1.5rem;
    }}
    .stat-card {{
        background: {THEME["bg_card"]};
        border: 1px solid {THEME["border"]};
        border-radius: 12px;
        padding: 1rem 1.25rem;
        transition: all 0.2s;
        position: relative;
        overflow: hidden;
    }}
    .stat-card:hover {{
        border-color: {THEME["primary"]}66;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(99,102,241,0.1);
    }}
    .stat-card .stat-icon {{
        font-size: 1.2rem;
        margin-bottom: 0.3rem;
    }}
    .stat-card .stat-value {{
        font-size: 1.6rem;
        font-weight: 700;
        color: {THEME["text"]};
        line-height: 1.2;
    }}
    .stat-card .stat-label {{
        font-size: 0.75rem;
        color: {THEME["text_muted"]};
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }}
    .stat-card .stat-bar {{
        position: absolute;
        bottom: 0;
        left: 0;
        height: 3px;
        border-radius: 0 2px 0 0;
    }}

    /* Input area */
    .input-area {{
        background: {THEME["bg_card"]};
        border: 1px solid {THEME["border"]};
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }}

    /* Steps */
    .steps-bar {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem;
        background: {THEME["bg_card"]};
        border-radius: 12px;
        border: 1px solid {THEME["border"]};
        margin-bottom: 1rem;
        overflow-x: auto;
    }}
    .step-item {{
        display: flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.4rem 0.75rem;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 500;
        white-space: nowrap;
        color: {THEME["text_muted"]};
        background: transparent;
        transition: all 0.2s;
    }}
    .step-item.active {{
        background: {THEME["primary"]}22;
        color: {THEME["primary"]};
        border: 1px solid {THEME["primary"]}44;
    }}
    .step-item.done {{
        color: {THEME["success"]};
    }}
    .step-item.done::before {{
        content: "✓";
        font-weight: 700;
    }}
    .step-arrow {{
        color: {THEME["border"]};
        font-size: 0.8rem;
        flex-shrink: 0;
    }}

    /* Log */
    .log-box {{
        background: #0d0f14;
        border: 1px solid {THEME["border"]};
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.78rem;
        color: {THEME["text_muted"]};
        max-height: 150px;
        overflow-y: auto;
        margin-bottom: 1rem;
    }}
    .log-box .timestamp {{
        color: {THEME["accent"]}88;
    }}

    /* Chat */
    .chat-area {{
        background: {THEME["bg_card"]};
        border: 1px solid {THEME["border"]};
        border-radius: 12px;
        padding: 1rem;
        height: 100%;
    }}
    .quick-actions-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.4rem;
        margin-bottom: 0.75rem;
    }}
    .quick-actions-grid .stButton button {{
        font-size: 0.78rem !important;
        padding: 0.3rem 0.6rem !important;
        border-radius: 8px !important;
        border: 1px solid {THEME["border"]} !important;
        background: transparent !important;
        color: {THEME["text_muted"]} !important;
        transition: all 0.15s !important;
    }}
    .quick-actions-grid .stButton button:hover {{
        border-color: {THEME["primary"]} !important;
        color: {THEME["primary"]} !important;
        background: {THEME["primary"]}11 !important;
    }}

    /* Thesis display */
    .thesis-panel {{
        background: {THEME["bg_card"]};
        border: 1px solid {THEME["border"]};
        border-radius: 12px;
        padding: 1.5rem;
        max-height: 75vh;
        overflow-y: auto;
    }}
    .thesis-panel h1 {{ color: {THEME["primary"]}; font-size: 1.5rem; }}
    .thesis-panel h2 {{ color: {THEME["secondary"]}; font-size: 1.2rem; margin-top: 1.5rem; }}
    .thesis-panel h3 {{ color: {THEME["text"]}; font-size: 1.05rem; }}
    .thesis-panel p {{ line-height: 1.7; color: {THEME["text"]}; }}
    .thesis-panel img {{
        max-width: 100%;
        border-radius: 8px;
        border: 1px solid {THEME["border"]};
        margin: 0.75rem 0;
    }}
    .thesis-panel strong {{ color: {THEME["accent"]}; }}

    /* Metrics */
    .metric-card {{
        background: {THEME["bg_card"]};
        border: 1px solid {THEME["border"]};
        border-radius: 10px;
        padding: 0.75rem 1rem;
        text-align: center;
    }}
    .metric-card .metric-value {{
        font-size: 1.4rem;
        font-weight: 700;
    }}
    .metric-card .metric-label {{
        font-size: 0.7rem;
        color: {THEME["text_muted"]};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .metric-card .metric-bar {{
        height: 4px;
        border-radius: 2px;
        margin-top: 0.5rem;
        background: {THEME["border"]};
        overflow: hidden;
    }}
    .metric-card .metric-fill {{
        height: 100%;
        border-radius: 2px;
        transition: width 0.5s;
    }}

    /* Evaluation report */
    .eval-section {{
        background: {THEME["bg_card"]};
        border: 1px solid {THEME["border"]};
        border-radius: 12px;
        padding: 1.25rem;
        margin-top: 1rem;
    }}

    /* Buttons */
    .stButton button[kind="primary"] {{
        background: {THEME["gradient_1"]} !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.2s !important;
    }}
    .stButton button[kind="primary"]:hover {{
        transform: translateY(-1px);
        box-shadow: 0 8px 24px rgba(99,102,241,0.3) !important;
    }}

    /* Divider */
    .custom-divider {{
        height: 1px;
        background: {THEME["border"]};
        margin: 1.5rem 0;
    }}

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px !important;
        padding: 0.4rem 1rem !important;
        font-size: 0.85rem !important;
        color: {THEME["text_muted"]} !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: {THEME["primary"]}22 !important;
        color: {THEME["primary"]} !important;
        border-color: {THEME["primary"]}44 !important;
    }}

    /* Spinner */
    .stSpinner > div {{
        border-color: {THEME["primary"]} !important;
    }}

    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}
    ::-webkit-scrollbar-track {{
        background: transparent;
    }}
    ::-webkit-scrollbar-thumb {{
        background: {THEME["border"]};
        border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {THEME["text_muted"]};
    }}

    /* StError / StWarning / StInfo */
    div[data-testid="stMarkdownContainer"] .st-emotion-cache-1mi37y6 {{
        color: {THEME["text"]} !important;
    }}
    .stAlert {{
        background: {THEME["bg_card"]} !important;
        border: 1px solid {THEME["border"]} !important;
        border-radius: 10px !important;
    }}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# State
# ──────────────────────────────────────────────
if "workflow" not in st.session_state:
    st.session_state.workflow = None
    st.session_state.topic = ""
    st.session_state.result = None
    st.session_state.current_thesis = ""
    st.session_state.chat_messages = []
    st.session_state.chat_llm = None
    st.session_state.generation_log = []
    st.session_state.history = []
    st.session_state.selected_model = None
    st.session_state.selected_provider = None
    st.session_state.edit_mode = False
    st.session_state.pipeline_mode = "basic"

# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 0.5rem 0 1rem 0; border-bottom: 1px solid {THEME["border"]}; margin-bottom: 1rem;">
        <div style="font-size: 0.7rem; color: {THEME["text_muted"]}; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.25rem;">AI Thesis Agent</div>
        <div style="font-size: 1.4rem; font-weight: 700; background: {THEME["gradient_1"]}; -webkit-background-clip: text; -webkit-text-fill-color: transparent;">⚙️ 控制面板</div>
    </div>
    """, unsafe_allow_html=True)

    # Pipeline mode
    mode_options = {"basic": "⚡ 基础模式", "enhanced": "🔬 增强模式"}
    mode_labels = list(mode_options.values())
    mode_keys = list(mode_options.keys())
    default_mode_idx = mode_keys.index(st.session_state.pipeline_mode) if st.session_state.pipeline_mode in mode_keys else 0

    selected_mode_label = st.selectbox("运行模式", options=mode_labels, index=default_mode_idx, label_visibility="collapsed")
    st.session_state.pipeline_mode = mode_keys[mode_labels.index(selected_mode_label)]

    mode_desc = {
        "basic": "线性流程：文献 → 代码 → 论文 → 图表，适合快速生成初稿",
        "enhanced": "迭代流程：文献 → 方法 → 实验 → 论文 → 评估 → 改写，含质量门控与 Word 导出",
    }
    st.caption(mode_desc[st.session_state.pipeline_mode])

    st.markdown(f"<div style='height:1px;background:{THEME['border']};margin:0.75rem 0;'></div>", unsafe_allow_html=True)

    # Provider + Model
    provider_icons = {
        "openai": "🟢", "anthropic": "🟣", "deepseek": "🔵",
        "qwen": "🟠", "kimi": "🌙", "glm": "🔴",
        "baichuan": "⚪", "minimax": "🟡",
    }
    providers = get_providers()
    provider_labels = [f"{provider_icons.get(p, '')} {p.upper()}" for p in providers]
    provider_map = dict(zip(provider_labels, providers))

    default_provider_idx = 0
    if st.session_state.selected_provider:
        try:
            default_provider_idx = providers.index(st.session_state.selected_provider)
        except ValueError:
            pass

    selected_label = st.selectbox(
        "模型提供商",
        options=provider_labels,
        index=default_provider_idx,
        label_visibility="collapsed",
    )
    selected_provider = provider_map[selected_label]

    provider_models = get_models_by_provider(selected_provider)
    model_names = list(provider_models.keys())
    recommended = [n for n in model_names if provider_models[n].is_recommended]

    default_model_idx = 0
    if st.session_state.selected_model and st.session_state.selected_model in model_names:
        default_model_idx = model_names.index(st.session_state.selected_model)
    elif recommended:
        default_model_idx = model_names.index(recommended[0])

    model_options = [(f"{'⭐ ' if provider_models[m].is_recommended else ''}{provider_models[m].name}", m) for m in model_names]

    selected_model_label = st.selectbox(
        "模型",
        options=[l for l, _ in model_options],
        index=default_model_idx if default_model_idx < len(model_options) else 0,
        label_visibility="collapsed",
    )
    selected_model = dict(model_options).get(selected_model_label, model_options[0][1])
    config = MODEL_REGISTRY[selected_model]

    api_key = st.text_input(
        f"{config.name} API Key",
        value=os.getenv(config.api_key_env, ""),
        type="password",
        help=f"环境变量: {config.api_key_env}",
    )

    st.markdown(f"""
    <div style="background:{THEME['bg']};border-radius:8px;padding:0.6rem 0.75rem;margin-top:0.5rem;">
        <div style="font-size:0.75rem;color:{THEME['text_muted']};">{config.description or ''}</div>
        <div style="font-size:0.7rem;color:{THEME['text_muted']};margin-top:0.3rem;">
            📦 {config.context_window:,} ctx · 📤 {config.max_tokens:,} tok
            {f' · 💰 {config.price_info}' if config.price_info else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div style='height:1px;background:{THEME['border']};margin:0.75rem 0;'></div>", unsafe_allow_html=True)

    # Reset + History
    if st.button("🔄 重置", use_container_width=True, type="secondary"):
        st.session_state.workflow = None
        st.session_state.result = None
        st.session_state.current_thesis = ""
        st.session_state.chat_messages = []
        st.session_state.chat_llm = None
        st.session_state.generation_log = []
        st.session_state.edit_mode = False
        st.rerun()

    if st.session_state.history:
        st.markdown(f"<div style='font-size:0.75rem;color:{THEME['text_muted']};font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-top:0.5rem;'>📋 历史记录</div>", unsafe_allow_html=True)
        for h in reversed(st.session_state.history[-5:]):
            st.markdown(f"""
            <div style="font-size:0.75rem;padding:0.3rem 0;border-bottom:1px solid {THEME['border']}44;">
                <span style="color:{THEME['text']};">{h['topic'][:25]}</span>
                <span style="color:{THEME['text_muted']};float:right;">{h['time']}</span>
            </div>
            """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Main Content
# ──────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
    <h1>📄 AI 论文写作 Agent</h1>
    <span class="badge">v2.0</span>
</div>
<div class="app-subtitle">多阶段论文智能生成 · LLM 驱动的学术写作助手</div>
""", unsafe_allow_html=True)

# Stats
rec_count = len(get_recommended_models())
st.markdown(f"""
<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-icon">🤖</div>
        <div class="stat-value">{len(MODEL_REGISTRY)}</div>
        <div class="stat-label">可用模型</div>
        <div class="stat-bar" style="width:100%;background:{THEME['gradient_1']};"></div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">🏢</div>
        <div class="stat-value">{len(get_providers())}</div>
        <div class="stat-label">LLM 提供商</div>
        <div class="stat-bar" style="width:100%;background:{THEME['gradient_2']};"></div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">⭐</div>
        <div class="stat-value">{rec_count}</div>
        <div class="stat-label">推荐模型</div>
        <div class="stat-bar" style="width:100%;background:{THEME['gradient_4']};"></div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">📄</div>
        <div class="stat-value">{len(st.session_state.history)}</div>
        <div class="stat-label">已生成论文</div>
        <div class="stat-bar" style="width:100%;background:{THEME['gradient_3']};"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Input + Generate
# ──────────────────────────────────────────────
if not st.session_state.result:
    st.markdown(f"""
    <div class="input-area">
        <div style="font-size:0.85rem;font-weight:600;color:{THEME['text']};margin-bottom:0.5rem;">📝 论文主题</div>
    </div>
    """, unsafe_allow_html=True)

    topic = st.text_input("论文主题", placeholder="例如：基于深度学习的图像去雾算法研究", label_visibility="collapsed")

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        generate_clicked = st.button("🚀 开始生成", type="primary", use_container_width=True, disabled=not topic or not api_key)
    with col_btn2:
        if not api_key:
            st.warning("⚠️ 请在左侧输入 API Key")
        elif not topic:
            st.info("💡 请输入论文主题")
        else:
            mode_tag = "⚡ 基础模式" if st.session_state.pipeline_mode == "basic" else "🔬 增强模式"
            st.info(f"✅ 准备就绪 · {mode_tag} · {config.name}")

    # ── Generate ──
    if generate_clicked and topic and api_key:
        st.session_state.selected_model = selected_model
        st.session_state.selected_provider = selected_provider

        with st.spinner("🔧 初始化模型..."):
            try:
                llm = create_llm(model_name=selected_model, api_key=api_key, temperature=0.7)
                if st.session_state.pipeline_mode == "basic":
                    st.session_state.workflow = create_thesis_workflow(llm)
                else:
                    st.session_state.workflow = "enhanced"
                st.session_state.chat_llm = llm
            except Exception as e:
                st.error(f"❌ 初始化失败: {str(e)}")
                st.session_state.workflow = None

        if st.session_state.workflow:
            # Steps bar
            if st.session_state.pipeline_mode == "basic":
                steps = ["📚 文献研究", "💻 代码编写", "📝 论文撰写", "🎨 图表生成", "✅ 完成"]
            else:
                steps = ["📚 文献调研", "🔧 方法设计", "🧪 实验", "📝 论文撰写", "🎨 图表生成", "🔍 评估", "📄 导出"]

            step_placeholder = st.empty()
            log_placeholder = st.empty()
            log_lines = []

            def render_steps(current: int):
                html = '<div class="steps-bar">'
                for i, s in enumerate(steps):
                    cls = "step-item"
                    if i < current: cls += " done"
                    elif i == current: cls += " active"
                    html += f'<div class="{cls}">{s}</div>'
                    if i < len(steps) - 1:
                        html += '<span class="step-arrow">›</span>'
                html += "</div>"
                step_placeholder.markdown(html, unsafe_allow_html=True)

            def add_log(msg: str):
                ts = datetime.now().strftime("%H:%M:%S")
                log_lines.append(f'<span class="timestamp">[{ts}]</span> {msg}')
                log_placeholder.markdown(
                    f'<div class="log-box">{"<br>".join(log_lines[-12:])}</div>',
                    unsafe_allow_html=True,
                )

            render_steps(0)
            add_log("🚀 启动生成流程...")

            try:
                if st.session_state.pipeline_mode == "basic":
                    render_steps(1)
                    add_log("📚 文献研究阶段...")
                    time.sleep(0.2)
                    render_steps(2)
                    add_log("💻 代码编写阶段...")
                    time.sleep(0.2)
                    render_steps(3)
                    add_log("📝 论文撰写阶段...")

                    result = st.session_state.workflow.invoke({
                        "messages": [HumanMessage(content=topic)],
                        "current_task": "research",
                        "research_results": "",
                        "code_results": "",
                        "thesis_content": "",
                        "feedback": "",
                    })

                    thesis_content = result.get("thesis_content", "")
                    st.session_state.result = result
                    st.session_state.current_thesis = thesis_content
                    st.session_state.topic = topic
                    st.session_state.chat_messages = [
                        {"role": "assistant", "content": f"✅ 论文已生成！主题：**{topic}**\n\n您可以直接告诉我需要修改的地方，例如：\n- 帮我修改摘要部分\n- 增加更多实验数据\n- 调整论文结构\n- 润色语言表达"}
                    ]
                    render_steps(5)
                    add_log("✅ 论文生成完成！")

                else:
                    render_steps(1)
                    add_log("📚 文献调研中...")
                    import asyncio
                    from src.workflows.enhanced_pipeline import EnhancedResearchPipeline

                    async def run_pipeline():
                        pipeline = EnhancedResearchPipeline(llm)
                        return await pipeline.run(topic, max_iterations=3, enable_comparison=True)

                    result = asyncio.run(run_pipeline())

                    thesis_content = result.get("thesis", "")
                    st.session_state.result = {
                        "thesis_content": thesis_content,
                        "research_results": result.get("research_results", ""),
                        "code_results": result.get("experiment_results", ""),
                        "evaluation_report": result.get("evaluation_report"),
                        "quality_score": result.get("quality_score", 0),
                        "aigc_score": result.get("aigc_score", 0),
                        "data_authenticity": result.get("data_authenticity", 0),
                        "is_pass": result.get("is_pass", False),
                    }
                    if result.get("docx_path"):
                        st.session_state.result["docx_path"] = result["docx_path"]
                    if result.get("pdf_path"):
                        st.session_state.result["pdf_path"] = result["pdf_path"]

                    st.session_state.current_thesis = thesis_content
                    st.session_state.topic = topic
                    st.session_state.chat_messages = [
                        {"role": "assistant", "content": f"✅ 论文已生成！主题：**{topic}**\n\n📊 质量评分: {result.get('quality_score', 0):.1f}/10 · AIGC率: {result.get('aigc_score', 0):.1f}%\n\n您可以直接告诉我需要修改的地方。"}
                    ]
                    render_steps(6)
                    add_log("✅ 增强模式流程完成！")

                st.session_state.history.append({
                    "topic": topic,
                    "model": selected_model,
                    "time": datetime.now().strftime("%m-%d %H:%M"),
                    "length": len(thesis_content),
                })
                st.balloons()
                st.rerun()

            except Exception as e:
                render_steps(0)
                st.error(f"❌ 生成失败: {str(e)}")
                add_log(f"❌ 错误: {str(e)}")

# ──────────────────────────────────────────────
# Results View
# ──────────────────────────────────────────────
if st.session_state.result:
    thesis = st.session_state.current_thesis
    code_result = st.session_state.result.get("code_results", "")
    research_result = st.session_state.result.get("research_results", "")

    # Toolbar
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">
        <div style="display:flex;align-items:center;gap:0.75rem;">
            <span style="font-size:1.1rem;font-weight:600;color:{THEME['text']};">✅ {st.session_state.topic}</span>
            <span style="font-size:0.7rem;padding:0.2rem 0.5rem;border-radius:4px;background:{THEME['primary']}22;color:{THEME['primary']};font-weight:500;">
                {'⚡ 基础' if st.session_state.pipeline_mode == 'basic' else '🔬 增强'}
            </span>
        </div>
        <div style="font-size:0.8rem;color:{THEME['text_muted']};">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics row
    is_enhanced = st.session_state.pipeline_mode == "enhanced"
    m_cols = st.columns(5 if is_enhanced else 4)

    metrics_data = [
        ("📝", f"{len(thesis):,}", "总字数", THEME["gradient_1"], f"{min(len(thesis)/5000*100, 100):.0f}%"),
        ("💬", str(len([m for m in st.session_state.chat_messages if m["role"] == "user"])), "对话轮次", THEME["gradient_2"], "100%"),
        ("📊", f"{len(code_result):,}", "代码结果", THEME["gradient_4"], "100%"),
    ]

    if is_enhanced:
        quality = st.session_state.result.get("quality_score", 0)
        fill_pct = f"{quality/10*100:.0f}%"
        metrics_data.append(("🏆", f"{quality:.1f}/10", "质量评分", THEME["gradient_3"], fill_pct))
        aigc = st.session_state.result.get("aigc_score", 0)
        aigc_fill = f"{min(aigc*2, 100):.0f}%"
        grad = THEME["gradient_4"] if aigc < 20 else (THEME["gradient_3"] if aigc < 40 else THEME["gradient_1"])
        metrics_data.append(("🤖", f"{aigc:.1f}%", "AIGC 率", grad, aigc_fill))
    else:
        metrics_data.append(("⚡", st.session_state.selected_model or "N/A", "生成模型", THEME["gradient_3"], "100%"))

    for i, (icon, val, label, grad, fill) in enumerate(metrics_data):
        with m_cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:1.1rem;margin-bottom:0.15rem;">{icon}</div>
                <div class="metric-value" style="background:{grad};-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{val}</div>
                <div class="metric-label">{label}</div>
                <div class="metric-bar"><div class="metric-fill" style="width:{fill};background:{grad};"></div></div>
            </div>
            """, unsafe_allow_html=True)

    # Main layout
    chat_col, thesis_col = st.columns([1, 1.8])

    # ── Chat ──
    with chat_col:
        st.markdown(f'<div class="chat-area">', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:0.9rem;font-weight:600;color:{THEME["text"]};margin-bottom:0.5rem;">💬 对话修改</div>', unsafe_allow_html=True)

        # Quick actions
        quick_actions = [
            ("📝 润色摘要", "请帮我润色摘要部分，使其更加精炼和专业"),
            ("📊 增加实验", "请帮我增加更多实验数据和对比分析"),
            ("🔧 调整结构", "请帮我调整论文结构，使其更加合理"),
            ("✨ 优化语言", "请帮我优化论文的语言表达"),
            ("📚 补充文献", "请帮我补充更多相关文献引用"),
            ("🎯 强化结论", "请帮我强化结论部分"),
        ]
        st.markdown('<div class="quick-actions-grid">', unsafe_allow_html=True)
        qa_cols = st.columns(2)
        for i, (action, prompt) in enumerate(quick_actions):
            with qa_cols[i % 2]:
                if st.button(action, key=f"qa_{i}", use_container_width=True):
                    st.session_state.chat_messages.append({"role": "user", "content": prompt})
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Messages
        chat_container = st.container(height=350)
        with chat_container:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Input
        if user_input := st.chat_input("输入修改要求..."):
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            with st.spinner("🤖 AI 正在修改..."):
                try:
                    if st.session_state.chat_llm:
                        prompt = f"""你是一位专业的学术论文修改助手。请根据用户的要求修改论文。

当前论文内容：
{thesis[:8000]}

用户要求：{user_input}

请输出修改后的完整论文内容。保持论文的学术性和专业性。"""
                        response = st.session_state.chat_llm.invoke([HumanMessage(content=prompt)])
                        new_thesis = response.content
                        if isinstance(new_thesis, list):
                            new_thesis = " ".join(block.get("text", "") if isinstance(block, dict) else str(block) for block in new_thesis)
                        if len(new_thesis) > 100:
                            st.session_state.current_thesis = new_thesis
                            assistant_msg = f"✅ 已完成修改！论文字数：{len(new_thesis):,}"
                        else:
                            assistant_msg = f"⚠️ AI 返回较短，请重新描述。\n\n回复：{new_thesis}"
                    else:
                        assistant_msg = "❌ 模型未初始化"
                    st.session_state.chat_messages.append({"role": "assistant", "content": assistant_msg})
                    st.rerun()
                except Exception as e:
                    st.session_state.chat_messages.append({"role": "assistant", "content": f"❌ 修改失败: {str(e)}"})
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Thesis ──
    with thesis_col:
        st.markdown(f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;"><span style="font-size:0.9rem;font-weight:600;color:{THEME["text"]};">📄 论文内容</span><span style="font-size:0.75rem;color:{THEME["text_muted"]};">{len(thesis):,} 字</span></div>', unsafe_allow_html=True)

        # Convert image paths in thesis to absolute and check existence
        thesis_display = thesis
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        def fix_img_path(m):
            alt, path = m.groups()
            abs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path)
            if os.path.exists(abs_path):
                return f'![{alt}]({path})'
            return m.group(0)
        thesis_display = re.sub(img_pattern, fix_img_path, thesis_display)

        st.markdown(f'<div class="thesis-panel">{thesis_display}</div>', unsafe_allow_html=True)

        # Download buttons
        st.markdown(f"<div style='height:1px;background:{THEME['border']};margin:1rem 0;'></div>", unsafe_allow_html=True)
        dl_cols = st.columns(3)
        with dl_cols[0]:
            st.download_button("📥 Markdown", data=thesis or "", file_name=f"thesis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", mime="text/markdown", use_container_width=True)
        with dl_cols[1]:
            st.download_button("📥 纯文本", data=thesis or "", file_name=f"thesis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain", use_container_width=True)
        with dl_cols[2]:
            docx_path = st.session_state.result.get("docx_path")
            if docx_path and os.path.exists(docx_path):
                with open(docx_path, "rb") as f:
                    st.download_button("📥 Word", data=f.read(), file_name=os.path.basename(docx_path), mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            else:
                st.button("📥 Word (仅增强)", disabled=True, use_container_width=True)

    # ── Bottom tabs ──
    st.markdown(f"<div style='height:1px;background:{THEME['border']};margin:1.5rem 0;'></div>", unsafe_allow_html=True)
    tab_labels = ["💻 代码结果", "📚 研究资料"]
    if is_enhanced:
        tab_labels.append("🔍 质量评估")
    tab_labels.append("🖼️ 图表预览")

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        if code_result:
            st.code(code_result, language="python")
        else:
            st.info("📭 无代码执行结果")

    with tabs[1]:
        if research_result:
            st.markdown(research_result)
        else:
            st.info("📭 无研究资料")

    # Evaluation tab (enhanced only)
    tab_idx = 2
    if is_enhanced:
        with tabs[2]:
            eval_report = st.session_state.result.get("evaluation_report")
            if eval_report:
                overall = st.session_state.result.get("quality_score", 0)
                aigc = st.session_state.result.get("aigc_score", 0)
                data_auth = st.session_state.result.get("data_authenticity", 0)
                is_pass = st.session_state.result.get("is_pass", False)

                st.markdown(f'<div class="eval-section">', unsafe_allow_html=True)
                ecols = st.columns(4)
                with ecols[0]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">综合评分</div>
                        <div class="metric-value" style="background:{THEME['gradient_1']};-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{overall:.1f}/10</div>
                        <div class="metric-bar"><div class="metric-fill" style="width:{overall/10*100:.0f}%;background:{THEME['gradient_1']};"></div></div>
                    </div>
                    """, unsafe_allow_html=True)
                with ecols[1]:
                    aigc_color = THEME["gradient_4"] if aigc < 20 else (THEME["gradient_3"] if aigc < 40 else THEME["gradient_1"])
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">AIGC 率</div>
                        <div class="metric-value" style="background:{aigc_color};-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{aigc:.1f}%</div>
                        <div class="metric-bar"><div class="metric-fill" style="width:{min(aigc*2,100):.0f}%;background:{aigc_color};"></div></div>
                    </div>
                    """, unsafe_allow_html=True)
                with ecols[2]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">数据真实性</div>
                        <div class="metric-value" style="background:{THEME['gradient_4']};-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{data_auth:.1f}%</div>
                        <div class="metric-bar"><div class="metric-fill" style="width:{data_auth:.0f}%;background:{THEME['gradient_4']};"></div></div>
                    </div>
                    """, unsafe_allow_html=True)
                with ecols[3]:
                    pass_icon = "✅" if is_pass else "❌"
                    pass_color = THEME["success"] if is_pass else THEME["danger"]
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">通过状态</div>
                        <div class="metric-value" style="color:{pass_color};">{pass_icon}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                if hasattr(eval_report, 'to_dict'):
                    report_dict = eval_report.to_dict() if hasattr(eval_report, 'to_dict') else eval_report
                    dims = report_dict.get('dimensions', []) if isinstance(report_dict, dict) else []
                    if dims:
                        st.markdown(f"<div style='font-size:0.85rem;font-weight:600;color:{THEME['text']};margin:0.75rem 0 0.5rem;'>📊 各维度评分</div>", unsafe_allow_html=True)
                        dim_cols = st.columns(len(dims))
                        for i, dim in enumerate(dims):
                            score = dim.get('score', 0) if isinstance(dim, dict) else getattr(dim, 'score', 0)
                            name = dim.get('dimension', '') if isinstance(dim, dict) else getattr(dim, 'dimension', '')
                            with dim_cols[i]:
                                st.markdown(f"""
                                <div class="metric-card">
                                    <div class="metric-label">{name}</div>
                                    <div class="metric-value" style="font-size:1.1rem;">{score:.1f}/10</div>
                                    <div class="metric-bar"><div class="metric-fill" style="width:{score*10:.0f}%;background:{THEME['gradient_1']};"></div></div>
                                </div>
                                """, unsafe_allow_html=True)
            else:
                st.info("📭 无评估报告")
        tab_idx = 3

    # Figures tab
    with tabs[tab_idx]:
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        imgs = re.findall(img_pattern, thesis)
        if imgs:
            st.markdown(f"<div style='font-size:0.9rem;font-weight:600;color:{THEME['text']};margin-bottom:0.75rem;'>🖼️ 论文中包含 {len(imgs)} 张插图</div>", unsafe_allow_html=True)
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            img_cols = st.columns(2)
            for i, (alt, path) in enumerate(imgs):
                abs_path = os.path.join(base, path)
                if os.path.exists(abs_path):
                    # Look for PNG version
                    png_path = abs_path.rsplit('.', 1)[0] + '.png'
                    display_path = png_path if os.path.exists(png_path) else abs_path
                    with img_cols[i % 2]:
                        st.markdown(f"""
                        <div style="background:{THEME['bg']};border:1px solid {THEME['border']};border-radius:10px;padding:0.75rem;margin-bottom:0.75rem;">
                            <div style="font-size:0.8rem;font-weight:600;color:{THEME['text']};margin-bottom:0.5rem;">图{i+1}: {alt}</div>
                        """, unsafe_allow_html=True)
                        st.image(display_path, use_container_width=True)
                        size = os.path.getsize(abs_path)
                        st.markdown(f"""
                            <div style="font-size:0.7rem;color:{THEME['text_muted']};margin-top:0.3rem;">📁 {os.path.basename(path)} · {size/1024:.1f} KB</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("📭 论文中未嵌入插图")
