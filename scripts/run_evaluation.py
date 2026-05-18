import sys
sys.path.insert(0, '.')

import asyncio
from src.tools.aigc_detector import AIGCDetector
from src.tools.data_verifier import DataVerifier

# Read thesis
with open('output/test_thesis.md', 'r', encoding='utf-8') as f:
    thesis_content = f.read()

print(f'Paper length: {len(thesis_content)} characters')

# Run AIGC detection
detector = AIGCDetector()
aigc_result = detector.detect(thesis_content)
print(f'\nAIGC Detection:')
print(f'  AIGC Score: {aigc_result.get("aigc_score", 0):.1f}%')
print(f'  Risk Level: {aigc_result.get("risk_level", "N/A")}')

# Run Data verification
verifier = DataVerifier()
data_result = verifier.verify(thesis_content)
print(f'\nData Authenticity:')
print(f'  Score: {data_result.get("authenticity_score", 0):.1f}%')
print(f'  Suspicious points: {len(data_result.get("suspicious_data_points", []))}')
print(f'  Inconsistencies: {len(data_result.get("numerical_inconsistencies", []))}')

# Run full evaluation
print('\n' + '='*60)
print('Running Full Quality Evaluation...')
print('='*60)

from src.agents.evaluation.agent import evaluate_thesis

async def run_eval():
    report = await evaluate_thesis(
        thesis_content,
        thesis_title='基于 LangChain 框架的检索增强生成系统研究与实现',
        iteration=1
    )
    return report

report = asyncio.run(run_eval())

print(f'\nOverall Score: {report.overall_score}/10 ({report._score_to_letter(report.overall_score)})')
print(f'AIGC Score: {report.aigc_score}% (threshold: {report.aigc_threshold}%)')
print(f'Data Authenticity: {report.data_authenticity}%')
print(f'Pass Status: {"PASS" if report.is_pass else "FAIL"}')

print('\nDimension Scores:')
for dim in report.dimensions:
    print(f'  {dim.dimension}: {dim.score}/10 ({dim.level.value})')

print('\nIssues found:')
for issue in report.issues[:5]:
    print(f'  - [{issue.get("severity", "N/A")}] {issue.get("description", "N/A")[:80]}...')

print('\nStrengths:')
for s in report.strengths:
    print(f'  + {s}')

print('\nRevision Suggestions:')
for i, sug in enumerate(report.revision_suggestions[:5], 1):
    print(f'  {i}. {sug}')