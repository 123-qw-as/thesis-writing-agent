"""
融合最佳版本 - 以低AIGC版本为基础，提升综合评分
"""
import sys
sys.path.insert(0, '.')

import asyncio
from src.agents.evaluation.agent import evaluate_thesis
from src.tools.aigc_detector import detect_aigc

print('='*60)
print('COMBINING BEST VERSIONS')
print('='*60)

# Load the low AIGC version
with open('output/test_thesis_round2.md', 'r', encoding='utf-8') as f:
    thesis = f.read()

print(f'Base (round2): {len(thesis)} chars, AIGC: {detect_aigc(thesis)["aigc_score"]}%')

# Load high overall version
with open('output/test_thesis_best_current.md', 'r', encoding='utf-8') as f:
    best_overall = f.read()

print(f'Best Overall: {len(best_overall)} chars')

async def eval_thesis(content, name):
    report = await evaluate_thesis(content, '检查', 1)
    print(f'{name}: Overall={report.overall_score}, AIGC={report.aigc_score}%, Data={report.data_authenticity}%')
    return report

async def main():
    # Compare dimensions
    report1 = await eval_thesis(thesis, 'Round2 (Low AIGC)')
    report2 = await eval_thesis(best_overall, 'Best Overall')

    print('\nRound2 Dimensions:')
    for d in report1.dimensions:
        print(f'  {d.dimension}: {d.score}/10')

    print('\nBest Overall Dimensions:')
    for d in report2.dimensions:
        print(f'  {d.dimension}: {d.score}/10')

asyncio.run(main())