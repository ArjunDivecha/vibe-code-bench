import os
import re
import json
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

LOG_FILE = "server.log"


def generate_fake_log(path: str, lines: int = 1000) -> None:
    """Generate fake log lines with timestamps and various levels."""
    levels = [
        ("INFO", 0.6),
        ("WARN", 0.15),
        ("ERROR", 0.18),
        ("CRITICAL", 0.07),
    ]
    messages = {
        "INFO": [
            "User session validated",
            "Cache refreshed successfully",
            "Scheduled job executed",
            "Background sync completed",
            "Health check OK",
        ],
        "WARN": [
            "Disk usage above 80%",
            "High memory consumption detected",
            "Response time slower than expected",
            "Retrying request to upstream service",
            "Deprecated API call received",
        ],
        "ERROR": [
            "Failed to connect to database",
            "Timeout while calling payment gateway",
            "Authentication failed for user",
            "Queue processing halted unexpectedly",
            "File upload failed integrity check",
        ],
        "CRITICAL": [
            "Data corruption detected in shard 3",
            "Multiple login failures detected",
            "Primary database unreachable",
            "System out of memory crash",
            "Security breach attempt blocked",
        ],
    }

    def pick_level():
        r = random.random()
        cumulative = 0
        for lvl, prob in levels:
            cumulative += prob
            if r <= cumulative:
                return lvl
        return levels[-1][0]

    random.seed()
    start_time = datetime.now() - timedelta(hours=48)
    with open(path, "w", encoding="utf-8") as f:
        for _ in range(lines):
            lvl = pick_level()
            msg = random.choice(messages[lvl])
            ts = start_time + timedelta(seconds=random.randint(0, 48 * 3600))
            timestamp = ts.strftime("%Y-%m-%d %H:%M:%S")
            line = f"{timestamp} [{lvl}] {msg}"
            f.write(line + "\n")


