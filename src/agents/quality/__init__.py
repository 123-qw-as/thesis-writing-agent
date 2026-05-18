"""
Quality Improvement Module - 论文质量改进系统

提供论文质量评估、AIGC检测、数据真实性验证和改进功能
"""

from .agent import (
    QualityImprovementAgent,
    QualityTargets,
    QualityResult,
    improve_thesis_quality
)

__all__ = [
    'QualityImprovementAgent',
    'QualityTargets',
    'QualityResult',
    'improve_thesis_quality'
]