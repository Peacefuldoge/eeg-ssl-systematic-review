"""Chart entry points for the review figures generated from Data S2."""
import argparse
import json
from pathlib import Path
from reference_style import draw_annual, draw_backbone, draw_disease, draw_pie, draw_year
from review_data import (DEFAULT_CSV, GROUPS, VIEW_LABELS, disease_counts,
                         field_counts, load_records, select_group, write_csv, year_counts)

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = SCRIPT_DIR/'figures_latest'
FILES = {
    'disease': 'disease_type_distribution_bar',
    'method': 'model_method_distribution',
    'backbone': 'backbone_distribution',
    'method_by_year': 'model_method_distribution_by_year',
    'backbone_by_year': 'backbone_distribution_by_year',
    'year': 'publication_trend_by_year',
}

def generate_group(rows, group, output_dir, charts=None, show=False, year_line=None):
    rows = select_group(rows, group)
    output_dir = Path(output_dir)/group
    charts = list(FILES) if charts is None else charts
    paths = []
    for kind in charts:
        stem = output_dir/FILES[kind]
        if kind == 'method':
            path = draw_pie(rows, group, stem, show)
        elif kind == 'disease':
            path = draw_disease(rows, stem, show)
        elif kind == 'backbone':
            path = draw_backbone(rows, stem, show)
        elif kind in ['method_by_year', 'backbone_by_year']:
            path = draw_annual(rows, group, 'Method_1' if kind == 'method_by_year' else 'Backbone', stem, show)
        else:
            path = draw_year(rows, stem, show, line=group in ['ssl', 'combined'] if year_line is None else year_line)
        paths.append(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir/'plotted_reports.csv', rows)
    summary = {'group': group, 'n': len(rows), 'disease_denominator': len(rows),
               'diseases': disease_counts(rows), 'methods': dict(field_counts(rows, 'Method_1')),
               'backbones': dict(field_counts(rows, 'Backbone')), 'publication_years': year_counts(rows),
               'figures': [Path(p).name for p in paths]}
    if group == 'combined':
        summary['source_groups'] = dict(field_counts(rows, 'Analysis group'))
        summary['method_note'] = 'Conventional autoencoder reports are kept distinct from strict SSL objectives, following SI2.'
    (output_dir/'counts.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{group}: {len(rows)} reports, {len(paths)} PNG + {len(paths)} SVG figures -> {output_dir.resolve()}')
    return paths

def cli(default_group='both', charts=None, year_line=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=DEFAULT_CSV)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument('--group', choices=['ssl', 'traditional_ae', 'both', 'combined', 'all'], default=default_group)
    parser.add_argument('--show', action='store_true')
    args = parser.parse_args()
    rows = load_records(args.csv)
    groups = list(VIEW_LABELS) if args.group == 'all' else list(GROUPS) if args.group == 'both' else [args.group]
    for group in groups:
        generate_group(rows, group, args.output_dir, charts, args.show, year_line)
