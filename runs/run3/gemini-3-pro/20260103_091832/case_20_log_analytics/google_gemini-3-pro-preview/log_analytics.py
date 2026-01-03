import http.server
import socketserver
import os
import random
import datetime
import re
import json
import sys
from collections import Counter, defaultdict

LOG_FILE = "server.log"
PORT = 8000

def generate_logs_if_missing():
    if os.path.exists(LOG_FILE):
        print(f"Using existing {LOG_FILE}")
        return

    print(f"Generating fake log data in {LOG_FILE}...")
    levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    messages = {
        "INFO": ["User logged in", "Health check passed", "Data synced", "Job started", "Cache refreshed"],
        "WARN": ["High memory usage", "Response time slow", "Disk space low", "API deprecated", "Retrying connection"],
        "ERROR": ["Connection refused", "Timeout waiting for DB", "NullPointer Exception", "File not found", "Payment gateway error"],
        "CRITICAL": ["System crash", "Data corruption detected", "Security breach attempt", "Service down", "Database deadlock"]
    }
    
    now = datetime.datetime.now()
    logs = []
    # Generate 1000 lines scattered over last 24 hours
    for _ in range(1000):
        dt = now - datetime.timedelta(minutes=random.randint(0, 24*60))
        # Weighted distribution
        lvl = random.choices(levels, weights=[50, 30, 15, 5])[0]
        msg = random.choice(messages[lvl])
        ts = dt.strftime("%Y-%m-%d %H:%M:%S")
        logs.append(f"[{ts}] {lvl}: {msg}")
    
    logs.sort() # Sort by timestamp
    with open(LOG_FILE, "w") as f:
        f.write("\n".join(logs))
    print("Log generation complete.")

def parse_logs():
    stats = {
        "level_counts": Counter(),
        "timeline": defaultdict(int),
        "error_messages": Counter(),
        "all_logs": []
    }
    
    # Regex: [2023-10-27 10:00:00] LEVEL: Message
    pattern = re.compile(r"\[(.*?)\] (\w+): (.*)")
    
    if not os.path.exists(LOG_FILE):
        return stats

    with open(LOG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            match = pattern.match(line)
            if match:
                ts_str, level, msg = match.groups()
                
                # Add to all logs
                stats["all_logs"].append({
                    "timestamp": ts_str,
                    "level": level,
                    "message": msg
                })
                
                # Count levels
                stats["level_counts"][level] += 1
                
                # For timeline and common errors, only count ERROR and CRITICAL
                if level in ["ERROR", "CRITICAL"]:
                    try:
                        # Group by hour
                        dt = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                        hour_key = dt.strftime("%Y-%m-%d %H:00")
                        stats["timeline"][hour_key] += 1
                        stats["error_messages"][msg] += 1
                    except ValueError:
                        pass
    
    # Format data for JSON response
    # 1. Timeline sorted by time
    sorted_timeline = [{"hour": k, "count": v} for k, v in sorted(stats["timeline"].items())]
    
    # 2. Top errors
    top_errors = [{"message": k, "count": v} for k, v in stats["error_messages"].most_common(5)]
    
    return {
        "levels": dict(stats["level_counts"]),
        "timeline": sorted_timeline,
        "top_errors": top_errors,
        "logs": stats["all_logs"]
    }

class LogHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            if os.path.exists("index.html"):
                with open("index.html", "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b"index.html not found")
        
        elif self.path == "/api/data":
            data = parse_logs()
            json_data = json.dumps(data)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json_data.encode('utf-8'))
            
        else:
            # Fallback to default behavior (serving other static files if needed)
            super().do_GET()

if __name__ == "__main__":
    generate_logs_if_missing()
    
    print(f"Starting Dashboard at http://localhost:{PORT}")
    print("Press Ctrl+C to stop.")
    
    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), LogHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            sys.exit(0)