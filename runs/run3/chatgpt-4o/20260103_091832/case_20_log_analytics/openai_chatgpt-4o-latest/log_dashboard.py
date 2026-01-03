import os
import sys
import json
import random
import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import Counter, defaultdict
from urllib.parse import urlparse, parse_qs

LOG_FILE = "server.log"
LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]
ERROR_LEVELS = ["ERROR", "CRITICAL"]
SAMPLE_MESSAGES = {
    "INFO": [
        "User logged in",
        "Scheduled job executed",
        "Data synced successfully"
    ],
    "WARN": [
        "Disk space low",
        "High memory usage detected",
        "Slow response time"
    ],
    "ERROR": [
        "Database connection failed",
        "File not found",
        "Unable to reach external API"
    ],
    "CRITICAL": [
        "System crash",
        "Data corruption detected",
        "Security breach detected"
    ]
}

def generate_fake_logs():
    now = datetime.datetime.now()
    with open(LOG_FILE, "w") as f:
        for _ in range(1000):
            delta_minutes = random.randint(0, 60 * 24 * 5)  # random time in last 5 days
            timestamp = now - datetime.timedelta(minutes=delta_minutes)
            level = random.choices(LEVELS, weights=[0.5, 0.2, 0.2, 0.1])[0]
            message = random.choice(SAMPLE_MESSAGES[level])
            line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {level} - {message}\n"
            f.write(line)

def parse_logs():
    level_counts = Counter()
    errors_per_hour = defaultdict(int)
    error_messages = Counter()
    critical_errors = []

    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                timestamp_str, rest = line.strip().split(" - ", 1)
                level, message = rest.split(" - ", 1)
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                level = level.strip()
                message = message.strip()
                level_counts[level] += 1
                if level in ERROR_LEVELS:
                    hour = timestamp.replace(minute=0, second=0, microsecond=0)
                    errors_per_hour[hour.isoformat()] += 1
                    error_messages[message] += 1
                if level == "CRITICAL":
                    critical_errors.append({
                        "timestamp": timestamp_str,
                        "message": message
                    })
            except Exception as e:
                continue

    total = sum(level_counts.values())
    level_percentages = {level: round((count / total) * 100, 2) for level, count in level_counts.items()}
    top_errors = error_messages.most_common(5)

    return {
        "level_percentages": level_percentages,
        "errors_per_hour": dict(errors_per_hour),
        "top_errors": top_errors,
        "critical_errors": critical_errors
    }

class DashboardHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type="text/html"):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == "/":
            self._set_headers()
            with open("dashboard.html", "r") as f:
                self.wfile.write(f.read().encode())
        elif parsed_path.path == "/data":
            self._set_headers("application/json")
            data = parse_logs()
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_error(404)

def run_server(port=8000):
    print(f"Starting server at http://localhost:{port}")
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        print("Log file not found. Generating fake logs...")
        generate_fake_logs()
    run_server()