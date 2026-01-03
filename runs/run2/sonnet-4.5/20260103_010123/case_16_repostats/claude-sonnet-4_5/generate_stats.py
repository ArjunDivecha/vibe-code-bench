#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Scans directory and creates a beautiful HTML visualization
"""

import os
import pathlib
from collections import defaultdict
import math
import datetime


def scan_directory(root_dir='.'):
    """Recursively scan directory and gather stats"""
    stats = {
        'files_by_ext': defaultdict(int),
        'lines_by_ext': defaultdict(int),
        'total_lines': 0,
        'total_files': 0,
        'largest_files': [],
        'max_depth': 0
    }
    
    # Extensions to try reading as text
    text_extensions = {
        '.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.hpp',
        '.rb', '.go', '.rs', '.swift', '.kt', '.ts', '.jsx', '.tsx', '.vue',
        '.php', '.pl', '.sh', '.bash', '.sql', '.r', '.m', '.scala', '.clj',
        '.lua', '.vim', '.el', '.md', '.txt', '.json', '.xml', '.yaml', '.yml',
        '.toml', '.ini', '.cfg', '.conf', '.cs', '.dart', '.ex', '.exs'
    }
    
    for root, dirs, files in os.walk(root_dir):
        # Calculate depth
        depth = root.replace(root_dir, '').count(os.sep)
        stats['max_depth'] = max(stats['max_depth'], depth)
        
        # Filter out common ignored directories
        dirs[:] = [d for d in dirs if d not in {
            '.git', 'node_modules', '__pycache__', '.venv', 'venv', 
            'dist', 'build', '.next', '.nuxt', 'target', 'bin', 'obj'
        }]
        
        for file in files:
            filepath = os.path.join(root, file)
            
            # Get extension
            ext = pathlib.Path(file).suffix.lower() or 'no_ext'
            stats['files_by_ext'][ext] += 1
            stats['total_files'] += 1
            
            # Get file size
            try:
                size = os.path.getsize(filepath)
                stats['largest_files'].append((filepath, size))
            except:
                pass
            
            # Count lines for text files
            if ext in text_extensions:
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for line in f if line.strip())
                        stats['lines_by_ext'][ext] += lines
                        stats['total_lines'] += lines
                except:
                    pass
    
    # Sort and limit largest files
    stats['largest_files'].sort(key=lambda x: x[1], reverse=True)
    stats['largest_files'] = stats['largest_files'][:10]
    
    return stats


def generate_pie_chart(data):
    """Generate SVG pie chart"""
    if not data:
        return '<p style="color: #888;">No data available</p>'
    
    total = sum(count for _, count in data)
    colors = [
        '#00d4ff', '#ff00ff', '#00ff88', '#ffaa00', '#ff4444', 
        '#44ff44', '#4444ff', '#ffff44', '#ff44ff', '#44ffff'
    ]
    
    svg_parts = ['<svg viewBox="0 0 400 450" style="max-width: 400px; margin: 0 auto; display: block;">']
    
    start_angle = -math.pi / 2  # Start at top
    cx, cy, r = 200, 180, 140
    
    legend_items = []
    
    for i, (ext, count) in enumerate(data):
        percentage = count / total
        angle = percentage * 2 * math.pi
        
        # Calculate arc
        end_angle = start_angle + angle
        
        x1 = cx + r * math.cos(start_angle)
        y1 = cy + r * math.sin(start_angle)
        x2 = cx + r * math.cos(end_angle)
        y2 = cy + r * math.sin(end_angle)
        
        large_arc = 1 if angle > math.pi else 0
        
        color = colors[i % len(colors)]
        
        # Draw slice
        svg_parts.append(
            f'<path d="M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z" '
            f'fill="{color}" stroke="#1a1a2e" stroke-width="2"/>'
        )
        
        # Add percentage label on slice
        mid_angle = start_angle + angle / 2
        label_x = cx + (r * 0.65) * math.cos(mid_angle)
        label_y = cy + (r * 0.65) * math.sin(mid_angle)
        
        if percentage > 0.05:  # Only show label if > 5%
            svg_parts.append(
                f'<text x="{label_x}" y="{label_y}" fill="white" text-anchor="middle" '
                f'dominant-baseline="middle" font-size="14" font-weight="bold">'
                f'{percentage*100:.1f}%</text>'
            )
        
        legend_items.append(
            f'<div class="legend-item">'
            f'<div class="legend-color" style="background: {color};"></div>'
            f'<span>{ext} ({count})</span>'
            f'</div>'
        )
        
        start_angle = end_angle
    
    svg_parts.append('</svg>')
    svg_parts.append('<div class="legend">')
    svg_parts.extend(legend_items)
    svg_parts.append('</div>')
    
    return '\n'.join(svg_parts)


def generate_bar_chart(data):
    """Generate SVG bar chart"""
    if not data:
        return '<p style="color: #888;">No data available</p>'
    
    max_lines = max(count for _, count in data) if data else 1
    colors = [
        '#00d4ff', '#ff00ff', '#00ff88', '#ffaa00', '#ff4444', 
        '#44ff44', '#4444ff', '#ffff44', '#ff44ff', '#44ffff'
    ]
    
    height = len(data) * 40 + 40
    svg_parts = [f'<svg viewBox="0 0 520 {height}" style="max-width: 520px; margin: 0 auto; display: block;">']
    
    bar_height = 28
    bar_spacing = 12
    chart_width = 350
    label_width = 90
    
    for i, (ext, count) in enumerate(data):
        y = i * (bar_height + bar_spacing) + 20
        bar_width = max((count / max_lines) * chart_width, 2)
        color = colors[i % len(colors)]
        
        # Label
        svg_parts.append(
            f'<text x="5" y="{y + bar_height/2}" fill="#aaa" dominant-baseline="middle" '
            f'font-size="14" font-family="monospace">{ext}</text>'
        )
        
        # Bar with gradient
        svg_parts.append(
            f'<rect x="{label_width}" y="{y}" width="{bar_width}" height="{bar_height}" '
            f'fill="{color}" rx="5" opacity="0.9"/>'
        )
        
        # Value
        svg_parts.append(
            f'<text x="{label_width + bar_width + 10}" y="{y + bar_height/2}" '
            f'fill="white" dominant-baseline="middle" font-size="12" font-weight="bold">'
            f'{count:,}</text>'
        )
    
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)


def generate_largest_files(files):
    """Generate HTML for largest files list"""
    if not files:
        return '<p style="color: #888;">No files found</p>'
    
    items = []
    for filepath, size in files:
        # Format size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        
        # Shorten path if too long
        display_path = filepath
        if len(display_path) > 60:
            display_path = "..." + display_path[-57:]
        
        items.append(
            f'<div class="file-item">'
            f'<span class="file-name" title="{filepath}">{display_path}</span>'
            f'<span class="file-size">{size_str}</span>'
            f'</div>'
        )
    
    return '\n'.join(items)


def generate_html(stats):
    """Generate complete HTML infographic"""
    
    # Prepare data for charts
    files_data = sorted(stats['files_by_ext'].items(), key=lambda x: x[1], reverse=True)[:10]
    lines_data = sorted(stats['lines_by_ext'].items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Generate charts
    pie_svg = generate_pie_chart(files_data)
    bar_svg = generate_bar_chart(lines_data)
    largest_files_html = generate_largest_files(stats['largest_files'])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: #e0e0e0;
            padding: 2rem;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        h1 {{
            text-align: center;
            font-size: 3.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, #00d4ff, #ff00ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradient-shift 4s ease infinite;
            text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
        }}
        
        @keyframes gradient-shift {{
            0%, 100% {{ filter: hue-rotate(0deg); }}
            50% {{ filter: hue-rotate(30deg); }}
        }}
        
        .subtitle {{
            text-align: center;
            color: #999;
            margin-bottom: 3rem;
            font-size: 1rem;
            letter-spacing: 1px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2rem 1.5rem;
            text-align: center;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #00d4ff, #ff00ff);
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 15px 40px rgba(0, 212, 255, 0.3);
            border-color: rgba(0, 212, 255, 0.5);
        }}
        
        .stat-card:hover::before {{
            opacity: 1;
        }}
        
        .stat-value {{
            font-size: 3rem;
            font-weight: bold;
            background: linear-gradient(135deg, #00d4ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            line-height: 1;
        }}
        
        .stat-label {{
            color: #aaa;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 0.5rem;
        }}
        
        .charts-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }}
        
        @media (max-width: 900px) {{
            .charts-container {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .chart-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2rem;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }}
        
        .chart-card:hover {{
            border-color: rgba(255, 0, 255, 0.5);
            box-shadow: 0 10px 30px rgba(255, 0, 255, 0.2);
        }}
        
        .chart-title {{
            font-size: 1.4rem;
            margin-bottom: 1.5rem;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .file-list {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2rem;
            backdrop-filter: blur(10px);
        }}
        
        .file-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            margin-bottom: 0.5rem;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 10px;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }}
        
        .file-item:hover {{
            background: rgba(0, 212, 255, 0.1);
            border-color: rgba(0, 212, 255, 0.3);
            transform: translateX(5px);
        }}
        
        .file-name {{
            color: #00d4ff;
            font-family: 'Courier New', monospace;
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-size: 0.9rem;
        }}
        
        .file-size {{
            color: #ff00ff;
            font-weight: bold;
            margin-left: 1rem;
            font-size: 0.9rem;
            white-space: nowrap;
        }}
        
        svg {{
            max-width: 100%;
            height: auto;
        }}
        
        .legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.8rem;
            margin-top: 1.5rem;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            color: #ccc;
        }}
        
        .legend-color {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2.5rem;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }}
            
            .stat-value {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Codebase Fingerprint</h1>
        <div class="subtitle">Generated on {datetime.datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_files']}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['total_lines']:,}</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(stats['files_by_ext'])}</div>
                <div class="stat-label">File Types</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['max_depth']}</div>
                <div class="stat-label">Max Depth</div>
            </div>
        </div>
        
        <div class="charts-container">
            <div class="chart-card">
                <div class="chart-title">📊 Files by Extension</div>
                {pie_svg}
            </div>
            <div class="chart-card">
                <div class="chart-title">📈 Lines of Code by Type</div>
                {bar_svg}
            </div>
        </div>
        
        <div class="file-list">
            <div class="chart-title">📦 Largest Files (Top 10)</div>
            {largest_files_html}
        </div>
    </div>
</body>
</html>"""
    
    return html


def main():
    """Main entry point"""
    print("🔍 Scanning codebase...")
    stats = scan_directory('.')
    
    print(f"✅ Found {stats['total_files']} files")
    print(f"✅ Counted {stats['total_lines']:,} lines of code")
    print(f"✅ Detected {len(stats['files_by_ext'])} file types")
    print(f"✅ Maximum directory depth: {stats['max_depth']}")
    
    print("\n🎨 Generating infographic...")
    html = generate_html(stats)
    
    with open('stats.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✨ Done! Open 'stats.html' in your browser to view the infographic.")


if __name__ == '__main__':
    main()