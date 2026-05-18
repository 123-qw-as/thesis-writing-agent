"""
LLM Response 工具函数
处理 MiniMax/Anthropic API 返回的不同响应格式
"""

from typing import Any, List, Union


def extract_text_from_response(response: Any) -> str:
    """
    从 LLM 响应中提取文本内容

    支持的响应格式：
    1. 字符串直接返回
    2. List[dict] - MiniMax 格式 [{"type": "text", "text": "..."}]
    3. List[object] - 旧版对象格式
    """
    content = getattr(response, 'content', None)
    if content is None:
        content = str(response) if response else ""

    if isinstance(content, list):
        text_blocks = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text_blocks.append(block.get("text", ""))
            elif hasattr(block, 'type') and hasattr(block, 'text'):
                if block.type == "text":
                    text_blocks.append(block.text)

        if text_blocks:
            return text_blocks[0]

        if len(content) > 0:
            last_block = content[-1]
            if isinstance(last_block, dict) and "text" in last_block:
                return last_block["text"]
            elif hasattr(last_block, 'text'):
                return str(last_block.text)

        return ""

    return str(content) if content else ""


def extract_all_texts_from_response(response: Any) -> List[str]:
    """从响应中提取所有文本块"""
    content = getattr(response, 'content', None)
    if content is None:
        content = str(response) if response else ""

    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
        return texts

    return [str(content)] if content else []