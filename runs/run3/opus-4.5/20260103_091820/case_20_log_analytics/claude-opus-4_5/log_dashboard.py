#!/usr/bin/env python3
"""
Log Analytics Dashboard
Generates fake logs if needed, parses them, and serves an interactive dashboard.
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
PORT = 8080

# Sample error messages for fake log generation
ERROR_MESSAGES = [
    "Connection timeout to database server",
    "Failed to authenticate user",
    "Disk space running low",
    "Memory allocation failed",
    "Network interface unreachable",
    "SSL certificate expired",
    "Rate limit exceeded for API",
    "Invalid JSON payload received",
    "File not found: config.yaml",
    "Permission denied accessing resource",
    "Database query timeout",
    "Service unavailable: payment gateway",
    "Invalid session token",
    "Cache miss for user session",
    "Queue overflow detected",
]

WARN_MESSAGES = [
    "High CPU usage detected",
    "Response time exceeding threshold",
    "Deprecated API endpoint called",
    "Retry attempt 3 of 5",
    "Low disk space warning",
    "Connection pool nearly exhausted",
    "Slow database query detected",
    "Memory usage above 80%",
]

INFO_MESSAGES = [
    "Server started successfully",
    "User login successful",
    "Request processed in 45ms",
    "Cache refreshed",
    "Scheduled job completed",
    "Health check passed",
    "Configuration reloaded",
    "New connection established",
    "Session created for user",
    "Background task completed",
]

CRITICAL_MESSAGES = [
    "SYSTEM FAILURE: Database cluster down",
    "CRITICAL: All replicas unavailable",
    "EMERGENCY: Security breach detected",
    "FATAL: Out of memory - service crashing",
    "CRITICAL: Data corruption detected",
    "SYSTEM HALT: Unrecoverable error",
]


def generate_fake_logs(num_lines=1000):
    """Generate fake log data with realistic timestamps and messages."""
    logs = []
    base_time = datetime.now() - timedelta(hours=48)
    
    levels = {
        'INFO': (0.60, INFO_MESSAGES),
        'WARN': (0.25, WARN_MESSAGES),
        'ERROR': (0.12, ERROR_MESSAGES),
        'CRITICAL': (0.03, CRITICAL_MESSAGES),
    }
    
    level_list = []
    for level, (prob, _) in levels.items():
        level_list.extend([level] * int(prob * 100))
    
    for i in range(num_lines):
        # Random time increment
        time_offset = timedelta(
            seconds=random.randint(0, int(48 * 3600 / num_lines * 2))
        )
        base_time += time_offset
        
        level = random.choice(level_list)
        message = random.choice(levels[level][1])
        
        # Add some variation to messages
        if random.random() > 0.7:
            message += f" [id={random.randint(1000, 9999)}]"
        
        log_line = f"{base_time.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}"
        logs.append(log_line)
    
    with open(LOG_FILE, 'w') as f:
        f.write('\n'.join(logs))
    
    print(f"Generated {num_lines} fake log entries in {LOG_FILE}")
    return logs


def parse_logs():
    """Parse the log file and extract statistics."""
    log_pattern = re.compile(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (.+)'
    )
    
    level_counts = Counter()
    errors_per_hour = defaultdict(int)
    error_messages = Counter()
    critical_logs = []
    all_logs = []
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            match = log_pattern.match(line)
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
                
                if level in ('ERROR', 'CRITICAL'):
                    hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                    errors_per_hour[hour_key] += 1
                    # Normalize message for counting (remove IDs)
                    normalized_msg = re.sub(r'\[id=\d+\]', '', message).strip()
                    error_messages[normalized_msg] += 1
                
                if level == 'CRITICAL':
                    critical_logs.append(log_entry)
    
    total = sum(level_counts.values())
    level_percentages = {
        level: round(count / total * 100, 2) if total > 0 else 0
        for level, count in level_counts.items()
    }
    
    # Sort errors by hour
    sorted_hours = sorted(errors_per_hour.keys())
    timeline = [
        {'hour': hour, 'count': errors_per_hour[hour]}
        for hour in sorted_hours
    ]
    
    # Top error messages
    top_errors = [
        {'message': msg, 'count': count}
        for msg, count in error_messages.most_common(10)
    ]
    
    return {
        'level_percentages': level_percentages,
        'level_counts': dict(level_counts),
        'timeline': timeline,
        'top_errors': top_errors,
        'critical_logs': critical_logs,
        'all_logs': all_logs,
        'total_logs': total
    }


# HTML Dashboard Template
DASHBOARD_HTML = '''<!DOCTYPE html>
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
            color: #e0e0e0;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }
        
        header h1 {
            font-size: 2.5em;
            background: linear-gradient(90deg, #00d4ff, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        header p {
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
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-card .label {
            color: #888;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }
        
        .stat-card.info .value { color: #00d4ff; }
        .stat-card.warn .value { color: #fbbf24; }
        .stat-card.error .value { color: #f87171; }
        .stat-card.critical .value { color: #dc2626; }
        
        .charts-row {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        @media (max-width: 900px) {
            .charts-row {
                grid-template-columns: 1fr;
            }
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .card h2 {
            margin-bottom: 20px;
            font-size: 1.2em;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card h2::before {
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(180deg, #00d4ff, #7c3aed);
            border-radius: 2px;
        }
        
        svg {
            width: 100%;
            height: auto;
        }
        
        .pie-legend {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
            margin-top: 15px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
        }
        
        .legend-color {
            width: 14px;
            height: 14px;
            border-radius: 3px;
        }
        
        .filters {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .filter-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: #e0e0e0;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9em;
        }
        
        .filter-btn:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .filter-btn.active {
            background: linear-gradient(90deg, #00d4ff, #7c3aed);
            color: #fff;
        }
        
        .search-box {
            flex: 1;
            min-width: 200px;
            padding: 10px 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            color: #e0e0e0;
            font-size: 0.9em;
        }
        
        .search-box:focus {
            outline: none;
            border-color: #00d4ff;
        }
        
        .table-container {
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        th {
            background: rgba(255, 255, 255, 0.1);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 1px;
            position: sticky;
            top: 0;
        }
        
        tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        
        .level-badge {
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .level-INFO { background: rgba(0, 212, 255, 0.2); color: #00d4ff; }
        .level-WARN { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
        .level-ERROR { background: rgba(248, 113, 113, 0.2); color: #f87171; }
        .level-CRITICAL { background: rgba(220, 38, 38, 0.3); color: #dc2626; }
        
        .top-errors-list {
            list-style: none;
        }
        
        .top-errors-list li {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            gap: 15px;
        }
        
        .top-errors-list li:last-child {
            border-bottom: none;
        }
        
        .error-msg {
            flex: 1;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #f87171;
        }
        
        .error-count {
            background: rgba(248, 113, 113, 0.2);
            color: #f87171;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 0.85em;
        }
        
        .no-results {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .bar-label {
            font-size: 10px;
            fill: #888;
        }
        
        .axis-label {
            font-size: 11px;
            fill: #888;
        }
        
        .grid-line {
            stroke: rgba(255, 255, 255, 0.1);
            stroke-dasharray: 3, 3;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Log Analytics Dashboard</h1>
            <p id="summary">Loading log data...</p>
        </header>
        
        <div class="stats-grid" id="statsGrid">
            <!-- Stats cards will be inserted here -->
        </div>
        
        <div class="charts-row">
            <div class="card">
                <h2>Log Level Distribution</h2>
                <svg id="pieChart" viewBox="0 0 300 300"></svg>
                <div class="pie-legend" id="pieLegend"></div>
            </div>
            <div class="card">
                <h2>Errors Over Time</h2>
                <svg id="timelineChart" viewBox="0 0 700 300"></svg>
            </div>
        </div>
        
        <div class="card" style="margin-bottom: 30px;">
            <h2>Top Error Messages</h2>
            <ul class="top-errors-list" id="topErrorsList">
                <!-- Top errors will be inserted here -->
            </ul>
        </div>
        
        <div class="card">
            <h2>Log Entries</h2>
            <div class="filters">
                <button class="filter-btn active" data-filter="ALL">All</button>
                <button class="filter-btn" data-filter="ERROR">Error</button>
                <button class="filter-btn" data-filter="CRITICAL">Critical</button>
                <button class="filter-btn" data-filter="WARN">Warning</button>
                <button class="filter-btn" data-filter="INFO">Info</button>
                <input type="text" class="search-box" id="searchBox" placeholder="Search logs...">
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Level</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody id="logsTable">
                        <!-- Log entries will be inserted here -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let logData = null;
        let currentFilter = 'ALL';
        let searchTerm = '';
        
        const COLORS = {
            INFO: '#00d4ff',
            WARN: '#fbbf24',
            ERROR: '#f87171',
            CRITICAL: '#dc2626'
        };
        
        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                logData = await response.json();
                renderDashboard();
            } catch (error) {
                console.error('Failed to fetch data:', error);
            }
        }
        
        function renderDashboard() {
            renderSummary();
            renderStatsCards();
            renderPieChart();
            renderTimelineChart();
            renderTopErrors();
            renderLogsTable();
        }
        
        function renderSummary() {
            const summary = document.getElementById('summary');
            summary.textContent = `Analyzing ${logData.total_logs.toLocaleString()} log entries`;
        }
        
        function renderStatsCards() {
            const grid = document.getElementById('statsGrid');
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            
            grid.innerHTML = levels.map(level => {
                const count = logData.level_counts[level] || 0;
                const pct = logData.level_percentages[level] || 0;
                return `
                    <div class="stat-card ${level.toLowerCase()}">
                        <div class="value">${count.toLocaleString()}</div>
                        <div class="label">${level} (${pct}%)</div>
                    </div>
                `;
            }).join('');
        }
        
        function renderPieChart() {
            const svg = document.getElementById('pieChart');
            const legend = document.getElementById('pieLegend');
            const cx = 150, cy = 130, r = 100;
            
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const total = Object.values(logData.level_counts).reduce((a, b) => a + b, 0);
            
            let paths = '';
            let startAngle = -90;
            
            levels.forEach(level => {
                const count = logData.level_counts[level] || 0;
                if (count === 0) return;
                
                const percentage = count / total;
                const angle = percentage * 360;
                const endAngle = startAngle + angle;
                
                const startRad = startAngle * Math.PI / 180;
                const endRad = endAngle * Math.PI / 180;
                
                const x1 = cx + r * Math.cos(startRad);
                const y1 = cy + r * Math.sin(startRad);
                const x2 = cx + r * Math.cos(endRad);
                const y2 = cy + r * Math.sin(endRad);
                
                const largeArc = angle > 180 ? 1 : 0;
                
                paths += `
                    <path d="M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z"
                          fill="${COLORS[level]}" 
                          stroke="#1a1a2e" 
                          stroke-width="2"
                          opacity="0.9">
                        <title>${level}: ${count} (${(percentage * 100).toFixed(1)}%)</title>
                    </path>
                `;
                
                startAngle = endAngle;
            });
            
            svg.innerHTML = paths;
            
            legend.innerHTML = levels.map(level => `
                <div class="legend-item">
                    <div class="legend-color" style="background: ${COLORS[level]}"></div>
                    <span>${level}</span>
                </div>
            `).join('');
        }
        
        function renderTimelineChart() {
            const svg = document.getElementById('timelineChart');
            const timeline = logData.timeline;
            
            if (timeline.length === 0) {
                svg.innerHTML = '<text x="350" y="150" text-anchor="middle" fill="#666">No error data available</text>';
                return;
            }
            
            const margin = { top: 20, right: 30, bottom: 60, left: 50 };
            const width = 700 - margin.left - margin.right;
            const height = 300 - margin.top - margin.bottom;
            
            const maxCount = Math.max(...timeline.map(d => d.count));
            const barWidth = Math.max(8, (width / timeline.length) - 4);
            
            let bars = '';
            let labels = '';
            
            // Grid lines
            const gridLines = 5;
            for (let i = 0; i <= gridLines; i++) {
                const y = margin.top + (height / gridLines) * i;
                const value = Math.round(maxCount - (maxCount / gridLines) * i);
                bars += `<line class="grid-line" x1="${margin.left}" y1="${y}" x2="${width + margin.left}" y2="${y}"/>`;
                bars += `<text class="axis-label" x="${margin.left - 10}" y="${y + 4}" text-anchor="end">${value}</text>`;
            }
            
            timeline.forEach((d, i) => {
                const barHeight = (d.count / maxCount) * height || 0;
                const x = margin.left + (i * (width / timeline.length)) + 2;
                const y = margin.top + height - barHeight;
                
                bars += `
                    <rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}"
                          fill="url(#barGradient)" rx="2">
                        <title>${d.hour}: ${d.count} errors</title>
                    </rect>
                `;
                
                // Show every nth label based on data size
                const labelInterval = Math.ceil(timeline.length / 12);
                if (i % labelInterval === 0) {
                    const label = d.hour.split(' ')[1] || d.hour;
                    labels += `
                        <text class="bar-label" x="${x + barWidth/2}" y="${height + margin.top + 15}" 
                              text-anchor="middle" transform="rotate(45, ${x + barWidth/2}, ${height + margin.top + 15})">
                            ${label}
                        </text>
                    `;
                }
            });
            
            svg.innerHTML = `
                <defs>
                    <linearGradient id="barGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#f87171;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#dc2626;stop-opacity:0.7" />
                    </linearGradient>
                </defs>
                ${bars}
                ${labels}
                <text class="axis-label" x="${margin.left + width/2}" y="${height + margin.top + 50}" text-anchor="middle">Time (Hour)</text>
                <text class="axis-label" x="15" y="${margin.top + height/2}" text-anchor="middle" transform="rotate(-90, 15, ${margin.top + height/2})">Error Count</text>
            `;
        }
        
        function renderTopErrors() {
            const list = document.getElementById('topErrorsList');
            
            if (logData.top_errors.length === 0) {
                list.innerHTML = '<li class="no-results">No errors found</li>';
                return;
            }
            
            list.innerHTML = logData.top_errors.map(err => `
                <li>
                    <span class="error-msg">${escapeHtml(err.message)}</span>
                    <span class="error-count">${err.count}</span>
                </li>
            `).join('');
        }
        
        function renderLogsTable() {
            const tbody = document.getElementById('logsTable');
            
            let logs = logData.all_logs;
            
            // Apply filter
            if (currentFilter !== 'ALL') {
                logs = logs.filter(log => log.level === currentFilter);
            }
            
            // Apply search
            if (searchTerm) {
                const term = searchTerm.toLowerCase();
                logs = logs.filter(log => 
                    log.message.toLowerCase().includes(term) ||
                    log.timestamp.includes(term)
                );
            }
            
            // Limit to most recent 500 for performance
            logs = logs.slice(-500).reverse();
            
            if (logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="no-results">No matching log entries</td></tr>';
                return;
            }
            
            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td>${escapeHtml(log.timestamp)}</td>
                    <td><span class="level-badge level-${log.level}">${log.level}</span></td>
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
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                renderLogsTable();
            });
        });
        
        document.getElementById('searchBox').addEventListener('input', (e) => {
            searchTerm = e.target.value;
            renderLogsTable();
        });
        
        // Initial load
        fetchData();
    </script>
</body>
</html>
'''


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for the dashboard."""
    
    log_stats = None
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())
        
        elif path == '/api/data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(json.dumps(self.log_stats).encode())
        
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')


