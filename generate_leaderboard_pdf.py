#!/usr/bin/env python3
"""
Generate PDF leaderboard from evaluation results.
"""

import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

def generate_leaderboard_pdf(json_path: str, output_path: str):
    """Generate a PDF leaderboard from results JSON."""
    
    with open(json_path) as f:
        data = json.load(f)
    
    # Get sorted models
    averages = data.get('absolute_averages', {})
    sorted_models = sorted(averages.items(), key=lambda x: x[1], reverse=True)
    
    # Get metrics
    case_details = data.get('case_results_details', {})
    model_stats = {}
    
    MODEL_PRICING = {
        "openai/gpt-5.2": (1.75, 14.0),
        "openai/gpt-5.2-codex": (1.25, 10.0),
        "anthropic/claude-opus-4.5": (5.0, 25.0),
        "anthropic/claude-sonnet-4.5": (3.0, 15.0),
        "google/gemini-3-flash-preview": (0.50, 3.0),
        "google/gemini-3-pro-preview": (2.0, 12.0),
        "moonshotai/kimi-k2.5": (0.60, 2.5),
        "z-ai/glm-4.7": (0.30, 1.2),
        "qwen/qwen3-coder": (0.30, 1.2),
        "minimax/minimax-m2.1": (0.30, 1.2),
        "arcee-ai/trinity-large-preview:free": (0.0, 0.0),
    }
    
    def calculate_cost(model_id, total_input, total_output):
        pricing = MODEL_PRICING.get(model_id, (3.0, 15.0))
        input_rate, output_rate = pricing
        cost = (total_input / 1_000_000) * input_rate
        cost += (total_output / 1_000_000) * output_rate
        return round(cost, 2)
    
    for model_id, _ in sorted_models:
        times = []
        tokens = []
        input_tokens = []
        output_tokens = []
        
        for case_name in case_details:
            metrics = case_details[case_name].get('model_metrics', {}).get(model_id, {})
            if metrics:
                times.append(metrics.get('time_seconds', 0))
                in_tok = metrics.get('input_tokens', 0)
                out_tok = metrics.get('output_tokens', 0)
                tokens.append(in_tok + out_tok)
                input_tokens.append(in_tok)
                output_tokens.append(out_tok)
        
        from statistics import mean
        model_stats[model_id] = {
            'avg_time': mean(times) if times else 0,
            'avg_tokens': mean(tokens) if tokens else 0,
            'total_input': sum(input_tokens),
            'total_output': sum(output_tokens),
            'total_cost': calculate_cost(model_id, sum(input_tokens), sum(output_tokens))
        }
    
    # Create PDF
    with PdfPages(output_path) as pdf:
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis('tight')
        ax.axis('off')
        
        # Title
        fig.suptitle('Vibe Code Bench - Leaderboard', fontsize=20, fontweight='bold', y=0.98)
        date_str = data['timestamp'][:10] if 'timestamp' in data else 'N/A'
        ax.text(0.5, 0.95, f'Evaluation Date: {date_str}', 
                transform=fig.transFigure, ha='center', fontsize=12, color='#666666')
        
        # Prepare table data
        table_data = []
        headers = ['Rank', 'Model', 'Score', 'Avg Time (s)', 'Avg Tokens', 'Total Cost']
        table_data.append(headers)
        
        for rank, (model_id, score) in enumerate(sorted_models, 1):
            stats = model_stats[model_id]
            model_name = model_id.split('/')[-1].replace(':free', '')
            
            table_data.append([
                str(rank),
                model_name,
                f"{score:.1f}",
                f"{stats['avg_time']:.1f}",
                f"{int(stats['avg_tokens']):,}",
                f"${stats['total_cost']:.2f}"
            ])
        
        # Create table
        table = ax.table(cellText=table_data[1:], colLabels=headers,
                        cellLoc='center', loc='center',
                        bbox=[0, 0.1, 1, 0.8])
        
        # Style header row
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#2c3e50')
            table[(0, i)].set_text_props(weight='bold', color='white')
            table[(0, i)].set_height(0.06)
        
        # Style data rows
        for i in range(1, len(table_data)):
            for j in range(len(headers)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f8f9fa')
                else:
                    table[(i, j)].set_facecolor('white')
                table[(i, j)].set_height(0.05)
        
        # Adjust column widths
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Footer
        footer_text = f"Based on {len(data['cases'])} evaluation cases | {len(data['models'])} models tested"
        ax.text(0.5, 0.02, footer_text, transform=fig.transFigure, 
                ha='center', fontsize=9, color='#999999')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    print(f"✅ PDF leaderboard created: {output_path}")

if __name__ == "__main__":
    import sys
    json_file = sys.argv[1] if len(sys.argv) > 1 else "results/20260129_merged_results.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "LEADERBOARD.pdf"
    generate_leaderboard_pdf(json_file, output_file)