def parse_log(path: str) -> dict:
    """Parse log file into structured analytics data."""
    pattern = re.compile(r"(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>[A-Z]+)\] (?P<msg>.*)")
    entries = []
    level_counts: Counter = Counter()
    timeline_counts: defaultdict = defaultdict(Counter)  # hour -> Counter(level)
    message_counts: defaultdict = defaultdict(Counter)  # msg -> Counter(level)
    critical_entries = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            m = pattern.match(line)
            if not m:
                continue
            ts = m.group("ts")
            level = m.group("level")
            msg = m.group("msg")
            entries.append({"time": ts, "level": level, "message": msg})
            level_counts[level] += 1
            if level in ("ERROR", "CRITICAL"):
                hour = ts[:13] + ":00"
                timeline_counts[hour][level] += 1
                message_counts[msg][level] += 1
            if level == "CRITICAL":
                critical_entries.append({"time": ts, "message": msg})

    total = len(entries) or 1
    percentages = []
    for lvl in ["INFO", "WARN", "ERROR", "CRITICAL"]:
        count = level_counts.get(lvl, 0)
        percentages.append(
            {"level": lvl, "count": count, "percent": round((count / total) * 100, 2)}
        )

    timeline_list = []
    for hour in sorted(timeline_counts.keys()):
        counts = timeline_counts[hour]
        timeline_list.append(
            {
                "hour": hour,
                "ERROR": counts.get("ERROR", 0),
                "CRITICAL": counts.get("CRITICAL", 0),
            }
        )

    common_errors = []
    for msg, cnts in message_counts.items():
        common_errors.append(
            {
                "message": msg,
                "ERROR": cnts.get("ERROR", 0),
                "CRITICAL": cnts.get("CRITICAL", 0),
                "total": cnts.get("ERROR", 0) + cnts.get("CRITICAL", 0),
            }
        )
    common_errors.sort(key=lambda x: x["total"], reverse=True)

    data = {
        "entries": entries,
        "percentages": percentages,
        "timeline": timeline_list,
        "common_errors": common_errors,
        "critical": critical_entries,
    }
    return data


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Log Analytics Dashboard</title>
<style>
    :root {
        --bg: #0f172a;
        --panel: #111827;
        --accent: #22d3ee;
        --accent2: #a78bfa;
        --text: #e5e7eb;
        --muted: #9ca3af;
        --error: #f87171;
        --warn: #fbbf24;
    }
    * { box-sizing: border-box; }
    body {
        margin: 0; padding: 0;
        font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
        background: radial-gradient(circle at 20% 20%, rgba(56,189,248,0.08), transparent 25%),
                    radial-gradient(circle at 80% 10%, rgba(192,132,252,0.08), transparent 25%),
                    var(--bg);
        color: var(--text);
        min-height: 100vh;
    }
    header {
        padding: 24px 28px 12px 28px;
    }
    h1 {
        margin: 0;
        font-size: 28px;
        letter-spacing: 0.2px;
    }
    p.subtitle { margin: 6px 0 0 0; color: var(--muted); }
    .container { padding: 0 28px 40px 28px; display: grid; grid-template-columns: 1fr; gap: 18px; }
    .card {
        background: linear-gradient(135deg, rgba(34,211,238,0.06), rgba(167,139,250,0.06));
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    }
    .card h2 { margin: 0 0 10px 0; font-size: 18px; }
    .flex { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    .pill {
        border: 1px solid rgba(255,255,255,0.14);
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(255,255,255,0.04);
        color: var(--muted);
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .pill.active { color: #0f172a; background: var(--accent); border-color: transparent; font-weight: 600; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }
    svg { width: 100%; height: 240px; background: rgba(255,255,255,0.02); border-radius: 10px; }
    .legend { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 8px; }
    .legend span { display: inline-flex; align-items: center; gap: 6px; color: var(--muted); font-size: 13px; }
    .legend i { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
    .list { margin: 10px 0 0 0; padding: 0; list-style: none; }
    .list li { padding: 10px 12px; border-radius: 10px; margin-bottom: 8px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 10px; font-size: 14px; }
    th { color: var(--muted); font-weight: 600; border-bottom: 1px solid rgba(255,255,255,0.08); }
    tr:nth-child(even) { background: rgba(255,255,255,0.02); }
    input[type="search"] {
        width: 100%;
        padding: 10px 12px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        color: var(--text);
        outline: none;
    }
    .stat { display: flex; flex-direction: column; gap: 4px; padding: 10px; border-radius: 12px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); }
    .stat strong { font-size: 20px; }
    @media (max-width: 720px) { svg { height: 200px; } }
</style>
</head>
<body>
<header>
    <h1>Log Analytics Dashboard</h1>
    <p class="subtitle">Live view of log levels, error trends, and critical incidents</p>
</header>
<div class="container">
    <div class="card">
        <div class="flex" style="justify-content: space-between;">
            <div class="flex" style="gap: 8px;">
                <span class="pill active" data-filter="all">All</span>
                <span class="pill" data-filter="error">Error</span>
                <span class="pill" data-filter="alert">Alert</span>
            </div>
            <div id="summary" class="flex" style="gap:10px;"></div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>Log Level Distribution</h2>
            <svg id="levelChart"></svg>
            <div class="legend">
                <span><i style="background: var(--accent)"></i>INFO</span>
                <span><i style="background: var(--warn)"></i>WARN</span>
                <span><i style="background: var(--error)"></i>ERROR</span>
                <span><i style="background: var(--accent2)"></i>CRITICAL</span>
            </div>
        </div>
        <div class="card">
            <h2>Errors per Hour</h2>
            <svg id="timelineChart"></svg>
            <div class="legend">
                <span><i style="background: var(--error)"></i>Error</span>
                <span><i style="background: var(--accent2)"></i>Alert</span>
            </div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>Most Common Errors</h2>
            <ul class="list" id="commonList"></ul>
        </div>
        <div class="card">
            <h2>Critical Incidents</h2>
            <input id="search" type="search" placeholder="Search critical messages...">
            <div style="max-height: 260px; overflow: auto; margin-top: 12px;">
                <table id="criticalTable">
                    <thead>
                        <tr><th>Timestamp</th><th>Message</th></tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
const BOOT_DATA = __DATA_PLACEHOLDER__;

const state = {
    filter: 'all',
    data: BOOT_DATA
};

function setFilter(f) {
    state.filter = f;
    document.querySelectorAll('.pill').forEach(p => {
        p.classList.toggle('active', p.dataset.filter === f);
    });
    render();
}

function summarize() {
    const total = state.data.entries.length;
    const errors = state.data.timeline.reduce((s, t) => s + t.ERROR, 0);
    const alerts = state.data.timeline.reduce((s, t) => s + t.CRITICAL, 0);
    const summary = document.getElementById('summary');
    summary.innerHTML = `
        <div class="stat"><span>Total entries</span><strong>${total}</strong></div>
        <div class="stat"><span>Total errors</span><strong style="color:var(--error)">${errors}</strong></div>
        <div class="stat"><span>Total alerts</span><strong style="color:var(--accent2)">${alerts}</strong></div>
    `;
}

function renderLevelChart() {
    const svg = document.getElementById('levelChart');
    svg.innerHTML = '';
    const data = state.data.percentages;
    const colors = {INFO:'var(--accent)', WARN:'var(--warn)', ERROR:'var(--error)', CRITICAL:'var(--accent2)'};
    const width = svg.clientWidth || 500;
    const height = svg.clientHeight || 240;
    const barWidth = width / (data.length * 1.5);
    const max = 100;
    data.forEach((d, i) => {
        const x = (i + 0.5) * barWidth * 1.5;
        const h = (d.percent / max) * (height - 40);
        const y = height - h - 20;
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', barWidth);
        rect.setAttribute('height', h);
        rect.setAttribute('rx', 6);
        rect.setAttribute('fill', colors[d.level]);
        svg.appendChild(rect);

        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', x + barWidth / 2);
        label.setAttribute('y', height - 6);
        label.setAttribute('fill', '#d1d5db');
        label.setAttribute('font-size', '12');
        label.setAttribute('text-anchor', 'middle');
        label.textContent = d.level;
        svg.appendChild(label);

        const value = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        value.setAttribute('x', x + barWidth / 2);
        value.setAttribute('y', y - 6);
        value.setAttribute('fill', '#e5e7eb');
        value.setAttribute('font-size', '12');
        value.setAttribute('text-anchor', 'middle');
        value.textContent = d.percent + '%';
        svg.appendChild(value);
    });
}

function renderTimeline() {
    const svg = document.getElementById('timelineChart');
    svg.innerHTML = '';
    const raw = state.data.timeline;
    if (!raw.length) return;
    const width = svg.clientWidth || 500;
    const height = svg.clientHeight || 240;
    const paddedWidth = width - 40;
    const paddedHeight = height - 40;
    const counts = raw.map(r => {
        if (state.filter === 'all') return r.ERROR + r.CRITICAL;
        if (state.filter === 'error') return r.ERROR;
        return r.CRITICAL;
    });
    const max = Math.max(...counts, 1);
    const points = counts.map((c, i) => {
        const x = 20 + (paddedWidth * i / Math.max(1, counts.length - 1));
        const y = height - 20 - (c / max) * paddedHeight;
        return [x, y];
    });
    const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    poly.setAttribute('fill', 'none');
    poly.setAttribute('stroke', state.filter === 'alert' ? 'var(--accent2)' : 'var(--error)');
    poly.setAttribute('stroke-width', 2.5);
    poly.setAttribute('points', points.map(p => p.join(',')).join(' '));
    svg.appendChild(poly);

    points.forEach((p, i) => {
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', p[0]);
        circle.setAttribute('cy', p[1]);
        circle.setAttribute('r', 3.5);
        circle.setAttribute('fill', state.filter === 'alert' ? 'var(--accent2)' : 'var(--error)');
        svg.appendChild(circle);
        if (counts.length <= 24 || i % Math.ceil(counts.length / 12) === 0) {
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', p[0]);
            label.setAttribute('y', height - 4);
            label.setAttribute('fill', '#9ca3af');
            label.setAttribute('font-size', '10');
            label.setAttribute('text-anchor', 'middle');
            label.textContent = raw[i].hour.slice(11,16);
            svg.appendChild(label);
        }
    });
}

function renderCommonErrors() {
    const ul = document.getElementById('commonList');
    ul.innerHTML = '';
    const list = state.data.common_errors.map(item => {
        let val = item.total;
        if (state.filter === 'error') val = item.ERROR;
        if (state.filter === 'alert') val = item.CRITICAL;
        return {...item, value: val};
    }).filter(i => i.value > 0);
    list.sort((a,b) => b.value - a.value);
    const top = list.slice(0, 8);
    top.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `<strong style="color:var(--text)">${item.message}</strong>
                        <div style="color:var(--muted); font-size:13px; margin-top:4px;">Count: ${item.value}</div>`;
        ul.appendChild(li);
    });
    if (top.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No errors for selected filter.';
        ul.appendChild(li);
    }
}

function renderCriticalTable() {
    const tbody = document.querySelector('#criticalTable tbody');
    const q = document.getElementById('search').value.toLowerCase();
    tbody.innerHTML = '';
    state.data.critical.filter(item => item.message.toLowerCase().includes(q)).forEach(item => {
        const tr = document.createElement('tr');
        const td1 = document.createElement('td');
        td1.textContent = item.time;
        const td2 = document.createElement('td');
        td2.textContent = item.message;
        tr.appendChild(td1); tr.appendChild(td2);
        tbody.appendChild(tr);
    });
}

function render() {
    summarize();
    renderLevelChart();
    renderTimeline();
    renderCommonErrors();
    renderCriticalTable();
}

document.querySelectorAll('.pill').forEach(p => {
    p.addEventListener('click', () => setFilter(p.dataset.filter));
});
document.getElementById('search').addEventListener('input', renderCriticalTable);

// Initial paint
render();
</script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.data_json = kwargs.pop("data_json")
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            content = HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", self.data_json)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        elif self.path == "/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(self.data_json.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # reduce noise
        pass


def run_server(data):
    data_json = json.dumps(data)
    def handler(*args, **kwargs):
        DashboardHandler(*args, data_json=data_json, **kwargs)

    server = ThreadingHTTPServer(("localhost", 8000), handler)
    print("\nDashboard available at http://localhost:8000")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


def main():
    if not os.path.exists(LOG_FILE):
        print(f"{LOG_FILE} not found, generating fake log data...")
        generate_fake_log(LOG_FILE, 1000)
        print(f"Generated {LOG_FILE}")
    data = parse_log(LOG_FILE)
    run_server(data)


if __name__ == "__main__":
    main()