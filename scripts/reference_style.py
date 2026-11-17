"""Shared rendering parameters for the review charts."""
import os
from pathlib import Path
import sys
import tempfile
import textwrap

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'review_eeg_ssl_mpl'))
import matplotlib
if '--show' not in sys.argv:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import findfont
from matplotlib.ticker import MaxNLocator
from matplotlib.transforms import Bbox

from review_data import BACKBONES, DISEASES, YEARS, disease_counts, field_counts, year_counts

PALETTE = ['#6AD1A3', '#7FBDDA', '#BBC7BE', '#FFD47D', '#FFA288',
           '#C49892', '#929EAB', '#84ADDC', '#B7ABD1', '#D3C3A3', '#9BC8BD', '#DAB4C8']
# Display order shared with Figure 13 (heatmap); colours stay tied to each method, not to its position.
METHOD_ORDER = ['Predictive SSL', 'Generative SSL', 'Discriminative SSL', 'Hybrid SSL', 'Conventional autoencoder']
METHOD_COLORS = {'Generative SSL': PALETTE[0], 'Discriminative SSL': PALETTE[1], 'Hybrid SSL': PALETTE[2],
                 'Predictive SSL': PALETTE[3], 'Conventional autoencoder': PALETTE[4]}
# Colours stay tied to each disease family, not to its position in DISEASES, so
# inserting a family never repaints the others.
DISEASE_COLORS = {
    'Epilepsy and seizures': '#6AD1A3',
    'Mood disorders': '#7FBDDA',
    'Neurodegenerative disorders': '#FFD47D',
    'Neurodevelopmental disorders': '#FFA288',
    'Schizophrenia spectrum disorders': '#C49892',
    'Cerebrovascular disorders': '#BBC7BE',
    'Other neurological disorders': '#DAB4C8',
    'Anxiety disorders': '#929EAB',
    'Obsessive-compulsive and related disorders': '#84ADDC',
    'Trauma- and stress-related disorders': '#B7ABD1',
    'Addictive disorders': '#D3C3A3',
}
BACKBONE_COLORS = dict(zip(BACKBONES, PALETTE))


def configure_export_style():
    font = 'Times New Roman'
    findfont(font, fallback_to_default=False)
    plt.rcParams.update({'font.family': font, 'figure.facecolor': 'white',
                         'axes.facecolor': 'white', 'savefig.facecolor': 'white',
                         'savefig.transparent': False, 'svg.fonttype': 'path',
                         'pdf.fonttype': 42})


def base_style(backbone=False):
    configure_export_style()
    plt.rcParams.update({'font.size': 16 if backbone else 10,
                         'axes.labelsize': 17 if backbone else 10,
                         'xtick.labelsize': 16 if backbone else 10,
                         'ytick.labelsize': 16 if backbone else 10,
                         'legend.fontsize': 10})


def export(fig, stem, show=False, kind='ordinary'):
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    dpi = 600 if kind == 'backbone' else 300
    pixels = {'ordinary': (2400, 1800), 'disease': (2670, 1926), 'backbone': (8231, 4635)}[kind]
    bbox = None
    if kind != 'ordinary':
        fig.canvas.draw()
        tight = fig.get_tightbbox(fig.canvas.get_renderer()).padded(0.1)
        bbox = Bbox.from_bounds(tight.x0, tight.y0, pixels[0]/dpi+1e-8, pixels[1]/dpi+1e-8)
    for suffix in ['.png', '.svg']:
        fig.savefig(stem.with_suffix(suffix), dpi=dpi, bbox_inches=bbox, pad_inches=0)
    if show:
        plt.show()
    plt.close(fig)
    return str(stem.with_suffix('.png').resolve())


def draw_pie(rows, group, stem, show=False):
    base_style()
    raw = field_counts(rows, 'Method_1')
    counts = {name: raw[name] for name in METHOD_ORDER if raw[name]}
    plot_colors = [METHOD_COLORS[name] for name in counts]
    if group == 'traditional_ae':
        plot_colors = [PALETTE[0]]
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_axes([0.04, 0.10, 0.58, 0.80])
    wedges, _ = ax.pie(list(counts.values()), labels=None, colors=plot_colors, startangle=140,
                       counterclock=True, wedgeprops={'linewidth': 0})
    legend_labels = [f'{name}:\n{value} ({value/len(rows)*100:.1f}%)' if name == 'Conventional autoencoder'
                     else f'{name}: {value} ({value/len(rows)*100:.1f}%)' for name, value in counts.items()]
    ax.legend(wedges, legend_labels,
              title='Category', loc='center left',
              bbox_to_anchor=(1.00, 0.5), frameon=False, labelcolor='black',
              title_fontsize=12, fontsize=10)
    ax.axis('equal')
    return export(fig, stem, show)


def draw_disease(rows, stem, show=False):
    base_style()
    raw = disease_counts(rows)
    # Families with no report in this view are omitted, matching the backbone chart.
    counts = [(name, raw.get(name, 0)) for name in DISEASES if raw.get(name, 0) > 0]
    counts.sort(key=lambda item: (-item[1], DISEASES.index(item[0])))
    counts = counts[::-1]
    labels = [textwrap.fill(name, 38, break_long_words=False, break_on_hyphens=False) for name, _ in counts]
    fig, ax = plt.subplots(figsize=(9, 6.5))
    bars = ax.barh(labels, [value for _, value in counts],
                   color=[DISEASE_COLORS[name] for name, _ in counts], height=0.68)
    for bar, (_, value) in zip(bars, counts):
        ax.text(bar.get_width()+0.2, bar.get_y()+bar.get_height()/2,
                f'{value} ({value/len(rows)*100:.1f}%)', va='center', ha='left', fontsize=12, color='#333333')
    ax.set_xlabel('Number of reports', fontsize=12, color='#333333')
    ax.set_ylabel('')
    ax.tick_params(axis='both', labelsize=12, colors='#333333')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for name in ['left', 'bottom']:
        ax.spines[name].set_color('#B8B8B8')
        ax.spines[name].set_linewidth(0.8)
    ax.grid(axis='x', linestyle='-', linewidth=0.5, color='#D9D9D9', alpha=0.6)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(value for _, value in counts)*1.30)
    fig.tight_layout()
    return export(fig, stem, show, kind='disease')


