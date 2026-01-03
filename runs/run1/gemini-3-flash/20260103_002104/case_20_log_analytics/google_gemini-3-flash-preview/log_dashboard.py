import os
import json
import random
import time
import datetime
import http.server
import socketserver
import threading
from collections import Counter, defaultdict

LOG_FILE = "server.log"
PORT = 8000

# 1. Generate Fake Log Data if missing
def generate_fake_logs(filename, count=1000):
    levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    messages = {
        "INFO": ["User logged in", "Database connection successful", "Request processed", "Cache cleared"],
        "WARN": ["Disk usage at 80%", "Slow query detected", "API rate limit approaching", "Deprecated function call"],
        "ERROR": ["Failed to connect to DB", "Timeout on external API", "Null pointer exception", "File not found"],
        "CRITICAL": ["Kernel panic", "Power failure in zone B", "Security breach detected", "Data corruption in sector 7"]
    }
    
    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    
    with open(filename, "w") as f:
        for i in range(count):
            # Spread logs over the last 24 hours
            log_time = start_time + datetime.timedelta(seconds=random.randint(0, 86400))
            level = random.choices(levels, weights=[70, 15, 10, 5])[0]
            msg = random.choice(messages[level])
            timestamp = log_time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {level}: {msg}\n")
    print(f"Generated {count} lines of fake logs in {filename}")

# 2. Parse Log Data
def parse_logs(filename):
    data = {
        "levels": Counter(),
        "hourly_errors": defaultdict(int),
        "common_errors": Counter(),
        "critical_logs": []
    }
    
    if not os.path.exists(filename):
        return data

    with open(filename, "r") as f:
        for line in f:
            try:
                # Format: [YYYY-MM-DD HH:MM:SS] LEVEL: MESSAGE
                parts = line.split("] ", 1)
                timestamp_str = parts[0][1:]
                rest = parts[1].split(": ", 1)
                level = rest[0]
                message = rest[1].strip()
                
                data["levels"][level] += 1
                
                if level in ["ERROR", "CRITICAL"]:
                    hour = timestamp_str.split(":")[0] # YYYY-MM-DD HH
                    data["hourly_errors"][hour] += 1
                    data["common_errors"][message] += 1
                
                if level == "CRITICAL":
                    data["critical_logs"].append({
                        "time": timestamp_str,
                        "msg": message
                    })
            except Exception:
                continue

    # Format data for JSON
    total = sum(data["levels"].values())
    level_pct = {k: round((v/total)*100, 2) for k, v in data["levels"].items()}
    
    # Sort hourly errors by time
    sorted_hours = sorted(data["hourly_errors"].items())
    
    return {
        "level_distribution": level_pct,
        "timeline": sorted_hours,
        "top_errors": data["common_errors"].most_common(5),
        "critical_list": data["critical_logs"]
    }

# 3. HTTP Server
class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            stats = parse_logs(LOG_FILE)
            self.wfile.write(json.dumps(stats).encode())
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
        .container { max-width: 1000px; margin: auto; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2 { margin-top: 0; font-size: 1.2rem; color: #555; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #eee; }
        th { background: #fafafa; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
        .CRITICAL { background: #ffebee; color: #c62828; }
        .ERROR { background: #fff3e0; color: #ef6c00; }
        .INFO { background: #e3f2fd; color: #1565c0; }
        .chart-container { height: 200px; width: 100%; }
        input[type="text"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .bar { fill: #4a90e2; transition: height 0.3s; }
        .bar:hover { fill: #357abd; }
        .axis-label { font-size: 10px; fill: #888; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Log Analytics Dashboard</h1>
        
        <div class="grid">
            <div class="card">
                <h2>Log Level Distribution (%)</h2>
                <div id="level-list"></div>
            </div>
            <div class="card">
                <h2>Top Error Messages</h2>
                <div id="top-errors"></div>
            </div>
        </div>

        <div class="card" style="margin-bottom: 20px;">
            <h2>Errors Per Hour (Timeline)</h2>
            <div class="chart-container" id="timeline-chart">
                <!-- SVG injected here -->
            </div>
        </div>

        <div class="card">
            <h2>Critical Logs Explorer</h2>
            <input type="text" id="searchInput" placeholder="Search critical messages..." onkeyup="filterTable()">
            <table id="criticalTable">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Level</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody id="criticalBody"></tbody>
            </table>
        </div>
    </div>

    <script>
        async function loadData() {
            const resp = await fetch('/api/data');
            const data = await resp.json();
            
            // Render Levels
            const levelDiv = document.getElementById('level-list');
            levelDiv.innerHTML = Object.entries(data.level_distribution).map(([lvl, pct]) => `
                <div style="margin-bottom:10px">
                    <strong>${lvl}</strong>: ${pct}%
                    <div style="background:#eee; height:8px; border-radius:4px; margin-top:4px">
                        <div style="background:${lvl=='CRITICAL'?'#c62828':lvl=='ERROR'?'#ef6c00':'#4a90e2'}; width:${pct}%; height:100%; border-radius:4px"></div>
                    </div>
                </div>
            `).join('');

            // Render Top Errors
            const errDiv = document.getElementById('top-errors');
            errDiv.innerHTML = '<ul>' + data.top_errors.map(e => `<li>${e[0]} (<strong>${e[1]}</strong>)</li>`).join('') + '</ul>';

            // Render Timeline SVG
            renderTimeline(data.timeline);

            // Render Table
            const tbody = document.getElementById('criticalBody');
            tbody.innerHTML = data.critical_list.map(log => `
                <tr>
                    <td>${log.time}</td>
                    <td><span class="badge CRITICAL">CRITICAL</span></td>
                    <td>${log.msg}</td>
                </tr>
            `).join('');
        }

        function renderTimeline(timeline) {
            if (timeline.length === 0) return;
            const container = document.getElementById('timeline-chart');
            const width = container.clientWidth;
            const height = 200;
            const padding = 30;
            
            const maxVal = Math.max(...timeline.map(d => d[1]));
            const barWidth = (width - (padding * 2)) / timeline.length;

            let svg = `<svg width="${width}" height="${height}">`;
            timeline.forEach((d, i) => {
                const barHeight = (d[1] / maxVal) * (height - padding * 2);
                const x = padding + (i * barWidth);
                const y = height - padding - barHeight;
                svg += `
                    <rect class="bar" x="${x}" y="${y}" width="${barWidth - 5}" height="${barHeight}" />
                    <text class="axis-label" x="${x}" y="${height - 10}" transform="rotate(45, ${x}, ${height-10})">${d[0].split(' ')[1]}:00</text>
                `;
            });
            svg += `</svg>`;
            container.innerHTML = svg;
        }

        function filterTable() {
            const input = document.getElementById("searchInput");
            const filter = input.value.toUpperCase();
            const table = document.getElementById("criticalTable");
            const tr = table.getElementsByTagName("tr");

            for (let i = 1; i < tr.length; i++) {
                const td = tr[i].getElementsByTagName("td")[2];
                if (td) {
                    const txtValue = td.textContent || td.innerText;
                    tr[i].style.display = txtValue.toUpperCase().indexOf(filter) > -1 ? "" : "none";
                }
            }
        }

        loadData();
    </script>
</body>
</html>
"""

def run_server():
    if not os.path.exists(LOG_FILE):
        generate_fake_logs(LOG_FILE)
    
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()