import os
import sys
import html
from collections import defaultdict
import math

OUTPUT_FILE = "stats.html"
MAX_LARGEST_FILES = 10

def get_all_files(base_path):
    file_info = []
    max_depth = 0
    for root, dirs, files in os.walk(base_path):
        rel_path = os.path.relpath(root, base_path)
        depth = rel_path.count(os.sep)
        max_depth = max(max_depth, depth)
        for file in files:
            full_path = os.path.join(root, file)
            try:
                size = os.path.getsize(full_path)
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = sum(1 for _ in f)
                ext = os.path.splitext(file)[1].lower()
                file_info.append({
                    'path': os.path.relpath(full_path, base_path),
                    'ext': ext if ext else 'No Ext',
                    'lines': lines,
                    'size': size,
                    'depth': depth
                })
            except Exception as e:
                continue  # Skip unreadable files
    return file_info, max_depth

def generate_pie_chart(data, width=300, height=300):
    total = sum(data.values())
    if total == 0:
        return "<text x='10' y='20' fill='white'>No data</text>"
    cx, cy = width // 2, height // 2
    radius = min(cx, cy) - 10
    angle = 0
    svg_parts = []
    colors = generate_colors(len(data))
    for i, (key, value) in enumerate(sorted(data.items(), key=lambda x: -x[1])):
        portion = value / total
        angle2 = angle + portion * 360
        x1 = cx + radius * math.cos(math.radians(angle))
        y1 = cy + radius * math.sin(math.radians(angle))
        x2 = cx + radius * math.cos(math.radians(angle2))
        y2 = cy + radius * math.sin(math.radians(angle2))
        large_arc = 1 if angle2 - angle > 180 else 0
        path = f"M{cx},{cy} L{x1},{y1} A{radius},{radius} 0 {large_arc},1 {x2},{y2} Z"
        svg_parts.append(f"<path d='{path}' fill='{colors[i]}'><title>{key}: {value}</title></path>")
        angle = angle2
    return "\n".join(svg_parts)

def generate_bar_chart(data, width=500, height=300):
    max_value = max(data.values(), default=1)
    bar_width = width // len(data) if data else 0
    svg_parts = []
    colors = generate_colors(len(data))
    for i, (key, value) in enumerate(data.items()):
        bar_height = int((value / max_value) * (height - 20))
        x = i * bar_width
        y = height - bar_height
        svg_parts.append(
            f"<rect x='{x}' y='{y}' width='{bar_width - 4}' height='{bar_height}' fill='{colors[i]}'><title>{key}: {value} lines</title></rect>"
        )
        svg_parts.append(
            f"<text x='{x + bar_width // 2}' y='{height}' fill='white' font-size='10' text-anchor='middle' transform='rotate(45,{x + bar_width // 2},{height + 5})'>{html.escape(key)}</text>"
        )
    return "\n".join(svg_parts)

def generate_colors(n):
    base_colors = [
        "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
        "#911eb4", "#46f0f0", "#f032e6", "#bcf60c", "#fabebe",
        "#008080", "#e6beff", "#9a6324", "#fffac8", "#800000",
        "#aaffc3", "#808000", "#ffd8b1", "#000075", "#808080"
    ]
    return (base_colors * ((n // len(base_colors)) + 1))[:n]

def generate_html(stats):
    ext_counts = stats['ext_counts']
    largest_files = stats['largest_files']
    total_lines = stats['total_lines']
    total_files = stats['total_files']
    max_depth = stats['max_depth']

    pie_svg = generate_pie_chart(ext_counts)
    bar_svg = generate_bar_chart({f['path']: f['lines'] for f in largest_files})

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Codebase Fingerprint</title>
<style>
body {{
    background-color: #121212;
    color: #ffffff;
    font-family: sans-serif;
    margin: 0;
    padding: 0;
}}
h1 {{
    text-align: center;
    padding: 1rem;
    font-size: 2rem;
    color: #00eaff;
}}
.container {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    padding: 1rem;
}}
.card {{
    background-color: #1e1e1e;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0,0,0,0.5);
}}
svg {{
    width: 100%;
    height: auto;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    color: #fff;
    font-size: 0.9rem;
}}
th, td {{
    text-align: left;
    padding: 0.5rem;
    border-bottom: 1px solid #333;
}}
</style>
</head>
<body>
<h1>Codebase Fingerprint</h1>
<div class="container">
    <div class="card">
        <h2>Summary</h2>
        <p>Total Files: {total_files}</p>
        <p>Total Lines: {total_lines}</p>
        <p>Max Directory Depth: {max_depth}</p>
    </div>
    <div class="card">
        <h2>File Types</h2>
        <svg viewBox="0 0 300 300">{pie_svg}</svg>
    </div>
    <div class="card">
        <h2>Largest Files by Lines</h2>
        <svg viewBox="0 0 500 300">{bar_svg}</svg>
    </div>
    <div class="card">
        <h2>Top Largest Files</h2>
        <table>
            <tr><th>File</th><th>Lines</th><th>Size (bytes)</th></tr>
            {''.join(f"<tr><td>{html.escape(f['path'])}</td><td>{f['lines']}</td><td>{f['size']}</td></tr>" for f in largest_files)}
        </table>
    </div>
</div>
</body>
</html>
"""
    return html_content

def main():
    base_path = os.getcwd()
    files, max_depth = get_all_files(base_path)

    ext_counts = defaultdict(int)
    total_lines = 0
    for f in files:
        ext_counts[f['ext']] += 1
        total_lines += f['lines']

    largest_files = sorted(files, key=lambda x: x['lines'], reverse=True)[:MAX_LARGEST_FILES]

    stats = {
        'ext_counts': dict(ext_counts),
        'total_lines': total_lines,
        'total_files': len(files),
        'largest_files': largest_files,
        'max_depth': max_depth,
    }

    html_output = generate_html(stats)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write(html_output)
    print(f"Infographic generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()