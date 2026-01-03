#!/usr/bin/env python3
"""
Log Analytics Dashboard
A local HTTP server that serves an interactive log analysis dashboard.
"""

import http.server
import json
import os
import random
import socketserver
import threading
import time
from collections import Counter
from datetime import datetime, timedelta
from html import escape
from urllib.parse import parse_qs, urlparse

PORT = 8000
LOG_FILE = "server.log"

# Fake log data templates
LOG_TEMPLATES = {
    "INFO": [
        "User {user} logged in successfully",
        "Cache refreshed for key: {key}",
        "API request completed in {ms}ms",
        "Database connection pool status: {status}",
        "Background job {job} started",
        "Session established for user {user}",
        "File {file} uploaded successfully",
        "Configuration reloaded",
        "Health check passed",
        "Service {service} is healthy"
    ],
    "WARN": [
        "High memory usage detected: {percent}%",
        "Slow query detected: {ms}ms",
        "Rate limit approaching for user {user}",
        "Disk space low: {percent}% remaining",
        "Deprecated API endpoint accessed",
        "Retry attempt {attempt} for job {job}",
        "Connection pool at {percent}% capacity",
        "Cache miss rate increased to {percent}%",
        "Authentication token expiring soon",
        "Invalid request parameter: {param}"
    ],
    "ERROR": [
        "Failed to connect to database: {error}",
        "API request failed with status {code}: {error}",
        "File {file} not found",
        "Authentication failed for user {user}",
        "Background job {job} failed: {error}",
        "External service timeout: {service}",
        "Invalid data format in request",
        "Permission denied for operation",
        "Configuration error: {error}",
        "Memory allocation failed"
    ],
    "CRITICAL": [
        "System out of memory - OOM killer activated",
        "Database connection pool exhausted",
        "Primary server unreachable",
        "Disk failure imminent: {error}",
        "Security breach detected from IP {ip}",
        "Service {service} completely unresponsive",
        "Data corruption detected in {table}",
        "SSL certificate validation failed",
        "Kernel panic detected",
        "RAID array degradation critical"
    ]
}

USERS = ["alice", "bob", "charlie", "dave", "eve", "frank", "grace", "henry"]
SERVICES = ["auth", "payment", "notification", "analytics", "storage", "api"]
KEYS = ["user_session", "config_v1", "cache_main", "metrics", "queue_state"]
JOBS = ["cleanup", "backup", "sync", "index", "report"]


