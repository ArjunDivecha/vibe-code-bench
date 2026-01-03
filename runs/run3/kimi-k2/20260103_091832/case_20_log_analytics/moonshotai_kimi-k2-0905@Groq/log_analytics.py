#!/usr/bin/env python3
import os
import json
import random
import datetime
import collections
import http.server
import socketserver
import threading
import time
import re
from collections import defaultdict, Counter

LOG_FILE = "server.log"
PORT = 8080

# Log level percentages
LOG_LEVELS = {
    "INFO": 70,
    "WARN": 20,
    "ERROR": 8,
    "CRITICAL": 2
}

# Sample log messages
LOG_MESSAGES = {
    "INFO": [
        "User login successful",
        "Database connection established",
        "Request processed successfully",
        "Cache cleared",
        "Service started",
        "Configuration loaded",
        "Backup completed",
        "Email sent successfully",
        "API call completed",
        "Session created"
    ],
    "WARN": [
        "High memory usage detected",
        "Slow query detected",
        "Rate limit approaching",
        "Deprecated API usage",
        "Certificate expiring soon",
        "Disk space low",
        "Connection timeout warning",
        "High CPU usage",
        "Memory leak detected",
        "Database connection pool low"
    ],
    "ERROR": [
        "Database connection failed",
        "File not found",
        "Permission denied",
        "Invalid API key",
        "Service unavailable",
        "Request timeout",
        "Invalid request format",
        "Authentication failed",
        "Resource not found",
        "Internal server error"
    ],
    "CRITICAL": [
        "System crash detected",
        "Data corruption detected",
        "Security breach attempt",
        "Database corrupted",
        "Service completely down",
        "Hardware failure",
        "Power failure detected",
        "Network completely down",
        "Critical security vulnerability",
        "Complete system failure"
    ]
}

def generate_log_line(timestamp, level, message):
    """Generate a log line in common log format"""
    return f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}"

