import os
import json
import datetime
from typing import Dict, List, Tuple

SKIP_DIRS = {'.git', '.hg', '.svn', '__pycache__', 'node_modules', '.idea', '.venv', 'venv', 'env'}


def human_size(num: float) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024 or unit == 'TB':
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} TB"


def count_lines(path: str) -> int:
    lines = 0
    last_char = None
    non_empty = False
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                if not chunk:
                    break
                non_empty = True
                lines += chunk.count(b'\n')
                last_char = chunk[-1]
        if non_empty and last_char != ord('\n'):
            lines += 1
    except (OSError, PermissionError):
        return 0
    return lines


def scan_directory(base: str = '.') -> Dict[str, any]:
    file_counts: Dict[str, int] = {}
    line_counts: Dict[str, int] = {}
    largest_files: List[Tuple[int, str, int]] = []  # size, path, lines
    total_lines = 0
    total_size = 0
    total_files = 0
    max_depth = 0

    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel_root = os.path.relpath(root, base)
        depth = 0 if rel_root == '.' else len(rel_root.split(os.sep))
        max_depth = max(max_depth, depth)

        for fname in files:
            if fname == 'stats.html':
                continue
            path = os.path.join(root, fname)
            rel_path = os.path.relpath(path, base)
            ext = os.path.splitext(fname)[1].lower()
            if not ext:
                ext = "<no_ext>"

            try:
                size = os.path.getsize(path)
            except (OSError, PermissionError):
                continue

            lines = count_lines(path)

            file_counts[ext] = file_counts.get(ext, 0) + 1
            line_counts[ext] = line_counts.get(ext, 0) + lines

            total_lines += lines
            total_size += size
            total_files += 1

            largest_files.append((size, rel_path, lines))

    largest_files.sort(key=lambda x: x[0], reverse=True)
    largest_files = largest_files[:7]

    ext_count_list = sorted(
        [{'ext': k, 'count': v} for k, v in file_counts.items()],
        key=lambda x: x['count'], reverse=True
    )
    ext_line_list = sorted(
        [{'ext': k, 'lines': v} for k, v in line_counts.items()],
        key=lambda x: x['lines'], reverse=True
    )

    largest_prepared = [{
        'path': p,
        'size': s,
        'lines': l
    } for s, p, l in largest_files]

    return {
        'file_counts': ext_count_list,
        'line_counts': ext_line_list,
        'largest_files': largest_prepared,
        'totals': {
            'files': total_files,
            'lines': total_lines,
            'size': total_size,
            'extensions': len(file_counts),
            'depth': max_depth,
        }
    }


def generate_html(stats: Dict[str, any], output_path: str = 'stats.html') -> None:
    data_json = json.dumps(stats, separators=(',', ':'))
    generated_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Codebase Fingerprint</title>
<style>
:root {{
    --bg: #0b1021;
    --panel: #121836;
    --muted: #7c8db5;
    --text: #dbe6ff;
    --accent: #7af0e3;
    --accent-2: #ff7ad1;
    --card-border: rgba(255,255,255,0.05);
    --shadow: 0 20px 60px rgba(0,0,0,0.45);
}}
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    padding: 0;
    background: radial-gradient(circle at 20% 20%, rgba(122,240,227,0.12), transparent 25%),
                radial-gradient(circle at 80% 10%, rgba(255,122,209,0.12), transparent 20%),
                radial-gradient(circle at 50% 80%, rgba(124,99,255,0.1), transparent 25%),
                var(--bg);
    color: var(--text);
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    min-height: 100vh;
}}
.page {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 28px 22px 60px;
}}
header {{
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--card-border);
}}
.title {{
    font-size: 32px;
    letter-spacing: 0.02em;
    font-weight: 700;
}}
.subtitle {{
    color: var(--muted);
    font-size: 14px;
}}
.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 18px;
    margin-top: 18px;
}}
.card {{
    background: linear-gradient(140deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 16px 18px 18px;
    box-shadow: var(--shadow);
    position: relative;
    overflow: hidden;
}}
.card::after {{
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background: radial-gradient(circle at 20% 20%, rgba(122,240,227,0.08), transparent 40%);
}}
.card h3 {{
    margin: 0 0 10px;
    font-size: 16px;
    letter-spacing: 0.01em;
}}
.metrics {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
}}
.metric {{
    padding: 12px;
    border-radius: 12px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
}}
.metric .label {{
    color: var(--muted);
    font-size: 12px;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}}
