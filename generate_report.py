import json
import argparse
from statistics import mean

def generate_markdown(json_path: str, md_path: str):
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    models = sorted(list(set(m for res in data["case_results"].values() for m in res["absolute_scores"].keys())))
    cases = sorted(data["case_results"].keys())
    
    # Calculate global averages
    model_stats = {m: {"scores": [], "times": [], "tokens": []} for m in models}
    
    for case in cases:
        res = data["case_results"][case]
        for m in models:
            # Score
            score_data = res["absolute_scores"].get(m, {})
            score = score_data.get("total_score", 0)
            model_stats[m]["scores"].append(score)
            
            # Metrics
            metrics = res["model_metrics"].get(m, {})
            model_stats[m]["times"].append(metrics.get("time_seconds", 0))
            # approximate tokens as input+output if available
            in_tok = metrics.get("input_tokens", 0)
            out_tok = metrics.get("output_tokens", 0)
            model_stats[m]["tokens"].append(in_tok + out_tok)

    # Sort comparisons
    leaderboard = []
    for m in models:
        avg_score = mean(model_stats[m]["scores"])
        avg_time = mean(model_stats[m]["times"])
        avg_tokens = mean(model_stats[m]["tokens"])
        leaderboard.append({
            "model": m,
            "score": avg_score,
            "time": avg_time,
            "tokens": avg_tokens
        })
        
    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    
    # Generate MD content
    lines = []
    lines.append("# Vibe Code Bench - Final Report")
    lines.append(f"**Date:** {data.get('timestamp')}")
    lines.append(f"**Runs Averaged:** {data.get('runs_averaged')}")
    lines.append("")
    
    lines.append("## 🏆 Leaderboard")
    lines.append("| Rank | Model | Average Score (0-100) | Avg Time (s) | Avg Tokens |")
    lines.append("|------|-------|-----------------------|--------------|------------|")
    
    for idx, row in enumerate(leaderboard, 1):
        lines.append(f"| {idx} | `{row['model']}` | **{row['score']:.1f}** | {row['time']:.1f} | {int(row['tokens'])} |")
        
    lines.append("")
    lines.append("## 📊 Case Breakdown")
    
    # Header - simplify model names for columns
    def clean_name(n):
        if "/" in n: n = n.split("/")[-1]
        n = n.replace("-latest", "").replace("claude-", "").replace("gpt-", "").replace("gemini-", "")
        return n
        
    header = "| Case | " + " | ".join([f"`{clean_name(m['model'])}`" for m in leaderboard]) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(leaderboard) + 1))
    
    for case in cases:
        row = [f"`{case}`"]
        for m_data in leaderboard:
            m = m_data["model"]
            score = data["case_results"][case]["absolute_scores"].get(m, {}).get("total_score", "-")
            row.append(str(score))
        lines.append("| " + " | ".join(row) + " |")

    with open(md_path, 'w') as f:
        f.write("\n".join(lines))
    
    print(f"Report generated at {md_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    parser.add_argument("-o", "--output", default="BENCHMARK_REPORT.md")
    args = parser.parse_args()
    generate_markdown(args.json_file, args.output)
