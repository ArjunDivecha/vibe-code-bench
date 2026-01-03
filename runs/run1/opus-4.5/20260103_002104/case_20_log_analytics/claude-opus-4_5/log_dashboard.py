#!/usr/bin/env python3
"""
Log Analytics Dashboard
Parses server logs and serves an interactive web dashboard
"""

import os
import json
import random
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

LOG_FILE = "server.log"

# Sample error messages for fake log generation
ERROR_MESSAGES = [
    "Connection timeout to database server",
    "Failed to authenticate user",
    "Memory allocation failed",
    "Disk space critically low",
    "Network interface unavailable",
    "SSL certificate expired",
    "File not found: config.yaml",
    "Invalid JSON payload received",
    "Rate limit exceeded for API",
    "Service dependency unavailable",
    "Cache invalidation failed",
    "Queue overflow detected",
    "Deadlock detected in transaction",
    "Permission denied for resource",
    "Malformed request headers",
]

INFO_MESSAGES = [
    "Server started successfully",
    "User logged in",
    "Request processed",
    "Cache refreshed",
    "Scheduled task completed",
    "Connection established",
    "Configuration reloaded",
    "Health check passed",
    "Session created",
    "Data synchronized",
]

WARN_MESSAGES = [
    "High memory usage detected",
    "Slow query execution",
    "Deprecated API endpoint used",
    "Connection pool nearly exhausted",
    "Retry attempt for failed operation",
    "Disk usage above 80%",
    "Response time exceeded threshold",
    "Unhandled exception caught",
]

CRITICAL_MESSAGES = [
    "Database connection lost",
    "System out of memory",
    "Security breach detected",
    "Data corruption detected",
    "Service crash imminent",
    "Unrecoverable error in core module",
    "Cluster node failed",
    "Backup system offline",
]


def generate_fake_logs(num_lines=1000):
    """Generate fake log data"""
    logs = []
    levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    weights = [60, 20, 15, 5]  # Probability weights
    
    base_time = datetime.now() - timedelta(hours=48)
    
    for i in range(num_lines):
        # Random timestamp within last 48 hours
        offset_seconds = random.randint(0, 48 * 3600)
        timestamp = base_time + timedelta(seconds=offset_seconds)
        ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        level = random.choices(levels, weights=weights)[0]
        
        if level == "INFO":
            message = random.choice(INFO_MESSAGES)
        elif level == "WARN":
            message = random.choice(WARN_MESSAGES)
        elif level == "ERROR":
            message = random.choice(ERROR_MESSAGES)
        else:  # CRITICAL
            message = random.choice(CRITICAL_MESSAGES)
        
        # Add some variation
        if random.random() > 0.7:
            message += f" (id={random.randint(1000, 9999)})"
        
        log_line = f"[{ts_str}] [{level}] {message}"
        logs.append((timestamp, log_line))
    
    # Sort by timestamp
    logs.sort(key=lambda x: x[0])
    
    with open(LOG_FILE, "w") as f:
        for _, line in logs:
            f.write(line + "\n")
    
    print(f"Generated {num_lines} fake log entries in {LOG_FILE}")


