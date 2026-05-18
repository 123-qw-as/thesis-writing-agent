"""
Quality Improvement Agent - 论文质量综合改进系统
自动化执行8步流程并循环改进直至达到目标

目标阈值:
- Overall Score >= 8.0
- AIGC Score < 18%
- Data Authenticity >= 75%
"""

import asyncio
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.tools.aigc_detector import AIGCDetector
from src.tools.data_verifier import DataVerifier
from src.agents.evaluation.agent import EvaluationAgent, EvaluationReport


@dataclass
class QualityTargets:
    overall: float = 8.0
    aigc: float = 18.0
    data_auth: float = 75.0


@dataclass
class QualityResult:
    success: bool
    iteration: int
    thesis_content: str
    overall_score: float
    aigc_score: float
    data_authenticity: float
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    duration_seconds: float


class QualityImprovementAgent:
    """论文质量改进Agent"""

    def __init__(self, llm=None, targets: QualityTargets = None):
        self.llm = llm
        self.targets = targets or QualityTargets()
        self.evaluation_agent = EvaluationAgent(llm)
        self.aigc_detector = AIGCDetector()
        self.data_verifier = DataVerifier()

    async def improve(
        self,
        thesis_content: str,
        thesis_title: str = "未命名论文",
        max_iterations: int = 10
    ) -> QualityResult:
        """
        执行质量改进流程

        Args:
            thesis_content: 论文内容
            thesis_title: 论文标题
            max_iterations: 最大迭代次数

        Returns:
            QualityResult: 改进结果
        """
        start_time = datetime.now()
        current_content = thesis_content
        best_content = thesis_content
        best_score = 0.0
        iteration = 0

        for iteration in range(1, max_iterations + 1):
            print(f"\n{'='*60}")
            print(f"Iteration {iteration}/{max_iterations}")
            print(f"{'='*60}")

            report = await self.evaluation_agent.evaluate(
                current_content, thesis_title, iteration
            )

            print(f"Overall: {report.overall_score}/10")
            print(f"AIGC: {report.aigc_score}%")
            print(f"Data Auth: {report.data_authenticity}%")

            if self._check_targets_met(report):
                duration = (datetime.now() - start_time).total_seconds()
                return QualityResult(
                    success=True,
                    iteration=iteration,
                    thesis_content=current_content,
                    overall_score=report.overall_score,
                    aigc_score=report.aigc_score,
                    data_authenticity=report.data_authenticity,
                    issues=report.issues,
                    suggestions=report.revision_suggestions,
                    duration_seconds=duration
                )

            if report.overall_score > best_score:
                best_score = report.overall_score
                best_content = current_content

            current_content = await self._apply_improvements(
                current_content, report
            )

        duration = (datetime.now() - start_time).total_seconds()
        final_report = await self.evaluation_agent.evaluate(
            best_content, thesis_title, iteration
        )

        return QualityResult(
            success=False,
            iteration=iteration,
            thesis_content=best_content,
            overall_score=final_report.overall_score,
            aigc_score=final_report.aigc_score,
            data_authenticity=final_report.data_authenticity,
            issues=final_report.issues,
            suggestions=final_report.revision_suggestions,
            duration_seconds=duration
        )

    def _check_targets_met(self, report: EvaluationReport) -> bool:
        return (
            report.overall_score >= self.targets.overall and
            report.aigc_score < self.targets.aigc and
            report.data_authenticity >= self.targets.data_auth
        )

    async def _apply_improvements(
        self,
        thesis: str,
        report: EvaluationReport
    ) -> str:
        """根据评估报告应用相应的改进"""
        improvements = []

        if report.overall_score < self.targets.overall:
            improvements.append(self._improve_overall_quality)
        if report.aigc_score >= self.targets.aigc:
            improvements.append(self._reduce_aigc)
        if report.data_authenticity < self.targets.data_auth:
            improvements.append(self._improve_data_authenticity)

        if not improvements:
            improvements.append(self._reduce_aigc)

        for improve_func in improvements:
            thesis = await improve_func(thesis, report)

        return thesis

    async def _improve_overall_quality(
        self,
        thesis: str,
        report: EvaluationReport
    ) -> str:
        """改进论文整体质量"""
        if not self.llm:
            return thesis

        issues_text = '\n'.join([
            f"- {i.get('description', '')}"
            for i in report.issues[:3]
        ])

        prompt = f"""请改进以下学术论文，消除以下问题：

问题列表：
{issues_text}

改进要求：
1. 明确阐述研究贡献（列出2-3个具体贡献）
2. 补充方法论细节和评估指标说明
3. 增强创新点表述
4. 保持现有结构不变
5. 保持自然的写作风格，不要使用AI模板句
6. 不要添加任何新的具体数据数字

论文：
{thesis[:10000]}"""

        try:
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            from src.utils.llm_utils import extract_text_from_response
            improved = extract_text_from_response(response)
            if len(improved) > len(thesis) * 0.5:
                return improved
        except Exception as e:
            print(f"LLM improvement failed: {e}")

        return thesis

    async def _reduce_aigc(self, thesis: str, report: EvaluationReport) -> str:
        """降低AIGC率"""
        if not self.llm:
            return self._rule_based_deai(thesis)

        prompt = f"""将以下学术论文进行深度改写，消除AI写作特征。

重点消除以下内容：
1. 模板化连接词：首先、其次、最后、因此、然而、但是、此外、与此同时
2. 空洞修饰词：非常重要、十分关键、具有重要意义、取得了显著成果
3. 重复句式结构：...的工作、...的研究、...的方法
4. 最高级夸张：最优，最佳，最好，最先进，显著提升

改写要求：
- 替换为自然、口语化但仍学术的表达
- 保持所有技术内容不变
- 不要添加或删除任何实质内容
- 保持论文长度基本不变

论文：
{thesis[:12000]}"""

        try:
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            from src.utils.llm_utils import extract_text_from_response
            improved = extract_text_from_response(response)
            if len(improved) > len(thesis) * 0.5:
                return improved
        except Exception as e:
            print(f"LLM De-AI failed: {e}")

        return self._rule_based_deai(thesis)

    def _rule_based_deai(self, thesis: str) -> str:
        """基于规则的De-AI改写"""
        replacements = [
            (r'\b首先\b', '开篇'),
            (r'\b其次\b', '接下来'),
            (r'\b最后\b', '在此基础上'),
            (r'\b因此\b', '基于此'),
            (r'\b然而\b', '不过'),
            (r'\b但是\b', '不过'),
            (r'\b此外\b', '同时'),
            (r'\b与此同时\b', '在此期间'),
            (r'\b综上所述\b', '总的来说'),
            (r'\b总之\b', '整体来看'),
            (r'\b非常重要\b', '需要认真对待'),
            (r'\b十分关键\b', '具有实际意义'),
            (r'\b具有重要意义\b', '对实际应用有参考价值'),
            (r'\b取得了显著成果\b', '表现良好'),
            (r'\b最优\b', '较好'),
            (r'\b最佳\b', '较好'),
            (r'\b最先进\b', '较为先进'),
            (r'\b显著提升\b', '有所提升'),
            (r'\b大幅改进\b', '有所改进'),
        ]

        improved = thesis
        for pattern, replacement in replacements:
            improved, _ = re.subn(pattern, replacement, improved, flags=re.IGNORECASE)

        return improved

    async def _improve_data_authenticity(
        self,
        thesis: str,
        report: EvaluationReport
    ) -> str:
        """改进数据真实性"""
        if not self.llm:
            return thesis

        prompt = f"""请检查并改进以下论文中的数据描述：

要求：
1. 移除或替换可疑的数据描述
2. 避免完美分数（100%、1.0等）
3. 避免异常精度的数字
4. 使用真实可信的数据描述
5. 保持技术准确性

论文：
{thesis[:10000]}"""

        try:
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            from src.utils.llm_utils import extract_text_from_response
            improved = extract_text_from_response(response)
            if len(improved) > len(thesis) * 0.5:
                return improved
        except Exception as e:
            print(f"Data authenticity improvement failed: {e}")

        return thesis


async def improve_thesis_quality(
    thesis_content: str,
    thesis_title: str = "未命名论文",
    llm=None,
    max_iterations: int = 10,
    targets: QualityTargets = None
) -> QualityResult:
    """快捷质量改进函数"""
    agent = QualityImprovementAgent(llm, targets)
    return await agent.improve(thesis_content, thesis_title, max_iterations)