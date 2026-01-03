import os
import json
import random
import datetime
import http.server
import socketserver
import collections
import re

# --- CONFIGURATION ---
LOG_FILE = "server.log"
PORT = 8000
LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]
ERROR_MESSAGES = [
    "Database connection failed",
    "Timeout waiting for response",
    "Out of memory error",
    "Disk space low",
    "Unauthorized access attempt",
    "Invalid API token",
    "Service unavailable",
    "Internal server error",
    "File not found",
    "Socket exception"
]

def generate_fake_logs(filename, count=1000):
    """Generates a fake server.log file if it doesn't exist."""
    print(f"Generating {count} fake log entries...")
    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    
    with open(filename, "w") as f:
        for i in range(count):
            # Spread logs over the last 24 hours
            log_time = start_time + datetime.timedelta(seconds=random.randint(0, 86400))
            level = random.choices(LEVELS, weights=[60, 20, 15, 5])[0]
            msg = random.choice(ERROR_MESSAGES) if level in ["ERROR", "CRITICAL"] else "Processing request"
            timestamp = log_time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {level}: {msg}\n")
    print(f"Log file created: {filename}")

def parse_logs(filename):
    """Parses the log file and returns structured data."""
    stats = {
        "level_counts": collections.Counter(),
        "hourly_errors": collections.defaultdict(int),
        "common_errors": collections.defaultdict(int),
        "critical_logs": []
    }
    
    pattern = re.compile(r"\[(?P<ts>.*?)\] (?P<lvl>\w+): (?P<msg>.*)")
    
    try:
        with open(filename, "r") as f:
            for line in f:
                match = pattern.match(line)
                if match:
                    d = match.groupdict()
                    lvl = d['lvl']
                    ts_str = d['ts']
                    msg = d['msg']
                    
                    stats["level_counts"][lvl] += 1
                    
                    if lvl in ["ERROR", "CRITICAL"]:
                        # Extract hour for timeline
                        hour = ts_str.split(":")[0] # YYYY-MM-DD HH
                        stats["hourly_errors"][hour] += 1
                        stats["common_errors"][msg] += 1
                        
                    if lvl == "CRITICAL":
                        stats["critical_logs"].append({"timestamp": ts_str, "message": msg})
                        
    except Exception as e:
        print(f"Error parsing logs: {e}")
        
    # Sort hourly data and format for frontend
    sorted_hours = sorted(stats["hourly_errors"].items())
    stats["timeline"] = [{"label": h, "count": c} for h, c in sorted_hours]
    
    # Format common errors
    sorted_errs = sorted(stats["common_errors"].items(), key=lambda x: x[1], reverse=True)[:5]
    stats["top_errors"] = [{"msg": m, "count": c} for m, c in sorted_errs]
    
    # Calculate percentages
    total = sum(stats["level_counts"].values())
    stats["percentages"] = {k: round((v/total)*100, 2) for k, v in stats["level_counts"].items()}
    
    return stats

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        elif self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            data = parse_logs(LOG_FILE)
            self.wfile.write(json.dumps(data).encode())
        else:
            super().do_GET()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Log Analytics Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f4f7f9; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 1200px; margin: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .card h3 { margin-top: 0; font-size: 0.9rem; color: #666; text-transform: uppercase; }
        .card .value { font-size: 1.8rem; font-weight: bold; }
        .charts { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .chart-box { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); min-height: 300px; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; }
        .critical-row { color: #d9534f; font-weight: 500; }
        .search-box { margin-bottom: 15px; width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; color: white; }
        .badge-info { background: #5bc0de; }
        .badge-warn { background: #f0ad4e; }
        .badge-error { background: #d9534f; }
        .badge-critical { background: #000; }
        svg { width: 100%; height: 200px; }
        .bar { fill: #4a90e2; transition: fill 0.3s; }
        .bar:hover { fill: #357abd; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Log Analytics Dashboard</h1>
            <button onclick="fetchData()">Refresh Data</button>
        </div>

        <div class="cards" id="stat-cards">
            <!-- Stats will be injected here -->
        </div>

        <div class="charts">
            <div class="chart-box">
                <h3>Error Distribution (Top 5)</h3>
                <div id="pie-chart-container"></div>
            </div>
            <div class="chart-box">
                <h3>Errors Per Hour (Timeline)</h3>
                <div id="timeline-chart"></div>
            </div>
        </div>

        <div class="card">
            <h3>Critical Logs & Search</h3>
            <input type="text" id="searchInput" class="search-box" placeholder="Search critical messages..." onkeyup="filterTable()">
            <table id="criticalTable">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody id="criticalBody">
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let criticalData = [];

        async function fetchData() {
            const res = await fetch('/api/data');
            const data = await res.json();
            renderDashboard(data);
        }

        function renderDashboard(data) {
            // Render Stats
            const cards = document.getElementById('stat-cards');
            cards.innerHTML = '';
            Object.entries(data.percentages).forEach(([level, pct]) => {
                cards.innerHTML += `
                    <div class="card">
                        <h3>${level}</h3>
                        <div class="value">${pct}%</div>
                        <div style="font-size:0.8rem; color:#888">${data.level_counts[level]} events</div>
                    </div>
                `;
            });

            // Render Timeline SVG
            const timelineDiv = document.getElementById('timeline-chart');
            const maxVal = Math.max(...data.timeline.map(d => d.count), 1);
            const barWidth = 100 / data.timeline.length;
            
            let svgHtml = `<svg viewBox="0 0 100 40" preserveAspectRatio="none">`;
            data.timeline.forEach((d, i) => {
                const h = (d.count / maxVal) * 35;
                svgHtml += `<rect class="bar" x="${i * barWidth}" y="${40 - h}" width="${barWidth - 0.5}" height="${h}">
                    <title>${d.label}: ${d.count} errors</title>
                </rect>`;
            });
            svgHtml += `</svg><div style="display:flex; justify-content:space-between; font-size:10px; color:#666; margin-top:5px;">
                <span>${data.timeline[0]?.label.split(' ')[1] || ''}:00</span>
                <span>${data.timeline[data.timeline.length-1]?.label.split(' ')[1] || ''}:00</span>
            </div>`;
            timelineDiv.innerHTML = svgHtml;

            // Render Common Errors List
            const pieContainer = document.getElementById('pie-chart-container');
            let errList = '<ul>';
            data.top_errors.forEach(err => {
                errList += `<li><strong>${err.count}</strong> - ${err.msg}</li>`;
            });
            errList += '</ul>';
            pieContainer.innerHTML = errList;

            // Render Table
            criticalData = data.critical_logs;
            renderTable(criticalData);
        }

        function renderTable(logs) {
            const body = document.getElementById('criticalBody');
            body.innerHTML = logs.map(log => `
                <tr class="critical-row">
                    <td>${log.timestamp}</td>
                    <td>${log.message}</td>
                </tr>
            `).join('');
        }

        function filterTable() {
            const term = document.getElementById('searchInput').value.toLowerCase();
            const filtered = criticalData.filter(log => 
                log.message.toLowerCase().includes(term) || 
                log.timestamp.toLowerCase().includes(term)
            );
            renderTable(filtered);
        }

        fetchData();
        setInterval(fetchData, 30000); // Refresh every 30s
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        generate_fake_logs(LOG_FILE)
    
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"--- Log Analytics Dashboard ---")
        print(f"Serving at: http://localhost:{PORT}")
        print(f"Using log file: {os.path.abspath(LOG_FILE)}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")