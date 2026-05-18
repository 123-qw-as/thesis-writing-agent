"""
Unit tests for score_trajectory.py - Score Trajectory & Regression Detection
"""
import pytest
from src.evaluation.score_trajectory import ScoreTrajectory, ScoreSnapshot


class TestScoreSnapshot:
    def test_default_timestamp(self):
        s = ScoreSnapshot(iteration=1, scores={'quality': 85.0})
        assert s.iteration == 1
        assert s.scores == {'quality': 85.0}
        assert s.timestamp


class TestScoreTrajectory:
    def test_empty_init(self):
        t = ScoreTrajectory()
        assert t.snapshots == []

    def test_record(self):
        t = ScoreTrajectory()
        t.record(1, {'originality': 80, 'methodology': 75})
        assert len(t.snapshots) == 1
        assert t.snapshots[0].iteration == 1

    def test_get_latest_empty(self):
        t = ScoreTrajectory()
        assert t.get_latest() is None

    def test_get_latest(self):
        t = ScoreTrajectory()
        t.record(1, {'q': 80})
        t.record(2, {'q': 90})
        assert t.get_latest() == {'q': 90}

    def test_get_best_empty(self):
        t = ScoreTrajectory()
        assert t.get_best() == {}

    def test_get_best(self):
        t = ScoreTrajectory()
        t.record(1, {'a': 70, 'b': 80})
        t.record(2, {'a': 85, 'b': 75})
        t.record(3, {'a': 80, 'b': 90})
        best = t.get_best()
        assert best['a'] == 85
        assert best['b'] == 90

    def test_get_delta_insufficient(self):
        t = ScoreTrajectory()
        t.record(1, {'q': 80})
        assert t.get_delta('q') == 0.0

    def test_get_delta_positive(self):
        t = ScoreTrajectory()
        t.record(1, {'q': 80})
        t.record(2, {'q': 90})
        assert t.get_delta('q') == 10.0

    def test_get_delta_negative(self):
        t = ScoreTrajectory()
        t.record(1, {'q': 90})
        t.record(2, {'q': 80})
        assert t.get_delta('q') == -10.0

    def test_regression_detected_none(self):
        t = ScoreTrajectory()
        assert t.regression_detected() == []

    def test_regression_detected_single_iteration(self):
        t = ScoreTrajectory()
        t.record(1, {'q': 80})
        assert t.regression_detected() == []

    def test_regression_detected_clear(self):
        t = ScoreTrajectory()
        t.record(1, {'a': 70, 'b': 75})
        t.record(2, {'a': 80, 'b': 78})
        assert t.regression_detected() == []

    def test_regression_detected_found(self):
        t = ScoreTrajectory()
        t.record(1, {'a': 85, 'b': 80})
        t.record(2, {'a': 70, 'b': 85})
        regressed = t.regression_detected(threshold=0.3)
        assert 'a' in regressed
        assert 'b' not in regressed

    def test_regression_detected_custom_threshold(self):
        t = ScoreTrajectory()
        t.record(1, {'a': 85, 'b': 80})
        t.record(2, {'a': 84, 'b': 79})
        assert t.regression_detected(threshold=1.0) == []
        regressed = t.regression_detected(threshold=0.5)
        assert 'b' in regressed

    def test_summary_empty(self):
        t = ScoreTrajectory()
        assert 'No trajectory' in t.summary()

    def test_summary_with_data(self):
        t = ScoreTrajectory()
        t.record(1, {'originality': 80, 'methodology': 75})
        s = t.summary()
        assert 'Iteration 1' in s
        assert 'originality' in s

    def test_summary_with_regression(self):
        t = ScoreTrajectory()
        t.record(1, {'a': 85, 'b': 80})
        t.record(2, {'a': 70, 'b': 85})
        s = t.summary()
        assert 'Regression detected' in s

    def test_to_dict(self):
        t = ScoreTrajectory()
        t.record(1, {'a': 85})
        d = t.to_dict()
        assert len(d) == 1
        assert d[0]['iteration'] == 1
        assert d[0]['scores']['a'] == 85
