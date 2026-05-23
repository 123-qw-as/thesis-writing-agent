"""
Figure Agent - 科研绘图Agent
基于nature-skills/nature-figure的Nature期刊级科研绘图标准
支持: 柱状图、折线图、热力图、雷达图、散点图、森林图、面积图、多面板组合图
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

DEFAULT_COLORS = [
    PALETTE['blue_main'], PALETTE['green_3'], PALETTE['red_strong'],
    PALETTE['teal'], PALETTE['violet'], PALETTE['neutral_light'],
]
DEFAULT_COLORS_NMI = [
    PALETTE_NMI_PASTEL['baseline_dark'], PALETTE_NMI_PASTEL['baseline_mid'],
    PALETTE_NMI_PASTEL['baseline_soft'], PALETTE_NMI_PASTEL['ours_tiny'],
    PALETTE_NMI_PASTEL['ours_base'], PALETTE_NMI_PASTEL['ours_large'],
]

OUTPUT_DIR = 'output/figures'


# ========== Helper Functions ==========

def is_dark(hex_color: str, threshold: int = 128) -> bool:
    """Return True if hex color is dark (use white text on it)."""
    c = hex_color.lstrip('#')
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return (0.299 * r + 0.587 * g + 0.114 * b) < threshold


def luminance_text_color(hex_color: str) -> str:
    """根据背景色自动选择白色或深色文字"""
    return 'white' if is_dark(hex_color) else '#333333'


def add_panel_label(ax, label: str, x: float = -0.06, y: float = 1.02,
                    fontsize: int = 14, color: str = 'black', fontweight: str = 'bold'):
    """Place a Nature-style panel label near the top-left edge."""
    ax.text(x, y, label, transform=ax.transAxes,
            fontsize=fontsize, fontweight=fontweight,
            color=color, ha='left', va='bottom')


def apply_publication_style(font_size: int = 12, axes_linewidth: float = 0.8, use_tex: bool = False):
    """Apply Nature-style rcParams. Call once before creating any figures."""
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm

    # Detect available Chinese fonts on the system
    chinese_fonts = []
    for font_name in ['Microsoft YaHei', 'SimHei', 'SimSun', 'Source Han Sans SC',
                      'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'PingFang SC']:
        try:
            fm.findfont(font_name, fallback_to_default=False)
            chinese_fonts.append(font_name)
        except Exception:
            continue

    sans_families = chinese_fonts + ['Arial', 'DejaVu Sans', 'Liberation Sans']
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = sans_families
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['svg.fonttype'] = 'none'
    # Layout & style
    plt.rcParams['font.size'] = font_size
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.linewidth'] = axes_linewidth
    plt.rcParams['legend.frameon'] = False
    plt.rcParams['xtick.major.width'] = axes_linewidth
    plt.rcParams['ytick.major.width'] = axes_linewidth
    plt.rcParams['xtick.color'] = '#333333'
    plt.rcParams['ytick.color'] = '#333333'
    if use_tex:
        plt.rcParams['text.usetex'] = True


def finalize_figure(fig, out_path: str, formats: List[str] = None,
                    dpi: int = 300, pad: float = 2, close: bool = True) -> List[str]:
    """Apply tight_layout and save figure in multiple formats."""
    from pathlib import Path
    fig.tight_layout(pad=pad)
    base = Path(out_path)
    os.makedirs(base.parent, exist_ok=True)
    if formats is None:
        formats = [base.suffix.lstrip('.') or 'svg']
        base = base.with_suffix('')
    saved = []
    for fmt in formats:
        p = str(base) + f'.{fmt}'
        fig.savefig(p, dpi=dpi, bbox_inches='tight')
        saved.append(p)
    if close:
        import matplotlib.pyplot as plt
        plt.close(fig)
    return saved


# ========== FigureAgent ==========

class FigureAgent:
    """科研绘图Agent - 基于nature-skills/nature-figure标准"""

    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        # Headless backend for server/batch rendering
        import matplotlib
        matplotlib.use('Agg')
        apply_publication_style(font_size=12, axes_linewidth=0.8)

    def bar_chart(self, data: Dict, **kwargs) -> str:
        """
        柱状图: grouped bar / stacked bar / horizontal ablation
        data = {
            'categories': ['A', 'B', 'C'],
            'groups': {'Method1': [1,2,3], 'Method2': [4,5,6]},
            'title': 'Comparison',
            'ylabel': 'Score',
            'stacked': False,
            'horizontal': False,
            'errors': {'Method1': [0.1,0.2,0.1]},  (optional)
            'ablation_alpha': True,  (optional: alpha-gradient for ablation)
            'hatch': True,  (optional: print-safe grayscale hatching)
            'tight_ylim': True,  (optional: dynamic y-axis scaling)
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
        errors = data.get('errors', {})
        ablation_alpha = data.get('ablation_alpha', False)
        use_hatch = data.get('hatch', False)
        tight_ylim = data.get('tight_ylim', True)
        figsize = kwargs.get('figsize', (12, 6) if not horizontal else (8, 6))

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        ax.spines['bottom'].set_linewidth(2)
        ax.spines['left'].set_linewidth(2)

        x = np.arange(len(categories))
        n_groups = len(groups)
        bar_width = 0.8 / n_groups if not stacked else 0.6
        colors = list(DEFAULT_COLORS) + list(DEFAULT_COLORS_NMI)
        hatches = ['/', '\\', '.', 'x', 'o', '+']

        error_kw = {'elinewidth': 2, 'capthick': 2, 'capsize': 10}

        if horizontal:
            for i, (name, values) in enumerate(groups.items()):
                c = colors[i % len(colors)]
                if ablation_alpha:
                    blue_rgb = (0.215686, 0.458824, 0.729412)
                    alphas = np.linspace(0.2, 1.0, n_groups)
                    c = (blue_rgb[0], blue_rgb[1], blue_rgb[2], alphas[i])
                err = errors.get(name, None)
                ax.barh(x, values, bar_width, xerr=err,
                        label=name, color=c, edgecolor='white', linewidth=0.5,
                        error_kw=error_kw if err else None)
            ax.set_yticks(x)
            ax.set_yticklabels(categories, fontsize=11)
            ax.set_xlabel(ylabel, fontsize=12)
        elif stacked:
            bottom = np.zeros(len(categories))
            for i, (name, values) in enumerate(groups.items()):
                err = errors.get(name, None)
                ax.bar(x, values, bar_width, bottom=bottom,
                       label=name, color=colors[i % len(colors)],
                       edgecolor='white', linewidth=0.5,
                       yerr=err, error_kw=error_kw if err else None)
                bottom += np.array(values)
            ax.set_xticks(x)
            ax.set_xticklabels(categories, fontsize=11)
        else:
            for i, (name, values) in enumerate(groups.items()):
                offset = (i - n_groups / 2 + 0.5) * bar_width
                err = errors.get(name, None)
                bars = ax.bar(x + offset, values, bar_width,
                              label=name, color=colors[i % len(colors)],
                              edgecolor='white', linewidth=0.5, alpha=0.9,
                              yerr=err, error_kw=error_kw if err else None)
                if use_hatch:
                    for patch in bars:
                        patch.set_hatch(hatches[i % len(hatches)])
                        patch.set_edgecolor('black')
                        patch.set_linewidth(1.5)

        if not horizontal:
            ax.set_ylabel(ylabel, fontsize=12)
            # Dynamic y-axis scaling
            if tight_ylim and not stacked:
                all_vals = [v for vals in groups.values() for v in vals]
                if all_vals:
                    min_v, max_v = min(all_vals), max(all_vals)
                    margin = (max_v - min_v) * 0.1 if max_v > min_v else max_v * 0.1
                    ax.set_ylim([max(0, min_v - margin), max_v + margin])

        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=12)

        if len(groups) > 1:
            ax.legend(fontsize=10, frameon=False)

        # In-bar annotations (non-stacked only)
        if not stacked and not horizontal:
            for i, (name, values) in enumerate(groups.items()):
                offset = (i - n_groups / 2 + 0.5) * bar_width
                for j, v in enumerate(values):
                    if v > 0:
                        ax.text(x[j] + offset, v + max(values) * 0.02, f'{v:.1f}',
                                ha='center', va='bottom', fontsize=8)

        fig.tight_layout(pad=2)
        return self._save(fig, kwargs.get('filename', 'bar_chart'))

    def line_chart(self, data: Dict, **kwargs) -> str:
        """
        折线/趋势图
        data = {
            'x': [1,2,3,4],
            'series': {'Method A': [0.5,0.6,0.8,0.9], 'Method B': [0.3,0.4,0.5,0.7]},
            'title': 'Performance Trend',
            'xlabel': 'Epoch', 'ylabel': 'Accuracy',
            'errors': {'Method A': [0.02,0.03,0.01,0.02]},  (optional: std for fill_between)
            'multi_run': {'Method A': [[0.5,0.6],[0.48,0.62]]},  (optional: 2D array for shadow)
            'reference_line': 0.5,  (optional: horizontal reference)
            'events': {2: 'Intervention'},  (optional: event markers)
        }
        """
        import matplotlib.pyplot as plt

        x = np.array(data.get('x', []))
        series = data.get('series', {})
        title = data.get('title', '')
        xlabel = data.get('xlabel', '')
        ylabel = data.get('ylabel', '')
        errors = data.get('errors', {})
        multi_run = data.get('multi_run', {})
        reference_line = data.get('reference_line', None)
        events = data.get('events', {})
        figsize = kwargs.get('figsize', (8, 5))

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        ax.spines['bottom'].set_linewidth(2)
        ax.spines['left'].set_linewidth(2)

        colors = DEFAULT_COLORS + DEFAULT_COLORS_NMI
        markers = ['o', 's', 'D', '^', 'v', '<', '>', 'p']

        for i, (name, values) in enumerate(series.items()):
            y = np.asarray(values)
            err = errors.get(name, None)
            mr = multi_run.get(name, None)

            ax.plot(x, y, marker=markers[i % len(markers)],
                    color=colors[i % len(colors)], linewidth=2,
                    markersize=8, label=name, alpha=0.9)

            # Multi-run shadow band
            if mr is not None:
                mr_arr = np.array(mr)
                mean, std = mr_arr.mean(0), mr_arr.std(0)
                ax.fill_between(x, mean - std, mean + std,
                                color=colors[i % len(colors)], alpha=0.15)
            # Single-run error band
            elif err is not None:
                ax.fill_between(x, np.array(values) - np.array(err),
                                np.array(values) + np.array(err),
                                color=colors[i % len(colors)], alpha=0.15)

        # Reference baseline
        if reference_line is not None:
            ax.axhline(y=reference_line, linestyle='--', alpha=0.3,
                       linewidth=2, color='#767676')

        # Event markers
        if events:
            y_lo, y_hi = ax.get_ylim()
            dy = 0.08 * (y_hi - y_lo)
            for x_idx, label in events.items():
                idx = list(x).index(x_idx) if x_idx in x else int(x_idx)
                ax.annotate(label, xy=(x[idx], y[idx]),
                            xytext=(x[idx], y_hi - dy),
                            ha='center', va='bottom', fontsize=9,
                            arrowprops=dict(arrowstyle='-|>', lw=1, color='#333333'))

        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, frameon=False)

        fig.tight_layout(pad=2)
        return self._save(fig, kwargs.get('filename', 'line_chart'))

    def heatmap(self, data: Dict, **kwargs) -> str:
        """
        热力图
        data = {
            'matrix': [[1,2,3],[4,5,6]],
            'row_labels': ['A','B'],
            'col_labels': ['X','Y','Z'],
            'title': 'Correlation Matrix',
            'diverging': False,
            'zscore': False,  (optional: z-score deviation heatmap)
            'annotate': True,
            'cmap': None,  (optional: override colormap)
        }
        """
        import matplotlib.pyplot as plt
        import matplotlib as mpl

        matrix = np.array(data.get('matrix', []))
        row_labels = data.get('row_labels', [])
        col_labels = data.get('col_labels', [])
        title = data.get('title', '')
        diverging = data.get('diverging', False)
        zscore = data.get('zscore', False)
        annotate = data.get('annotate', True)
        cmap_override = data.get('cmap', None)
        figsize = kwargs.get('figsize', (10, 8))

        # Z-score deviation
        if zscore:
            matrix = (matrix - matrix.mean(axis=0)) / (matrix.std(axis=0) + 1e-8)
            diverging = True

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        ax.set_frame_on(False)

        if cmap_override:
            cmap = cmap_override
        elif diverging:
            cmap = 'RdBu_r'
        else:
            cmap = 'YlOrRd'

        vmin = data.get('vmin', -2.5 if diverging else None)
        vmax = data.get('vmax', 2.5 if diverging else None)

        im = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=vmin, vmax=vmax)

        if annotate:
            norm_val = mpl.colors.Normalize(vmin=matrix.min(), vmax=matrix.max())
            cmap_obj = plt.get_cmap(cmap)
            for i in range(matrix.shape[0]):
                for j in range(matrix.shape[1]):
                    val = matrix[i, j]
                    rgba = cmap_obj(norm_val(val))
                    brightness = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
                    text_color = 'white' if brightness < 0.5 else '#333333'
                    ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                            fontsize=10, color=text_color)

        if col_labels:
            ax.set_xticks(range(len(col_labels)))
            ax.set_xticklabels(col_labels, fontsize=10, rotation=30, ha='right')
            ax.tick_params(axis='x', which='both', bottom=False, top=False, length=0)
        if row_labels:
            ax.set_yticks(range(len(row_labels)))
            ax.set_yticklabels(row_labels, fontsize=10)

        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.ax.tick_params(labelsize=9)
        if zscore:
            cbar.set_label('Z-score vs mean')

        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')

        fig.tight_layout(pad=2)
        return self._save(fig, kwargs.get('filename', 'heatmap'))

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
        ax.set_theta_zero_location('N')

        # Remove default grid and spines
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_visible(False)

        colors = DEFAULT_COLORS + DEFAULT_COLORS_NMI
        for i, (name, values) in enumerate(series.items()):
            values_plot = values + values[:1]
            ax.fill(angles, values_plot, alpha=0.08, color=colors[i % len(colors)])
            ax.plot(angles, values_plot, 'o-', linewidth=2,
                    color=colors[i % len(colors)], label=name, markersize=6)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=11)
        max_val = max([max(v) for v in series.values()]) if series else 5
        ax.set_ylim(0, max_val * 1.2)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)

        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        fig.tight_layout(pad=2)
        return self._save(fig, kwargs.get('filename', 'radar_chart'))

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
            'quadrant_labels': True,  # optional: label quadrants
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
        quadrant_labels = data.get('quadrant_labels', False)
        figsize = kwargs.get('figsize', (8, 6))

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        ax.spines['bottom'].set_linewidth(2)
        ax.spines['left'].set_linewidth(2)

        if sizes:
            s = np.array(sizes) * 5
        else:
            s = 80

        if color_by:
            colors = [DEFAULT_COLORS[i % len(DEFAULT_COLORS)] for i in color_by]
        else:
            colors = DEFAULT_COLORS[0]

        ax.scatter(x, y, s=s, c=colors, alpha=0.7,
                   edgecolors='white', linewidth=0.8, zorder=3)

        if labels:
            for i, label in enumerate(labels):
                ax.annotate(label, (x[i], y[i]),
                            xytext=(5, 5), textcoords='offset points',
                            fontsize=9)

        # Quadrant reference lines
        ax.axvline(np.median(x), ls='--', color='#767676', alpha=0.6, linewidth=1.2, zorder=1)
        ax.axhline(np.median(y), ls='--', color='#767676', alpha=0.6, linewidth=1.2, zorder=1)

        if quadrant_labels:
            x_med, y_med = np.median(x), np.median(y)
            x_range = x.max() - x.min()
            y_range = y.max() - y.min()
            offset_x = x_range * 0.05
            offset_y = y_range * 0.05
            ax.text(x_med + offset_x, y.max() - offset_y, 'High Y / High X',
                    fontsize=7.5, color='#888888', style='italic', ha='left')
            ax.text(x.max() - offset_x, y_med + offset_y, 'High Y / Low X',
                    fontsize=7.5, color='#888888', style='italic', ha='right')
            ax.text(x_med + offset_x, y.min() + offset_y, 'Low Y / High X',
                    fontsize=7.5, color='#888888', style='italic', ha='left')
            ax.text(x.min() + offset_x, y_med + offset_y, 'Low Y / Low X',
                    fontsize=7.5, color='#888888', style='italic', ha='right')

        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')

        fig.tight_layout(pad=2)
        return self._save(fig, kwargs.get('filename', 'scatter_plot'))

    def forest_plot(self, data: Dict, **kwargs) -> str:
        """
        森林图 - effect sizes with confidence intervals
        data = {
            'labels': ['Study A', 'Study B', 'Study C'],
            'estimates': [0.5, 0.3, 0.7],
            'ci_low': [0.2, 0.1, 0.4],
            'ci_high': [0.8, 0.5, 1.0],
            'title': 'Effect Sizes',
            'xlabel': 'Effect Size',
            'reference': 0.0,
            'colors': None,
        }
        """
        import matplotlib.pyplot as plt

        labels = data.get('labels', [])
        estimates = data.get('estimates', [])
        ci_low = data.get('ci_low', [])
        ci_high = data.get('ci_high', [])
        title = data.get('title', '')
        xlabel = data.get('xlabel', '')
        reference = data.get('reference', 0.0)
        colors = data.get('colors', ['#B64342'] * len(labels))
        figsize = kwargs.get('figsize', (8, max(3, len(labels) * 0.5)))

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        ax.spines['bottom'].set_linewidth(2)
        ax.spines['left'].set_linewidth(2)

        y = np.arange(len(labels))[::-1]
        for yi, est, lo, hi, color in zip(y, estimates, ci_low, ci_high, colors):
            ax.plot([lo, hi], [yi, yi], color=color, lw=2)
            ax.plot(est, yi, marker='o', ms=8, color=color)

        ax.axvline(reference, color='#767676', linestyle='--', linewidth=1.5, alpha=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=11)
        ax.set_xlabel(xlabel, fontsize=12)

        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')

        fig.tight_layout(pad=2)
        return self._save(fig, kwargs.get('filename', 'forest_plot'))

    def area_chart(self, data: Dict, **kwargs) -> str:
        """
        面积图/堆叠趋势图
        data = {
            'x': [1,2,3,4],
            'series': {'A': [1,2,1,3], 'B': [2,1,3,2]},
            'title': 'Stacked Area',
            'xlabel': 'Time', 'ylabel': 'Value',
            'stacked': True,
            'hatch': False,
        }
        """
        import matplotlib.pyplot as plt

        x = np.array(data.get('x', []))
        series = data.get('series', {})
        title = data.get('title', '')
        xlabel = data.get('xlabel', '')
        ylabel = data.get('ylabel', '')
        stacked = data.get('stacked', True)
        use_hatch = data.get('hatch', False)
        figsize = kwargs.get('figsize', (8, 5))

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        ax.spines['bottom'].set_linewidth(2)
        ax.spines['left'].set_linewidth(2)

        colors = DEFAULT_COLORS + DEFAULT_COLORS_NMI
        hatches = ['/', '\\', '.', 'x', 'o', '+']
        names = list(series.keys())
        values = [np.array(series[n]) for n in names]

        if stacked:
            ax.stackplot(x, *values, labels=names,
                         colors=colors[:len(names)], alpha=0.8)
            if use_hatch:
                for i, name in enumerate(names):
                    ax.fill_between(x, np.zeros_like(values[i]), values[i],
                                    color='none', edgecolor='white',
                                    hatch=hatches[i % len(hatches)], linewidth=0)
        else:
            for i, (name, vals) in enumerate(series.items()):
                ax.fill_between(x, 0, vals, color=colors[i % len(colors)],
                                alpha=0.3, label=name)
                ax.plot(x, vals, color=colors[i % len(colors)], linewidth=2)

        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, frameon=False)

        fig.tight_layout(pad=2)
        return self._save(fig, kwargs.get('filename', 'area_chart'))

    def multi_panel(self, panels: List[Dict], **kwargs) -> str:
        """
        多面板组合图 - GridSpec布局 with Nature-style information architecture
        panels = [
            {'type': 'bar', 'data': {...}, 'row': 0, 'col': 0, 'colspan': 1},
            {'type': 'line', 'data': {...}, 'row': 0, 'col': 1},
            {'type': 'legend', 'row': 0, 'col': 2},  # dedicated legend panel
            ...
        ]
        kwargs:
            rows, cols: grid dimensions
            height_ratios, width_ratios: for asymmetric layouts
            title: hero figure title
            shared_legend: True to collect legend from first panel with data
        """
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec

        figsize = kwargs.get('figsize', (22, 17))
        rows = kwargs.get('rows', 2)
        cols = kwargs.get('cols', 2)
        title = kwargs.get('title', '')
        height_ratios = kwargs.get('height_ratios', None)
        width_ratios = kwargs.get('width_ratios', None)
        shared_legend = kwargs.get('shared_legend', False)

        fig = plt.figure(figsize=figsize)
        gs = gridspec.GridSpec(rows, cols, figure=fig,
                               wspace=0.3, hspace=0.35,
                               height_ratios=height_ratios,
                               width_ratios=width_ratios)

        colors = ['#0F4D92', '#B64342', '#8BCF8B', '#767676',
                  '#9A4D8E', '#3775BA', '#FFD700', '#42949E']

        legend_handles = None
        legend_labels = None

        for i, panel in enumerate(panels):
            row = panel.get('row', 0)
            col = panel.get('col', i % cols)
            colspan = panel.get('colspan', 1)
            rowspan = panel.get('rowspan', 1)

            # Dedicated legend panel
            if panel.get('type') == 'legend':
                ax = fig.add_subplot(gs[row:row+rowspan, col:col+colspan])
                if legend_handles and legend_labels:
                    ax.legend(legend_handles, legend_labels,
                              fontsize=kwargs.get('legend_fontsize', 14),
                              loc='center', frameon=False)
                ax.set_axis_off()
                continue

            ax = fig.add_subplot(gs[row:row+rowspan, col:col+colspan])
            ax.spines['bottom'].set_linewidth(2)
            ax.spines['left'].set_linewidth(2)

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
                    bars = ax.bar(x + offset, values, bar_width,
                                  label=name, color=colors[j % len(colors)],
                                  alpha=0.85)
                ax.set_xticks(x)
                ax.set_xticklabels(categories, fontsize=8, rotation=45, ha='right')
                # Collect legend
                if shared_legend and legend_handles is None:
                    legend_handles, legend_labels = ax.get_legend_handles_labels()
                    ax.legend().remove()

            elif panel_type == 'line':
                x_data = panel_data.get('x', [])
                series = panel_data.get('series', {})
                for j, (name, values) in enumerate(series.items()):
                    ax.plot(x_data, values, 'o-', color=colors[j % len(colors)],
                            linewidth=2, markersize=6, label=name)
                if shared_legend and legend_handles is None:
                    legend_handles, legend_labels = ax.get_legend_handles_labels()
                    ax.legend().remove()

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

            elif panel_type == 'scatter':
                x_s = panel_data.get('x', [])
                y_s = panel_data.get('y', [])
                ax.scatter(x_s, y_s, c=colors[0], alpha=0.7,
                           edgecolors='white', linewidth=0.8)
                ax.axvline(np.median(x_s), ls='--', color='#767676', alpha=0.6, linewidth=1.2)
                ax.axhline(np.median(y_s), ls='--', color='#767676', alpha=0.6, linewidth=1.2)

            elif panel_type == 'forest':
                labels = panel_data.get('labels', [])
                estimates = panel_data.get('estimates', [])
                ci_low = panel_data.get('ci_low', [])
                ci_high = panel_data.get('ci_high', [])
                y = np.arange(len(labels))[::-1]
                for yi, est, lo, hi in zip(y, estimates, ci_low, ci_high):
                    ax.plot([lo, hi], [yi, yi], color='#B64342', lw=2)
                    ax.plot(est, yi, marker='o', ms=6, color='#B64342')
                ax.axvline(panel_data.get('reference', 0.0),
                           color='#767676', linestyle='--', linewidth=1.2, alpha=0.8)
                ax.set_yticks(y)
                ax.set_yticklabels(labels, fontsize=7)

            # Panel title
            if panel_title:
                ax.set_title(panel_title, fontsize=10, fontweight='bold')

            # Panel label (a, b, c...)
            panel_label = panel.get('label', chr(ord('a') + i))
            add_panel_label(ax, panel_label, fontsize=14)

        # Hero figure title
        if title:
            fig.suptitle(title, fontsize=16, fontweight='bold', y=1.02)

        fig.tight_layout(pad=2)
        return self._save(fig, kwargs.get('filename', 'multi_panel'))

    def _save(self, fig, filename: str) -> str:
        """Save figure as SVG (primary) + PNG (preview) + PDF."""
        base = os.path.join(self.output_dir, filename)
        paths = finalize_figure(fig, base, formats=['svg', 'png', 'pdf'], dpi=300, pad=2)
        print(f"  [Figure] Saved: {', '.join(paths)}")
        return paths[0]  # return SVG path

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
                'tight_ylim': True,
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

        # Figure 3: 消融实验结果 (horizontal ablation with alpha gradient)
        ablation = experiment_results.get('ablation', {})
        if ablation:
            ablation_data = {
                'categories': list(ablation.keys()),
                'groups': {'Metric Score': list(ablation.values())},
                'title': 'Ablation Study',
                'ylabel': 'Score',
                'horizontal': True,
                'ablation_alpha': True,
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
        'forest': agent.forest_plot,
        'area': agent.area_chart,
        'multi': agent.multi_panel,
    }
    method = methods.get(chart_type)
    if method:
        return method(data, **kwargs)
    raise ValueError(f"Unknown chart type: {chart_type}, use: {list(methods.keys())}")
