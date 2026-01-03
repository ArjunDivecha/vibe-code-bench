#!/usr/bin/env python3
"""Log Analytics Dashboard - Python 3 Stdlib Only"""

import http.server
import json
import os
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from urllib.parse import urlparse
import socketserver

LOG_FILE = "server.log"

# Error message templates
ERROR_MESSAGES = [
    "Connection timeout to database server",
    "Failed to authenticate user",
    "Memory allocation failed",
    "Disk space critically low",
    "Network interface unreachable",
    "SSL certificate expired",
    "Invalid request format",
    "Service unavailable",
    "Rate limit exceeded",
    "Permission denied for resource",
    "File not found",
    "Configuration error detected",
    "Cache miss for key",
    "Queue overflow detected",
    "Deadlock detected in transaction",
]

INFO_MESSAGES = [
    "User logged in successfully",
    "Request processed",
    "Cache hit for query",
    "Connection established",
    "File uploaded successfully",
    "Scheduled task completed",
    "Configuration reloaded",
    "Health check passed",
    "Session started",
    "Data synchronized",
]

WARN_MESSAGES = [
    "High memory usage detected",
    "Slow query detected",
    "Deprecated API endpoint used",
    "Connection pool running low",
    "Retry attempt initiated",
    "Response time exceeded threshold",
    "Temporary file cleanup pending",
    "Session about to expire",
]


def generate_fake_logs(num_lines=1000):
    """Generate fake log data."""
    levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    weights = [0.6, 0.25, 0.12, 0.03]
    
    base_time = datetime.now() - timedelta(hours=24)
    logs = []
    
    for i in range(num_lines):
        level = random.choices(levels, weights=weights)[0]
        timestamp = base_time + timedelta(seconds=random.randint(0, 86400))
        
        if level == "INFO":
            message = random.choice(INFO_MESSAGES)
        elif level == "WARN":
            message = random.choice(WARN_MESSAGES)
        else:
            message = random.choice(ERROR_MESSAGES)
        
        log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}"
        logs.append((timestamp, log_line))
    
    logs.sort(key=lambda x: x[0])
    
    with open(LOG_FILE, 'w') as f:
        for _, line in logs:
            f.write(line + '\n')
    
    print(f"Generated {num_lines} log entries in {LOG_FILE}")


def parse_logs():
    """Parse the log file and extract analytics."""
    log_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (.+)$')
    
    level_counts = Counter()
    errors_per_hour = defaultdict(int)
    error_messages = Counter()
    critical_logs = []
    all_logs = []
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
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
                
                if level in ['ERROR', 'CRITICAL']:
                    hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                    errors_per_hour[hour_key] += 1
                    error_messages[message] += 1
                
                if level == 'CRITICAL':
                    critical_logs.append(log_entry)
    
    total = sum(level_counts.values())
    level_percentages = {level: (count / total * 100) if total > 0 else 0 
                         for level, count in level_counts.items()}
    
    sorted_hours = sorted(errors_per_hour.keys())
    errors_timeline = [{'hour': h, 'count': errors_per_hour[h]} for h in sorted_hours]
    
    top_errors = [{'message': msg, 'count': count} 
                  for msg, count in error_messages.most_common(10)]
    
    return {
        'level_percentages': level_percentages,
        'level_counts': dict(level_counts),
        'errors_timeline': errors_timeline,
        'top_errors': top_errors,
        'critical_logs': critical_logs,
        'all_logs': all_logs,
        'total_logs': total
    }


