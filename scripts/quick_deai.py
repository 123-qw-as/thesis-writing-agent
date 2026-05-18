import os, sys
sys.path.insert(0, '.')
os.environ['MINIMAX_API_KEY'] = 'sk-cp-D0MsxcdMlbmX8bJNvhTXjM8MyViiLof_eqMAPSKYHxNrSKa9DDd1cvlT9UQ52n0Mg2jfa4avTEmyEMMMcnEkqjfBFVTAcrvUMsWgOcSYakxvc9QL1BtQnW4'

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response

print('Step 6: LLM De-AI Rewrite')

llm = ChatAnthropic(
    model='MiniMax-M2.7',
    temperature=0.7,
    api_key=os.environ['MINIMAX_API_KEY'],
    base_url='https://api.minimaxi.com/anthropic',
    max_tokens=8192
)

with open('output/test_thesis.md', 'r', encoding='utf-8') as f:
    thesis = f.read()

print('Loaded: ' + str(len(thesis)) + ' chars')

prompt = '''将以下学术论文改写，消除AI写作特征。保持学术严谨但使用更自然的人类表达方式。

论文：
''' + thesis[:8000]

print('Sending request...')
response = llm.invoke([HumanMessage(content=prompt)])
text = extract_text_from_response(response)
print('Response: ' + str(len(text)) + ' chars')

with open('output/test_thesis_deai.md', 'w', encoding='utf-8') as f:
    f.write(text)

from src.tools.aigc_detector import detect_aigc
result = detect_aigc(text)
aigc_score = result['aigc_score']
print('AIGC Score: ' + str(aigc_score) + '%')