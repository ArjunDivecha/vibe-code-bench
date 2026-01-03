#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Generates a beautiful HTML infographic of codebase statistics
"""

import os
import math
import json
from collections import defaultdict
from datetime import datetime

def scan_directory(root_path="."):
    """Recursively scan directory and collect statistics."""
    stats = {
        "files_by_extension": defaultdict(int),
        "lines_by_extension": defaultdict(int),
        "largest_files": [],
        "max_depth": 0,
        "total_files": 0,
        "total_lines": 0,
        "total_dirs": 0,
        "file_sizes": [],
    }
    
    # Extensions to count lines for (text-based files)
    text_extensions = {
        '.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.txt',
        '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rs', '.rb',
        '.php', '.ts', '.tsx', '.jsx', '.vue', '.svelte', '.sql', '.sh',
        '.bash', '.zsh', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
        '.swift', '.kt', '.scala', '.r', '.R', '.pl', '.pm', '.lua'
    }
    
    # Directories to skip
    skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 
                 'env', '.env', 'dist', 'build', '.idea', '.vscode'}
    
    root_depth = root_path.rstrip(os.sep).count(os.sep)
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip unwanted directories
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        
        stats["total_dirs"] += 1
        
        # Calculate depth
        current_depth = dirpath.count(os.sep) - root_depth
        stats["max_depth"] = max(stats["max_depth"], current_depth)
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            
            # Skip the output file and this script
            if filename in ['stats.html', 'git_stats.py']:
                continue
                
            try:
                file_size = os.path.getsize(filepath)
            except (OSError, IOError):
                continue
            
            # Get extension
            _, ext = os.path.splitext(filename)
            ext = ext.lower() if ext else '(no ext)'
            
            stats["files_by_extension"][ext] += 1
            stats["total_files"] += 1
            stats["file_sizes"].append((filepath, file_size))
            
            # Count lines for text files
            if ext in text_extensions:
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        line_count = sum(1 for _ in f)
                        stats["lines_by_extension"][ext] += line_count
                        stats["total_lines"] += line_count
                except (OSError, IOError):
                    pass
    
    # Get largest files
    stats["file_sizes"].sort(key=lambda x: x[1], reverse=True)
    stats["largest_files"] = stats["file_sizes"][:10]
    del stats["file_sizes"]
    
    # Convert defaultdicts to regular dicts
    stats["files_by_extension"] = dict(stats["files_by_extension"])
    stats["lines_by_extension"] = dict(stats["lines_by_extension"])
    
    return stats


def format_size(size_bytes):
    """Format bytes to human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def generate_pie_chart_svg(data, width=300, height=300):
    """Generate SVG pie chart for file types."""
    if not data:
        return '<svg width="300" height="300"><text x="150" y="150" text-anchor="middle" fill="#888">No data</text></svg>'
    
    # Sort and take top 8, group rest as "other"
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_data) > 8:
        top_data = sorted_data[:7]
        other_sum = sum(v for _, v in sorted_data[7:])
        top_data.append(("other", other_sum))
        sorted_data = top_data
    
    total = sum(v for _, v in sorted_data)
    if total == 0:
        return '<svg width="300" height="300"><text x="150" y="150" text-anchor="middle" fill="#888">No data</text></svg>'
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE']
    
    cx, cy = width // 2, height // 2
    radius = min(width, height) // 2 - 40
    
    svg_parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    
    start_angle = -90  # Start from top
    
    for i, (label, value) in enumerate(sorted_data):
        if value == 0:
            continue
            
        percentage = value / total
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
        
        color = colors[i % len(colors)]
        
        # Create path
        if percentage >= 0.999:
            # Full circle
            svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" opacity="0.9"/>')
        else:
            path = f'M {cx} {cy} L {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2} Z'
            svg_parts.append(f'<path d="{path}" fill="{color}" opacity="0.9" stroke="#1a1a2e" stroke-width="2"/>')
        
        # Add label
        label_angle = math.radians(start_angle + angle / 2)
        label_radius = radius * 0.65
        label_x = cx + label_radius * math.cos(label_angle)
        label_y = cy + label_radius * math.sin(label_angle)
        
        if percentage > 0.05:
            svg_parts.append(f'<text x="{label_x}" y="{label_y}" text-anchor="middle" fill="white" font-size="11" font-weight="bold">{label}</text>')
            svg_parts.append(f'<text x="{label_x}" y="{label_y + 14}" text-anchor="middle" fill="white" font-size="10">{percentage*100:.1f}%</text>')
        
        start_angle = end_angle
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def generate_bar_chart_svg(data, width=400, height=250, title=""):
    """Generate SVG bar chart."""
    if not data:
        return f'<svg width="{width}" height="{height}"><text x="{width//2}" y="{height//2}" text-anchor="middle" fill="#888">No data</text></svg>'
    
    # Sort and take top 8
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:8]
    
    if not sorted_data:
        return f'<svg width="{width}" height="{height}"><text x="{width//2}" y="{height//2}" text-anchor="middle" fill="#888">No data</text></svg>'
    
    max_value = max(v for _, v in sorted_data)
    if max_value == 0:
        max_value = 1
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    
    padding = 50
    chart_width = width - padding * 2
    chart_height = height - padding * 2
    bar_width = chart_width / len(sorted_data) * 0.7
    bar_gap = chart_width / len(sorted_data) * 0.3
    
    svg_parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    
    # Draw bars
    for i, (label, value) in enumerate(sorted_data):
        bar_height = (value / max_value) * chart_height
        x = padding + i * (bar_width + bar_gap)
        y = height - padding - bar_height
        
        color = colors[i % len(colors)]
        
        # Bar with rounded top
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="4" opacity="0.9"/>')
        
        # Value label
        svg_parts.append(f'<text x="{x + bar_width/2}" y="{y - 5}" text-anchor="middle" fill="#fff" font-size="11">{value:,}</text>')
        
        # Extension label
        display_label = label[:6] + '..' if len(label) > 8 else label
        svg_parts.append(f'<text x="{x + bar_width/2}" y="{height - padding + 15}" text-anchor="middle" fill="#888" font-size="10">{display_label}</text>')
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def generate_largest_files_svg(files, width=400, height=300):
    """Generate SVG horizontal bar chart for largest files."""
    if not files:
        return f'<svg width="{width}" height="{height}"><text x="{width//2}" y="{height//2}" text-anchor="middle" fill="#888">No files found</text></svg>'
    
    files = files[:8]  # Top 8
    max_size = files[0][1] if files else 1
    if max_size == 0:
        max_size = 1
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    
    bar_height = 25
    gap = 10
    padding_left = 10
    padding_right = 80
    chart_width = width - padding_left - padding_right
    
    svg_parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    
    for i, (filepath, size) in enumerate(files):
        filename = os.path.basename(filepath)
        display_name = filename[:20] + '..' if len(filename) > 22 else filename
        
        bar_width = (size / max_size) * chart_width
        y = 20 + i * (bar_height + gap)
        
        color = colors[i % len(colors)]
        
        # Bar
        svg_parts.append(f'<rect x="{padding_left}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="4" opacity="0.85"/>')
        
        # Filename inside bar
        svg_parts.append(f'<text x="{padding_left + 8}" y="{y + bar_height/2 + 4}" fill="white" font-size="11" font-weight="500">{display_name}</text>')
        
        # Size label
        svg_parts.append(f'<text x="{width - 10}" y="{y + bar_height/2 + 4}" text-anchor="end" fill="#888" font-size="11">{format_size(size)}</text>')
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def generate_html(stats):
    """Generate the HTML infographic."""
    
    # Generate charts
    pie_chart = generate_pie_chart_svg(stats["files_by_extension"], 280, 280)
    bar_chart = generate_bar_chart_svg(stats["lines_by_extension"], 380, 220)
    files_chart = generate_largest_files_svg(stats["largest_files"], 380, 280)
    
    # Calculate some derived stats
    avg_lines_per_file = stats["total_lines"] / max(stats["total_files"], 1)
    
    # Top extensions for legend
    top_extensions = sorted(stats["files_by_extension"].items(), key=lambda x: x[1], reverse=True)[:8]
    
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
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 40px 0;
            position: relative;
        }}
        
        h1 {{
            font-size: 3rem;
            background: linear-gradient(135deg, #FF6B6B, #4ECDC4, #45B7D1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            text-shadow: 0 0 40px rgba(78, 205, 196, 0.3);
        }}
        
        .subtitle {{
            color: #888;
            font-size: 1rem;
            font-weight: 300;
        }}
        
        .timestamp {{
            color: #666;
            font-size: 0.85rem;
            margin-top: 5px;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        
        .card {{
            background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }}
        
        .card-title {{
            font-size: 1.1rem;
            color: #4ECDC4;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .card-title::before {{
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(180deg, #FF6B6B, #4ECDC4);
            border-radius: 2px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 20px;
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.05);
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #FF6B6B, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .stat-label {{
            color: #888;
            font-size: 0.85rem;
            margin-top: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .chart-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 250px;
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
            font-size: 0.8rem;
            color: #aaa;
        }}
        
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }}
        
        .full-width {{
            grid-column: 1 / -1;
        }}
        
        .depth-indicator {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 20px;
        }}
        
        .depth-bar {{
            flex: 1;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .depth-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4ECDC4, #45B7D1);
            border-radius: 4px;
            transition: width 1s ease;
        }}
        
        .depth-label {{
            color: #4ECDC4;
            font-weight: 600;
            min-width: 80px;
            text-align: right;
        }}
        
        footer {{
            text-align: center;
            padding: 40px;
            color: #555;
            font-size: 0.85rem;
        }}
        
        footer a {{
            color: #4ECDC4;
            text-decoration: none;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .card {{
            animation: fadeIn 0.6s ease forwards;
        }}
        
        .card:nth-child(1) {{ animation-delay: 0.1s; }}
        .card:nth-child(2) {{ animation-delay: 0.2s; }}
        .card:nth-child(3) {{ animation-delay: 0.3s; }}
        .card:nth-child(4) {{ animation-delay: 0.4s; }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2rem;
            }}
            
            .dashboard {{
                grid-template-columns: 1fr;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stat-value {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Codebase Fingerprint</h1>
            <p class="subtitle">A visual snapshot of your project's DNA</p>
            <p class="timestamp">Generated on {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>
        </header>
        
        <div class="dashboard">
            <!-- Overview Stats -->
            <div class="card">
                <h2 class="card-title">Overview</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">{stats["total_files"]:,}</div>
                        <div class="stat-label">Total Files</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{stats["total_lines"]:,}</div>
                        <div class="stat-label">Lines of Code</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{stats["total_dirs"]:,}</div>
                        <div class="stat-label">Directories</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{avg_lines_per_file:.0f}</div>
                        <div class="stat-label">Avg Lines/File</div>
                    </div>
                </div>
                <div class="depth-indicator">
                    <span style="color: #888;">Max Depth:</span>
                    <div class="depth-bar">
                        <div class="depth-fill" style="width: {min(stats['max_depth'] * 10, 100)}%;"></div>
                    </div>
                    <span class="depth-label">{stats["max_depth"]} levels</span>
                </div>
            </div>
            
            <!-- File Types Pie Chart -->
            <div class="card">
                <h2 class="card-title">File Types Distribution</h2>
                <div class="chart-container">
                    {pie_chart}
                </div>
                <div class="legend">
                    {''.join(f'<div class="legend-item"><div class="legend-color" style="background: {["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F"][i % 8]};"></div>{ext} ({count})</div>' for i, (ext, count) in enumerate(top_extensions))}
                </div>
            </div>
            
            <!-- Lines by Extension -->
            <div class="card">
                <h2 class="card-title">Lines of Code by Type</h2>
                <div class="chart-container">
                    {bar_chart}
                </div>
            </div>
            
            <!-- Largest Files -->
            <div class="card">
                <h2 class="card-title">Largest Files</h2>
                <div class="chart-container">
                    {files_chart}
                </div>
            </div>
        </div>
        
        <footer>
            <p>Generated with ❤️ by <a href="#">Git Stats Infographic Generator</a></p>
        </footer>
    </div>
    
    <script>
        // Add some interactivity
        document.querySelectorAll('.stat-value').forEach(el => {{
            const finalValue = el.textContent;
            const numericValue = parseInt(finalValue.replace(/,/g, ''));
            if (!isNaN(numericValue) && numericValue > 0) {{
                let current = 0;
                const increment = Math.ceil(numericValue / 50);
                const timer = setInterval(() => {{
                    current += increment;
                    if (current >= numericValue) {{
                        el.textContent = numericValue.toLocaleString();
                        clearInterval(timer);
                    }} else {{
                        el.textContent = current.toLocaleString();
                    }}
                }}, 30);
            }}
        }});
        
        // Animate depth bar
        setTimeout(() => {{
            document.querySelector('.depth-fill').style.width = '{min(stats['max_depth'] * 10, 100)}%';
        }}, 500);
    </script>
</body>
</html>'''
    
    return html


def main():
    print("🔍 Scanning codebase...")
    stats = scan_directory(".")
    
    print(f"   Found {stats['total_files']:,} files")
    print(f"   Found {stats['total_lines']:,} lines of code")
    print(f"   Found {len(stats['files_by_extension'])} file types")
    
    print("\n🎨 Generating infographic...")
    html = generate_html(stats)
    
    with open("stats.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("✅ Generated stats.html")
    print("\n📊 Quick Summary:")
    print(f"   • Total Files: {stats['total_files']:,}")
    print(f"   • Total Lines: {stats['total_lines']:,}")
    print(f"   • Directories: {stats['total_dirs']:,}")
    print(f"   • Max Depth: {stats['max_depth']} levels")
    
    if stats['files_by_extension']:
        top_ext = max(stats['files_by_extension'].items(), key=lambda x: x[1])
        print(f"   • Most Common Type: {top_ext[0]} ({top_ext[1]} files)")
    
    if stats['largest_files']:
        largest = stats['largest_files'][0]
        print(f"   • Largest File: {os.path.basename(largest[0])} ({format_size(largest[1])})")


if __name__ == "__main__":
    main()