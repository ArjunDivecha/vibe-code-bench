#!/usr/bin/env python3
"""
Log Analytics Dashboard
A self-contained log analysis tool with interactive web dashboard.
"""

import http.server
import socketserver
import json
import os
import random
import re
import threading
import webbrowser
from datetime import datetime, timedelta
from collections import Counter
from urllib.parse import urlparse, parse_qs
import sys

# Configuration
PORT = 8000
LOG_FILE = "server.log"
MAX_LOG_LINES = 1000

# Log levels and their approximate distribution
LOG_LEVELS = ['INFO', 'WARN', 'ERROR', 'CRITICAL']
LOG_DISTRIBUTION = [0.5, 0.25, 0.2, 0.05]  # 50% INFO, 25% WARN, 20% ERROR, 5% CRITICAL

# Sample log messages for each level
INFO_MESSAGES = [
    "Server started successfully",
    "User authenticated successfully",
    "Cache cleared",
    "Database connection established",
    "Health check passed",
    "Request processed in 45ms",
    "Session created for user_id=12345",
    "Configuration reloaded",
    "Backup completed",
    "Service heartbeat received",
    "API endpoint /api/users called",
    "File uploaded successfully",
    "Email notification sent",
    "Rate limit check passed",
    "Memory usage within limits",
]

WARN_MESSAGES = [
    "High memory usage detected (85%)",
    "Slow query detected (2.3s)",
    "Disk space running low (15% free)",
    "Connection pool near capacity",
    "Deprecated API endpoint accessed",
    "Retry attempt 2 of 3",
    "Token expiring soon",
    "Rate limit approaching threshold",
    "Cache miss ratio increasing",
    "SSL certificate expires in 30 days",
]

ERROR_MESSAGES = [
    "Database connection failed",
    "Null pointer exception in module",
    "Timeout waiting for response",
    "Invalid input received",
    "File not found: /data/config.yaml",
    "Authentication failed for user",
    "Permission denied for operation",
    "External API returned 500",
    "Disk write failed",
    "Memory allocation error",
    "Index out of bounds",
    "Connection refused by upstream",
]

CRITICAL_MESSAGES = [
    "System crash imminent - OOM killer activated",
    "Database corruption detected",
    "Primary server unreachable",
    "All nodes down in cluster",
    "Data integrity violation",
    "Security breach attempt detected",
    "Hardware failure on disk array",
    "Kernel panic detected",
    "Service completely unresponsive",
    "SLA breach - service down for 10 minutes",
]


def generate_log_data():
    """Generate fake log data and save to server.log"""
    print(f"Generating {MAX_LOG_LINES} lines of fake log data...")
    
    logs = []
    base_time = datetime.now() - timedelta(hours=24)
    
    for i in range(MAX_LOG_LINES):
        # Random timestamp within the last 24 hours
        offset = random.randint(0, 86400)  # 24 hours in seconds
        timestamp = base_time + timedelta(seconds=offset)
        
        # Choose log level based on distribution
        level = random.choices(LOG_LEVELS, weights=LOG_DISTRIBUTION)[0]
        
        # Choose message based on level
        if level == 'INFO':
            message = random.choice(INFO_MESSAGES)
        elif level == 'WARN':
            message = random.choice(WARN_MESSAGES)
        elif level == 'ERROR':
            message = random.choice(ERROR_MESSAGES)
        else:
            message = random.choice(CRITICAL_MESSAGES)
        
        # Add some variance to messages
        if random.random() < 0.1:
            message += f" - request_id={random.randint(10000, 99999)}"
        if random.random() < 0.05:
            message += f" - user_id={random.randint(1, 1000)}"
        
        log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}"
        logs.append(log_line)
    
    # Sort logs by timestamp
    logs.sort(key=lambda x: x.split(']')[0].strip('['))
    
    with open(LOG_FILE, 'w') as f:
        f.write('\n'.join(logs))
    
    print(f"Generated {LOG_FILE} with {len(logs)} log entries.")


