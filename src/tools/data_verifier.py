"""
数据真实性验证工具 - 验证论文中数据的可信度和一致性
修复版 - 正确处理中文内容
"""

import re
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class DataVerificationResult:
    authenticity_score: float
    suspicious_data_points: List[Dict[str, Any]]
    numerical_inconsistencies: List[Dict[str, Any]]
    statistical_anomalies: List[Dict[str, Any]]
    verified_claims: List[str]
    suggestions: List[str]


class DataVerifier:
    """数据验证器 - 检测论文中的数据问题"""

    SUSPICIOUS_THRESHOLDS = {
        "perfect_score": 1.0,
        "round_number_freq": 0.3,
        "unusual_precision": 4,
        "impossible_combinations": [
            ({"accuracy": (0.99, 1.0), "dataset": "small"}, "准确率过高且数据集小"),
            ({"speedup": (50, float("inf")), "method": "incremental"}, "增量方法加速比过高"),
        ]
    }

    def __init__(self):
        self.number_pattern = re.compile(r'(\d+\.?\d*)\s*%?|(\d+\.\d+)')

    def verify(self, text: str) -> Dict[str, Any]:
        """
        验证论文中的数据真实性

        Returns:
            {
                "authenticity_score": float,  # 0-100
                "suspicious_data_points": [...],
                "numerical_inconsistencies": [...],
                "statistical_anomalies": [...],
                "verified_claims": [...],
                "suggestions": [...]
            }
        """
        numbers = self._extract_numbers(text)
        metrics = self._extract_metrics(text)
        comparisons = self._extract_comparisons(text)

        suspicious = []
        inconsistencies = []
        anomalies = []

        suspicious.extend(self._check_suspicious_numbers(numbers))
        inconsistencies.extend(self._check_numerical_consistency(text, metrics))
        anomalies.extend(self._check_statistical_anomalies(metrics))

        score = 100.0
        # 降低扣分权重，避免误杀正常数字
        score -= len(suspicious) * 1.5
        score -= len(inconsistencies) * 5
        score -= len(anomalies) * 3
        score = max(score, 0.0)

        suggestions = self._generate_suggestions(suspicious, inconsistencies, anomalies)

        verified = []
        if len(suspicious) == 0:
            verified.append("未发现明显可疑数据点")
        if len(inconsistencies) == 0:
            verified.append("数值一致性检查通过")
        if len(anomalies) == 0:
            verified.append("统计分析未发现明显异常")

        return {
            "authenticity_score": round(score, 1),
            "suspicious_data_points": suspicious,
            "numerical_inconsistencies": inconsistencies,
            "statistical_anomalies": anomalies,
            "verified_claims": verified,
            "suggestions": suggestions
        }

    def _extract_numbers(self, text: str) -> List[Dict[str, Any]]:
        numbers = []
        lines = text.split('\n')

        for i, line in enumerate(lines):
            matches = self.number_pattern.findall(line)
            for match in matches:
                num_str = match[0] if match[0] else match[1]
                try:
                    num = float(num_str)
                    context = line.strip()
                    numbers.append({
                        "value": num,
                        "line": i + 1,
                        "context": context[:100],
                        "is_percentage": '%' in line and match[0]
                    })
                except ValueError:
                    continue

        return numbers

    def _extract_metrics(self, text: str) -> Dict[str, List[float]]:
        metrics = {
            "accuracy": [],
            "precision": [],
            "recall": [],
            "f1": [],
            "auc": [],
            "speedup": [],
            "time": [],
            "memory": [],
        }

        patterns = {
            "accuracy": r'acc(?:uracy)?[:\s]*(\d+\.?\d*)%?|(\d+\.\d+)(?:\s*-?\s*acc)',
            "precision": r'precision[:\s]*(\d+\.?\d*)%?|(\d+\.\d+)(?:\s*-?\s*prec)',
            "recall": r'recall[:\s]*(\d+\.?\d*)%?|(\d+\.\d+)(?:\s*-?\s*rec)',
            "f1": r'F1[:\s]*(\d+\.?\d*)%?|(\d+\.\d+)(?:\s*-?\s*F1)',
            "auc": r'AUC[:\s]*(\d+\.?\d*)%?|(\d+\.\d+)(?:\s*-?\s*AUC)',
            "speedup": r'speedup[:\s*x]*(\d+\.?\d*)|(\d+\.\d+)(?:\s*×|\s*x)',
            "time": r'(\d+\.?\d*)\s*(?:ms|s|min|hour|h)',
            "memory": r'(\d+\.?\d*)\s*(?:MB|GB|KB)',
        }

        for metric, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                for val in match:
                    if val:
                        try:
                            metrics[metric].append(float(val))
                        except ValueError:
                            continue

        return metrics

    def _extract_comparisons(self, text: str) -> List[Dict[str, Any]]:
        comparisons = []

        gt_pattern = r'(\d+\.?\d*)\s*%?\s*(?:>| greater than|优于|高于)'
        for match in re.finditer(gt_pattern, text, re.IGNORECASE):
            comparisons.append({
                "type": "greater_than",
                "value": float(re.search(r'\d+\.?\d*', match.group()).group()),
                "position": match.start()
            })

        lt_pattern = r'(\d+\.?\d*)\s*%?\s*(?:<| less than|低于|差于)'
        for match in re.finditer(lt_pattern, text, re.IGNORECASE):
            comparisons.append({
                "type": "less_than",
                "value": float(re.search(r'\d+\.?\d*', match.group()).group()),
                "position": match.start()
            })

        return comparisons

    def _check_suspicious_numbers(self, numbers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        suspicious = []

        for num_data in numbers:
            val = num_data["value"]
            context = num_data.get("context", "")

            # 跳过代码块中的数字
            if self._is_in_code_block(context):
                continue

            # 跳过 DOI、版本号、年份、章节号等
            if self._is_doi_number(val, context):
                continue
            if self._is_version_number(val, context):
                continue
            if self._is_year_number(val, context):
                continue
            if self._is_section_number(val, context):
                continue
            if self._is_citation_number(val, context):
                continue

            # 完美分数检查
            if val == 1.0 or val == 100.0:
                if "=" in context or "==" in context or "return" in context.lower():
                    continue
                suspicious.append({
                    "type": "perfect_score",
                    "value": val,
                    "line": num_data["line"],
                    "context": context,
                    "reason": "完美分数(100%或1.0)较为罕见，需确认"
                })

            # 零值检查
            if val == 0.0:
                suspicious.append({
                    "type": "zero_value",
                    "value": val,
                    "line": num_data["line"],
                    "context": context,
                    "reason": "零值需要上下文确认是否合理"
                })

            # 高精度检查（仅对 0-1 之间的小数）
            if 0 < val < 1:
                decimal = str(val).split('.')
                if len(decimal) > 1 and len(decimal[1]) > 4:
                    suspicious.append({
                        "type": "unusual_precision",
                        "value": val,
                        "line": num_data["line"],
                        "context": context,
                        "reason": f"异常高精度: {val}，实际中罕见此精度"
                    })

        return suspicious

    def _is_in_code_block(self, context: str) -> bool:
        if not context:
            return False
        code_indicators = ['def ', 'class ', 'import ', 'return ', 'if ', 'else:', '```', '()', '=>', '->']
        return any(indicator in context for indicator in code_indicators)

    def _is_doi_number(self, val: float, context: str) -> bool:
        if not context:
            return False
        if 'doi' in context.lower() or 'arxiv' in context.lower() or '10.' in context:
            if 10.0 <= val <= 11.0:
                return True
        return False

    def _is_version_number(self, val: float, context: str) -> bool:
        if not context:
            return False
        version_indicators = ['v1.', 'v2.', 'version', 'Version', 'SDK', 'API']
        if any(ind in context for ind in version_indicators):
            if 0 <= val <= 5:
                return True
        return False

    def _is_year_number(self, val: float, context: str) -> bool:
        """检查是否为年份数字（如 2024, 2023 等）"""
        if not context:
            return False
        if 1990 <= val <= 2030:
            year_indicators = ['年', 'year', 'Year', 'published', 'Published', '©', '(20', '（20']
            if any(ind in context for ind in year_indicators):
                return True
        return False

    def _is_section_number(self, val: float, context: str) -> bool:
        """检查是否为章节号、图表编号等"""
        if not context:
            return False
        # 匹配如 "1.", "2.1", "图3", "表2", "Figure 1" 等模式
        section_patterns = ['^\\d+\\.', '图', '表', 'Figure', 'Table', 'Chapter', '第.*章', '第.*节', '编号', 'No.']
        import re
        for pattern in section_patterns:
            if re.search(pattern, context):
                if 0 < val < 100:
                    return True
        return False

    def _is_citation_number(self, val: float, context: str) -> bool:
        """检查是否为引用编号，如 [1], [2], (3) 等"""
        if not context:
            return False
        import re
        citation_patterns = [r'\[\d+\]', r'\(\d+\)', r'参考文献', r'Reference', r'Citation']
        for pattern in citation_patterns:
            if re.search(pattern, context):
                if 0 < val < 500:
                    return True
        return False

    def _check_numerical_consistency(
        self,
        text: str,
        metrics: Dict[str, List[float]]
    ) -> List[Dict[str, Any]]:
        inconsistencies = []

        abstract_nums = re.findall(r'(\d+\.?\d*)\s*%?', text[:2000])
        body_nums = re.findall(r'acc(?:uracy)?[:\s]*(\d+\.?\d*)', text, re.IGNORECASE)

        if abstract_nums and body_nums:
            try:
                abs_acc = float(re.search(r'\d+\.?\d*', abstract_nums[0]).group())
                if abs_acc > 1:
                    abs_acc = abs_acc / 100

                body_accs = [float(m) for m in body_nums[:3]]
                if body_accs and abs_acc > 0.9 and max(body_accs) < 0.9:
                    inconsistencies.append({
                        "type": "abstract_body_mismatch",
                        "description": "摘要中的准确率与正文不一致",
                        "abstract_value": abs_acc,
                        "body_values": body_accs,
                        "severity": "high"
                    })
            except (ValueError, IndexError):
                pass

        if metrics.get("f1") and metrics.get("precision") and metrics.get("recall"):
            for f1 in metrics["f1"]:
                for prec in metrics["precision"]:
                    for rec in metrics["recall"]:
                        if f1 > 0:
                            expected_f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0
                            if abs(f1 - expected_f1) > 0.1:
                                inconsistencies.append({
                                    "type": "f1_inconsistency",
                                    "description": "F1分数与precision/recall不匹配",
                                    "f1": f1,
                                    "precision": prec,
                                    "recall": rec,
                                    "expected_f1": round(expected_f1, 4),
                                    "severity": "medium"
                                })
                                break

        return inconsistencies[:5]

    def _check_statistical_anomalies(self, metrics: Dict[str, List[float]]) -> List[Dict[str, Any]]:
        anomalies = []

        for metric_name, values in metrics.items():
            if len(values) >= 3:
                mean_val = sum(values) / len(values)

                variance = sum((v - mean_val) ** 2 for v in values) / len(values)
                std_val = math.sqrt(variance)

                if std_val > 0:
                    coefficients = []
                    for v in values:
                        if mean_val != 0:
                            coeff = abs((v - mean_val) / std_val)
                            coefficients.append(coeff)

                    if coefficients and max(coefficients) > 3:
                        outliers = [v for v in values if abs((v - mean_val) / std_val) > 2]
                        if outliers:
                            anomalies.append({
                                "type": "statistical_outlier",
                                "metric": metric_name,
                                "values": values,
                                "mean": round(mean_val, 4),
                                "std": round(std_val, 4),
                                "outliers": outliers[:3],
                                "reason": f"发现{len(outliers)}个统计异常值"
                            })

        return anomalies[:3]

    def _generate_suggestions(
        self,
        suspicious: List[Dict],
        inconsistencies: List[Dict],
        anomalies: List[Dict]
    ) -> List[str]:
        suggestions = []

        if len(suspicious) > 5:
            suggestions.append("发现较多可疑数据点，建议逐一核实")

        if any(s.get("type") == "perfect_score" for s in suspicious):
            suggestions.append("注意完美分数(100%/1.0)的合理性证明")

        if inconsistencies:
            types = set(i.get("type") for i in inconsistencies)
            if "abstract_body_mismatch" in types:
                suggestions.append("确保摘要中的数值与正文一致")
            if "f1_inconsistency" in types:
                suggestions.append("检查F1分数计算公式的正确性")

        if anomalies:
            suggestions.append("发现统计异常值，考虑是否为笔误或异常数据")

        if not suggestions:
            suggestions.append("数据验证通过，未发现明显问题")

        return suggestions


class CitationDataCrossChecker:
    """引用数据交叉验证 - 验证引用数据的一致性"""

    def verify_citation_data(self, thesis_text: str, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证论文中的引用数据是否与原始文献一致

        Args:
            thesis_text: 论文正文
            citations: 引用列表，格式: [{"title": "...", "venue": "...", "year": ..., "claimed_result": "..."}]
        """
        results = {
            "verified": [],
            "mismatched": [],
            "cannot_verify": [],
            "overall_score": 100.0
        }

        for citation in citations:
            title = citation.get("title", "")
            claimed_result = citation.get("claimed_result", "")

            if not claimed_result:
                results["cannot_verify"].append(citation)
                continue

            if title.lower() in thesis_text.lower():
                results["verified"].append({
                    "title": title,
                    "status": "claimed_in_text"
                })
            else:
                results["mismatched"].append({
                    "title": title,
                    "claimed_result": claimed_result,
                    "issue": "引用声明未在正文中明确体现"
                })
                results["overall_score"] -= 5

        results["overall_score"] = max(results["overall_score"], 0.0)
        return results


def verify_data(text: str) -> Dict[str, Any]:
    """快捷数据验证函数"""
    verifier = DataVerifier()
    return verifier.verify(text)