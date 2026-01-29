"""
=============================================================================
SCRIPT NAME: differentiation.py
=============================================================================

INPUT FILES:
- /Users/arjundivecha/Dropbox/AAA Backup/Temp/vibe-code-bench/results/*.json:
  Evaluation result files created by `python -m vibe_eval run`.

OUTPUT FILES:
- /Users/arjundivecha/Dropbox/AAA Backup/Temp/vibe-code-bench/reports/differentiation_baseline.md:
  Markdown summary of variance, runtime, and signal-per-minute.
- /Users/arjundivecha/Dropbox/AAA Backup/Temp/vibe-code-bench/reports/variance_tables.xlsx:
  Spreadsheet tables for case and dimension variance.

VERSION: 1.0
LAST UPDATED: 2026-01-27
AUTHOR: Arjun (automated by assistant)

DESCRIPTION:
Generate variance and runtime diagnostics from prior evaluation runs. This
helps identify cases that are low-signal (scores too similar) or expensive
(slow runtime) so we can speed up the benchmark while improving separation.

DEPENDENCIES:
- Python standard library only (json, statistics, zipfile, xml)

USAGE:
python -m vibe_eval diagnose --results-dir results --output-dir reports

NOTES:
- This script writes .xlsx without external dependencies using the Excel
  OpenXML format. It is a minimal spreadsheet writer.
- Outputs are designed for quick review by non-technical readers.
=============================================================================
"""

from __future__ import annotations

import json
import statistics
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape


@dataclass
class CaseStats:
    """Computed statistics for a single case."""
    case_name: str
    models: list[str]
    scores: dict[str, float]
    avg_score: float
    score_range: float
    std_dev: float
    avg_time_seconds: float
    signal_per_minute: float


@dataclass
class DimensionStats:
    """Computed statistics for a single dimension within a case."""
    case_name: str
    dimension: str
    avg_score: float
    score_range: float
    std_dev: float


def load_results(results_dir: Path) -> list[dict]:
    """Load all result JSON files from a directory."""
    results = []
    for path in sorted(results_dir.glob("*_results.json")):
        try:
            results.append(json.loads(path.read_text()))
        except Exception:
            continue
    return results


def compute_case_stats(data: dict) -> list[CaseStats]:
    """Compute per-case variance and runtime stats."""
    case_results = data.get("case_results", {})
    case_details = data.get("case_results_details", {})
    stats: list[CaseStats] = []

    for case_name, case in case_results.items():
        scores = {
            model: details["total_score"]
            for model, details in case.get("absolute_scores", {}).items()
        }
        if not scores:
            continue

        model_scores = list(scores.values())
        avg_score = statistics.mean(model_scores)
        score_range = max(model_scores) - min(model_scores)
        std_dev = statistics.pstdev(model_scores) if len(model_scores) > 1 else 0.0

        metrics = case_details.get(case_name, {}).get("model_metrics", {})
        times = [m.get("time_seconds", 0.0) for m in metrics.values()]
        avg_time = statistics.mean(times) if times else 0.0

        signal_per_minute = 0.0
        if avg_time > 0:
            signal_per_minute = score_range / (avg_time / 60.0)

        stats.append(
            CaseStats(
                case_name=case_name,
                models=list(scores.keys()),
                scores=scores,
                avg_score=round(avg_score, 2),
                score_range=round(score_range, 2),
                std_dev=round(std_dev, 2),
                avg_time_seconds=round(avg_time, 2),
                signal_per_minute=round(signal_per_minute, 2),
            )
        )

    return stats


def compute_dimension_stats(data: dict) -> list[DimensionStats]:
    """Compute per-dimension variance across models for each case."""
    case_results = data.get("case_results", {})
    stats: list[DimensionStats] = []

    for case_name, case in case_results.items():
        by_model = case.get("absolute_scores", {})
        if not by_model:
            continue

        # Collect dimensions present in the first model
        first = next(iter(by_model.values()), {})
        dimensions = [d for d in first.keys() if d not in {"total_score", "execution_gated", "judge_metrics"}]

        for dim in dimensions:
            values = []
            for model, score_data in by_model.items():
                if isinstance(score_data.get(dim), dict):
                    values.append(score_data[dim].get("score", 0))
            if not values:
                continue
            avg_score = statistics.mean(values)
            score_range = max(values) - min(values)
            std_dev = statistics.pstdev(values) if len(values) > 1 else 0.0
            stats.append(
                DimensionStats(
                    case_name=case_name,
                    dimension=dim,
                    avg_score=round(avg_score, 2),
                    score_range=round(score_range, 2),
                    std_dev=round(std_dev, 2),
                )
            )

    return stats


def _xml_row(row_idx: int, values: list[str]) -> str:
    """Convert a row of strings to Excel XML cells."""
    cells = []
    for col_idx, value in enumerate(values, start=1):
        cell_ref = f"{_col_letter(col_idx)}{row_idx}"
        escaped = escape(str(value))
        cells.append(
            f'<c r="{cell_ref}" t="s"><v>{escaped}</v></c>'
        )
    return f"<row r=\"{row_idx}\">{''.join(cells)}</row>"


