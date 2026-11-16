"""Refresh chart data from Supplemental Information 2 (included reports); never edits the source."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from datetime import date
from pathlib import Path
from review_data import DEFAULT_CSV, write_csv, load_records, select_group

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SI2 = (SCRIPT_DIR.parent
               /'Supplemental_Files'/'Supplemental_Data_S2_Included_Reports.csv')
GROUP_MAP = {'Self-supervised learning': 'ssl', 'Conventional autoencoder': 'traditional_ae'}
PARTITION_FIELD = 'Downstream participant partition'
UNCLEAR_PARTITION = 'Participant separation unclear'
RISK_DOMAINS = {
    'downstream_participant_separation': 'Risk of bias: downstream participant separation',
    'pretraining_exposure_of_test_participants': 'Risk of bias: pretraining exposure of test participants',
    'supervised_comparator': 'Risk of bias: supervised comparator',
}


COMPARATOR_FIELD = 'Same-backbone random-initialization or SSL-removal comparator'


def comparison_conditions(ssl):
    """Narrow same-backbone comparisons by label budget, test set and participant separation."""
    controlled = [row for row in ssl if row[COMPARATOR_FIELD] == 'Yes']
    same_test = [row for row in controlled if row['Same downstream test set'] == 'Yes']
    return {
        'same_backbone_comparators': len(controlled),
        'matched_label_budget': sum(row['Matched downstream label budget'] == 'Yes' for row in controlled),
        'same_test_set_confirmed': len(same_test),
        'same_test_set_and_participant_disjoint': sum(
            row[PARTITION_FIELD] == 'Participant-disjoint only' for row in same_test),
    }


def summarize_evaluation(records):
    """Count the report-level codes used in Table 5 and the sensitivity analysis."""
    ssl = [row for row in records if row['Analysis group'] == 'Self-supervised learning']
    retained = [row for row in ssl if row['Excluded in event-only sensitivity analysis'] == 'No']
    annual_counts = {}
    for row in sorted(ssl, key=lambda row: row['Year']):
        year = row['Year']
        counts = annual_counts.setdefault(year, {'reports': 0, 'participant_separation_unclear': 0})
        counts['reports'] += 1
        counts['participant_separation_unclear'] += row[PARTITION_FIELD] == UNCLEAR_PARTITION
    return {
        'reports': len(ssl),
        'downstream_participant_partition': dict(Counter(row[PARTITION_FIELD] for row in ssl)),
        'risk_of_bias': {
            domain: dict(Counter(row[field] for row in ssl))
            for domain, field in RISK_DOMAINS.items()
        },
        'same_backbone_comparators': sum(
            row['Same-backbone random-initialization or SSL-removal comparator'] == 'Yes'
            for row in ssl
        ),
        'comparison_conditions': comparison_conditions(ssl),
        'by_epilepsy_coverage': {
            label: {
                'reports': len(group),
                'participant_separation_unclear': sum(row[PARTITION_FIELD] == UNCLEAR_PARTITION for row in group),
                'same_backbone_comparators': sum(row[COMPARATOR_FIELD] == 'Yes' for row in group),
            }
            for label, group in [
                ('with_epilepsy_related_data', [row for row in ssl if 'Epilepsy' in row['Disorder coverage']]),
                ('without_epilepsy_related_data', [row for row in ssl if 'Epilepsy' not in row['Disorder coverage']]),
            ]
        },
        'reporting_items': {
            'limited_label_evaluation': sum(row['Limited-label evaluation'] == 'Yes' for row in ssl),
            'encoder_update_extent_unclear': sum('encoder update extent unclear' in row['Downstream adaptation modes'] for row in ssl),
            'implementation_entry_identified': sum(row['Reported implementation entry'] == 'Yes' for row in ssl),
        },
        'annual_counts': annual_counts,
        'event_only_sensitivity': {
            'retained_reports': len(retained),
            'excluded_reports': len(ssl) - len(retained),
            'downstream_participant_partition': dict(Counter(row[PARTITION_FIELD] for row in retained)),
        },
    }


def prepare(si2_path=DEFAULT_SI2, output_dir=SCRIPT_DIR):
    si2_path, output_dir = Path(si2_path), Path(output_dir)
    with si2_path.open(encoding='utf-8-sig', newline='') as f:
        source = [r for r in csv.DictReader(f) if any((v or '').strip() for v in r.values())]
    source = [{k: (v or '').strip() for k, v in record.items()} for record in source]
    rows = []
    for r in source:
        if r['Analysis group'] not in GROUP_MAP:
            raise ValueError(f"Unknown analysis group in SI2: {r['Record ID']} {r['Analysis group']!r}")
        rows.append({
            'Record ID': r['Record ID'], 'Analysis group': GROUP_MAP[r['Analysis group']],
            'Title': r['Report title'], 'First author': r['First author'],
            'DOI or proceedings URL': r['DOI or proceedings URL'], 'Year': r['Year'],
            'Identification source': r['Identification source'],
            'Method_1': r['Learning method'], 'Backbone': r['Encoder architecture'],
            'Disorders': r['Disorder coverage'],
        })
    output = output_dir/DEFAULT_CSV.name
    write_csv(output, rows)
    load_records(output)  # validates IDs, years, methods, backbones and disease families
    groups = Counter(r['Analysis group'] for r in rows)
    for group, filename in [('ssl', 'data_si2_ssl.csv'), ('traditional_ae', 'data_si2_traditional_ae.csv')]:
        write_csv(output_dir/filename, select_group(rows, group))
    manifest = {'as_of': date.today().isoformat(), 'n': len(rows), 'groups': dict(groups),
                'disease_rule': 'SI2 "Disorder coverage" column; deduplicated per report',
                'sources': [{'path': str(si2_path.resolve()),
                             'sha256': hashlib.sha256(si2_path.read_bytes()).hexdigest()}]}
    (output_dir/'latest_data_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = json.dumps(summarize_evaluation(source), ensure_ascii=False, indent=2)
    (output_dir/'evaluation_summary.json').write_text(summary + '\n', encoding='utf-8')
    print(f"Prepared {len(rows)} reports from SI2: {groups['ssl']} SSL / {groups['traditional_ae']} conventional AE -> {output}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--si2', type=Path, default=DEFAULT_SI2, help='Path to Supplemental_Data_S2_Included_Reports.csv')
    parser.add_argument('--output-dir', type=Path, default=SCRIPT_DIR)
    args = parser.parse_args()
    prepare(args.si2, args.output_dir)
