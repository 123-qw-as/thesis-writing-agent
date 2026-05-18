"""
迭代改进循环 - 持续优化论文直至达到预期目标
目标: Overall >= 8.0, AIGC < 15%, Data Auth >= 95%
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
print('ITERATIVE IMPROVEMENT LOOP')
print('Goal: Overall >= 8.0, AIGC < 15%, Data Auth >= 95%')
print('='*60)

llm = ChatAnthropic(
    model='MiniMax-M2.7',
    temperature=0.7,
    api_key=os.environ['MINIMAX_API_KEY'],
    base_url='https://api.minimaxi.com/anthropic',
    max_tokens=16384
)

iteration = 0
max_iterations = 5

current_thesis_path = 'output/test_thesis_clean.md'

with open(current_thesis_path, 'r', encoding='utf-8') as f:
    thesis = f.read()

print('Initial thesis length:', len(thesis), 'chars')

async def evaluate_thesis(thesis_content, iteration):
    from src.agents.evaluation.agent import evaluate_thesis as eval_func
    return await eval_func(thesis_content, '基于LangChain框架的检索增强生成系统研究与实现', iteration)

while iteration < max_iterations:
    iteration += 1
    print('\n' + '='*60)
    print(f'Iteration {iteration}/{max_iterations}')
    print('='*60)

    # Check current quality
    aigc = detect_aigc(thesis)
    data = verify_data(thesis)

    print('\n[Current Status]')
    print('  AIGC Score: ' + str(aigc['aigc_score']) + '% (target: <15%)')
    print('  Data Auth: ' + str(data['authenticity_score']) + '% (target: >=95%)')

    # Run full evaluation
    import asyncio
    report = asyncio.run(evaluate_thesis(thesis, iteration))

    print('  Overall Score: ' + str(report.overall_score) + '/10 (target: >=8.0)')
    print('  Pass Status: ' + ('PASS' if report.is_pass else 'FAIL'))

    if report.is_pass:
        print('\n*** PASS - All thresholds met! ***')
        break

    # Identify issues
    issues = report.issues[:3]
    print('\n[Top Issues]')
    for i, issue in enumerate(issues, 1):
        print('  ' + str(i) + '. ' + str(issue.get('description', ''))[:60])

    # Strategy: Use LLM to improve
    print('\n[Applying Improvements...]')

    improvement_prompt = '''请改进以下学术论文，消除以下问题：

问题列表：
''' + '\n'.join(['- ' + str(issue.get('description', '')) for issue in issues[:3]])

    improvement_prompt += '''

改进要求：
1. 增加研究贡献声明
2. 完善方法论描述，添加评估指标
3. 增强创新点表述
4. 保持学术规范语气
5. 不要添加可疑数据（如完美分数100%）

论文内容：
''' + thesis[:10000]

    try:
        response = llm.invoke([HumanMessage(content=improvement_prompt)])
        improved_text = extract_text_from_response(response)

        if len(improved_text) > len(thesis) * 0.5:
            thesis = improved_text
            print('  -> LLM improvement applied')
        else:
            print('  -> LLM response too short, keeping current version')
    except Exception as e:
        print('  -> LLM improvement failed: ' + str(e)[:50])

    # Save current state
    output_path = 'output/thesis_iteration_' + str(iteration) + '.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(thesis)
    print('  -> Saved to: ' + output_path)

print('\n' + '='*60)
print('LOOP COMPLETED')
print('='*60)

# Final evaluation
import asyncio
final_report = asyncio.run(evaluate_thesis(thesis, iteration))

print('\n[FINAL RESULTS]')
print('Overall Score: ' + str(final_report.overall_score) + '/10')
print('AIGC Score: ' + str(final_report.aigc_score) + '%')
print('Data Authenticity: ' + str(final_report.data_authenticity) + '%')
print('Pass Status: ' + ('PASS' if final_report.is_pass else 'FAIL'))

if final_report.is_pass:
    # Save final thesis
    with open('output/test_thesis_final_pass.md', 'w', encoding='utf-8') as f:
        f.write(thesis)
    print('\nFinal thesis saved to: output/test_thesis_final_pass.md')