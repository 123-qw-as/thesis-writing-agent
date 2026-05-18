import os
import sys

sys.path.insert(0, '.')

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

os.environ['MINIMAX_API_KEY'] = 'sk-cp-D0MsxcdMlbmX8bJNvhTXjM8MyViiLof_eqMAPSKYHxNrSKa9DDd1cvlT9UQ52n0Mg2jfa4avTEmyEMMMcnEkqjfBFVTAcrvUMsWgOcSYakxvc9QL1BtQnW4'

print('='*60)
print('Step 6: LLM-based Deep De-AI Rewrite')
print('='*60)

llm = ChatAnthropic(
    model='MiniMax-M2.7',
    temperature=0.7,
    api_key=os.environ['MINIMAX_API_KEY'],
    base_url='https://api.minimaxi.com/anthropic',
    max_tokens=4096
)
print('[OK] LLM initialized')

with open('output/test_thesis.md', 'r', encoding='utf-8') as f:
    thesis_content = f.read()

print(f'[OK] Loaded thesis: {len(thesis_content)} characters')

from src.agents.deai.agent import DeAIAgent

agent = DeAIAgent(llm=llm)
result = agent.rewrite(thesis_content, llm=llm, max_iterations=3)

print(f'\nDe-AI Rewrite Results:')
print(f'  Original AIGC: {result["aigc_score_before"]:.1f}%')
print(f'  Final AIGC: {result["aigc_score_after"]:.1f}%')
print(f'  Iterations: {result["iterations"]}')
print(f'  Changes: {result["changes_count"]}')

deai_path = 'output/test_thesis_deai.md'
with open(deai_path, 'w', encoding='utf-8') as f:
    f.write(result["rewritten_content"])
print(f'\n[OK] Saved to: {deai_path}')