import http.server
import json
import os
import collections
import random
import socket
import struct
import time
from urllib.parse import urlparse

# Function to generate fake log data
def generate_fake_log_data():
    levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    log_messages = [
        "Operation successful",
        "Connection timeout",
        "Resource not found",
        "Invalid credentials",
        "System error",
        "File not found",
        "Permission denied",
    ]
    with open("server.log", "w") as f:
        for _ in range(1000):
            level = random.choice(levels)
            message = random.choice(log_messages)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} {level} {message}\n")

# Function to parse log file and extract required data
def parse_log_file():
    errors_per_hour = {}
    log_levels = collections.defaultdict(int)
    critical_errors = []
    with open("server.log", "r") as f:
        for line in f:
            timestamp, level, message = line.strip().split(" ", 2)
            log_levels[level] += 1
            if level == "CRITICAL":
                critical_errors.append((timestamp, message))
            hour = int(timestamp[:2])
            if hour not in errors_per_hour:
                errors_per_hour[hour] = []
            errors_per_hour[hour].append((timestamp, message))
    return (
        log_levels,
        errors_per_hour,
        collections.Counter(error[1] for error in critical_errors),
    )

# Function to launch local HTTP server
class Dashboard(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                """<html>
                <head>
                <title>Log Analytics Dashboard</title>
                <style>
                body { font-family: Arial, sans-serif; }
                table { border-collapse: collapse; width: 80%; }
                th, td { border: 1px solid black; padding: 5px; }
                .graph { width: 100%; height: 200px; }
                </style>
                </head>
                <body>
                <h1>Log Analytics Dashboard</h1>
                <form action="/filter" method="get">
                <label>Filter by level:</label>
                <select name="level">
                <option value="">All</option>
                <option value="ERROR">Error</option>
                <option value="CRITICAL">Alert</option>
                </select>
                <input type="submit" value="Filter">
                </form>
                <table>
                <tr><th>Timestamp</th><th>Level</th><th>Message</th></tr>
                {% for error in errors %}
                <tr><td>{{ error[0] }}</td><td>{{ error[1] }}</td><td>{{ error[2] }}</td></tr>
                {% endfor %}
                </table>
                <div class="graph">
                <svg width="100%" height="200">
                <rect x="0" y="0" width="100%" height="100%" fill="#ccc" rx="10" />
                {% for level in log_levels %}
                <rect x="5" y="{{ 200 - log_levels[level] * 5 }}" width="20" height="{{ log_levels[level] * 5 }}" fill="#{{ 'FF0000' if level == 'CRITICAL' else 'FFFF00' if level == 'ERROR' else '00FF00' if level == 'INFO' else '0000FF' }}" rx="5" />
                <text x="25" y="{{ 200 - log_levels[level] * 5 + 10 }}">{{ level }}</text>
                {% endfor %}
                </svg>
                </div>
                <script>
                function filterByLevel() {
                var level = document.querySelector("select[name='level']").value;
                var errors = document.querySelector("table tr");
                if (level == "") {
                errors.style.display = "";
                } else {
                errors.style.display = "none";
                }
                var levelElements = document.querySelectorAll(".level-" + level);
                levelElements.forEach(function(element) {
                element.style.display = "";
                });
                }
                document.querySelector("form").addEventListener("submit", function(event) {
                event.preventDefault();
                filterByLevel();
                });
                </script>
                </body>
                </html>
                """
            )
        elif parsed_url.path == "/filter":
            level = parsed_url.query.get("level")
            errors = []
            with open("server.log", "r") as f:
                for line in f:
                    timestamp, level_name, message = line.strip().split(" ", 2)
                    if level_name == level or level == "":
                        errors.append((timestamp, level_name, message))
            return self.send_response(200), self.send_header("Content-type", "text/html"), self.end_headers(), self.wfile.write(
                f"""
                <html>
                <head>
                <title>Filtered Log Data</title>
                </head>
                <body>
                <h1>Filtered Log Data</h1>
                <table>
                <tr><th>Timestamp</th><th>Level</th><th>Message</th></tr>
                {% for error in errors %}
                <tr><td>{{ error[0] }}</td><td class="level-{error[1]}"> {{ error[1] }} </td><td>{{ error[2] }}</td></tr>
                {% endfor %}
                </table>
                </body>
                </html>
                """
            )
        elif parsed_url.path == "/errors":
            critical_errors = []
            with open("server.log", "r") as f:
                for line in f:
                    timestamp, level, message = line.strip().split(" ", 2)
                    if level == "CRITICAL":
                        critical_errors.append((timestamp, message))
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(critical_errors).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/errors":
            content_length = int(self.headers["Content-Length"])
            error_message = self.rfile.read(content_length).decode()
            with open("server.log", "a") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " CRITICAL " + error_message + "\n")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

# Main function
if __name__ == "__main__":
    socket_address = ("", 8000)
    server_address = ("", 8000)
    httpd = http.server.HTTPServer(server_address, Dashboard)
    print("Server started at http://localhost:8000")
    generate_fake_log_data()
    log_levels, errors_per_hour, critical_errors = parse_log_file()
    httpd.serve_forever()