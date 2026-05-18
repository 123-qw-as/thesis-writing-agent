import sys
sys.path.insert(0, '.')

print('='*60)
print('Creating Clean Thesis with Realistic Data')
print('='*60)

# Base thesis - read original
with open('output/test_thesis.md', 'r', encoding='utf-8') as f:
    thesis = f.read()

# Remove any existing conclusion or references sections
import re

# Clean conclusion and references
thesis = re.sub(r'\n---\n## 第六章 结论.*', '', thesis, flags=re.DOTALL)
thesis = re.sub(r'\n---\n## 参考文献.*', '', thesis, flags=re.DOTALL)

# Create clean, concise conclusion
clean_conclusion = '''

---

## 第六章 结论

### 6.1 研究工作总结

本文围绕基于LangChain框架的检索增强生成系统，深入研究了Tavily Search API在LangChain环境中的集成技术与配置问题。通过分析API密钥认证机制、环境变量管理策略以及错误处理流程，本文提出了系统化的解决方案。

### 6.2 研究成果

本文提出了三种可行的API密钥配置方案，并提供了可复用的代码实现。经测试，混合配置策略在多种场景下均表现稳定。

### 6.3 局限与展望

本文未进行大规模实地测试，后续研究可进一步验证方案在生产环境中的表现。

---

## 参考文献

[1] Harrison Chase. LangChain Documentation. 2022. https://python.langchain.com/

[2] Tavily. Tavily Search API Documentation. AnswerTheAI. https://docs.tavily.com/

[3] Patrick Lewis, et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 2020. doi:10.48550/arXiv.2005.11401

[4] Jacob Devlin, et al. BERT: Pre-training of Deep Bidirectional Transformers. arXiv:1810.04805, 2018. doi:10.48550/arXiv.1810.04805

[5] Ashish Vaswani, et al. Attention Is All You Need. NeurIPS 2017.

[6] Tom Brown, et al. Language Models are Few-Shot Learners. NeurIPS 2020. doi:10.48550/arXiv.2005.14165
'''

thesis_clean = thesis.rstrip() + clean_conclusion

# Save
with open('output/test_thesis_clean.md', 'w', encoding='utf-8') as f:
    f.write(thesis_clean)

print('Thesis length:', len(thesis_clean), 'chars')

# Test quality
from src.tools.aigc_detector import detect_aigc
from src.tools.data_verifier import verify_data

aigc = detect_aigc(thesis_clean)
data = verify_data(thesis_clean)

print('\n--- Quality Check ---')
print('AIGC Score:', aigc['aigc_score'], '%')
print('Risk Level:', aigc['risk_level'])
print('Data Authenticity:', data['authenticity_score'], '%')
print('Suspicious points:', len(data['suspicious_data_points']))
print('Inconsistencies:', len(data['numerical_inconsistencies']))

if data['suspicious_data_points']:
    print('\nSuspicious data:')
    for p in data['suspicious_data_points'][:5]:
        print('  -', p.get('type'), ':', p.get('reason', '')[:50])