"""
Feedback Loop - 基于评估反馈驱动Agent输出改进
根据错误类型选择合适的修复策略，修改Prompt重新调用LLM
"""
import json
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response
from src.evaluation.judge import LLMJudge, EvaluationResult
from src.evaluation.error_analyzer import ErrorAnalyzer, ErrorReport, ErrorCategory


FEEDBACK_PROMPTS = {
    'literature': '''你是一个文献调研Agent。你之前的输出存在以下问题：

问题列表：
{issues_text}

请根据上述反馈改进你的输出。要求：
1. 保留所有正确内容，只修复标注的问题
2. 补充缺失的关键论文和引用
3. 细化研究Gap分析（每个Gap不少于50字）
4. 确保所有论文信息准确可查

原始输出：
{original_output}

请输出改进后的JSON格式结果：''',

    'method': '''你是一个方法设计Agent。你之前的设计存在以下问题：

问题列表：
{issues_text}

请根据反馈改进方法设计。要求：
1. 确保方法名称具体且有意义
2. 补充架构细节和关键组件描述
3. 明确创新点，与现有方法做对比
4. 考虑计算资源约束

原始输出（JSON格式）：
{original_output}

请输出改进后的JSON结果：''',

    'experiment': '''你是一个实验设计Agent。之前的实验设计存在以下问题：

问题列表：
{issues_text}

请根据反馈改进实验设计。要求：
1. 确保指标完备
2. 数据范围合理
3. 如果使用模拟数据，必须标记is_simulated=true
4. 多组运行之间应有合理差异

原始输出：
{original_output}

请输出改进后的JSON结果：''',

    'writing': '''你是一个学术写作Agent。之前的论文存在以下问题：

问题列表：
{issues_text}

请根据反馈改进论文。要求：
1. 补充缺失的章节
2. 确保摘要准确反映正文内容
3. 统一术语和数字
4. 保证引用格式规范

论文内容：
{original_output}

请输出改进后的完整论文：''',
}


class FeedbackLoop:
    """反馈循环 - 评估→修复→重评估"""

    def __init__(self, llm, max_iterations: int = 3):
        self.llm = llm
        self.max_iterations = max_iterations

    def improve(
        self,
        output: Any,
        agent_type: str,
        rubric,
        error_analyzer_func=None,
        context: dict = None
    ) -> Any:
        """
        对Agent输出执行评估→修复循环
        
        Args:
            output: Agent输出
            agent_type: Agent类型 (literature/method/experiment/writing)
            rubric: 对应的评估Rubric
            error_analyzer_func: 专用错误分析函数
            context: 上下文信息
            
        Returns:
            改进后的输出
        """
        llm_judge = LLMJudge(self.llm)

        for iteration in range(self.max_iterations):
            # 1. 用Rubric评估
            eval_result = rubric.evaluate(output)

            # 2. 错误分析
            error_report = None
            if error_analyzer_func:
                error_report = error_analyzer_func(output)
            else:
                error_report = ErrorAnalyzer.from_evaluation(eval_result, agent_type)

            # 3. 判断是否通过
            if error_report.passes() and eval_result.passes():
                print(f'  [Feedback] {agent_type} 通过评估 (迭代{iteration+1})')
                break

            # 4. 生成修复并应用
            if iteration < self.max_iterations - 1:
                output = self._apply_fixes(
                    output, agent_type, error_report, eval_result
                )
                print(f'  [Feedback] {agent_type} 修复完成 (迭代{iteration+1})')
            else:
                print(f'  [Feedback] {agent_type} 达到最大迭代次数')

        return output

    def _apply_fixes(
        self,
        output: Any,
        agent_type: str,
        error_report: ErrorReport,
        eval_result: EvaluationResult
    ) -> Any:
        """根据错误报告应用修复"""
        issues_text = self._format_issues(error_report, eval_result)
        original_text = self._format_output(output)
        prompt_template = FEEDBACK_PROMPTS.get(agent_type, FEEDBACK_PROMPTS['writing'])
        prompt = prompt_template.format(
            issues_text=issues_text,
            original_output=original_text
        )

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw = extract_text_from_response(response)

            if isinstance(output, dict):
                try:
                    import re
                    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                except (json.JSONDecodeError, Exception):
                    pass
                return output
            else:
                if len(raw) > len(str(output)) * 0.3:
                    return raw
                return output
        except Exception as e:
            print(f'  [Feedback] 修复失败: {e}')
            return output

    def _format_issues(self, error_report: ErrorReport, eval_result: EvaluationResult) -> str:
        """格式化问题描述"""
        parts = []
        for error in error_report.errors[:5]:
            parts.append(f'- [{error.severity.upper()}] {error.location}: {error.description}')
        for dim in eval_result.dimensions:
            if dim.score <= 2:
                parts.append(f'- [MEDIUM] {dim.name}: 评分{dim.score}/5 - {dim.reasoning}')
        return '\n'.join(parts)

    def _format_output(self, output: Any) -> str:
        """格式化输出内容"""
        if isinstance(output, str):
            return output[:5000]
        if isinstance(output, dict):
            return json.dumps(output, ensure_ascii=False, indent=2)[:5000]
        return str(output)[:5000]