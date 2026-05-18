"""
LLM Provider Configuration - 多模型支持配置

支持的提供商:
- OpenAI (GPT-4o, GPT-4o-mini, o1, o3-mini)
- DeepSeek (deepseek-chat, deepseek-reasoner)
- Claude (Sonnet 4, Opus 4, Haiku 3.5)
- Qwen 通义千问 (qwen-max, qwen-plus, qwen-turbo)
- Kimi 月之暗面 (moonshot-v1-8k/32k/128k)
- GLM 智谱 (glm-4, glm-4-plus, glm-4-flash)
- Baichuan 百川 (baichuan4)
- MiniMax (MiniMax-M2.7, abab6.5s-chat)

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
    # OpenAI
    # ═══════════════════════════════════════════
    "gpt-4o": ModelConfig(
        name="GPT-4o",
        model_id="gpt-4o",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        max_tokens=4096,
        context_window=128_000,
        description="OpenAI最新旗舰模型，支持多模态，综合能力最强",
        price_info="输入 $2.50/M, 输出 $10/M",
        is_recommended=True,
    ),
    "gpt-4o-mini": ModelConfig(
        name="GPT-4o Mini",
        model_id="gpt-4o-mini",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        max_tokens=4096,
        context_window=128_000,
        description="GPT-4o的轻量版，性价比高，适合日常任务",
        price_info="输入 $0.15/M, 输出 $0.60/M",
    ),
    "gpt-4-turbo": ModelConfig(
        name="GPT-4 Turbo",
        model_id="gpt-4-turbo",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        max_tokens=4096,
        context_window=128_000,
        description="GPT-4的升级版，速度更快",
        price_info="输入 $10/M, 输出 $30/M",
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
    "o3-mini": ModelConfig(
        name="o3-mini",
        model_id="o3-mini",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        max_tokens=8192,
        context_window=200_000,
        description="OpenAI轻量级推理模型，性价比高",
        price_info="输入 $1.10/M, 输出 $4.40/M",
    ),

    # ═══════════════════════════════════════════
    # Anthropic Claude
    # ═══════════════════════════════════════════
    "claude-sonnet-4-20250514": ModelConfig(
        name="Claude Sonnet 4",
        model_id="claude-sonnet-4-20250514",
        provider="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        max_tokens=8192,
        context_window=200_000,
        description="Claude最新Sonnet模型，平衡性能与速度",
        price_info="输入 $3/M, 输出 $15/M",
        is_recommended=True,
    ),
    "claude-opus-4-20250414": ModelConfig(
        name="Claude Opus 4",
        model_id="claude-opus-4-20250414",
        provider="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        max_tokens=8192,
        context_window=200_000,
        description="Claude最强模型，适合复杂推理和长文档",
        price_info="输入 $15/M, 输出 $75/M",
    ),
    "claude-3-5-haiku-20241022": ModelConfig(
        name="Claude Haiku 3.5",
        model_id="claude-3-5-haiku-20241022",
        provider="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        max_tokens=4096,
        context_window=200_000,
        description="Claude轻量模型，速度快，成本低",
        price_info="输入 $0.80/M, 输出 $4/M",
    ),

    # ═══════════════════════════════════════════
    # DeepSeek
    # ═══════════════════════════════════════════
    "deepseek-chat": ModelConfig(
        name="DeepSeek V3",
        model_id="deepseek-chat",
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com/v1",
        max_tokens=8192,
        context_window=64_000,
        description="DeepSeek最新V3模型，中文能力强，性价比高",
        price_info="输入 ¥1/M, 输出 ¥5/M",
        is_recommended=True,
    ),
    "deepseek-reasoner": ModelConfig(
        name="DeepSeek R1",
        model_id="deepseek-reasoner",
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com/v1",
        max_tokens=8192,
        context_window=64_000,
        description="DeepSeek推理模型，适合复杂逻辑推理",
        price_info="输入 ¥4/M, 输出 ¥16/M",
    ),

    # ═══════════════════════════════════════════
    # Qwen 通义千问
    # ═══════════════════════════════════════════
    "qwen-max": ModelConfig(
        name="Qwen Max",
        model_id="qwen-max",
        provider="qwen",
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        max_tokens=8192,
        context_window=32_768,
        description="通义千问最强模型，中文能力优秀",
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
        is_recommended=True,
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
    # Kimi 月之暗面
    # ═══════════════════════════════════════════
    "moonshot-v1-8k": ModelConfig(
        name="Kimi 8K",
        model_id="moonshot-v1-8k",
        provider="kimi",
        api_key_env="KIMI_API_KEY",
        base_url="https://api.moonshot.cn/v1",
        max_tokens=4096,
        context_window=8_192,
        description="Kimi基础模型，适合短文本任务",
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
        description="Kimi标准版，支持较长上下文",
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
        description="Kimi超长上下文版，适合长文档分析",
        price_info="输入 ¥60/M, 输出 ¥60/M",
    ),

    # ═══════════════════════════════════════════
    # GLM 智谱
    # ═══════════════════════════════════════════
    "glm-4": ModelConfig(
        name="GLM-4",
        model_id="glm-4",
        provider="glm",
        api_key_env="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        max_tokens=4096,
        context_window=128_000,
        description="智谱最强模型，中文能力优秀",
        price_info="输入 ¥50/M, 输出 ¥50/M",
    ),
    "glm-4-plus": ModelConfig(
        name="GLM-4 Plus",
        model_id="glm-4-plus",
        provider="glm",
        api_key_env="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        max_tokens=4096,
        context_window=128_000,
        description="智谱增强版，平衡性能与成本",
        price_info="输入 ¥50/M, 输出 ¥50/M",
    ),
    "glm-4-flash": ModelConfig(
        name="GLM-4 Flash",
        model_id="glm-4-flash",
        provider="glm",
        api_key_env="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        max_tokens=4096,
        context_window=128_000,
        description="智谱轻量版，速度快，成本低",
        price_info="输入 ¥0/M, 输出 ¥0/M (免费)",
        is_recommended=True,
    ),

    # ═══════════════════════════════════════════
    # Baichuan 百川
    # ═══════════════════════════════════════════
    "baichuan4": ModelConfig(
        name="Baichuan 4",
        model_id="Baichuan4",
        provider="baichuan",
        api_key_env="BAICHUAN_API_KEY",
        base_url="https://api.baichuan-ai.com/v1",
        max_tokens=4096,
        context_window=32_768,
        description="百川最新模型，中文能力强",
        price_info="输入 ¥10/M, 输出 ¥10/M",
    ),

    # ═══════════════════════════════════════════
    # MiniMax
    # ═══════════════════════════════════════════
    "minimax-m2.7": ModelConfig(
        name="MiniMax M2.7",
        model_id="MiniMax-M2.7",
        provider="minimax",
        api_key_env="MINIMAX_API_KEY",
        base_url="https://api.minimaxi.com/anthropic",
        max_tokens=4096,
        context_window=8_192,
        description="MiniMax最新模型，中文能力优秀",
        price_info="按量计费",
        is_recommended=True,
    ),
    "minimax-abab6.5s": ModelConfig(
        name="MiniMax abab6.5s",
        model_id="abab6.5s-chat",
        provider="minimax",
        api_key_env="MINIMAX_API_KEY",
        base_url="https://api.minimax.chat/v1",
        max_tokens=4096,
        context_window=8_192,
        description="MiniMax标准版，稳定可靠",
        price_info="按量计费",
    ),
    "minimax-abab6.5g": ModelConfig(
        name="MiniMax abab6.5g",
        model_id="abab6.5g-chat",
        provider="minimax",
        api_key_env="MINIMAX_API_KEY",
        base_url="https://api.minimax.chat/v1",
        max_tokens=4096,
        context_window=8_192,
        description="MiniMax MoE架构，适合复杂任务",
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
        return ChatOpenAI(
            model=config.model_id,
            temperature=temperature,
            api_key=key,
            base_url=base_url,
            max_tokens=effective_max_tokens,
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

    # ── MiniMax (Anthropic 兼容) ──
    elif provider == "minimax":
        if "anthropic" in (base_url or ""):
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=config.model_id,
                temperature=temperature,
                api_key=key,
                base_url=base_url,
                max_tokens=effective_max_tokens,
                **kwargs
            )
        else:
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
