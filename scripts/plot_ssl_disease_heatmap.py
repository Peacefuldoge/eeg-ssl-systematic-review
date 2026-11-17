"""Plot SSL method-by-disorder coverage from the included-report coding CSV.

Run: python plot_ssl_disease_heatmap.py
Requires: numpy and matplotlib. The original CSV is read without modification.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import textwrap

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".mpl_cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np

from reference_style import configure_export_style


METHODS = ("Predictive SSL", "Generative SSL", "Discriminative SSL", "Hybrid SSL")
DISEASES = (
    "Epilepsy and seizures",
    "Mood disorders",
    "Neurodegenerative disorders",
    "Neurodevelopmental disorders",
    "Schizophrenia spectrum disorders",
    "Obsessive-compulsive and related disorders",
    "Cerebrovascular disorders",
    "Other neurological disorders",
    "Anxiety disorders",
    "Trauma- and stress-related disorders",
    "Addictive disorders",
)
REQUIRED = {"Record ID", "Analysis group", "Learning method", "Disorder coverage"}


def coded_diseases(value: str) -> set[str]:
    """Split SI2 disorder coding.

    The qualifier written in parentheses after 'Other neurological disorders' can
    itself contain a semicolon, so only separators outside parentheses delimit
    families; the qualifier is then dropped to reach the approved family name.
    """
    parts, buf, depth = [], [], 0
    for char in value or "":
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(depth - 1, 0)
        if char == ";" and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(char)
    parts.append("".join(buf))
    coded = set()
    for part in parts:
        head = part.split("(", 1)[0].strip()
        if head:
            coded.add(head)
    return coded


def load_reports(path: Path, expected_reports: int | None):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Missing input columns: {sorted(missing)}")
        records = list(reader)
    reports = [r for r in records if r["Analysis group"].strip() == "Self-supervised learning"]
    ids = [r["Record ID"].strip() for r in reports]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate SSL report IDs would inflate the counts.")
    if not reports:
        raise ValueError("No reports in the Self-supervised learning analysis group.")
    if expected_reports is not None and len(reports) != expected_reports:
        raise ValueError(f"Expected {expected_reports} SSL reports; found {len(reports)}.")
    for report in reports:
        if report["Learning method"].strip() not in METHODS:
            raise ValueError(f"Unknown SSL method for {report['Record ID']}: {report['Learning method']}")
        diseases = coded_diseases(report["Disorder coverage"])
        if not diseases or diseases - set(DISEASES):
            raise ValueError(f"Missing/unknown disorder coding for {report['Record ID']}: {diseases}")
    return reports


def aggregate(reports):
    """Count each report once per method/disorder pair; preserve multi-disorder coverage."""
    counts = np.zeros((len(DISEASES), len(METHODS)), dtype=int)
    method_totals = {method: 0 for method in METHODS}
    contributing_ids = {d: {m: [] for m in METHODS} for d in DISEASES}
    for report in reports:
        method = report["Learning method"].strip()
        method_totals[method] += 1
        diseases = coded_diseases(report["Disorder coverage"])
        for disease in diseases:
            counts[DISEASES.index(disease), METHODS.index(method)] += 1
            contributing_ids[disease][method].append(report["Record ID"])
    for diseases in contributing_ids.values():
        for ids in diseases.values():
            ids.sort()
    assert sum(method_totals.values()) == len(reports)
    assert int(counts.sum()) == sum(len(coded_diseases(r["Disorder coverage"])) for r in reports)
    return counts, method_totals, contributing_ids


def draw(counts, method_totals, output_dir: Path, mode: str, dpi: int):
    visible = counts.sum(axis=1) > 0
    diseases = tuple(disease for disease, show in zip(DISEASES, visible) if show)
    counts = counts[visible]
    disease_totals = counts.sum(axis=1)
    if mode == "count":
        values = counts.astype(float)
        vmax = max(1, int(counts.max()))
        colorbar_label = "Number of reports"
        filename = "SSL_method_disorder_counts"
    else:
        # Within each disease family, the method shares sum to 100%.
        values = np.divide(counts * 100.0, disease_totals[:, None],
                           out=np.full(counts.shape, np.nan), where=disease_totals[:, None] > 0)
        vmax = 100
        colorbar_label = "Within-disorder share (%)"
        filename = "SSL_method_disorder_within_disorder_percent"
    configure_export_style()
    plt.rcParams.update({
        "font.size": 13, "axes.labelsize": 14, "xtick.labelsize": 13,
        "ytick.labelsize": 13,
    })
    fig, ax = plt.subplots(figsize=(8.5, 6.0))
    fig.subplots_adjust(left=0.385, right=0.88, top=0.82, bottom=0.10)
    cmap = plt.colormaps["Blues"].copy()
    cmap.set_bad("#ededed")
    im = ax.pcolormesh(np.arange(len(METHODS) + 1) - 0.5,
                       np.arange(len(diseases) + 1) - 0.5,
                       np.ma.masked_invalid(values), vmin=0, vmax=vmax,
                       cmap=cmap, shading="flat", rasterized=False)
    ax.set_xlim(-0.5, len(METHODS) - 0.5)
    ax.set_ylim(len(diseases) - 0.5, -0.5)
    xticklabels = [m.replace(" SSL", "") + f"\n(n = {method_totals[m]})" for m in METHODS]
    yticklabels = [textwrap.fill(d, width=30, break_long_words=False, break_on_hyphens=False)
                  + f"  (n = {int(n)})" for d, n in zip(diseases, disease_totals)]
    ax.set_xticks(range(len(METHODS)), labels=xticklabels)
    ax.set_yticks(range(len(diseases)), labels=yticklabels)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlabel("SSL category", labelpad=13)
    ax.set_ylabel("Disorder family", labelpad=11)
    ax.tick_params(axis="both", which="both", length=0, pad=8)
    ax.set_xticks(np.arange(-0.5, len(METHODS), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(diseases), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for i in range(len(diseases)):
        for j in range(len(METHODS)):
            value = values[i, j]
            label = "—" if np.isnan(value) else (str(counts[i, j]) if mode == "count" else f"{value:.0f}%")
            color = "white" if np.isfinite(value) and value > 0.58 * vmax else "#242424"
            ax.text(j, i, label, ha="center", va="center", color=color, fontsize=13)
    cb_ax = fig.add_axes([0.90, 0.18, 0.022, 0.58])
    colorbar = fig.colorbar(im, cax=cb_ax)
    if colorbar.solids is not None:
        colorbar.solids.set_rasterized(False)
    colorbar.set_label(colorbar_label, labelpad=10)
    if mode == "count":
        colorbar.locator = MaxNLocator(nbins=6, integer=True)
        colorbar.update_ticks()
    colorbar.outline.set_visible(False)
    for extension in ("pdf", "svg", "png"):
        fig.savefig(output_dir / f"{filename}.{extension}", dpi=dpi)
    plt.close(fig)


def main():
    project_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=project_root / "Supplemental_Files" /
                        "Supplemental_Data_S2_Included_Reports.csv")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "figures")
    parser.add_argument("--expected-reports", type=int, default=61,
                        help="Expected SSL report count; set to 0 to disable this check for a future dataset.")
    parser.add_argument("--dpi", type=int, default=400)
    args = parser.parse_args()
    reports = load_reports(args.input, args.expected_reports or None)
    counts, method_totals, contributing_ids = aggregate(reports)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for mode in ("count", "within-disorder"):
        draw(counts, method_totals, args.output_dir, mode, args.dpi)
    with (args.output_dir / "heatmap_counts.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Disorder family", *METHODS, "Reports covering disorder"])
        for disease, row in zip(DISEASES, counts):
            writer.writerow([disease, *map(int, row), int(row.sum())])
    summary = {
        "input": str(args.input.resolve()), "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "SSL_reports": len(reports), "method_totals": method_totals,
        "disease_totals": dict(zip(DISEASES, map(int, counts.sum(axis=1)))),
        "report_disorder_memberships": int(counts.sum()),
        "counting_rule": "Documented pretraining or downstream use, once per report per disease family; disease families may overlap.",
        "normalization": "Percentages use the number of reports covering each disorder as denominator; zero-report disorders have undefined shares.",
        "interpretation": "Coverage, not comparative model performance, clinical effectiveness, or downstream-only validation.",
        "contributing_report_IDs": contributing_ids,
    }
    (args.output_dir / "heatmap_provenance.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created two heatmaps (PDF/SVG/PNG), counts and provenance in {args.output_dir.resolve()}")
    print(f"SSL reports: {len(reports)}; report-disorder memberships: {int(counts.sum())}")


if __name__ == "__main__":
    main()
