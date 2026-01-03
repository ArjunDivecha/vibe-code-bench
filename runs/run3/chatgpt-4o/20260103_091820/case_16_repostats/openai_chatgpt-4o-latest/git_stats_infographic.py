import os
import sys
import collections
import math
import html

OUTPUT_FILE = 'stats.html'
MAX_LARGEST_FILES = 10

def scan_directory(base_path='.'):
    file_counts = collections.Counter()
    line_counts = {}
    total_lines = 0
    largest_files = []
    max_depth = 0

    for root, dirs, files in os.walk(base_path):
        rel_root = os.path.relpath(root, base_path)
        depth = rel_root.count(os.sep)
        max_depth = max(max_depth, depth)

        for file in files:
            filepath = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower() or 'no_ext'
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    line_count = len(lines)
            except Exception as e:
                continue

            file_counts[ext] += 1
            line_counts[filepath] = line_count
            total_lines += line_count

    sorted_largest_files = sorted(line_counts.items(), key=lambda x: x[1], reverse=True)[:MAX_LARGEST_FILES]

    return {
        'file_counts': file_counts,
        'line_counts': line_counts,
        'total_lines': total_lines,
        'largest_files': sorted_largest_files,
        'max_depth': max_depth
    }

def generate_pie_chart(file_counts):
    total = sum(file_counts.values())
    if total == 0:
        return '<text x="50%" y="50%" text-anchor="middle" fill="white">No files found</text>'
    radius = 100
    cx, cy = 120, 120
    svg_parts = []
    angle = 0
    colors = generate_colors(len(file_counts))
    for i, (ext, count) in enumerate(file_counts.items()):
        proportion = count / total
        theta = proportion * 2 * math.pi
        x1 = cx + radius * math.cos(angle)
        y1 = cy + radius * math.sin(angle)
        angle += theta
        x2 = cx + radius * math.cos(angle)
        y2 = cy + radius * math.sin(angle)
        large_arc = 1 if theta > math.pi else 0
        path = f'M {cx},{cy} L {x1},{y1} A {radius},{radius} 0 {large_arc},1 {x2},{y2} Z'
        svg_parts.append(f'<path d="{path}" fill="{colors[i]}" stroke="#222"/>')
    return ''.join(svg_parts)

def generate_bar_chart(largest_files):
    max_lines = max((lines for _, lines in largest_files), default=1)
    bar_svg = ''
    bar_width = 40
    spacing = 20
    for i, (filename, lines) in enumerate(largest_files):
        height = int((lines / max_lines) * 100)
        x = i * (bar_width + spacing)
        y = 120 - height
        label = html.escape(os.path.basename(filename))
        bar_svg += f'''
            <g>
                <rect x="{x}" y="{y}" width="{bar_width}" height="{height}" fill="#4dd0e1"/>
                <text x="{x + bar_width/2}" y="130" fill="white" font-size="10" text-anchor="middle" transform="rotate(45, {x + bar_width/2}, 130)">{label}</text>
                <text x="{x + bar_width/2}" y="{y - 5}" fill="white" font-size="10" text-anchor="middle">{lines}</text>
            </g>
        '''
    return bar_svg

def generate_colors(n):
    colors = []
    for i in range(n):
        hue = i * (360 / n)
        colors.append(f'hsl({hue}, 70%, 50%)')
    return colors

def generate_html(stats):
    file_counts = stats['file_counts']
    total_lines = stats['total_lines']
    largest_files = stats['largest_files']
    max_depth = stats['max_depth']

    pie_chart_svg = generate_pie_chart(file_counts)
    bar_chart_svg = generate_bar_chart(largest_files)

    file_types_html = ''.join(
        f'<li>{html.escape(ext)}: {count}</li>' for ext, count in file_counts.most_common()
    )

    largest_files_html = ''.join(
        f'<li>{html.escape(path)} - {lines} lines</li>' for path, lines in largest_files
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Codebase Fingerprint</title>
<style>
body {{
    background-color: #121212;
    color: #e0e0e0;
    font-family: sans-serif;
    padding: 20px;
}}
h1 {{
    text-align: center;
    color: #ffffff;
}}
.dashboard {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    margin-top: 30px;
}}
.card {{
    background-color: #1e1e1e;
    padding: 20px;
    border-radius: 10px;
}}
.card h2 {{
    margin-top: 0;
    color: #80cbc4;
}}
svg {{
    width: 100%;
    height: 250px;
}}
ul {{
    list-style: none;
    padding: 0;
}}
li {{
    margin: 5px 0;
}}
@media (max-width: 800px) {{
    .dashboard {{
        grid-template-columns: 1fr;
    }}
}}
</style>
</head>
<body>
<h1>Codebase Fingerprint</h1>
<div class="dashboard">
    <div class="card">
        <h2>File Types</h2>
        <svg viewBox="0 0 240 240">
            {pie_chart_svg}
        </svg>
        <ul>
            {file_types_html}
        </ul>
    </div>
    <div class="card">
        <h2>Largest Files</h2>
        <svg viewBox="0 0 500 150">
            {bar_chart_svg}
        </svg>
        <ul>
            {largest_files_html}
        </ul>
    </div>
    <div class="card">
        <h2>Summary</h2>
        <ul>
            <li>Total Lines of Code: {total_lines}</li>
            <li>Directory Depth: {max_depth}</li>
            <li>Total Files: {sum(file_counts.values())}</li>
            <li>Unique Extensions: {len(file_counts)}</li>
        </ul>
    </div>
</div>
</body>
</html>
'''

def main():
    stats = scan_directory()
    html_output = generate_html(stats)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_output)
    print(f"Generated {OUTPUT_FILE}")

if __name__ == '__main__':
    main()