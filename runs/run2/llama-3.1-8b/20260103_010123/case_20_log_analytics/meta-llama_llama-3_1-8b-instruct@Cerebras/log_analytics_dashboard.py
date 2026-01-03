import os
import http.server
import json
import collections
from datetime import datetime, timedelta
import random

# Generate fake log data if server.log is missing
def generate_fake_log_data():
    log_data = []
    for _ in range(1000):
        level = random.choice(['INFO', 'WARN', 'ERROR', 'CRITICAL'])
        timestamp = datetime.now() - timedelta(seconds=random.randint(0, 86400))
        message = f"{level} - {random.choice(['app', 'service'])} - {random.choice(['error', 'warning'])}"
        log_data.append((level, timestamp.strftime("%Y-%m-%d %H:%M:%S"), message))
    return log_data

# Parse log file
def parse_log_file(filename):
    log_data = []
    with open(filename, 'r') as f:
        for line in f:
            level, timestamp, message = line.strip().split(' - ')
            log_data.append((level, timestamp, message))
    return log_data

# Calculate statistics
def calculate_statistics(log_data):
    log_levels = collections.Counter(x[0] for x in log_data)
    errors_per_hour = collections.defaultdict(int)
    for level, timestamp, _ in log_data:
        if level in ['ERROR', 'CRITICAL']:
            errors_per_hour[timestamp] += 1
    return log_levels, errors_per_hour

# Launch HTTP server
class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open('dashboard.html', 'r') as f:
            self.wfile.write(f.read())

# Main script
def main():
    filename = 'server.log'
    if not os.path.exists(filename):
        log_data = generate_fake_log_data()
        with open(filename, 'w') as f:
            for level, timestamp, message in log_data:
                f.write(f"{level} - {timestamp} - {message}\n")
    log_data = parse_log_file(filename)
    log_levels, errors_per_hour = calculate_statistics(log_data)
    critical_errors = [x for x in log_data if x[0] == 'CRITICAL']

    with open('dashboard.html', 'w') as f:
        f.write("""
        <html>
        <head>
        <title>Log Analytics Dashboard</title>
        <style>
        /* Add some basic styling */
        body { font-family: Arial, sans-serif; }
        table { border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        </style>
        </head>
        <body>
        <h1>Log Analytics Dashboard</h1>
        <p><a href="?level=All">All</a> | <a href="?level=Error">Error</a> | <a href="?level=Alert">Alert</a></p>
        <svg id="log-level-chart" width="400" height="200"></svg>
        <svg id="errors-per-hour-chart" width="400" height="200"></svg>
        <table id="critical-errors-table">
        <tr><th>Error Message</th><th>Timestamp</th></tr>
        """)
        for critical_error in critical_errors:
            timestamp = critical_error[1]
            message = critical_error[2]
            f.write(f"""
            <tr><td>{message}</td><td>{timestamp}</td></tr>
            """)
        f.write("""
        </table>
        <script>
        // Update charts and table on URL change
        var urlParams = new URLSearchParams(window.location.search);
        var level = urlParams.get('level');
        if (level === 'All') {
            // Update charts and table for all levels
            // ...
        } else if (level === 'Error') {
            // Update charts and table for Error level
            // ...
        } else if (level === 'Alert') {
            // Update charts and table for Alert level
            // ...
        }
        </script>
        </body>
        </html>
        """)

    print(f"Server running at http://localhost:8000")
    with http.server.HTTPServer(("", 8000), DashboardHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    main()