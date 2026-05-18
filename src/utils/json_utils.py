"""
JSON安全解析工具 - 替代所有Agent中的不安全 re.search 方式
"""
import json
import re
from typing import Any, Dict, Optional, TypeVar, Type

T = TypeVar('T')


def safe_parse_json(text: str, default: T = None) -> Optional[Dict[str, Any]]:
    """
    安全解析LLM响应中的JSON

    与 re.search 方式不同:
    1. 使用非贪婪匹配，避免灾难性回溯
    2. 先尝试直接解析整个文本
    3. 支持markdown代码块
    4. 多个JSON对象时选择最长的有效对象
    """
    if not text:
        return default

    # 1. 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. 尝试提取markdown代码块
    code_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. 非贪婪匹配所有可能的JSON对象
    candidates = []
    pos = 0
    while True:
        start = text.find('{', pos)
        if start == -1:
            break
        depth = 0
        for end in range(start, len(text)):
            if text[end] == '{':
                depth += 1
            elif text[end] == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:end + 1]
                    try:
                        parsed = json.loads(candidate)
                        candidates.append(parsed)
                    except json.JSONDecodeError:
                        pass
                    pos = end + 1
                    break
        else:
            pos = start + 1

    # 4. 返回最长的有效JSON（通常包含最多信息）
    if candidates:
        return max(candidates, key=lambda x: len(str(x)))

    return default


def safe_parse_json_with_schema(text: str, schema_cls: Type[T]) -> Optional[T]:
    """
    解析JSON并用pydantic schema验证
    
    Args:
        text: LLM返回的文本
        schema_cls: pydantic BaseModel子类
        
    Returns:
        验证通过的实例，或None
    """
    data = safe_parse_json(text)
    if data is None:
        return None
    try:
        if hasattr(schema_cls, 'model_validate'):
            return schema_cls.model_validate(data)
        return schema_cls(**data)
    except Exception:
        return None