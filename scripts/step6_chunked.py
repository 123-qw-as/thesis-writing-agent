import os
import sys
sys.path.insert(0, '.')

os.environ['MINIMAX_API_KEY'] = 'sk-cp-D0MsxcdMlbmX8bJNvhTXjM8MyViiLof_eqMAPSKYHxNrSKa9DDd1cvlT9UQ52n0Mg2jfa4avTEmyEMMMcnEkqjfBFVTAcrvUMsWgOcSYakxvc9QL1BtQnW4'

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response

print('='*60)
print('Step 6: LLM-based De-AI Rewrite (Chunked)')
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

parts = thesis_content.split('\n\n')
print(f'Split into {len(parts)} paragraphs')

rewritten_parts = []
for i, part in enumerate(parts):
    if len(part.strip()) < 50:
        rewritten_parts.append(part)
        continue

    print(f'Processing paragraph {i+1}/{len(parts)}...')

    prompt = f'''请将以下段落改写，消除AI写作特征（模板化连接词、空洞修饰词、重复句式），使其更自然。

段落：
{part}

改写后：'''

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        text = extract_text_from_response(response)
        rewritten_parts.append(text)
        print(f'  -> {len(text)} chars')
    except Exception as e:
        print(f'  -> Error: {e}, keeping original')
        rewritten_parts.append(part)

rewritten = '\n\n'.join(rewritten_parts)
print(f'\nTotal rewritten: {len(rewritten)} chars')

deai_path = 'output/test_thesis_deai.md'
with open(deai_path, 'w', encoding='utf-8') as f:
    f.write(rewritten)
print(f'[OK] Saved to: {deai_path}')

from src.tools.aigc_detector import detect_aigc
result = detect_aigc(rewritten)
print(f'\nNew AIGC Score: {result["aigc_score"]}%')
print(f'Risk Level: {result["risk_level"]}')