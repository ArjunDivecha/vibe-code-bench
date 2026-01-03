#!/usr/bin/env python3
"""
Log Analytics Dashboard
A Python script that analyzes log files and serves an interactive dashboard.
"""

import os
import json
import random
import datetime
import re
import collections
import http.server
import socketserver
import threading
import time
from urllib.parse import urlparse, parse_qs

LOG_FILE = "server.log"
PORT = 8080

# Sample log messages for generation
LOG_MESSAGES = {
    "INFO": [
        "Server started successfully",
        "Database connection established",
        "User logged in",
        "Request processed successfully",
        "Cache cleared",
        "Backup completed",
        "Service health check passed",
        "Configuration updated",
        "API endpoint called",
        "Task queue processed"
    ],
    "WARN": [
        "High memory usage detected",
        "Slow query detected",
        "Deprecated API usage",
        "Rate limit approaching",
        "Disk space low",
        "Connection timeout",
        "Invalid configuration value",
        "Service degradation detected",
        "Retry attempt initiated",
        "Cache miss occurred"
    ],
    "ERROR": [
        "Database connection failed",
        "Authentication error",
        "File not found",
        "Permission denied",
        "Service unavailable",
        "Invalid request format",
        "Timeout occurred",
        "Resource exhausted",
        "API rate limit exceeded",
        "Internal server error"
    ],
    "CRITICAL": [
        "System crash detected",
        "Data corruption identified",
        "Security breach attempt",
        "Service completely down",
        "Hardware failure",
        "Database corruption",
        "Power failure",
        "Network partition",
        "Memory exhaustion",
        "Disk failure"
    ]
}

def generate_log_data():
    """Generate fake log data if server.log doesn't exist"""
    if os.path.exists(LOG_FILE):
        return
    
    print("Generating fake log data...")
    with open(LOG_FILE, 'w') as f:
        for i in range(1000):
            # Generate random timestamp within last 7 days
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            seconds_ago = random.randint(0, 59)
            
            now = datetime.datetime.now()
            log_time = now - datetime.timedelta(days=days_ago, hours=hours_ago, 
                                               minutes=minutes_ago, seconds=seconds_ago)
            timestamp = log_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Random log level with weighted distribution
            level_weights = [50, 25, 15, 10]  # INFO, WARN, ERROR, CRITICAL
            level = random.choices(["INFO", "WARN", "ERROR", "CRITICAL"], 
                                weights=level_weights)[0]
            
            # Random message
            message = random.choice(LOG_MESSAGES[level])
            
            # Write log entry
            f.write(f"[{timestamp}] [{level}] {message}\n")
    
    print(f"Generated 1000 log entries in {LOG_FILE}")

def parse_log_file():
    """Parse log file and extract analytics data"""
    log_entries = []
    level_counts = collections.Counter()
    errors_per_hour = collections.defaultdict(int)
    error_messages = collections.Counter()
    critical_errors = []
    
    log_pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\] (.+)')
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                log_entries.append({
                    'timestamp': timestamp_str,
                    'level': level,
                    'message': message,
                    'datetime': timestamp
                })
                
                level_counts[level] += 1
                
                if level in ["ERROR", "CRITICAL"]:
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    errors_per_hour[hour_key] += 1
                    error_messages[message] += 1
                    
                    if level == "CRITICAL":
                        critical_errors.append({
                            'timestamp': timestamp_str,
                            'message': message
                        })
    
    # Calculate percentages
    total_entries = len(log_entries)
    level_percentages = {
        level: (count / total_entries) * 100 
        for level, count in level_counts.items()
    }
    
    # Sort errors per hour by time
    sorted_errors = sorted(errors_per_hour.items())
    
    # Get top error messages
    top_errors = error_messages.most_common(10)
    
    return {
        'level_percentages': level_percentages,
        'errors_per_hour': sorted_errors,
        'top_errors': top_errors,
        'critical_errors': critical_errors,
        'total_entries': total_entries
    }

