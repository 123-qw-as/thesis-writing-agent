import sys
sys.path.insert(0, '.')

import os
os.environ['MINIMAX_API_KEY'] = 'sk-cp-D0MsxcdMlbmX8bJNvhTXjM8MyViiLof_eqMAPSKYHxNrSKa9DDd1cvlT9UQ52n0Mg2jfa4avTEmyEMMMcnEkqjfBFVTAcrvUMsWgOcSYakxvc9QL1BtQnW4'

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from src.tools.aigc_detector import detect_aigc
from src.tools.data_verifier import verify_data
import asyncio
from src.agents.evaluation.agent import evaluate_thesis

print('='*60)
print('IMPROVEMENT ROUND 2')
print('='*60)

llm = ChatAnthropic(
    model='MiniMax-M2.7',
    temperature=0.5,
    api_key=os.environ['MINIMAX_API_KEY'],
    base_url='https://api.minimaxi.com/anthropic',
    max_tokens=8192
)

with open('output/test_thesis_llm_improved.md', 'r', encoding='utf-8') as f:
    thesis = f.read()

print('Original length:', len(thesis), 'chars')

prompt = '''将以下学术论文进行轻度改写，重点减少AI写作特征，使其更像人类写作。

改写要点：
1. 将"首先"改为"开篇"或直接开始
2. 将"其次"改为"随后"或"接下来"
3. 将"最后"改为"在此基础上"或省略
4. 将"因此"改为"基于此"或"从而"
5. 将"然而"改为"不过"或"但"
6. 将"但是"改为"不过"或省略
7. 避免重复的句式开头

保持所有内容不变，只修改连接词和过渡词。

论文：
''' + thesis[:12000]

print('Sending to LLM...')
try:
    response = llm.invoke([HumanMessage(content=prompt)])
    improved = extract_text_from_response(response)
    print('Response length:', len(improved), 'chars')

    with open('output/test_thesis_round2.md', 'w', encoding='utf-8') as f:
        f.write(improved)

    aigc = detect_aigc(improved)
    data = verify_data(improved)

    print('\n--- Quality After Round 2 ---')
    print('AIGC Score:', aigc['aigc_score'], '%')
    print('Data Auth:', data['authenticity_score'], '%')
    print('Suspicious:', len(data['suspicious_data_points']))

    async def eval():
        return await evaluate_thesis(improved, '基于LangChain框架的检索增强生成系统研究与实现', 3)

    report = asyncio.run(eval())

    print('\n--- Full Evaluation ---')
    print('Overall:', report.overall_score, '/10')
    print('AIGC:', report.aigc_score, '%')
    print('Data Auth:', report.data_authenticity, '%')
    print('Pass:', 'YES' if report.is_pass else 'NO')

    if report.is_pass:
        print('\n*** ALL THRESHOLDS MET - PASS! ***')
        with open('output/test_thesis_FINAL_PASS.md', 'w', encoding='utf-8') as f:
            f.write(improved)
        print('Saved to: output/test_thesis_FINAL_PASS.md')

except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()