"""
Experiment History - 实验历史记录模块
负责存储和管理实验配置、结果、图表等
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any


class ExperimentHistory:
    """实验历史记录管理器"""

    def __init__(self, storage_path: str = "output/experiments.json"):
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self):
        """确保存储目录存在"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({"experiments": [], "metadata": {}}, f, ensure_ascii=False, indent=2)

    def add_experiment(self, experiment: dict) -> str:
        """添加实验记录"""
        data = self._load()
        exp_id = f"exp_{len(data['experiments']) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        experiment_entry = {
            "id": exp_id,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "results": {},
            "metrics": {},
            **experiment
        }

        data['experiments'].append(experiment_entry)
        self._save(data)
        return exp_id

    def update_experiment(self, exp_id: str, updates: dict) -> bool:
        """更新实验记录"""
        data = self._load()
        for i, exp in enumerate(data['experiments']):
            if exp['id'] == exp_id:
                data['experiments'][i].update(updates)
                data['experiments'][i]['updated_at'] = datetime.now().isoformat()
                self._save(data)
                return True
        return False

    def complete_experiment(self, exp_id: str, results: dict, metrics: dict) -> bool:
        """标记实验完成并记录结果"""
        return self.update_experiment(exp_id, {
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "results": results,
            "metrics": metrics
        })

    def get_experiment(self, exp_id: str) -> Optional[dict]:
        """获取单个实验"""
        data = self._load()
        for exp in data['experiments']:
            if exp['id'] == exp_id:
                return exp
        return None

    def get_all_experiments(self) -> List[dict]:
        """获取所有实验"""
        data = self._load()
        return data['experiments']

    def get_recent_experiments(self, limit: int = 10) -> List[dict]:
        """获取最近的实验"""
        data = self._load()
        sorted_exps = sorted(
            data['experiments'],
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
        return sorted_exps[:limit]

    def get_experiment_by_config(self, config: dict) -> Optional[dict]:
        """根据配置查找相似实验"""
        data = self._load()
        for exp in reversed(data['experiments']):
            if exp.get('config') == config:
                return exp
        return None

    def compare_experiments(self, exp_ids: List[str]) -> dict:
        """比较多个实验的结果"""
        experiments = []
        for eid in exp_ids:
            exp = self.get_experiment(eid)
            if exp:
                experiments.append(exp)

        if len(experiments) < 2:
            return {"error": "Need at least 2 experiments to compare"}

        comparison = {
            "compared_experiments": [e['id'] for e in experiments],
            "metrics_comparison": {},
            "best_performer": {}
        }

        all_metrics = set()
        for exp in experiments:
            all_metrics.update(exp.get('metrics', {}).keys())

        for metric in all_metrics:
            values = {}
            best_exp_id = None
            best_value = None

            for exp in experiments:
                val = exp.get('metrics', {}).get(metric)
                if val is not None:
                    values[exp['id']] = val
                    if best_value is None or val > best_value:
                        best_value = val
                        best_exp_id = exp['id']

            comparison['metrics_comparison'][metric] = values
            if best_exp_id:
                comparison['best_performer'][metric] = best_exp_id

        return comparison

    def _load(self) -> dict:
        """加载数据"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"experiments": [], "metadata": {}}

    def _save(self, data: dict):
        """保存数据"""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def clear_old_experiments(self, days: int = 30):
        """清除指定天数之前的实验"""
        data = self._load()
        cutoff = datetime.now().timestamp() - (days * 86400)

        filtered = []
        for exp in data['experiments']:
            created = exp.get('created_at', '')
            if created:
                try:
                    exp_time = datetime.fromisoformat(created).timestamp()
                    if exp_time > cutoff:
                        filtered.append(exp)
                except:
                    filtered.append(exp)

        data['experiments'] = filtered
        self._save(data)


if __name__ == "__main__":
    history = ExperimentHistory()

    test_experiments = [
        {
            "name": "ResNet-50 Baseline",
            "config": {
                "model": "ResNet-50",
                "dataset": "CIFAR-10",
                "epochs": 100,
                "batch_size": 128
            },
            "metrics": {
                "accuracy": 0.923,
                "f1_score": 0.921,
                "training_time": 3600
            }
        },
        {
            "name": "Our Method",
            "config": {
                "model": "OurModel",
                "dataset": "CIFAR-10",
                "epochs": 100,
                "batch_size": 128
            },
            "metrics": {
                "accuracy": 0.951,
                "f1_score": 0.949,
                "training_time": 4200
            }
        }
    ]

    exp_ids = []
    for exp in test_experiments:
        eid = history.add_experiment(exp)
        history.complete_experiment(eid, {"accuracy": exp['metrics']['accuracy']}, exp['metrics'])
        exp_ids.append(eid)
        print(f"Added experiment: {eid}")

    print("\nComparing experiments:")
    comparison = history.compare_experiments(exp_ids)
    print(json.dumps(comparison, indent=2))