def _col_letter(index: int) -> str:
    """Convert column number (1-based) to Excel column letters."""
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def write_simple_xlsx(path: Path, sheets: dict[str, list[list[str]]]) -> None:
    """Write a minimal .xlsx with multiple sheets."""
    path.parent.mkdir(parents=True, exist_ok=True)

    # Build shared strings table
    shared_strings = []
    string_index = {}

    def add_shared(value: str) -> int:
        if value not in string_index:
            string_index[value] = len(shared_strings)
            shared_strings.append(value)
        return string_index[value]

    sheet_xml = {}
    for sheet_name, rows in sheets.items():
        row_xml = []
        for r_idx, row in enumerate(rows, start=1):
            cell_xml = []
            for c_idx, value in enumerate(row, start=1):
                idx = add_shared(str(value))
                cell_ref = f"{_col_letter(c_idx)}{r_idx}"
                cell_xml.append(f'<c r="{cell_ref}" t="s"><v>{idx}</v></c>')
            row_xml.append(f"<row r=\"{r_idx}\">{''.join(cell_xml)}</row>")
        sheet_xml[sheet_name] = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f"<sheetData>{''.join(row_xml)}</sheetData>"
            "</worksheet>"
        )

    shared_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{len(shared_strings)}" uniqueCount="{len(shared_strings)}">'
        + "".join(f"<si><t>{escape(s)}</t></si>" for s in shared_strings)
        + "</sst>"
    )

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets>"
        + "".join(
            f'<sheet name="{escape(name)}" sheetId="{idx}" r:id="rId{idx}"/>'
            for idx, name in enumerate(sheets.keys(), start=1)
        )
        + "</sheets></workbook>"
    )

    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{idx}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{idx}.xml"/>'
            for idx in range(1, len(sheets) + 1)
        )
        + '<Relationship Id="rIdShared" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" '
        'Target="sharedStrings.xml"/>'
        + "</Relationships>"
    )

    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        + "</Relationships>"
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        + "".join(
            f'<Override PartName="/xl/worksheets/sheet{idx}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for idx in range(1, len(sheets) + 1)
        )
        + "</Types>"
    )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/sharedStrings.xml", shared_xml)
        for idx, name in enumerate(sheets.keys(), start=1):
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", sheet_xml[name])


def write_markdown_report(path: Path, case_stats: list[CaseStats]) -> None:
    """Write a markdown summary report."""
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Differentiation Baseline",
        "",
        "This report summarizes score variance and runtime costs.",
        "",
        "## Top Signal-Per-Minute Cases",
        "",
        "| Case | Score Range | Avg Score | Avg Time (s) | Signal/Min |",
        "|------|-------------|-----------|--------------|------------|",
    ]
    for entry in sorted(case_stats, key=lambda c: c.signal_per_minute, reverse=True)[:10]:
        lines.append(
            f"| {entry.case_name} | {entry.score_range:.1f} | {entry.avg_score:.1f} | "
            f"{entry.avg_time_seconds:.1f} | {entry.signal_per_minute:.1f} |"
        )

    lines += [
        "",
        "## Slowest Cases",
        "",
        "| Case | Avg Time (s) | Score Range |",
        "|------|--------------|-------------|",
    ]
    for entry in sorted(case_stats, key=lambda c: c.avg_time_seconds, reverse=True)[:10]:
        lines.append(
            f"| {entry.case_name} | {entry.avg_time_seconds:.1f} | {entry.score_range:.1f} |"
        )

    path.write_text("\n".join(lines))


def generate_reports(results_dir: Path, output_dir: Path) -> None:
    """Generate markdown and xlsx variance reports from results."""
    results = load_results(results_dir)
    if not results:
        raise ValueError(f"No results found in {results_dir}")

    # Use most recent results file
    data = results[-1]

    case_stats = compute_case_stats(data)
    dimension_stats = compute_dimension_stats(data)

    # Markdown report
    write_markdown_report(output_dir / "differentiation_baseline.md", case_stats)

    # XLSX report
    case_rows = [
        ["case", "avg_score", "score_range", "std_dev", "avg_time_seconds", "signal_per_minute"]
    ]
    for entry in case_stats:
        case_rows.append(
            [
                entry.case_name,
                entry.avg_score,
                entry.score_range,
                entry.std_dev,
                entry.avg_time_seconds,
                entry.signal_per_minute,
            ]
        )

    dim_rows = [["case", "dimension", "avg_score", "score_range", "std_dev"]]
    for entry in dimension_stats:
        dim_rows.append(
            [
                entry.case_name,
                entry.dimension,
                entry.avg_score,
                entry.score_range,
                entry.std_dev,
            ]
        )

    write_simple_xlsx(
        output_dir / "variance_tables.xlsx",
        {"case_variance": case_rows, "dimension_variance": dim_rows},
    )


def _find_results_dir(candidate: Path | None) -> Path:
    """Resolve results directory, defaulting to ./results."""
    if candidate:
        return candidate
    return Path("results")


def _find_output_dir(candidate: Path | None) -> Path:
    """Resolve output directory, defaulting to ./reports."""
    if candidate:
        return candidate
    return Path("reports")


def main(results_dir: Path | None = None, output_dir: Path | None = None) -> None:
    """Entry point for CLI usage."""
    results = _find_results_dir(results_dir)
    output = _find_output_dir(output_dir)
    generate_reports(results, output)


if __name__ == "__main__":
    main()
