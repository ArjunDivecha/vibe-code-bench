#!/usr/bin/env python3
"""Log Analytics Dashboard - Python 3 Stdlib Only"""

import http.server
import json
import os
import random
import re
import socketserver
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from urllib.parse import urlparse

LOG_FILE = "server.log"
PORT = 8080

# Sample messages for generation
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
    "Database query timeout",
    "File not found",
    "Permission denied",
    "Invalid configuration",
    "Out of memory error",
    "Connection refused",
]

INFO_MESSAGES = [
    "User logged in successfully",
    "Request processed",
    "Cache refreshed",
    "Scheduled task completed",
    "Connection established",
    "Service started",
    "Health check passed",
    "Configuration loaded",
    "Session created",
    "Data synchronized",
]

WARN_MESSAGES = [
    "High memory usage detected",
    "Slow database query",
    "Deprecated API called",
    "Connection pool nearly exhausted",
    "Cache miss rate high",
    "Retry attempt",
    "Response time degraded",
    "Queue size increasing",
]


def generate_fake_logs(num_lines=1000):
    """Generate fake log data"""
    levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    weights = [60, 25, 12, 3]
    
    logs = []
    base_time = datetime.now() - timedelta(hours=24)
    
    for i in range(num_lines):
        time_offset = timedelta(seconds=random.randint(0, 86400))
        timestamp = base_time + time_offset
        
        level = random.choices(levels, weights=weights)[0]
        
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
    """Parse log file and extract analytics"""
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
            match = log_pattern.match(line.strip())
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
                    error_messages[message] += 1
                
                if level == 'CRITICAL':
                    critical_logs.append(log_entry)
    
    total = sum(level_counts.values())
    level_percentages = {
        level: round(count / total * 100, 2) if total > 0 else 0
        for level, count in level_counts.items()
    }
    
    sorted_hours = sorted(errors_per_hour.keys())
    errors_timeline = [
        {'hour': hour, 'count': errors_per_hour[hour]}
        for hour in sorted_hours
    ]
    
    top_errors = [
        {'message': msg, 'count': count}
        for msg, count in error_messages.most_common(10)
    ]
    
    return {
        'level_percentages': level_percentages,
        'level_counts': dict(level_counts),
        'errors_timeline': errors_timeline,
        'top_errors': top_errors,
        'critical_logs': critical_logs,
        'all_logs': all_logs,
        'total_logs': total
    }


DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log Analytics Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container { max-width: 1400px; margin: 0 auto; }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #00d9ff;
            font-size: 2.5rem;
            text-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(145deg, #16213e, #1a1a2e);
            border-radius: 16px;
            padding: 25px 20px;
            text-align: center;
            border: 1px solid #0f3460;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
        }
        
        .stat-card.info { border-top: 4px solid #00d9ff; }
        .stat-card.warn { border-top: 4px solid #ffc107; }
        .stat-card.error { border-top: 4px solid #ff6b6b; }
        .stat-card.critical { border-top: 4px solid #e63946; }
        .stat-card.total { border-top: 4px solid #9d4edd; }
        
        .stat-value {
            font-size: 2.8rem;
            font-weight: bold;
            margin-bottom: 8px;
            background: linear-gradient(90deg, #fff, #00d9ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stat-label {
            color: #888;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-percent {
            color: #00d9ff;
            font-size: 0.9rem;
            margin-top: 5px;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: linear-gradient(145deg, #16213e, #1a1a2e);
            border-radius: 16px;
            padding: 25px;
            border: 1px solid #0f3460;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        .chart-title {
            font-size: 1.2rem;
            margin-bottom: 20px;
            color: #00d9ff;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .table-container {
            background: linear-gradient(145deg, #16213e, #1a1a2e);
            border-radius: 16px;
            padding: 25px;
            border: 1px solid #0f3460;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .search-box {
            padding: 12px 18px;
            border-radius: 10px;
            border: 2px solid #0f3460;
            background: #1a1a2e;
            color: #eee;
            font-size: 1rem;
            width: 300px;
            transition: border-color 0.3s;
        }
        
        .search-box:focus {
            outline: none;
            border-color: #00d9ff;
        }
        
        .filter-buttons { display: flex; gap: 10px; }
        
        .filter-btn {
            padding: 12px 24px;
            border-radius: 10px;
            border: 2px solid #0f3460;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.3s;
            background: transparent;
            color: #888;
        }
        
        .filter-btn:hover { border-color: #00d9ff; color: #00d9ff; }
        
        .filter-btn.active {
            background: #00d9ff;
            color: #1a1a2e;
            border-color: #00d9ff;
        }
        
        table { width: 100%; border-collapse: collapse; }
        
        th, td {
            padding: 14px 12px;
            text-align: left;
            border-bottom: 1px solid #0f3460;
        }
        
        th {
            background: #0f3460;
            color: #00d9ff;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 1px;
        }
        
        tr:hover { background: rgba(0, 217, 255, 0.05); }
        
        .level-badge {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .level-INFO { background: rgba(0, 217, 255, 0.2); color: #00d9ff; }
        .level-WARN { background: rgba(255, 193, 7, 0.2); color: #ffc107; }
        .level-ERROR { background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }
        .level-CRITICAL { background: rgba(230, 57, 70, 0.2); color: #e63946; }
        
        .svg-chart { width: 100%; height: 280px; }
        
        .pie-container { display: flex; align-items: center; justify-content: center; gap: 40px; flex-wrap: wrap; }
        
        .pie-legend { display: flex; flex-direction: column; gap: 12px; }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.95rem;
        }
        
        .legend-color {
            width: 18px;
            height: 18px;
            border-radius: 5px;
        }
        
        .top-errors-list { list-style: none; }
        
        .top-errors-list li {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 0;
            border-bottom: 1px solid #0f3460;
            gap: 15px;
        }
        
        .top-errors-list li:last-child { border-bottom: none; }
        
        .error-msg {
            flex: 1;
            color: #ccc;
        }
        
        .error-count {
            background: rgba(255, 107, 107, 0.2);
            color: #ff6b6b;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: bold;
            white-space: nowrap;
        }
        
        .table-scroll {
            max-height: 450px;
            overflow-y: auto;
        }
        
        .table-scroll::-webkit-scrollbar { width: 8px; }
        .table-scroll::-webkit-scrollbar-track { background: #1a1a2e; border-radius: 4px; }
        .table-scroll::-webkit-scrollbar-thumb { background: #0f3460; border-radius: 4px; }
        .table-scroll::-webkit-scrollbar-thumb:hover { background: #00d9ff; }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }
        
        .bar-label { fill: #888; font-size: 10px; }
        .axis-line { stroke: #0f3460; stroke-width: 1; }
        .grid-line { stroke: #0f3460; stroke-width: 1; stroke-dasharray: 3,3; }
        
        @media (max-width: 768px) {
            .charts-grid { grid-template-columns: 1fr; }
            .search-box { width: 100%; }
            h1 { font-size: 1.8rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Log Analytics Dashboard</h1>
        
        <div class="stats-grid" id="statsGrid"></div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3 class="chart-title">📈 Log Level Distribution</h3>
                <div class="pie-container">
                    <svg id="pieChart" width="200" height="200" viewBox="0 0 200 200"></svg>
                    <div class="pie-legend" id="pieLegend"></div>
                </div>
            </div>
            
            <div class="chart-card">
                <h3 class="chart-title">⏰ Errors per Hour (Last 24h)</h3>
                <svg id="barChart" class="svg-chart" viewBox="0 0 600 280"></svg>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card" style="grid-column: 1 / -1;">
                <h3 class="chart-title">🔥 Top Error Messages</h3>
                <ul class="top-errors-list" id="topErrorsList"></ul>
            </div>
        </div>
        
        <div class="table-container">
            <div class="table-header">
                <h3 class="chart-title">📋 Log Entries</h3>
                <div class="filter-buttons">
                    <button class="filter-btn active" data-filter="ALL">All</button>
                    <button class="filter-btn" data-filter="ERROR">Error</button>
                    <button class="filter-btn" data-filter="CRITICAL">Critical</button>
                </div>
                <input type="text" class="search-box" id="searchBox" placeholder="🔍 Search logs...">
            </div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Level</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody id="logsTable"></tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let logData = null;
        let currentFilter = 'ALL';
        let searchTerm = '';
        
        const COLORS = {
            INFO: '#00d9ff',
            WARN: '#ffc107',
            ERROR: '#ff6b6b',
            CRITICAL: '#e63946'
        };
        
        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                logData = await response.json();
                renderDashboard();
            } catch (error) {
                console.error('Failed to fetch data:', error);
                document.body.innerHTML = '<div class="no-data">Failed to load log data</div>';
            }
        }
        
        function renderDashboard() {
            renderStats();
            renderPieChart();
            renderBarChart();
            renderTopErrors();
            renderTable();
        }
        
        function renderStats() {
            const grid = document.getElementById('statsGrid');
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            
            grid.innerHTML = `
                <div class="stat-card total">
                    <div class="stat-value">${logData.total_logs.toLocaleString()}</div>
                    <div class="stat-label">Total Logs</div>
                </div>
                ${levels.map(level => `
                    <div class="stat-card ${level.toLowerCase()}">
                        <div class="stat-value">${(logData.level_counts[level] || 0).toLocaleString()}</div>
                        <div class="stat-label">${level}</div>
                        <div class="stat-percent">${logData.level_percentages[level] || 0}%</div>
                    </div>
                `).join('')}
            `;
        }
        
        function renderPieChart() {
            const svg = document.getElementById('pieChart');
            const legend = document.getElementById('pieLegend');
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const total = logData.total_logs;
            
            if (total === 0) {
                svg.innerHTML = '<text x="100" y="100" text-anchor="middle" fill="#888">No data</text>';
                return;
            }
            
            const cx = 100, cy = 100, r = 80;
            let startAngle = -90;
            let paths = '';
            let legendHtml = '';
            
            levels.forEach(level => {
                const count = logData.level_counts[level] || 0;
                const percentage = count / total;
                const angle = percentage * 360;
                
                if (percentage > 0) {
                    const endAngle = startAngle + angle;
                    const largeArc = angle > 180 ? 1 : 0;
                    
                    const x1 = cx + r * Math.cos(startAngle * Math.PI / 180);
                    const y1 = cy + r * Math.sin(startAngle * Math.PI / 180);
                    const x2 = cx + r * Math.cos(endAngle * Math.PI / 180);
                    const y2 = cy + r * Math.sin(endAngle * Math.PI / 180);
                    
                    if (percentage === 1) {
                        paths += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${COLORS[level]}"/>`;
                    } else {
                        paths += `<path d="M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z" 
                                  fill="${COLORS[level]}" stroke="#1a1a2e" stroke-width="2" style="cursor:pointer">
                                  <title>${level}: ${count.toLocaleString()} (${(percentage * 100).toFixed(1)}%)</title>
                                  </path>`;
                    }
                    startAngle = endAngle;
                }
                
                legendHtml += `
                    <div class="legend-item">
                        <div class="legend-color" style="background: ${COLORS[level]}"></div>
                        <span><strong>${level}</strong>: ${count.toLocaleString()} (${(percentage * 100).toFixed(1)}%)</span>
                    </div>
                `;
            });
            
            svg.innerHTML = paths;
            legend.innerHTML = legendHtml;
        }
        
        function renderBarChart() {
            const svg = document.getElementById('barChart');
            const timeline = logData.errors_timeline;
            
            if (timeline.length === 0) {
                svg.innerHTML = '<text x="300" y="140" text-anchor="middle" fill="#888" font-size="14">No errors recorded</text>';
                return;
            }
            
            const maxCount = Math.max(...timeline.map(d => d.count), 1);
            const chartWidth = 540;
            const chartHeight = 200;
            const marginLeft = 50;
            const marginTop = 20;
            const marginBottom = 60;
            
            const barWidth = Math.max(8, Math.min(25, (chartWidth / timeline.length) - 4));
            const barGap = (chartWidth - (timeline.length * barWidth)) / (timeline.length + 1);
            
            let content = '';
            
            // Y-axis
            content += `<line x1="${marginLeft}" y1="${marginTop}" x2="${marginLeft}" y2="${marginTop + chartHeight}" class="axis-line"/>`;
            
            // Y-axis labels and grid
            for (let i = 0; i <= 5; i++) {
                const y = marginTop + chartHeight - (i * chartHeight / 5);
                const val = Math.round(maxCount * i / 5);
                content += `<text x="${marginLeft - 8}" y="${y + 4}" fill="#888" font-size="11" text-anchor="end">${val}</text>`;
                if (i > 0) {
                    content += `<line x1="${marginLeft}" y1="${y}" x2="${marginLeft + chartWidth}" y2="${y}" class="grid-line"/>`;
                }
            }
            
            // X-axis
            content += `<line x1="${marginLeft}" y1="${marginTop + chartHeight}" x2="${marginLeft + chartWidth}" y2="${marginTop + chartHeight}" class="axis-line"/>`;
            
            // Bars
            timeline.forEach((d, i) => {
                const x = marginLeft + barGap + i * (barWidth + barGap);
                const height = (d.count / maxCount) * chartHeight;
                const y = marginTop + chartHeight - height;
                
                content += `<rect x="${x}" y="${y}" width="${barWidth}" height="${height}" 
                           fill="url(#barGradient)" rx="3" style="cursor:pointer">
                           <title>${d.hour}\\n${d.count} error${d.count !== 1 ? 's' : ''}</title>
                           </rect>`;
                
                // X-axis labels (show every nth label to avoid crowding)
                const showEvery = Math.max(1, Math.ceil(timeline.length / 12));
                if (i % showEvery === 0) {
                    const hour = d.hour.split(' ')[1] || d.hour.substring(11);
                    content += `<text x="${x + barWidth/2}" y="${marginTop + chartHeight + 15}" 
                               fill="#888" font-size="10" text-anchor="middle"
                               transform="rotate(45, ${x + barWidth/2}, ${marginTop + chartHeight + 15})">${hour}</text>`;
                }
            });
            
            // Gradient definition
            const defs = `<defs>
                <linearGradient id="barGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#ff6b6b"/>
                    <stop offset="100%" style="stop-color:#e63946"/>
                </linearGradient>
            </defs>`;
            
            svg.innerHTML = defs + content;
        }
        
        function renderTopErrors() {
            const list = document.getElementById('topErrorsList');
            
            if (logData.top_errors.length === 0) {
                list.innerHTML = '<li class="no-data">No errors found</li>';
                return;
            }
            
            list.innerHTML = logData.top_errors.map((e, i) => `
                <li>
                    <span style="color:#666;font-weight:bold;min-width:25px;">#${i + 1}</span>
                    <span class="error-msg">${escapeHtml(e.message)}</span>
                    <span class="error-count">${e.count} occurrence${e.count !== 1 ? 's' : ''}</span>
                </li>
            `).join('');
        }
        
        function renderTable() {
            const tbody = document.getElementById('logsTable');
            let logs = logData.all_logs;
            
            if (currentFilter !== 'ALL') {
                logs = logs.filter(l => l.level === currentFilter);
            }
            
            if (searchTerm) {
                const term = searchTerm.toLowerCase();
                logs = logs.filter(l => 
                    l.message.toLowerCase().includes(term) ||
                    l.timestamp.toLowerCase().includes(term) ||
                    l.level.toLowerCase().includes(term)
                );
            }
            
            logs = logs.slice().reverse().slice(0, 500);
            
            if (logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="no-data">No logs match your criteria</td></tr>';
                return;
            }
            
            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td style="white-space:nowrap;color:#888;">${log.timestamp}</td>
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
                renderTable();
            });
        });
        
        document.getElementById('searchBox').addEventListener('input', (e) => {
            searchTerm = e.target.value;
            renderTable();
        });
        
        // Initial load
        fetchData();
    </script>
</body>
</html>
'''


class LogDashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for the log dashboard"""
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode('utf-8'))
        
        elif parsed_path.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            try:
                data = parse_logs()
                self.wfile.write(json.dumps(data).encode('utf-8'))
            except Exception as e:
                error_response = {'error': str(e)}
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
        
        else:
            self.send_error(404, 'Not Found')
    
    def log_message(self, format, *args):
        # Custom logging format
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    # Check for log file, generate if missing
    if not os.path.exists(LOG_FILE):
        print(f"📝 Log file '{LOG_FILE}' not found. Generating fake data...")
        generate_fake_logs(1000)
    else:
        # Count lines in existing file
        with open(LOG_FILE, 'r') as f:
            line_count = sum(1 for _ in f)
        print(f"📂 Using existing log file: {LOG_FILE} ({line_count} entries)")
    
    # Start the server
    try:
        with ReusableTCPServer(("", PORT), LogDashboardHandler) as httpd:
            print(f"\n{'═' * 52}")
            print(f"  🚀 Log Analytics Dashboard is running!")
            print(f"  📊 Open your browser at: http://localhost:{PORT}")
            print(f"{'═' * 52}")
            print(f"\n  Press Ctrl+C to stop the server\n")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n\n👋 Shutting down server...")
    except OSError as e:
        if e.errno == 98 or e.errno == 48:  # Address already in use
            print(f"\n❌ Error: Port {PORT} is already in use.")
            print(f"   Try stopping other services or change the PORT variable.\n")
        else:
            raise


if __name__ == '__main__':
    main()