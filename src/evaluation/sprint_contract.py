"""
Sprint Contract - 修订Sprint管理
每个修订轮次是一个Sprint，带有范围、预算、时间线和回顾
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


SprintState = str  # PLANNING | ACTIVE | REVIEW | COMPLETED | CANCELLED


@dataclass
class SprintTask:
    task_id: str
    description: str
    source: str  # e.g. 'R1', 'DA'
    severity: str  # critical / major / minor
    priority: str  # must_fix / should_fix / consider
    effort_estimate: str  # small / medium / large
    status: str = 'PENDING'  # PENDING → IN_PROGRESS → DONE → VERIFIED
    assigned_to: str = ''
    completed_at: str = ''
    verification_result: str = ''
    llm_cost_estimate: float = 0.0
    notes: str = ''

    def to_dict(self) -> dict:
        return {
            'task_id': self.task_id,
            'description': self.description,
            'source': self.source,
            'severity': self.severity,
            'priority': self.priority,
            'effort_estimate': self.effort_estimate,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'completed_at': self.completed_at,
            'llm_cost_estimate': self.llm_cost_estimate,
            'notes': self.notes[:100],
        }


@dataclass
class SprintContract:
    sprint_id: str
    name: str
    start_date: str = ''
    deadline: str = ''
    budget_llm_calls: int = 10
    budget_iterations: int = 3
    scope_focus: str = 'ALL'  # ALL | METHODOLOGY | WRITING | EXPERIMENTS | ...
    goals: List[str] = field(default_factory=list)
    tasks: List[SprintTask] = field(default_factory=list)
    state: SprintState = 'PLANNING'

    @property
    def progress(self) -> float:
        if not self.tasks:
            return 0.0
        done = sum(1 for t in self.tasks if t.status == 'DONE')
        return done / len(self.tasks)

    @property
    def is_overdue(self) -> bool:
        if not self.deadline:
            return False
        try:
            dl = datetime.fromisoformat(self.deadline)
            return datetime.now() > dl and self.state != 'COMPLETED'
        except ValueError:
            return False

    @property
    def days_remaining(self) -> int:
        if not self.deadline:
            return 0
        try:
            dl = datetime.fromisoformat(self.deadline)
            delta = dl - datetime.now()
            return max(0, delta.days)
        except ValueError:
            return 0

    @property
    def summary(self) -> str:
        return (f'Sprint {self.sprint_id} [{self.state}]: '
                f'{len(self.tasks)} tasks, {self.progress:.0%} done, '
                f'{self.days_remaining}d left')

    def to_dict(self) -> dict:
        return {
            'sprint_id': self.sprint_id,
            'name': self.name,
            'start_date': self.start_date,
            'deadline': self.deadline,
            'budget_llm_calls': self.budget_llm_calls,
            'budget_iterations': self.budget_iterations,
            'scope_focus': self.scope_focus,
            'goals': self.goals[:5],
            'tasks': [t.to_dict() for t in self.tasks],
            'state': self.state,
            'progress': round(self.progress, 2),
            'is_overdue': self.is_overdue,
            'days_remaining': self.days_remaining,
            'summary': self.summary,
        }


@dataclass
class SprintRetrospective:
    sprint_id: str
    completed_tasks: int = 0
    carried_over: List[str] = field(default_factory=list)
    lessons: List[str] = field(default_factory=list)
    blocker_frequency: Dict[str, int] = field(default_factory=dict)
    actual_llm_cost: float = 0.0
    actual_iterations: int = 0
    satisfaction_score: int = 0  # 1-5
    notes: str = ''

    def to_dict(self) -> dict:
        return {
            'sprint_id': self.sprint_id,
            'completed_tasks': self.completed_tasks,
            'carried_over': self.carried_over,
            'lessons': self.lessons,
            'blocker_frequency': self.blocker_frequency,
            'actual_llm_cost': self.actual_llm_cost,
            'actual_iterations': self.actual_iterations,
            'satisfaction_score': self.satisfaction_score,
            'notes': self.notes[:200],
        }


class SprintManager:
    def __init__(self):
        self.sprints: List[SprintContract] = []
        self.retrospectives: List[SprintRetrospective] = []
        self._sprint_counter = 0

    def plan_sprint(self, name: str = '', roadmap: Optional[List[dict]] = None,
                    focus: str = 'ALL', llm_budget: int = 10,
                    iter_budget: int = 3, days: int = 7) -> SprintContract:
        self._sprint_counter += 1
        sid = f'SP{self._sprint_counter:03d}'
        now = datetime.now()
        start = now.isoformat()
        deadline = (now + timedelta(days=days)).isoformat()
        if not name:
            name = f'Sprint {self._sprint_counter}: {focus}'

        contract = SprintContract(
            sprint_id=sid,
            name=name,
            start_date=start,
            deadline=deadline,
            budget_llm_calls=llm_budget,
            budget_iterations=iter_budget,
            scope_focus=focus,
            state='PLANNING',
        )

        if roadmap:
            contract.tasks = self._roadmap_to_tasks(roadmap)

        self.sprints.append(contract)
        return contract

    def start_sprint(self, sprint_id: str) -> bool:
        contract = self._find(sprint_id)
        if not contract or contract.state != 'PLANNING':
            return False
        contract.state = 'ACTIVE'
        return True

    def complete_task(self, sprint_id: str, task_id: str,
                      result: str = '') -> bool:
        task = self._find_task(sprint_id, task_id)
        if not task:
            return False
        task.status = 'DONE'
        task.completed_at = datetime.now().isoformat()
        task.verification_result = result
        return True

    def close_sprint(self, sprint_id: str) -> Optional[SprintRetrospective]:
        contract = self._find(sprint_id)
        if not contract or contract.state not in ('ACTIVE', 'REVIEW'):
            return None
        contract.state = 'COMPLETED'
        done = sum(1 for t in contract.tasks if t.status == 'DONE')
        carried = [t.description for t in contract.tasks if t.status != 'DONE']

        retro = SprintRetrospective(
            sprint_id=sprint_id,
            completed_tasks=done,
            carried_over=carried,
            actual_iterations=contract.budget_iterations,
        )
        self.retrospectives.append(retro)
        return retro

    def current_sprint(self) -> Optional[SprintContract]:
        active = [s for s in self.sprints if s.state in ('PLANNING', 'ACTIVE', 'REVIEW')]
        if active:
            return active[0]
        return None

    def _find(self, sprint_id: str) -> Optional[SprintContract]:
        for s in self.sprints:
            if s.sprint_id == sprint_id:
                return s
        return None

    def _find_task(self, sprint_id: str, task_id: str) -> Optional[SprintTask]:
        contract = self._find(sprint_id)
        if not contract:
            return None
        for t in contract.tasks:
            if t.task_id == task_id:
                return t
        return None

    def _roadmap_to_tasks(self, roadmap: List[dict]) -> List[SprintTask]:
        tasks = []
        for idx, item in enumerate(roadmap):
            sev = item.get('severity', 'minor')
            effort = {'critical': 'large', 'major': 'medium', 'minor': 'small'}.get(sev, 'small')
            llm_cost = {'critical': 3.0, 'major': 2.0, 'minor': 0.5}.get(sev, 0.5)
            tasks.append(SprintTask(
                task_id=item.get('id', f'T{idx+1:03d}'),
                description=item.get('description', ''),
                source=item.get('source', ''),
                severity=sev,
                priority=item.get('priority', 'consider'),
                effort_estimate=effort,
                llm_cost_estimate=llm_cost,
            ))
        return tasks

    def summary(self) -> str:
        if not self.sprints:
            return 'No sprints planned'
        lines = ['Sprint Manager Summary:']
        for s in self.sprints:
            lines.append(f'  {s.summary}')
        line = '\n'.join(lines)
        return line
