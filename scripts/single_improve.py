"""
Single improvement pass with LLM
"""
import sys
sys.path.insert(0, '.')

import os
os.environ['MINIMAX_API_KEY'] = 'sk-cp-D0MsxcdMlbmX8bJNvhTXjM8MyViiLof_eqMAPSKYHxNrSKa9DDd1cvlT9UQ52n0Mg2jfa4avTEmyEMMMcnEkqjfBFVTAcrvUMsWgOcSYakxvc9QL1BtQnW4'

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from src.tools.aigc_detector import detect_aigc
from src.tools.data_verifier import verify_data

print('='*60)
print('Single LLM Improvement Pass')
print('='*60)

llm = ChatAnthropic(
    model='MiniMax-M2.7',
    temperature=0.7,
    api_key=os.environ['MINIMAX_API_KEY'],
    base_url='https://api.minimaxi.com/anthropic',
    max_tokens=8192
)

with open('output/test_thesis_clean.md', 'r', encoding='utf-8') as f:
    thesis = f.read()

print('Original length:', len(thesis), 'chars')

# Quick improvement prompt - focus on reducing AIGC patterns
prompt = '''将以下学术论文改写，使其更接近人类写作风格，消除AI写作特征。

具体要求：
1. 替换"首先、其次、最后、因此、然而、但是"等模板词
2. 消除"非常重要、十分关键、具有重要意义"等空洞表达
3. 避免重复句式结构
4. 增加自然过渡和多样化表达
5. 保持学术严谨性和专业术语
6. 不要添加任何新的数据或数字

论文：
''' + thesis

print('Sending to LLM...')
try:
    response = llm.invoke([HumanMessage(content=prompt)])
    improved = extract_text_from_response(response)
    print('Response length:', len(improved), 'chars')

    # Save improved version
    with open('output/test_thesis_llm_improved.md', 'w', encoding='utf-8') as f:
        f.write(improved)

    # Check quality
    aigc = detect_aigc(improved)
    data = verify_data(improved)

    print('\n--- Quality After LLM ---')
    print('AIGC Score:', aigc['aigc_score'], '%')
    print('Risk Level:', aigc['risk_level'])
    print('Data Authenticity:', data['authenticity_score'], '%')

except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()