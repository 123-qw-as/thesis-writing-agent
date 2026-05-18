"""
Evaluation Module - 中间输出质量评估与反馈改进系统
"""
from .judge import LLMJudge
from .error_analyzer import ErrorAnalyzer, Error, ErrorCategory, ErrorReport
from .feedback_loop import FeedbackLoop
from .orchestrator import EvaluationOrchestrator
from .rendering_auditor import RenderingAuditor, RenderingReport, FallbackEvent
from .docx_validator import DocxValidator, DocxAnalysis, validate_docx
from .rubrics import (
    LiteratureRubric, MethodRubric, ExperimentRubric,
    WritingRubric, FigureRubric, DocxRubric
)
from .integrity_gate import IntegrityGate, IntegrityReport, ModeCheckResult
from .traceability import RRTraceabilityMatrix, TraceabilityItem
from .sprint_contract import SprintManager, SprintContract, SprintTask, SprintRetrospective
from .claim_verifier import ClaimVerifier, ClaimVerificationReport, Claim
from .style_calibrator import StyleCalibrator, StyleCalibrationReport
from .anti_leakage import AntiLeakageChecker, AntiLeakageReport, LeakIssue

__all__ = [
    'LLMJudge', 'ErrorAnalyzer', 'Error', 'ErrorCategory', 'ErrorReport',
    'FeedbackLoop', 'EvaluationOrchestrator',
    'RenderingAuditor', 'RenderingReport', 'FallbackEvent',
    'DocxValidator', 'DocxAnalysis', 'validate_docx',
    'LiteratureRubric', 'MethodRubric', 'ExperimentRubric',
    'WritingRubric', 'FigureRubric', 'DocxRubric',
    'IntegrityGate', 'IntegrityReport', 'ModeCheckResult',
    'RRTraceabilityMatrix', 'TraceabilityItem',
    'SprintManager', 'SprintContract', 'SprintTask', 'SprintRetrospective',
    'ClaimVerifier', 'ClaimVerificationReport', 'Claim',
    'StyleCalibrator', 'StyleCalibrationReport',
    'AntiLeakageChecker', 'AntiLeakageReport', 'LeakIssue',
]