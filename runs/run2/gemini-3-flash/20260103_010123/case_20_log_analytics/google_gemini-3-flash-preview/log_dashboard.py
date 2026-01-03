import os
import random
import json
import datetime
import http.server
import socketserver
import threading
from collections import Counter, defaultdict

# Configuration
LOG_FILE = "server.log"
PORT = 8000
LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]
ERROR_MESSAGES = [
    "Database connection timeout",
    "Disk space low on /dev/sda1",
    "Unauthorized access attempt detected",
    "API rate limit exceeded",
    "Null pointer exception in worker thread",
    "Failed to sync with upstream peer",
    "Memory threshold reached",
    "Invalid CSRF token received"
]

def generate_fake_logs(filename, count=1000):
    """Generates a fake log file if it doesn't exist."""
    print(f"Generating {count} lines of fake log data...")
    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    with open(filename, "w") as f:
        for i in range(count):
            # Spread logs over the last 24 hours
            log_time = start_time + datetime.timedelta(seconds=random.randint(0, 86400))
            level = random.choices(LEVELS, weights=[60, 20, 15, 5])[0]
            msg = random.choice(ERROR_MESSAGES) if level in ["ERROR", "CRITICAL"] else "Process heartbeat check successful"
            f.write(f"[{log_time.strftime('%Y-%m-%d %H:%M:%S')}] {level}: {msg}\n")
    print(f"Log file '{filename}' created.")

def parse_logs(filename):
    """Parses the log file and returns structured data."""
    data = {
        "levels": Counter(),
        "hourly_errors": defaultdict(int),
        "common_errors": Counter(),
        "critical_logs": [],
        "all_logs": []
    }
    
    if not os.path.exists(filename):
        return data

    with open(filename, "r") as f:
        for line in f:
            try:
                # Format: [YYYY-MM-DD HH:MM:SS] LEVEL: Message
                parts = line.split("] ", 1)
                timestamp_str = parts[0][1:]
                rest = parts[1].split(": ", 1)
                level = rest[0]
                message = rest[1].strip()
                
                dt = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                hour_key = dt.strftime("%H:00")
                
                data["levels"][level] += 1
                data["all_logs"].append({"time": timestamp_str, "level": level, "msg": message})
                
                if level in ["ERROR", "CRITICAL"]:
                    data["hourly_errors"][hour_key] += 1
                    data["common_errors"][message] += 1
                
                if level == "CRITICAL":
                    data["critical_logs"].append({"time": timestamp_str, "msg": message})
            except Exception:
                continue
    
    # Sort hourly data for chart
    sorted_hours = sorted(data["hourly_errors"].items())
    data["timeline"] = {"labels": [x[0] for x in sorted_hours], "values": [x[1] for x in sorted_hours]}
    
    # Convert counters to dicts for JSON
    data["levels_perc"] = {k: round((v / len(data["all_logs"])) * 100, 2) for k, v in data["levels"].items()}
    data["common_errors"] = dict(data["common_errors"].most_common(5))
    
    return data

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            log_data = parse_logs(LOG_FILE)
            self.wfile.write(json.dumps(log_data).encode())
        elif self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
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
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 1100px; margin: auto; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .full-width { grid-column: span 2; }
        h2 { margin-top: 0; font-size: 1.2rem; color: #555; border-bottom: 1px solid #eee; padding-bottom: 10px; }
        .stat-val { font-size: 24px; font-weight: bold; color: #2c3e50; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { text-align: left; padding: 10px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
        th { background: #f9f9f9; }
        .level-tag { padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; color: white; }
        .INFO { background: #27ae60; } .WARN { background: #f39c12; } .ERROR { background: #e74c3c; } .CRITICAL { background: #8e44ad; }
        .controls { margin-bottom: 20px; display: flex; gap: 10px; align-items: center; }
        select, input { padding: 8px; border-radius: 4px; border: 1px solid #ddd; }
        svg { background: #fff; }
        .bar { fill: #3498db; }
        .bar:hover { fill: #2980b9; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Log Analytics Dashboard</h1>
        
        <div class="grid">
            <div class="card">
                <h2>Log Distribution (%)</h2>
                <div id="distribution-list"></div>
            </div>
            <div class="card">
                <h2>Top Error Messages</h2>
                <div id="top-errors"></div>
            </div>
            <div class="card full-width">
                <h2>Error Timeline (Errors/Hour)</h2>
                <div id="chart-container">
                    <svg id="timeline-svg" width="1000" height="200"></svg>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Log Explorer</h2>
            <div class="controls">
                <select id="level-filter" onchange="renderTable()">
                    <option value="ALL">All Levels</option>
                    <option value="ERROR">Errors</option>
                    <option value="CRITICAL">Critical Only</option>
                    <option value="WARN">Warnings</option>
                </select>
                <input type="text" id="search-input" placeholder="Search logs..." onkeyup="renderTable()">
            </div>
            <table id="log-table">
                <thead>
                    <tr><th>Timestamp</th><th>Level</th><th>Message</th></tr>
                </thead>
                <tbody id="log-body"></tbody>
            </table>
        </div>
    </div>

    <script>
        let logData = { all_logs: [] };

        async function fetchData() {
            const res = await fetch('/api/data');
            logData = await res.json();
            renderStats();
            renderTimeline();
            renderTable();
        }

        function renderStats() {
            const dist = document.getElementById('distribution-list');
            dist.innerHTML = Object.entries(logData.levels_perc).map(([lvl, perc]) => 
                `<div style="margin-bottom:8px">
                    <span class="level-tag ${lvl}">${lvl}</span> <strong>${perc}%</strong>
                </div>`
            ).join('');

            const errors = document.getElementById('top-errors');
            errors.innerHTML = Object.entries(logData.common_errors).map(([msg, count]) => 
                `<div style="font-size:0.85rem; padding:4px 0;"><strong>${count}x</strong> ${msg}</div>`
            ).join('');
        }

        function renderTimeline() {
            const svg = document.getElementById('timeline-svg');
            const data = logData.timeline.values;
            const labels = logData.timeline.labels;
            if(!data.length) return;

            const maxVal = Math.max(...data);
            const width = 1000;
            const height = 200;
            const barWidth = width / labels.length;

            let html = '';
            data.forEach((val, i) => {
                const barHeight = (val / maxVal) * (height - 40);
                const x = i * barWidth;
                const y = height - barHeight - 20;
                html += `<rect class="bar" x="${x+2}" y="${y}" width="${barWidth-4}" height="${barHeight}" />`;
                if(i % 3 === 0) {
                    html += `<text x="${x}" y="${height-5}" font-size="10" fill="#666">${labels[i]}</text>`;
                }
            });
            svg.innerHTML = html;
        }

        function renderTable() {
            const filter = document.getElementById('level-filter').value;
            const search = document.getElementById('search-input').value.toLowerCase();
            const body = document.getElementById('log-body');
            
            const filtered = logData.all_logs.filter(log => {
                const matchesLevel = filter === 'ALL' || log.level === filter;
                const matchesSearch = log.msg.toLowerCase().includes(search);
                return matchesLevel && matchesSearch;
            });

            body.innerHTML = filtered.slice(0, 100).map(log => `
                <tr>
                    <td>${log.time}</td>
                    <td><span class="level-tag ${log.level}">${log.level}</span></td>
                    <td>${log.msg}</td>
                </tr>
            `).join('');
        }

        fetchData();
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        generate_fake_logs(LOG_FILE)
    
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"Dashboard available at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.server_close()