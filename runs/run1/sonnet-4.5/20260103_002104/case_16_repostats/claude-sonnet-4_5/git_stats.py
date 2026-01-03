#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Scans directory and generates a beautiful HTML infographic
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import json
import math


def scan_directory(root_path="."):
    """Recursively scan directory and collect statistics"""
    stats = {
        'file_count_by_ext': defaultdict(int),
        'lines_by_ext': defaultdict(int),
        'total_lines': 0,
        'total_files': 0,
        'largest_files': [],
        'max_depth': 0,
        'total_size': 0
    }
    
    all_files = []
    root_path = os.path.abspath(root_path)
    
    for root, dirs, files in os.walk(root_path):
        # Calculate depth
        depth = root.replace(root_path, '').count(os.sep)
        stats['max_depth'] = max(stats['max_depth'], depth)
        
        # Skip hidden directories and common ignore patterns
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                   ['node_modules', '__pycache__', 'venv', 'env', 'dist', 'build']]
        
        for file in files:
            if file.startswith('.'):
                continue
                
            file_path = os.path.join(root, file)
            try:
                size = os.path.getsize(file_path)
                ext = os.path.splitext(file)[1] or '.txt'
                
                # Count lines for text files
                lines = 0
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                except:
                    pass
                
                stats['file_count_by_ext'][ext] += 1
                stats['lines_by_ext'][ext] += lines
                stats['total_lines'] += lines
                stats['total_files'] += 1
                stats['total_size'] += size
                
                rel_path = os.path.relpath(file_path, root_path)
                all_files.append({
                    'path': rel_path,
                    'size': size,
                    'lines': lines,
                    'ext': ext
                })
            except Exception as e:
                pass
    
    # Get largest files
    stats['largest_files'] = sorted(all_files, key=lambda x: x['size'], reverse=True)[:10]
    
    return stats


def format_size(size_bytes):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def generate_pie_chart_svg(data, width=300, height=300):
    """Generate SVG pie chart for file type distribution"""
    total = sum(data.values())
    if total == 0:
        return '<text x="150" y="150" text-anchor="middle" fill="#666">No data</text>'
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', 
              '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788',
              '#FF8B94', '#A8E6CF', '#FFD3B6', '#FFAAA5', '#FF8C94']
    
    svg_parts = []
    cx, cy = width / 2, height / 2
    radius = min(width, height) / 2 - 10
    
    start_angle = -90  # Start from top
    idx = 0
    
    # Sort and take top items
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:8]
    
    for label, value in sorted_data:
        percentage = value / total
        angle = percentage * 360
        
        if angle < 1:
            continue
            
        end_angle = start_angle + angle
        
        # Calculate arc
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        x1 = cx + radius * math.cos(start_rad)
        y1 = cy + radius * math.sin(start_rad)
        x2 = cx + radius * math.cos(end_rad)
        y2 = cy + radius * math.sin(end_rad)
        
        large_arc = 1 if angle > 180 else 0
        
        path = f'M {cx},{cy} L {x1},{y1} A {radius},{radius} 0 {large_arc},1 {x2},{y2} Z'
        
        color = colors[idx % len(colors)]
        svg_parts.append(f'<path d="{path}" fill="{color}" opacity="0.85" stroke="#1a1a2e" stroke-width="2"/>')
        
        # Add percentage label if significant
        if percentage > 0.05:
            mid_angle = (start_angle + end_angle) / 2
            mid_rad = math.radians(mid_angle)
            label_x = cx + (radius * 0.6) * math.cos(mid_rad)
            label_y = cy + (radius * 0.6) * math.sin(mid_rad)
            
            svg_parts.append(f'<text x="{label_x}" y="{label_y}" text-anchor="middle" fill="white" font-size="14" font-weight="bold">{percentage*100:.0f}%</text>')
        
        start_angle = end_angle
        idx += 1
    
    return '\n'.join(svg_parts)


def generate_bar_chart_svg(data, width=500, height=250, title=""):
    """Generate SVG bar chart"""
    if not data:
        return '<text x="250" y="125" text-anchor="middle" fill="#666">No data</text>'
    
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:8]
    
    max_value = max(v for _, v in sorted_data) if sorted_data else 1
    bar_height = 25
    bar_spacing = 10
    margin_left = 80
    margin_right = 100
    chart_width = width - margin_left - margin_right
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', 
              '#F7DC6F', '#BB8FCE', '#85C1E2']
    
    svg_parts = []
    y_pos = 20
    
    for idx, (label, value) in enumerate(sorted_data):
        bar_width = (value / max_value) * chart_width if max_value > 0 else 0
        color = colors[idx % len(colors)]
        
        # Bar
        svg_parts.append(f'<rect x="{margin_left}" y="{y_pos}" width="{bar_width}" height="{bar_height}" fill="{color}" opacity="0.85" rx="3"/>')
        
        # Label
        svg_parts.append(f'<text x="{margin_left - 10}" y="{y_pos + bar_height/2 + 5}" text-anchor="end" fill="#aaa" font-size="12">{label}</text>')
        
        # Value
        svg_parts.append(f'<text x="{margin_left + bar_width + 10}" y="{y_pos + bar_height/2 + 5}" fill="white" font-size="12" font-weight="bold">{value:,}</text>')
        
        y_pos += bar_height + bar_spacing
    
    return '\n'.join(svg_parts)


