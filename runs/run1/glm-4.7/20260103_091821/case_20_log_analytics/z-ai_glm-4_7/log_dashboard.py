#!/usr/bin/env python3
"""
Log Analytics Dashboard
A simple log analyzer with web dashboard interface
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
LOG_FILE = "server.log"
PORT = 8000


def generate_fake_logs(filename, num_lines=1000):
    """Generate fake log data with various log levels"""
    log_levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    
    # Sample log messages
    info_messages = [
        "Connection established from {ip}",
        "Request processed successfully",
        "User {user} logged in",
        "Cache hit for key: {key}",
        "Database query executed in {time}ms",
        "File uploaded: {file}",
        "Background task completed",
        "Health check passed",
        "API response sent: 200 OK",
        "Session started for user {user}"
    ]
    
    warn_messages = [
        "High memory usage: {percent}%",
        "Slow query detected: {time}ms",
        "Rate limit approaching for {ip}",
        "Deprecated API endpoint used",
        "Disk space low: {percent}% remaining",
        "Connection pool nearly exhausted",
        "Retrying failed request (attempt {attempt})",
        "Cache miss for key: {key}"
    ]
    
    error_messages = [
        "Failed to connect to database",
        "Timeout waiting for response",
        "Invalid authentication token",
        "Resource not found: {resource}",
        "Failed to write to file: {file}",
        "Network connection lost",
        "Invalid request parameters",
        "Service temporarily unavailable",
        "Query execution failed: constraint violation",
        "Unable to parse incoming data"
    ]
    
    critical_messages = [
        "Database connection pool exhausted",
        "Out of memory error - cannot allocate {size}MB",
        "Security breach detected from {ip}",
        "Critical service failure - component: {component}",
        "Data corruption detected in table: {table}",
        "System crash imminent - temperature: {temp}C",
        "Unauthorized root access attempt from {ip}",
        "Primary server unresponsive - failover initiated",
        "Disk failure imminent on /dev/sda1",
        "Kernel panic - dumping core"
    ]
    
    # Generate timestamps over the last 48 hours
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=48)
    
    with open(filename, 'w') as f:
        for _ in range(num_lines):
            # Random timestamp within range
            timestamp = start_time + timedelta(
                seconds=random.randint(0, int((end_time - start_time).total_seconds()))
            )
            
            level = random.choice(log_levels)
            
            if level == "INFO":
                msg = random.choice(info_messages)
            elif level == "WARN":
                msg = random.choice(warn_messages)
            elif level == "ERROR":
                msg = random.choice(error_messages)
            else:  # CRITICAL
                msg = random.choice(critical_messages)
            
            # Format message with random values
            msg = msg.format(
                ip=f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                user=f"user_{random.randint(1000,9999)}",
                key=f"key_{random.randint(1,100)}",
                time=random.randint(10, 5000),
                file=f"file_{random.randint(1,100)}.txt",
                percent=random.randint(5, 95),
                resource=f"/api/resource/{random.randint(1,100)}",
                attempt=random.randint(1, 5),
                size=random.randint(10, 500),
                component=random.choice(["auth", "database", "cache", "api", "worker"]),
                table=random.choice(["users", "logs", "sessions", "transactions"]),
                temp=random.randint(70, 95)
            )
            
            log_line = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {level} - {msg}"
            f.write(log_line + '\n')
    
    print(f"Generated {num_lines} fake log entries in {filename}")


def parse_logs(filename):
    """Parse log file and return analytics data"""
    log_pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+) - (.+)')
    
    level_counts = Counter()
    errors_per_hour = defaultdict(int)
    critical_errors = []
    all_errors = []
    all_logs = []
    
    with open(filename, 'r') as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                level_counts[level] += 1
                
                hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                
                if level in ['ERROR', 'CRITICAL']:
                    errors_per_hour[hour_key] += 1
                    all_errors.append({
                        'timestamp': timestamp_str,
                        'level': level,
                        'message': message
                    })
                
                if level == 'CRITICAL':
                    critical_errors.append({
                        'timestamp': timestamp_str,
                        'message': message
                    })
                
                all_logs.append({
                    'timestamp': timestamp_str,
                    'level': level,
                    'message': message
                })
    
    # Calculate percentages
    total = sum(level_counts.values())
    level_percentages = {
        level: (count / total) * 100 
        for level, count in level_counts.items()
    }
    
    # Sort errors per hour by time
    sorted_errors_per_hour = sorted(errors_per_hour.items())
    
    # Most common error messages (from ERROR and CRITICAL)
    error_messages = [log['message'] for log in all_errors]
    common_errors = Counter(error_messages).most_common(10)
    
    return {
        'level_counts': dict(level_counts),
        'level_percentages': level_percentages,
        'errors_per_hour': sorted_errors_per_hour,
        'common_errors': common_errors,
        'critical_errors': critical_errors,
        'all_errors': all_errors
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
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        .header h1 {
            font-size: 1.8rem;
            margin-bottom: 5px;
        }
        
        .header p {
            opacity: 0.8;
            font-size: 0.9rem;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: #16213e;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            border-left: 4px solid;
        }
        
        .stat-card.info { border-color: #4facfe; }
        .stat-card.warn { border-color: #f093fb; }
        .stat-card.error { border-color: #ff6b6b; }
        .stat-card.critical { border-color: #ff4757; }
        
        .stat-card h3 {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            opacity: 0.7;
        }
        
        .stat-card .value {
            font-size: 2rem;
            font-weight: bold;
        }
        
        .stat-card .percentage {
            font-size: 0.9rem;
            opacity: 0.6;
            margin-top: 5px;
        }
        
        .charts-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: #16213e;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        
        .chart-card h2 {
            font-size: 1.2rem;
            margin-bottom: 20px;
            color: #4facfe;
        }
        
        .bar-chart {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .bar-row {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .bar-label {
            width: 100px;
            font-size: 0.85rem;
        }
        
        .bar-container {
            flex: 1;
            height: 30px;
            background: #0f3460;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .bar {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        
        .bar.info { background: linear-gradient(90deg, #4facfe, #00f2fe); }
        .bar.warn { background: linear-gradient(90deg, #f093fb, #f5576c); }
        .bar.error { background: linear-gradient(90deg, #ff6b6b, #ee5a24); }
        .bar.critical { background: linear-gradient(90deg, #ff4757, #c0392b); }
        
        .bar-value {
            width: 60px;
            text-align: right;
            font-size: 0.85rem;
        }
        
        .timeline-chart {
            height: 200px;
            position: relative;
        }
        
        .timeline-svg {
            width: 100%;
            height: 100%;
        }
        
        .table-section {
            background: #16213e;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        
        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .table-header h2 {
            color: #4facfe;
        }
        
        .filters {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            background: #0f3460;
            color: #eee;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }
        
        .filter-btn:hover {
            background: #1a4a8a;
        }
        
        .filter-btn.active {
            background: #4facfe;
            color: #1a1a2e;
        }
        
        .search-box {
            padding: 8px 12px;
            border: 1px solid #0f3460;
            border-radius: 6px;
            background: #0f3460;
            color: #eee;
            font-size: 0.85rem;
            width: 250px;
        }
        
        .search-box:focus {
            outline: none;
            border-color: #4facfe;
        }
        
        .log-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .log-table th,
        .log-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #0f3460;
        }
        
        .log-table th {
            background: #0f3460;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .log-table tr:hover {
            background: rgba(79, 172, 254, 0.1);
        }
        
        .level-badge {
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .level-badge.ERROR {
            background: rgba(255, 107, 107, 0.2);
            color: #ff6b6b;
        }
        
        .level-badge.CRITICAL {
            background: rgba(255, 71, 87, 0.2);
            color: #ff4757;
        }
        
        .timestamp {
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            color: #888;
        }
        
        .message {
            max-width: 500px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .common-errors {
            margin-top: 30px;
        }
        
        .common-errors-list {
            display: grid;
            gap: 10px;
        }
        
        .error-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: #0f3460;
            border-radius: 6px;
        }
        
        .error-message {
            flex: 1;
            font-size: 0.9rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .error-count {
            background: #4facfe;
            color: #1a1a2e;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.85rem;
        }
        
        @media (max-width: 768px) {
            .charts-section {
                grid-template-columns: 1fr;
            }
            
            .table-header {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .filters {
                width: 100%;
            }
            
            .search-box {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Log Analytics Dashboard</h1>
        <p>Real-time log monitoring and analysis</p>
    </div>
    
    <div class="container">
        <div class="stats-grid" id="statsGrid">
            <!-- Stats will be populated by JS -->
        </div>
        
        <div class="charts-section">
            <div class="chart-card">
                <h2>Log Level Distribution</h2>
                <div class="bar-chart" id="levelChart">
                    <!-- Bars will be populated by JS -->
                </div>
            </div>
            
            <div class="chart-card">
                <h2>Errors Per Hour (Timeline)</h2>
                <div class="timeline-chart">
                    <svg class="timeline-svg" id="timelineChart"></svg>
                </div>
            </div>
        </div>
        
        <div class="chart-card common-errors">
            <h2>Most Common Error Messages</h2>
            <div class="common-errors-list" id="commonErrors">
                <!-- Will be populated by JS -->
            </div>
        </div>
        
        <div class="table-section">
            <div class="table-header">
                <h2>🚨 Critical & Error Logs</h2>
                <div class="filters">
                    <input type="text" class="search-box" id="searchBox" placeholder="Search logs...">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="ERROR">Error</button>
                    <button class="filter-btn" data-filter="CRITICAL">Critical</button>
                </div>
            </div>
            <table class="log-table">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Level</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody id="logTableBody">
                    <!-- Rows will be populated by JS -->
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        let analyticsData = null;
        let currentFilter = 'all';
        let searchTerm = '';
        
        // Fetch analytics data
        async function fetchAnalytics() {
            try {
                const response = await fetch('/api/analytics');
                analyticsData = await response.json();
                renderDashboard();
            } catch (error) {
                console.error('Failed to fetch analytics:', error);
            }
        }
        
        // Render the entire dashboard
        function renderDashboard() {
            renderStats();
            renderLevelChart();
            renderTimelineChart();
            renderCommonErrors();
            renderLogTable();
        }
        
        // Render statistics cards
        function renderStats() {
            const grid = document.getElementById('statsGrid');
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const colors = ['info', 'warn', 'error', 'critical'];
            
            grid.innerHTML = levels.map((level, i) => {
                const count = analyticsData.level_counts[level] || 0;
                const percentage = analyticsData.level_percentages[level] || 0;
                return `
                    <div class="stat-card ${colors[i]}">
                        <h3>${level}</h3>
                        <div class="value">${count}</div>
                        <div class="percentage">${percentage.toFixed(1)}%</div>
                    </div>
                `;
            }).join('');
        }
        
        // Render log level distribution chart
        function renderLevelChart() {
            const chart = document.getElementById('levelChart');
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const colors = ['info', 'warn', 'error', 'critical'];
            
            const maxCount = Math.max(...levels.map(l => analyticsData.level_counts[l] || 0));
            
            chart.innerHTML = levels.map((level, i) => {
                const count = analyticsData.level_counts[level] || 0;
                const percentage = analyticsData.level_percentages[level] || 0;
                const width = maxCount > 0 ? (count / maxCount) * 100 : 0;
                
                return `
                    <div class="bar-row">
                        <div class="bar-label">${level}</div>
                        <div class="bar-container">
                            <div class="bar ${colors[i]}" style="width: ${width}%"></div>
                        </div>
                        <div class="bar-value">${count}</div>
                    </div>
                `;
            }).join('');
        }
        
        // Render timeline chart using SVG
        function renderTimelineChart() {
            const svg = document.getElementById('timelineChart');
            const data = analyticsData.errors_per_hour;
            
            if (data.length === 0) {
                svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#888">No error data available</text>';
                return;
            }
            
            const width = svg.clientWidth || 500;
            const height = 200;
            const padding = 40;
            
            const maxValue = Math.max(...data.map(d => d[1]));
            const chartWidth = width - padding * 2;
            const chartHeight = height - padding * 2;
            
            // Create bars
            const barWidth = Math.max(2, (chartWidth / data.length) - 2);
            
            let bars = '';
            data.forEach(([hour, count], i) => {
                const x = padding + (i * (chartWidth / data.length));
                const barHeight = maxValue > 0 ? (count / maxValue) * chartHeight : 0;
                const y = height - padding - barHeight;
                
                const color = count > maxValue * 0.7 ? '#ff4757' : '#ff6b6b';
                
                bars += `
                    <rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" fill="${color}" rx="2">
                        <title>${hour}: ${count} errors</title>
                    </rect>
                `;
            });
            
            // Add axes
            const axes = `
                <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="#4facfe" stroke-width="2"/>
                <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" stroke="#4facfe" stroke-width="2"/>
            `;
            
            // Add Y-axis labels
            let yLabels = '';
            for (let i = 0; i <= 4; i++) {
                const value = Math.round((maxValue / 4) * i);
                const y = height - padding - (chartHeight / 4) * i;
                yLabels += `<text x="${padding - 10}" y="${y + 4}" text-anchor="end" fill="#888" font-size="10">${value}</text>`;
            }
            
            svg.innerHTML = axes + bars + yLabels;
        }
        
        // Render common errors
        function renderCommonErrors() {
            const container = document.getElementById('commonErrors');
            const errors = analyticsData.common_errors;
            
            if (errors.length === 0) {
                container.innerHTML = '<p style="color: #888;">No error data available</p>';
                return;
            }
            
            container.innerHTML = errors.map(([msg, count]) => `
                <div class="error-item">
                    <div class="error-message" title="${msg}">${msg}</div>
                    <div class="error-count">${count}</div>
                </div>
            `).join('');
        }
        
        // Render log table
        function renderLogTable() {
            const tbody = document.getElementById('logTableBody');
            
            let logs = analyticsData.all_errors;
            
            // Apply filter
            if (currentFilter !== 'all') {
                logs = logs.filter(log => log.level === currentFilter);
            }
            
            // Apply search
            if (searchTerm) {
                const term = searchTerm.toLowerCase();
                logs = logs.filter(log => 
                    log.message.toLowerCase().includes(term) ||
                    log.timestamp.toLowerCase().includes(term)
                );
            }
            
            if (logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #888; padding: 30px;">No logs found</td></tr>';
                return;
            }
            
            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td><span class="timestamp">${log.timestamp}</span></td>
                    <td><span class="level-badge ${log.level}">${log.level}</span></td>
                    <td><span class="message" title="${log.message}">${log.message}</span></td>
                </tr>
            `).join('');
        }
        
        // Event listeners
        document.getElementById('searchBox').addEventListener('input', (e) => {
            searchTerm = e.target.value;
            renderLogTable();
        });
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                renderLogTable();
            });
        });
        
        // Handle window resize for timeline chart
        window.addEventListener('resize', () => {
            if (analyticsData) {
                renderTimelineChart();
            }
        });
        
        // Initialize
        fetchAnalytics();
    </script>
</body>
</html>
'''


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for serving the dashboard and API"""
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())
        
        elif parsed_path.path == '/api/analytics':
            analytics = parse_logs(LOG_FILE)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(analytics).encode())
        
        else:
            self.send_error(404, 'Not Found')
    
    def log_message(self, format, *args):
        # Suppress default HTTP logging for cleaner output
        pass


def main():
    # Check for log file, generate if missing
    if not os.path.exists(LOG_FILE):
        print(f"Log file '{LOG_FILE}' not found. Generating fake log data...")
        generate_fake_logs(LOG_FILE, 1000)
    else:
        print(f"Using existing log file: {LOG_FILE}")
    
    # Parse logs to verify and show summary
    analytics = parse_logs(LOG_FILE)
    print(f"\n{'='*50}")
    print("Log Summary:")
    print(f"{'='*50}")
    for level, count in analytics['level_counts'].items():
        print(f"  {level}: {count} ({analytics['level_percentages'][level]:.1f}%)")
    print(f"\n  Critical Errors: {len(analytics['critical_errors'])}")
    print(f"  Total Errors: {len(analytics['all_errors'])}")
    print(f"  Hours with errors: {len(analytics['errors_per_hour'])}")
    
    # Start HTTP server
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"\n{'='*50}")
        print(f"🚀 Dashboard running at: http://localhost:{PORT}")
        print(f"{'='*50}")
        print("Press Ctrl+C to stop the server\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            httpd.shutdown()


if __name__ == "__main__":
    main()