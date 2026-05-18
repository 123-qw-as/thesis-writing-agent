"""
快速AIGC降低脚本 - 只专注于降低AIGC率
"""
import sys
sys.path.insert(0, '.')

import os
os.environ['MINIMAX_API_KEY'] = 'sk-cp-D0MsxcdMlbmX8bJNvhTXjM8MyViiLof_eqMAPSKYHxNrSKa9DDd1cvlT9UQ52n0Mg2jfa4avTEmyEMMMcnEkqjfBFVTAcrvUMsWgOcSYakxvc9QL1BtQnW4'

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from src.tools.aigc_detector import detect_aigc
import asyncio
from src.agents.evaluation.agent import evaluate_thesis

print('='*60)
print('FAST AIGC REDUCTION')
print('='*60)

llm = ChatAnthropic(
    model='MiniMax-M2.7',
    temperature=0.5,
    api_key=os.environ['MINIMAX_API_KEY'],
    base_url='https://api.minimaxi.com/anthropic',
    max_tokens=8192
)

with open('output/test_thesis_best_current.md', 'r', encoding='utf-8') as f:
    thesis = f.read()

print(f'Starting thesis: {len(thesis)} chars')

aigc = detect_aigc(thesis)
print(f'Starting AIGC: {aigc["aigc_score"]}%')
print(f'Patterns found:')
for p in aigc['detected_patterns'][:3]:
    print(f'  - {p["description"]}: {p["count"]} instances')

for round_num in range(1, 4):
    print(f'\n--- Round {round_num} ---')

    prompt = f'''将以下学术论文进行深度改写，消除所有AI写作特征。

重点消除以下内容：
1. 模板化连接词：首先、其次、最后、因此、然而、但是、此外、与此同时、综上所述、总之、值得注意的是
2. 空洞修饰词：非常重要、十分关键、具有重要意义、取得了显著成果、非常好、极为出色
3. 重复句式结构：...的工作、...的研究、...的方法、...的系统
4. 最高级夸张：最优、最佳、最好、最高、最先进、显著提升、大幅改进
5. 模糊数量：很多、许多、大量、丰富、各种

改写要求：
- 替换为自然、口语化但仍学术的表达
- 保持所有技术内容不变
- 不要添加或删除任何实质内容
- 保持论文长度基本不变

论文：
{thesis}'''

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        rewritten = extract_text_from_response(response)
        print(f'Response: {len(rewritten)} chars')

        new_aigc = detect_aigc(rewritten)
        print(f'New AIGC: {new_aigc["aigc_score"]}%')

        if new_aigc["aigc_score"] < aigc["aigc_score"]:
            thesis = rewritten
            aigc = new_aigc
            print('Improved!')
        else:
            print('No improvement, trying different approach...')

            prompt2 = f'''请将以下中文论文改写成更自然的人类写作风格。将每句话用不同的方式重新表达，消除所有模板化的AI表达。

原文：
{thesis[:8000]}'''

            response2 = llm.invoke([HumanMessage(content=prompt2)])
            rewritten2 = extract_text_from_response(response2)

            new_aigc2 = detect_aigc(rewritten2)
            print(f'Alt approach AIGC: {new_aigc2["aigc_score"]}%')

            if new_aigc2["aigc_score"] < aigc["aigc_score"]:
                thesis = rewritten2
                aigc = new_aigc2

    except Exception as e:
        print(f'Error: {e}')

    if aigc["aigc_score"] < 15:
        print('Target AIGC reached!')
        break

print(f'\nFinal AIGC: {aigc["aigc_score"]}%')

with open('output/test_thesis_low_aigc.md', 'w', encoding='utf-8') as f:
    f.write(thesis)

print('Saved to: output/test_thesis_low_aigc.md')

async def eval():
    return await evaluate_thesis(thesis, '基于LangChain框架', 6)

report = asyncio.run(eval())

print('\n--- Full Evaluation ---')
print('Overall:     ' + str(report.overall_score) + '/10')
print('AIGC:        ' + str(report.aigc_score) + '%')
print('Data Auth:   ' + str(report.data_authenticity) + '%')
print('Status:      ' + ('PASS' if report.is_pass else 'FAIL'))