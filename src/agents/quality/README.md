# Thesis Quality Improvement Module

论文质量改进模块，提供自动化的论文质量评估和改进功能。

## 功能特性

- **质量评估**: 多维度评估论文质量（结构、内容、方法、实验、写作等）
- **AIGC检测**: 检测AI生成特征，提供改写建议
- **数据真实性验证**: 验证论文中数据的可信度
- **自动改进**: 基于LLM或规则进行De-AI改写和质量提升
- **迭代优化**: 循环改进直至达到目标阈值

## 目标阈值

| 指标 | 阈值 | 说明 |
|------|------|------|
| 综合评分 | >= 8.0 | 论文整体质量 |
| AIGC率 | < 18% | AI生成特征比例 |
| 数据真实性 | >= 75% | 数据可信度 |

## 使用方法

### Python API

```python
import asyncio
from src.workflows.quality_workflow import run_quality_workflow

# 改进论文质量
result = asyncio.run(run_quality_workflow(
    thesis_path='input/thesis.md',
    thesis_title='我的论文',
    llm=llm,  # 可选，传入LLM进行深度改写
    output_dir='output'
))

if result['success']:
    print("质量改进成功！")
    print(result['quality_report'])
```

### 命令行工具

```bash
# 评估论文质量
python -m src.main_quality input/thesis.md

# 改进论文质量（使用LLM）
python -m src.main_quality input/thesis.md --improve --title "我的论文"

# 仅检测AIGC
python -m src.main_quality input/thesis.md --detect-aigc

# 不使用LLM（仅规则改写）
python -m src.main_quality input/thesis.md --improve --no-llm
```

## 模块结构

```
src/
├── agents/
│   ├── quality/
│   │   ├── agent.py          # QualityImprovementAgent
│   │   └── __init__.py
│   └── evaluation/
│       └── agent.py           # EvaluationAgent
├── workflows/
│   ├── quality_workflow.py    # QualityWorkflow
│   └── enhanced_pipeline.py   # 增强版研究Pipeline
└── tools/
    ├── aigc_detector.py      # AIGC检测工具
    └── data_verifier.py      # 数据真实性验证
```

## 8步质量改进流程

1. **论文质量评估** - 综合评估论文各维度质量
2. **AIGC检测** - 检测AI生成特征
3. **De-AI改写** - 消除AI写作特征
4. **数据真实性检验** - 验证数据可信度
5. **结构完整性检查** - 确保包含标准章节
6. **基于LLM的深度改写** - 使用LLM进行深度改进
7. **补充论文缺失章节** - 添加结论、参考文献等
8. **重新评估验证** - 验证改进效果

## 评估维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 结构完整性 | 15% | 论文结构是否完整 |
| 内容质量 | 20% | 内容深度和准确性 |
| 方法论 | 15% | 研究方法的合理性 |
| 实验验证 | 20% | 实验设计和结果 |
| 写作质量 | 15% | 写作规范和表达 |
| 引用规范 | 10% | 引用完整性 |
| 原创性 | 5% | 创新程度 |

## 注意事项

- AIGC阈值设为18%是考虑到AI辅助写作的普遍性
- 数据真实性阈值设为75%是因为DOI和代码中的数字可能触发误报
- 建议配合LLM使用以获得更好的改写效果