log_data = None


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
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #00d4ff;
            font-size: 2.5em;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        }
        .stats-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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
        .stat-card h3 {
            font-size: 0.9em;
            color: #888;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
        }
        .stat-card.info .value { color: #00d4ff; }
        .stat-card.warn .value { color: #ffc107; }
        .stat-card.error .value { color: #ff6b6b; }
        .stat-card.critical .value { color: #ff4757; }
        .stat-card.total .value { color: #a855f7; }
        
        .charts-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        @media (max-width: 900px) {
            .charts-row {
                grid-template-columns: 1fr;
            }
        }
        .chart-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .chart-card h2 {
            margin-bottom: 20px;
            color: #00d4ff;
            font-size: 1.2em;
        }
        .chart-container {
            width: 100%;
            height: 300px;
        }
        
        .pie-section {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 40px;
            flex-wrap: wrap;
        }
        .pie-legend {
            display: flex;
            flex-direction: column;
            gap: 10px;
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
        
        .table-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .table-section h2 {
            margin-bottom: 20px;
            color: #00d4ff;
            font-size: 1.2em;
        }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .search-box {
            flex: 1;
            min-width: 200px;
            padding: 12px 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 25px;
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
            font-size: 1em;
            outline: none;
            transition: border-color 0.3s;
        }
        .search-box:focus {
            border-color: #00d4ff;
        }
        .search-box::placeholder {
            color: #666;
        }
        .filter-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .filter-btn {
            padding: 12px 20px;
            border: none;
            border-radius: 25px;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9em;
        }
        .filter-btn:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        .filter-btn.active {
            background: #00d4ff;
            color: #1a1a2e;
        }
        
        .log-table {
            width: 100%;
            border-collapse: collapse;
        }
        .log-table th {
            background: rgba(0, 212, 255, 0.2);
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #00d4ff;
        }
        .log-table td {
            padding: 12px 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .log-table tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        .level-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .level-INFO { background: rgba(0, 212, 255, 0.2); color: #00d4ff; }
        .level-WARN { background: rgba(255, 193, 7, 0.2); color: #ffc107; }
        .level-ERROR { background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }
        .level-CRITICAL { background: rgba(255, 71, 87, 0.3); color: #ff4757; }
        
        .table-wrapper {
            max-height: 400px;
            overflow-y: auto;
        }
        .table-wrapper::-webkit-scrollbar {
            width: 8px;
        }
        .table-wrapper::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
        .table-wrapper::-webkit-scrollbar-thumb {
            background: #00d4ff;
            border-radius: 4px;
        }
        
        .top-errors {
            max-height: 280px;
            overflow-y: auto;
        }
        .error-bar {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }
        .error-bar-label {
            width: 250px;
            font-size: 0.85em;
            color: #ccc;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .error-bar-container {
            flex: 1;
            height: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            margin: 0 15px;
            overflow: hidden;
        }
        .error-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #ff4757);
            border-radius: 10px;
            transition: width 0.5s ease;
        }
        .error-bar-count {
            min-width: 40px;
            text-align: right;
            color: #ff6b6b;
            font-weight: bold;
        }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .results-count {
            color: #888;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Log Analytics Dashboard</h1>
        
        <div class="stats-row" id="statsRow"></div>
        
        <div class="charts-row">
            <div class="chart-card">
                <h2>📈 Errors Over Time (24h)</h2>
                <div class="chart-container" id="timelineChart"></div>
            </div>
            <div class="chart-card">
                <h2>🔴 Top Error Messages</h2>
                <div class="top-errors" id="topErrors"></div>
            </div>
        </div>
        
        <div class="table-section">
            <h2>🚨 Log Entries</h2>
            <div class="controls">
                <input type="text" class="search-box" id="searchBox" placeholder="Search logs by message or timestamp...">
                <div class="filter-buttons">
                    <button class="filter-btn active" data-level="ALL">All</button>
                    <button class="filter-btn" data-level="CRITICAL">Critical</button>
                    <button class="filter-btn" data-level="ERROR">Error</button>
                    <button class="filter-btn" data-level="WARN">Warning</button>
                    <button class="filter-btn" data-level="INFO">Info</button>
                </div>
            </div>
            <div class="results-count" id="resultsCount"></div>
            <div class="table-wrapper">
                <table class="log-table">
                    <thead>
                        <tr>
                            <th style="width: 180px;">Timestamp</th>
                            <th style="width: 100px;">Level</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody id="logTableBody"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        let logData = null;
        let currentFilter = 'ALL';
        let searchTerm = '';
        
        async function fetchData() {
            try {
                const response = await fetch('/api/stats');
                logData = await response.json();
                renderDashboard();
            } catch (err) {
                console.error('Failed to fetch data:', err);
            }
        }
        
        function renderDashboard() {
            renderStats();
            renderTimeline();
            renderTopErrors();
            renderTable();
        }
        
        function renderStats() {
            const statsRow = document.getElementById('statsRow');
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const levelClasses = { INFO: 'info', WARN: 'warn', ERROR: 'error', CRITICAL: 'critical' };
            
            let html = `
                <div class="stat-card total">
                    <h3>Total Logs</h3>
                    <div class="value">${logData.total_logs.toLocaleString()}</div>
                </div>
            `;
            
            levels.forEach(level => {
                const count = logData.level_counts[level] || 0;
                const pct = logData.level_percentages[level] || 0;
                html += `
                    <div class="stat-card ${levelClasses[level]}">
                        <h3>${level}</h3>
                        <div class="value">${pct.toFixed(1)}%</div>
                        <div style="color: #666; font-size: 0.9em; margin-top: 5px;">${count} entries</div>
                    </div>
                `;
            });
            
            statsRow.innerHTML = html;
        }
        
        function renderTimeline() {
            const container = document.getElementById('timelineChart');
            const data = logData.errors_timeline;
            
            if (data.length === 0) {
                container.innerHTML = '<div class="no-data">No error data available</div>';
                return;
            }
            
            const maxCount = Math.max(...data.map(d => d.count), 1);
            const width = container.clientWidth || 500;
            const height = 280;
            const padding = { top: 20, right: 30, bottom: 70, left: 50 };
            const chartWidth = width - padding.left - padding.right;
            const chartHeight = height - padding.top - padding.bottom;
            
            const barWidth = Math.max(6, Math.min(30, (chartWidth / data.length) - 3));
            const totalBarsWidth = data.length * (barWidth + 3);
            const startX = padding.left + (chartWidth - totalBarsWidth) / 2;
            
            let svg = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`;
            
            // Gradient definition
            svg += `
                <defs>
                    <linearGradient id="barGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#ff6b6b;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#ff4757;stop-opacity:1" />
                    </linearGradient>
                </defs>
            `;
            
            // Y-axis gridlines and labels
            const ySteps = 5;
            for (let i = 0; i <= ySteps; i++) {
                const y = padding.top + (chartHeight / ySteps) * i;
                const value = Math.round(maxCount * (1 - i / ySteps));
                svg += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="rgba(255,255,255,0.1)" />`;
                svg += `<text x="${padding.left - 10}" y="${y + 4}" fill="#888" text-anchor="end" font-size="11">${value}</text>`;
            }
            
            // Bars
            data.forEach((d, i) => {
                const x = startX + (i * (barWidth + 3));
                const barHeight = (d.count / maxCount) * chartHeight;
                const y = padding.top + chartHeight - barHeight;
                
                svg += `
                    <rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" 
                          fill="url(#barGradient)" rx="3">
                        <title>${d.hour}: ${d.count} errors</title>
                    </rect>
                `;
                
                // X-axis labels
                if (data.length <= 12 || i % Math.ceil(data.length / 10) === 0) {
                    const hour = d.hour.split(' ')[1] || d.hour;
                    svg += `<text x="${x + barWidth/2}" y="${height - 25}" fill="#888" text-anchor="middle" font-size="10" transform="rotate(-45 ${x + barWidth/2} ${height - 25})">${hour}</text>`;
                }
            });
            
            // Axis lines
            svg += `<line x1="${padding.left}" y1="${padding.top + chartHeight}" x2="${width - padding.right}" y2="${padding.top + chartHeight}" stroke="rgba(255,255,255,0.3)" />`;
            svg += `<line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${padding.top + chartHeight}" stroke="rgba(255,255,255,0.3)" />`;
            
            svg += '</svg>';
            container.innerHTML = svg;
        }
        
        function renderTopErrors() {
            const container = document.getElementById('topErrors');
            const errors = logData.top_errors;
            
            if (errors.length === 0) {
                container.innerHTML = '<div class="no-data">No errors found</div>';
                return;
            }
            
            const maxCount = errors[0].count;
            
            let html = '';
            errors.forEach(err => {
                const percentage = (err.count / maxCount) * 100;
                html += `
                    <div class="error-bar">
                        <div class="error-bar-label" title="${err.message}">${err.message}</div>
                        <div class="error-bar-container">
                            <div class="error-bar-fill" style="width: ${percentage}%"></div>
                        </div>
                        <div class="error-bar-count">${err.count}</div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        function renderTable() {
            const tbody = document.getElementById('logTableBody');
            const resultsCount = document.getElementById('resultsCount');
            let logs = logData.all_logs;
            
            // Filter by level
            if (currentFilter !== 'ALL') {
                logs = logs.filter(log => log.level === currentFilter);
            }
            
            // Filter by search term
            if (searchTerm) {
                const term = searchTerm.toLowerCase();
                logs = logs.filter(log => 
                    log.message.toLowerCase().includes(term) ||
                    log.timestamp.toLowerCase().includes(term)
                );
            }
            
            const totalFiltered = logs.length;
            
            // Show most recent first, limit to 500
            logs = logs.slice().reverse().slice(0, 500);
            
            resultsCount.textContent = `Showing ${logs.length} of ${totalFiltered} matching entries`;
            
            if (logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="no-data">No matching logs found</td></tr>';
                return;
            }
            
            let html = '';
            logs.forEach(log => {
                html += `
                    <tr>
                        <td style="white-space: nowrap; font-family: monospace; font-size: 0.9em;">${log.timestamp}</td>
                        <td><span class="level-badge level-${log.level}">${log.level}</span></td>
                        <td>${escapeHtml(log.message)}</td>
                    </tr>
                `;
            });
            
            tbody.innerHTML = html;
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
                currentFilter = btn.dataset.level;
                renderTable();
            });
        });
        
        let searchTimeout;
        document.getElementById('searchBox').addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchTerm = e.target.value;
                renderTable();
            }, 200);
        });
        
        // Handle window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (logData) {
                    renderTimeline();
                }
            }, 250);
        });
        
        // Initial load
        fetchData();
    </script>
</body>
</html>
'''


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for the dashboard."""
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode('utf-8'))
        
        elif parsed_path.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(json.dumps(log_data).encode('utf-8'))
        
        else:
            self.send_error(404, 'Not Found')
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class ReusableTCPServer(socketserver.TCPServer):
    """TCP Server that allows address reuse."""
    allow_reuse_address = True


def main():
    global log_data
    
    print("=" * 55)
    print("       📊 Log Analytics Dashboard")
    print("=" * 55)
    
    # Check for log file and generate if missing
    if not os.path.exists(LOG_FILE):
        print(f"\n[INFO] {LOG_FILE} not found. Generating fake log data...")
        generate_fake_logs(1000)
    else:
        print(f"\n[INFO] Found existing {LOG_FILE}")
    
    # Parse logs
    print("[INFO] Parsing log file...")
    log_data = parse_logs()
    
    print(f"[INFO] Processed {log_data['total_logs']} log entries")
    print(f"       ├─ INFO:     {log_data['level_counts'].get('INFO', 0):>5} ({log_data['level_percentages'].get('INFO', 0):.1f}%)")
    print(f"       ├─ WARN:     {log_data['level_counts'].get('WARN', 0):>5} ({log_data['level_percentages'].get('WARN', 0):.1f}%)")
    print(f"       ├─ ERROR:    {log_data['level_counts'].get('ERROR', 0):>5} ({log_data['level_percentages'].get('ERROR', 0):.1f}%)")
    print(f"       └─ CRITICAL: {log_data['level_counts'].get('CRITICAL', 0):>5} ({log_data['level_percentages'].get('CRITICAL', 0):.1f}%)")
    
    # Start server
    PORT = 8080
    
    try:
        with ReusableTCPServer(("", PORT), DashboardHandler) as httpd:
            print(f"\n[INFO] Starting HTTP server on port {PORT}")
            print("=" * 55)
            print(f"\n   🚀 Dashboard URL: http://localhost:{PORT}")
            print(f"\n   Press Ctrl+C to stop the server")
            print("\n" + "=" * 55 + "\n")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n\n[INFO] Shutting down server...")
                
    except OSError as e:
        if e.errno == 98 or e.errno == 48:  # Address already in use
            print(f"\n[ERROR] Port {PORT} is already in use.")
            print("        Try stopping any other servers or use a different port.")
        else:
            raise


if __name__ == "__main__":
    main()