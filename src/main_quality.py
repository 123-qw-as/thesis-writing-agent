"""
Thesis Quality Improvement CLI

论文质量改进命令行工具

用法:
    python -m src.main_quality input.md --title "论文标题" --output output/
    python -m src.main_quality input.md --evaluate-only
    python -m src.main_quality input.md --detect-aigc-only
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflows.quality_workflow import QualityWorkflow, run_quality_workflow
from src.tools.aigc_detector import detect_aigc, AIGCDetector
from src.tools.data_verifier import verify_data, DataVerifier
from src.agents.evaluation.agent import evaluate_thesis, EvaluationAgent


def print_quality_report(thesis_path: str):
    """仅评估论文质量"""
    print("=" * 60)
    print("THESIS QUALITY EVALUATION")
    print("=" * 60)

    with open(thesis_path, 'r', encoding='utf-8') as f:
        thesis = f.read()

    print(f"File: {thesis_path}")
    print(f"Length: {len(thesis)} chars")
    print()

    aigc_result = detect_aigc(thesis)
    print("[AIGC Detection]")
    print(f"  Score: {aigc_result['aigc_score']}%")
    print(f"  Risk Level: {aigc_result['risk_level']}")
    if aigc_result['detected_patterns']:
        print("  Top Patterns:")
        for p in aigc_result['detected_patterns'][:3]:
            print(f"    - {p['description']}: {p['count']} instances")
    print()

    data_result = verify_data(thesis)
    print("[Data Authenticity]")
    print(f"  Score: {data_result['authenticity_score']}%")
    if data_result['suspicious_data_points']:
        print(f"  Suspicious Points: {len(data_result['suspicious_data_points'])}")
    print()


def detect_aigc_only(thesis_path: str):
    """仅检测AIGC"""
    print("=" * 60)
    print("AIGC DETECTION")
    print("=" * 60)

    with open(thesis_path, 'r', encoding='utf-8') as f:
        thesis = f.read()

    detector = AIGCDetector()
    result = detector.detect(thesis)

    print(f"File: {thesis_path}")
    print(f"Length: {len(thesis)} chars")
    print()
    print(f"AIGC Score: {result['aigc_score']}%")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Pattern Count: {result['pattern_count']}")
    print()

    if result['detected_patterns']:
        print("Detected Patterns:")
        for p in result['detected_patterns']:
            print(f"  [{p['description']}] {p['count']} instances")
            if p.get('examples'):
                print(f"    Examples: {p['examples'][:2]}")


async def improve_quality(
    thesis_path: str,
    title: str,
    output_dir: str,
    use_llm: bool = True
):
    """改进论文质量"""
    print("=" * 60)
    print("THESIS QUALITY IMPROVEMENT")
    print("=" * 60)

    with open(thesis_path, 'r', encoding='utf-8') as f:
        thesis = f.read()

    llm = None
    if use_llm:
        from src.llm_config import auto_select_llm
        model_name, llm = auto_select_llm(temperature=0.5, max_tokens=16384)
        if llm:
            print(f"LLM initialized: {model_name}")
        else:
            print("No API key found, using rule-based improvements only")

    os.makedirs(output_dir, exist_ok=True)

    result = await run_quality_workflow(
        thesis_path=thesis_path,
        thesis_title=title,
        llm=llm,
        output_dir=output_dir
    )

    if result['success']:
        output_path = os.path.join(output_dir, 'thesis_final_pass.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['thesis'])
        print(f"\nFinal thesis saved: {output_path}")
    else:
        output_path = os.path.join(output_dir, 'thesis_best_effort.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['thesis'])
        print(f"\nBest effort saved: {output_path}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Thesis Quality Improvement Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate thesis quality
  python -m src.main_quality input/thesis.md

  # Improve thesis quality with LLM
  python -m src.main_quality input/thesis.md --title "My Thesis" --improve

  # AIGC detection only
  python -m src.main_quality input/thesis.md --detect-aigc

  # Evaluate with custom output
  python -m src.main_quality input/thesis.md --output output/ --improve
"""
    )

    parser.add_argument('input', help='Input thesis file (Markdown)')
    parser.add_argument('--title', '-t', default='论文质量评估', help='Thesis title')
    parser.add_argument('--output', '-o', default='output', help='Output directory')
    parser.add_argument('--evaluate-only', '-e', action='store_true', help='Only evaluate quality')
    parser.add_argument('--detect-aigc', '-a', action='store_true', help='Only detect AIGC')
    parser.add_argument('--no-llm', action='store_true', help='Disable LLM improvements')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    if args.detect_aigc:
        detect_aigc_only(args.input)
    elif args.evaluate_only:
        print_quality_report(args.input)
    else:
        asyncio.run(improve_quality(
            args.input,
            args.title,
            args.output,
            use_llm=not args.no_llm
        ))


if __name__ == '__main__':
    main()