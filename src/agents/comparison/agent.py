"""
Comparison Agent - 论文对比系统
将生成的论文与领域内高质量论文进行对比评估
"""

from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage
from langchain_anthropic import ChatAnthropic
from src.utils.llm_utils import extract_text_from_response
import json


COMPARISON_PROMPT = """你是一个专业的学术论文评审专家，负责对比评估论文质量。

## 任务
对比分析以下【待评估论文】与【参考高质量论文】，给出详细的对比报告。

## 待评估论文
{thesis_content}

## 参考高质量论文
{reference_papers}

## 对比维度

### 1. 结构对比 (25%)
- 章节完整性
- 逻辑组织
- 格式规范

### 2. 方法论对比 (25%)
- 方法描述清晰度
- 技术深度
- 创新性

### 3. 实验对比 (25%)
- 实验设计合理性
- 数据可信度
- 结果呈现

### 4. 写作对比 (25%)
- 语言规范性
- 学术语气
- 表达清晰度

## 输出格式
请以JSON格式输出对比结果：

{{
    "comparison_id": "对比唯一标识",
    "timestamp": "对比时间",
    "overall_similarity_score": 0-100,  // 与高质量论文的相似度
    "quality_gap": "low/medium/high",  // 质量差距
    "dimensions": {{
        "structure": {{
            "score": 0-10,
            "gap": "具体差距描述",
            "suggestions": ["改进建议"]
        }},
        "methodology": {{
            "score": 0-10,
            "gap": "具体差距描述",
            "suggestions": ["改进建议"]
        }},
        "experiment": {{
            "score": 0-10,
            "gap": "具体差距描述",
            "suggestions": ["改进建议"]
        }},
        "writing": {{
            "score": 0-10,
            "gap": "具体差距描述",
            "suggestions": ["改进建议"]
        }}
    }},
    "reference_quality_features": ["参考论文的亮点特征"],
    "missing_features": ["待评估论文缺失的特征"],
    "priority_improvements": ["优先改进项"]
}}"""


HIGH_QUALITY_PAPER_TEMPLATE = """
论文标题: {title}
作者: {authors}
发表年份: {year}
发表 venue: {venue}
摘要: {abstract}

## 方法特点
{method_summary}

## 实验设置
{experiment_summary}

## 主要贡献
{contributions}
"""


