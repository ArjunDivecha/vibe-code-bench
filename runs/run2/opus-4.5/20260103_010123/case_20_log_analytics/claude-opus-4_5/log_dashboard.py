#!/usr/bin/env python3
"""
Log Analytics Dashboard
A Python script that analyzes log files and serves an interactive dashboard.
Uses only Python standard library.
"""

import os
import json
import random
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
LOG_FILE = "server.log"
PORT = 8080

# Sample messages for fake data generation
ERROR_MESSAGES = [
    "Connection timeout to database server",
    "Failed to authenticate user",
    "Disk space critically low",
    "Memory allocation failed",
    "Network interface unreachable",
    "SSL certificate expired",
    "API rate limit exceeded",
    "Invalid configuration detected",
    "Service dependency unavailable",
    "Queue overflow detected",
]

WARN_MESSAGES = [
    "High memory usage detected",
    "Slow query execution",
    "Cache miss rate increasing",
    "Connection pool nearly exhausted",
    "Deprecated API endpoint called",
]

INFO_MESSAGES = [
    "Server started successfully",
    "User logged in",
    "Request processed",
    "Cache refreshed",
    "Scheduled task completed",
    "Configuration reloaded",
    "Health check passed",
]

CRITICAL_MESSAGES = [
    "System crash imminent",
    "Data corruption detected",
    "Security breach attempt",
    "Primary database offline",
    "Cluster node failure",
]


def generate_fake_logs(filename, num_lines=1000):
    """Generate fake log data with realistic patterns."""
    levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    weights = [60, 25, 12, 3]
    
    base_time = datetime.now() - timedelta(hours=48)
    
    with open(filename, 'w') as f:
        for i in range(num_lines):
            base_time += timedelta(seconds=random.randint(30, 300))
            timestamp = base_time.strftime("%Y-%m-%d %H:%M:%S")
            
            level = random.choices(levels, weights=weights)[0]
            
            if level == "INFO":
                message = random.choice(INFO_MESSAGES)
            elif level == "WARN":
                message = random.choice(WARN_MESSAGES)
            elif level == "ERROR":
                message = random.choice(ERROR_MESSAGES)
            else:
                message = random.choice(CRITICAL_MESSAGES)
            
            f.write(f"{timestamp} [{level}] {message}\n")
    
    print(f"Generated {num_lines} log entries in {filename}")


