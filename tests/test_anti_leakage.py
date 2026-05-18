"""
Unit tests for anti_leakage.py - Anti-Leakage Checker
"""
import pytest
from src.evaluation.anti_leakage import (
    AntiLeakageChecker, AntiLeakageReport, LeakIssue, LEAK_TYPES,
)
from tests.conftest import MockLLM, MockResponse


CLEAN_JSON = '''{
    "issues": [],
    "score": 95,
    "summary": "No leakage detected"
}'''

WITH_ISSUES_JSON = '''{
    "issues": [
        {
            "leak_type": "DATA_CONTAMINATION",
            "description": "Test data may overlap with training data",
            "severity": "critical",
            "confidence": 75,
            "location": "Experiment section",
            "suggestion": "Check for duplicates"
        }
    ],
    "score": 45,
    "summary": "Potential data contamination"
}'''


class TestLeakIssue:
    def test_defaults(self):
        i = LeakIssue(leak_type='DATA_CONTAMINATION', name='Data Contamination',
                      description='test leak', severity='critical', confidence=80)
        assert i.leak_type == 'DATA_CONTAMINATION'

    def test_to_dict(self):
        i = LeakIssue(leak_type='FEATURE_LEAKAGE', name='Feature Leakage',
                      description='feature leak', severity='major', confidence=70)
        d = i.to_dict()
        assert d['leak_type'] == 'FEATURE_LEAKAGE'


class TestAntiLeakageReport:
    def test_passed_no_critical(self):
        r = AntiLeakageReport(verdict='PASS')
        assert r.passed is True

    def test_failed_with_critical(self):
        issues = [LeakIssue('DATA_CONTAMINATION', 'Contamination', 'desc', 'critical', 80)]
        r = AntiLeakageReport(issues=issues, verdict='FAIL')
        assert r.passed is False

    def test_to_dict(self):
        r = AntiLeakageReport(score=85, verdict='PASS', summary='Clean')
        d = r.to_dict()
        assert d['passed'] is True
        assert d['score'] == 85


class TestAntiLeakageChecker:
    def test_check_clean(self):
        llm = MockLLM(response=CLEAN_JSON)
        c = AntiLeakageChecker(llm)
        report = c.check('content')
        assert report.verdict == 'PASS'
        assert report.score >= 90

    def test_check_with_issues(self):
        llm = MockLLM(response=WITH_ISSUES_JSON)
        c = AntiLeakageChecker(llm)
        report = c.check('content')
        assert len(report.issues) > 0
        assert report.verdict == 'NEEDS_REVIEW'

    def test_check_fallback(self):
        class FailLLM:
            def invoke(self, messages):
                raise Exception('API error')
        c = AntiLeakageChecker(FailLLM())
        report = c.check('content')
        assert report.verdict == 'PASS_WITH_CAVEAT'

    def test_check_invalid_json(self):
        llm = MockLLM(response='not json')
        c = AntiLeakageChecker(llm)
        report = c.check('content')
        assert report.verdict == 'PASS_WITH_CAVEAT'

    def test_issue_has_name_from_types(self):
        llm = MockLLM(response=WITH_ISSUES_JSON)
        c = AntiLeakageChecker(llm)
        report = c.check('content')
        assert report.issues[0].name == 'Data Contamination'

    def test_leak_types_defined(self):
        types = [l[0] for l in LEAK_TYPES]
        assert 'DATA_CONTAMINATION' in types
        assert 'FEATURE_LEAKAGE' in types
        assert 'TEMPORAL_LEAKAGE' in types
        assert len(LEAK_TYPES) == 8
