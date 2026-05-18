import sys
sys.path.insert(0, '.')

print('='*60)
print('Step 8: Final Quality Evaluation')
print('='*60)

with open('output/test_thesis_complete.md', 'r', encoding='utf-8') as f:
    thesis = f.read()

print('Thesis length: ' + str(len(thesis)) + ' chars')

import asyncio
from src.agents.evaluation.agent import evaluate_thesis

async def run_eval():
    report = await evaluate_thesis(
        thesis,
        thesis_title='基于LangChain框架的检索增强生成系统研究与实现',
        iteration=2
    )
    return report

report = asyncio.run(run_eval())

print('\n' + '='*60)
print('FINAL EVALUATION RESULTS')
print('='*60)

print('\nOverall Score: ' + str(report.overall_score) + '/10 (' + report._score_to_letter(report.overall_score) + ')')
print('AIGC Score: ' + str(report.aigc_score) + '% (threshold: <' + str(report.aigc_threshold) + '%)')
print('Data Authenticity: ' + str(report.data_authenticity) + '%')
print('Pass Status: ' + ('PASS' if report.is_pass else 'FAIL'))

print('\n--- Dimension Scores ---')
for dim in report.dimensions:
    print('  ' + dim.dimension + ': ' + str(dim.score) + '/10 (' + dim.level.value + ')')

print('\n--- Issues ---')
for issue in report.issues[:5]:
    print('  - [' + str(issue.get('severity')) + '] ' + str(issue.get('description', ''))[:60])

print('\n--- Revision Suggestions ---')
for i, sug in enumerate(report.revision_suggestions[:5], 1):
    print('  ' + str(i) + '. ' + sug)

print('\n--- Strengths ---')
for s in report.strengths:
    print('  + ' + s)

print('\n' + '='*60)
if report.is_pass:
    print('STATUS: PASS - All quality thresholds met!')
else:
    print('STATUS: FAIL - Some thresholds not met')
    print('\nRemaining issues:')
    if report.overall_score < 8.0:
        print('  - Overall score: ' + str(report.overall_score) + ' (need >= 8.0)')
    if report.aigc_score >= 15.0:
        print('  - AIGC score: ' + str(report.aigc_score) + '% (need < 15%)')
    if report.data_authenticity < 95.0:
        print('  - Data authenticity: ' + str(report.data_authenticity) + '% (need >= 95%)')
print('='*60)