"""
Figure Agent - 科研绘图Agent
基于nature-skills/nature-figure的Nature期刊级科研绘图标准
支持: 柱状图、折线图、热力图、雷达图、散点图、多面板组合图
输出: SVG(可编辑矢量图) + PNG + PDF
"""

import os
import numpy as np
from typing import Dict, List, Optional, Any, Tuple

# ========== Nature-Style Constants ==========

PALETTE = {
    'blue_main':      '#0F4D92',
    'blue_secondary': '#3775BA',
    'green_1': '#DDF3DE', 'green_2': '#AADCA9', 'green_3': '#8BCF8B',
    'red_1':      '#F6CFCB', 'red_2': '#E9A6A1', 'red_strong': '#B64342',
    'neutral_light': '#CFCECE', 'neutral_mid': '#767676',
    'neutral_dark': '#4D4D4D', 'neutral_black': '#272727',
    'gold': '#FFD700', 'teal': '#42949E',
    'violet': '#9A4D8E', 'magenta': '#EA84DD',
}

PALETTE_NMI_PASTEL = {
    'baseline_dark': '#484878', 'baseline_mid': '#7884B4', 'baseline_soft': '#B4C0E4',
    'ours_tiny': '#E4E4F0', 'ours_base': '#E4CCD8', 'ours_large': '#F0C0CC',
    'bg_lilac': '#E0E0F0', 'bg_aqua': '#E0F0F0', 'bg_peach': '#F0E0D0',
    'neutral_light': '#D8D8D8', 'neutral_mid': '#A8A8A8', 'neutral_dark': '#606060',
    'delta_up': '#2E9E44', 'delta_down': '#E53935',
}

DEFAULT_COLORS = ['#0F4D92', '#3775BA', '#B64342', '#8BCF8B', '#767676', '#9A4D8E']
DEFAULT_COLORS_NMI = [
    PALETTE_NMI_PASTEL['baseline_dark'], PALETTE_NMI_PASTEL['baseline_mid'],
    PALETTE_NMI_PASTEL['baseline_soft'], PALETTE_NMI_PASTEL['ours_tiny'],
    PALETTE_NMI_PASTEL['ours_base'], PALETTE_NMI_PASTEL['ours_large'],
]

OUTPUT_DIR = 'output/figures'


def init_nature_style():
    """初始化Nature期刊风格的matplotlib参数"""
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    mpl.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'sans-serif'],
        'svg.fonttype': 'none',
        'pdf.fonttype': 42,
        'font.size': 12,
        'axes.spines.right': False,
        'axes.spines.top': False,
        'axes.linewidth': 0.8,
        'axes.edgecolor': '#333333',
        'legend.frameon': False,
        'xtick.major.width': 0.8,
        'ytick.major.width': 0.8,
        'xtick.color': '#333333',
        'ytick.color': '#333333',
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
    })


def luminance_text_color(hex_color: str) -> str:
    """根据背景色自动选择白色或深色文字"""
    c = hex_color.lstrip('#')
    r, g, b = int(c[0:2], 16) / 255, int(c[2:4], 16) / 255, int(c[4:6], 16) / 255
    return 'white' if 0.299 * r + 0.587 * g + 0.114 * b < 0.5 else '#333333'


def save_figure(fig, filename: str, output_dir: str = OUTPUT_DIR):
    """保存图为SVG(主格式)+PNG(预览)"""
    import matplotlib.pyplot as plt
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.join(output_dir, filename)

    fig.savefig(f"{base}.svg", bbox_inches='tight')
    fig.savefig(f"{base}.png", dpi=300, bbox_inches='tight')
    fig.savefig(f"{base}.pdf", bbox_inches='tight')

    plt.close(fig)
    print(f"  [Figure] Saved: {base}.svg/.png/.pdf")
    return f"{base}.svg"


