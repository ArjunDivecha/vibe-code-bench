#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Generates a beautiful HTML dashboard with codebase statistics
"""

import os
import math
from collections import defaultdict
from pathlib import Path

def scan_directory(root_path="."):
    """Recursively scan directory and collect statistics."""
    stats = {
        'file_counts': defaultdict(int),
        'lines_by_ext': defaultdict(int),
        'files': [],
        'max_depth': 0,
        'total_files': 0,
        'total_lines': 0,
        'total_size': 0,
        'dir_count': 0
    }
    
    # Directories to skip
    skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.idea', '.vscode', 'dist', 'build'}
    
    # Binary/non-text extensions to skip for line counting
    binary_exts = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz', 
                   '.exe', '.dll', '.so', '.dylib', '.pyc', '.pyo', '.class', '.o', '.a',
                   '.mp3', '.mp4', '.wav', '.avi', '.mov', '.woff', '.woff2', '.ttf', '.eot'}
    
    root = Path(root_path).resolve()
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filter out skip directories
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        
        # Calculate depth
        rel_path = Path(dirpath).resolve()
        try:
            depth = len(rel_path.relative_to(root).parts)
        except ValueError:
            depth = 0
        stats['max_depth'] = max(stats['max_depth'], depth)
        stats['dir_count'] += 1
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            
            # Get extension
            ext = Path(filename).suffix.lower() or '.no-ext'
            
            # File size
            try:
                size = os.path.getsize(filepath)
            except (OSError, IOError):
                continue
            
            stats['file_counts'][ext] += 1
            stats['total_files'] += 1
            stats['total_size'] += size
            
            # Count lines for text files
            lines = 0
            if ext not in binary_exts:
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                    stats['lines_by_ext'][ext] += lines
                    stats['total_lines'] += lines
                except (OSError, IOError):
                    pass
            
            # Store file info
            rel_filepath = os.path.relpath(filepath, root_path)
            stats['files'].append({
                'path': rel_filepath,
                'ext': ext,
                'size': size,
                'lines': lines
            })
    
    return stats

def format_size(size):
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def generate_colors(n):
    """Generate n vibrant colors for charts."""
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8B500', '#FF6F61', '#6B5B95', '#88B04B', '#F7CAC9',
        '#92A8D1', '#955251', '#B565A7', '#009B77', '#DD4124'
    ]
    return colors[:n] if n <= len(colors) else colors + colors * (n // len(colors) + 1)

def generate_pie_chart_svg(data, width=300, height=300):
    """Generate SVG pie chart."""
    if not data:
        return '<svg width="300" height="300"><text x="150" y="150" text-anchor="middle" fill="#888">No data</text></svg>'
    
    cx, cy = width // 2, height // 2
    radius = min(width, height) // 2 - 20
    
    total = sum(d['value'] for d in data)
    if total == 0:
        return '<svg width="300" height="300"><text x="150" y="150" text-anchor="middle" fill="#888">No data</text></svg>'
    
    colors = generate_colors(len(data))
    svg_parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    
    start_angle = -90  # Start from top
    
    for i, item in enumerate(data):
        if item['value'] == 0:
            continue
            
        percentage = item['value'] / total
        angle = percentage * 360
        
        # Calculate arc
        end_angle = start_angle + angle
        
        # Convert to radians
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        # Calculate points
        x1 = cx + radius * math.cos(start_rad)
        y1 = cy + radius * math.sin(start_rad)
        x2 = cx + radius * math.cos(end_rad)
        y2 = cy + radius * math.sin(end_rad)
        
        # Large arc flag
        large_arc = 1 if angle > 180 else 0
        
        # Create path
        if percentage >= 0.9999:
            # Full circle
            svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{colors[i]}" class="pie-slice" data-label="{item["label"]}" data-value="{item["value"]}" data-percent="{percentage*100:.1f}"/>')
        else:
            path = f'M {cx} {cy} L {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2} Z'
            svg_parts.append(f'<path d="{path}" fill="{colors[i]}" class="pie-slice" data-label="{item["label"]}" data-value="{item["value"]}" data-percent="{percentage*100:.1f}"/>')
        
        start_angle = end_angle
    
    # Center circle for donut effect
    inner_radius = radius * 0.5
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{inner_radius}" fill="#1a1a2e"/>')
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)

def generate_bar_chart_svg(data, width=500, height=250):
    """Generate SVG horizontal bar chart."""
    if not data:
        return '<svg width="500" height="250"><text x="250" y="125" text-anchor="middle" fill="#888">No data</text></svg>'
    
    colors = generate_colors(len(data))
    max_value = max(d['value'] for d in data) if data else 1
    
    padding = 40
    bar_height = 25
    gap = 10
    chart_width = width - padding * 2 - 100
    
    svg_parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    
    for i, item in enumerate(data[:8]):  # Limit to 8 bars
        y = padding + i * (bar_height + gap)
        bar_width = (item['value'] / max_value) * chart_width if max_value > 0 else 0
        
        # Label
        svg_parts.append(f'<text x="{padding - 5}" y="{y + bar_height/2 + 5}" text-anchor="end" fill="#aaa" font-size="12">{item["label"][:12]}</text>')
        
        # Bar
        svg_parts.append(f'<rect x="{padding}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{colors[i]}" rx="4" class="bar"/>')
        
        # Value
        svg_parts.append(f'<text x="{padding + bar_width + 10}" y="{y + bar_height/2 + 5}" fill="#fff" font-size="12">{item["value"]:,}</text>')
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)

def generate_html(stats):
    """Generate the HTML infographic."""
    
    # Prepare data for charts
    file_type_data = sorted(
        [{'label': ext, 'value': count} for ext, count in stats['file_counts'].items()],
        key=lambda x: x['value'],
        reverse=True
    )[:10]
    
    lines_data = sorted(
        [{'label': ext, 'value': lines} for ext, lines in stats['lines_by_ext'].items()],
        key=lambda x: x['value'],
        reverse=True
    )[:8]
    
    largest_files = sorted(stats['files'], key=lambda x: x['size'], reverse=True)[:10]
    most_lines = sorted(stats['files'], key=lambda x: x['lines'], reverse=True)[:10]
    
    # Generate charts
    pie_chart = generate_pie_chart_svg(file_type_data)
    bar_chart = generate_bar_chart_svg(lines_data)
    
    # Generate legend for pie chart
    colors = generate_colors(len(file_type_data))
    legend_items = []
    total_files = stats['total_files']
    for i, item in enumerate(file_type_data):
        pct = (item['value'] / total_files * 100) if total_files > 0 else 0
        legend_items.append(f'''
            <div class="legend-item">
                <span class="legend-color" style="background: {colors[i]}"></span>
                <span class="legend-label">{item['label']}</span>
                <span class="legend-value">{item['value']} ({pct:.1f}%)</span>
            </div>
        ''')
    legend_html = '\n'.join(legend_items)
    
    # Generate largest files table
    largest_files_rows = []
    for f in largest_files:
        largest_files_rows.append(f'''
            <tr>
                <td class="file-path">{f['path'][:50]}{'...' if len(f['path']) > 50 else ''}</td>
                <td class="file-size">{format_size(f['size'])}</td>
            </tr>
        ''')
    largest_files_html = '\n'.join(largest_files_rows)
    
    # Generate most lines table
    most_lines_rows = []
    for f in most_lines:
        if f['lines'] > 0:
            most_lines_rows.append(f'''
                <tr>
                    <td class="file-path">{f['path'][:50]}{'...' if len(f['path']) > 50 else ''}</td>
                    <td class="file-lines">{f['lines']:,}</td>
                </tr>
            ''')
    most_lines_html = '\n'.join(most_lines_rows[:10])
    
    # Extension breakdown for bar chart
    ext_breakdown = []
    for item in lines_data:
        ext_breakdown.append(f'<div class="ext-item"><span class="ext-name">{item["label"]}</span><span class="ext-lines">{item["value"]:,} lines</span></div>')
    ext_breakdown_html = '\n'.join(ext_breakdown)
    
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
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f0f23 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 40px 20px;
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            letter-spacing: -1px;
        }}
        
        .subtitle {{
            color: #888;
            font-size: 1.1rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 5px;
        }}
        
        .stat-card:nth-child(1) .stat-value {{ color: #FF6B6B; }}
        .stat-card:nth-child(2) .stat-value {{ color: #4ECDC4; }}
        .stat-card:nth-child(3) .stat-value {{ color: #45B7D1; }}
        .stat-card:nth-child(4) .stat-value {{ color: #FFEAA7; }}
        
        .stat-label {{
            color: #888;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .card-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .card-title::before {{
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 2px;
        }}
        
        .chart-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }}
        
        .legend {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.85rem;
        }}
        
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
            flex-shrink: 0;
        }}
        
        .legend-label {{
            color: #ccc;
            min-width: 70px;
        }}
        
        .legend-value {{
            color: #888;
            font-size: 0.8rem;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        th {{
            color: #888;
            font-weight: 500;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .file-path {{
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 0.85rem;
            color: #4ECDC4;
        }}
        
        .file-size, .file-lines {{
            font-weight: 600;
            color: #FF6B6B;
            text-align: right;
        }}
        
        .bar {{
            transition: opacity 0.3s;
        }}
        
        .bar:hover {{
            opacity: 0.8;
        }}
        
        .pie-slice {{
            transition: transform 0.3s, opacity 0.3s;
            transform-origin: center;
        }}
        
        .pie-slice:hover {{
            opacity: 0.8;
            transform: scale(1.02);
        }}
        
        .ext-breakdown {{
            display: grid;
            gap: 10px;
            margin-top: 20px;
        }}
        
        .ext-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
        }}
        
        .ext-name {{
            color: #4ECDC4;
            font-family: monospace;
        }}
        
        .ext-lines {{
            color: #888;
        }}
        
        .full-width {{
            grid-column: 1 / -1;
        }}
        
        footer {{
            text-align: center;
            padding: 30px;
            color: #555;
            font-size: 0.9rem;
        }}
        
        .depth-visual {{
            display: flex;
            align-items: center;
            gap: 5px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        
        .depth-level {{
            padding: 8px 16px;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
            border-radius: 20px;
            font-size: 0.85rem;
            border: 1px solid rgba(102, 126, 234, 0.5);
        }}
        
        .depth-arrow {{
            color: #667eea;
        }}
        
        @media (max-width: 1000px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            .dashboard {{
                grid-template-columns: 1fr;
            }}
        }}
        
        @media (max-width: 600px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            h1 {{
                font-size: 2rem;
            }}
            .stat-value {{
                font-size: 2rem;
            }}
        }}
        
        .tooltip {{
            position: fixed;
            background: rgba(0, 0, 0, 0.9);
            color: #fff;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 0.85rem;
            pointer-events: none;
            z-index: 1000;
            display: none;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Codebase Fingerprint</h1>
            <p class="subtitle">A visual analysis of your repository</p>
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
                <div class="stat-value">{format_size(stats['total_size'])}</div>
                <div class="stat-label">Total Size</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['max_depth']}</div>
                <div class="stat-label">Max Depth</div>
            </div>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <div class="card-title">File Types Distribution</div>
                <div class="chart-container">
                    {pie_chart}
                    <div class="legend">
                        {legend_html}
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">Lines of Code by Extension</div>
                {bar_chart}
                <div class="ext-breakdown">
                    {ext_breakdown_html}
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">Largest Files</div>
                <table>
                    <thead>
                        <tr>
                            <th>File Path</th>
                            <th style="text-align: right">Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        {largest_files_html}
                    </tbody>
                </table>
            </div>
            
            <div class="card">
                <div class="card-title">Most Lines of Code</div>
                <table>
                    <thead>
                        <tr>
                            <th>File Path</th>
                            <th style="text-align: right">Lines</th>
                        </tr>
                    </thead>
                    <tbody>
                        {most_lines_html}
                    </tbody>
                </table>
            </div>
            
            <div class="card full-width">
                <div class="card-title">Directory Structure</div>
                <p style="color: #888; margin-bottom: 15px;">
                    Your codebase contains <strong style="color: #4ECDC4">{stats['dir_count']}</strong> directories 
                    with a maximum nesting depth of <strong style="color: #FF6B6B">{stats['max_depth']}</strong> levels.
                </p>
                <div class="depth-visual">
                    {'<span class="depth-arrow">→</span>'.join([f'<span class="depth-level">Level {i}</span>' for i in range(min(stats['max_depth'] + 1, 6))])}
                    {' <span class="depth-level">...</span>' if stats['max_depth'] > 5 else ''}
                </div>
            </div>
        </div>
        
        <footer>
            Generated with ❤️ by Codebase Fingerprint Generator
        </footer>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        // Tooltip functionality
        const tooltip = document.getElementById('tooltip');
        
        document.querySelectorAll('.pie-slice').forEach(slice => {{
            slice.addEventListener('mouseenter', (e) => {{
                const label = slice.getAttribute('data-label');
                const value = slice.getAttribute('data-value');
                const percent = slice.getAttribute('data-percent');
                tooltip.innerHTML = `<strong>${{label}}</strong><br>${{value}} files (${{percent}}%)`;
                tooltip.style.display = 'block';
            }});
            
            slice.addEventListener('mousemove', (e) => {{
                tooltip.style.left = (e.clientX + 15) + 'px';
                tooltip.style.top = (e.clientY + 15) + 'px';
            }});
            
            slice.addEventListener('mouseleave', () => {{
                tooltip.style.display = 'none';
            }});
        }});
        
        // Animate stat values on load
        document.querySelectorAll('.stat-value').forEach(el => {{
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.5s, transform 0.5s';
        }});
        
        setTimeout(() => {{
            document.querySelectorAll('.stat-value').forEach((el, i) => {{
                setTimeout(() => {{
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }}, i * 100);
            }});
        }}, 100);
    </script>
</body>
</html>
'''
    return html

def main():
    print("🔍 Scanning codebase...")
    stats = scan_directory(".")
    
    print(f"📊 Found {stats['total_files']} files with {stats['total_lines']:,} lines of code")
    print(f"📁 {stats['dir_count']} directories, max depth: {stats['max_depth']}")
    
    print("🎨 Generating infographic...")
    html = generate_html(stats)
    
    with open('stats.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ Generated stats.html successfully!")
    print("   Open stats.html in your browser to view the infographic.")

if __name__ == '__main__':
    main()