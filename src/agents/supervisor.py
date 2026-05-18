from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from src.prompts.system import SUPERVISOR_PROMPT


def create_supervisor_agent(model_name: str = "gpt-4o-mini"):
    """
    Create the supervisor agent that coordinates the workflow.
    """
    llm = ChatOpenAI(model=model_name, temperature=0.7)

    supervisor_agent = create_react_agent(
        model=llm,
        prompt=SUPERVISOR_PROMPT,
        tools=[]
    )

    return supervisor_agent