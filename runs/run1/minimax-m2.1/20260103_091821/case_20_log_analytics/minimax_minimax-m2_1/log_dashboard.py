#!/usr/bin/env python3
"""
Log Analytics Dashboard
A self-contained Python script that generates log data, parses it, and serves an interactive dashboard.
"""

import http.server
import socketserver
import json
import os
import random
import re
import math
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from urllib.parse import urlparse
import sys

# Configuration
LOG_FILE = "server.log"
PORT = 8000
HOST = "localhost"

# Log level distribution for generation
LOG_LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]
LOG_LEVEL_WEIGHTS = [0.5, 0.25, 0.2, 0.05]  # INFO: 50%, WARN: 25%, ERROR: 20%, CRITICAL: 5%

# Sample log messages by level
LOG_MESSAGES = {
    "INFO": [
        "User login successful",
        "Database connection established",
        "Cache cleared successfully",
        "Scheduled task completed",
        "API request processed",
        "Session created for user",
        "File upload completed",
        "Configuration reloaded",
        "Health check passed",
        "Service heartbeat received",
        "Request completed in 245ms",
        "User logged out",
        "Email notification sent",
        "Backup completed successfully",
        "New user registered"
    ],
    "WARN": [
        "High memory usage detected (85%)",
        "Slow database query detected",
        "Rate limit approaching threshold",
        "Disk space running low (15% remaining)",
        "Connection pool utilization high",
        "API response time degraded",
        "Deprecated API endpoint accessed",
        "Failed retry attempt for job",
        "Token expiring soon",
        "Cache miss rate increased"
    ],
    "ERROR": [
        "Database connection failed after 3 retries",
        "API request timeout (30s)",
        "Failed to process payment transaction",
        "Email delivery failed",
        "File not found: /data/config.json",
        "Authentication service unavailable",
        "Invalid input parameter detected",
        "External API returned 500 error",
        "Job queue processing failed",
        "Permission denied for user action",
        "Memory allocation failed",
        "Connection refused by upstream server"
    ],
    "CRITICAL": [
        "System out of memory - OOM killer activated",
        "Database corruption detected",
        "Primary server unreachable",
        "SSL certificate expired",
        "All worker nodes down",
        "Data loss detected in partition",
        "Kernel panic imminent",
        "RAID array degraded",
        "Security breach attempt detected",
        "Service mesh failure - cascading errors"
    ]
}

# IP addresses for fake logs
IP_ADDRESSES = [
    "192.168.1.100", "10.0.0.50", "172.16.0.25", "192.168.1.45",
    "10.10.10.100", "192.168.0.1", "172.31.255.100", "8.8.8.8"
]

# User agents for fake logs
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
    "curl/7.68.0", "Python-urllib/3.8", "Apache-HttpClient/4.5.12"
]


def generate_log_line(timestamp: datetime) -> str:
    """Generate a single fake log line."""
    level = random.choices(LOG_LEVELS, weights=LOG_LEVEL_WEIGHTS)[0]
    message = random.choice(LOG_MESSAGES[level])
    ip = random.choice(IP_ADDRESSES)
    
    # Add some variability to messages
    if level in ["ERROR", "CRITICAL"]:
        message = f"{message} (request_id={random.randint(10000, 99999)})"
    
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp_str}] {level:8} {ip} - {message}"


def generate_log_file():
    """Generate 1000 lines of fake log data."""
    print(f"Generating {LOG_FILE} with 1000 log lines...")
    
    end_time = datetime.now()
    
    logs = []
    for _ in range(1000):
        # More weight to recent times
        if random.random() < 0.7:
            seconds_ago = random.randint(0, 86400)
        else:
            seconds_ago = random.randint(86400, 604800)
        
        timestamp = end_time - timedelta(seconds=seconds_ago)
        logs.append(generate_log_line(timestamp))
    
    # Sort by timestamp
    logs.sort(key=lambda x: datetime.strptime(x.split("]")[0][1:], "%Y-%m-%d %H:%M:%S"))
    
    with open(LOG_FILE, "w") as f:
        f.write("\n".join(logs) + "\n")
    
    print(f"Generated {LOG_FILE} with {len(logs)} log entries.")


