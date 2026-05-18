import os, sys, re
sys.path.insert(0, '.')
os.environ['MINIMAX_API_KEY'] = 'sk-cp-D0MsxcdMlbmX8bJNvhTXjM8MyViiLof_eqMAPSKYHxNrSKa9DDd1cvlT9UQ52n0Mg2jfa4avTEmyEMMMcnEkqjfBFVTAcrvUMsWgOcSYakxvc9QL1BtQnW4'

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response

print('='*60)
print('Complete De-AI Rewrite with Full Thesis')
print('='*60)

llm = ChatAnthropic(model='MiniMax-M2.7', temperature=0.7, api_key=os.environ['MINIMAX_API_KEY'], base_url='https://api.minimaxi.com/anthropic', max_tokens=16384)

with open('output/test_thesis.md', 'r', encoding='utf-8') as f:
    thesis = f.read()

print('Original thesis: ' + str(len(thesis)) + ' chars')

# Split into sections for processing
sections = thesis.split('\n## ')
print('Split into ' + str(len(sections)) + ' sections')

rewritten_sections = []

for i, section in enumerate(sections):
    if i == 0:
        # First section (before ##)
        rewritten_sections.append(section)
        continue

    full_section = '\n## ' + section
    print('Processing section ' + str(i+1) + '... (' + str(len(full_section)) + ' chars)')

    prompt = '''将以下学术论文章节改写，消除AI写作特征（模板化连接词、空洞修饰词、重复句式），使其更自然。保持学术严谨但使用更口语化但仍学术的表达。

章节：
''' + full_section

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        text = extract_text_from_response(response)
        rewritten_sections.append(text)
        print('  -> ' + str(len(text)) + ' chars')
    except Exception as e:
        print('  -> Error: ' + str(e)[:50] + ', keeping original')
        rewritten_sections.append(full_section)

rewritten = ''.join(rewritten_sections)
print('\nTotal rewritten: ' + str(len(rewritten)) + ' chars')

# Add conclusion and references
conclusion = '''
---

## 第六章 结论

### 6.1 研究工作总结

本文围绕基于LangChain框架的检索增强生成系统，深入研究了Tavily Search API在LangChain环境中的集成技术与配置方法。通过系统分析API密钥认证机制、环境变量管理策略以及错误处理流程，本文提出了切实可行的系统化解决方案。

在研究过程中，本文主要完成了以下工作：首先，对LangChain框架的核心架构和设计理念进行了详细剖析；其次，针对Tavily API的集成问题，从环境配置、代码实现两个层面进行了深入分析；最后，在解决方案的设计上，本文提出了三种可行方案（环境变量配置、参数直接传入、混合配置策略），并给出了最佳实践建议。

### 6.2 研究成果与创新

本研究的主要成果和创新点体现在以下几个方面：

1. 系统化的解决方案：本文提供了从问题诊断到解决方案的完整技术路径，涵盖了开发者实际项目中可能遇到的各类场景。
2. 实用性的代码实现：本文提供的代码示例具有高度的可复用性，开发者可以直接应用到实际项目中。
3. 完善的配置管理：通过使用pydantic进行配置管理，实现了环境变量和配置文件的统一管理。
4. 健壮的错误处理：系统实现了针对不同异常类型的清晰错误提示。

### 6.3 研究局限与展望

尽管本文取得了预期的研究成果，但仍存在一些局限性：实验验证方面未能进行大规模实地测试；在API密钥管理方面，对于生产环境下的密钥轮换等问题涉及较少。

展望未来，RAG技术将会在以下方向取得进一步突破：一是多模态RAG的发展；二是知识图谱与RAG的深度融合；三是个性化RAG的研究。

### 6.4 小结

综上所述，本文对基于LangChain和Tavily的RAG系统集成技术进行了系统性的研究与实践，提供了完整的解决方案和可复用的代码实现。

---

## 参考文献

[1] Harrison Chase. LangChain Documentation. 2022. https://python.langchain.com/

[2] Tavily. Tavily Search API Documentation. AnswerTheAI. https://docs.tavily.com/

[3] Patrick Lewis, Ethan Perez, et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 2020.

[4] Jacob Devlin, Ming-Wei Chang, et al. BERT: Pre-training of Deep Bidirectional Transformers. arXiv:1810.04805, 2018.

[5] Ashish Vaswani, Noam Shazeer, et al. Attention Is All You Need. NeurIPS 2017.

[6] Tom Brown, Benjamin Mann, et al. Language Models are Few-Shot Learners. NeurIPS 2020.
'''

rewritten_with_conclusion = rewritten.rstrip() + '\n\n' + conclusion

with open('output/test_thesis_final.md', 'w', encoding='utf-8') as f:
    f.write(rewritten_with_conclusion)

print('Saved complete thesis to: output/test_thesis_final.md')
print('Total length: ' + str(len(rewritten_with_conclusion)) + ' chars')

# Run final evaluation
from src.tools.aigc_detector import detect_aigc
aigc_result = detect_aigc(rewritten_with_conclusion)
print('\nAIGC Score: ' + str(aigc_result['aigc_score']) + '%')
print('Risk Level: ' + aigc_result['risk_level'])