"""
Score Trajectory - 跨迭代分数追踪与回归检测
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ScoreSnapshot:
    iteration: int
    scores: Dict[str, float]
    timestamp: str = ''

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ScoreTrajectory:
    def __init__(self):
        self.snapshots: List[ScoreSnapshot] = []

    def record(self, iteration: int, scores: Dict[str, float]):
        self.snapshots.append(ScoreSnapshot(iteration=iteration, scores=dict(scores)))

    def get_latest(self) -> Optional[Dict[str, float]]:
        return self.snapshots[-1].scores if self.snapshots else None

    def get_best(self) -> Dict[str, float]:
        if not self.snapshots:
            return {}
        dims = set()
        for s in self.snapshots:
            dims.update(s.scores.keys())
        best = {}
        for dim in dims:
            best[dim] = max(s.scores.get(dim, 0) for s in self.snapshots)
        return best

    def get_delta(self, dim: str) -> float:
        if len(self.snapshots) < 2:
            return 0.0
        prev = self.snapshots[-2].scores.get(dim, 0)
        curr = self.snapshots[-1].scores.get(dim, 0)
        return curr - prev

    def regression_detected(self, threshold: float = 0.3) -> List[str]:
        if len(self.snapshots) < 2:
            return []
        regressed = []
        prev, curr = self.snapshots[-2], self.snapshots[-1]
        all_dims = set(prev.scores.keys()) | set(curr.scores.keys())
        for dim in all_dims:
            delta = curr.scores.get(dim, 0) - prev.scores.get(dim, 0)
            if delta < -threshold:
                regressed.append(dim)
        return regressed

    def summary(self) -> str:
        if not self.snapshots:
            return 'No trajectory data'
        lines = [f'Score Trajectory ({len(self.snapshots)} iterations):']
        for s in self.snapshots:
            scores_str = ', '.join(f'{k}={v:.2f}' for k, v in sorted(s.scores.items()))
            lines.append(f'  Iteration {s.iteration}: {scores_str}')
        regressed = self.regression_detected()
        if regressed:
            lines.append(f'  Regression detected in: {", ".join(regressed)}')
        return '\n'.join(lines)

    def to_dict(self) -> list:
        return [{'iteration': s.iteration, 'scores': dict(s.scores), 'timestamp': s.timestamp} for s in self.snapshots]