def parse_log_file():
    """Parse the log file and extract analytics data"""
    if not os.path.exists(LOG_FILE):
        generate_log_data()
    
    logs = []
    level_counts = Counter()
    errors_by_hour = Counter()
    error_messages = []
    critical_logs = []
    
    # Pattern to parse log lines
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (.+)$'
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            match = re.match(pattern, line)
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                
                log_entry = {
                    'timestamp': timestamp_str,
                    'level': level,
                    'message': message
                }
                logs.append(log_entry)
                level_counts[level] += 1
                
                if level in ['ERROR', 'CRITICAL']:
                    errors_by_hour[hour_key] += 1
                    error_messages.append(message)
                    if level == 'CRITICAL':
                        critical_logs.append(log_entry)
    
    # Calculate percentages
    total = sum(level_counts.values())
    level_percentages = {level: (count / total * 100) for level, count in level_counts.items()}
    
    # Get most common error messages
    common_errors = Counter(error_messages).most_common(10)
    
    # Sort errors by hour for timeline
    sorted_hours = sorted(errors_by_hour.keys())
    errors_timeline = [{'hour': hour, 'count': errors_by_hour[hour]} for hour in sorted_hours]
    
    return {
        'total_logs': total,
        'level_counts': dict(level_counts),
        'level_percentages': level_percentages,
        'errors_timeline': errors_timeline,
        'common_errors': common_errors,
        'critical_logs': critical_logs,
        'all_logs': logs[-100:]  # Last 100 logs for display
    }


class LogDashboardHandler(http.server.BaseHTTPRequestHandler):
    """Custom HTTP handler for the dashboard"""
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        if path == '/' or path == '/index.html':
            self.serve_dashboard()
        elif path == '/api/analytics':
            self.serve_analytics()
        elif path == '/api/logs':
            self.serve_logs(query_params)
        elif path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html = get_dashboard_html()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(html))
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_analytics(self):
        """Serve analytics data as JSON"""
        analytics = parse_log_file()
        response = json.dumps(analytics)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response.encode())
    
    def serve_logs(self, params):
        """Serve filtered logs as JSON"""
        analytics = parse_log_file()
        level_filter = params.get('level', [None])[0]
        
        if level_filter == 'critical':
            logs = analytics['critical_logs']
        else:
            logs = analytics['all_logs']
        
        response = json.dumps(logs)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response.encode())


