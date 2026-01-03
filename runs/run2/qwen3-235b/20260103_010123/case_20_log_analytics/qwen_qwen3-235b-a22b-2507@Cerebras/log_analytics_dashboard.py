import os
import re
import json
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from functools import lru_cache

LOG_FILE = "server.log"

# Generate fake log data if file doesn't exist
def generate_log_file():
    if os.path.exists(LOG_FILE):
        return

    log_levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    start_time = datetime.now() - timedelta(days=7)
    
    with open(LOG_FILE, "w") as f:
        for _ in range(1000):
            level = random.choices(log_levels, weights=[60, 20, 15, 5])[0]
            timestamp = start_time + timedelta(seconds=random.randint(0, 7 * 24 * 3600))
            messages = {
                "INFO": f"User {random.randint(1000,9999)} accessed resource /page/{random.randint(1,20)}",
                "WARN": f"High response time detected for endpoint /api/v1/data/{random.randint(1,50)}",
                "ERROR": f"Database connection timeout for query ID {random.randint(10000,99999)}",
                "CRITICAL": f"System failure in module XYZ: Unable to recover process {random.randint(100,999)}"
            }
            log_entry = f"{timestamp.isoformat()} [{level}] {messages[level]}\n"
            f.write(log_entry)
    print(f"Generated {LOG_FILE} with 1000 fake log entries.")

# Parse log file and extract analytics
@lru_cache(maxsize=1)
def parse_logs():
    if not os.path.exists(LOG_FILE):
        return {}, {}, []

    log_pattern = re.compile(r'(\S+T\S+)\s+\[(\w+)\]\s+(.+)')
    level_counter = Counter()
    errors_per_hour = defaultdict(int)
    critical_errors = []

    with open(LOG_FILE, "r") as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except ValueError:
                    continue

                level_counter[level] += 1

                if level in ["ERROR", "CRITICAL"]:
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    errors_per_hour[hour_key] += 1

                if level == "CRITICAL":
                    critical_errors.append({
                        "timestamp": timestamp_str,
                        "message": message
                    })

    return dict(level_counter), dict(errors_per_hour), critical_errors

