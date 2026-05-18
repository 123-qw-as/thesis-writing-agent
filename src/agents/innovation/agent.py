"""
Innovation Agent - 创新点发现Agent
负责组合已有方法、寻找研究空白、生成新假设
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from langgraph.prebuilt import create_react_agent
import json


INNOVATION_PROMPT = """你是一个专业的AI研究创新顾问，负责发现研究创新点。

你的职责：
1. 分析现有方法的组合可能性
2. 识别研究空白和未解决问题
3. 生成创新性假设和研究方向
4. 评估创新点的可行性和潜力

创新发现策略：
1. 组合创新：将不同领域的方法组合
2. 跨域迁移：将一个领域成功的方法迁移到另一个领域
3. 问题转化：将分类问题转化为其他形式
4. 效率优化：提升现有方法的效率
5. 鲁棒性增强：提高方法在边缘情况的表现

输出格式（JSON）：
{{
    "innovation_opportunities": [
        {{
            "type": "combination|cross_domain|problem_transformation|efficiency|robustness",
            "title": "创新点标题",
            "description": "详细描述",
            "related_methods": ["相关方法列表"],
            "potential_impact": "潜在影响",
            "feasibility": "可行性评估(1-10)",
            "risk": "风险描述"
        }}
    ],
    "research_gaps": [
        {{
            "gap": "研究空白描述",
            "current_approaches": "现有方法",
            "why_gap_exists": "为什么存在这个空白",
            "how_to_address": "如何填补"
        }}
    ],
    "promising_directions": [
        {{
            "direction": "研究方向",
            "rationale": "理由",
            "key_questions": ["关键问题"],
            "expected_outcomes": "预期产出"
        }}
    ]
}}

请基于提供的SOTA分析和研究背景，发现创新机会。"""


def create_innovation_agent(llm) -> any:
    """创建Innovation Agent"""
    innovation_agent = create_react_agent(
        model=llm,
        prompt=INNOVATION_PROMPT,
        tools=[]
    )
    return innovation_agent


def discover_innovations(research_topic: str, sota_analysis: dict, existing_methods: list, llm) -> dict:
    """发现创新点"""

    prompt = f"""请为以下研究主题分析创新机会。

## 研究主题
{research_topic}

## SOTA分析
{json.dumps(sota_analysis, ensure_ascii=False, indent=2)}

## 现有方法
{json.dumps(existing_methods, ensure_ascii=False, indent=2)}

请分析研究领域的创新机会，输出JSON格式的创新报告。
包括：innovation_opportunities, research_gaps, promising_directions"""

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
        "innovation_opportunities": [],
        "research_gaps": [],
        "promising_directions": []
    }


def evaluate_innovation(innovation: dict, existing_knowledge: dict) -> dict:
    """评估创新点"""
    return {
        "innovation": innovation,
        "novelty_score": 7.0,
        "feasibility_score": 8.0,
        "potential_impact": "high",
        "risks": [],
        "recommendations": []
    }


def rank_innovations(innovations: list) -> list:
    """对创新点排序"""
    def score(innovation):
        impact_map = {"high": 3, "medium": 2, "low": 1}
        impact = impact_map.get(innovation.get("potential_impact", "medium"), 2)
        feasibility = innovation.get("feasibility", 5)
        return impact * 0.4 + feasibility * 0.6

    return sorted(innovations, key=score, reverse=True)


def generate_innovation_summary(innovations: dict) -> str:
    """生成创新点摘要"""
    opportunities = innovations.get("innovation_opportunities", [])

    if not opportunities:
        return "未发现明显创新机会"

    lines = ["## 创新点分析\n"]

    lines.append("### 创新机会\n")
    for i, opp in enumerate(opportunities[:3], 1):
        lines.append(f"{i}. **{opp.get('title', 'N/A')}** ({opp.get('type', 'N/A')})")
        lines.append(f"   - {opp.get('description', 'N/A')}")
        lines.append(f"   - 可行性: {opp.get('feasibility', 'N/A')}/10")
        lines.append(f"   - 潜在影响: {opp.get('potential_impact', 'N/A')}\n")

    gaps = innovations.get("research_gaps", [])
    if gaps:
        lines.append("### 研究空白\n")
        for gap in gaps[:3]:
            lines.append(f"- {gap.get('gap', 'N/A')}")

    return "\n".join(lines)