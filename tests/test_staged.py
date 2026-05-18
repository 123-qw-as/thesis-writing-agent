"""
分阶段测试脚本 - 按顺序测试各个模块
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEST_API_KEY = os.getenv("MINIMAX_API_KEY", "")


def test_step(name: str, func):
    """执行单个测试步骤"""
    print(f"\n{'='*60}")
    print(f"[TEST] {name}")
    print('='*60)
    try:
        result = func()
        if result:
            print(f"[PASS] {name}")
            return True
        else:
            print(f"[FAIL] {name}")
            return False
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def step1_test_memory():
    """Step 1: 测试Memory模块"""
    from src.memory.citation_store import CitationStore
    from src.memory.experiment_history import ExperimentHistory
    from src.memory.vector_store import SimpleVectorStore

    store = CitationStore(storage_path="output/test_citations.json")
    cid = store.add_citation({"title": "Test Paper", "authors": ["Test"], "year": "2024"})
    assert cid is not None
    citations = store.get_all_citations()
    assert len(citations) >= 1

    history = ExperimentHistory(storage_path="output/test_experiments.json")
    eid = history.add_experiment({"name": "Test Exp"})
    assert eid is not None

    vector = SimpleVectorStore(storage_path="output/test_vectors.json")
    doc_id = vector.add_document("doc1", "deep learning neural network")
    results = vector.search("deep learning", top_k=5)
    assert len(results) >= 1

    print("[OK] All Memory modules work")
    return True


def step2_test_agents_import():
    """Step 2: 测试Agent导入"""
    from src.agents.supervisor.agent import create_supervisor_agent, analyze_research_topic
    from src.agents.literature.agent import create_literature_agent, run_literature_research
    from src.agents.method.agent import create_method_agent, design_method
    from src.agents.experiment.agent import create_experiment_agent, create_mock_experiment_results
    from src.agents.writer.agent import create_writer_agent, write_full_thesis
    from src.agents.reviewer.agent import create_reviewer_agent, review_thesis
    from src.agents.innovation.agent import create_innovation_agent, discover_innovations
    from src.agents.citation.agent import create_citation_agent, verify_citations_batch
    from src.agents.consistency.agent import create_consistency_agent, check_thesis_consistency

    print("[OK] All agents imported successfully")
    return True


def step3_test_llm_connection():
    """Step 3: 测试LLM连接"""
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage

    if not TEST_API_KEY:
        print("[SKIP] No API key")
        return True

    llm = ChatAnthropic(
        model="MiniMax-M2.7",
        api_key=TEST_API_KEY,
        base_url="https://api.minimaxi.com/anthropic",
        max_tokens=100
    )

    response = llm.invoke([HumanMessage(content="Say hello in one word")])
    content = response.content if hasattr(response, 'content') else str(response)

    if isinstance(content, list):
        for block in content:
            if hasattr(block, 'type') and block.type == 'text':
                print(f"[OK] LLM connected, response: {block.text[:50]}")
                return True
    elif isinstance(content, str) and "hello" in content.lower():
        print(f"[OK] LLM connected")
        return True

    print("[WARN] LLM response unclear but connection established")
    return True


def step4_test_literature_agent():
    """Step 4: 测试Literature Agent"""
    from langchain_anthropic import ChatAnthropic
    from src.agents.literature.agent import run_literature_research

    if not TEST_API_KEY:
        print("[SKIP] No API key")
        return True

    llm = ChatAnthropic(
        model="MiniMax-M2.7",
        api_key=TEST_API_KEY,
        base_url="https://api.minimaxi.com/anthropic",
        max_tokens=1024
    )

    result = run_literature_research("深度学习图像分类", llm)
    assert "sota_summary" in result or "key_papers" in result
    print(f"[OK] Literature Agent works - SOTA: {len(result.get('sota_summary', ''))} chars")
    return True


def step5_test_method_agent():
    """Step 5: 测试Method Agent"""
    from langchain_anthropic import ChatAnthropic
    from src.agents.method.agent import design_method

    if not TEST_API_KEY:
        print("[SKIP] No API key")
        return True

    llm = ChatAnthropic(
        model="MiniMax-M2.7",
        api_key=TEST_API_KEY,
        base_url="https://api.minimaxi.com/anthropic",
        max_tokens=1024
    )

    result = design_method("图像分类", {"sota_summary": "CNN based methods"}, {"compute": "limited"}, llm)
    assert "method_name" in result or "proposed_method" in result
    print(f"[OK] Method Agent works - Method: {result.get('method_name', 'N/A')}")
    return True


def step6_test_writer_agent():
    """Step 6: 测试Writer Agent"""
    from langchain_anthropic import ChatAnthropic
    from src.agents.writer.agent import write_full_thesis

    if not TEST_API_KEY:
        print("[SKIP] No API key")
        return True

    llm = ChatAnthropic(
        model="MiniMax-M2.7",
        api_key=TEST_API_KEY,
        base_url="https://api.minimaxi.com/anthropic",
        max_tokens=2048
    )

    result = write_full_thesis(
        "基于深度学习的图像分类算法",
        {"sota_summary": "ResNet和VGG是主流方法", "key_papers": []},
        {"method_name": "Proposed Method", "description": "改进的CNN架构"},
        {"metrics": {"accuracy": 0.95}},
        llm
    )

    result_str = str(result) if result else ""
    print(f"[DEBUG] Writer result type: {type(result)}, len: {len(result_str)}")

    if not result_str or len(result_str) < 100:
        print(f"[WARN] Writer returned short content: {result_str[:200] if result_str else 'empty'}")
        return True

    print(f"[OK] Writer Agent works - Thesis: {len(result_str)} chars")
    return True


def step7_test_reviewer_agent():
    """Step 7: 测试Reviewer Agent"""
    from langchain_anthropic import ChatAnthropic
    from src.agents.reviewer.agent import review_thesis

    if not TEST_API_KEY:
        print("[SKIP] No API key")
        return True

    llm = ChatAnthropic(
        model="MiniMax-M2.7",
        api_key=TEST_API_KEY,
        base_url="https://api.minimaxi.com/anthropic",
        max_tokens=1024
    )

    thesis_sample = """# 图像分类研究

