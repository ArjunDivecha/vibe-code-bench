#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Generates a beautiful HTML infographic from codebase statistics
"""

import os
import math
from collections import defaultdict
from datetime import datetime


def scan_directory(root_path='.'):
    """Recursively scan directory and collect statistics"""
    stats = {
        'files_by_ext': defaultdict(int),
        'lines_by_ext': defaultdict(int),
        'total_files': 0,
        'total_lines': 0,
        'total_size': 0,
        'largest_files': [],
        'max_depth': 0,
        'directories': 0
    }
    
    # Common text file extensions for line counting
    text_extensions = {
        '.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.txt',
        '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
        '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rs',
        '.ts', '.tsx', '.jsx', '.vue', '.svelte',
        '.php', '.rb', '.pl', '.sh', '.bash', '.zsh',
        '.sql', '.graphql', '.prisma', '.scss', '.sass', '.less',
        '.dockerfile', '.gitignore', '.env', '.mk', '.cmake'
    }
    
    skip_dirs = {
        'node_modules', '__pycache__', 'venv', 'env', '.git', 
        'dist', 'build', '.idea', '.vscode', 'target', 'vendor',
        '.next', '.nuxt', 'coverage', '.tox', 'eggs', '.eggs'
    }
    
    root_depth = root_path.rstrip(os.sep).count(os.sep)
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip hidden and common non-source directories
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in skip_dirs]
        
        current_depth = dirpath.rstrip(os.sep).count(os.sep) - root_depth
        stats['max_depth'] = max(stats['max_depth'], current_depth)
        stats['directories'] += 1
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
                
            filepath = os.path.join(dirpath, filename)
            
            # Get extension
            _, ext = os.path.splitext(filename)
            ext = ext.lower() if ext else '(no ext)'
            
            stats['files_by_ext'][ext] += 1
            stats['total_files'] += 1
            
            try:
                file_size = os.path.getsize(filepath)
                stats['total_size'] += file_size
                
                # Count lines for text files
                lines = 0
                if ext in text_extensions or ext == '(no ext)':
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = sum(1 for _ in f)
                            stats['lines_by_ext'][ext] += lines
                            stats['total_lines'] += lines
                    except:
                        pass
                
                stats['largest_files'].append({
                    'path': filepath,
                    'size': file_size,
                    'lines': lines,
                    'ext': ext
                })
            except:
                pass
    
    # Sort and limit largest files
    stats['largest_files'].sort(key=lambda x: x['size'], reverse=True)
    stats['largest_files'] = stats['largest_files'][:10]
    
    return stats


def format_size(size):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def escape_html(text):
    """Escape HTML special characters"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def generate_pie_chart(data, colors):
    """Generate an SVG pie chart with legend"""
    if not data:
        return '<p style="color: #666; text-align: center;">No data available</p>'
    
    total = sum(data.values())
    if total == 0:
        return '<p style="color: #666; text-align: center;">No data available</p>'
    
    cx, cy, r = 120, 120, 100
    svg_parts = [f'<svg width="240" height="240" viewBox="0 0 240 240" style="filter: drop-shadow(0 4px 20px rgba(0,0,0,0.3));">']
    
    # Add background circle
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r+5}" fill="rgba(255,255,255,0.02)"/>')
    
    start_angle = -90
    legend_items = []
    
    items = list(data.items())
    
    for i, (ext, count) in enumerate(items):
        percentage = count / total
        angle = percentage * 360
        
        if angle < 0.5:  # Skip tiny slices
            continue
        
        end_angle = start_angle + angle
        
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        x1 = cx + r * math.cos(start_rad)
        y1 = cy + r * math.sin(start_rad)
        x2 = cx + r * math.cos(end_rad)
        y2 = cy + r * math.sin(end_rad)
        
        large_arc = 1 if angle > 180 else 0
        color = colors[i % len(colors)]
        
        if len(items) == 1:
            # Full circle for single item
            svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" class="pie-segment" style="cursor: pointer;"><title>{escape_html(ext)}: {count} files ({percentage*100:.1f}%)</title></circle>')
        else:
            path = f'M {cx},{cy} L {x1:.2f},{y1:.2f} A {r},{r} 0 {large_arc},1 {x2:.2f},{y2:.2f} Z'
            svg_parts.append(f'<path class="pie-segment" d="{path}" fill="{color}" stroke="#1a1a2e" stroke-width="2" style="cursor: pointer;"><title>{escape_html(ext)}: {count} files ({percentage*100:.1f}%)</title></path>')
        
        legend_items.append(f'''
            <div class="legend-item">
                <span class="legend-color" style="background: {color};"></span>
                <span class="legend-ext">{escape_html(ext)}</span>
                <span class="legend-count">{count}</span>
                <span class="legend-pct">{percentage*100:.1f}%</span>
            </div>
        ''')
        
        start_angle = end_angle
    
    # Center hole for donut effect
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r*0.5}" fill="#1a1a2e"/>')
    svg_parts.append(f'<text x="{cx}" y="{cy-5}" text-anchor="middle" fill="#fff" font-size="24" font-weight="bold">{total}</text>')
    svg_parts.append(f'<text x="{cx}" y="{cy+15}" text-anchor="middle" fill="#888" font-size="11">FILES</text>')
    svg_parts.append('</svg>')
    
    legend_html = '<div class="legend">' + ''.join(legend_items) + '</div>'
    
    return ''.join(svg_parts) + legend_html


