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
from collections import Counter
import urllib.parse

# Configuration
LOG_FILE = 'server.log'
PORT = 8000

# Log level colors for the dashboard
LEVEL_COLORS = {
    'INFO': '#10b981',
    'WARN': '#f59e0b',
    'ERROR': '#ef4444',
    'CRITICAL': '#7c3aed'
}

def generate_fake_logs(num_lines=1000):
    """Generate fake log data with timestamps and various log levels."""
    levels = ['INFO', 'INFO', 'INFO', 'INFO', 'WARN', 'WARN', 'ERROR', 'CRITICAL']
    messages = {
        'INFO': [
            'Connection established from 192.168.1.{}',
            'Request processed successfully',
            'Cache hit for key: user_{}',
            'Database query completed in {}ms',
            'User {} logged in successfully',
            'Scheduled task completed',
            'Health check passed',
            'Configuration reloaded',
            'Backup completed successfully',
            'Service started on port 8080'
        ],
        'WARN': [
            'High memory usage detected: {}%',
            'Slow query detected: {}ms',
            'Rate limit approaching for IP {}',
            'Deprecated API endpoint called',
            'Connection pool running low',
            'Disk space below 20%',
            'Retrying request (attempt {}/3)',
            'Response time above threshold',
            'Session timeout warning for user {}',
            'SSL certificate expiring soon'
        ],
        'ERROR': [
            'Failed to connect to database',
            'Authentication failed for user {}',
            'File not found: {}',
            'Connection timeout after 30s',
            'Invalid request payload',
            'Service unavailable: {}',
            'NullPointerException in module {}',
            'Failed to write to disk',
            'API rate limit exceeded',
            'Query execution failed: {}'
        ],
        'CRITICAL': [
            'SYSTEM CRASH: Out of memory',
            'Database connection lost - retrying',
            'Security breach detected from IP {}',
            'Core service stopped unexpectedly',
            'Data corruption detected in shard {}',
            'Emergency shutdown initiated',
            'All nodes offline',
            'Firewall breach blocked',
            'Critical security patch required',
            'System failure: unable to recover'
        ]
    }
    
    logs = []
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    for i in range(num_lines):
        level = random.choice(levels)
        message_templates = messages[level]
        message = random.choice(message_templates)
        
        # Fill in placeholders
        if '{}' in message:
            num_placeholders = message.count('{}')
            args = [random.randint(1, 1000) for _ in range(num_placeholders)]
            message = message.format(*args)
        
        # Generate timestamp
        timestamp = start_time + timedelta(
            seconds=random.randint(0, int((end_time - start_time).total_seconds()))
        )
        
        log_line = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {level}: {message}"
        logs.append((timestamp, log_line))
    
    # Sort by timestamp
    logs.sort(key=lambda x: x[0])
    
    with open(LOG_FILE, 'w') as f:
        f.write('\n'.join(line for _, line in logs))
    
    print(f"Generated {num_lines} fake log lines in {LOG_FILE}")

