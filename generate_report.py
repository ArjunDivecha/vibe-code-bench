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

    # Model pricing per 1M tokens (input, output) - OpenRouter rates
    MODEL_PRICING = {
        "openai/gpt-5.2": (1.75, 14.0),
        "openai/gpt-5.2-codex": (1.25, 10.0),
        "anthropic/claude-opus-4.5": (5.0, 25.0),
        "anthropic/claude-sonnet-4.5": (3.0, 15.0),
        "google/gemini-3-flash-preview": (0.50, 3.0),
        "moonshotai/kimi-k2.5": (0.60, 2.5),  # Approximate based on Kimi K2 Thinking
        "z-ai/glm-4.7": (0.30, 1.2),  # Approximate based on similar models
        "qwen/qwen3-coder": (0.30, 1.2),  # Approximate
        "minimax/minimax-m2.1": (0.30, 1.2),  # Approximate based on MiniMax M2
        "arcee-ai/trinity-large-preview:free": (0.0, 0.0),  # Free model
    }

    def calculate_model_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for model execution."""
        pricing = MODEL_PRICING.get(model_id, (3.0, 15.0))  # Default fallback
        input_rate, output_rate = pricing
        cost = (input_tokens / 1_000_000) * input_rate
        cost += (output_tokens / 1_000_000) * output_rate
        return round(cost, 6)

    # Calculate global averages
    model_stats = {m: {"scores": [], "times": [], "tokens": [], "input_tokens": [], "output_tokens": [], "cost": []} for m in models}

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
            model_stats[m]["input_tokens"].append(in_tok)
            model_stats[m]["output_tokens"].append(out_tok)
            model_stats[m]["tokens"].append(in_tok + out_tok)
            # Calculate cost for this case
            case_cost = calculate_model_cost(m, in_tok, out_tok)
            model_stats[m]["cost"].append(case_cost)

    leaderboard = []
    for m in models:
        total_input = sum(model_stats[m]["input_tokens"])
        total_output = sum(model_stats[m]["output_tokens"])
        total_cost = calculate_model_cost(m, total_input, total_output)
        
        leaderboard.append(
            {
                "model": m,
                "score": mean(model_stats[m]["scores"]) if model_stats[m]["scores"] else 0,
                "time": mean(model_stats[m]["times"]) if model_stats[m]["times"] else 0,
                "tokens": mean(model_stats[m]["tokens"]) if model_stats[m]["tokens"] else 0,
                "total_cost": total_cost,
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
    lines.append("| Rank | Model | Average Score (0-100) | Avg Time (s) | Avg Tokens | Total Cost |")
    lines.append("|------|-------|-----------------------|--------------|------------|------------|")

    for idx, row in enumerate(leaderboard, 1):
        lines.append(
            f"| {idx} | `{row['model']}` | **{row['score']:.1f}** | "
            f"{row['time']:.1f} | {int(row['tokens'])} | ${row['total_cost']:.2f} |"
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
