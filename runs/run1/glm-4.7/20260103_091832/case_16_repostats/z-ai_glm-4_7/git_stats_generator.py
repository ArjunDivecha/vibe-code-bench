#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Scans the current directory and generates a beautiful HTML infographic.
"""

import os
import sys
from collections import defaultdict
from pathlib import Path
from math import pi


def scan_directory(root_dir="."):
    """Recursively scan directory and gather statistics."""
    file_stats = defaultdict(lambda: {"count": 0, "lines": 0})
    total_lines = 0
    total_files = 0
    largest_files = []
    max_depth = 0
    dir_sizes = defaultdict(int)

    # Common text file extensions to count lines for
    text_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.json',
        '.md', '.txt', '.java', '.c', '.cpp', '.h', '.hpp', '.go', '.rs',
        '.rb', '.php', '.sh', '.bat', '.yml', '.yaml', '.xml', '.sql',
        '.vue', '.svelte', '.swift', '.kt', '.dart', '.lua', '.r', '.m',
        '.mm', '.cs', '.fs', '.fsx', '.pl', '.pm', '.t', '.hs', '.lhs'
    }

    ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv',
                   'env', '.env', 'dist', 'build', '.idea', '.vscode',
                   'target', 'bin', 'obj', 'out', '.next', '.nuxt'}

    for root, dirs, files in os.walk(root_dir):
        # Calculate depth
        rel_path = os.path.relpath(root, root_dir)
        depth = 0 if rel_path == '.' else rel_path.count(os.sep)
        max_depth = max(max_depth, depth)

        # Filter out ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                file_size = os.path.getsize(filepath)
                ext = Path(filename).suffix.lower()
                
                # Track largest files
                largest_files.append({
                    "name": filename,
                    "path": filepath,
                    "size": file_size,
                    "ext": ext or "(no extension)"
                })
                
                # Count by extension
                file_stats[ext or "(no extension)"]["count"] += 1
                total_files += 1
                dir_sizes[root] += file_size

                # Count lines for text files
                if ext in text_extensions or ext == '':
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = sum(1 for _ in f)
                            file_stats[ext or "(no extension)"]["lines"] += lines
                            total_lines += lines
                    except Exception:
                        pass
            except (OSError, PermissionError):
                continue

    # Sort largest files
    largest_files.sort(key=lambda x: x["size"], reverse=True)
    largest_files = largest_files[:10]

    # Sort file stats by count
    sorted_stats = sorted(file_stats.items(), key=lambda x: x[1]["count"], reverse=True)

    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "file_stats": sorted_stats,
        "largest_files": largest_files,
        "max_depth": max_depth,
        "dir_sizes": dict(sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)[:10])
    }


def format_size(size):
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def generate_pie_chart_svg(data, total):
    """Generate SVG pie chart for file extensions."""
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8B500', '#FF6F61', '#6B5B95', '#88B04B', '#F7CAC9'
    ]
    
    svg_parts = []
    current_angle = -90  # Start from top
    center_x, center_y = 150, 150
    radius = 120
    
    # Filter to top 8, group rest as "Other"
    top_data = data[:8]
    other_count = sum(item[1]["count"] for item in data[8:])
    if other_count > 0:
        top_data.append(("Other", {"count": other_count, "lines": 0}))
    
    for idx, (ext, stats) in enumerate(top_data):
        count = stats["count"]
        if count == 0:
            continue
            
        percentage = count / total
        angle = percentage * 360
        
        if angle == 360:
            # Full circle
            svg_parts.append(f'<circle cx="{center_x}" cy="{center_y}" r="{radius}" fill="{colors[idx % len(colors)]}"/>')
        else:
            start_rad = pi * current_angle / 180
            end_rad = pi * (current_angle + angle) / 180
            
            x1 = center_x + radius * (1 if percentage > 0.5 else 0.5) * (1 if angle > 180 else 1) * 0
            y1 = center_y
            
            start_x = center_x + radius * (1 if percentage > 0.5 else 0.5) * 0
            start_y = center_y
            
            x1 = center_x + radius * (1 if percentage > 0.5 else 0.5) * 0
            y1 = center_y
            
            large_arc = 1 if angle > 180 else 0
            
            start_x = center_x + radius * (pi * current_angle / 180).__cos__()
            start_y = center_y + radius * (pi * current_angle / 180).__sin__()
            end_x = center_x + radius * (pi * (current_angle + angle) / 180).__cos__()
            end_y = center_y + radius * (pi * (current_angle + angle) / 180).__sin__()
            
            path = f'M {center_x} {center_y} L {start_x} {start_y} A {radius} {radius} 0 {large_arc} 1 {end_x} {end_y} Z'
            svg_parts.append(f'<path d="{path}" fill="{colors[idx % len(colors)]}" class="pie-slice" data-ext="{ext}" data-count="{count}" data-pct="{percentage:.1%}"/>')
        
        current_angle += angle
    
    # Add center hole for donut effect
    svg_parts.append(f'<circle cx="{center_x}" cy="{center_y}" r="60" fill="#1a1a2e"/>')
    
    return '\n'.join(svg_parts)


def generate_bar_chart_svg(data):
    """Generate SVG bar chart for line counts by extension."""
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    
    max_lines = max((item[1]["lines"] for item in data if item[1]["lines"] > 0), default=1)
    top_data = [item for item in data if item[1]["lines"] > 0][:10]
    
    if not top_data:
        return '<text x="200" y="150" fill="#888" text-anchor="middle">No line data available</text>'
    
    bar_height = 30
    gap = 15
    start_y = 40
    max_width = 350
    
    svg_parts = []
    
    for idx, (ext, stats) in enumerate(top_data):
        lines = stats["lines"]
        bar_width = (lines / max_lines) * max_width
        y = start_y + idx * (bar_height + gap)
        color = colors[idx % len(colors)]
        
        # Bar background
        svg_parts.append(f'<rect x="100" y="{y}" width="{max_width}" height="{bar_height}" fill="#2a2a4a" rx="4"/>')
        
        # Bar fill
        svg_parts.append(f'<rect x="100" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="4" class="bar" data-ext="{ext}" data-lines="{lines}"/>')
        
        # Extension label
        svg_parts.append(f'<text x="90" y="{y + bar_height/2 + 5}" fill="#fff" text-anchor="end" font-size="12">{ext}</text>')
        
        # Lines count
        svg_parts.append(f'<text x="{100 + bar_width + 10}" y="{y + bar_height/2 + 5}" fill="#888" font-size="11">{lines:,} lines</text>')
    
    return '\n'.join(svg_parts)


def generate_html(stats):
    """Generate the HTML infographic."""
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
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }}

        h1 {{
            font-size: 3rem;
            background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 40px rgba(78, 205, 196, 0.3);
            margin-bottom: 10px;
        }}

        .subtitle {{
            color: #888;
            font-size: 1.1rem;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}

        .card {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 25px;
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border-color: rgba(78, 205, 196, 0.3);
        }}

        .card-title {{
            font-size: 1.2rem;
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

        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }}

        .stat-item {{
            text-align: center;
            padding: 15px;
            background: rgba(0,0,0,0.2);
            border-radius: 12px;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            background: linear-gradient(90deg, #FF6B6B, #FFEAA7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .stat-label {{
            color: #888;
            font-size: 0.9rem;
            margin-top: 5px;
        }}

        .chart-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 300px;
        }}

        .legend {{
            margin-top: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 0.85rem;
            color: #aaa;
        }}

        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}

        th {{
            color: #4ECDC4;
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        td {{
            color: #ccc;
            font-size: 0.9rem;
        }}

        tr:hover td {{
            background: rgba(255,255,255,0.05);
        }}

        .ext-badge {{
            display: inline-block;
            padding: 4px 8px;
            background: rgba(78, 205, 196, 0.2);
            color: #4ECDC4;
            border-radius: 4px;
            font-size: 0.8rem;
            font-family: monospace;
        }}

        .size-bar {{
            height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 5px;
        }}

        .size-fill {{
            height: 100%;
            background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
            border-radius: 3px;
            transition: width 0.5s ease;
        }}

        .tooltip {{
            position: fixed;
            background: rgba(0,0,0,0.9);
            color: #fff;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 0.9rem;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s ease;
            z-index: 1000;
            border: 1px solid rgba(78, 205, 196, 0.3);
        }}

        .tooltip.visible {{
            opacity: 1;
        }}

        .pie-slice, .bar {{
            cursor: pointer;
            transition: opacity 0.2s ease;
        }}

        .pie-slice:hover, .bar:hover {{
            opacity: 0.8;
        }}

        .wide-card {{
            grid-column: 1 / -1;
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
        .card:nth-child(5) {{ animation-delay: 0.5s; }}

        footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.9rem;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">Visual analysis of your project structure</p>
        </header>

        <div class="grid">
            <!-- Overview Stats -->
            <div class="card">
                <h2 class="card-title">Overview</h2>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-value">{stats["total_files"]:,}</div>
                        <div class="stat-label">Total Files</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{stats["total_lines"]:,}</div>
                        <div class="stat-label">Lines of Code</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{stats["max_depth"]}</div>
                        <div class="stat-label">Max Depth</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{len(stats["file_stats"])}</div>
                        <div class="stat-label">File Types</div>
                    </div>
                </div>
            </div>

            <!-- File Types Pie Chart -->
            <div class="card">
                <h2 class="card-title">File Distribution</h2>
                <div class="chart-container">
                    <svg width="300" height="300" viewBox="0 0 300 300">
                        {generate_pie_chart_svg(stats["file_stats"], stats["total_files"])}
                    </svg>
                </div>
                <div class="legend">
                    {generate_legend(stats["file_stats"][:8], stats["total_files"])}
                </div>
            </div>

            <!-- Lines by Extension Bar Chart -->
            <div class="card wide-card">
                <h2 class="card-title">Lines of Code by Extension</h2>
                <div class="chart-container">
                    <svg width="600" height="350" viewBox="0 0 600 350">
                        {generate_bar_chart_svg(stats["file_stats"])}
                    </svg>
                </div>
            </div>

            <!-- Largest Files -->
            <div class="card wide-card">
                <h2 class="card-title">Largest Files</h2>
                <table>
                    <thead>
                        <tr>
                            <th>File</th>
                            <th>Type</th>
                            <th>Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_largest_files_table(stats["largest_files"])}
                    </tbody>
                </table>
            </div>

            <!-- File Types Breakdown -->
            <div class="card wide-card">
                <h2 class="card-title">File Types Breakdown</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Extension</th>
                            <th>Count</th>
                            <th>Percentage</th>
                            <th>Lines</th>
                            <th>Distribution</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_file_types_table(stats["file_stats"], stats["total_files"])}
                    </tbody>
                </table>
            </div>
        </div>

        <footer>
            Generated by Git Stats Infographic Generator
        </footer>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <script>
        const tooltip = document.getElementById('tooltip');

        // Pie slice tooltips
        document.querySelectorAll('.pie-slice').forEach(slice => {{
            slice.addEventListener('mouseenter', (e) => {{
                const ext = e.target.dataset.ext;
                const count = parseInt(e.target.dataset.count).toLocaleString();
                const pct = e.target.dataset.pct;
                tooltip.innerHTML = `<strong>${ext}</strong><br>${count} files (${pct})`;
                tooltip.classList.add('visible');
            }});
            slice.addEventListener('mousemove', (e) => {{
                tooltip.style.left = e.pageX + 15 + 'px';
                tooltip.style.top = e.pageY + 15 + 'px';
            }});
            slice.addEventListener('mouseleave', () => {{
                tooltip.classList.remove('visible');
            }});
        }});

        // Bar tooltips
        document.querySelectorAll('.bar').forEach(bar => {{
            bar.addEventListener('mouseenter', (e) => {{
                const ext = e.target.dataset.ext;
                const lines = parseInt(e.target.dataset.lines).toLocaleString();
                tooltip.innerHTML = `<strong>${ext}</strong><br>${lines} lines`;
                tooltip.classList.add('visible');
            }});
            bar.addEventListener('mousemove', (e) => {{
                tooltip.style.left = e.pageX + 15 + 'px';
                tooltip.style.top = e.pageY + 15 + 'px';
            }});
            bar.addEventListener('mouseleave', () => {{
                tooltip.classList.remove('visible');
            }});
        }});
    </script>
</body>
</html>'''
    return html


def generate_legend(data, total):
    """Generate legend HTML for pie chart."""
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    
    legend_items = []
    for idx, (ext, stats) in enumerate(data):
        count = stats["count"]
        pct = (count / total) * 100
        color = colors[idx % len(colors)]
        legend_items.append(f'''
            <div class="legend-item">
                <span class="legend-color" style="background: {color}"></span>
                <span>{ext} ({pct:.1f}%)</span>
            </div>''')
    
    # Add "Other" if needed
    other_count = sum(item[1]["count"] for item in list(data)[8:] if hasattr(data, '__iter__'))
    if len(data) >= 8:
        legend_items.append('''
            <div class="legend-item">
                <span class="legend-color" style="background: #888"></span>
                <span>Other</span>
            </div>''')
    
    return ''.join(legend_items)


def generate_largest_files_table(files):
    """Generate HTML table rows for largest files."""
    rows = []
    max_size = files[0]["size"] if files else 1
    
    for file in files:
        name = file["name"]
        if len(name) > 40:
            name = name[:37] + "..."
        
        ext = file["ext"]
        size = file["size"]
        size_formatted = format_size(size)
        bar_width = (size / max_size) * 100
        
        rows.append(f'''
            <tr>
                <td title="{file['path']}">{name}</td>
                <td><span class="ext-badge">{ext}</span></td>
                <td>
                    <div>{size_formatted}</div>
                    <div class="size-bar">
                        <div class="size-fill" style="width: {bar_width}%"></div>
                    </div>
                </td>
            </tr>''')
    
    return ''.join(rows)


def generate_file_types_table(data, total_files):
    """Generate HTML table rows for file types breakdown."""
    rows = []
    max_count = data[0][1]["count"] if data else 1
    
    for ext, stats in data[:15]:
        count = stats["count"]
        lines = stats["lines"]
        pct = (count / total_files) * 100
        bar_width = (count / max_count) * 100
        
        rows.append(f'''
            <tr>
                <td><span class="ext-badge">{ext}</span></td>
                <td>{count:,}</td>
                <td>{pct:.1f}%</td>
                <td>{lines:,}</td>
                <td>
                    <div class="size-bar">
                        <div class="size-fill" style="width: {bar_width}%"></div>
                    </div>
                </td>
            </tr>''')
    
    return ''.join(rows)


def main():
    """Main entry point."""
    print("🔍 Scanning directory...")
    
    # Get the directory to scan (default to current)
    scan_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    
    # Scan and gather stats
    stats = scan_directory(scan_dir)
    
    print(f"📊 Found {stats['total_files']:,} files")
    print(f"📝 Total lines of code: {stats['total_lines']:,}")
    print(f"📁 Maximum directory depth: {stats['max_depth']}")
    
    # Generate HTML
    print("🎨 Generating infographic...")
    html = generate_html(stats)
    
    # Write to file
    output_path = os.path.join(scan_dir, "stats.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Infographic saved to: {output_path}")
    print(f"🌐 Open the file in your browser to view!")


if __name__ == "__main__":
    main()