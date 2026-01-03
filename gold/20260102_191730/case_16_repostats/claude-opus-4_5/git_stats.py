#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Generates a beautiful HTML infographic of codebase statistics
"""

import os
import math
import html
from collections import defaultdict
from pathlib import Path


def scan_directory(root_path="."):
    """Recursively scan directory and collect statistics"""
    stats = {
        'files_by_extension': defaultdict(int),
        'lines_by_extension': defaultdict(int),
        'largest_files': [],
        'total_files': 0,
        'total_lines': 0,
        'max_depth': 0,
        'total_dirs': 0,
    }
    
    root_path = Path(root_path).resolve()
    root_depth = len(root_path.parts)
    
    # Directories to skip
    skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.idea', '.vscode', 'dist', 'build', '.cache'}
    
    # Binary extensions to skip
    binary_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.exe', '.dll', 
        '.so', '.dylib', '.zip', '.tar', '.gz', '.rar', '.7z', '.mp3', 
        '.mp4', '.wav', '.avi', '.mov', '.ttf', '.woff', '.woff2', '.eot',
        '.pyc', '.pyo', '.class', '.o', '.a', '.lib', '.bin', '.dat'
    }
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip certain directories
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        
        current_path = Path(dirpath)
        depth = len(current_path.parts) - root_depth
        stats['max_depth'] = max(stats['max_depth'], depth)
        stats['total_dirs'] += 1
        
        for filename in filenames:
            filepath = current_path / filename
            ext = filepath.suffix.lower() or '(no ext)'
            
            if ext in binary_extensions:
                continue
            
            # Skip hidden files
            if filename.startswith('.'):
                continue
                
            stats['files_by_extension'][ext] += 1
            stats['total_files'] += 1
            
            # Count lines
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = sum(1 for _ in f)
                    stats['lines_by_extension'][ext] += lines
                    stats['total_lines'] += lines
                    
                    # Track file size for largest files
                    file_size = filepath.stat().st_size
                    rel_path = filepath.relative_to(root_path)
                    stats['largest_files'].append({
                        'path': str(rel_path),
                        'lines': lines,
                        'size': file_size
                    })
            except (IOError, OSError):
                pass
    
    # Sort and keep top 10 largest files by lines
    stats['largest_files'].sort(key=lambda x: x['lines'], reverse=True)
    stats['largest_files'] = stats['largest_files'][:10]
    
    return stats


def generate_pie_chart_svg(data, width=300, height=300):
    """Generate SVG pie chart with smooth gradients"""
    if not data:
        return f'<svg width="{width}" height="{height}"><text x="50%" y="50%" text-anchor="middle" fill="#888">No data</text></svg>'
    
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', 
        '#F8B500', '#00CED1', '#E74C3C', '#9B59B6', '#1ABC9C'
    ]
    
    cx, cy = width // 2, height // 2
    radius = min(width, height) // 2 - 30
    inner_radius = radius * 0.6  # Donut chart
    
    total = sum(data.values())
    if total == 0:
        return f'<svg width="{width}" height="{height}"><text x="50%" y="50%" text-anchor="middle" fill="#888">No data</text></svg>'
    
    svg_parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    
    # Add definitions for gradients
    svg_parts.append('<defs>')
    for i, color in enumerate(colors):
        svg_parts.append(f'''
        <linearGradient id="grad{i}" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
            <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
        </linearGradient>''')
    svg_parts.append('</defs>')
    
    start_angle = -90
    items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:12]
    
    for i, (label, value) in enumerate(items):
        if value == 0:
            continue
        percentage = value / total
        angle = percentage * 360
        
        start_rad = math.radians(start_angle)
        end_rad = math.radians(start_angle + angle)
        
        # Outer arc
        x1_outer = cx + radius * math.cos(start_rad)
        y1_outer = cy + radius * math.sin(start_rad)
        x2_outer = cx + radius * math.cos(end_rad)
        y2_outer = cy + radius * math.sin(end_rad)
        
        # Inner arc
        x1_inner = cx + inner_radius * math.cos(start_rad)
        y1_inner = cy + inner_radius * math.sin(start_rad)
        x2_inner = cx + inner_radius * math.cos(end_rad)
        y2_inner = cy + inner_radius * math.sin(end_rad)
        
        large_arc = 1 if angle > 180 else 0
        
        if percentage >= 0.999:
            # Full circle (donut)
            svg_parts.append(f'''
            <circle cx="{cx}" cy="{cy}" r="{radius}" fill="url(#grad{i % len(colors)})" />
            <circle cx="{cx}" cy="{cy}" r="{inner_radius}" fill="#1a1a2e" />''')
        else:
            # Donut segment
            path = f'''M {x1_outer},{y1_outer} 
                       A {radius},{radius} 0 {large_arc},1 {x2_outer},{y2_outer}
                       L {x2_inner},{y2_inner}
                       A {inner_radius},{inner_radius} 0 {large_arc},0 {x1_inner},{y1_inner}
                       Z'''
            svg_parts.append(f'<path d="{path}" fill="url(#grad{i % len(colors)})" stroke="#1a1a2e" stroke-width="2" class="pie-slice" data-label="{html.escape(label)}" data-value="{value}"/>')
        
        start_angle += angle
    
    # Center text
    svg_parts.append(f'''
    <text x="{cx}" y="{cy - 10}" text-anchor="middle" fill="#fff" font-size="24" font-weight="bold">{total:,}</text>
    <text x="{cx}" y="{cy + 15}" text-anchor="middle" fill="#888" font-size="12">files</text>
    ''')
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def generate_bar_chart_svg(data, width=500, height=320):
    """Generate SVG horizontal bar chart"""
    if not data:
        return f'<svg width="{width}" height="{height}"><text x="50%" y="50%" text-anchor="middle" fill="#888">No data</text></svg>'
    
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    
    items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    if not items:
        return f'<svg width="{width}" height="{height}"><text x="50%" y="50%" text-anchor="middle" fill="#888">No data</text></svg>'
    
    max_value = max(v for _, v in items) if items else 1
    
    padding_left = 90
    padding_right = 80
    padding_top = 20
    padding_bottom = 20
    
    chart_width = width - padding_left - padding_right
    chart_height = height - padding_top - padding_bottom
    
    bar_height = min(28, (chart_height - 20) // len(items))
    gap = 8
    
    svg_parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    
    # Add gradient definitions
    svg_parts.append('<defs>')
    for i, color in enumerate(colors):
        svg_parts.append(f'''
        <linearGradient id="barGrad{i}" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
            <stop offset="100%" style="stop-color:{color};stop-opacity:0.6" />
        </linearGradient>''')
    svg_parts.append('</defs>')
    
    for i, (label, value) in enumerate(items):
        bar_width = (value / max_value) * chart_width if max_value > 0 else 0
        y = padding_top + i * (bar_height + gap)
        
        # Label
        display_label = label if len(label) <= 10 else label[:8] + '..'
        svg_parts.append(f'<text x="{padding_left - 10}" y="{y + bar_height/2 + 5}" text-anchor="end" fill="#ccc" font-size="13" font-family="monospace">{html.escape(display_label)}</text>')
        
        # Bar background
        svg_parts.append(f'<rect x="{padding_left}" y="{y}" width="{chart_width}" height="{bar_height}" fill="rgba(255,255,255,0.03)" rx="5"/>')
        
        # Bar
        if bar_width > 0:
            svg_parts.append(f'<rect x="{padding_left}" y="{y}" width="{bar_width}" height="{bar_height}" fill="url(#barGrad{i % len(colors)})" rx="5" class="bar-rect"/>')
        
        # Value
        formatted_value = f"{value:,}"
        svg_parts.append(f'<text x="{padding_left + bar_width + 10}" y="{y + bar_height/2 + 5}" fill="#888" font-size="12">{formatted_value}</text>')
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def format_number(n):
    """Format large numbers with K/M suffix"""
    if n >= 1000000:
        return f"{n/1000000:.1f}M"
    elif n >= 1000:
        return f"{n/1000:.1f}K"
    return str(n)


def generate_html(stats):
    """Generate the HTML infographic"""
    
    # Prepare pie chart data
    pie_data = dict(stats['files_by_extension'])
    pie_chart = generate_pie_chart_svg(pie_data, 300, 300)
    
    # Prepare bar chart data (lines by extension)
    bar_data = dict(stats['lines_by_extension'])
    bar_chart = generate_bar_chart_svg(bar_data, 520, 340)
    
    # Generate legend for pie chart
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', 
        '#F8B500', '#00CED1', '#E74C3C', '#9B59B6', '#1ABC9C'
    ]
    legend_items = sorted(pie_data.items(), key=lambda x: x[1], reverse=True)[:12]
    
    legend_html = ''
    total_files = sum(pie_data.values())
    for i, (ext, count) in enumerate(legend_items):
        pct = (count / total_files * 100) if total_files > 0 else 0
        legend_html += f'''
        <div class="legend-item">
            <span class="legend-color" style="background: {colors[i % len(colors)]};"></span>
            <span class="legend-label">{html.escape(ext)}</span>
            <span class="legend-value">{count} <span class="legend-pct">({pct:.1f}%)</span></span>
        </div>'''
    
    # Generate largest files list
    largest_files_html = ''
    for idx, f in enumerate(stats['largest_files']):
        largest_files_html += f'''
        <div class="file-item" style="animation-delay: {idx * 0.05}s">
            <div class="file-rank">#{idx + 1}</div>
            <div class="file-info">
                <span class="file-path">{html.escape(f['path'])}</span>
                <span class="file-size">{f['size']:,} bytes</span>
            </div>
            <span class="file-lines">{f['lines']:,} lines</span>
        </div>'''
    
    # Calculate average lines per file
    avg_lines = stats['total_lines'] // stats['total_files'] if stats['total_files'] > 0 else 0
    
    # Most common extension
    most_common_ext = max(stats['files_by_extension'].items(), key=lambda x: x[1])[0] if stats['files_by_extension'] else 'N/A'
    
    html_content = f'''<!DOCTYPE html>
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
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --border-color: #30363d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --accent-1: #FF6B6B;
            --accent-2: #4ECDC4;
            --accent-3: #45B7D1;
            --accent-4: #FFEAA7;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            text-align: center;
            padding: 60px 20px 40px;
            position: relative;
        }}
        
        header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
            height: 300px;
            background: radial-gradient(ellipse at center top, rgba(78, 205, 196, 0.15) 0%, transparent 70%);
            pointer-events: none;
        }}
        
        .logo {{
            font-size: 4rem;
            margin-bottom: 20px;
            animation: float 3s ease-in-out infinite;
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
        }}
        
        h1 {{
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-1), var(--accent-2), var(--accent-3));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 15px;
            letter-spacing: -1px;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.2rem;
            max-width: 500px;
            margin: 0 auto;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 20px;
            margin-top: 20px;
        }}
        
        .card {{
            background: var(--bg-secondary);
            border-radius: 16px;
            padding: 28px;
            border: 1px solid var(--border-color);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        
        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--accent-1), var(--accent-2), var(--accent-3));
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            border-color: var(--accent-2);
        }}
        
        .card:hover::before {{
            opacity: 1;
        }}
        
        .card-title {{
            font-size: 1rem;
            color: var(--text-secondary);
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .card-title svg {{
            width: 20px;
            height: 20px;
        }}
        
        /* Grid layout for cards */
        .card-stats {{ grid-column: span 6; }}
        .card-pie {{ grid-column: span 6; }}
        .card-bar {{ grid-column: span 7; }}
        .card-files {{ grid-column: span 5; }}
        
        @media (max-width: 1200px) {{
            .card-stats, .card-pie, .card-bar, .card-files {{
                grid-column: span 12;
            }}
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}
        
        .stat-box {{
            background: var(--bg-tertiary);
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }}
        
        .stat-box:hover {{
            border-color: var(--accent-2);
            background: rgba(78, 205, 196, 0.05);
        }}
        
        .stat-icon {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        
        .stat-value {{
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-4), var(--accent-1));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-top: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* Pie Chart Section */
        .pie-section {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: flex-start;
            gap: 30px;
        }}
        
        .chart-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        
        .legend {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 300px;
            overflow-y: auto;
            padding-right: 10px;
        }}
        
        .legend::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .legend::-webkit-scrollbar-track {{
            background: var(--bg-tertiary);
            border-radius: 3px;
        }}
        
        .legend::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 3px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.9rem;
            padding: 6px 10px;
            border-radius: 8px;
            transition: background 0.2s ease;
        }}
        
        .legend-item:hover {{
            background: var(--bg-tertiary);
        }}
        
        .legend-color {{
            width: 14px;
            height: 14px;
            border-radius: 4px;
            flex-shrink: 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        .legend-label {{
            color: var(--text-primary);
            font-family: 'SF Mono', Monaco, monospace;
            min-width: 70px;
        }}
        
        .legend-value {{
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}
        
        .legend-pct {{
            color: var(--accent-2);
        }}
        
        /* Bar Chart */
        .bar-chart-container {{
            width: 100%;
            overflow-x: auto;
            padding: 10px 0;
        }}
        
        .bar-chart-container svg {{
            display: block;
            margin: 0 auto;
        }}
        
        /* Files List */
        .files-list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 400px;
            overflow-y: auto;
            padding-right: 10px;
        }}
        
        .files-list::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .files-list::-webkit-scrollbar-track {{
            background: var(--bg-tertiary);
            border-radius: 3px;
        }}
        
        .files-list::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 3px;
        }}
        
        .file-item {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 14px 16px;
            background: var(--bg-tertiary);
            border-radius: 10px;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
            animation: slideIn 0.4s ease forwards;
            opacity: 0;
            transform: translateX(-20px);
        }}
        
        @keyframes slideIn {{
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        
        .file-item:hover {{
            border-color: var(--accent-2);
            background: rgba(78, 205, 196, 0.05);
        }}
        
        .file-rank {{
            background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
            color: #000;
            font-weight: 700;
            font-size: 0.75rem;
            padding: 4px 8px;
            border-radius: 6px;
            min-width: 32px;
            text-align: center;
        }}
        
        .file-info {{
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        
        .file-path {{
            color: var(--text-primary);
            font-size: 0.9rem;
            font-family: 'SF Mono', Monaco, monospace;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .file-size {{
            color: var(--text-secondary);
            font-size: 0.75rem;
        }}
        
        .file-lines {{
            color: var(--accent-4);
            font-weight: 700;
            font-size: 0.9rem;
            white-space: nowrap;
            font-family: 'SF Mono', Monaco, monospace;
        }}
        
        /* Footer */
        footer {{
            text-align: center;
            padding: 50px 20px;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        
        footer .hearts {{
            color: var(--accent-1);
        }}
        
        /* Quick Stats Bar */
        .quick-stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            padding: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .quick-stat {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 20px;
            background: var(--bg-secondary);
            border-radius: 50px;
            border: 1px solid var(--border-color);
        }}
        
        .quick-stat-icon {{
            font-size: 1.2rem;
        }}
        
        .quick-stat-value {{
            font-weight: 700;
            color: var(--accent-2);
        }}
        
        .quick-stat-label {{
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}
        
        /* SVG Styles */
        .pie-slice {{
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .pie-slice:hover {{
            filter: brightness(1.2);
            transform-origin: center;
        }}
        
        .bar-rect {{
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .bar-rect:hover {{
            filter: brightness(1.3);
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2.2rem;
            }}
            
            .logo {{
                font-size: 3rem;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stat-value {{
                font-size: 2rem;
            }}
            
            .pie-section {{
                flex-direction: column;
                align-items: center;
            }}
            
            .quick-stats {{
                gap: 15px;
            }}
            
            .quick-stat {{
                padding: 8px 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">🔬</div>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">A comprehensive visual analysis of your project's DNA</p>
        </header>
        
        <div class="quick-stats">
            <div class="quick-stat">
                <span class="quick-stat-icon">📊</span>
                <span class="quick-stat-value">{avg_lines:,}</span>
                <span class="quick-stat-label">avg lines/file</span>
            </div>
            <div class="quick-stat">
                <span class="quick-stat-icon">🏆</span>
                <span class="quick-stat-value">{html.escape(most_common_ext)}</span>
                <span class="quick-stat-label">most common</span>
            </div>
            <div class="quick-stat">
                <span class="quick-stat-icon">📁</span>
                <span class="quick-stat-value">{len(stats['files_by_extension'])}</span>
                <span class="quick-stat-label">file types</span>
            </div>
        </div>
        
        <div class="dashboard">
            <!-- Overview Stats -->
            <div class="card card-stats">
                <h2 class="card-title">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 3v18h18"/>
                        <path d="M18 17V9"/>
                        <path d="M13 17V5"/>
                        <path d="M8 17v-3"/>
                    </svg>
                    Overview
                </h2>
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-icon">📄</div>
                        <div class="stat-value">{stats['total_files']:,}</div>
                        <div class="stat-label">Total Files</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-icon">📝</div>
                        <div class="stat-value">{format_number(stats['total_lines'])}</div>
                        <div class="stat-label">Lines of Code</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-icon">📂</div>
                        <div class="stat-value">{stats['total_dirs']:,}</div>
                        <div class="stat-label">Directories</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-icon">🌳</div>
                        <div class="stat-value">{stats['max_depth']}</div>
                        <div class="stat-label">Max Depth</div>
                    </div>
                </div>
            </div>
            
            <!-- File Types Pie Chart -->
            <div class="card card-pie">
                <h2 class="card-title">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 2v10l8.5 5"/>
                    </svg>
                    File Types Distribution
                </h2>
                <div class="pie-section">
                    <div class="chart-container">
                        {pie_chart}
                    </div>
                    <div class="legend">
                        {legend_html}
                    </div>
                </div>
            </div>
            
            <!-- Lines by Extension Bar Chart -->
            <div class="card card-bar">
                <h2 class="card-title">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <path d="M7 16h10"/>
                        <path d="M7 12h7"/>
                        <path d="M7 8h4"/>
                    </svg>
                    Lines of Code by Type
                </h2>
                <div class="bar-chart-container">
                    {bar_chart}
                </div>
            </div>
            
            <!-- Largest Files -->
            <div class="card card-files">
                <h2 class="card-title">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    Largest Files
                </h2>
                <div class="files-list">
                    {largest_files_html if largest_files_html else '<p style="color: var(--text-secondary); text-align: center; padding: 40px;">No files found</p>'}
                </div>
            </div>
        </div>
        
        <footer>
            <p>Generated with <span class="hearts">♥</span> by Codebase Fingerprint Generator</p>
        </footer>
    </div>
    
    <script>
        // Add interactive tooltips to pie slices
        document.querySelectorAll('.pie-slice').forEach(slice => {{
            slice.addEventListener('mouseenter', function(e) {{
                const label = this.getAttribute('data-label');
                const value = this.getAttribute('data-value');
                this.style.transform = 'scale(1.05)';
            }});
            
            slice.addEventListener('mouseleave', function(e) {{
                this.style.transform = 'scale(1)';
            }});
        }});
        
        // Add hover effects to bar rectangles
        document.querySelectorAll('.bar-rect').forEach(bar => {{
            bar.addEventListener('mouseenter', function() {{
                this.style.transform = 'scaleX(1.02)';
                this.style.transformOrigin = 'left center';
            }});
            
            bar.addEventListener('mouseleave', function() {{
                this.style.transform = 'scaleX(1)';
            }});
        }});
        
        // Animate stats on scroll
        const observerOptions = {{
            threshold: 0.2,
            rootMargin: '0px'
        }};
        
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }}
            }});
        }}, observerOptions);
        
        document.querySelectorAll('.card').forEach(card => {{
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(card);
        }});
        
        // Trigger initial animation
        setTimeout(() => {{
            document.querySelectorAll('.card').forEach((card, index) => {{
                setTimeout(() => {{
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }}, index * 100);
            }});
        }}, 100);
    </script>
</body>
</html>'''
    
    return html_content


def main():
    print("🔬 Codebase Fingerprint Generator")
    print("=" * 40)
    print("\n📂 Scanning directory...")
    
    stats = scan_directory(".")
    
    print(f"\n📊 Analysis Complete!")
    print(f"   ├── Files: {stats['total_files']:,}")
    print(f"   ├── Lines: {stats['total_lines']:,}")
    print(f"   ├── Directories: {stats['total_dirs']:,}")
    print(f"   └── Max Depth: {stats['max_depth']}")
    
    if stats['files_by_extension']:
        top_ext = max(stats['files_by_extension'].items(), key=lambda x: x[1])
        print(f"\n🏆 Most common: {top_ext[0]} ({top_ext[1]} files)")
    
    print("\n🎨 Generating infographic...")
    html_content = generate_html(stats)
    
    output_file = "stats.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Generated: {output_file}")
    print("🌐 Open the file in your browser to view your codebase fingerprint!")


if __name__ == "__main__":
    main()