def generate_html_dashboard(data):
    """Generate HTML dashboard with embedded CSS and JavaScript"""
    level_percentages = data['level_percentages']
    errors_per_hour = data['errors_per_hour']
    top_errors = data['top_errors']
    critical_errors = data['critical_errors']
    
    html = f"""<!DOCTYPE html>
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
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-card h3 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        
        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .chart-title {{
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #333;
            text-align: center;
        }}
        
        .level-percentages {{
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 20px;
        }}
        
        .level-item {{
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            min-width: 120px;
        }}
        
        .level-info {{ background-color: #e3f2fd; }}
        .level-warn {{ background-color: #fff3e0; }}
        .level-error {{ background-color: #ffebee; }}
        .level-critical {{ background-color: #fce4ec; }}
        
        .level-label {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .level-percentage {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        
        .timeline-chart {{
            width: 100%;
            height: 300px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background: #fafafa;
        }}
        
        .search-container {{
            margin-bottom: 20px;
        }}
        
        .search-input {{
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
            outline: none;
        }}
        
        .search-input:focus {{
            border-color: #667eea;
        }}
        
        .filter-buttons {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }}
        
        .filter-btn.active {{
            background-color: #667eea;
            color: white;
        }}
        
        .filter-btn:not(.active) {{
            background-color: #e0e0e0;
            color: #333;
        }}
        
        .filter-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
        
        .error-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .error-table th {{
            background-color: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: bold;
        }}
        
        .error-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        
        .error-table tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .error-table tr.hidden {{
            display: none;
        }}
        
        .top-errors-list {{
            list-style: none;
            padding: 0;
        }}
        
        .top-errors-list li {{
            padding: 10px;
            margin-bottom: 5px;
            background-color: #f8f9fa;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .error-count {{
            background-color: #667eea;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.9em;
        }}
        
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 1.1em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Log Analytics Dashboard</h1>
            <p>Total Log Entries: {data['total_entries']:,}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Log Level Distribution</h3>
                <div class="level-percentages">
    """
    
    # Add level percentages
    for level in ['INFO', 'WARN', 'ERROR', 'CRITICAL']:
        percentage = level_percentages.get(level, 0)
        html += f"""
                    <div class="level-item level-{level.lower()}">
                        <div class="level-label">{level}</div>
                        <div class="level-percentage">{percentage:.1f}%</div>
                    </div>
        """
    
    html += """
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2 class="chart-title">Errors per Hour Timeline</h2>
            <svg class="timeline-chart" id="timelineChart">
    """
    
    # Generate timeline chart
    if errors_per_hour:
        max_errors = max(count for _, count in errors_per_hour)
        width = 800
        height = 250
        padding = 40
        
        html += f'<g transform="translate({padding}, {padding})">'
        
        # Draw axes
        html += f'<line x1="0" y1="{height - 2 * padding}" x2="{width - 2 * padding}" y2="{height - 2 * padding}" stroke="#ccc" stroke-width="2"/>'
        html += f'<line x1="0" y1="0" x2="0" y2="{height - 2 * padding}" stroke="#ccc" stroke-width="2"/>'
        
        # Draw data points and lines
        bar_width = (width - 2 * padding) / len(errors_per_hour)
        
        for i, (hour, count) in enumerate(errors_per_hour):
            x = i * bar_width
            bar_height = (count / max_errors) * (height - 2 * padding) if max_errors > 0 else 0
            
            # Draw bar
            html += f'<rect x="{x}" y="{height - 2 * padding - bar_height}" width="{bar_width - 2}" height="{bar_height}" fill="#667eea" opacity="0.7"/>'
            
            # Draw hour label (every 3rd hour to avoid crowding)
            if i % 3 == 0:
                html += f'<text x="{x}" y="{height - padding + 20}" font-size="10" fill="#666" transform="rotate(-45, {x}, {height - padding + 20})">{hour}</text>'
        
        # Add chart labels
        html += f'<text x="{width/2 - padding}" y="{height - padding + 40}" text-anchor="middle" font-size="12" fill="#333">Time (Hours)</text>'
        html += f'<text x="-{height/2}" y="-20" text-anchor="middle" font-size="12" fill="#333" transform="rotate(-90)">Error Count</text>'
        
        html += '</g>'
    
    html += """
            </svg>
        </div>
        
        <div class="chart-container">
            <h2 class="chart-title">Top 10 Error Messages</h2>
            <ul class="top-errors-list">
    """
    
    # Add top errors
    for message, count in top_errors:
        html += f"""
                <li>
                    <span>{message}</span>
                    <span class="error-count">{count}</span>
                </li>
        """
    
    html += """
            </ul>
        </div>
        
        <div class="chart-container">
            <h2 class="chart-title">Critical Errors</h2>
            <div class="search-container">
                <input type="text" class="search-input" id="searchInput" placeholder="Search critical errors...">
            </div>
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="filterTable('all')">All Levels</button>
                <button class="filter-btn" onclick="filterTable('ERROR')">Error</button>
                <button class="filter-btn" onclick="filterTable('CRITICAL')">Critical</button>
            </div>
    """
    
    # Add critical errors table
    if critical_errors:
        html += """
            <table class="error-table">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody id="errorTableBody">
        """
        
        for error in critical_errors:
            html += f"""
                    <tr data-level="CRITICAL">
                        <td>{error['timestamp']}</td>
                        <td>{error['message']}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        """
    else:
        html += '<div class="no-results">No critical errors found.</div>'
    
    html += """
        </div>
    </div>
    
    <script>
        // Search functionality
        document.getElementById('searchInput').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#errorTableBody tr');
            
            rows.forEach(row => {
                const message = row.cells[1].textContent.toLowerCase();
                if (message.includes(searchTerm)) {
                    row.classList.remove('hidden');
                } else {
                    row.classList.add('hidden');
                }
            });
        });
        
        // Filter functionality
        function filterTable(level) {
            const rows = document.querySelectorAll('#errorTableBody tr');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // Update button states
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // Filter rows
            rows.forEach(row => {
                if (level === 'all' || row.dataset.level === level) {
                    row.classList.remove('hidden');
                } else {
                    row.classList.add('hidden');
                }
            });
        }
    </script>
</body>
</html>
    """
    
    return html

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Generate and parse log data
            generate_log_data()
            data = parse_log_file()
            
            # Generate HTML dashboard
            html = generate_html_dashboard(data)
            self.wfile.write(html.encode())
        
        elif self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            generate_log_data()
            data = parse_log_file()
            self.wfile.write(json.dumps(data).encode())
        
        else:
            self.send_error(404)

def run_server():
    """Run the HTTP server"""
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"Log Analytics Dashboard running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()