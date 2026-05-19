"""
毕设论文写作 Agent 系统 - Streamlit Web UI

运行: streamlit run src/app.py
"""

import streamlit as st
import os
import sys
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from src.graph import create_thesis_workflow
from src.llm_config import (
    MODEL_REGISTRY, create_llm, auto_select_llm,
    get_providers, get_models_by_provider, get_recommended_models,
)

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="毕设论文写作 Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* 全局 */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }

    /* 卡片样式 */
    .model-card {
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        background: #fafafa;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .model-card:hover {
        border-color: #667eea;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
    }
    .model-card.selected {
        border-color: #667eea;
        background: #f0f2ff;
    }
    .provider-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        background: #e8eaf6;
        color: #3f51b5;
    }
    .rec-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        background: #e8f5e9;
        color: #2e7d32;
        margin-left: 4px;
    }

    /* 步骤指示器 */
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin: 1.5rem 0;
    }
    .step {
        flex: 1;
        text-align: center;
        padding: 0.8rem 0.5rem;
        border-radius: 8px;
        background: #f5f5f5;
        color: #999;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .step.active {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .step.done {
        background: #4caf50;
        color: white;
    }
    .step-arrow {
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ccc;
        font-size: 1.2rem;
        padding: 0 0.3rem;
    }

    /* 统计卡片 */
    .stat-card {
        padding: 1rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
    }
    .stat-card .number {
        font-size: 1.8rem;
        font-weight: 700;
    }
    .stat-card .label {
        font-size: 0.8rem;
        opacity: 0.85;
    }

    /* 侧边栏 */
    .sidebar-section {
        margin-bottom: 1.5rem;
    }

    /* 下载按钮 */
    .download-row {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# State Management
# ──────────────────────────────────────────────
if "workflow" not in st.session_state:
    st.session_state.workflow = None
    st.session_state.topic = ""
    st.session_state.result = None
    st.session_state.generation_log = []
    st.session_state.history = []
    st.session_state.selected_model = None
    st.session_state.selected_provider = None

# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 设置")

    # Provider selection with icons
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
        "提供商",
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

    model_options = []
    for m in model_names:
        cfg = provider_models[m]
        label = f"{'⭐ ' if cfg.is_recommended else ''}{cfg.name}"
        model_options.append((label, m))

    selected_model_label = st.selectbox(
        "模型",
        options=[l for l, _ in model_options],
        index=default_model_idx if default_model_idx < len(model_options) else 0,
        label_visibility="collapsed",
    )
    selected_model = dict(model_options).get(selected_model_label, model_options[0][1])

    config = MODEL_REGISTRY[selected_model]

    # API Key input
    env_value = os.getenv(config.api_key_env, "")
    api_key = st.text_input(
        f"{config.name} API Key",
        value=env_value,
        type="password",
        help=f"环境变量: {config.api_key_env}",
    )

    # Model info card
    st.markdown("---")
    st.markdown(f"**{config.name}**")
    st.caption(f"上下文: {config.context_window:,} tokens | 最大输出: {config.max_tokens:,}")
    if config.price_info:
        st.caption(f"价格: {config.price_info}")
    if config.description:
        st.caption(config.description)

    # Quick actions
    st.markdown("---")
    if st.button("🔄 重置状态", use_container_width=True, type="secondary"):
        st.session_state.workflow = None
        st.session_state.result = None
        st.session_state.generation_log = []
        st.rerun()

    # History
    if st.session_state.history:
        st.markdown("---")
        st.markdown("**📋 历史记录**")
        for i, h in enumerate(reversed(st.session_state.history[-5:])):
            st.caption(f"{h['time']} - {h['topic'][:20]}...")

# ──────────────────────────────────────────────
# Main Content
# ──────────────────────────────────────────────
st.markdown('<div class="main-header">🎓 毕设论文写作 Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI 驱动的多阶段论文生成与质量评估系统</div>', unsafe_allow_html=True)

# Stats row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="stat-card"><div class="number">{len(MODEL_REGISTRY)}</div><div class="label">可用模型</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stat-card"><div class="number">{len(get_providers())}</div><div class="label">LLM 提供商</div></div>', unsafe_allow_html=True)
with col3:
    rec_count = len(get_recommended_models())
    st.markdown(f'<div class="stat-card"><div class="number">{rec_count}</div><div class="label">推荐模型</div></div>', unsafe_allow_html=True)
with col4:
    hist_count = len(st.session_state.history)
    st.markdown(f'<div class="stat-card"><div class="number">{hist_count}</div><div class="label">已生成论文</div></div>', unsafe_allow_html=True)

# Topic input
st.markdown("---")
topic = st.text_input(
    "📝 论文主题",
    placeholder="例如：基于深度学习的图像去雾算法研究",
    value=st.session_state.topic if st.session_state.topic else "",
    label_visibility="visible",
)

# Generate button
col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    generate_clicked = st.button(
        "🚀 开始生成",
        type="primary",
        use_container_width=True,
        disabled=not topic or not api_key,
    )

with col_btn2:
    if not api_key:
        st.warning("⚠️ 请在左侧输入 API Key")
    elif not topic:
        st.info("💡 请输入论文主题")

# ──────────────────────────────────────────────
# Generation Process
# ──────────────────────────────────────────────
if generate_clicked:
    if not api_key:
        st.error("请先输入 API Key")
    elif not topic:
        st.error("请输入论文主题")
    else:
        # Save selections
        st.session_state.selected_model = selected_model
        st.session_state.selected_provider = selected_provider

        # Initialize workflow
        with st.spinner("🔧 初始化模型..."):
            try:
                llm = create_llm(
                    model_name=selected_model,
                    api_key=api_key,
                    temperature=0.7,
                )
                st.session_state.workflow = create_thesis_workflow(llm)
                st.success(f"✅ 模型初始化成功: {config.name}")
            except Exception as e:
                st.error(f"❌ 初始化失败: {str(e)}")
                st.session_state.workflow = None

        if st.session_state.workflow:
            # Step indicators
            steps = ["📚 文献研究", "💻 代码编写", "📝 论文撰写", "✅ 完成"]
            step_placeholder = st.empty()

            def render_steps(current_idx: int):
                cols = step_placeholder.columns([2, 1, 2, 1, 2, 1, 2])
                for i, s in enumerate(steps):
                    col_idx = i * 2
                    if i < current_idx:
                        cols[col_idx].markdown(f'<div class="step done">{s}</div>', unsafe_allow_html=True)
                    elif i == current_idx:
                        cols[col_idx].markdown(f'<div class="step active">{s}</div>', unsafe_allow_html=True)
                    else:
                        cols[col_idx].markdown(f'<div class="step">{s}</div>', unsafe_allow_html=True)
                    if i < len(steps) - 1:
                        cols[col_idx + 1].markdown('<div class="step-arrow">→</div>', unsafe_allow_html=True)

            render_steps(0)

            # Status log
            log_container = st.empty()
            log_messages = []

            def add_log(msg: str):
                log_messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
                log_container.code("\n".join(log_messages[-10:]), language=None)

            try:
                # Phase 1: Research
                render_steps(0)
                add_log("开始文献研究阶段...")
                time.sleep(0.3)

                # Phase 2: Code
                render_steps(1)
                add_log("文献研究完成，开始代码编写...")
                time.sleep(0.3)

                # Phase 3: Write
                render_steps(2)
                add_log("代码编写完成，开始论文撰写...")

                result = st.session_state.workflow.invoke({
                    "messages": [HumanMessage(content=topic)],
                    "current_task": "research",
                    "research_results": "",
                    "code_results": "",
                    "thesis_content": "",
                    "feedback": ""
                })

                # Done
                render_steps(3)
                add_log("论文生成完成！")

                st.session_state.result = result
                st.session_state.topic = topic
                st.session_state.history.append({
                    "topic": topic,
                    "model": selected_model,
                    "time": datetime.now().strftime("%m-%d %H:%M"),
                    "length": len(result.get("thesis_content", "")),
                })

                st.balloons()
                st.rerun()

            except Exception as e:
                render_steps(0)
                st.error(f"❌ 生成失败: {str(e)}")
                add_log(f"错误: {str(e)}")

# ──────────────────────────────────────────────
# Results Display
# ──────────────────────────────────────────────
if st.session_state.result:
    result = st.session_state.result
    thesis = result.get("thesis_content", "")
    code_result = result.get("code_results", "")
    research_result = result.get("research_results", "")

    st.markdown("---")
    st.success(f"✅ 论文生成完成！主题: {st.session_state.topic}")

    # Result stats
    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        st.metric("论文字数", f"{len(thesis):,}")
    with r_col2:
        st.metric("研究资料", f"{len(research_result):,} 字符")
    with r_col3:
        st.metric("代码结果", f"{len(code_result):,} 字符")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📄 论文内容", "💻 代码结果", "📊 研究资料"])

    with tab1:
        if thesis:
            st.markdown(thesis)
        else:
            st.info("论文内容为空")

        # Download buttons
        st.markdown("---")
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                "📥 下载 Markdown",
                data=thesis or "",
                file_name=f"thesis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with dl_col2:
            st.download_button(
                "📥 下载纯文本",
                data=thesis or "",
                file_name=f"thesis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

    with tab2:
        if code_result:
            st.code(code_result, language="python")
        else:
            st.info("无代码执行结果")

    with tab3:
        if research_result:
            st.markdown(research_result)
        else:
            st.info("无研究资料")
