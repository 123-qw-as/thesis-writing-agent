"""
Rubric基类 - 所有评估Rubric的公共接口
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from src.evaluation.judge import LLMJudge, EvaluationResult, ScoreDimension


@dataclass
class RubricDimension:
    """Rubric维度定义"""
    name: str
    weight: float
    criterion: str
    level5: str = ''
    level3: str = ''
    level1: str = ''

    def to_judge_format(self) -> Dict[str, str]:
        return {
            'name': self.name,
            'criterion': f'{self.criterion}\n  5分={self.level5}\n  3分={self.level3}\n  1分={self.level1}'
        }


class BaseRubric:
    """评估Rubric基类"""

    def __init__(self, llm_judge: LLMJudge):
        self.judge = llm_judge
        self.dimensions: List[RubricDimension] = []
        self.output_type: str = '通用输出'
        self.pass_threshold: float = 0.7

    def evaluate(self, content: Any) -> EvaluationResult:
        """对输出执行评估"""
        content_str = self._prepare_content(content)
        dim_formats = [d.to_judge_format() for d in self.dimensions]
        result = self.judge.evaluate(content_str, self.output_type, dim_formats)

        overall = self._calc_weighted_score(result.dimensions)
        result.overall_score = overall
        result.pass_threshold = self.pass_threshold
        result.passed = overall >= self.pass_threshold
        return result

    def _prepare_content(self, content: Any) -> str:
        """将待评估内容转为字符串"""
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            import json
            return json.dumps(content, ensure_ascii=False, indent=2)
        return str(content)

    def _calc_weighted_score(self, dim_scores: List[ScoreDimension]) -> float:
        """计算加权总分"""
        if not self.dimensions or not dim_scores:
            return 0.0
        total_weight = sum(d.weight for d in self.dimensions)
        if total_weight == 0:
            return 0.0
        weighted = 0.0
        score_map = {d.name: d.score / d.max_score for d in dim_scores}
        for dim in self.dimensions:
            norm_score = score_map.get(dim.name, 0.5)
            weighted += norm_score * dim.weight
        return round(weighted / total_weight, 2)