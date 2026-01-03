import os
import random
import json
import datetime
from collections import Counter, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket

LOG_FILE = "server.log"

# ----------------------------------------------------------------------
# Log generation
# ----------------------------------------------------------------------
LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]
ERROR_MESSAGES = [
    "Database connection lost",
    "Timeout while contacting service",
    "Null pointer dereference",
    "User authentication failed",
    "Disk space critically low",
    "Failed to parse configuration",
    "Cache miss storm detected",
    "Third-party API returned 500",
    "Queue backlog exceeded",
    "Unhandled exception occurred",
]
INFO_MESSAGES = [
    "User logged in",
    "Scheduled job completed",
    "Cache warmed successfully",
    "Background sync finished",
    "Metrics flushed",
    "Health check OK",
    "Configuration loaded",
    "Started worker thread",
    "Periodic cleanup executed",
]
WARN_MESSAGES = [
    "High memory usage detected",
    "Slow response time observed",
    "Retrying connection",
    "Deprecated API in use",
    "Minor clock skew detected",
    "Missing optional dependency",
]


def ensure_log_file():
    """Create a sample log file if missing."""
    if os.path.exists(LOG_FILE):
        return
    now = datetime.datetime.now()
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for _ in range(1000):
            delta_minutes = random.randint(0, 48 * 60)
            ts = now - datetime.timedelta(minutes=delta_minutes, seconds=random.randint(0, 59))
            level = random.choices(LEVELS, weights=[55, 20, 18, 7], k=1)[0]
            if level == "INFO":
                msg = random.choice(INFO_MESSAGES)
            elif level == "WARN":
                msg = random.choice(WARN_MESSAGES)
            elif level == "ERROR":
                msg = random.choice(ERROR_MESSAGES[:7])
            else:
                msg = random.choice(ERROR_MESSAGES)
            f.write(f"{ts.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {msg}\n")


# ----------------------------------------------------------------------
# Log parsing and analytics
# ----------------------------------------------------------------------
def parse_log_file(path=LOG_FILE):
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ts_part, rest = line.split(" ", 1)
                if len(ts_part) == 10:  # only date, need another token for time
                    date_part = ts_part
                    time_part, rest = rest.split(" ", 1)
                    ts_str = f"{date_part} {time_part}"
                else:
                    ts_str = ts_part
                if "[" not in rest or "]" not in rest:
                    continue
                level = rest[rest.find("[") + 1 : rest.find("]")]
                message = rest[rest.find("]") + 2 :]
                dt = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                entries.append({"timestamp": dt, "level": level.strip(), "message": message.strip()})
            except Exception:
                continue
    return entries


def build_dataset():
    raw_entries = parse_log_file()
    total = len(raw_entries)
    level_counts = Counter(e["level"] for e in raw_entries)

    error_entries = []
    critical_entries = []
    for e in raw_entries:
        if e["level"] in ("ERROR", "CRITICAL"):
            error_entries.append(
                {
                    "timestamp": e["timestamp"].isoformat(sep=" "),
                    "level": e["level"],
                    "message": e["message"],
                }
            )
        if e["level"] == "CRITICAL":
            critical_entries.append(
                {
                    "timestamp": e["timestamp"].isoformat(sep=" "),
                    "message": e["message"],
                }
            )

    per_hour = defaultdict(int)
    for e in error_entries:
        dt = datetime.datetime.fromisoformat(e["timestamp"])
        hour_key = dt.replace(minute=0, second=0, microsecond=0).isoformat(sep=" ")
        per_hour[hour_key] += 1

    data = {
        "total": total,
        "levels": {k: int(v) for k, v in level_counts.items()},
        "error_entries": error_entries,
        "critical_entries": critical_entries,
        "errors_per_hour": {k: int(v) for k, v in per_hour.items()},
    }
    return data


