"""
批量修复所有Agent文件中的响应提取逻辑
"""

import os
import re


def fix_file(file_path: str) -> int:
    """修复单个文件，返回修复数量"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    content = content.replace(
        "from langchain_anthropic import ChatAnthropic\nfrom langchain_core.messages import HumanMessage",
        "from langchain_anthropic import ChatAnthropic\nfrom langchain_core.messages import HumanMessage\nfrom src.utils.llm_utils import extract_text_from_response"
    )

    pattern = r'if isinstance\(content, list\):\s*\n\s*for block in content:\s*\n\s*if hasattr\(block, \'type\'\) and block\.type == \'text\':\s*\n\s*return block\.text\s*\nreturn content'
    replacement = """if isinstance(content, list):
        return extract_text_from_response(response)
    return str(content) if content else """""

    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return 1
    return 0


def main():
    agent_files = [
        "src/agents/writer/agent.py",
        "src/agents/literature/agent.py",
        "src/agents/method/agent.py",
        "src/agents/experiment/agent.py",
        "src/agents/reviewer/agent.py",
        "src/agents/innovation/agent.py",
        "src/agents/citation/agent.py",
        "src/agents/consistency/agent.py",
        "src/agents/supervisor/agent.py",
        "tests/test_staged.py",
    ]

    total = 0
    for f in agent_files:
        if os.path.exists(f):
            count = fix_file(f)
            if count > 0:
                print(f"Fixed: {f}")
                total += count
            else:
                print(f"No changes: {f}")
        else:
            print(f"Not found: {f}")

    print(f"\nTotal files fixed: {total}")


if __name__ == "__main__":
    main()