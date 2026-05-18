"""
Editor-in-Chief - 主编审稿人
汇总R1/R2/DA的报告，输出最终决策和修订路线图
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from .base_reviewer import BaseReviewer, ReviewerReport


@dataclass
class EditorialDecision:
    decision: str  # Accept / Minor Revision / Major Revision / Reject
    confidence: int  # 0-100
    avg_score: float  # 加权平均
    consensus_level: str  # CONSENSUS / SPLIT / DA-CRITICAL
    revision_roadmap: List[dict] = field(default_factory=list)
    summary: str = ''
    strengths_summary: List[str] = field(default_factory=list)
    weaknesses_summary: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'decision': self.decision,
            'confidence': self.confidence,
            'avg_score': round(self.avg_score, 2),
            'consensus_level': self.consensus_level,
            'revision_roadmap': self.revision_roadmap,
            'summary': self.summary,
            'strengths_summary': self.strengths_summary,
            'weaknesses_summary': self.weaknesses_summary,
        }


DIM_WEIGHTS = {
    'originality': 0.15,
    'methodology': 0.25,
    'evidence': 0.25,
    'coherence': 0.20,
    'writing': 0.15,
}

DECISION_THRESHOLDS = [
    (4.5, 'Accept'),
    (3.5, 'Minor Revision'),
    (2.5, 'Major Revision'),
    (0.0, 'Reject'),
]


class EditorInChief(BaseReviewer):
    def __init__(self, llm):
        super().__init__(llm, 'EIC', 'Editor-in-Chief')

    def make_decision(self, reports: List[ReviewerReport]) -> EditorialDecision:
        avg_scores = self._calc_weighted_average(reports)
        overall = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0

        for threshold, decision in DECISION_THRESHOLDS:
            if overall >= threshold:
                break

        consensus = self._assess_consensus(reports)
        roadmap = self._build_roadmap(reports)
        all_strengths = []
        all_weaknesses = []
        for r in reports:
            all_strengths.extend(r.strengths)
            for w in r.weaknesses:
                desc = w.get('description', str(w))
                sev = w.get('severity', 'minor')
                src = r.reviewer_id
                all_weaknesses.append({'description': desc, 'severity': sev, 'source': src})

        return EditorialDecision(
            decision=decision,
            confidence=int(overall * 20),
            avg_score=overall,
            consensus_level=consensus,
            revision_roadmap=roadmap[:10],
            summary=f'EIC决策: {decision} (综合评分 {overall:.1f}/5, 共识: {consensus})',
            strengths_summary=all_strengths[:5],
            weaknesses_summary=all_weaknesses[:10],
        )

    def review(self, content: str, context: Optional[dict] = None) -> ReviewerReport:
        raise NotImplementedError('EIC use make_decision() instead')

    def _calc_weighted_average(self, reports: List[ReviewerReport]) -> Dict[str, float]:
        if not reports:
            return {}
        dims = ['originality', 'methodology', 'evidence', 'coherence', 'writing']
        result = {}
        for dim in dims:
            weighted = 0.0
            total_w = 0
            for r in reports:
                w = DIM_WEIGHTS.get(dim, 0.2)
                weighted += r.scores.get(dim, 3) * w
                total_w += w
            result[dim] = weighted / total_w if total_w > 0 else 3.0
        return result

    def _assess_consensus(self, reports: List[ReviewerReport]) -> str:
        if not reports:
            return 'NO_REVIEWS'
        scores_by_dim = {}
        for r in reports:
            for dim, score in r.scores.items():
                scores_by_dim.setdefault(dim, []).append(score)
        max_spread = 0
        for dim, scores in scores_by_dim.items():
            spread = max(scores) - min(scores)
            max_spread = max(max_spread, spread)

        if max_spread <= 1:
            return 'CONSENSUS'
        elif max_spread <= 2:
            return 'SPLIT'
        else:
            return 'DA-CRITICAL'

    def _build_roadmap(self, reports: List[ReviewerReport]) -> List[dict]:
        roadmap = []
        idx = 0
        for r in reports:
            for w in r.weaknesses:
                idx += 1
                sev = w.get('severity', 'minor')
                priority = {'critical': 'must_fix', 'major': 'should_fix', 'minor': 'consider'}.get(sev, 'consider')
                roadmap.append({
                    'id': f'REV-{idx:03d}',
                    'description': w.get('description', str(w)),
                    'source': r.reviewer_id,
                    'priority': priority,
                    'type': w.get('type', 'general'),
                    'severity': sev,
                })
        roadmap.sort(key=lambda x: {'must_fix': 0, 'should_fix': 1, 'consider': 2}.get(x['priority'], 3))
        return roadmap
