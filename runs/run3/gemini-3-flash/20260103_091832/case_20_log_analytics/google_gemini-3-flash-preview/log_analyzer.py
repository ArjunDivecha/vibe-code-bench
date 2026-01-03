import os
import random
import json
import datetime
import http.server
import socketserver
from collections import Counter, defaultdict

# Configuration
LOG_FILE = "server.log"
PORT = 8000
LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]
MESSAGES = {
    "INFO": ["User logged in", "Database connection successful", "Request processed", "Cache cleared"],
    "WARN": ["Slow response time", "Disk usage at 80%", "Invalid login attempt", "Deprecated API call"],
    "ERROR": ["Connection timeout", "Database query failed", "File not found", "Permission denied"],
    "CRITICAL": ["System crash", "Kernel panic", "Data corruption detected", "Out of memory"]
}

def generate_logs(filename, count=1000):
    """Generates fake log data."""
    print(f"Generating {count} lines of fake log data in {filename}...")
    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    
    with open(filename, "w") as f:
        for i in range(count):
            # Spread logs over the last 24 hours
            log_time = start_time + datetime.timedelta(seconds=random.randint(0, 86400))
            level = random.choices(LEVELS, weights=[0.6, 0.2, 0.15, 0.05])[0]
            msg = random.choice(MESSAGES[level])
            f.write(f"{log_time.strftime('%Y-%m-%d %H:%M:%S')} - {level} - {msg}\n")
    print("Log generation complete.")