.metric .value {{
    font-size: 22px;
    font-weight: 700;
}}
.charts {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 14px;
}}
.chart-wrap {{
    display: flex;
    gap: 14px;
    align-items: center;
}}
.chart-legend {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 6px;
    margin-top: 10px;
}}
.legend-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--muted);
    font-size: 13px;
}}
.swatch {{
    width: 12px;
    height: 12px;
    border-radius: 4px;
    flex-shrink: 0;
}}
.list {{
    list-style: none;
    padding: 0;
    margin: 4px 0 0;
}}
.list li {{
    display: flex;
    justify-content: space-between;
    padding: 8px 6px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    color: var(--muted);
    font-size: 13px;
}}
.list li:last-child {{
    border-bottom: none;
}}
.badge {{
    background: rgba(255,255,255,0.08);
    color: var(--text);
    padding: 4px 8px;
    border-radius: 10px;
    font-size: 12px;
}}
.generated {{
    color: var(--muted);
    font-size: 12px;
    text-align: right;
    margin-top: 14px;
}}
.bar-label {{
    fill: var(--muted);
    font-size: 12px;
}}
.bar-value {{
    fill: var(--text);
    font-size: 11px;
}}
</style>
</head>
<body>
<div class="page">
<header>
  <div>
    <div class="title">Codebase Fingerprint</div>
    <div class="subtitle">Auto-generated insight into your repository</div>
  </div>
  <div class="badge">Generated {generated_at}</div>
</header>

<div class="grid">
  <div class="card">
    <h3>Key Metrics</h3>
    <div class="metrics">
      <div class="metric">
        <div class="label">Files</div>
        <div class="value" id="totalFiles">-</div>
      </div>
      <div class="metric">
        <div class="label">Lines of Code</div>
        <div class="value" id="totalLines">-</div>
      </div>
      <div class="metric">
        <div class="label">Extensions</div>
        <div class="value" id="extCount">-</div>
      </div>
      <div class="metric">
        <div class="label">Total Size</div>
        <div class="value" id="totalSize">-</div>
      </div>
      <div class="metric">
        <div class="label">Directory Depth</div>
        <div class="value" id="depth">-</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h3>File Types</h3>
    <div class="chart-wrap">
      <svg id="pieChart" width="220" height="220" viewBox="0 0 240 240"></svg>
      <div style="flex:1;">
        <div class="chart-legend" id="pieLegend"></div>
      </div>
    </div>
  </div>

  <div class="card">
    <h3>Lines by Extension</h3>
    <svg id="barChart" width="100%" height="260"></svg>
  </div>

  <div class="card">
    <h3>Largest Files</h3>
    <ul class="list" id="largestList"></ul>
  </div>

  <div class="card">
    <h3>Top Extensions</h3>
    <ul class="list" id="topExtensions"></ul>
  </div>
</div>
<div class="generated">Made with &lt;3 by Git Stats Infographic Generator</div>
</div>

<script>
const stats = {data_json};
const palette = [
  '#7af0e3', '#ff7ad1', '#7c63ff', '#f5c15c', '#57c7ff',
  '#ff8f6f', '#9bff7a', '#7ab8ff', '#f57cf5', '#c0ff7a',
  '#ffda7a', '#7affc8'
];

function colorForIndex(i) {{
  return palette[i % palette.length];
}}

function formatNumber(num) {{
  return num.toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
}}

function formatBytes(bytes) {{
  const units = ['B','KB','MB','GB','TB'];
  let b = bytes;
  for (let u of units) {{
    if (b < 1024 || u === 'TB') return `${{b.toFixed(1)}} ${{u}}`;
    b = b / 1024;
  }}
}}

function renderMetrics() {{
  document.getElementById('totalFiles').textContent = formatNumber(stats.totals.files);
  document.getElementById('totalLines').textContent = formatNumber(stats.totals.lines);
  document.getElementById('extCount').textContent = stats.totals.extensions;
  document.getElementById('totalSize').textContent = formatBytes(stats.totals.size);
  document.getElementById('depth').textContent = stats.totals.depth;
}}

function polarToCartesian(cx, cy, r, angle) {{
  const rad = (angle - 90) * Math.PI / 180;
  return {{
    x: cx + r * Math.cos(rad),
    y: cy + r * Math.sin(rad)
  }};
}}

function arcPath(cx, cy, r, startAngle, endAngle) {{
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle <= 180 ? '0' : '1';
  return [
    'M', start.x, start.y,
    'A', r, r, 0, largeArc, 0, end.x, end.y
  ].join(' ');
}}

