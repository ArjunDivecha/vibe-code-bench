#!/usr/bin/env python3
"""
Log Analytics Dashboard
A Python script that analyzes log files and serves an interactive dashboard.
"""

import http.server
import socketserver
import json
import os
import re
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import urllib.parse

# Configuration
LOG_FILE = 'server.log'
PORT = 8000
FAKE_LOG_LINES = 1000

# Log levels
LOG_LEVELS = ['INFO', 'WARN', 'ERROR', 'CRITICAL']

# Fake log messages for different levels
FAKE_MESSAGES = {
    'INFO': [
        'User login successful',
        'Request processed',
        'Data synchronized',
        'Cache refreshed',
        'Service started',
        'Connection established',
        'File uploaded',
        'Backup completed',
        'Task scheduled',
        'Configuration loaded'
    ],
    'WARN': [
        'High memory usage detected',
        'Slow query execution',
        'Connection timeout warning',
        'Disk space low',
        'Rate limit approaching',
        'Deprecated API usage',
        'Response time above threshold',
        'Cache miss rate high',
        'Retry attempt initiated',
        'Unusual traffic pattern'
    ],
    'ERROR': [
        'Failed to connect to database',
        'Null pointer exception',
        'File not found',
        'Permission denied',
        'Invalid API key',
        'Timeout while fetching data',
        'Failed to parse JSON',
        'Connection refused',
        'Service unavailable',
        'Authentication failed'
    ],
    'CRITICAL': [
        'System crash imminent',
        'Database connection lost',
        'Out of memory',
        'Disk full',
        'Security breach detected',
        'Core service stopped',
        'Data corruption detected',
        'Network partition',
        'Fatal error in main process',
        'Cannot recover from error'
    ]
}


def generate_fake_log():
    """Generate fake log data."""
    print(f"Generating {FAKE_LOG_LINES} lines of fake log data...")
    
    # Generate timestamps over the last 7 days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    with open(LOG_FILE, 'w') as f:
        for _ in range(FAKE_LOG_LINES):
            # Random timestamp
            timestamp = start_time + timedelta(
                seconds=random.randint(0, int((end_time - start_time).total_seconds()))
            )
            
            # Weighted random log level (more INFO, fewer CRITICAL)
            weights = [0.6, 0.25, 0.1, 0.05]
            level = random.choices(LOG_LEVELS, weights=weights)[0]
            
            # Random message
            message = random.choice(FAKE_MESSAGES[level])
            
            # Format: 2024-01-15 14:30:45 [INFO] Message here
            log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}\n"
            f.write(log_line)
    
    print(f"Fake log data written to {LOG_FILE}")


