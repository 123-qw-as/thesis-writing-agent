"""
Literature Agent - 文献调研与研究问题发现
支持多源搜索: Semantic Scholar, CrossRef, ArXiv, GitHub, Tavily
"""

import json
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from src.tools.research_tools import (
    search_semantic_scholar, search_openalex, search_crossref,
    search_arxiv, search_github_repos, search_tavily, format_search_results
)

LITERATURE_PROMPT = """你是一个专业的研究文献Agent，负责深度文献调研。

你的职责：
1. 使用多源工具搜索相关学术文献
2. 总结当前SOTA（State-of-the-Art）
3. 分析研究Gap和创新机会
4. 整理关键引用和参考

输出格式：
请按以下JSON格式输出分析结果：
{{
    "sota_summary": "当前SOTA总结（200字）",
    "key_papers": [
        {{
            "title": "论文标题",
            "authors": ["作者列表"],
            "year": 年份,
            "venue": "发表venue",
            "url": "论文URL",
            "key_contribution": "主要贡献",
            "method_summary": "方法摘要"
        }}
    ],
    "research_gaps": [
        {{
            "gap": "Gap描述",
            "impact": "影响程度",
            "difficulty": "解决难度1-5"
        }}
    ],
    "innovation_candidates": [
        {{
            "idea": "创新点描述",
            "related_gap": "对应的Gap",
            "feasibility": "可行性评估"
        }}
    ],
    "research_questions": ["待研究的问题列表"]
}}

搜索策略：
- 使用精确的搜索词
- 优先搜索近3年的论文
- 关注顶会顶刊（CVPR, NeurIPS, ICML, AAAI, ICLR等）
- 注意引用数和影响力"""


def run_literature_research(topic: str, llm) -> dict:
    """
    执行文献调研 - 使用多源搜索
    搜索来源: Semantic Scholar(免费), CrossRef(免费), GitHub(免费)
    """
    print(f"  [Literature] Searching papers on: {topic}")

    search_queries = [
        topic,
        f"{topic} deep learning",
        f"{topic} recent advances survey"
    ]

    all_papers = []

    for query in search_queries[:2]:
        for src_name, src_func in [
            ('OpenAlex', search_openalex),
            ('Semantic Scholar', search_semantic_scholar),
            ('CrossRef', search_crossref),
            ('GitHub', search_github_repos),
        ]:
            try:
                results = src_func(query, 5)
                valid = [p for p in results if not p.get('error')]
                if valid:
                    all_papers.extend(valid)
                    print(f"    {src_name}: {len(valid)} papers")
            except Exception as e:
                print(f"    {src_name}: skipped ({e})")

    paper_summary = "\n".join([
        f"[{p.get('year', '')}] {p.get('title', '')[:100]} | "
        f"Citations:{p.get('citations', 'N/A')} | "
        f"Venue:{p.get('venue', 'N/A')[:30]}"
        for p in all_papers[:20]
    ])

    synthesis_prompt = f"""基于以下搜索结果，进行深度分析并输出结构化报告：

主题：{topic}

搜索结果：
{paper_summary}

请输出JSON格式的完整分析报告（包含sota_summary, key_papers, research_gaps, innovation_candidates, research_questions）"""

    synthesis = llm.invoke([HumanMessage(content=synthesis_prompt)])
    content = extract_text_from_response(synthesis)

    try:
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass

    return {
        "sota_summary": "文献搜索完成，等待深度分析...",
        "key_papers": [{'title': p.get('title', ''), 'year': p.get('year', '')}
                       for p in all_papers[:10]],
        "research_gaps": [],
        "innovation_candidates": [],
        "research_questions": []
    }