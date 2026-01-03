import os
import json
import math
from collections import Counter

def get_stats():
    stats = {
        'extensions': Counter(),
        'total_lines': 0,
        'file_count': 0,
        'max_depth': 0,
        'largest_files': [],
        'dir_structure': {}
    }
    
    root_dir = os.getcwd()
    
    for root, dirs, files in os.walk(root_dir):
        # Calculate depth
        rel_path = os.path.relpath(root, root_dir)
        depth = 0 if rel_path == "." else rel_path.count(os.sep) + 1
        stats['max_depth'] = max(stats['max_depth'], depth)
        
        # Skip hidden directories like .git
        if '.git' in dirs:
            dirs.remove('.git')
            
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower() or 'no-ext'
            
            try:
                file_size = os.path.getsize(file_path)
                stats['file_count'] += 1
                stats['extensions'][ext] += 1
                
                # Try to read lines (skip binary files)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                        stats['total_lines'] += lines
                except:
                    lines = 0
                
                stats['largest_files'].append({
                    'name': os.path.relpath(file_path, root_dir),
                    'size': file_size,
                    'lines': lines
                })
            except (PermissionError, OSError):
                continue

    # Sort largest files and keep top 10
    stats['largest_files'].sort(key=lambda x: x['size'], reverse=True)
    stats['largest_files'] = stats['largest_files'][:10]
    
    return stats

def generate_html(stats):
    # Prepare Data for Charts
    ext_labels = list(stats['extensions'].keys())
    ext_values = list(stats['extensions'].values())
    
    # Colors for charts
    colors = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#2ecc71", "#e74c3c", "#34495e", "#9b59b6"]

    # SVG Pie Chart Logic
    total_ext_count = sum(ext_values)
    pie_paths = ""
    current_angle = 0
    
    sorted_ext = sorted(stats['extensions'].items(), key=lambda x: x[1], reverse=True)[:8]
    
    for i, (label, val) in enumerate(sorted_ext):
        percent = val / total_ext_count
        angle = percent * 360
        
        # SVG Arc coordinates
        x1 = 50 + 40 * math.cos(math.radians(current_angle - 90))
        y1 = 50 + 40 * math.sin(math.radians(current_angle - 90))
        
        current_angle += angle
        
        x2 = 50 + 40 * math.cos(math.radians(current_angle - 90))
        y2 = 50 + 40 * math.sin(math.radians(current_angle - 90))
        
        large_arc = 1 if angle > 180 else 0
        
        color = colors[i % len(colors)]
        pie_paths += f'<path d="M 50 50 L {x1} {y1} A 40 40 0 {large_arc} 1 {x2} {y2} Z" fill="{color}"><title>{label}: {val} files</title></path>'

    # SVG Bar Chart Logic (Largest Files)
    bar_html = ""
    max_size = max([f['size'] for f in stats['largest_files']]) if stats['largest_files'] else 1
    for i, f in enumerate(stats['largest_files']):
        width = (f['size'] / max_size) * 100
        color = colors[i % len(colors)]
        name = f['name'] if len(f['name']) < 30 else "..." + f['name'][-27:]
        bar_html += f'''
        <div class="bar-row">
            <div class="bar-label">{name}</div>
            <div class="bar-container">
                <div class="bar-fill" style="width: {width}%; background: {color};"></div>
            </div>
            <div class="bar-value">{f['size'] // 1024} KB</div>
        </div>
        '''

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
            --text: #f8fafc;
            --accent: #38bdf8;
            --secondary: #94a3b8;
        }}
        body {{
            background-color: var(--bg);
            color: var(--text);
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
            border-bottom: 2px solid var(--card-bg);
            padding-bottom: 1rem;
        }}
        header h1 {{
            margin: 0;
            font-size: 2.5rem;
            letter-spacing: -1px;
            background: linear-gradient(90deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        .stat-card {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255,255,255,0.05);
        }}
        .stat-card h3 {{
            margin: 0;
            color: var(--secondary);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .stat-card .value {{
            font-size: 2rem;
            font-weight: bold;
            margin-top: 0.5rem;
            color: var(--accent);
        }}
        .charts-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }}
        .chart-card {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 12px;
            min-height: 400px;
        }}
        .chart-card h2 {{
            font-size: 1.25rem;
            margin-bottom: 1.5rem;
            color: var(--secondary);
        }}
        .pie-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: 250px;
        }}
        .legend {{
            margin-top: 1rem;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 0.8rem;
        }}
        .dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .bar-row {{
            margin-bottom: 1rem;
        }}
        .bar-label {{
            font-size: 0.75rem;
            margin-bottom: 4px;
            color: var(--secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .bar-container {{
            background: #334155;
            height: 12px;
            border-radius: 6px;
            overflow: hidden;
            display: flex;
        }}
        .bar-fill {{
            height: 100%;
            transition: width 1s ease-in-out;
        }}
        .bar-value {{
            font-size: 0.7rem;
            text-align: right;
            margin-top: 2px;
            color: var(--secondary);
        }}
        @media (max-width: 768px) {{
            .charts-row {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p style="color: var(--secondary)">System Scan Analysis</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Files</h3>
                <div class="value">{stats['file_count']}</div>
            </div>
            <div class="stat-card">
                <h3>Lines of Code</h3>
                <div class="value">{stats['total_lines']:,}</div>
            </div>
            <div class="stat-card">
                <h3>Max Depth</h3>
                <div class="value">{stats['max_depth']}</div>
            </div>
            <div class="stat-card">
                <h3>Extensions</h3>
                <div class="value">{len(stats['extensions'])}</div>
            </div>
        </div>

        <div class="charts-row">
            <div class="chart-card">
                <h2>File Composition</h2>
                <div class="pie-container">
                    <svg viewBox="0 0 100 100" width="200" height="200">
                        {pie_paths}
                    </svg>
                </div>
                <div class="legend">
                    {"".join([f'<div class="legend-item"><span class="dot" style="background:{colors[i%len(colors)]}"></span>{ext} ({count})</div>' for i, (ext, count) in enumerate(sorted_ext)])}
                </div>
            </div>
            <div class="chart-card">
                <h2>Largest Files (By Size)</h2>
                <div style="margin-top: 1rem;">
                    {bar_html}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    """
    return html_template

if __name__ == "__main__":
    print("Scanning directory...")
    data = get_stats()
    html_content = generate_html(data)
    
    output_file = "stats.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Success! Infographic generated at: {os.path.abspath(output_file)}")