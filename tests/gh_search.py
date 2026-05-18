import requests

queries = [
    'thesis+writing+AI+agent',
    'academic+paper+agent+LangGraph',
    'research+paper+generation+AI',
    'AI+writing+assistant+academic',
    'multi-agent+paper+writing'
]

for q in queries:
    url = f'https://api.github.com/search/repositories?q={q}&per_page=5&sort=stars'
    resp = requests.get(url)
    print(f'Query: {q}')
    data = resp.json()
    for item in data.get('items', [])[:3]:
        stars = item['stargazers_count']
        name = item['full_name']
        desc = item.get('description') or 'N/A'
        if len(desc) > 50:
            desc = desc[:50] + '...'
        print(f'  [{stars}s] {name}')
        print(f'       {desc}')
    print()