def generate_bar_chart(data, colors):
    """Generate an SVG horizontal bar chart"""
    if not data:
        return '<p style="color: #666; text-align: center;">No code files found</p>'
    
    max_value = max(data.values()) if data else 1
    if max_value == 0:
        return '<p style="color: #666; text-align: center;">No lines counted</p>'
    
    bar_height = 32
    spacing = 12
    label_width = 70
    value_width = 70
    chart_width = 300
    padding = 20
    chart_height = len(data) * (bar_height + spacing) + padding
    total_width = label_width + chart_width + value_width + 20
    
    svg_parts = [f'<svg class="bar-chart" viewBox="0 0 {total_width} {chart_height}" style="width: 100%; max-width: {total_width}px;">']
    
    for i, (ext, count) in enumerate(data.items()):
        y = i * (bar_height + spacing) + padding/2
        bar_width = max((count / max_value) * chart_width, 4)
        color = colors[i % len(colors)]
        
        # Background bar
        svg_parts.append(f'<rect x="{label_width}" y="{y}" width="{chart_width}" height="{bar_height}" rx="6" fill="rgba(255,255,255,0.05)"/>')
        
        # Actual bar with gradient effect
        svg_parts.append(f'''
            <defs>
                <linearGradient id="grad{i}" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                    <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
                </linearGradient>
            </defs>
        ''')
        svg_parts.append(f'<rect x="{label_width}" y="{y}" width="{bar_width:.1f}" height="{bar_height}" rx="6" fill="url(#grad{i})" class="bar-rect"><title>{escape_html(ext)}: {count:,} lines</title></rect>')
        
        # Label
        svg_parts.append(f'<text x="{label_width - 8}" y="{y + bar_height/2 + 5}" fill="#aaa" font-size="13" text-anchor="end" font-family="monospace">{escape_html(ext)}</text>')
        
        # Value
        if count >= 1000000:
            formatted = f'{count/1000000:.1f}M'
        elif count >= 1000:
            formatted = f'{count/1000:.1f}k'
        else:
            formatted = str(count)
        svg_parts.append(f'<text x="{label_width + chart_width + 12}" y="{y + bar_height/2 + 5}" fill="#fff" font-size="13" font-weight="bold">{formatted}</text>')
    
    svg_parts.append('</svg>')
    return ''.join(svg_parts)


def generate_depth_visualization(max_depth):
    """Generate a visual representation of directory depth"""
    if max_depth == 0:
        return '<div class="depth-bar"><div class="depth-fill" style="width: 10%;"></div></div>'
    
    levels = min(max_depth, 10)
    width_pct = (levels / 10) * 100
    
    bars = []
    for i in range(levels):
        opacity = 1 - (i * 0.08)
        bars.append(f'<div class="depth-level" style="opacity: {opacity}; animation-delay: {i * 0.1}s;"></div>')
    
    return f'<div class="depth-visual">{"".join(bars)}</div>'


