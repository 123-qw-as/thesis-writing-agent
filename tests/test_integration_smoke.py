"""
Integration Smoke Test - 全项目集成验证
Tests imports, graph creation, pipeline instantiation, and end-to-end module coherency
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

PASS = 0
FAIL = 0

def check(name, ok):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f'  [PASS] {name}')
    else:
        FAIL += 1
        print(f'  [FAIL] {name}')

def section(title):
    print(f'\n{"="*60}')
    print(f'  {title}')
    print(f'{"="*60}')

# ── 1. Core Module Imports ──
section('1. Core Module Imports')
try:
    import src.graph as m; check('src.graph', True)
except Exception as e: check(f'src.graph: {e}', False)

try:
    from src.workflows.research_pipeline import run_full_pipeline, get_pipeline_status
    check('workflows.research_pipeline', True)
except Exception as e: check(f'research_pipeline: {e}', False)

try:
    from src.workflows.enhanced_pipeline import EnhancedResearchPipeline
    check('workflows.enhanced_pipeline', True)
except Exception as e: check(f'enhanced_pipeline: {e}', False)

try:
    from src.workflows.quality_workflow import QualityWorkflow, run_quality_workflow
    check('workflows.quality_workflow', True)
except Exception as e: check(f'quality_workflow: {e}', False)

# ── 2. Agent Imports ──
section('2. Agent Imports')
agents = [
    'literature.agent', 'method.agent', 'experiment.agent',
    'writer.agent', 'reviewer.agent', 'deai.agent',
    'comparison.agent', 'citation.agent', 'consistency.agent',
    'innovation.agent', 'evaluation.agent',
]
for a in agents:
    try:
        __import__(f'src.agents.{a}', fromlist=[''])
        check(f'agents.{a}', True)
    except Exception as e:
        check(f'agents.{a}: {str(e)[:50]}', False)

# ── 3. Tool Imports ──
section('3. Tool Imports')
try:
    from src.tools.aigc_detector import detect_aigc, AIGCDetector
    check('tools.aigc_detector', True)
except Exception as e: check(f'aigc_detector: {e}', False)

try:
    from src.tools.data_verifier import verify_data, DataVerifier
    check('tools.data_verifier', True)
except Exception as e: check(f'data_verifier: {e}', False)

# ── 3b. LLM Config ──
section('3b. LLM Config')
try:
    from src.llm_config import MODEL_REGISTRY, create_llm, auto_select_llm, get_providers, get_recommended_models
    check('llm_config imported', True)
    check(f'  providers: {", ".join(get_providers())}', True)
    check(f'  total models: {len(MODEL_REGISTRY)}', True)
    check(f'  recommended: {", ".join(get_recommended_models().keys())}', True)
except Exception as e: check(f'llm_config: {e}', False)

# ── 4. Evaluation Module (New Modules) ──
section('4. Evaluation Module (New)')
eval_imports = [
    ('judge', 'LLMJudge'),
    ('error_analyzer', 'ErrorAnalyzer, Error, ErrorCategory, ErrorReport'),
    ('feedback_loop', 'FeedbackLoop'),
    ('orchestrator', 'EvaluationOrchestrator'),
    ('rendering_auditor', 'RenderingAuditor, RenderingReport, FallbackEvent'),
    ('docx_validator', 'DocxValidator, DocxAnalysis, validate_docx'),
    ('passport', 'MaterialPassport'),
    ('score_trajectory', 'ScoreTrajectory'),
    ('integrity_gate', 'IntegrityGate, IntegrityReport, ModeCheckResult'),
    ('traceability', 'RRTraceabilityMatrix, TraceabilityItem'),
    ('sprint_contract', 'SprintManager, SprintContract, SprintTask'),
    ('claim_verifier', 'ClaimVerifier, ClaimVerificationReport, Claim'),
    ('style_calibrator', 'StyleCalibrator, StyleCalibrationReport'),
    ('anti_leakage', 'AntiLeakageChecker, AntiLeakageReport, LeakIssue'),
]
for module, names in eval_imports:
    try:
        exec(f'from src.evaluation.{module} import {names}')
        check(f'evaluation.{module}', True)
    except Exception as e: check(f'evaluation.{module}: {str(e)[:50]}', False)

# ── 5. Reviewers Package ──
section('5. Reviewers Package')
try:
    from src.evaluation.reviewers import (
        BaseReviewer, ReviewerReport, FieldReviewer, DevilsAdvocate,
        EditorInChief, EditorialDecision, ReviewOrchestrator,
    )
    check('reviewers package (all 7)', True)
except Exception as e: check(f'reviewers package: {e}', False)

# Test FieldReviewer instantiation
try:
    from tests.conftest import MockLLM
    from src.evaluation.reviewers import FieldReviewer
    r = FieldReviewer(MockLLM(), 'R1', 'methodology')
    check('FieldReviewer(MockLLM) instantiation', True)
except Exception as e: check(f'FieldReviewer instantiation: {str(e)[:50]}', False)

# ── 6. Memory Module ──
section('6. Memory Module')
try:
    from src.memory.citation_store import CitationStore
    from src.memory.experiment_history import ExperimentHistory
    from src.memory.vector_store import SimpleVectorStore
    check('memory modules', True)
except Exception as e: check(f'memory: {e}', False)

# ── 7. LangGraph Workflow (import only - requires real LLM for instantiation) ──
section('7. LangGraph Workflow')
try:
    from src.graph import create_thesis_workflow, AgentState
    check('create_thesis_workflow + AgentState imported', True)
except Exception as e: check(f'graph import: {e}', False)

# ── 8. Enhanced Pipeline Instantiation ──
section('8. Pipeline Instantiation')
try:
    from src.workflows.enhanced_pipeline import EnhancedResearchPipeline
    p = EnhancedResearchPipeline(llm=None)
    check('EnhancedResearchPipeline()', True)
    check(f'  thresholds.min_overall={p.thresholds.MIN_OVERALL_SCORE}', True)
except Exception as e: check(f'enhanced pipeline: {e}', False)

try:
    from src.workflows.quality_workflow import QualityWorkflow
    q = QualityWorkflow(llm=None)
    check('QualityWorkflow()', True)
except Exception as e: check(f'quality workflow: {e}', False)

# ── 9. AIGC Detector & Data Verifier (no API needed) ──
section('9. Tools (no API)')
try:
    from src.tools.aigc_detector import detect_aigc
    result = detect_aigc('This is a test paper about deep learning.')
    assert 'aigc_score' in result
    assert 'risk_level' in result
    check(f'detect_aigc() -> score={result["aigc_score"]}%', True)
except Exception as e: check(f'detect_aigc: {e}', False)

try:
    from src.tools.data_verifier import verify_data
    result = verify_data('Our method achieves 95.5% accuracy on ImageNet.')
    assert 'authenticity_score' in result
    check(f'verify_data() -> score={result["authenticity_score"]}%', True)
except Exception as e: check(f'verify_data: {e}', False)

# ── 10. Rubrics ──
section('10. Evaluation Rubrics')
from src.evaluation.judge import LLMJudge
from tests.conftest import MockLLM
mock_judge = LLMJudge(llm=MockLLM())
rubrics = ['LiteratureRubric', 'MethodRubric', 'ExperimentRubric', 'WritingRubric', 'FigureRubric', 'DocxRubric']
for name in rubrics:
    try:
        exec(f'from src.evaluation.rubrics import {name}')
        exec(f'r = {name}(mock_judge)')
        check(f'{name}(LLMJudge) instantiation', True)
    except Exception as e: check(f'{name}: {str(e)[:50]}', False)

# ── 11. RenderingAuditor + DocxValidator ──
section('11. Rendering & Validator')
try:
    from src.evaluation.rendering_auditor import RenderingAuditor
    au = RenderingAuditor()
    au.record_fallback('test.png', 'SVG_TO_PNG', 'ok')
    report = au.get_report()
    assert len(report.fallback_events) == 1
    assert report.images_requested == 0
    check('RenderingAuditor fallback recording', True)
except Exception as e: check(f'RenderingAuditor: {e}', False)

try:
    from src.evaluation.docx_validator import DocxValidator
    dv = DocxValidator(llm=MockLLM())
    check('DocxValidator(llm=MockLLM())', True)
except Exception as e: check(f'DocxValidator: {e}', False)

# ── 12. Mini Pipeline End-to-End (Mock) ──
section('12. Mock E2E: Passport + ScoreTrajectory + SprintManager')
try:
    from src.evaluation.passport import MaterialPassport
    from src.evaluation.score_trajectory import ScoreTrajectory
    from src.evaluation.sprint_contract import SprintManager
    p = MaterialPassport()
    p.record('writing', 'Writer', 'paper v1', verification_status='PASS', score=85)
    p.record('review', 'Reviewer', 'review v1', upstream=[p.entries[0].content_hash])
    chain_ok = len(p.verify_chain()) == 0
    check('MaterialPassport: record+chain verify', chain_ok)

    t = ScoreTrajectory()
    t.record(1, {'quality': 75, 'novelty': 80})
    t.record(2, {'quality': 85, 'novelty': 82})
    t.record(3, {'quality': 90, 'novelty': 78})
    best = t.get_best()
    regressed = t.regression_detected(threshold=2)
    check(f'ScoreTrajectory: best={best}, regressed={regressed}', best.get('quality') == 90)

    s = SprintManager()
    c = s.plan_sprint(name='Integration Test')
    s.start_sprint(c.sprint_id)
    assert c.state == 'ACTIVE'
    check('SprintManager: plan+start', True)
except Exception as e: check(f'E2E mock: {e}', False)

# ── 13. Full Report ──
section('FINAL RESULT')
total = PASS + FAIL
print(f'  Passed: {PASS}/{total}')
print(f'  Failed: {FAIL}/{total}')
if FAIL == 0:
    print(f'  STATUS: ALL INTEGRATION CHECKS PASSED')
else:
    print(f'  STATUS: {FAIL} CHECK(S) FAILED')

sys.exit(0 if FAIL == 0 else 1)