def parse_logs(filename):
    """Parse log file and extract analytics data."""
    log_pattern = re.compile(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (.+)'
    )
    
    level_counts = Counter()
    errors_per_hour = defaultdict(int)
    error_messages = Counter()
    critical_entries = []
    all_entries = []
    
    with open(filename, 'r') as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                level_counts[level] += 1
                
                entry = {
                    "timestamp": timestamp_str,
                    "level": level,
                    "message": message
                }
                all_entries.append(entry)
                
                if level in ("ERROR", "CRITICAL"):
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    errors_per_hour[hour_key] += 1
                    error_messages[message] += 1
                
                if level == "CRITICAL":
                    critical_entries.append(entry)
    
    total = sum(level_counts.values())
    level_percentages = {
        level: round((count / total) * 100, 2) if total > 0 else 0
        for level, count in level_counts.items()
    }
    
    sorted_errors_per_hour = sorted(errors_per_hour.items())
    top_errors = error_messages.most_common(10)
    
    return {
        "level_percentages": level_percentages,
        "level_counts": dict(level_counts),
        "errors_per_hour": sorted_errors_per_hour,
        "top_errors": top_errors,
        "critical_entries": critical_entries,
        "all_entries": all_entries,
        "total_entries": total
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
            min-height: 100vh;
            color: #e0e0e0;
        }
        
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 30px;
        }
        
        header h1 {
            font-size: 2.5rem;
            color: #00d4ff;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
        }
        
        header p { color: #888; margin-top: 10px; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
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
            font-size: 0.85rem;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-card .value {
            font-size: 2.2rem;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .stat-card .percent { font-size: 0.9rem; color: #666; }
        
        .stat-card.info .value { color: #4caf50; }
        .stat-card.warn .value { color: #ff9800; }
        .stat-card.error .value { color: #f44336; }
        .stat-card.critical .value { color: #e91e63; }
        .stat-card.total .value { color: #00d4ff; }
        
        .charts-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .chart-card h2 {
            font-size: 1.2rem;
            margin-bottom: 20px;
            color: #00d4ff;
        }
        
        .chart-container { width: 100%; height: 300px; position: relative; }
        .chart-container svg { width: 100%; height: 100%; }
        
        .pie-chart-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .legend {
            margin-top: 20px;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }
        
        .top-errors-list { list-style: none; }
        
        .top-errors-list li {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .top-errors-list li:last-child { border-bottom: none; }
        
        .error-message {
            flex: 1;
            color: #f44336;
            font-size: 0.9rem;
            margin-right: 15px;
        }
        
        .error-count {
            background: rgba(244, 67, 54, 0.2);
            color: #f44336;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            white-space: nowrap;
        }
        
        .table-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 30px;
        }
        
        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .table-header h2 { font-size: 1.2rem; color: #00d4ff; }
        
        .controls { display: flex; gap: 15px; flex-wrap: wrap; }
        
        .search-box {
            padding: 10px 15px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
            font-size: 0.9rem;
            min-width: 250px;
        }
        
        .search-box:focus { outline: none; border-color: #00d4ff; }
        .search-box::placeholder { color: #666; }
        
        .filter-buttons { display: flex; gap: 5px; }
        
        .filter-btn {
            padding: 10px 20px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(0, 0, 0, 0.3);
            color: #888;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9rem;
        }
        
        .filter-btn:hover { background: rgba(255, 255, 255, 0.1); }
        
        .filter-btn.active {
            background: #00d4ff;
            color: #000;
            border-color: #00d4ff;
        }
        
        .table-wrapper {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .table-wrapper::-webkit-scrollbar { width: 8px; }
        .table-wrapper::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.2); border-radius: 4px; }
        .table-wrapper::-webkit-scrollbar-thumb { background: #00d4ff; border-radius: 4px; }
        
        .log-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        
        .log-table th {
            text-align: left;
            padding: 15px;
            background: rgba(0, 0, 0, 0.3);
            color: #00d4ff;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 0.8rem;
            position: sticky;
            top: 0;
        }
        
        .log-table td {
            padding: 12px 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .log-table tr:hover { background: rgba(255, 255, 255, 0.05); }
        
        .level-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: bold;
            text-transform: uppercase;
            display: inline-block;
        }
        
        .level-badge.INFO { background: rgba(76, 175, 80, 0.2); color: #4caf50; }
        .level-badge.WARN { background: rgba(255, 152, 0, 0.2); color: #ff9800; }
        .level-badge.ERROR { background: rgba(244, 67, 54, 0.2); color: #f44336; }
        .level-badge.CRITICAL { background: rgba(233, 30, 99, 0.2); color: #e91e63; }
        
        .no-results { text-align: center; padding: 40px; color: #666; }
        
        .results-count { color: #666; font-size: 0.9rem; margin-bottom: 10px; }
        
        @media (max-width: 768px) {
            .charts-section { grid-template-columns: 1fr; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .table-header { flex-direction: column; align-items: stretch; }
            .search-box { min-width: unset; width: 100%; }
            .filter-buttons { justify-content: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Log Analytics Dashboard</h1>
            <p id="summary">Loading...</p>
        </header>
        
        <div class="stats-grid" id="statsGrid"></div>
        
        <div class="charts-section">
            <div class="chart-card">
                <h2>📈 Log Level Distribution</h2>
                <div class="chart-container pie-chart-container">
                    <svg id="pieChart" viewBox="0 0 300 300"></svg>
                </div>
                <div class="legend" id="pieLegend"></div>
            </div>
            
            <div class="chart-card">
                <h2>📉 Errors Per Hour</h2>
                <div class="chart-container">
                    <svg id="lineChart" viewBox="0 0 500 300"></svg>
                </div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-card" style="grid-column: 1 / -1;">
                <h2>🔥 Top Error Messages</h2>
                <ul class="top-errors-list" id="topErrorsList"></ul>
            </div>
        </div>
        
        <div class="table-section">
            <div class="table-header">
                <h2>🚨 Log Entries</h2>
                <div class="controls">
                    <input type="text" class="search-box" id="searchBox" placeholder="Search logs...">
                    <div class="filter-buttons">
                        <button class="filter-btn active" data-level="ALL">All</button>
                        <button class="filter-btn" data-level="ERROR">Error</button>
                        <button class="filter-btn" data-level="CRITICAL">Critical</button>
                    </div>
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
                const response = await fetch('/api/data');
                logData = await response.json();
                renderDashboard();
            } catch (error) {
                console.error('Failed to fetch data:', error);
                document.getElementById('summary').textContent = 'Error loading data';
            }
        }
        
        function renderDashboard() {
            if (!logData) return;
            
            document.getElementById('summary').textContent = 
                `Analyzing ${logData.total_entries.toLocaleString()} log entries`;
            
            renderStats();
            renderPieChart();
            renderLineChart();
            renderTopErrors();
            renderTable();
        }
        
        function renderStats() {
            const statsGrid = document.getElementById('statsGrid');
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const colors = { INFO: 'info', WARN: 'warn', ERROR: 'error', CRITICAL: 'critical' };
            
            let html = `
                <div class="stat-card total">
                    <h3>Total Entries</h3>
                    <div class="value">${logData.total_entries.toLocaleString()}</div>
                </div>
            `;
            
            levels.forEach(level => {
                const count = logData.level_counts[level] || 0;
                const percentage = logData.level_percentages[level] || 0;
                html += `
                    <div class="stat-card ${colors[level]}">
                        <h3>${level}</h3>
                        <div class="value">${count.toLocaleString()}</div>
                        <div class="percent">${percentage}%</div>
                    </div>
                `;
            });
            
            statsGrid.innerHTML = html;
        }
        
        function renderPieChart() {
            const svg = document.getElementById('pieChart');
            const legend = document.getElementById('pieLegend');
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const colors = ['#4caf50', '#ff9800', '#f44336', '#e91e63'];
            
            const centerX = 150, centerY = 150, radius = 100;
            let startAngle = 0;
            let paths = '';
            let legendHtml = '';
            
            levels.forEach((level, index) => {
                const percentage = logData.level_percentages[level] || 0;
                const angle = (percentage / 100) * 360;
                const endAngle = startAngle + angle;
                
                if (percentage > 0) {
                    const startRad = (startAngle - 90) * Math.PI / 180;
                    const endRad = (endAngle - 90) * Math.PI / 180;
                    
                    const x1 = centerX + radius * Math.cos(startRad);
                    const y1 = centerY + radius * Math.sin(startRad);
                    const x2 = centerX + radius * Math.cos(endRad);
                    const y2 = centerY + radius * Math.sin(endRad);
                    
                    const largeArc = angle > 180 ? 1 : 0;
                    
                    paths += `
                        <path d="M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z"
                              fill="${colors[index]}" opacity="0.8" stroke="#1a1a2e" stroke-width="2"
                              style="cursor: pointer;">
                            <title>${level}: ${percentage}% (${logData.level_counts[level] || 0})</title>
                        </path>
                    `;
                }
                
                legendHtml += `
                    <div class="legend-item">
                        <div class="legend-color" style="background: ${colors[index]}"></div>
                        <span>${level}: ${percentage}%</span>
                    </div>
                `;
                
                startAngle = endAngle;
            });
            
            svg.innerHTML = paths;
            legend.innerHTML = legendHtml;
        }
        
        function renderLineChart() {
            const svg = document.getElementById('lineChart');
            const data = logData.errors_per_hour;
            
            if (data.length === 0) {
                svg.innerHTML = '<text x="250" y="150" text-anchor="middle" fill="#666">No error data available</text>';
                return;
            }
            
            const padding = { top: 30, right: 30, bottom: 60, left: 50 };
            const width = 500 - padding.left - padding.right;
            const height = 300 - padding.top - padding.bottom;
            
            const maxValue = Math.max(...data.map(d => d[1])) || 1;
            const xStep = data.length > 1 ? width / (data.length - 1) : width / 2;
            
            let pathD = '';
            let areaD = '';
            let dots = '';
            
            data.forEach((point, index) => {
                const x = padding.left + (data.length > 1 ? index * xStep : width / 2);
                const y = padding.top + height - (point[1] / maxValue) * height;
                
                if (index === 0) {
                    pathD += `M ${x} ${y}`;
                    areaD += `M ${x} ${padding.top + height} L ${x} ${y}`;
                } else {
                    pathD += ` L ${x} ${y}`;
                    areaD += ` L ${x} ${y}`;
                }
                
                dots += `<circle cx="${x}" cy="${y}" r="5" fill="#f44336" style="cursor: pointer;">
                    <title>${point[0]}\\n${point[1]} errors</title>
                </circle>`;
            });
            
            const lastX = padding.left + (data.length > 1 ? (data.length - 1) * xStep : width / 2);
            areaD += ` L ${lastX} ${padding.top + height} Z`;
            
            let yLabels = '';
            for (let i = 0; i <= 5; i++) {
                const y = padding.top + (height / 5) * i;
                const value = Math.round(maxValue - (maxValue / 5) * i);
                yLabels += `
                    <text x="${padding.left - 10}" y="${y + 4}" text-anchor="end" fill="#666" font-size="11">${value}</text>
                    <line x1="${padding.left}" y1="${y}" x2="${padding.left + width}" y2="${y}" stroke="#333" stroke-dasharray="2"/>
                `;
            }
            
            let xLabels = '';
            const step = Math.max(1, Math.ceil(data.length / 6));
            data.forEach((point, index) => {
                if (index % step === 0 || index === data.length - 1) {
                    const x = padding.left + (data.length > 1 ? index * xStep : width / 2);
                    const label = point[0].split(' ')[1] || point[0];
                    xLabels += `
                        <text x="${x}" y="${padding.top + height + 20}" text-anchor="end" fill="#666" font-size="10" 
                              transform="rotate(-45, ${x}, ${padding.top + height + 20})">${label}</text>
                    `;
                }
            });
            
            svg.innerHTML = `
                <defs>
                    <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#f44336;stop-opacity:0.4"/>
                        <stop offset="100%" style="stop-color:#f44336;stop-opacity:0.05"/>
                    </linearGradient>
                </defs>
                ${yLabels}
                ${xLabels}
                <path d="${areaD}" fill="url(#areaGradient)"/>
                <path d="${pathD}" fill="none" stroke="#f44336" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                ${dots}
            `;
        }
        
        function renderTopErrors() {
            const list = document.getElementById('topErrorsList');
            
            if (logData.top_errors.length === 0) {
                list.innerHTML = '<li class="no-results">No errors found</li>';
                return;
            }
            
            list.innerHTML = logData.top_errors.map(([message, count]) => `
                <li>
                    <span class="error-message">${escapeHtml(message)}</span>
                    <span class="error-count">${count} occurrences</span>
                </li>
            `).join('');
        }
        
        function renderTable() {
            const tbody = document.getElementById('logTableBody');
            const resultsCount = document.getElementById('resultsCount');
            
            let entries = logData.all_entries;
            
            if (currentFilter !== 'ALL') {
                entries = entries.filter(e => e.level === currentFilter);
            }
            
            if (searchTerm) {
                const term = searchTerm.toLowerCase();
                entries = entries.filter(e => 
                    e.message.toLowerCase().includes(term) ||
                    e.timestamp.toLowerCase().includes(term) ||
                    e.level.toLowerCase().includes(term)
                );
            }
            
            resultsCount.textContent = `Showing ${Math.min(entries.length, 200)} of ${entries.length} entries`;
            
            if (entries.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="no-results">No matching entries found</td></tr>';
                return;
            }
            
            const displayEntries = entries.slice().reverse().slice(0, 200);
            
            tbody.innerHTML = displayEntries.map(entry => `
                <tr>
                    <td>${escapeHtml(entry.timestamp)}</td>
                    <td><span class="level-badge ${entry.level}">${entry.level}</span></td>
                    <td>${escapeHtml(entry.message)}</td>
                </tr>
            `).join('');
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        document.getElementById('searchBox').addEventListener('input', (e) => {
            searchTerm = e.target.value;
            renderTable();
        });
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.level;
                renderTable();
            });
        });
        
        fetchData();
    </script>
</body>
</html>
'''


class LogDashboardHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler for the log dashboard."""
    
    log_data = None
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode('utf-8'))
        elif self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(json.dumps(self.log_data).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        pass  # Suppress default logging


def run_server(port, log_data):
    """Run the HTTP server."""
    LogDashboardHandler.log_data = log_data
    
    server = HTTPServer(('127.0.0.1', port), LogDashboardHandler)
    
    print(f"\n{'='*55}")
    print(f"  🚀 Log Analytics Dashboard is running!")
    print(f"  📊 Open your browser: http://127.0.0.1:{port}")
    print(f"{'='*55}")
    print(f"\n  Press Ctrl+C to stop the server\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n  Server stopped gracefully.")
        server.shutdown()


def main():
    print("\n📋 Log Analytics Dashboard")
    print("-" * 40)
    
    # Check if log file exists, generate if not
    if not os.path.exists(LOG_FILE):
        print(f"⚠️  Log file '{LOG_FILE}' not found.")
        print("📝 Generating fake log data...")
        generate_fake_logs(LOG_FILE)
    else:
        print(f"✅ Found existing log file: {LOG_FILE}")
    
    # Parse logs
    print("🔍 Parsing log file...")
    log_data = parse_logs(LOG_FILE)
    
    print(f"📊 Parsed {log_data['total_entries']} log entries")
    print(f"   - INFO: {log_data['level_counts'].get('INFO', 0)}")
    print(f"   - WARN: {log_data['level_counts'].get('WARN', 0)}")
    print(f"   - ERROR: {log_data['level_counts'].get('ERROR', 0)}")
    print(f"   - CRITICAL: {log_data['level_counts'].get('CRITICAL', 0)}")
    
    # Start server
    run_server(PORT, log_data)


if __name__ == '__main__':
    main()