def parse_logs():
    """Parse the log file and extract statistics."""
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
    
    all_logs = []
    level_counts = Counter()
    errors_per_hour = Counter()
    error_messages = Counter()
    
    log_pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+): (.+)')
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            match = log_pattern.match(line)
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                log_entry = {
                    'timestamp': timestamp_str,
                    'level': level,
                    'message': message
                }
                all_logs.append(log_entry)
                level_counts[level] += 1
                
                if level in ['ERROR', 'CRITICAL']:
                    hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                    errors_per_hour[hour_key] += 1
                    error_messages[message] += 1
    
    # Calculate percentages
    total = sum(level_counts.values())
    level_percentages = {
        level: (count / total) * 100 if total > 0 else 0
        for level, count in level_counts.items()
    }
    
    # Sort errors per hour by timestamp
    errors_per_hour_sorted = dict(sorted(errors_per_hour.items()))
    
    # Get top error messages
    top_errors = error_messages.most_common(10)
    
    return {
        'level_counts': dict(level_counts),
        'level_percentages': level_percentages,
        'errors_per_hour': errors_per_hour_sorted,
        'all_logs': all_logs,
        'top_errors': top_errors,
        'total_logs': total
    }

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler that serves the dashboard."""
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/api/data':
            self.send_api_data()
        elif parsed_path.path == '/':
            self.send_dashboard()
        else:
            self.send_error(404, 'Not found')
    
    def send_api_data(self):
        """Send log analysis data as JSON."""
        data = parse_logs()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_dashboard(self):
        """Send the HTML dashboard."""
        html_content = self.get_dashboard_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
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
            color: #e4e4e7;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #3f3f46;
        }
        
        h1 {
            font-size: 2rem;
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: #71717a;
            margin-top: 5px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
        }
        
        .stat-card h3 {
            font-size: 0.75rem;
            color: #a1a1aa;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .chart-card h3 {
            margin-bottom: 20px;
            font-size: 1.1rem;
        }
        
        .chart-container {
            height: 250px;
            position: relative;
        }
        
        .table-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .table-header h3 {
            font-size: 1.1rem;
        }
        
        .filter-buttons {
            display: flex;
            gap: 10px;
        }
        
        .filter-btn {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #e4e4e7;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.875rem;
        }
        
        .filter-btn:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .filter-btn.active {
            background: #60a5fa;
            border-color: #60a5fa;
        }
        
        .search-box {
            position: relative;
        }
        
        .search-box input {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #e4e4e7;
            padding: 10px 15px;
            border-radius: 6px;
            width: 280px;
            font-size: 0.875rem;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: #60a5fa;
        }
        
        .search-box input::placeholder {
            color: #71717a;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            text-align: left;
            padding: 12px;
            background: rgba(255, 255, 255, 0.05);
            color: #a1a1aa;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        tr:hover {
            background: rgba(255, 255, 255, 0.02);
        }
        
        .level-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .level-INFO { background: rgba(16, 185, 129, 0.2); color: #10b981; }
        .level-WARN { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
        .level-ERROR { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
        .level-CRITICAL { background: rgba(124, 58, 237, 0.2); color: #7c3aed; }
        
        /* SVG Chart Styles */
        svg {
            display: block;
        }
        
        .bar-chart rect {
            transition: height 0.3s ease, opacity 0.2s;
        }
        
        .bar-chart rect:hover {
            opacity: 0.8;
        }
        
        .line-chart path {
            fill: none;
            stroke-width: 2;
        }
        
        .line-chart circle {
            transition: r 0.2s;
        }
        
        .line-chart circle:hover {
            r: 6;
            cursor: pointer;
        }
        
        .axis text {
            fill: #71717a;
            font-size: 11px;
        }
        
        .legend {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.875rem;
        }
        
        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 2px;
        }
        
        .error-list {
            max-height: 280px;
            overflow-y: auto;
        }
        
        .error-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.8rem;
        }
        
        .error-message {
            flex: 1;
            margin-right: 15px;
            word-break: break-word;
        }
        
        .error-count {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            white-space: nowrap;
        }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #71717a;
        }
        
        .table-info {
            text-align: center;
            padding: 20px;
            color: #71717a;
            font-size: 0.875rem;
        }
        
        .timestamp-cell {
            color: #71717a;
            font-size: 0.8rem;
            font-family: 'Monaco', 'Menlo', monospace;
        }
        
        .message-cell {
            font-size: 0.875rem;
        }
        
        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
            
            .search-box input {
                width: 100%;
            }
            
            .table-header {
                flex-direction: column;
                align-items: stretch;
            }
            
            .filter-buttons {
                flex-wrap: wrap;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Log Analytics Dashboard</h1>
            <p class="subtitle">Real-time log monitoring and analysis</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Logs</h3>
                <div class="stat-value" id="totalLogs">-</div>
            </div>
            <div class="stat-card">
                <h3>Critical Errors</h3>
                <div class="stat-value" style="color: #7c3aed;" id="criticalCount">-</div>
            </div>
            <div class="stat-card">
                <h3>Errors</h3>
                <div class="stat-value" style="color: #ef4444;" id="errorCount">-</div>
            </div>
            <div class="stat-card">
                <h3>Warnings</h3>
                <div class="stat-value" style="color: #f59e0b;" id="warnCount">-</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>Log Level Distribution</h3>
                <div class="chart-container" id="pieChart"></div>
                <div class="legend" id="pieLegend"></div>
            </div>
            <div class="chart-card">
                <h3>Errors per Hour Timeline</h3>
                <div class="chart-container" id="lineChart"></div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>Log Level Breakdown</h3>
                <div class="chart-container" id="barChart"></div>
            </div>
            <div class="chart-card">
                <h3>Most Common Error Messages</h3>
                <div class="error-list" id="topErrors"></div>
            </div>
        </div>
        
        <div class="table-section">
            <div class="table-header">
                <h3>Log Entries</h3>
                <div class="filter-buttons">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="ERROR">Error</button>
                    <button class="filter-btn" data-filter="CRITICAL">Alert</button>
                </div>
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="🔍 Search logs...">
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Level</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody id="logTableBody"></tbody>
            </table>
            <div id="tableInfo" class="table-info"></div>
        </div>
    </div>
    
    <script>
        let logData = null;
        let currentFilter = 'all';
        let searchQuery = '';
        
        // Colors for log levels
        const levelColors = {
            'INFO': '#10b981',
            'WARN': '#f59e0b',
            'ERROR': '#ef4444',
            'CRITICAL': '#7c3aed'
        };
        
        // Fetch data from API
        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                logData = await response.json();
                updateDashboard();
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }
        
        // Update all dashboard components
        function updateDashboard() {
            updateStats();
            drawPieChart();
            drawBarChart();
            drawLineChart();
            updateTopErrors();
            updateTable();
        }
        
        // Update statistics cards
        function updateStats() {
            document.getElementById('totalLogs').textContent = logData.total_logs.toLocaleString();
            document.getElementById('criticalCount').textContent = 
                (logData.level_counts['CRITICAL'] || 0).toLocaleString();
            document.getElementById('errorCount').textContent = 
                (logData.level_counts['ERROR'] || 0).toLocaleString();
            document.getElementById('warnCount').textContent = 
                (logData.level_counts['WARN'] || 0).toLocaleString();
        }
        
        // Draw pie chart for log level distribution
        function drawPieChart() {
            const container = document.getElementById('pieChart');
            const legend = document.getElementById('pieLegend');
            const data = logData.level_percentages;
            const levels = Object.keys(data);
            const values = Object.values(data);
            const total = values.reduce((a, b) => a + b, 0);
            
            if (total === 0) {
                container.innerHTML = '<div class="no-data">No data available</div>';
                legend.innerHTML = '';
                return;
            }
            
            const size = 200;
            const radius = size / 2;
            const center = size / 2;
            
            let startAngle = -Math.PI / 2;
            let paths = '';
            
            levels.forEach((level, i) => {
                const value = values[i];
                const angle = (value / total) * 2 * Math.PI;
                const endAngle = startAngle + angle;
                
                const x1 = center + radius * Math.cos(startAngle);
                const y1 = center + radius * Math.sin(startAngle);
                const x2 = center + radius * Math.cos(endAngle);
                const y2 = center + radius * Math.sin(endAngle);
                
                const largeArc = angle > Math.PI ? 1 : 0;
                
                const path = `M ${center} ${center} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
                
                paths += `<path d="${path}" fill="${levelColors[level]}" stroke="rgba(255,255,255,0.1)" stroke-width="1">
                    <title>${level}: ${value.toFixed(1)}%</title>
                </path>`;
                
                startAngle = endAngle;
            });
            
            container.innerHTML = `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
                ${paths}
            </svg>`;
            
            // Update legend
            legend.innerHTML = levels.map(level => `
                <div class="legend-item">
                    <div class="legend-color" style="background: ${levelColors[level]}"></div>
                    <span>${level}: ${data[level].toFixed(1)}%</span>
                </div>
            `).join('');
        }
        
        // Draw bar chart for log level counts
        function drawBarChart() {
            const container = document.getElementById('barChart');
            const data = logData.level_counts;
            const levels = Object.keys(data);
            const values = Object.values(data);
            const maxValue = Math.max(...values, 1);
            
            const width = container.offsetWidth || 400;
            const height = 250;
            const barWidth = Math.min((width - 60) / levels.length - 20, 60);
            const chartHeight = height - 40;
            const startX = (width - (levels.length * (barWidth + 20) - 20)) / 2;
            
            let bars = '';
            let axisLabels = '';
            
            levels.forEach((level, i) => {
                const value = values[i];
                const barHeight = (value / maxValue) * (chartHeight - 30);
                const x = startX + i * (barWidth + 20);
                const y = chartHeight - barHeight;
                
                bars += `<rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" 
                    fill="${levelColors[level]}" rx="4">
                    <title>${level}: ${value.toLocaleString()}</title>
                </rect>`;
                
                bars += `<text x="${x + barWidth/2}" y="${y - 5}" fill="#e4e4e7" text-anchor="middle" font-size="11" font-weight="600">
                    ${value}
                </text>`;
                
                axisLabels += `<text x="${x + barWidth/2}" y="${chartHeight + 15}" fill="#a1a1aa" text-anchor="middle" font-size="11">
                    ${level}
                </text>`;
            });
            
            // Grid lines
            let gridLines = '';
            for (let i = 0; i <= 4; i++) {
                const y = 10 + (i * (chartHeight - 30) / 4);
                gridLines += `<line x1="20" y1="${y}" x2="${width - 20}" y2="${y}" stroke="#27272a" stroke-width="1"/>`;
            }
            
            container.innerHTML = `<svg width="${width}" height="${height}" class="bar-chart">
                ${gridLines}
                ${bars}
                ${axisLabels}
            </svg>`;
        }
        
        // Draw line chart for errors per hour
        function drawLineChart() {
            const container = document.getElementById('lineChart');
            const data = logData.errors_per_hour;
            const hours = Object.keys(data);
            const values = Object.values(data);
            
            if (hours.length === 0) {
                container.innerHTML = '<div class="no-data">No error data available</div>';
                return;
            }
            
            const width = container.offsetWidth || 400;
            const height = 250;
            const padding = { top: 20, right: 20, bottom: 40, left: 50 };
            const chartWidth = width - padding.left - padding.right;
            const chartHeight = height - padding.top - padding.bottom;
            
            const maxValue = Math.max(...values, 1);
            
            // Calculate points
            const points = hours.map((hour, i) => {
                const x = padding.left + (i / (hours.length - 1 || 1)) * chartWidth;
                const y = padding.top + chartHeight - (values[i] / maxValue) * chartHeight;
                return { x, y, value: values[i], hour };
            });
            
            // Create path
            const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
            
            // Create area fill
            const areaD = pathD + ` L ${points[points.length - 1].x} ${padding.top + chartHeight} L ${points[0].x} ${padding.top + chartHeight} Z`;
            
            let circles = points.map(p => 
                `<circle cx="${p.x}" cy="${p.y}" r="4" fill="#ef4444" stroke="#1a1a2e" stroke-width="2">
                    <title>${p.hour}: ${p.value} errors</title>
                </circle>`
            ).join('');
            
            // X-axis labels
            const labelStep = Math.max(1, Math.ceil(hours.length / 6));
            let xLabels = hours.map((hour, i) => {
                if (i % labelStep === 0) {
                    const x = padding.left + (i / (hours.length - 1 || 1)) * chartWidth;
                    const date = new Date(hour);
                    const label = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', hour12: false });
                    return `<text x="${x}" y="${height - 10}" fill="#71717a" text-anchor="middle" font-size="10">${label}</text>`;
                }
                return '';
            }).join('');
            
            // Y-axis labels
            let yLabels = '';
            for (let i = 0; i <= 4; i++) {
                const value = Math.round((i / 4) * maxValue);
                const y = padding.top + chartHeight - (i / 4) * chartHeight;
                yLabels += `<text x="${padding.left - 10}" y="${y + 4}" fill="#71717a" text-anchor="end" font-size="10">${value}</text>`;
                yLabels += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="#27272a" stroke-width="1"/>`;
            }
            
            container.innerHTML = `<svg width="${width}" height="${height}" class="line-chart">
                <defs>
                    <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#ef4444;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#ef4444;stop-opacity:0" />
                    </linearGradient>
                </defs>
                ${yLabels}
                <path d="${areaD}" fill="url(#areaGradient)"/>
                <path d="${pathD}" stroke="#ef4444" fill="none" stroke-width="2"/>
                ${circles}
                ${xLabels}
            </svg>`;
        }
        
        // Update top errors list
        function updateTopErrors() {
            const container = document.getElementById('topErrors');
            const errors = logData.top_errors || [];
            
            if (errors.length === 0) {
                container.innerHTML = '<div class="no-data">No errors found</div>';
                return;
            }
            
            container.innerHTML = errors.map(([message, count]) => `
                <div class="error-item">
                    <span class="error-message">${message.length > 60 ? message.substring(0, 60) + '...' : message}</span>
                    <span class="error-count">${count}</span>
                </div>
            `).join('');
        }
        
        // Update log table
        function updateTable() {
            const tbody = document.getElementById('logTableBody');
            const tableInfo = document.getElementById('tableInfo');
            let logs = logData.all_logs || [];
            
            // Apply filter
            if (currentFilter !== 'all') {
                logs = logs.filter(log => log.level === currentFilter);
            }
            
            // Apply search
            if (searchQuery) {
                const query = searchQuery.toLowerCase();
                logs = logs.filter(log => 
                    log.message.toLowerCase().includes(query) ||
                    log.timestamp.toLowerCase().includes(query) ||
                    log.level.toLowerCase().includes(query)
                );
            }
            
            if (logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="no-data">No logs match the current filter</td></tr>';
                tableInfo.textContent = '';
                return;
            }
            
            // Show only first 100 logs for performance
            const displayLogs = logs.slice(0, 100);
            
            tbody.innerHTML = displayLogs.map(log => `
                <tr>
                    <td class="timestamp-cell">${log.timestamp}</td>
                    <td><span class="level-badge level-${log.level}">${log.level}</span></td>
                    <td class="message-cell">${log.message}</td>
                </tr>
            `).join('');
            
            if (logs.length > 100) {
                tableInfo.textContent = `Showing 100 of ${logs.length.toLocaleString()} matching logs`;
            } else {
                tableInfo.textContent = `Showing ${logs.length.toLocaleString()} log(s)`;
            }
        }
        
        // Filter button handlers
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentFilter = this.dataset.filter;
                updateTable();
            });
        });
        
        // Search input handler
        document.getElementById('searchInput').addEventListener('input', function() {
            searchQuery = this.value;
            updateTable();
        });
        
        // Handle window resize
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (logData) {
                    drawBarChart();
                    drawLineChart();
                }
            }, 250);
        });
        
        // Initialize
        fetchData();
        
        // Auto-refresh every 30 seconds
        setInterval(fetchData, 30000);
    </script>
</body>
</html>'''

def main():
    """Main entry point."""
    # Check if log file exists, generate if not
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
        print(f"Created {LOG_FILE} with fake log data")
    else:
        print(f"Using existing {LOG_FILE}")
    
    # Start HTTP server
    class QuietServer(socketserver.TCPServer):
        allow_reuse_address = True
    
    with QuietServer(('', PORT), DashboardHandler) as httpd:
        print(f'\n{"="*60}')
        print(f'Log Analytics Dashboard is running!')
        print(f'{"="*60}')
        print(f'Open your browser and visit: http://localhost:{PORT}')
        print(f'Press Ctrl+C to stop the server')
        print(f'{"="*60}\n')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n\nShutting down the server...')
            httpd.shutdown()

if __name__ == '__main__':
    main()