def get_dashboard_html():
    """Generate the dashboard HTML with embedded CSS and JS"""
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
            color: #e4e4e4;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }
        
        header h1 {
            font-size: 2.5rem;
            font-weight: 300;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        header p {
            color: #888;
            font-size: 0.95rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .stat-card h3 {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #888;
            margin-bottom: 12px;
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 600;
        }
        
        .stat-card.INFO .stat-value { color: #00d4ff; }
        .stat-card.WARN .stat-value { color: #ffc107; }
        .stat-card.ERROR .stat-value { color: #ff6b6b; }
        .stat-card.CRITICAL .stat-value { color: #ff0040; }
        .stat-card.total .stat-value { color: #7b2cbf; }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .chart-card h3 {
            font-size: 1rem;
            margin-bottom: 20px;
            color: #fff;
        }
        
        .chart-container {
            width: 100%;
            height: 300px;
            position: relative;
        }
        
        /* Pie Chart */
        .pie-chart {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
        }
        
        .pie-chart svg {
            transform: rotate(-90deg);
        }
        
        .pie-legend {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-left: 30px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }
        
        .legend-item span {
            font-size: 0.9rem;
        }
        
        /* Timeline Chart */
        .timeline-chart {
            width: 100%;
            height: 100%;
        }
        
        /* Error Messages */
        .errors-section {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }
        
        .errors-section h3 {
            font-size: 1rem;
            margin-bottom: 20px;
        }
        
        .error-bars {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .error-bar-item {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .error-bar-label {
            width: 200px;
            font-size: 0.85rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .error-bar-track {
            flex: 1;
            height: 24px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .error-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #ff0040);
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        
        .error-bar-count {
            width: 50px;
            text-align: right;
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        /* Critical Logs Table */
        .table-section {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.1);
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
            font-size: 1rem;
        }
        
        .filter-buttons {
            display: flex;
            gap: 10px;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: 1px solid rgba(255,255,255,0.2);
            background: transparent;
            color: #e4e4e4;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.85rem;
        }
        
        .filter-btn:hover, .filter-btn.active {
            background: rgba(255,255,255,0.1);
            border-color: #00d4ff;
        }
        
        .filter-btn.active {
            background: #00d4ff;
            color: #1a1a2e;
        }
        
        .search-box {
            padding: 8px 16px;
            border: 1px solid rgba(255,255,255,0.2);
            background: transparent;
            color: #e4e4e4;
            border-radius: 6px;
            font-size: 0.85rem;
            width: 250px;
        }
        
        .search-box::placeholder {
            color: #666;
        }
        
        .logs-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        
        .logs-table th {
            text-align: left;
            padding: 12px 16px;
            background: rgba(255,255,255,0.05);
            font-weight: 600;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .logs-table td {
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .logs-table tr:hover {
            background: rgba(255,255,255,0.02);
        }
        
        .log-level {
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .log-level.INFO { background: rgba(0,212,255,0.2); color: #00d4ff; }
        .log-level.WARN { background: rgba(255,193,7,0.2); color: #ffc107; }
        .log-level.ERROR { background: rgba(255,107,107,0.2); color: #ff6b6b; }
        .log-level.CRITICAL { background: rgba(255,0,64,0.2); color: #ff0040; }
        
        .timestamp {
            color: #888;
            font-family: monospace;
        }
        
        .log-message {
            max-width: 500px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #888;
        }
        
        .no-results {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
            
            .table-header {
                flex-direction: column;
                align-items: stretch;
            }
            
            .filter-buttons {
                flex-wrap: wrap;
            }
            
            .search-box {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Log Analytics Dashboard</h1>
            <p>Real-time log analysis and visualization</p>
        </header>
        
        <div id="stats" class="stats-grid">
            <div class="loading">Loading statistics...</div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>Log Level Distribution</h3>
                <div id="distribution-chart" class="chart-container">
                    <div class="loading">Loading chart...</div>
                </div>
            </div>
            <div class="chart-card">
                <h3>Errors Timeline (Last 24 Hours)</h3>
                <div id="timeline-chart" class="chart-container">
                    <div class="loading">Loading chart...</div>
                </div>
            </div>
        </div>
        
        <div class="errors-section">
            <h3>Most Common Error Messages</h3>
            <div id="error-bars" class="error-bars">
                <div class="loading">Loading errors...</div>
            </div>
        </div>
        
        <div class="table-section">
            <div class="table-header">
                <h3>Critical Errors Log</h3>
                <div class="filter-buttons">
                    <button class="filter-btn active" data-level="all">All</button>
                    <button class="filter-btn" data-level="error">Error</button>
                    <button class="filter-btn" data-level="critical">Critical</button>
                </div>
                <input type="text" class="search-box" id="search-input" placeholder="Search messages...">
            </div>
            <div id="logs-table-container">
                <div class="loading">Loading logs...</div>
            </div>
        </div>
    </div>
    
    <script>
        let currentFilter = 'all';
        let allLogs = [];
        let analyticsData = null;
        
        async function loadAnalytics() {
            try {
                const response = await fetch('/api/analytics');
                analyticsData = await response.json();
                renderStats();
                renderDistributionChart();
                renderTimelineChart();
                renderErrorBars();
                loadLogs();
            } catch (error) {
                console.error('Failed to load analytics:', error);
            }
        }
        
        function renderStats() {
            const stats = document.getElementById('stats');
            const { level_counts, total_logs } = analyticsData;
            
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL', 'total'];
            
            stats.innerHTML = levels.map(level => {
                const count = level === 'total' ? total_logs : (level_counts[level] || 0);
                const percentage = ((count / total_logs) * 100).toFixed(1);
                return `
                    <div class="stat-card ${level}">
                        <h3>${level === 'total' ? 'Total Logs' : level}</h3>
                        <div class="stat-value">${count}</div>
                        <div style="color: #666; font-size: 0.85rem;">${percentage}%</div>
                    </div>
                `;
            }).join('');
        }
        
        function renderDistributionChart() {
            const container = document.getElementById('distribution-chart');
            const { level_percentages, level_counts, total_logs } = analyticsData;
            
            const colors = {
                'INFO': '#00d4ff',
                'WARN': '#ffc107',
                'ERROR': '#ff6b6b',
                'CRITICAL': '#ff0040'
            };
            
            const size = 180;
            const strokeWidth = 30;
            const radius = (size - strokeWidth) / 2;
            const circumference = 2 * Math.PI * radius;
            
            let offset = 0;
            let circles = '';
            let legendItems = '';
            
            for (const level of ['INFO', 'WARN', 'ERROR', 'CRITICAL']) {
                const percentage = level_percentages[level] || 0;
                const dashArray = (percentage / 100) * circumference;
                const dashOffset = -offset;
                
                circles += `
                    <circle
                        cx="${size/2}" cy="${size/2}" r="${radius}"
                        fill="none" stroke="${colors[level]}" stroke-width="${strokeWidth}"
                        stroke-dasharray="${dashArray} ${circumference}"
                        stroke-dashoffset="${dashOffset}"
                        style="transition: stroke-dasharray 0.5s ease"
                    />
                `;
                
                const count = level_counts[level] || 0;
                legendItems += `
                    <div class="legend-item">
                        <div class="legend-color" style="background: ${colors[level]}"></div>
                        <span>${level}: ${count} (${percentage.toFixed(1)}%)</span>
                    </div>
                `;
                
                offset += (percentage / 100) * circumference;
            }
            
            container.innerHTML = `
                <div class="pie-chart">
                    <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
                        ${circles}
                    </svg>
                    <div class="pie-legend">
                        ${legendItems}
                    </div>
                </div>
            `;
        }
        
        function renderTimelineChart() {
            const container = document.getElementById('timeline-chart');
            const { errors_timeline } = analyticsData;
            
            if (errors_timeline.length === 0) {
                container.innerHTML = '<div class="no-results">No errors in the timeline</div>';
                return;
            }
            
            const maxCount = Math.max(...errors_timeline.map(e => e.count), 1);
            const width = container.clientWidth - 60;
            const height = 250;
            const padding = { top: 20, right: 20, bottom: 40, left: 50 };
            const chartWidth = width - padding.left - padding.right;
            const chartHeight = height - padding.top - padding.bottom;
            
            const pointSpacing = chartWidth / (errors_timeline.length - 1 || 1);
            const stepY = chartHeight / maxCount;
            
            let points = '';
            let bars = '';
            let labels = '';
            let gridLines = '';
            
            // Create grid lines
            for (let i = 0; i <= 4; i++) {
                const y = padding.top + (chartHeight / 4) * i;
                const value = Math.round(maxCount - (maxCount / 4) * i);
                gridLines += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="rgba(255,255,255,0.1)" />`;
                labels += `<text x="${padding.left - 10}" y="${y + 4}" text-anchor="end" fill="#888" font-size="12">${value}</text>`;
            }
            
            // Create bars
            errors_timeline.forEach((item, index) => {
                const x = padding.left + index * pointSpacing;
                const barHeight = (item.count / maxCount) * chartHeight;
                const y = padding.top + chartHeight - barHeight;
                
                bars += `
                    <rect
                        x="${x + pointSpacing/4}"
                        y="${y}"
                        width="${pointSpacing/2}"
                        height="${barHeight}"
                        fill="rgba(255,107,107,0.6)"
                        rx="2"
                    >
                        <title>${item.hour}: ${item.count} errors</title>
                    </rect>
                `;
                
                // X-axis labels (show every nth label)
                if (errors_timeline.length <= 12 || index % Math.ceil(errors_timeline.length / 12) === 0) {
                    const hour = item.hour.split(' ')[1].split(':')[0];
                    labels += `<text x="${x + pointSpacing/2}" y="${height - 10}" text-anchor="middle" fill="#888" font-size="10">${hour}h</text>`;
                }
            });
            
            // X-axis line
            gridLines += `<line x1="${padding.left}" y1="${padding.top + chartHeight}" x2="${width - padding.right}" y2="${padding.top + chartHeight}" stroke="rgba(255,255,255,0.2)" />`;
            
            container.innerHTML = `
                <svg class="timeline-chart" viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid meet">
                    ${gridLines}
                    ${bars}
                    ${labels}
                </svg>
            `;
        }
        
        function renderErrorBars() {
            const container = document.getElementById('error-bars');
            const { common_errors } = analyticsData;
            
            if (common_errors.length === 0) {
                container.innerHTML = '<div class="no-results">No error messages found</div>';
                return;
            }
            
            const maxCount = common_errors[0][1];
            
            container.innerHTML = common_errors.map(([message, count]) => `
                <div class="error-bar-item">
                    <div class="error-bar-label" title="${escapeHtml(message)}">${escapeHtml(message)}</div>
                    <div class="error-bar-track">
                        <div class="error-bar-fill" style="width: ${(count / maxCount) * 100}%"></div>
                    </div>
                    <div class="error-bar-count">${count}</div>
                </div>
            `).join('');
        }
        
        async function loadLogs() {
            try {
                const response = await fetch(`/api/logs?level=${currentFilter}`);
                allLogs = await response.json();
                renderLogsTable(allLogs);
            } catch (error) {
                console.error('Failed to load logs:', error);
            }
        }
        
        function renderLogsTable(logs) {
            const container = document.getElementById('logs-table-container');
            
            if (logs.length === 0) {
                container.innerHTML = '<div class="no-results">No logs found</div>';
                return;
            }
            
            container.innerHTML = `
                <table class="logs-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Level</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${logs.map(log => `
                            <tr>
                                <td class="timestamp">${log.timestamp}</td>
                                <td><span class="log-level ${log.level}">${log.level}</span></td>
                                <td class="log-message" title="${escapeHtml(log.message)}">${escapeHtml(log.message)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Event Listeners
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.level;
                loadLogs();
            });
        });
        
        document.getElementById('search-input').addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const filteredLogs = allLogs.filter(log => 
                log.message.toLowerCase().includes(searchTerm) ||
                log.level.toLowerCase().includes(searchTerm)
            );
            renderLogsTable(filteredLogs);
        });
        
        // Initial load
        loadAnalytics();
        
        // Auto-refresh every 30 seconds
        setInterval(loadAnalytics, 30000);
    </script>
</body>
</html>'''


def main():
    """Main entry point"""
    print("=" * 50)
    print("Log Analytics Dashboard")
    print("=" * 50)
    
    # Parse logs to check if file exists
    if not os.path.exists(LOG_FILE):
        generate_log_data()
    
    # Start the server
    with socketserver.TCPServer(("", PORT), LogDashboardHandler) as httpd:
        print(f"\n✓ Dashboard server running at http://localhost:{PORT}")
        print("✓ Press Ctrl+C to stop the server\n")
        
        # Open browser automatically in a separate thread
        def open_browser():
            webbrowser.open(f'http://localhost:{PORT}')
        
        browser_thread = threading.Timer(1.0, open_browser)
        browser_thread.start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            httpd.shutdown()
            print("Server stopped.")


if __name__ == "__main__":
    main()