import os
import sys
import math
import html
from collections import Counter
from datetime import datetime

# --- Configuration ---
IGNORE_DIRS = {
    '.git', '__pycache__', 'node_modules', 'venv', '.env', 
    '.idea', '.vscode', 'dist', 'build', 'target', 'bin', 'obj'
}
IGNORE_EXTS = {
    '.pyc', '.o', '.obj', '.dll', '.so', '.exe', '.class', 
    '.jpg', '.png', '.gif', '.ico', '.svg', '.woff', '.woff2', '.ttf', '.eot',
    '.zip', '.tar', '.gz', '.7z', '.rar', '.pdf', '.db', '.sqlite'
}
# Files that are definitely code/text
TEXT_EXTS = {
    '.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.h', '.hpp', 
    '.rs', '.go', '.ts', '.json', '.md', '.txt', '.xml', '.yaml', '.yml', 
    '.sh', '.bat', '.ps1', '.rb', '.php', '.sql', '.jsx', '.tsx', '.vue'
}
OUTPUT_FILE = "stats.html"

# --- Vibrant Color Palette ---
COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFEEAD", "#D4A5A5", 
    "#9B59B6", "#3498DB", "#E67E22", "#2ECC71", "#F1C40F", 
    "#E74C3C", "#1ABC9C", "#8E44AD", "#34495E", "#16A085"
]

