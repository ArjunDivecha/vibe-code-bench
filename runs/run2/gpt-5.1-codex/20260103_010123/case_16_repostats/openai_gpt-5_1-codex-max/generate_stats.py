import os
import math
import datetime
import html
from collections import defaultdict
from string import Template

PALETTE = [
    "#7C3AED", "#06B6D4", "#F59E0B", "#10B981", "#EF4444",
    "#8B5CF6", "#F472B6", "#22D3EE", "#F97316", "#4ADE80",
    "#A855F7", "#38BDF8"
]

IGNORE_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.idea', '.DS_Store'}


def human_bytes(num):
    step = 1024.0
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num < step:
            return f"{num:.1f} {unit}"
        num /= step
    return f"{num:.1f} PB"


def format_int(n):
    return f"{n:,}"


def count_lines(path):
    total = 0
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                total += chunk.count(b'\n')
    except Exception:
        return 0
    return total


def scan_codebase(root="."):
    ext_counts = defaultdict(int)
    ext_lines = defaultdict(int)
    largest = []  # list of (size, relpath, lines)
    total_lines = 0
    total_files = 0
    max_depth = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        rel_dir = os.path.relpath(dirpath, root)
        depth = 0 if rel_dir == '.' else len(rel_dir.split(os.sep))
        max_depth = max(max_depth, depth)

        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            relpath = os.path.relpath(fpath, root)
            ext = os.path.splitext(fname)[1].lower()
            ext = ext[1:] if ext.startswith('.') else ext
            if not ext:
                ext = "(none)"

            try:
                size = os.path.getsize(fpath)
            except Exception:
                continue

            lines = count_lines(fpath)
            total_lines += lines
            total_files += 1
            ext_counts[ext] += 1
            ext_lines[ext] += lines

            largest.append((size, relpath, lines))
            largest.sort(key=lambda x: x[0], reverse=True)
            if len(largest) > 7:
                largest.pop()

    scanned_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "root": os.path.abspath(root),
        "ext_counts": dict(ext_counts),
        "ext_lines": dict(ext_lines),
        "largest": largest,
        "total_lines": total_lines,
        "total_files": total_files,
        "max_depth": max_depth,
        "scanned_at": scanned_at
    }


def assign_colors(labels):
    colors = {}
    for i, label in enumerate(labels):
        colors[label] = PALETTE[i % len(PALETTE)]
    return colors


