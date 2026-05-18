import sys
sys.path.insert(0, '.')

import asyncio
from src.agents.evaluation.agent import evaluate_thesis

with open('output/test_thesis_llm_improved.md', 'r', encoding='utf-8') as f:
    thesis = f.read()

print('Evaluating LLM-improved thesis...')
print('Length:', len(thesis), 'chars')

async def eval():
    return await evaluate_thesis(thesis, '基于LangChain框架的检索增强生成系统研究与实现', 2)

report = asyncio.run(eval())

print('\n' + '='*60)
print('EVALUATION RESULTS')
print('='*60)

print('\nOverall Score:     ' + str(report.overall_score) + '/10 (need >=8.0)')
print('AIGC Score:         ' + str(report.aigc_score) + '% (need <15%)')
print('Data Authenticity:  ' + str(report.data_authenticity) + '% (need >=95%)')
print('Pass Status:        ' + ('PASS' if report.is_pass else 'FAIL'))

print('\nDimension Scores:')
for dim in report.dimensions:
    print('  ' + dim.dimension + ': ' + str(round(dim.score, 1)) + '/10')

# Check data verifier details
from src.tools.data_verifier import verify_data
data = verify_data(thesis)

print('\nData Verification Details:')
print('  Authenticity Score: ' + str(data['authenticity_score']) + '%')
print('  Suspicious points: ' + str(len(data['suspicious_data_points'])))
if data['suspicious_data_points']:
    print('  Top suspicious issues:')
    for p in data['suspicious_data_points'][:5]:
        print('    - ' + str(p.get('type')) + ': ' + str(p.get('value')) + ' at line ' + str(p.get('line')))

print('\n' + '='*60)
if report.is_pass:
    print('FINAL STATUS: PASS')
else:
    print('FINAL STATUS: FAIL')
    print('\nRemaining issues:')
    if report.overall_score < 8.0:
        print('  - Overall score too low: ' + str(report.overall_score))
    if report.aigc_score >= 15.0:
        print('  - AIGC score too high: ' + str(report.aigc_score) + '%')
    if report.data_authenticity < 95.0:
        print('  - Data authenticity too low: ' + str(report.data_authenticity) + '%')
print('='*60)