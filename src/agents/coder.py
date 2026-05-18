from langgraph.prebuilt import create_react_agent
from src.prompts.system import CODER_PROMPT
from src.tools.code_tools import create_python_repl


def create_coder_agent(llm):
    """
    Create the coder agent for Python code execution.
    """
    coder_agent = create_react_agent(
        model=llm,
        prompt=CODER_PROMPT,
        tools=[create_python_repl]
    )

    return coder_agent