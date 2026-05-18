import os
import sys

sys.path.insert(0, '.')

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

# Initialize LLM
api_key = os.getenv("MINIMAX_API_KEY")
print(f'Initializing MiniMax LLM...')

llm = ChatAnthropic(
    model="MiniMax-M2.7",
    temperature=0.7,
    api_key=api_key,
    base_url="https://api.minimaxi.com/anthropic",
    max_tokens=4096
)
print('LLM initialized successfully')

# Read current thesis
with open('output/test_thesis.md', 'r', encoding='utf-8') as f:
    thesis_content = f.read()

print(f'\nThesis length: {len(thesis_content)} characters')

# Run De-AI rewrite with LLM
print('\n' + '='*60)
print('Running LLM-based De-AI Rewrite')
print('='*60)

from src.agents.deai.agent import DeAIAgent

agent = DeAIAgent(llm=llm)
result = agent.rewrite(thesis_content, llm=llm, max_iterations=2)

print(f'\nDe-AI Rewrite Results:')
print(f'  Original AIGC Score: {result["aigc_score_before"]:.1f}%')
print(f'  Final AIGC Score: {result["aigc_score_after"]:.1f}%')
print(f'  Iterations: {result["iterations"]}')
print(f'  Changes: {result["changes_count"]}')

# Save result
output_path = 'output/test_thesis_deai.md'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(result["rewritten_content"])
print(f'\nSaved rewritten thesis to: {output_path}')

# Final evaluation
print('\n' + '='*60)
print('Running Final Quality Evaluation')
print('='*60)

import asyncio
from src.agents.evaluation.agent import evaluate_thesis

async def run_eval():
    report = await evaluate_thesis(
        result["rewritten_content"],
        thesis_title='基于 LangChain 框架的检索增强生成系统研究与实现',
        iteration=2
    )
    return report

report = asyncio.run(run_eval())

print(f'\nFinal Evaluation:')
print(f'  Overall Score: {report.overall_score}/10 ({report._score_to_letter(report.overall_score)})')
print(f'  AIGC Score: {report.aigc_score}% (threshold: <{report.aigc_threshold}%)')
print(f'  Data Authenticity: {report.data_authenticity}%')
print(f'  Pass Status: {"PASS" if report.is_pass else "FAIL"}')

print('\nDimension Scores:')
for dim in report.dimensions:
    print(f'  {dim.dimension}: {dim.score}/10 ({dim.level.value})')

print('\nIssues:')
for issue in report.issues[:5]:
    print(f'  - [{issue.get("severity")}] {issue.get("description", "")[:80]}')

print('\nRevision Suggestions:')
for i, sug in enumerate(report.revision_suggestions[:5], 1):
    print(f'  {i}. {sug}')