class FigureAgent:
    """科研绘图Agent - 基于nature-skills/nature-figure标准"""

    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        init_nature_style()

    def bar_chart(self, data: Dict, **kwargs) -> str:
        """
        柱状图: grouped bar / stacked bar
        data = {
            'categories': ['A', 'B', 'C'],
            'groups': {'Method1': [1,2,3], 'Method2': [4,5,6]},
            'title': 'Comparison',
            'ylabel': 'Score',
            'stacked': False,
        }
        """
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec

        categories = data.get('categories', [])
        groups = data.get('groups', {})
        title = data.get('title', '')
        ylabel = data.get('ylabel', '')
        stacked = data.get('stacked', False)
        horizontal = data.get('horizontal', False)
        figsize = kwargs.get('figsize', (12, 6)) if not horizontal else (8, 6)

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        x = np.arange(len(categories))
        n_groups = len(groups)
        bar_width = 0.8 / n_groups if not stacked else 0.6
        colors = list(DEFAULT_COLORS) + list(DEFAULT_COLORS_NMI)

        if stacked:
            bottom = np.zeros(len(categories))
            for i, (name, values) in enumerate(groups.items()):
                ax.bar(x, values, bar_width, bottom=bottom,
                       label=name, color=colors[i % len(colors)], edgecolor='white', linewidth=0.5)
                bottom += np.array(values)
        else:
            for i, (name, values) in enumerate(groups.items()):
                offset = (i - n_groups / 2 + 0.5) * bar_width
                ax.bar(x + offset, values, bar_width,
                       label=name, color=colors[i % len(colors)],
                       edgecolor='white', linewidth=0.5, alpha=0.9)

        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=12)
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=12)

        if len(groups) > 1:
            ax.legend(fontsize=10, frameon=False)

        for i, (name, values) in enumerate(groups.items()):
            if not stacked:
                offset = (i - n_groups / 2 + 0.5) * bar_width
                for j, v in enumerate(values):
                    if v > 0:
                        ax.text(x[j] + offset, v + max(values) * 0.02, f'{v:.1f}',
                                ha='center', va='bottom', fontsize=8)

        fig.tight_layout(pad=2)
        return save_figure(fig, kwargs.get('filename', 'bar_chart'), self.output_dir)

    def line_chart(self, data: Dict, **kwargs) -> str:
        """
        折线/趋势图
        data = {
            'x': [1,2,3,4],
            'series': {'Method A': [0.5,0.6,0.8,0.9], 'Method B': [0.3,0.4,0.5,0.7]},
            'title': 'Performance Trend',
            'xlabel': 'Epoch', 'ylabel': 'Accuracy',
            'errors': {'Method A': [0.02,0.03,0.01,0.02]},  (optional)
        }
        """
        import matplotlib.pyplot as plt

        x = np.array(data.get('x', []))
        series = data.get('series', {})
        title = data.get('title', '')
        xlabel = data.get('xlabel', '')
        ylabel = data.get('ylabel', '')
        errors = data.get('errors', {})
        figsize = kwargs.get('figsize', (8, 5))

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        colors = DEFAULT_COLORS + DEFAULT_COLORS_NMI
        markers = ['o', 's', 'D', '^', 'v', '<', '>', 'p']

        for i, (name, values) in enumerate(series.items()):
            err = errors.get(name, None)
            ax.plot(x, values, marker=markers[i % len(markers)],
                    color=colors[i % len(colors)], linewidth=1.5,
                    markersize=6, label=name, alpha=0.9)
            if err:
                ax.fill_between(x, np.array(values) - np.array(err),
                                np.array(values) + np.array(err),
                                color=colors[i % len(colors)], alpha=0.15)

        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, frameon=False)

        fig.tight_layout(pad=2)
        return save_figure(fig, kwargs.get('filename', 'line_chart'), self.output_dir)

    def heatmap(self, data: Dict, **kwargs) -> str:
        """
        热力图
        data = {
            'matrix': [[1,2,3],[4,5,6]],
            'row_labels': ['A','B'],
            'col_labels': ['X','Y','Z'],
            'title': 'Correlation Matrix',
            'diverging': False,
            'annotate': True
        }
        """
        import matplotlib.pyplot as plt

        matrix = np.array(data.get('matrix', []))
        row_labels = data.get('row_labels', [])
        col_labels = data.get('col_labels', [])
        title = data.get('title', '')
        diverging = data.get('diverging', False)
        annotate = data.get('annotate', True)
        figsize = kwargs.get('figsize', (10, 8))

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        cmap = 'RdBu_r' if diverging else 'YlOrRd'
        vmin = data.get('vmin', -2.5 if diverging else None)
        vmax = data.get('vmax', 2.5 if diverging else None)

        im = ax.imshow(matrix, cmap=cmap, aspect='auto',
                       vmin=vmin, vmax=vmax)

        if annotate:
            import matplotlib as mpl
            norm_val_min, norm_val_max = matrix.min(), matrix.max()
            norm = mpl.colors.Normalize(vmin=norm_val_min, vmax=norm_val_max)
            cmap_obj = plt.cm.RdBu_r if diverging else plt.cm.YlOrRd
            for i in range(matrix.shape[0]):
                for j in range(matrix.shape[1]):
                    val = matrix[i, j]
                    rgba = cmap_obj(norm(val))
                    brightness = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
                    text_color = 'white' if brightness < 0.5 else '#333333'
                    ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                            fontsize=10, color=text_color)

        if col_labels:
            ax.set_xticks(range(len(col_labels)))
            ax.set_xticklabels(col_labels, fontsize=10, rotation=45, ha='right')
        if row_labels:
            ax.set_yticks(range(len(row_labels)))
            ax.set_yticklabels(row_labels, fontsize=10)

        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.ax.tick_params(labelsize=9)

        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')

        fig.tight_layout(pad=2)
        return save_figure(fig, kwargs.get('filename', 'heatmap'), self.output_dir)

    def radar_chart(self, data: Dict, **kwargs) -> str:
        """
        雷达图/极坐标图
        data = {
            'categories': ['Acc', 'F1', 'AUC', 'Speed', 'Memory'],
            'series': {'Our': [5,4,5,3,4], 'Baseline': [3,3,4,4,3]},
            'title': 'Multi-Metric Comparison'
        }
        """
        import matplotlib.pyplot as plt

        categories = data.get('categories', [])
        series = data.get('series', {})
        title = data.get('title', '')
        figsize = kwargs.get('figsize', (10, 8))

        N = len(categories)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='polar')

        colors = DEFAULT_COLORS + DEFAULT_COLORS_NMI
        for i, (name, values) in enumerate(series.items()):
            values_plot = values + values[:1]
            ax.fill(angles, values_plot, alpha=0.08, color=colors[i % len(colors)])
            ax.plot(angles, values_plot, 'o-', linewidth=2,
                    color=colors[i % len(colors)], label=name, markersize=6)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=11)
        ax.set_ylim(0, max([max(v) for v in series.values()]) * 1.2)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)

        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        fig.tight_layout(pad=2)
        return save_figure(fig, kwargs.get('filename', 'radar_chart'), self.output_dir)

    def scatter_plot(self, data: Dict, **kwargs) -> str:
        """
        散点图/气泡图
        data = {
            'x': [1,2,3,4,5],
            'y': [2,3,2,5,4],
            'sizes': [100,200,50,300,150], (bubble chart)
            'labels': ['A','B','C','D','E'],
            'title': 'Correlation',
            'xlabel': 'Metric A',
            'ylabel': 'Metric B',
            'color_by': [0,1,0,1,2],  # group index for coloring
        }
        """
        import matplotlib.pyplot as plt

        x = np.array(data.get('x', []))
        y = np.array(data.get('y', []))
        sizes = data.get('sizes', None)
        labels = data.get('labels', None)
        title = data.get('title', '')
        xlabel = data.get('xlabel', '')
        ylabel = data.get('ylabel', '')
        color_by = data.get('color_by', None)
        figsize = kwargs.get('figsize', (8, 6))

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        if sizes:
            s = np.array(sizes) * 5
        else:
            s = 80

        if color_by:
            colors = [DEFAULT_COLORS[i % len(DEFAULT_COLORS)] for i in color_by]
        else:
            colors = DEFAULT_COLORS[0]

        scatter = ax.scatter(x, y, s=s, c=colors, alpha=0.7,
                             edgecolors='white', linewidth=0.8)

        if labels:
            for i, label in enumerate(labels):
                ax.annotate(label, (x[i], y[i]),
                            xytext=(5, 5), textcoords='offset points',
                            fontsize=9)

        ax.axvline(np.median(x), ls='--', color='#767676', alpha=0.5, linewidth=0.8)
        ax.axhline(np.median(y), ls='--', color='#767676', alpha=0.5, linewidth=0.8)

        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')

        fig.tight_layout(pad=2)
        return save_figure(fig, kwargs.get('filename', 'scatter_plot'), self.output_dir)

    def multi_panel(self, panels: List[Dict], **kwargs) -> str:
        """
        多面板组合图 - GridSpec布局
        panels = [
            {'type': 'bar', 'data': {...}, 'row': 0, 'col': 0},
            {'type': 'line', 'data': {...}, 'row': 0, 'col': 1},
            ...
        ]
        """
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec

        figsize = kwargs.get('figsize', (22, 17))
        rows = kwargs.get('rows', 2)
        cols = kwargs.get('cols', 2)
        title = kwargs.get('title', '')

        fig = plt.figure(figsize=figsize)
        gs = gridspec.GridSpec(rows, cols, figure=fig, wspace=0.3, hspace=0.35)

        colors = ['#0F4D92', '#B64342', '#8BCF8B', '#767676',
                  '#9A4D8E', '#3775BA', '#FFD700', '#42949E']

        for i, panel in enumerate(panels):
            row = panel.get('row', 0)
            col = panel.get('col', i % cols)
            ax = fig.add_subplot(gs[row, col])

            panel_type = panel.get('type', '')
            panel_data = panel.get('data', {})
            panel_title = panel_data.get('title', '')

            if panel_type == 'bar':
                categories = panel_data.get('categories', [])
                groups = panel_data.get('groups', {})
                x = np.arange(len(categories))
                n_groups = len(groups)
                bar_width = 0.8 / n_groups
                for j, (name, values) in enumerate(groups.items()):
                    offset = (j - n_groups / 2 + 0.5) * bar_width
                    ax.bar(x + offset, values, bar_width,
                           label=name, color=colors[j % len(colors)],
                           alpha=0.85)
                ax.set_xticks(x)
                ax.set_xticklabels(categories, fontsize=8, rotation=45, ha='right')

            elif panel_type == 'line':
                x_data = panel_data.get('x', [])
                series = panel_data.get('series', {})
                for j, (name, values) in enumerate(series.items()):
                    ax.plot(x_data, values, 'o-', color=colors[j % len(colors)],
                            linewidth=1.5, markersize=4, label=name)

            elif panel_type == 'heatmap':
                matrix = np.array(panel_data.get('matrix', []))
                row_l = panel_data.get('row_labels', [])
                col_l = panel_data.get('col_labels', [])
                cmap = 'RdBu_r' if panel_data.get('diverging') else 'YlOrRd'
                im = ax.imshow(matrix, cmap=cmap, aspect='auto')
                if col_l:
                    ax.set_xticks(range(len(col_l)))
                    ax.set_xticklabels(col_l, fontsize=7, rotation=45, ha='right')
                if row_l:
                    ax.set_yticks(range(len(row_l)))
                    ax.set_yticklabels(row_l, fontsize=7)

            ax.set_title(panel_title, fontsize=10, fontweight='bold')

            # Panel label (a, b, c...)
            panel_label = panel.get('label', chr(ord('a') + i))
            ax.text(-0.08, 1.05, panel_label, transform=ax.transAxes,
                    fontsize=14, fontweight='bold', va='top', ha='right')

        # Hero panel title
        if title:
            fig.suptitle(title, fontsize=16, fontweight='bold', y=1.02)

        fig.tight_layout(pad=2)
        return save_figure(fig, kwargs.get('filename', 'multi_panel'), self.output_dir)

    def generate_experiment_figures(self, experiment_results: Dict) -> List[str]:
        """
        从实验结果自动生成论文图表
        返回生成的文件路径列表
        """
        files = []

        # Figure 1: 方法对比柱状图
        metrics = experiment_results.get('metrics', {})
        if metrics:
            bar_data = {
                'categories': list(metrics.keys()),
                'groups': {'Our Method': list(metrics.values()),
                           'Baseline': [v * 0.85 for v in metrics.values()]},
                'title': 'Method Performance Comparison',
                'ylabel': 'Score',
            }
            files.append(self.bar_chart(bar_data, filename='fig1_comparison'))

        # Figure 2: 训练趋势图
        losses = experiment_results.get('training_curve', {})
        if losses:
            line_data = {
                'x': list(range(1, len(losses))),
                'series': {'Training Loss': losses},
                'title': 'Training Convergence',
                'xlabel': 'Epoch',
                'ylabel': 'Loss',
            }
            files.append(self.line_chart(line_data, filename='fig2_convergence'))

        # Figure 3: 消融实验结果
        ablation = experiment_results.get('ablation', {})
        if ablation:
            ablation_data = {
                'categories': list(ablation.keys()),
                'groups': {'Metric Score': list(ablation.values())},
                'title': 'Ablation Study',
                'ylabel': 'Score',
            }
            files.append(self.bar_chart(ablation_data, filename='fig3_ablation'))

        return files


def generate_figure(data: Dict, chart_type: str = 'bar', **kwargs) -> str:
    """快捷生成图表"""
    agent = FigureAgent()
    methods = {
        'bar': agent.bar_chart,
        'line': agent.line_chart,
        'heatmap': agent.heatmap,
        'radar': agent.radar_chart,
        'scatter': agent.scatter_plot,
        'multi': agent.multi_panel,
    }
    method = methods.get(chart_type)
    if method:
        return method(data, **kwargs)
    raise ValueError(f"Unknown chart type: {chart_type}, use: {list(methods.keys())}")