def parse_log_file():
    """Parse the log file and extract structured data."""
    if not os.path.exists(LOG_FILE):
        generate_log_file()
    
    logs = []
    level_counts = Counter()
    errors_by_hour = defaultdict(list)
    error_messages = []
    critical_logs = []
    
    log_pattern = re.compile(
        r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+(\w+)\s+([\d.]+)\s+-\s+(.+)'
    )
    
    with open(LOG_FILE, "r") as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, ip, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                log_entry = {
                    "timestamp": timestamp_str,
                    "level": level,
                    "ip": ip,
                    "message": message,
                    "hour": timestamp.strftime("%Y-%m-%d %H:00")
                }
                
                logs.append(log_entry)
                level_counts[level] += 1
                
                if level in ["ERROR", "CRITICAL"]:
                    error_messages.append(message)
                    errors_by_hour[log_entry["hour"]].append(log_entry)
                
                if level == "CRITICAL":
                    critical_logs.append(log_entry)
    
    # Calculate percentages
    total = sum(level_counts.values())
    level_percentages = {
        level: (count / total * 100) for level, count in level_counts.items()
    }
    
    # Get most common error messages
    common_errors = Counter(error_messages).most_common(10)
    
    return {
        "logs": logs,
        "level_counts": dict(level_counts),
        "level_percentages": level_percentages,
        "errors_by_hour": dict(errors_by_hour),
        "common_errors": common_errors,
        "critical_logs": critical_logs,
        "total_logs": total
    }