def draw_backbone(rows, stem, show=False):
    base_style(backbone=True)
    raw = field_counts(rows, 'Backbone')
    counts = [(name, raw.get(name, 0)) for name in BACKBONES if raw.get(name, 0) > 0]
    counts.sort(key=lambda item: (-item[1], BACKBONES.index(item[0])))
    labels = [('Transformer-' + chr(10) + 'based') if name == 'Transformer-based' else name for name, _ in counts]
    fig, ax = plt.subplots(figsize=(14, 8))
    bars = ax.bar(labels, [value for _, value in counts], width=0.6,
                  color=[BACKBONE_COLORS[name] for name, _ in counts], edgecolor='none', zorder=3)
    maximum = max(value for _, value in counts)
    for bar, (_, value) in zip(bars, counts):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(maximum*.018, .18),
                f'{value} ({value/len(rows)*100:.1f}%)', ha='center', va='bottom', fontsize=15, color='#333333')
    ax.set_xlabel('Backbone architecture', fontsize=18, labelpad=8)
    ax.set_ylabel('Number of reports', fontsize=18, labelpad=8)
    ax.set_ylim(0, maximum*1.18)
    ax.grid(axis='y', color='#E6E6E6', linewidth=0.8, zorder=0)
    ax.grid(axis='x', visible=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#B0B0B0')
    ax.spines['bottom'].set_color('#B0B0B0')
    ax.tick_params(axis='x', rotation=0)
    plt.setp(ax.get_xticklabels(), ha='center')
    fig.tight_layout()
    return export(fig, stem, show, kind='backbone')


def draw_annual(rows, group, field, stem, show=False):
    base_style()
    order = METHOD_ORDER if field == 'Method_1' else BACKBONES
    colors = METHOD_COLORS if field == 'Method_1' else BACKBONE_COLORS
    order = [name for name in order if any(r[field] == name for r in rows)]
    fig, ax = plt.subplots(figsize=(8, 6))
    bottoms = [0]*len(YEARS)
    for name in order:
        values = [sum(int(r['Year']) == year and r[field] == name for r in rows) for year in YEARS]
        color = PALETTE[0] if group == 'traditional_ae' and field == 'Method_1' else colors[name]
        ax.bar(YEARS, values, bottom=bottoms, width=.68, color=color, edgecolor='none', label=name, zorder=2)
        bottoms = [a+b for a, b in zip(bottoms, values)]
    ax.set_xlabel('Year', fontsize=11, fontweight='normal', labelpad=8)
    ax.set_ylabel('Number of reports', fontsize=11, fontweight='normal', labelpad=8)
    ax.set_xticks(YEARS)
    ax.set_ylim(0, max(bottoms)*1.08)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=7))
    ax.tick_params(axis='both', labelsize=9, colors='black')
    ax.set_axisbelow(True)
    ax.grid(axis='y', linestyle='--', linewidth=.7, color='#BBC7BE', alpha=.65)
    for spine in ax.spines.values():
        spine.set_color('#929EAB')
        spine.set_linewidth(.8)
    is_method = field == 'Method_1'
    title = ('SSL Method' if group == 'ssl' else 'Category') if is_method else 'Backbone'
    columns = 3 if not is_method or len(order)>4 else 2
    ax.legend(title=title, loc='upper center', bbox_to_anchor=(.5, 1.18 if is_method else 1.23),
              ncol=columns, frameon=False, fontsize=9, title_fontsize=11,
              handlelength=2.0, handleheight=1.0, handletextpad=.8, columnspacing=1.5, labelspacing=.5)
    fig.subplots_adjust(left=.13, right=.96, top=.80 if is_method else .78, bottom=.13)
    return export(fig, stem, show)


def draw_year(rows, stem, show=False, line=True):
    base_style()
    counts = year_counts(rows)
    years, values = list(counts), list(counts.values())
    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(years, values, width=.60, color='#BFBFBF', edgecolor='none', label='Number of reports', zorder=2)
    if line:
        trend, = ax.plot(years, values, color='#4D4D4D', linewidth=1.8, marker='o', markersize=4.5,
                         markerfacecolor='#8C8C8C', markeredgecolor='#4D4D4D', markeredgewidth=.8,
                         label='Trend', zorder=3)
        ax.legend(handles=[trend, bars], labels=['Trend', 'Number of reports'],
                  loc='upper left', frameon=False, fontsize=9)
    ax.set_xlabel('Year', fontsize=11, fontweight='normal', labelpad=8)
    ax.set_ylabel('Number of reports', fontsize=11, fontweight='normal', labelpad=8)
    ax.set_xticks(years)
    ax.tick_params(axis='both', labelsize=9, colors='black')
    ax.set_ylim(0, max(values)*1.08)
    ax.set_axisbelow(True)
    ax.grid(axis='y', color='#D9DEE3', linestyle='--', linewidth=.7, alpha=.65)
    ax.grid(axis='x', visible=False)
    for spine in ax.spines.values():
        spine.set_color('#929EAB')
        spine.set_linewidth(.8)
    fig.subplots_adjust(left=.13, right=.96, bottom=.13, top=.96)
    return export(fig, stem, show)
