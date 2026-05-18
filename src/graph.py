from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_task: str
    research_results: str
    code_results: str
    thesis_content: str
    feedback: str


def create_thesis_workflow(llm):
    """
    Create the thesis writing workflow using LangGraph.
    """
    from src.agents.researcher import create_researcher_agent
    from src.agents.coder import create_coder_agent
    from src.agents.writer import create_writer_agent

    researcher = create_researcher_agent(llm)
    coder = create_coder_agent(llm)
    writer = create_writer_agent(llm)

    def supervisor_node(state: AgentState) -> AgentState:
        """Supervisor decides next action based on current state."""
        messages = state["messages"]
        last_message = messages[-1] if messages else None

        if isinstance(last_message, HumanMessage):
            task = last_message.content
            return {
                "current_task": "research",
                "messages": messages + [AIMessage(content="开始研究阶段...")]
            }
        elif state["current_task"] == "research":
            return {
                "current_task": "code",
                "messages": messages + [AIMessage(content="研究完成，开始编写代码...")]
            }
        elif state["current_task"] == "code":
            return {
                "current_task": "write",
                "messages": messages + [AIMessage(content="代码完成，开始撰写论文...")]
            }
        elif state["current_task"] == "write":
            return {
                "current_task": "done",
                "messages": messages + [AIMessage(content="论文撰写完成。")]
            }
        return state

    def researcher_node(state: AgentState) -> AgentState:
        """Researcher searches for relevant literature."""
        messages = state["messages"]
        user_input = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")

        result = researcher.invoke({"messages": [HumanMessage(content=user_input)]})

        return {
            "research_results": result.get("messages", [])[-1].content if result.get("messages") else "",
            "messages": messages + result.get("messages", [])
        }

    def coder_node(state: AgentState) -> AgentState:
        """Coder executes Python for analysis."""
        messages = state["messages"]
        task = state.get("research_results", "")

        result = coder.invoke({
            "messages": [HumanMessage(content=f"基于以下研究结果编写Python代码：\n{task}")]
        })

        return {
            "code_results": result.get("messages", [])[-1].content if result.get("messages") else "",
            "messages": messages + result.get("messages", [])
        }

    def writer_node(state: AgentState) -> AgentState:
        """Writer composes the thesis."""
        messages = state["messages"]
        research = state.get("research_results", "")
        code = state.get("code_results", "")

        result = writer.invoke({
            "messages": [HumanMessage(content=f"根据以下内容撰写论文：\n研究结果：{research}\n代码结果：{code}")]
        })

        return {
            "thesis_content": result.get("messages", [])[-1].content if result.get("messages") else "",
            "messages": messages + result.get("messages", [])
        }

    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("writer", writer_node)

    workflow.add_edge("supervisor", "researcher")
    workflow.add_edge("researcher", "coder")
    workflow.add_edge("coder", "writer")
    workflow.add_edge("writer", END)

    workflow.set_entry_point("supervisor")

    return workflow.compile()