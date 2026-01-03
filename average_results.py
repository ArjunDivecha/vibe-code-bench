import json
import os
import argparse
from typing import List, Dict, Any
from statistics import mean
import datetime

def average_results(file_paths: List[str], output_path: str):
    """Averages results from multiple vibe-eval JSON result files."""
    if not file_paths:
        return

    all_data = []
    for path in file_paths:
        with open(path, 'r') as f:
            all_data.append(json.load(f))

    # Assume all runs have the same models and cases (mostly)
    models = all_data[0].get("models", [])
    cases = all_data[0].get("cases", [])
    
    averaged = {
        "timestamp": datetime.datetime.now().isoformat(),
        "runs_averaged": len(file_paths),
        "models": models,
        "cases": cases,
        "case_results": {}
    }

    for case in cases:
        averaged["case_results"][case] = {
            "absolute_scores": {},
            "model_metrics": {}
        }
        
        for model in models:
            scores = []
            metrics = {
                "time_seconds": [],
                "turns": [],
                "files_created": [],
                "input_tokens": [],
                "output_tokens": []
            }
            
            for data in all_data:
                # Get score
                case_res = data.get("case_results", {}).get(case, {})
                abs_scores = case_res.get("absolute_scores", {}).get(model, {})
                if "total_score" in abs_scores:
                    scores.append(abs_scores["total_score"])
                
                # Get metrics from details
                details = data.get("case_results_details", {}).get(case, {})
                model_metrics = details.get("model_metrics", {}).get(model, {})
                for k in metrics.keys():
                    if k in model_metrics:
                        metrics[k].append(model_metrics[k])

            # Average them
            if scores:
                averaged["case_results"][case]["absolute_scores"][model] = {
                    "total_score": round(mean(scores), 1)
                }
            
            if any(metrics.values()):
                averaged["case_results"][case]["model_metrics"][model] = {
                    k: round(mean(v), 2) if v else 0 for k, v in metrics.items()
                }

    with open(output_path, 'w') as f:
        json.dump(averaged, f, indent=2)
    
    print(f"Averaged results saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", help="JSON result files to average")
    parser.add_argument("-o", "--output", default="averaged_results.json", help="Output file path")
    args = parser.parse_args()
    average_results(args.files, args.output)
