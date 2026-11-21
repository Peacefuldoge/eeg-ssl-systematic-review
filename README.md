# EEG self-supervised learning systematic review

Data and analysis scripts for *Self-Supervised Learning for EEG in Neurological and Psychiatric Disorders: A Systematic Literature Review*. The review covers publications from 2020 through 2025. The included-report dataset contains 101 reports: 60 in the main self-supervised learning (SSL) analysis and 41 in the conventional autoencoder analysis.

## Supplementary files

| File | Contents and use |
| --- | --- |
| [Data S1 (PDF)](Supplemental_Files/Supplemental_Data_S1_Search_Strategies.pdf) | Readable search appendix. Records the Web of Science, IEEE Xplore, and PubMed search strings, field codes, filters, dates, and database totals. Also documents the three IEEE Xplore queries and the deduplication of their results. |
| [Data S1 (LaTeX)](Supplemental_Files/Supplemental_Data_S1_Search_Strategies.tex) | Editable source of the S1 PDF. Compile it with `latexmk -pdf Supplemental_Files/Supplemental_Data_S1_Search_Strategies.tex` using a TeX distribution. |
| [Data S2 (CSV)](Supplemental_Files/Supplemental_Data_S2_Included_Reports.csv) | One row per included report. Contains bibliographic identifiers, identification source, analysis group, SSL method, backbone, disorder and dataset coverage, evaluation design, label budget, comparator, adaptation, implementation evidence, and risk-of-bias codes. This is the input to the Python analysis. |
| [Data S3 (CSV)](Supplemental_Files/Supplemental_Data_S3_Full_Text_Exclusions.csv) | One row per full-text exclusion, with the report ID, title, exclusion category, and primary reason. Use it to trace the full-text exclusion totals in Figure 4. |
| [Data S4 (XLSX)](Supplemental_Files/Supplemental_Data_S4_Pretraining_Downstream_Exposure.xlsx) | Documents pretraining exposure for test participants and exact downstream test recordings. `Reports` contains report-level coding and source evidence, `Summary` aggregates the codes, and `Definitions` explains the categories. Join to S2 using `Record ID`. |
| [Data S5 (PDF)](Supplemental_Files/Supplemental_Data_S5_PRISMA_2020_checklist.pdf) | Completed PRISMA 2020 checklist with locations in the manuscript and supplements. |

## Reproduce the charts

Run these commands from the repository root with Python 3.10 or newer. Use the input and output paths below to keep generated files under `outputs/`.

Install Times New Roman before running the plotting commands. All plots use a white background. SVG exports store the letter shapes as paths to preserve the typography on other systems.

```sh
python -m pip install -r requirements.txt
python scripts/prepare_latest_data.py --output-dir outputs/data
python scripts/generate_ssl_summary_charts.py --csv outputs/data/data_si2_latest.csv --output-dir outputs/charts
python scripts/plot_ae_publication_trend.py --csv outputs/data/data_si2_latest.csv --output-dir outputs/charts
python scripts/plot_ssl_method_disorder_heatmap.py --output-dir outputs/heatmap
```

The preparation step reads S2 and builds the plotting CSV used by the two chart commands. The heatmap reads S2 directly. The scripts leave the input data intact.

### Manuscript figure map

| Figure | Content | Script | Generated file |
| --- | --- | --- | --- |
| **5** | Annual counts of SSL reports | `generate_ssl_summary_charts.py` | `outputs/charts/ssl/publication_trend_by_year.png` |
| **6** | SSL methods by year | `generate_ssl_summary_charts.py` | `outputs/charts/ssl/model_method_distribution_by_year.png` |
| **11** | SSL reports by backbone architecture | `generate_ssl_summary_charts.py` | `outputs/charts/ssl/backbone_distribution.png` |
| **12** | SSL backbone architectures by year | `generate_ssl_summary_charts.py` | `outputs/charts/ssl/backbone_distribution_by_year.png` |
| **13** | SSL methods by disorder group | `plot_ssl_method_disorder_heatmap.py` | `outputs/heatmap/SSL_method_disorder_counts.png` |
| **14** | Annual counts of conventional autoencoder reports | `plot_ae_publication_trend.py` | `outputs/charts/traditional_ae/publication_trend_by_year.png` |

Figures 1–3 are conceptual diagrams about disorder overlap, learning workflows, and the SSL taxonomy. Figure 4 is the PRISMA study-selection diagram. Figures 7–10 illustrate masked prediction, masked waveform reconstruction, contrastive learning, and the joint objectives in PPi. These figures are maintained with the manuscript artwork and have no Python generator in this repository.

