import os
import html
import math
import sys

def scan_directory(root_dir):
    """
    Recursively scans directory to collect statistics.
    """
    stats = {
        'files_by_ext': {},
        'lines_by_ext': {},
        'total_files': 0,
        'total_lines': 0,
        'total_size': 0,
        'max_depth': 0,
        'largest_files': [] # (path, size, lines)
    }

    # Directories to ignore to keep stats relevant
    ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', 'env', 
                   '.idea', '.vscode', 'dist', 'build', 'target', 'bin', 'obj'}

    print(f"Scanning: {root_dir}")

    for root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        # Calculate directory depth relative to root
        rel_path = os.path.relpath(root, root_dir)
        if rel_path == '.':
            depth = 0
        else:
            depth = rel_path.count(os.sep) + 1
        stats['max_depth'] = max(stats['max_depth'], depth)

        for file in files:
            file_path = os.path.join(root, file)
            
            # Determine extension/type
            _, ext = os.path.splitext(file)
            if not ext:
                if file.startswith('.'):
                    ext = file
                else:
                    ext = 'no_ext'
            else:
                ext = ext.lstrip('.').lower()
            
            try:
                size = os.path.getsize(file_path)
                stats['total_size'] += size
                stats['total_files'] += 1
                
                # Count lines (heuristic to avoid binary files)
                lines = 0
                is_binary = False
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # Read first chunk to check for null bytes (binary indicator)
                        chunk = f.read(8192)
                        if '\0' in chunk:
                            is_binary = True
                        else:
                            lines = chunk.count('\n')
                            # Read the rest of the file
                            for chunk in iter(lambda: f.read(8192), ''):
                                lines += chunk.count('\n')
                            
                            # Handle single line files without newline at EOF
                            if size > 0 and lines == 0:
                                lines = 1
                except Exception:
                    is_binary = True

                if is_binary:
                    lines = 0

                stats['total_lines'] += lines
                
                # Aggregate stats
                stats['files_by_ext'][ext] = stats['files_by_ext'].get(ext, 0) + 1
                stats['lines_by_ext'][ext] = stats['lines_by_ext'].get(ext, 0) + lines
                
                stats['largest_files'].append({
                    'path': os.path.relpath(file_path, root_dir),
                    'size': size,
                    'lines': lines
                })

            except OSError:
                # Skip files we can't read
                continue

    # Process largest files (Top 10)
    stats['largest_files'].sort(key=lambda x: x['size'], reverse=True)
    stats['largest_files'] = stats['largest_files'][:10]
    
    return stats

def generate_pie_chart(data):
    """
    Generates an inline SVG pie chart for file extensions.
    """
    total = sum(data.values())
    if total == 0:
        return '<div style="text-align:center; padding: 20px; color: #666;">No data available</div>'
    
    # Sort and group small slices into "Other"
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_data) > 7:
        others = sorted_data[7:]
        sorted_data = sorted_data[:7]
        other_val = sum(x[1] for x in others)
        sorted_data.append(('other', other_val))
    
    svg_parts = []
    cx, cy, r = 100, 100, 80
    current_angle = 0
    
    # Vibrant palette
    colors = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
        "#FFEEAD", "#D4A5A5", "#9B59B6", "#3498DB", "#95A5A6"
    ]
    
    legend_items = []

    for i, (label, value) in enumerate(sorted_data):
        percentage = value / total
        angle = percentage * 2 * math.pi
        
        # Calculate coordinates
        x1 = cx + r * math.cos(current_angle)
        y1 = cy + r * math.sin(current_angle)
        x2 = cx + r * math.cos(current_angle + angle)
        y2 = cy + r * math.sin(current_angle + angle)
        
        # SVG Path command for arc
        large_arc_flag = 1 if angle > math.pi else 0
        
        # Handle 100% case (circle)
        if percentage > 0.999:
            path_d = f"M {cx} {cy - r} A {r} {r} 0 1 1 {cx} {cy + r} A {r} {r} 0 1 1 {cx} {cy - r}"
        else:
            path_d = f"M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc_flag} 1 {x2} {y2} Z"
        
        color = colors[i % len(colors)]
        svg_parts.append(f'<path d="{path_d}" fill="{color}" stroke="#2d2d2d" stroke-width="2" />')
        
        # Legend
        pct_label = f"{percentage*100:.1f}%"
        legend_items.append(f'''
            <div class="legend-item">
                <span class="color-dot" style="background-color: {color}"></span>
                <span class="label">{label} <span class="dim">({value})</span></span>
            </div>
        ''')
        
        current_angle += angle

    return f'''
    <div class="chart-container">
        <svg viewBox="0 0 200 200" class="pie-chart">
            {"".join(svg_parts)}
        </svg>
        <div class="legend">
            {"".join(legend_items)}
        </div>
    </div>
    '''

