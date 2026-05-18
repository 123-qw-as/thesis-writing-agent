"""
Reviewer Agent - 论文审查与质量评估Agent
负责逻辑一致性检查、AI味检测、质量评估
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from langgraph.prebuilt import create_react_agent
import json
import re


REVIEWER_PROMPT = """你是一个专业的学术论文审稿人，负责评估和改进研究论文。

你的职责：
1. 检查论文逻辑一致性和完整性
2. 识别AI生成内容的特征（AI味检测）
3. 评估研究创新性和实验合理性
4. 检查引用真实性和完整性
5. 提供具体的修改建议

评估维度：
1. 逻辑一致性 (1-10分)
   - 章节之间逻辑是否连贯
   - 论证链条是否完整
   - 是否存在自相矛盾

2. AI味检测 (1-10分，10分=无AI味)
   - 句式是否过于模板化
   - 表达是否缺乏个性化
   - 是否有明显的AI写作特征

3. 创新性评估 (1-10分)
   - 相比SOTA是否有实质性贡献
   - 创新点是否明确
   - 是否解决了有价值的研究问题

4. 实验合理性 (1-10分)
   - 实验设置是否充分
   - 评估指标是否合理
   - 结果分析是否深入

5. 引用质量 (1-10分)
   - 引用是否真实存在
   - 格式是否规范
   - 是否覆盖关键工作

输出格式（JSON）：
{{
    "overall_score": 总体评分(0-10),
    "scores": {{
        "logical_consistency": 逻辑一致性评分,
        "ai_detection_score": AI味检测评分,
        "innovation_score": 创新性评分,
        "experiment_score": 实验合理性评分,
        "citation_score": 引用质量评分
    }},
    "issues": [
        {{
            "severity": "critical|major|minor",
            "location": "问题位置",
            "description": "问题描述",
            "suggestion": "修改建议"
        }}
    ],
    "strengths": ["论文优点列表"],
    "revision_priority": ["优先修改项"],
    "verdict": "accept|minor_revision|major_revision|reject"
}}

请进行详细评审并输出JSON格式的报告。"""


def create_reviewer_agent(llm) -> any:
    """创建Reviewer Agent"""
    reviewer_agent = create_react_agent(
        model=llm,
        prompt=REVIEWER_PROMPT,
        tools=[]
    )
    return reviewer_agent


def review_thesis(thesis_content: str, context: dict, llm) -> dict:
    """审查论文"""

    prompt = f"""请审查以下论文并提供详细的评审报告。

## 论文内容
{thesis_content}

## 研究主题
{context.get('topic', 'N/A')}

## 研究背景（SOTA）
{context.get('sota_summary', 'N/A')}

请进行全面的论文评审，检查逻辑一致性、AI味、创新性、实验合理性、引用质量。
输出JSON格式的详细评审报告。"""

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, 'content') else str(response)

    try:
        if isinstance(content, list):
            for block in content:
                if hasattr(block, 'type') and block.type == 'text':
                    content = block.text
                    break

        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass

    return {
        "overall_score": 5.0,
        "scores": {
            "logical_consistency": 5.0,
            "ai_detection_score": 5.0,
            "innovation_score": 5.0,
            "experiment_score": 5.0,
            "citation_score": 5.0
        },
        "issues": [],
        "strengths": [],
        "revision_priority": [],
        "verdict": "minor_revision"
    }


def check_logical_consistency(thesis_content: str) -> dict:
    """检查逻辑一致性"""
    issues = []

    sections = re.split(r'##\s+', thesis_content)
    section_names = [s.split('\n')[0].strip() for s in sections[1:]]

    required_sections = ['摘要', '引言', '相关工作', '方法', '实验', '结论']
    for req in required_sections:
        if req not in ' '.join(section_names):
            issues.append({
                "type": "missing_section",
                "description": f"缺少必要章节：{req}"
            })

    if "方法" in thesis_content and "实验" in thesis_content:
        method_exp = re.search(r'##\s*方法.*?(?=##\s*实验|$)', thesis_content, re.DOTALL)
        experiment_exp = re.search(r'##\s*实验.*?(?=##\s*结论|$)', thesis_content, re.DOTALL)
        if method_exp and experiment_exp:
            method_text = method_exp.group()
            exp_text = experiment_exp.group()
            if len(method_text) < 500:
                issues.append({
                    "type": "insufficient_detail",
                    "description": "方法章节内容过少，可能缺乏技术细节"
                })

    return {
        "consistent": len(issues) == 0,
        "issues": issues
    }


def detect_ai_patterns(text: str) -> dict:
    """检测AI生成内容特征"""
    ai_patterns = {
        "模板化句式": [
            r"首先，", r"其次，", r"最后，",
            r"总的来说", r"综上所述",
            r"值得注意的是", r"不言而喻",
            r"众所周知", r"显而易见"
        ],
        "过度使用连接词": r"\b而且\b|\b但是\b|\b因此\b|\b于是\b",
        "重复性结构": r"这表明.*?这意味着",
        "空洞表达": r"非常重要|显著提高|明显改善"
    }

    detected = []
    for pattern_name, pattern in ai_patterns.items():
        matches = re.findall(pattern, text)
        if len(matches) > 5:
            detected.append({
                "pattern": pattern_name,
                "count": len(matches),
                "severity": "high" if len(matches) > 10 else "medium"
            })

    return {
        "has_ai_patterns": len(detected) > 0,
        "patterns": detected,
        "ai_score": max(0, 10 - len(detected) * 2)
    }


def generate_revision_feedback(review_result: dict) -> str:
    """根据评审结果生成修改建议"""
    if review_result.get("overall_score", 0) >= 8:
        return "论文质量良好，仅需少量修改。"

    issues = review_result.get("issues", [])
    if not issues:
        return "未发现明显问题，建议通读全文确认表述。"

    feedback_parts = ["请根据以下意见修改论文：\n"]
    for i, issue in enumerate(issues[:5], 1):
        feedback_parts.append(f"{i}. [{issue.get('severity', 'unknown')}] {issue.get('description', '')}")
        if issue.get('suggestion'):
            feedback_parts.append(f"   建议：{issue.get('suggestion')}")
        feedback_parts.append("")

    return "\n".join(feedback_parts)


def should_accept(review_result: dict, threshold: float = 7.0) -> bool:
    """判断是否接受当前版本"""
    score = review_result.get("overall_score", 0)
    verdict = review_result.get("verdict", "")

    if verdict in ["accept"]:
        return True
    if score >= threshold and verdict in ["minor_revision"]:
        return True
    return False


def extract_citations(thesis_content: str) -> list:
    """从论文中提取引用列表"""
    import re

    citations = []

    ref_patterns = [
        r'\[(\d+)\]\s*(.*?)(?:\n|$)',
        r'\(([\w\s]+,\s*\d{4})\)',
        r'（(\d+)）'
    ]

    for pattern in ref_patterns:
        matches = re.findall(pattern, thesis_content)
        citations.extend(matches)

    unique_citations = list(set(citations))
    return [{"citation": c} for c in unique_citations]