# ----------------------------------------------------------------------
# HTTP Handler and HTML
# ----------------------------------------------------------------------
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Log Analytics Dashboard</title>
<style>
    :root {
        --bg: #0f172a;
        --panel: #111827;
        --accent: #3b82f6;
        --text: #e5e7eb;
        --muted: #9ca3af;
        --critical: #ef4444;
        --error: #f59e0b;
        --success: #22c55e;
        --warn: #f97316;
    }
    * { box-sizing: border-box; }
    body {
        margin: 0;
        background: radial-gradient(circle at 20% 20%, #111827, #0b1120 50%);
        color: var(--text);
        font-family: 'Segoe UI', Tahoma, sans-serif;
    }
    header {
        padding: 20px 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1f2937;
    }
    header h1 { margin: 0; font-size: 24px; letter-spacing: 0.5px; }
    header .status {
        font-size: 14px;
        color: var(--muted);
    }
    main {
        padding: 20px 30px 40px 30px;
        max-width: 1200px;
        margin: auto;
    }
    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
    }
    .card {
        background: linear-gradient(135deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border: 1px solid #1f2937;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 15px 30px rgba(0,0,0,0.25);
    }
    .card h3 {
        margin: 0 0 10px 0;
        font-size: 16px;
        color: #cbd5e1;
    }
    .pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: #1f2937;
        color: var(--muted);
        font-size: 12px;
    }
    #levelBars .bar {
        display: flex;
        align-items: center;
        margin: 8px 0;
    }
    #levelBars .label {
        width: 70px;
        color: var(--muted);
        font-size: 13px;
    }
    #levelBars .track {
        flex: 1;
        background: #1f2937;
        border-radius: 8px;
        height: 10px;
        overflow: hidden;
        margin-right: 8px;
    }
    #levelBars .fill {
        height: 100%;
        border-radius: 8px;
    }
    #levelBars .value {
        width: 50px;
        text-align: right;
        font-size: 12px;
        color: #cbd5e1;
    }
    .section-title {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .section-title h2 {
        margin: 0;
        font-size: 18px;
        color: #e5e7eb;
    }
    button.filter {
        background: #1f2937;
        border: 1px solid #1f2937;
        color: #cbd5e1;
        padding: 6px 12px;
        border-radius: 8px;
        cursor: pointer;
        margin-right: 6px;
        transition: all .2s ease;
        font-size: 13px;
    }
    button.filter.active {
        background: var(--accent);
        color: white;
        border-color: var(--accent);
        box-shadow: 0 6px 12px rgba(59,130,246,0.25);
    }
    #timeline, #commonErrors {
        width: 100%;
        height: 240px;
        background: #0b1220;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 12px;
    }
    svg {
        width: 100%;
        height: 100%;
    }
    ul#commonList {
        list-style: none;
        padding: 0;
        margin: 0;
        max-height: 200px;
        overflow: auto;
    }
    ul#commonList li {
        padding: 8px 6px;
        border-bottom: 1px solid #1f2937;
        display: flex;
        justify-content: space-between;
        color: #cbd5e1;
        font-size: 14px;
    }
    ul#commonList li:last-child { border-bottom: none; }
    .table-wrap {
        overflow: auto;
        max-height: 320px;
        border-radius: 10px;
        border: 1px solid #1f2937;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }
    thead {
        background: #111827;
        position: sticky;
        top: 0;
    }
    th, td {
        padding: 10px 12px;
        border-bottom: 1px solid #1f2937;
        text-align: left;
        color: #cbd5e1;
    }
    tr:hover { background: rgba(255,255,255,0.02); }
    #searchBox {
        width: 100%;
        padding: 10px 12px;
        margin: 10px 0 12px 0;
        border-radius: 10px;
        border: 1px solid #1f2937;
        background: #0b1220;
        color: #e5e7eb;
        outline: none;
    }
    .badge {
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 11px;
        letter-spacing: 0.2px;
    }
    .badge.error { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
    .badge.critical { background: rgba(239, 68, 68, 0.15); color: #f87171; }
    .muted { color: var(--muted); }
    .small { font-size: 12px; }
</style>
</head>
<body>
<header>
    <div>
        <h1>Log Analytics Dashboard</h1>
        <div class="status">Real-time view of server.log</div>
    </div>
    <div class="pill" id="summaryPill">Loading...</div>
</header>
<main>
    <div class="grid">
        <div class="card">
            <div class="section-title"><h2>Level Distribution</h2></div>
            <div id="levelBars"></div>
        </div>
        <div class="card">
            <div class="section-title">
                <h2>Error Timeline</h2>
                <div>
                    <button class="filter" data-level="ALL">All</button>
                    <button class="filter" data-level="ERROR">Error</button>
                    <button class="filter" data-level="CRITICAL">Alert</button>
                </div>
            </div>
            <div id="timeline">
                <svg id="timelineSvg"></svg>
            </div>
        </div>
        <div class="card">
            <div class="section-title">
                <h2>Common Error Messages</h2>
            </div>
            <div id="commonErrors">
                <ul id="commonList"></ul>
            </div>
        </div>
    </div>

    <div class="card" style="margin-top:18px;">
        <div class="section-title">
            <div>
                <h2>Critical Errors</h2>
                <div class="muted small">Search within critical events</div>
            </div>
        </div>
        <input type="text" id="searchBox" placeholder="Search critical messages or timestamps...">
        <div class="table-wrap">
            <table>
                <thead>
                    <tr><th style="width: 200px;">Timestamp</th><th>Message</th><th style="width: 100px;">Level</th></tr>
                </thead>
                <tbody id="criticalTable"></tbody>
            </table>
        </div>
    </div>
</main>
<script>
let DASH_DATA = null;
let currentFilter = "ALL";

function fetchData() {
    fetch('/data').then(r => r.json()).then(data => {
        DASH_DATA = data;
        renderAll();
    }).catch(err => {
        console.error(err);
        document.getElementById('summaryPill').innerText = 'Failed to load data';
    });
}

function renderAll() {
    if (!DASH_DATA) return;
    renderSummary();
    renderLevelBars();
    renderTimeline();
    renderCommonErrors();
    renderCriticalTable();
}

function renderSummary() {
    const total = DASH_DATA.total;
    const criticalCount = DASH_DATA.levels.CRITICAL || 0;
    const errCount = DASH_DATA.levels.ERROR || 0;
    document.getElementById('summaryPill').innerText = `${total} lines • ${errCount} errors • ${criticalCount} alerts`;
}

function renderLevelBars() {
    const container = document.getElementById('levelBars');
    container.innerHTML = '';
    const colors = {
        INFO: 'var(--success)',
        WARN: 'var(--warn)',
        ERROR: 'var(--error)',
        CRITICAL: 'var(--critical)'
    };
    const total = DASH_DATA.total || 1;
    ['INFO','WARN','ERROR','CRITICAL'].forEach(level => {
        const count = DASH_DATA.levels[level] || 0;
        const pct = Math.round((count / total) * 1000) / 10;
        const row = document.createElement('div');
        row.className = 'bar';
        row.innerHTML = `
            <div class="label">${level}</div>
            <div class="track"><div class="fill" style="width:${pct}%; background:${colors[level]};"></div></div>
            <div class="value">${pct}%</div>
        `;
        container.appendChild(row);
    });
}

function renderTimeline() {
    const svg = document.getElementById('timelineSvg');
    svg.innerHTML = '';
    const filtered = DASH_DATA.error_entries.filter(e => {
        if (currentFilter === 'ALL') return true;
        return e.level === currentFilter;
    });
    if (!filtered.length) {
        svg.innerHTML = `<text x="50%" y="50%" fill="#6b7280" text-anchor="middle">No data for selection</text>`;
        return;
    }
    const byHour = {};
    filtered.forEach(e => {
        const d = new Date(e.timestamp);
        const key = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:00`;
        byHour[key] = (byHour[key] || 0) + 1;
    });
    const points = Object.keys(byHour).sort().map(k => ({ label: k, value: byHour[k] }));
    const maxV = Math.max(...points.map(p => p.value));
    const padding = 30;
    const w = svg.clientWidth || 600;
    const h = svg.clientHeight || 200;
    const coords = points.map((p, idx) => {
        const x = padding + idx * ((w - 2*padding) / Math.max(1, points.length - 1));
        const y = h - padding - (p.value / maxV) * (h - 2*padding);
        return {x,y,label:p.label,value:p.value};
    });
    const polyline = coords.map(c => `${c.x},${c.y}`).join(' ');
    svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    svg.innerHTML = `
        <defs>
            <linearGradient id="grad" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="rgba(59,130,246,0.6)"/>
                <stop offset="100%" stop-color="rgba(59,130,246,0)"/>
            </linearGradient>
        </defs>
        <polyline points="${polyline}" fill="none" stroke="var(--accent)" stroke-width="2.5" />
        <polygon points="${polyline} ${w-padding},${h-padding} ${padding},${h-padding}" fill="url(#grad)" opacity="0.35"></polygon>
    `;
    coords.forEach(c => {
        const circle = document.createElementNS('http://www.w3.org/2000/svg','circle');
        circle.setAttribute('cx', c.x);
        circle.setAttribute('cy', c.y);
        circle.setAttribute('r', 4);
        circle.setAttribute('fill', '#fff');
        circle.setAttribute('stroke', 'var(--accent)');
        circle.setAttribute('stroke-width', '2');
        circle.addEventListener('mouseover', () => {
            circle.setAttribute('r', 6);
            tooltip(`${c.label} — ${c.value} errors`, c.x, c.y);
        });
        circle.addEventListener('mouseout', () => {
            circle.setAttribute('r', 4);
            tooltip();
        });
        svg.appendChild(circle);
    });
}

function tooltip(text, x, y) {
    let tip = document.getElementById('svg-tip');
    if (!text) {
        if (tip) tip.remove();
        return;
    }
    if (!tip) {
        tip = document.createElementNS('http://www.w3.org/2000/svg','text');
        tip.setAttribute('id','svg-tip');
        tip.setAttribute('fill','#cbd5e1');
        tip.setAttribute('font-size','12');
        tip.setAttribute('text-anchor','middle');
        document.getElementById('timelineSvg').appendChild(tip);
    }
    tip.textContent = text;
    tip.setAttribute('x', x);
    tip.setAttribute('y', y - 10);
}

function renderCommonErrors() {
    const list = document.getElementById('commonList');
    list.innerHTML = '';
    const filtered = DASH_DATA.error_entries.filter(e => {
        if (currentFilter === 'ALL') return true;
        return e.level === currentFilter;
    });
    const counts = {};
    filtered.forEach(e => counts[e.message] = (counts[e.message] || 0) + 1);
    const top = Object.entries(counts).sort((a,b) => b[1]-a[1]).slice(0,8);
    if (!top.length) {
        list.innerHTML = '<li><span>No data</span></li>';
        return;
    }
    top.forEach(([msg,count]) => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${msg}</span><span class="muted">${count}</span>`;
        list.appendChild(li);
    });
}

function renderCriticalTable() {
    const tbody = document.getElementById('criticalTable');
    const term = document.getElementById('searchBox').value.toLowerCase();
    tbody.innerHTML = '';
    DASH_DATA.critical_entries.forEach(entry => {
        const hay = (entry.timestamp + ' ' + entry.message).toLowerCase();
        if (term && !hay.includes(term)) return;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${entry.timestamp}</td>
            <td>${entry.message}</td>
            <td><span class="badge critical">CRITICAL</span></td>
        `;
        tbody.appendChild(tr);
    });
    if (!tbody.children.length) {
        tbody.innerHTML = `<tr><td colspan="3" class="muted">No matching results</td></tr>`;
    }
}

document.querySelectorAll('button.filter').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('button.filter').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.level;
        renderTimeline();
        renderCommonErrors();
    });
});
document.querySelector('button.filter[data-level="ALL"]').classList.add('active');
document.getElementById('searchBox').addEventListener('input', renderCriticalTable);

fetchData();
setInterval(fetchData, 10000);
</script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self.respond_html(DASHBOARD_HTML)
        elif path == "/data":
            data = build_dataset()
            payload = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def respond_html(self, content: str):
        payload = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()  # fixed missing call
        self.wfile.write(payload)

    def log_message(self, format, *args):
        return


def find_free_port(start=8000, end=8100):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found in range.")


def main():
    ensure_log_file()
    port = find_free_port()
    server = HTTPServer(("0.0.0.0", port), DashboardHandler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Log Analytics Dashboard is running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()