#!/usr/bin/env python3
"""
Log Analytics Dashboard
Generates fake log data, analyzes it, and serves an interactive dashboard
"""

import os
import json
import random
import datetime
from collections import defaultdict, Counter
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time
import sys

# Configuration
LOG_FILE = "server.log"
NUM_LOG_LINES = 1000
DASHBOARD_PORT = 8080

# Log level distribution
LOG_LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]
LOG_LEVEL_WEIGHTS = [0.60, 0.25, 0.10, 0.05]

# Sample error messages
ERROR_MESSAGES = [
    "Database connection timeout",
    "Authentication failed",
    "Memory allocation failed",
    "File not found",
    "Permission denied",
    "Network unreachable",
    "Invalid configuration",
    "Service unavailable",
    "Request timeout",
    "Disk space low",
    "CPU usage critical",
    "SSL certificate error",
    "DNS resolution failed",
    "Port already in use",
    "Process crashed unexpectedly",
]

# Sample info/warn messages
INFO_MESSAGES = [
    "Server started successfully",
    "User login successful",
    "Cache cleared",
    "Backup completed",
    "Configuration reloaded",
    "Health check passed",
    "Database query executed",
    "API request processed",
    "File uploaded",
    "Job scheduled",
]

WARN_MESSAGES = [
    "High memory usage detected",
    "Slow query detected",
    "Deprecated API usage",
    "Connection pool nearly exhausted",
    "Retry attempt 1 of 3",
    "Rate limit approaching",
    "Certificate expires in 30 days",
    "Disk usage at 80%",
    "Unusual activity detected",
    "Performance degradation",
]


def generate_fake_logs(num_lines=NUM_LOG_LINES):
    """Generate fake log data"""
    print(f"Generating {num_lines} fake log lines...")
    
    # Start from 24 hours ago
    start_time = datetime.datetime.now() - datetime.timedelta(hours=24)
    
    logs = []
    for i in range(num_lines):
        # Distribute logs evenly over 24 hours
        timestamp = start_time + datetime.timedelta(
            seconds=(86400 * i / num_lines)
        )
        
        # Choose log level based on weights
        level = random.choices(LOG_LEVELS, weights=LOG_LEVEL_WEIGHTS)[0]
        
        # Choose message based on level
        if level == "INFO":
            message = random.choice(INFO_MESSAGES)
        elif level == "WARN":
            message = random.choice(WARN_MESSAGES)
        elif level == "ERROR":
            message = random.choice(ERROR_MESSAGES)
        else:  # CRITICAL
            message = random.choice(ERROR_MESSAGES)
            message = f"CRITICAL: {message}"
        
        # Add optional details
        if random.random() > 0.7:
            details = f" [Code: {random.randint(100, 999)}]"
            message += details
        
        log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}\n"
        logs.append(log_line)
    
    with open(LOG_FILE, 'w') as f:
        f.writelines(logs)
    
    print(f"Generated {LOG_FILE} with {num_lines} lines")


def parse_logs():
    """Parse log file and extract analytics"""
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
    
    print("Parsing logs...")
    
    level_counts = defaultdict(int)
    errors_by_hour = defaultdict(int)
    critical_errors = []
    error_messages = []
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Parse log line: YYYY-MM-DD HH:MM:SS [LEVEL] message
            try:
                parts = line.split(' [')
                if len(parts) < 2:
                    continue
                
                timestamp_str = parts[0]
                level_and_msg = parts[1]
                
                # Extract level
                level = level_and_msg.split(']')[0]
                message = ']'.join(level_and_msg.split(']')[1:]).strip()
                
                # Count by level
                level_counts[level] += 1
                
                # Extract hour from timestamp
                try:
                    dt = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    hour_key = dt.strftime('%Y-%m-%d %H:00')
                    
                    if level in ["ERROR", "CRITICAL"]:
                        errors_by_hour[hour_key] += 1
                    
                    if level == "CRITICAL":
                        critical_errors.append({
                            "timestamp": timestamp_str,
                            "message": message,
                            "level": level
                        })
                    
                    if level in ["ERROR", "CRITICAL"]:
                        error_messages.append(message)
                except ValueError:
                    pass
                
            except (IndexError, ValueError):
                continue
    
    # Calculate percentages
    total = sum(level_counts.values())
    level_percentages = {
        level: (count / total * 100) if total > 0 else 0
        for level, count in level_counts.items()
    }
    
    # Get most common error messages
    most_common_errors = Counter(error_messages).most_common(10)
    
    # Sort errors by hour
    sorted_errors_by_hour = sorted(errors_by_hour.items())
    
    analytics = {
        "level_percentages": level_percentages,
        "level_counts": dict(level_counts),
        "total_logs": total,
        "errors_by_hour": sorted_errors_by_hour,
        "critical_errors": critical_errors,
        "most_common_errors": [
            {"message": msg, "count": count}
            for msg, count in most_common_errors
        ]
    }
    
    print(f"Parsed {total} log lines")
    return analytics


class AnalyticsRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for the dashboard"""
    
    analytics_data = {}
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.serve_dashboard()
        elif self.path == '/api/analytics':
            self.serve_analytics()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(get_dashboard_html().encode('utf-8'))
    
    def serve_analytics(self):
        """Serve analytics data as JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(self.analytics_data).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def get_dashboard_html():
    """Return the dashboard HTML"""
    return """
<!DOCTYPE html>
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
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .header p {
            color: #666;
            font-size: 14px;
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
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .stat-card h3 {
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-info {
            font-size: 12px;
            color: #999;
        }
        
        .info { color: #3498db; }
        .warn { color: #f39c12; }
        .error { color: #e74c3c; }
        .critical { color: #c0392b; }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .chart-container h2 {
            color: #333;
            font-size: 16px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        svg {
            width: 100%;
            height: auto;
        }
        
        .full-width {
            grid-column: 1 / -1;
        }
        
        .filters {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: 2px solid #ddd;
            background: white;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .filter-btn:hover {
            border-color: #667eea;
            color: #667eea;
        }
        
        .filter-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .search-box {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            margin-bottom: 15px;
        }
        
        .search-box:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .table-container {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        
        th {
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e0e0e0;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .timestamp {
            color: #999;
            font-family: 'Courier New', monospace;
        }
        
        .message {
            color: #333;
            word-break: break-word;
        }
        
        .level-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
        }
        
        .level-badge.critical {
            background: #c0392b;
            color: white;
        }
        
        .level-badge.error {
            background: #e74c3c;
            color: white;
        }
        
        .level-badge.warn {
            background: #f39c12;
            color: white;
        }
        
        .level-badge.info {
            background: #3498db;
            color: white;
        }
        
        .loading {
            text-align: center;
            color: #999;
            padding: 40px;
        }
        
        .error-message {
            background: #fee;
            color: #c00;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
            
            .stat-card h3 {
                font-size: 10px;
            }
            
            .stat-value {
                font-size: 24px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Log Analytics Dashboard</h1>
            <p>Real-time analysis of server logs</p>
        </div>
        
        <div class="stats-grid" id="statsGrid">
            <div class="loading">Loading analytics...</div>
        </div>
        
        <div class="charts-grid" id="chartsGrid">
            <div class="loading">Loading charts...</div>
        </div>
        
        <div class="chart-container full-width">
            <h2>🚨 Critical Errors</h2>
            <input type="text" class="search-box" id="searchBox" placeholder="Search critical errors...">
            <div class="filters">
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="error">Errors</button>
                <button class="filter-btn" data-filter="critical">Critical</button>
            </div>
            <div class="table-container">
                <table id="errorsTable">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Level</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody id="errorsTableBody">
                        <tr><td colspan="3" class="loading">Loading errors...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let analyticsData = null;
        let currentFilter = 'all';
        let currentSearch = '';
        
        async function loadAnalytics() {
            try {
                const response = await fetch('/api/analytics');
                analyticsData = await response.json();
                renderDashboard();
            } catch (error) {
                console.error('Error loading analytics:', error);
                document.getElementById('statsGrid').innerHTML = 
                    '<div class="error-message">Failed to load analytics data</div>';
            }
        }
        
        function renderDashboard() {
            renderStats();
            renderCharts();
            renderErrorsTable();
        }
        
        function renderStats() {
            const grid = document.getElementById('statsGrid');
            const data = analyticsData.level_percentages;
            const counts = analyticsData.level_counts;
            
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            let html = '';
            
            for (const level of levels) {
                const percentage = (data[level] || 0).toFixed(1);
                const count = counts[level] || 0;
                html += `
                    <div class="stat-card">
                        <h3>${level}</h3>
                        <div class="stat-value ${level.toLowerCase()}">${percentage}%</div>
                        <div class="stat-info">${count} entries</div>
                    </div>
                `;
            }
            
            grid.innerHTML = html;
        }
        
        function renderCharts() {
            const grid = document.getElementById('chartsGrid');
            grid.innerHTML = '';
            
            // Pie chart for log levels
            grid.appendChild(createPieChart());
            
            // Timeline chart for errors
            grid.appendChild(createTimelineChart());
            
            // Top errors chart
            grid.appendChild(createTopErrorsChart());
        }
        
        function createPieChart() {
            const container = document.createElement('div');
            container.className = 'chart-container';
            container.innerHTML = '<h2>📈 Log Level Distribution</h2>';
            
            const data = analyticsData.level_percentages;
            const colors = {
                'INFO': '#3498db',
                'WARN': '#f39c12',
                'ERROR': '#e74c3c',
                'CRITICAL': '#c0392b'
            };
            
            const svg = createPieChartSVG(data, colors);
            container.appendChild(svg);
            
            return container;
        }
        
        function createPieChartSVG(data, colors) {
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('viewBox', '0 0 300 300');
            
            const centerX = 150;
            const centerY = 150;
            const radius = 100;
            
            let currentAngle = -Math.PI / 2;
            
            for (const [level, percentage] of Object.entries(data)) {
                const sliceAngle = (percentage / 100) * 2 * Math.PI;
                const x1 = centerX + radius * Math.cos(currentAngle);
                const y1 = centerY + radius * Math.sin(currentAngle);
                const x2 = centerX + radius * Math.cos(currentAngle + sliceAngle);
                const y2 = centerY + radius * Math.sin(currentAngle + sliceAngle);
                
                const largeArc = sliceAngle > Math.PI ? 1 : 0;
                const pathData = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
                
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', pathData);
                path.setAttribute('fill', colors[level]);
                path.setAttribute('stroke', 'white');
                path.setAttribute('stroke-width', '2');
                svg.appendChild(path);
                
                // Add label
                const labelAngle = currentAngle + sliceAngle / 2;
                const labelRadius = radius * 0.65;
                const labelX = centerX + labelRadius * Math.cos(labelAngle);
                const labelY = centerY + labelRadius * Math.sin(labelAngle);
                
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', labelX);
                text.setAttribute('y', labelY);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('dominant-baseline', 'middle');
                text.setAttribute('fill', 'white');
                text.setAttribute('font-weight', 'bold');
                text.setAttribute('font-size', '14');
                text.textContent = `${percentage.toFixed(0)}%`;
                svg.appendChild(text);
                
                currentAngle += sliceAngle;
            }
            
            return svg;
        }
        
        function createTimelineChart() {
            const container = document.createElement('div');
            container.className = 'chart-container';
            container.innerHTML = '<h2>⏱️ Errors Over Time</h2>';
            
            const data = analyticsData.errors_by_hour;
            if (data.length === 0) {
                container.innerHTML += '<p style="color: #999; text-align: center; padding: 40px;">No error data available</p>';
                return container;
            }
            
            const svg = createTimelineChartSVG(data);
            container.appendChild(svg);
            
            return container;
        }
        
        function createTimelineChartSVG(data) {
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('viewBox', '0 0 600 300');
            
            const padding = 40;
            const width = 600 - 2 * padding;
            const height = 300 - 2 * padding;
            
            const maxErrors = Math.max(...data.map(d => d[1]));
            const pointCount = data.length;
            
            // Draw axes
            const xAxisLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            xAxisLine.setAttribute('x1', padding);
            xAxisLine.setAttribute('y1', padding + height);
            xAxisLine.setAttribute('x2', padding + width);
            xAxisLine.setAttribute('y2', padding + height);
            xAxisLine.setAttribute('stroke', '#ddd');
            xAxisLine.setAttribute('stroke-width', '2');
            svg.appendChild(xAxisLine);
            
            const yAxisLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            yAxisLine.setAttribute('x1', padding);
            yAxisLine.setAttribute('y1', padding);
            yAxisLine.setAttribute('x2', padding);
            yAxisLine.setAttribute('y2', padding + height);
            yAxisLine.setAttribute('stroke', '#ddd');
            yAxisLine.setAttribute('stroke-width', '2');
            svg.appendChild(yAxisLine);
            
            // Draw points and lines
            let pathData = '';
            for (let i = 0; i < pointCount; i++) {
                const x = padding + (i / (pointCount - 1 || 1)) * width;
                const y = padding + height - (data[i][1] / maxErrors) * height;
                
                if (i === 0) {
                    pathData = `M ${x} ${y}`;
                } else {
                    pathData += ` L ${x} ${y}`;
                }
                
                // Draw point
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', x);
                circle.setAttribute('cy', y);
                circle.setAttribute('r', '4');
                circle.setAttribute('fill', '#e74c3c');
                svg.appendChild(circle);
            }
            
            // Draw line
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', pathData);
            path.setAttribute('stroke', '#e74c3c');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('fill', 'none');
            svg.appendChild(path);
            
            // Add Y-axis label
            const yLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            yLabel.setAttribute('x', 10);
            yLabel.setAttribute('y', padding + height / 2);
            yLabel.setAttribute('font-size', '12');
            yLabel.setAttribute('fill', '#999');
            yLabel.textContent = 'Errors';
            svg.appendChild(yLabel);
            
            return svg;
        }
        
        function createTopErrorsChart() {
            const container = document.createElement('div');
            container.className = 'chart-container';
            container.innerHTML = '<h2>🔥 Top Error Messages</h2>';
            
            const data = analyticsData.most_common_errors.slice(0, 8);
            if (data.length === 0) {
                container.innerHTML += '<p style="color: #999; text-align: center; padding: 40px;">No error data available</p>';
                return container;
            }
            
            const svg = createBarChartSVG(data);
            container.appendChild(svg);
            
            return container;
        }
        
        function createBarChartSVG(data) {
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('viewBox', '0 0 600 300');
            
            const padding = 40;
            const width = 600 - 2 * padding;
            const height = 300 - 2 * padding;
            
            const maxCount = Math.max(...data.map(d => d.count));
            const barWidth = width / data.length;
            
            for (let i = 0; i < data.length; i++) {
                const barHeight = (data[i].count / maxCount) * height;
                const x = padding + i * barWidth;
                const y = padding + height - barHeight;
                
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', x + 5);
                rect.setAttribute('y', y);
                rect.setAttribute('width', barWidth - 10);
                rect.setAttribute('height', barHeight);
                rect.setAttribute('fill', '#667eea');
                svg.appendChild(rect);
                
                // Add count label
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', x + barWidth / 2);
                text.setAttribute('y', y - 5);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('font-size', '11');
                text.setAttribute('fill', '#333');
                text.textContent = data[i].count;
                svg.appendChild(text);
            }
            
            return svg;
        }
        
        function renderErrorsTable() {
            const errors = analyticsData.critical_errors;
            const tbody = document.getElementById('errorsTableBody');
            
            updateErrorsTable(errors);
        }
        
        function updateErrorsTable(errors) {
            const tbody = document.getElementById('errorsTableBody');
            
            let filtered = errors.filter(err => {
                const matchesFilter = currentFilter === 'all' || err.level.toLowerCase() === currentFilter;
                const matchesSearch = err.message.toLowerCase().includes(currentSearch.toLowerCase()) ||
                                    err.timestamp.toLowerCase().includes(currentSearch.toLowerCase());
                return matchesFilter && matchesSearch;
            });
            
            if (filtered.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #999;">No errors found</td></tr>';
                return;
            }
            
            tbody.innerHTML = filtered.map(err => `
                <tr>
                    <td class="timestamp">${err.timestamp}</td>
                    <td><span class="level-badge ${err.level.toLowerCase()}">${err.level}</span></td>
                    <td class="message">${escapeHtml(err.message)}</td>
                </tr>
            `).join('');
        }
        
        function escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
        }
        
        // Event listeners
        document.getElementById('searchBox').addEventListener('input', (e) => {
            currentSearch = e.target.value;
            updateErrorsTable(analyticsData.critical_errors);
        });
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                currentFilter = e.target.dataset.filter;
                updateErrorsTable(analyticsData.critical_errors);
            });
        });
        
        // Load analytics on page load
        loadAnalytics();
        
        // Refresh analytics every 30 seconds
        setInterval(loadAnalytics, 30000);
    </script>
</body>
</html>
"""


def start_server(port=DASHBOARD_PORT):
    """Start the HTTP server"""
    AnalyticsRequestHandler.analytics_data = parse_logs()
    
    server = HTTPServer(('localhost', port), AnalyticsRequestHandler)
    
    print(f"\n{'='*60}")
    print(f"✅ Log Analytics Dashboard Started!")
    print(f"{'='*60}")
    print(f"🌐 Open your browser and go to: http://localhost:{port}/")
    print(f"{'='*60}")
    print(f"Press Ctrl+C to stop the server\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped.")
        server.shutdown()


def main():
    """Main entry point"""
    # Check if log file exists, if not generate it
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
    
    # Start the server
    start_server()


if __name__ == '__main__':
    main()