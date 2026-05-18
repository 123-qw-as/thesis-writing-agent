"""
Vector Store - 轻量向量存储模块
使用JSON文件存储文献向量，支持基本的相似度检索
"""

import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import math


class SimpleVectorStore:
    """轻量级向量存储（使用词袋模型模拟）"""

    def __init__(self, storage_path: str = "output/vectors.json"):
        self.storage_path = storage_path
        self.dimension = 128
        self._ensure_storage()

    def _ensure_storage(self):
        """确保存储目录存在"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({"vectors": [], "metadata": {}}, f, ensure_ascii=False, indent=2)

    def _text_to_vector(self, text: str, dimension: int = 128) -> List[float]:
        """简单文本向量化（词频统计）"""
        words = text.lower().split()
        word_freq = {}

        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        vector = [0.0] * dimension
        unique_words = list(word_freq.keys())[:dimension]

        for i, word in enumerate(unique_words):
            vector[i] = word_freq[word] / max(len(words), 1)

        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        if len(v1) != len(v2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(v1, v2))
        return max(0.0, min(1.0, dot_product))

    def add_document(self, doc_id: str, text: str, metadata: dict = None) -> str:
        """添加文档到向量库"""
        data = self._load()

        existing = [d for d in data['vectors'] if d['id'] == doc_id]
        if existing:
            return doc_id

        vector = self._text_to_vector(text, self.dimension)

        doc_entry = {
            "id": doc_id,
            "text": text[:500],
            "vector": vector,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }

        data['vectors'].append(doc_entry)
        self._save(data)
        return doc_id

    def search(self, query: str, top_k: int = 5, threshold: float = 0.1) -> List[Dict]:
        """向量检索"""
        data = self._load()
        query_vector = self._text_to_vector(query, self.dimension)

        results = []
        for doc in data['vectors']:
            similarity = self._cosine_similarity(query_vector, doc['vector'])
            if similarity >= threshold:
                results.append({
                    "id": doc['id'],
                    "text": doc['text'],
                    "metadata": doc.get('metadata', {}),
                    "similarity": similarity
                })

        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]

    def get_document(self, doc_id: str) -> Optional[dict]:
        """获取文档"""
        data = self._load()
        for doc in data['vectors']:
            if doc['id'] == doc_id:
                return doc
        return None

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        data = self._load()
        original_count = len(data['vectors'])
        data['vectors'] = [d for d in data['vectors'] if d['id'] != doc_id]

        if len(data['vectors']) < original_count:
            self._save(data)
            return True
        return False

    def get_all_documents(self) -> List[dict]:
        """获取所有文档"""
        data = self._load()
        return [{
            "id": d['id'],
            "text": d['text'],
            "metadata": d.get('metadata', {}),
            "created_at": d.get('created_at', '')
        } for d in data['vectors']]

    def similarity_between(self, doc_id1: str, doc_id2: str) -> float:
        """计算两个文档的相似度"""
        data = self._load()
        doc1 = next((d for d in data['vectors'] if d['id'] == doc_id1), None)
        doc2 = next((d for d in data['vectors'] if d['id'] == doc_id2), None)

        if not doc1 or not doc2:
            return 0.0

        return self._cosine_similarity(doc1['vector'], doc2['vector'])

    def find_duplicates(self, threshold: float = 0.9) -> List[Tuple[str, str]]:
        """查找近似重复的文档"""
        data = self._load()
        duplicates = []

        for i, doc1 in enumerate(data['vectors']):
            for doc2 in data['vectors'][i+1:]:
                sim = self._cosine_similarity(doc1['vector'], doc2['vector'])
                if sim >= threshold:
                    duplicates.append((doc1['id'], doc2['id'], sim))

        return duplicates

    def _load(self) -> dict:
        """加载数据"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"vectors": [], "metadata": {}}

    def _save(self, data: dict):
        """保存数据"""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def clear(self):
        """清空向量库"""
        self._save({"vectors": [], "metadata": {}})


class PaperIndex:
    """论文索引管理器（基于向量存储）"""

    def __init__(self, vector_store: SimpleVectorStore = None):
        self.vector_store = vector_store or SimpleVectorStore()

    def index_paper(self, paper: dict) -> str:
        """索引论文"""
        doc_id = f"paper_{paper.get('id', hashlib.md5(str(paper.get('title', '')).encode()).hexdigest()[:8])}"

        index_text = f"""
        {paper.get('title', '')}
        {paper.get('abstract', '')}
        {paper.get('authors', [])}
        {paper.get('key_contribution', '')}
        {paper.get('method_summary', '')}
        """.strip()

        metadata = {
            "title": paper.get('title', ''),
            "authors": paper.get('authors', []),
            "year": paper.get('year', ''),
            "venue": paper.get('venue', ''),
            "url": paper.get('url', ''),
            "key_contribution": paper.get('key_contribution', '')
        }

        return self.vector_store.add_document(doc_id, index_text, metadata)

    def search_papers(self, query: str, top_k: int = 10) -> List[dict]:
        """搜索论文"""
        results = self.vector_store.search(query, top_k)
        return [{
            "id": r['id'],
            "title": r['metadata'].get('title', 'N/A'),
            "authors": r['metadata'].get('authors', []),
            "year": r['metadata'].get('year', 'N/A'),
            "similarity": r['similarity']
        } for r in results]

    def find_related_papers(self, paper_id: str, top_k: int = 5) -> List[dict]:
        """查找相关论文"""
        source = self.vector_store.get_document(paper_id)
        if not source:
            return []

        related = self.vector_store.search(source['text'], top_k + 1)
        return [r for r in related if r['id'] != paper_id]


if __name__ == "__main__":
    store = SimpleVectorStore()

    test_papers = [
        {
            "id": "p1",
            "title": "Attention Is All You Need",
            "abstract": "We propose a new simple network architecture based solely on attention mechanisms.",
            "authors": ["Vaswani et al."],
            "year": "2017",
            "venue": "NeurIPS",
            "key_contribution": "Transformer architecture"
        },
        {
            "id": "p2",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "abstract": "We introduce a new language representation model called BERT.",
            "authors": ["Devlin et al."],
            "year": "2019",
            "venue": "NAACL",
            "key_contribution": "Bidirectional pre-training"
        }
    ]

    indexer = PaperIndex(store)

    for paper in test_papers:
        indexer.index_paper(paper)
        print(f"Indexed: {paper['title']}")

    print("\nSearching 'attention mechanism':")
    results = store.search("attention mechanism neural network", top_k=5)
    for r in results:
        print(f"  - {r['metadata'].get('title', 'N/A')} (sim: {r['similarity']:.3f})")