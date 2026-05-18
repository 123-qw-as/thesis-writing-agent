"""
Unit tests for traceability.py - R&R Traceability Matrix
"""
import pytest
from src.evaluation.traceability import RRTraceabilityMatrix, TraceabilityItem


class TestTraceabilityItem:
    def test_defaults(self):
        item = TraceabilityItem(
            concern_id='REV-001',
            description='Method is not novel',
            source='R1',
            priority='must_fix',
            severity='critical',
        )
        assert item.verified == 'PENDING'
        assert item.status == 'NOT_ADDRESSED'

    def test_to_dict(self):
        item = TraceabilityItem(
            concern_id='REV-001',
            description='Fix methodology',
            source='R1',
            priority='must_fix',
            severity='critical',
        )
        d = item.to_dict()
        assert d['concern_id'] == 'REV-001'
        assert d['priority'] == 'must_fix'


class TestRRTraceabilityMatrix:
    def test_empty_init(self):
        m = RRTraceabilityMatrix()
        assert m.items == []

    def test_from_roadmap(self):
        m = RRTraceabilityMatrix()
        roadmap = [
            {'id': 'REV-001', 'description': 'Fix A', 'source': 'R1',
             'priority': 'must_fix', 'severity': 'critical'},
            {'id': 'REV-002', 'description': 'Fix B', 'source': 'DA',
             'priority': 'consider', 'severity': 'minor'},
        ]
        m.from_roadmap(roadmap)
        assert len(m.items) == 2
        assert m.items[0].concern_id == 'REV-001'
        assert m.items[1].priority == 'consider'

    def test_from_roadmap_empty(self):
        m = RRTraceabilityMatrix()
        m.from_roadmap([])
        assert m.items == []

    def test_update_from_response(self):
        m = RRTraceabilityMatrix()
        m.from_roadmap([
            {'id': 'REV-001', 'description': 'Fix A', 'source': 'R1',
             'priority': 'must_fix', 'severity': 'critical'},
        ])
        responses = [
            {'roadmap_item_id': 'REV-001', 'author_response': 'Fixed in section 3.2',
             'change_location': 'section_3.2', 'status': 'RESOLVED'},
        ]
        m.update_from_response(responses)
        assert m.items[0].authors_claim == 'Fixed in section 3.2'
        assert m.items[0].revision_location == 'section_3.2'
        assert m.items[0].status == 'FULLY_ADDRESSED'

    def test_update_from_response_partial(self):
        m = RRTraceabilityMatrix()
        m.from_roadmap([
            {'id': 'REV-001', 'description': 'Fix A', 'source': 'R1',
             'priority': 'must_fix', 'severity': 'critical'},
        ])
        responses = [
            {'roadmap_item_id': 'REV-001', 'author_response': 'Deliberate limitation',
             'change_location': '', 'status': 'DELIBERATE_LIMITATION'},
        ]
        m.update_from_response(responses)
        assert m.items[0].status == 'PARTIALLY_ADDRESSED'

    def test_update_from_response_unresolvable(self):
        m = RRTraceabilityMatrix()
        m.from_roadmap([
            {'id': 'REV-001', 'description': 'Fix A', 'source': 'R1',
             'priority': 'must_fix', 'severity': 'critical'},
        ])
        responses = [
            {'roadmap_item_id': 'REV-001', 'author_response': 'Cannot fix',
             'change_location': '', 'status': 'UNRESOLVABLE'},
        ]
        m.update_from_response(responses)
        assert m.items[0].status == 'NOT_ADDRESSED'

    def test_update_from_response_no_match(self):
        m = RRTraceabilityMatrix()
        m.from_roadmap([
            {'id': 'REV-001', 'description': 'Fix A', 'source': 'R1',
             'priority': 'must_fix', 'severity': 'critical'},
        ])
        responses = [
            {'roadmap_item_id': 'REV-999', 'author_response': 'N/A',
             'change_location': '', 'status': 'RESOLVED'},
        ]
        m.update_from_response(responses)
        assert m.items[0].status == 'NOT_ADDRESSED'

    def test_verify_no_inconsistencies(self):
        m = RRTraceabilityMatrix()
        m.from_roadmap([
            {'id': 'REV-001', 'description': 'Fix A', 'source': 'R1',
             'priority': 'must_fix', 'severity': 'critical'},
        ])
        m.update_from_response([
            {'roadmap_item_id': 'REV-001', 'author_response': 'Done',
             'change_location': 'section_3', 'status': 'RESOLVED'},
        ])
        issues = m.verify()
        assert len(issues) == 0

    def test_verify_unaddressed_must_fix(self):
        m = RRTraceabilityMatrix()
        m.from_roadmap([
            {'id': 'REV-001', 'description': 'Fix A', 'source': 'R1',
             'priority': 'must_fix', 'severity': 'critical'},
        ])
        issues = m.verify()
        assert len(issues) == 1
        assert 'must_fix' in issues[0]

    def test_verify_resolved_without_location(self):
        m = RRTraceabilityMatrix()
        m.from_roadmap([
            {'id': 'REV-001', 'description': 'Fix A', 'source': 'R1',
             'priority': 'consider', 'severity': 'minor'},
        ])
        m.update_from_response([
            {'roadmap_item_id': 'REV-001', 'author_response': 'Done',
             'change_location': '', 'status': 'RESOLVED'},
        ])
        issues = m.verify()
        assert len(issues) == 1
        assert '无修改位置' in issues[0]

    def test_summary_empty(self):
        m = RRTraceabilityMatrix()
        assert 'No traceability' in m.summary()

    def test_summary(self):
        m = RRTraceabilityMatrix()
        m.from_roadmap([
            {'id': 'REV-001', 'description': 'Fix A', 'source': 'R1',
             'priority': 'must_fix', 'severity': 'critical'},
        ])
        m.update_from_response([
            {'roadmap_item_id': 'REV-001', 'author_response': 'Done',
             'change_location': 'sec3', 'status': 'RESOLVED'},
        ])
        s = m.summary()
        assert '1 items' in s
        assert 'Fully addressed' in s

    def test_to_dict(self):
        m = RRTraceabilityMatrix()
        m.from_roadmap([
            {'id': 'REV-001', 'description': 'Fix A', 'source': 'R1',
             'priority': 'must_fix', 'severity': 'critical'},
        ])
        d = m.to_dict()
        assert d['created_at']
        assert len(d['items']) == 1