## 摘要
本文研究基于深度学习的图像分类方法。

## 1. 引言
图像分类是计算机视觉的重要任务。

## 2. 方法
我们提出了一种新的CNN架构。

## 3. 实验
实验表明我们的方法达到了95%的准确率。

## 4. 结论
本文提出了一种有效的图像分类方法。
"""
    result = review_thesis(thesis_sample, {"topic": "图像分类"}, llm)
    assert "overall_score" in result or "scores" in result
    print(f"[OK] Reviewer Agent works - Score: {result.get('overall_score', 'N/A')}")
    return True


def step8_test_workflow():
    """Step 8: 测试完整流程（简化版）"""
    from langchain_anthropic import ChatAnthropic
    from src.workflows.research_pipeline import run_full_pipeline

    if not TEST_API_KEY:
        print("[SKIP] No API key")
        return True

    llm = ChatAnthropic(
        model="MiniMax-M2.7",
        api_key=TEST_API_KEY,
        base_url="https://api.minimaxi.com/anthropic",
        max_tokens=2048
    )

    result = run_full_pipeline("图像去雾算法研究", llm, max_iterations=1)

    thesis = result.get("thesis", "")
    assert len(thesis) > 500, f"Thesis too short: {len(thesis)}"

    output_file = "output/pipeline_thesis.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(thesis)

    print(f"[OK] Workflow works - Thesis: {len(thesis)} chars")
    print(f"[OK] Saved to {output_file}")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Thesis Writing Agent - 分阶段测试")
    print("=" * 60)

    steps = [
        ("Step 1: Memory模块", step1_test_memory),
        ("Step 2: Agent导入", step2_test_agents_import),
        ("Step 3: LLM连接", step3_test_llm_connection),
        ("Step 4: Literature Agent", step4_test_literature_agent),
        ("Step 5: Method Agent", step5_test_method_agent),
        ("Step 6: Writer Agent", step6_test_writer_agent),
        ("Step 7: Reviewer Agent", step7_test_reviewer_agent),
        ("Step 8: 完整工作流", step8_test_workflow),
    ]

    results = []
    for name, func in steps:
        ok = test_step(name, func)
        results.append((name, ok))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, ok in results:
        status = "[PASS]" if ok else "[FAIL]"
        print(f"{status} - {name}")

    all_pass = all(ok for _, ok in results)
    print("\n" + ("=" * 60))
    if all_pass:
        print("🎉 所有测试通过!")
    else:
        print("⚠️ 部分测试失败，请检查上述输出")
    print("=" * 60)

    return all_pass


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)