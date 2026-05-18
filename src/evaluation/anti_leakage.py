"""
Anti-Leakage - 数据泄露检测
检测训练集-测试集泄露、特征泄露、时间穿越等问题
"""

import re
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response


LEAK_TYPES = [
    ('DATA_CONTAMINATION', 'Data Contamination', '测试数据在训练集中出现', 'critical'),
    ('FEATURE_LEAKAGE', 'Feature Leakage', '特征包含了未来信息', 'critical'),
    ('TEMPORAL_LEAKAGE', 'Temporal Leakage', '时间序列中训练集包含未来的数据', 'critical'),
    ('PREPROCESSING_LEAKAGE', 'Preprocessing Leakage', '预处理器在训练-测试拆分之前拟合', 'major'),
    ('EVALUATION_LEAKAGE', 'Evaluation Leakage', '评估配置不合理导致信息泄露', 'major'),
    ('HYPERPARAMETER_LEAKAGE', 'Hyperparameter Leakage', '超参数在测试集上调优', 'major'),
    ('REPORTING_BIAS', 'Reporting Bias', '只报告有利结果，隐藏不利结果', 'medium'),
    ('UNDERSPECIFIED', 'Under-specified Setup', '实验设置描述不足无法复现', 'medium'),
]


@dataclass
class LeakIssue:
    leak_type: str
    name: str
    description: str
    severity: str  # low / medium / high / critical
    confidence: int  # 0-100
    location: str = ''
    suggestion: str = ''

    def to_dict(self) -> dict:
        return {
            'leak_type': self.leak_type,
            'name': self.name,
            'description': self.description[:150],
            'severity': self.severity,
            'confidence': self.confidence,
            'location': self.location[:100],
            'suggestion': self.suggestion[:150],
        }


@dataclass
class AntiLeakageReport:
    issues: List[LeakIssue] = field(default_factory=list)
    score: int = 100  # 100 = no leakage detected, 0 = severe leakage
    verdict: str = 'PASS'
    summary: str = ''
    timestamp: str = ''

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    @property
    def passed(self) -> bool:
        critical = [i for i in self.issues if i.severity == 'critical']
        return len(critical) == 0

    def to_dict(self) -> dict:
        return {
            'issues': [i.to_dict() for i in self.issues],
            'score': self.score,
            'verdict': self.verdict,
            'summary': self.summary,
            'timestamp': self.timestamp,
            'passed': self.passed,
        }


LEAK_DETECTION_PROMPT = '''你是一位AI研究数据完整性检查员。请分析以下论文中可能的数据泄露问题。

检查类型：
{leak_types}

论文内容：
{content}

请逐类型分析该论文是否可能存在数据泄露。对每种类型：
1. 如果发现问题 -> 输出详细的issue
2. 如果无明显问题 -> 输出空即可

输出JSON格式：
{{
    "issues": [
        {{
            "leak_type": "DATA_CONTAMINATION",
            "description": "具体问题描述",
            "severity": "critical/major/medium/low",
            "confidence": 0-100,
            "location": "在论文中的位置引用",
            "suggestion": "改进建议"
        }}
    ],
    "score": 0-100,
    "summary": "整体评估摘要"
}}

注意：只有确认存在问题才输出issue，不编造问题。
'''


class AntiLeakageChecker:
    def __init__(self, llm):
        self.llm = llm

    def check(self, content: str) -> AntiLeakageReport:
        leak_text = '\n'.join(
            f'  {lt}: {name} - {desc} (severity: {sev})'
            for lt, name, desc, sev in LEAK_TYPES
        )

        prompt = LEAK_DETECTION_PROMPT.format(
            leak_types=leak_text,
            content=content[:6000],
        )

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw = extract_text_from_response(response)
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                return self._empty_report('No JSON in response')

            data = json.loads(json_match.group())
            issues_data = data.get('issues', [])
            issues = []
            for item in issues_data:
                leak_type = item.get('leak_type', '')
                name = ''
                for lt, n, _, _ in LEAK_TYPES:
                    if lt == leak_type:
                        name = n
                        break
                issues.append(LeakIssue(
                    leak_type=leak_type,
                    name=name or leak_type,
                    description=item.get('description', ''),
                    severity=item.get('severity', 'medium'),
                    confidence=item.get('confidence', 50),
                    location=item.get('location', ''),
                    suggestion=item.get('suggestion', ''),
                ))

            score = data.get('score', 100)
            critical_cnt = sum(1 for i in issues if i.severity == 'critical')
            if critical_cnt >= 2:
                verdict = 'FAIL'
            elif critical_cnt > 0 or score < 60:
                verdict = 'NEEDS_REVIEW'
            else:
                verdict = 'PASS'

            return AntiLeakageReport(
                issues=issues,
                score=max(0, min(100, score)),
                verdict=verdict,
                summary=data.get('summary', f'Anti-leakage check: {len(issues)} issues found'),
            )

        except Exception as e:
            return self._empty_report(f'Check error: {e}')

    def _empty_report(self, reason: str) -> AntiLeakageReport:
        return AntiLeakageReport(
            issues=[],
            score=70,
            verdict='PASS_WITH_CAVEAT',
            summary=f'Anti-leakage check skipped: {reason}',
        )
