"""
Unit tests for llm_config.py - LLM Provider Configuration
"""
import pytest
import os
from src.llm_config import (
    MODEL_REGISTRY, ModelConfig, create_llm, auto_select_llm,
    get_models_by_provider, get_recommended_models, get_providers,
    get_model_info,
)


class TestModelRegistry:
    def test_not_empty(self):
        assert len(MODEL_REGISTRY) > 0

    def test_has_openai_models(self):
        openai = get_models_by_provider("openai")
        assert "gpt-4o" in openai
        assert "gpt-4o-mini" in openai

    def test_has_deepseek_models(self):
        deepseek = get_models_by_provider("deepseek")
        assert "deepseek-chat" in deepseek
        assert "deepseek-reasoner" in deepseek

    def test_has_claude_models(self):
        anthropic = get_models_by_provider("anthropic")
        assert "claude-sonnet-4-20250514" in anthropic

    def test_has_qwen_models(self):
        qwen = get_models_by_provider("qwen")
        assert "qwen-max" in qwen
        assert "qwen-plus" in qwen
        assert "qwen-turbo" in qwen

    def test_has_kimi_models(self):
        kimi = get_models_by_provider("kimi")
        assert "moonshot-v1-8k" in kimi
        assert "moonshot-v1-32k" in kimi
        assert "moonshot-v1-128k" in kimi

    def test_has_glm_models(self):
        glm = get_models_by_provider("glm")
        assert "glm-4" in glm
        assert "glm-4-plus" in glm
        assert "glm-4-flash" in glm

    def test_has_baichuan_models(self):
        baichuan = get_models_by_provider("baichuan")
        assert "baichuan4" in baichuan

    def test_has_minimax_models(self):
        minimax = get_models_by_provider("minimax")
        assert "minimax-m2.7" in minimax
        assert "minimax-abab6.5s" in minimax

    def test_all_configs_have_required_fields(self):
        for name, config in MODEL_REGISTRY.items():
            assert config.name, f"{name} missing name"
            assert config.model_id, f"{name} missing model_id"
            assert config.provider, f"{name} missing provider"
            assert config.api_key_env, f"{name} missing api_key_env"
            assert config.context_window > 0, f"{name} invalid context_window"

    def test_has_recommended_models(self):
        recommended = get_recommended_models()
        assert len(recommended) > 0
        for name in recommended:
            assert MODEL_REGISTRY[name].is_recommended

    def test_get_providers(self):
        providers = get_providers()
        assert "openai" in providers
        assert "deepseek" in providers
        assert "anthropic" in providers
        assert "qwen" in providers
        assert "kimi" in providers
        assert "glm" in providers
        assert "minimax" in providers


class TestGetModelInfo:
    def test_existing_model(self):
        info = get_model_info("gpt-4o")
        assert info is not None
        assert info.model_id == "gpt-4o"
        assert info.provider == "openai"

    def test_nonexistent_model(self):
        info = get_model_info("nonexistent-model")
        assert info is None


