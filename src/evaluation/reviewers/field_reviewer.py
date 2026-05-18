"""
Field Reviewer - 领域审稿人
支持方法论审稿人和领域审稿人两种角色
"""

import json
import re
from typing import Dict, Optional
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from .base_reviewer import BaseReviewer, ReviewerReport


FIELD_PROMPTS = {
    'methodology': '''
你是一位**方法论审稿人**。你的专长是评估研究方法的严谨性、可复现性和技术深度。
重点关注：
- 方法设计是否合理，核心组件是否完整
- 是否有足够的消融实验和对比实验
- 超参数设置、评估指标是否合理
- 基线方法选择和比对是否公平
''',
    'domain': '''
你是一位**领域审稿人**。你的专长是评估该领域内的学术贡献和文献覆盖。
重点关注：
- 是否覆盖了该领域的重要相关工作
- 研究问题是否有理论/实践意义
- 实验结果是否在领域基准上有竞争力
- 讨论是否充分，局限性和未来工作是否提及
''',
}


class FieldReviewer(BaseReviewer):
    def __init__(self, llm, reviewer_id: str, focus: str = 'methodology'):
        focus_label = {'methodology': '方法论审稿人', 'domain': '领域审稿人'}.get(focus, focus)
        super().__init__(llm, reviewer_id, focus_label)
        self.focus = focus
        self._prompt_extra = FIELD_PROMPTS.get(focus, '')

    def _build_prompt(self, content: str, context: Optional[dict] = None) -> str:
        dim_text = '\n'.join(
            f'  - {d["label"]}({d["name"]}): {d["criterion"]}'
            for d in self.dimensions
        )
        context_text = ''
        if context:
            context_text = '\n## 上下文\n' + json.dumps(context, ensure_ascii=False, indent=2)

        return f"""你是一位学术论文审稿人（ID: {self.reviewer_id}, 角色: {self.role}）。
{self._prompt_extra}
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

    def review(self, content: str, context: Optional[dict] = None) -> ReviewerReport:
        prompt = self._build_prompt(content, context)
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw = extract_text_from_response(response)
            parsed = self._parse_report(raw)
            return parsed
        except Exception as e:
            return ReviewerReport(
                reviewer_id=self.reviewer_id, role=self.role,
                scores={'originality': 3, 'methodology': 3, 'evidence': 3, 'coherence': 3, 'writing': 3},
                weaknesses=[{'description': f'审稿过程出错: {e}', 'severity': 'major'}],
                overall_comment='审稿服务暂时不可用',
                confidence=30,
            )

    def _parse_report(self, raw: str) -> ReviewerReport:
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not json_match:
            raise ValueError('No JSON found')
        data = json.loads(json_match.group())
        scores = data.get('scores', {})
        for k in ['originality', 'methodology', 'evidence', 'coherence', 'writing']:
            scores.setdefault(k, 3)
            scores[k] = max(1, min(5, int(scores[k])))
        return ReviewerReport(
            reviewer_id=self.reviewer_id,
            role=self.role,
            scores=scores,
            strengths=data.get('strengths', []),
            weaknesses=data.get('weaknesses', []),
            questions=data.get('questions', []),
            overall_comment=data.get('overall_comment', ''),
            confidence=data.get('confidence', 80),
        )
