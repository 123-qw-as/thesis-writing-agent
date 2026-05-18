"""
De-AI Agent - 降低论文的AIGC特征，使其更接近人类写作风格
基于Trivium项目的De-AI rewrite实现
"""

from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage
from langchain_anthropic import ChatAnthropic
from src.utils.llm_utils import extract_text_from_response


DEAI_SYSTEM_PROMPT = """你是一个专业的学术写作编辑，专门帮助将AI生成的文本改写成更自然的人类写作风格。

你的任务是检测并改写论文中具有明显AI生成特征的文本，使其：
1. 保持原意和学术准确性
2. 消除AI写作的模板化痕迹
3. 增加语言的多样性和自然度
4. 使用更具体、更有特色的表达

## 需要消除的AI写作模式（24种）

### 1. 模板化连接词
- 过度使用：首先、其次、最后、因此、然而、但是
- 替换为：开篇、随后、在此基础上、基于此、但需要指出的是

### 2. 空洞修饰词
- 存在问题：非常重要、十分关键、具有重要意义、取得显著成果
- 替换为：需要认真对待、对实际应用有参考价值、在标准测试集上达到X%

### 3. 重复性句式
- 存在问题：...的方法、...的工作、...的研究、...的系统
- 替换为：具体技术名称或更精确的描述

### 4. 最高级夸张
- 存在问题：最优、最佳、最好、最高、最先进
- 替换为：相比基线提升XX%、达到主流水平

### 5. 缺乏具体细节
- 存在问题：等...技术、相关...方法、各种...算法
- 替换为：具体技术名称和实现细节

### 6. 模糊数量
- 存在问题：很多、许多、大量、丰富
- 替换为：具体数字或量化描述

### 7. AI特定声明缺乏细节
- 存在问题：利用深度学习、采用Transformer、通过神经网络
- 替换为：具体模型架构、参数数量、训练策略

## 改写原则

1. **保持学术规范**：改写后仍需保持学术论文的严谨性
2. **保留专业术语**：核心专业术语需要保留
3. **量化表达**：将模糊描述改为具体数字
4. **多样化句式**：避免重复使用相同的句式结构
5. **自然过渡**：使用更自然的话语标记

## 输出格式

请按以下格式输出改写后的论文：

<ORIGINAL>
[原文中有AIGC特征的段落]
</ORIGINAL>

<REWRITTEN>
[改写后的段落]
</REWRITTEN>

<CHANGES>
1. [具体改动说明]
2. [具体改动说明]
</CHANGES>"""


DEAI_REWRITE_PROMPT = """请分析并改写以下论文段落，消除AI写作特征：

{paper_content}

请识别并改写：
1. 模板化连接词和过渡语
2. 空洞的修饰词和夸张表述
3. 重复的句式结构
4. 缺乏具体细节的泛泛之谈
5. 不自然的AI特定表达

确保改写后：
- 保持学术严谨性
- 保留核心专业术语
- 增加量化表达
- 使用更自然的写作风格"""


