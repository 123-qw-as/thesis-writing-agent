"""
Devil's Advocate - 对抗性审稿人
专找漏洞和反例，防止确认偏误
"""

import json
import re
from typing import Dict, Optional
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from .base_reviewer import BaseReviewer, ReviewerReport


class DevilsAdvocate(BaseReviewer):
    """对抗性审稿人 - 专找论文的漏洞和假设缺陷"""

    def __init__(self, llm, reviewer_id: str = 'DA'):
        super().__init__(llm, reviewer_id, 'Devil\'s Advocate')

    def _build_prompt(self, content: str, context: Optional[dict] = None) -> str:
        dim_text = '\n'.join(
            f'  - {d["label"]}({d["name"]}): {d["criterion"]}'
            for d in self.dimensions
        )
        context_text = ''
        if context:
            context_text = '\n## 上下文\n' + json.dumps(context, ensure_ascii=False, indent=2)

        return f"""你是一位**Devil's Advocate（对抗性审稿人）**。

你的独特职责是：
1. 挑战论文的基本假设，而非仅仅攻击论证细节
2. 寻找被忽略的反例和替代解释
3. 指出确认偏误 (confirmation bias) 的痕迹
4. 检查是否有框架锁定 (frame-lock) 问题——即是否只在一个预设框架内思考
5. 验证结论是否超出了证据所能支撑的范围

规则：
- 每次攻击必须评分1-5: ≤3分表示该攻击仍有反驳空间，必须坚持立场
- 连续两次concession（承认对方的反驳有效）需要合理解释
- 如果发现论文有框架锁定问题，必须在weaknesses中标记

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
    "strengths": ["优点1"],
    "weaknesses": [{{"description": "批判性意见", "severity": "critical/major/minor", "type": "assumption/evidence/frame-lock/confirmation-bias"}}],
    "questions": ["挑战性问题"],
    "overall_comment": "对抗性审稿总结",
    "confidence": 置信度0-100,
    "frame_lock_detected": true/false,
    "concession_score": 分数1-5
}}"""

    def review(self, content: str, context: Optional[dict] = None) -> ReviewerReport:
        prompt = self._build_prompt(content, context)
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw = extract_text_from_response(response)
            return self._parse_report(raw)
        except Exception as e:
            return ReviewerReport(
                reviewer_id=self.reviewer_id, role=self.role,
                scores={'originality': 3, 'methodology': 3, 'evidence': 3, 'coherence': 3, 'writing': 3},
                weaknesses=[{'description': f'DA审稿出错: {e}', 'severity': 'critical'}],
                questions=['LLM审稿服务暂时不可用，请手动审查论文假设'],
                overall_comment='对抗性审稿未完成',
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
        weaknesses = data.get('weaknesses', [])
        frame_lock = data.get('frame_lock_detected', False)
        if frame_lock:
            weaknesses.append({
                'description': '论文可能存在框架锁定 (frame-lock) 问题，仅在预设假设框架内推理',
                'severity': 'major',
                'type': 'frame-lock',
            })
        return ReviewerReport(
            reviewer_id=self.reviewer_id,
            role=self.role,
            scores=scores,
            strengths=data.get('strengths', []),
            weaknesses=weaknesses,
            questions=data.get('questions', []),
            overall_comment=data.get('overall_comment', ''),
            confidence=data.get('confidence', 80),
        )
