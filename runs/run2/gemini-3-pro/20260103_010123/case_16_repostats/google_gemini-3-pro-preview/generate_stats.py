import os
import math
import mimetypes
import datetime

# Configuration
IGNORED_DIRS = {
    '.git', '__pycache__', 'node_modules', 'venv', 'env', '.idea', '.vscode', 
    'dist', 'build', 'target', 'bin', 'obj', '.next', '.nuxt'
}
IGNORED_EXTS = {
    '.pyc', '.o', '.obj', '.dll', '.so', '.exe', '.class', '.png', '.jpg', 
    '.jpeg', '.gif', '.ico', '.zip', '.tar', '.gz', '.pdf', '.woff', '.woff2'
}
# Vibrant colors for dark mode
COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEEAD", 
    "#D4A5A5", "#9B59B6", "#3498DB", "#E67E22", "#2ECC71"
]

def get_file_stats(filepath):
    """
    Returns (size, line_count) for a file.
    Line count is 0 if file appears binary or unreadable.
    """
    try:
        size = os.path.getsize(filepath)
    except OSError:
        return 0, 0

    # Skip line counting for obvious binaries based on extension
    _, ext = os.path.splitext(filepath)
    if ext.lower() in IGNORED_EXTS:
        return size, 0

    lines = 0
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = sum(1 for _ in f)
    except UnicodeDecodeError:
        try:
            # Fallback for some legacy encodings
            with open(filepath, 'r', encoding='latin-1') as f:
                lines = sum(1 for _ in f)
        except Exception:
            # Likely binary
            pass
    except Exception:
        pass
        
    return size, lines

def scan_directory(root_path):
    stats = {
        'total_files': 0,
        'total_lines': 0,
        'total_size': 0,
        'max_depth': 0,
        'extensions': {},  # ext: {'count': int, 'lines': int, 'size': int}
        'largest_files': [], # list of dicts
        'depth_map': {} # depth: count
    }

    root_abs = os.path.abspath(root_path)

    for root, dirs, files in os.walk(root_path):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        
        # Calculate depth
        rel_path = os.path.relpath(root, root_path)
        if rel_path == '.':
            depth = 0
        else:
            depth = rel_path.count(os.sep) + 1
        
        stats['max_depth'] = max(stats['max_depth'], depth)
        stats['depth_map'][depth] = stats['depth_map'].get(depth, 0) + len(files)

        for file in files:
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file)
            ext = ext.lower() or 'no-ext'
            
            size, lines = get_file_stats(file_path)
            
            # Update totals
            stats['total_files'] += 1
            stats['total_lines'] += lines
            stats['total_size'] += size
            
            # Update extension stats
            if ext not in stats['extensions']:
                stats['extensions'][ext] = {'count': 0, 'lines': 0, 'size': 0}
            stats['extensions'][ext]['count'] += 1
            stats['extensions'][ext]['lines'] += lines
            stats['extensions'][ext]['size'] += size
            
            # Track largest files
            stats['largest_files'].append({
                'path': os.path.relpath(file_path, root_path),
                'size': size,
                'lines': lines,
                'ext': ext
            })

    # Sort largest files and keep top 10
    stats['largest_files'].sort(key=lambda x: x['size'], reverse=True)
    stats['largest_files'] = stats['largest_files'][:10]
    
    return stats

def bytes_to_human(n):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(n) < 1024.0:
            return f"{n:3.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TB"

def generate_pie_chart_svg(data, size=200):
    """
    data: list of tuples (label, value, color)
    """
    total = sum(x[1] for x in data)
    if total == 0:
        return '<svg width="{0}" height="{0}"><circle cx="{1}" cy="{1}" r="{1}" fill="#333"/></svg>'.format(size, size/2)
    
    cx = cy = size / 2
    r = size / 2
    
    paths = []
    current_angle = 0
    
    # Legend data
    legend_items = []

    for label, value, color in data:
        percentage = value / total
        angle = percentage * 2 * math.pi
        
        x1 = cx + r * math.cos(current_angle)
        y1 = cy + r * math.sin(current_angle)
        x2 = cx + r * math.cos(current_angle + angle)
        y2 = cy + r * math.sin(current_angle + angle)
        
        large_arc = 1 if angle > math.pi else 0
        
        path_d = f"M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z"
        paths.append(f'<path d="{path_d}" fill="{color}" stroke="#1e1e1e" stroke-width="2"><title>{label}: {value} ({percentage:.1%})</title></path>')
        
        legend_items.append((label, value, color, percentage))
        
        current_angle += angle

    svg_chart = f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">' + "".join(paths) + '</svg>'
    
    return svg_chart, legend_items

def generate_bar_chart_svg(data, width=400, height=200):
    """
    data: list of tuples (label, value)
    """
    if not data:
        return ""
        
    max_val = max(x[1] for x in data) if data else 1
    bar_width = (width / len(data)) * 0.8
    gap = (width / len(data)) * 0.2
    
    bars = []
    for i, (label, value) in enumerate(data):
        bar_h = (value / max_val) * (height - 30) # leave room for text
        x = i * (bar_width + gap) + gap/2
        y = height - bar_h - 20
        color = COLORS[i % len(COLORS)]
        
        rect = f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_h}" fill="{color}" rx="4" />'
        text = f'<text x="{x + bar_width/2}" y="{height}" fill="#aaa" font-size="10" text-anchor="middle">{label}</text>'
        val_text = f'<text x="{x + bar_width/2}" y="{y - 5}" fill="#fff" font-size="10" text-anchor="middle">{value}</text>'
        
        bars.append(rect + text + val_text)
        
    return f'<svg width="100%" height="100%" viewBox="0 0 {width} {height}">' + "".join(bars) + '</svg>'

