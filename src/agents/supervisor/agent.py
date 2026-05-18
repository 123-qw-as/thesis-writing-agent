"""
Supervisor Agent - 任务调度与协调
负责任务拆解、状态管理、Agent调度
"""

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
import operator
import json


class SupervisorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_phase: str
    task_decomposition: dict
    agent_outputs: dict
    research_gap: str
    thesis_structure: dict
    quality_score: float
    iteration_count: int
    max_iterations: int


SUPERVISOR_PROMPT = """你是一个智能研究调度Agent，负责协调整个研究-写作流程。

你的职责：
1. 理解用户输入的研究主题
2. 将复杂任务拆解为可执行的子任务
3. 协调多个专业Agent的工作
4. 管理全局状态和进度
5. 确保最终输出质量

工作流程阶段：
- PHASE_1_RESEARCH: 文献调研与研究问题分析
- PHASE_2_METHOD: 方法设计与创新点确定
- PHASE_3_EXPERIMENT: 实验执行与结果收集
- PHASE_4_WRITING: 论文写作
- PHASE_5_REVIEW: 质量审查与反馈
- PHASE_6_REVISION: 根据反馈修改
- PHASE_7_FINAL: 最终输出

决策规则：
1. 每个阶段完成后，评估输出质量
2. 如果质量不达标，返回上一阶段重做
3. 记录迭代次数，超过max_iterations强制结束
4. 跟踪研究Gap并在创新点模块中处理

状态管理：
- current_phase: 当前执行阶段
- task_decomposition: 拆解后的任务列表
- agent_outputs: 各Agent输出
- quality_score: 当前质量评分(0-10)

输出要求：
- 每次决策都要明确下一步行动
- 包含详细的阶段状态报告
- 识别关键研究Gap和创新机会"""



def create_supervisor_agent(llm) -> any:
    """创建Supervisor Agent"""
    supervisor_agent = create_react_agent(
        model=llm,
        prompt=SUPERVISOR_PROMPT,
        tools=[]
    )
    return supervisor_agent


def analyze_research_topic(topic: str, llm) -> dict:
    """分析研究主题，拆解任务"""
    prompt = f"""分析以下研究主题，拆解为可执行的任务计划：

主题：{topic}

请输出JSON格式的任务拆解计划：
{{
    "main_topic": "主研究主题",
    "sub_tasks": [
        {{
            "id": "task_1",
            "name": "任务名称",
            "type": "research|method|experiment|writing|review",
            "priority": 1-5,
            "dependencies": [],
            "description": "任务描述"
        }}
    ],
    "research_questions": ["研究问题列表"],
    "expected_outcomes": ["预期产出"],
    "initial_gap_analysis": "初步研究Gap分析"
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, 'content') else str(response)

    try:
        if isinstance(content, list):
            for block in content:
                if hasattr(block, 'type') and block.type == 'text':
                    content = block.text
                    break

        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass

    return {
        "main_topic": topic,
        "sub_tasks": [],
        "research_questions": [],
        "expected_outcomes": [],
        "initial_gap_analysis": ""
    }


def should_continue(state: SupervisorState) -> str:
    """判断是否继续迭代"""
    if state.get("quality_score", 0) >= 8.0:
        return "finalize"
    if state.get("iteration_count", 0) >= state.get("max_iterations", 5):
        return "finalize"
    return "continue"


def route_to_agent(task_type: str) -> str:
    """根据任务类型路由到对应Agent"""
    routing = {
        "research": "literature",
        "method": "method",
        "experiment": "experiment",
        "writing": "writer",
        "review": "reviewer"
    }
    return routing.get(task_type, "supervisor")


INITIAL_STATE = {
    "current_phase": "PHASE_1_RESEARCH",
    "task_decomposition": {},
    "agent_outputs": {},
    "research_gap": "",
    "thesis_structure": {},
    "quality_score": 0.0,
    "iteration_count": 0,
    "max_iterations": 5
}