import sys
sys.path.insert(0, '.')

print('='*60)
print('Step 7: Add Missing Chapters (Conclusion + References)')
print('='*60)

with open('output/test_thesis_deai.md', 'r', encoding='utf-8') as f:
    thesis = f.read()

conclusion = '''
---

## 第六章 结论

### 6.1 研究工作总结

本文围绕基于LangChain框架的检索增强生成系统，深入研究了Tavily Search API在LangChain环境中的集成技术与配置方法。通过系统分析API密钥认证机制、环境变量管理策略以及错误处理流程，本文提出了切实可行的系统化解决方案。

在研究过程中，本文主要完成了以下工作：首先，对LangChain框架的核心架构和设计理念进行了详细剖析，明确了其在RAG系统中的定位和优势；其次，针对Tavily API的集成问题，从环境配置、代码实现两个层面进行了深入分析，找出了问题的根本原因；最后，在解决方案的设计上，本文提出了三种可行方案（环境变量配置、参数直接传入、混合配置策略），并给出了最佳实践建议。

### 6.2 研究成果与创新

本研究的主要成果和创新点体现在以下几个方面：

1. **系统化的解决方案**：不同于已有的零散资料，本文提供了从问题诊断到解决方案的完整技术路径，涵盖了开发者在实际项目中可能遇到的各类场景。

2. **实用性的代码实现**：本文提供的代码示例具有高度的可复用性，开发者可以直接将搜索检索器封装类和RAG应用主类应用到实际项目中。

3. **完善的配置管理**：通过使用pydantic进行配置管理，实现了环境变量和配置文件的统一管理，提高了系统的可维护性。

4. **健壮的错误处理**：系统实现了针对不同异常类型的清晰错误提示，便于开发者快速定位和解决问题。

### 6.3 研究局限与展望

尽管本文取得了预期的研究成果，但仍存在一些局限性需要在后续工作中加以改进：

首先，在实验验证方面，由于条件限制，本文未能进行大规模的实地测试，所提方案在超大规模RAG系统中的表现有待进一步验证。其次，在API密钥管理方面，本文主要关注了开发环境下的配置问题，对于生产环境下的密钥轮换、安全审计等问题涉及较少。

展望未来，RAG技术将会在以下方向取得进一步突破：一是多模态RAG的发展，使得系统能够处理图像、音频等多种类型的输入；二是知识图谱与RAG的深度融合，提高检索的准确性和可解释性；三是个性化RAG的研究，使系统能够根据用户偏好动态调整检索策略。

### 6.4 小结

综上所述，本文对基于LangChain和Tavily的RAG系统集成技术进行了系统性的研究与实践，提供了完整的解决方案和可复用的代码实现。本研究对于推动RAG技术在生产环境中的广泛应用具有重要的参考价值。

---

## 参考文献

[1] Harrison Chase. LangChain Documentation. 2022. https://python.langchain.com/

[2] Tavily. Tavily Search API Documentation. AnswerTheAI. https://docs.tavily.com/

[3] Patrick Lewis, Ethan Perez, et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. Advances in Neural Information Processing Systems, 2020.

[4] Jacob Devlin, Ming-Wei Chang, et al. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. arXiv:1810.04805, 2018.

[5] Ashish Vaswani, Noam Shazeer, et al. Attention Is All You Need. Advances in Neural Information Processing Systems, 2017.

[6] Tom Brown, Benjamin Mann, et al. Language Models are Few-Shot Learners. Advances in Neural Information Processing Systems, 2020.

[7] OpenAI. ChatGPT: Optimizing Language Models for Dialogue. 2022. https://openai.com/blog/chatgpt/

[8] AWS Secrets Manager Documentation. Amazon Web Services. https://docs.aws.amazon.com/secretsmanager/

[9] HashiCorp Vault Documentation. https://www.vaultproject.io/docs

[10] Pydantic Settings Documentation. https://docs.pydantic.dev/latest/usage/settings/
'''

thesis_with_chapters = thesis.rstrip() + '\n\n' + conclusion

with open('output/test_thesis_complete.md', 'w', encoding='utf-8') as f:
    f.write(thesis_with_chapters)

print('Added: Conclusion (6.1-6.4) and References (10 items)')
print('Total length: ' + str(len(thesis_with_chapters)) + ' chars')
print('Saved to: output/test_thesis_complete.md')