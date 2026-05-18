"""
Error Analyzer - 错误分析与分类
将评估结果中的问题进行分类，并生成修复建议
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.evaluation.judge import EvaluationResult


class ErrorCategory(Enum):
    MISSING = 'missing'
    INCONSISTENCY = 'inconsistency'
    LOW_QUALITY = 'low_quality'
    FACTUAL = 'factual'
    FORMAT = 'format'


ERROR_TYPE_INFO = {
    ErrorCategory.MISSING: {
        'severity': 'high',
        'label': '缺失型',
        'description': '缺少必要的内容、字段或引用',
        'fix_strategy': 'auto_complete'
    },
    ErrorCategory.INCONSISTENCY: {
        'severity': 'high',
        'label': '不一致型',
        'description': '前后矛盾、术语不统一、数字不一致',
        'fix_strategy': 'llm_rewrite'
    },
    ErrorCategory.LOW_QUALITY: {
        'severity': 'medium',
        'label': '低质量型',
        'description': '内容空洞、分析肤浅、描述模糊',
        'fix_strategy': 'llm_improve'
    },
    ErrorCategory.FACTUAL: {
        'severity': 'critical',
        'label': '事实错误型',
        'description': '虚构引用、DOI无效、数据矛盾',
        'fix_strategy': 'external_verify'
    },
    ErrorCategory.FORMAT: {
        'severity': 'low',
        'label': '格式型',
        'description': '格式不规范、排版问题',
        'fix_strategy': 'rule_based'
    },
}


@dataclass
class Error:
    category: ErrorCategory
    severity: str
    location: str
    description: str
    suggestion: str = ''
    fix_strategy: str = 'llm_improve'

    def to_dict(self) -> dict:
        return {
            'category': self.category.value,
            'severity': self.severity,
            'location': self.location,
            'description': self.description,
            'suggestion': self.suggestion,
            'fix_strategy': self.fix_strategy,
        }


@dataclass
class ErrorReport:
    errors: List[Error] = field(default_factory=list)
    overall_quality: float = 1.0
    pass_threshold: float = 0.7

    def passes(self) -> bool:
        critical = [e for e in self.errors if e.severity == 'critical']
        high = [e for e in self.errors if e.severity in ('critical', 'high')]
        return len(critical) == 0 and len(high) <= 2 and self.overall_quality >= self.pass_threshold

    def get_fix_plan(self) -> List[Dict]:
        """生成修复计划"""
        plan = []
        for error in self.errors:
            if error.severity in ('critical', 'high'):
                plan.append({
                    'location': error.location,
                    'description': error.description,
                    'strategy': error.fix_strategy,
                    'suggestion': error.suggestion,
                })
        return plan

    def summary(self) -> str:
        lines = [f'错误报告: {len(self.errors)} 个问题']
        for cat in ErrorCategory:
            cat_errors = [e for e in self.errors if e.category == cat]
            if cat_errors:
                info = ERROR_TYPE_INFO[cat]
                lines.append(f'  {info["label"]}: {len(cat_errors)} 个')
        lines.append(f'  总体质量: {self.overall_quality:.1%}')
        lines.append(f'  是否通过: {"是" if self.passes() else "否"}')
        return '\n'.join(lines)


class ErrorAnalyzer:
    """错误分析器 - 分析Agent输出中的问题"""

    @staticmethod
    def from_evaluation(result: EvaluationResult, location: str) -> ErrorReport:
        """从评估结果生成错误报告"""
        errors = []

        for dim in result.dimensions:
            for issue in dim.issues:
                category = ErrorAnalyzer._classify_issue(issue, dim.name)
                info = ERROR_TYPE_INFO[category]
                errors.append(Error(
                    category=category,
                    severity=info['severity'],
                    location=f'{location}.{dim.name}',
                    description=issue,
                    fix_strategy=info['fix_strategy']
                ))

            if dim.score <= 2:
                errors.append(Error(
                    category=ErrorCategory.LOW_QUALITY,
                    severity='high' if dim.score == 1 else 'medium',
                    location=f'{location}.{dim.name}',
                    description=f'{dim.name}评分仅{dim.score}/5: {dim.reasoning}',
                    fix_strategy='llm_improve'
                ))

        return ErrorReport(
            errors=errors,
            overall_quality=result.overall_score,
            pass_threshold=result.pass_threshold
        )

    @staticmethod
    def analyze_literature(output: dict) -> ErrorReport:
        """分析文献输出的特定错误"""
        errors = []

        if not output.get('key_papers'):
            errors.append(Error(
                ErrorCategory.MISSING, 'high', 'key_papers',
                '无关键论文列表'
            ))
        else:
            if len(output['key_papers']) < 3:
                errors.append(Error(
                    ErrorCategory.LOW_QUALITY, 'medium', 'key_papers',
                    f'论文数量过少({len(output["key_papers"])}篇)'
                ))

        gaps = output.get('research_gaps', [])
        vague_gaps = [g for g in gaps if len(g.get('gap', '')) < 30]
        if vague_gaps:
            errors.append(Error(
                ErrorCategory.LOW_QUALITY, 'medium', 'research_gaps',
                f'{len(vague_gaps)}个Gap描述过于简短'
            ))

        innovations = output.get('innovation_candidates', [])
        if not innovations:
            errors.append(Error(
                ErrorCategory.MISSING, 'medium', 'innovation_candidates',
                '无创新点建议'
            ))

        return ErrorReport(errors=errors)

    @staticmethod
    def analyze_method(output: dict) -> ErrorReport:
        """分析方法输出的特定错误"""
        errors = []

        method_name = output.get('method_name', '')
        if not method_name or method_name in ('Proposed Method', 'unknown'):
            errors.append(Error(
                ErrorCategory.LOW_QUALITY, 'high', 'method_name',
                '方法名称为默认值，缺少具体命名'
            ))

        proposed = output.get('proposed_method', {})
        if not proposed.get('key_components'):
            errors.append(Error(
                ErrorCategory.MISSING, 'high', 'proposed_method.key_components',
                '缺少关键组件描述'
            ))

        if not proposed.get('novelty') or len(str(proposed.get('novelty', ''))) < 20:
            errors.append(Error(
                ErrorCategory.LOW_QUALITY, 'high', 'proposed_method.novelty',
                '创新点描述过于简短或无实质内容'
            ))

        return ErrorReport(errors=errors)

    @staticmethod
    def analyze_experiment(output: dict) -> ErrorReport:
        """分析实验输出的特定错误"""
        errors = []

        if not output.get('is_simulated', False):
            errors.append(Error(
                ErrorCategory.FORMAT, 'low', 'is_simulated',
                '模拟实验未标记is_simulated标志'
            ))

        metrics = output.get('metrics', {})
        if not metrics:
            errors.append(Error(
                ErrorCategory.MISSING, 'high', 'metrics',
                '缺少评估指标'
            ))

        if 'all_runs' in output and output['all_runs']:
            accuracies = [r.get('accuracy', 0) for r in output['all_runs'] if 'accuracy' in r]
            if accuracies and max(accuracies) - min(accuracies) < 0.001:
                errors.append(Error(
                    ErrorCategory.LOW_QUALITY, 'medium', 'all_runs',
                    '多次运行结果完全一致，不合理'
                ))

        return ErrorReport(errors=errors)

    @staticmethod
    def analyze_writing(thesis: str) -> ErrorReport:
        """分析论文写作的特定错误"""
        errors = []

        if len(thesis) < 500:
            errors.append(Error(
                ErrorCategory.MISSING, 'critical', 'thesis_content',
                '论文内容过短(<500字)'
            ))

        sections = ['摘要', '引言', '方法', '实验', '结论', '参考文献']
        missing = [s for s in sections if s not in thesis]
        if missing:
            errors.append(Error(
                ErrorCategory.MISSING, 'high', 'sections',
                f'缺少章节: {", ".join(missing)}'
            ))

        return ErrorReport(errors=errors)

    @staticmethod
    def _classify_issue(issue: str, dimension: str) -> ErrorCategory:
        """根据问题描述自动分类"""
        missing_keywords = ['缺少', '缺失', '无', '没有', '未包含']
        inconsistency_keywords = ['不一致', '矛盾', '不匹配', '不统一']
        factual_keywords = ['虚构', '虚假', '无效', '不存在', '错误']
        format_keywords = ['格式', '排版', '字体', '颜色', '对齐']

        for kw in factual_keywords:
            if kw in issue:
                return ErrorCategory.FACTUAL
        for kw in missing_keywords:
            if kw in issue:
                return ErrorCategory.MISSING
        for kw in inconsistency_keywords:
            if kw in issue:
                return ErrorCategory.INCONSISTENCY
        for kw in format_keywords:
            if kw in issue:
                return ErrorCategory.FORMAT

        return ErrorCategory.LOW_QUALITY