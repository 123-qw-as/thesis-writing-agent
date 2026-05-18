"""
Review Orchestrator - 审稿流程协调器
按顺序执行 R1→R2→DA→EIC，输出完整审稿报告
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

from .base_reviewer import ReviewerReport
from .field_reviewer import FieldReviewer
from .devils_advocate import DevilsAdvocate
from .editor_in_chief import EditorInChief, EditorialDecision


@dataclass
class ReviewPackage:
    reports: List[ReviewerReport]
    decision: EditorialDecision
    topic: str = ''

    def to_dict(self) -> dict:
        return {
            'topic': self.topic,
            'reports': [r.to_dict() for r in self.reports],
            'decision': self.decision.to_dict(),
        }

    def summary(self) -> str:
        lines = [
            f'Review Summary for: {self.topic}',
            f'Decision: {self.decision.decision} (score: {self.decision.avg_score:.1f}/5)',
            f'Consensus: {self.decision.consensus_level}',
            f'Confidence: {self.decision.confidence}%',
            '',
            'Reviewers:',
        ]
        for r in self.reports:
            status = '✓' if r.passed else '✗'
            lines.append(f'  [{status}] {r.reviewer_id:5s} ({r.role:25s}) avg={r.avg_score:.1f} conf={r.confidence}%')
        lines.extend(['', 'Revision Roadmap:'])
        for item in self.decision.revision_roadmap[:8]:
            lines.append(f'  [{item["priority"]}] {item["id"]}: {item["description"][:80]}')
        return '\n'.join(lines)


class ReviewOrchestrator:
    def __init__(self, llm):
        self.llm = llm
        self.reports: List[ReviewerReport] = []

    def conduct_review(self, content: str, topic: str = '',
                       context: Optional[dict] = None) -> ReviewPackage:
        r1 = FieldReviewer(self.llm, 'R1', 'methodology')
        r2 = FieldReviewer(self.llm, 'R2', 'domain')
        da = DevilsAdvocate(self.llm)
        eic = EditorInChief(self.llm)

        print('  [Review] R1 (Methodology) reviewing...')
        report_r1 = r1.review(content, context)
        print(f'    avg={report_r1.avg_score:.1f} conf={report_r1.confidence}%')

        print('  [Review] R2 (Domain) reviewing...')
        report_r2 = r2.review(content, context)
        print(f'    avg={report_r2.avg_score:.1f} conf={report_r2.confidence}%')

        print('  [Review] DA (Devil\'s Advocate) reviewing...')
        report_da = da.review(content, context)
        print(f'    avg={report_da.avg_score:.1f} conf={report_da.confidence}%')

        print('  [Review] EIC synthesizing...')
        reports = [report_r1, report_r2, report_da]
        decision = eic.make_decision(reports)
        print(f'    Decision: {decision.decision} ({decision.avg_score:.1f}/5)')

        self.reports = reports
        return ReviewPackage(
            reports=reports,
            decision=decision,
            topic=topic,
        )
