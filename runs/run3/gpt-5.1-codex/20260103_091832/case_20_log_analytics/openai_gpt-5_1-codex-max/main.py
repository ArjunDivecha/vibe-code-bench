import os
import re
import json
import random
import datetime
from datetime import datetime, timedelta
from collections import Counter
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

LOG_FILE = "server.log"

HTML_PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Log Analytics Dashboard</title>
<style>
:root {
    --bg: #0b1021;
    --panel: #11182d;
    --accent: #55d1ff;
    --muted: #9fb0c3;
    --text: #e7ecf3;
    --error: #f44336;
    --warn: #ffa726;
    --info: #4caf50;
    --critical: #c2185b;
}
* { box-sizing: border-box; }
body {
    font-family: "Segoe UI", sans-serif;
    margin: 0;
    background: var(--bg);
    color: var(--text);
}
header {
    padding: 24px;
    border-bottom: 1px solid #1b2438;
    background: linear-gradient(135deg, rgba(85,209,255,0.08), rgba(85,209,255,0));
}
h1 { margin: 0; font-size: 24px; letter-spacing: .3px; }
h2 { margin: 0 0 8px 0; font-size: 18px; }
.wrapper { padding: 20px; }
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit,minmax(280px,1fr));
    gap: 16px;
}
.card {
    background: var(--panel);
    border: 1px solid #1b2438;
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 8px 22px rgba(0,0,0,0.35);
}
.stat {
    display: flex; justify-content: space-between; margin-bottom: 6px; color: var(--muted);
}
.badge {
    padding: 4px 10px; border-radius: 16px; font-size: 12px;
    background: rgba(85,209,255,0.1); color: var(--accent); border: 1px solid rgba(85,209,255,0.2);
}
.filter {
    display: inline-flex; gap: 8px; margin: 12px 0;
}
.filter button {
    background: #121a2f; color: var(--text); border: 1px solid #1f2a45;
    padding: 8px 14px; border-radius: 20px; cursor: pointer; transition: all .15s ease;
}
.filter button.active { background: var(--accent); color: #042033; border-color: transparent; }
small { color: var(--muted); }
svg { width: 100%; height: 220px; }
.table-container {
    max-height: 340px; overflow: auto; border: 1px solid #1b2438; border-radius: 8px;
}
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 8px 10px; border-bottom: 1px solid #1c263e; text-align: left; }
th { position: sticky; top: 0; background: #0f1528; z-index: 1; }
tr:nth-child(even) td { background: #0d1325; }
.search {
    display: flex; gap: 10px; margin: 8px 0 12px;
}
.search input {
    flex: 1; padding: 10px 12px; border-radius: 8px; border: 1px solid #1f2a45;
    background: #0d1325; color: var(--text); outline: none;
}
.tag {
    padding: 3px 8px; border-radius: 12px; font-size: 11px; color: #fff;
}
.tag.INFO { background: var(--info); }
.tag.WARN { background: var(--warn); color:#000; }
.tag.ERROR { background: var(--error); }
.tag.CRITICAL { background: var(--critical); }
.footer { color: var(--muted); text-align: right; margin-top: 8px; font-size: 12px; }
.note { color: var(--muted); margin-bottom: 8px; }
.legend { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;}
.legend span { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--muted);}
.legend b { display: inline-block; width: 14px; height: 8px; border-radius: 4px; }
</style>
</head>
<body>
<header>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h1>Log Analytics Dashboard</h1>
            <small>Live insight from server.log</small>
        </div>
        <div class="badge" id="recordCount">Loading…</div>
    </div>
</header>

<div class="wrapper">
    <div class="filter">
        <button data-filter="all" class="active">All</button>
        <button data-filter="error">Error</button>
        <button data-filter="alert">Alert</button>
    </div>
    <small id="filterHint">Showing all log levels</small>

    <div class="grid" style="margin-top: 10px;">
        <div class="card">
            <h2>Level Distribution</h2>
            <small>Percentage share of each level</small>
            <svg id="distChart" viewBox="0 0 400 220"></svg>
        </div>
        <div class="card">
            <h2>Errors per Hour</h2>
            <small>Timeline of ERROR + CRITICAL</small>
            <svg id="timelineChart" viewBox="0 0 600 220"></svg>
        </div>
        <div class="card">
            <h2>Most Common Errors</h2>
            <small>Top recurring error messages</small>
            <svg id="topErrorsChart" viewBox="0 0 400 220"></svg>
        </div>
    </div>

    <div class="grid" style="margin-top: 16px;">
        <div class="card">
            <h2>Critical Errors</h2>
            <div class="note">Searchable table of all CRITICAL entries.</div>
            <div class="search">
                <input id="criticalSearch" placeholder="Search critical errors (message or time)…">
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr><th style="width:170px;">Timestamp</th><th>Message</th></tr>
                    </thead>
                    <tbody id="criticalTable"></tbody>
                </table>
            </div>
        </div>
        <div class="card">
            <h2>Log Explorer</h2>
            <div class="note">Filtered list of ERROR/CRITICAL entries.</div>
            <div class="table-container" style="max-height: 340px;">
                <table>
                    <thead>
                        <tr><th style="width:140px;">Level</th><th style="width:170px;">Timestamp</th><th>Message</th></tr>
                    </thead>
                    <tbody id="logTable"></tbody>
                </table>
            </div>
        </div>
    </div>
    <div class="legend">
        <span><b style="background: var(--info);"></b>INFO</span>
        <span><b style="background: var(--warn);"></b>WARN</span>
        <span><b style="background: var(--error);"></b>ERROR</span>
        <span><b style="background: var(--critical);"></b>CRITICAL</span>
    </div>
    <div class="footer">Generated at <span id="generatedAt">—</span></div>
</div>

<script>
const levelColors = {
    "INFO": getComputedStyle(document.documentElement).getPropertyValue('--info').trim(),
    "WARN": getComputedStyle(document.documentElement).getPropertyValue('--warn').trim(),
    "ERROR": getComputedStyle(document.documentElement).getPropertyValue('--error').trim(),
    "CRITICAL": getComputedStyle(document.documentElement).getPropertyValue('--critical').trim(),
};
let logData = null;
let currentFilter = "all";

function applyFilter(entries) {
    if (currentFilter === "error") return entries.filter(e => e.level === "ERROR");
    if (currentFilter === "alert") return entries.filter(e => e.level === "CRITICAL");
    return entries;
}
function computePercentages(entries) {
    const levels = ["INFO","WARN","ERROR","CRITICAL"];
    const counts = {INFO:0,WARN:0,ERROR:0,CRITICAL:0};
    entries.forEach(e => { counts[e.level] = (counts[e.level] || 0) + 1; });
    const total = entries.length || 1;
    const perc = {};
    levels.forEach(l => perc[l] = +(counts[l] * 100 / total).toFixed(2));
    return {counts, perc};
}
function computeTimeline(entries) {
    const relevant = entries.filter(e => e.level === "ERROR" || e.level === "CRITICAL");
    const buckets = {};
    relevant.forEach(e => {
        const hour = e.timestamp.slice(0,13) + ":00";
        buckets[hour] = (buckets[hour] || 0) + 1;
    });
    return Object.entries(buckets).sort((a,b)=> new Date(a[0]) - new Date(b[0]))
        .map(([hour,count])=>({hour,count}));
}
function computeTopErrors(entries) {
    const relevant = entries.filter(e => e.level === "ERROR" || e.level === "CRITICAL");
    const counts = {};
    relevant.forEach(e => counts[e.message] = (counts[e.message]||0)+1);
    return Object.entries(counts).sort((a,b)=> b[1]-a[1]).slice(0,8)
        .map(([message,count])=>({message,count}));
}
function renderDistribution(perc) {
    const svg = document.getElementById("distChart");
    const levels = Object.keys(perc);
    const barH = 34, width = 400, maxBar = width - 140;
    const height = levels.length * barH + 10;
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.innerHTML = "";
    levels.forEach((lvl,i)=>{
        const y = i*barH + 10;
        const pct = perc[lvl] || 0;
        const barW = Math.max(2, pct/100 * maxBar);
        svg.innerHTML += `
            <text x="0" y="${y}" fill="#9fb0c3" font-size="12" dy="12">${lvl}</text>
            <rect x="70" y="${y}" width="${barW}" height="18" rx="5" fill="${levelColors[lvl]}"></rect>
            <text x="${80+barW}" y="${y}" dy="14" fill="#fff" font-size="12">${pct.toFixed(2)}%</text>
        `;
    });
}
function renderTimeline(points) {
    const svg = document.getElementById("timelineChart");
    if (!points.length) { svg.innerHTML = '<text x="10" y="50" fill="#9fb0c3">No error data</text>'; return; }
    const padding = 30, w = 600, h = 220;
    const maxY = Math.max(...points.map(p=>p.count));
    const stepX = (w - padding*2) / Math.max(points.length-1,1);
    let path = "";
    points.forEach((p,i)=>{
        const x = padding + i*stepX;
        const y = h - padding - (p.count / maxY) * (h - padding*2);
        path += `${i===0 ? 'M':'L'}${x},${y} `;
    });
    svg.innerHTML = `
        <polyline points="${path.replace(/M|L/g,'')}" fill="none" stroke="${levelColors['ERROR']}" stroke-width="2.2" />
    `;
    points.forEach((p,i)=>{
        const x = padding + i*stepX;
        const y = h - padding - (p.count / maxY) * (h - padding*2);
        svg.innerHTML += `<circle cx="${x}" cy="${y}" r="4" fill="${levelColors['CRITICAL']}"></circle>`;
        svg.innerHTML += `<text x="${x}" y="${h-6}" fill="#9fb0c3" font-size="11" text-anchor="middle">${p.hour.slice(11,16)}</text>`;
        svg.innerHTML += `<text x="${x}" y="${y-8}" fill="#fff" font-size="11" text-anchor="middle">${p.count}</text>`;
    });
}
function renderTopErrors(items) {
    const svg = document.getElementById("topErrorsChart");
    if (!items.length) { svg.innerHTML = '<text x="10" y="50" fill="#9fb0c3">No error data</text>'; return; }
    const w = 400, barH = 24, height = items.length * barH + 18;
    const maxCount = Math.max(...items.map(i=>i.count));
    svg.setAttribute("viewBox", `0 0 ${w} ${height}`);
    svg.innerHTML = "";
    items.forEach((item,i)=>{
        const y = i*barH + 12;
        const barW = (item.count / maxCount) * (w - 120);
        svg.innerHTML += `
            <rect x="0" y="${y-10}" width="${w}" height="22" fill="rgba(255,255,255,0.02)"></rect>
            <rect x="8" y="${y-8}" width="${barW}" height="14" rx="4" fill="${levelColors['ERROR']}"></rect>
            <text x="${8+barW+6}" y="${y+2}" fill="#fff" font-size="12">${item.count}</text>
            <text x="${8}" y="${y-2}" fill="#9fb0c3" font-size="11">${item.message.slice(0,55)}${item.message.length>55?'…':''}</text>
        `;
    });
}
function renderCriticalTable(query="") {
    const tbody = document.getElementById("criticalTable");
    const q = query.trim().toLowerCase();
    const rows = logData.critical.filter(row => {
        const text = (row.timestamp + " " + row.message).toLowerCase();
        return text.includes(q);
    }).map(row=>`
        <tr>
            <td>${row.timestamp}</td>
            <td>${row.message}</td>
        </tr>
    `).join("");
    tbody.innerHTML = rows || `<tr><td colspan="2" style="color:#9fb0c3;">No critical errors match.</td></tr>`;
}
function renderLogTable(filteredEntries) {
    const tbody = document.getElementById("logTable");
    const rows = filteredEntries
        .filter(e => e.level === "ERROR" || e.level === "CRITICAL")
        .slice(-150) // keep it light
        .reverse()
        .map(e=>`
            <tr>
                <td><span class="tag ${e.level}">${e.level}</span></td>
                <td>${e.timestamp}</td>
                <td>${e.message}</td>
            </tr>`).join("");
    tbody.innerHTML = rows || `<tr><td colspan="3" style="color:#9fb0c3;">No entries in this filter.</td></tr>`;
}
function renderAll() {
    if (!logData) return;
    const filtered = applyFilter(logData.entries);
    const {counts, perc} = computePercentages(filtered.length ? filtered : logData.entries);
    renderDistribution(perc);
    renderTimeline(computeTimeline(filtered));
    renderTopErrors(computeTopErrors(filtered));
    document.getElementById("recordCount").textContent = `${filtered.length} shown / ${logData.entries.length} total`;
    document.getElementById("filterHint").textContent =
        currentFilter === "all" ? "Showing all log levels" :
        currentFilter === "error" ? "Filtered to ERROR only" :
        "Filtered to CRITICAL only";
    renderLogTable(filtered);
}
function setupFilters() {
    document.querySelectorAll(".filter button").forEach(btn=>{
        btn.addEventListener("click", ()=>{
            document.querySelectorAll(".filter button").forEach(b=>b.classList.remove("active"));
            btn.classList.add("active");
            currentFilter = btn.dataset.filter;
            renderAll();
        });
    });
}
function init() {
    fetch("/data").then(r=>r.json()).then(data=>{
        logData = data;
        document.getElementById("generatedAt").textContent = data.generated_at;
        renderAll();
        renderCriticalTable();
        document.getElementById("criticalSearch").addEventListener("input", (e)=>renderCriticalTable(e.target.value));
    }).catch(err=>{
        console.error(err);
        alert("Failed to load data");
    });
    setupFilters();
}
init();
</script>
</body>
</html>
"""

def generate_fake_log(path: str, lines: int = 1000) -> None:
    random.seed()
    base_time = datetime.now() - timedelta(hours=24)
    levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    weights = [0.55, 0.2, 0.18, 0.07]
    message_pool = {
        "INFO": [
            "Scheduled task completed",
            "Heartbeat received from worker-{id}",
            "Cache warm complete ({id} keys)",
            "Health check OK for service-{id}",
            "Background job id={id} finished successfully",
        ],
        "WARN": [
            "Slow response detected on endpoint /api/v{id}",
            "High memory usage warning ({id}%)",
            "Retrying connection to database shard-{id}",
            "Queue latency warning ({id} seconds)",
            "Disk space warning on volume-{id}",
        ],
        "ERROR": [
            "User authentication failed for user-{id}",
            "Database timeout while reading shard-{id}",
            "Payment processing error: invalid token",
            "File upload failed for request-{id}",
            "Cache miss storm detected on key group-{id}",
            "Email delivery failed for batch-{id}",
        ],
        "CRITICAL": [
            "Service outage detected in region-{id}",
            "Data corruption detected on shard-{id}",
            "Unrecoverable error in worker-{id}",
            "Kernel panic on host-{id}",
            "RAID failure reported on controller-{id}",
        ],
    }
    entries = []
    for i in range(lines):
        dt = base_time + timedelta(seconds=random.randint(0, 24 * 3600 - 1))
        level = random.choices(levels, weights=weights, k=1)[0]
        template = random.choice(message_pool[level])
        msg = template.replace("{id}", str(random.randint(1, 99)))
        entries.append((dt, level, msg))
    entries.sort(key=lambda x: x[0])
    with open(path, "w", encoding="utf-8") as f:
        for dt, level, msg in entries:
            f.write(f"{dt.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {msg}\n")

def parse_log(path: str):
    pattern = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) \[(?P<level>[A-Z]+)\] (?P<message>.*)$")
    counts = Counter()
    error_messages = Counter()
    timeline = Counter()
    entries = []
    critical_entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = pattern.match(line)
            if not m:
                continue
            level = m.group("level")
            message = m.group("message")
            ts_str = f"{m.group('date')} {m.group('time')}"
            try:
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            counts[level] += 1
            entry = {"timestamp": ts_str, "level": level, "message": message}
            entries.append(entry)
            if level == "CRITICAL":
                critical_entries.append(entry)
            if level in ("ERROR", "CRITICAL"):
                error_messages[message] += 1
                hour_bucket = ts.replace(minute=0, second=0, microsecond=0)
                timeline[hour_bucket] += 1
    total = len(entries) or 1
    percentages = {lvl: round(counts.get(lvl, 0) * 100.0 / total, 2) for lvl in ["INFO","WARN","ERROR","CRITICAL"]}
    timeline_list = [{"hour": k.strftime("%Y-%m-%d %H:%M"), "count": v} for k, v in sorted(timeline.items())]
    top_errors = [{"message": msg, "count": cnt} for msg, cnt in error_messages.most_common(10)]
    return {
        "percentages": percentages,
        "counts": {lvl: counts.get(lvl, 0) for lvl in ["INFO","WARN","ERROR","CRITICAL"]},
        "timeline": timeline_list,
        "top_errors": top_errors,
        "entries": entries,
        "critical": critical_entries,
    }

class DashboardHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="text/html"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self._set_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif path == "/data":
            payload = ANALYTICS.copy()
            payload["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._set_headers(content_type="application/json")
            self.wfile.write(json.dumps(payload).encode("utf-8"))
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        # Silence default logging to keep console clean
        return

def ensure_log():
    if not os.path.exists(LOG_FILE):
        print(f"[setup] {LOG_FILE} not found, generating synthetic log data …")
        generate_fake_log(LOG_FILE)
    else:
        # If file exists but is empty, generate content too
        if os.path.getsize(LOG_FILE) == 0:
            print(f"[setup] {LOG_FILE} is empty, generating synthetic log data …")
            generate_fake_log(LOG_FILE)

def main():
    global ANALYTICS
    ensure_log()
    ANALYTICS = parse_log(LOG_FILE)

    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), DashboardHandler)
    print(f"[info] Log Analytics Dashboard running at http://localhost:{port}")
    print("[info] Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[info] Shutting down…")
        server.server_close()

if __name__ == "__main__":
    main()