def parse_logs():
    """Parse log file and extract analytics data"""
    log_pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\] (.+)')
    
    level_counts = Counter()
    errors_per_hour = defaultdict(int)
    error_messages = Counter()
    critical_logs = []
    all_logs = []
    
    with open(LOG_FILE, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            match = log_pattern.match(line)
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                level_counts[level] += 1
                
                log_entry = {
                    "id": line_num,
                    "timestamp": timestamp_str,
                    "level": level,
                    "message": message
                }
                all_logs.append(log_entry)
                
                if level in ["ERROR", "CRITICAL"]:
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    errors_per_hour[hour_key] += 1
                    # Clean message for grouping (remove IDs)
                    clean_msg = re.sub(r'\s*\(id=\d+\)', '', message)
                    error_messages[clean_msg] += 1
                
                if level == "CRITICAL":
                    critical_logs.append(log_entry)
    
    total = sum(level_counts.values())
    level_percentages = {
        level: round(count / total * 100, 2) if total > 0 else 0
        for level, count in level_counts.items()
    }
    
    # Sort errors per hour by time
    sorted_hours = sorted(errors_per_hour.keys())
    errors_timeline = [
        {"hour": hour, "count": errors_per_hour[hour]}
        for hour in sorted_hours
    ]
    
    # Top error messages
    top_errors = [
        {"message": msg, "count": count}
        for msg, count in error_messages.most_common(10)
    ]
    
    return {
        "level_percentages": level_percentages,
        "level_counts": dict(level_counts),
        "errors_timeline": errors_timeline,
        "top_errors": top_errors,
        "critical_logs": critical_logs,
        "all_logs": all_logs,
        "total_logs": total
    }


def get_dashboard_html():
    """Return the dashboard HTML"""
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
            color: #e4e4e4;
            min-height: 100vh;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            color: #00d4ff;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        }
        
        .header p {
            color: #888;
            margin-top: 10px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        .stat-card.info { border-left: 4px solid #00d4ff; }
        .stat-card.warn { border-left: 4px solid #ffc107; }
        .stat-card.error { border-left: 4px solid #ff6b6b; }
        .stat-card.critical { border-left: 4px solid #ff0055; }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-card.info .stat-value { color: #00d4ff; }
        .stat-card.warn .stat-value { color: #ffc107; }
        .stat-card.error .stat-value { color: #ff6b6b; }
        .stat-card.critical .stat-value { color: #ff0055; }
        
        .stat-label {
            color: #888;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        @media (max-width: 900px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .panel {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .panel h2 {
            color: #00d4ff;
            margin-bottom: 20px;
            font-size: 1.2em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .panel h2::before {
            content: '';
            width: 4px;
            height: 20px;
            background: #00d4ff;
            border-radius: 2px;
        }
        
        .chart-container {
            width: 100%;
            height: 250px;
            position: relative;
        }
        
        .chart-container svg {
            width: 100%;
            height: 100%;
        }
        
        .pie-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 15px;
            justify-content: center;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
        }
        
        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }
        
        .error-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .error-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: rgba(255, 107, 107, 0.1);
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 3px solid #ff6b6b;
        }
        
        .error-item .message {
            flex: 1;
            font-size: 0.9em;
            color: #ddd;
        }
        
        .error-item .count {
            background: #ff6b6b;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        .full-width {
            grid-column: 1 / -1;
        }
        
        .filter-bar {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .search-input {
            flex: 1;
            min-width: 200px;
            padding: 12px 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 25px;
            background: rgba(255, 255, 255, 0.05);
            color: white;
            font-size: 1em;
        }
        
        .search-input:focus {
            outline: none;
            border-color: #00d4ff;
            box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
        }
        
        .filter-buttons {
            display: flex;
            gap: 10px;
        }
        
        .filter-btn {
            padding: 10px 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 25px;
            background: transparent;
            color: #888;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9em;
        }
        
        .filter-btn:hover {
            border-color: #00d4ff;
            color: #00d4ff;
        }
        
        .filter-btn.active {
            background: #00d4ff;
            border-color: #00d4ff;
            color: #1a1a2e;
        }
        
        .log-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        .log-table th {
            text-align: left;
            padding: 15px;
            background: rgba(0, 212, 255, 0.1);
            color: #00d4ff;
            font-weight: 600;
            border-bottom: 2px solid rgba(0, 212, 255, 0.2);
        }
        
        .log-table td {
            padding: 12px 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.9em;
        }
        
        .log-table tr:hover {
            background: rgba(255, 255, 255, 0.02);
        }
        
        .level-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .level-badge.INFO { background: rgba(0, 212, 255, 0.2); color: #00d4ff; }
        .level-badge.WARN { background: rgba(255, 193, 7, 0.2); color: #ffc107; }
        .level-badge.ERROR { background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }
        .level-badge.CRITICAL { background: rgba(255, 0, 85, 0.2); color: #ff0055; }
        
        .table-container {
            max-height: 400px;
            overflow-y: auto;
            border-radius: 10px;
        }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(0, 212, 255, 0.3);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 212, 255, 0.5);
        }
        
        .timeline-bar {
            fill: #ff6b6b;
            transition: fill 0.3s;
        }
        
        .timeline-bar:hover {
            fill: #ff8a8a;
        }
        
        .axis-line {
            stroke: rgba(255, 255, 255, 0.2);
        }
        
        .axis-text {
            fill: #888;
            font-size: 10px;
        }
        
        .grid-line {
            stroke: rgba(255, 255, 255, 0.05);
        }
        
        .tooltip {
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            pointer-events: none;
            z-index: 100;
            display: none;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Log Analytics Dashboard</h1>
        <p id="summary">Loading data...</p>
    </div>
    
    <div class="stats-grid" id="statsGrid">
        <!-- Stats will be populated by JS -->
    </div>
    
    <div class="dashboard-grid">
        <div class="panel">
            <h2>Log Level Distribution</h2>
            <div class="chart-container" id="pieChart"></div>
            <div class="pie-legend" id="pieLegend"></div>
        </div>
        
        <div class="panel">
            <h2>Errors Over Time</h2>
            <div class="chart-container" id="timelineChart"></div>
        </div>
        
        <div class="panel full-width">
            <h2>Top Error Messages</h2>
            <div class="error-list" id="errorList"></div>
        </div>
        
        <div class="panel full-width">
            <h2>Critical & Error Logs</h2>
            <div class="filter-bar">
                <input type="text" class="search-input" id="searchInput" placeholder="Search logs...">
                <div class="filter-buttons">
                    <button class="filter-btn active" data-level="all">All</button>
                    <button class="filter-btn" data-level="ERROR">Error</button>
                    <button class="filter-btn" data-level="CRITICAL">Critical</button>
                </div>
            </div>
            <div class="table-container">
                <table class="log-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Timestamp</th>
                            <th>Level</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody id="logTableBody">
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        let logData = null;
        let currentFilter = 'all';
        let searchTerm = '';
        
        const colors = {
            INFO: '#00d4ff',
            WARN: '#ffc107',
            ERROR: '#ff6b6b',
            CRITICAL: '#ff0055'
        };
        
        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                logData = await response.json();
                renderDashboard();
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }
        
        function renderDashboard() {
            renderStats();
            renderPieChart();
            renderTimeline();
            renderErrorList();
            renderLogTable();
            
            document.getElementById('summary').textContent = 
                `Analyzing ${logData.total_logs.toLocaleString()} log entries`;
        }
        
        function renderStats() {
            const grid = document.getElementById('statsGrid');
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            
            grid.innerHTML = levels.map(level => {
                const count = logData.level_counts[level] || 0;
                const pct = logData.level_percentages[level] || 0;
                return `
                    <div class="stat-card ${level.toLowerCase()}">
                        <div class="stat-value">${count}</div>
                        <div class="stat-label">${level} (${pct}%)</div>
                    </div>
                `;
            }).join('');
        }
        
        function renderPieChart() {
            const container = document.getElementById('pieChart');
            const legend = document.getElementById('pieLegend');
            
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const data = levels.map(level => ({
                level,
                value: logData.level_counts[level] || 0,
                color: colors[level]
            })).filter(d => d.value > 0);
            
            const total = data.reduce((sum, d) => sum + d.value, 0);
            if (total === 0) {
                container.innerHTML = '<div class="no-data">No data available</div>';
                return;
            }
            
            const size = 200;
            const cx = size / 2;
            const cy = size / 2;
            const radius = 80;
            
            let startAngle = -90;
            const paths = data.map(d => {
                const angle = (d.value / total) * 360;
                const endAngle = startAngle + angle;
                
                const start = polarToCartesian(cx, cy, radius, startAngle);
                const end = polarToCartesian(cx, cy, radius, endAngle);
                const largeArc = angle > 180 ? 1 : 0;
                
                const path = `M ${cx} ${cy} L ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArc} 1 ${end.x} ${end.y} Z`;
                
                startAngle = endAngle;
                return `<path d="${path}" fill="${d.color}" opacity="0.8">
                    <title>${d.level}: ${d.value} (${((d.value/total)*100).toFixed(1)}%)</title>
                </path>`;
            }).join('');
            
            container.innerHTML = `
                <svg viewBox="0 0 ${size} ${size}">
                    ${paths}
                    <circle cx="${cx}" cy="${cy}" r="40" fill="#1a1a2e"/>
                    <text x="${cx}" y="${cy}" text-anchor="middle" dy="5" fill="white" font-size="14">${total}</text>
                </svg>
            `;
            
            legend.innerHTML = data.map(d => `
                <div class="legend-item">
                    <div class="legend-color" style="background: ${d.color}"></div>
                    <span>${d.level}: ${d.value}</span>
                </div>
            `).join('');
        }
        
        function polarToCartesian(cx, cy, r, angle) {
            const rad = (angle * Math.PI) / 180;
            return {
                x: cx + r * Math.cos(rad),
                y: cy + r * Math.sin(rad)
            };
        }
        
        function renderTimeline() {
            const container = document.getElementById('timelineChart');
            const data = logData.errors_timeline;
            
            if (data.length === 0) {
                container.innerHTML = '<div class="no-data">No error data available</div>';
                return;
            }
            
            const width = 450;
            const height = 220;
            const margin = { top: 20, right: 20, bottom: 50, left: 40 };
            const chartWidth = width - margin.left - margin.right;
            const chartHeight = height - margin.top - margin.bottom;
            
            const maxCount = Math.max(...data.map(d => d.count));
            const barWidth = Math.max(8, (chartWidth / data.length) - 4);
            
            const bars = data.map((d, i) => {
                const barHeight = (d.count / maxCount) * chartHeight;
                const x = margin.left + (i * (chartWidth / data.length)) + (chartWidth / data.length - barWidth) / 2;
                const y = margin.top + chartHeight - barHeight;
                
                return `
                    <rect class="timeline-bar" x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="2">
                        <title>${d.hour}: ${d.count} errors</title>
                    </rect>
                `;
            }).join('');
            
            // Y-axis labels
            const yLabels = [0, Math.round(maxCount/2), maxCount].map((val, i) => {
                const y = margin.top + chartHeight - (val / maxCount) * chartHeight;
                return `<text class="axis-text" x="${margin.left - 10}" y="${y + 4}" text-anchor="end">${val}</text>`;
            }).join('');
            
            // Grid lines
            const gridLines = [0, 0.5, 1].map(pct => {
                const y = margin.top + chartHeight * (1 - pct);
                return `<line class="grid-line" x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}"/>`;
            }).join('');
            
            // X-axis labels (show subset)
            const step = Math.ceil(data.length / 6);
            const xLabels = data.filter((_, i) => i % step === 0).map((d, i) => {
                const x = margin.left + (i * step * (chartWidth / data.length)) + (chartWidth / data.length) / 2;
                const hour = d.hour.split(' ')[1] || d.hour;
                return `<text class="axis-text" x="${x}" y="${height - 10}" text-anchor="middle">${hour}</text>`;
            }).join('');
            
            container.innerHTML = `
                <svg viewBox="0 0 ${width} ${height}">
                    ${gridLines}
                    <line class="axis-line" x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${margin.top + chartHeight}"/>
                    <line class="axis-line" x1="${margin.left}" y1="${margin.top + chartHeight}" x2="${width - margin.right}" y2="${margin.top + chartHeight}"/>
                    ${bars}
                    ${yLabels}
                    ${xLabels}
                </svg>
            `;
        }
        
        function renderErrorList() {
            const container = document.getElementById('errorList');
            const errors = logData.top_errors;
            
            if (errors.length === 0) {
                container.innerHTML = '<div class="no-data">No errors found</div>';
                return;
            }
            
            container.innerHTML = errors.map(e => `
                <div class="error-item">
                    <span class="message">${escapeHtml(e.message)}</span>
                    <span class="count">${e.count}</span>
                </div>
            `).join('');
        }
        
        function renderLogTable() {
            const tbody = document.getElementById('logTableBody');
            
            // Filter logs to show ERROR and CRITICAL
            let logs = logData.all_logs.filter(log => 
                log.level === 'ERROR' || log.level === 'CRITICAL'
            );
            
            // Apply level filter
            if (currentFilter !== 'all') {
                logs = logs.filter(log => log.level === currentFilter);
            }
            
            // Apply search filter
            if (searchTerm) {
                const term = searchTerm.toLowerCase();
                logs = logs.filter(log => 
                    log.message.toLowerCase().includes(term) ||
                    log.timestamp.includes(term)
                );
            }
            
            if (logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="no-data">No matching logs found</td></tr>';
                return;
            }
            
            // Show most recent first, limit to 100
            logs = logs.slice(-100).reverse();
            
            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td>${log.id}</td>
                    <td>${log.timestamp}</td>
                    <td><span class="level-badge ${log.level}">${log.level}</span></td>
                    <td>${escapeHtml(log.message)}</td>
                </tr>
            `).join('');
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Event listeners
        document.getElementById('searchInput').addEventListener('input', (e) => {
            searchTerm = e.target.value;
            renderLogTable();
        });
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.level;
                renderLogTable();
            });
        });
        
        // Initial load
        fetchData();
        
        // Auto-refresh every 30 seconds
        setInterval(fetchData, 30000);
    </script>
</body>
</html>'''


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the dashboard"""
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(get_dashboard_html().encode())
        
        elif path == '/api/data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            data = parse_logs()
            self.wfile.write(json.dumps(data).encode())
        
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')


def main():
    # Check for log file, generate if missing
    if not os.path.exists(LOG_FILE):
        print(f"Log file '{LOG_FILE}' not found. Generating fake data...")
        generate_fake_logs(1000)
    else:
        print(f"Found existing log file: {LOG_FILE}")
    
    # Parse logs to show initial stats
    data = parse_logs()
    print(f"\n📊 Log Analysis Summary:")
    print(f"   Total entries: {data['total_logs']}")
    print(f"   Level breakdown: {data['level_counts']}")
    print(f"   Critical errors: {len(data['critical_logs'])}")
    
    # Start HTTP server
    port = 8080
    server = HTTPServer(('localhost', port), DashboardHandler)
    
    print(f"\n🚀 Dashboard running at: http://localhost:{port}")
    print("   Press Ctrl+C to stop the server\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
        server.shutdown()


if __name__ == "__main__":
    main()