def generate_fake_logs():
    """Generate 1000 lines of fake log data."""
    logs = []
    start_time = datetime.now() - timedelta(hours=24)
    
    for i in range(1000):
        # Random timestamp within the last 24 hours
        timestamp = start_time + timedelta(seconds=random.randint(0, 86400))
        
        # Choose log level with weighted probabilities
        level = random.choices(
            ["INFO", "WARN", "ERROR", "CRITICAL"],
            weights=[50, 25, 20, 5]
        )[0]
        
        # Get random template and fill in placeholders
        template = random.choice(LOG_TEMPLATES[level])
        log_entry = template.format(
            user=random.choice(USERS),
            key=random.choice(KEYS),
            ms=random.randint(1, 5000),
            status=random.choice(["healthy", "degraded", "busy"]),
            job=random.choice(JOBS),
            file=f"/var/log/app_{random.choice(['access', 'error', 'debug'])}.log",
            service=random.choice(SERVICES),
            percent=random.randint(10, 99),
            param=f"param_{random.randint(1, 10)}",
            error=random.choice(["connection refused", "timeout", "invalid credentials", "resource unavailable"]),
            code=random.choice(["400", "401", "403", "404", "500", "502", "503"]),
            table=f"users_{random.randint(1, 5)}",
            ip=f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            attempt=random.randint(1, 5)
        )
        
        # Format: [TIMESTAMP] LEVEL Message
        logs.append(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {log_entry}")
    
    # Shuffle logs so they're not sorted by level
    random.shuffle(logs)
    
    # Sort by timestamp
    logs.sort(key=lambda x: x.split("]")[0].strip("["))
    
    with open(LOG_FILE, "w") as f:
        f.write("\n".join(logs))
    
    print(f"Generated {len(logs)} log entries in {LOG_FILE}")


def parse_log_file():
    """Parse the log file and return structured data."""
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
    
    logs = []
    level_counts = Counter()
    errors_by_hour = Counter()
    error_messages = Counter()
    critical_errors = []
    
    with open(LOG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Parse log line format: [TIMESTAMP] [LEVEL] Message
            try:
                # Extract timestamp
                timestamp_str = line.split("]")[0].strip("[")
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                # Extract level
                level = line.split("]")[1].strip("[] ")
                
                # Extract message
                message = "]".join(line.split("]")[2:]).strip()
                
                log_entry = {
                    "timestamp": timestamp.isoformat(),
                    "level": level,
                    "message": message
                }
                
                logs.append(log_entry)
                level_counts[level] += 1
                
                # Track errors per hour
                if level in ["ERROR", "CRITICAL"]:
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    errors_by_hour[hour_key] += 1
                
                # Track error messages
                if level in ["ERROR", "CRITICAL"]:
                    error_messages[message] += 1
                
                # Store critical errors
                if level == "CRITICAL":
                    critical_errors.append(log_entry)
                    
            except (ValueError, IndexError):
                continue
    
    return {
        "logs": logs,
        "level_counts": dict(level_counts),
        "errors_by_hour": dict(sorted(errors_by_hour.items())),
        "error_messages": dict(error_messages.most_common(10)),
        "critical_errors": critical_errors
    }


def calculate_percentages(level_counts):
    """Calculate percentage of each log level."""
    total = sum(level_counts.values())
    percentages = {}
    for level, count in level_counts.items():
        percentages[level] = round((count / total) * 100, 2)
    return percentages


def generate_dashboard_html(data):
    """Generate the complete HTML dashboard."""
    level_counts = data["level_counts"]
    percentages = calculate_percentages(level_counts)
    errors_by_hour = data["errors_by_hour"]
    error_messages = data["error_messages"]
    critical_errors = data["critical_errors"]
    
    # Prepare timeline data for SVG
    if errors_by_hour:
        hours = sorted(errors_by_hour.keys())
        max_errors = max(errors_by_hour.values())
        hour_values = [errors_by_hour[h] for h in hours]
    else:
        hours = []
        hour_values = []
        max_errors = 1
    
    # Color scheme
    colors = {
        "INFO": "#28a745",
        "WARN": "#ffc107",
        "ERROR": "#dc3545",
        "CRITICAL": "#6f42c1"
    }
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log Analytics Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 2.5rem;
            color: #fff;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #888;
            font-size: 1rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #fff;
        }}
        
        .stat-label {{
            color: #888;
            margin-top: 5px;
        }}
        
        .level-info {{ color: #28a745; }}
        .level-warn {{ color: #ffc107; }}
        .level-error {{ color: #dc3545; }}
        .level-critical {{ color: #6f42c1; }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        @media (max-width: 900px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .chart-card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .chart-title {{
            font-size: 1.2rem;
            margin-bottom: 20px;
            color: #fff;
        }}
        
        .donut-chart {{
            width: 200px;
            height: 200px;
            margin: 0 auto;
            position: relative;
        }}
        
        .legend {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }}
        
        .timeline-svg {{
            width: 100%;
            height: 200px;
        }}
        
        .error-messages {{
            margin-bottom: 30px;
        }}
        
        .message-list {{
            list-style: none;
            max-height: 300px;
            overflow-y: auto;
        }}
        
        .message-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px 15px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 3px solid #dc3545;
        }}
        
        .message-text {{
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-right: 15px;
        }}
        
        .message-count {{
            background: rgba(220, 53, 69, 0.2);
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.85rem;
        }}
        
        .filter-bar {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .filter-btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
        }}
        
        .filter-btn:hover, .filter-btn.active {{
            background: #4a90d9;
        }}
        
        .search-input {{
            padding: 10px 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            color: #fff;
            font-size: 0.9rem;
            width: 250px;
        }}
        
        .search-input::placeholder {{
            color: #666;
        }}
        
        .table-container {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        th {{
            background: rgba(0, 0, 0, 0.3);
            font-weight: 600;
            color: #fff;
        }}
        
        tr:hover td {{
            background: rgba(255, 255, 255, 0.05);
        }}
        
        .level-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        
        .badge-info {{ background: rgba(40, 167, 69, 0.2); color: #28a745; }}
        .badge-warn {{ background: rgba(255, 193, 7, 0.2); color: #ffc107; }}
        .badge-error {{ background: rgba(220, 53, 69, 0.2); color: #dc3545; }}
        .badge-critical {{ background: rgba(111, 66, 193, 0.2); color: #a855f7; }}
        
        .timestamp-col {{
            white-space: nowrap;
            color: #888;
            font-size: 0.9rem;
        }}
        
        .message-col {{
            max-width: 400px;
            word-break: break-word;
        }}
        
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #888;
        }}
        
        .section {{
            margin-bottom: 30px;
        }}
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(255, 255, 255, 0.05);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(255, 255, 255, 0.3);
        }}
        
        .hidden {{
            display: none !important;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Log Analytics Dashboard</h1>
            <p class="subtitle">Real-time log analysis and monitoring</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(data["logs"])}</div>
                <div class="stat-label">Total Log Entries</div>
            </div>
            <div class="stat-card">
                <div class="stat-value level-info">{level_counts.get("INFO", 0)}</div>
                <div class="stat-label">Info Messages</div>
            </div>
            <div class="stat-card">
                <div class="stat-value level-warn">{level_counts.get("WARN", 0)}</div>
                <div class="stat-label">Warnings</div>
            </div>
            <div class="stat-card">
                <div class="stat-value level-error">{level_counts.get("ERROR", 0)}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-value level-critical">{level_counts.get("CRITICAL", 0)}</div>
                <div class="stat-label">Critical</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3 class="chart-title">Log Level Distribution</h3>
                <div class="donut-chart">
                    <svg viewBox="0 0 100 100" width="200" height="200">
                        <circle cx="50" cy="50" r="40" fill="none" stroke="#333" stroke-width="12"/>
'''
    
    # Add donut chart segments
    total = sum(level_counts.values())
    current_angle = -90
    
    for level in ["INFO", "WARN", "ERROR", "CRITICAL"]:
        if level in level_counts:
            count = level_counts[level]
            angle = (count / total) * 360
            end_angle = current_angle + angle
            
            # Calculate SVG arc
            start_rad = (current_angle - 90) * 3.14159 / 180
            end_rad = (end_angle - 90) * 3.14159 / 180
            
            x1 = 50 + 40 * 3.14159 * (1 + 0.5 * 3.14159 * (current_angle - 180) / 90)
            y1 = 50 + 40 * 3.14159 * (1 + 0.5 * 3.14159 * current_angle / 90)
            
            # Simplified donut chart using stroke-dasharray
            circumference = 2 * 3.14159 * 40
            dash_length = (count / total) * circumference
            dash_array = f"{dash_length} {circumference - dash_length}"
            
            html += f'''                        <circle cx="50" cy="50" r="20" fill="none" stroke="{colors[level]}" 
                              stroke-width="12" stroke-dasharray="{dash_array}" stroke-dashoffset="{-2 * 3.14159 * 20 * (current_angle / 360)}"
                              transform="rotate({current_angle} 50 50)" />
'''
            current_angle = end_angle
    
    html += f'''                    </svg>
                </div>
                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-color" style="background: {colors["INFO"]}"></div>
                        <span>INFO ({percentages.get("INFO", 0)}%)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: {colors["WARN"]}"></div>
                        <span>WARN ({percentages.get("WARN", 0)}%)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: {colors["ERROR"]}"></div>
                        <span>ERROR ({percentages.get("ERROR", 0)}%)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: {colors["CRITICAL"]}"></div>
                        <span>CRITICAL ({percentages.get("CRITICAL", 0)}%)</span>
                    </div>
                </div>
            </div>
            
            <div class="chart-card">
                <h3 class="chart-title">Errors Per Hour</h3>
                <svg class="timeline-svg" viewBox="0 0 600 200" preserveAspectRatio="none">
                    <!-- Grid lines -->
'''
    
    # Add grid lines
    for i in range(5):
        y = 30 + i * 35
        html += f'''                    <line x1="50" y1="{y}" x2="580" y2="{y}" stroke="#333" stroke-width="1"/>\n'''
    
    # Add timeline bars
    if hours:
        bar_width = 500 / len(hours)
        for i, hour in enumerate(hours):
            errors = errors_by_hour[hour]
            bar_height = (errors / max_errors) * 140
            x = 50 + i * bar_width
            y = 170 - bar_height
            bar_color = "#dc3545" if errors > max_errors * 0.7 else "#ffc107" if errors > max_errors * 0.4 else "#28a745"
            
            html += f'''                    <rect x="{x + 2}" y="{y}" width="{bar_width - 4}" height="{bar_height}" fill="{bar_color}" rx="2"/>
'''
    
    html += '''                </svg>
                <div class="legend">
'''
    
    # Add hour labels
    if hours:
        step = max(1, len(hours) // 8)
        for i, hour in enumerate(hours[::step]):
            x = 50 + i * step * (500 / len(hours)) + 25
            html += f'''                    <div style="text-align: center; min-width: 60px;">
                        <div style="font-size: 0.75rem; color: #888;">{hour.split()[1]}</div>
                    </div>
'''
    
    html += '''                </div>
            </div>
        </div>
        
        <div class="section error-messages">
            <div class="chart-card">
                <h3 class="chart-title">Most Common Error Messages</h3>
                <ul class="message-list">
'''
    
    for message, count in list(error_messages.items())[:10]:
        escaped_message = escape(message[:80] + "..." if len(message) > 80 else message)
        html += f'''                    <li class="message-item">
                        <span class="message-text" title="{escape(message)}">{escaped_message}</span>
                        <span class="message-count">{count}</span>
                    </li>
'''
    
    html += '''                </ul>
            </div>
        </div>
        
        <div class="section">
            <div class="chart-card">
                <h3 class="chart-title">Critical Errors Log</h3>
                <div class="filter-bar">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="ERROR">Error</button>
                    <button class="filter-btn" data-filter="CRITICAL">Critical</button>
                    <input type="text" class="search-input" id="searchInput" placeholder="Search messages...">
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Level</th>
                                <th>Message</th>
                            </tr>
                        </thead>
                        <tbody id="errorTableBody">
'''
    
    # Add critical errors rows
    all_errors = [l for l in data["logs"] if l["level"] in ["ERROR", "CRITICAL"]]
    for log in all_errors[:100]:  # Limit to 100 for performance
        timestamp = log["timestamp"].replace("T", " ").split(".")[0]
        level = log["level"]
        message = escape(log["message"])
        badge_class = f"badge-{level.lower()}"
        
        html += f'''                            <tr data-level="{level}" data-message="{message.lower()}">
                                <td class="timestamp-col">{timestamp}</td>
                                <td><span class="level-badge {badge_class}">{level}</span></td>
                                <td class="message-col">{message}</td>
                            </tr>
'''
    
    html += '''                        </tbody>
                    </table>
                    <div id="noResults" class="no-results hidden">No matching errors found</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Filter functionality
        const filterBtns = document.querySelectorAll('.filter-btn');
        const searchInput = document.getElementById('searchInput');
        const tableBody = document.getElementById('errorTableBody');
        const rows = tableBody.querySelectorAll('tr');
        const noResults = document.getElementById('noResults');
        let currentFilter = 'all';
        
        function filterRows() {
            const searchTerm = searchInput.value.toLowerCase();
            let visibleCount = 0;
            
            rows.forEach(row => {
                const level = row.dataset.level;
                const message = row.dataset.message;
                const matchesFilter = currentFilter === 'all' || level === currentFilter;
                const matchesSearch = message.includes(searchTerm);
                
                if (matchesFilter && matchesSearch) {
                    row.classList.remove('hidden');
                    visibleCount++;
                } else {
                    row.classList.add('hidden');
                }
            });
            
            if (visibleCount === 0) {
                noResults.classList.remove('hidden');
            } else {
                noResults.classList.add('hidden');
            }
        }
        
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                filterRows();
            });
        });
        
        searchInput.addEventListener('input', filterRows);
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    if (data.updated) {
                        location.reload();
                    }
                })
                .catch(() => {});
        }, 30000);
    </script>
