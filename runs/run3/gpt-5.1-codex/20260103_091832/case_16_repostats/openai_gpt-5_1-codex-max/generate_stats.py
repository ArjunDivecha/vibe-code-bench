import os
import math
import html
from string import Template

# ----------------------- Data Collection --------------------------------- #

def is_binary_file(path):
    try:
        with open(path, 'rb') as f:
            chunk = f.read(2048)
            if b'\0' in chunk:
                return True
            try:
                chunk.decode('utf-8')
            except UnicodeDecodeError:
                return True
    except (IOError, OSError):
        return True
    return False

def count_lines(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except (IOError, OSError):
        return 0

def human_size(num):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} TB"

def scan_directory(root='.'):
    counts_by_ext = {}
    lines_by_ext = {}
    total_lines = 0
    largest_files = []
    max_depth = 0
    total_files = 0

    for current_root, dirs, files in os.walk(root):
        # Skip the output file if regenerating
        files = [f for f in files if f != 'stats.html']
        for name in files:
            full_path = os.path.join(current_root, name)
            if os.path.islink(full_path):
                continue
            rel_path = os.path.relpath(full_path, root)
            depth = len(rel_path.split(os.sep)) - 1
            if depth > max_depth:
                max_depth = depth

            ext = os.path.splitext(name)[1].lower()
            if not ext:
                ext = "(no ext)"
            counts_by_ext[ext] = counts_by_ext.get(ext, 0) + 1
            total_files += 1

            try:
                size = os.path.getsize(full_path)
            except (IOError, OSError):
                size = 0
            largest_files.append((size, rel_path))

            if not is_binary_file(full_path):
                lines = count_lines(full_path)
                total_lines += lines
                lines_by_ext[ext] = lines_by_ext.get(ext, 0) + lines

    largest_files.sort(key=lambda x: x[0], reverse=True)
    largest_files = largest_files[:10]
    return {
        'counts_by_ext': counts_by_ext,
        'lines_by_ext': lines_by_ext,
        'total_lines': total_lines,
        'largest_files': largest_files,
        'max_depth': max_depth,
        'total_files': total_files
    }

# ----------------------- Visualization Helpers --------------------------- #

PALETTE = [
    "#f94144", "#f3722c", "#f8961e", "#f9c74f", "#90be6d",
    "#43aa8b", "#4d96ff", "#9d4edd", "#ff6bcb", "#56cfe1"
]

def build_pie_paths(data, cx=140, cy=140, r=110):
    total = sum(v for _, v, _ in data)
    if total == 0:
        return ""
    start_angle = -math.pi / 2  # Start at top
    paths = []
    for label, value, color in data:
        if value == 0:
            continue
        angle = (value / total) * 2 * math.pi
        end_angle = start_angle + angle
        x1 = cx + r * math.cos(start_angle)
        y1 = cy + r * math.sin(start_angle)
        x2 = cx + r * math.cos(end_angle)
        y2 = cy + r * math.sin(end_angle)
        large_arc = 1 if angle > math.pi else 0
        path_d = f"M {cx},{cy} L {x1},{y1} A {r},{r} 0 {large_arc} 1 {x2},{y2} Z"
        percent = (value / total) * 100
        paths.append(f'<path d="{path_d}" fill="{color}"><title>{html.escape(label)}: {value} file(s) ({percent:.1f}%)</title></path>')
        start_angle = end_angle
    return "\n".join(paths)

def build_bar_rects(data, width=520, height=260, padding=40):
    if not data:
        return "", 0
    max_val = max(v for _, v, _ in data) or 1
    bar_space = (width - padding * 2) / len(data)
    bar_width = bar_space * 0.62
    rects = []
    for idx, (label, value, color) in enumerate(data):
        x = padding + idx * bar_space + (bar_space - bar_width) / 2
        bar_height = (value / max_val) * (height - padding * 2)
        y = height - padding - bar_height
        rects.append(
            f'<g class="bar"><rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="{color}"></rect>'
            f'<text x="{x + bar_width/2:.1f}" y="{height - padding/2:.1f}" text-anchor="middle" class="bar-label">{html.escape(label)}</text>'
            f'<text x="{x + bar_width/2:.1f}" y="{y - 8:.1f}" text-anchor="middle" class="bar-value">{value:,}</text></g>'
        )
    return "\n".join(rects), max_val

# ----------------------- HTML Generation --------------------------------- #