def generate_dashboard_html(data: dict) -> str:
    """Generate the complete HTML dashboard."""
    level_percentages = data["level_percentages"]
    level_counts = data["level_counts"]
    common_errors = data["common_errors"]
    critical_logs = data["critical_logs"]
    errors_by_hour = data["errors_by_hour"]
    
    # Colors for charts
    colors = {"INFO": "#28a745", "WARN": "#ffc107", "ERROR": "#dc3545", "CRITICAL": "#6f42c1"}
    total = data["total_logs"]
    
    # Pie chart calculation
    cx, cy, r = 100, 100, 80
    start_angle = 0
    pie_segments = []
    
    for level in LOG_LEVELS:
        if level in level_percentages:
            angle = (level_percentages[level] / 100) * 360
            end_angle = start_angle + angle
            
            x1 = cx + r * math.cos(math.radians(start_angle))
            y1 = cy + r * math.sin(math.radians(start_angle))
            x2 = cx + r * math.cos(math.radians(end_angle))
            y2 = cy + r * math.sin(math.radians(end_angle))
            
            large_arc = 1 if angle > 180 else 0
            
            path_d = f"M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z"
            
            pie_segments.append({
                "path": path_d,
                "color": colors[level],
                "label": level,
                "percentage": round(level_percentages[level], 1),
                "count": level_counts.get(level, 0)
            })
            
            start_angle = end_angle
    
    # Bar chart for errors per hour
    hours = sorted(errors_by_hour.keys())
    max_errors = max(len(v) for v in errors_by_hour.values()) if errors_by_hour else 1
    bar_width = 40
    bar_spacing = 15
    chart_width = max(len(hours) * (bar_width + bar_spacing) + 50, 400)
    chart_height = 200
    
    bar_svg = ""
    for i, hour in enumerate(hours):
        count = len(errors_by_hour[hour])
        bar_height = (count / max_errors) * 150
        x = 50 + i * (bar_width + bar_spacing)
        y = chart_height - bar_height - 30
        
        bar_svg += f'''
        <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" 
              fill="#dc3545" rx="4" class="bar" data-count="{count}">
            <title>{hour}: {count} errors</title>
        </rect>
        <text x="{x + bar_width/2}" y="{chart_height - 10}" 
              text-anchor="middle" font-size="10" fill="#888">
            {hour.split()[-1]}h
        </text>
        '''
    
    # Common errors list
    errors_html = ""
    for i, (error, count) in enumerate(common_errors, 1):
        errors_html += f'''
        <div class="message-item">
            <span class="rank">#{i}</span>
            <span class="count">{count}</span>
            <span class="message">{error}</span>
        </div>
        '''
    
    # Critical logs table
    critical_table_rows = ""
    for log in critical_logs[:100]:
        critical_table_rows += f'''
        <tr data-level="{log['level']}" data-message="{log['message'].lower()}">
            <td class="timestamp">{log['timestamp']}</td>
            <td><span class="badge badge-{log['level'].lower()}">{log['level']}</span></td>
            <td class="ip">{log['ip']}</td>
            <td class="message">{log['message']}</td>
        </tr>
        '''
    
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
        
        .bar {{
            transition: opacity 0.2s;
        }}
        
        .bar:hover {{
            opacity: 0.8;
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
            align-items: center;
            gap: 15px;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .message-item:last-child {{
            border-bottom: none;
        }}
        
        .rank {{
            font-weight: bold;
            color: #667eea;
            min-width: 30px;
        }}
        
        .count {{
            background: #dc3545;
            color: white;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: bold;
        }}
        
        .message {{
            flex: 1;
            font-size: 14px;
        }}
        
        .critical-section {{
            grid-column: 1 / -1;
        }}
        
        .filter-bar {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }}
        
        .filter-btn.active {{
            background: #667eea;
            color: white;
        }}
        
        .filter-btn:not(.active) {{
            background: rgba(255, 255, 255, 0.1);
            color: #888;
        }}
        
        .filter-btn:hover {{
            transform: translateY(-1px);
        }}
        
        .search-box {{
            flex: 1;
            min-width: 200px;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 8px 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            font-size: 14px;
            background: rgba(255, 255, 255, 0.05);
            color: #fff;
        }}
        
        .search-box input::placeholder {{
            color: #666;
        }}
        
        .table-container {{
            max-height: 400px;
            overflow-y: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        th {{
            background: rgba(255, 255, 255, 0.05);
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        
        tr:hover {{
            background: rgba(255, 255, 255, 0.05);
        }}
        
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .badge-critical {{
            background: rgba(111, 66, 193, 0.2);
            color: #a855f7;
        }}
        
        .badge-error {{
            background: rgba(220, 53, 69, 0.2);
            color: #f87171;
        }}
        
        .timestamp {{
            white-space: nowrap;
            font-family: monospace;
            color: #888;
        }}
        
        .ip {{
            font-family: monospace;
            color: #888;
        }}
        
        .message {{
            max-width: 400px;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        
        .full-width {{
            grid-column: 1 / -1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Log Analytics Dashboard</h1>
            <p class="subtitle">Real-time log analysis and monitoring</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total}</div>
                <div class="stat-label">Total Logs</div>
            </div>
            <div class="stat-card">
                <div class="stat-value level-info">{level_counts.get('INFO', 0)}</div>
                <div class="stat-label">INFO ({level_percentages.get('INFO', 0):.1f}%)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value level-warn">{level_counts.get('WARN', 0)}</div>
                <div class="stat-label">WARN ({level_percentages.get('WARN', 0):.1f}%)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value level-error">{level_counts.get('ERROR', 0)}</div>
                <div class="stat-label">ERROR ({level_percentages.get('ERROR', 0):.1f}%)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value level-critical">{level_counts.get('CRITICAL', 0)}</div>
                <div class="stat-label">CRITICAL ({level_percentages.get('CRITICAL', 0):.1f}%)</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <div class="chart-title">Log Level Distribution</div>
                <div class="donut-chart">
                    <svg viewBox="0 0 200 200">
                        {''.join(f'<path d="{s["path"]}" fill="{s["color"]}"/>' for s in pie_segments)}
                    </svg>
                </div>
                <div class="legend">
                    {''.join(f'''
                    <div class="legend-item">
                        <div class="legend-color" style="background: {s['color']}"></div>
                        <span>{s['label']} ({s['percentage']}%)</span>
                    </div>
                    ''' for s in pie_segments)}
                </div>
            </div>
            
            <div class="chart-card">
                <div class="chart-title">Errors Per Hour</div>
                <div class="timeline-svg">
                    <svg viewBox="0 0 {chart_width} {chart_height}">
                        {bar_svg}
                    </svg>
                </div>
            </div>
            
            <div class="chart-card full-width">
                <div class="chart-title">Most Common Error Messages</div>
                <div class="error-messages">
                    <div class="message-list">
                        {errors_html if errors_html else '<div class="no-results">No error messages found</div>'}
                    </div>
                </div>
            </div>
            
            <div class="chart-card full-width">
                <div class="chart-title">Critical Logs</div>
                <div class="filter-bar">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="CRITICAL">Critical</button>
                    <button class="filter-btn" data-filter="ERROR">Error</button>
                    <div class="search-box">
                        <input type="text" id="searchInput" placeholder="Search messages...">
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Level</th>
                                <th>IP Address</th>
                                <th>Message</th>
                            </tr>
                        </thead>
                        <tbody id="criticalTableBody">
                            {critical_table_rows if critical_table_rows else '<tr><td colspan="4" class="no-results">No critical logs found</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const filterBtns = document.querySelectorAll('.filter-btn');
        const searchInput = document.getElementById('searchInput');
        const tableBody = document.getElementById('criticalTableBody');
        const rows = tableBody.querySelectorAll('tr');
        
        let currentFilter = 'all';
        let currentSearch = '';
        
        function filterRows() {{
            rows.forEach(row => {{
                const level = row.dataset.level;
                const message = row.dataset.message;
                const matchesFilter = currentFilter === 'all' || level === currentFilter;
                const matchesSearch = !currentSearch || message.includes(currentSearch.toLowerCase());
                
                row.style.display = matchesFilter && matchesSearch ? '' : 'none';
            }});
            
            const visibleRows = Array.from(rows).filter(r => r.style.display !== 'none');
            const noResultsRow = tableBody.querySelector('.no-results');
            
            if (visibleRows.length === 0 && !noResultsRow) {{
                const noResults = document.createElement('tr');
                noResults.innerHTML = '<td colspan="4" class="no-results">No matching logs found</td>';
                tableBody.appendChild(noResults);
            }} else if (visibleRows.length > 0 && noResultsRow) {{
                noResultsRow.remove();
            }}
        }}
        
        filterBtns.forEach(btn => {{
            btn.addEventListener('click', () => {{
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                filterRows();
            }});
        }});
        
        searchInput.addEventListener('input', (e) => {{
            currentSearch = e.target.value;
            filterRows();
        }});
        
        // Auto-refresh every 30 seconds
        setTimeout(() => {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>'''
    return html


class LogDashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for serving the dashboard."""
    
    def __init__(self, *args, **kwargs):
        self.data = kwargs.pop('data', None)
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            html = generate_dashboard_html(self.data)
            self.wfile.write(html.encode('utf-8'))
        elif parsed_path.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            stats = {
                'level_counts': self.data['level_counts'],
                'level_percentages': self.data['level_percentages'],
                'total_logs': self.data['total_logs'],
                'common_errors': self.data['common_errors'],
                'critical_count': len(self.data['critical_logs'])
            }
            self.wfile.write(json.dumps(stats).encode('utf-8'))
        else:
            super().do_GET()
    
    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}")


class ReusableTCPServer(socketserver.TCPServer):
    """TCP Server with address reuse enabled."""
    allow_reuse_address = True


def main():
    """Main function to run the log analytics dashboard."""
    print("=" * 60)
    print("       Log Analytics Dashboard")
    print("=" * 60)
    
    if not os.path.exists(LOG_FILE):
        generate_log_file()
    else:
        print(f"Found existing {LOG_FILE}")
    
    print("\nParsing log file...")
    data = parse_log_file()
    print(f"  Total logs: {data['total_logs']}")
    print(f"  Level distribution:")
    for level in LOG_LEVELS:
        count = data['level_counts'].get(level, 0)
        pct = data['level_percentages'].get(level, 0)
        print(f"    {level}: {count} ({pct:.1f}%)")
    print(f"  Critical logs: {len(data['critical_logs'])}")
    
    handler = lambda *args, **kwargs: LogDashboardHandler(*args, data=data, **kwargs)
    
    with ReusableTCPServer((HOST, PORT), handler) as httpd:
        url = f"http://{HOST}:{PORT}"
        print("\n" + "=" * 60)
        print(f"  Dashboard available at: {url}")
        print("  Press Ctrl+C to stop")
        print("=" * 60 + "\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down dashboard...")
            httpd.shutdown()


if __name__ == "__main__":
    main()