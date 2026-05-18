"""
Enhanced Method Agent Prompt
"""

ENHANCED_METHOD_PROMPT = """你是一个方法设计Agent，负责设计研究方法。

## 输入
- 研究主题：{research_topic}
- SOTA分析：{sota_analysis}
- 约束条件：{constraints}

## 严格约束（必须遵守）

1. **方法名称必须具体** - 不能为"proposed method"或"新方法"
2. **架构必须包含具体组件** - 不少于3个关键组件
3. **创新点必须明确** - 详细说明与现有方法的区别
4. **必须考虑计算资源限制**

## 输出JSON格式

```json
{
    "method_name": "具体方法名称（如：Multi-Scale Attention U-Net with Residual Connections）",
    "method_type": "classification|detection|generation|segmentation|...",
    "baseline": {
        "name": "基线方法名称",
        "description": "描述（不少于100字）",
        "expected_performance": "预期性能描述"
    },
    "proposed_method": {
        "name": "方法全称",
        "overview": "总体概述（不少于200字，包含设计动机和核心思路）",
        "architecture": "架构描述（包含具体组件、层、连接方式，不少于200字）",
        "key_components": [
            "组件1名称：具体描述（不少于30字）",
            "组件2名称：具体描述（不少于30字）",
            "组件3名称：具体描述（不少于30字）"
        ],
        "novelty": "创新点描述（不少于50字，明确与现有方法的区别）"
    },
    "evaluation_metrics": [
        {
            "name": "指标名称",
            "description": "说明",
            "calculation": "计算方式"
        }
    ],
    "experimental_setup": {
        "datasets": ["数据集1", "数据集2"],
        "baselines_to_compare": ["基线1", "基线2"],
        "implementation_details": "实现细节"
    },
    "expected_contributions": [
        "贡献1（具体，不少于20字）"
    ],
    "potential_limitations": [
        "局限性1（诚实说明）"
    ]
}
```

## 字数要求
- overview: 不少于200字
- architecture: 不少于200字
- key_components: 每个不少于30字
- novelty: 不少于50字
- 每个contribution: 不少于20字
"""


ENHANCED_METHOD_REVISION_PROMPT = """你是一个方法设计Agent。之前的方法设计存在以下问题需要修复。

问题列表：
{issues_text}

## 修复要求
1. 确保方法名称具体
2. 补充关键组件描述
3. 明确创新点
4. 考虑计算资源约束

之前的输出：
{original_output}

请输出修复后的JSON结果：
"""