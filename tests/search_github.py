import requests
import os

token = os.getenv('GITHUB_TOKEN', '')
headers = {'Authorization': f'token {token}'} if token else {}

queries = [
    'thesis writing agent academic AI LangGraph',
    'research paper generation AI agent',
    'scientific writing assistant LangChain',
    'academic paper workflow multi-agent',
    'literature review automation AI'
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print('='*60)

    url = f'https://api.github.com/search/repositories?q={query}&per_page=10&sort=stars'
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        data = resp.json()
        for item in data.get('items', [])[:8]:
            desc = item.get('description') or 'No description'
            if len(desc) > 80:
                desc = desc[:80] + '...'
            print(f"[{item['stargazers_count']} stars] {item['full_name']}")
            print(f"   {desc}")
            print(f"   {item['html_url']}")
            print()
    else:
        print(f'Status: {resp.status_code} - {resp.text[:200]}')