class ComparisonAgent:
    """论文对比Agent"""

    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm

    async def compare(
        self,
        thesis_content: str,
        thesis_title: str = "待评估论文",
        reference_papers: Optional[List[Dict[str, Any]]] = None,
        llm=None
    ) -> Dict[str, Any]:
        """
        对比评估论文与参考高质量论文

        Args:
            thesis_content: 待评估论文内容
            thesis_title: 论文标题
            reference_papers: 参考论文列表
                格式: [{{"title": "", "authors": [], "year": 2024, "venue": "",
                       "abstract": "", "method_summary": "", "experiment_summary": "",
                       "contributions": []}}]
            llm: Language model
        """
        effective_llm = llm or self.llm

        if not reference_papers:
            reference_papers = []

        ref_formatted = self._format_reference_papers(reference_papers)

        if effective_llm:
            comparison_result = await self._compare_with_llm(
                thesis_content, ref_formatted, effective_llm
            )
        else:
            comparison_result = self._compare_without_llm(thesis_content, reference_papers)

        comparison_result["thesis_title"] = thesis_title
        comparison_result["reference_count"] = len(reference_papers)

        return comparison_result

    def _format_reference_papers(self, papers: List[Dict[str, Any]]) -> str:
        """格式化参考论文"""
        if not papers:
            return "未提供参考论文"

        formatted = []
        for i, paper in enumerate(papers, 1):
            content = HIGH_QUALITY_PAPER_TEMPLATE.format(
                title=paper.get("title", "未知标题"),
                authors=", ".join(paper.get("authors", [])),
                year=paper.get("year", "未知年份"),
                venue=paper.get("venue", "未知发表场所"),
                abstract=paper.get("abstract", "无摘要")[:500],
                method_summary=paper.get("method_summary", "无方法描述"),
                experiment_summary=paper.get("experiment_summary", "无实验描述"),
                contributions=", ".join(paper.get("contributions", [])) if paper.get("contributions") else "无"
            )
            formatted.append(f"### 参考论文 {i}\n{content}")

        return "\n".join(formatted)

    async def _compare_with_llm(
        self,
        thesis_content: str,
        reference_papers: str,
        llm
    ) -> Dict[str, Any]:
        """使用LLM进行对比"""
        try:
            prompt = COMPARISON_PROMPT.format(
                thesis_content=thesis_content[:8000],
                reference_papers=reference_papers[:4000]
            )

            response = await llm.ainvoke([HumanMessage(content=prompt)])
            text = extract_text_from_response(response)

            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result

            return {
                "error": "JSON解析失败",
                "raw_response": text[:500],
                "overall_similarity_score": 50.0,
                "quality_gap": "unknown"
            }

        except Exception as e:
            return {
                "error": str(e),
                "overall_similarity_score": 50.0,
                "quality_gap": "unknown"
            }

    def _compare_without_llm(
        self,
        thesis_content: str,
        reference_papers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """不使用LLM的简单对比"""
        thesis_lower = thesis_content.lower()

        features_found = 0
        features_missing = []

        quality_indicators = {
            "abstract": len(thesis_content) > 200 and "摘要" in thesis_content,
            "introduction": "引言" in thesis_content or "introduction" in thesis_lower,
            "method": "方法" in thesis_content or "method" in thesis_lower,
            "experiment": "实验" in thesis_content or "experiment" in thesis_lower,
            "conclusion": "结论" in thesis_content or "conclusion" in thesis_lower,
            "reference": "参考文献" in thesis_content or "reference" in thesis_lower,
            "citation": "[" in thesis_content and "]" in thesis_content,
            "quantitative": any(c in thesis_content for c in ["%", "率", "准确率", "accuracy"]),
        }

        for feature, found in quality_indicators.items():
            if found:
                features_found += 1
            else:
                features_missing.append(feature)

        score = (features_found / len(quality_indicators)) * 100

        return {
            "comparison_id": f"local_{hash(thesis_content) % 10000}",
            "timestamp": "2026-01-01",
            "overall_similarity_score": round(score, 1),
            "quality_gap": "medium" if score < 70 else "low",
            "dimensions": {
                "structure": {
                    "score": 7.0 if quality_indicators["abstract"] else 5.0,
                    "gap": "结构完整但深度可能不足",
                    "suggestions": ["增加文献综述", "完善实验描述"]
                },
                "methodology": {
                    "score": 6.0,
                    "gap": "方法描述需要更详细",
                    "suggestions": ["增加技术细节", "添加复杂度分析"]
                },
                "experiment": {
                    "score": 6.5 if quality_indicators["quantitative"] else 5.0,
                    "gap": "需要更多量化结果",
                    "suggestions": ["添加具体数值", "完善对比实验"]
                },
                "writing": {
                    "score": 7.0,
                    "gap": "写作较为规范但缺乏亮点",
                    "suggestions": ["增加创新性表述", "丰富表达方式"]
                }
            },
            "reference_quality_features": [
                "结构完整，包含标准章节",
                "包含一定的量化分析"
            ],
            "missing_features": features_missing,
            "priority_improvements": features_missing[:3] if features_missing else []
        }

    async def fetch_high_quality_papers(
        self,
        topic: str,
        max_results: int = 5,
        llm=None
    ) -> List[Dict[str, Any]]:
        """
        获取领域内高质量论文

        Args:
            topic: 研究主题
            max_results: 最大返回数量
            llm: Language model
        """
        from src.tools.research_tools import tavily_search, arxiv_search

        papers = []

        try:
            arxiv_results = await arxiv_search(topic, max_results=max_results)
            for r in arxiv_results:
                papers.append({
                    "title": r.get("title", ""),
                    "authors": r.get("authors", []),
                    "year": r.get("year", 2024),
                    "venue": f"arXiv:{r.get('arxiv_id', '')}",
                    "abstract": r.get("abstract", ""),
                    "url": r.get("url", ""),
                    "method_summary": r.get("summary", ""),
                    "experiment_summary": r.get("publish_date", ""),
                    "contributions": []
                })
        except Exception as e:
            print(f"[WARN] arxiv_search failed: {e}")

        try:
            tavily_results = tavily_search(f"{topic} survey review", max_results=max_results)
            for r in tavily_results:
                papers.append({
                    "title": r.get("title", ""),
                    "authors": r.get("authors", []),
                    "year": 2024,
                    "venue": r.get("source", "web"),
                    "abstract": r.get("description", ""),
                    "url": r.get("url", ""),
                    "method_summary": "",
                    "experiment_summary": "",
                    "contributions": []
                })
        except Exception as e:
            print(f"[WARN] tavily_search failed: {e}")

        return papers[:max_results]


async def compare_with_references(
    thesis_content: str,
    thesis_title: str,
    reference_papers: List[Dict[str, Any]],
    llm=None
) -> Dict[str, Any]:
    """快捷论文对比函数"""
    agent = ComparisonAgent(llm)
    return await agent.compare(thesis_content, thesis_title, reference_papers, llm)


async def fetch_and_compare(
    thesis_content: str,
    thesis_title: str,
    topic: str,
    llm=None
) -> Dict[str, Any]:
    """获取高质量论文并对比"""
    agent = ComparisonAgent(llm)

    papers = await agent.fetch_high_quality_papers(topic, max_results=5, llm=llm)

    comparison = await agent.compare(thesis_content, thesis_title, papers, llm=llm)
    comparison["fetched_papers"] = papers

    return comparison