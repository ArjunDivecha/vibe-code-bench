import http.server
import json
import os
import random
import re
import socket
import socketserver
import threading
from collections import Counter, defaultdict
from datetime import datetime, timedelta

LOG_FILE = "server.log"

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Log Analytics Dashboard</title>
<style>
    :root { color-scheme: light dark; }
    body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #111827; color: #e5e7eb; }
    header { background: linear-gradient(120deg, #2563eb, #1e3a8a); padding: 18px 24px; color: #fff; }
    h1 { margin: 0; font-size: 24px; }
    main { padding: 20px; max-width: 1100px; margin: auto; }
    section { background: #1f2937; border: 1px solid #374151; border-radius: 12px; padding: 16px; margin-bottom: 18px; box-shadow: 0 6px 16px rgba(0,0,0,.25); }
    .flex { display: flex; gap: 16px; flex-wrap: wrap; }
    .card { flex: 1 1 280px; }
    svg { width: 100%; height: 240px; background: #111827; border-radius: 8px; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th, td { padding: 8px 10px; border-bottom: 1px solid #374151; text-align: left; }
    th { color: #9ca3af; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }
    input, select { background: #0f172a; border: 1px solid #374151; color: #e5e7eb; padding: 8px 10px; border-radius: 8px; }
    .badge { display: inline-block; padding: 4px 8px; border-radius: 6px; font-size: 12px; }
    .info { background:#1e40af; }
    .warn { background:#92400e; }
    .error { background:#991b1b; }
    .critical { background:#7c2d12; }
    .chip { padding: 4px 10px; background:#0f172a; border:1px solid #374151; border-radius: 999px; }
    .grid { display:grid; grid-template-columns: repeat(auto-fit,minmax(240px,1fr)); gap:12px; }
    .small { font-size: 12px; color:#9ca3af; }
    a { color:#93c5fd; }
</style>
</head>
<body>
<header>
  <h1>Log Analytics Dashboard</h1>
  <div class="small">Local real-time insights from server.log</div>
</header>
<main>
  <section class="flex">
    <div class="card">
      <h3>Log Level Distribution</h3>
      <svg id="levelChart"></svg>
    </div>
    <div class="card">
      <h3>Error Timeline <span class="small">(per hour)</span></h3>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
        <label for="filterSelect">Filter:</label>
        <select id="filterSelect">
          <option value="all">All</option>
          <option value="error">Error</option>
          <option value="alert">Alert</option>
        </select>
      </div>
      <svg id="timelineChart"></svg>
    </div>
  </section>

  <section>
    <h3>Most Common Errors</h3>
    <div id="topErrors" class="grid"></div>
  </section>

  <section>
    <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
      <h3>Critical Errors</h3>
      <input id="searchInput" placeholder="Search critical messages...">
    </div>
    <table>
      <thead>
        <tr><th>Timestamp</th><th>Message</th></tr>
      </thead>
      <tbody id="criticalTable"></tbody>
    </table>
  </section>
</main>
<script>
let dashboardData = null;

function fetchData() {
    fetch('/api/data').then(r => r.json()).then(data => {
        dashboardData = data;
        renderPercentages(data.percentages);
        renderTimeline();
        renderTopErrors(data.top_errors);
        renderCriticalTable(data.critical_logs);
    }).catch(err => {
        console.error(err);
    });
}

function renderPercentages(percentages) {
    const svg = document.getElementById('levelChart');
    svg.innerHTML = '';
    const levels = Object.keys(percentages);
    const values = levels.map(l => percentages[l]);
    const maxVal = Math.max(...values, 1);
    const width = svg.clientWidth || 400;
    const height = svg.clientHeight || 240;
    const barWidth = width / (levels.length * 1.5);
    levels.forEach((lvl, idx) => {
        const val = percentages[lvl];
        const barHeight = (val / maxVal) * (height - 40);
        const x = 20 + idx * (barWidth * 1.5);
        const y = height - barHeight - 20;
        const color = levelColor(lvl);
        const rect = `<rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" fill="${color}" rx="6" />`;
        const textVal = `<text x="${x + barWidth/2}" y="${y - 6}" fill="#e5e7eb" font-size="12" text-anchor="middle">${val.toFixed(1)}%</text>`;
        const textLbl = `<text x="${x + barWidth/2}" y="${height - 6}" fill="#9ca3af" font-size="12" text-anchor="middle">${lvl}</text>`;
        svg.insertAdjacentHTML('beforeend', rect + textVal + textLbl);
    });
}

function renderTimeline() {
    if (!dashboardData) return;
    const filter = document.getElementById('filterSelect').value;
    const series = dashboardData.timeline[filter] || [];
    const svg = document.getElementById('timelineChart');
    svg.innerHTML = '';
    const width = svg.clientWidth || 400;
    const height = svg.clientHeight || 240;
    if (!series.length) return;

    const counts = series.map(p => p.count);
    const maxVal = Math.max(...counts, 1);
    const step = width / Math.max(series.length - 1, 1);

    // axes
    svg.insertAdjacentHTML('beforeend', `<line x1="30" y1="${height-30}" x2="${width-10}" y2="${height-30}" stroke="#4b5563"/>`);
    svg.insertAdjacentHTML('beforeend', `<line x1="30" y1="10" x2="30" y2="${height-30}" stroke="#4b5563"/>`);

    const points = series.map((p, idx) => {
        const x = 30 + idx * (step * ((width-40)/width));
        const y = (height - 30) - (p.count / maxVal) * (height - 50);
        return {x,y,label:p.hour,count:p.count};
    });

    // polyline
    const pts = points.map(pt => `${pt.x},${pt.y}`).join(' ');
    svg.insertAdjacentHTML('beforeend', `<polyline points="${pts}" fill="none" stroke="#60a5fa" stroke-width="2"/>`);

    points.forEach(pt => {
        svg.insertAdjacentHTML('beforeend', `<circle cx="${pt.x}" cy="${pt.y}" r="4" fill="#2563eb"/>`);
        svg.insertAdjacentHTML('beforeend', `<text x="${pt.x}" y="${pt.y - 8}" fill="#e5e7eb" font-size="11" text-anchor="middle">${pt.count}</text>`);
    });

    const labelsEvery = Math.max(1, Math.floor(points.length / 6));
    points.forEach((pt, idx) => {
        if (idx % labelsEvery === 0 || idx === points.length-1) {
            svg.insertAdjacentHTML('beforeend', `<text x="${pt.x}" y="${height-10}" fill="#9ca3af" font-size="11" text-anchor="middle">${pt.label.slice(5)}</text>`);
        }
    });
}

function renderTopErrors(list) {
    const container = document.getElementById('topErrors');
    container.innerHTML = '';
    if (!list.length) {
        container.textContent = 'No error data';
        return;
    }
    list.slice(0, 8).forEach(item => {
        const div = document.createElement('div');
        div.className = 'chip';
        div.innerHTML = `<strong>${item.count}x</strong> &mdash; ${item.message}`;
        container.appendChild(div);
    });
}

function renderCriticalTable(rows) {
    const tbody = document.getElementById('criticalTable');
    tbody.innerHTML = '';
    rows.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${r.timestamp}</td><td>${r.message}</td>`;
        tbody.appendChild(tr);
    });
}

function levelColor(level) {
    const map = {INFO:'#2563eb', WARN:'#f59e0b', ERROR:'#ef4444', CRITICAL:'#f97316'};
    return map[level] || '#6b7280';
}

document.getElementById('filterSelect').addEventListener('change', renderTimeline);
document.getElementById('searchInput').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    const rows = Array.from(document.querySelectorAll('#criticalTable tr'));
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(q) ? '' : 'none';
    });
});

fetchData();
setInterval(fetchData, 10000);
</script>
</body>
</html>
"""

# ------------------------------------------------------------
# Log generation utilities
# ------------------------------------------------------------

LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]

INFO_MESSAGES = [
    "User logged in", "Background job completed", "Cache refreshed",
    "Heartbeat received", "Metrics flushed", "Configuration loaded"
]
WARN_MESSAGES = [
    "Memory usage high", "Slow response detected", "Disk nearing capacity",
    "Retrying connection", "Deprecated API used"
]
ERROR_MESSAGES = [
    "Database connection failed", "Timeout while calling service",
    "Permission denied", "Failed to write file", "Queue overflow",
    "Authentication token expired", "Unexpected None value"
]
CRITICAL_MESSAGES = [
    "System outage detected", "Data corruption detected",
    "Kernel panic imminent", "Unrecoverable error in module",
    "Critical dependency unavailable"
]

TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S,%f"


def ensure_log_file():
    if os.path.exists(LOG_FILE):
        return
    random.seed(42)
    base = datetime.now() - timedelta(hours=24)
    times = [base + timedelta(seconds=random.randint(0, 24 * 3600)) for _ in range(1000)]
    times.sort()
    level_weights = [0.58, 0.2, 0.15, 0.07]
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for t in times:
            level = random.choices(LEVELS, weights=level_weights, k=1)[0]
            if level == "INFO":
                msg = random.choice(INFO_MESSAGES)
            elif level == "WARN":
                msg = random.choice(WARN_MESSAGES)
            elif level == "ERROR":
                msg = random.choice(ERROR_MESSAGES)
            else:
                msg = random.choice(CRITICAL_MESSAGES)
            line = f"{t.strftime(TIMESTAMP_FMT)[:-3]} [{level}] {msg}\n"
            f.write(line)


def parse_log():
    level_counts = Counter()
    errors_by_hour = Counter()
    error_only_by_hour = Counter()
    critical_by_hour = Counter()
    error_messages = Counter()
    critical_rows = []
    total_lines = 0

    line_re = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[(?P<level>[A-Z]+)\] (?P<msg>.+)$")

    if not os.path.exists(LOG_FILE):
        return {}
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = line_re.match(line)
            if not m:
                continue
            total_lines += 1
            ts_str = m.group("ts")
            level = m.group("level")
            msg = m.group("msg")
            level_counts[level] += 1
            try:
                ts = datetime.strptime(ts_str, TIMESTAMP_FMT)
            except Exception:
                continue
            hour_key = ts.strftime("%Y-%m-%d %H:00")
            if level in ("ERROR", "CRITICAL"):
                errors_by_hour[hour_key] += 1
                error_messages[msg] += 1
                if level == "ERROR":
                    error_only_by_hour[hour_key] += 1
                else:
                    critical_by_hour[hour_key] += 1
            if level == "CRITICAL":
                critical_rows.append({"timestamp": ts_str, "message": msg})

    percentages = {}
    for lvl in LEVELS:
        count = level_counts[lvl]
        percentages[lvl] = (count / total_lines * 100) if total_lines else 0.0

    def pack_timeline(counter):
        items = []
        for hour, count in sorted(counter.items()):
            items.append({"hour": hour, "count": count})
        return items

    top_errors = [{"message": msg, "count": cnt} for msg, cnt in error_messages.most_common(20)]

    data = {
        "percentages": percentages,
        "timeline": {
            "all": pack_timeline(errors_by_hour),
            "error": pack_timeline(error_only_by_hour),
            "alert": pack_timeline(critical_by_hour),
        },
        "top_errors": top_errors,
        "critical_logs": critical_rows,
    }
    return data


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path.startswith("/api/data"):
            data = parse_log()
            payload = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == "/server.log":
            # allow direct download of the log
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Log file not found")
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        # Quiet server logs
        return


def find_port(start=8000):
    port = start
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("", port))
                return port
            except OSError:
                port += 1


def run_server():
    ensure_log_file()
    port = find_port()
    handler = DashboardHandler
    server = socketserver.ThreadingTCPServer(("", port), handler)
    server.daemon_threads = True

    print(f"Log Analytics Dashboard running at http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()