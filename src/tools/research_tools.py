"""
论文搜索工具集 - 多源论文检索
支持: Semantic Scholar(免费), CrossRef(免费), OpenAlex(免费), ArXiv, GitHub, Tavily
"""

import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Any, Optional

# ──────────────────────────────────────────────
# 1. Semantic Scholar API (免费，可选API Key提速)
# ──────────────────────────────────────────────

def search_semantic_scholar(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    搜索Semantic Scholar学术论文
    - 免费，无需强制API Key
    - 无Key: ~1请求/秒 (可能429)
    - 有Key: 100请求/秒 (免费申请: https://www.semanticscholar.org/product/api)
    - 环境变量: SEMANTIC_SCHOLAR_API_KEY (可选)
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        'query': query,
        'limit': min(limit, 100),
        'fields': 'title,authors,year,venue,externalIds,abstract,citationCount'
    }

    api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')

    for attempt in range(3):
        try:
            full_url = f"{url}?{urllib.parse.urlencode(params)}"
            headers = {'User-Agent': 'ThesisBot/1.0'}
            if api_key:
                headers['x-api-key'] = api_key

            req = urllib.request.Request(full_url, headers=headers)

            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode()
                data = json.loads(raw)

            results = []
            for paper in data.get('data', []):
                authors = [a.get('name', '') for a in paper.get('authors', [])]
                title = paper.get('title', '')
                if not title:
                    continue
                ext_ids = paper.get('externalIds') or {}
                results.append({
                    'title': title,
                    'authors': authors[:10],
                    'year': paper.get('year', ''),
                    'venue': paper.get('venue', '') or '',
                    'abstract': (paper.get('abstract', '') or '')[:500],
                    'citations': paper.get('citationCount', 0),
                    'url': paper.get('url', ''),
                    'arxiv_id': ext_ids.get('ArXiv', ''),
                    'doi': ext_ids.get('DOI', ''),
                    'source': 'semantic_scholar'
                })

            return results

        except urllib.error.HTTPError as e:
            wait = (attempt + 1) * 2
            if e.code == 429:
                if attempt < 2:
                    hint = '' if api_key else ' (建议设置 SEMANTIC_SCHOLAR_API_KEY 免费提速)'
                    print(f'  [Semantic Scholar] 频率限制, {wait}秒后重试{hint}')
                    time.sleep(wait)
                    continue
                msg = '频率限制，多次重试仍失败' if api_key else '频率限制，建议设置 SEMANTIC_SCHOLAR_API_KEY 免费解锁'
                return [{'error': f'429 {msg}', 'source': 'semantic_scholar'}]
            return [{'error': f'HTTP {e.code}', 'source': 'semantic_scholar'}]

        except Exception as e:
            if attempt < 2:
                time.sleep(1)
                continue
            return [{'error': str(e)[:80], 'source': 'semantic_scholar'}]


def search_semantic_scholar_by_id(paper_id: str) -> Dict[str, Any]:
    """通过ID获取单篇论文详情"""
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
    params = {
        'fields': 'title,authors,year,venue,externalIds,abstract,citationCount,references,url'
    }

    try:
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(full_url, headers={'User-Agent': 'ThesisBot/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}


# ──────────────────────────────────────────────
# 2. CrossRef API (免费，无需API Key)
# ──────────────────────────────────────────────

def search_crossref(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    搜索CrossRef学术论文
    API: https://api.crossref.org/works
    免费，建议设置mailto礼貌限制
    """
    url = "https://api.crossref.org/works"
    params = {
        'query': query,
        'rows': min(limit, 100),
        'sort': 'relevance',
        'order': 'desc',
    }

    try:
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            full_url,
            headers={'User-Agent': 'ThesisBot/1.0 (mailto:research@example.com)'}
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        results = []
        for item in data.get('message', {}).get('items', []):
            authors = [
                f"{a.get('given', '')} {a.get('family', '')}"
                for a in item.get('author', [])
            ]
            results.append({
                'title': item.get('title', [''])[0],
                'authors': authors[:10],
                'year': item.get('published-print', {}).get('date-parts', [[None]])[0][0]
                         or item.get('published-online', {}).get('date-parts', [[None]])[0][0],
                'venue': item.get('container-title', [''])[0],
                'doi': item.get('DOI', ''),
                'url': f"https://doi.org/{item.get('DOI', '')}" if item.get('DOI') else '',
                'type': item.get('type', ''),
                'publisher': item.get('publisher', ''),
                'is_referenced_by_count': item.get('is-referenced-by-count', 0),
                'source': 'crossref'
            })

        return results

    except Exception as e:
        return [{'error': str(e), 'source': 'crossref'}]


def resolve_doi(doi: str) -> Dict[str, Any]:
    """
    通过DOI解析论文元数据
    例: resolve_doi("10.48550/arXiv.2005.11401")
    """
    url = f"https://api.crossref.org/works/{doi}"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'ThesisBot/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        item = data.get('message', {})
        authors = [
            f"{a.get('given', '')} {a.get('family', '')}"
            for a in item.get('author', [])
        ]

        return {
            'title': item.get('title', [''])[0],
            'authors': authors,
            'year': item.get('published-print', {}).get('date-parts', [[None]])[0][0]
                     or item.get('created', {}).get('date-parts', [[None]])[0][0],
            'venue': item.get('container-title', [''])[0],
            'doi': doi,
            'type': item.get('type', ''),
            'publisher': item.get('publisher', ''),
        }

    except Exception as e:
        return {'error': str(e), 'doi': doi}


# ──────────────────────────────────────────────
# 3. OpenAlex API (完全免费，无需API Key)
# ──────────────────────────────────────────────

def search_openalex(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    搜索OpenAlex学术论文索引
    API: https://api.openalex.org/works
    完全免费，无需API Key，日限10万次
    覆盖2.5亿+论文，含引用数、概念标签、开放获取等
    """
    url = "https://api.openalex.org/works"
    params = {
        'search': query,
        'per-page': min(limit, 200),
        'sort': 'cited_by_count:desc',
        'select': 'id,doi,title,authorships,publication_year,primary_location,cited_by_count,concepts,open_access,abstract_inverted_index'
    }

    try:
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            full_url,
            headers={'User-Agent': 'ThesisBot/1.0 (mailto:research@example.com)'}
        )

        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())

        results = []
        for work in data.get('results', []):
            title = work.get('title', '')
            if not title:
                continue

            authors = []
            for a in work.get('authorships', []):
                author = a.get('author', {})
                authors.append(author.get('display_name', ''))

            venue_info = work.get('primary_location', {}) or {}
            source = venue_info.get('source', {}) or {}
            venue_name = source.get('display_name', '') or ''

            concepts = [c.get('display_name', '') for c in work.get('concepts', [])[:5]]

            abstract = ''
            inverted = work.get('abstract_inverted_index')
            if inverted:
                word_positions = []
                for word, positions in inverted.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = ' '.join(w for _, w in word_positions)[:500]

            oa_info = work.get('open_access', {}) or {}
            oa_url = oa_info.get('oa_url', '') if oa_info else ''

            results.append({
                'title': title,
                'authors': authors[:10],
                'year': work.get('publication_year', ''),
                'venue': venue_name,
                'abstract': abstract,
                'citations': work.get('cited_by_count', 0),
                'doi': work.get('doi', ''),
                'concepts': concepts,
                'open_access': oa_url,
                'url': work.get('id', ''),
                'source': 'openalex'
            })

        return results

    except Exception as e:
        return [{'error': str(e), 'source': 'openalex'}]


def search_openalex_by_concept(concept: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    按OpenAlex概念标签搜索论文
    例: 'Deep learning', 'Computer vision', 'Natural language processing'
    """
    url = "https://api.openalex.org/works"
    params = {
        'filter': f'concepts.display_name:{concept}',
        'per-page': min(limit, 200),
        'sort': 'cited_by_count:desc',
        'select': 'id,doi,title,authorships,publication_year,primary_location,cited_by_count'
    }

    try:
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(full_url, headers={'User-Agent': 'ThesisBot/1.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())

        results = []
        for work in data.get('results', []):
            results.append({
                'title': work.get('title', ''),
                'year': work.get('publication_year', ''),
                'citations': work.get('cited_by_count', 0),
                'doi': work.get('doi', ''),
                'source': 'openalex'
            })
        return results
    except Exception as e:
        return [{'error': str(e), 'source': 'openalex'}]


def search_openalex_by_author(author_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    按作者搜索论文
    """
    url = "https://api.openalex.org/works"
    params = {
        'filter': f'authorships.author.display_name:{author_name}',
        'per-page': min(limit, 200),
        'sort': 'cited_by_count:desc',
        'select': 'id,doi,title,publication_year,primary_location,cited_by_count'
    }

    try:
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(full_url, headers={'User-Agent': 'ThesisBot/1.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())

        results = []
        for work in data.get('results', []):
            results.append({
                'title': work.get('title', ''),
                'year': work.get('publication_year', ''),
                'citations': work.get('cited_by_count', 0),
                'doi': work.get('doi', ''),
                'source': 'openalex'
            })
        return results
    except Exception as e:
        return [{'error': str(e), 'source': 'openalex'}]


# ──────────────────────────────────────────────
# 4. ArXiv API (通过langchain工具)
# ──────────────────────────────────────────────

def search_arxiv(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    搜索ArXiv学术论文
    免费，无需Key，无限制
    使用官方API: http://export.arxiv.org/api/query
    """
    url = "http://export.arxiv.org/api/query"
    params = {
        'search_query': f'all:{query}',
        'start': 0,
        'max_results': min(limit, 50),
        'sortBy': 'relevance',
        'sortOrder': 'descending'
    }

    try:
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(full_url, headers={'User-Agent': 'ThesisBot/1.0'})

        with urllib.request.urlopen(req, timeout=20) as resp:
            xml_data = resp.read().decode('utf-8')

        import xml.etree.ElementTree as ET
        ns = {'atom': 'http://www.w3.org/2005/Atom',
              'arxiv': 'http://arxiv.org/schemas/atom'}

        root = ET.fromstring(xml_data)
        entries = root.findall('atom:entry', ns)

        results = []
        for entry in entries[:limit]:
            title = entry.find('atom:title', ns)
            title = (title.text or '').replace('\n', ' ').strip() if title is not None else ''

            summary = entry.find('atom:summary', ns)
            abstract = (summary.text or '').replace('\n', ' ').strip()[:500] if summary is not None else ''

            published = entry.find('atom:published', ns)
            year = published.text[:4] if published is not None else ''

            authors = []
            for author in entry.findall('atom:author', ns):
                name = author.find('atom:name', ns)
                if name is not None:
                    authors.append(name.text or '')

            link_el = entry.find('atom:id', ns)
            arxiv_id = link_el.text.strip().split('/')[-1] if link_el is not None else ''

            doi = ''
            for link in entry.findall('atom:link', ns):
                href = link.get('href', '')
                if 'doi.org' in href:
                    doi = href
                    break

            results.append({
                'title': title,
                'authors': authors[:10],
                'year': year,
                'abstract': abstract,
                'arxiv_id': arxiv_id,
                'doi': doi,
                'url': f'https://arxiv.org/abs/{arxiv_id}' if arxiv_id else '',
                'venue': 'arXiv',
                'citations': 0,
                'source': 'arxiv'
            })

        if not results:
            return [{'error': 'No results found', 'source': 'arxiv'}]

        return results

    except Exception as e:
        return [{'error': str(e)[:80], 'source': 'arxiv'}]


# ──────────────────────────────────────────────
# 4. GitHub搜索 (集成到工具)
# ──────────────────────────────────────────────

def search_github_repos(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    搜索GitHub上与学术相关的仓库
    API: https://api.github.com/search/repositories
    免费，未认证限制60次/小时
    """
    url = "https://api.github.com/search/repositories"
    params = {
        'q': query,
        'sort': 'stars',
        'order': 'desc',
        'per_page': min(limit, 30)
    }

    try:
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            full_url,
            headers={'User-Agent': 'ThesisBot/1.0', 'Accept': 'application/vnd.github.v3+json'}
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        results = []
        for repo in data.get('items', []):
            desc = (repo.get('description') or '')[:200]
            results.append({
                'title': repo.get('full_name', ''),
                'description': desc.replace('\U0001f9d1', '').replace('\ufe0f', '').strip() if desc else '',
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'language': repo.get('language', ''),
                'url': repo.get('html_url', ''),
                'topics': repo.get('topics', []),
                'source': 'github'
            })

        return results

    except Exception as e:
        return [{'error': str(e), 'source': 'github'}]


# ──────────────────────────────────────────────
# 5. Tavily搜索 (需要TAVILY_API_KEY)
# ──────────────────────────────────────────────

def search_tavily(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    通过Tavily搜索网络（实时信息、技术文档）
    需要设置环境变量 TAVILY_API_KEY
    """
    try:
        from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper

        api_key = os.getenv('TAVILY_API_KEY')
        if not api_key:
            return [{'error': 'TAVILY_API_KEY not set', 'source': 'tavily'}]

        wrapper = TavilySearchAPIWrapper(tavily_api_key=api_key)
        results = wrapper.results(query, max_results)

        parsed = []
        for item in results if isinstance(results, list) else results.get('results', []):
            if isinstance(item, dict):
                parsed.append(item)

        return parsed if parsed else [{'raw': str(results)[:500], 'source': 'tavily'}]

    except Exception as e:
        return [{'error': str(e), 'source': 'tavily'}]


# ──────────────────────────────────────────────
# 6. 统一搜索接口
# ──────────────────────────────────────────────

PAPER_SOURCES = {
    'semantic_scholar': {
        'name': 'Semantic Scholar',
        'free': True,
        'key_required': False,
        'func': search_semantic_scholar,
        'description': '学术论文搜索引擎，覆盖计算机科学、生物学等多领域'
    },
    'openalex': {
        'name': 'OpenAlex',
        'free': True,
        'key_required': False,
        'func': search_openalex,
        'description': '开放学术图谱，覆盖2.5亿+论文，含概念标签和引用分析'
    },
    'crossref': {
        'name': 'CrossRef',
        'free': True,
        'key_required': False,
        'func': search_crossref,
        'description': '学术DOI注册机构，覆盖所有有DOI的正式出版物'
    },
    'arxiv': {
        'name': 'ArXiv',
        'free': True,
        'key_required': False,
        'func': search_arxiv,
        'description': '学术预印本，物理、数学、计算机科学等'
    },
    'github': {
        'name': 'GitHub',
        'free': True,
        'key_required': False,
        'func': search_github_repos,
        'description': '代码仓库搜索，可找到项目实现和开源论文'
    },
    'tavily': {
        'name': 'Tavily',
        'free': False,
        'key_required': True,
        'func': search_tavily,
        'description': 'AI搜索API，需TAVILY_API_KEY，适合实时信息'
    },
}


def search_all_sources(query: str, limit_per_source: int = 5) -> Dict[str, Any]:
    """搜索所有可用源并汇总结果"""
    results = {}

    for source_key, source_info in PAPER_SOURCES.items():
        if source_info['key_required']:
            if not os.getenv('TAVILY_API_KEY'):
                continue

        try:
            papers = source_info['func'](query, limit_per_source)
            if papers and not papers[0].get('error'):
                results[source_key] = papers
        except Exception as e:
            results[source_key] = [{'error': str(e)}]

    return results


def format_search_results(results: Dict[str, Any]) -> str:
    """格式化搜索结果用于LLM输入"""
    output = []
    for source, papers in results.items():
        source_name = PAPER_SOURCES.get(source, {}).get('name', source)
        output.append(f"\n=== {source_name} ({len(papers)} results) ===")

        for i, paper in enumerate(papers[:5], 1):
            if paper.get('error'):
                output.append(f"  [{i}] Error: {paper['error']}")
                continue

            title = paper.get('title', '')[:100]
            if not title:
                title = (paper.get('raw', '') or '')[:100]
            authors = ', '.join(paper.get('authors', []))[:80] if isinstance(paper.get('authors'), list) else ''
            year = paper.get('year', '')
            venue = paper.get('venue', '')
            doi = paper.get('doi', '')
            url = paper.get('url', paper.get('arxiv_id', ''))
            citations = paper.get('citations', '')

            output.append(f"  [{i}] {title}")
            if authors:
                output.append(f"       Authors: {authors}")
            if venue:
                output.append(f"       Venue: {venue} ({year})" if year else f"       Venue: {venue}")
            if doi:
                output.append(f"       DOI: {doi}")
            if citations:
                output.append(f"       Cited: {citations} times")
            if url:
                output.append(f"       URL: {url}")

            concepts = paper.get('concepts')
            if concepts:
                output.append(f"       Concepts: {', '.join(concepts[:3])}")

            oa = paper.get('open_access')
            if oa:
                output.append(f"       Open Access: {oa}")

    return '\n'.join(output)


# 快捷函数
def search_papers(query: str, sources: List[str] = None) -> str:
    """
    快捷论文搜索
    
    Args:
        query: 搜索关键词
        sources: 可用源 ['semantic_scholar', 'crossref', 'arxiv', 'github', 'tavily']
                 默认全部可用源
    """
    if sources is None:
        sources = [k for k, v in PAPER_SOURCES.items() if not v['key_required']]

    all_results = {}
    for src in sources:
        info = PAPER_SOURCES.get(src)
        if info and (not info['key_required'] or os.getenv('TAVILY_API_KEY')):
            try:
                papers = info['func'](query, limit=5)
                if papers and 'error' not in papers[0]:
                    all_results[src] = papers
            except:
                pass

    return format_search_results(all_results)


# ──────────────────────────────────────────────
# 7. LangChain Tool wrappers (for LangGraph agents)
# ──────────────────────────────────────────────

def create_tavily_search(**kwargs):
    """
    Create a Tavily search tool for LangChain agents.
    包装 search_tavily 为可被 LangGraph React Agent 调用的工具
    """
    api_key = os.getenv('TAVILY_API_KEY')
    if api_key:
        from langchain_community.tools.tavily_search import TavilySearchResults
        return TavilySearchResults(
            max_results=kwargs.get('max_results', 5),
            tavily_api_key=api_key,
        )

    from langchain_core.tools import Tool
    return Tool(
        name="tavily_search",
        func=lambda q: search_tavily(q),
        description="Search the web using Tavily (requires TAVILY_API_KEY)"
    )


def create_arxiv_search(**kwargs):
    """
    Create an ArXiv search tool for LangChain agents.
    包装 search_arxiv 为可被 LangGraph React Agent 调用的工具
    """
    from langchain_core.tools import Tool
    return Tool(
        name="arxiv_search",
        func=lambda q: search_arxiv(q),
        description="Search academic papers on ArXiv"
    )