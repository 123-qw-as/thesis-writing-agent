"""
Unit tests for reviewers - FieldReviewer, DevilsAdvocate, EditorInChief, ReviewOrchestrator
"""
import pytest
from src.evaluation.reviewers.base_reviewer import ReviewerReport
from src.evaluation.reviewers.field_reviewer import FieldReviewer
from src.evaluation.reviewers.devils_advocate import DevilsAdvocate
from src.evaluation.reviewers.editor_in_chief import EditorInChief, EditorialDecision
from src.evaluation.reviewers.orchestrator import ReviewOrchestrator, ReviewPackage
from tests.conftest import MockLLM, MockResponse


def make_mock_llm(json_str: str):
    return MockLLM(response=json_str)


class TestFieldReviewer:
    def test_init(self):
        llm = make_mock_llm('{"scores":{}}')
        r = FieldReviewer(llm, 'R1', 'methodology')
        assert r.reviewer_id == 'R1'
        assert r.focus == 'methodology'
        assert '方法论' in r.role

    def test_init_domain(self):
        llm = make_mock_llm('{"scores":{}}')
        r = FieldReviewer(llm, 'R2', 'domain')
        assert r.focus == 'domain'
        assert '领域' in r.role

    def test_parse_report_valid(self):
        llm = make_mock_llm('{"scores":{}}')
        raw = '''{
            "scores": {"originality": 4, "methodology": 5, "evidence": 3, "coherence": 4, "writing": 5},
            "strengths": ["Good novelty", "Solid experiments"],
            "weaknesses": [{"description": "Limited discussion", "severity": "minor"}],
            "questions": ["Why only one dataset?"],
            "overall_comment": "Interesting work",
            "confidence": 85
        }'''
        r = FieldReviewer(llm, 'R1', 'methodology')
        report = r._parse_report(raw)
        assert report.scores['originality'] == 4
        assert report.scores['methodology'] == 5
        assert 'Good novelty' in report.strengths
        assert report.confidence == 85

    def test_parse_report_clamps_scores(self):
        llm = make_mock_llm('{"scores":{}}')
        raw = '{"scores": {"originality": 10, "methodology": -1}}'
        r = FieldReviewer(llm, 'R1', 'methodology')
        report = r._parse_report(raw)
        assert report.scores['originality'] == 5
        assert report.scores['methodology'] == 1

    def test_review_fallback_on_error(self):
        class FailLLM:
            def invoke(self, messages):
                raise Exception('API down')
        r = FieldReviewer(FailLLM(), 'R1', 'methodology')
        report = r.review('content')
        assert report.reviewer_id == 'R1'
        assert report.confidence == 30

    def test_default_dimensions(self):
        llm = make_mock_llm('{}')
        r = FieldReviewer(llm, 'R1', 'methodology')
        assert len(r.dimensions) == 5


class TestDevilsAdvocate:
    def test_init(self):
        llm = make_mock_llm('{}')
        da = DevilsAdvocate(llm)
        assert da.reviewer_id == 'DA'
        assert 'Devil' in da.role

    def test_parse_report_with_frame_lock(self):
        llm = make_mock_llm('{}')
        raw = '''{
            "scores": {"originality": 3, "methodology": 2, "evidence": 3, "coherence": 4, "writing": 4},
            "weaknesses": [{"description": "Weak assumption", "severity": "major", "type": "assumption"}],
            "overall_comment": "Challenging paper",
            "confidence": 90,
            "frame_lock_detected": true,
            "concession_score": 3
        }'''
        da = DevilsAdvocate(llm)
        report = da._parse_report(raw)
        assert report.scores['methodology'] == 2
        types = [w.get('type') for w in report.weaknesses]
        assert 'frame-lock' in types

    def test_parse_report_valid(self):
        llm = make_mock_llm('{}')
        raw = '''{
            "scores": {"originality": 4, "methodology": 4, "evidence": 3, "coherence": 4, "writing": 4},
            "strengths": ["Clear research question"],
            "weaknesses": [],
            "overall_comment": "Good but needs more rigor",
            "confidence": 80,
            "frame_lock_detected": false,
            "concession_score": 4
        }'''
        da = DevilsAdvocate(llm)
        report = da._parse_report(raw)
        assert len(report.weaknesses) == 0
        assert report.scores['originality'] == 4

    def test_review_fallback(self):
        class FailLLM:
            def invoke(self, messages):
                raise Exception('DA fail')
        da = DevilsAdvocate(FailLLM())
        report = da.review('content')
        assert report.reviewer_id == 'DA'
        assert len(report.weaknesses) == 1
        assert 'DA审稿出错' in report.weaknesses[0]['description']
        assert report.confidence == 30


