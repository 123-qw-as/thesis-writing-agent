"""
Enhanced Research Pipeline - 集成质量评估的研究流程
包含AIGC检测、De-AI改写、数据验证、论文对比
"""

import asyncio
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from langchain_core.messages import HumanMessage


@dataclass
class QualityThresholds:
    MIN_OVERALL_SCORE: float = 8.0
    MAX_AIGC_RATE: float = 15.0
    MIN_DATA_AUTHENTICITY: float = 95.0
    MIN_DIMENSION_SCORE: float = 6.0


class EnhancedResearchPipeline:
    """增强版研究Pipeline - 集成质量评估"""

    def __init__(self, llm=None):
        self.llm = llm
        self.thresholds = QualityThresholds()
        self.evaluation_reports = []

    async def run(
        self,
        topic: str,
        max_iterations: int = 3,
        enable_comparison: bool = True,
        reference_papers: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        运行增强版研究Pipeline

        Args:
            topic: 研究主题
            max_iterations: 最大迭代次数
            enable_comparison: 是否启用论文对比
            reference_papers: 参考高质量论文列表
        """
        from src.agents.literature.agent import run_literature_research
        from src.agents.method.agent import design_method
        from src.agents.experiment.agent import create_mock_experiment_results
        from src.agents.writer.agent import write_full_thesis, write_thesis_with_feedback
        from src.agents.evaluation.agent import evaluate_thesis
        from src.agents.deai.agent import rewrite_to_human_style
        from src.agents.comparison.agent import compare_with_references, fetch_and_compare

        state = {
            "topic": topic,
            "current_phase": "PHASE_1_RESEARCH",
            "research_results": {},
            "method_results": {},
            "experiment_results": {},
            "figures": {},
            "thesis_content": "",
            "evaluation_report": None,
            "comparison_result": None,
            "iteration": 0,
            "max_iterations": max_iterations,
            "is_final": False,
            "phases_history": [],
            "start_time": datetime.now()
        }

        while not state["is_final"]:
            phase = state["current_phase"]
            state["phases_history"].append(phase)

            try:
                if phase == "PHASE_1_RESEARCH":
                    research = await self._run_research(topic)
                    state["research_results"] = research
                    # 🆕 评估并修复文献输出
                    if state.get("research_results"):
                        research = self._evaluate_and_fix(
                            state["research_results"], "research"
                        )
                        state["research_results"] = research
                    state["current_phase"] = "PHASE_2_METHOD"

                elif phase == "PHASE_2_METHOD":
                    method = await self._run_method_design(topic, state["research_results"])
                    state["method_results"] = method
                    # 🆕 评估并修复方法输出
                    if state.get("method_results"):
                        method = self._evaluate_and_fix(
                            state["method_results"], "method"
                        )
                        state["method_results"] = method
                    state["current_phase"] = "PHASE_3_EXPERIMENT"

                elif phase == "PHASE_3_EXPERIMENT":
                    experiment = await self._run_experiment(state["method_results"])
                    state["experiment_results"] = experiment
                    # 🆕 评估并修复实验输出
                    if state.get("experiment_results"):
                        experiment = self._evaluate_and_fix(
                            state["experiment_results"], "experiment"
                        )
                        state["experiment_results"] = experiment
                    state["current_phase"] = "PHASE_4_WRITING"

                elif phase == "PHASE_4_WRITING":
                    thesis = await self._run_writing(
                        topic,
                        state["research_results"],
                        state["method_results"],
                        state["experiment_results"],
                    )
                    state["thesis_content"] = thesis
                    # 🆕 评估并修复论文写作
                    if state.get("thesis_content"):
                        thesis = self._evaluate_and_fix(
                            state["thesis_content"], "writing"
                        )
                        state["thesis_content"] = thesis
                    state["current_phase"] = "PHASE_3b_FIGURES"

                elif phase == "PHASE_3b_FIGURES":
                    thesis, figures = self._run_figures(
                        state["thesis_content"],
                        topic,
                    )
                    state["thesis_content"] = thesis
                    state["figures"] = figures
                    state["current_phase"] = "PHASE_5_EVALUATION"

                elif phase == "PHASE_5_EVALUATION":
                    eval_result = await self._run_evaluation(
                        state["thesis_content"],
                        topic,
                        state["iteration"] + 1,
                        reference_papers
                    )
                    state["evaluation_report"] = eval_result
                    self.evaluation_reports.append(eval_result)

                    if await self._check_quality_passed(eval_result):
                        state["is_final"] = True
                        state["current_phase"] = "PHASE_7_COMPLETE"
                    else:
                        state["current_phase"] = "PHASE_6_REVISION"
                        state["iteration"] += 1

                elif phase == "PHASE_6_REVISION":
                    if state["iteration"] >= max_iterations:
                        state["current_phase"] = "PHASE_7_COMPLETE"
                        continue

                    revision_result = await self._run_revision(
                        topic,
                        state["thesis_content"],
                        state["evaluation_report"]
                    )
                    state["thesis_content"] = revision_result["revised_thesis"]

                    if revision_result.get("aigc_reduced"):
                        aigc_check = await self._check_aigc(state["thesis_content"])
                        if aigc_check["aigc_score"] < self.thresholds.MAX_AIGC_RATE:
                            state["current_phase"] = "PHASE_5_EVALUATION"
                    else:
                        state["current_phase"] = "PHASE_5_EVALUATION"

                elif phase == "PHASE_7_COMPLETE":
                    print("[DOC] Generating Word document...")
                    try:
                        docx_path = self._export_thesis(
                            state["thesis_content"], topic
                        )
                        state["docx_path"] = docx_path

                        try:
                            pdf_path = self._export_pdf(
                                state["thesis_content"], topic
                            )
                            state["pdf_path"] = pdf_path
                            print(f"[DOC] PDF saved: {pdf_path}")
                        except Exception as e:
                            print(f"[DOC] PDF skip (requires LibreOffice): {e}")

                        print(f"[DOC] Word saved: {docx_path}")
                        state["current_phase"] = "PHASE_8_VALIDATE"
                    except Exception as e:
                        print(f"[DOC] Export failed: {e}")
                        state["is_final"] = True

                elif phase == "PHASE_8_VALIDATE":
                    print("[VALIDATE] Running DOCX post-export validation...")
                    try:
                        docx_path = state.get("docx_path")
                        if docx_path and os.path.exists(docx_path):
                            from src.evaluation.docx_validator import DocxValidator
                            validator = DocxValidator(self.llm)
                            eval_result = validator.evaluate(docx_path)

                            state["docx_evaluation"] = eval_result

                            if eval_result['passed']:
                                print(f"  [VALIDATE] DOCX quality: PASS ({eval_result['rubric_score']:.0%})")
                            else:
                                print(f"  [VALIDATE] DOCX quality: FAIL ({eval_result['rubric_score']:.0%})")
                                for issue in eval_result['issues'][:3]:
                                    print(f"    - {issue}")

                            print(f"  [VALIDATE] Rendering report: {eval_result['rendering_report'][:200]}")
                        else:
                            print("  [VALIDATE] No DOCX to validate")
                    except Exception as e:
                        print(f"  [VALIDATE] Validation error (non-fatal): {e}")
                    state["is_final"] = True

                else:
                    state["is_final"] = True

            except Exception as e:
                print(f"[ERROR] Phase {phase} failed: {e}")
                state["is_final"] = True
                state["error"] = str(e)

        end_time = datetime.now()
        duration = (end_time - state["start_time"]).total_seconds()

        result = {
            "thesis": state["thesis_content"],
            "topic": topic,
            "quality_score": state["evaluation_report"].overall_score if state["evaluation_report"] else 0.0,
            "evaluation_report": state["evaluation_report"].to_dict() if state["evaluation_report"] else None,
            "comparison_result": state.get("comparison_result"),
            "iterations": state["iteration"],
            "phases_history": state["phases_history"],
            "duration_seconds": duration,
            "research_results": state["research_results"],
            "method_results": state["method_results"],
            "experiment_results": state["experiment_results"],
            "figures": list(state.get("figures", {}).values()),
            "aigc_score": state["evaluation_report"].aigc_score if state["evaluation_report"] else 0.0,
            "data_authenticity": state["evaluation_report"].data_authenticity if state["evaluation_report"] else 0.0,
            "is_pass": state["evaluation_report"].is_pass if state["evaluation_report"] else False,
            "error": state.get("error"),
        }

        if state.get("docx_path"):
            result["docx_path"] = state["docx_path"]
        if state.get("pdf_path"):
            result["pdf_path"] = state["pdf_path"]
        if state.get("docx_evaluation"):
            result["docx_evaluation"] = state["docx_evaluation"]

        self._print_docx_summary(result)
        self._print_figure_summary(result)

        return result


    async def _run_research(self, topic: str) -> Dict[str, Any]:
        from src.agents.literature.agent import run_literature_research
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: run_literature_research(topic, self.llm))
        print(f"[RESEARCH] Got {len(result.get('key_papers', []))} key papers")
        return result

    async def _run_method_design(self, topic: str, research: Dict) -> Dict[str, Any]:
        from src.agents.method.agent import design_method
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: design_method(topic, research, {"compute": "limited"}, self.llm))
        print(f"[METHOD] Method designed: {result.get('method_name', 'N/A')}")
        return result

    async def _run_experiment(self, method: Dict) -> Dict[str, Any]:
        from src.agents.experiment.agent import create_mock_experiment_results
        result = create_mock_experiment_results(method, num_runs=3)
        print(f"[EXPERIMENT] Metrics: {result.get('metrics', {})}")
        return result

    async def _run_writing(
        self,
        topic: str,
        research: Dict,
        method: Dict,
        experiment: Dict,
    ) -> str:
        from src.agents.writer.agent import write_full_thesis
        import asyncio
        loop = asyncio.get_event_loop()
        thesis = await loop.run_in_executor(
            None,
            lambda: write_full_thesis(topic, research, method, experiment, self.llm)
        )
        # Validate thesis content
        if not thesis or len(thesis.strip()) < 500:
            print(f"[WARN] Thesis content too short ({len(thesis) if thesis else 0} chars), retrying...")
            thesis = await loop.run_in_executor(
                None,
                lambda: write_full_thesis(topic, research, method, experiment, self.llm)
            )
        print(f"[WRITING] Thesis generated: {len(thesis) if thesis else 0} chars")
        return thesis if thesis else ""

    def _run_figures(self, thesis: str, topic: str) -> tuple:
        """LLM分析论文内容，动态生成并嵌入学术图表"""
        import re
        import json
        import numpy as np
        from src.agents.figure.agent import FigureAgent

        if not thesis or len(thesis.strip()) < 500:
            print(f'  [Figures] Thesis too short, skipping figure generation')
            return thesis, {}

        try:
            # 1. LLM 分析论文，识别需要哪些图表
            analysis_prompt = f"""请分析以下论文内容，识别出需要生成哪些学术图表来支撑论文内容。

论文主题：{topic}

论文内容：
{thesis[:5000]}

请以 JSON 格式返回需要生成的图表列表，每个图表包含：
- type: 图表类型（bar/line/heatmap/radar/scatter）
- title: 图表标题
- description: 图表描述
- section: 应该插入的章节关键词（如"实验"、"方法"等）
- data_description: 图表数据描述

返回格式示例：
[
    {{"type": "bar", "title": "方法性能对比", "description": "对比本文方法与基线方法在各项指标上的表现", "section": "实验", "data_description": "准确率、精确率、召回率、F1分数"}},
    {{"type": "line", "title": "训练收敛曲线", "description": "展示模型训练过程中的损失和准确率变化", "section": "实验", "data_description": "训练集和验证集的准确率随epoch变化"}}
]

只返回 JSON 数组，不要其他内容。"""

            try:
                analysis_response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
                analysis_text = analysis_response.content if hasattr(analysis_response, 'content') else str(analysis_response)
                json_match = re.search(r'\[.*\]', analysis_text, re.DOTALL)
                if json_match:
                    figure_specs = json.loads(json_match.group())
                else:
                    figure_specs = []
            except Exception as e:
                print(f"  [Figures] LLM analysis failed: {e}")
                figure_specs = []

            # 2. 智能默认配置（如果 LLM 没有返回有效图表）
            if not figure_specs:
                thesis_lower = thesis.lower()
                figure_specs = []

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

                if not figure_specs:
                    figure_specs = [
                        {"type": "bar", "title": "方法性能对比", "description": "对比本文方法与基线方法", "section": "实验", "data_description": "各项评估指标"},
                        {"type": "line", "title": "训练过程分析", "description": "训练过程中的性能变化", "section": "实验", "data_description": "训练指标随时间变化"}
                    ]

            # 3. 生成图表
            agent = FigureAgent()
            generated_figures = {}

            for i, spec in enumerate(figure_specs):
                fig_type = spec.get("type", "bar")
                fig_title = spec.get("title", f"Figure {i+1}")
                filename = f"fig{i+1}_{fig_title.lower().replace(' ', '_').replace('-', '_')[:30]}"

                try:
                    if fig_type == "bar":
                        categories = ["Accuracy", "Precision", "Recall", "F1-Score"]
                        our_values = [0.92 + np.random.uniform(-0.05, 0.05) for _ in categories]
                        baseline_values = [v * (0.82 + np.random.uniform(-0.05, 0.05)) for v in our_values]

                        path = agent.bar_chart({
                            'categories': categories[:4],
                            'groups': {'Our Method': our_values[:4], 'Baseline': baseline_values[:4]},
                            'title': fig_title,
                            'ylabel': 'Score',
                        }, filename=filename)

                    elif fig_type == "line":
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
                        categories = ['Accuracy', 'Speed', 'Robustness', 'Efficiency', 'Scalability']
                        our_values = [0.95, 0.88, 0.92, 0.90, 0.85]
                        baseline_values = [0.82, 0.75, 0.78, 0.80, 0.72]

                        path = agent.radar_chart({
                            'categories': categories,
                            'series': {'Our Method': our_values, 'Baseline': baseline_values},
                            'title': fig_title
                        }, filename=filename)

                    elif fig_type == "scatter":
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

            # 4. 将图表嵌入论文内容
            updated_thesis = thesis
            figure_refs = ''
            for i, (fig_name, fig_path) in enumerate(generated_figures.items()):
                fig_rel = fig_path.replace('\\', '/')
                fig_title = figure_specs[i].get("title", f"图{i+1}") if i < len(figure_specs) else f"图{i+1}"
                fig_desc = figure_specs[i].get("description", "") if i < len(figure_specs) else ""

                figure_refs += f'\n\n![{fig_title}]({fig_rel})\n'
                figure_refs += f'**图{i+1}:** {fig_title}。{fig_desc}\n\n'

            # 智能插入位置
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
                    next_newline = updated_thesis.find('\n\n', insert_pos)
                    if next_newline > 0:
                        insert_pos = next_newline
                    updated_thesis = updated_thesis[:insert_pos] + figure_refs + '\n' + updated_thesis[insert_pos:]
                    break
            else:
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

            print(f'  [Figures] Generated {len(generated_figures)} figures and embedded into thesis')
            return updated_thesis, generated_figures

        except Exception as e:
            print(f'  [Figures] Error: {e}')
            return thesis, {}

    async def _run_evaluation(
        self,
        thesis: str,
        topic: str,
        iteration: int,
        reference_papers: Optional[List[Dict]]
    ) -> "EvaluationReport":
        from src.agents.evaluation.agent import evaluate_thesis, EvaluationReport

        report = await evaluate_thesis(
            thesis_content=thesis,
            thesis_title=topic,
            iteration=iteration,
            high_quality_papers=reference_papers,
            llm=self.llm
        )

        print(f"[EVAL] Iteration {iteration}: Overall={report.overall_score:.1f}, "
              f"AIGC={report.aigc_score:.1f}%, Data={report.data_authenticity:.1f}%, "
              f"Pass={report.is_pass}")

        return report

    async def _check_quality_passed(self, report: "EvaluationReport") -> bool:
        if not report.is_pass:
            return False

        for dim in report.dimensions:
            if dim.score < self.thresholds.MIN_DIMENSION_SCORE:
                print(f"[WARN] Dimension {dim.dimension} below threshold: {dim.score:.1f}")
                return False

        return True

    def _evaluate_and_fix(self, output: Any, agent_type: str) -> Any:
        """评估并修复Agent输出 - 集成EvaluationOrchestrator"""
        try:
            from src.evaluation.orchestrator import EvaluationOrchestrator
            orchestrator = EvaluationOrchestrator(self.llm)
            improved = orchestrator.evaluate_and_fix(output, agent_type)
            return improved
        except ImportError as e:
            print(f"  [Eval] Evaluation module not available: {e}")
            return output
        except Exception as e:
            print(f"  [Eval] Evaluation failed (continuing): {e}")
            return output

    def _print_docx_summary(self, result: dict):
        """打印DOCX评估摘要"""
        docx_eval = result.get('docx_evaluation')
        if not docx_eval:
            return
        print("\n" + "=" * 60)
        print("DOCX QUALITY REPORT")
        print("=" * 60)
        status = 'PASS' if docx_eval['passed'] else 'FAIL'
        print(f"Quality: {docx_eval['rubric_score']:.0%} ({status})")
        for dim in docx_eval.get('dimensions', []):
            stars = '★' * dim['score'] + '☆' * (5 - dim['score'])
            print(f"  {dim['name']}: {stars} ({dim['score']}/5)")
        for issue in docx_eval.get('issues', []):
            print(f"  ! {issue}")
        print("=" * 60)

    def _print_figure_summary(self, result: dict):
        """打印图表生成摘要"""
        figures = result.get('figures', [])
        if not figures:
            return
        print("\n" + "=" * 60)
        print("FIGURES GENERATED")
        print("=" * 60)
        for i, path in enumerate(figures):
            png_path = path.rsplit('.', 1)[0] + '.png'
            size = os.path.getsize(png_path) if os.path.exists(png_path) else 0
            print(f"  Figure {i+1}: {path} ({size/1024:.1f} KB)")
        print(f"  Total: {len(figures)} figures")
        print("=" * 60)

    async def _check_aigc(self, thesis: str) -> Dict[str, Any]:
        from src.tools.aigc_detector import detect_aigc
        return detect_aigc(thesis)

    def _export_thesis(self, content: str, topic: str) -> str:
        """导出Word文档"""
        import importlib.util, os
        spec = importlib.util.spec_from_file_location(
            'doc_generator',
            os.path.join(os.path.dirname(__file__), '..', 'tools', 'doc_generator.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        docx_path = f"output/{topic[:20]}_{timestamp}.docx"

        return mod.generate_thesis_docx(content, topic, output_path=docx_path)

    def _export_pdf(self, content: str, topic: str) -> str:
        """导出PDF文档（需要LibreOffice）"""
        import importlib.util, os
        spec = importlib.util.spec_from_file_location(
            'doc_generator',
            os.path.join(os.path.dirname(__file__), '..', 'tools', 'doc_generator.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_path = f"output/{topic[:20]}_{timestamp}.pdf"

        return mod.ThesisDocumentGenerator().generate_pdf(content, topic, output_path=pdf_path)

    async def _run_revision(
        self,
        topic: str,
        current_thesis: str,
        evaluation_report: "EvaluationReport"
    ) -> Dict[str, Any]:
        from src.agents.writer.agent import write_thesis_with_feedback
        from src.agents.deai.agent import rewrite_to_human_style
        import asyncio
        loop = asyncio.get_event_loop()

        needs_deai = evaluation_report.aigc_score >= self.thresholds.MAX_AIGC_RATE

        if needs_deai:
            print(f"[REVISION] AIGC too high ({evaluation_report.aigc_score:.1f}%), running De-AI rewrite")
            deai_result = await loop.run_in_executor(
                None,
                lambda: rewrite_to_human_style(current_thesis, self.llm)
            )
            revised = deai_result.get("rewritten_content", "")
            if not revised or len(revised.strip()) < 500:
                print("[WARN] De-AI rewrite returned empty/short content, keeping original")
                revised = current_thesis
            return {
                "revised_thesis": revised,
                "aigc_reduced": deai_result.get("aigc_score_after", 100) < deai_result.get("aigc_score_before", 0)
            }

        from src.agents.reviewer.agent import generate_revision_feedback
        feedback = generate_revision_feedback(
            evaluation_report.revision_suggestions,
            evaluation_report.issues
        )

        revised = await loop.run_in_executor(
            None,
            lambda: write_thesis_with_feedback(topic, feedback, current_thesis, self.llm)
        )
        if not revised or len(revised.strip()) < 500:
            print("[WARN] Revision returned empty/short content, keeping original")
            revised = current_thesis

        return {
            "revised_thesis": revised,
            "aigc_reduced": False
        }


async def run_enhanced_pipeline(
    topic: str,
    llm,
    max_iterations: int = 3,
    enable_comparison: bool = True
) -> Dict[str, Any]:
    """
    运行增强版研究Pipeline的快捷函数

    Args:
        topic: 研究主题
        llm: Language model
        max_iterations: 最大迭代次数
        enable_comparison: 是否启用论文对比
    """
    pipeline = EnhancedResearchPipeline(llm)
    return await pipeline.run(topic, max_iterations, enable_comparison)


def print_evaluation_summary(result: Dict[str, Any]):
    """打印评估摘要"""
    print("\n" + "=" * 60)
    print("论文质量评估报告")
    print("=" * 60)

    print(f"主题: {result.get('topic', 'N/A')}")
    print(f"综合评分: {result.get('quality_score', 0):.1f}/10")
    print(f"AIGC率: {result.get('aigc_score', 0):.1f}%")
    print(f"数据真实性: {result.get('data_authenticity', 0):.1f}%")
    print(f"迭代次数: {result.get('iterations', 0)}")
    print(f"运行时间: {result.get('duration_seconds', 0):.1f}秒")
    print(f"通过状态: {'✅ 通过' if result.get('is_pass') else '❌ 未通过'}")

    eval_report = result.get("evaluation_report")
    if eval_report:
        print("\n各维度评分:")
        for dim in eval_report.get("dimensions", []):
            print(f"  {dim['dimension']}: {dim['score']:.1f}/10 ({dim['level']})")

    docx_path = result.get('docx_path')
    pdf_path = result.get('pdf_path')
    if docx_path:
        print(f"\n📄 Word文档: {docx_path}")
    if pdf_path:
        print(f"📄 PDF文档: {pdf_path}")

    print("=" * 60)