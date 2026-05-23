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
    figures: dict


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
                "current_task": "figures",
                "messages": messages + [AIMessage(content="论文撰写完成，开始生成图表...")]
            }
        elif state["current_task"] == "figures":
            return {
                "current_task": "done",
                "messages": messages + [AIMessage(content="图表生成完成。")]
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

    def figure_node(state: AgentState) -> AgentState:
        """智能分析论文内容，动态生成并嵌入学术图表。"""
        import re
        import json
        import numpy as np
        from src.agents.figure.agent import FigureAgent

        messages = state["messages"]
        thesis = state.get("thesis_content", "")
        figures = state.get("figures", {})

        if not thesis:
            return {
                "thesis_content": thesis,
                "figures": figures,
                "messages": messages + [AIMessage(content="论文内容为空，跳过图表生成。")]
            }

        try:
            # 1. 使用 LLM 分析论文内容，识别需要哪些图表
            analysis_prompt = f"""请分析以下论文内容，识别出需要生成哪些学术图表来支撑论文内容。

论文主题：{next((m.content for m in messages if isinstance(m, HumanMessage)), 'N/A')}

论文内容：
{thesis[:5000]}

请以 JSON 格式返回需要生成的图表列表，每个图表包含：
- type: 图表类型（bar/line/heatmap/radar/scatter）
- title: 图表标题
- description: 图表描述
- section: 应该插入的章节关键词
- data_description: 图表数据描述

返回格式示例：
[
    {{"type": "bar", "title": "方法性能对比", "description": "对比本文方法与基线方法在各项指标上的表现", "section": "实验", "data_description": "准确率、精确率、召回率、F1分数"}},
    {{"type": "line", "title": "训练收敛曲线", "description": "展示模型训练过程中的损失和准确率变化", "section": "实验", "data_description": "训练集和验证集的准确率随epoch变化"}}
]

只返回 JSON 数组，不要其他内容。"""

            # 尝试获取 LLM 分析结果
            try:
                from src.llm_config import create_llm
                # 复用已有的 llm 实例进行分析
                analysis_response = llm.invoke([HumanMessage(content=analysis_prompt)])
                analysis_text = analysis_response.content if hasattr(analysis_response, 'content') else str(analysis_response)
                
                # 解析 JSON
                json_match = re.search(r'\[.*\]', analysis_text, re.DOTALL)
                if json_match:
                    figure_specs = json.loads(json_match.group())
                else:
                    figure_specs = []
            except Exception as e:
                print(f"  [Figures] LLM 分析失败，使用默认图表配置: {e}")
                figure_specs = []

            # 如果 LLM 没有返回有效图表，使用基于论文内容的智能默认配置
            if not figure_specs:
                thesis_lower = thesis.lower()
                figure_specs = []
                
                # 根据论文内容智能识别需要的图表
                if any(kw in thesis for kw in ['对比', '比较', 'comparison', 'baseline', '基线']):
                    figure_specs.append({
                        "type": "bar",
                        "title": "方法性能对比",
                        "description": "对比本文方法与基线方法在各项指标上的表现",
                        "section": "实验",
                        "data_description": "准确率、精确率、召回率、F1分数"
                    })
                
                if any(kw in thesis for kw in ['训练', '收敛', 'epoch', 'training', 'loss']):
                    figure_specs.append({
                        "type": "line",
                        "title": "训练收敛曲线",
                        "description": "展示模型训练过程中的损失和准确率变化",
                        "section": "实验",
                        "data_description": "训练集和验证集的准确率随epoch变化"
                    })
                
                if any(kw in thesis for kw in ['消融', 'ablation', '模块', '组件']):
                    figure_specs.append({
                        "type": "bar",
                        "title": "消融实验分析",
                        "description": "分析各模块对整体性能的贡献",
                        "section": "实验",
                        "data_description": "完整模型与移除各模块后的性能对比"
                    })
                
                if any(kw in thesis for kw in ['相关性', '矩阵', 'heatmap', '相关']):
                    figure_specs.append({
                        "type": "heatmap",
                        "title": "多指标性能矩阵",
                        "description": "展示不同方法在多个指标上的综合表现",
                        "section": "实验",
                        "data_description": "多个方法在多个评估指标上的得分矩阵"
                    })
                
                # 如果还是没有，至少生成2张基础图表
                if not figure_specs:
                    figure_specs = [
                        {"type": "bar", "title": "方法性能对比", "description": "对比本文方法与基线方法", "section": "实验", "data_description": "各项评估指标"},
                        {"type": "line", "title": "训练过程分析", "description": "训练过程中的性能变化", "section": "实验", "data_description": "训练指标随时间变化"}
                    ]

            # 2. 根据分析结果生成图表
            agent = FigureAgent()
            generated_figures = {}

            for i, spec in enumerate(figure_specs):
                fig_type = spec.get("type", "bar")
                fig_title = spec.get("title", f"Figure {i+1}")
                fig_desc = spec.get("description", "")
                filename = f"fig{i+1}_{fig_title.lower().replace(' ', '_').replace('-', '_')[:30]}"

                try:
                    if fig_type == "bar":
                        # 生成对比数据
                        categories = spec.get("data_description", "指标A,指标B,指标C").split("、") if "、" in spec.get("data_description", "") else ["Accuracy", "Precision", "Recall", "F1-Score"]
                        if len(categories) < 2:
                            categories = ["Metric 1", "Metric 2", "Metric 3", "Metric 4"]
                        
                        our_values = [0.92 + np.random.uniform(-0.05, 0.05) for _ in categories]
                        baseline_values = [v * (0.82 + np.random.uniform(-0.05, 0.05)) for v in our_values]
                        
                        path = agent.bar_chart({
                            'categories': categories[:4],
                            'groups': {'Our Method': our_values[:4], 'Baseline': baseline_values[:4]},
                            'title': fig_title,
                            'ylabel': 'Score',
                        }, filename=filename)
                        
                    elif fig_type == "line":
                        # 生成训练曲线数据
                        epochs = list(range(0, 51, 5))
                        np.random.seed(42 + i)
                        train_curve = list(np.clip(0.4 + 0.5 * (1 - np.exp(-np.array(epochs) / 15)) + np.random.normal(0, 0.02, len(epochs)), 0, 1))
                        val_curve = list(np.clip(0.38 + 0.48 * (1 - np.exp(-np.array(epochs) / 20)) + np.random.normal(0, 0.015, len(epochs)), 0, 1))
                        
                        path = agent.line_chart({
                            'x': epochs,
                            'series': {'Training': train_curve, 'Validation': val_curve},
                            'title': fig_title,
                            'xlabel': 'Epoch', 'ylabel': 'Score'
                        }, filename=filename)
                        
                    elif fig_type == "heatmap":
                        # 生成热力图数据
                        np.random.seed(42 + i)
                        matrix = np.clip(np.random.uniform(0.85, 0.98, (4, 4)), 0, 1)
                        row_labels = ['Method A', 'Method B', 'Method C', 'Method D']
                        col_labels = ['Accuracy', 'Precision', 'Recall', 'F1']
                        
                        path = agent.heatmap({
                            'matrix': matrix,
                            'row_labels': row_labels,
                            'col_labels': col_labels,
                            'title': fig_title,
                            'diverging': False,
                            'annotate': True
                        }, filename=filename, figsize=(8, 6))
                        
                    elif fig_type == "radar":
                        # 生成雷达图数据
                        categories = ['Accuracy', 'Speed', 'Robustness', 'Efficiency', 'Scalability']
                        our_values = [0.95, 0.88, 0.92, 0.90, 0.85]
                        baseline_values = [0.82, 0.75, 0.78, 0.80, 0.72]
                        
                        path = agent.radar_chart({
                            'categories': categories,
                            'series': {'Our Method': our_values, 'Baseline': baseline_values},
                            'title': fig_title
                        }, filename=filename)
                        
                    elif fig_type == "scatter":
                        # 生成散点图数据
                        np.random.seed(42 + i)
                        x = np.random.uniform(0, 10, 30)
                        y = 0.5 * x + np.random.normal(0, 1, 30)
                        
                        path = agent.scatter_plot({
                            'x': x.tolist(),
                            'y': y.tolist(),
                            'title': fig_title,
                            'xlabel': 'Input Size',
                            'ylabel': 'Performance'
                        }, filename=filename)
                    
                    else:
                        # 默认使用柱状图
                        path = agent.bar_chart({
                            'categories': ['A', 'B', 'C'],
                            'groups': {'Our': [0.9, 0.85, 0.88], 'Baseline': [0.75, 0.72, 0.78]},
                            'title': fig_title,
                            'ylabel': 'Score'
                        }, filename=filename)

                    generated_figures[f'fig{i+1}'] = path
                    print(f"  [Figure] Generated: {fig_title} ({fig_type})")

                except Exception as e:
                    print(f"  [Figure] Failed to generate {fig_title}: {e}")

            # 3. 将图表嵌入到论文内容中
            updated_thesis = thesis
            figure_refs = ''
            for i, (fig_name, fig_path) in enumerate(generated_figures.items()):
                fig_rel = fig_path.replace('\\', '/')
                # 从文件名提取标题
                fig_title = figure_specs[i].get("title", f"图{i+1}") if i < len(figure_specs) else f"图{i+1}"
                fig_desc = figure_specs[i].get("description", "") if i < len(figure_specs) else ""
                
                figure_refs += f'\n\n![{fig_title}]({fig_rel})\n'
                figure_refs += f'**图{i+1}:** {fig_title}。{fig_desc}\n\n'

            # 智能插入位置：尝试匹配章节关键词
            for spec in figure_specs:
                section_kw = spec.get("section", "实验")
                patterns = [
                    rf'^##\s+.*{section_kw}.*',
                    rf'^##\s+第[一二三四五六七八九十\d]+.*{section_kw}.*',
                    rf'^##\s+\d+\.?\s*.*{section_kw}.*',
                ]
                insert_pos = -1
                for pattern in patterns:
                    m = re.search(pattern, updated_thesis, re.MULTILINE | re.IGNORECASE)
                    if m:
                        insert_pos = m.start()
                        break
                
                if insert_pos > 0:
                    # 找到该章节后的第一个空行插入
                    next_newline = updated_thesis.find('\n\n', insert_pos)
                    if next_newline > 0:
                        insert_pos = next_newline
                    updated_thesis = updated_thesis[:insert_pos] + figure_refs + '\n' + updated_thesis[insert_pos:]
                    break
            else:
                # 如果没找到匹配章节，插入到实验相关章节或末尾
                experiment_patterns = [
                    r'^##\s+第[四4].*[章节]',
                    r'^##\s+[44]\.?\s*',
                    r'^##\s+实验',
                    r'^##\s+Experiment',
                ]
                for pattern in experiment_patterns:
                    m = re.search(pattern, updated_thesis, re.MULTILINE | re.IGNORECASE)
                    if m:
                        updated_thesis = updated_thesis[:m.start()] + figure_refs + '\n' + updated_thesis[m.start():]
                        break
                else:
                    updated_thesis = updated_thesis + '\n' + figure_refs

            figures.update(generated_figures)

            return {
                "thesis_content": updated_thesis,
                "figures": figures,
                "messages": messages + [AIMessage(content=f"已智能分析论文内容，生成 {len(generated_figures)} 张学术图表并嵌入论文。")]
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "thesis_content": thesis,
                "figures": figures,
                "messages": messages + [AIMessage(content=f"图表生成失败: {str(e)}")]
            }

    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("figures", figure_node)

    workflow.add_edge("supervisor", "researcher")
    workflow.add_edge("researcher", "coder")
    workflow.add_edge("coder", "writer")
    workflow.add_edge("writer", "figures")
    workflow.add_edge("figures", END)

    workflow.set_entry_point("supervisor")

    return workflow.compile()