class TestEditorInChief:
    def test_init(self):
        llm = make_mock_llm('{}')
        eic = EditorInChief(llm)
        assert eic.reviewer_id == 'EIC'

    def test_make_decision_accept(self):
        llm = make_mock_llm('{}')
        eic = EditorInChief(llm)
        reports = [
            ReviewerReport('R1', 'Methodology', {'originality': 5, 'methodology': 5, 'evidence': 5, 'coherence': 4, 'writing': 5}),
            ReviewerReport('R2', 'Domain', {'originality': 4, 'methodology': 5, 'evidence': 5, 'coherence': 5, 'writing': 4}),
        ]
        d = eic.make_decision(reports)
        assert d.decision == 'Accept'
        assert d.consensus_level == 'CONSENSUS'
        assert d.avg_score >= 4.5

    def test_make_decision_reject(self):
        llm = make_mock_llm('{}')
        eic = EditorInChief(llm)
        reports = [
            ReviewerReport('R1', 'Methodology', {'originality': 1, 'methodology': 1, 'evidence': 1, 'coherence': 1, 'writing': 2}),
        ]
        d = eic.make_decision(reports)
        assert d.decision == 'Reject'

    def test_make_decision_empty(self):
        llm = make_mock_llm('{}')
        eic = EditorInChief(llm)
        d = eic.make_decision([])
        assert d.avg_score == 0.0
        assert d.consensus_level == 'NO_REVIEWS'

    def test_build_roadmap_priority_order(self):
        llm = make_mock_llm('{}')
        eic = EditorInChief(llm)
        reports = [
            ReviewerReport('R1', 'Reviewer', scores={},
                           weaknesses=[
                               {'description': 'Critical bug', 'severity': 'critical'},
                               {'description': 'Minor typo', 'severity': 'minor'},
                           ]),
        ]
        d = eic.make_decision(reports)
        roadmap = d.revision_roadmap
        assert len(roadmap) == 2
        assert roadmap[0]['priority'] == 'must_fix'

    def test_consensus_split(self):
        llm = make_mock_llm('{}')
        eic = EditorInChief(llm)
        reports = [
            ReviewerReport('R1', 'Reviewer', {'q': 5, 'w': 5, 'e': 5, 'r': 5, 't': 5}),
            ReviewerReport('R2', 'Reviewer', {'q': 1, 'w': 1, 'e': 1, 'r': 1, 't': 1}),
        ]
        d = eic.make_decision(reports)
        assert d.consensus_level in ('SPLIT', 'DA-CRITICAL')

    def test_editorial_decision_to_dict(self):
        d = EditorialDecision(decision='Accept', confidence=85, avg_score=4.2,
                              consensus_level='CONSENSUS',
                              revision_roadmap=[{'id': 'REV-001', 'description': 'Fix', 'priority': 'must_fix'}],
                              summary='Good paper')
        dd = d.to_dict()
        assert dd['decision'] == 'Accept'
        assert dd['avg_score'] == 4.2
        assert dd['confidence'] == 85
        assert len(dd['revision_roadmap']) == 1


class TestReviewPackage:
    def test_report_strengths_aggregation(self):
        reports = [
            ReviewerReport('R1', 'Reviewer', {},
                           strengths=['Good method'], weaknesses=[]),
        ]
        d = EditorialDecision(decision='Accept', confidence=80, avg_score=4.0,
                              consensus_level='CONSENSUS',
                              strengths_summary=['Good method'])
        pkg = ReviewPackage(reports=reports, decision=d, topic='Test Topic')
        assert pkg.topic == 'Test Topic'
        assert pkg.decision.decision == 'Accept'

    def test_to_dict(self):
        reports = [
            ReviewerReport('R1', 'Reviewer', scores={'q': 4}),
        ]
        d = EditorialDecision(decision='Accept', confidence=80, avg_score=4.0,
                              consensus_level='CONSENSUS')
        pkg = ReviewPackage(reports=reports, decision=d, topic='Test')
        dd = pkg.to_dict()
        assert 'decision' in dd
        assert len(dd['reports']) == 1
