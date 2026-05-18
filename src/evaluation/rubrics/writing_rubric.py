"""
Writing Rubric - 论文写作评估（增强版）
在原有7维度基础上增加一致性+可复现性，并将关键词评估升级为LLM评估
"""
from src.evaluation.judge import LLMJudge
from src.evaluation.rubrics.base_rubric import BaseRubric, RubricDimension


class WritingRubric(BaseRubric):
    """论文写作质量评估Rubric（增强版）"""

    def __init__(self, llm_judge: LLMJudge):
        super().__init__(llm_judge)
        self.output_type = '论文章节'
        self.pass_threshold = 0.7
        self.dimensions = [
            RubricDimension(
                name='结构完整性', weight=0.10,
                criterion='论文结构是否完整，章节组织是否合理',
                level5='包含所有标准章节，逻辑递进清晰',
                level3='大部分章节存在但有遗漏',
                level1='结构混乱，多个章节缺失'
            ),
            RubricDimension(
                name='内容质量', weight=0.15,
                criterion='内容深度、论证质量、分析是否充分',
                level5='论证深入，分析透彻，有独到见解',
                level3='内容基本充实，但分析不够深入',
                level1='内容空洞或流于表面'
            ),
            RubricDimension(
                name='方法论', weight=0.10,
                criterion='方法描述是否清晰、准确、完整',
                level5='方法描述详尽，技术细节清晰，易于理解',
                level3='方法描述基本完整但部分不清晰',
                level1='方法描述模糊或缺失'
            ),
            RubricDimension(
                name='实验验证', weight=0.15,
                criterion='实验设计、结果分析和结论是否合理',
                level5='实验严谨，分析充分，结论有数据支撑',
                level3='实验基本合理但有改进空间',
                level1='实验设计有缺陷或分析不足'
            ),
            RubricDimension(
                name='写作质量', weight=0.15,
                criterion='语言表达、学术规范性、可读性',
                level5='语言规范、表达清晰、符合学术写作标准',
                level3='语言基本规范但有改进空间',
                level1='语言表达问题较多'
            ),
            RubricDimension(
                name='引用规范', weight=0.15,
                criterion='引用格式、DOI有效性、引用与内容匹配',
                level5='引用格式规范，DOI有效，引用与内容高度匹配',
                level3='引用基本规范但部分有格式问题',
                level1='引用格式混乱或缺少关键引用'
            ),
            RubricDimension(
                name='原创性', weight=0.10,
                criterion='创新点阐述是否明确、有实质性贡献',
                level5='创新点明确具体，贡献清晰可量化',
                level3='有创新点但表述不够鲜明',
                level1='无明显创新点'
            ),
            RubricDimension(
                name='一致性', weight=0.05,
                criterion='摘要与正文内容一致，全篇术语统一，数字一致',
                level5='摘要准确反映正文，术语统一，数字完全一致',
                level3='基本一致但有少量出入',
                level1='摘要与正文存在明显矛盾'
            ),
            RubricDimension(
                name='可复现性', weight=0.05,
                criterion='方法描述是否足够详细以支持复现',
                level5='数据集、参数、环境、代码链接完整',
                level3='部分信息可获取但关键细节缺失',
                level1='完全不具备可复现条件'
            ),
        ]

    def should_retry(self, result) -> bool:
        if not result.passes():
            return True
        for dim in result.dimensions:
            if dim.name in ('内容质量', '实验验证') and dim.score < 2:
                return True
        return False