def generate_html(stats):
    """Generate the complete HTML infographic"""
    
    # Prepare data for charts
    ext_data = dict(stats['file_count_by_ext'])
    lines_data = dict(stats['lines_by_ext'])
    
    # Generate legend for pie chart
    sorted_exts = sorted(ext_data.items(), key=lambda x: x[1], reverse=True)[:8]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', 
              '#F7DC6F', '#BB8FCE', '#85C1E2']
    
    legend_html = ""
    for idx, (ext, count) in enumerate(sorted_exts):
        color = colors[idx % len(colors)]
        percentage = (count / stats['total_files'] * 100) if stats['total_files'] > 0 else 0
        legend_html += f'''
        <div class="legend-item">
            <div class="legend-color" style="background-color: {color};"></div>
            <span class="legend-label">{ext}</span>
            <span class="legend-value">{count} files ({percentage:.1f}%)</span>
        </div>
        '''
    
    # Generate largest files list
    largest_files_html = ""
    for file_info in stats['largest_files']:
        largest_files_html += f'''
        <div class="file-item">
            <div class="file-name">{file_info['path']}</div>
            <div class="file-stats">
                <span class="file-size">{format_size(file_info['size'])}</span>
                <span class="file-lines">{file_info['lines']:,} lines</span>
            </div>
        </div>
        '''
    
    html = f'''<!DOCTYPE html>
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
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 40px 0;
            margin-bottom: 40px;
            border-bottom: 2px solid #0f3460;
        }}
        
        h1 {{
            font-size: 3.5em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            font-weight: 800;
            letter-spacing: -1px;
        }}
        
        .subtitle {{
            color: #aaa;
            font-size: 1.2em;
            font-weight: 300;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            backdrop-filter: blur(10px);
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }}
        
        .stat-value {{
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            color: #aaa;
            font-size: 1.1em;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        
        .charts-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }}
        
        .chart-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }}
        
        .chart-title {{
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #fff;
            text-align: center;
            font-weight: 600;
        }}
        
        .chart-wrapper {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 300px;
        }}
        
        .legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            flex-shrink: 0;
        }}
        
        .legend-label {{
            font-weight: 600;
            color: #fff;
        }}
        
        .legend-value {{
            margin-left: auto;
            color: #aaa;
            font-size: 0.9em;
        }}
        
        .files-section {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }}
        
        .section-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #fff;
            font-weight: 600;
        }}
        
        .file-item {{
            padding: 15px;
            margin-bottom: 10px;
            background: rgba(255, 255, 255, 0.03);
            border-left: 3px solid #4ECDC4;
            border-radius: 8px;
            transition: background 0.2s ease;
        }}
        
        .file-item:hover {{
            background: rgba(255, 255, 255, 0.08);
        }}
        
        .file-name {{
            color: #fff;
            font-family: 'Courier New', monospace;
            margin-bottom: 8px;
            word-break: break-all;
        }}
        
        .file-stats {{
            display: flex;
            gap: 20px;
            font-size: 0.9em;
        }}
        
        .file-size {{
            color: #FFA07A;
            font-weight: 600;
        }}
        
        .file-lines {{
            color: #98D8C8;
        }}
        
        footer {{
            text-align: center;
            margin-top: 50px;
            padding: 30px;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .charts-container {{
                grid-template-columns: 1fr;
            }}
            
            h1 {{
                font-size: 2.5em;
            }}
            
            .stat-value {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎨 Codebase Fingerprint</h1>
            <p class="subtitle">A visual journey through your code</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_files']:,}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['total_lines']:,}</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(stats['file_count_by_ext'])}</div>
                <div class="stat-label">File Types</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['max_depth']}</div>
                <div class="stat-label">Max Depth</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{format_size(stats['total_size'])}</div>
                <div class="stat-label">Total Size</div>
            </div>
        </div>
        
        <div class="charts-container">
            <div class="chart-card">
                <h2 class="chart-title">📊 File Distribution</h2>
                <div class="chart-wrapper">
                    <svg width="300" height="300" viewBox="0 0 300 300">
                        {generate_pie_chart_svg(ext_data, 300, 300)}
                    </svg>
                </div>
                <div class="legend">
                    {legend_html}
                </div>
            </div>
            
            <div class="chart-card">
                <h2 class="chart-title">📝 Lines by File Type</h2>
                <div class="chart-wrapper">
                    <svg width="500" height="350" viewBox="0 0 500 350">
                        {generate_bar_chart_svg(lines_data, 500, 350)}
                    </svg>
                </div>
            </div>
        </div>
        
        <div class="files-section">
            <h2 class="section-title">📁 Largest Files</h2>
            {largest_files_html if largest_files_html else '<p style="color: #666;">No files found</p>'}
        </div>
        
        <footer>
            Generated with ❤️ by Codebase Fingerprint Generator
        </footer>
    </div>
</body>
</html>'''
    
    return html


def main():
    """Main function"""
    print("🔍 Scanning directory...")
    
    # Scan current directory
    stats = scan_directory(".")
    
    print(f"✅ Found {stats['total_files']} files")
    print(f"📝 Total lines: {stats['total_lines']:,}")
    print(f"📊 File types: {len(stats['file_count_by_ext'])}")
    
    # Generate HTML
    print("🎨 Generating infographic...")
    html = generate_html(stats)
    
    # Write to file
    output_file = "stats.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✨ Infographic generated: {output_file}")
    print(f"🌐 Open it in your browser to view!")


if __name__ == "__main__":
    main()