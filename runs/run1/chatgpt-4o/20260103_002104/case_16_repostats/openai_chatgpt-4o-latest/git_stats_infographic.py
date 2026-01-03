import os
import sys
import collections
import html
import math

OUTPUT_FILE = "stats.html"
MAX_LARGEST_FILES = 10

def get_all_files(base_dir):
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            yield os.path.join(root, f)

def get_extension(filename):
    return os.path.splitext(filename)[1].lower() or 'no_ext'

def count_lines(filepath):
    try:
        with open(filepath, 'rb') as f:
            return sum(1 for line in f)
    except Exception:
        return 0

def calculate_directory_depth(base_dir):
    max_depth = 0
    for root, dirs, files in os.walk(base_dir):
        rel_path = os.path.relpath(root, base_dir)
        if rel_path == ".":
            depth = 0
        else:
            depth = rel_path.count(os.sep)
        max_depth = max(max_depth, depth)
    return max_depth

def generate_stats(base_dir):
    ext_counter = collections.Counter()
    total_lines = 0
    largest_files = []
    files_info = []

    for filepath in get_all_files(base_dir):
        ext = get_extension(filepath)
        ext_counter[ext] += 1
        lines = count_lines(filepath)
        total_lines += lines
        size = os.path.getsize(filepath)
        files_info.append((filepath, size, lines))

    files_info.sort(key=lambda x: x[1], reverse=True)
    largest_files = files_info[:MAX_LARGEST_FILES]
    depth = calculate_directory_depth(base_dir)

    return {
        'file_counts': ext_counter,
        'total_lines': total_lines,
        'largest_files': largest_files,
        'directory_depth': depth
    }

def generate_pie_chart(file_counts):
    total = sum(file_counts.values())
    if total == 0:
        return '<text x="50%" y="50%" fill="white" text-anchor="middle">No data</text>'

    radius = 80
    cx, cy = 100, 100
    angle_start = 0
    colors = ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4",
              "#46f0f0", "#f032e6", "#bcf60c", "#fabebe", "#008080", "#e6beff",
              "#9a6324", "#fffac8", "#800000", "#aaffc3", "#808000", "#ffd8b1"]

    svg_parts = []
    for i, (ext, count) in enumerate(file_counts.items()):
        angle = count / total * 360
        angle_end = angle_start + angle
        x1 = cx + radius * math.cos(math.radians(angle_start))
        y1 = cy + radius * math.sin(math.radians(angle_start))
        x2 = cx + radius * math.cos(math.radians(angle_end))
        y2 = cy + radius * math.sin(math.radians(angle_end))
        large_arc = 1 if angle > 180 else 0

        path = f"M{cx},{cy} L{x1},{y1} A{radius},{radius} 0 {large_arc},1 {x2},{y2} Z"
        color = colors[i % len(colors)]
        svg_parts.append(f'<path d="{path}" fill="{color}"><title>{ext}: {count}</title></path>')
        angle_start = angle_end

    return "\n".join(svg_parts)

def generate_bar_chart(largest_files):
    if not largest_files:
        return '<text x="10" y="20" fill="white">No files to display</text>'

    max_lines = max(lines for _, _, lines in largest_files) or 1
    chart_height = 150
    bar_width = 40
    spacing = 10
    svg_parts = []
    for i, (path, size, lines) in enumerate(largest_files):
        height = lines / max_lines * chart_height
        x = i * (bar_width + spacing)
        y = chart_height - height
        filename = os.path.basename(path)
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{bar_width}" height="{height}" fill="#00d6ff">'
            f'<title>{filename}: {lines} lines</title></rect>'
            f'<text x="{x + bar_width/2}" y="{chart_height + 15}" fill="white" text-anchor="middle" font-size="10">{html.escape(filename[:10])}</text>'
        )
    return "\n".join(svg_parts)

def generate_html(stats):
    file_counts = stats['file_counts']
    total_lines = stats['total_lines']
    largest_files = stats['largest_files']
    directory_depth = stats['directory_depth']

    pie_chart = generate_pie_chart(file_counts)
    bar_chart = generate_bar_chart(largest_files)

    file_count_items = "".join(
        f"<li>{html.escape(ext)}: {count}</li>" for ext, count in file_counts.most_common()
    )

    largest_files_list = "".join(
        f"<li>{html.escape(os.path.basename(path))} - {size} bytes, {lines} lines</li>"
        for path, size, lines in largest_files
    )

    return f"""<!DOCTYPE html>
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
        header {{
            padding: 20px;
            text-align: center;
            background-color: #1e1e1e;
            font-size: 2em;
            color: #00d6ff;
        }}
        main {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-gap: 20px;
            padding: 20px;
        }}
        section {{
            background-color: #1e1e1e;
            padding: 20px;
            border-radius: 8px;
        }}
        h2 {{
            color: #00d6ff;
        }}
        ul {{
            list-style: none;
            padding: 0;
        }}
        svg {{
            display: block;
            margin: auto;
        }}
        .full {{
            grid-column: span 2;
        }}
    </style>
</head>
<body>
    <header>Codebase Fingerprint</header>
    <main>
        <section>
            <h2>File Types</h2>
            <svg width="200" height="200">{pie_chart}</svg>
            <ul>{file_count_items}</ul>
        </section>
        <section>
            <h2>Largest Files</h2>
            <svg width="100%" height="180">{bar_chart}</svg>
            <ul>{largest_files_list}</ul>
        </section>
        <section>
            <h2>Summary</h2>
            <ul>
                <li>Total lines of code: {total_lines}</li>
                <li>Directory depth: {directory_depth}</li>
                <li>Total files: {sum(file_counts.values())}</li>
            </ul>
        </section>
    </main>
</body>
</html>
"""

def main():
    base_dir = os.getcwd()
    stats = generate_stats(base_dir)
    html_content = generate_html(stats)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()