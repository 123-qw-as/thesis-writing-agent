"""
DOCX Rubric - 编译后Word文档质量评估
6维度评估最终DOCX输出文件的质量
"""
from src.evaluation.judge import LLMJudge
from src.evaluation.rubrics.base_rubric import BaseRubric, RubricDimension


class DocxRubric(BaseRubric):
    """DOCX文档质量评估Rubric"""

    def __init__(self, llm_judge: LLMJudge):
        super().__init__(llm_judge)
        self.output_type = 'Word文档输出'
        self.pass_threshold = 0.65
        self.dimensions = [
            RubricDimension(
                name='公式渲染', weight=0.25,
                criterion='LaTeX公式是否成功渲染为Word原生OMML公式，而非退化文本',
                level5='所有公式都渲染为OMML(100%)',
                level3='大部分公式为OMML(>80%)',
                level1='公式全部退化文本或无公式'
            ),
            RubricDimension(
                name='图片嵌入', weight=0.25,
                criterion='科研图表是否正确嵌入文档中',
                level5='所有图片成功嵌入',
                level3='部分图片嵌入(>50%)',
                level1='无图片嵌入'
            ),
            RubricDimension(
                name='无退化痕迹', weight=0.20,
                criterion='文档中不应存在"[Image not found]"等退化占位文本',
                level5='完全无退化痕迹',
                level3='存在1-2处退化',
                level1='存在多处退化'
            ),
            RubricDimension(
                name='结构完整性', weight=0.15,
                criterion='文档结构完整：页眉、页码、章节标题层级',
                level5='页眉+页码+多级标题完整',
                level3='部分存在但缺少量元素',
                level1='结构不完整'
            ),
            RubricDimension(
                name='文档健全度', weight=0.10,
                criterion='文档文件基本指标：文件大小、段落数',
                level5='大小>50KB，段落>30',
                level3='大小>20KB，段落>10',
                level1='文件过小或内容过少'
            ),
            RubricDimension(
                name='排版规范性', weight=0.05,
                criterion='字体、行距、页边距等排版规范',
                level5='完全符合学术排版规范',
                level3='基本符合但有少量偏差',
                level1='排版明显不规范'
            ),
        ]

    def evaluate_from_report(self, rendering_report, docx_path: str, docx_analysis: dict) -> 'EvaluationResult':
        """从渲染报告和DOCX分析生成评估结果"""
        from src.evaluation.judge import ScoreDimension, EvaluationResult

        dims = []

        # 1. 公式渲染
        formula_rate = rendering_report.formula_success_rate
        if formula_rate >= 1.0:
            fs = 5
        elif formula_rate >= 0.8:
            fs = 4
        elif formula_rate >= 0.5:
            fs = 3
        elif formula_rate > 0:
            fs = 2
        else:
            fs = 1
        dims.append(ScoreDimension(
            name='公式渲染', score=fs,
            reasoning=f'OMML转换率: {rendering_report.formulas_omml}/{rendering_report.formulas_omml + rendering_report.formulas_fallback}'
        ))

        # 2. 图片嵌入
        img_rate = rendering_report.image_success_rate
        if img_rate >= 1.0 and rendering_report.images_requested > 0:
            iscore = 5
        elif img_rate >= 0.5:
            iscore = 3
        else:
            iscore = 1
        dims.append(ScoreDimension(
            name='图片嵌入', score=iscore,
            reasoning=f'图片嵌入率: {rendering_report.images_embedded}/{rendering_report.images_requested}'
        ))

        # 3. 无退化痕迹
        fallback_count = len(rendering_report.fallback_events)
        if fallback_count == 0:
            fscore = 5
        elif fallback_count <= 2:
            fscore = 3
        else:
            fscore = 1
        dims.append(ScoreDimension(
            name='无退化痕迹', score=fscore,
            reasoning=f'降级事件数: {fallback_count}'
        ))

        # 4. 结构完整性
        has_header = docx_analysis.get('has_header', False)
        has_footer = docx_analysis.get('has_footer', False)
        heading_count = docx_analysis.get('heading_count', 0)
        sscore = 3
        if has_header and has_footer and heading_count >= 5:
            sscore = 5
        elif has_header or has_footer:
            sscore = 3
        dims.append(ScoreDimension(
            name='结构完整性', score=sscore,
            reasoning=f'页眉={has_header}, 页码={has_footer}, 标题数={heading_count}'
        ))

        # 5. 文档健全度
        import os
        file_size = os.path.getsize(docx_path) if docx_path else 0
        para_count = docx_analysis.get('paragraph_count', 0)
        if file_size > 50000 and para_count > 30:
            rscore = 5
        elif file_size > 20000 and para_count > 10:
            rscore = 3
        else:
            rscore = 1
        dims.append(ScoreDimension(
            name='文档健全度', score=rscore,
            reasoning=f'大小={file_size}字节, 段落={para_count}'
        ))

        # 6. 排版规范性
        margins = docx_analysis.get('margins', {})
        line_spacing = docx_analysis.get('line_spacing', 0)
        if margins and line_spacing >= 1.5:
            pscore = 5
        elif margins:
            pscore = 3
        else:
            pscore = 1
        dims.append(ScoreDimension(
            name='排版规范性', score=pscore,
            reasoning=f'边距={bool(margins)}, 行距={line_spacing}'
        ))

        overall = self._calc_weighted_score(dims)
        return EvaluationResult(
            overall_score=overall,
            dimensions=dims,
            passed=overall >= self.pass_threshold
        )