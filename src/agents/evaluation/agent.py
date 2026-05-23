"""
Evaluation Agent - 论文质量综合评估系统
负责多维度质量评估、问题诊断、改进建议生成
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class ScoreLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAIL = "fail"


@dataclass
class DimensionScore:
    dimension: str
    score: float
    max_score: float = 10.0
    level: ScoreLevel = ScoreLevel.ACCEPTABLE
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class EvaluationReport:
    thesis_title: str
    overall_score: float
    max_score: float = 10.0
    pass_threshold: float = 8.0
    dimensions: List[DimensionScore] = field(default_factory=list)
    aigc_score: float = 0.0
    aigc_threshold: float = 15.0
    data_authenticity: float = 100.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    revision_suggestions: List[str] = field(default_factory=list)
    iteration: int = 1
    is_pass: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thesis_title": self.thesis_title,
            "overall_score": round(self.overall_score, 2),
            "max_score": self.max_score,
            "pass_threshold": self.pass_threshold,
            "is_pass": self.is_pass,
            "aigc_score": round(self.aigc_score, 2),
            "aigc_threshold": self.aigc_threshold,
            "aigc_pass": self.aigc_score < self.aigc_threshold,
            "data_authenticity": round(self.data_authenticity, 2),
            "dimensions": [
                {
                    "dimension": d.dimension,
                    "score": round(d.score, 2),
                    "max_score": d.max_score,
                    "level": d.level.value,
                    "strengths": d.strengths,
                    "weaknesses": d.weaknesses,
                    "suggestions": d.suggestions
                }
                for d in self.dimensions
            ],
            "issues": self.issues,
            "strengths": self.strengths,
            "revision_suggestions": self.revision_suggestions,
            "iteration": self.iteration
        }

    def to_markdown(self) -> str:
        lines = [
            f"# 论文质量评估报告",
            f"",
            f"## 基本信息",
            f"- **论文标题**: {self.thesis_title}",
            f"- **评估轮次**: 第 {self.iteration} 轮",
            f"- **综合评分**: {self.overall_score:.2f}/{self.max_score} ({self._score_to_letter(self.overall_score)})",
            f"- **通过状态**: {'✅ 通过' if self.is_pass else '❌ 未通过'}",
            f"- **AIGC率**: {self.aigc_score:.1f}% (阈值: {self.aigc_threshold}%)",
            f"- **数据真实性**: {self.data_authenticity:.1f}%",
            f"",
            f"## 维度评分",
            f"",
            f"| 维度 | 评分 | 等级 | 评价 |",
            f"|------|------|------|------|",
        ]

        for d in self.dimensions:
            emoji = self._level_emoji(d.level)
            lines.append(f"| {d.dimension} | {d.score:.1f}/{d.max_score} | {emoji} {d.level.value} | {self._weaknesses_summary(d.weaknesses)} |")

        lines.extend([
            f"",
            f"## AIGC检测",
            f"- **检测率**: {self.aigc_score:.1f}%",
            f"- **通过标准**: < {self.aigc_threshold}%",
            f"- **状态**: {'✅ 通过' if self.aigc_score < self.aigc_threshold else '❌ 未通过 - 需要De-AI改写'}",
            f"",
            f"## 数据真实性",
            f"- **可信度**: {self.data_authenticity:.1f}%",
            f"- **状态**: {'✅ 通过' if self.data_authenticity >= 95 else '⚠️ 需要核实'}",
            f"",
        ])

        if self.strengths:
            lines.extend([
                f"## 亮点",
                f"",
            ])
            for s in self.strengths[:5]:
                lines.append(f"- {s}")
            lines.append("")

        if self.issues:
            lines.extend([
                f"## 发现的问题 ({len(self.issues)}个)",
                f"",
            ])
            for i, issue in enumerate(self.issues[:10], 1):
                lines.append(f"### {i}. {issue.get('type', '问题')} - {issue.get('severity', '中等')}级别")
                lines.append(f"- 位置: {issue.get('location', '未知')}")
                lines.append(f"- 描述: {issue.get('description', '')}")
                if issue.get('suggestion'):
                    lines.append(f"- 建议: {issue['suggestion']}")
                lines.append("")
            lines.append("")

        if self.revision_suggestions:
            lines.extend([
                f"## 改进建议",
                f"",
            ])
            for i, suggestion in enumerate(self.revision_suggestions[:5], 1):
                lines.append(f"{i}. {suggestion}")
            lines.append("")

        return "\n".join(lines)

    def _score_to_letter(self, score: float) -> str:
        if score >= 9.5: return "A+"
        elif score >= 9.0: return "A"
        elif score >= 8.5: return "A-"
        elif score >= 8.0: return "B+"
        elif score >= 7.5: return "B"
        elif score >= 7.0: return "B-"
        elif score >= 6.5: return "C+"
        elif score >= 6.0: return "C"
        elif score >= 5.0: return "C-"
        else: return "F"

    def _level_emoji(self, level: ScoreLevel) -> str:
        return {
            ScoreLevel.EXCELLENT: "🟢",
            ScoreLevel.GOOD: "🔵",
            ScoreLevel.ACCEPTABLE: "🟡",
            ScoreLevel.POOR: "🟠",
            ScoreLevel.FAIL: "🔴"
        }.get(level, "⚪")

    def _weaknesses_summary(self, weaknesses: List[str]) -> str:
        if not weaknesses:
            return "无明显问题"
        return "; ".join(weaknesses[:2])


class EvaluationAgent:
    DIMENSION_WEIGHTS = {
        "结构完整性": 0.15,
        "内容质量": 0.20,
        "方法论": 0.15,
        "实验验证": 0.20,
        "写作质量": 0.15,
        "引用规范": 0.10,
        "原创性": 0.05
    }

    PASS_THRESHOLD = 8.0
    AIGC_THRESHOLD = 18.0
    DATA_AUTHENTICITY_THRESHOLD = 75.0

    def __init__(self, llm=None):
        self.llm = llm

    async def evaluate(
        self,
        thesis_content: str,
        thesis_title: str = "未命名论文",
        iteration: int = 1,
        high_quality_papers: Optional[List[Dict[str, Any]]] = None,
        llm=None
    ) -> EvaluationReport:
        """
        综合评估论文质量

        Args:
            thesis_content: 论文完整内容 (Markdown或LaTeX)
            thesis_title: 论文标题
            iteration: 当前迭代轮次
            high_quality_papers: 高质量参考论文列表，用于对比评估
            llm: Language model instance
        """
        effective_llm = llm or self.llm

        if not thesis_content or len(thesis_content) < 500:
            return self._create_empty_report(thesis_title, iteration, "论文内容过短")

        dimension_scores = []
        all_issues = []
        all_strengths = []
        all_suggestions = []

        dimension_results = await self._evaluate_all_dimensions(
            thesis_content, high_quality_papers, effective_llm
        )

        for dim_name, result in dimension_results.items():
            dimension_scores.append(result)
            all_issues.extend(result.weaknesses)
            all_strengths.extend(result.strengths)
            all_suggestions.extend(result.suggestions)

        aigc_score = await self._detect_aigc(thesis_content, effective_llm)

        data_authenticity = await self._check_data_authenticity(
            thesis_content, effective_llm
        )

        overall_score = self._calculate_overall_score(dimension_scores)

        report = EvaluationReport(
            thesis_title=thesis_title,
            overall_score=overall_score,
            dimensions=dimension_scores,
            aigc_score=aigc_score,
            data_authenticity=data_authenticity,
            issues=[{"type": "质量", "description": w, "severity": "中等", "location": "全文"}
                    for w in all_issues],
            strengths=all_strengths[:5],
            revision_suggestions=all_suggestions[:5],
            iteration=iteration,
            is_pass=(
                overall_score >= self.PASS_THRESHOLD and
                aigc_score < self.AIGC_THRESHOLD and
                data_authenticity >= self.DATA_AUTHENTICITY_THRESHOLD
            )
        )

        return report

    async def _evaluate_all_dimensions(
        self,
        thesis_content: str,
        reference_papers: Optional[List[Dict[str, Any]]],
        llm
    ) -> Dict[str, DimensionScore]:
        tasks = [
            ("结构完整性", self._evaluate_structure(thesis_content, llm)),
            ("内容质量", self._evaluate_content_quality(thesis_content, llm)),
            ("方法论", self._evaluate_methodology(thesis_content, llm)),
            ("实验验证", self._evaluate_experiment(thesis_content, llm)),
            ("写作质量", self._evaluate_writing_quality(thesis_content, llm)),
            ("引用规范", self._evaluate_citation(thesis_content, llm)),
            ("原创性", self._evaluate_originality(thesis_content, reference_papers, llm)),
        ]

        results = {}
        for name, task in tasks:
            if task is None:
                results[name] = DimensionScore(name, 5.0, level=ScoreLevel.ACCEPTABLE)
            else:
                results[name] = await task

        return results

    async def _evaluate_structure(self, content: str, llm) -> DimensionScore:
        required_sections = [
            "摘要", "Abstract", "引言", "Introduction",
            "方法", "Method", "实验", "Experiment",
            "结论", "Conclusion", "参考文献", "Reference"
        ]

        present_sections = []
        missing_sections = []

        content_lower = content.lower()

        section_mappings = {
            "abstract": ["摘要", "abstract"],
            "introduction": ["引言", "introduction"],
            "related": ["相关工作", "related work", "文献综述"],
            "method": ["方法", "method", " methodology"],
            "experiment": ["实验", "experiment", " results"],
            "conclusion": ["结论", "conclusion"],
            "reference": ["参考文献", "reference", "bibliography"]
        }

        found_sections = set()
        for key, variations in section_mappings.items():
            for var in variations:
                if var in content_lower:
                    found_sections.add(key)
                    present_sections.append(key)
                    break

        all_keys = set(section_mappings.keys())
        missing = all_keys - found_sections

        score = (len(found_sections) / len(all_keys)) * 10 if all_keys else 5.0

        level = ScoreLevel.EXCELLENT if score >= 9 else \
                ScoreLevel.GOOD if score >= 8 else \
                ScoreLevel.ACCEPTABLE if score >= 6 else \
                ScoreLevel.POOR if score >= 4 else ScoreLevel.FAIL

        strengths = [f"包含{len(found_sections)}个标准章节"] if found_sections else []
        weaknesses = [f"缺少: {', '.join(list(missing)[:3])}"] if missing else []
        suggestions = ["确保包含所有标准章节: 摘要、引言、方法、实验、结论、参考文献"]

        return DimensionScore(
            dimension="结构完整性",
            score=score,
            level=level,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )

    async def _evaluate_content_quality(self, content: str, llm) -> DimensionScore:
        has_problem = any(kw in content.lower() for kw in ["问题", "problem", "挑战", "challenge"])
        has_contribution = any(kw in content.lower() for kw in ["贡献", "contribution", "创新", "novel"])
        has_motivation = any(kw in content.lower() for kw in ["动机", "motivation", "背景", "background"])

        depth_indicators = ["具体", "详细", "深入", "实验表明", "结果显示", "具体来说"]
        depth_count = sum(1 for kw in depth_indicators if kw in content.lower())

        score = 5.0
        if has_problem: score += 1.0
        if has_contribution: score += 1.5
        if has_motivation: score += 1.0
        if depth_count >= 3: score += 1.5
        score = min(score, 10.0)

        level = ScoreLevel.EXCELLENT if score >= 9 else \
                ScoreLevel.GOOD if score >= 8 else \
                ScoreLevel.ACCEPTABLE if score >= 6 else \
                ScoreLevel.POOR if score >= 4 else ScoreLevel.FAIL

        strengths = []
        weaknesses = []
        suggestions = []

        if has_contribution:
            strengths.append("明确阐述研究贡献")
        else:
            weaknesses.append("缺少清晰的研究贡献声明")

        if depth_count >= 3:
            strengths.append("内容分析有一定深度")
        else:
            suggestions.append("增加更深入的分析和讨论")

        if not has_problem:
            weaknesses.append("问题陈述不够明确")

        return DimensionScore(
            dimension="内容质量",
            score=score,
            level=level,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )

    async def _evaluate_methodology(self, content: str, llm) -> DimensionScore:
        method_keywords = ["方法", "method", "算法", "algorithm", "模型", "model", "框架", "framework"]
        has_method = any(kw in content.lower() for kw in method_keywords)

        baseline_keywords = ["baseline", "基线", "对比", "compare", "现有方法", "state-of-the-art"]
        has_baseline = any(kw in content.lower() for kw in baseline_keywords)

        evaluation_keywords = ["评估", "evaluation", "指标", "metric", "准确率", "accuracy", "f1", "auc"]
        has_evaluation = any(kw in content.lower() for kw in evaluation_keywords)

        score = 5.0
        if has_method: score += 2.0
        if has_baseline: score += 2.0
        if has_evaluation: score += 2.0
        score = min(score, 10.0)

        level = ScoreLevel.EXCELLENT if score >= 9 else \
                ScoreLevel.GOOD if score >= 8 else \
                ScoreLevel.ACCEPTABLE if score >= 6 else \
                ScoreLevel.POOR if score >= 4 else ScoreLevel.FAIL

        strengths = []
        weaknesses = []
        suggestions = []

        if has_method:
            strengths.append("清晰描述了研究方法")
        else:
            weaknesses.append("方法描述不清晰")

        if has_baseline:
            strengths.append("包含基线对比")
        else:
            suggestions.append("添加基线方法对比实验")

        if not has_evaluation:
            weaknesses.append("缺少评估指标说明")

        return DimensionScore(
            dimension="方法论",
            score=score,
            level=level,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )

    async def _evaluate_experiment(self, content: str, llm) -> DimensionScore:
        table_keywords = ["表", "table", "图", "figure", "fig", "实验结果", "result"]
        has_table = any(kw in content.lower() for kw in table_keywords)

        dataset_keywords = ["数据集", "dataset", "数据", "data", "训练", "train", "测试", "test"]
        has_dataset = any(kw in content.lower() for kw in dataset_keywords)

        quantitative_keywords = ["%", "率", "ratio", "score", "precision", "recall", "f1"]
        has_quantitative = any(kw in content for kw in quantitative_keywords)

        score = 5.0
        if has_table: score += 1.5
        if has_dataset: score += 2.0
        if has_quantitative: score += 2.0
        score = min(score, 10.0)

        level = ScoreLevel.EXCELLENT if score >= 9 else \
                ScoreLevel.GOOD if score >= 8 else \
                ScoreLevel.ACCEPTABLE if score >= 6 else \
                ScoreLevel.POOR if score >= 4 else ScoreLevel.FAIL

        strengths = []
        weaknesses = []
        suggestions = []

        if has_quantitative:
            strengths.append("包含定量实验结果")
        else:
            weaknesses.append("缺少量化指标")

        if has_dataset:
            strengths.append("说明了使用的数据集")
        else:
            suggestions.append("明确实验使用的数据集")

        return DimensionScore(
            dimension="实验验证",
            score=score,
            level=level,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )

    async def _evaluate_writing_quality(self, content: str, llm) -> DimensionScore:
        length = len(content)

        academic_keywords = ["研究表明", "本文", "我们提出", "我们认为", "综上所述", "因此"]
        has_academic_tone = sum(1 for kw in academic_keywords if kw in content) >= 3

        vague_keywords = ["非常好", "非常好", "很重要", "很有意义", "十分", "极其"]
        has_vague = any(kw in content for kw in vague_keywords)

        repetition_patterns = ["首先，然后，因此，于是，从而", "第一，第二，第三"]
        has_repetition = any(pat in content for pat in repetition_patterns)

        score = 7.0
        if has_academic_tone: score += 1.0
        if has_vague: score -= 1.0
        if has_repetition: score -= 1.0
        if length < 2000: score -= 1.0
        if length > 50000: score -= 0.5
        score = max(min(score, 10.0), 0.0)

        level = ScoreLevel.EXCELLENT if score >= 9 else \
                ScoreLevel.GOOD if score >= 8 else \
                ScoreLevel.ACCEPTABLE if score >= 6 else \
                ScoreLevel.POOR if score >= 4 else ScoreLevel.FAIL

        strengths = []
        weaknesses = []
        suggestions = []

        if has_academic_tone:
            strengths.append("使用学术写作语气")
        else:
            weaknesses.append("学术语气不够规范")
            suggestions.append("多使用学术表达: 本文提出、实验表明、结果表明等")

        if not has_vague:
            strengths.append("避免空洞修饰词")
        else:
            weaknesses.append("存在过于空洞的修饰词")
            suggestions.append("避免使用: 非常好、很重要、十分有意义的等")

        return DimensionScore(
            dimension="写作质量",
            score=score,
            level=level,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )

    async def _evaluate_citation(self, content: str, llm) -> DimensionScore:
        import re

        doi_pattern = r'doi[:\s]*(10\.\d{4,}[^\s]+)'
        dois = re.findall(doi_pattern, content, re.IGNORECASE)

        arxiv_pattern = r'arxiv[:\s]*([\d\.]+)|arxiv\.org/abs/(\w+)'
        arxiv_ids = re.findall(arxiv_pattern, content, re.IGNORECASE)

        citation_markers = re.findall(r'\[.*?\]|\(.*?\d{4}.*?\)', content)

        has_reference_section = any(kw in content.lower() for kw in ["参考文献", "reference", "bibliography"])

        score = 5.0
        if citation_markers: score += 1.5
        if dois: score += 1.5
        if arxiv_ids: score += 1.0
        if has_reference_section: score += 1.0
        score = min(score, 10.0)

        level = ScoreLevel.EXCELLENT if score >= 9 else \
                ScoreLevel.GOOD if score >= 8 else \
                ScoreLevel.ACCEPTABLE if score >= 6 else \
                ScoreLevel.POOR if score >= 4 else ScoreLevel.FAIL

        strengths = []
        weaknesses = []
        suggestions = []

        if citation_markers:
            strengths.append(f"包含{len(citation_markers)}处引用")
        else:
            weaknesses.append("缺少文献引用")

        if dois:
            strengths.append(f"包含{len(dois)}个DOI标识")
        else:
            suggestions.append("使用DOI标识参考文献便于验证")

        if not has_reference_section:
            weaknesses.append("缺少参考文献章节")

        return DimensionScore(
            dimension="引用规范",
            score=score,
            level=level,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )

    async def _evaluate_originality(
        self,
        content: str,
        reference_papers: Optional[List[Dict[str, Any]]],
        llm
    ) -> DimensionScore:
        innovation_keywords = ["创新", "novel", "新", "首次", "首次提出", "首次实现", "首次发现"]
        innovation_count = sum(1 for kw in innovation_keywords if kw in content.lower())

        improvement_keywords = ["提升", "improve", "改进", "enhance", "优于", "更好", " outperform"]
        improvement_count = sum(1 for kw in improvement_keywords if kw in content.lower())

        score = 5.0 + min(innovation_count * 0.5, 2.5) + min(improvement_count * 0.5, 2.5)
        score = min(score, 10.0)

        level = ScoreLevel.EXCELLENT if score >= 9 else \
                ScoreLevel.GOOD if score >= 8 else \
                ScoreLevel.ACCEPTABLE if score >= 6 else \
                ScoreLevel.POOR if score >= 4 else ScoreLevel.FAIL

        strengths = []
        weaknesses = []
        suggestions = []

        if innovation_count >= 2:
            strengths.append(f"明确提出{innovation_count}个创新点")
        else:
            weaknesses.append("创新点不够突出")
            suggestions.append("明确阐述本研究的创新之处")

        return DimensionScore(
            dimension="原创性",
            score=score,
            level=level,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )

    async def _detect_aigc(self, content: str, llm) -> float:
        from src.tools.aigc_detector import AIGCDetector

        detector = AIGCDetector()
        result = detector.detect(content)
        return result.get("aigc_score", 0.0)

    async def _check_data_authenticity(self, content: str, llm) -> float:
        from src.tools.data_verifier import DataVerifier

        verifier = DataVerifier()
        result = verifier.verify(content)
        print(f"  [DataVerifier] Score: {result.get('authenticity_score', 'N/A')}")
        print(f"  [DataVerifier] Suspicious: {len(result.get('suspicious_data_points', []))}")
        print(f"  [DataVerifier] Inconsistencies: {len(result.get('numerical_inconsistencies', []))}")
        print(f"  [DataVerifier] Anomalies: {len(result.get('statistical_anomalies', []))}")
        return result.get("authenticity_score", 80.0)

    def _calculate_overall_score(self, dimension_scores: List[DimensionScore]) -> float:
        if not dimension_scores:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for score in dimension_scores:
            weight = self.DIMENSION_WEIGHTS.get(score.dimension, 0.1)
            normalized_score = score.score / score.max_score
            weighted_sum += normalized_score * weight
            total_weight += weight

        overall = (weighted_sum / total_weight) * 10 if total_weight > 0 else 0.0
        return round(overall, 2)

    def _create_empty_report(self, title: str, iteration: int, reason: str) -> EvaluationReport:
        return EvaluationReport(
            thesis_title=title,
            overall_score=0.0,
            issues=[{"type": "错误", "description": reason, "severity": "高", "location": "全文"}],
            revision_suggestions=["请检查论文内容是否完整"],
            iteration=iteration,
            is_pass=False
        )


async def evaluate_thesis(
    thesis_content: str,
    thesis_title: str = "未命名论文",
    iteration: int = 1,
    high_quality_papers: Optional[List[Dict[str, Any]]] = None,
    llm=None
) -> EvaluationReport:
    """快捷评估函数"""
    agent = EvaluationAgent(llm)
    return await agent.evaluate(
        thesis_content=thesis_content,
        thesis_title=thesis_title,
        iteration=iteration,
        high_quality_papers=high_quality_papers,
        llm=llm
    )