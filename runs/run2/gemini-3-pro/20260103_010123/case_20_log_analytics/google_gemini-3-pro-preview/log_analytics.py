import http.server
import socketserver
import json
import os
import random
import datetime
import collections
import re
import sys
import webbrowser
from threading import Timer

LOG_FILE = "server.log"
PORT = 8000

# --- Log Generation ---
def generate_logs_if_missing():
    if os.path.exists(LOG_FILE):
        print(f"[{LOG_FILE}] exists. Skipping generation.")
        return

    print(f"[{LOG_FILE}] missing. Generating 1000 lines of fake data...")
    levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    weights = [0.6, 0.2, 0.15, 0.05]
    
    messages = {
        "INFO": ["User logged in", "Health check passed", "Job started", "Job finished", "Cache refreshed"],
        "WARN": ["High memory usage", "Response time slow", "Disk space low", "Deprecated API usage"],
        "ERROR": ["Database connection failed", "Timeout waiting for service", "NullPointerException", "File not found"],
        "CRITICAL": ["System crash", "Data corruption detected", "Security breach attempt", "Main process terminated"]
    }

    start_time = datetime.datetime.now() - datetime.timedelta(hours=48)
    logs = []

    for _ in range(1000):
        # Random time within the last 48 hours
        dt = start_time + datetime.timedelta(seconds=random.randint(0, 48*3600))
        level = random.choices(levels, weights=weights)[0]
        msg = random.choice(messages[level])
        
        # Add some random IDs to make messages distinct for grouping logic test
        if random.random() > 0.5:
            msg += f" [ID:{random.randint(1000, 9999)}]"
            
        logs.append((dt, level, msg))

    # Sort by time
    logs.sort(key=lambda x: x[0])

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for dt, level, msg in logs:
            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {level}: {msg}\n")
    
    print("Generation complete.")

# --- Log Parsing ---
def parse_logs():
    if not os.path.exists(LOG_FILE):
        return {}

    log_pattern = re.compile(r"^\[(.*?)\] (\w+): (.*)$")
    
    stats = {
        "levels": collections.Counter(),
        "errors_per_hour": collections.Counter(),
        "common_errors": collections.Counter(),
        "logs": [] 
    }

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                ts_str, level, msg = match.groups()
                stats["levels"][level] += 1
                
                # Keep raw log for table (limit payload if necessary, but 1000 is fine)
                stats["logs"].append({
                    "timestamp": ts_str,
                    "level": level,
                    "message": msg
                })

                # Stats for charts
                if level in ["ERROR", "CRITICAL"]:
                    # Extract base message (remove ID for grouping)
                    base_msg = re.sub(r" \[ID:\d+\]", "", msg)
                    stats["common_errors"][base_msg] += 1
                    
                    # Hourly timeline
                    try:
                        dt = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                        hour_key = dt.strftime("%Y-%m-%d %H:00")
                        stats["errors_per_hour"][hour_key] += 1
                    except ValueError:
                        pass

    # Format for JSON
    return {
        "level_counts": dict(stats["levels"]),
        "errors_timeline": [{"hour": k, "count": v} for k, v in sorted(stats["errors_per_hour"].items())],
        "top_errors": [{"message": k, "count": v} for k, v in stats["common_errors"].most_common(5)],
        "all_logs": stats["logs"]
    }

# --- HTTP Server ---
class LogRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            data = parse_logs()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        else:
            # Serve static files (index.html)
            super().do_GET()

def open_browser():
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == "__main__":
    generate_logs_if_missing()
    
    # Ensure index.html exists in current dir (it should be created by the user/AI instructions)
    if not os.path.exists("index.html"):
        print("Warning: index.html not found. Dashboard will not load correctly.")

    print(f"Starting server at http://localhost:{PORT}")
    
    # Timer to open browser automatically
    t = Timer(1.0, open_browser)
    t.start()

    with socketserver.TCPServer(("", PORT), LogRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.shutdown()