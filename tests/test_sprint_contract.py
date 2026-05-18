"""
Unit tests for sprint_contract.py - Sprint Contract & Sprint Manager
"""
import pytest
from src.evaluation.sprint_contract import (
    SprintManager, SprintContract, SprintTask, SprintRetrospective,
)


class TestSprintTask:
    def test_basic(self):
        t = SprintTask(task_id='T001', description='Fix methodology', source='R1',
                       severity='critical', priority='must_fix', effort_estimate='large')
        assert t.task_id == 'T001'
        assert t.status == 'PENDING'

    def test_to_dict(self):
        t = SprintTask(task_id='T001', description='Fix methodology', source='R1',
                       severity='critical', priority='must_fix', effort_estimate='large')
        d = t.to_dict()
        assert d['task_id'] == 'T001'
        assert d['status'] == 'PENDING'


class TestSprintContract:
    def test_defaults(self):
        c = SprintContract(sprint_id='SP001', name='Test Sprint')
        assert c.state == 'PLANNING'
        assert c.progress == 0.0
        assert c.tasks == []

    def test_progress(self):
        c = SprintContract(sprint_id='SP001', name='Test Sprint')
        c.tasks = [
            SprintTask('T1', 'task1', 'R1', 'critical', 'must_fix', 'small', 'DONE'),
            SprintTask('T2', 'task2', 'R1', 'minor', 'consider', 'small'),
        ]
        assert c.progress == 0.5

    def test_progress_no_tasks(self):
        c = SprintContract(sprint_id='SP001', name='Empty')
        assert c.progress == 0.0

    def test_not_overdue_if_no_deadline(self):
        c = SprintContract(sprint_id='SP001', name='No deadline')
        assert c.is_overdue is False

    def test_summary(self):
        c = SprintContract(sprint_id='SP001', name='Test')
        c.tasks = [SprintTask('T1', 't', 'R1', 'minor', 'consider', 'small', 'DONE')]
        s = c.summary
        assert 'SP001' in s
        assert '100%' in s or '1.0' in s

    def test_to_dict(self):
        c = SprintContract(sprint_id='SP001', name='Test')
        d = c.to_dict()
        assert d['sprint_id'] == 'SP001'
        assert d['state'] == 'PLANNING'


class TestSprintManager:
    def test_empty_init(self):
        m = SprintManager()
        assert m.sprints == []
        assert m.current_sprint() is None


class TestSprintManager:
    def test_empty_init(self):
        m = SprintManager()
        assert m.sprints == []
        assert m.current_sprint() is None

    def test_plan_sprint(self):
        m = SprintManager()
        c = m.plan_sprint(name='First Sprint')
        assert c.sprint_id == 'SP001'
        assert c.state == 'PLANNING'
        assert c in m.sprints

    def test_plan_sprint_with_roadmap(self):
        m = SprintManager()
        roadmap = [
            {'id': 'REV-001', 'description': 'Fix X', 'source': 'R1', 'severity': 'critical', 'priority': 'must_fix'},
            {'id': 'REV-002', 'description': 'Add Y', 'source': 'DA', 'severity': 'minor', 'priority': 'consider'},
        ]
        c = m.plan_sprint(name='With Roadmap', roadmap=roadmap)
        assert len(c.tasks) == 2
        assert c.tasks[0].task_id == 'REV-001'
        assert c.tasks[0].effort_estimate == 'large'

    def test_auto_naming(self):
        m = SprintManager()
        c = m.plan_sprint()
        assert 'Sprint' in c.name

    def test_start_sprint(self):
        m = SprintManager()
        c = m.plan_sprint()
        assert m.start_sprint(c.sprint_id) is True
        assert c.state == 'ACTIVE'

    def test_start_sprint_invalid_id(self):
        m = SprintManager()
        assert m.start_sprint('nonexistent') is False

    def test_start_sprint_twice_fails(self):
        m = SprintManager()
        c = m.plan_sprint()
        m.start_sprint(c.sprint_id)
        assert m.start_sprint(c.sprint_id) is False

    def test_complete_task(self):
        m = SprintManager()
        c = m.plan_sprint(name='Test', roadmap=[
            {'id': 'T1', 'description': 'Fix X', 'source': 'R1', 'severity': 'major', 'priority': 'should_fix'},
        ])
        assert m.complete_task(c.sprint_id, 'T1', 'Done') is True
        assert c.tasks[0].status == 'DONE'
        assert c.tasks[0].completed_at

    def test_complete_task_invalid_sprint(self):
        m = SprintManager()
        assert m.complete_task('bad', 'T1') is False

    def test_complete_task_invalid_task(self):
        m = SprintManager()
        c = m.plan_sprint()
        assert m.complete_task(c.sprint_id, 'nonexistent') is False

    def test_close_sprint(self):
        m = SprintManager()
        c = m.plan_sprint(name='Test')
        m.start_sprint(c.sprint_id)
        retro = m.close_sprint(c.sprint_id)
        assert retro is not None
        assert retro.sprint_id == 'SP001'
        assert c.state == 'COMPLETED'

    def test_close_sprint_not_started(self):
        m = SprintManager()
        c = m.plan_sprint()
        assert m.close_sprint(c.sprint_id) is None

    def test_close_sprint_tracks_carryover(self):
        m = SprintManager()
        c = m.plan_sprint(name='Test', roadmap=[
            {'id': 'T1', 'description': 'Done task', 'source': 'R1', 'severity': 'major', 'priority': 'should_fix'},
            {'id': 'T2', 'description': 'Pending task', 'source': 'DA', 'severity': 'minor', 'priority': 'consider'},
        ])
        m.start_sprint(c.sprint_id)
        m.complete_task(c.sprint_id, 'T1')
        retro = m.close_sprint(c.sprint_id)
        assert retro.completed_tasks == 1
        assert 'Pending task' in retro.carried_over

    def test_current_sprint_returns_active(self):
        m = SprintManager()
        c = m.plan_sprint()
        m.start_sprint(c.sprint_id)
        assert m.current_sprint() is c

    def test_current_sprint_prefers_active_over_completed(self):
        m = SprintManager()
        c1 = m.plan_sprint()
        m.start_sprint(c1.sprint_id)
        m.close_sprint(c1.sprint_id)
        c2 = m.plan_sprint()
        m.start_sprint(c2.sprint_id)
        assert m.current_sprint() is c2

    def test_summary_empty(self):
        m = SprintManager()
        assert 'No sprints' in m.summary()

    def test_summary_with_sprints(self):
        m = SprintManager()
        m.plan_sprint(name='Sprint A')
        m.plan_sprint(name='Sprint B')
        s = m.summary()
        assert 'SP001' in s
        assert 'SP002' in s

    def test_sequential_id(self):
        m = SprintManager()
        c1 = m.plan_sprint()
        c2 = m.plan_sprint()
        assert c2.sprint_id == 'SP002'
