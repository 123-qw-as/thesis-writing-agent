"""
Rendering Auditor - 渲染过程降级事件审计器
记录Word文档渲染过程中的所有降级事件，用于后期质量评估
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FallbackEvent:
    """单个降级事件"""
    event_type: str          # image_missing / formula_fallback / latex_error / font_fallback
    source: str              # 来源位置（行号、公式文本、图片路径）
    reason: str              # 降级原因
    resolved: bool = False   # 是否已解决
    timestamp: str = ''

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime('%H:%M:%S')


@dataclass
class RenderingReport:
    """渲染审计报告"""
    images_requested: int = 0
    images_embedded: int = 0
    formulas_requested: int = 0
    formulas_omml: int = 0
    formulas_fallback: int = 0
    fallback_events: List[FallbackEvent] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def image_success_rate(self) -> float:
        if self.images_requested == 0:
            return 1.0
        return self.images_embedded / self.images_requested

    @property
    def formula_success_rate(self) -> float:
        total = self.formulas_omml + self.formulas_fallback
        if total == 0:
            return 1.0
        return self.formulas_omml / total

    @property
    def has_critical_issues(self) -> bool:
        return len(self.errors) > 0 or len([e for e in self.fallback_events if not e.resolved]) > 5

    def merge(self, other: 'RenderingReport'):
        """合并另一个报告"""
        self.images_requested += other.images_requested
        self.images_embedded += other.images_embedded
        self.formulas_requested += other.formulas_requested
        self.formulas_omml += other.formulas_omml
        self.formulas_fallback += other.formulas_fallback
        self.fallback_events.extend(other.fallback_events)
        self.warnings.extend(other.warnings)
        self.errors.extend(other.errors)

    def summary(self) -> str:
        lines = ['=== Rendering Audit Report ===']
        lines.append(f'Images: {self.images_embedded}/{self.images_requested} ({self.image_success_rate:.0%})')
        lines.append(f'Formulas: OMML={self.formulas_omml}, Fallback={self.formulas_fallback} ({self.formula_success_rate:.0%})')
        lines.append(f'Fallback events: {len(self.fallback_events)}')
        if self.fallback_events:
            for e in self.fallback_events[:5]:
                lines.append(f'  [{e.event_type}] {e.reason}')
        if self.warnings:
            lines.append(f'Warnings: {len(self.warnings)}')
        if self.errors:
            lines.append(f'Errors: {len(self.errors)}')
        lines.append('=' * 35)
        return '\n'.join(lines)


class RenderingAuditor:
    """渲染审计器 - 单例模式，全局记录渲染事件"""

    _instance = None
    _current_report: RenderingReport = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.reset()
        return cls._instance

    def reset(self):
        """重置审计报告"""
        self._current_report = RenderingReport()

    def get_report(self) -> RenderingReport:
        """获取当前报告"""
        return self._current_report

    def record_image_request(self, count: int = 1):
        """记录图片请求"""
        self._current_report.images_requested += count

    def record_image_embedded(self, count: int = 1):
        """记录成功嵌入的图片"""
        self._current_report.images_embedded += count

    def record_formula_request(self, count: int = 1):
        """记录公式请求"""
        self._current_report.formulas_requested += count

    def record_formula_omml(self):
        """记录成功转换为OMML的公式"""
        self._current_report.formulas_omml += 1

    def record_formula_fallback(self):
        """记录退化文本的公式"""
        self._current_report.formulas_fallback += 1

    def record_fallback(self, event_type: str, source: str, reason: str):
        """记录降级事件"""
        self._current_report.fallback_events.append(
            FallbackEvent(event_type=event_type, source=source, reason=reason)
        )

    def record_warning(self, msg: str):
        """记录警告"""
        self._current_report.warnings.append(msg)

    def record_error(self, msg: str):
        """记录错误"""
        self._current_report.errors.append(msg)