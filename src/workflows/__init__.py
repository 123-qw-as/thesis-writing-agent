"""
Workflows Module - 研究流程工作流

提供各类研究流程的自动化执行
"""

from .quality_workflow import QualityWorkflow, run_quality_workflow
from .enhanced_pipeline import EnhancedResearchPipeline, run_enhanced_pipeline
from .research_pipeline import run_full_pipeline, get_pipeline_status

__all__ = [
    'QualityWorkflow',
    'run_quality_workflow',
    'EnhancedResearchPipeline',
    'run_enhanced_pipeline',
    'run_full_pipeline',
    'get_pipeline_status'
]