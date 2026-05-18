"""
Experiment Rubric - 实验设计评估
"""
from src.evaluation.judge import LLMJudge
from src.evaluation.rubrics.base_rubric import BaseRubric, RubricDimension


class ExperimentRubric(BaseRubric):
    """实验设计质量评估Rubric"""

    def __init__(self, llm_judge: LLMJudge):
        super().__init__(llm_judge)
        self.output_type = '实验设计结果'
        self.pass_threshold = 0.65
        self.dimensions = [
            RubricDimension(
                name='指标完备性', weight=0.25,
                criterion='是否包含足够的评估指标来全面衡量方法性能',
                level5='多维度指标(准确率/效率/鲁棒性/泛化性等)',
                level3='包含2-3个基础指标',
                level1='仅1个指标或指标不相关'
            ),
            RubricDimension(
                name='实验设计', weight=0.25,
                criterion='实验设置是否合理，对照组是否完整',
                level5='多基线对比+消融实验+统计分析，设计严谨',
                level3='有基本对照组',
                level1='无对照或实验设计有明显缺陷'
            ),
            RubricDimension(
                name='数据合理性', weight=0.25,
                criterion='实验中使用的数据是否合理，数值分布是否真实',
                level5='数据分布合理，数值范围符合常识，异常有解释',
                level3='数据基本合理但有可疑之处',
                level1='数据明显异常或完全不合理'
            ),
            RubricDimension(
                name='可复现性', weight=0.25,
                criterion='实验参数、环境是否描述清楚，他人能否复现',
                level5='数据集+参数+环境+种子完整，可完全复现',
                level3='有部分参数但缺关键信息',
                level1='无可复现信息'
            ),
        ]

    def check_simulated_flag(self, result: dict) -> bool:
        """检查模拟实验是否有明确标记"""
        is_sim = result.get('is_simulated', False)
        return is_sim

    def should_retry(self, result) -> bool:
        if not result.passes():
            return True
        for dim in result.dimensions:
            if dim.name == '数据合理性' and dim.score < 2:
                return True
            if dim.name == '可复现性' and dim.score < 2:
                return True
        return False