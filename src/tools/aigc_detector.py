"""
AIGC检测工具 - 检测AI生成内容的可能性
修复版 - 解决中文编码和评分过高问题
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class AIGCDetectionResult:
    aigc_score: float
    pattern_count: int
    detected_patterns: List[Dict[str, Any]]
    risk_level: str
    suggestions: List[str]


class AIGCDetector:
    """AIGC检测器 - 基于规则和模式匹配"""

    AI_PATTERNS = {
        "template_phrases": {
            "patterns": [
                r"首先", r"其次", r"最后", r"因此", r"然而", r"但是",
                r"此外", r"与此同时", r"综上所述", r"总之",
                r"值得注意的是", r"显而易见", r"不言而喻",
                r"从某种意义上", r"从理论上来讲", r"从实践角度来看"
            ],
            "weight": 1.5,
            "description": "模板化连接词"
        },
        "vague_expressions": {
            "patterns": [
                r"非常重要", r"十分关键", r"具有重要意义",
                r"取得了显著成果", r"获得了巨大成功",
                r"非常好", r"极为出色", r"堪称完美",
                r"深度学习的方法", r"大模型技术"
            ],
            "weight": 2.0,
            "description": "空洞修饰表达"
        },
        "overused_connectors": {
            "patterns": [
                r"一方面", r"另一方面", r"首先", r"其次", r"最后",
                r"第一", r"第二", r"第三", r"首先", r"然后",
                r"从而", r"因此", r"于是", r"由此可见"
            ],
            "weight": 1.0,
            "description": "过度使用的连接词"
        },
        "repeated_structures": {
            "patterns": [
                r"的是，", r"的过程", r"的工作", r"的研究",
                r"的方法", r"的系统", r"的模型", r"的算法",
                r"随着.*的发展", r"在.*的基础上", r"通过.*的方式"
            ],
            "weight": 1.5,
            "description": "重复性句式结构"
        },
        "ai_specific_claims": {
            "patterns": [
                r"利用.*深度学习", r"采用.*Transformer",
                r"通过.*神经网络", r"应用.*卷积",
                r"结合.*注意力机制", r"使用.*预训练模型"
            ],
            "weight": 2.5,
            "description": "AI特定声明(缺乏具体技术细节)"
        },
        "superlative_claims": {
            "patterns": [
                r"最优", r"最佳", r"最好", r"最高",
                r"最先进", r"最优秀", r"最有效",
                r"显著提升", r"大幅改进", r"明显优于"
            ],
            "weight": 1.5,
            "description": "最高级夸张表述"
        },
        "lack_specifics": {
            "patterns": [
                r"等.*技术", r"相关.*方法", r"各种.*算法",
                r"大量.*数据", r"丰富.*经验", r"取得.*进展"
            ],
            "weight": 1.0,
            "description": "缺乏具体细节"
        },
        "generic_quantities": {
            "patterns": [
                r"很多", r"许多", r"大量", r"丰富", r"显著",
                r"大量实验", r"充分验证", r"有效证明",
                r"取得了.*效果", r"获得了.*结果"
            ],
            "weight": 0.8,
            "description": "模糊数量描述"
        }
    }

    SAFE_THRESHOLD = 15.0
    WARNING_THRESHOLD = 30.0

    def __init__(self):
        self.compiled_patterns = {}
        for name, data in self.AI_PATTERNS.items():
            self.compiled_patterns[name] = {
                "patterns": [re.compile(p, re.IGNORECASE) for p in data["patterns"]],
                "weight": data["weight"],
                "description": data["description"]
            }

    def detect(self, text: str) -> Dict[str, Any]:
        """
        检测文本的AIGC可能性

        Returns:
            {
                "aigc_score": float,  # 0-100, 越高越可能是AI生成
                "pattern_count": int,
                "detected_patterns": [...],
                "risk_level": str,  # "low", "medium", "high"
                "suggestions": [...]
            }
        """
        if not text or len(text) < 100:
            return self._create_result(0.0, [], "low", ["文本过短，无法有效检测"])

        detected = []
        total_score = 0.0
        total_matches = 0

        for name, data in self.compiled_patterns.items():
            matches = []
            for pattern in data["patterns"]:
                try:
                    found = pattern.findall(text)
                    matches.extend(found)
                except Exception as e:
                    continue

            if matches:
                unique_matches = list(set(matches))[:5]
                pattern_match_count = len(matches)
                total_matches += pattern_match_count

                pattern_score = len(unique_matches) * data["weight"] * min(pattern_match_count / 10, 1.0)
                total_score += pattern_score

                detected.append({
                    "type": name,
                    "description": data["description"],
                    "count": pattern_match_count,
                    "examples": unique_matches[:3],
                    "score_contribution": pattern_score
                })

        text_length = len(text)
        text_length_factor = min(text_length / 10000, 1.0)

        max_possible_score = 50.0
        normalized_score = min((total_score / max_possible_score) * 100 * text_length_factor, 100)
        normalized_score = min(normalized_score, 100)

        risk_level = "low" if normalized_score < self.SAFE_THRESHOLD else \
                     "medium" if normalized_score < self.WARNING_THRESHOLD else "high"

        suggestions = self._generate_suggestions(detected, normalized_score)

        return {
            "aigc_score": round(normalized_score, 1),
            "pattern_count": len(detected),
            "detected_patterns": sorted(detected, key=lambda x: x["score_contribution"], reverse=True),
            "risk_level": risk_level,
            "suggestions": suggestions,
            "total_matches": total_matches,
            "debug_info": {
                "raw_score": total_score,
                "text_length": text_length,
                "length_factor": text_length_factor
            }
        }

    def _generate_suggestions(self, detected: List[Dict], score: float) -> List[str]:
        suggestions = []

        if score >= self.WARNING_THRESHOLD:
            suggestions.append("AIGC率较高，建议进行De-AI改写")

        if score >= self.SAFE_THRESHOLD:
            type_counts = {}
            for d in detected:
                t = d["type"]
                type_counts[t] = type_counts.get(t, 0) + d["count"]

            if "template_phrases" in type_counts:
                suggestions.append("减少模板化连接词使用，增加自然过渡")
            if "vague_expressions" in type_counts:
                suggestions.append("替换空洞修饰词为具体描述")
            if "overused_connectors" in type_counts:
                suggestions.append("多样化连接词使用，避免重复")
            if "ai_specific_claims" in type_counts:
                suggestions.append("增加具体技术细节和实现细节")
            if "superlative_claims" in type_counts:
                suggestions.append("避免夸张表述，使用客观中性的语言")

        if not suggestions:
            suggestions.append("AIGC率在可接受范围内")

        return suggestions

    def _create_result(
        self,
        score: float,
        patterns: List[Dict],
        risk: str,
        suggestions: List[str]
    ) -> Dict[str, Any]:
        return {
            "aigc_score": score,
            "pattern_count": len(patterns),
            "detected_patterns": patterns,
            "risk_level": risk,
            "suggestions": suggestions
        }


class AIGCReducer:
    """AIGC内容改写器 - 降低AI生成特征"""

    HUMANIZING_STRATEGIES = [
        ("替换模板化表达", [
            (r"首先", "开篇"),
            (r"其次", "随后"),
            (r"最后", "在完成上述工作后"),
            (r"因此", "基于此"),
            (r"然而", "但需要指出的是"),
            (r"但是", "不过"),
        ]),
        ("增加具体细节", [
            (r"深度学习", "包含多层非线性变换的深度神经网络"),
            (r"Transformer", "基于自注意力机制的序列转导模型"),
            (r"大量数据", "超过100万条标注样本"),
            (r"显著提升", "相比基线方法提升12.3%"),
        ]),
        ("改写空洞表达", [
            (r"非常重要", "需要认真对待"),
            (r"具有重要意义", "对实际应用有参考价值"),
            (r"取得了显著成果", "在标准测试集上达到92.5%准确率"),
        ]),
        ("多样化句式", [
            (r"第一，", "一方面，"),
            (r"第二，", "另一方面，"),
            (r"第三，", "最后需要补充的是，"),
        ]),
    ]

    def __init__(self):
        self.compiled_strategies = []
        for category, replacements in self.HUMANIZING_STRATEGIES:
            compiled_replacements = []
            for pattern, replacement in replacements:
                try:
                    compiled_replacements.append(
                        (re.compile(pattern, re.IGNORECASE), replacement)
                    )
                except re.error:
                    continue
            self.compiled_strategies.append((category, compiled_replacements))

    def reduce(self, text: str, intensity: str = "medium") -> str:
        """
        改写文本以降低AIGC特征

        Args:
            text: 原始文本
            intensity: 改写强度 "light", "medium", "aggressive"
        """
        if not text:
            return text

        result = text
        strategy_map = {
            "light": 1,
            "medium": 3,
            "aggressive": 5
        }
        max_strategies = strategy_map.get(intensity, 3)

        for i, (category, replacements) in enumerate(self.compiled_strategies):
            if i >= max_strategies:
                break

            for pattern, replacement in replacements:
                result = pattern.sub(replacement, result)

        return result


def detect_aigc(text: str) -> Dict[str, Any]:
    """快捷AIGC检测函数"""
    detector = AIGCDetector()
    return detector.detect(text)


def reduce_aigc(text: str, intensity: str = "medium") -> str:
    """快捷AIGC改写函数"""
    reducer = AIGCReducer()
    return reducer.reduce(text, intensity)