def create_html(stats):
    # Prepare data for charts
    
    # 1. File Count by Extension (Pie Chart)
    ext_counts = [(k, v['count']) for k, v in stats['extensions'].items()]
    ext_counts.sort(key=lambda x: x[1], reverse=True)
    top_exts = ext_counts[:8]
    other_count = sum(x[1] for x in ext_counts[8:])
    if other_count > 0:
        top_exts.append(('Other', other_count))
    
    pie_data = []
    for i, (label, val) in enumerate(top_exts):
        pie_data.append((label, val, COLORS[i % len(COLORS)]))
        
    pie_svg, pie_legend = generate_pie_chart_svg(pie_data, size=250)
    
    # 2. Lines of Code by Extension (Bar Chart)
    line_counts = [(k, v['lines']) for k, v in stats['extensions'].items() if v['lines'] > 0]
    line_counts.sort(key=lambda x: x[1], reverse=True)
    top_lines = line_counts[:6] # Top 6 languages by lines
    
    bar_svg = generate_bar_chart_svg(top_lines)

    # 3. Depth Chart (Simple Bar)
    depth_data = sorted(stats['depth_map'].items())
    # Limit depth display if too wide
    if len(depth_data) > 15:
        depth_data = depth_data[:15]
    depth_svg = generate_bar_chart_svg([(str(d), c) for d, c in depth_data], width=400, height=150)

    # HTML Template
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        :root {{
            --bg-dark: #121212;
            --bg-card: #1e1e1e;
            --text-main: #e0e0e0;
            --text-muted: #a0a0a0;
            --accent: #bb86fc;
            --border: #333;
        }}
        body {{
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }}
        h1 {{
            font-size: 2.5rem;
            margin: 0;
            background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
        
        /* Grid Layout */
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .card {{
            background-color: var(--bg-card);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: transform 0.2s;
        }}
        .card:hover {{
            transform: translateY(-2px);
        }}
        
        .card.full-width {{
            grid-column: 1 / -1;
        }}
        
        .card h2 {{
            margin-top: 0;
            font-size: 1.2rem;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        /* Summary Metrics */
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }}
        @media (max-width: 768px) {{
            .metric-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        .metric {{
            text-align: center;
        }}
        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--accent);
            display: block;
        }}
        .metric-label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Charts */
        .chart-flex {{
            display: flex;
            align-items: center;
            justify-content: space-around;
            flex-wrap: wrap;
        }}
        .legend {{
            font-size: 0.9rem;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }}
        .color-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
            display: inline-block;
        }}
        
        /* Table */
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        th {{
            text-align: left;
            color: var(--accent);
            padding: 12px;
            border-bottom: 1px solid var(--border);
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #2a2a2a;
        }}
        tr:last-child td {{ border-bottom: none; }}
        .path-cell {{
            font-family: monospace;
            color: #4ECDC4;
            max-width: 300px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .footer {{
            text-align: center;
            color: var(--text-muted);
            margin-top: 40px;
            font-size: 0.8rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <div class="subtitle">Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
        </header>
        
        <!-- Summary Cards -->
        <div class="card full-width">
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">{stats['total_files']:,}</span>
                    <span class="metric-label">Total Files</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{stats['total_lines']:,}</span>
                    <span class="metric-label">Total Lines</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{bytes_to_human(stats['total_size'])}</span>
                    <span class="metric-label">Total Size</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{stats['max_depth']}</span>
                    <span class="metric-label">Max Depth</span>
                </div>
            </div>
        </div>
        
        <div class="dashboard">
            <!-- File Types Pie Chart -->
            <div class="card">
                <h2>File Types Distribution</h2>
                <div class="chart-flex">
                    {pie_svg}
                    <div class="legend">
                        {''.join(f'<div class="legend-item"><span class="color-dot" style="background:{item[2]}"></span>{item[0]} ({item[3]:.1%})</div>' for item in pie_legend)}
                    </div>
                </div>
            </div>
            
            <!-- Lines by Language Bar Chart -->
            <div class="card">
                <h2>Lines of Code by Type</h2>
                <div style="height: 250px;">
                    {bar_svg if top_lines else '<p style="text-align:center; padding-top:100px; color:#555;">No text files found</p>'}
                </div>
            </div>
            
             <!-- Directory Depth -->
            <div class="card">
                <h2>Files by Directory Depth</h2>
                <div style="height: 200px;">
                    {depth_svg}
                </div>
            </div>
        </div>
        
        <!-- Largest Files Table -->
        <div class="card full-width">
            <h2>Largest Files</h2>
            <table>
                <thead>
                    <tr>
                        <th>Path</th>
                        <th>Extension</th>
                        <th>Lines</th>
                        <th>Size</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'<tr><td class="path-cell" title="{f["path"]}">{f["path"]}</td><td>{f["ext"]}</td><td>{f["lines"]:,}</td><td>{bytes_to_human(f["size"])}</td></tr>' for f in stats['largest_files'])}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            Generated by Python Standard Library
        </div>
    </div>
</body>
</html>
"""
    
    with open('stats.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Successfully generated stats.html for {stats['total_files']} files.")

if __name__ == "__main__":
    print("Scanning directory...")
    current_dir = os.getcwd()
    stats = scan_directory(current_dir)
    create_html(stats)