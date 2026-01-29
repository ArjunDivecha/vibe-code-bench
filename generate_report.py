"""
=============================================================================
SCRIPT NAME: generate_report.py
=============================================================================

INPUT FILES:
- /Users/arjundivecha/Dropbox/AAA Backup/Temp/vibe-code-bench/results/*.json:
  Evaluation result files from `python -m vibe_eval run`.

OUTPUT FILES:
- /Users/arjundivecha/Dropbox/AAA Backup/Temp/vibe-code-bench/BENCHMARK_REPORT.md:
  Markdown report with leaderboard, case breakdown, and differentiation stats.

VERSION: 2.0
LAST UPDATED: 2026-01-27
AUTHOR: Arjun (automated by assistant)

DESCRIPTION:
Generate a Markdown report from an evaluation JSON. Includes leaderboard,
case-by-case breakdown, runtime summary, and differentiation indicators.

DEPENDENCIES:
- Python standard library only

USAGE:
python generate_report.py results/TIMESTAMP_results.json -o BENCHMARK_REPORT.md

NOTES:
- Supports both V2/V3 result formats.
=============================================================================
"""

import argparse
import json
from statistics import mean, pstdev


def _get_case_results(data: dict) -> dict:
    """Return case results with model metrics if available."""
    if "case_results_details" in data:
        return data["case_results_details"]
    return data.get("case_results", {})


def _collect_models(case_results: dict) -> list[str]:
    """Collect models from case results."""
    models = set()
    for res in case_results.values():
        for model in res.get("absolute_scores", {}).keys():
            models.add(model)
    return sorted(models)


def generate_markdown(json_path: str, md_path: str) -> None:
    with open(json_path, "r") as f:
        data = json.load(f)

    case_results = _get_case_results(data)
    models = _collect_models(case_results)
    cases = sorted(case_results.keys())

    # Calculate global averages
    model_stats = {m: {"scores": [], "times": [], "tokens": [], "judge_cost": []} for m in models}

    for case in cases:
        res = case_results[case]
        for m in models:
            score_data = res.get("absolute_scores", {}).get(m, {})
            score = score_data.get("total_score", 0)
            model_stats[m]["scores"].append(score)

            metrics = res.get("model_metrics", {}).get(m, {})
            model_stats[m]["times"].append(metrics.get("time_seconds", 0))
            in_tok = metrics.get("input_tokens", 0)
            out_tok = metrics.get("output_tokens", 0)
            model_stats[m]["tokens"].append(in_tok + out_tok)
            model_stats[m]["judge_cost"].append(metrics.get("judge_cost", 0))

    leaderboard = []
    for m in models:
        leaderboard.append(
            {
                "model": m,
                "score": mean(model_stats[m]["scores"]) if model_stats[m]["scores"] else 0,
                "time": mean(model_stats[m]["times"]) if model_stats[m]["times"] else 0,
                "tokens": mean(model_stats[m]["tokens"]) if model_stats[m]["tokens"] else 0,
                "judge_cost": mean(model_stats[m]["judge_cost"]) if model_stats[m]["judge_cost"] else 0,
            }
        )

    leaderboard.sort(key=lambda x: x["score"], reverse=True)

    # Differentiation stats
    gaps = []
    for case in cases:
        scores = [
            res.get("absolute_scores", {}).get(m, {}).get("total_score", 0)
            for m in models
        ]
        if scores:
            gaps.append(max(scores) - min(scores))

    median_gap = sorted(gaps)[len(gaps) // 2] if gaps else 0
    std_gap = pstdev(gaps) if len(gaps) > 1 else 0

    # Generate MD content
    lines = []
    lines.append("# Vibe Code Bench - Final Report")
    lines.append(f"**Date:** {data.get('timestamp')}")
    lines.append(f"**Suite:** {data.get('suite', 'full')}")
    lines.append("")

    lines.append("## Leaderboard")
    lines.append("| Rank | Model | Average Score (0-100) | Avg Time (s) | Avg Tokens | Avg Judge Cost |")
    lines.append("|------|-------|-----------------------|--------------|------------|----------------|")

    for idx, row in enumerate(leaderboard, 1):
        lines.append(
            f"| {idx} | `{row['model']}` | **{row['score']:.1f}** | "
            f"{row['time']:.1f} | {int(row['tokens'])} | ${row['judge_cost']:.4f} |"
        )

    lines.append("")
    lines.append("## Differentiation Summary")
    lines.append(f"- Median score gap per case: {median_gap:.1f}")
    lines.append(f"- Score gap standard deviation: {std_gap:.1f}")
    lines.append("")

    lines.append("## Case Breakdown")

    def clean_name(name: str) -> str:
        if "/" in name:
            name = name.split("/")[-1]
        return (
            name.replace("-latest", "")
            .replace("claude-", "")
            .replace("gpt-", "")
            .replace("gemini-", "")
        )

    header = "| Case | " + " | ".join([f"`{clean_name(m['model'])}`" for m in leaderboard]) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(leaderboard) + 1))

    for case in cases:
        row = [f"`{case}`"]
        for m_data in leaderboard:
            m = m_data["model"]
            score = case_results[case]["absolute_scores"].get(m, {}).get("total_score", "-")
            row.append(str(score))
        lines.append("| " + " | ".join(row) + " |")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Report generated at {md_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    parser.add_argument("-o", "--output", default="BENCHMARK_REPORT.md")
    args = parser.parse_args()
    generate_markdown(args.json_file, args.output)