### Additional outputs

- The standard chart and annual trend scripts export PNG and SVG files. The default SSL command also produces `disease_type_distribution_bar` and `model_method_distribution` for checking the disease and method totals. Each chart group includes `plotted_reports.csv` and `counts.json`.
- Figure 13 uses **report counts**. The heatmap script also exports a within-disorder percentage view, `SSL_method_disorder_within_disorder_percent`, and writes `heatmap_counts.csv` and `heatmap_provenance.json`. Both heatmap views are exported as PDF, SVG, and PNG.
- Disease coverage counts documented use in pretraining or downstream evaluation once per report per disorder family. A report may contribute to more than one family. The percentage heatmap uses the number of reports covering each disorder as its denominator.

### Reproduce the evaluation summaries

`prepare_latest_data.py` writes the following files in `outputs/data/`.

| Output | Contents |
| --- | --- |
| `data_si2_latest.csv` | Plotting dataset for all included reports. |
| `data_si2_ssl.csv` and `data_si2_traditional_ae.csv` | Plotting subsets for the two analysis groups. |
| `latest_data_manifest.json` | Report counts and source provenance, including the SHA-256 of the input S2 CSV. |
| `evaluation_summary.json` | Counts for the downstream partition and risk-of-bias ratings in Table 5, the same-backbone comparison conditions in Section 4.2, and selected documentation counts in Table 12. Also includes annual counts of unclear participant separation, summaries stratified by epilepsy coverage, and the sensitivity analysis excluding reports eligible only through TUEV or TUSL event classification. |

Use S4 for the participant-level and recording-level exposure evidence summarized in Table 12. In the partition summaries, a report with both a non-disjoint setting and an unclear setting has its own category.

## Source files

| File | Role |
| --- | --- |
| [`prepare_latest_data.py`](scripts/prepare_latest_data.py) | Converts S2 into plotting datasets, validates the coded records, and writes the evaluation summary and input manifest. |
| [`generate_ssl_summary_charts.py`](scripts/generate_ssl_summary_charts.py) | Entry point for standard descriptive charts. Defaults to the SSL group and generates the outputs for Figures 5, 6, 11, and 12, along with auxiliary charts. |
| [`plot_ae_publication_trend.py`](scripts/plot_ae_publication_trend.py) | Generates the bar-only annual publication counts for the conventional autoencoder group in Figure 14. |
| [`plot_ssl_method_disorder_heatmap.py`](scripts/plot_ssl_method_disorder_heatmap.py) | Aggregates SSL report counts by method and disorder directly from S2. Produces Figure 13, the percentage view, and the report IDs used in the counts. |
| [`review_charts.py`](scripts/review_charts.py) | Shared chart command-line interface and export logic for Figures 5, 6, 11, 12, and 14. Selects the analysis group, dispatches each chart, and writes the group-level counts and report list. |
| [`review_data.py`](scripts/review_data.py) | Shared CSV parsing, validation, group selection, disease coding, and aggregation for data preparation and the standard charts. |
| [`reference_style.py`](scripts/reference_style.py) | Sets the font and background for all charts. Provides layout, colors, and export for Figures 5, 6, 11, 12, and 14. The heatmap script defines the Figure 13 layout and colors. |
| [`requirements.txt`](requirements.txt) | Python dependencies for the analysis and figure scripts. |
| [`LICENSE`](LICENSE) | MIT license for the repository's analysis and plotting code. |
| [`.gitignore`](.gitignore) | Excludes Python caches, virtual environments, and generated outputs. |
| [`README.md`](README.md) | Repository guide, manuscript figure map, and reproduction commands. |

## License

The repository code is available under the [MIT License](LICENSE). Supplementary materials and third-party content are outside its scope.

### Screening rescreening

The first two authors jointly screened each title-and-abstract record and assessed each retrieved full-text report. The third author independently rescreened random samples. The screening comparison covered 92 of 919 title-and-abstract records (10.01%). The full-text sample was drawn from the 322 reports available at the time and comprised 31 database reports and two reports identified by supplementary methods (33 of 337 reports in the final full-text set, 9.79%). Agreement was 74/92 at title-and-abstract screening (80.4%; Cohen's kappa = 0.60) and 26/33 at full text (78.8%; Cohen's kappa = 0.54). After re-inspection, the title-and-abstract decisions agreed for 80/92 records (87.0%; Cohen's kappa = 0.73). Full-text agreement after re-inspection was 27/33 (81.8%; Cohen's kappa = 0.60).