def polar_to_cart(cx, cy, r, angle_deg):
    rad = math.radians(angle_deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def render_pie(data, color_map, size=240):
    if not data:
        return f'<svg viewBox="0 0 {size} {size}" aria-label="empty pie"></svg>'

    total = sum(v for _, v in data)
    if total == 0:
        return f'<svg viewBox="0 0 {size} {size}" aria-label="empty pie"></svg>'

    cx = cy = size / 2
    r = size * 0.38
    if len(data) == 1:
        label, value = data[0]
        color = color_map.get(label, PALETTE[0])
        return (f'<svg viewBox="0 0 {size} {size}">'
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="0.9"></circle>'
                f'</svg>')

    start_angle = -90
    paths = []
    for label, value in data:
        if value == 0:
            continue
        angle = (value / total) * 360
        end_angle = start_angle + angle
        start_x, start_y = polar_to_cart(cx, cy, r, start_angle)
        end_x, end_y = polar_to_cart(cx, cy, r, end_angle)
        large_arc = 1 if angle > 180 else 0
        path = (
            f'M {cx} {cy} '
            f'L {start_x:.4f} {start_y:.4f} '
            f'A {r} {r} 0 {large_arc} 1 {end_x:.4f} {end_y:.4f} Z'
        )
        color = color_map.get(label, PALETTE[0])
        paths.append(f'<path d="{path}" fill="{color}" opacity="0.9"></path>')
        start_angle = end_angle

    return f'<svg viewBox="0 0 {size} {size}">{"".join(paths)}</svg>'


def render_bars(data, color_map, width=620, height=320):
    if not data:
        return f'<svg viewBox="0 0 {width} {height}" aria-label="empty chart"></svg>'

    max_val = max(v for _, v in data) or 1
    margin_left, margin_right, margin_top, margin_bottom = 60, 20, 20, 70
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    gap = 16
    n = len(data)
    bar_w = max(12, (plot_w - gap * (n - 1)) / n)

    bars = []
    labels = []
    baseline_y = margin_top + plot_h
    for i, (label, value) in enumerate(data):
        x = margin_left + i * (bar_w + gap)
        h = (value / max_val) * plot_h
        y = baseline_y - h
        color = color_map.get(label, PALETTE[0])
        bars.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{h:.2f}" rx="4" fill="{color}" opacity="0.9"></rect>')
        labels.append(
            f'<text x="{x + bar_w / 2:.2f}" y="{baseline_y + 22}" fill="#cdd6f4" font-size="12" text-anchor="middle">{html.escape(label)}</text>'
        )
        value_text = format_int(value)
        labels.append(
            f'<text x="{x + bar_w / 2:.2f}" y="{y - 6:.2f}" fill="#9ae6b4" font-size="12" text-anchor="middle">{value_text}</text>'
        )

    axis = f'<line x1="{margin_left}" y1="{baseline_y}" x2="{width - margin_right}" y2="{baseline_y}" stroke="#233554" stroke-width="2" />'
    return f'<svg viewBox="0 0 {width} {height}">{axis}{"".join(bars)}{"".join(labels)}</svg>'


def build_html(stats):
    ext_counts = stats["ext_counts"]
    ext_lines = stats["ext_lines"]

    sorted_counts = sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)
    pie_limit = 7
    pie_data = sorted_counts[:pie_limit]
    if len(sorted_counts) > pie_limit:
        other_sum = sum(v for _, v in sorted_counts[pie_limit:])
        pie_data.append(("Other", other_sum))

    sorted_lines = sorted(ext_lines.items(), key=lambda x: x[1], reverse=True)
    bar_data = sorted_lines[:8]

    labels_for_color = [label for label, _ in pie_data if label != "Other"] + [label for label, _ in bar_data]
    color_map = assign_colors(labels_for_color)
    if any(label == "Other" for label, _ in pie_data):
        color_map["Other"] = "#475569"

    pie_svg = render_pie(pie_data, color_map)
    bar_svg = render_bars(bar_data, color_map)

    largest_rows_html = "".join(
        f"<tr><td>{html.escape(relpath)}</td><td>{human_bytes(size)}</td><td>{format_int(lines)}</td></tr>"
        for size, relpath, lines in stats["largest"]
    )

    legend_items_html = "".join(
        f'<div class="legend-item"><span style="background:{color_map.get(label, PALETTE[0])}"></span>'
        f'<div class="legend-text"><strong>{html.escape(label)}</strong><small>{format_int(value)} files</small></div></div>'
        for label, value in pie_data
    )

    top_ext = sorted_lines[0][0] if sorted_lines else "N/A"

    top_counts_html = "".join(
        f'<div class="legend-item"><span style="background:{color_map.get(label, PALETTE[0])}"></span>'
        f'<div class="legend-text"><strong>{html.escape(label)}</strong><small>{format_int(value)} files</small></div></div>'
        for label, value in sorted_counts[:6]
    )

    top_lines_html = "".join(
        f'<div class="legend-item"><span style="background:{color_map.get(label, PALETTE[1])}"></span>'
        f'<div class="legend-text"><strong>{html.escape(label)}</strong><small>{format_int(value)} lines</small></div></div>'
        for label, value in sorted_lines[:6]
    )

    template = Template("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Codebase Fingerprint</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {
    --bg: #0b1021;
    --card: #0f172a;
    --muted: #94a3b8;
    --border: #1f2937;
    --accent: #7c3aed;
}
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
    background: radial-gradient(circle at 20% 20%, rgba(124,58,237,0.08), transparent 35%), var(--bg);
    color: #e2e8f0;
    padding: 28px;
}
h1 {
    font-size: 34px;
    margin: 0;
    background: linear-gradient(120deg, #22d3ee, #a855f7, #f97316);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 20px;
}
header .subtitle {
    color: var(--muted);
    font-size: 14px;
}
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 16px;
}
.card {
    background: linear-gradient(145deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.25);
    backdrop-filter: blur(6px);
}
.stat-number {
    font-size: 30px;
    font-weight: 700;
}
.stat-label {
    color: var(--muted);
    font-size: 13px;
    letter-spacing: 0.3px;
}
.pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 999px;
    color: #cbd5e1;
    font-size: 13px;
}
.section-title {
    font-size: 17px;
    margin: 0 0 12px;
    letter-spacing: 0.2px;
}
.chart-wrap {
    display: grid;
    grid-template-columns: 1.1fr 1fr;
    gap: 18px;
}
@media (max-width: 900px) {
    .chart-wrap { grid-template-columns: 1fr; }
}
.legend {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 10px;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 10px;
}
.legend-item span {
    width: 14px;
    height: 14px;
    border-radius: 4px;
    display: inline-block;
}
.legend-item strong {
    display: block;
    font-size: 14px;
}
.legend-item small {
    color: var(--muted);
}
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}
th, td {
    padding: 10px;
    border-bottom: 1px solid #1f2937;
}
th {
    text-align: left;
    color: var(--muted);
    font-weight: 600;
    letter-spacing: 0.3px;
}
tr:last-child td {
    border-bottom: none;
}
.tag {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 10px;
    background: rgba(124, 58, 237, 0.15);
    color: #c4b5fd;
    border: 1px solid rgba(124,58,237,0.3);
    font-weight: 600;
    font-size: 12px;
}
.banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    padding: 14px 18px;
    border-radius: 12px;
    background: linear-gradient(120deg, rgba(34,211,238,0.18), rgba(168,85,247,0.12));
    border: 1px solid rgba(124,58,237,0.25);
    margin-bottom: 14px;
}
.muted {
    color: var(--muted);
}
</style>
</head>
<body>
<header>
    <div>
        <h1>Codebase Fingerprint</h1>
        <div class="subtitle">A quick visual of <strong>$root</strong></div>
    </div>
    <div class="pill">Scanned on $scanned_at</div>
