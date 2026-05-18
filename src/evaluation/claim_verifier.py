"""
Claim Verification - 论文事实性声明核查
验证论文中引用的文献、实验数据、方法声明等是否准确一致
"""

import re
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response


@dataclass
class Claim:
    claim_type: str  # citation | experimental_result | methodological_claim | numerical_claim | definitional_claim
    text: str
    verification_status: str = 'UNVERIFIED'  # UNVERIFIED | VERIFIED_TRUE | VERIFIED_FALSE | UNVERIFIABLE | INCONSISTENT
    confidence: int = 0
    evidence: str = ''
    severity: str = 'medium'

    def to_dict(self) -> dict:
        return {
            'claim_type': self.claim_type,
            'text': self.text[:150],
            'verification_status': self.verification_status,
            'confidence': self.confidence,
            'evidence': self.evidence[:200],
            'severity': self.severity,
        }


@dataclass
class ClaimVerificationReport:
    total_claims: int = 0
    claims: List[Claim] = field(default_factory=list)
    problematic_claims: List[Claim] = field(default_factory=list)
    verdict: str = 'PASS'  # PASS | NEEDS_REVIEW | FAIL
    summary: str = ''
    timestamp: str = ''

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    @property
    def passed(self) -> bool:
        false_count = sum(1 for c in self.claims if c.verification_status == 'VERIFIED_FALSE')
        return false_count == 0

    def to_dict(self) -> dict:
        return {
            'total_claims': self.total_claims,
            'claims': [c.to_dict() for c in self.claims],
            'problematic_count': len(self.problematic_claims),
            'verdict': self.verdict,
            'summary': self.summary,
            'timestamp': self.timestamp,
        }


CLAIM_EXTRACTION_PROMPT = """你是一个研究事实核验员。请从以下论文内容中提取所有可验证的事实性声明。

可验证的声明类型包括：
1. citation（文献引用）："Smith et al. (2023) 发现..."
2. experimental_result（实验结果）："我们的方法达到95.2%准确率"
3. methodological_claim（方法声明）："这是首个使用X技术的系统"
4. numerical_claim（数据声明）："数据集包含10万样本"
5. definitional_claim（定义声明）："X在文献中被定义为Y"

输出JSON格式：
{{
    "claims": [
        {{
            "type": "citation",
            "text": "原文引用片段",
            "severity": "low/medium/high/critical"
        }}
    ]
}}
"""

CLAIM_VERIFICATION_PROMPT = """请核验以下学术声明：

声明类型：{claim_type}
声明原文：{claim_text}

请基于你的知识判断其真实性，输出JSON：
{{
    "status": "VERIFIED_TRUE/VERIFIED_FALSE/UNVERIFIABLE/INCONSISTENT",
    "confidence": 0-100,
    "evidence": "判断依据（20-100字）"
}}

注意：
- VERIFIED_TRUE = 确认该声明属实
- VERIFIED_FALSE = 确认该声明有误
- UNVERIFIABLE = 无法确认（缺少公开信息或需要专业领域知识）
- INCONSISTENT = 声明内部不一致或与上下文矛盾
"""


class ClaimVerifier:
    def __init__(self, llm):
        self.llm = llm

    def verify(self, content: str) -> ClaimVerificationReport:
        claims = self._extract_claims(content)
        report = ClaimVerificationReport(total_claims=len(claims))

        for c in claims:
            result = self._verify_single(c)
            cv = Claim(
                claim_type=c['type'],
                text=c['text'],
                severity=c.get('severity', 'medium'),
                verification_status=result.get('status', 'UNVERIFIABLE'),
                confidence=result.get('confidence', 0),
                evidence=result.get('evidence', ''),
            )
            report.claims.append(cv)
            if cv.verification_status in ('VERIFIED_FALSE', 'INCONSISTENT'):
                report.problematic_claims.append(cv)

        false_cnt = sum(1 for c in report.claims if c.verification_status == 'VERIFIED_FALSE')
        inconsistent_cnt = sum(1 for c in report.claims if c.verification_status == 'INCONSISTENT')

        if false_cnt >= 3:
            report.verdict = 'FAIL'
        elif false_cnt > 0 or inconsistent_cnt > 0:
            report.verdict = 'NEEDS_REVIEW'
        else:
            report.verdict = 'PASS'

        report.summary = (
            f'核验{report.total_claims}条声明: '
            f'{sum(1 for c in report.claims if c.verification_status == "VERIFIED_TRUE")}条属实, '
            f'{false_cnt}条有误, '
            f'{inconsistent_cnt}条不一致, '
            f'{sum(1 for c in report.claims if c.verification_status == "UNVERIFIABLE")}条无法确认'
        )
        return report

    def _extract_claims(self, content: str) -> List[dict]:
        try:
            prompt = CLAIM_EXTRACTION_PROMPT.format(content=content[:6000])
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw = extract_text_from_response(response)
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                return []
            data = json.loads(json_match.group())
            return data.get('claims', [])[:20]
        except Exception:
            return []

    def _verify_single(self, claim: dict) -> dict:
        try:
            prompt = CLAIM_VERIFICATION_PROMPT.format(
                claim_type=claim.get('type', 'citation'),
                claim_text=claim.get('text', '')[:500],
            )
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw = extract_text_from_response(response)
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                return {'status': 'UNVERIFIABLE', 'confidence': 0, 'evidence': 'Extraction failed'}
            return json.loads(json_match.group())
        except Exception as e:
            return {'status': 'UNVERIFIABLE', 'confidence': 0, 'evidence': f'Verification error: {e}'}