def main():
    """Main entry point."""
    print("=" * 60)
    print("       LOG ANALYTICS DASHBOARD")
    print("=" * 60)
    
    # Check for log file and generate if missing
    if not os.path.exists(LOG_FILE):
        print(f"\n[*] Log file '{LOG_FILE}' not found.")
        print("[*] Generating fake log data...")
        generate_fake_logs(1000)
    else:
        print(f"\n[*] Found existing log file: {LOG_FILE}")
    
    # Parse logs
    print("[*] Parsing log file...")
    log_stats = parse_logs()
    
    print(f"\n[+] Total log entries: {log_stats['total_logs']}")
    print(f"[+] Log level breakdown:")
    for level, pct in sorted(log_stats['level_percentages'].items()):
        count = log_stats['level_counts'].get(level, 0)
        print(f"    - {level}: {count} ({pct}%)")
    print(f"[+] Critical entries: {len(log_stats['critical_logs'])}")
    
    # Set up HTTP server
    DashboardHandler.log_stats = log_stats
    
    server = HTTPServer(('localhost', PORT), DashboardHandler)
    
    print(f"\n{'=' * 60}")
    print(f"  Dashboard running at: http://localhost:{PORT}")
    print(f"  Press Ctrl+C to stop the server")
    print(f"{'=' * 60}\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down server...")
        server.shutdown()
        print("[*] Server stopped. Goodbye!")


if __name__ == '__main__':
    main()