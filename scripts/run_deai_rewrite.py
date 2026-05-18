import sys
sys.path.insert(0, '.')

import asyncio
from src.agents.deai.agent import DeAIAgent

# Read thesis
with open('output/test_thesis.md', 'r', encoding='utf-8') as f:
    thesis_content = f.read()

print(f'Paper length: {len(thesis_content)} characters')
print(f'Starting De-AI rewrite process...')
print('='*60)

# Run De-AI rewrite
agent = DeAIAgent(llm=None)  # Will use rule-based reduction

result = agent.rewrite(thesis_content, llm=None, max_iterations=2)

print(f'\nDe-AI Rewrite Results:')
print(f'  Original AIGC Score: {result["aigc_score_before"]:.1f}%')
print(f'  Final AIGC Score: {result["aigc_score_after"]:.1f}%')
print(f'  Iterations: {result["iterations"]}')
print(f'  Changes made: {result["changes_count"]}')

# Check if AIGC is now acceptable
if result["aigc_score_after"] < 15.0:
    print(f'\n[PASS] AIGC score is now below threshold (15%)!')

    # Save rewritten thesis
    output_path = 'output/test_thesis_deai.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result["rewritten_content"])
    print(f'Saved rewritten thesis to: {output_path}')

    # Run final evaluation
    print('\n' + '='*60)
    print('Running Final Quality Evaluation...')
    print('='*60)

    from src.agents.evaluation.agent import evaluate_thesis

    async def run_final_eval():
        report = await evaluate_thesis(
            result["rewritten_content"],
            thesis_title='基于 LangChain 框架的检索增强生成系统研究与实现',
            iteration=2
        )
        return report

    report = asyncio.run(run_final_eval())

    print(f'\nFinal Evaluation:')
    print(f'  Overall Score: {report.overall_score}/10 ({report._score_to_letter(report.overall_score)})')
    print(f'  AIGC Score: {report.aigc_score}% (threshold: {report.aigc_threshold}%)')
    print(f'  Data Authenticity: {report.data_authenticity}%')
    print(f'  Pass Status: {"PASS" if report.is_pass else "FAIL"}')

    print('\nDimension Scores:')
    for dim in report.dimensions:
        print(f'  {dim.dimension}: {dim.score}/10 ({dim.level.value})')

else:
    print(f'\n[FAIL] AIGC score still above threshold: {result["aigc_score_after"]:.1f}%')
    print('Consider more aggressive rewriting or manual editing.')