#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Generates a beautiful HTML infographic of codebase statistics
"""

import os
import math
from collections import defaultdict
from pathlib import Path

def scan_directory(root_path="."):
    """Recursively scan directory and collect statistics"""
    stats = {
        'file_count_by_ext': defaultdict(int),
        'lines_by_ext': defaultdict(int),
        'total_files': 0,
        'total_lines': 0,
        'largest_files': [],
        'max_depth': 0,
        'directory_count': 0,
        'files_list': []
    }
    
    root_depth = os.path.abspath(root_path).count(os.sep)
    
    # Directories to skip
    skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.idea', '.vscode', 'dist', 'build'}
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip hidden/ignored directories
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith('.')]
        
        current_depth = os.path.abspath(dirpath).count(os.sep) - root_depth
        stats['max_depth'] = max(stats['max_depth'], current_depth)
        stats['directory_count'] += 1
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
                
            filepath = os.path.join(dirpath, filename)
            
            # Get extension
            ext = Path(filename).suffix.lower() or '(none)'
            
            # Count file
            stats['file_count_by_ext'][ext] += 1
            stats['total_files'] += 1
            
            # Try to count lines and get size
            try:
                file_size = os.path.getsize(filepath)
                line_count = 0
                
                # Only count lines for reasonable sized text files
                if file_size < 10 * 1024 * 1024:  # Skip files > 10MB
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            line_count = sum(1 for _ in f)
                    except:
                        pass
                
                stats['lines_by_ext'][ext] += line_count
                stats['total_lines'] += line_count
                
                rel_path = os.path.relpath(filepath, root_path)
                stats['files_list'].append({
                    'path': rel_path,
                    'name': filename,
                    'ext': ext,
                    'size': file_size,
                    'lines': line_count
                })
            except:
                pass
    
    # Get largest files
    stats['largest_files'] = sorted(stats['files_list'], key=lambda x: x['size'], reverse=True)[:10]
    
    return stats


def generate_pie_chart(data, colors):
    """Generate an SVG donut pie chart"""
    if not data:
        return '<svg width="280" height="280"><text x="140" y="140" text-anchor="middle" fill="#666">No data</text></svg>'
    
    total = sum(count for _, count in data)
    if total == 0:
        return '<svg width="280" height="280"><text x="140" y="140" text-anchor="middle" fill="#666">No data</text></svg>'
    
    cx, cy = 140, 140
    radius = 110
    inner_radius = 65
    
    svg_parts = ['<svg width="280" height="280" viewBox="0 0 280 280">']
    svg_parts.append('<defs>')
    svg_parts.append('<filter id="glow"><feGaussianBlur stdDeviation="3" result="coloredBlur"/>')
    svg_parts.append('<feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    svg_parts.append('</defs>')
    
    start_angle = -90
    
    for i, (ext, count) in enumerate(data):
        if count == 0:
            continue
        percentage = count / total
        angle = percentage * 360
        
        if angle < 0.5:  # Skip very tiny slices
            continue
            
        color = colors[i % len(colors)]
        end_angle = start_angle + angle
        
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        x1_outer = cx + radius * math.cos(start_rad)
        y1_outer = cy + radius * math.sin(start_rad)
        x2_outer = cx + radius * math.cos(end_rad)
        y2_outer = cy + radius * math.sin(end_rad)
        
        x1_inner = cx + inner_radius * math.cos(start_rad)
        y1_inner = cy + inner_radius * math.sin(start_rad)
        x2_inner = cx + inner_radius * math.cos(end_rad)
        y2_inner = cy + inner_radius * math.sin(end_rad)
        
        large_arc = 1 if angle > 180 else 0
        
        path = f'M {x1_outer:.2f} {y1_outer:.2f} '
        path += f'A {radius} {radius} 0 {large_arc} 1 {x2_outer:.2f} {y2_outer:.2f} '
        path += f'L {x2_inner:.2f} {y2_inner:.2f} '
        path += f'A {inner_radius} {inner_radius} 0 {large_arc} 0 {x1_inner:.2f} {y1_inner:.2f} '
        path += 'Z'
        
        svg_parts.append(f'<path class="pie-slice" d="{path}" fill="{color}" stroke="#1a1a2e" stroke-width="2" opacity="0.9">')
        svg_parts.append(f'<title>{escape_html(ext)}: {count} files ({percentage*100:.1f}%)</title>')
        svg_parts.append('</path>')
        
        start_angle = end_angle
    
    # Center circle with glow
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{inner_radius - 5}" fill="#1a1a2e" filter="url(#glow)"/>')
    svg_parts.append(f'<text x="{cx}" y="{cy - 8}" text-anchor="middle" fill="#fff" font-size="28" font-weight="bold">{total}</text>')
    svg_parts.append(f'<text x="{cx}" y="{cy + 14}" text-anchor="middle" fill="#888" font-size="12" text-transform="uppercase">files</text>')
    
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)


def generate_bar_chart(data, colors):
    """Generate an SVG horizontal bar chart"""
    if not data:
        return '<svg width="420" height="320"><text x="210" y="160" text-anchor="middle" fill="#666">No data</text></svg>'
    
    # Filter out zero values
    data = [(ext, count) for ext, count in data if count > 0]
    
    if not data:
        return '<svg width="420" height="320"><text x="210" y="160" text-anchor="middle" fill="#666">No data</text></svg>'
    
    max_value = max(count for _, count in data)
    if max_value == 0:
        max_value = 1
    
    width = 420
    height = 40 + len(data) * 38
    padding_left = 70
    padding_right = 70
    bar_height = 26
    gap = 12
    
    svg_parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    svg_parts.append('<defs>')
    for i, color in enumerate(colors):
        svg_parts.append(f'<linearGradient id="barGrad{i}" x1="0%" y1="0%" x2="100%" y2="0%">')
        svg_parts.append(f'<stop offset="0%" style="stop-color:{color};stop-opacity:1"/>')
        svg_parts.append(f'<stop offset="100%" style="stop-color:{color};stop-opacity:0.6"/>')
        svg_parts.append('</linearGradient>')
    svg_parts.append('</defs>')
    
    for i, (ext, count) in enumerate(data):
        y = 20 + i * (bar_height + gap)
        bar_width = max(4, (count / max_value) * (width - padding_left - padding_right))
        
        color_idx = i % len(colors)
        
        # Bar background
        svg_parts.append(f'<rect x="{padding_left}" y="{y}" width="{width - padding_left - padding_right}" height="{bar_height}" fill="rgba(255,255,255,0.03)" rx="4"/>')
        
        # Animated bar
        svg_parts.append(f'<rect class="bar" x="{padding_left}" y="{y}" width="{bar_width:.2f}" height="{bar_height}" fill="url(#barGrad{color_idx})" rx="4">')
        svg_parts.append(f'<title>{escape_html(ext)}: {count:,} lines</title>')
        svg_parts.append('</rect>')
        
        # Glow effect
        svg_parts.append(f'<rect x="{padding_left}" y="{y}" width="{bar_width:.2f}" height="{bar_height}" fill="{colors[color_idx]}" rx="4" opacity="0.3" filter="url(#glow)"/>')
        
        # Extension label
        svg_parts.append(f'<text x="{padding_left - 8}" y="{y + bar_height/2 + 5}" text-anchor="end" fill="#aaa" font-size="12" font-weight="500">{escape_html(ext)}</text>')
        
        # Value
        svg_parts.append(f'<text x="{width - 10}" y="{y + bar_height/2 + 5}" text-anchor="end" fill="#4ECDC4" font-size="12" font-family="monospace">{format_number(count)}</text>')
    
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)


def generate_legend(data, colors):
    """Generate legend HTML"""
    legend_html = ""
    for i, (ext, count) in enumerate(data):
        color = colors[i % len(colors)]
        legend_html += f'''
        <div class="legend-item">
            <span class="legend-color" style="background: {color};"></span>
            <span>{escape_html(ext)} ({count})</span>
        </div>
        '''
    return legend_html


def format_size(size):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            if unit == 'B':
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def format_number(num):
    """Format large numbers with K/M suffix"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)


