# EEG self-supervised learning systematic review

This repository contains the report-level data and scripts used to summarize EEG self-supervised learning for neurological and psychiatric disorders. Data S2 lists all 102 included reports (61 self-supervised learning and 41 conventional autoencoder reports).

## Data

- S1 gives the database search strategies (PDF and LaTeX).
- S2 lists included reports and their coding.
- S3 lists full-text exclusions and their primary reasons.
- S4 documents exposure of downstream test participants and recordings during pretraining.
- S5 is the PRISMA 2020 checklist.

## Reproduce the descriptive charts

From the repository root, use Python 3.10 or newer:

```sh
python -m pip install -r requirements.txt
python scripts/prepare_latest_data.py --output-dir outputs/data
python scripts/generate_all_pie_charts.py --csv outputs/data/data_si2_latest.csv --output-dir outputs/charts
python scripts/year_publication_trend_no_line.py --csv outputs/data/data_si2_latest.csv --output-dir outputs/charts
python scripts/plot_ssl_disease_heatmap.py --output-dir outputs/heatmap
```

The chart scripts generate figure files and count summaries. The input CSV is kept intact. Disease coverage counts a report once per family with documented use in pretraining or downstream evaluation. A report can contribute to multiple families.

`prepare_latest_data.py` also writes `outputs/data/evaluation_summary.json` from Data S2. It reproduces the report-level downstream partition and risk-of-bias counts in Table 5, the annual counts of reports coded as unclear, the narrowing of same-backbone comparisons by label budget, test set and participant separation (Section 4.2), the documentation counts in Table 12, the split by epilepsy-related data, and the sensitivity analysis that excludes reports whose only eligible downstream task is classification on TUEV or TUSL. The mixed code for a report with a non-disjoint setting and an unclear setting is counted separately from the overall unclear category.
