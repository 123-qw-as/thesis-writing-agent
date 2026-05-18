import os, sys
sys.path.insert(0, '.')
os.environ['MINIMAX_API_KEY'] = os.getenv('MINIMAX_API_KEY', '')

if not os.environ.get('MINIMAX_API_KEY'):
    print('[SKIP] No API key')
    sys.exit(0)

from langchain_anthropic import ChatAnthropic
from src.workflows.research_pipeline import run_full_pipeline

llm = ChatAnthropic(
    model='MiniMax-M2.7',
    api_key=os.environ['MINIMAX_API_KEY'],
    base_url='https://api.minimaxi.com/anthropic',
    max_tokens=2048
)

print('[TEST] Running pipeline with max_iterations=1...')
result = run_full_pipeline('图像去雾算法研究', llm, max_iterations=1)
thesis = result.get('thesis', '')
print(f'[RESULT] Thesis length: {len(thesis)} chars')

if thesis and len(thesis) > 500:
    with open('output/pipeline_thesis.md', 'w', encoding='utf-8') as f:
        f.write(thesis)
    print('[OK] Saved to output/pipeline_thesis.md')
else:
    short = thesis[:200] if thesis else 'empty'
    print(f'[WARN] Thesis too short: {short}...')