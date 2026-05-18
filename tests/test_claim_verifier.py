"""
Unit tests for claim_verifier.py - Claim Verification
"""
import pytest
from src.evaluation.claim_verifier import (
    ClaimVerifier, ClaimVerificationReport, Claim,
)
from tests.conftest import MockLLM, MockResponse


class TestClaim:
    def test_defaults(self):
        c = Claim(claim_type='citation', text='Smith et al.')
        assert c.verification_status == 'UNVERIFIED'
        assert c.confidence == 0

    def test_to_dict(self):
        c = Claim(claim_type='citation', text='Smith et al.', verification_status='VERIFIED_TRUE', confidence=90)
        d = c.to_dict()
        assert d['claim_type'] == 'citation'
        assert d['verification_status'] == 'VERIFIED_TRUE'


class TestClaimVerificationReport:
    def test_passed(self):
        r = ClaimVerificationReport(verdict='PASS')
        assert r.passed is True

    def test_failed(self):
        claims = [Claim('citation', 'fake', 'VERIFIED_FALSE', 90)]
        r = ClaimVerificationReport(claims=claims, verdict='FAIL')
        assert r.passed is False

    def test_auto_timestamp(self):
        r = ClaimVerificationReport()
        assert r.timestamp


class TestClaimVerifier:
    def test_verify_all_true(self):
        v = ClaimVerifier(MockLLM())
        v._extract_claims = lambda content: [
            {'type': 'citation', 'text': 'Smith et al. (2023)', 'severity': 'medium'},
            {'type': 'experimental_result', 'text': '95.5% accuracy', 'severity': 'high'},
        ]
        v._verify_single = lambda claim: {'status': 'VERIFIED_TRUE', 'confidence': 90, 'evidence': 'Known result'}
        report = v.verify('content')
        assert report.total_claims == 2
        assert report.verdict == 'PASS'

    def test_verify_with_false_claim(self):
        v = ClaimVerifier(MockLLM())
        v._extract_claims = lambda content: [
            {'type': 'citation', 'text': 'Fake citation', 'severity': 'high'},
        ]
        v._verify_single = lambda claim: {'status': 'VERIFIED_FALSE', 'confidence': 85, 'evidence': 'Fake'}
        report = v.verify('content')
        assert report.verdict == 'NEEDS_REVIEW'

    def test_verify_extraction_error(self):
        class FailLLM:
            def invoke(self, messages):
                raise Exception('LLM error')
        v = ClaimVerifier(FailLLM())
        report = v.verify('content')
        assert report.total_claims == 0

    def test_verify_single_error(self):
        v = ClaimVerifier(MockLLM())
        v._extract_claims = lambda content: [{'type': 'citation', 'text': 'some claim', 'severity': 'low'}]
        v._verify_single = lambda claim: {'status': 'UNVERIFIABLE', 'confidence': 0, 'evidence': 'Error'}
        report = v.verify('content')
        assert report.claims[0].verification_status == 'UNVERIFIABLE'

    def test_fail_on_three_false(self):
        v = ClaimVerifier(MockLLM())
        v._extract_claims = lambda content: [{'type': 'citation', 'text': f'fake{i}', 'severity': 'high'} for i in range(5)]
        v._verify_single = lambda claim: {'status': 'VERIFIED_FALSE', 'confidence': 90, 'evidence': 'Fake'}
        report = v.verify('content')
        assert report.verdict == 'FAIL'
