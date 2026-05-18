"""
Research Pipeline - 研究流程编排
整合所有Agent实现完整的研究-写作流程
"""

from typing import TypedDict, Annotated, Sequence, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
import operator
import json


class ResearchPipelineState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    topic: str
    current_phase: str
    research_results: Dict[str, Any]
    method_results: Dict[str, Any]
    experiment_results: Dict[str, Any]
    thesis_content: str
    review_results: Dict[str, Any]
    quality_score: float
    iteration_count: int
    max_iterations: int
    is_final: bool


def run_full_pipeline(topic: str, llm, max_iterations: int = 3) -> dict:
    """运行完整的研究-写作流程"""

    from src.agents.literature.agent import run_literature_research
    from src.agents.method.agent import design_method
    from src.agents.experiment.agent import create_mock_experiment_results
    from src.agents.writer.agent import write_full_thesis, write_thesis_with_feedback
    from src.agents.reviewer.agent import review_thesis, generate_revision_feedback

    state = {
        "topic": topic,
        "current_phase": "PHASE_1_RESEARCH",
        "research_results": {},
        "method_results": {},
        "experiment_results": {},
        "thesis_content": "",
        "review_results": {},
        "quality_score": 0.0,
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "is_final": False,
        "messages": []
    }

    phase_order = ["PHASE_1_RESEARCH", "PHASE_2_METHOD", "PHASE_3_EXPERIMENT",
                    "PHASE_4_WRITING", "PHASE_5_REVIEW", "PHASE_6_REVISION"]

    while not state["is_final"]:
        current_phase = state["current_phase"]

        if current_phase == "PHASE_1_RESEARCH":
            research = run_literature_research(topic, llm)
            state["research_results"] = research
            state["current_phase"] = "PHASE_2_METHOD"

        elif current_phase == "PHASE_2_METHOD":
            method = design_method(topic, state["research_results"], {"compute": "limited"}, llm)
            state["method_results"] = method
            state["current_phase"] = "PHASE_3_EXPERIMENT"

        elif current_phase == "PHASE_3_EXPERIMENT":
            experiment = create_mock_experiment_results(state["method_results"], num_runs=3)
            state["experiment_results"] = experiment
            state["current_phase"] = "PHASE_4_WRITING"

        elif current_phase == "PHASE_4_WRITING":
            thesis = write_full_thesis(topic, state["research_results"], state["method_results"], state["experiment_results"], llm)
            state["thesis_content"] = thesis
            state["current_phase"] = "PHASE_5_REVIEW"

        elif current_phase == "PHASE_5_REVIEW":
            review = review_thesis(state["thesis_content"], {"topic": topic}, llm)
            state["review_results"] = review
            state["quality_score"] = review.get("overall_score", 5.0)
            state["iteration_count"] += 1

            if state["quality_score"] >= 8.0 or state["iteration_count"] >= max_iterations:
                state["is_final"] = True
            else:
                state["current_phase"] = "PHASE_6_REVISION"

        elif current_phase == "PHASE_6_REVISION":
            feedback = generate_revision_feedback(state["review_results"])
            new_thesis = write_thesis_with_feedback(topic, feedback, state["thesis_content"], llm)
            state["thesis_content"] = new_thesis
            state["current_phase"] = "PHASE_5_REVIEW"
            state["iteration_count"] += 1

        else:
            state["is_final"] = True

        if state["iteration_count"] >= state["max_iterations"] and not state["is_final"]:
            state["is_final"] = True

    return {
        "thesis": state["thesis_content"],
        "quality_score": state["quality_score"],
        "iterations": state["iteration_count"],
        "research_results": state["research_results"],
        "method_results": state["method_results"],
        "experiment_results": state["experiment_results"],
        "review_results": state["review_results"]
    }


def get_pipeline_status(state: dict) -> str:
    """获取Pipeline状态报告"""
    lines = ["## Pipeline Status Report\n"]
    lines.append(f"- Current Phase: {state.get('current_phase', 'N/A')}")
    lines.append(f"- Quality Score: {state.get('quality_score', 0):.1f}/10")
    lines.append(f"- Iterations: {state.get('iteration_count', 0)}/{state.get('max_iterations', 3)}")
    lines.append(f"- Is Final: {'Yes' if state.get('is_final') else 'No'}")
    return "\n".join(lines)