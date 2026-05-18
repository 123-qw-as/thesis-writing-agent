import requests

repos = [
    'PaperDebugger/paperdebugger',
    'andyshen1121/paper-agent',
    'hhc2002/papercoder',
    'LTzycLT/Awesome-Autonomous-Research-Agent'
]

for repo in repos:
    url = f'https://api.github.com/repos/{repo}'
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        print(f"{data['full_name']}")
        print(f"  Stars: {data['stargazers_count']}")
        print(f"  Forks: {data['forks_count']}")
        print(f"  Lang: {data.get('language', 'N/A')}")
        print(f"  Desc: {data.get('description', 'N/A')}")
        print(f"  URL: {data['html_url']}")
        print()
    else:
        print(f'{repo}: {resp.status_code}')