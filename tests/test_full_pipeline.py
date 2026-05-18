"""
完整流程测试 - 测试所有Agent和Workflow的集成
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.workflows.research_pipeline import run_full_pipeline, get_pipeline_status


def test_full_pipeline():
    """测试完整的研究-写作流程"""

    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("[ERROR] MINIMAX_API_KEY not set")
        return False

    print("[TEST] Initializing MiniMax M2.7...")
    try:
        llm = ChatAnthropic(
            model="MiniMax-M2.7",
            temperature=0.7,
            api_key=api_key,
            base_url="https://api.minimaxi.com/anthropic",
            max_tokens=4096
        )
        print("[OK] Model initialized")
    except Exception as e:
        print(f"[ERROR] Model initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    topic = "基于深度学习的图像去雾算法研究"

    print(f"[TEST] Running full pipeline with topic: {topic}")
    print("[INFO] This may take several minutes...\n")

    try:
        result = run_full_pipeline(topic, llm, max_iterations=2)
        print("[OK] Pipeline execution completed")
    except Exception as e:
        print(f"[ERROR] Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    thesis = result.get("thesis", "")
    quality_score = result.get("quality_score", 0)
    iterations = result.get("iterations", 0)

    print(f"[RESULTS]")
    print(f"  - Thesis length: {len(thesis)} chars")
    print(f"  - Quality score: {quality_score:.1f}/10")
    print(f"  - Iterations: {iterations}")

    if thesis and len(thesis) > 500:
        print(f"\n[OK] Thesis generated successfully")
        print("\n--- Thesis Preview (first 800 chars) ---")
        print(thesis[:800])
        print("--- End Preview ---\n")

        output_file = "output/full_pipeline_thesis.md"
        os.makedirs("output", exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(thesis)
        print(f"[OK] Thesis saved to {output_file}")
        return True
    else:
        print("[WARN] Thesis content is too short or empty")
        if thesis:
            print(f"Content: {thesis[:200]}")
        return False


def test_individual_agents():
    """测试各个单独的Agent"""

    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("[ERROR] MINIMAX_API_KEY not set")
        return False

    print("[TEST] Testing individual agents...")

    llm = ChatAnthropic(
        model="MiniMax-M2.7",
        temperature=0.7,
        api_key=api_key,
        base_url="https://api.minimaxi.com/anthropic",
        max_tokens=2048,
        anthropic_api_key=api_key
    )

    from src.agents.literature.agent import run_literature_research
    from src.agents.method.agent import design_method
    from src.agents.experiment.agent import create_mock_experiment_results
    from src.agents.writer.agent import write_full_thesis
    from src.agents.reviewer.agent import review_thesis

    topic = "图像去雾算法"

    print("\n[TEST 1] Literature Agent...")
    try:
        research = run_literature_research(topic, llm)
        print(f"[OK] Research completed - {len(research.get('sota_summary', ''))} chars SOTA summary")
    except Exception as e:
        print(f"[ERROR] Literature agent failed: {e}")
        return False

    print("\n[TEST 2] Method Agent...")
    try:
        method = design_method(topic, research, {"compute": "limited"}, llm)
        print(f"[OK] Method design completed - {method.get('method_name', 'N/A')}")
    except Exception as e:
        print(f"[ERROR] Method agent failed: {e}")
        return False

    print("\n[TEST 3] Experiment Agent (mock)...")
    try:
        experiment = create_mock_experiment_results(method, num_runs=2)
        print(f"[OK] Experiment completed - {len(experiment.get('metrics', {}))} metrics")
    except Exception as e:
        print(f"[ERROR] Experiment agent failed: {e}")
        return False

    print("\n[TEST 4] Writer Agent...")
    try:
        thesis = write_full_thesis(topic, research, method, experiment, llm)
        print(f"[OK] Writing completed - {len(thesis)} chars")
    except Exception as e:
        print(f"[ERROR] Writer agent failed: {e}")
        return False

    print("\n[TEST 5] Reviewer Agent...")
    try:
        review = review_thesis(thesis, {"topic": topic}, llm)
        print(f"[OK] Review completed - Score: {review.get('overall_score', 'N/A')}/10")
    except Exception as e:
        print(f"[ERROR] Reviewer agent failed: {e}")
        return False

    print("\n[OK] All individual agents passed!")
    return True


def test_memory_modules():
    """测试Memory模块"""

    from src.memory.citation_store import CitationStore
    from src.memory.experiment_history import ExperimentHistory
    from src.memory.vector_store import SimpleVectorStore, PaperIndex

    print("[TEST] Testing Memory modules...")

    print("\n[TEST 1] CitationStore...")
    try:
        store = CitationStore(storage_path="output/test_citations.json")
        cid = store.add_citation({
            "title": "Test Paper",
            "authors": ["Test Author"],
            "year": "2024"
        })
        citations = store.get_all_citations()
        print(f"[OK] CitationStore - {len(citations)} citations stored")
    except Exception as e:
        print(f"[ERROR] CitationStore failed: {e}")
        return False

    print("\n[TEST 2] ExperimentHistory...")
    try:
        history = ExperimentHistory(storage_path="output/test_experiments.json")
        eid = history.add_experiment({
            "name": "Test Experiment",
            "config": {"epochs": 100}
        })
        history.complete_experiment(eid, {"accuracy": 0.95}, {"accuracy": 0.95})
        experiments = history.get_all_experiments()
        print(f"[OK] ExperimentHistory - {len(experiments)} experiments stored")
    except Exception as e:
        print(f"[ERROR] ExperimentHistory failed: {e}")
        return False

    print("\n[TEST 3] VectorStore...")
    try:
        vector_store = SimpleVectorStore(storage_path="output/test_vectors.json")
        doc_id = vector_store.add_document("doc1", "This is a test document about deep learning")
        results = vector_store.search("deep learning neural network", top_k=5)
        print(f"[OK] VectorStore - Indexed {len(results)} documents")
    except Exception as e:
        print(f"[ERROR] VectorStore failed: {e}")
        return False

    print("\n[OK] All Memory modules passed!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Thesis Writing Agent - Full Pipeline Test")
    print("=" * 60)

    print("\n[STEP 1] Testing Memory modules...")
    memory_ok = test_memory_modules()

    if memory_ok:
        print("\n[STEP 2] Testing individual agents...")
        agents_ok = test_individual_agents()

    if memory_ok and agents_ok:
        print("\n[STEP 3] Testing full pipeline (this may take a while)...")
        pipeline_ok = test_full_pipeline()

        if pipeline_ok:
            print("\n" + "=" * 60)
            print("[SUCCESS] All tests passed!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("[PARTIAL] Pipeline test failed")
            print("=" * 60)
            sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("[FAILED] Individual tests failed")
        print("=" * 60)
        sys.exit(1)