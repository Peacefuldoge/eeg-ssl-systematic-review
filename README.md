# Self-Supervised Learning for Electroencephalography in Neurological and Psychiatric Disorders: A Systematic Literature Review

Data and analysis scripts for *Self-Supervised Learning for Electroencephalography in Neurological and Psychiatric Disorders: A Systematic Literature Review*. The review covers 2020–2025 and includes 101 reports: 60 on self-supervised learning (SSL) and 41 on conventional autoencoders.

## Supplementary data

| File | Contents |
| --- | --- |
| [S1 (PDF)](Supplemental_Files/Supplemental_Data_S1_Search_Strategies.pdf) · [LaTeX source](Supplemental_Files/Supplemental_Data_S1_Search_Strategies.tex) | Database search strategies and supplementary identification |
| [S2 (CSV)](Supplemental_Files/Supplemental_Data_S2_Included_Reports.csv) | Included reports and their coding. Input for the analysis scripts |
| [S3 (CSV)](Supplemental_Files/Supplemental_Data_S3_Full_Text_Exclusions.csv) | Full-text exclusions and reasons |
| [S4 (XLSX)](Supplemental_Files/Supplemental_Data_S4_Pretraining_Downstream_Exposure.xlsx) | Pretraining exposure of downstream test participants and recordings |
| [S5 (PDF)](Supplemental_Files/Supplemental_Data_S5_PRISMA_2020_checklist.pdf) | PRISMA 2020 checklist |

## Run the analysis

From the repository root, use Python 3.10 or newer. Install Times New Roman to match the manuscript figures.

```sh
python -m pip install -r requirements.txt
python scripts/prepare_latest_data.py --output-dir outputs/data
python scripts/generate_ssl_summary_charts.py --csv outputs/data/data_si2_latest.csv --output-dir outputs/charts
python scripts/plot_ae_publication_trend.py --csv outputs/data/data_si2_latest.csv --output-dir outputs/charts
python scripts/plot_ssl_method_disorder_heatmap.py --output-dir outputs/heatmap
```

The preparation script writes the plotting dataset and `outputs/data/evaluation_summary.json`. The SSL charts cover Figures 5, 6, 11 and 12. The autoencoder trend is Figure 14, and the report-count heatmap is Figure 13.

## License

The analysis and plotting code is released under the [MIT License](LICENSE).