def parse_logs():
    """Parse the log file and extract analytics."""
    if not os.path.exists(LOG_FILE):
        generate_fake_log()
    
    print(f"Parsing {LOG_FILE}...")
    
    level_counts = Counter()
    errors_per_hour = defaultdict(int)
    critical_errors = []
    error_messages = Counter()
    
    log_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (.+)$')
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                
                level_counts[level] += 1
                
                # Parse timestamp
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                    
                    if level in ['ERROR', 'CRITICAL']:
                        errors_per_hour[hour_key] += 1
                        error_messages[message] += 1
                        
                        if level == 'CRITICAL':
                            critical_errors.append({
                                'timestamp': timestamp_str,
                                'message': message
                            })
                except ValueError:
                    continue
    
    # Calculate percentages
    total = sum(level_counts.values())
    level_percentages = {
        level: (count / total * 100) if total > 0 else 0
        for level, count in level_counts.items()
    }
    
    # Sort errors per hour chronologically
    sorted_errors_per_hour = dict(sorted(errors_per_hour.items()))
    
    # Get top error messages
    top_errors = error_messages.most_common(10)
    
    # Sort critical errors by timestamp (newest first)
    critical_errors.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return {
        'level_percentages': level_percentages,
        'level_counts': dict(level_counts),
        'errors_per_hour': sorted_errors_per_hour,
        'top_errors': top_errors,
        'critical_errors': critical_errors,
        'total_logs': total
    }


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler that serves the dashboard."""
    
    analytics_data = None
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/api/analytics':
            self.send_json_response(self.analytics_data)
        elif parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.serve_dashboard()
        else:
            self.send_error(404, 'File not found')
    
    def send_json_response(self, data):
        """Send a JSON response."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def serve_dashboard(self):
        """Serve the dashboard HTML."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = self.get_dashboard_html()
        self.wfile.write(html.encode('utf-8'))
    
    def get_dashboard_html(self):
        """Generate the dashboard HTML."""
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e4e4e7;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid #3f3f46;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: #a1a1aa;
            margin-top: 10px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(39, 39, 42, 0.8);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #3f3f46;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        .stat-card.info { border-left: 4px solid #60a5fa; }
        .stat-card.warn { border-left: 4px solid #fbbf24; }
        .stat-card.error { border-left: 4px solid #f87171; }
        .stat-card.critical { border-left: 4px solid #f43f5e; }
        
        .stat-label {
            font-size: 0.875rem;
            color: #a1a1aa;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-top: 10px;
        }
        
        .stat-percentage {
            font-size: 1rem;
            color: #71717a;
            margin-top: 5px;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: rgba(39, 39, 42, 0.8);
            border-radius: 12px;
            padding: 25px;
            border: 1px solid #3f3f46;
        }
        
        .chart-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: #f4f4f5;
        }
        
        .chart-container {
            height: 300px;
            position: relative;
        }
        
        svg {
            width: 100%;
            height: 100%;
        }
        
        .bar {
            transition: fill-opacity 0.2s;
        }
        
        .bar:hover {
            fill-opacity: 0.8;
        }
        
        .axis-label {
            fill: #71717a;
            font-size: 12px;
        }
        
        .grid-line {
            stroke: #3f3f46;
            stroke-dasharray: 4;
        }
        
        .errors-section {
            background: rgba(39, 39, 42, 0.8);
            border-radius: 12px;
            padding: 25px;
            border: 1px solid #3f3f46;
        }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .search-box {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        input[type="text"] {
            background: #27272a;
            border: 1px solid #3f3f46;
            border-radius: 8px;
            padding: 10px 15px;
            color: #e4e4e7;
            font-size: 0.9rem;
            width: 250px;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #60a5fa;
        }
        
        select {
            background: #27272a;
            border: 1px solid #3f3f46;
            border-radius: 8px;
            padding: 10px 15px;
            color: #e4e4e7;
            font-size: 0.9rem;
            cursor: pointer;
        }
        
        select:focus {
            outline: none;
            border-color: #60a5fa;
        }
        
        .errors-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .errors-table th {
            text-align: left;
            padding: 15px;
            background: #27272a;
            color: #a1a1aa;
            font-weight: 600;
            border-bottom: 2px solid #3f3f46;
        }
        
        .errors-table td {
            padding: 15px;
            border-bottom: 1px solid #3f3f46;
        }
        
        .errors-table tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        
        .level-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .level-badge.error { background: rgba(248, 113, 113, 0.2); color: #f87171; }
        .level-badge.critical { background: rgba(244, 63, 94, 0.2); color: #f43f5e; }
        
        .timestamp {
            color: #a1a1aa;
            font-family: 'Courier New', monospace;
        }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #71717a;
        }
        
        .pie-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 20px;
            justify-content: center;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }
        
        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
            
            .section-header {
                flex-direction: column;
                align-items: flex-start;
            }
            
            input[type="text"] {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Log Analytics Dashboard</h1>
            <p class="subtitle">Real-time log monitoring and analysis</p>
        </header>
        
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card info">
                <div class="stat-label">INFO</div>
                <div class="stat-value" id="infoValue">-</div>
                <div class="stat-percentage" id="infoPercent">-</div>
            </div>
            <div class="stat-card warn">
                <div class="stat-label">WARN</div>
                <div class="stat-value" id="warnValue">-</div>
                <div class="stat-percentage" id="warnPercent">-</div>
            </div>
            <div class="stat-card error">
                <div class="stat-label">ERROR</div>
                <div class="stat-value" id="errorValue">-</div>
                <div class="stat-percentage" id="errorPercent">-</div>
            </div>
            <div class="stat-card critical">
                <div class="stat-label">CRITICAL</div>
                <div class="stat-value" id="criticalValue">-</div>
                <div class="stat-percentage" id="criticalPercent">-</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h2 class="chart-title">Log Level Distribution</h2>
                <div class="chart-container" id="pieChart"></div>
                <div class="pie-legend">
                    <div class="legend-item">
                        <div class="legend-color" style="background: #60a5fa;"></div>
                        <span>INFO</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #fbbf24;"></div>
                        <span>WARN</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #f87171;"></div>
                        <span>ERROR</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #f43f5e;"></div>
                        <span>CRITICAL</span>
                    </div>
                </div>
            </div>
            
            <div class="chart-card">
                <h2 class="chart-title">Errors Per Hour</h2>
                <div class="chart-container" id="barChart"></div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h2 class="chart-title">Top Error Messages</h2>
                <div class="chart-container" id="topErrorsChart"></div>
            </div>
        </div>
        
        <div class="errors-section">
            <div class="section-header">
                <h2 class="chart-title">Critical Errors & Alerts</h2>
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Search errors...">
                    <select id="levelFilter">
                        <option value="all">All Levels</option>
                        <option value="CRITICAL">Critical Only</option>
                        <option value="ERROR">Error Only</option>
                    </select>
                </div>
            </div>
            <table class="errors-table">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Level</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody id="errorsTableBody">
                    <tr>
                        <td colspan="3" class="no-data">Loading...</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        let analyticsData = null;
        let allErrors = [];
        
        // Fetch analytics data
        async function fetchAnalytics() {
            try {
                const response = await fetch('/api/analytics');
                analyticsData = await response.json();
                updateDashboard();
            } catch (error) {
                console.error('Failed to fetch analytics:', error);
            }
        }
        
        // Update dashboard with data
        function updateDashboard() {
            updateStats();
            drawPieChart();
            drawBarChart();
            drawTopErrorsChart();
            updateErrorsTable();
        }
        
        // Update statistics cards
        function updateStats() {
            const percentages = analyticsData.level_percentages;
            const counts = analyticsData.level_counts;
            
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const levelIds = {
                'INFO': 'info',
                'WARN': 'warn',
                'ERROR': 'error',
                'CRITICAL': 'critical'
            };
            
            levels.forEach(level => {
                const id = levelIds[level];
                const valueEl = document.getElementById(id + 'Value');
                const percentEl = document.getElementById(id + 'Percent');
                
                valueEl.textContent = counts[level] || 0;
                percentEl.textContent = `${(percentages[level] || 0).toFixed(1)}%`;
            });
        }
        
        // Draw pie chart
        function drawPieChart() {
            const percentages = analyticsData.level_percentages;
            const colors = {
                'INFO': '#60a5fa',
                'WARN': '#fbbf24',
                'ERROR': '#f87171',
                'CRITICAL': '#f43f5e'
            };
            
            const container = document.getElementById('pieChart');
            const width = container.clientWidth;
            const height = container.clientHeight;
            const radius = Math.min(width, height) / 2 - 20;
            const centerX = width / 2;
            const centerY = height / 2;
            
            let svg = `<svg viewBox="0 0 ${width} ${height}">`;
            
            let startAngle = -90;
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            
            levels.forEach(level => {
                const percentage = percentages[level] || 0;
                if (percentage > 0) {
                    const angle = (percentage / 100) * 360;
                    const endAngle = startAngle + angle;
                    
                    const x1 = centerX + radius * Math.cos(startAngle * Math.PI / 180);
                    const y1 = centerY + radius * Math.sin(startAngle * Math.PI / 180);
                    const x2 = centerX + radius * Math.cos(endAngle * Math.PI / 180);
                    const y2 = centerY + radius * Math.sin(endAngle * Math.PI / 180);
                    
                    const largeArcFlag = angle > 180 ? 1 : 0;
                    
                    svg += `<path d="M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z" 
                            fill="${colors[level]}" 
                            stroke="#27272a" 
                            stroke-width="2"
                            class="bar">
                            <title>${level}: ${percentage.toFixed(1)}%</title>
                            </path>`;
                    
                    startAngle = endAngle;
                }
            });
            
            svg += '</svg>';
            container.innerHTML = svg;
        }
        
        // Draw bar chart for errors per hour
        function drawBarChart() {
            const errorsPerHour = analyticsData.errors_per_hour;
            const container = document.getElementById('barChart');
            const width = container.clientWidth;
            const height = container.clientHeight;
            const padding = { top: 20, right: 20, bottom: 60, left: 50 };
            
            const chartWidth = width - padding.left - padding.right;
            const chartHeight = height - padding.top - padding.bottom;
            
            const entries = Object.entries(errorsPerHour);
            const maxErrors = Math.max(...Object.values(errorsPerHour), 1);
            const barWidth = Math.max(5, chartWidth / entries.length - 5);
            
            let svg = `<svg viewBox="0 0 ${width} ${height}">`;
            
            // Grid lines
            for (let i = 0; i <= 5; i++) {
                const y = padding.top + (chartHeight / 5) * i;
                svg += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" 
                        class="grid-line"/>`;
                svg += `<text x="${padding.left - 10}" y="${y + 4}" text-anchor="end" class="axis-label">
                        ${Math.round(maxErrors - (maxErrors / 5) * i)}</text>`;
            }
            
            // Bars
            entries.forEach(([hour, count], index) => {
                const barHeight = (count / maxErrors) * chartHeight;
                const x = padding.left + index * (chartWidth / entries.length);
                const y = padding.top + chartHeight - barHeight;
                
                const gradientId = `bar-${index}`;
                svg += `<defs>
                        <linearGradient id="${gradientId}" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#f87171;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#dc2626;stop-opacity:1" />
                        </linearGradient>
                        </defs>`;
                
                svg += `<rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" 
                        fill="url(#${gradientId})" rx="2" class="bar">
                        <title>${hour}: ${count} errors</title>
                        </rect>`;
                
                // X-axis labels (show every nth label to avoid crowding)
                const skip = Math.ceil(entries.length / 8);
                if (index % skip === 0) {
                    const label = hour.split(' ')[1];
                    svg += `<text x="${x + barWidth / 2}" y="${height - 10}" text-anchor="middle" class="axis-label">
                            ${label}</text>`;
                }
            });
            
            svg += '</svg>';
            container.innerHTML = svg;
        }
        
        // Draw top errors chart
        function drawTopErrorsChart() {
            const topErrors = analyticsData.top_errors;
            const container = document.getElementById('topErrorsChart');
            const width = container.clientWidth;
            const height = container.clientHeight;
            const padding = { top: 20, right: 20, bottom: 100, left: 150 };
            
            const chartWidth = width - padding.left - padding.right;
            const chartHeight = height - padding.top - padding.bottom;
            
            const maxCount = Math.max(...topErrors.map(e => e[1]), 1);
            const barHeight = Math.max(20, chartHeight / topErrors.length - 10);
            
            let svg = `<svg viewBox="0 0 ${width} ${height}">`;
            
            // Grid lines
            for (let i = 0; i <= 5; i++) {
                const x = padding.left + (chartWidth / 5) * i;
                svg += `<line x1="${x}" y1="${padding.top}" x2="${x}" y2="${height - padding.bottom}" 
                        class="grid-line"/>`;
                svg += `<text x="${x}" y="${height - padding.bottom + 20}" text-anchor="middle" class="axis-label">
                        ${Math.round((maxCount / 5) * i)}</text>`;
            }
            
            // Horizontal bars
            topErrors.forEach(([message, count], index) => {
                const barWidth = (count / maxCount) * chartWidth;
                const y = padding.top + index * (chartHeight / topErrors.length);
                
                // Truncate message
                const displayMessage = message.length > 40 ? message.substring(0, 37) + '...' : message;
                
                svg += `<rect x="${padding.left}" y="${y}" width="${barWidth}" height="${barHeight}" 
                        fill="#f87171" rx="2" class="bar">
                        <title>${message}: ${count} occurrences</title>
                        </rect>`;
                
                svg += `<text x="${padding.left - 10}" y="${y + barHeight / 2 + 4}" text-anchor="end" class="axis-label">
                        ${displayMessage}</text>`;
                
                svg += `<text x="${padding.left + barWidth + 5}" y="${y + barHeight / 2 + 4}" 
                        class="axis-label" fill="#e4e4e7">${count}</text>`;
            });
            
            svg += '</svg>';
            container.innerHTML = svg;
        }
        
        // Update errors table
        function updateErrorsTable() {
            const criticalErrors = analyticsData.critical_errors || [];
            allErrors = criticalErrors.map(e => ({
                ...e,
                level: 'CRITICAL'
            }));
            
            renderErrorsTable(allErrors);
        }
        
        // Render errors table
        function renderErrorsTable(errors) {
            const tbody = document.getElementById('errorsTableBody');
            
            if (errors.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="no-data">No errors found</td></tr>';
                return;
            }
            
            tbody.innerHTML = errors.map(error => `
                <tr>
                    <td class="timestamp">${error.timestamp}</td>
                    <td><span class="level-badge ${error.level.toLowerCase()}">${error.level}</span></td>
                    <td>${error.message}</td>
                </tr>
            `).join('');
        }
        
        // Filter and search
        function filterErrors() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const levelFilter = document.getElementById('levelFilter').value;
            
            let filtered = allErrors.filter(error => {
                const matchesSearch = error.message.toLowerCase().includes(searchTerm) ||
                                     error.timestamp.toLowerCase().includes(searchTerm);
                const matchesLevel = levelFilter === 'all' || error.level === levelFilter;
                return matchesSearch && matchesLevel;
            });
            
            renderErrorsTable(filtered);
        }
        
        // Event listeners
        document.getElementById('searchInput').addEventListener('input', filterErrors);
        document.getElementById('levelFilter').addEventListener('change', filterErrors);
        
        // Handle window resize
        window.addEventListener('resize', () => {
            if (analyticsData) {
                drawPieChart();
                drawBarChart();
                drawTopErrorsChart();
            }
        });
        
        // Initial load
        fetchAnalytics();
        
        // Auto-refresh every 30 seconds
        setInterval(fetchAnalytics, 30000);
    </script>
</body>
</html>'''


def main():
    """Main entry point."""
    print("=" * 60)
    print("Log Analytics Dashboard")
    print("=" * 60)
    
    # Parse logs and get analytics
    analytics_data = parse_logs()
    
    # Set analytics data for the handler
    DashboardHandler.analytics_data = analytics_data
    
    # Start server
    with socketserver.TCPServer(('', PORT), DashboardHandler) as httpd:
        print(f"\n🚀 Dashboard running at: http://localhost:{PORT}")
        print(f"📊 Analyzed {analytics_data['total_logs']} log entries")
        print(f"⚠️  Found {len(analytics_data['critical_errors'])} critical errors")
        print("\nPress Ctrl+C to stop the server\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped.")


if __name__ == '__main__':
    main()