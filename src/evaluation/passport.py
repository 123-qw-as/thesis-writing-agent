"""
Material Passport - 数据血缘追踪
记录每个阶段输出的来源、验证状态和版本信息
"""

import hashlib
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PassportEntry:
    phase: str
    agent: str
    timestamp: str
    content_hash: str
    verification_status: str = 'UNVERIFIED'
    version_label: str = 'v1.0'
    score: Optional[float] = None
    upstream: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    notes: str = ''

    def to_dict(self) -> dict:
        return {
            'phase': self.phase,
            'agent': self.agent,
            'timestamp': self.timestamp,
            'content_hash': self.content_hash,
            'verification_status': self.verification_status,
            'version_label': self.version_label,
            'score': self.score,
            'upstream': self.upstream,
            'issues': self.issues,
            'notes': self.notes,
        }


class MaterialPassport:
    def __init__(self):
        self.entries: List[PassportEntry] = []

    def record(self, phase: str, agent: str, content: Any,
               verification_status: str = 'UNVERIFIED',
               score: Optional[float] = None,
               upstream: Optional[List[str]] = None,
               issues: Optional[List[str]] = None,
               notes: str = '') -> PassportEntry:
        content_str = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()[:12]
        version = f'v{len([e for e in self.entries if e.phase.startswith(phase[:6])]) + 1}.0'

        entry = PassportEntry(
            phase=phase,
            agent=agent,
            timestamp=datetime.now().isoformat(),
            content_hash=content_hash,
            verification_status=verification_status,
            version_label=version,
            score=score,
            upstream=upstream or [],
            issues=issues or [],
            notes=notes,
        )
        self.entries.append(entry)
        return entry

    def get_entry(self, phase_prefix: str) -> Optional[PassportEntry]:
        for e in reversed(self.entries):
            if e.phase.startswith(phase_prefix):
                return e
        return None

    def get_all_by_phase(self, phase: str) -> List[PassportEntry]:
        return [e for e in self.entries if e.phase == phase]

    def get_latest_hash(self, phase_prefix: str) -> Optional[str]:
        entry = self.get_entry(phase_prefix)
        return entry.content_hash if entry else None

    def verify_chain(self) -> List[str]:
        inconsistencies = []
        for i, entry in enumerate(self.entries):
            for dep in entry.upstream:
                found = any(e.content_hash == dep for e in self.entries[:i])
                if not found:
                    inconsistencies.append(f'{entry.phase}: 上游依赖 {dep[:8]} 未找到')
        return inconsistencies

    def summary(self) -> str:
        lines = ['Material Passport Summary:']
        for e in self.entries:
            status_icon = {'PASS': '✓', 'FAIL': '✗', 'UNVERIFIED': '○', 'STALE': '⚠'}.get(e.verification_status, '?')
            lines.append(f'  [{status_icon}] {e.phase:25s} | {e.agent:20s} | {e.version_label:6s} | {e.content_hash[:8]}')
        return '\n'.join(lines)

    def to_dict(self) -> List[dict]:
        return [e.to_dict() for e in self.entries]
