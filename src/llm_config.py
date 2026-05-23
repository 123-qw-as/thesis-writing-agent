"""
LLM Provider Configuration - 多模型支持配置

支持的提供商:
- OpenAI (GPT-5.5, GPT-5.4, GPT-5.4-mini, GPT-Image-2, GPT-Realtime-2)
- Anthropic (Claude Opus 4.7, Sonnet 4.6, Haiku 4.5)
- DeepSeek (V4-Pro, V4-Flash)
- Qwen 通义千问 (Qwen3.6-Max-Preview, Qwen3.6-Plus, Qwen3.6-Flash)
- Kimi 月之暗面 (Kimi K2.6, Kimi K2, moonshot-v1)
- GLM 智谱 (GLM-5.1, GLM-5, GLM-5-Turbo, GLM-4.7)
- Baichuan 百川 (Baichuan4-Turbo, Baichuan4-Air, Baichuan4)
- MiniMax (MiniMax-M2.7, MiniMax-M2.7-highspeed, MiniMax-M2.5)

用法:
    from src.llm_config import create_llm, MODEL_REGISTRY, get_models_by_provider

    # 创建LLM实例
    llm = create_llm("gpt-4o", api_key="sk-xxx")

    # 获取所有模型列表
    models = list(MODEL_REGISTRY.keys())

    # 按提供商筛选
    openai_models = get_models_by_provider("openai")
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """单个模型的配置信息"""
    name: str
    model_id: str
    provider: str
    api_key_env: str
    base_url: Optional[str] = None
    max_tokens: int = 4096
    context_window: int = 8192
    description: str = ""
    price_info: str = ""
    is_recommended: bool = False
    default_api_base: Optional[str] = None


# ──────────────────────────────────────────────
# 模型注册表
# ──────────────────────────────────────────────

MODEL_REGISTRY: Dict[str, ModelConfig] = {
    # ═══════════════════════════════════════════
    # OpenAI (来源: openai.com/api/pricing/)
    # ═══════════════════════════════════════════
    "gpt-5.5": ModelConfig(
        name="GPT-5.5",
        model_id="gpt-5.5",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        max_tokens=32_768,
        context_window=1_048_576,
        description="OpenAI 2026年4月旗舰模型，编程/知识工作/研究全面升级，效率优于GPT-5.4",
        price_info="输入 $5.00/M, 输出 $30.00/M",
        is_recommended=True,
    ),
    "gpt-5.4": ModelConfig(
        name="GPT-5.4",
        model_id="gpt-5.4",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        max_tokens=32_768,
        context_window=1_048_576,
        description="编程与专业工作高性价比模型",
        price_info="输入 $2.50/M, 输出 $15.00/M",
    ),
    "gpt-5.4-mini": ModelConfig(
        name="GPT-5.4 Mini",
        model_id="gpt-5.4-mini",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        max_tokens=16_384,
        context_window=200_000,
        description="最强Mini模型，编程/Computer Use/Subagent优化",
        price_info="输入 $0.75/M, 输出 $4.50/M",
        is_recommended=True,
    ),
    "gpt-4o": ModelConfig(
        name="GPT-4o",
        model_id="gpt-4o",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        max_tokens=4096,
        context_window=128_000,
        description="OpenAI多模态模型，支持图像/音频/文本",
        price_info="输入 $2.50/M, 输出 $10/M",
    ),
    "gpt-4o-mini": ModelConfig(
        name="GPT-4o Mini",
        model_id="gpt-4o-mini",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        max_tokens=4096,
        context_window=128_000,
        description="GPT-4o轻量版，性价比高",
        price_info="输入 $0.15/M, 输出 $0.60/M",
    ),
    "o1": ModelConfig(
        name="o1",
        model_id="o1",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        max_tokens=8192,
        context_window=200_000,
        description="OpenAI推理模型，适合复杂逻辑和数学推理",
        price_info="输入 $15/M, 输出 $60/M",
    ),

    # ═══════════════════════════════════════════
    # Anthropic Claude (来源: anthropic.com)
    # ═══════════════════════════════════════════
    "claude-opus-4-7": ModelConfig(
        name="Claude Opus 4.7",
        model_id="claude-opus-4-7",
        provider="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        max_tokens=8192,
        context_window=1_000_000,
        description="Anthropic 2026年4月旗舰，Agentic Coding/复杂推理/视觉全面升级，1M上下文",
        price_info="输入 $5/M, 输出 $25/M",
        is_recommended=True,
    ),
    "claude-sonnet-4-6": ModelConfig(
        name="Claude Sonnet 4.6",
        model_id="claude-sonnet-4-6",
        provider="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        max_tokens=8192,
        context_window=1_000_000,
        description="生产环境首选，编程/Agent/长上下文全面优化，性价比之王",
        price_info="输入 $3/M, 输出 $15/M",
        is_recommended=True,
    ),
    "claude-haiku-4-5": ModelConfig(
        name="Claude Haiku 4.5",
        model_id="claude-haiku-4-5",
        provider="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        max_tokens=4096,
        context_window=200_000,
        description="最快最便宜的Claude，编码接近Sonnet 4，速度极快",
        price_info="输入 $1/M, 输出 $5/M",
    ),

    # ═══════════════════════════════════════════
    # DeepSeek (来源: platform.deepseek.com)
    # ═══════════════════════════════════════════
    "deepseek-v4-pro": ModelConfig(
        name="DeepSeek V4 Pro",
        model_id="deepseek-v4-pro",
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com",
        max_tokens=8192,
        context_window=128_000,
        description="DeepSeek最新Pro模型，支持思考模式，适合复杂任务",
        price_info="按量计费",
        is_recommended=True,
    ),
    "deepseek-v4-flash": ModelConfig(
        name="DeepSeek V4 Flash",
        model_id="deepseek-v4-flash",
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com",
        max_tokens=8192,
        context_window=128_000,
        description="DeepSeek最新Flash模型，速度快，性价比高",
        price_info="按量计费",
    ),
    "deepseek-chat": ModelConfig(
        name="DeepSeek Chat (V3)",
        model_id="deepseek-chat",
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com",
        max_tokens=8192,
        context_window=64_000,
        description="DeepSeek V3非思考模式，2026/07/24将弃用，建议迁移至V4-Flash",
        price_info="输入 ¥1/M, 输出 ¥5/M",
    ),
    "deepseek-reasoner": ModelConfig(
        name="DeepSeek Reasoner (R1)",
        model_id="deepseek-reasoner",
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com",
        max_tokens=8192,
        context_window=64_000,
        description="DeepSeek R1思考模式，2026/07/24将弃用，建议迁移至V4-Pro",
        price_info="输入 ¥4/M, 输出 ¥16/M",
    ),

    # ═══════════════════════════════════════════
    # Qwen 通义千问 (来源: help.aliyun.com/zh/model-studio/models)
    # ═══════════════════════════════════════════
    "qwen3.6-max-preview": ModelConfig(
        name="Qwen3.6-Max-Preview",
        model_id="qwen3.6-max-preview",
        provider="qwen",
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        max_tokens=8192,
        context_window=262_144,
        description="通义千问最新最强模型，预览版",
        price_info="输入 ¥40/M, 输出 ¥120/M",
        is_recommended=True,
    ),
    "qwen3.6-plus": ModelConfig(
        name="Qwen3.6-Plus",
        model_id="qwen3.6-plus",
        provider="qwen",
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        max_tokens=8192,
        context_window=131_072,
        description="通义千问3.6平衡版，性价比极高",
        price_info="输入 ¥4/M, 输出 ¥12/M",
        is_recommended=True,
    ),
    "qwen3.6-flash": ModelConfig(
        name="Qwen3.6-Flash",
        model_id="qwen3.6-flash",
        provider="qwen",
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        max_tokens=8192,
        context_window=131_072,
        description="通义千问3.6轻量版，速度快，成本低",
        price_info="输入 ¥0.3/M, 输出 ¥1.2/M",
    ),
    "qwen3-max": ModelConfig(
        name="Qwen3-Max",
        model_id="qwen3-max",
        provider="qwen",
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        max_tokens=8192,
        context_window=262_144,
        description="通义千问3代最强，1T+参数",
        price_info="输入 ¥40/M, 输出 ¥120/M",
    ),
    "qwen-plus": ModelConfig(
        name="Qwen Plus",
        model_id="qwen-plus",
        provider="qwen",
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        max_tokens=8192,
        context_window=131_072,
        description="通义千问平衡版，性价比高",
        price_info="输入 ¥4/M, 输出 ¥12/M",
    ),
    "qwen-turbo": ModelConfig(
        name="Qwen Turbo",
        model_id="qwen-turbo",
        provider="qwen",
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        max_tokens=8192,
        context_window=131_072,
        description="通义千问轻量版，速度快，成本极低",
        price_info="输入 ¥0.3/M, 输出 ¥1.2/M",
    ),

    # ═══════════════════════════════════════════
    # Kimi 月之暗面 (来源: platform.moonshot.cn)
    # ═══════════════════════════════════════════
    "kimi-k2.6": ModelConfig(
        name="Kimi K2.6",
        model_id="kimi-k2.6",
        provider="kimi",
        api_key_env="KIMI_API_KEY",
        base_url="https://api.moonshot.cn/v1",
        max_tokens=8192,
        context_window=262_144,
        description="Kimi最新最智能模型，多模态(文本/图片/视频输入)，支持长思考，256K上下文",
        price_info="输入(缓存命中) ¥1.10/M, 输入(缓存未命中) ¥6.50/M, 输出 ¥27/M",
        is_recommended=True,
    ),
    "kimi-k2": ModelConfig(
        name="Kimi K2",
        model_id="kimi-k2",
        provider="kimi",
        api_key_env="KIMI_API_KEY",
        base_url="https://api.moonshot.cn/v1",
        max_tokens=8192,
        context_window=131_072,
        description="超强代码和Agent能力的MoE模型",
        price_info="按量计费",
    ),
    "moonshot-v1-8k": ModelConfig(
        name="Kimi 8K",
        model_id="moonshot-v1-8k",
        provider="kimi",
        api_key_env="KIMI_API_KEY",
        base_url="https://api.moonshot.cn/v1",
        max_tokens=4096,
        context_window=8_192,
        description="Kimi经典生成模型",
        price_info="输入 ¥12/M, 输出 ¥12/M",
    ),
    "moonshot-v1-32k": ModelConfig(
        name="Kimi 32K",
        model_id="moonshot-v1-32k",
        provider="kimi",
        api_key_env="KIMI_API_KEY",
        base_url="https://api.moonshot.cn/v1",
        max_tokens=8192,
        context_window=32_768,
        description="Kimi标准版",
        price_info="输入 ¥24/M, 输出 ¥24/M",
    ),
    "moonshot-v1-128k": ModelConfig(
        name="Kimi 128K",
        model_id="moonshot-v1-128k",
        provider="kimi",
        api_key_env="KIMI_API_KEY",
        base_url="https://api.moonshot.cn/v1",
        max_tokens=8192,
        context_window=131_072,
        description="Kimi超长上下文版",
        price_info="输入 ¥60/M, 输出 ¥60/M",
    ),

    # ═══════════════════════════════════════════
    # GLM 智谱 (来源: docs.bigmodel.cn)
    # ═══════════════════════════════════════════
    "glm-5.1": ModelConfig(
        name="GLM-5.1",
        model_id="glm-5.1",
        provider="glm",
        api_key_env="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        max_tokens=8192,
        context_window=200_000,
        description="智谱最新旗舰模型，开源SOTA，Coding对齐Claude Opus 4.6，长程任务可自主工作8小时",
        price_info="按量计费",
        is_recommended=True,
    ),
    "glm-5": ModelConfig(
        name="GLM-5",
        model_id="glm-5",
        provider="glm",
        api_key_env="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        max_tokens=8192,
        context_window=200_000,
        description="编程对齐Claude Opus 4.5，擅长Agentic长程规划与执行",
        price_info="按量计费",
    ),
    "glm-5-turbo": ModelConfig(
        name="GLM-5-Turbo",
        model_id="glm-5-turbo",
        provider="glm",
        api_key_env="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        max_tokens=8192,
        context_window=200_000,
        description="复杂长任务执行连续性好",
        price_info="按量计费",
    ),
    "glm-4.7": ModelConfig(
        name="GLM-4.7",
        model_id="glm-4.7",
        provider="glm",
        api_key_env="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        max_tokens=8192,
        context_window=200_000,
        description="通用对话/推理/智能体全面升级，编程更强更稳",
        price_info="按量计费",
    ),
    "glm-4.7-flash": ModelConfig(
        name="GLM-4.7-Flash",
        model_id="glm-4.7-flash",
        provider="glm",
        api_key_env="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        max_tokens=4096,
        context_window=200_000,
        description="最新基座模型的普惠免费版本",
        price_info="免费",
    ),
    "glm-4-flash": ModelConfig(
        name="GLM-4-Flash",
        model_id="glm-4-flash",
        provider="glm",
        api_key_env="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        max_tokens=4096,
        context_window=128_000,
        description="智谱轻量版，速度快，成本低",
        price_info="免费",
    ),

    # ═══════════════════════════════════════════
    # Baichuan 百川 (来源: baichuan-ai.com)
    # ═══════════════════════════════════════════
    "baichuan4-turbo": ModelConfig(
        name="Baichuan4-Turbo",
        model_id="Baichuan4-Turbo",
        provider="baichuan",
        api_key_env="BAICHUAN_API_KEY",
        base_url="https://api.baichuan-ai.com/v1",
        max_tokens=4096,
        context_window=32_768,
        description="针对企业高频场景优化，可用性较Baichuan4提升10%+，价格仅为GPT-4o的80%",
        price_info="按量计费",
        is_recommended=True,
    ),
    "baichuan4-air": ModelConfig(
        name="Baichuan4-Air",
        model_id="Baichuan4-Air",
        provider="baichuan",
        api_key_env="BAICHUAN_API_KEY",
        base_url="https://api.baichuan-ai.com/v1",
        max_tokens=4096,
        context_window=32_768,
        description="百川首创MoE架构，大幅降低推理成本，单价仅0.98厘/千token",
        price_info="输入 ¥0.98/千tokens",
    ),
    "baichuan4": ModelConfig(
        name="Baichuan 4",
        model_id="Baichuan4",
        provider="baichuan",
        api_key_env="BAICHUAN_API_KEY",
        base_url="https://api.baichuan-ai.com/v1",
        max_tokens=4096,
        context_window=32_768,
        description="SuperCLUE评测国内第一，具备多模态能力和Search Agent",
        price_info="输入 ¥10/M, 输出 ¥10/M",
    ),

    # ═══════════════════════════════════════════
    # MiniMax (来源: platform.minimaxi.com)
    # ═══════════════════════════════════════════
    "minimax-m2.7": ModelConfig(
        name="MiniMax M2.7",
        model_id="MiniMax-M2.7",
        provider="minimax",
        api_key_env="MINIMAX_API_KEY",
        base_url="https://api.minimaxi.com/v1",
        max_tokens=8192,
        context_window=205_000,
        description="MiniMax最新旗舰文本模型，开启模型自我迭代",
        price_info="按量计费",
        is_recommended=True,
    ),
    "minimax-m2.7-highspeed": ModelConfig(
        name="MiniMax M2.7 Highspeed",
        model_id="MiniMax-M2.7-highspeed",
        provider="minimax",
        api_key_env="MINIMAX_API_KEY",
        base_url="https://api.minimaxi.com/v1",
        max_tokens=8192,
        context_window=205_000,
        description="与M2.7效果不变，速度大幅提升",
        price_info="按量计费",
    ),
    "minimax-m2.5": ModelConfig(
        name="MiniMax M2.5",
        model_id="MiniMax-M2.5",
        provider="minimax",
        api_key_env="MINIMAX_API_KEY",
        base_url="https://api.minimaxi.com/v1",
        max_tokens=8192,
        context_window=205_000,
        description="顶尖性能与极致性价比，轻松驾驭复杂任务",
        price_info="按量计费",
    ),
    "minimax-m2.5-highspeed": ModelConfig(
        name="MiniMax M2.5 Highspeed",
        model_id="MiniMax-M2.5-highspeed",
        provider="minimax",
        api_key_env="MINIMAX_API_KEY",
        base_url="https://api.minimaxi.com/v1",
        max_tokens=8192,
        context_window=205_000,
        description="与M2.5效果不变，速度大幅提升",
        price_info="按量计费",
    ),
    "minimax-m2-her": ModelConfig(
        name="MiniMax M2-Her",
        model_id="M2-her",
        provider="minimax",
        api_key_env="MINIMAX_API_KEY",
        base_url="https://api.minimaxi.com/v1",
        max_tokens=4096,
        context_window=32_768,
        description="文本对话模型，专为角色扮演、多轮对话等场景设计",
        price_info="按量计费",
    ),
}


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────

def get_models_by_provider(provider: str) -> Dict[str, ModelConfig]:
    """按提供商筛选模型"""
    return {k: v for k, v in MODEL_REGISTRY.items() if v.provider == provider}


def get_recommended_models() -> Dict[str, ModelConfig]:
    """获取推荐的模型"""
    return {k: v for k, v in MODEL_REGISTRY.items() if v.is_recommended}


def get_providers() -> List[str]:
    """获取所有支持的提供商列表"""
    return sorted(set(m.provider for m in MODEL_REGISTRY.values()))


def get_model_info(model_name: str) -> Optional[ModelConfig]:
    """获取模型配置信息"""
    return MODEL_REGISTRY.get(model_name)


# ──────────────────────────────────────────────
# LLM 工厂函数
# ──────────────────────────────────────────────

def create_llm(
    model_name: str,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
):
    """
    工厂函数：根据模型名称创建LLM实例

    Args:
        model_name: 模型名称（必须是 MODEL_REGISTRY 中的键）
        api_key: API Key（可选，不传则从环境变量读取）
        temperature: 温度参数 (0-1)
        max_tokens: 最大输出token数
        **kwargs: 其他参数传递给底层LLM

    Returns:
        LangChain ChatModel 实例

    Raises:
        ValueError: 模型不存在或缺少API Key
    """
    config = MODEL_REGISTRY.get(model_name)
    if not config:
        available = ', '.join(MODEL_REGISTRY.keys())
        raise ValueError(f"Unknown model '{model_name}'. Available: {available}")

    key = api_key or os.getenv(config.api_key_env, "")
    if not key:
        raise ValueError(
            f"No API key for {config.name}. "
            f"Set environment variable {config.api_key_env} or pass api_key parameter."
        )

    effective_max_tokens = max_tokens or config.max_tokens
    base_url = config.base_url or config.default_api_base

    provider = config.provider

    # ── OpenAI 兼容接口 (OpenAI, DeepSeek, Qwen, Kimi, GLM, Baichuan, MiniMax OpenAI) ──
    if provider in ("openai", "deepseek", "qwen", "kimi", "glm", "baichuan"):
        from langchain_openai import ChatOpenAI
        
        # DeepSeek 需要禁用 thinking 模式，否则多轮对话会报 reasoning_content 错误
        extra_body = {"thinking": {"type": "disabled"}} if provider == "deepseek" else {}
        
        return ChatOpenAI(
            model=config.model_id,
            temperature=temperature,
            api_key=key,
            base_url=base_url,
            max_tokens=effective_max_tokens,
            extra_body=extra_body,
            **kwargs
        )

    # ── Anthropic Claude ──
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=config.model_id,
            temperature=temperature,
            api_key=key,
            base_url=base_url,
            max_tokens=effective_max_tokens,
            **kwargs
        )

    # ── MiniMax (OpenAI 兼容) ──
    elif provider == "minimax":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.model_id,
            temperature=temperature,
            api_key=key,
            base_url=base_url,
            max_tokens=effective_max_tokens,
            **kwargs
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}")


# ──────────────────────────────────────────────
# 快捷函数：自动选择可用模型
# ──────────────────────────────────────────────

def auto_select_llm(
    temperature: float = 0.7,
    preferred_providers: Optional[List[str]] = None,
    **kwargs
):
    """
    自动选择可用的模型（按优先级尝试）

    Args:
        temperature: 温度参数
        preferred_providers: 优先尝试的提供商列表
        **kwargs: 传递给 create_llm 的参数

    Returns:
        (model_name, llm_instance) 或 (None, None)
    """
    if preferred_providers is None:
        preferred_providers = ["deepseek", "qwen", "glm", "openai", "anthropic", "minimax", "kimi", "baichuan"]

    for provider in preferred_providers:
        models = get_models_by_provider(provider)
        for name, config in models.items():
            api_key = os.getenv(config.api_key_env, "")
            if api_key:
                try:
                    llm = create_llm(name, temperature=temperature, **kwargs)
                    return name, llm
                except Exception:
                    continue

    return None, None
