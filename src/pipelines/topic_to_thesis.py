"""
Topic-to-Thesis Pipeline - 给题目就生成完整论文
简化版，直接使用LLM生成论文内容 → 评估 → Word/PDF输出
"""

import os, sys, asyncio, json, re, importlib.util
from typing import Dict
from datetime import datetime
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.utils.llm_utils import extract_text_from_response


class TopicToThesisPipeline:
    """题目→论文 Pipeline，带科研图表生成"""

    def __init__(self, llm=None, generate_figures: bool = True):
        api_key = os.environ.get('MINIMAX_API_KEY')
        self.llm = llm or ChatAnthropic(
            model='MiniMax-M2.7', temperature=0.7,
            api_key=api_key,
            base_url='https://api.minimaxi.com/anthropic',
            max_tokens=16384
        )
        self.doc_generator = None
        self.figure_agent = None
        self._generate_figures = generate_figures

    def _load_figure_agent(self):
        if self.figure_agent:
            return self.figure_agent
        from src.agents.figure.agent import FigureAgent
        self.figure_agent = FigureAgent()
        return self.figure_agent

    def _load_doc_generator(self):
        if self.doc_generator:
            # Ensure it has the latest code
            import sys as _sys
            for _m in list(_sys.modules.keys()):
                if 'doc_generator' in _m:
                    del _sys.modules[_m]
        spec = importlib.util.spec_from_file_location(
            'doc_generator',
            os.path.join(os.path.dirname(__file__), '..', 'tools', 'doc_generator.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.doc_generator = mod
        return mod

    def generate_thesis_content(self, topic: str) -> str:
        """生成完整论文Markdown内容"""
        print(f'[1/3] Generating thesis for: {topic}')

        prompt = f'''请撰写一篇完整的学术论文，主题为：{topic}

要求：
1. **论文结构和章节必须完整**，包括以下所有部分：
   - 摘要 (100-150字)
   - 第一章 绪论 (研究背景、研究目的与意义、相关工作、论文结构)
   - 第二章 相关技术与理论基础 (至少3个小节)
   - 第三章 方法设计 (核心算法/方法详细描述)
   - 第四章 实验验证 (数据集、实验设置、结果分析)
   - 第五章 结论与展望
   - 参考文献 (至少5篇真实引用)

2. 写作规范：
   - 使用正式的学术中文写作风格
   - 每章节下应有2-3个小节
   - 包含具体的技术细节，不能空洞
   - 引用使用 [1][2] 格式
   - 论文总字数在3000-5000字左右

3. 格式要求：
   - 一级标题: # 论文标题
   - 二级标题: ## 第一章 绪论
   - 三级标题: ### 1.1 研究背景
   - 四级标题: #### 具体方法名称

请直接输出完整的论文内容。'''

        response = self.llm.invoke([HumanMessage(content=prompt)])
        content = extract_text_from_response(response)

        print(f'  Generated: {len(content)} chars')

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe = re.sub(r'[\\/:*?"<>|\s]', '_', topic)[:30]
        safe = re.sub(r'[^\w\-_]', '', safe, flags=re.ASCII)
        md_path = f'output/thesis_{safe}_{timestamp}.md'
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  Saved Markdown: {md_path}')

        return content

    def evaluate_thesis(self, content: str, topic: str):
        """评估论文质量"""
        print(f'[2/3] Evaluating thesis quality...')

        from src.agents.evaluation.agent import evaluate_thesis as eval_fn

        async def _eval():
            report = await eval_fn(content, topic, 1)
            return report

        report = asyncio.run(_eval())

        print(f'  Overall: {report.overall_score}/10')
        print(f'  AIGC: {report.aigc_score}%')
        print(f'  Data: {report.data_authenticity}%')
        print(f'  Pass: {"YES" if report.is_pass else "NO"}')

        return report

    def export_word(self, content: str, topic: str) -> str:
        """导出Word文档"""
        print(f'[3/3] Exporting Word document...')

        mod = self._load_doc_generator()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe = re.sub(r'[\\/:*?"<>|\s]', '_', topic)[:30]
        safe = re.sub(r'[^\w\-_]', '', safe, flags=re.ASCII)
        docx_path = f'output/thesis_{safe}_{timestamp}.docx'

        actual = mod.generate_thesis_docx(content, topic, output_path=docx_path)

        size = os.path.getsize(actual)
        print(f'  Saved: {actual}')
        print(f'  Size: {size:,} bytes')

        return actual

    def generate_figures(self, topic: str) -> Dict[str, str]:
        """为论文生成科研图表"""
        if not self._generate_figures:
            return {}

        print(f'[1b/3] Generating scientific figures...')

        agent = self._load_figure_agent()
        import numpy as np

        np.random.seed(42)
        models = ['Ours', 'Baseline-A', 'Baseline-B', 'SOTA']
        datasets = ['Dataset-A', 'Dataset-B', 'Dataset-C', 'Dataset-D']
        metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']

        bar_base = [96.2, 93.1, 91.5, 94.8]
        rand_offsets = np.random.uniform(-2, 2, (len(models), len(datasets)))

        figures = {}

        f1 = agent.bar_chart({
            'categories': datasets,
            'groups': {m: list(np.clip(np.array(bar_base) + rand_offsets[i], 85, 99))
                       for i, m in enumerate(models)},
            'title': f'{topic} - Performance Comparison',
            'ylabel': 'Score (%)'
        }, filename='fig1_performance_comparison')
        figures['fig1'] = f1

        epochs = list(range(0, 51, 5))
        train_curve = np.clip(0.4 + 0.5 * (1 - np.exp(-np.array(epochs) / 15)) + np.random.normal(0, 0.02, len(epochs)), 0, 1)
        val_curve = np.clip(0.38 + 0.48 * (1 - np.exp(-np.array(epochs) / 20)) + np.random.normal(0, 0.015, len(epochs)), 0, 1)

        f2 = agent.line_chart({
            'x': epochs,
            'series': {'Training Acc': list(train_curve), 'Validation Acc': list(val_curve)},
            'title': 'Training Convergence',
            'xlabel': 'Epoch', 'ylabel': 'Accuracy'
        }, filename='fig2_convergence')
        figures['fig2'] = f2

        ablation_data = {
            'Full Model': 96.2, '-w/o Attention': 92.8, '-w/o Residual': 93.5,
            '-w/o Augmentation': 94.1, '-w/o Regularization': 93.8
        }
        f3 = agent.bar_chart({
            'categories': list(ablation_data.keys()),
            'groups': {'Score': list(ablation_data.values())},
            'title': 'Ablation Study',
            'ylabel': 'Accuracy (%)',
            'stacked': False
        }, filename='fig3_ablation', figsize=(10, 6))
        figures['fig3'] = f3

        metrics_matrix = np.array([
            [96.2, 95.8, 95.1, 95.5],
            [93.1, 92.5, 91.8, 92.3],
            [91.5, 90.8, 90.2, 90.7],
            [94.8, 94.2, 93.7, 94.1],
        ])
        f4 = agent.heatmap({
            'matrix': metrics_matrix,
            'row_labels': models,
            'col_labels': metrics_names,
            'title': 'Multi-Metric Performance Matrix',
            'diverging': False,
            'annotate': True
        }, filename='fig4_metrics_heatmap', figsize=(8, 6))
        figures['fig4'] = f4

        print(f'  Generated {len(figures)} figures in output/figures/')
        return figures

    def embed_figures_in_thesis(self, content: str, figures: Dict[str, str]) -> str:
        """将图表嵌入到论文中"""
        if not figures:
            return content

        for fig_name, fig_path in figures.items():
            fig_rel = fig_path.replace('\\', '/')
            img_md = f'\n![{fig_name}]({fig_rel})\n\n'

            import re
            experiment_patterns = [
                r'^##\s+第[四四4].*[章节]',
                r'^##\s+[44]\.?\s*',
                r'^##\s+实验',
                r'^##\s+Experiment',
            ]
            insert_pos = -1
            for pattern in experiment_patterns:
                m = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                if m:
                    insert_pos = m.start()
                    break

            if insert_pos != -1:
                fig_idx = list(figures.keys()).index(fig_name) + 1
                ref_md = f'**Figure {fig_idx}: Experimental results of the proposed method.**\n'
                content = content[:insert_pos] + f'\n{img_md}{ref_md}\n' + content[insert_pos:]

        return content

    def run(self, topic: str) -> dict:
        """完整执行：生成 → 图表 → 评估 → 导出"""
        print('='*60)
        print('TOPIC → THESIS PIPELINE (with Scientific Figures)')
        print('='*60)
        print(f'Topic: {topic}')
        print()

        content = self.generate_thesis_content(topic)

        figures = self.generate_figures(topic)
        if figures:
            content = self.embed_figures_in_thesis(content, figures)

        report = self.evaluate_thesis(content, topic)

        docx_path = self.export_word(content, topic)

        result = {
            'topic': topic,
            'content': content,
            'overall_score': report.overall_score,
            'aigc_score': report.aigc_score,
            'data_authenticity': report.data_authenticity,
            'is_pass': report.is_pass,
            'docx_path': docx_path,
            'figures': list(figures.values())
        }

        print()
        print('='*60)
        print('COMPLETE!')
        print(f'  Topic: {topic}')
        print(f'  Quality: {result["overall_score"]}/10')
        print(f'  Document: {docx_path}')
        print(f'  Figures: {len(figures)} generated')
        print(f'  PASS: {"YES" if result["is_pass"] else "NO"}')
        print('='*60)

        return result


# CLI入口
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Topic → Thesis Generator')
    parser.add_argument('topic', nargs='?', default='基于知识图谱的个性化推荐系统研究',
                       help='论文题目')
    args = parser.parse_args()

    pipeline = TopicToThesisPipeline()
    result = pipeline.run(args.topic)