function renderPie() {{
  const svg = document.getElementById('pieChart');
  svg.innerHTML = '';
  const total = stats.file_counts.reduce((sum, d) => sum + d.count, 0) || 1;
  const cx = 120, cy = 120, r = 90;
  let angle = 0;
  stats.file_counts.forEach((d, i) => {{
    const slice = (d.count / total) * 360;
    const path = document.createElementNS('http://www.w3.org/2000/svg','path');
    const endAngle = angle + slice;
    path.setAttribute('d', arcPath(cx, cy, r, angle, endAngle));
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', colorForIndex(i));
    path.setAttribute('stroke-width', '30');
    path.setAttribute('stroke-linecap', 'butt');
    svg.appendChild(path);
    angle = endAngle;
  }});
  const center = document.createElementNS('http://www.w3.org/2000/svg','circle');
  center.setAttribute('cx', cx);
  center.setAttribute('cy', cy);
  center.setAttribute('r', r-35);
  center.setAttribute('fill', 'rgba(0,0,0,0.45)');
  center.setAttribute('stroke', 'rgba(255,255,255,0.05)');
  center.setAttribute('stroke-width', '1');
  svg.appendChild(center);

  const legend = document.getElementById('pieLegend');
  legend.innerHTML = '';
  stats.file_counts.slice(0, 12).forEach((d, i) => {{
    const div = document.createElement('div');
    div.className = 'legend-item';
    div.innerHTML = `<span class="swatch" style="background:${{colorForIndex(i)}}"></span>
                     <span>${{d.ext}}</span>
                     <span style="margin-left:auto; color:var(--text);">${{formatNumber(d.count)}}</span>`;
    legend.appendChild(div);
  }});
}}

function renderBars() {{
  const svg = document.getElementById('barChart');
  svg.innerHTML = '';
  const data = stats.line_counts.slice(0, 8);
  const margin = {{top: 14, right: 18, bottom: 18, left: 28}};
  const width = svg.clientWidth || 360;
  const height = svg.getAttribute('height') - margin.top - margin.bottom;
  const maxVal = data.reduce((m, d) => Math.max(m, d.lines), 1);
  data.forEach((d, i) => {{
    const barHeight = height / data.length - 10;
    const x = margin.left;
    const y = margin.top + i * (barHeight + 10);
    const barWidth = ((width - margin.left - margin.right) * d.lines) / maxVal;

    const rect = document.createElementNS('http://www.w3.org/2000/svg','rect');
    rect.setAttribute('x', x);
    rect.setAttribute('y', y);
    rect.setAttribute('width', barWidth);
    rect.setAttribute('height', barHeight);
    rect.setAttribute('rx', 6);
    rect.setAttribute('fill', colorForIndex(i));
    rect.setAttribute('opacity', '0.85');
    svg.appendChild(rect);

    const label = document.createElementNS('http://www.w3.org/2000/svg','text');
    label.setAttribute('x', x - 8);
    label.setAttribute('y', y + barHeight / 2 + 4);
    label.setAttribute('text-anchor', 'end');
    label.setAttribute('class', 'bar-label');
    label.textContent = d.ext;
    svg.appendChild(label);

    const value = document.createElementNS('http://www.w3.org/2000/svg','text');
    value.setAttribute('x', x + barWidth + 6);
    value.setAttribute('y', y + barHeight / 2 + 4);
    value.setAttribute('class', 'bar-value');
    value.textContent = formatNumber(d.lines);
    svg.appendChild(value);
  }});
}}

function renderLargest() {{
  const list = document.getElementById('largestList');
  list.innerHTML = '';
  if (!stats.largest_files.length) {{
    list.innerHTML = '<li><span>No files found</span></li>';
    return;
  }}
  stats.largest_files.forEach(item => {{
    const li = document.createElement('li');
    li.innerHTML = `<span style="max-width:60%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${{item.path}}</span>
                    <span style="color:var(--text);">${{formatBytes(item.size)}} · ${{formatNumber(item.lines)}} lines</span>`;
    list.appendChild(li);
  }});
}}

function renderTopExtensions() {{
  const list = document.getElementById('topExtensions');
  list.innerHTML = '';
  const combined = stats.file_counts.map(fc => {{
    const lines = (stats.line_counts.find(lc => lc.ext === fc.ext) || {{lines:0}}).lines;
    return {{ext: fc.ext, count: fc.count, lines}};
  }});
  combined.sort((a,b) => b.count - a.count);
  combined.slice(0,8).forEach((d,i) => {{
    const li = document.createElement('li');
    li.innerHTML = `<span>${{d.ext}}</span>
                    <span style="color:var(--text);">${{formatNumber(d.count)}} files · ${{formatNumber(d.lines)}} lines</span>`;
    list.appendChild(li);
  }});
}}

function init() {{
  renderMetrics();
  renderPie();
  renderBars();
  renderLargest();
  renderTopExtensions();
}}

window.addEventListener('resize', renderBars);
init();
</script>
</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Infographic generated at {output_path}")


def main():
    stats = scan_directory('.')
    generate_html(stats)


if __name__ == '__main__':
    main()