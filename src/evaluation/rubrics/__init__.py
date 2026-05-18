"""
Rubrics 模块初始化
"""
from .base_rubric import BaseRubric, RubricDimension
from .literature_rubric import LiteratureRubric
from .method_rubric import MethodRubric
from .experiment_rubric import ExperimentRubric
from .writing_rubric import WritingRubric
from .figure_rubric import FigureRubric
from .docx_rubric import DocxRubric

__all__ = [
    'BaseRubric', 'RubricDimension',
    'LiteratureRubric', 'MethodRubric',
    'ExperimentRubric', 'WritingRubric', 'FigureRubric',
    'DocxRubric',
]