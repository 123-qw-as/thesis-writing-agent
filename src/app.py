"""
毕设论文写作 Agent 系统 - Streamlit Web UI

运行: streamlit run src/app.py
"""

import streamlit as st
import os
import sys
import time
from datetime import datetime

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
    .chat-container {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1rem;
        background: #fafafa;
        max-height: 600px;
        overflow-y: auto;
    }
    .thesis-editor {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1rem;
        background: white;
        max-height: 600px;
        overflow-y: auto;
    }
    .quick-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .quick-btn {
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        border: 1px solid #667eea;
        background: white;
        color: #667eea;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .quick-btn:hover {
        background: #667eea;
        color: white;
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
    st.session_state.current_thesis = ""
    st.session_state.chat_messages = []
    st.session_state.chat_llm = None
    st.session_state.generation_log = []
    st.session_state.history = []
    st.session_state.selected_model = None
    st.session_state.selected_provider = None
    st.session_state.edit_mode = False

# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 设置")

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

    env_value = os.getenv(config.api_key_env, "")
    api_key = st.text_input(
        f"{config.name} API Key",
        value=env_value,
        type="password",
        help=f"环境变量: {config.api_key_env}",
    )

    st.markdown("---")
    st.markdown(f"**{config.name}**")
    st.caption(f"上下文: {config.context_window:,} tokens | 最大输出: {config.max_tokens:,}")
    if config.price_info:
        st.caption(f"价格: {config.price_info}")
    if config.description:
        st.caption(config.description)

    st.markdown("---")
    if st.button("🔄 重置状态", use_container_width=True, type="secondary"):
        st.session_state.workflow = None
        st.session_state.result = None
        st.session_state.current_thesis = ""
        st.session_state.chat_messages = []
        st.session_state.chat_llm = None
        st.session_state.generation_log = []
        st.session_state.edit_mode = False
        st.rerun()

    if st.session_state.history:
        st.markdown("---")
        st.markdown("**📋 历史记录**")
        for h in reversed(st.session_state.history[-5:]):
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

# ──────────────────────────────────────────────
# Generation Phase (no result yet)
# ──────────────────────────────────────────────
if not st.session_state.result:
    st.markdown("---")
    topic = st.text_input(
        "📝 论文主题",
        placeholder="例如：基于深度学习的图像去雾算法研究",
        label_visibility="visible",
    )

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

    if generate_clicked and topic and api_key:
        st.session_state.selected_model = selected_model
        st.session_state.selected_provider = selected_provider

        with st.spinner("🔧 初始化模型..."):
            try:
                llm = create_llm(
                    model_name=selected_model,
                    api_key=api_key,
                    temperature=0.7,
                )
                st.session_state.workflow = create_thesis_workflow(llm)
                st.session_state.chat_llm = llm
                st.success(f"✅ 模型初始化成功: {config.name}")
            except Exception as e:
                st.error(f"❌ 初始化失败: {str(e)}")
                st.session_state.workflow = None

        if st.session_state.workflow:
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
            log_container = st.empty()
            log_messages = []

            def add_log(msg: str):
                log_messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
                log_container.code("\n".join(log_messages[-10:]), language=None)

            try:
                render_steps(0)
                add_log("开始文献研究阶段...")
                time.sleep(0.3)

                render_steps(1)
                add_log("文献研究完成，开始代码编写...")
                time.sleep(0.3)

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

                render_steps(3)
                add_log("论文生成完成！")

                thesis_content = result.get("thesis_content", "")
                st.session_state.result = result
                st.session_state.current_thesis = thesis_content
                st.session_state.topic = topic
                st.session_state.chat_messages = [
                    {"role": "assistant", "content": f"论文已生成完成！主题：{topic}\n\n您可以直接告诉我需要修改的地方，例如：\n- 帮我修改摘要部分\n- 增加更多实验数据\n- 调整论文结构\n- 润色语言表达"}
                ]
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
                add_log(f"错误: {str(e)}")

# ──────────────────────────────────────────────
# Results + Chat Phase
# ──────────────────────────────────────────────
if st.session_state.result:
    thesis = st.session_state.current_thesis
    code_result = st.session_state.result.get("code_results", "")
    research_result = st.session_state.result.get("research_results", "")

    st.markdown("---")
    st.success(f"✅ 论文生成完成！主题: {st.session_state.topic}")

    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        st.metric("论文字数", f"{len(thesis):,}")
    with r_col2:
        st.metric("对话轮次", len([m for m in st.session_state.chat_messages if m["role"] == "user"]))
    with r_col3:
        st.metric("代码结果", f"{len(code_result):,} 字符")

    # Main layout: Chat + Thesis side by side
    chat_col, thesis_col = st.columns([1, 2])

    with chat_col:
        st.markdown("### 💬 对话修改")

        # Quick action buttons
        quick_actions = [
            "📝 润色摘要",
            "📊 增加实验数据",
            "🔧 调整结构",
            "✨ 优化语言",
            "📚 补充文献",
            "🎯 强化结论",
        ]
        st.markdown('<div class="quick-actions">', unsafe_allow_html=True)
        qa_cols = st.columns(2)
        for i, action in enumerate(quick_actions):
            with qa_cols[i % 2]:
                if st.button(action, key=f"qa_{action}", use_container_width=True, type="secondary"):
                    action_prompts = {
                        "📝 润色摘要": "请帮我润色摘要部分，使其更加精炼和专业，突出研究贡献和创新点",
                        "📊 增加实验数据": "请帮我增加更多实验数据和对比分析，使实验部分更加充实",
                        "🔧 调整结构": "请帮我调整论文结构，使其更加合理和符合学术规范",
                        "✨ 优化语言": "请帮我优化论文的语言表达，使其更加流畅和学术化",
                        "📚 补充文献": "请帮我补充更多相关文献引用，增强论文的学术支撑",
                        "🎯 强化结论": "请帮我强化结论部分，使研究贡献和未来展望更加明确",
                    }
                    user_msg = action_prompts.get(action, action)
                    st.session_state.chat_messages.append({"role": "user", "content": user_msg})
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Chat messages display
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.markdown(msg["content"])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(msg["content"])

        # Chat input
        if user_input := st.chat_input("输入修改要求，如：帮我修改摘要部分..."):
            st.session_state.chat_messages.append({"role": "user", "content": user_input})

            # Process with LLM
            with st.spinner("🤖 AI 正在修改论文..."):
                try:
                    if st.session_state.chat_llm:
                        prompt = f"""你是一位专业的学术论文修改助手。请根据用户的要求修改论文。

当前论文内容：
{thesis[:8000]}

用户要求：{user_input}

请输出修改后的完整论文内容。保持论文的学术性和专业性。
如果用户的要求不适用于当前论文，请说明原因并给出建议。"""

                        response = st.session_state.chat_llm.invoke([HumanMessage(content=prompt)])
                        new_thesis = response.content
                        if isinstance(new_thesis, list):
                            new_thesis = " ".join(
                                block.get("text", "") if isinstance(block, dict) else str(block)
                                for block in new_thesis
                            )

                        if len(new_thesis) > 100:
                            st.session_state.current_thesis = new_thesis
                            assistant_msg = f"✅ 已完成修改！\n\n修改内容：\n- 根据要求：{user_input}\n- 论文字数：{len(new_thesis):,} 字\n\n请查看右侧更新后的论文内容。"
                        else:
                            assistant_msg = f"⚠️ AI 返回的内容较短，可能是理解有误。请重新描述您的要求。\n\nAI 回复：{new_thesis}"
                    else:
                        assistant_msg = "❌ 模型未初始化，请重新生成论文。"

                    st.session_state.chat_messages.append({"role": "assistant", "content": assistant_msg})
                    st.rerun()

                except Exception as e:
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"❌ 修改失败: {str(e)}\n\n请重试或检查 API Key 是否有效。"
                    })
                    st.rerun()

    with thesis_col:
        st.markdown("### 📄 论文内容")

        # Version info
        version_info = f"当前版本 | {len(thesis):,} 字"
        st.caption(version_info)

        thesis_container = st.container()
        with thesis_container:
            st.markdown(thesis)

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

    # Additional tabs below
    st.markdown("---")
    tab2, tab3 = st.tabs(["💻 代码结果", "📊 研究资料"])

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
