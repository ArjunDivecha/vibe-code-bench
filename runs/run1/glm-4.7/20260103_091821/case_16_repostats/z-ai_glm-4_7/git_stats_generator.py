#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Scans current directory and generates a beautiful HTML infographic
"""

import os
import sys
from pathlib import Path
from collections import defaultdict, Counter
import math

def scan_directory(root_dir="."):
    """Recursively scan directory and collect stats"""
    extensions = Counter()
    lines_by_ext = Counter()
    total_lines = 0
    file_sizes = []
    max_depth = 0
    total_files = 0
    
    root_path = Path(root_dir).resolve()
    
    # Directories to skip
    skip_dirs = {'.git', 'node_modules', '__pycache__', 'venv', 'env', 
                 'virtualenv', '.venv', 'dist', 'build', 'target', '.idea',
                 '.vscode', 'vendor', 'bower_components'}
    
    for root, dirs, files in os.walk(root_path):
        # Filter out hidden and skip directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in skip_dirs]
        
        current_depth = len(Path(root).relative_to(root_path).parts)
        max_depth = max(max_depth, depth)
        
        for file in files:
            if file.startswith('.'):
                continue
                
            file_path = Path(root) / file
            try:
                file_size = file_path.stat().st_size
                file_sizes.append((str(file_path.relative_to(root_path)), file_size))
                total_files += 1
                
                # Get extension
                ext = file_path.suffix.lower()
                if not ext:
                    ext = '(no extension)'
                extensions[ext] += 1
                
                # Count lines for text files
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                        total_lines += lines
                        lines_by_ext[ext] += lines
                except:
                    pass
            except:
                continue
    
    # Get top 10 largest files
    largest_files = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'extensions': extensions,
        'lines_by_ext': lines_by_ext,
        'total_lines': total_lines,
        'largest_files': largest_files,
        'max_depth': max_depth,
        'total_files': total_files
    }

def format_size(size):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def generate_svg_pie_chart(data, width=350, height=350):
    """Generate SVG donut pie chart"""
    total = sum(data.values())
    if total == 0:
        return '<p class="no-data">No files found</p>'
    
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8B500', '#FF6F61', '#6B5B95', '#88B04B', '#F7CAC9',
        '#00B4DB', '#0083B0', '#FF416C', '#FF4B2B', '#11998e'
    ]
    
    svg_parts = []
    start_angle = -math.pi / 2  # Start from top
    cx, cy = width / 2, height / 2
    outer_radius = min(width, height) / 2 - 10
    inner_radius = outer_radius * 0.55
    
    # Legend items
    legend_parts = []
    
    for i, (label, value) in enumerate(data.most_common(12)):
        if value == 0:
            continue
        percentage = value / total
        angle = percentage * 2 * math.pi
        
        # Calculate slice coordinates
        end_angle = start_angle + angle
        
        x1 = cx + outer_radius * math.cos(start_angle)
        y1 = cy + outer_radius * math.sin(start_angle)
        x2 = cx + outer_radius * math.cos(end_angle)
        y2 = cy + outer_radius * math.sin(end_angle)
        
        x3 = cx + inner_radius * math.cos(end_angle)
        y3 = cy + inner_radius * math.sin(end_angle)
        x4 = cx + inner_radius * math.cos(start_angle)
        y4 = cy + inner_radius * math.sin(start_angle)
        
        large_arc = 1 if angle > math.pi else 0
        
        color = colors[i % len(colors)]
        
        if percentage >= 0.999:
            # Full circle
            svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{outer_radius}" fill="{color}"/>')
            svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{inner_radius}" fill="#1a1a2e"/>')
        else:
            # Donut slice
            path = f'''<path d="M {x1} {y1} A {outer_radius} {outer_radius} 0 {large_arc} 1 {x2} {y2} 
                           L {x3} {y3} A {inner_radius} {inner_radius} 0 {large_arc} 0 {x4} {y4} Z" 
                      fill="{color}" class="pie-slice"/>'''
            svg_parts.append(path)
        
        # Add to legend
        display_label = label if label else '(none)'
        legend_parts.append(f'''<div class="legend-item">
            <span class="legend-color" style="background: {color}"></span>
            <span class="legend-label">{display_label}</span>
            <span class="legend-value">{value} ({percentage*100:.1f}%)</span>
        </div>''')
        
        start_angle = end_angle
    
    # Add total in center
    svg_parts.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle" fill="#fff" font-size="24" font-weight="bold">{total:,}</text>')
    svg_parts.append(f'<text x="{cx}" y="{cy + 20}" text-anchor="middle" dominant-baseline="middle" fill="#888" font-size="12">FILES</text>')
    
    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        {"".join(svg_parts)}
    </svg>'''
    
    return f'''<div class="chart-container">
        <div class="pie-chart">{svg}</div>
        <div class="legend">{"".join(legend_parts)}</div>
    </div>'''

def generate_svg_bar_chart(data, width=550, height=320, max_bars=10):
    """Generate SVG horizontal bar chart"""
    if not data:
        return '<p class="no-data">No data available</p>'
    
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    
    max_value = max(data.values()) if data else 1
    bar_height = 24
    bar_gap = 12
    left_margin = 150
    right_margin = 80
    bottom_margin = 30
    top_margin = 20
    chart_width = width - left_margin - right_margin
    chart_height = height - top_margin - bottom_margin
    
    svg_parts = []
    
    for i, (label, value) in enumerate(data.most_common(max_bars)):
        y = top_margin + i * (bar_height + bar_gap)
        bar_width = (value / max_value) * chart_width
        
        color = colors[i % len(colors)]
        
        # Background bar
        svg_parts.append(f'<rect x="{left_margin}" y="{y}" width="{chart_width}" height="{bar_height}" fill="rgba(255,255,255,0.05)" rx="4"/>')
        
        # Value bar with animation
        svg_parts.append(f'''<rect x="{left_margin}" y="{y}" width="0" height="{bar_height}" fill="{color}" rx="4">
            <animate attributeName="width" from="0" to="{bar_width}" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
        </rect>''')
        
        # Label
        display_label = label[:20] + '...' if len(label) > 20 else label
        svg_parts.append(f'<text x="{left_margin - 10}" y="{y + bar_height/2 + 4}" text-anchor="end" fill="#ccc" font-size="12" font-family="monospace">{display_label}</text>')
        
        # Value label
        svg_parts.append(f'<text x="{left_margin + bar_width + 10}" y="{y + bar_height/2 + 4}" text-anchor="start" fill="#fff" font-size="12" font-weight="bold">{value:,}</text>')
    
    # Y-axis line
    svg_parts.append(f'<line x1="{left_margin}" y1="{top_margin}" x2="{left_margin}" y2="{height - bottom_margin}" stroke="#444" stroke-width="1"/>')
    
    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        {"".join(svg_parts)}
    </svg>'''
    
    return svg

def generate_html(stats):
    """Generate the HTML infographic"""
    
    pie_chart = generate_svg_pie_chart(stats['extensions'])
    bar_chart = generate_svg_bar_chart(stats['lines_by_ext'])
    
    # Generate file list HTML
    files_list_html = ""
    for name, size in stats['largest_files']:
        display_name = name
        if len(display_name) > 50:
            display_name = '...' + display_name[-47:]
        files_list_html += f'''<div class="file-item">
            <span class="file-name" title="{name}">{display_name}</span>
            <span class="file-size">{format_size(size)}</span>
        </div>'''
    
    if not stats['largest_files']:
        files_list_html = '<p class="no-data">No files found</p>'
    
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1c2128 100%);
            min-height: 100vh;
            color: #e6edf3;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 50px 0 40px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 40px;
            position: relative;
        }}
        
        header::after {{
            content: '';
            position: absolute;
            bottom: -1px;
            left: 50%;
            transform: translateX(-50%);
            width: 200px;
            height: 3px;
            background: linear-gradient(90deg, transparent, #4ECDC4, transparent);
        }}
        
        h1 {{
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 50%, #4ECDC4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 15px;
            letter-spacing: -1px;
        }}
        
        .subtitle {{
            color: #8b949e;
            font-size: 1.2rem;
            font-weight: 300;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 25px;
            margin-bottom: 50px;
        }}
        
        .stat-card {{
            background: linear-gradient(145deg, rgba(22,27,34,0.8), rgba(13,17,23,0.9));
            border-radius: 16px;
            padding: 30px 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.08);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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
            background: linear-gradient(90deg, #4ECDC4, #44A08D);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(78, 205, 196, 0.15);
            border-color: rgba(78, 205, 196, 0.3);
        }}
        
        .stat-card:hover::before {{
            transform: scaleX(1);
        }}
        
        .stat-icon {{
            font-size: 2rem;
            margin-bottom: 15px;
            opacity: 0.7;
        }}
        
        .stat-value {{
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #FF6B6B, #FFEAA7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            line-height: 1;
        }}
        
        .stat-label {{
            color: #8b949e;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 2.5px;
            font-weight: 600;
        }}
        
        .charts-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 35px;
            margin-bottom: 50px;
        }}
        
        .chart-card {{
            background: linear-gradient(145deg, rgba(22,27,34,0.8), rgba(13,17,23,0.9));
            border-radius: 20px;
            padding: 35px;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        
        .chart-title {{
            font-size: 1.4rem;
            margin-bottom: 30px;
            color: #4ECDC4;
            text-align: center;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }}
        
        .chart-title::before {{
            content: '';
            width: 30px;
            height: 3px;
            background: linear-gradient(90deg, #4ECDC4, #44A08D);
            border-radius: 2px;
        }}
        
        .chart-title::after {{
            content: '';
            width: 30px;
            height: 3px;
            background: linear-gradient(90deg, #44A08D, #4ECDC4);
            border-radius: 2px;
        }}
        
        .chart-container {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: flex-start;
            gap: 30px;
        }}
        
        .pie-chart {{
            flex-shrink: 0;
        }}
        
        .pie-slice {{
            transition: opacity 0.2s;
            cursor: pointer;
        }}
        
        .pie-slice:hover {{
            opacity: 0.8;
        }}
        
        .legend {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 320px;
            overflow-y: auto;
            padding-right: 5px;
        }}
        
        .legend::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .legend::-webkit-scrollbar-track {{
            background: rgba(255,255,255,0.05);
            border-radius: 3px;
        }}
        
        .legend::-webkit-scrollbar-thumb {{
            background: rgba(78, 205, 196, 0.5);
            border-radius: 3px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.9rem;
            padding: 8px 12px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            transition: background 0.2s;
        }}
        
        .legend-item:hover {{
            background: rgba(255,255,255,0.08);
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
            flex-shrink: 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }}
        
        .legend-label {{
            color: #e6edf3;
            flex: 1;
            font-family: monospace;
        }}
        
        .legend-value {{
            color: #8b949e;
            font-weight: 600;
        }}
        
        .files-list {{
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .files-list::-webkit-scrollbar {{
            width: 8px;
        }}
        
        .files-list::-webkit-scrollbar-track {{
            background: rgba(255,255,255,0.05);
            border-radius: 4px;
        }}
        
        .files-list::-webkit-scrollbar-thumb {{
            background: rgba(78, 205, 196, 0.4);
            border-radius: 4px;
        }}
        
        .file-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 16px;
            margin-bottom: 8px;
            background: rgba(255,255,255,0.04);
            border-radius: 10px;
            border-left: 4px solid #4ECDC4;
            transition: all 0.2s;
        }}
        
        .file-item:hover {{
            background: rgba(255,255,255,0.08);
            transform: translateX(5px);
        }}
        
        .file-name {{
            color: #e6edf3;
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 0.85rem;
            flex: 1;
            margin-right: 15px;
            word-break: break-all;
        }}
        
        .file-size {{
            color: #4ECDC4;
            font-weight: 700;
            font-size: 0.9rem;
            flex-shrink: 0;
            background: rgba(78, 205, 196, 0.15);
            padding: 4px 10px;
            border-radius: 6px;
        }}
        
        .no-data {{
            text-align: center;
            color: #8b949e;
            padding: 40px;
            font-style: italic;
        }}
        
        footer {{
            text-align: center;
            padding: 40px;
            color: #484f58;
            border-top: 1px solid rgba(255,255,255,0.08);
            margin-top: 50px;
        }}
        
        footer p {{
            font-size: 0.9rem;
        }}
        
        svg {{
            display: block;
            margin: 0 auto;
            max-width: 100%;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2.2rem;
            }}
            
            .charts-section {{
                grid-template-columns: 1fr;
            }}
            
            .stat-value {{
                font-size: 2.2rem;
            }}
            
            .chart-container {{
                flex-direction: column;
                align-items: center;
            }}
            
            .legend {{
                width: 100%;
                max-height: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">Visual analysis of your project structure</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">📁</div>
                <div class="stat-value">{stats['total_files']:,}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📝</div>
                <div class="stat-value">{stats['total_lines']:,}</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🔽</div>
                <div class="stat-value">{stats['max_depth']}</div>
                <div class="stat-label">Max Depth</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📋</div>
                <div class="stat-value">{len(stats['extensions'])}</div>
                <div class="stat-label">File Types</div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-card">
                <h2 class="chart-title">Files by Extension</h2>
                {pie_chart}
            </div>
            
            <div class="chart-card">
                <h2 class="chart-title">Lines of Code by Type</h2>
                {bar_chart}
            </div>
        </div>
        
        <div class="chart-card">
            <h2 class="chart-title">Largest Files</h2>
            <div class="files-list">
                {files_list_html}
            </div>
        </div>
        
        <footer>
            <p>Generated by Git Stats Infographic Generator • Built with Python & SVG</p>
        </footer>
    </div>
</body>
</html>'''
    
    return html

def main():
    print("🔍 Scanning directory...")
    stats = scan_directory()
    
    print(f"📊 Found {stats['total_files']:,} files")
    print(f"📝 Total lines: {stats['total_lines']:,}")
    print(f"📁 Max depth: {stats['max_depth']}")
    print(f"📋 File types: {len(stats['extensions'])}")
    
    print("🎨 Generating infographic...")
    html = generate_html(stats)
    
    output_path = 'stats.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Generated {output_path}")
    print(f"🌐 Open {output_path} in your browser to view the infographic")

if __name__ == '__main__':
    main()