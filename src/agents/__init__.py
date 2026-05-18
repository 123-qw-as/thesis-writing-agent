from src.agents.supervisor.agent import create_supervisor_agent, analyze_research_topic
from src.agents.literature.agent import run_literature_research
from src.agents.method.agent import design_method
from src.agents.experiment.agent import create_mock_experiment_results, generate_experiment_code
from src.agents.writer.agent import write_full_thesis, write_thesis_with_feedback
from src.agents.reviewer.agent import review_thesis, generate_revision_feedback
from src.agents.innovation.agent import discover_innovations
from src.agents.citation.agent import verify_citations_batch
from src.agents.consistency.agent import check_thesis_consistency

__all__ = [
    "create_supervisor_agent",
    "analyze_research_topic",
    "run_literature_research",
    "design_method",
    "create_mock_experiment_results",
    "generate_experiment_code",
    "write_full_thesis",
    "write_thesis_with_feedback",
    "review_thesis",
    "generate_revision_feedback",
    "discover_innovations",
    "verify_citations_batch",
    "check_thesis_consistency",
]