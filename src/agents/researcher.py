from langgraph.prebuilt import create_react_agent
from src.prompts.system import RESEARCHER_PROMPT
from src.tools.research_tools import create_tavily_search, create_arxiv_search


def create_researcher_agent(llm):
    """
    Create the researcher agent for literature search.
    """
    researcher_agent = create_react_agent(
        model=llm,
        prompt=RESEARCHER_PROMPT,
        tools=[create_tavily_search(), create_arxiv_search()]
    )

    return researcher_agent