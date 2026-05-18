"""
Unit tests for base_reviewer.py - BaseReviewer, ReviewerReport
"""
import pytest
from src.evaluation.reviewers.base_reviewer import BaseReviewer, ReviewerReport
from tests.conftest import MockLLM


class TestReviewerReport:
    def test_defaults(self):
        r = ReviewerReport(reviewer_id='R1', role='Reviewer', scores={'q': 4})
        assert r.reviewer_id == 'R1'
        assert r.passed is True

    def test_passed_false_when_below_3(self):
        r = ReviewerReport(reviewer_id='R1', role='Reviewer',
                           scores={'q': 2, 'w': 1})
        assert r.passed is False

    def test_avg_score_calculation(self):
        r = ReviewerReport(reviewer_id='R1', role='Reviewer',
                           scores={'a': 80, 'b': 90, 'c': 70})
        assert r.avg_score == 80.0

    def test_avg_score_empty(self):
        r = ReviewerReport(reviewer_id='R1', role='Reviewer', scores={})
        assert r.avg_score == 0.0

    def test_to_dict(self):
        r = ReviewerReport(reviewer_id='R1', role='Methodology Reviewer',
                           scores={'originality': 4, 'methodology': 5, 'evidence': 3, 'coherence': 4, 'writing': 5},
                           strengths=['Good method'],
                           weaknesses=[{'description': 'Weak lit', 'severity': 'minor'}],
                           questions=['Why?'],
                           overall_comment='Solid paper',
                           confidence=85)
        d = r.to_dict()
        assert d['reviewer_id'] == 'R1'
        assert d['avg_score'] == 4.2
        assert d['passed'] is True


class TestBaseReviewer:
    def test_init_has_default_dimensions(self):
        r = BaseReviewer(MockLLM(), 'TEST', 'Tester')
        assert r.reviewer_id == 'TEST'
        assert r.role == 'Tester'
        assert len(r.dimensions) == 5
        assert r.dimensions[0]['name'] == 'originality'

    def test_requires_subclass_review(self):
        r = BaseReviewer(MockLLM(), 'T1', 'Tester')
        with pytest.raises(NotImplementedError):
            r.review('content')
