import sys
sys.path.insert(0, '.')

import asyncio
from src.agents.evaluation.agent import evaluate_thesis

print('='*60)
print('FULL QUALITY EVALUATION')
print('='*60)

# Read clean thesis
with open('output/test_thesis_clean.md', 'r', encoding='utf-8') as f:
    thesis = f.read()

print('Thesis length:', len(thesis), 'chars')

async def eval():
    return await evaluate_thesis(
        thesis,
        thesis_title='基于LangChain框架的检索增强生成系统研究与实现',
        iteration=1
    )

report = asyncio.run(eval())

print('\n' + '='*60)
print('EVALUATION RESULTS')
print('='*60)

print('\n[OVERALL]')
print('  Overall Score:     ' + str(report.overall_score) + '/10 (need >=8.0)')
print('  AIGC Score:         ' + str(report.aigc_score) + '% (need <15%)')
print('  Data Authenticity:  ' + str(report.data_authenticity) + '% (need >=95%)')
print('  Pass Status:        ' + ('PASS' if report.is_pass else 'FAIL'))

print('\n[DIMENSIONS]')
for dim in report.dimensions:
    print('  ' + dim.dimension + ': ' + str(round(dim.score, 1)) + '/10')

print('\n[ISSUES]')
for i, issue in enumerate(report.issues[:5], 1):
    print('  ' + str(i) + '. ' + str(issue.get('description', ''))[:60])

print('\n[SUGGESTIONS]')
for i, sug in enumerate(report.revision_suggestions[:5], 1):
    print('  ' + str(i) + '. ' + sug)

print('\n[STRENGTHS]')
for s in report.strengths[:3]:
    print('  + ' + s)

print('\n' + '='*60)
status = 'PASS' if report.is_pass else 'FAIL'
print('FINAL STATUS: ' + status)
print('='*60)

# Save report
import json
report_dict = report.to_dict()
with open('output/evaluation_report.json', 'w', encoding='utf-8') as f:
    json.dump(report_dict, f, ensure_ascii=False, indent=2)
print('\nReport saved to: output/evaluation_report.json')