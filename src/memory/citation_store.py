"""
Citation Store - 引用存储模块
负责存储和管理论文中的引用信息
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class CitationStore:
    """引用存储管理器"""

    def __init__(self, storage_path: str = "output/citations.json"):
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self):
        """确保存储目录存在"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({"citations": [], "metadata": {}}, f, ensure_ascii=False, indent=2)

    def add_citation(self, citation: dict) -> str:
        """添加引用"""
        data = self._load()
        citation_id = f"cit_{len(data['citations']) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        citation_entry = {
            "id": citation_id,
            "added_at": datetime.now().isoformat(),
            "verified": False,
            **citation
        }

        data['citations'].append(citation_entry)
        self._save(data)
        return citation_id

    def add_citations_batch(self, citations: List[dict]) -> List[str]:
        """批量添加引用"""
        ids = []
        for citation in citations:
            cid = self.add_citation(citation)
            ids.append(cid)
        return ids

    def get_citation(self, citation_id: str) -> Optional[dict]:
        """获取单个引用"""
        data = self._load()
        for cit in data['citations']:
            if cit['id'] == citation_id:
                return cit
        return None

    def get_all_citations(self) -> List[dict]:
        """获取所有引用"""
        data = self._load()
        return data['citations']

    def verify_citation(self, citation_id: str) -> bool:
        """标记引用为已验证"""
        data = self._load()
        for cit in data['citations']:
            if cit['id'] == citation_id:
                cit['verified'] = True
                cit['verified_at'] = datetime.now().isoformat()
                self._save(data)
                return True
        return False

    def update_citation(self, citation_id: str, updates: dict) -> bool:
        """更新引用信息"""
        data = self._load()
        for i, cit in enumerate(data['citations']):
            if cit['id'] == citation_id:
                data['citations'][i].update(updates)
                data['citations'][i]['updated_at'] = datetime.now().isoformat()
                self._save(data)
                return True
        return False

    def search_citations(self, keyword: str) -> List[dict]:
        """搜索引用"""
        data = self._load()
        results = []
        keyword_lower = keyword.lower()

        for cit in data['citations']:
            search_fields = ['title', 'authors', 'abstract', 'venue']
            for field in search_fields:
                if field in cit and keyword_lower in str(cit[field]).lower():
                    results.append(cit)
                    break

        return results

    def get_unverified_citations(self) -> List[dict]:
        """获取未验证的引用"""
        data = self._load()
        return [cit for cit in data['citations'] if not cit.get('verified', False)]

    def _load(self) -> dict:
        """加载数据"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"citations": [], "metadata": {}}

    def _save(self, data: dict):
        """保存数据"""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def export_citations(self, format: str = "bibtex") -> str:
        """导出引用为指定格式"""
        data = self._load()
        citations = data['citations']

        if format == "bibtex":
            lines = []
            for cit in citations:
                key = cit.get('key', cit['id'])
                lines.append(f"@article{{{key},")
                for k, v in cit.items():
                    if k not in ['id', 'key', 'added_at', 'verified', 'verified_at']:
                        lines.append(f"  {k} = {{{v}}},")
                lines.append("}\n")
            return "\n".join(lines)

        elif format == "text":
            lines = []
            for i, cit in enumerate(citations, 1):
                lines.append(f"[{i}] {cit.get('title', 'N/A')} - {cit.get('authors', 'N/A')}")
            return "\n".join(lines)

        return ""

    def clear(self):
        """清空所有引用"""
        self._save({"citations": [], "metadata": {}})


if __name__ == "__main__":
    store = CitationStore()

    test_citations = [
        {
            "title": "Attention Is All You Need",
            "authors": ["Vaswani et al."],
            "year": "2017",
            "venue": "NeurIPS",
            "key": "vaswani2017attention"
        },
        {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "authors": ["Devlin et al."],
            "year": "2019",
            "venue": "NAACL",
            "key": "devlin2019bert"
        }
    ]

    ids = store.add_citations_batch(test_citations)
    print(f"Added citations with IDs: {ids}")

    all_citations = store.get_all_citations()
    print(f"Total citations: {len(all_citations)}")

    print("\nExported BibTeX:")
    print(store.export_citations(format="bibtex"))