def generate_html(stats):
    counts_by_ext = stats['counts_by_ext']
    lines_by_ext = stats['lines_by_ext']
    total_files = stats['total_files']
    total_lines = stats['total_lines']
    largest_files = stats['largest_files']
    max_depth = stats['max_depth']

    sorted_ext_counts = sorted(counts_by_ext.items(), key=lambda x: x[1], reverse=True)
    sorted_ext_lines = sorted(lines_by_ext.items(), key=lambda x: x[1], reverse=True)

    def top_data(entries):
        top = entries[:8]
        if len(entries) > 8:
            remainder = sum(v for _, v in entries[8:])
            top.append(("Other", remainder))
        return top

    pie_entries = top_data(sorted_ext_counts)
    pie_data = []
    for idx, (label, value) in enumerate(pie_entries):
        pie_data.append((label, value, PALETTE[idx % len(PALETTE)]))

    bar_entries = top_data(sorted_ext_lines)
    bar_data = []
    for idx, (label, value) in enumerate(bar_entries):
        bar_data.append((label, value, PALETTE[idx % len(PALETTE)]))

    pie_paths = build_pie_paths(pie_data)
    bar_rects, bar_max = build_bar_rects(bar_data)

    pie_legend = ""
    total_pie = sum(v for _, v, _ in pie_data) or 1
    for label, value, color in pie_data:
        percent = (value / total_pie) * 100
        pie_legend += (
            f'<div class="legend-item">'
            f'<span class="dot" style="background:{color}"></span>'
            f'<div><div class="legend-label">{html.escape(label)}</div>'
            f'<div class="legend-sub">{value} file(s) • {percent:.1f}%</div></div>'
            f'</div>'
        )

    bars_present = bool(bar_data)
    bar_note = "Top extensions by line count" if bars_present else "No text-based files detected."

    largest_rows = ""
    if largest_files:
        for size, path in largest_files:
            largest_rows += (
                f'<div class="file-row">'
                f'<div class="file-name">{html.escape(path)}</div>'
                f'<div class="file-size">{human_size(size)}</div>'
                f'</div>'
            )
    else:
        largest_rows = '<div class="file-row">No files found.</div>'

    ext_count = len(counts_by_ext)

    html_template = Template(r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Codebase Fingerprint</title>
<style>
:root {
    --bg: #0b1021;
    --panel: #131b33;
    --glow: #1f2a4d;
    --text: #e6e8f0;
    --muted: #9aa0b8;
    --accent: #7dd3fc;
    --accent-2: #ff6bcb;
    --accent-3: #9d4edd;
    --radius: 14px;
    --shadow: 0 10px 30px rgba(0,0,0,0.35);
}
* { box-sizing: border-box; }
body {
    margin: 0;
    padding: 28px;
    background: radial-gradient(circle at 20% 20%, rgba(79,70,229,0.12), transparent 25%),
                radial-gradient(circle at 80% 0%, rgba(13,148,136,0.14), transparent 30%),
                var(--bg);
    color: var(--text);
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    line-height: 1.5;
}
h1 {
    letter-spacing: 1px;
    margin: 0 0 6px 0;
    font-weight: 800;
}
.subtitle {
    color: var(--muted);
    margin-bottom: 24px;
}
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 18px;
}
.card {
    background: linear-gradient(145deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border: 1px solid rgba(255,255,255,0.04);
    box-shadow: var(--shadow);
    border-radius: var(--radius);
    padding: 18px;
    position: relative;
    overflow: hidden;
}
.card::before {
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.06), transparent 30%);
    opacity: 0.4;
    pointer-events: none;
}
.card h2 {
    margin: 0 0 12px 0;
    font-size: 18px;
    color: #f4f5fb;
}
.kpi-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
}
.kpi {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
    padding: 12px 14px;
    border-radius: 12px;
}
.kpi .label { color: var(--muted); font-size: 13px; }
.kpi .value { font-size: 26px; font-weight: 700; }
.pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(255,255,255,0.06);
    color: var(--muted);
    font-size: 12px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.charts {
    display: grid;
    grid-template-columns: 1.1fr 1fr;
    gap: 14px;
}
@media(max-width: 900px){
    .charts { grid-template-columns: 1fr; }
}
.chart-area {
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}
.legend {
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
    margin-top: 10px;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 10px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
}
.dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 0 4px rgba(255,255,255,0.02);
}
.legend-label { font-weight: 600; color: #f8f9ff; }
.legend-sub { font-size: 12px; color: var(--muted); }
svg { width: 100%; height: auto; }
.pie-svg {
    max-width: 320px;
    filter: drop-shadow(0 10px 25px rgba(0,0,0,0.35));
}
.bar-svg text { fill: var(--muted); font-size: 12px; }
.bar-svg .bar-label { fill: var(--muted); font-size: 12px; }
.bar-svg .bar-value { fill: #fff; font-size: 11px; }
.bar-svg line.axis { stroke: rgba(255,255,255,0.08); }
.file-row {
    display: grid;
    grid-template-columns: 1fr auto;
    padding: 10px 12px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 10px;
    margin-bottom: 8px;
}
.file-row .file-name { color: #f4f5fb; overflow-wrap: anywhere; }
.file-row .file-size { color: var(--muted); font-variant-numeric: tabular-nums; }
.badge {
    padding: 4px 8px;
    background: rgba(125,211,252,0.12);
    border: 1px solid rgba(125,211,252,0.4);
    color: #7dd3fc;
    border-radius: 8px;
    font-size: 12px;
}
.depth-bar {
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
    height: 14px;
    overflow: hidden;
    position: relative;
}
.depth-fill {
    height: 100%;
    background: linear-gradient(90deg, #7dd3fc, #9d4edd);
    width: 0;
}
footer {
    margin-top: 24px;
    text-align: center;
    color: var(--muted);
    font-size: 13px;
}
</style>
</head>
<body>
<header>
    <div class="pill">Codebase Fingerprint</div>
    <h1>Codebase Fingerprint</h1>
    <div class="subtitle">An at-a-glance fingerprint of this repository's structure and scale.</div>
</header>

<div class="grid">
    <div class="card">
        <h2>Snapshot</h2>
        <div class="kpi-row">
            <div class="kpi">
                <div class="label">Total Files</div>
                <div class="value">${total_files}</div>
            </div>
            <div class="kpi">
                <div class="label">Lines of Code</div>
                <div class="value">${total_lines}</div>
            </div>
            <div class="kpi">
                <div class="label">File Types</div>
                <div class="value">${ext_count}</div>
            </div>
            <div class="kpi">
                <div class="label">Max Depth</div>
                <div class="value">${max_depth}</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>File Type Footprint</h2>
        <div class="charts">
            <div class="chart-area">
                <svg class="pie-svg" viewBox="0 0 280 280" role="img" aria-label="File type distribution pie chart">
                    ${pie_paths}
                </svg>
            </div>
            <div>
                <div class="legend">
                    ${pie_legend}
                </div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>Line Density</h2>
        <p style="color:var(--muted); margin-top:-6px; margin-bottom:8px;">${bar_note}</p>
        <svg class="bar-svg" viewBox="0 0 560 280" role="img" aria-label="Line counts per extension">
            <line class="axis" x1="32" y1="240" x2="540" y2="240" />
            ${bar_rects}
        </svg>
    </div>

    <div class="card">
        <h2>Largest Files</h2>
        ${largest_rows}
    </div>

    <div class="card">
        <h2>Structure</h2>
        <p style="color:var(--muted);">Maximum directory nesting depth observed in this scan.</p>
        <div class="depth-bar">
            <div class="depth-fill" style="width:${depth_percent}%;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:8px; color:var(--muted);">
            <span>Shallow</span><span>${max_depth} levels</span><span>Deep</span>
        </div>
    </div>
</div>

<footer>
    Generated by Git Stats Infographic Generator — ${total_files} files parsed.
</footer>
</body>
</html>
""")

    depth_percent = max(8, min(100, (max_depth / 12) * 100)) if max_depth else 8

    html_output = html_template.substitute(
        total_files=f"{total_files:,}",
        total_lines=f"{total_lines:,}",
        ext_count=len(counts_by_ext),
        max_depth=max_depth,
        pie_paths=pie_paths or '<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#777">No data</text>',
        pie_legend=pie_legend or '<div class="legend-item"><div class="legend-label">No files</div></div>',
        bar_rects=bar_rects or '',
        bar_note=bar_note,
        largest_rows=largest_rows,
        depth_percent=f"{depth_percent:.1f}"
    )
    return html_output

# ----------------------- Main -------------------------------------------- #

def main():
    stats = scan_directory('.')
    html_content = generate_html(stats)
    output_path = os.path.join(os.getcwd(), 'stats.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Infographic generated: {output_path}")

if __name__ == "__main__":
    main()