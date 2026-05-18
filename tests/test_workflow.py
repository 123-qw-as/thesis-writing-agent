import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from langchain_anthropic import ChatAnthropic
from src.graph import create_thesis_workflow


def test_thesis_generation():
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("[ERROR] MINIMAX_API_KEY not set")
        return False

    print("[TEST] Initializing workflow with MiniMax M2.7...")
    try:
        llm = ChatAnthropic(
            model="MiniMax-M2.7",
            temperature=0.7,
            api_key=api_key,
            base_url="https://api.minimaxi.com/anthropic",
            max_tokens=4096
        )
        app = create_thesis_workflow(llm)
        print("[OK] Workflow created")
    except Exception as e:
        print(f"[ERROR] Workflow creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    topic = "基于深度学习的图像去雾算法"

    print(f"[TEST] Running workflow with topic: {topic}")
    try:
        result = app.invoke({
            "messages": [HumanMessage(content=topic)],
            "current_task": "research",
            "research_results": "",
            "code_results": "",
            "thesis_content": "",
            "feedback": ""
        }, config={"recursion_limit": 50})
        print("[OK] Workflow execution completed")
    except Exception as e:
        print(f"[ERROR] Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    thesis = result.get("thesis_content", "")
    if thesis:
        if isinstance(thesis, list):
            thesis_text = ""
            for block in thesis:
                if isinstance(block, dict) and block.get("type") == "text":
                    thesis_text += block.get("text", "")
                elif isinstance(block, str):
                    thesis_text += block
            thesis = thesis_text
        else:
            thesis = str(thesis)
        print(f"[OK] Thesis generated ({len(thesis)} chars)")

        output_file = "output/test_thesis.md"
        os.makedirs("output", exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(thesis)
        print(f"[OK] Thesis saved to {output_file}")
        print("\n--- Thesis Preview (first 500 chars) ---")
        print(thesis[:500])
        print("--- End Preview ---\n")
        return True
    else:
        print("[WARN] No thesis content generated")
        research = result.get("research_results", "")
        code = result.get("code_results", "")
        print(f"Research results: {len(research)} chars")
        print(f"Code results: {len(code)} chars")
        if research:
            print("\n--- Research Preview ---")
            print(research[:300])
        return False


if __name__ == "__main__":
    success = test_thesis_generation()
    sys.exit(0 if success else 1)