class TestCreateLLM:
    def test_unknown_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            create_llm("nonexistent-model")

    def test_missing_api_key_raises(self):
        old_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = ""
        try:
            with pytest.raises(ValueError, match="No API key"):
                create_llm("gpt-4o")
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key

    def test_create_openai_model(self):
        old_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "test-key"
        try:
            llm = create_llm("gpt-4o", temperature=0.5)
            assert llm is not None
            assert llm.model_name == "gpt-4o"
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key
            else:
                os.environ.pop("OPENAI_API_KEY", None)

    def test_create_deepseek_model(self):
        old_key = os.environ.get("DEEPSEEK_API_KEY")
        os.environ["DEEPSEEK_API_KEY"] = "test-key"
        try:
            llm = create_llm("deepseek-chat", temperature=0.5)
            assert llm is not None
            assert llm.model_name == "deepseek-chat"
        finally:
            if old_key:
                os.environ["DEEPSEEK_API_KEY"] = old_key
            else:
                os.environ.pop("DEEPSEEK_API_KEY", None)

    def test_create_qwen_model(self):
        old_key = os.environ.get("DASHSCOPE_API_KEY")
        os.environ["DASHSCOPE_API_KEY"] = "test-key"
        try:
            llm = create_llm("qwen-plus", temperature=0.5)
            assert llm is not None
            assert llm.model_name == "qwen-plus"
        finally:
            if old_key:
                os.environ["DASHSCOPE_API_KEY"] = old_key
            else:
                os.environ.pop("DASHSCOPE_API_KEY", None)

    def test_create_kimi_model(self):
        old_key = os.environ.get("KIMI_API_KEY")
        os.environ["KIMI_API_KEY"] = "test-key"
        try:
            llm = create_llm("moonshot-v1-32k", temperature=0.5)
            assert llm is not None
            assert llm.model_name == "moonshot-v1-32k"
        finally:
            if old_key:
                os.environ["KIMI_API_KEY"] = old_key
            else:
                os.environ.pop("KIMI_API_KEY", None)

    def test_create_glm_model(self):
        old_key = os.environ.get("ZHIPU_API_KEY")
        os.environ["ZHIPU_API_KEY"] = "test-key"
        try:
            llm = create_llm("glm-4-flash", temperature=0.5)
            assert llm is not None
            assert llm.model_name == "glm-4-flash"
        finally:
            if old_key:
                os.environ["ZHIPU_API_KEY"] = old_key
            else:
                os.environ.pop("ZHIPU_API_KEY", None)

    def test_create_baichuan_model(self):
        old_key = os.environ.get("BAICHUAN_API_KEY")
        os.environ["BAICHUAN_API_KEY"] = "test-key"
        try:
            llm = create_llm("baichuan4", temperature=0.5)
            assert llm is not None
            assert llm.model_name == "Baichuan4"
        finally:
            if old_key:
                os.environ["BAICHUAN_API_KEY"] = old_key
            else:
                os.environ.pop("BAICHUAN_API_KEY", None)

    def test_create_claude_model(self):
        old_key = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        try:
            llm = create_llm("claude-sonnet-4-20250514", temperature=0.5)
            assert llm is not None
            assert llm.model == "claude-sonnet-4-20250514"
        finally:
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key
            else:
                os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_create_minimax_model(self):
        old_key = os.environ.get("MINIMAX_API_KEY")
        os.environ["MINIMAX_API_KEY"] = "test-key"
        try:
            llm = create_llm("minimax-m2.7", temperature=0.5)
            assert llm is not None
        finally:
            if old_key:
                os.environ["MINIMAX_API_KEY"] = old_key
            else:
                os.environ.pop("MINIMAX_API_KEY", None)

    def test_api_key_parameter(self):
        llm = create_llm("gpt-4o", api_key="direct-key", temperature=0.5)
        assert llm is not None


class TestAutoSelectLLM:
    def test_auto_select_with_env(self):
        old_key = os.environ.get("DEEPSEEK_API_KEY")
        os.environ["DEEPSEEK_API_KEY"] = "test-key"
        try:
            name, llm = auto_select_llm(preferred_providers=["deepseek"])
            assert name == "deepseek-chat"
            assert llm is not None
        finally:
            if old_key:
                os.environ["DEEPSEEK_API_KEY"] = old_key
            else:
                os.environ.pop("DEEPSEEK_API_KEY", None)

    def test_auto_select_no_keys(self):
        keys_to_clear = ["DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "KIMI_API_KEY",
                         "ZHIPU_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                         "MINIMAX_API_KEY", "BAICHUAN_API_KEY"]
        saved = {}
        for k in keys_to_clear:
            saved[k] = os.environ.get(k)
            os.environ[k] = ""
        try:
            name, llm = auto_select_llm()
            assert name is None
            assert llm is None
        finally:
            for k, v in saved.items():
                if v:
                    os.environ[k] = v
                else:
                    os.environ.pop(k, None)
