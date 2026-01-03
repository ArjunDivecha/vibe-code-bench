#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Scans codebase and creates a beautiful HTML visualization
"""

import os
import math
from pathlib import Path
from collections import defaultdict


def scan_directory(root_path='.'):
    """Recursively scan directory and collect statistics"""
    stats = {
        'file_count_by_ext': defaultdict(int),
        'lines_by_ext': defaultdict(int),
        'largest_files': [],
        'max_depth': 0,
        'total_files': 0,
        'total_lines': 0,
        'total_size': 0
    }
    
    all_files = []
    
    # Skip common non-code directories
    skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build'}
    
    for root, dirs, files in os.walk(root_path):
        # Filter out directories to skip
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        # Calculate depth
        depth = root.replace(root_path, '').count(os.sep)
        stats['max_depth'] = max(stats['max_depth'], depth)
        
        for file in files:
            # Skip the output file itself
            if file == 'stats.html':
                continue
                
            filepath = os.path.join(root, file)
            
            try:
                # Get file extension
                ext = os.path.splitext(file)[1] if os.path.splitext(file)[1] else 'no extension'
                
                # Get file size
                size = os.path.getsize(filepath)
                
                # Count lines for text files
                lines = 0
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for line in f if line.strip())
                except:
                    lines = 0
                
                stats['file_count_by_ext'][ext] += 1
                stats['lines_by_ext'][ext] += lines
                stats['total_files'] += 1
                stats['total_lines'] += lines
                stats['total_size'] += size
                
                all_files.append({
                    'path': filepath,
                    'size': size,
                    'lines': lines,
                    'ext': ext
                })
                
            except Exception:
                continue
    
    # Sort and get largest files
    all_files.sort(key=lambda x: x['size'], reverse=True)
    stats['largest_files'] = all_files[:10]
    
    return stats


def generate_pie_chart(data):
    """Generate SVG pie chart"""
    if not data:
        return '<text x="200" y="200" fill="#fff" text-anchor="middle">No data</text>'
    
    total = sum(item['count'] for item in data)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', 
              '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788']
    
    svg_parts = []
    start_angle = 0
    cx, cy, r = 200, 200, 150
    
    for i, item in enumerate(data):
        angle = (item['count'] / total) * 360
        end_angle = start_angle + angle
        
        # Convert to radians
        start_rad = (start_angle - 90) * math.pi / 180
        end_rad = (end_angle - 90) * math.pi / 180
        
        # Calculate arc points
        x1 = cx + r * math.cos(start_rad)
        y1 = cy + r * math.sin(start_rad)
        x2 = cx + r * math.cos(end_rad)
        y2 = cy + r * math.sin(end_rad)
        
        large_arc = 1 if angle > 180 else 0
        
        path = f'M {cx},{cy} L {x1:.2f},{y1:.2f} A {r},{r} 0 {large_arc},1 {x2:.2f},{y2:.2f} Z'
        svg_parts.append(f'<path d="{path}" fill="{colors[i % len(colors)]}" stroke="#1a1a2e" stroke-width="2"/>')
        
        start_angle = end_angle
    
    return ''.join(svg_parts)


def generate_bar_chart(data):
    """Generate SVG bar chart"""
    if not data:
        return '<text x="300" y="150" fill="#fff" text-anchor="middle">No data</text>'
    
    max_lines = max(item['lines'] for item in data) if data else 1
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', 
              '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788']
    
    svg_parts = []
    bar_width = 50
    max_height = 250
    spacing = 10
    start_x = 50
    
    for i, item in enumerate(data):
        height = (item['lines'] / max_lines) * max_height if max_lines > 0 else 0
        x = start_x + i * (bar_width + spacing)
        y = 300 - height
        
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{height}" fill="{colors[i % len(colors)]}" rx="4"/>')
        svg_parts.append(f'<text x="{x + bar_width/2}" y="{y - 5}" fill="#fff" text-anchor="middle" font-size="12">{item["lines"]}</text>')
        
        # Truncate long extensions
        ext_label = item["ext"][:8] + '...' if len(item["ext"]) > 8 else item["ext"]
        svg_parts.append(f'<text x="{x + bar_width/2}" y="320" fill="#aaa" text-anchor="middle" font-size="11" transform="rotate(-45 {x + bar_width/2} 320)">{ext_label}</text>')
    
    return ''.join(svg_parts)


def format_size(size):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def generate_html(stats):
    """Generate beautiful HTML infographic"""
    
    # Prepare data for charts
    ext_data = []
    for ext, count in sorted(stats['file_count_by_ext'].items(), key=lambda x: x[1], reverse=True)[:10]:
        ext_data.append({'ext': ext, 'count': count})
    
    lines_data = []
    for ext, lines in sorted(stats['lines_by_ext'].items(), key=lambda x: x[1], reverse=True)[:10]:
        if lines > 0:  # Only include extensions with code
            lines_data.append({'ext': ext, 'lines': lines})
    
    # Generate charts
    pie_svg = generate_pie_chart(ext_data)
    bar_svg = generate_bar_chart(lines_data)
    
    # Build legend for pie chart
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', 
              '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788']
    legend_html = []
    for i, item in enumerate(ext_data):
        legend_html.append(f'''
            <div class="legend-item">
                <div class="legend-color" style="background: {colors[i % len(colors)]};"></div>
                <span>{item['ext']}: {item['count']} files</span>
            </div>
        ''')
    
    # Build largest files list
    files_html = []
    for file_info in stats['largest_files'][:5]:
        files_html.append(f'''
            <div class="file-item">
                <div class="file-name">{os.path.basename(file_info['path'])}</div>
                <div class="file-stats">
                    <span>{format_size(file_info['size'])}</span>
                    <span>•</span>
                    <span>{file_info['lines']:,} lines</span>
                </div>
            </div>
        ''')
    
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
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #fff;
            padding: 40px 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        h1 {{
            text-align: center;
            font-size: 3.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: glow 2s ease-in-out infinite alternate;
        }}
        
        @keyframes glow {{
            from {{
                filter: drop-shadow(0 0 5px rgba(78, 205, 196, 0.3));
            }}
            to {{
                filter: drop-shadow(0 0 20px rgba(78, 205, 196, 0.6));
            }}
        }}
        
        .subtitle {{
            text-align: center;
            color: #aaa;
            margin-bottom: 50px;
            font-size: 1.2em;
            letter-spacing: 1px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            text-align: center;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(78, 205, 196, 0.3);
        }}
        
        .stat-value {{
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .stat-label {{
            font-size: 1em;
            color: #aaa;
            margin-top: 10px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        
        .charts-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 40px;
            margin-bottom: 40px;
        }}
        
        .chart-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .chart-title {{
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #4ECDC4;
            text-align: center;
        }}
        
        .legend {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9em;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            flex-shrink: 0;
        }}
        
        .files-section {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .section-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #4ECDC4;
        }}
        
        .file-item {{
            background: rgba(255, 255, 255, 0.03);
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #FF6B6B;
            transition: all 0.3s;
        }}
        
        .file-item:hover {{
            background: rgba(255, 255, 255, 0.08);
            transform: translateX(5px);
        }}
        
        .file-name {{
            font-size: 1.1em;
            margin-bottom: 5px;
            color: #fff;
            font-weight: 500;
        }}
        
        .file-stats {{
            color: #aaa;
            font-size: 0.9em;
        }}
        
        .file-stats span {{
            margin-right: 10px;
        }}
        
        svg {{
            display: block;
            margin: 0 auto;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 60px;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2em;
            }}
            
            .charts-section {{
                grid-template-columns: 1fr;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Codebase Fingerprint</h1>
        <div class="subtitle">A visual journey through your code</div>
        
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
                <div class="stat-value">{len(stats['file_count_by_ext'])}</div>
                <div class="stat-label">File Types</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['max_depth']}</div>
                <div class="stat-label">Max Depth</div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-card">
                <div class="chart-title">📊 File Distribution</div>
                <svg width="400" height="400" viewBox="0 0 400 400">
                    {pie_svg}
                </svg>
                <div class="legend">
                    {''.join(legend_html)}
                </div>
            </div>
            
            <div class="chart-card">
                <div class="chart-title">📈 Lines of Code by Type</div>
                <svg width="600" height="400" viewBox="0 0 600 400">
                    {bar_svg}
                </svg>
            </div>
        </div>
        
        <div class="files-section">
            <div class="section-title">🔥 Largest Files</div>
            {''.join(files_html) if files_html else '<p style="color: #666;">No files found</p>'}
        </div>
        
        <div class="footer">
            Generated with ❤️ by Codebase Fingerprint Generator
        </div>
    </div>
    
    <script>
        // Add subtle animations on scroll
        const observerOptions = {{
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        }};
        
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }}
            }});
        }}, observerOptions);
        
        document.querySelectorAll('.stat-card, .chart-card, .files-section').forEach(el => {{
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(el);
        }});
    </script>
</body>
</html>'''
    
    return html


def main():
    print("🔍 Scanning codebase...")
    stats = scan_directory('.')
    
    print(f"✅ Found {stats['total_files']} files")
    print(f"📝 Total lines: {stats['total_lines']:,}")
    print(f"📁 Max depth: {stats['max_depth']}")
    print(f"🗂️  File types: {len(stats['file_count_by_ext'])}")
    
    print("\n🎨 Generating infographic...")
    html = generate_html(stats)
    
    with open('stats.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✨ Generated stats.html - Open it in your browser!")


if __name__ == '__main__':
    main()