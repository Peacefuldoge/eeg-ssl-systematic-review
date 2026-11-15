"""Validated report-level counts shared by every review chart entrypoint."""
from collections import Counter
import csv
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = SCRIPT_DIR / 'data_si2_latest.csv'
YEARS = list(range(2020, 2026))
GROUPS = {'ssl': 'Self-supervised learning', 'traditional_ae': 'Conventional autoencoder'}
VIEW_LABELS = {**GROUPS, 'combined': 'Self-supervised learning and conventional autoencoder'}
DISEASES = [
    'Epilepsy and seizures', 'Mood disorders', 'Neurodegenerative disorders',
    'Neurodevelopmental disorders', 'Schizophrenia spectrum disorders', 'Cerebrovascular disorders',
    'Other neurological disorders',
    'Anxiety disorders', 'Obsessive-compulsive and related disorders',
    'Trauma- and stress-related disorders', 'Addictive disorders',
]
METHODS = ['Generative SSL', 'Discriminative SSL', 'Predictive SSL', 'Hybrid SSL', 'Conventional autoencoder']
BACKBONES = ['Transformer-based', 'CNN-based', 'GNN-based', 'AE-based', 'RNN-based',
             'Mamba-based', 'SNN-based', 'Not specified']


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def canonical_disease(name):
    """Map a SI2 disorder label to its approved family.

    SI2 qualifies one family in parentheses -- 'Other neurological disorders
    (disorders of consciousness or acquired brain injury)'. The qualifier is
    dropped and, because it may itself contain a semicolon, splitting has to
    ignore separators inside parentheses.
    """
    name = name.strip()
    head = name.split('(', 1)[0].strip()
    return head or name


def split_diseases(row):
    parts, buf, depth = [], [], 0
    for ch in (row.get('Disorders', '') or ''):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth = max(depth - 1, 0)
        if ch == ';' and depth == 0:
            parts.append(''.join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append(''.join(buf))
    return {canonical_disease(p) for p in parts if p.strip()}


def load_records(path=DEFAULT_CSV):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        required = {'Record ID', 'Analysis group', 'Year', 'Method_1', 'Backbone', 'Disorders'}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
        rows = [{k: (v or '').strip() for k, v in r.items()} for r in reader if any(r.values())]
    if not rows:
        raise ValueError('No report records found')
    seen = set()
    for row in rows:
        rid = row['Record ID']
        if not rid or rid in seen:
            raise ValueError('Duplicate or blank Record ID: ' + rid)
        seen.add(rid)
        if row['Analysis group'] not in GROUPS:
            raise ValueError('Invalid analysis group: ' + rid)
        try:
            year = int(row['Year'])
        except ValueError:
            raise ValueError('Invalid publication year: ' + rid) from None
        if year not in YEARS:
            raise ValueError('Year outside 2020-2025: ' + rid)
        if row['Method_1'] not in METHODS or row['Backbone'] not in BACKBONES:
            raise ValueError('Missing or unapproved method/backbone: ' + rid)
        diseases = split_diseases(row)
        if not diseases or diseases - set(DISEASES):
            raise ValueError('Missing or unapproved disease family: ' + rid)
    return rows


def select_group(rows, group):
    if group == 'combined':
        if {r['Analysis group'] for r in rows} != set(GROUPS):
            raise ValueError('Combined view requires both SSL and traditional AE source groups')
        return list(rows)
    if group not in GROUPS:
        raise ValueError('Choose ssl, traditional_ae, or combined')
    selected = [r for r in rows if r['Analysis group'] == group]
    if not selected:
        raise ValueError('No reports in group: ' + group)
    return selected


def field_counts(rows, field):
    return Counter(r[field] for r in rows)


def disease_counts(rows):
    counts = Counter()
    for row in rows:
        counts.update(split_diseases(row))
    return {name: counts[name] for name in DISEASES}


def country_counts(rows, group_singletons=True):
    counts = field_counts(rows, 'Nation')
    if not group_singletons:
        return dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))
    displayed = {k: v for k, v in counts.items() if v > 1}
    singles = sum(v for v in counts.values() if v == 1)
    if singles:
        displayed['Other'] = singles
    return dict(sorted(displayed.items(), key=lambda x: (x[0] == 'Other', -x[1], x[0])))


def year_counts(rows):
    counts = Counter(int(r['Year']) for r in rows)
    return {year: counts[year] for year in YEARS}