def parse_logs(filename):
    """Parses the log file and returns structured data."""
    level_counts = Counter()
    hourly_errors = defaultdict(int)
    error_msgs = Counter()
    critical_logs = []
    all_logs = []

    if not os.path.exists(filename):
        return None

    with open(filename, "r") as f:
        for line in f:
            try:
                parts = line.strip().split(" - ")
                if len(parts) < 3: continue
                
                timestamp_str, level, message = parts[0], parts[1], parts[2]
                dt = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                level_counts[level] += 1
                all_logs.append({"time": timestamp_str, "level": level, "msg": message})
                
                if level in ["ERROR", "CRITICAL"]:
                    hour_key = dt.strftime("%H:00")
                    hourly_errors[hour_key] += 1
                    error_msgs[message] += 1
                
                if level == "CRITICAL":
                    critical_logs.append({"time": timestamp_str, "msg": message})
            except Exception as e:
                continue

    # Sort hourly errors by key (time)
    sorted_hours = sorted(hourly_errors.items())
    
    total = sum(level_counts.values())
    stats = {
        "levels": {k: (v/total)*100 for k, v in level_counts.items()},
        "timeline": [{"hour": k, "count": v} for k, v in sorted_hours],
        "top_errors": error_msgs.most_common(5),
        "critical": critical_logs,
        "all": all_logs
    }
    return stats

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            data = parse_logs(LOG_FILE)
            self.wfile.write(json.dumps(data).encode())
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        else:
            super().do_GET()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Log Analytics Dashboard</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; color: #333; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2 { margin-top: 0; font-size: 1.2rem; color: #555; }
        .stat-bar { height: 24px; background: #eee; border-radius: 4px; overflow: hidden; display: flex; margin-bottom: 10px; }
        .bar-segment { height: 100%; transition: width 0.3s; }
        .legend { display: flex; gap: 15px; font-size: 0.8rem; margin-bottom: 20px; }
        .legend-item { display: flex; align-items: center; gap: 5px; }
        .dot { width: 10px; height: 10px; border-radius: 50%; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { text-align: left; padding: 10px; border-bottom: 1px solid #eee; }
        tr:hover { background: #fafafa; }
        .level-tag { padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
        .CRITICAL { background: #fee2e2; color: #991b1b; }
        .ERROR { background: #ffedd5; color: #9a3412; }
        .WARN { background: #fef9c3; color: #854d0e; }
        .INFO { background: #dcfce7; color: #166534; }
        input, select { padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 10px; }
        svg { background: #fff; width: 100%; height: 200px; }
    </style>
</head>
<body>
    <h1>Log Analytics Dashboard</h1>
    
    <div class="grid">
        <div class="card">
            <h2>Log Level Distribution</h2>
            <div id="dist-legend" class="legend"></div>
            <div id="dist-bar" class="stat-bar"></div>
            <div id="dist-list"></div>
        </div>
        <div class="card">
            <h2>Error Timeline (Errors/Hour)</h2>
            <div id="timeline-chart"></div>
        </div>
    </div>

    <div class="card">
        <div style="display:flex; justify-content: space-between; align-items: center;">
            <h2>Log Explorer</h2>
            <div>
                <input type="text" id="search" placeholder="Search critical logs...">
                <select id="levelFilter">
                    <option value="ALL">All Levels</option>
                    <option value="ERROR_ALERT">Errors & Critical</option>
                    <option value="CRITICAL">Critical Only</option>
                </select>
            </div>
        </div>
        <table id="logTable">
            <thead>
                <tr><th>Timestamp</th><th>Level</th><th>Message</th></tr>
            </thead>
            <tbody id="logBody"></tbody>
        </table>
    </div>

    <script>
        const COLORS = { INFO: '#22c55e', WARN: '#eab308', ERROR: '#f97316', CRITICAL: '#ef4444' };
        let logData = null;

        async function fetchData() {
            const res = await fetch('/api/data');
            logData = await res.json();
            renderDashboard();
        }

        function renderDashboard() {
            // Render Bar
            const distBar = document.getElementById('dist-bar');
            const distLegend = document.getElementById('dist-legend');
            distBar.innerHTML = '';
            distLegend.innerHTML = '';
            for (const [lvl, pct] of Object.entries(logData.levels)) {
                distBar.innerHTML += `<div class="bar-segment" style="width: ${pct}%; background: ${COLORS[lvl]}" title="${lvl}: ${pct.toFixed(1)}%"></div>`;
                distLegend.innerHTML += `<div class="legend-item"><div class="dot" style="background:${COLORS[lvl]}"></div>${lvl} (${pct.toFixed(1)}%)</div>`;
            }

            // Render SVG Timeline
            const chartDiv = document.getElementById('timeline-chart');
            const points = logData.timeline;
            const maxVal = Math.max(...points.map(p => p.count), 1);
            const width = 500;
            const height = 150;
            const step = width / (points.length - 1 || 1);
            
            let pathD = `M 0 ${height - (points[0].count / maxVal * height)} `;
            points.forEach((p, i) => {
                const x = i * step;
                const y = height - (p.count / maxVal * height);
                pathD += `L ${x} ${y} `;
            });

            chartDiv.innerHTML = `
                <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
                    <path d="${pathD}" fill="none" stroke="#ef4444" stroke-width="2" />
                    ${points.map((p, i) => `<circle cx="${i * step}" cy="${height - (p.count / maxVal * height)}" r="3" fill="#ef4444" />`).join('')}
                </svg>
                <div style="display:flex; justify-content:space-between; font-size:10px; color:#999; margin-top:5px">
                    <span>${points[0].hour}</span><span>${points[points.length-1].hour}</span>
                </div>
            `;

            updateTable();
        }

        function updateTable() {
            const filter = document.getElementById('levelFilter').value;
            const search = document.getElementById('search').value.toLowerCase();
            const body = document.getElementById('logBody');
            body.innerHTML = '';

            let filtered = logData.all;
            if (filter === 'CRITICAL') filtered = logData.all.filter(l => l.level === 'CRITICAL');
            else if (filter === 'ERROR_ALERT') filtered = logData.all.filter(l => l.level === 'ERROR' || l.level === 'CRITICAL');

            filtered.filter(l => l.msg.toLowerCase().includes(search))
                .slice(0, 50) // Limit display
                .forEach(l => {
                    body.innerHTML += `<tr>
                        <td style="font-family:monospace; font-size:0.85rem">${l.time}</td>
                        <td><span class="level-tag ${l.level}">${l.level}</span></td>
                        <td>${l.msg}</td>
                    </tr>`;
                });
        }

        document.getElementById('levelFilter').onchange = updateTable;
        document.getElementById('search').oninput = updateTable;

        fetchData();
    </script>
</body>
</html>
"""

def run():
    if not os.path.exists(LOG_FILE):
        generate_logs(LOG_FILE)
    
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.server_close()

if __name__ == "__main__":
    run()