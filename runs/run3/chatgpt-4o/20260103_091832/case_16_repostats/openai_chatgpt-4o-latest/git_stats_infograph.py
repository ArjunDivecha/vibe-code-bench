import os
import sys
import collections
import html
import math

OUTPUT_FILE = "stats.html"
MAX_LARGEST_FILES = 10


def scan_directory(root):
    file_extensions = collections.Counter()
    total_lines = 0
    largest_files = []
    max_depth = 0

    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath[len(root):].count(os.sep)
        max_depth = max(max_depth, depth)

        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                ext = os.path.splitext(filename)[1].lower() or "NO_EXT"
                file_extensions[ext] += 1

                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = sum(1 for _ in f)
                    total_lines += lines
                    largest_files.append((lines, filepath))
            except Exception:
                continue  # skip unreadable files

    largest_files.sort(reverse=True)
    largest_files = largest_files[:MAX_LARGEST_FILES]

    return {
        "file_extensions": file_extensions,
        "total_lines": total_lines,
        "largest_files": largest_files,
        "max_depth": max_depth,
    }


def generate_pie_chart(file_extensions):
    total = sum(file_extensions.values())
    if total == 0:
        return ""

    colors = [
        "#e6194b", "#3cb44b", "#ffe119", "#4363d8",
        "#f58231", "#911eb4", "#46f0f0", "#f032e6",
        "#bcf60c", "#fabebe", "#008080", "#e6beff",
        "#9a6324", "#fffac8", "#800000", "#aaffc3",
        "#808000", "#ffd8b1", "#000075", "#808080"
    ]
    svg_parts = []
    cx, cy, r = 100, 100, 100
    start_angle = 0
    idx = 0

    for ext, count in file_extensions.most_common(10):
        angle = (count / total) * 360
        end_angle = start_angle + angle

        x1 = cx + r * math.cos(math.radians(start_angle))
        y1 = cy + r * math.sin(math.radians(start_angle))
        x2 = cx + r * math.cos(math.radians(end_angle))
        y2 = cy + r * math.sin(math.radians(end_angle))
        large_arc = 1 if angle > 180 else 0

        path = f"M {cx},{cy} L {x1},{y1} A {r},{r} 0 {large_arc},1 {x2},{y2} Z"
        color = colors[idx % len(colors)]
        svg_parts.append(f'<path d="{path}" fill="{color}"><title>{ext}: {count}</title></path>')
        start_angle = end_angle
        idx += 1

    legend_items = []
    idx = 0
    for ext, count in file_extensions.most_common(10):
        color = colors[idx % len(colors)]
        legend_items.append(f'<div class="legend-item"><span style="background:{color}"></span>{html.escape(ext)} ({count})</div>')
        idx += 1

    legend_html = '<div class="legend">' + "".join(legend_items) + '</div>'
    svg_html = f'<svg viewBox="0 0 200 200" class="pie-chart">{"".join(svg_parts)}</svg>'
    return f'<div class="chart-section">{svg_html}{legend_html}</div>'


def generate_bar_chart(largest_files):
    if not largest_files:
        return ""

    max_lines = max([lines for lines, _ in largest_files])
    bars = []
    for lines, filepath in largest_files:
        width = (lines / max_lines) * 100
        bars.append(f'''
        <div class="bar-item">
            <div class="bar-label">{html.escape(filepath)}</div>
            <div class="bar" style="width:{width}%">
                <span>{lines} lines</span>
            </div>
        </div>
        ''')

    return '<div class="bar-chart">' + "".join(bars) + '</div>'


def generate_html(stats):
    pie_chart = generate_pie_chart(stats["file_extensions"])
    bar_chart = generate_bar_chart(stats["largest_files"])

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Codebase Fingerprint</title>
<style>
body {{
    background: #121212;
    color: #e0e0e0;
    font-family: sans-serif;
    margin: 0;
    padding: 2em;
}}
h1 {{
    text-align: center;
    color: #ffffff;
}}
.dashboard {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2em;
}}
.section {{
    background: #1e1e1e;
    padding: 1em;
    border-radius: 10px;
}}
.chart-section {{
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
}}
.pie-chart {{
    width: 200px;
    height: 200px;
}}
.legend {{
    display: flex;
    flex-direction: column;
    margin-left: 1em;
}}
.legend-item {{
    display: flex;
    align-items: center;
    margin-bottom: 0.3em;
    font-size: 0.9em;
}}
.legend-item span {{
    display: inline-block;
    width: 1em;
    height: 1em;
    margin-right: 0.5em;
}}
.bar-chart {{
    display: flex;
    flex-direction: column;
    gap: 0.5em;
}}
.bar-item {{
    display: flex;
    flex-direction: column;
}}
.bar-label {{
    font-size: 0.8em;
    color: #aaa;
    margin-bottom: 0.2em;
    overflow-wrap: anywhere;
}}
.bar {{
    background: #333;
    height: 20px;
    position: relative;
    border-radius: 5px;
    overflow: hidden;
}}
.bar span {{
    position: absolute;
    right: 5px;
    top: 0;
    font-size: 0.8em;
    color: #fff;
}}
.bar::before {{
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    background: #03dac6;
    width: 100%;
    z-index: -1;
}}
.summary {{
    font-size: 1.2em;
    display: flex;
    flex-direction: column;
    gap: 0.5em;
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
    <div class="section">
        <h2>File Types Distribution</h2>
        {pie_chart}
    </div>
    <div class="section">
        <h2>Largest Files</h2>
        {bar_chart}
    </div>
    <div class="section summary">
        <h2>Summary</h2>
        <div><strong>Total Lines of Code:</strong> {stats['total_lines']}</div>
        <div><strong>Unique File Extensions:</strong> {len(stats['file_extensions'])}</div>
        <div><strong>Max Directory Depth:</strong> {stats['max_depth']}</div>
    </div>
</div>
</body>
</html>
"""
    return html_content


def main():
    root = os.getcwd()
    stats = scan_directory(root)
    html_code = generate_html(stats)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_code)

    print(f"Generated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()