</body>
</html>'''
    
    return html


class LogDashboardHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for the log dashboard."""
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/" or path == "/index.html":
            self.serve_dashboard()
        elif path == "/api/logs":
            self.serve_api()
        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_response()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML."""
        try:
            data = parse_log_file()
            html = generate_dashboard_html(data)
            
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_api(self):
        """Serve log data as JSON."""
        try:
            data = parse_log_file()
            json_data = json.dumps(data)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(json_data.encode("utf-8"))
        except Exception as e:
            error = {"error": str(e)}
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(error).encode("utf-8"))


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP server for handling concurrent requests."""
    allow_reuse_address = True
    daemon_threads = True


def run_server():
    """Run the log analytics dashboard server."""
    # Check and generate logs if needed
    if not os.path.exists(LOG_FILE):
        print(f"Creating {LOG_FILE} with sample log data...")
        generate_fake_logs()
    
    # Parse logs to verify
    data = parse_log_file()
    print(f"Loaded {len(data['logs'])} log entries")
    
    # Start server
    server = ThreadedHTTPServer(("0.0.0.0", PORT), LogDashboardHandler)
    
    print(f"\n{'='*50}")
    print(f"  🚀 Log Analytics Dashboard")
    print(f"{'='*50}")
    print(f"\n  📊 Dashboard running at:")
    print(f"     http://localhost:{PORT}")
    print(f"     http://0.0.0.0:{PORT}")
    print(f"\n  💡 Press Ctrl+C to stop")
    print(f"\n  📁 Monitoring: {os.path.abspath(LOG_FILE)}")
    print(f"{'='*50}\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n  👋 Shutting down dashboard...")
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    run_server()