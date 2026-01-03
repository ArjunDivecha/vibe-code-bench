#!/usr/bin/env python3
"""
Log Analytics Dashboard
Generates fake logs, parses them, and serves an interactive dashboard
"""

import http.server
import socketserver
import json
import random
import os
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from urllib.parse import urlparse, parse_qs

# Configuration
LOG_FILE = "server.log"
PORT = 8000

# Sample log messages
LOG_MESSAGES = {
    "INFO": [
        "Server started successfully",
        "Request processed",
        "User logged in",
        "Configuration loaded",
        "Cache refreshed",
        "Backup completed",
        "Health check passed",
        "Database connection established",
    ],
    "WARN": [
        "High memory usage detected",
        "Slow query detected",
        "Connection timeout, retrying",
        "Cache miss",
        "Deprecated API call",
        "Rate limit approaching",
    ],
    "ERROR": [
        "Failed to connect to database",
        "Invalid request parameter",
        "File not found",
        "Authentication failed",
        "Permission denied",
        "Timeout exceeded",
        "Invalid JSON payload",
        "Network unreachable",
    ],
    "CRITICAL": [
        "Database connection lost",
        "Out of memory",
        "Disk space critical",
        "Service unavailable",
        "Security breach detected",
        "System crash imminent",
    ]
}

def generate_fake_logs(num_lines=1000):
    """Generate fake log data"""
    print(f"Generating {num_lines} lines of fake log data...")
    
    # Weight distribution: more INFO, fewer CRITICAL
    levels = ["INFO"] * 60 + ["WARN"] * 25 + ["ERROR"] * 12 + ["CRITICAL"] * 3
    
    start_time = datetime.now() - timedelta(hours=24)
    
    logs = []
    for i in range(num_lines):
        timestamp = start_time + timedelta(seconds=random.randint(0, 86400))
        level = random.choice(levels)
        message = random.choice(LOG_MESSAGES[level])
        
        log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}\n"
        logs.append(log_line)
    
    # Sort by timestamp
    logs.sort()
    
    with open(LOG_FILE, 'w') as f:
        f.writelines(logs)
    
    print(f"✓ Generated {LOG_FILE}")