class DeAIAgent:
    """De-AI改写Agent"""

    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm

    def rewrite(
        self,
        paper_content: str,
        llm: Optional[Any] = None,
        max_iterations: int = 2
    ) -> Dict[str, Any]:
        """
        改写论文以降低AIGC率

        Args:
            paper_content: 原始论文内容
            llm: Language model
            max_iterations: 最大改写轮次

        Returns:
            {
                "original_content": str,  # 原始内容
                "rewritten_content": str,  # 改写后内容
                "aigc_score_before": float,  # 改写前AIGC率
                "aigc_score_after": float,  # 改写后AIGC率
                "changes_count": int,  # 改动次数
                "iterations": int,  # 实际迭代次数
            }
        """
        effective_llm = llm or self.llm

        from src.tools.aigc_detector import detect_aigc

        aigc_before = detect_aigc(paper_content)
        aigc_score_before = aigc_before.get("aigc_score", 0.0)

        current_content = paper_content
        iterations = 0
        changes_log = []

        while iterations < max_iterations and aigc_score_before > 15.0:
            iterations += 1

            if effective_llm:
                rewritten = self._rewrite_with_llm(current_content, effective_llm)
            else:
                from src.tools.aigc_detector import reduce_aigc
                rewritten = reduce_aigc(current_content, intensity="medium")

            aigc_after = detect_aigc(rewritten)
            aigc_score_after = aigc_after.get("aigc_score", aigc_score_before)

            changes = self._count_changes(current_content, rewritten)
            changes_log.append({
                "iteration": iterations,
                "aigc_score": aigc_score_after,
                "changes": changes
            })

            if aigc_score_after >= aigc_score_before:
                break

            current_content = rewritten

        return {
            "original_content": paper_content,
            "rewritten_content": current_content,
            "aigc_score_before": aigc_score_before,
            "aigc_score_after": aigc_score_after,
            "changes_count": sum(c["changes"] for c in changes_log),
            "iterations": iterations,
            "changes_log": changes_log
        }

    def _rewrite_with_llm(self, content: str, llm) -> str:
        """使用LLM进行改写"""
        try:
            response = llm.invoke([
                HumanMessage(content=DEAI_REWRITE_PROMPT.format(paper_content=content))
            ])

            text = extract_text_from_response(response)

            rewritten = self._extract_section(text, "REWRITTEN")
            if rewritten:
                return rewritten

            return text if len(text) > len(content) * 0.5 else content

        except Exception as e:
            print(f"[WARN] LLM rewrite failed: {e}")
            from src.tools.aigc_detector import reduce_aigc
            return reduce_aigc(content, intensity="medium")

    def _extract_section(self, text: str, section: str) -> Optional[str]:
        """提取指定section的内容"""
        import re
        pattern = rf'<{section}>(.*?)</{section}>'
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else None

    def _count_changes(self, original: str, rewritten: str) -> int:
        """计算改动次数"""
        if original == rewritten:
            return 0

        original_words = set(original.split())
        rewritten_words = set(rewritten.split())

        changes = len(rewritten_words - original_words) + len(original_words - rewritten_words)
        return min(changes, 100)


class HumanizationReviewer:
    """人类化风格审查员 - 评估改写后的文本是否足够自然"""

    HUMANITY_CHECKS = [
        ("has_template_phrases", "是否包含模板化短语"),
        ("uses_vague_modifiers", "是否使用空洞修饰词"),
        ("has_repetitive_structure", "是否有重复性句式"),
        ("lacks_specificity", "是否缺乏具体细节"),
        ("uses_superlatives", "是否使用最高级夸张"),
        ("has_ai_specific_vague", "是否有AI相关的模糊表述"),
    ]

    def review(self, text: str) -> Dict[str, Any]:
        """
        审查文本的人类化程度

        Returns:
            {
                "humanity_score": float,  # 0-100, 越高越像人类
                "issues": [...],
                "suggestions": [...],
            }
        """
        from src.tools.aigc_detector import detect_aigc

        aigc_result = detect_aigc(text)
        aigc_score = aigc_result.get("aigc_score", 50.0)

        humanity_score = 100.0 - aigc_score

        issues = []
        suggestions = []

        detected = aigc_result.get("detected_patterns", [])
        for pattern in detected:
            if pattern.get("count", 0) >= 3:
                issues.append({
                    "type": pattern.get("type"),
                    "description": pattern.get("description"),
                    "count": pattern.get("count")
                })

        if humanity_score < 70:
            suggestions.append("文本仍有一定AI特征，建议进一步改写")
        if humanity_score < 50:
            suggestions.append("AI特征明显，需要大幅改写")

        return {
            "humanity_score": round(humanity_score, 1),
            "aigc_score": round(aigc_score, 1),
            "issues": issues,
            "suggestions": suggestions
        }


def rewrite_to_human_style(
    paper_content: str,
    llm: Optional[Any] = None
) -> Dict[str, Any]:
    """快捷De-AI改写函数"""
    agent = DeAIAgent(llm)
    return agent.rewrite(paper_content, llm)