"""
Unit tests for passport.py - Material Passport
"""
import pytest
from src.evaluation.passport import MaterialPassport, PassportEntry


class TestMaterialPassport:
    def test_record_creates_entry(self):
        p = MaterialPassport()
        entry = p.record('writing', 'WriterAgent', 'content')
        assert len(p.entries) == 1
        assert entry.phase == 'writing'
        assert entry.agent == 'WriterAgent'
        assert entry.content_hash
        assert entry.version_label == 'v1.0'

    def test_record_with_all_fields(self):
        p = MaterialPassport()
        entry = p.record('review', 'ReviewerAgent', 'paper content',
                         verification_status='PASS', score=85.0,
                         upstream=['hash1', 'hash2'], issues=['minor issue'],
                         notes='test run')
        assert entry.verification_status == 'PASS'
        assert entry.score == 85.0
        assert entry.upstream == ['hash1', 'hash2']
        assert entry.issues == ['minor issue']
        assert entry.notes == 'test run'

    def test_version_increment(self):
        p = MaterialPassport()
        p.record('writing', 'W1', 'v1')
        p.record('writing', 'W2', 'v2')
        p.record('review', 'R1', 'v3')
        entry = p.record('writing', 'W3', 'v4')
        assert entry.version_label == 'v3.0'

    def test_get_entry_finds_latest(self):
        p = MaterialPassport()
        p.record('writing', 'W1', 'v1')
        p.record('review', 'R1', 'v2')
        p.record('writing', 'W2', 'v3')
        entry = p.get_entry('writing')
        assert entry.agent == 'W2'

    def test_get_entry_not_found(self):
        p = MaterialPassport()
        assert p.get_entry('nonexistent') is None

    def test_get_all_by_phase(self):
        p = MaterialPassport()
        p.record('writing', 'W1', 'v1')
        p.record('review', 'R1', 'v2')
        p.record('writing', 'W2', 'v3')
        entries = p.get_all_by_phase('writing')
        assert len(entries) == 2

    def test_get_latest_hash(self):
        p = MaterialPassport()
        e = p.record('writing', 'W1', 'content')
        assert p.get_latest_hash('writing') == e.content_hash
        assert p.get_latest_hash('nonexistent') is None

    def test_verify_chain_ok(self):
        p = MaterialPassport()
        e1 = p.record('writing', 'W1', 'v1')
        p.record('review', 'R1', 'v2', upstream=[e1.content_hash])
        issues = p.verify_chain()
        assert len(issues) == 0

    def test_verify_chain_broken(self):
        p = MaterialPassport()
        p.record('review', 'R1', 'v2', upstream=['nonexistent_hash'])
        issues = p.verify_chain()
        assert len(issues) == 1

    def test_summary(self):
        p = MaterialPassport()
        p.record('writing', 'W1', 'content')
        summary = p.summary()
        assert 'Material Passport' in summary
        assert 'W1' in summary

    def test_to_dict(self):
        p = MaterialPassport()
        e = p.record('writing', 'W1', 'content')
        d = p.to_dict()
        assert len(d) == 1
        assert d[0]['phase'] == 'writing'
        assert d[0]['content_hash'] == e.content_hash
