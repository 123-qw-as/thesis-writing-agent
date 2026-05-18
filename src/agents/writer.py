from langgraph.prebuilt import create_react_agent
from src.prompts.system import WRITER_PROMPT


def create_writer_agent(llm):
    """
    Create the writer agent for thesis writing.
    """
    writer_agent = create_react_agent(
        model=llm,
        prompt=WRITER_PROMPT,
        tools=[]
    )

    return writer_agent