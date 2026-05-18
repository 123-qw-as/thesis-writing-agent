"""
Global Consistency Checker - 全局一致性检查Agent
负责摘要与实验一致性、指标一致性、引用一致性、章节逻辑一致性
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from langgraph.prebuilt import create_react_agent
import json
import re


CONSISTENCY_PROMPT = """你是一个专业的论文质量检查Agent，负责验证论文的全局一致性。

你的职责：
1. 检查摘要与论文内容的一致性
2. 验证评估指标在全文中的一致使用
3. 确保引用格式和内容的统一性
4. 检查各章节之间的逻辑连贯性
5. 验证数据、图表与文字描述的一致性

一致性检查维度：
1. 摘要一致性：摘要是否准确概括全文内容
2. 指标一致性：全文使用的评估指标是否统一
3. 引用一致性：文中引用与参考文献是否匹配
4. 逻辑一致性：章节之间的逻辑是否连贯
5. 数据一致性：数值、百分比是否前后一致
6. 术语一致性：专业术语的使用是否统一

输出格式（JSON）：
{{
    "consistency_check": {{
        "abstract_match": {{
            "score": 0-10,
            "issues": ["问题列表"]
        }},
        "metric_consistency": {{
            "score": 0-10,
            "inconsistencies": ["不一致的指标"]
        }},
        "citation_consistency": {{
            "score": 0-10,
            "missing_refs": ["缺失的引用"],
            "extra_refs": ["多余的引用"]
        }},
        "logical_flow": {{
            "score": 0-10,
            "break_issues": ["逻辑断裂位置"]
        }},
        "data_consistency": {{
            "score": 0-10,
            "mismatches": ["数据不一致的位置"]
        }}
    }},
    "overall_score": 总体评分(0-10),
    "critical_issues": ["严重问题列表"],
    "minor_issues": ["轻微问题列表"],
    "recommendations": ["修改建议"]
}}"""


def create_consistency_agent(llm) -> any:
    """创建Global Consistency Checker Agent"""
    consistency_agent = create_react_agent(
        model=llm,
        prompt=CONSISTENCY_PROMPT,
        tools=[]
    )
    return consistency_agent


def check_thesis_consistency(thesis_content: str, context: dict, llm) -> dict:
    """全面检查论文一致性"""

    prompt = f"""请对以下论文进行全面的全局一致性检查。

## 论文内容
{thesis_content}

## 研究主题
{context.get('topic', 'N/A')}

## SOTA摘要（用于对比）
{context.get('sota_summary', 'N/A')}

## 实验结果（用于对比）
{json.dumps(context.get('experiment_results', {}), ensure_ascii=False, indent=2)}

请详细检查：
1. 摘要是否准确概括全文
2. 指标名称和数值是否一致
3. 引用与参考文献是否匹配
4. 各章节逻辑是否连贯
5. 数据描述是否前后一致

