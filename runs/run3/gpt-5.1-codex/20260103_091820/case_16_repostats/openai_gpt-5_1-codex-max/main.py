import os
import json
from collections import defaultdict

PAGE_TITLE = "Codebase Fingerprint"


def count_lines(path: str) -> int:
    """Return line count of a file, safely."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except (OSError, UnicodeDecodeError):
        return 0


def human_size(num: int) -> str:
    """Human-readable size string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024 or unit == "TB":
            return f"{num:.1f}{unit}"
        num /= 1024
    return f"{num:.1f}TB"


def scan_codebase(base: str = ".") -> dict:
    ext_counts = defaultdict(int)
    ext_lines = defaultdict(int)
    file_records = []
    total_lines = 0
    total_files = 0
    max_depth = 0

    for root, dirs, files in os.walk(base):
        rel_root = os.path.relpath(root, base)
        depth = 0 if rel_root == "." else rel_root.count(os.sep) + 1
        max_depth = max(max_depth, depth)

        for fname in files:
            path = os.path.join(root, fname)
            rel_path = os.path.relpath(path, base)
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0

            ext = os.path.splitext(fname)[1].lower()
            ext = ext if ext else "(no ext)"

            lines = count_lines(path)
            total_files += 1
            total_lines += lines
            ext_counts[ext] += 1
            ext_lines[ext] += lines
            file_records.append({"path": rel_path, "size": size, "lines": lines})

    largest_files = sorted(file_records, key=lambda x: x["size"], reverse=True)[:7]

    return {
        "totalFiles": total_files,
        "totalLines": total_lines,
        "uniqueExt": len(ext_counts),
        "maxDepth": max_depth,
        "extCounts": sorted(ext_counts.items(), key=lambda x: x[1], reverse=True),
        "extLines": sorted(ext_lines.items(), key=lambda x: x[1], reverse=True),
        "largest": largest_files,
    }


def build_table_rows(largest):
    if not largest:
        return "<tr><td colspan='3'>No files found</td></tr>"
    rows = []
    for item in largest:
        rows.append(
            f"<tr><td>{item['path']}</td>"
            f"<td>{human_size(item['size'])}</td>"
            f"<td>{item['lines']:,}</td></tr>"
        )
    return "\n".join(rows)


