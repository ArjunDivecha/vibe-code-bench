import os
import math
import html
import mimetypes

def is_text_file(filepath):
    """Check if a file is text-based to count lines."""
    try:
        # Check first 1024 bytes for null character
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return False
            
        # Try decoding as utf-8
        with open(filepath, 'r', encoding='utf-8') as f:
            for _ in range(5):
                f.readline()
        return True
    except Exception:
        return False

def count_lines(filepath):
    """Count lines in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except:
        return 0

def scan_directory(root_path):
    stats = {
        'total_files': 0,
        'total_lines': 0,
        'total_size': 0,
        'extensions': {},
        'largest_files': [], # (path, size, lines)
        'max_depth': 0,
        'dirs_scanned': 0
    }
    
    ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.env', 'dist', 'build', '.idea', '.vscode'}
    
    abs_root = os.path.abspath(root_path)

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filter directories
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        
        rel_path = os.path.relpath(dirpath, root_path)
        if rel_path == '.':
            depth = 0
        else:
            depth = rel_path.count(os.sep) + 1
        
        stats['max_depth'] = max(stats['max_depth'], depth)
        stats['dirs_scanned'] += 1

        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            stats['total_files'] += 1
            
            # Extension
            _, ext = os.path.splitext(filename)
            ext = ext.lower() if ext else '(no ext)'
            stats['extensions'][ext] = stats['extensions'].get(ext, 0) + 1
            
            # Size
            try:
                size = os.path.getsize(filepath)
                stats['total_size'] += size
                
                # Lines (only for text files)
                lines = 0
                if is_text_file(filepath):
                    lines = count_lines(filepath)
                    stats['total_lines'] += lines
                
                stats['largest_files'].append({
                    'name': filename,
                    'path': os.path.relpath(filepath, root_path),
                    'size': size,
                    'lines': lines,
                    'ext': ext
                })
            except OSError:
                pass

    # Sort largest files
    stats['largest_files'].sort(key=lambda x: x['size'], reverse=True)
    stats['largest_files'] = stats['largest_files'][:10]
    
    return stats

def get_color(index, total):
    """Generate a vibrant color based on index."""
    colors = [
        '#FF6B6B', '#4ECDC4', '#FFE66D', '#FF9F43', '#54A0FF', 
        '#5F27CD', '#FF9FF3', '#00D2D3', '#1DD1A1', '#FECA57'
    ]
    return colors[index % len(colors)]

def generate_pie_chart(data):
    """Generate SVG Pie Chart for extensions."""
    # Sort data by value
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    
    # Take top 8 and group rest as "Other"
    if len(sorted_data) > 8:
        top = sorted_data[:8]
        other_count = sum(item[1] for item in sorted_data[8:])
        top.append(('Other', other_count))
        sorted_data = top
    
    total = sum(item[1] for item in sorted_data)
    if total == 0:
        return "<svg></svg>"

    cx, cy, r = 150, 150, 100
    start_angle = 0
    svg_parts = []
    
    # Legend data
    legend_items = []

    for i, (label, value) in enumerate(sorted_data):
        percentage = value / total
        angle = percentage * 360
        end_angle = start_angle + angle
        
        # Calculate coordinates
        x1 = cx + r * math.cos(math.radians(start_angle - 90))
        y1 = cy + r * math.sin(math.radians(start_angle - 90))
        x2 = cx + r * math.cos(math.radians(end_angle - 90))
        y2 = cy + r * math.sin(math.radians(end_angle - 90))
        
        large_arc_flag = 1 if angle > 180 else 0
        
        color = get_color(i, len(sorted_data))
        
        path_d = f"M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc_flag} 1 {x2} {y2} Z"
        
        svg_parts.append(f'<path d="{path_d}" fill="{color}" stroke="#1a1a1a" stroke-width="2" />')
        
        # Legend item
        legend_items.append(f"""
            <div class="legend-item">
                <span class="color-dot" style="background-color: {color}"></span>
                <span class="label">{label}</span>
                <span class="value">{value} ({percentage:.1%})</span>
            </div>
        """)
        
        start_angle = end_angle

    svg_content = "".join(svg_parts)
    
    return f"""
    <div class="chart-container">
        <svg viewBox="0 0 300 300" class="pie-chart">
            {svg_content}
            <circle cx="{cx}" cy="{cy}" r="{r/2}" fill="#1a1a1a" />
        </svg>
        <div class="legend">
            {"".join(legend_items)}
        </div>
    </div>
    """

def generate_bar_chart(files):
    """Generate SVG Bar Chart for largest files."""
    if not files:
        return ""
    
    width = 600
    row_height = 40
    height = len(files) * row_height
    max_size = files[0]['size'] if files else 1
    
    svg_parts = []
    
    for i, file in enumerate(files):
        y = i * row_height
        bar_width = (file['size'] / max_size) * (width - 150) # Leave space for text
        bar_width = max(bar_width, 5) # Minimum width
        
        color = get_color(i, len(files))
        
        # Bar
        svg_parts.append(f'<rect x="0" y="{y + 10}" width="{bar_width}" height="20" rx="4" fill="{color}" />')
        
        # Text (Filename)
        name = file['name']
        if len(name) > 30: name = name[:27] + "..."
        svg_parts.append(f'<text x="{bar_width + 10}" y="{y + 25}" fill="#ffffff" font-size="12" font-family="monospace">{name}</text>')
        
        # Text (Size)
        size_str = format_size(file['size'])
        svg_parts.append(f'<text x="{width}" y="{y + 25}" fill="#aaaaaa" font-size="12" text-anchor="end">{size_str}</text>')

    return f"""
    <svg viewBox="0 0 {width} {height}" class="bar-chart">
        { "".join(svg_parts) }
    </svg>
    """

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def generate_html(stats):
    pie_chart = generate_pie_chart(stats['extensions'])
    bar_chart = generate_bar_chart(stats['largest_files'])
    
    total_size_str = format_size(stats['total_size'])
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        :root {{
            --bg-color: #1a1a1a;
            --card-bg: #2d2d2d;
            --text-main: #ffffff;
            --text-muted: #a0a0a0;
            --accent: #4ECDC4;
        }}
        
        body {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            margin-bottom: 40px;
            border-bottom: 1px solid #333;
            padding-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        h1 {{
            margin: 0;
            font-weight: 300;
            letter-spacing: 2px;
            text-transform: uppercase;
            font-size: 2rem;
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            transition: transform 0.2s;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
        }}
        
        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--accent);
            margin: 10px 0;
        }}
        
        .metric-label {{
            color: var(--text-muted);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .big-card {{
            grid-column: span 2;
        }}
        
        @media (max-width: 768px) {{
            .big-card {{
                grid-column: span 1;
            }}
        }}

        .chart-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        
        .pie-chart {{
            width: 200px;
            height: 200px;
        }}
        
        .bar-chart {{
            width: 100%;
            height: auto;
        }}
        
        .legend {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 0.9rem;
        }}
        
        .color-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        
        .label {{
            margin-right: 10px;
            width: 80px;
        }}
        
        .value {{
            color: var(--text-muted);
        }}
        
        h2 {{
            font-size: 1.2rem;
            margin-top: 0;
            margin-bottom: 20px;
            color: var(--text-muted);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        
        th {{
            text-align: left;
            padding: 10px;
            border-bottom: 2px solid #444;
            color: var(--text-muted);
        }}
        
        td {{
            padding: 10px;
            border-bottom: 1px solid #333;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        .path-cell {{
            font-family: monospace;
            color: #ddd;
            word-break: break-all;
        }}

        .footer {{
            margin-top: 50px;
            text-align: center;
            color: #555;
            font-size: 0.8rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <div style="color: #666;">Generated via Python</div>
        </header>
        
        <div class="grid">
            <div class="card">
                <div class="metric-label">Total Files</div>
                <div class="metric-value">{stats['total_files']:,}</div>
            </div>
            <div class="card">
                <div class="metric-label">Lines of Code</div>
                <div class="metric-value">{stats['total_lines']:,}</div>
            </div>
            <div class="card">
                <div class="metric-label">Total Size</div>
                <div class="metric-value">{total_size_str}</div>
            </div>
            <div class="card">
                <div class="metric-label">Max Depth</div>
                <div class="metric-value">{stats['max_depth']}</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card big-card">
                <h2>File Types Distribution</h2>
                {pie_chart}
            </div>
            <div class="card big-card">
                <h2>Largest Files</h2>
                {bar_chart}
            </div>
        </div>

        <div class="card" style="margin-bottom: 30px;">
            <h2>Top 10 Largest Files Details</h2>
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
                    {''.join(f'''
                    <tr>
                        <td class="path-cell">{f['path']}</td>
                        <td>{f['ext']}</td>
                        <td>{f['lines']:,}</td>
                        <td>{format_size(f['size'])}</td>
                    </tr>
                    ''' for f in stats['largest_files'])}
                </tbody>
            </table>
        </div>

        <div class="footer">
            Scanned {stats['dirs_scanned']} directories.
        </div>
    </div>
</body>
</html>
    """
    
    with open('stats.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Successfully generated stats.html")
    print(f"Stats: {stats['total_files']} files, {stats['total_lines']} lines")

def main():
    print("Scanning directory...")
    current_dir = os.getcwd()
    stats = scan_directory(current_dir)
    generate_html(stats)

if __name__ == "__main__":
    main()