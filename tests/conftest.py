import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Union, Optional


@dataclass
class MockTextBlock:
    type: str = 'text'
    text: str = ''


class MockResponse:
    def __init__(self, content: Union[str, list]):
        self.content = content


DEFAULT_MOCK_RESPONSE = '{"scores": {"originality": 3, "methodology": 3, "evidence": 3, "coherence": 3, "writing": 3}}'


class MockLLM:
    def __init__(self, response: str = ''):
        self.response = response or DEFAULT_MOCK_RESPONSE
        self.call_count = 0
        self.last_prompt = ''

    def invoke(self, messages):
        self.call_count += 1
        prompt = messages[0].content if hasattr(messages[0], 'content') else str(messages[0])
        self.last_prompt = prompt
        return MockResponse(content=self.response)

    def bind_tools(self, tools):
        return self