def generate_html(stats: dict) -> str:
    data_json = json.dumps(stats, indent=2)
    table_rows = build_table_rows(stats["largest"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{PAGE_TITLE}</title>
<style>
:root {{
    --bg: #0b1220;
    --card: #11182b;
    --accent: #7c3aed;
    --accent-2: #22d3ee;
    --text: #e2e8f0;
    --muted: #94a3b8;
    --border: #1f2937;
}}
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    font-family: 'Segoe UI', 'Inter', system-ui, -apple-system, sans-serif;
    background: radial-gradient(circle at 10% 20%, rgba(124,58,237,0.08), transparent 25%),
                radial-gradient(circle at 90% 10%, rgba(34,211,238,0.08), transparent 20%),
                radial-gradient(circle at 50% 80%, rgba(99,102,241,0.08), transparent 20%),
                var(--bg);
    color: var(--text);
}}
.page {{
    max-width: 1100px;
    margin: 40px auto 64px;
    padding: 0 24px 40px;
}}
header {{
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 24px;
}}
.title {{
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.5px;
    display: inline-flex;
    align-items: center;
    gap: 10px;
}}
.pill {{
    padding: 6px 10px;
    background: rgba(124,58,237,0.12);
    color: #c4b5fd;
    font-size: 12px;
    border: 1px solid rgba(124,58,237,0.35);
    border-radius: 999px;
}}
.subtitle {{
    color: var(--muted);
    font-size: 15px;
}}
.cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 14px;
    margin: 14px 0 22px;
}}
.card {{
    background: linear-gradient(145deg, rgba(255,255,255,0.02), rgba(255,255,255,0));
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(4px);
    box-shadow: 0 10px 35px rgba(0,0,0,0.45);
}}
.card::after {{
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 20% 20%, rgba(255,255,255,0.04), transparent 40%);
    opacity: 0.7;
}}
.card label {{
    display: block;
    color: var(--muted);
    font-size: 12px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
}}
.card .value {{
    font-size: 26px;
    font-weight: 700;
}}
.card .hint {{
    color: var(--muted);
    font-size: 12px;
}}
.chart-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 16px;
    margin-bottom: 22px;
}}
.panel {{
    background: linear-gradient(150deg, rgba(124,58,237,0.07), rgba(34,211,238,0.04));
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px;
    box-shadow: 0 10px 35px rgba(0,0,0,0.45);
}}
.panel h3 {{
    margin: 0 0 6px;
    font-size: 17px;
}}
.panel p {{
    margin: 0 0 12px;
    color: var(--muted);
    font-size: 13px;
}}
svg {{
    width: 100%;
    height: auto;
}}
.legend {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 8px;
    margin-top: 10px;
}}
.legend-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--muted);
    font-size: 13px;
}}
.legend-swatch {{
    width: 12px;
    height: 12px;
    border-radius: 3px;
}}
.table-wrapper {{
    background: linear-gradient(120deg, rgba(34,211,238,0.05), rgba(124,58,237,0.03));
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px;
    overflow: hidden;
    box-shadow: 0 10px 35px rgba(0,0,0,0.45);
}}
table {{
    width: 100%;
    border-collapse: collapse;
    color: var(--text);
}}
th, td {{
    text-align: left;
    padding: 10px 8px;
    font-size: 13px;
}}
th {{
    color: var(--muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    border-bottom: 1px solid var(--border);
}}
tbody tr:nth-child(odd) td {{
    background: rgba(255,255,255,0.02);
}}
tbody tr:hover td {{
    background: rgba(124,58,237,0.07);
}}
.footer {{
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    margin-top: 24px;
}}
.badge {{
    color: #22d3ee;
}}
</style>
</head>
<body>
<div class="page">
    <header>
        <div class="title">
            {PAGE_TITLE}
            <span class="pill">Auto Generated</span>
        </div>
        <div class="subtitle">A quick visual fingerprint of the files living in this directory.</div>
    </header>

    <section class="cards">
        <div class="card">
            <label>Total Files</label>
            <div class="value">{stats['totalFiles']:,}</div>
            <div class="hint">Every file counted recursively.</div>
        </div>
        <div class="card">
            <label>Total Lines</label>
            <div class="value">{stats['totalLines']:,}</div>
            <div class="hint">Approximate, text-readable files.</div>
        </div>
        <div class="card">
            <label>Unique Extensions</label>
            <div class="value">{stats['uniqueExt']:,}</div>
            <div class="hint">Language + asset variety.</div>
        </div>
        <div class="card">
            <label>Directory Depth</label>
            <div class="value">{stats['maxDepth']:,}</div>
            <div class="hint">Deepest folder nesting.</div>
        </div>
    </section>

    <section class="chart-grid">
        <div class="panel">
            <h3>File Types Mix</h3>
            <p>Pie chart shows distribution of files by extension.</p>
            <svg id="pieChart" viewBox="0 0 320 320"></svg>
            <div class="legend" id="pieLegend"></div>
        </div>
        <div class="panel">
            <h3>Lines by Extension</h3>
            <p>Bar chart shows top extensions by total lines.</p>
            <svg id="barChart" viewBox="0 0 420 260"></svg>
        </div>
    </section>

    <section class="table-wrapper">
        <h3 style="margin:0 0 8px;">Largest Files</h3>
        <p style="margin:0 0 12px;color:var(--muted);">Top files by size.</p>
        <table>
            <thead>
                <tr><th>Path</th><th>Size</th><th>Lines</th></tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </section>

    <div class="footer">Generated by <span class="badge">Git Stats Infographic Generator</span>. Dark mode &amp; data-driven.</div>
</div>

<script id="stats-data" type="application/json">
{data_json}
</script>
<script>
(function() {{
    const data = JSON.parse(document.getElementById('stats-data').textContent);

    const colorPool = [
        "#7c3aed","#22d3ee","#f59e0b","#10b981","#a855f7",
        "#ef4444","#38bdf8","#f97316","#8b5cf6","#14b8a6"
    ];

    function drawPie() {{
        const svg = document.getElementById('pieChart');
        const legend = document.getElementById('pieLegend');
        svg.innerHTML = "";
        legend.innerHTML = "";

        let items = data.extCounts.slice();
        if (items.length === 0) {{
            svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#94a3b8" font-size="14">No data</text>';
            return;
        }}
        const others = items.slice(7);
        const otherTotal = others.reduce((a,b)=>a+b[1],0);
        items = items.slice(0,7);
        if (otherTotal > 0) items.push(["Other", otherTotal]);

        const total = items.reduce((sum, item)=>sum + item[1], 0);
        const cx = 160, cy = 160, r = 110;
        let angle = -Math.PI / 2;

        items.forEach((item, idx) => {{
            const value = item[1];
            const slice = (value / total) * Math.PI * 2;
            const startX = cx + r * Math.cos(angle);
            const startY = cy + r * Math.sin(angle);
            const endAngle = angle + slice;
            const endX = cx + r * Math.cos(endAngle);
            const endY = cy + r * Math.sin(endAngle);
            const largeArc = slice > Math.PI ? 1 : 0;
            const color = colorPool[idx % colorPool.length];
            const pathData = [
                `M ${cx} ${cy}`,
                `L ${startX} ${startY}`,
                `A ${r} ${r} 0 ${largeArc} 1 ${endX} ${endY}`,
                "Z"
            ].join(" ");
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("d", pathData);
            path.setAttribute("fill", color);
            path.setAttribute("stroke", "rgba(255,255,255,0.06)");
            path.setAttribute("stroke-width", "1");
            svg.appendChild(path);

            // label
            const midAngle = angle + slice / 2;
            const labelR = r * 0.65;
            const lx = cx + labelR * Math.cos(midAngle);
            const ly = cy + labelR * Math.sin(midAngle);
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", lx);
            text.setAttribute("y", ly);
            text.setAttribute("fill", "#0b1220");
            text.setAttribute("font-size", "11");
            text.setAttribute("font-weight", "700");
            text.setAttribute("text-anchor", "middle");
            text.setAttribute("dominant-baseline", "middle");
            text.textContent = Math.round((value/total)*100) + "%";
            svg.appendChild(text);

            const legendItem = document.createElement("div");
            legendItem.className = "legend-item";
            legendItem.innerHTML = `<span class="legend-swatch" style="background:${color}"></span>
                <span>${item[0]} <strong style="color:#e2e8f0;">${value}</strong> files</span>`;
            legend.appendChild(legendItem);

            angle = endAngle;
        }});
    }}

    function drawBars() {{
        const svg = document.getElementById('barChart');
        svg.innerHTML = "";
        let items = data.extLines.slice(0, 8);
        if (items.length === 0) {{
            svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#94a3b8" font-size="14">No data</text>';
            return;
        }}
        const padding = 40;
        const width = 420;
        const height = 240;
        const chartHeight = height - padding * 1.4;
        const barWidth = (width - padding*2) / items.length * 0.6;
        const maxValue = Math.max(...items.map(i=>i[1])) || 1;

        items.forEach((item, idx) => {{
            const value = item[1];
            const barHeight = (value / maxValue) * chartHeight;
            const x = padding + idx * ((width - padding*2) / items.length) + 10;
            const y = height - padding - barHeight;
            const color = colorPool[idx % colorPool.length];
            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("x", x);
            rect.setAttribute("y", y);
            rect.setAttribute("width", barWidth);
            rect.setAttribute("height", barHeight);
            rect.setAttribute("rx", "4");
            rect.setAttribute("fill", color);
            svg.appendChild(rect);

            const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
            label.setAttribute("x", x + barWidth/2);
            label.setAttribute("y", height - padding + 16);
            label.setAttribute("fill", "#cbd5e1");
            label.setAttribute("font-size", "11");
            label.setAttribute("text-anchor", "middle");
            label.textContent = item[0];
            svg.appendChild(label);

            const valLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
            valLabel.setAttribute("x", x + barWidth/2);
            valLabel.setAttribute("y", y - 6);
            valLabel.setAttribute("fill", "#e2e8f0");
            valLabel.setAttribute("font-size", "11");
            valLabel.setAttribute("text-anchor", "middle");
            valLabel.textContent = value.toLocaleString();
            svg.appendChild(valLabel);
        }});

        const axis = document.createElementNS("http://www.w3.org/2000/svg", "line");
        axis.setAttribute("x1", padding - 6);
        axis.setAttribute("x2", width - padding + 6);
        axis.setAttribute("y1", height - padding);
        axis.setAttribute("y2", height - padding);
        axis.setAttribute("stroke", "rgba(255,255,255,0.12)");
        axis.setAttribute("stroke-width", "2");
        svg.appendChild(axis);
    }}

    drawPie();
    drawBars();
}})();
</script>
</body>
</html>
"""


def main():
    stats = scan_codebase(os.getcwd())
    html = generate_html(stats)
    out_path = os.path.join(os.getcwd(), "stats.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated stats.html with {stats['totalFiles']} files analyzed.")


if __name__ == "__main__":
    main()