import os
import random
import datetime
import json
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from collections import Counter, defaultdict

LOG_FILE = "server.log"
LEVELS = ['INFO', 'WARN', 'ERROR', 'CRITICAL']
ERROR_LEVELS = ['ERROR', 'CRITICAL']

# Generate 1000 lines of fake log data
def generate_logs():
    with open(LOG_FILE, 'w') as f:
        now = datetime.datetime.now()
        for _ in range(1000):
            level = random.choices(LEVELS, weights=[0.5, 0.2, 0.2, 0.1])[0]
            time = now - datetime.timedelta(minutes=random.randint(0, 1440))
            message = f"{level} - {time.strftime('%Y-%m-%d %H:%M:%S')} - " \
                      f"{generate_message(level)}"
            f.write(message + "\n")

def generate_message(level):
    base_messages = {
        'INFO': ['User logged in', 'Data synced', 'Heartbeat received'],
        'WARN': ['Disk usage high', 'Memory usage nearing limit'],
        'ERROR': ['Connection timeout', 'Service unavailable', 'DB error occurred'],
        'CRITICAL': ['System crash', 'Data loss detected', 'Security breach']
    }
    return random.choice(base_messages[level])

# Parse the log file
def parse_logs():
    level_counter = Counter()
    errors_per_hour = defaultdict(int)
    error_messages = Counter()
    critical_entries = []

    with open(LOG_FILE, 'r') as f:
        for line in f:
            parts = line.strip().split(' - ')
            if len(parts) != 3:
                continue
            level, timestamp_str, message = parts
            level_counter[level] += 1

            if level in ERROR_LEVELS:
                try:
                    timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                    errors_per_hour[hour_key] += 1
                    error_messages[message] += 1
                except ValueError:
                    continue

            if level == 'CRITICAL':
                critical_entries.append({'timestamp': timestamp_str, 'message': message})

    total = sum(level_counter.values())
    level_percentages = {k: round((v / total) * 100, 2) for k, v in level_counter.items()}

    return {
        'level_percentages': level_percentages,
        'errors_per_hour': dict(sorted(errors_per_hour.items())),
        'common_errors': error_messages.most_common(10),
        'critical_entries': critical_entries
    }

# Serve HTTP with dashboard
class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/data':
            data = parse_logs()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        else:
            if self.path == '/':
                self.path = '/dashboard.html'
            return super().do_GET()

def run_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, DashboardHandler)
    print("Serving dashboard at http://localhost:8000")
    httpd.serve_forever()

if __name__ == '__main__':
    if not os.path.exists(LOG_FILE):
        print("Generating log file...")
        generate_logs()
    run_server()