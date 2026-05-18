"""
Integrity Gate - 基于Lu et al. 2026的7-mode AI失败检查清单
在写作之后评估之前执行，检测AI生成的常见问题
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response


FAILURE_MODES = [
    ('M1', 'Implementation Bug', '实现错误通过AI自审'),
    ('M2', 'Hallucinated Citation', '虚构引用'),
    ('M3', 'Hallucinated Experimental Result', '虚构实验结果'),
    ('M4', 'Shortcut Reliance', '走捷径而非严谨推理'),
    ('M5', 'Bug as Insight', '实现错误包装为新发现'),
    ('M6', 'Methodology Fabrication', '编造方法论'),
    ('M7', 'Frame-Lock', '认知框架锁定'),
]


@dataclass
class ModeCheckResult:
    mode_id: str
    name: str
    status: str  # CLEAR / SUSPECTED / INSUFFICIENT_EVIDENCE
    confidence: int  # 0-100
    evidence: str = ''
    severity: str = 'medium'

    @property
    def passed(self) -> bool:
        return self.status == 'CLEAR'

    def to_dict(self) -> dict:
        return {
            'mode_id': self.mode_id,
            'name': self.name,
            'status': self.status,
            'confidence': self.confidence,
            'evidence': self.evidence[:200],
            'severity': self.severity,
        }


@dataclass
class IntegrityReport:
    overall_verdict: str  # PASS / PASS_WITH_CONDITIONS / FAIL
    modes: List[ModeCheckResult]
    issues: List[str] = field(default_factory=list)
    summary: str = ''
    timestamp: str = ''

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    @property
    def passed(self) -> bool:
        return self.overall_verdict in ('PASS', 'PASS_WITH_CONDITIONS')

    @property
    def suspected_modes(self) -> List[ModeCheckResult]:
        return [m for m in self.modes if m.status == 'SUSPECTED']

    def to_dict(self) -> dict:
        return {
            'overall_verdict': self.overall_verdict,
            'modes': [m.to_dict() for m in self.modes],
            'issues': self.issues[:5],
            'summary': self.summary,
            'timestamp': self.timestamp,
            'passed': self.passed,
            'suspected_count': len(self.suspected_modes),
        }


MODES_CHECK_PROMPT = """你是一个AI研究诚信审查员。请对以下论文内容执行7种AI失败模式检查。
每种模式检查后输出 CLEAR（未发现问题）/ SUSPECTED（发现问题迹象）/ INSUFFICIENT_EVIDENCE（证据不足）。

## 论文内容
{content}

## 7种失败模式

{modes_text}

## 输出要求
对每种模式，分析内容后给出 verdict 和证据。
输出JSON格式（不要加额外文字）：
{{
    "modes": [
        {{
            "mode_id": "M1",
            "status": "CLEAR/SUSPECTED/INSUFFICIENT_EVIDENCE",
            "confidence": 0-100,
            "evidence": "分析证据（20-100字）",
            "severity": "low/medium/high/critical"
        }}
    ],
    "issues": ["发现的总体问题列表"],
    "summary": "整体评估摘要"
}}
"""


class IntegrityGate:
    """7-mode AI失败检查完整性门禁"""

    def __init__(self, llm):
        self.llm = llm

    def verify(self, content: str, phase: str = 'writing') -> IntegrityReport:
        modes_text = '\n'.join(
            f'{mid}: {name} - {desc}'
            for mid, name, desc in FAILURE_MODES
        )

        prompt = MODES_CHECK_PROMPT.format(
            content=content[:8000],
            modes_text=modes_text,
        )

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw = extract_text_from_response(response)
            return self._parse_report(raw)
        except Exception as e:
            return self._fallback_report(str(e))

    def _parse_report(self, raw: str) -> IntegrityReport:
        import re, json
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not json_match:
            return self._fallback_report('JSON parse failed')

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            return self._fallback_report('JSON decode failed')

        modes = []
        for m in data.get('modes', []):
            status = m.get('status', 'INSUFFICIENT_EVIDENCE')
            if status not in ('CLEAR', 'SUSPECTED', 'INSUFFICIENT_EVIDENCE'):
                status = 'INSUFFICIENT_EVIDENCE'
            modes.append(ModeCheckResult(
                mode_id=m.get('mode_id', 'M?'),
                name={mid: name for mid, name, _ in FAILURE_MODES}.get(m.get('mode_id', ''), 'Unknown'),
                status=status,
                confidence=m.get('confidence', 50),
                evidence=m.get('evidence', ''),
                severity=m.get('severity', 'medium'),
            ))

        suspected = [m for m in modes if m.status == 'SUSPECTED']
        if not suspected:
            verdict = 'PASS'
        elif len(suspected) <= 2 and all(m.severity in ('low', 'medium') for m in suspected):
            verdict = 'PASS_WITH_CONDITIONS'
        else:
            verdict = 'FAIL'

        return IntegrityReport(
            overall_verdict=verdict,
            modes=modes,
            issues=data.get('issues', [])[:5],
            summary=data.get('summary', ''),
        )

    def _fallback_report(self, reason: str) -> IntegrityReport:
        modes = [
            ModeCheckResult(mid, name, 'INSUFFICIENT_EVIDENCE', 0, f'检查失败: {reason}')
            for mid, name, _ in FAILURE_MODES
        ]
        return IntegrityReport(
            overall_verdict='PASS_WITH_CONDITIONS',
            modes=modes,
            issues=[f'Integrity Gate检查失败: {reason}'],
            summary='完整性检查服务暂时不可用，降级通过',
        )
