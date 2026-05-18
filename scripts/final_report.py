import sys
sys.path.insert(0, '.')

print('='*60)
print('Complete Quality Evaluation - Final Report')
print('='*60)

with open('output/test_thesis_final.md', 'r', encoding='utf-8') as f:
    content = f.read()

print('Thesis length:', len(content), 'chars')

import asyncio
from src.agents.evaluation.agent import evaluate_thesis

async def run_eval():
    return await evaluate_thesis(
        content,
        thesis_title='基于LangChain框架的检索增强生成系统研究与实现',
        iteration=2
    )

report = asyncio.run(run_eval())

print('\n' + '='*60)
print('FINAL QUALITY ASSESSMENT')
print('='*60)

print('\n[OVERALL METRICS]')
print('  Overall Score:     ' + str(report.overall_score) + '/10 (Threshold: >=8.0)')
print('  AIGC Score:         ' + str(report.aigc_score) + '% (Threshold: <15%)')
print('  Data Authenticity: ' + str(report.data_authenticity) + '% (Threshold: >=95%)')
print('  Pass Status:       ' + ('PASS' if report.is_pass else 'FAIL'))

print('\n[DIMENSION SCORES]')
level_map = {'excellent': '[EXC]', 'good': '[GOOD]', 'acceptable': '[OK]', 'poor': '[POOR]', 'fail': '[FAIL]'}
for dim in report.dimensions:
    lvl = level_map.get(dim.level.value, '[???]')
    print('  ' + lvl + ' ' + dim.dimension + ': ' + str(round(dim.score, 1)) + '/10')

print('\n[AIGC ANALYSIS]')
print('  AIGC Score: ' + str(report.aigc_score) + '%')
print('  Threshold: <' + str(report.aigc_threshold) + '%')
print('  Status: ' + ('PASS' if report.aigc_score < report.aigc_threshold else 'FAIL'))

print('\n[DATA AUTHENTICITY]')
print('  Score: ' + str(report.data_authenticity) + '%')
print('  Threshold: >=95%')
print('  Status: ' + ('PASS' if report.data_authenticity >= 95 else 'FAIL'))

print('\n[ISSUES FOUND]')
for issue in report.issues[:5]:
    print('  - [' + str(issue.get('severity')) + '] ' + str(issue.get('description', ''))[:60])

print('\n[STRENGTHS]')
for s in report.strengths:
    print('  + ' + s)

print('\n[REVISION SUGGESTIONS]')
for i, sug in enumerate(report.revision_suggestions[:5], 1):
    print('  ' + str(i) + '. ' + sug)

print('\n' + '='*60)
if report.is_pass:
    print('STATUS: PASS - All quality thresholds met!')
else:
    print('STATUS: FAIL - Needs further improvement')
    print('\nRemaining thresholds not met:')
    if report.overall_score < 8.0:
        print('  - Overall score: ' + str(report.overall_score) + ' (need >= 8.0)')
    if report.aigc_score >= 15.0:
        print('  - AIGC score: ' + str(report.aigc_score) + '% (need < 15%)')
    if report.data_authenticity < 95.0:
        print('  - Data authenticity: ' + str(report.data_authenticity) + '% (need >= 95%)')
print('='*60)