def generate_fake_logs():
    """Generate 1000 lines of fake log data"""
    print("Generating fake log data...")
    logs = []
    start_time = datetime.datetime.now() - datetime.timedelta(days=2)
    
    for i in range(1000):
        # Random timestamp within last 2 days
        timestamp = start_time + datetime.timedelta(
            hours=random.randint(0, 48),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        
        # Choose log level based on percentages
        rand = random.randint(1, 100)
        if rand <= LOG_LEVELS["INFO"]:
            level = "INFO"
        elif rand <= LOG_LEVELS["INFO"] + LOG_LEVELS["WARN"]:
            level = "WARN"
        elif rand <= LOG_LEVELS["INFO"] + LOG_LEVELS["WARN"] + LOG_LEVELS["ERROR"]:
            level = "ERROR"
        else:
            level = "CRITICAL"
        
        # Choose random message for the level
        message = random.choice(LOG_MESSAGES[level])
        
        logs.append(generate_log_line(timestamp, level, message))
    
    # Write logs to file
    with open(LOG_FILE, 'w') as f:
        for log in logs:
            f.write(log + '\n')
    
    print(f"Generated {len(logs)} log entries")

def parse_logs():
    """Parse log file and extract analytics data"""
    print("Parsing log data...")
    
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
    
    level_counts = Counter()
    errors_per_hour = defaultdict(int)
    error_messages = Counter()
    critical_errors = []
    
    log_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (.+)')
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                level_counts[level] += 1
                
                if level in ["ERROR", "CRITICAL"]:
                    hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                    errors_per_hour[hour_key] += 1
                    error_messages[message] += 1
                    
                    if level == "CRITICAL":
                        critical_errors.append({
                            'timestamp': timestamp_str,
                            'message': message
                        })
    
    total_logs = sum(level_counts.values())
    level_percentages = {
        level: (count / total_logs * 100) if total_logs > 0 else 0
        for level, count in level_counts.items()
    }
    
    # Prepare timeline data
    timeline_data = []
    for hour, count in sorted(errors_per_hour.items()):
        timeline_data.append({
            'time': hour,
            'errors': count
        })
    
    # Prepare common errors data
    common_errors = []
    for message, count in error_messages.most_common(10):
        common_errors.append({
            'message': message,
            'count': count
        })
    
    return {
        'level_percentages': level_percentages,
        'timeline_data': timeline_data,
        'common_errors': common_errors,
        'critical_errors': critical_errors,
        'total_logs': total_logs
    }

class LogAnalyticsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_dashboard_html().encode())
        elif self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            data = parse_logs()
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_error(404)
    
    def get_dashboard_html(self):
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log Analytics Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #2c3e50;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            margin-bottom: 15px;
            color: #34495e;
            font-size: 1.2em;
        }
        
        .chart-container {
            height: 200px;
            position: relative;
        }
        
        .bar-chart {
            display: flex;
            align-items: flex-end;
            height: 100%;
            gap: 5px;
        }
        
        .bar {
            flex: 1;
            background: linear-gradient(to top, #3498db, #2980b9);
            border-radius: 3px 3px 0 0;
            position: relative;
            min-height: 20px;
        }
        
        .bar.error { background: linear-gradient(to top, #e74c3c, #c0392b); }
        .bar.warn { background: linear-gradient(to top, #f39c12, #d68910); }
        .bar.critical { background: linear-gradient(to top, #8e44ad, #7d3c98); }
        
        .bar-label {
            position: absolute;
            bottom: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.8em;
            color: #666;
        }
        
        .bar-value {
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.8em;
            font-weight: bold;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        
        .search-box {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .filter-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .filter-btn.active {
            background: #3498db;
            color: white;
            border-color: #3498db;
        }
        
        .timeline-chart {
            height: 150px;
            position: relative;
            overflow-x: auto;
        }
        
        .timeline-line {
            stroke: #e74c3c;
            stroke-width: 2;
            fill: none;
        }
        
        .timeline-dot {
            fill: #e74c3c;
            r: 3;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .error-message {
            background: #fee;
            color: #c33;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Log Analytics Dashboard</h1>
        
        <div class="dashboard-grid">
            <div class="card">
                <h2>Log Level Distribution</h2>
                <div id="level-chart" class="chart-container">
                    <div class="loading">Loading...</div>
                </div>
            </div>
            
            <div class="card">
                <h2>Errors per Hour</h2>
                <div id="timeline-chart" class="chart-container">
                    <div class="loading">Loading...</div>
                </div>
            </div>
            
            <div class="card">
                <h2>Most Common Errors</h2>
                <div id="common-errors">
                    <div class="loading">Loading...</div>
                </div>
            </div>
            
            <div class="card">
                <h2>Critical Errors</h2>
                <input type="text" id="search-critical" class="search-box" placeholder="Search critical errors...">
                <div class="filter-buttons">
                    <button class="filter-btn active" onclick="filterCritical('all')">All</button>
                    <button class="filter-btn" onclick="filterCritical('recent')">Recent</button>
                </div>
                <div id="critical-errors">
                    <div class="loading">Loading...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let dashboardData = null;
        
        async function loadData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                dashboardData = data;
                updateDashboard();
            } catch (error) {
                console.error('Error loading data:', error);
                document.querySelectorAll('.loading').forEach(el => {
                    el.innerHTML = '<div class="error-message">Error loading data</div>';
                });
            }
        }
        
        function updateDashboard() {
            updateLevelChart();
            updateTimelineChart();
            updateCommonErrors();
            updateCriticalErrors();
        }
        
        function updateLevelChart() {
            const container = document.getElementById('level-chart');
            const data = dashboardData.level_percentages;
            const maxValue = Math.max(...Object.values(data));
            
            let html = '<div class="bar-chart">';
            Object.entries(data).forEach(([level, percentage]) => {
                const height = (percentage / maxValue) * 160;
                const levelClass = level.toLowerCase();
                html += `
                    <div class="bar ${levelClass}" style="height: ${height}px">
                        <div class="bar-value">${percentage.toFixed(1)}%</div>
                        <div class="bar-label">${level}</div>
                    </div>
                `;
            });
            html += '</div>';
            
            container.innerHTML = html;
        }
        
        function updateTimelineChart() {
            const container = document.getElementById('timeline-chart');
            const data = dashboardData.timeline_data;
            
            if (data.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">No errors found</div>';
                return;
            }
            
            const maxErrors = Math.max(...data.map(d => d.errors));
            const width = Math.max(400, data.length * 30);
            const height = 150;
            const padding = 20;
            
            let svg = `<svg width="${width}" height="${height}" style="overflow: visible;">`;
            
            // Draw line
            let pathData = '';
            data.forEach((point, i) => {
                const x = (i / (data.length - 1)) * (width - 2 * padding) + padding;
                const y = height - padding - (point.errors / maxErrors) * (height - 2 * padding);
                if (i === 0) pathData += `M ${x} ${y}`;
                else pathData += ` L ${x} ${y}`;
            });
            
            svg += `<path class="timeline-line" d="${pathData}" />`;
            
            // Draw dots
            data.forEach((point, i) => {
                const x = (i / (data.length - 1)) * (width - 2 * padding) + padding;
                const y = height - padding - (point.errors / maxErrors) * (height - 2 * padding);
                svg += `<circle class="timeline-dot" cx="${x}" cy="${y}" />`;
                
                // Add time labels for every 5th point
                if (i % 5 === 0) {
                    svg += `<text x="${x}" y="${height - 5}" text-anchor="middle" font-size="10" fill="#666">${point.time.split(' ')[1]}</text>`;
                }
            });
            
            svg += '</svg>';
            container.innerHTML = `<div class="timeline-chart">${svg}</div>`;
        }
        
        function updateCommonErrors() {
            const container = document.getElementById('common-errors');
            const data = dashboardData.common_errors;
            
            if (data.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">No errors found</div>';
                return;
            }
            
            let html = '<table><thead><tr><th>Error Message</th><th>Count</th></tr></thead><tbody>';
            data.forEach(error => {
                html += `<tr><td>${error.message}</td><td>${error.count}</td></tr>`;
            });
            html += '</tbody></table>';
            
            container.innerHTML = html;
        }
        
        function updateCriticalErrors() {
            const container = document.getElementById('critical-errors');
            const data = dashboardData.critical_errors;
            
            if (data.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">No critical errors found</div>';
                return;
            }
            
            let html = '<table><thead><tr><th>Timestamp</th><th>Message</th></tr></thead><tbody>';
            data.slice(0, 10).forEach(error => {
                html += `<tr><td>${error.timestamp}</td><td>${error.message}</td></tr>`;
            });
            html += '</tbody></table>';
            
            container.innerHTML = html;
        }
        
        function filterCritical(filter) {
            // Update active button
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // In a real implementation, this would filter the data
            // For now, just reload the data
            updateCriticalErrors();
        }
        
        // Search functionality
        document.getElementById('search-critical').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#critical-errors tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
        
        // Load data on page load
        loadData();
        
        // Refresh data every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>"""

def start_server():
    """Start the HTTP server"""
    with socketserver.TCPServer(("", PORT), LogAnalyticsHandler) as httpd:
        print(f"Serving dashboard at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")
        httpd.serve_forever()

if __name__ == "__main__":
    # Check if log file exists, if not generate it
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
    else:
        print(f"Using existing log file: {LOG_FILE}")
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Parse and display initial analytics
    data = parse_logs()
    print("\n=== Log Analytics Summary ===")
    print(f"Total log entries: {data['total_logs']}")
    print("\nLog level distribution:")
    for level, percentage in data['level_percentages'].items():
        print(f"  {level}: {percentage:.1f}%")
    
    print(f"\nCritical errors found: {len(data['critical_errors'])}")
    print(f"Error timeline entries: {len(data['timeline_data'])}")
    
    print(f"\nDashboard is running at: http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")