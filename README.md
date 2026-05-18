# 毕设论文写作 Agent 系统

AI 驱动的毕业论文自动写作系统，支持多模型、多阶段质量评估与改进。

## 特性

- **8 家 LLM 提供商，23 个模型**：OpenAI、DeepSeek、Claude、Qwen、Kimi、GLM、Baichuan、MiniMax
- **自动模型选择**：按优先级自动检测可用 API Key
- **LangGraph 工作流**：Research → Code → Write 三阶段流水线
- **完整质量评估体系**：Multi-Reviewer、Integrity Gate、Sprint Contract、Claim Verification 等 13 个模块
- **多源论文搜索**：Semantic Scholar、OpenAlex、CrossRef、ArXiv、GitHub
- **AIGC 检测 + De-AI 改写**：降低 AI 生成痕迹
- **Streamlit Web UI + CLI 双入口**

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 设置 API Key

```bash
cp .env.example .env
# 编辑 .env 填入至少一个 API Key
```

### 运行

**CLI 模式：**
```bash
# 自动选择可用模型
python -m src.main

# 指定模型
python -m src.main --model deepseek-chat

# 列出所有可用模型
python -m src.main --list-models
```

**Web UI 模式：**
```bash
streamlit run src/app.py
```

**质量改进工具：**
```bash
python -m src.main_quality input.md --title "论文标题" --improve
```

## 支持的模型

| 提供商 | 模型 | 环境变量 |
|---|---|---|
| OpenAI | gpt-4o, gpt-4o-mini, o1, o3-mini | `OPENAI_API_KEY` |
| DeepSeek | deepseek-chat, deepseek-reasoner | `DEEPSEEK_API_KEY` |
| Claude | Sonnet 4, Opus 4, Haiku 3.5 | `ANTHROPIC_API_KEY` |
| Qwen | qwen-max, qwen-plus, qwen-turbo | `DASHSCOPE_API_KEY` |
| Kimi | moonshot-v1-8k/32k/128k | `KIMI_API_KEY` |
| GLM | glm-4, glm-4-plus, glm-4-flash | `ZHIPU_API_KEY` |
| Baichuan | baichuan4 | `BAICHUAN_API_KEY` |
| MiniMax | M2.7, abab6.5s, abab6.5g | `MINIMAX_API_KEY` |

## 项目结构

```
project/
├── src/
│   ├── agents/          # Agent 模块 (literature, method, writer, reviewer...)
│   ├── evaluation/      # 质量评估体系 (13 个模块)
│   │   ├── reviewers/   # Multi-Reviewer (R1, R2, DA, EIC)
│   │   └── rubrics/     # 评分标准 (6 维度)
│   ├── workflows/       # 工作流 (research, quality, enhanced)
│   ├── tools/           # 工具 (AIGC检测, 数据验证, 论文搜索)
│   ├── memory/          # 记忆模块 (citation, experiment, vector)
│   ├── llm_config.py    # LLM 配置中心
│   ├── graph.py         # LangGraph 工作流定义
│   ├── app.py           # Streamlit Web UI
│   └── main.py          # CLI 入口
├── tests/               # 单元测试 (169 tests)
└── .env.example         # 环境变量模板
```

## 测试

```bash
# 运行所有单元测试
pytest tests/test_*.py -v

# 运行集成测试
python tests/test_integration_smoke.py
```

## LLM 配置 API

```python
from src.llm_config import create_llm, auto_select_llm

# 工厂函数
llm = create_llm("gpt-4o", api_key="sk-xxx")

# 自动选择
name, llm = auto_select_llm()
```

## License

MIT