def generate_bar_chart(data):
    """
    Generates HTML/CSS bar chart for lines of code.
    """
    if not data:
        return '<div style="text-align:center; padding: 20px; color: #666;">No data available</div>'
        
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:8]
    if not sorted_data:
        return ""
        
    max_val = sorted_data[0][1] if sorted_data[0][1] > 0 else 1
    
    bars = []
    colors = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
        "#FFEEAD", "#D4A5A5", "#9B59B6", "#3498DB"
    ]
    
    for i, (label, value) in enumerate(sorted_data):
        pct = (value / max_val) * 100
        color = colors[i % len(colors)]
        bars.append(f'''
        <div class="bar-row">
            <div class="bar-header">
                <span class="bar-label">{label}</span>
                <span class="bar-value-text">{value:,} lines</span>
            </div>
            <div class="bar-track">
                <div class="bar-fill" style="width: {pct}%; background-color: {color};"></div>
            </div>
        </div>
        ''')
        
    return f'''
    <div class="bar-chart">
        {"".join(bars)}
    </div>
    '''

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def generate_html(stats):
    pie_chart = generate_pie_chart(stats['files_by_ext'])
    bar_chart = generate_bar_chart(stats['lines_by_ext'])
    
    largest_files_rows = ""
    for f in stats['largest_files']:
        largest_files_rows += f'''
        <tr>
            <td class="path" title="{f['path']}">{f['path']}</td>
            <td>{format_size(f['size'])}</td>
            <td>{f['lines']:,}</td>
        </tr>
        '''

    css = """
        :root {
            --bg-color: #1a1a1a;
            --card-bg: #2d2d2d;
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --accent: #4ECDC4;
            --border: #404040;
        }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 40px 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 50px;
        }
        h1 {
            font-size: 3rem;
            margin: 0 0 10px 0;
            background: linear-gradient(135deg, #FF6B6B, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }
        .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
        
        /* Summary Cards */
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .card {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            border: 1px solid var(--border);
        }
        .metric-card {
            text-align: center;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-5px);
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--accent);
            margin-bottom: 5px;
        }
        .metric-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 600;
        }
        
        /* Charts Area */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        h2 {
            border-bottom: 1px solid var(--border);
            padding-bottom: 15px;
            margin-top: 0;
            margin-bottom: 25px;
            font-size: 1.4rem;
            color: var(--text-primary);
            font-weight: 600;
        }

        /* Pie Chart */
        .chart-container {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 30px;
        }
        .pie-chart {
            width: 220px;
            height: 220px;
            transform: rotate(-90deg);
            filter: drop-shadow(0 0 10px rgba(0,0,0,0.3));
        }
        .legend {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            font-size: 0.95rem;
        }
        .color-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
            box-shadow: 0 0 5px rgba(0,0,0,0.5);
        }
        .dim {
            color: var(--text-secondary);
            font-size: 0.85em;
            margin-left: 5px;
        }

        /* Bar Chart */
        .bar-chart {
            padding: 10px 0;
        }
        .bar-row {
            margin-bottom: 15px;
        }
        .bar-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 0.95rem;
        }
        .bar-track {
            background-color: #383838;
            height: 12px;
            border-radius: 6px;
            overflow: hidden;
        }
        .bar-fill {
            height: 100%;
            border-radius: 6px;
            width: 0;
            transition: width 1.5s cubic-bezier(0.22, 1, 0.36, 1);
        }
        .bar-value-text {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        /* Table */
        .table-container {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
        }
        th, td {
            text-align: left;
            padding: 15px;
            border-bottom: 1px solid var(--border);
        }
        th {
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 1px;
        }
        tr:last-child td {
            border-bottom: none;
        }
        .path {
            font-family: 'Consolas', 'Monaco', monospace;
            color: var(--accent);
            max-width: 400px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
            .chart-container {
                flex-direction: column;
            }
            .path {
                max-width: 200px;
            }
        }
    """

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        {css}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <div class="subtitle">Scanned: {html.escape(os.getcwd())}</div>
        </header>

        <div class="summary-grid">
            <div class="card metric-card">
                <div class="metric-value">{stats['total_files']:,}</div>
                <div class="metric-label">Total Files</div>
            </div>
            <div class="card metric-card">
                <div class="metric-value">{stats['total_lines']:,}</div>
                <div class="metric-label">Total Lines</div>
            </div>
            <div class="card metric-card">
                <div class="metric-value">{format_size(stats['total_size'])}</div>
                <div class="metric-label">Total Size</div>
            </div>
            <div class="card metric-card">
                <div class="metric-value">{stats['max_depth']}</div>
                <div class="metric-label">Max Depth</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="card">
                <h2>File Types Distribution</h2>
                {pie_chart}
            </div>
            <div class="card">
                <h2>Lines of Code by Language</h2>
                {bar_chart}
            </div>
        </div>

        <div class="card">
            <h2>Largest Files</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Path</th>
                            <th>Size</th>
                            <th>Lines</th>
                        </tr>
                    </thead>
                    <tbody>
                        {largest_files_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Animate bars on load
        document.addEventListener('DOMContentLoaded', () => {{
            requestAnimationFrame(() => {{
                const bars = document.querySelectorAll('.bar-fill');
                bars.forEach(bar => {{
                    // Trigger reflow to ensure transition happens
                    const width = bar.style.width;
                    bar.style.width = '0%';
                    requestAnimationFrame(() => {{
                        bar.style.width = width;
                    }});
                }});
            }});
        }});
    </script>
</body>
</html>
    '''
    
    output_path = os.path.abspath('stats.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nSuccess! Infographic generated at:\n{output_path}")

if __name__ == "__main__":
    current_dir = os.getcwd()
    stats = scan_directory(current_dir)
    generate_html(stats)