#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Generates a beautiful, single-file HTML infographic of your codebase.
"""

import os
import json
from pathlib import Path
from collections import defaultdict
import re


class CodebaseAnalyzer:
    """Analyzes a codebase and collects statistics."""
    
    def __init__(self):
        self.extension_counts = defaultdict(int)
        self.extension_lines = defaultdict(int)
        self.file_sizes = []
        self.max_depth = 0
        self.total_files = 0
        self.total_lines = 0
        self.directory_count = 0
        
    def should_skip(self, path):
        """Check if path should be skipped (git, node_modules, etc.)"""
        skip_patterns = [
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'env', '.env', 'dist', 'build', '.idea', '.vscode',
            '*.pyc', '*.egg-info', '*.so', '*.o', '*.a', '*.lib',
            '*.dll', '*.exe', '*.bin', '*.min.js', '*.min.css'
        ]
        
        path_str = str(path)
        for pattern in skip_patterns:
            if pattern.startswith('*'):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_str.split(os.sep):
                return True
        return False
    
    def count_lines(self, file_path):
        """Count lines in a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except:
            return 0
    
    def get_file_extension(self, filename):
        """Extract file extension from filename."""
        parts = filename.rsplit('.', 1)
        if len(parts) > 1:
            ext = parts[1].lower()
            # Group similar extensions
            if ext in ['js', 'jsx', 'mjs', 'cjs']:
                return 'js'
            elif ext in ['ts', 'tsx']:
                return 'ts'
            elif ext in ['py', 'pyw']:
                return 'py'
            elif ext in ['html', 'htm']:
                return 'html'
            elif ext in ['css', 'scss', 'sass', 'less']:
                return 'css'
            elif ext in ['json', 'jsonl']:
                return 'json'
            elif ext in ['md', 'markdown']:
                return 'md'
            elif ext in ['yml', 'yaml']:
                return 'yaml'
            elif ext in ['sh', 'bash', 'zsh']:
                return 'sh'
            elif ext in ['sql']:
                return 'sql'
            elif ext in ['java']:
                return 'java'
            elif ext in ['c', 'cpp', 'cc', 'cxx', 'h', 'hpp']:
                return 'cpp'
            elif ext in ['go']:
                return 'go'
            elif ext in ['rs']:
                return 'rs'
            elif ext in ['rb']:
                return 'rb'
            elif ext in ['php']:
                return 'php'
            elif ext in ['swift']:
                return 'swift'
            elif ext in ['kt', 'kts']:
                return 'kt'
            elif ext in ['vue']:
                return 'vue'
            elif ext in ['xml']:
                return 'xml'
            elif ext in ['svg']:
                return 'svg'
            elif ext in ['txt']:
                return 'txt'
            elif ext in ['log']:
                return 'log'
            elif ext in ['gitignore', 'eslintrc', 'prettierrc', 'babelrc']:
                return 'config'
            return ext
        return 'noext'
    
    def analyze(self, root_path='.'):
        """Recursively analyze the codebase."""
        root_path = Path(root_path).resolve()
        
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Skip hidden and build directories
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ['node_modules', 'venv', 'env', 'dist', 'build']]
            
            depth = len(Path(dirpath).relative_to(root_path).parts)
            self.max_depth = max(self.max_depth, depth)
            self.directory_count += 1
            
            for filename in filenames:
                if self.should_skip(filename):
                    continue
                    
                file_path = Path(dirpath) / filename
                try:
                    file_size = file_path.stat().st_size
                    lines = self.count_lines(file_path)
                    
                    ext = self.get_file_extension(filename)
                    self.extension_counts[ext] += 1
                    self.extension_lines[ext] += lines
                    self.total_lines += lines
                    self.total_files += 1
                    
                    self.file_sizes.append({
                        'name': filename,
                        'path': str(file_path.relative_to(root_path)),
                        'size': file_size,
                        'lines': lines,
                        'extension': ext
                    })
                except (PermissionError, OSError):
                    continue
        
        # Sort file sizes by size (largest first)
        self.file_sizes.sort(key=lambda x: x['size'], reverse=True)
        
        return self.get_stats()
    
    def get_stats(self):
        """Return collected statistics."""
        return {
            'extension_counts': dict(self.extension_counts),
            'extension_lines': dict(self.extension_lines),
            'largest_files': self.file_sizes[:15],
            'max_depth': self.max_depth,
            'total_files': self.total_files,
            'total_lines': self.total_lines,
            'directory_count': self.directory_count
        }


def format_number(num):
    """Format large numbers with K, M suffix."""
    if num >= 1000000:
        return f"{num / 1000000:.1f}M"
    elif num >= 1000:
        return f"{num / 1000:.1f}K"
    return str(num)


