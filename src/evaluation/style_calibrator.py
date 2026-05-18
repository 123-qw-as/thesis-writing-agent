"""
Style Calibration - 写作风格校准
分析论文写作风格与目标发表标准的匹配度
"""

import re
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response


VENUE_STYLES = {
    'CVPR': {
        'name': 'IEEE/CVF Conference on Computer Vision and Pattern Recognition',
        'style': 'technical_concise', 'max_pages': 8, 'max_references': 50,
    },
    'ICCV': {
        'name': 'International Conference on Computer Vision',
        'style': 'technical_concise', 'max_pages': 8, 'max_references': 50,
    },
    'ECCV': {
        'name': 'European Conference on Computer Vision',
        'style': 'technical_concise', 'max_pages': 14, 'max_references': 50,
    },
    'NeurIPS': {
        'name': 'Neural Information Processing Systems',
        'style': 'technical_rigorous', 'max_pages': 9, 'max_references': 50,
    },
    'ICML': {
        'name': 'International Conference on Machine Learning',
        'style': 'technical_rigorous', 'max_pages': 8, 'max_references': 50,
    },
    'ICLR': {
        'name': 'International Conference on Learning Representations',
        'style': 'technical_rigorous', 'max_pages': 9, 'max_references': 50,
    },
    'ACL': {
        'name': 'Association for Computational Linguistics',
        'style': 'linguistic_precise', 'max_pages': 8, 'max_references': 25,
    },
    'EMNLP': {
        'name': 'Empirical Methods in Natural Language Processing',
        'style': 'linguistic_precise', 'max_pages': 8, 'max_references': 25,
    },
    'AAAI': {
        'name': 'AAAI Conference on Artificial Intelligence',
        'style': 'balanced', 'max_pages': 7, 'max_references': 30,
    },
    'IJCAI': {
        'name': 'International Joint Conference on Artificial Intelligence',
        'style': 'balanced', 'max_pages': 7, 'max_references': 30,
    },
}


@dataclass
class DimensionScore:
    dimension: str
    score: float  # 0-100
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'dimension': self.dimension,
            'score': self.score,
            'issues': self.issues[:3],
            'suggestions': self.suggestions[:3],
        }


@dataclass
class StyleCalibrationReport:
    overall_score: float = 0.0
    venue_alignment: float = 0.0
    dimensions: List[DimensionScore] = field(default_factory=list)
    top_suggestions: List[str] = field(default_factory=list)
    target_venue: str = ''
    summary: str = ''
    timestamp: str = ''

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            'overall_score': round(self.overall_score, 1),
            'venue_alignment': round(self.venue_alignment, 1),
            'dimensions': [d.to_dict() for d in self.dimensions],
            'top_suggestions': self.top_suggestions,
            'target_venue': self.target_venue,
            'summary': self.summary,
            'timestamp': self.timestamp,
        }


STYLE_ANALYSIS_PROMPT = '''你是一位学术写作顾问。请分析以下论文片段的写作风格。

目标会议/期刊：{target_venue}
该会议的典型风格特征：{venue_style}

请从以下维度分析并评分（0-100）：
1. formality（正式度）：学术写作的正式程度，是否避免了口语化表达
2. clarity（清晰度）：表达是否清晰直接，没有歧义
3. conciseness（简洁性）：是否避免了冗余和啰唆的表达
4. technical_precision（技术严谨度）：术语使用是否准确规范
5. narrative_flow（叙事流畅度）：段落过渡是否自然，逻辑是否连贯
6. self_promotion（自我推销度）：是否过分夸大贡献，或者过于谦虚

论文内容：
{content}

输出JSON格式：
{{
    "formality": {{"score": 0-100, "issues": ["问题1"], "suggestions": ["建议1"]}},
    "clarity": {{"score": 0-100, "issues": [], "suggestions": []}},
    "conciseness": {{"score": 0-100, "issues": [], "suggestions": []}},
    "technical_precision": {{"score": 0-100, "issues": [], "suggestions": []}},
    "narrative_flow": {{"score": 0-100, "issues": [], "suggestions": []}},
    "self_promotion": {{"score": 0-100, "issues": [], "suggestions": []}},
    "top_suggestions": ["最重要的改进建议1", "建议2", "建议3"],
    "venue_alignment": 0-100
}}
'''


class StyleCalibrator:
    def __init__(self, llm):
        self.llm = llm

    def calibrate(self, content: str, target_venue: str = '') -> StyleCalibrationReport:
        if not target_venue or target_venue not in VENUE_STYLES:
            target_venue = 'NeurIPS'

        venue_info = VENUE_STYLES[target_venue]
        prompt = STYLE_ANALYSIS_PROMPT.format(
            target_venue=target_venue,
            venue_style=venue_info.get('style', 'balanced'),
            content=content[:5000],
        )

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw = extract_text_from_response(response)
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}
        except Exception:
            data = {}

        dims = ['formality', 'clarity', 'conciseness', 'technical_precision',
                'narrative_flow', 'self_promotion']

        dimensions = []
        total_score = 0.0
        for d in dims:
            ddata = data.get(d, {})
            score = max(0, min(100, ddata.get('score', 70)))
            total_score += score
            dimensions.append(DimensionScore(
                dimension=d,
                score=score,
                issues=ddata.get('issues', []),
                suggestions=ddata.get('suggestions', []),
            ))

        venue_alignment = data.get('venue_alignment', total_score / len(dims))
        overall_score = total_score / len(dims) if dims else 70.0

        return StyleCalibrationReport(
            overall_score=overall_score,
            venue_alignment=venue_alignment,
            dimensions=dimensions,
            top_suggestions=data.get('top_suggestions', [])[:5],
            target_venue=target_venue,
            summary=f'Style calibration: {overall_score:.0f}/100 (venue alignment: {venue_alignment:.0f}/100)',
        )