def is_text_file(filepath):
    """Determine if a file is text based on extension or content inspection."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in TEXT_EXTS:
        return True
    
    # Fallback: try reading first 1024 bytes
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
            return True
    except (UnicodeDecodeError, OSError):
        return False

def scan_directory(root_dir):
    """Recursively scan directory and collect statistics."""
    stats = {
        'total_files': 0,
        'total_lines': 0,
        'total_size': 0,
        'max_depth': 0,
        'extensions': Counter(),
        'files': [] # List of {path, size, lines, ext}
    }

    abs_root = os.path.abspath(root_dir)
    start_depth = abs_root.count(os.sep)

    print(f"Scanning {abs_root}...")

    for root, dirs, files in os.walk(abs_root):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        current_depth = root.count(os.sep) - start_depth
        if current_depth > stats['max_depth']:
            stats['max_depth'] = current_depth

        for file in files:
            if file == OUTPUT_FILE:
                continue
                
            filepath = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            
            if ext in IGNORE_EXTS:
                continue

            try:
                size = os.path.getsize(filepath)
                stats['total_size'] += size
                stats['total_files'] += 1
                
                # Normalize extension for grouping (e.g., makefile -> no_ext)
                display_ext = ext if ext else 'No Extension'
                stats['extensions'][display_ext] += 1
                
                lines = 0
                if is_text_file(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = sum(1 for _ in f)
                        stats['total_lines'] += lines
                    except OSError:
                        pass
                
                rel_path = os.path.relpath(filepath, abs_root)
                stats['files'].append({
                    'path': rel_path,
                    'size': size,
                    'lines': lines,
                    'ext': display_ext
                })
            except OSError:
                continue
                
    return stats

def generate_pie_chart_svg(data):
    """Generate an inline SVG pie chart from data dictionary."""
    # data: list of (label, count)
    total = sum(item[1] for item in data)
    if total == 0:
        return '<svg viewBox="-1 -1 2 2"><circle cx="0" cy="0" r="1" fill="#333"/></svg>', []
    
    # Sort and group small slices
    data.sort(key=lambda x: x[1], reverse=True)
    
    chart_data = data[:8]
    if len(data) > 8:
        others_count = sum(item[1] for item in data[8:])
        chart_data.append(('Others', others_count))
    
    paths = []
    legend_items = []
    start_angle = 0
    cx, cy, r = 0, 0, 1
    
    for i, (label, count) in enumerate(chart_data):
        fraction = count / total
        end_angle = start_angle + fraction * 2 * math.pi
        
        # Calculate SVG path coordinates
        x1 = cx + r * math.cos(start_angle)
        y1 = cy + r * math.sin(start_angle)
        x2 = cx + r * math.cos(end_angle)
        y2 = cy + r * math.sin(end_angle)
        
        large_arc = 1 if fraction > 0.5 else 0
        color = COLORS[i % len(COLORS)]
        
        if fraction > 0.9999:
            path = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" />'
        else:
            path = f'<path d="M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z" fill="{color}" stroke="#1e1e1e" stroke-width="0.05" />'
        
        paths.append(path)
        
        legend_items.append({
            'label': label,
            'count': count,
            'color': color,
            'pct': f"{fraction*100:.1f}%"
        })
        
        start_angle = end_angle

    svg = f'<svg viewBox="-1.1 -1.1 2.2 2.2" class="pie-chart">{"".join(paths)}</svg>'
    return svg, legend_items

def generate_bar_chart_html(files):
    """Generate HTML for bar chart of largest files."""
    # Top 10 files by lines of code
    text_files = [f for f in files if f['lines'] > 0]
    sorted_files = sorted(text_files, key=lambda x: x['lines'], reverse=True)[:10]
    
    if not sorted_files:
        return '<div class="empty-state">No code files found to analyze.</div>'
        
    max_val = sorted_files[0]['lines']
    
    bars = []
    for i, f in enumerate(sorted_files):
        width_pct = (f['lines'] / max_val) * 100
        color = COLORS[i % len(COLORS)]
        
        bars.append(f'''
        <div class="bar-row">
            <div class="bar-info">
                <span class="bar-label" title="{html.escape(f['path'])}">{html.escape(f['path'])}</span>
                <span class="bar-val-text">{f['lines']:,} LOC</span>
            </div>
            <div class="bar-track">
                <div class="bar-fill" style="width: {width_pct}%; background-color: {color};"></div>
            </div>
        </div>
        ''')
        
    return f'<div class="bar-chart">{"".join(bars)}</div>'

def generate_html(stats):
    """Construct the final HTML file."""
    # Process Pie Chart Data
    ext_counts = list(stats['extensions'].items())
    pie_svg, pie_legend = generate_pie_chart_svg(ext_counts)
    
    # Process Bar Chart Data
    bar_html = generate_bar_chart_html(stats['files'])
    
    # Meta
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_size_mb = stats['total_size'] / (1024 * 1024)
    cwd = os.getcwd()
    
    # Legend HTML
    legend_html = "".join([
        f'''<div class="legend-item">
            <span class="dot" style="background-color:{item['color']}"></span>
            <span class="l-label">{html.escape(item['label'])}</span>
            <span class="l-val">{item['pct']}</span>
           </div>''' 
        for item in pie_legend
    ])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        :root {{
            --bg-color: #121212;
            --card-bg: #1E1E1E;
            --text-primary: #E0E0E0;
            --text-secondary: #A0A0A0;
            --accent: #4ECDC4;
            --border: #333;
        }}
        body {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 2rem;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        /* Header */
        header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1rem;
        }}
        h1 {{
            margin: 0;
            font-size: 2.2rem;
            background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .meta {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            text-align: right;
        }}
        
        /* KPI Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        .kpi-card {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            text-align: center;
            border: 1px solid var(--border);
            transition: transform 0.2s;
        }}
        .kpi-card:hover {{
            transform: translateY(-2px);
            border-color: var(--accent);
        }}
        .kpi-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 0.5rem;
        }}
        .kpi-label {{
            color: var(--text-secondary);
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 1px;
        }}
        
        /* Dashboard Grid */
        .dash-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 1.5rem;
        }}
        .card {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }}
        .card h2 {{
            margin-top: 0;
            margin-bottom: 1.5rem;
            font-size: 1.25rem;
            border-left: 4px solid var(--accent);
            padding-left: 1rem;
        }}
        
        /* Pie Chart */
        .pie-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 2rem;
        }}
        .pie-wrapper {{
            width: 220px;
            height: 220px;
        }}
        .pie-chart {{
            width: 100%;
            height: 100%;
            transform: rotate(-90deg);
        }}
        .legend {{
            flex: 1;
            min-width: 200px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            padding: 4px 8px;
            border-radius: 4px;
            background: rgba(255,255,255,0.03);
        }}
        .dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        .l-label {{ flex: 1; }}
        .l-val {{ font-weight: bold; color: var(--text-primary); }}
        
        /* Bar Chart */
        .bar-chart {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        .bar-row {{
            width: 100%;
        }}
        .bar-info {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.25rem;
            font-size: 0.9rem;
        }}
        .bar-label {{
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 70%;
        }}
        .bar-val-text {{
            color: var(--text-secondary);
            font-family: monospace;
        }}
        .bar-track {{
            height: 12px;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            overflow: hidden;
        }}
        .bar-fill {{
            height: 100%;
            border-radius: 6px;
            transition: width 0.5s ease-out;
        }}
        
        .empty-state {{
            text-align: center;
            color: var(--text-secondary);
            padding: 2rem;
            font-style: italic;
        }}
        
        footer {{
            margin-top: 3rem;
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.8rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
        }}
        
        @media (max-width: 768px) {{
            .dash-grid {{ grid-template-columns: 1fr; }}
            header {{ flex-direction: column; align-items: flex-start; }}
            .meta {{ text-align: left; margin-top: 0.5rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <div class="meta">
                <div>Generated: {timestamp}</div>
                <div>Path: {html.escape(cwd)}</div>
            </div>
        </header>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-value">{stats['total_files']:,}</div>
                <div class="kpi-label">Total Files</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{stats['total_lines']:,}</div>
                <div class="kpi-label">Lines of Code</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{total_size_mb:.2f} MB</div>
                <div class="kpi-label">Total Size</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{stats['max_depth']}</div>
                <div class="kpi-label">Max Depth</div>
            </div>
        </div>

        <div class="dash-grid">
            <div class="card">
                <h2>File Extension Breakdown</h2>
                <div class="pie-container">
                    <div class="pie-wrapper">
                        {pie_svg}
                    </div>
                    <div class="legend">
                        {legend_html}
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Largest Files (by Lines of Code)</h2>
                {bar_html}
            </div>
        </div>

        <footer>
            Generated by Python Standard Library Script
        </footer>
    </div>
</body>
</html>
"""

def main():
    # Scan
    stats = scan_directory(".")
    
    # Generate
    print("Generating report...")
    html_content = generate_html(stats)
    
    # Save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Done! Open {OUTPUT_FILE} to view the infographic.")

if __name__ == "__main__":
    main()