def format_bytes(num):
    """Format bytes to human readable."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} TB"


def generate_html(stats):
    """Generate the HTML infographic."""
    
    # Color palette for charts
    colors = [
        '#00D4FF', '#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3',
        '#F38181', '#AA96DA', '#FCBAD3', '#A8D8EA', '#AA96DA',
        '#FFC93C', '#6EB5FF', '#C689C6', '#B5EAD7', '#E2F0CB'
    ]
    
    # Prepare pie chart data
    ext_data = sorted(stats['extension_counts'].items(), key=lambda x: x[1], reverse=True)
    total_ext = sum(stats['extension_counts'].values())
    
    # Line chart data (top extensions by lines)
    line_data = sorted(
        [(ext, stats['extension_lines'][ext]) for ext in stats['extension_counts']],
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    # Generate pie chart SVG
    pie_svg = generate_pie_chart(ext_data, total_ext, colors)
    
    # Generate bar chart SVG
    bar_svg = generate_bar_chart(line_data, colors)
    
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
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0a0a0f 100%);
            min-height: 100vh;
            color: #e0e0e0;
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
            background: linear-gradient(90deg, #00D4FF, #4ECDC4, #FF6B6B);
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
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(0, 212, 255, 0.3);
            background: rgba(255, 255, 255, 0.05);
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, #00D4FF, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .stat-label {{
            color: #888;
            margin-top: 8px;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .charts-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .chart-card {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 30px;
        }}
        
        .chart-title {{
            font-size: 1.2rem;
            margin-bottom: 20px;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .chart-title::before {{
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(180deg, #00D4FF, #4ECDC4);
            border-radius: 2px;
        }}
        
        .chart-container {{
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
            justify-content: center;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            color: #aaa;
        }}
        
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }}
        
        .files-card {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
        }}
        
        .files-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .files-table th {{
            text-align: left;
            padding: 12px 15px;
            color: #888;
            font-weight: 500;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .files-table td {{
            padding: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .files-table tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}
        
        .file-name {{
            color: #00D4FF;
            font-weight: 500;
        }}
        
        .file-path {{
            color: #666;
            font-size: 0.85rem;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .ext-badge {{
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .ext-py {{ background: rgba(255, 215, 0, 0.2); color: #FFD700; }}
        .ext-js {{ background: rgba(247, 223, 30, 0.2); color: #F7DF1E; }}
        .ext-ts {{ background: rgba(0, 122, 204, 0.2); color: #3178C6; }}
        .ext-html {{ background: rgba(227, 76, 38, 0.2); color: #E34F26; }}
        .ext-css {{ background: rgba(21, 114, 182, 0.2); color: #1572B6; }}
        .ext-json {{ background: rgba(0, 0, 0, 0.3); color: #fff; }}
        .ext-md {{ background: rgba(5, 143, 245, 0.2); color: #058FDE; }}
        .ext-default {{ background: rgba(150, 150, 150, 0.2); color: #969696; }}
        
        .progress-bar {{
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 8px;
        }}
        
        .progress-fill {{
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }}
        
        .depth-viz {{
            margin-top: 30px;
        }}
        
        .depth-bar {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .depth-label {{
            width: 100px;
            color: #888;
            font-size: 0.9rem;
        }}
        
        .depth-track {{
            flex: 1;
            height: 30px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .depth-fill {{
            height: 100%;
            background: linear-gradient(90deg, #00D4FF, #4ECDC4);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            font-size: 0.85rem;
            font-weight: 600;
            color: #000;
            transition: width 0.8s ease;
        }}
        
        @media (max-width: 768px) {{
            h1 {{ font-size: 2rem; }}
            .charts-row {{ grid-template-columns: 1fr; }}
            .files-table {{ font-size: 0.85rem; }}
            .file-path {{ max-width: 150px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">A visual analysis of your project structure</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{format_number(stats['total_files'])}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{format_number(stats['total_lines'])}</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['directory_count']}</div>
                <div class="stat-label">Directories</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['max_depth']}</div>
                <div class="stat-label">Max Depth</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(stats['extension_counts'])}</div>
                <div class="stat-label">File Types</div>
            </div>
        </div>
        
        <div class="charts-row">
            <div class="chart-card">
                <h2 class="chart-title">File Types Distribution</h2>
                <div class="chart-container">
                    {pie_svg}
                </div>
                <div class="legend">
                    {generate_legend(ext_data, colors)}
                </div>
            </div>
            
            <div class="chart-card">
                <h2 class="chart-title">Lines of Code by Type</h2>
                <div class="chart-container">
                    {bar_svg}
                </div>
            </div>
        </div>
        
        <div class="depth-viz">
            <div class="chart-card">
                <h2 class="chart-title">Directory Structure Depth</h2>
                <p style="color: #888; margin-bottom: 20px;">Your project extends to <strong style="color: #00D4FF;">{stats['max_depth']}</strong> levels deep</p>
                <div class="depth-bar">
                    <span class="depth-label">Root level</span>
                    <div class="depth-track">
                        <div class="depth-fill" style="width: 100%">100%</div>
                    </div>
                </div>
                <div class="depth-bar">
                    <span class="depth-label">Level 2</span>
                    <div class="depth-track">
                        <div class="depth-fill" style="width: {max(10, (stats["max_depth"] / 2 / stats["max_depth"]) * 100 if stats["max_depth"] > 1 else 10)}%">
                            {int((stats["max_depth"] / 2 / stats["max_depth"]) * 100) if stats["max_depth"] > 1 else 10}%
                        </div>
                    </div>
                </div>
                <div class="depth-bar">
                    <span class="depth-label">Level 3</span>
                    <div class="depth-track">
                        <div class="depth-fill" style="width: {max(10, (stats["max_depth"] / 3 / stats["max_depth"]) * 100 if stats["max_depth"] > 2 else 10)}%">
                            {int((stats["max_depth"] / 3 / stats["max_depth"]) * 100) if stats["max_depth"] > 2 else 10}%
                        </div>
                    </div>
                </div>
                <div class="depth-bar">
                    <span class="depth-label">Level 4</span>
                    <div class="depth-track">
                        <div class="depth-fill" style="width: {max(10, (stats["max_depth"] / 4 / stats["max_depth"]) * 100 if stats["max_depth"] > 3 else 10)}%">
                            {int((stats["max_depth"] / 4 / stats["max_depth"]) * 100) if stats["max_depth"] > 3 else 10}%
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="files-card" style="margin-top: 30px;">
            <h2 class="chart-title">Largest Files</h2>
            <table class="files-table">
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Type</th>
                        <th>Size</th>
                        <th>Lines</th>
                    </tr>
                </thead>
                <tbody>
                    {generate_files_table(stats['largest_files'])}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Animate elements on scroll
        const observerOptions = {{
            threshold: 0.1,
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
        
        document.querySelectorAll('.stat-card, .chart-card, .files-card').forEach(el => {{
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(el);
        }});
        
        // Animate stat numbers
        document.querySelectorAll('.stat-value').forEach(el => {{
            const target = parseInt(el.textContent.replace(/[KMB]/g, ''));
            const suffix = el.textContent.replace(/[0-9.]/g, '');
            let current = 0;
            const increment = target / 50;
            const timer = setInterval(() => {{
                current += increment;
                if (current >= target) {{
                    el.textContent = el.textContent;
                    clearInterval(timer);
                }} else {{
                    el.textContent = Math.floor(current) + suffix;
                }}
            }}, 30);
        }});
        
        // Animate progress bars on scroll
        const progressObserver = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const fills = entry.target.querySelectorAll('.depth-fill');
                    fills.forEach(fill => {{
                        const width = fill.style.width;
                        fill.style.width = '0%';
                        setTimeout(() => {{
                            fill.style.width = width;
                        }}, 100);
                    }});
                    progressObserver.unobserve(entry.target);
                }}
            }});
        }}, observerOptions);
        
        document.querySelectorAll('.depth-viz').forEach(el => {{
            progressObserver.observe(el);
        }});
    </script>
</body>
</html>'''
    return html


def generate_pie_chart(data, total, colors):
    """Generate SVG pie chart."""
    if not data or total == 0:
        return '<svg width="300" height="300" viewBox="0 0 300 300"><text x="150" y="150" text-anchor="middle" fill="#888">No data</text></svg>'
    
    # Group small entries into "Other"
    threshold = 0.03  # 3%
    pie_data = []
    other_count = 0
    
    for i, (ext, count) in enumerate(data):
        if len(pie_data) < 8:
            pie_data.append((ext, count, colors[i % len(colors)]))
        else:
            other_count += count
    
    if other_count > 0:
        pie_data.append(('other', other_count, colors[8 % len(colors)]))
    
    center_x, center_y = 150, 150
    radius = 120
    inner_radius = 70
    
    paths = []
    start_angle = -90
    
    for ext, count, color in pie_data:
        percentage = count / total
        angle = percentage * 360
        end_angle = start_angle + angle
        
        # Calculate path
        x1 = center_x + radius * (start_angle * 3.14159 / 180)
        y1 = center_y + radius * (start_angle * 3.14159 / 180)
        x2 = center_x + radius * (end_angle * 3.14159 / 180)
        y2 = center_y + radius * (end_angle * 3.14159 / 180)
        
        x3 = center_x + inner_radius * (end_angle * 3.14159 / 180)
        y3 = center_y + inner_radius * (end_angle * 3.14159 / 180)
        x4 = center_x + inner_radius * (start_angle * 3.14159 / 180)
        y4 = center_y + inner_radius * (start_angle * 3.14159 / 180)
        
        large_arc = 1 if angle > 180 else 0
        
        path = f"M {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2} L {x3} {y3} A {inner_radius} {inner_radius} 0 0 0 {x4} {y4} Z"
        
        paths.append(f'<path d="{path}" fill="{color}" opacity="0.9"><title>{ext}: {count} files ({percentage*100:.1f}%)</title></path>')
        
        start_angle = end_angle
    
    svg = f'''<svg width="300" height="300" viewBox="0 0 300 300">
        <defs>
            <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
        </defs>
        <g filter="url(#glow)">
            {''.join(paths)}
        </g>
    </svg>'''
    
    return svg


def generate_bar_chart(data, colors):
    """Generate SVG bar chart for lines of code."""
    if not data:
        return '<svg width="500" height="300" viewBox="0 0 500 300"><text x="250" y="150" text-anchor="middle" fill="#888">No data</text></svg>'
    
    max_lines = max(lines for _, lines in data)
    bar_height = 35
    gap = 15
    chart_height = len(data) * (bar_height + gap) + 60
    chart_width = 500
    bar_width = chart_width - 150 - 60
    margin_left = 100
    margin_bottom = 50
    
    bars = []
    for i, (ext, lines) in enumerate(data):
        y = margin_bottom + i * (bar_height + gap)
        width = (lines / max_lines) * bar_width
        color = colors[i % len(colors)]
        
        # Bar
        bars.append(f'''<rect x="{margin_left}" y="{y}" width="{width}" height="{bar_height}" rx="6" fill="{color}" opacity="0.9">
            <title>{ext}: {format_number(lines)} lines</title>
        </rect>''')
        
        # Label
        bars.append(f'<text x="{margin_left - 10}" y="{y + bar_height/2 + 5}" text-anchor="end" fill="#888" font-size="13">{ext}</text>')
        
        # Value
        bars.append(f'<text x="{margin_left + width + 10}" y="{y + bar_height/2 + 5}" fill="#fff" font-size="13" font-weight="600">{format_number(lines)}</text>')
    
    svg = f'''<svg width="{chart_width}" height="{chart_height}" viewBox="0 0 {chart_width} {chart_height}">
        <defs>
            <filter id="barGlow">
                <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
        </defs>
        <g filter="url(#barGlow)">
            {''.join(bars)}
        </g>
        <!-- X-axis line -->
        <line x1="{margin_left}" y1="{margin_bottom}" x2="{chart_width - 30}" y2="{margin_bottom}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
    </svg>'''
    
    return svg


def generate_legend(data, colors):
    """Generate legend HTML."""
    items = []
    for i, (ext, count) in enumerate(data[:10]):
        color = colors[i % len(colors)]
        items.append(f'''<div class="legend-item">
            <span class="legend-color" style="background: {color}"></span>
            <span>{ext} ({count})</span>
        </div>''')
    return ''.join(items)


def get_ext_class(ext):
    """Get CSS class for extension badge."""
    classes = {
        'py': 'ext-py', 'js': 'ext-js', 'ts': 'ext-ts',
        'html': 'ext-html', 'css': 'ext-css', 'json': 'ext-json',
        'md': 'ext-md'
    }
    return classes.get(ext, 'ext-default')


def generate_files_table(files):
    """Generate HTML table for largest files."""
    rows = []
    for f in files:
        ext_class = get_ext_class(f['extension'])
        rows.append(f'''<tr>
            <td>
                <div class="file-name">{f['name']}</div>
                <div class="file-path">{f['path']}</div>
            </td>
            <td><span class="ext-badge {ext_class}">{f['extension']}</span></td>
            <td>{format_bytes(f['size'])}</td>
            <td>{f['lines']:,}</td>
        </tr>''')
    return ''.join(rows)


def main():
    """Main function to run the analyzer."""
    print("🔍 Scanning codebase...")
    
    analyzer = CodebaseAnalyzer()
    stats = analyzer.analyze('.')
    
    print(f"   Found {stats['total_files']} files")
    print(f"   Found {stats['total_lines']:,} lines of code")
    print(f"   Found {stats['directory_count']} directories")
    print(f"   Max depth: {stats['max_depth']}")
    
    print("\n📊 Generating infographic...")
    
    html = generate_html(stats)
    
    output_file = 'stats.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"   ✓ Generated: {output_file}")
    print("\n✨ Open stats.html in your browser to view the infographic!")


if __name__ == '__main__':
    main()