# HTTP Request Handler
class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self.get_dashboard_html().encode())
        elif url.path == "/data":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            level_counts, errors_per_hour, critical_errors = parse_logs()
            data = {
                "level_counts": level_counts,
                "errors_per_hour": errors_per_hour,
                "critical_errors": critical_errors
            }
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_error(404)

    def get_dashboard_html(self):
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Log Analytics Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 8px; }
        .flex { display: flex; gap: 20px; }
        .flex > div { flex: 1; }
        h2 { margin-top: 0; color: #333; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; cursor: pointer; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .search-box { width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .filter { margin-bottom: 10px; }
        .bar-chart { display: flex; align-items: flex-end; height: 150px; gap: 2px; }
        .bar { background-color: #3498db; flex: 1; text-align: center; color: white; font-size: 12px; overflow: hidden; }
        .bar-label { font-size: 10px; margin-top: 5px; color: #666; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .pie-chart { width: 200px; height: 200px; border-radius: 50%; background: conic-gradient(
            from 0deg,
            var(--colors)
        ); margin: 20px auto; }
        .legend { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
        .legend-item { display: flex; align-items: center; }
        .legend-color { width: 16px; height: 16px; margin-right: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Log Analytics Dashboard</h1>

        <div class="card">
            <h2>Log Level Distribution</h2>
            <div class="flex">
                <div>
                    <div class="pie-chart" id="pie-chart"></div>
                    <div class="legend" id="legend"></div>
                </div>
                <div>
                    <table id="level-table">
                        <tr><th>Level</th><th>Count</th><th>Percentage</th></tr>
                    </table>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Errors Per Hour (Timeline)</h2>
            <div class="bar-chart" id="error-bar-chart"></div>
        </div>

        <div class="card">
            <h2>CRITICAL Errors <span id="error-count"></span></h2>
            <input type="text" class="search-box" id="search" placeholder="Search critical errors...">
            <div class="filter">
                <label><input type="radio" name="level-filter" value="all" checked> All</label>
                <label><input type="radio" name="level-filter" value="ERROR"> ERROR</label>
                <label><input type="radio" name="level-filter" value="CRITICAL"> CRITICAL</label>
            </div>
            <table id="critical-table">
                <tr><th>Timestamp</th><th>Message</th></tr>
            </table>
        </div>
    </div>

    <script>
        const colors = {
            'INFO': '#2ecc71',
            'WARN': '#f39c12',
            'ERROR': '#e74c3c',
            'CRITICAL': '#c0392b'
        };

        let rawData = {};
        let filteredCriticals = [];
        let currentFilter = 'all';

        // Fetch data
        fetch('/data')
            .then(res => res.json())
            .then(data => {
                rawData = data;
                filteredCriticals = data.critical_errors;
                updateDashboard();
            });

        function updateDashboard() {
            updateLevelCharts();
            updateErrorTimeline();
            updateCriticalTable();
            updateErrorCount();
        }

        function updateLevelCharts() {
            const counts = rawData.level_counts;
            const total = Object.values(counts).reduce((a, b) => a + b, 0);

            // Create pie chart gradient
            let start = 0;
            let gradient = [];
            const legendEl = document.getElementById('legend');
            legendEl.innerHTML = '';

            Object.entries(counts).forEach(([level, count]) => {
                const percentage = total ? (count / total) * 100 : 0;
                const end = start + (percentage / 100) * 360;
                gradient.push(`${colors[level]} ${start}deg ${end}deg`);
                start = end;

                // Update table
                const row = document.createElement('tr');
                row.innerHTML = `<td>${level}</td><td>${count}</td><td>${percentage.toFixed(1)}%</td>`;
                document.getElementById('level-table').appendChild(row);

                // Add legend
                const legendItem = document.createElement('div');
                legendItem.className = 'legend-item';
                legendItem.innerHTML = `
                    <div class="legend-color" style="background-color: ${colors[level]}"></div>
                    ${level}
                `;
                legendEl.appendChild(legendItem);
            });

            document.getElementById('pie-chart').style.setProperty('--colors', gradient.join(', '));
        }

        function updateErrorTimeline() {
            const container = document.getElementById('error-bar-chart');
            container.innerHTML = '';

            const errors = rawData.errors_per_hour;
            const hours = Object.keys(errors).sort();
            const maxErrors = Math.max(...Object.values(errors), 1);

            hours.forEach(hour => {
                const height = (errors[hour] / maxErrors) * 100;
                const bar = document.createElement('div');
                bar.className = 'bar';
                bar.style.height = `${height}%`;
                bar.title = `${hour}: ${errors[hour]} errors`;
                bar.innerHTML = `<div class="bar-label">${hour.split(' ')[1]}</div>`;
                container.appendChild(bar);
            });
        }

        function updateCriticalTable() {
            const table = document.getElementById('critical-table');
            // Keep header
            while (table.rows.length > 1) {
                table.deleteRow(1);
            }

            filteredCriticals.forEach(error => {
                const row = table.insertRow();
                row.insertCell(0).textContent = new Date(error.timestamp).toLocaleString();
                row.insertCell(1).textContent = error.message;
            });
        }

        function updateErrorCount() {
            document.getElementById('error-count').textContent = 
                `(${filteredCriticals.length} entries)`;
        }

        // Search and filter
        document.getElementById('search').addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            filteredCriticals = rawData.critical_errors.filter(err => 
                err.message.toLowerCase().includes(query)
            );
            applyFilter();
        });

        document.querySelectorAll('input[name="level-filter"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                currentFilter = e.target.value;
                applyFilter();
            });
        });

        function applyFilter() {
            if (currentFilter === 'all') {
                // Already filtered by search
            } else if (currentFilter === 'ERROR') {
                // For demo, show CRITICAL when ERROR selected
                filteredCriticals = rawData.critical_errors;
            } else if (currentFilter === 'CRITICAL') {
                filteredCriticals = rawData.critical_errors;
            }
            updateCriticalTable();
            updateErrorCount();
        }
    </script>
</body>
</html>
        """

# Main execution
def main():
    generate_log_file()
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, DashboardHandler)
    print("Log Analytics Dashboard is running at http://localhost:8000")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == "__main__":
    main()