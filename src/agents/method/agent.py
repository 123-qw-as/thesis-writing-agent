"""
Method Agent - 方法设计Agent
负责Baseline设计、模型设计、实验规划
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from langgraph.prebuilt import create_react_agent
import json


METHOD_PROMPT = """你是一个专业的机器学习研究方法设计Agent，负责设计研究方法和实验方案。

你的职责：
1. 基于研究问题设计合适的基线方法（Baseline）
2. 提出创新性的方法架构
3. 设计评估指标和实验方案
4. 确保方法的可行性和创新性

设计原则：
1. 创新性：方法应有实质性的改进或创新点
2. 可行性：方法应能在合理时间内实现和验证
3. 可复现性：方法描述应足够详细以支持复现
4. 对比性：应能与现有方法进行公平比较

输出格式（JSON）：
{{
    "method_name": "方法名称",
    "method_type": "分类/回归/生成/增强/...",
    "baseline": {{
        "name": "基线方法名称",
        "description": "基线方法描述",
        "expected_performance": "预期性能"
    }},
    "proposed_method": {{
        "name": "提出的方法名称",
        "overview": "方法概述",
        "architecture": "详细架构描述",
        "key_components": ["关键组件列表"],
        "novelty": "创新点描述"
    }},
    "evaluation_metrics": [
        {{
            "name": "指标名称",
            "description": "指标描述",
            "calculation": "计算方式"
        }}
    ],
    "experimental_setup": {{
        "datasets": ["数据集列表"],
        "baselines_to_compare": ["对比基线列表"],
        "implementation_details": "实现细节"
    }},
    "expected_contributions": ["预期贡献列表"],
    "potential_limitations": ["潜在局限列表"]
}}

请基于研究问题和SOTA分析，设计完整的研究方法方案。"""


def create_method_agent(llm) -> any:
    """创建Method Agent"""
    method_agent = create_react_agent(
        model=llm,
        prompt=METHOD_PROMPT,
        tools=[]
    )
    return method_agent


def design_method(research_topic: str, sota_analysis: dict, constraints: dict, llm) -> dict:
    """设计研究方法"""

    prompt = f"""请为以下研究主题设计完整的研究方法方案。

## 研究主题
{research_topic}

## SOTA分析
{json.dumps(sota_analysis, ensure_ascii=False, indent=2)}

## 约束条件
{json.dumps(constraints, ensure_ascii=False, indent=2)}

约束条件可能包含：
- 可用计算资源
- 数据集限制
- 时间限制
- 实现难度要求

请设计一个完整的研究方法，包括基线、提出的方法、评估指标、实验方案。
输出JSON格式的方法设计方案。"""

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, 'content') else str(response)

    try:
        if isinstance(content, list):
            for block in content:
                if hasattr(block, 'type') and block.type == 'text':
                    content = block.text
                    break

        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass

    return {
        "method_name": "Proposed Method",
        "method_type": "unknown",
        "baseline": {},
        "proposed_method": {},
        "evaluation_metrics": [],
        "experimental_setup": {},
        "expected_contributions": [],
        "potential_limitations": []
    }


def compare_methods(method1: dict, method2: dict) -> dict:
    """比较两个方法"""
    return {
        "method1": method1.get("method_name", "Unknown"),
        "method2": method2.get("method_name", "Unknown"),
        "comparison_points": [],
        "advantages": [],
        "disadvantages": []
    }


def generate_baseline_comparison(method_design: dict, sota_methods: list) -> str:
    """生成基线对比说明"""
    baseline_name = method_design.get("baseline", {}).get("name", "Unknown")
    proposed_name = method_design.get("proposed_method", {}).get("name", "Proposed")

    lines = [f"## 方法对比\n"]
    lines.append(f"### 基线方法：{baseline_name}\n")
    lines.append(f"### 提出方法：{proposed_name}\n")
    lines.append("\n### 与SOTA方法的对比\n")

    for sota in sota_methods[:3]:
        lines.append(f"- {sota.get('name', 'N/A')}: {sota.get('key_contribution', 'N/A')}")

    return "\n".join(lines)


METHOD_REVISION_PROMPT = """请根据以下反馈意见修改方法设计。

## 原方法设计
{original_design}

## 反馈意见
{feedback}

## 约束条件
{constraints}

请修改方法设计，使其更好地满足反馈意见和约束条件。
输出JSON格式的更新后的方法设计方案。"""


def revise_method(original_design: dict, feedback: str, constraints: dict, llm) -> dict:
    """根据反馈修改方法设计"""
    prompt = METHOD_REVISION_PROMPT.format(
        original_design=json.dumps(original_design, ensure_ascii=False),
        feedback=feedback,
        constraints=json.dumps(constraints, ensure_ascii=False)
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, 'content') else str(response)

    try:
        if isinstance(content, list):
            for block in content:
                if hasattr(block, 'type') and block.type == 'text':
                    content = block.text
                    break

        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass

    return original_design