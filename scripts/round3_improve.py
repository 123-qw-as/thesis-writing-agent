import sys
sys.path.insert(0, '.')

import os
os.environ['MINIMAX_API_KEY'] = 'sk-cp-D0MsxcdMlbmX8bJNvhTXjM8MyViiLof_eqMAPSKYHxNrSKa9DDd1cvlT9UQ52n0Mg2jfa4avTEmyEMMMcnEkqjfBFVTAcrvUMsWgOcSYakxvc9QL1BtQnW4'

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
import asyncio
from src.agents.evaluation.agent import evaluate_thesis

print('='*60)
print('IMPROVEMENT ROUND 3 - Focus on Overall Score')
print('='*60)

llm = ChatAnthropic(
    model='MiniMax-M2.7',
    temperature=0.5,
    api_key=os.environ['MINIMAX_API_KEY'],
    base_url='https://api.minimaxi.com/anthropic',
    max_tokens=16384
)

with open('output/test_thesis_round2.md', 'r', encoding='utf-8') as f:
    thesis = f.read()

print('Current length:', len(thesis), 'chars')

prompt = '''请扩展并完善以下学术论文，提升论文质量和完整性。

具体要求：
1. 增加研究贡献声明（明确列出3-4个贡献点）
2. 补充方法论章节，添加具体评估指标
3. 添加基线对比说明
4. 增强原创性描述，明确创新点
5. 保持现有结构不变
6. 不要添加任何新的数据数字（避免降低数据真实性）
7. 保持自然的写作风格，避免AI模板句式

论文：
''' + thesis

print('Sending to LLM...')
try:
    response = llm.invoke([HumanMessage(content=prompt)])
    improved = extract_text_from_response(response)
    print('Response length:', len(improved), 'chars')

    with open('output/test_thesis_round3.md', 'w', encoding='utf-8') as f:
        f.write(improved)

    async def eval():
        return await evaluate_thesis(improved, '基于LangChain框架的检索增强生成系统研究与实现', 4)

    report = asyncio.run(eval())

    print('\n--- Full Evaluation ---')
    print('Overall:', report.overall_score, '/10 (need >=8.0)')
    print('AIGC:', report.aigc_score, '% (need <15%)')
    print('Data Auth:', report.data_authenticity, '% (need >=95%)')
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