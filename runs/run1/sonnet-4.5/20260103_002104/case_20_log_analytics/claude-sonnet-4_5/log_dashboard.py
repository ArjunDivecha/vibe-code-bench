#!/usr/bin/env python3
"""
Log Analytics Dashboard
Generates fake logs if needed, analyzes them, and serves an interactive dashboard.
"""

import http.server
import socketserver
import json
import random
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import urllib.parse
import re

# Configuration
LOG_FILE = "server.log"
PORT = 8000

# Fake log generation
LOG_LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]
LOG_LEVEL_WEIGHTS = [60, 25, 12, 3]  # Weighted distribution

ERROR_MESSAGES = [
    "Database connection timeout",
    "Failed to authenticate user",
    "API rate limit exceeded",
    "Memory allocation failed",
    "File not found",
    "Invalid request parameters",
    "Service unavailable",
    "Network timeout",
    "Permission denied",
    "Disk space full",
    "Failed to parse JSON",
    "SSL certificate expired",
    "Resource not found",
    "Connection refused",
    "Internal server error"
]

INFO_MESSAGES = [
    "User logged in successfully",
    "Request processed",
    "Cache hit",
    "Service started",
    "Configuration loaded",
    "Health check passed",
    "Task completed",
    "Data synchronized"
]

WARN_MESSAGES = [
    "High memory usage detected",
    "Slow query detected",
    "Deprecated API used",
    "Cache miss",
    "Retry attempt",
    "Queue size growing"
]


def generate_fake_logs(filename, num_lines=1000):
    """Generate fake log entries."""
    print(f"Generating {num_lines} fake log entries...")
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    logs = []
    for i in range(num_lines):
        # Random timestamp within last 24 hours
        random_seconds = random.randint(0, 24 * 3600)
        timestamp = start_time + timedelta(seconds=random_seconds)
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Random log level
        level = random.choices(LOG_LEVELS, weights=LOG_LEVEL_WEIGHTS)[0]
        
        # Select message based on level
        if level == "INFO":
            message = random.choice(INFO_MESSAGES)
        elif level == "WARN":
            message = random.choice(WARN_MESSAGES)
        else:  # ERROR or CRITICAL
            message = random.choice(ERROR_MESSAGES)
        
        # Add some variation
        if random.random() < 0.3:
            message += f" (code: {random.randint(1000, 9999)})"
        
        log_entry = f"{timestamp_str} [{level}] {message}"
        logs.append((timestamp, log_entry))
    
    # Sort by timestamp
    logs.sort(key=lambda x: x[0])
    
    # Write to file
    with open(filename, 'w') as f:
        for _, log_entry in logs:
            f.write(log_entry + "\n")
    
    print(f"Generated {num_lines} log entries in {filename}")


def parse_logs(filename):
    """Parse log file and extract analytics."""
    print("Parsing log file...")
    
    logs = []
    level_counts = Counter()
    errors_by_hour = defaultdict(int)
    error_messages = []
    critical_logs = []
    
    # Regex pattern to parse log entries
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(.*?)\] (.*)$'
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            match = re.match(pattern, line)
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                log_entry = {
                    'timestamp': timestamp_str,
                    'level': level,
                    'message': message
                }
                logs.append(log_entry)
                
                # Count log levels
                level_counts[level] += 1
                
                # Track errors by hour
                if level in ['ERROR', 'CRITICAL']:
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    errors_by_hour[hour_key] += 1
                    error_messages.append(message)
                
                # Track critical logs
                if level == 'CRITICAL':
                    critical_logs.append(log_entry)
    
    # Calculate percentages
    total = sum(level_counts.values())
    level_percentages = {level: (count / total * 100) for level, count in level_counts.items()}
    
    # Most common error messages
    error_message_counts = Counter(error_messages).most_common(10)
    
    # Sort errors by hour
    errors_timeline = sorted(errors_by_hour.items())
    
    analytics = {
        'total_logs': total,
        'level_counts': dict(level_counts),
        'level_percentages': level_percentages,
        'errors_timeline': errors_timeline,
        'common_errors': error_message_counts,
        'critical_logs': critical_logs,
        'all_logs': logs
    }
    
    print(f"Parsed {total} log entries")
    return analytics


class LogDashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for the log dashboard."""
    
    analytics = None
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_dashboard()
        elif parsed_path.path == '/api/analytics':
            self.serve_analytics()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the HTML dashboard."""
        html = self.get_dashboard_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_analytics(self):
        """Serve analytics data as JSON."""
        data = {
            'total_logs': self.analytics['total_logs'],
            'level_counts': self.analytics['level_counts'],
            'level_percentages': self.analytics['level_percentages'],
            'errors_timeline': self.analytics['errors_timeline'],
            'common_errors': self.analytics['common_errors'],
            'critical_logs': self.analytics['critical_logs']
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_dashboard_html(self):
        """Generate the dashboard HTML."""
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 2em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .stat-card h3 {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        
        .stat-card .percentage {
            font-size: 0.9em;
            color: #999;
            margin-top: 5px;
        }
        
        .stat-card.info { border-left: 4px solid #2196F3; }
        .stat-card.warn { border-left: 4px solid #FF9800; }
        .stat-card.error { border-left: 4px solid #F44336; }
        .stat-card.critical { border-left: 4px solid #9C27B0; }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .chart-card h2 {
            color: #333;
            font-size: 1.2em;
            margin-bottom: 20px;
        }
        
        .chart {
            width: 100%;
            height: 300px;
        }
        
        .table-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .table-card h2 {
            color: #333;
            font-size: 1.2em;
            margin-bottom: 20px;
        }
        
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        input[type="text"] {
            flex: 1;
            min-width: 200px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .filter-buttons {
            display: flex;
            gap: 5px;
        }
        
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            background: #e0e0e0;
            color: #333;
            transition: background 0.2s;
        }
        
        button:hover {
            background: #d0d0d0;
        }
        
        button.active {
            background: #2196F3;
            color: white;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #f5f5f5;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #666;
            border-bottom: 2px solid #ddd;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        
        tr:hover {
            background: #fafafa;
        }
        
        .level-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .level-badge.INFO { background: #E3F2FD; color: #1976D2; }
        .level-badge.WARN { background: #FFF3E0; color: #F57C00; }
        .level-badge.ERROR { background: #FFEBEE; color: #C62828; }
        .level-badge.CRITICAL { background: #F3E5F5; color: #7B1FA2; }
        
        .error-list {
            list-style: none;
        }
        
        .error-list li {
            padding: 10px;
            margin-bottom: 5px;
            background: #f9f9f9;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .error-count {
            background: #F44336;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Log Analytics Dashboard</h1>
        
        <div class="stats-grid" id="statsGrid"></div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h2>Errors Over Time</h2>
                <svg class="chart" id="timelineChart"></svg>
            </div>
            <div class="chart-card">
                <h2>Most Common Errors</h2>
                <ul class="error-list" id="errorList"></ul>
            </div>
        </div>
        
        <div class="table-card">
            <h2>Critical Logs</h2>
            <div class="controls">
                <input type="text" id="searchInput" placeholder="Search logs...">
                <div class="filter-buttons">
                    <button class="active" data-filter="all">All</button>
                    <button data-filter="ERROR">Errors</button>
                    <button data-filter="CRITICAL">Critical</button>
                </div>
            </div>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Level</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody id="logsTable"></tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let analyticsData = null;
        let currentFilter = 'all';
        let searchTerm = '';
        
        // Fetch analytics data
        async function loadAnalytics() {
            const response = await fetch('/api/analytics');
            analyticsData = await response.json();
            renderDashboard();
        }
        
        function renderDashboard() {
            renderStats();
            renderTimelineChart();
            renderCommonErrors();
            renderLogsTable();
        }
        
        function renderStats() {
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const statsHtml = levels.map(level => {
                const count = analyticsData.level_counts[level] || 0;
                const percentage = (analyticsData.level_percentages[level] || 0).toFixed(1);
                return `
                    <div class="stat-card ${level.toLowerCase()}">
                        <h3>${level}</h3>
                        <div class="value">${count}</div>
                        <div class="percentage">${percentage}%</div>
                    </div>
                `;
            }).join('');
            
            document.getElementById('statsGrid').innerHTML = statsHtml;
        }
        
        function renderTimelineChart() {
            const svg = document.getElementById('timelineChart');
            const width = svg.clientWidth;
            const height = svg.clientHeight;
            const padding = 40;
            
            const timeline = analyticsData.errors_timeline;
            if (timeline.length === 0) {
                svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#999">No error data available</text>';
                return;
            }
            
            // Find max value for scaling
            const maxValue = Math.max(...timeline.map(t => t[1]));
            const xStep = (width - 2 * padding) / Math.max(timeline.length - 1, 1);
            const yScale = (height - 2 * padding) / maxValue;
            
            // Create SVG elements
            let svgContent = '';
            
            // Draw axes
            svgContent += `<line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="#ddd" stroke-width="2"/>`;
            svgContent += `<line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" stroke="#ddd" stroke-width="2"/>`;
            
            // Draw line chart
            const points = timeline.map((t, i) => {
                const x = padding + i * xStep;
                const y = height - padding - t[1] * yScale;
                return `${x},${y}`;
            }).join(' ');
            
            svgContent += `<polyline points="${points}" fill="none" stroke="#F44336" stroke-width="2"/>`;
            
            // Draw points
            timeline.forEach((t, i) => {
                const x = padding + i * xStep;
                const y = height - padding - t[1] * yScale;
                svgContent += `<circle cx="${x}" cy="${y}" r="4" fill="#F44336"/>`;
            });
            
            // Draw labels (show every few hours)
            const labelStep = Math.max(1, Math.floor(timeline.length / 8));
            timeline.forEach((t, i) => {
                if (i % labelStep === 0) {
                    const x = padding + i * xStep;
                    const time = t[0].split(' ')[1].substring(0, 5);
                    svgContent += `<text x="${x}" y="${height - padding + 20}" text-anchor="middle" font-size="10" fill="#666">${time}</text>`;
                }
            });
            
            svg.innerHTML = svgContent;
        }
        
        function renderCommonErrors() {
            const list = document.getElementById('errorList');
            const html = analyticsData.common_errors.map(([message, count]) => `
                <li>
                    <span>${message}</span>
                    <span class="error-count">${count}</span>
                </li>
            `).join('');
            list.innerHTML = html || '<li>No errors found</li>';
        }
        
        function renderLogsTable() {
            const tbody = document.getElementById('logsTable');
            let logs = analyticsData.critical_logs;
            
            // Apply filter
            if (currentFilter === 'ERROR') {
                logs = logs.filter(log => log.level === 'ERROR');
            } else if (currentFilter === 'CRITICAL') {
                logs = logs.filter(log => log.level === 'CRITICAL');
            }
            
            // Apply search
            if (searchTerm) {
                const term = searchTerm.toLowerCase();
                logs = logs.filter(log => 
                    log.message.toLowerCase().includes(term) ||
                    log.timestamp.toLowerCase().includes(term)
                );
            }
            
            const html = logs.map(log => `
                <tr>
                    <td>${log.timestamp}</td>
                    <td><span class="level-badge ${log.level}">${log.level}</span></td>
                    <td>${log.message}</td>
                </tr>
            `).join('');
            
            tbody.innerHTML = html || '<tr><td colspan="3" style="text-align: center; color: #999;">No logs found</td></tr>';
        }
        
        // Event listeners
        document.getElementById('searchInput').addEventListener('input', (e) => {
            searchTerm = e.target.value;
            renderLogsTable();
        });
        
        document.querySelectorAll('.filter-buttons button').forEach(button => {
            button.addEventListener('click', () => {
                document.querySelectorAll('.filter-buttons button').forEach(b => b.classList.remove('active'));
                button.classList.add('active');
                currentFilter = button.dataset.filter;
                renderLogsTable();
            });
        });
        
        // Load data on page load
        loadAnalytics();
    </script>
</body>
</html>"""
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def main():
    """Main entry point."""
    print("=" * 60)
    print("Log Analytics Dashboard")
    print("=" * 60)
    
    # Check if log file exists, generate if not
    if not os.path.exists(LOG_FILE):
        print(f"\n{LOG_FILE} not found. Generating fake data...")
        generate_fake_logs(LOG_FILE)
    else:
        print(f"\nFound existing {LOG_FILE}")
    
    # Parse logs
    analytics = parse_logs(LOG_FILE)
    
    # Set analytics data for the handler
    LogDashboardHandler.analytics = analytics
    
    # Start HTTP server
    print(f"\n" + "=" * 60)
    print(f"Starting HTTP server on port {PORT}...")
    print(f"Dashboard URL: http://localhost:{PORT}")
    print(f"Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    with socketserver.TCPServer(("", PORT), LogDashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            httpd.shutdown()
            print("Server stopped.")


if __name__ == "__main__":
    main()