def generate_html(stats):
    """Generate the complete HTML infographic"""
    
    # Prepare chart data
    files_by_ext = dict(sorted(stats['files_by_ext'].items(), key=lambda x: x[1], reverse=True)[:10])
    lines_by_ext = dict(sorted(stats['lines_by_ext'].items(), key=lambda x: x[1], reverse=True)[:8])
    
    # Vibrant color palette
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#F39C12', '#3498DB', '#E74C3C', '#2ECC71',
        '#9B59B6', '#1ABC9C', '#E67E22', '#34495E', '#16A085'
    ]
    
    pie_svg = generate_pie_chart(files_by_ext, colors)
    bar_svg = generate_bar_chart(lines_by_ext, colors)
    
    # Generate largest files HTML
    largest_files_html = ""
    for i, f in enumerate(stats['largest_files']):
        path = f['path']
        if path.startswith('./'):
            path = path[2:]
        if len(path) > 50:
            path = '...' + path[-47:]
        
        lines_info = f" • {f['lines']:,} lines" if f['lines'] > 0 else ""
        color = colors[i % len(colors)]
        
        largest_files_html += f'''
            <div class="file-item" style="--accent-color: {color};">
                <span class="file-rank">#{i+1}</span>
                <div class="file-info">
                    <span class="file-path">{escape_html(path)}</span>
                    <span class="file-meta">{escape_html(f['ext'])}{lines_info}</span>
                </div>
                <span class="file-size">{format_size(f['size'])}</span>
            </div>
        '''
    
    # File types summary for stats card
    top_types = list(files_by_ext.keys())[:3]
    top_types_str = ', '.join(top_types) if top_types else 'None'
    
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
        
        :root {{
            --bg-primary: #0a0a12;
            --bg-secondary: #12121f;
            --bg-card: rgba(255, 255, 255, 0.03);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #ffffff;
            --text-secondary: #888899;
            --accent-1: #FF6B6B;
            --accent-2: #4ECDC4;
            --accent-3: #45B7D1;
            --accent-4: #FFEAA7;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
            min-height: 100vh;
            color: var(--text-primary);
            padding: 2rem;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        /* Header */
        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 3rem 2rem;
            background: var(--bg-card);
            border-radius: 24px;
            border: 1px solid var(--border-color);
            position: relative;
            overflow: hidden;
        }}
        
        header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 200px;
            height: 3px;
            background: linear-gradient(90deg, var(--accent-1), var(--accent-2), var(--accent-3));
            border-radius: 0 0 3px 3px;
        }}
        
        .logo {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        
        h1 {{
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-1), var(--accent-2), var(--accent-3));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.5px;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1rem;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            background: var(--bg-card);
            border-radius: 20px;
            padding: 1.8rem;
            text-align: center;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .stat-card::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--card-accent);
            opacity: 0.8;
        }}
        
        .stat-card:nth-child(1) {{ --card-accent: var(--accent-1); }}
        .stat-card:nth-child(2) {{ --card-accent: var(--accent-2); }}
        .stat-card:nth-child(3) {{ --card-accent: var(--accent-3); }}
        .stat-card:nth-child(4) {{ --card-accent: var(--accent-4); }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            border-color: var(--card-accent);
        }}
        
        .stat-icon {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--card-accent);
            margin-bottom: 0.3rem;
            font-variant-numeric: tabular-nums;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 600;
        }}
        
        /* Charts Grid */
        .charts-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }}
        
        .chart-card {{
            background: var(--bg-card);
            border-radius: 24px;
            padding: 2rem;
            border: 1px solid var(--border-color);
        }}
        
        .chart-title {{
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .chart-title::before {{
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(180deg, var(--accent-1), var(--accent-2));
            border-radius: 2px;
        }}
        
        .chart-container {{
            display: flex;
            align-items: flex-start;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
        }}
        
        /* Pie Chart Legend */
        .legend {{
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
            min-width: 150px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            font-size: 0.85rem;
            padding: 0.4rem 0.6rem;
            border-radius: 8px;
            transition: background 0.2s;
        }}
        
        .legend-item:hover {{
            background: rgba(255, 255, 255, 0.05);
        }}
        
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 4px;
            flex-shrink: 0;
        }}
        
        .legend-ext {{
            flex: 1;
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            color: var(--text-secondary);
        }}
        
        .legend-count {{
            color: var(--text-primary);
            font-weight: 600;
        }}
        
        .legend-pct {{
            color: var(--text-secondary);
            font-size: 0.75rem;
            min-width: 40px;
            text-align: right;
        }}
        
        /* Bar Chart */
        .bar-chart {{
            width: 100%;
        }}
        
        .bar-rect {{
            transition: opacity 0.2s;
        }}
        
        .bar-rect:hover {{
            opacity: 0.8;
        }}
        
        /* Files List */
        .files-card {{
            background: var(--bg-card);
            border-radius: 24px;
            padding: 2rem;
            border: 1px solid var(--border-color);
        }}
        
        .file-item {{
            display: flex;
            align-items: center;
            padding: 1rem 1.2rem;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 12px;
            margin-bottom: 0.6rem;
            border: 1px solid transparent;
            transition: all 0.2s;
        }}
        
        .file-item:hover {{
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--accent-color, var(--border-color));
            transform: translateX(5px);
        }}
        
        .file-rank {{
            color: var(--accent-color, var(--accent-2));
            font-weight: 800;
            font-size: 0.9rem;
            width: 36px;
            flex-shrink: 0;
        }}
        
        .file-info {{
            flex: 1;
            min-width: 0;
        }}
        
        .file-path {{
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            font-size: 0.9rem;
            color: var(--text-primary);
            display: block;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .file-meta {{
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}
        
        .file-size {{
            color: var(--accent-color, var(--accent-1));
            font-weight: 700;
            font-size: 0.9rem;
            padding-left: 1rem;
            flex-shrink: 0;
        }}
        
        /* Footer */
        footer {{
            text-align: center;
            margin-top: 3rem;
            padding: 2rem;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}
        
        footer span {{
            color: var(--accent-2);
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .stat-card, .chart-card, .files-card {{
            animation: fadeIn 0.6s ease-out backwards;
        }}
        
        .stat-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .stat-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .stat-card:nth-child(3) {{ animation-delay: 0.3s; }}
        .stat-card:nth-child(4) {{ animation-delay: 0.4s; }}
        .chart-card:nth-child(1) {{ animation-delay: 0.5s; }}
        .chart-card:nth-child(2) {{ animation-delay: 0.6s; }}
        .files-card {{ animation-delay: 0.7s; }}
        
        /* Responsive */
        @media (max-width: 1100px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        @media (max-width: 900px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 600px) {{
            body {{
                padding: 1rem;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            h1 {{
                font-size: 2rem;
            }}
            
            .stat-value {{
                font-size: 2rem;
            }}
            
            .chart-container {{
                flex-direction: column;
                align-items: center;
            }}
        }}
        
        /* Pie segment hover */
        .pie-segment {{
            transition: transform 0.2s, filter 0.2s;
            transform-origin: center;
        }}
        
        .pie-segment:hover {{
            filter: brightness(1.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">🔬</div>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">Analysis generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">📄</div>
                <div class="stat-value">{stats['total_files']:,}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💻</div>
                <div class="stat-value">{stats['total_lines']:,}</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💾</div>
                <div class="stat-value">{format_size(stats['total_size'])}</div>
                <div class="stat-label">Total Size</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📁</div>
                <div class="stat-value">{stats['max_depth']}</div>
                <div class="stat-label">Max Depth</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h2 class="chart-title">File Types Distribution</h2>
                <div class="chart-container">
                    {pie_svg}
                </div>
            </div>
            <div class="chart-card">
                <h2 class="chart-title">Lines of Code by Type</h2>
                <div class="chart-container">
                    {bar_svg}
                </div>
            </div>
        </div>
        
        <div class="files-card">
            <h2 class="chart-title">Largest Files</h2>
            {largest_files_html if largest_files_html else '<p style="color: var(--text-secondary); padding: 2rem; text-align: center;">No files found in the scanned directory</p>'}
        </div>
        
        <footer>
            <p>Scanned <span>{stats['directories']}</span> directories • Top file types: <span>{escape_html(top_types_str)}</span></p>
            <p style="margin-top: 0.5rem; opacity: 0.7;">Generated by Codebase Fingerprint</p>
        </footer>
    </div>
    
    <script>
        // Interactive enhancements
        document.addEventListener('DOMContentLoaded', function() {{
            // Animate stat values on scroll
            const observerOptions = {{
                threshold: 0.5
            }};
            
            const observer = new IntersectionObserver((entries) => {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting) {{
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }}
                }});
            }}, observerOptions);
            
            document.querySelectorAll('.stat-card, .chart-card, .files-card').forEach(el => {{
                observer.observe(el);
            }});
            
            // Pie chart segment hover effects
            const pieSegments = document.querySelectorAll('.pie-segment');
            const legendItems = document.querySelectorAll('.legend-item');
            
            pieSegments.forEach((segment, i) => {{
                segment.addEventListener('mouseenter', () => {{
                    if (legendItems[i]) {{
                        legendItems[i].style.background = 'rgba(255,255,255,0.1)';
                    }}
                }});
                segment.addEventListener('mouseleave', () => {{
                    if (legendItems[i]) {{
                        legendItems[i].style.background = '';
                    }}
                }});
            }});
            
            // File item click to copy path
            document.querySelectorAll('.file-item').forEach(item => {{
                item.style.cursor = 'pointer';
                item.addEventListener('click', function() {{
                    const path = this.querySelector('.file-path').textContent;
                    if (navigator.clipboard) {{
                        navigator.clipboard.writeText(path);
                        const original = this.style.borderColor;
                        this.style.borderColor = '#4ECDC4';
                        setTimeout(() => {{
                            this.style.borderColor = original;
                        }}, 500);
                    }}
                }});
            }});
        }});
    </script>
</body>
</html>
'''
    return html


def main():
    """Main entry point"""
    print("🔬 Codebase Fingerprint Generator")
    print("=" * 40)
    print()
    
    print("📂 Scanning directory...")
    stats = scan_directory('.')
    
    print(f"   ├─ Found {stats['total_files']:,} files")
    print(f"   ├─ In {stats['directories']:,} directories")
    print(f"   ├─ {stats['total_lines']:,} lines of code")
    print(f"   ├─ {format_size(stats['total_size'])} total size")
    print(f"   └─ Max depth: {stats['max_depth']} levels")
    print()
    
    print("🎨 Generating infographic...")
    html = generate_html(stats)
    
    output_file = 'stats.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Generated: {output_file}")
    print()
    print("Open stats.html in your browser to view the infographic!")


if __name__ == '__main__':
    main()