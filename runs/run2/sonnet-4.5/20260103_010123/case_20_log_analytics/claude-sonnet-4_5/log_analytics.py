#!/usr/bin/env python3
import os
import random
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
import re

# Configuration
LOG_FILE = "server.log"
PORT = 8000

# Log level distribution (weighted for realistic logs)
LOG_LEVELS = ["INFO", "INFO", "INFO", "INFO", "WARN", "WARN", "ERROR", "CRITICAL"]
ERROR_MESSAGES = [
    "Database connection timeout",
    "Failed to authenticate user",
    "Null pointer exception in module",
    "Disk space critically low",
    "Memory allocation failed",
    "Service unavailable",
    "Invalid request format",
    "Permission denied",
    "Network timeout occurred",
    "Configuration file not found",
    "API rate limit exceeded",
    "Corrupted data detected",
    "Resource not found",
    "Cache invalidation failed",
    "Session expired",
]


def generate_fake_logs(filename, num_lines=1000):
    """Generate fake log data with timestamps over the last 24 hours."""
    print(f"Generating {num_lines} fake log entries...")
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    logs = []
    for i in range(num_lines):
        # Random timestamp within the last 24 hours
        random_seconds = random.randint(0, 24 * 3600)
        timestamp = start_time + timedelta(seconds=random_seconds)
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Random log level
        level = random.choice(LOG_LEVELS)
        
        # Generate message based on level
        if level in ["ERROR", "CRITICAL"]:
            message = random.choice(ERROR_MESSAGES)
        elif level == "WARN":
            message = random.choice([
                "High CPU usage detected",
                "Slow query performance",
                "Deprecated API usage",
                "Cache miss rate increasing",
            ])
        else:  # INFO
            message = random.choice([
                "User logged in successfully",
                "Request processed",
                "Service started",
                "Health check passed",
                "Transaction completed",
            ])
        
        log_line = f"{timestamp_str} [{level}] {message}\n"
        logs.append((timestamp, log_line))
    
    # Sort by timestamp
    logs.sort(key=lambda x: x[0])
    
    with open(filename, 'w') as f:
        for _, line in logs:
            f.write(line)
    
    print(f"Generated {filename} with {num_lines} entries")


def parse_logs(filename):
    """Parse log file and extract analytics data."""
    print(f"Parsing {filename}...")
    
    log_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(.*?)\] (.*)')
    
    logs = []
    level_counts = Counter()
    error_messages = Counter()
    errors_per_hour = defaultdict(int)
    critical_errors = []
    
    with open(filename, 'r') as f:
        for line in f:
            match = log_pattern.match(line.strip())
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
                
                # Track error messages
                if level in ["ERROR", "CRITICAL"]:
                    error_messages[message] += 1
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    errors_per_hour[hour_key] += 1
                
                # Collect critical errors for table
                if level == "CRITICAL":
                    critical_errors.append(log_entry)
    
    total_logs = sum(level_counts.values())
    level_percentages = {
        level: round((count / total_logs) * 100, 2)
        for level, count in level_counts.items()
    }
    
    # Sort errors per hour by time
    errors_timeline = sorted(errors_per_hour.items())
    
    # Get top 10 error messages
    top_errors = error_messages.most_common(10)
    
    analytics = {
        'total_logs': total_logs,
        'level_counts': dict(level_counts),
        'level_percentages': level_percentages,
        'errors_timeline': errors_timeline,
        'top_error_messages': top_errors,
        'critical_errors': critical_errors,
        'all_logs': logs
    }
    
    print(f"Parsed {total_logs} log entries")
    return analytics


