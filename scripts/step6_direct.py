import os
import sys
sys.path.insert(0, '.')

os.environ['MINIMAX_API_KEY'] = 'sk-cp-D0MsxcdMlbmX8bJNvhTXjM8MyViiLof_eqMAPSKYHxNrSKa9DDd1cvlT9UQ52n0Mg2jfa4avTEmyEMMMcnEkqjfBFVTAcrvUMsWgOcSYakxvc9QL1BtQnW4'

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

print('='*60)
print('Step 6: LLM-based De-AI Rewrite (Direct)')
print('='*60)

llm = ChatAnthropic(
    model='MiniMax-M2.7',
    temperature=0.7,
    api_key=os.environ['MINIMAX_API_KEY'],
    base_url='https://api.minimaxi.com/anthropic',
    max_tokens=8192
)

with open('output/test_thesis.md', 'r', encoding='utf-8') as f:
    thesis_content = f.read()

print(f'Loaded thesis: {len(thesis_content)} chars')

DEAI_PROMPT = '''请将以下学术论文改写，消除AI写作特征，使其更接近人类写作风格。

要求：
1. 替换模板化连接词（首先、其次、因此、然而等）为更自然的表达
2. 消除空洞修饰词（非常重要、十分关键等）
3. 避免重复句式结构
4. 增加具体细节和量化表达
5. 保持学术严谨性和专业术语
6. 使用更口语化但仍学术的表达方式

原文：
'''

print('Sending to LLM for rewriting...')
try:
    response = llm.invoke([HumanMessage(content=DEAI_PROMPT + thesis_content)])
    if hasattr(response, 'content'):
        rewritten = response.content
    else:
        rewritten = str(response)

    print(f'Response length: {len(rewritten)} chars')

    deai_path = 'output/test_thesis_deai.md'
    with open(deai_path, 'w', encoding='utf-8') as f:
        f.write(rewritten)
    print(f'[OK] Saved to: {deai_path}')

    from src.tools.aigc_detector import detect_aigc
    result = detect_aigc(rewritten)
    print(f'\nNew AIGC Score: {result["aigc_score"]}%')

except Exception as e:
    print(f'Error: {e}')