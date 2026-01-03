import json
import os
import argparse
from typing import Dict, Any

def merge_run_files(run_dir: str, output_path: str):
    """Merges all *_results.json files in a directory into one."""
    merged = {
        "timestamp": None,
        "models": [],
        "cases": [],
        "case_results": {},
        "case_results_details": {}
    }
    
    # Walk directory to find all json results
    json_files = []
    for root, dirs, files in os.walk(run_dir):
        for file in files:
            if file.endswith("_results.json"):
                json_files.append(os.path.join(root, file))
                
    print(f"Found {len(json_files)} result files in {run_dir}")
    
    if not json_files:
        print("No files found.")
        return

    for path in json_files:
        with open(path, 'r') as f:
            data = json.load(f)
            
            # Set timestamp from first file (approximate is fine)
            if not merged["timestamp"]:
                merged["timestamp"] = data.get("timestamp")
            
            # Merge models list
            for m in data.get("models", []):
                if m not in merged["models"]:
                    merged["models"].append(m)
            
            # Merge cases list
            for c in data.get("cases", []):
                if c not in merged["cases"]:
                    merged["cases"].append(c)
                    
            # Merge case_results
            for case_name, case_data in data.get("case_results", {}).items():
                if case_name not in merged["case_results"]:
                    merged["case_results"][case_name] = {
                        "absolute_scores": {},
                        "comparisons": []
                    }
                
                # Merge absolute scores
                abs_scores = case_data.get("absolute_scores", {})
                for model, score_data in abs_scores.items():
                    merged["case_results"][case_name]["absolute_scores"][model] = score_data
                    
            # Merge case_results_details
            for case_name, case_details in data.get("case_results_details", {}).items():
                if case_name not in merged["case_results_details"]:
                    merged["case_results_details"][case_name] = {
                        "absolute_scores": {},
                        "model_metrics": {}
                    }
                
                # Merge details absolute scores
                abs_scores = case_details.get("absolute_scores", {})
                for model, score_data in abs_scores.items():
                    merged["case_results_details"][case_name]["absolute_scores"][model] = score_data
                    
                # Merge model metrics
                metrics = case_details.get("model_metrics", {})
                for model, metric_data in metrics.items():
                    merged["case_results_details"][case_name]["model_metrics"][model] = metric_data

    # Write merged file
    with open(output_path, 'w') as f:
        json.dump(merged, f, indent=2)
    
    print(f"Merged run data saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", help="Directory containing individual model results")
    parser.add_argument("-o", "--output", required=True, help="Output JSON path")
    args = parser.parse_args()
    merge_run_files(args.run_dir, args.output)
