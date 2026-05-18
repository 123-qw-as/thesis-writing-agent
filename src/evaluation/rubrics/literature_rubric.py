"""
Literature Rubric - 文献调研结果评估
"""
from src.evaluation.judge import LLMJudge
from src.evaluation.rubrics.base_rubric import BaseRubric, RubricDimension


class LiteratureRubric(BaseRubric):
    """文献调研质量评估Rubric"""

    def __init__(self, llm_judge: LLMJudge):
        super().__init__(llm_judge)
        self.output_type = '文献调研结果'
        self.pass_threshold = 0.65
        self.dimensions = [
            RubricDimension(
                name='覆盖度', weight=0.25,
                criterion='文献调研是否覆盖了核心方法、近期进展和经典工作',
                level5='全面覆盖经典工作+近期前沿+多种方法路线',
                level3='覆盖了主要方法和部分近期进展',
                level1='仅覆盖少量论文，缺乏系统性'
            ),
            RubricDimension(
                name='权威性', weight=0.20,
                criterion='引用来源是否为顶会/顶刊/高引论文，或相关研究',
                level5='全部来自顶会/顶刊/高引论文',
                level3='混合顶会与普通来源',
                level1='来源不明确或非学术来源'
            ),
            RubricDimension(
                name='时效性', weight=0.15,
                criterion='是否包含近年的最新成果',
                level5='包含近1-2年的最新研究成果',
                level3='包含近3-5年的研究',
                level1='全部是5年以前的成果'
            ),
            RubricDimension(
                name='Gap合理性', weight=0.25,
                criterion='研究空白分析是否具体、可操作、有依据',
                level5='Gap具体明确，有数据或文献支撑，可直接转化为研究方向',
                level3='Gap方向正确但描述比较笼统',
                level1='无具体Gap或Gap不相关'
            ),
            RubricDimension(
                name='搜索策略', weight=0.15,
                criterion='使用的搜索方法和关键词是否全面',
                level5='多角度、多源检索，关键词全面精准',
                level3='有基本的关键词搜索',
                level1='搜索策略单一或缺失'
            ),
        ]

    def should_retry(self, result) -> bool:
        """判断是否需要重新执行文献搜索"""
        if not result.passes():
            return True
        for dim in result.dimensions:
            if dim.name == 'Gap合理性' and dim.score < 3:
                return True
            if dim.name == '覆盖度' and dim.score < 2:
                return True
        return False