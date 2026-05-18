"""
Figure Rubric - 科研图表质量评估
基于nature-figure标准的图表规范检查
"""
from src.evaluation.judge import LLMJudge
from src.evaluation.rubrics.base_rubric import BaseRubric, RubricDimension


class FigureRubric(BaseRubric):
    """科研图表质量评估Rubric"""

    def __init__(self, llm_judge: LLMJudge):
        super().__init__(llm_judge)
        self.output_type = '科研图表'
        self.pass_threshold = 0.7
        self.dimensions = [
            RubricDimension(
                name='格式规范', weight=0.25,
                criterion='图表格式是否符合学术期刊标准（字体、分辨率、颜色）',
                level5='矢量格式(SVG/PDF)，Arial字体，色盲友好配色',
                level3='格式基本规范但部分不达标',
                level1='格式混乱，不符合出版标准'
            ),
            RubricDimension(
                name='数据准确性', weight=0.25,
                criterion='图表中的数据是否准确反映实验结果',
                level5='数据准确，坐标轴标签清晰，刻度合理',
                level3='数据基本准确但有少量标注问题',
                level1='数据有明显错误或误导性展示'
            ),
            RubricDimension(
                name='可读性', weight=0.25,
                criterion='图表是否易于理解和解读',
                level5='一目了然，图例清晰，标注完整，自解释性强',
                level3='基本可读但需要较多文字解释',
                level1='难以理解或信息过载'
            ),
            RubricDimension(
                name='无冗余', weight=0.25,
                criterion='多个图表之间是否存在信息冗余',
                level5='每个图/面板承载独立的信息，无重复',
                level3='部分面板有少量重复信息',
                level1='存在明显的信息冗余'
            ),
        ]

    def rule_check(self, svg_path: str) -> list:
        """基于规则的格式检查（不依赖LLM）"""
        issues = []
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'font-family="Arial"' not in content and 'font-family="sans-serif"' not in content:
                issues.append('缺少Arial/sans-serif字体设置')
        except Exception as e:
            issues.append(f'无法读取SVG文件: {e}')
        return issues