</header>

<div class="banner">
    <div>
        <div class="muted">Signature Insight</div>
        <div style="font-size:18px;font-weight:700;">Top language by lines: <span class="tag">$top_ext</span></div>
    </div>
    <div class="muted">Deepest path: $max_depth levels</div>
</div>

<div class="grid">
    <div class="card">
        <div class="stat-number">$total_files</div>
        <div class="stat-label">Files scanned</div>
    </div>
    <div class="card">
        <div class="stat-number">$total_lines</div>
        <div class="stat-label">Total lines of code</div>
    </div>
    <div class="card">
        <div class="stat-number">$unique_ext</div>
        <div class="stat-label">Unique extensions</div>
    </div>
    <div class="card">
        <div class="stat-number">$max_depth</div>
        <div class="stat-label">Directory depth</div>
    </div>
</div>

<div class="grid" style="margin-top:16px;">
    <div class="card">
        <div class="section-title">File type distribution</div>
        <div class="chart-wrap">
            <div class="chart">$pie_svg</div>
            <div class="legend">$legend_items</div>
        </div>
    </div>
    <div class="card">
        <div class="section-title">Lines by extension</div>
        <div class="chart">$bar_svg</div>
    </div>
</div>

<div class="grid" style="margin-top:16px;">
    <div class="card">
        <div class="section-title">Largest files</div>
        <table>
            <thead><tr><th>Path</th><th>Size</th><th>Lines</th></tr></thead>
            <tbody>
                $largest_rows
            </tbody>
        </table>
    </div>
    <div class="card">
        <div class="section-title">Quick glance</div>
        <p class="muted">Top extensions by file count</p>
        <div class="legend">
            $top_counts
        </div>
        <p class="muted" style="margin-top:16px;">Top extensions by lines</p>
        <div class="legend">
            $top_lines
        </div>
    </div>
</div>

</body>
</html>
""")
    html_doc = template.substitute(
        root=html.escape(stats["root"]),
        scanned_at=stats["scanned_at"],
        top_ext=html.escape(top_ext),
        max_depth=format_int(stats["max_depth"]),
        total_files=format_int(stats["total_files"]),
        total_lines=format_int(stats["total_lines"]),
        unique_ext=format_int(len(ext_counts)),
        pie_svg=pie_svg,
        legend_items=legend_items_html,
        bar_svg=bar_svg,
        largest_rows=largest_rows_html,
        top_counts=top_counts_html,
        top_lines=top_lines_html
    )
    return html_doc


def main():
    stats = scan_codebase(".")
    html_output = build_html(stats)
    out_path = os.path.join(os.getcwd(), "stats.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"Generated stats.html in {os.getcwd()}")


if __name__ == "__main__":
    main()