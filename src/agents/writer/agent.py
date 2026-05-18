"""
Writer Agent - 论文写作Agent
负责论文各章节的撰写与格式化
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from langgraph.prebuilt import create_react_agent
import json


WRITER_PROMPT = """你是一个专业的学术论文写作Agent，负责撰写高质量的研究论文。

你的职责：
1. 按照学术论文规范撰写各章节
2. 确保语言表达专业、准确
3. 保持逻辑连贯性和结构清晰
4. 正确引用参考文献

论文标准结构：
1. 摘要 (Abstract)
2. 引言 (Introduction)
3. 相关工作 (Related Work)
4. 方法 (Method)
5. 实验 (Experiments)
6. 结论 (Conclusion)
7. 参考文献 (References)

写作要求：
- 使用正式学术中文
- 逻辑清晰，条理分明
- 图表清晰，说明详尽
- 引用规范，格式统一

每章节要求：
- 摘要：简洁概括研究问题、方法、贡献、结果
- 引言：背景铺垫，问题定义，论文贡献
- 相关工作：同类研究对比，指出现有方法不足
- 方法：技术细节，算法的正确描述
- 实验：数据集、评估指标、结果分析
- 结论：总结贡献，讨论局限，展望未来"""


THESIS_STRUCTURE_TEMPLATE = """
# {title}

## 摘要
{abstract}

## 1. 引言
{introduction}

## 2. 相关工作
{related_work}

## 3. 方法
{method}

## 4. 实验
{experiments}

## 5. 结论
{conclusion}

## 参考文献
{references}
"""


def create_writer_agent(llm) -> any:
    """创建Writer Agent"""
    writer_agent = create_react_agent(
        model=llm,
        prompt=WRITER_PROMPT,
        tools=[]
    )
    return writer_agent


def write_section(section_name: str, context: dict, llm) -> str:
    """撰写单个章节"""
    prompt = f"""撰写论文的「{section_name}」章节。

当前论文主题：{context.get('topic', 'N/A')}
已完成的章节：{list(context.get('completed_sections', {}).keys())}

{context.get('completed_sections', {}).get(section_name, '')}

请撰写专业、详细的{section_name}章节内容，使用学术中文写作。
输出格式：直接输出Markdown格式的章节内容，不要使用JSON或其他格式包装。"""

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, 'content') else str(response)

    if isinstance(content, list):
        for block in content:
            if hasattr(block, 'type') and block.type == 'text':
                return block.text
    return content


def write_full_thesis(topic: str, research_results: dict, method_results: dict, experiment_results: dict, llm, figures: dict = None) -> str:
    """撰写完整论文"""

    sota = research_results.get("sota_summary", "")
    key_papers = research_results.get("key_papers", [])
    gaps = research_results.get("research_gaps", [])
    innovations = research_results.get("innovation_candidates", [])

    method_desc = method_results.get("description", "") if isinstance(method_results, dict) else str(method_results)
    experiment_data = experiment_results if isinstance(experiment_results, dict) else {}

    figure_count = len(figures) if figures else 0
    figure_hint = ""
    if figure_count > 0:
        figure_hint = f"""

图片嵌入说明：
- 论文将自动插入 {figure_count} 张实验图表
- 请在实验章节的结果分析中，在合适的位置插入图片占位符
- 占位符格式为: <!--FIGURE:N--> 其中N是图片编号(1-{figure_count})
- 占位符周围请写"如图N所示"等引用文字
- 例如: 如图1所示，本方法在各项指标上均优于基线模型。<!--FIGURE:1-->
- 请确保每个占位符前后有上下文描述"""

    prompt = f"""请撰写一篇完整的学术论文。

## 论文主题
{topic}

## 研究背景（SOTA摘要）
{sota}

## 关键论文引用
{json.dumps(key_papers[:5], ensure_ascii=False, indent=2)}

## 研究Gap分析
{json.dumps(gaps, ensure_ascii=False, indent=2)}

## 创新点
{json.dumps(innovations, ensure_ascii=False, indent=2)}

## 方法描述
{method_desc}

## 实验结果
{json.dumps(experiment_data, ensure_ascii=False, indent=2)}

请按以下结构撰写完整论文（Markdown格式）：
1. 摘要
2. 引言（背景、研究问题、论文贡献）
3. 相关工作（文献综述、现有方法分析）
4. 方法（详细技术描述）
5. 实验（数据集、评估指标、结果分析）
6. 结论（总结、局限、展望）
7. 参考文献

注意事项：
- 使用正式学术中文
- 字数要求：引言800字以上，方法1500字以上，实验1000字以上
- 正确引用文中的论文
- 输出完整的可直接使用的论文内容
- 实验章节中请提及对比实验、消融实验、收敛曲线分析等

{figure_hint}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, 'content') else str(response)

    if isinstance(content, list):
        text_blocks = [block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"]
        if text_blocks:
            return text_blocks[0]
        if len(content) > 0:
            last_block = content[-1]
            if isinstance(last_block, dict) and "text" in last_block:
                return last_block["text"]
    return str(content) if content else ""


def write_thesis_with_feedback(topic: str, feedback: str, previous_version: str, llm) -> str:
    """根据反馈修改论文"""

    if not previous_version:
        return write_full_thesis(topic, {}, {}, {}, llm)

    prompt = f"""请根据以下反馈意见修改论文。

## 论文主题
{topic}

## 反馈意见
{feedback}

## 上一版本论文
{previous_version}

请仔细阅读反馈意见，针对性地修改论文内容。
输出格式：直接输出修改后的完整论文（Markdown格式）。"""

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, 'content') else str(response)

    if isinstance(content, list):
        text_blocks = [block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"]
        if text_blocks:
            return text_blocks[0]
        if len(content) > 0:
            last_block = content[-1]
            if isinstance(last_block, dict) and "text" in last_block:
                return last_block["text"]
    return str(content) if content else ""


def extract_references(thesis_content: str) -> list:
    """从论文内容中提取参考文献列表"""
    import re

    refs = []
    ref_section = re.search(r'## 参考文献(.*?)(?:#|$)', thesis_content, re.DOTALL)

    if ref_section:
        ref_text = ref_section.group(1)
        ref_lines = re.findall(r'\[(\d+)\]\s*(.*?)(?:\n\[|\n\n|$)', ref_text, re.DOTALL)
        for num, ref in ref_lines:
            refs.append({
                "number": num,
                "citation": ref.strip()
            })

    return refs


THESIS_OUTLINE_PROMPT = """基于研究主题，生成论文大纲。

主题：{topic}

请输出JSON格式的大纲：
{{
    "outline": {{
        "abstract": "摘要要点",
        "introduction": ["引言要点1", "引言要点2"],
        "related_work": ["相关工作要点"],
        "method": ["方法要点"],
        "experiments": ["实验要点"],
        "conclusion": ["结论要点"]
    }},
    "estimated_length": "预估字数",
    "key_sections": ["关键章节"]
}}"""