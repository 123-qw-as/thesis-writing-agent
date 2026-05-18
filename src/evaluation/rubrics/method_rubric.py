"""
Method Rubric - 方法设计评估
"""
from src.evaluation.judge import LLMJudge
from src.evaluation.rubrics.base_rubric import BaseRubric, RubricDimension


class MethodRubric(BaseRubric):
    """方法设计质量评估Rubric"""

    def __init__(self, llm_judge: LLMJudge):
        super().__init__(llm_judge)
        self.output_type = '方法设计方案'
        self.pass_threshold = 0.65
        self.dimensions = [
            RubricDimension(
                name='创新性', weight=0.30,
                criterion='与现有方法相比，是否有实质性创新，而非简单组合',
                level5='有实质性创新，与现有方法有明确且可量化的区别',
                level3='有部分改进，但增量较小',
                level1='仅为现有方法的简单组合或复述'
            ),
            RubricDimension(
                name='可行性', weight=0.25,
                criterion='方法是否具体、可实现、在给定约束下可行',
                level5='架构清晰，组件具体，参数明确，在约束下完全可行',
                level3='有大致架构但部分细节缺失',
                level1='描述模糊，无法判断可行性'
            ),
            RubricDimension(
                name='技术细节', weight=0.25,
                criterion='方法的技术描述是否足够详细',
                level5='包含伪代码/公式/算法步骤，组件间交互清楚',
                level3='有框架性描述，缺具体细节',
                level1='仅有方法名称和大致方向'
            ),
            RubricDimension(
                name='SOTA对比', weight=0.20,
                criterion='是否与SOTA方法进行了有意义的对比',
                level5='详细对比多个SOTA方法，量化差距，分析优劣',
                level3='有对比但表面',
                level1='无对比或对比不相关'
            ),
        ]

    def should_retry(self, result) -> bool:
        if not result.passes():
            return True
        for dim in result.dimensions:
            if dim.name == '创新性' and dim.score < 3:
                return True
            if dim.name == '技术细节' and dim.score < 2:
                return True
        return False