import os
import json
import math
from collections import Counter

def get_stats():
    stats = {
        "extensions": Counter(),
        "total_lines": 0,
        "file_count": 0,
        "largest_files": [],
        "max_depth": 0,
        "dir_structure": {},
        "root_path": os.getcwd()
    }

    for root, dirs, files in os.walk("."):
        # Skip hidden directories like .git
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        # Calculate depth
        rel_path = os.path.relpath(root, ".")
        depth = 0 if rel_path == "." else rel_path.count(os.sep) + 1
        stats["max_depth"] = max(stats["max_depth"], depth)

        for file in files:
            if file.startswith('.'): continue
            
            file_path = os.path.join(root, file)
            stats["file_count"] += 1
            
            # Extension stats
            _, ext = os.path.splitext(file)
            ext = ext.lower() or "no-extension"
            stats["extensions"][ext] += 1

            # Line count and size
            try:
                size = os.path.getsize(file_path)
                with open(file_path, 'rb') as f:
                    lines = sum(1 for _ in f)
                stats["total_lines"] += lines
                
                stats["largest_files"].append({
                    "name": file,
                    "path": file_path,
                    "lines": lines,
                    "size": size
                })
            except (UnicodeDecodeError, PermissionError, FileNotFoundError):
                continue

    # Sort largest files and keep top 5
    stats["largest_files"].sort(key=lambda x: x["lines"], reverse=True)
    stats["largest_files"] = stats["largest_files"][:5]
    
    return stats

def generate_svg_pie(data):
    total = sum(data.values())
    if total == 0: return ""
    
    colors = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"]
    paths = []
    current_angle = 0
    
    sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:6]
    
    for i, (label, value) in enumerate(sorted_items):
        percentage = value / total
        angle = percentage * 360
        
        # Calculate SVG Arc
        x1 = 50 + 40 * math.cos(math.radians(current_angle - 90))
        y1 = 50 + 40 * math.sin(math.radians(current_angle - 90))
        
        current_angle += angle
        
        x2 = 50 + 40 * math.cos(math.radians(current_angle - 90))
        y2 = 50 + 40 * math.sin(math.radians(current_angle - 90))
        
        large_arc = 1 if angle > 180 else 0
        
        path = f'<path d="M 50 50 L {x1} {y1} A 40 40 0 {large_arc} 1 {x2} {y2} Z" fill="{colors[i % len(colors)]}"><title>{label}: {value}</title></path>'
        paths.append(path)
        
    return f'<svg viewBox="0 0 100 100" class="chart">{"".join(paths)}</svg>'

def generate_html(stats):
    ext_labels = sorted(stats["extensions"].items(), key=lambda x: x[1], reverse=True)[:6]
    pie_chart = generate_svg_pie(stats["extensions"])
    
    largest_files_html = "".join([
        f'<div class="file-item"><span>{f["name"]}</span><span class="val">{f["lines"]:,} lines</span></div>' 
        for f in stats["largest_files"]
    ])

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --accent: #38bdf8;
            --text-main: #f1f5f9;
            --text-dim: #94a3b8;
            --chart-1: #FF6384; --chart-2: #36A2EB; --chart-3: #FFCE56;
            --chart-4: #4BC0C0; --chart-5: #9966FF; --chart-6: #FF9F40;
        }}
        body {{
            background-color: var(--bg);
            color: var(--text-main);
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 2rem;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 1000px;
            width: 100%;
        }}
        header {{
            text-align: center;
            margin-bottom: 3rem;
        }}
        h1 {{
            font-size: 2.5rem;
            margin: 0;
            background: linear-gradient(90deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.025em;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }}
        .card {{
            background: var(--card-bg);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255,255,255,0.05);
        }}
        .stat-huge {{
            font-size: 3rem;
            font-weight: bold;
            color: var(--accent);
            display: block;
            margin-top: 0.5rem;
        }}
        .label {{
            color: var(--text-dim);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            font-weight: 600;
        }}
        .chart-container {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        .chart {{
            width: 150px;
            height: 150px;
            filter: drop-shadow(0 0 8px rgba(0,0,0,0.3));
        }}
        .legend {{
            flex: 1;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }}
        .dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .file-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.9rem;
        }}
        .file-item:last-child {{ border-bottom: none; }}
        .val {{ color: var(--accent); font-family: monospace; }}
        .pulse {{
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: .7; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p style="color: var(--text-dim)">Analysis of {os.path.basename(stats["root_path"])}</p>
        </header>

        <div class="grid">
            <div class="card">
                <span class="label">Total Scope</span>
                <span class="stat-huge">{stats["total_lines"]:,}</span>
                <span class="label">Lines of Code</span>
            </div>
            
            <div class="card">
                <span class="label">File Count</span>
                <span class="stat-huge">{stats["file_count"]:,}</span>
                <span class="label">Across {stats["max_depth"]} levels deep</span>
            </div>

            <div class="card" style="grid-column: span 1;">
                <span class="label">Composition</span>
                <div class="chart-container">
                    {pie_chart}
                    <div class="legend">
                        {"".join([f'<div class="legend-item"><div class="dot" style="background: var(--chart-{i+1})"></div>{ext} ({count})</div>' for i, (ext, count) in enumerate(ext_labels)])}
                    </div>
                </div>
            </div>

            <div class="card" style="grid-column: span 1;">
                <span class="label">Heavy Lifters (Largest Files)</span>
                <div style="margin-top: 1rem;">
                    {largest_files_html}
                </div>
            </div>
        </div>
        
        <footer style="margin-top: 3rem; text-align: center; color: var(--text-dim); font-size: 0.8rem;">
            Generated by Git Stats Infographic Engine
        </footer>
    </div>
</body>
</html>
    """
    return html_template

if __name__ == "__main__":
    print("🔍 Scanning codebase...")
    data = get_stats()
    html = generate_html(data)
    
    output_file = "stats.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✨ Infographic generated successfully: {output_file}")