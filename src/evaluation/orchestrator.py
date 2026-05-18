"""
Evaluation Orchestrator - 统一评估调度器
集成到Pipeline中，在每个Agent输出后进行评估和反馈
"""
import json
from typing import Dict, List, Any, Optional
from src.evaluation.judge import LLMJudge, EvaluationResult
from src.evaluation.feedback_loop import FeedbackLoop
from src.evaluation.error_analyzer import ErrorAnalyzer
from src.evaluation.rubrics import (
    LiteratureRubric, MethodRubric, ExperimentRubric,
    WritingRubric, FigureRubric
)


class EvaluationOrchestrator:
    """
    评估调度器 - 接管Pipeline中所有评估点
    
    在每个Agent执行后调用:
    1. evaluate_and_fix() → 评估输出质量
    2. 如果不通过 → 反馈循环修复
    3. 返回改进后的输出
    """

    def __init__(self, llm):
        self.llm = llm
        self.judge = LLMJudge(llm)
        self.feedback = FeedbackLoop(llm)

        self.rubrics = {
            'research': LiteratureRubric(self.judge),
            'method': MethodRubric(self.judge),
            'experiment': ExperimentRubric(self.judge),
            'writing': WritingRubric(self.judge),
            'figure': FigureRubric(self.judge),
        }

        self.analyzers = {
            'research': ErrorAnalyzer.analyze_literature,
            'method': ErrorAnalyzer.analyze_method,
            'experiment': ErrorAnalyzer.analyze_experiment,
            'writing': ErrorAnalyzer.analyze_writing,
        }

    def evaluate_and_fix(self, output: Any, agent_type: str, **kwargs) -> Any:
        """
        评估并修复Agent输出
        
        Args:
            output: Agent输出内容
            agent_type: Agent类型 (research/method/experiment/writing/figure)
            kwargs: 额外参数
            
        Returns:
            改进后的输出
        """
        rubric = self.rubrics.get(agent_type)
        if not rubric:
            return output

        print(f'  [Orchestrator] 评估 {agent_type} 输出...')

        improved = self.feedback.improve(
            output=output,
            agent_type=agent_type,
            rubric=rubric,
            error_analyzer_func=self.analyzers.get(agent_type),
            context=kwargs
        )

        return improved

    def evaluate_only(self, output: Any, agent_type: str) -> EvaluationResult:
        """仅评估，不修复"""
        rubric = self.rubrics.get(agent_type)
        if not rubric:
            return None
        return rubric.evaluate(output)

    def evaluate_pipeline_state(self, state: dict) -> Dict[str, Any]:
        """评估Pipeline完整状态"""
        results = {}
        phases = [
            ('research', 'research_results', '文献调研'),
            ('method', 'method_results', '方法设计'),
            ('experiment', 'experiment_results', '实验设计'),
            ('writing', 'thesis_content', '论文写作'),
        ]

        for agent_type, state_key, label in phases:
            content = state.get(state_key)
            if content:
                result = self.evaluate_only(content, agent_type)
                if result:
                    results[agent_type] = {
                        'score': result.overall_score,
                        'passed': result.passes(),
                        'issues': result.all_issues[:3],
                    }
                    status = '✅' if result.passes() else '❌'
                    print(f'  [Orchestrator] {label}: {result.overall_score:.0%} {status}')

        return results

    def get_improvement_suggestions(self, state: dict) -> List[str]:
        """基于状态生成改进建议"""
        suggestions = []

        research = state.get('research_results', {})
        if len(research.get('key_papers', [])) < 3:
            suggestions.append('文献调研: 增加论文覆盖数量')

        method = state.get('method_results', {})
        if not method.get('proposed_method', {}).get('key_components'):
            suggestions.append('方法设计: 补充关键组件描述')

        thesis = state.get('thesis_content', '')
        missing_sections = [s for s in ['摘要', '引言', '方法', '结论', '参考文献'] if s not in thesis]
        if missing_sections:
            suggestions.append(f'论文写作: 补充缺失章节 ({", ".join(missing_sections)})')

        return suggestions