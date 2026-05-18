"""
Unit tests for style_calibrator.py - Style Calibration
"""
import pytest
from src.evaluation.style_calibrator import (
    StyleCalibrator, StyleCalibrationReport, DimensionScore, VENUE_STYLES,
)
from tests.conftest import MockLLM, MockResponse


ANALYSIS_JSON = '''{
    "formality": {"score": 85, "issues": ["Some informal phrases"], "suggestions": ["Use passive voice more"]},
    "clarity": {"score": 90, "issues": [], "suggestions": []},
    "conciseness": {"score": 75, "issues": ["Wordy paragraphs"], "suggestions": ["Cut adverbs"]},
    "technical_precision": {"score": 88, "issues": [], "suggestions": []},
    "narrative_flow": {"score": 80, "issues": ["Abrupt transitions"], "suggestions": ["Add transition words"]},
    "self_promotion": {"score": 82, "issues": [], "suggestions": []},
    "top_suggestions": ["Reduce wordiness", "Improve transitions", "Use more passive voice"],
    "venue_alignment": 82
}'''

INCOMPLETE_JSON = '''{
    "formality": {"score": 70},
    "venue_alignment": 65
}'''


class TestDimensionScore:
    def test_defaults(self):
        d = DimensionScore(dimension='formality', score=85.0)
        assert d.dimension == 'formality'
        assert d.score == 85.0

    def test_to_dict(self):
        d = DimensionScore(dimension='formality', score=85.0,
                           issues=['too informal'], suggestions=['be formal'])
        dd = d.to_dict()
        assert dd['score'] == 85.0
        assert len(dd['issues']) == 1


class TestStyleCalibrationReport:
    def test_defaults(self):
        r = StyleCalibrationReport()
        assert r.overall_score == 0.0
        assert r.timestamp

    def test_to_dict(self):
        dims = [DimensionScore('formality', 85)]
        r = StyleCalibrationReport(overall_score=82.0, dimensions=dims, target_venue='NeurIPS')
        d = r.to_dict()
        assert d['overall_score'] == 82.0
        assert d['target_venue'] == 'NeurIPS'


class TestStyleCalibrator:
    def test_calibrate_default_venue(self):
        llm = MockLLM(response=ANALYSIS_JSON)
        s = StyleCalibrator(llm)
        report = s.calibrate('Some paper content')
        assert report.target_venue == 'NeurIPS'
        assert len(report.dimensions) == 6
        assert len(report.top_suggestions) == 3

    def test_calibrate_specific_venue(self):
        llm = MockLLM(response=ANALYSIS_JSON)
        s = StyleCalibrator(llm)
        report = s.calibrate('Content', target_venue='CVPR')
        assert report.target_venue == 'CVPR'

    def test_calibrate_scores(self):
        llm = MockLLM(response=ANALYSIS_JSON)
        s = StyleCalibrator(llm)
        report = s.calibrate('Content')
        assert report.overall_score > 0
        assert report.venue_alignment > 0

    def test_calibrate_incomplete_json(self):
        llm = MockLLM(response=INCOMPLETE_JSON)
        s = StyleCalibrator(llm)
        report = s.calibrate('Content')
        assert len(report.dimensions) == 6
        assert report.overall_score > 0

    def test_calibrate_unknown_venue_defaults(self):
        llm = MockLLM(response='invalid json')
        s = StyleCalibrator(llm)
        report = s.calibrate('Content', target_venue='UNKNOWN')
        assert report.overall_score > 0

    def test_venue_styles_defined(self):
        assert 'NeurIPS' in VENUE_STYLES
        assert 'CVPR' in VENUE_STYLES
        assert 'ACL' in VENUE_STYLES
        assert VENUE_STYLES['NeurIPS']['style'] == 'technical_rigorous'
