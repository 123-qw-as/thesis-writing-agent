"""
R&R Traceability Matrix - 审稿意见→修改→验证追踪
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TraceabilityItem:
    concern_id: str
    description: str
    source: str
    priority: str  # must_fix / should_fix / consider
    severity: str  # critical / major / minor
    authors_claim: str = ''
    revision_location: str = ''
    verified: str = 'PENDING'  # PENDING / YES / PARTIAL / NO / CANNOT_VERIFY
    status: str = 'NOT_ADDRESSED'  # FULLY / PARTIALLY / NOT_ADDRESSED / MADE_WORSE

    def to_dict(self) -> dict:
        return {
            'concern_id': self.concern_id,
            'description': self.description,
            'source': self.source,
            'priority': self.priority,
            'severity': self.severity,
            'authors_claim': self.authors_claim,
            'revision_location': self.revision_location,
            'verified': self.verified,
            'status': self.status,
        }


class RRTraceabilityMatrix:
    def __init__(self):
        self.items: List[TraceabilityItem] = []
        self.created_at: str = datetime.now().isoformat()
        self.updated_at: str = self.created_at

    def from_roadmap(self, roadmap: List[dict]):
        self.items = []
        for item in roadmap:
            self.items.append(TraceabilityItem(
                concern_id=item.get('id', f'REV-{len(self.items)+1:03d}'),
                description=item.get('description', ''),
                source=item.get('source', ''),
                priority=item.get('priority', 'consider'),
                severity=item.get('severity', 'minor'),
            ))
        self.updated_at = datetime.now().isoformat()

    def update_from_response(self, response_items: List[dict]):
        response_map = {r.get('roadmap_item_id', ''): r for r in response_items}
        for item in self.items:
            resp = response_map.get(item.concern_id)
            if resp:
                item.authors_claim = resp.get('author_response', '')
                item.revision_location = resp.get('change_location', '')
                status_map = {
                    'RESOLVED': 'FULLY_ADDRESSED',
                    'DELIBERATE_LIMITATION': 'PARTIALLY_ADDRESSED',
                    'UNRESOLVABLE': 'NOT_ADDRESSED',
                    'REVIEWER_DISAGREE': 'NOT_ADDRESSED',
                }
                item.status = status_map.get(resp.get('status', ''), 'NOT_ADDRESSED')
                item.verified = 'PENDING'
        self.updated_at = datetime.now().isoformat()

    def verify(self) -> List[str]:
        inconsistencies = []
        for item in self.items:
            if item.priority == 'must_fix' and item.status == 'NOT_ADDRESSED':
                inconsistencies.append(f'{item.concern_id}: must_fix 未处理')
            if item.status == 'FULLY_ADDRESSED' and not item.revision_location:
                inconsistencies.append(f'{item.concern_id}: 标记为已修复但无修改位置')
        if inconsistencies:
            self.updated_at = datetime.now().isoformat()
        return inconsistencies

    def summary(self) -> str:
        if not self.items:
            return 'No traceability items'
        counts = {'FULLY_ADDRESSED': 0, 'PARTIALLY_ADDRESSED': 0, 'NOT_ADDRESSED': 0, 'MADE_WORSE': 0}
        for item in self.items:
            counts[item.status] = counts.get(item.status, 0) + 1
        lines = [
            f'R&R Traceability Matrix ({len(self.items)} items):',
            f'  Fully addressed: {counts["FULLY_ADDRESSED"]}',
            f'  Partially addressed: {counts["PARTIALLY_ADDRESSED"]}',
            f'  Not addressed: {counts["NOT_ADDRESSED"]}',
            f'  Made worse: {counts["MADE_WORSE"]}',
        ]
        return '\n'.join(lines)

    def to_dict(self) -> dict:
        return {
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'items': [i.to_dict() for i in self.items],
            'summary': self.summary(),
        }
