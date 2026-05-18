"""
Base Reviewer - 审稿人基类
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ReviewerReport:
    reviewer_id: str
    role: str
    scores: Dict[str, int]
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[dict] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    overall_comment: str = ''
    confidence: int = 80

    @property
    def avg_score(self) -> float:
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)

    @property
    def passed(self) -> bool:
        return self.avg_score >= 3.0

    def to_dict(self) -> dict:
        return {
            'reviewer_id': self.reviewer_id,
            'role': self.role,
            'scores': self.scores,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'questions': self.questions,
            'overall_comment': self.overall_comment,
            'confidence': self.confidence,
            'avg_score': round(self.avg_score, 2),
            'passed': self.passed,
        }


REVIEW_DIMENSIONS = [
    ('originality', '原创性', '研究问题是否新颖，贡献是否明确'),
    ('methodology', '方法论', '方法设计是否合理、完整、可复现'),
    ('evidence', '证据充分性', '实验/论证是否支撑结论'),
    ('coherence', '逻辑连贯性', '论证链条是否清晰、前后一致'),
    ('writing', '写作质量', '语言表达、结构组织是否规范'),
]

DEFAULT_DIMENSIONS = [{'name': n, 'label': l, 'criterion': c} for n, l, c in REVIEW_DIMENSIONS]


class BaseReviewer:
    def __init__(self, llm, reviewer_id: str, role: str):
        self.llm = llm
        self.reviewer_id = reviewer_id
        self.role = role
        self.dimensions = DEFAULT_DIMENSIONS

    def review(self, content: str, context: Optional[dict] = None) -> ReviewerReport:
        raise NotImplementedError

    def _build_prompt(self, content: str, context: Optional[dict] = None) -> str:
        dim_text = '\n'.join(
            f'  - {d["label"]}({d["name"]}): {d["criterion"]}'
            for d in self.dimensions
        )
        context_text = ''
        if context:
            context_text = '\n## 上下文\n' + json.dumps(context, ensure_ascii=False, indent=2)

        return f"""你是一位学术论文审稿人（ID: {self.reviewer_id}, 角色: {self.role}）。

请对以下论文进行评审，按维度打分（1-5分）。

## 评分维度
{dim_text}

## 评分标准
5=优秀(无改进空间), 4=良好(小改进), 3=合格(明显改进), 2=不足(大改), 1=不合格(重做)

## 论文内容
{content[:6000]}
{context_text}

请输出 JSON 格式（不要加额外文字）：
{{
    "scores": {{"originality": 分, "methodology": 分, "evidence": 分, "coherence": 分, "writing": 分}},
    "strengths": ["优点1", "优点2"],
    "weaknesses": [{{"description": "问题", "severity": "critical/major/minor"}}],
    "questions": ["问题1"],
    "overall_comment": "总体评价",
    "confidence": 置信度0-100
}}"""