def parse_logs():
    """Parse log file and extract analytics"""
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
    
    print("Parsing logs...")
    
    level_counts = Counter()
    errors_per_hour = defaultdict(int)
    error_messages = []
    critical_errors = []
    all_logs = []
    
    # Pattern: YYYY-MM-DD HH:MM:SS [LEVEL] message
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(INFO|WARN|ERROR|CRITICAL)\] (.+)'
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            match = re.match(pattern, line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                level_counts[level] += 1
                
                log_entry = {
                    'timestamp': timestamp_str,
                    'level': level,
                    'message': message
                }
                all_logs.append(log_entry)
                
                if level in ['ERROR', 'CRITICAL']:
                    hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                    errors_per_hour[hour_key] += 1
                    error_messages.append(message)
                
                if level == 'CRITICAL':
                    critical_errors.append(log_entry)
    
    total = sum(level_counts.values())
    level_percentages = {
        level: round((count / total) * 100, 2)
        for level, count in level_counts.items()
    }
    
    # Most common error messages
    common_errors = Counter(error_messages).most_common(10)
    
    # Sort errors per hour chronologically
    errors_timeline = sorted(errors_per_hour.items())
    
    print(f"✓ Parsed {total} log entries")
    
    return {
        'level_percentages': level_percentages,
        'level_counts': dict(level_counts),
        'errors_timeline': errors_timeline,
        'common_errors': common_errors,
        'critical_errors': critical_errors,
        'all_logs': all_logs,
        'total_logs': total
    }

# Global analytics data
analytics_data = None

class LogDashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for the dashboard"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_dashboard()
        elif parsed_path.path == '/api/data':
            self.serve_api_data()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the HTML dashboard"""
        html = get_dashboard_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_api_data(self):
        """Serve analytics data as JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(analytics_data).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def get_dashboard_html():
    """Generate the dashboard HTML"""
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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }
        
        .stat-percentage {
            font-size: 0.9em;
            color: #999;
            margin-top: 5px;
        }
        
        .level-info { border-left: 4px solid #3498db; }
        .level-warn { border-left: 4px solid #f39c12; }
        .level-error { border-left: 4px solid #e74c3c; }
        .level-critical { border-left: 4px solid #c0392b; }
        
        .chart-section {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .chart-title {
            font-size: 1.5em;
            color: #333;
            margin-bottom: 20px;
        }
        
        #timeline-chart {
            width: 100%;
            height: 300px;
            margin-top: 20px;
        }
        
        .error-list {
            list-style: none;
        }
        
        .error-item {
            padding: 12px;
            margin-bottom: 8px;
            background: #f8f9fa;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .error-message {
            flex: 1;
            color: #333;
        }
        
        .error-count {
            background: #e74c3c;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .controls {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .search-box {
            flex: 1;
            min-width: 250px;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
        }
        
        .search-box:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .filter-btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            background: #f0f0f0;
            color: #333;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .filter-btn:hover {
            background: #e0e0e0;
        }
        
        .filter-btn.active {
            background: #667eea;
            color: white;
        }
        
        .table-section {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .level-badge {
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .badge-info { background: #3498db; color: white; }
        .badge-warn { background: #f39c12; color: white; }
        .badge-error { background: #e74c3c; color: white; }
        .badge-critical { background: #c0392b; color: white; }
        
        .no-results {
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Log Analytics Dashboard</h1>
        
        <div class="stats-grid" id="stats-grid"></div>
        
        <div class="chart-section">
            <h2 class="chart-title">⏱️ Errors Timeline (Per Hour)</h2>
            <svg id="timeline-chart"></svg>
        </div>
        
        <div class="chart-section">
            <h2 class="chart-title">🔥 Most Common Error Messages</h2>
            <ul class="error-list" id="error-list"></ul>
        </div>
        
        <div class="controls">
            <input type="text" class="search-box" id="search-box" placeholder="🔍 Search logs...">
            <button class="filter-btn active" data-filter="ALL">All</button>
            <button class="filter-btn" data-filter="ERROR">Error</button>
            <button class="filter-btn" data-filter="CRITICAL">Critical</button>
            <button class="filter-btn" data-filter="WARN">Warning</button>
            <button class="filter-btn" data-filter="INFO">Info</button>
        </div>
        
        <div class="table-section">
            <h2 class="chart-title">📋 Log Entries</h2>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Level</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody id="log-table"></tbody>
            </table>
            <div id="no-results" class="no-results" style="display: none;">
                No logs found matching your criteria
            </div>
        </div>
    </div>
    
    <script>
        let data = null;
        let currentFilter = 'ALL';
        let searchQuery = '';
        
        // Fetch data from API
        async function loadData() {
            try {
                const response = await fetch('/api/data');
                data = await response.json();
                renderDashboard();
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }
        
        function renderDashboard() {
            renderStats();
            renderTimeline();
            renderCommonErrors();
            renderLogTable();
        }
        
        function renderStats() {
            const statsGrid = document.getElementById('stats-grid');
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            
            statsGrid.innerHTML = levels.map(level => {
                const count = data.level_counts[level] || 0;
                const percentage = data.level_percentages[level] || 0;
                const levelClass = level.toLowerCase();
                
                return `
                    <div class="stat-card level-${levelClass}">
                        <div class="stat-label">${level}</div>
                        <div class="stat-value">${count.toLocaleString()}</div>
                        <div class="stat-percentage">${percentage}% of total</div>
                    </div>
                `;
            }).join('');
        }
        
        function renderTimeline() {
            const svg = document.getElementById('timeline-chart');
            const timeline = data.errors_timeline;
            
            if (timeline.length === 0) {
                svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#999">No error data available</text>';
                return;
            }
            
            const width = svg.clientWidth;
            const height = 300;
            const padding = 50;
            
            const maxCount = Math.max(...timeline.map(([_, count]) => count));
            const xStep = (width - 2 * padding) / (timeline.length - 1 || 1);
            const yScale = (height - 2 * padding) / (maxCount || 1);
            
            // Create path for line chart
            const points = timeline.map(([timestamp, count], i) => {
                const x = padding + i * xStep;
                const y = height - padding - count * yScale;
                return `${x},${y}`;
            }).join(' ');
            
            // Create area under the line
            const areaPoints = `${padding},${height - padding} ${points} ${width - padding},${height - padding}`;
            
            svg.innerHTML = `
                <defs>
                    <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#e74c3c;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#e74c3c;stop-opacity:0" />
                    </linearGradient>
                </defs>
                
                <!-- Grid lines -->
                ${[0, 1, 2, 3, 4].map(i => {
                    const y = height - padding - (i * (height - 2 * padding) / 4);
                    return `<line x1="${padding}" y1="${y}" x2="${width - padding}" y2="${y}" stroke="#eee" stroke-width="1"/>`;
                }).join('')}
                
                <!-- Area under curve -->
                <polygon points="${areaPoints}" fill="url(#areaGradient)"/>
                
                <!-- Line -->
                <polyline points="${points}" fill="none" stroke="#e74c3c" stroke-width="3"/>
                
                <!-- Points -->
                ${timeline.map(([timestamp, count], i) => {
                    const x = padding + i * xStep;
                    const y = height - padding - count * yScale;
                    return `<circle cx="${x}" cy="${y}" r="4" fill="#c0392b"/>`;
                }).join('')}
                
                <!-- Y-axis labels -->
                ${[0, 1, 2, 3, 4].map(i => {
                    const value = Math.round((i * maxCount) / 4);
                    const y = height - padding - (i * (height - 2 * padding) / 4);
                    return `<text x="${padding - 10}" y="${y + 5}" text-anchor="end" font-size="12" fill="#666">${value}</text>`;
                }).join('')}
                
                <!-- X-axis label -->
                <text x="${width / 2}" y="${height - 10}" text-anchor="middle" font-size="12" fill="#666">Time (hourly)</text>
            `;
        }
        
        function renderCommonErrors() {
            const errorList = document.getElementById('error-list');
            const errors = data.common_errors.slice(0, 10);
            
            if (errors.length === 0) {
                errorList.innerHTML = '<li class="error-item">No errors found</li>';
                return;
            }
            
            errorList.innerHTML = errors.map(([message, count]) => `
                <li class="error-item">
                    <span class="error-message">${message}</span>
                    <span class="error-count">${count}</span>
                </li>
            `).join('');
        }
        
        function renderLogTable() {
            const tbody = document.getElementById('log-table');
            const noResults = document.getElementById('no-results');
            
            let logs = data.all_logs;
            
            // Apply filter
            if (currentFilter !== 'ALL') {
                logs = logs.filter(log => log.level === currentFilter);
            }
            
            // Apply search
            if (searchQuery) {
                const query = searchQuery.toLowerCase();
                logs = logs.filter(log => 
                    log.message.toLowerCase().includes(query) ||
                    log.timestamp.includes(query)
                );
            }
            
            if (logs.length === 0) {
                tbody.innerHTML = '';
                noResults.style.display = 'block';
                return;
            }
            
            noResults.style.display = 'none';
            
            // Show only first 100 for performance
            const displayLogs = logs.slice(0, 100);
            
            tbody.innerHTML = displayLogs.map(log => {
                const badgeClass = `badge-${log.level.toLowerCase()}`;
                return `
                    <tr>
                        <td>${log.timestamp}</td>
                        <td><span class="level-badge ${badgeClass}">${log.level}</span></td>
                        <td>${log.message}</td>
                    </tr>
                `;
            }).join('');
        }
        
        // Event listeners
        document.getElementById('search-box').addEventListener('input', (e) => {
            searchQuery = e.target.value;
            renderLogTable();
        });
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                currentFilter = e.target.dataset.filter;
                renderLogTable();
            });
        });
        
        // Load data on page load
        loadData();
    </script>
</body>
</html>"""

def main():
    """Main function to run the dashboard server"""
    global analytics_data
    
    print("=" * 60)
    print("LOG ANALYTICS DASHBOARD")
    print("=" * 60)
    
    # Parse logs and prepare analytics
    analytics_data = parse_logs()
    
    print(f"\nStarting HTTP server on port {PORT}...")
    print(f"\n✓ Dashboard URL: http://localhost:{PORT}")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Start HTTP server
    with socketserver.TCPServer(("", PORT), LogDashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✓ Server stopped")

if __name__ == "__main__":
    main()