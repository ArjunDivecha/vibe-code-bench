import http.server
import socketserver
import json
import os
import random
import datetime
import re
from collections import Counter, defaultdict
import sys
import time

LOG_FILE = "server.log"

def generate_logs_if_missing():
    """Generates fake log data if server.log does not exist."""
    if os.path.exists(LOG_FILE):
        print(f"[{LOG_FILE}] found. Using existing logs.")
        return

    print(f"[{LOG_FILE}] missing. Generating 1000 lines of fake data...")
    
    levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    weights = [0.65, 0.20, 0.12, 0.03] 
    
    messages = {
        "INFO": [
            "User login successful", 
            "Job processing started", 
            "Health check passed", 
            "Cache refreshed", 
            "Request served successfully",
            "Background task initiated"
        ],
        "WARN": [
            "High memory usage detected", 
            "Response time > 500ms", 
            "Disk space low (85%)", 
            "API rate limit approaching",
            "Deprecated configuration used"
        ],
        "ERROR": [
            "Database connection timeout", 
            "NullPointerException in handler", 
            "File write permission denied", 
            "Payment gateway unavailable",
            "External service 502 Bad Gateway"
        ],
        "CRITICAL": [
            "Security breach detected: SQL Injection", 
            "Data corruption in block 42", 
            "Main service process crashed", 
            "Firewall disabled unexpectedly",
            "Root partition full"
        ]
    }
    
    current_time = datetime.datetime.now() - datetime.timedelta(hours=24)
    
    with open(LOG_FILE, "w") as f:
        for _ in range(1000):
            current_time += datetime.timedelta(seconds=random.randint(1, 180))
            
            level = random.choices(levels, weights=weights)[0]
            base_msg = random.choice(messages[level])
            
            # Add variation to message but keep base for counting? 
            # The prompt asks for "Most common error messages". 
            # If I add random IDs, exact grouping fails unless I strip them.
            # I'll append ID at the end and use regex to strip it for counting.
            
            variation = ""
            if random.random() > 0.7:
                variation = f" [ReqID:{random.randint(10000,99999)}]"
            
            line = f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] {level}: {base_msg}{variation}\n"
            f.write(line)
            
    print("Log generation complete.")

def parse_logs():
    """Parses the log file and returns statistics and data."""
    stats = {
        "level_counts": Counter(),
        "errors_per_hour": defaultdict(int),
        "all_logs": [],
        "error_messages": Counter()
    }
    
    log_pattern = re.compile(r"^\[(.*?)\] (\w+): (.*)$")
    # Regex to strip the random ID we added for cleaner grouping
    id_pattern = re.compile(r" \[ReqID:\d+\]$")
    
    if not os.path.exists(LOG_FILE):
        return stats

    with open(LOG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            match = log_pattern.match(line)
            if match:
                ts_str, level, msg = match.groups()
                
                stats["level_counts"][level] += 1
                
                if level in ["ERROR", "CRITICAL"]:
                    # Timeline
                    try:
                        hour_key = ts_str[:13] 
                        stats["errors_per_hour"][hour_key] += 1
                    except: pass
                    
                    # Common messages (clean up ID)
                    clean_msg = id_pattern.sub("", msg)
                    stats["error_messages"][clean_msg] += 1
                
                stats["all_logs"].append({
                    "timestamp": ts_str,
                    "level": level,
                    "message": msg
                })
    
    stats["all_logs"].reverse()
    return stats

class LogHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            try:
                with open("index.html", "rb") as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.wfile.write(b"index.html not found")
                
        elif self.path == "/api/data":
            data = parse_logs()
            
            response_data = {
                "level_counts": dict(data["level_counts"]),
                "errors_per_hour": dict(data["errors_per_hour"]),
                "top_errors": data["error_messages"].most_common(5),
                "all_logs": data["all_logs"]
            }
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            
        else:
            super().do_GET()

def run_server(port=8000):
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), LogHandler) as httpd:
        print(f"Starting dashboard at http://localhost:{port}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")

if __name__ == "__main__":
    generate_logs_if_missing()
    run_server()