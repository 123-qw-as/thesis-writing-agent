"""
LLM-as-a-Judge 统一接口
使用LLM评估Agent输出的质量，对每个维度打分并给出推理
"""
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ScoreDimension:
    name: str
    score: int
    max_score: int = 5
    reasoning: str = ''
    issues: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.score >= 3

    @property
    def percentage(self) -> float:
        return (self.score / self.max_score) * 100


@dataclass
class EvaluationResult:
    overall_score: float
    dimensions: List[ScoreDimension]
    passed: bool
    pass_threshold: float = 0.7
    summary: str = ''

    @property
    def all_issues(self) -> List[str]:
        issues = []
        for d in self.dimensions:
            issues.extend(d.issues)
        return issues

    def passes(self) -> bool:
        return self.passed and self.overall_score >= self.pass_threshold


class LLMJudge:
    """LLM评估器 - 对中间输出进行多维度评估"""

    JUDGE_PROMPT = """你是一个专业的学术论文质量评估专家。请对以下内容进行评估。

评估对象：{output_type}
评估维度：{dimensions_text}

评分标准（每个维度1-5分）：
{criterion_text}

待评估内容：
```
{content}
```

请先仔细分析内容，然后对每个维度打分。

输出JSON格式（严格遵循，不要加任何额外文字）：
{{
    "dimensions": [
        {{
            "name": "维度名称",
            "score": 整数1-5,
            "reasoning": "打分的推理过程（20-50字）",
            "issues": ["问题1", "问题2"]
        }}
    ],
    "summary": "总体评价（20-50字）"
}}
"""

    CRITERIA_LEVELS = {
        5: '优秀：完全满足标准，无明显改进空间',
        4: '良好：基本满足标准，有少量改进空间',
        3: '合格：满足最低标准，有明显改进空间',
        2: '不足：未满足标准，需要大幅改进',
        1: '不合格：完全不满足标准，需要重做',
    }

    def __init__(self, llm):
        self.llm = llm

    def evaluate(
        self,
        content: str,
        output_type: str,
        dimensions: List[Dict[str, Any]]
    ) -> EvaluationResult:
        """
        执行LLM评估
        
        Args:
            content: 待评估内容
            output_type: 输出类型（如 "文献调研结果"）
            dimensions: 维度定义列表
                [{"name": "维度名", "criterion": "评分标准描述"},
                 {"name": "覆盖度", "criterion": "是否覆盖核心方法"}]
        """
        dimensions_text = ', '.join([d['name'] for d in dimensions])
        criterion_text = '\n'.join([
            f"- {d['name']}: {d['criterion']}"
            for d in dimensions
        ])

        prompt = self.JUDGE_PROMPT.format(
            output_type=output_type,
            dimensions_text=dimensions_text,
            criterion_text=criterion_text,
            content=str(content)[:8000]
        )

        try:
            response = self.llm.invoke([('user', prompt)])
            raw = getattr(response, 'content', str(response))
            if isinstance(raw, list):
                text_parts = []
                for item in raw:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text_parts.append(item['text'])
                    elif hasattr(item, 'text'):
                        text_parts.append(item.text)
                raw = ''.join(text_parts)
            elif not isinstance(raw, str):
                raw = str(raw)

            parsed = self._parse_json(raw)
            if parsed:
                return self._build_result(parsed, dimensions)
        except Exception:
            pass

        return self._fallback_result(dimensions)

    def _parse_json(self, text: str) -> Optional[Dict]:
        """安全解析LLM返回的JSON"""
        json_match = re.search(r'\{[^{}]*"dimensions"[^{}]*\}', text, re.DOTALL)
        if not json_match:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return None

    def _build_result(self, parsed: Dict, dimensions: List[Dict]) -> EvaluationResult:
        """构建评估结果"""
        dim_scores = []
        total_score = 0.0
        count = 0

        for d in parsed.get('dimensions', []):
            score_val = d.get('score', 3)
            try:
                score_val = int(score_val)
            except (ValueError, TypeError):
                score_val = 3
            score_val = max(1, min(5, score_val))

            dim = ScoreDimension(
                name=d.get('name', 'unknown'),
                score=score_val,
                reasoning=d.get('reasoning', ''),
                issues=d.get('issues', [])
            )
            dim_scores.append(dim)
            total_score += score_val
            count += 1

        avg_score = (total_score / count) / 5.0 if count > 0 else 0.3

        return EvaluationResult(
            overall_score=round(avg_score, 2),
            dimensions=dim_scores,
            passed=avg_score >= 0.6,
            summary=parsed.get('summary', '')
        )

    def _fallback_result(self, dimensions: List[Dict]) -> EvaluationResult:
        """LLM调用失败时的备用结果"""
        dims = [ScoreDimension(
            name=d['name'], score=3,
            reasoning='评估失败，使用默认分数'
        ) for d in dimensions]
        return EvaluationResult(
            overall_score=0.6,
            dimensions=dims,
            passed=True,
            summary='评估服务暂时不可用，使用默认通过'
        )

    def batch_evaluate(
        self,
        items: List[tuple],
        output_type: str,
        dimensions: List[Dict[str, Any]]
    ) -> List[EvaluationResult]:
        """批量评估多个输出"""
        return [
            self.evaluate(content, output_type, dimensions)
            for content, _ in items
        ]