class DashboardHandler(BaseHTTPRequestHandler):
    analytics_data = None
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
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
            self.wfile.write(json.dumps(self.analytics_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def get_dashboard_html(self):
        return '''<!DOCTYPE html>
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
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
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
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .chart-title {
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #333;
            font-weight: 600;
        }
        
        .chart {
            width: 100%;
            height: 300px;
        }
        
        .table-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .search-box {
            flex: 1;
            min-width: 250px;
            padding: 10px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 1em;
        }
        
        .filter-select {
            padding: 10px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 1em;
            cursor: pointer;
            background: white;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        tr:hover {
            background: #f5f5f5;
        }
        
        .level-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .level-INFO { background: #4caf50; color: white; }
        .level-WARN { background: #ff9800; color: white; }
        .level-ERROR { background: #f44336; color: white; }
        .level-CRITICAL { background: #9c27b0; color: white; }
        
        .error-list {
            list-style: none;
        }
        
        .error-item {
            padding: 10px;
            background: #f5f5f5;
            margin-bottom: 8px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .error-count {
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Log Analytics Dashboard</h1>
        
        <div class="stats-grid" id="statsGrid">
            <!-- Stats will be injected here -->
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <div class="chart-title">Log Level Distribution</div>
                <svg id="pieChart" class="chart" viewBox="0 0 400 300"></svg>
            </div>
            
            <div class="chart-card">
                <div class="chart-title">Errors Over Time</div>
                <svg id="timelineChart" class="chart" viewBox="0 0 500 300"></svg>
            </div>
        </div>
        
        <div class="chart-card">
            <div class="chart-title">Top Error Messages</div>
            <ul class="error-list" id="errorList"></ul>
        </div>
        
        <div class="table-card">
            <div class="chart-title">Log Entries</div>
            <div class="controls">
                <input type="text" class="search-box" id="searchBox" placeholder="Search logs...">
                <select class="filter-select" id="levelFilter">
                    <option value="all">All Levels</option>
                    <option value="INFO">INFO</option>
                    <option value="WARN">WARN</option>
                    <option value="ERROR">ERROR</option>
                    <option value="CRITICAL">CRITICAL</option>
                </select>
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
                    <tbody id="logTable">
                        <!-- Table rows will be injected here -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let analyticsData = null;
        let filteredLogs = [];
        
        // Fetch data from API
        fetch('/api/data')
            .then(response => response.json())
            .then(data => {
                analyticsData = data;
                initDashboard();
            })
            .catch(error => console.error('Error loading data:', error));
        
        function initDashboard() {
            renderStats();
            renderPieChart();
            renderTimelineChart();
            renderErrorList();
            filteredLogs = analyticsData.all_logs;
            renderTable();
            setupEventListeners();
        }
        
        function renderStats() {
            const stats = [
                { label: 'Total Logs', value: analyticsData.total_logs },
                { label: 'INFO', value: analyticsData.level_counts.INFO || 0 },
                { label: 'WARN', value: analyticsData.level_counts.WARN || 0 },
                { label: 'ERROR', value: analyticsData.level_counts.ERROR || 0 },
                { label: 'CRITICAL', value: analyticsData.level_counts.CRITICAL || 0 }
            ];
            
            const statsGrid = document.getElementById('statsGrid');
            statsGrid.innerHTML = stats.map(stat => `
                <div class="stat-card">
                    <div class="stat-value">${stat.value}</div>
                    <div class="stat-label">${stat.label}</div>
                </div>
            `).join('');
        }
        
        function renderPieChart() {
            const svg = document.getElementById('pieChart');
            const centerX = 200;
            const centerY = 150;
            const radius = 100;
            
            const colors = {
                'INFO': '#4caf50',
                'WARN': '#ff9800',
                'ERROR': '#f44336',
                'CRITICAL': '#9c27b0'
            };
            
            const data = Object.entries(analyticsData.level_counts)
                .map(([level, count]) => ({
                    level,
                    count,
                    percentage: analyticsData.level_percentages[level]
                }));
            
            let currentAngle = 0;
            
            data.forEach(item => {
                const sliceAngle = (item.percentage / 100) * 2 * Math.PI;
                const endAngle = currentAngle + sliceAngle;
                
                const x1 = centerX + radius * Math.cos(currentAngle);
                const y1 = centerY + radius * Math.sin(currentAngle);
                const x2 = centerX + radius * Math.cos(endAngle);
                const y2 = centerY + radius * Math.sin(endAngle);
                
                const largeArc = sliceAngle > Math.PI ? 1 : 0;
                
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', `
                    M ${centerX} ${centerY}
                    L ${x1} ${y1}
                    A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}
                    Z
                `);
                path.setAttribute('fill', colors[item.level] || '#ccc');
                path.setAttribute('stroke', 'white');
                path.setAttribute('stroke-width', '2');
                
                svg.appendChild(path);
                
                // Add label
                const labelAngle = currentAngle + sliceAngle / 2;
                const labelX = centerX + (radius * 0.7) * Math.cos(labelAngle);
                const labelY = centerY + (radius * 0.7) * Math.sin(labelAngle);
                
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', labelX);
                text.setAttribute('y', labelY);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('dominant-baseline', 'middle');
                text.setAttribute('fill', 'white');
                text.setAttribute('font-weight', 'bold');
                text.setAttribute('font-size', '12');
                text.textContent = `${item.percentage}%`;
                
                svg.appendChild(text);
                
                currentAngle = endAngle;
            });
            
            // Add legend
            let legendY = 20;
            data.forEach(item => {
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', 320);
                rect.setAttribute('y', legendY);
                rect.setAttribute('width', 15);
                rect.setAttribute('height', 15);
                rect.setAttribute('fill', colors[item.level]);
                svg.appendChild(rect);
                
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', 340);
                text.setAttribute('y', legendY + 12);
                text.setAttribute('font-size', '12');
                text.textContent = item.level;
                svg.appendChild(text);
                
                legendY += 25;
            });
        }
        
        function renderTimelineChart() {
            const svg = document.getElementById('timelineChart');
            const timeline = analyticsData.errors_timeline;
            
            if (timeline.length === 0) return;
            
            const padding = 40;
            const chartWidth = 500 - 2 * padding;
            const chartHeight = 300 - 2 * padding;
            
            const maxErrors = Math.max(...timeline.map(t => t[1]));
            const xStep = chartWidth / (timeline.length - 1 || 1);
            
            // Draw axes
            const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            xAxis.setAttribute('x1', padding);
            xAxis.setAttribute('y1', 300 - padding);
            xAxis.setAttribute('x2', 500 - padding);
            xAxis.setAttribute('y2', 300 - padding);
            xAxis.setAttribute('stroke', '#333');
            xAxis.setAttribute('stroke-width', '2');
            svg.appendChild(xAxis);
            
            const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            yAxis.setAttribute('x1', padding);
            yAxis.setAttribute('y1', padding);
            yAxis.setAttribute('x2', padding);
            yAxis.setAttribute('y2', 300 - padding);
            yAxis.setAttribute('stroke', '#333');
            yAxis.setAttribute('stroke-width', '2');
            svg.appendChild(yAxis);
            
            // Draw line
            let pathData = '';
            timeline.forEach((point, index) => {
                const x = padding + index * xStep;
                const y = 300 - padding - (point[1] / maxErrors) * chartHeight;
                
                if (index === 0) {
                    pathData += `M ${x} ${y}`;
                } else {
                    pathData += ` L ${x} ${y}`;
                }
                
                // Draw point
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', x);
                circle.setAttribute('cy', y);
                circle.setAttribute('r', 4);
                circle.setAttribute('fill', '#667eea');
                svg.appendChild(circle);
            });
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', pathData);
            path.setAttribute('stroke', '#667eea');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('fill', 'none');
            svg.appendChild(path);
            
            // Y-axis label
            const yLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            yLabel.setAttribute('x', 10);
            yLabel.setAttribute('y', 20);
            yLabel.setAttribute('font-size', '12');
            yLabel.textContent = 'Errors';
            svg.appendChild(yLabel);
            
            // X-axis label
            const xLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            xLabel.setAttribute('x', 240);
            xLabel.setAttribute('y', 290);
            xLabel.setAttribute('font-size', '12');
            xLabel.textContent = 'Time (Hourly)';
            svg.appendChild(xLabel);
        }
        
        function renderErrorList() {
            const list = document.getElementById('errorList');
            const topErrors = analyticsData.top_error_messages;
            
            list.innerHTML = topErrors.map(([message, count]) => `
                <li class="error-item">
                    <span>${message}</span>
                    <span class="error-count">${count}</span>
                </li>
            `).join('');
        }
        
        function renderTable() {
            const tbody = document.getElementById('logTable');
            const displayLogs = filteredLogs.slice(0, 100); // Limit to 100 for performance
            
            tbody.innerHTML = displayLogs.map(log => `
                <tr>
                    <td>${log.timestamp}</td>
                    <td><span class="level-badge level-${log.level}">${log.level}</span></td>
                    <td>${log.message}</td>
                </tr>
            `).join('');
        }
        
        function setupEventListeners() {
            const searchBox = document.getElementById('searchBox');
            const levelFilter = document.getElementById('levelFilter');
            
            searchBox.addEventListener('input', filterLogs);
            levelFilter.addEventListener('change', filterLogs);
        }
        
        function filterLogs() {
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const levelFilter = document.getElementById('levelFilter').value;
            
            filteredLogs = analyticsData.all_logs.filter(log => {
                const matchesSearch = !searchTerm || 
                    log.message.toLowerCase().includes(searchTerm) ||
                    log.timestamp.includes(searchTerm);
                
                const matchesLevel = levelFilter === 'all' || log.level === levelFilter;
                
                return matchesSearch && matchesLevel;
            });
            
            renderTable();
        }
    </script>
</body>
</html>'''


def main():
    # Check if log file exists, generate if not
    if not os.path.exists(LOG_FILE):
        print(f"{LOG_FILE} not found.")
        generate_fake_logs(LOG_FILE, 1000)
    else:
        print(f"Found existing {LOG_FILE}")
    
    # Parse logs
    analytics = parse_logs(LOG_FILE)
    
    # Set analytics data for handler
    DashboardHandler.analytics_data = analytics
    
    # Start HTTP server
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, DashboardHandler)
    
    print(f"\n{'='*60}")
    print(f"🚀 Log Analytics Dashboard is running!")
    print(f"{'='*60}")
    print(f"\n📊 Dashboard URL: http://localhost:{PORT}")
    print(f"\n📈 Statistics:")
    print(f"   - Total logs: {analytics['total_logs']}")
    print(f"   - INFO: {analytics['level_counts'].get('INFO', 0)}")
    print(f"   - WARN: {analytics['level_counts'].get('WARN', 0)}")
    print(f"   - ERROR: {analytics['level_counts'].get('ERROR', 0)}")
    print(f"   - CRITICAL: {analytics['level_counts'].get('CRITICAL', 0)}")
    print(f"\n⏸️  Press Ctrl+C to stop the server\n")
    print(f"{'='*60}\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down server...")
        httpd.shutdown()
        print("✅ Server stopped successfully")


if __name__ == "__main__":
    main()