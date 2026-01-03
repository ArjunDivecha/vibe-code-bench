import os
import math
from collections import defaultdict, deque

start_dir = os.getcwd()

# Initialize data containers
file_extensions = defaultdict(int)
lines_per_ext = defaultdict(int)
total_lines = 0
largest_files = []
max_depth = 0

# Calculate max directory depth using BFS
queue = deque()
queue.append((start_dir, 0))
while queue:
    path, depth = queue.popleft()
    if depth > max_depth:
        max_depth = depth
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    queue.append((entry.path, depth + 1))
    except PermissionError:
        pass  # Skip directories we can't access

# Process all files for extensions, sizes, and line counts
for root, dirs, files in os.walk(start_dir):
    for filename in files:
        filepath = os.path.join(root, filename)
        # Extract extension
        ext = os.path.splitext(filename)[1][1:] if '.' in filename else 'no_ext'
        file_extensions[ext] += 1
        
        # Track file size
        try:
            size = os.path.getsize(filepath)
        except OSError:
            size = 0
        largest_files.append((size, filename, filepath))
        
        # Count lines if possible
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                line_count = len(lines)
                total_lines += line_count
                if ext:  # Only count if extension exists (not like .DS_Store)
                    lines_per_ext[ext] += line_count
        except (IOError, UnicodeDecodeError):
            pass  # Skip unreadable files

# Determine top 5 largest files
largest_files.sort(key=lambda x: -x[0])
top_files = largest_files[:5]

# Generate Pie Chart SVG
total_files_val = sum(file_extensions.values())
pie_svg = ''
if total_files_val > 0:
    colors = ['#FF5733', '#33FF57', '#3357FF', '#F3FF33', '#FF33A1',
             '#FF00FF', '#00FFFF', '#0000FF', '#FF0000', '#00FF00',
             '#800080', '#808080', '#C0C0C0', '#808000', '#008000']
    current_angle = 0
    cx, cy, r = 150, 150, 120
    pie_parts = ['<svg width="300" height="300" viewBox="0 0 300 300">']
    for ext, count in file_extensions.items():
        percentage = count / total_files_val
        angle = 2 * math.pi * percentage
        end_angle = current_angle + angle
        x1 = cx + r * math.cos(current_angle)
        y1 = cy + r * math.sin(current_angle)
        x2 = cx + r * math.cos(end_angle)
        y2 = cy + r * math.sin(end_angle)
        path_data = f"M {cx} {cy} L {x1:.0f} {y1:.0f} L {x2:.0f} {y2:.0f} Z"
        color = colors[len(pie_parts) % len(colors)]
        pie_parts.append(f'<path d="{path_data}" fill="{color}" />')
        current_angle = end_angle
    pie_parts.append('</svg>')
    pie_svg = ''.join(pie_parts)
else:
    pie_svg = '<svg width="300" height="300"><text x="150" y="150" fill="red">No files</text></svg>'

# Generate Bar Chart SVG
bar_svg = ''
sorted_exts = sorted(lines_per_ext.items(), key=lambda x: -x[1])[:5]
if sorted_exts:
    max_lines = max(ext[1] for ext in sorted_exts) if sorted_exts else 1
    scale = 180 / max_lines if max_lines > 0 else 1
    bar_parts = ['<svg width="300" height="200">']
    bar_parts.append('<g transform="translate(50, 180) scale(0.5)">')
    # Draw horizontal axis line
    bar_parts.append(f'<line x1="0" y1="0" x2="{len(sorted_exts)*40 + 50}" y2="0" stroke="black" />')
    for i, (ext, lines) in enumerate(sorted_exts):
        x_pos = i * 40 + 10
        h = lines * scale
        bar_parts.append(f'<rect x="{x_pos}" y="-{h:.0f}" width="20" height="{h:.0f}" fill="steelblue" />')
        bar_parts.append(f'<text x="{x_pos+15}" y="-{h-10:.0f}" text-anchor="middle" dominant-baseline="middle">{ext}: {lines}</text>')
    bar_parts.append('</g>')
    bar_parts.append('</svg>')
    bar_svg = ''.join(bar_parts)
else:
    bar_svg = '<svg width="300" height="200"><text x="150" y="100" fill="red">No data</text></svg>'

# Generate HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Codebase Fingerprint</title>
    <style>
        body {{
            background: #1a1a1a;
            color: white;
            font-family: Arial, sans-serif;
        }}
        .container {{
            display: grid;
            grid-template-areas: "header header header" "overview chart chart";
        }}
        .header {{
            grid-area: header;
            text-align: center;
            padding: 20px;
        }}
        .overview {{
            grid-area: overview;
            padding: 20px;
        }}
        .chart {{
            grid-area: chart;
            padding: 20px;
        }}
        .pie-chart, .bar-chart {{
            border: 1px solid white;
            padding: 10px;
        }}
        .pie-chart svg {{
            width: 300px;
            height: 300px;
        }}
        .bar-chart svg {{
            width: 300px;
            height: 200px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">Codebase Fingerprint</header>
        <div class="overview">
            <h2>Overview</h2>
            <ul>
                <li>Total Files: <span id="total-files">{total_files_val}</span></li>
                <li>Total Lines: <span id="total-lines">{total_lines}</span></li>
                <li>Max Directory Depth: <span id="max-depth">{max_depth}</span></li>
            </ul>
        </div>
        <div class="chart">
            <h2>File Type Distribution</h2>
            {pie_svg}
        </div>
        <div class="chart">
            <h2>Lines of Code by Type</h2>
            {bar_svg}
        </div>
    </div>
</body>
</html>
"""

with open('stats.html', 'w') as f:
    f.write(html_content)