def escape_html(text):
    """Escape HTML special characters"""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def generate_html(stats):
    """Generate the HTML infographic"""
    
    # Prepare data for charts
    ext_data = sorted(stats['file_count_by_ext'].items(), key=lambda x: x[1], reverse=True)[:10]
    lines_data = sorted(stats['lines_by_ext'].items(), key=lambda x: x[1], reverse=True)[:8]
    
    # Vibrant color palette
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8B500', '#FF8C94', '#91EAE4', '#FFA07A', '#98FB98'
    ]
    
    # Generate charts
    pie_svg = generate_pie_chart(ext_data, colors)
    bar_svg = generate_bar_chart(lines_data, colors)
    
    # Generate largest files list
    largest_files_html = ""
    for i, f in enumerate(stats['largest_files']):
        size_str = format_size(f['size'])
        lines_str = f"{f['lines']:,} lines" if f['lines'] > 0 else "binary"
        largest_files_html += f'''
        <div class="file-item">
            <span class="file-rank">#{i+1}</span>
            <div class="file-info">
                <span class="file-name" title="{escape_html(f['path'])}">{escape_html(f['name'])}</span>
                <span class="file-path">{escape_html(f['path'])}</span>
            </div>
            <div class="file-stats">
                <span class="file-size">{size_str}</span>
                <span class="file-lines">{lines_str}</span>
            </div>
        </div>
        '''
    
    # Extension breakdown for stats
    ext_breakdown = ""
    for i, (ext, count) in enumerate(ext_data[:6]):
        color = colors[i % len(colors)]
        pct = (count / stats['total_files'] * 100) if stats['total_files'] > 0 else 0
        ext_breakdown += f'''
        <div class="ext-item">
            <span class="ext-dot" style="background: {color};"></span>
            <span class="ext-name">{escape_html(ext)}</span>
            <span class="ext-count">{count}</span>
            <span class="ext-pct">{pct:.1f}%</span>
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #0d0d1a 0%, #1a1a2e 30%, #16213e 70%, #0f3460 100%);
            min-height: 100vh;
            color: #e4e4e4;
            padding: 20px;
            background-attachment: fixed;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 50px 20px 40px;
            position: relative;
        }}
        
        header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 200px;
            height: 4px;
            background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent);
            border-radius: 2px;
        }}
        
        h1 {{
            font-size: 3.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f64f59 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 12px;
            letter-spacing: -1px;
        }}
        
        .subtitle {{
            color: #666;
            font-size: 1.1rem;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        
        @media (max-width: 1200px) {{
            .dashboard {{
                grid-template-columns: repeat(3, 1fr);
            }}
        }}
        
        @media (max-width: 768px) {{
            .dashboard {{
                grid-template-columns: repeat(2, 1fr);
            }}
            h1 {{
                font-size: 2rem;
            }}
        }}
        
        .stat-card {{
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.08);
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
            background: linear-gradient(90deg, #667eea, #764ba2);
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-4px);
            border-color: rgba(102, 126, 234, 0.3);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }}
        
        .stat-card:hover::before {{
            opacity: 1;
        }}
        
        .stat-icon {{
            font-size: 1.5rem;
            margin-bottom: 8px;
        }}
        
        .stat-number {{
            font-size: 2.4rem;
            font-weight: 700;
            background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
        }}
        
        .stat-label {{
            color: #888;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-top: 6px;
        }}
        
        .main-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }}
        
        @media (max-width: 900px) {{
            .main-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .card {{
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            border-radius: 20px;
            padding: 28px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
        }}
        
        .card-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 24px;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .card-title::before {{
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(180deg, #667eea, #764ba2);
            border-radius: 2px;
        }}
        
        .chart-wrapper {{
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px 0;
        }}
        
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 24px;
            justify-content: center;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            color: #bbb;
            padding: 4px 10px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 20px;
        }}
        
        .legend-color {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }}
        
        .files-card {{
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            border-radius: 20px;
            padding: 28px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        
        .file-item {{
            display: flex;
            align-items: center;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 12px;
            margin-bottom: 10px;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }}
        
        .file-item:hover {{
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(102, 126, 234, 0.2);
            transform: translateX(4px);
        }}
        
        .file-rank {{
            color: #667eea;
            font-weight: 700;
            font-size: 0.9rem;
            width: 36px;
            flex-shrink: 0;
        }}
        
        .file-info {{
            flex: 1;
            min-width: 0;
            margin-right: 16px;
        }}
        
        .file-name {{
            color: #fff;
            font-weight: 500;
            display: block;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .file-path {{
            color: #555;
            font-size: 0.75rem;
            display: block;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-top: 2px;
        }}
        
        .file-stats {{
            text-align: right;
            flex-shrink: 0;
        }}
        
        .file-size {{
            color: #4ECDC4;
            font-weight: 600;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.9rem;
            display: block;
        }}
        
        .file-lines {{
            color: #666;
            font-size: 0.75rem;
        }}
        
        .ext-breakdown {{
            margin-top: 20px;
        }}
        
        .ext-item {{
            display: flex;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }}
        
        .ext-item:last-child {{
            border-bottom: none;
        }}
        
        .ext-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        
        .ext-name {{
            flex: 1;
            color: #ccc;
        }}
        
        .ext-count {{
            color: #888;
            margin-right: 16px;
            font-family: monospace;
        }}
        
        .ext-pct {{
            color: #4ECDC4;
            font-weight: 500;
            font-family: monospace;
            width: 50px;
            text-align: right;
        }}
        
        svg text {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        
        .pie-slice {{
            transition: all 0.2s ease;
            cursor: pointer;
        }}
        
        .pie-slice:hover {{
            opacity: 1 !important;
            filter: brightness(1.2);
        }}
        
        .bar {{
            transition: all 0.3s ease;
        }}
        
        footer {{
            text-align: center;
            padding: 40px 20px;
            color: #444;
            font-size: 0.85rem;
        }}
        
        footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        .glow {{
            animation: pulse 2s ease-in-out infinite alternate;
        }}
        
        @keyframes pulse {{
            from {{ opacity: 0.5; }}
            to {{ opacity: 1; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔬 Codebase Fingerprint</h1>
            <p class="subtitle">Visual Analysis of Your Project</p>
        </header>
        
        <div class="dashboard">
            <div class="stat-card">
                <div class="stat-icon">📁</div>
                <div class="stat-number">{stats['total_files']:,}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📝</div>
                <div class="stat-number">{stats['total_lines']:,}</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🏷️</div>
                <div class="stat-number">{len(stats['file_count_by_ext'])}</div>
                <div class="stat-label">File Types</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📂</div>
                <div class="stat-number">{stats['directory_count']}</div>
                <div class="stat-label">Directories</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🌳</div>
                <div class="stat-number">{stats['max_depth']}</div>
                <div class="stat-label">Max Depth</div>
            </div>
        </div>
        
        <div class="main-grid">
            <div class="card">
                <div class="card-title">File Types Distribution</div>
                <div class="chart-wrapper">
                    {pie_svg}
                </div>
                <div class="legend">
                    {generate_legend(ext_data, colors)}
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">Lines of Code by Type</div>
                <div class="chart-wrapper">
                    {bar_svg}
                </div>
            </div>
        </div>
        
        <div class="files-card">
            <div class="card-title">📊 Largest Files</div>
            {largest_files_html if largest_files_html else '<p style="color: #666; text-align: center; padding: 20px;">No files found</p>'}
        </div>
        
        <footer>
            Generated with Python • Codebase Fingerprint Generator<br>
            <span style="color: #333;">Scanned {stats['directory_count']} directories • {stats['total_files']} files • {stats['total_lines']:,} lines</span>
        </footer>
    </div>
    
    <script>
        // Add interactivity to pie slices
        document.querySelectorAll('.pie-slice').forEach((slice, index) => {{
            slice.addEventListener('mouseenter', function() {{
                this.style.transform = 'scale(1.03)';
                this.style.transformOrigin = 'center';
            }});
            slice.addEventListener('mouseleave', function() {{
                this.style.transform = 'scale(1)';
            }});
        }});
        
        // Animate bars on load
        document.querySelectorAll('.bar').forEach((bar, index) => {{
            const width = bar.getAttribute('width');
            bar.setAttribute('width', '0');
            setTimeout(() => {{
                bar.style.transition = 'width 0.8s ease-out';
                bar.setAttribute('width', width);
            }}, index * 100);
        }});
        
        // Add smooth scroll reveal
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }}
            }});
        }});
        
        document.querySelectorAll('.stat-card, .card, .files-card').forEach(el => {{
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'all 0.5s ease-out';
            observer.observe(el);
        }});
        
        // Trigger initial animation
        setTimeout(() => {{
            document.querySelectorAll('.stat-card, .card, .files-card').forEach((el, i) => {{
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
    print("🔬 Codebase Fingerprint Generator")
    print("=" * 40)
    print("\n📂 Scanning directory...")
    
    stats = scan_directory(".")
    
    print(f"   ✓ Found {stats['total_files']:,} files")
    print(f"   ✓ Found {stats['total_lines']:,} lines of code")
    print(f"   ✓ Found {len(stats['file_count_by_ext'])} file types")
    print(f"   ✓ Found {stats['directory_count']} directories")
    print(f"   ✓ Maximum depth: {stats['max_depth']} levels")
    
    print("\n📊 Generating infographic...")
    html = generate_html(stats)
    
    output_file = "stats.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"\n✅ Success! Generated: {output_file}")
    print(f"   Open in your browser to view the infographic.\n")


if __name__ == "__main__":
    main()