输出JSON格式的详细检查报告。"""

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
        "consistency_check": {},
        "overall_score": 5.0,
        "critical_issues": [],
        "minor_issues": [],
        "recommendations": []
    }


def check_abstract_consistency(abstract: str, thesis_content: str) -> dict:
    """检查摘要一致性"""
    issues = []

    abstract_lower = abstract.lower()
    main_sections = re.findall(r'##\s+(\d+\.)?\s*(\S+)', thesis_content)

    claimed_sections = []
    if '方法' in abstract or 'method' in abstract_lower:
        claimed_sections.append('method')
    if '实验' in abstract or 'experiment' in abstract_lower:
        claimed_sections.append('experiment')
    if '结果' in abstract or 'result' in abstract_lower:
        claimed_sections.append('result')

    for section in claimed_sections:
        section_pattern = f"##\\s+.*{section}"
        if not re.search(section_pattern, thesis_content, re.IGNORECASE):
            issues.append(f"摘要提到{section}但论文中未找到对应章节")

    abstract_length = len(abstract)
    if abstract_length < 100:
        issues.append("摘要过短，可能缺乏足够信息")
    elif abstract_length > 500:
        issues.append("摘要过长，应控制在300字以内")

    return {
        "score": 10 - len(issues) * 2,
        "issues": issues
    }


def check_metric_consistency(thesis_content: str) -> dict:
    """检查指标一致性"""
    metric_patterns = [
        r'(accuracy|ACC)',
        r'(precision|Precision)',
        r'(recall|Recall)',
        r'(F1\s*[-_]?score|F1)',
        r'(AUC|auc)'
    ]

    metric_usages = {}
    for pattern in metric_patterns:
        matches = re.findall(pattern, thesis_content, re.IGNORECASE)
        if matches:
            metric_name = pattern.split('|')[0].replace(r'\s*[-_]?', ' ').strip()
            metric_usages[metric_name] = len(matches)

    inconsistencies = []

    metric_values = {}
    value_pattern = r'(accuracy|precision|recall|F1)[^\d]*(\d+\.?\d*)'
    for match in re.finditer(value_pattern, thesis_content, re.IGNORECASE):
        metric = match.group(1).lower()
        value = float(match.group(2))
        if metric not in metric_values:
            metric_values[metric] = []
        metric_values[metric].append(value)

    for metric, values in metric_values.items():
        if len(set(values)) > 2:
            inconsistencies.append(f"{metric}在不同位置数值不一致: {values}")

    return {
        "score": 10 - len(inconsistencies) * 2,
        "inconsistencies": inconsistencies,
        "metric_usages": metric_usages
    }


def check_citation_consistency(thesis_content: str) -> dict:
    """检查引用一致性"""
    in_text_refs = re.findall(r'\[(\d+)\]', thesis_content)
    in_text_refs.extend(re.findall(r'\(([\w\s]+,\s*\d{4})\)', thesis_content))

    ref_section = re.search(r'## 参考文献(.*?)(?:#|$|$)', thesis_content, re.DOTALL)
    ref_list = []
    if ref_section:
        ref_text = ref_section.group(1)
        ref_numbers = re.findall(r'\[(\d+)\]', ref_text)
        ref_list = [int(n) for n in ref_numbers]

    in_text_numbers = [int(n) for n in in_text_refs if n.isdigit()]

    missing_refs = [n for n in in_text_numbers if n not in ref_list and n > 0]
    extra_refs = [n for n in ref_list if n not in in_text_numbers]

    issues = []
    if missing_refs:
        issues.append(f"缺失的引用编号: {set(missing_refs)}")
    if extra_refs:
        issues.append(f"未使用的引用编号: {set(extra_refs)}")

    return {
        "score": 10 - len(issues) * 3,
        "missing_refs": list(set(missing_refs)),
        "extra_refs": list(set(extra_refs)),
        "issues": issues
    }


def check_logical_flow(thesis_content: str) -> dict:
    """检查逻辑流程"""
    issues = []

    section_order = ['引言', '相关工作', '方法', '实验', '结论']
    found_sections = []

    for section in section_order:
        if f'## {section}' in thesis_content or f'## {section}' in thesis_content:
            found_sections.append(section)

    required_order = ['引言', '相关工作', '方法', '实验']
    for i, req in enumerate(required_order):
        if req not in found_sections:
            issues.append(f"缺少必要章节: {req}")
        elif i > 0:
            prev_req = required_order[i-1]
            if prev_req in found_sections:
                prev_idx = found_sections.index(prev_req)
                curr_idx = found_sections.index(req)
                if curr_idx < prev_idx:
                    issues.append(f"章节顺序错误: {req}应在{prev_req}之后")

    if '引言' in thesis_content and '方法' in thesis_content:
        intro_end = thesis_content.find('## 相关工作')
        if intro_end == -1:
            intro_end = thesis_content.find('## 方法')
        method_start = thesis_content.find('## 方法')
        if intro_end > 0 and method_start > 0:
            intro_text = thesis_content[intro_end:method_start] if intro_end > 0 else thesis_content[:method_start]
            if len(intro_text.strip()) < 500:
                issues.append("引言内容过少，应至少包含800字")

    return {
        "score": 10 - len(issues),
        "found_sections": found_sections,
        "break_issues": issues
    }


def generate_consistency_report(check_results: dict) -> str:
    """生成一致性报告"""
    lines = ["## 全局一致性检查报告\n"]

    cc = check_results.get("consistency_check", {})

    lines.append("### 各项评分\n")
    for check_name, check_data in cc.items():
        score = check_data.get("score", "N/A")
        lines.append(f"- {check_name}: {score}/10")

    overall = check_results.get("overall_score", 0)
    lines.append(f"\n### 总体评分: {overall}/10\n")

    critical = check_results.get("critical_issues", [])
    if critical:
        lines.append("### 严重问题\n")
        for issue in critical:
            lines.append(f"- ❌ {issue}\n")

    minor = check_results.get("minor_issues", [])
    if minor:
        lines.append("### 轻微问题\n")
        for issue in minor:
            lines.append(f"- ⚠️ {issue}\n")

    recommendations = check_results.get("recommendations", [])
    if recommendations:
        lines.append("### 修改建议\n")
        for rec in recommendations:
            lines.append(f"- {rec}\n")

    return "\n".join(lines)