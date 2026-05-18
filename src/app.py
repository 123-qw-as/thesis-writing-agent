import streamlit as st
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from src.graph import create_thesis_workflow
from src.llm_config import MODEL_REGISTRY, create_llm, get_providers, get_models_by_provider

st.set_page_config(
    page_title="毕设论文写作助手",
    page_icon="📚",
    layout="wide"
)

st.title("📚 毕设论文写作 Agent 系统")

if "workflow" not in st.session_state:
    st.session_state.workflow = None
    st.session_state.topic = ""
    st.session_state.result = None

def init_workflow(model_name: str, api_key: str):
    config = MODEL_REGISTRY[model_name]
    os.environ[config.api_key_env] = api_key

    llm = create_llm(
        model_name=model_name,
        api_key=api_key,
        temperature=0.7,
    )
    st.session_state.workflow = create_thesis_workflow(llm)

def get_api_help(provider: str) -> str:
    help_map = {
        "openai": """
**OpenAI API Key 获取：**
1. 访问 [OpenAI Platform](https://platform.openai.com)
2. 注册账号并创建 API Key
3. 复制 API Key 并粘贴
""",
        "anthropic": """
**Anthropic API Key 获取：**
1. 访问 [Anthropic Console](https://console.anthropic.com)
2. 注册账号并创建 API Key
3. 复制 API Key 并粘贴
""",
        "deepseek": """
**DeepSeek API Key 获取：**
1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com)
2. 注册账号并创建 API Key
3. 复制 API Key 并粘贴
""",
        "qwen": """
**通义千问 API Key 获取：**
1. 访问 [DashScope](https://dashscope.console.aliyun.com)
2. 注册阿里云账号并开通 DashScope
3. 创建 API Key 并粘贴
""",
        "kimi": """
**Kimi API Key 获取：**
1. 访问 [Moonshot 开放平台](https://platform.moonshot.cn)
2. 注册账号并创建 API Key
3. 复制 API Key 并粘贴
""",
        "glm": """
**智谱 API Key 获取：**
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn)
2. 注册账号并创建 API Key
3. 复制 API Key 并粘贴
""",
        "baichuan": """
**百川 API Key 获取：**
1. 访问 [百川智能](https://platform.baichuan-ai.com)
2. 注册账号并创建 API Key
3. 复制 API Key 并粘贴
""",
        "minimax": """
**MiniMax API Key 获取：**
1. 访问 [MiniMax开放平台](https://platform.minimax.chat)
2. 注册账号并申请 API Key
3. 复制 API Key 并粘贴
""",
    }
    return help_map.get(provider, "请参考对应提供商文档获取 API Key")


with st.sidebar:
    st.header("设置")

    # 按提供商分组选择
    selected_provider = st.selectbox("选择提供商", get_providers(), index=0)

    provider_models = get_models_by_provider(selected_provider)
    model_names = list(provider_models.keys())
    recommended = [n for n in model_names if provider_models[n].is_recommended]

    if recommended:
        selected_model = st.selectbox("选择模型", model_names, index=model_names.index(recommended[0]))
    else:
        selected_model = st.selectbox("选择模型", model_names, index=0)

    config = MODEL_REGISTRY[selected_model]

    api_key_label = f"{config.name} API Key"
    env_value = os.getenv(config.api_key_env, "")
    api_key = st.text_input(api_key_label, value=env_value, type="password")

    # 模型信息
    with st.expander("模型说明", expanded=False):
        st.markdown(f"**提供商:** {config.provider.upper()}")
        st.markdown(f"**上下文窗口:** {config.context_window:,} tokens")
        st.markdown(f"**最大输出:** {config.max_tokens:,} tokens")
        if config.price_info:
            st.markdown(f"**价格:** {config.price_info}")
        if config.description:
            st.markdown(f"**说明:** {config.description}")
        st.divider()
        st.markdown(get_api_help(config.provider))

    st.divider()
    st.markdown("**使用说明**\n1. 选择提供商和模型\n2. 输入 API Key\n3. 输入论文主题\n4. 点击生成按钮")

topic = st.text_input("📝 请输入论文主题", placeholder="例如：基于深度学习的图像去雾算法研究")

col1, col2 = st.columns([1, 4])
with col1:
    generate_btn = st.button("🚀 开始生成", type="primary", use_container_width=True)

if generate_btn and topic:
    if not api_key:
        st.error(f"请先输入 {config.name} API Key")
    else:
        with st.spinner("初始化模型..."):
            try:
                init_workflow(selected_model, api_key)
            except Exception as e:
                import traceback
                st.error(f"初始化失败: {str(e)}")
                st.code(traceback.format_exc())

        if st.session_state.workflow:
            with st.spinner("论文生成中，请稍候..."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    status_text.text("阶段 1/3: 研究文献...")
                    progress_bar.progress(33)

                    result = st.session_state.workflow.invoke({
                        "messages": [HumanMessage(content=topic)],
                        "current_task": "research",
                        "research_results": "",
                        "code_results": "",
                        "thesis_content": "",
                        "feedback": ""
                    })

                    progress_bar.progress(66)
                    status_text.text("阶段 2/3: 编写代码...")
                    time.sleep(0.5)

                    progress_bar.progress(100)
                    status_text.text("完成!")
                    time.sleep(0.3)
                    status_text.text("生成完成！")

                    st.session_state.result = result
                    st.session_state.topic = topic

                except Exception as e:
                    st.error(f"生成失败: {str(e)}")

if st.session_state.result:
    result = st.session_state.result
    thesis = result.get("thesis_content", "")

    st.success("✅ 论文生成完成！")

    tab1, tab2, tab3 = st.tabs(["📄 论文内容", "💻 代码结果", "📊 研究资料"])

    with tab1:
        if thesis:
            st.markdown(thesis)
        else:
            st.info("论文内容为空")

        col_down1, col_down2 = st.columns(2)
        with col_down1:
            st.download_button(
                "📥 下载为 Markdown",
                data=thesis or "",
                file_name=f"thesis_{int(time.time())}.md",
                mime="text/markdown"
            )

    with tab2:
        code_result = result.get("code_results", "")
        if code_result:
            st.text(code_result)
        else:
            st.info("无代码执行结果")

    with tab3:
        research_result = result.get("research_results", "")
        if research_result:
            st.text(research_result)
        else:
            st.info("无研究资料")
