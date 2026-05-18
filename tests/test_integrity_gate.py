"""
Unit tests for integrity_gate.py - Integrity Gate (7-mode AI failure check)
"""
import pytest
from src.evaluation.integrity_gate import (
    IntegrityGate, IntegrityReport, ModeCheckResult, FAILURE_MODES,
)
from tests.conftest import MockLLM, MockResponse


GOOD_JSON = '''{
    "modes": [
        {"mode_id": "M1", "status": "CLEAR", "confidence": 95, "evidence": "No bugs found", "severity": "low"},
        {"mode_id": "M2", "status": "CLEAR", "confidence": 90, "evidence": "Citations look real", "severity": "low"},
        {"mode_id": "M3", "status": "CLEAR", "confidence": 85, "evidence": "Results consistent", "severity": "low"},
        {"mode_id": "M4", "status": "CLEAR", "confidence": 80, "evidence": "Rigorous approach", "severity": "low"},
        {"mode_id": "M5", "status": "CLEAR", "confidence": 90, "evidence": "No false insights", "severity": "low"},
        {"mode_id": "M6", "status": "CLEAR", "confidence": 85, "evidence": "Methodology sound", "severity": "low"},
        {"mode_id": "M7", "status": "CLEAR", "confidence": 88, "evidence": "No frame lock", "severity": "low"}
    ],
    "issues": [],
    "summary": "All checks passed"
}'''

SUSPECTED_JSON = '''{
    "modes": [
        {"mode_id": "M1", "status": "CLEAR", "confidence": 90, "evidence": "OK", "severity": "low"},
        {"mode_id": "M2", "status": "SUSPECTED", "confidence": 60, "evidence": "Some citations look suspicious", "severity": "medium"},
        {"mode_id": "M3", "status": "CLEAR", "confidence": 85, "evidence": "OK", "severity": "low"},
        {"mode_id": "M4", "status": "SUSPECTED", "confidence": 55, "evidence": "Potential shortcuts", "severity": "medium"},
        {"mode_id": "M5", "status": "CLEAR", "confidence": 90, "evidence": "OK", "severity": "low"},
        {"mode_id": "M6", "status": "CLEAR", "confidence": 85, "evidence": "OK", "severity": "low"},
        {"mode_id": "M7", "status": "CLEAR", "confidence": 88, "evidence": "OK", "severity": "low"}
    ],
    "issues": ["Citations need verification"],
    "summary": "Minor issues found"
}'''

FAIL_JSON = '''{
    "modes": [
        {"mode_id": "M1", "status": "SUSPECTED", "confidence": 70, "evidence": "Implementation bug likely", "severity": "critical"},
        {"mode_id": "M2", "status": "SUSPECTED", "confidence": 80, "evidence": "Hallucinated citations", "severity": "critical"},
        {"mode_id": "M3", "status": "SUSPECTED", "confidence": 75, "evidence": "Results may be fabricated", "severity": "critical"},
        {"mode_id": "M4", "status": "CLEAR", "confidence": 85, "evidence": "OK", "severity": "low"},
        {"mode_id": "M5", "status": "CLEAR", "confidence": 90, "evidence": "OK", "severity": "low"},
        {"mode_id": "M6", "status": "CLEAR", "confidence": 85, "evidence": "OK", "severity": "low"},
        {"mode_id": "M7", "status": "CLEAR", "confidence": 88, "evidence": "OK", "severity": "low"}
    ],
    "issues": ["Multiple critical issues"],
    "summary": "Integrity check failed"
}'''


class TestModeCheckResult:
    def test_passed_when_clear(self):
        m = ModeCheckResult('M1', 'Bug', 'CLEAR', 90)
        assert m.passed is True

    def test_passed_when_suspected(self):
        m = ModeCheckResult('M1', 'Bug', 'SUSPECTED', 60)
        assert m.passed is False

    def test_to_dict(self):
        m = ModeCheckResult('M1', 'Bug', 'CLEAR', 90, 'No bugs', 'low')
        d = m.to_dict()
        assert d['mode_id'] == 'M1'
        assert d['status'] == 'CLEAR'


class TestIntegrityReport:
    def test_passed_pass(self):
        r = IntegrityReport(overall_verdict='PASS', modes=[])
        assert r.passed is True

    def test_passed_with_conditions(self):
        r = IntegrityReport(overall_verdict='PASS_WITH_CONDITIONS', modes=[])
        assert r.passed is True

    def test_failed(self):
        r = IntegrityReport(overall_verdict='FAIL', modes=[])
        assert r.passed is False

    def test_suspected_modes(self):
        modes = [
            ModeCheckResult('M1', 'Bug', 'CLEAR', 90),
            ModeCheckResult('M2', 'Citation', 'SUSPECTED', 60),
        ]
        r = IntegrityReport(overall_verdict='PASS_WITH_CONDITIONS', modes=modes)
        assert len(r.suspected_modes) == 1
        assert r.suspected_modes[0].mode_id == 'M2'

    def test_auto_timestamp(self):
        r = IntegrityReport(overall_verdict='PASS', modes=[])
        assert r.timestamp

    def test_to_dict(self):
        modes = [ModeCheckResult('M1', 'Bug', 'CLEAR', 90)]
        r = IntegrityReport(overall_verdict='PASS', modes=modes)
        d = r.to_dict()
        assert d['overall_verdict'] == 'PASS'
        assert d['passed'] is True


class TestIntegrityGate:
    def test_verify_pass(self):
        llm = MockLLM(response=GOOD_JSON)
        check = IntegrityGate(llm)
        report = check.verify('content')
        assert report.overall_verdict == 'PASS'
        assert report.passed is True
        assert len(report.issues) == 0

    def test_verify_pass_with_conditions(self):
        llm = MockLLM(response=SUSPECTED_JSON)
        check = IntegrityGate(llm)
        report = check.verify('content')
        assert report.overall_verdict == 'PASS_WITH_CONDITIONS'

    def test_verify_fail(self):
        llm = MockLLM(response=FAIL_JSON)
        check = IntegrityGate(llm)
        report = check.verify('content')
        assert report.overall_verdict == 'FAIL'
        assert report.passed is False

    def test_verify_fallback_on_error(self):
        class FailLLM:
            def invoke(self, messages):
                raise Exception('LLM error')
        check = IntegrityGate(FailLLM())
        report = check.verify('content')
        assert report.overall_verdict == 'PASS_WITH_CONDITIONS'
        assert len(report.issues) > 0

    def test_verify_invalid_json(self):
        llm = MockLLM(response='not json')
        check = IntegrityGate(llm)
        report = check.verify('content')
        assert report.overall_verdict == 'PASS_WITH_CONDITIONS'
