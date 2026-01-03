#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict

# Generate fake log data
def generate_fake_logs(filename='server.log', num_lines=1000):
    log_levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL']
    log_weights = [60, 25, 12, 3]  # Percentage weights
    
    error_messages = [
        "Database connection timeout",
        "Failed to authenticate user",
        "File not found: config.json",
        "Memory allocation failed",
        "Network request timeout",
        "Invalid API key provided",
        "Service unavailable",
        "Disk space running low",
        "Failed to write to cache",
        "Connection refused by remote server"
    ]
    
    info_messages = [
        "Server started successfully",
        "Request processed",
        "User logged in",
        "Cache cleared",
        "Background job completed",
        "Health check passed"
    ]
    
    warn_messages = [
        "High memory usage detected",
        "Response time exceeding threshold",
        "Retry attempt for failed request",
        "Deprecated API endpoint used",
        "Connection pool nearly exhausted"
    ]
    
    critical_messages = [
        "System crash imminent",
        "Data corruption detected",
        "Security breach attempt",
        "Complete service failure",
        "Unrecoverable error in core module"
    ]
    
    start_time = datetime.now() - timedelta(hours=24)
    
    with open(filename, 'w') as f:
        for i in range(num_lines):
            timestamp = start_time + timedelta(minutes=random.randint(0, 1440))
            level = random.choices(log_levels, weights=log_weights)[0]
            
            if level == 'INFO':
                message = random.choice(info_messages)
            elif level == 'WARN':
                message = random.choice(warn_messages)
            elif level == 'ERROR':
                message = random.choice(error_messages)
            else:  # CRITICAL
                message = random.choice(critical_messages)
            
            log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}\n"
            f.write(log_line)
    
    print(f"✅ Generated {num_lines} log lines in {filename}")

# Parse log file
def parse_logs(filename='server.log'):
    logs = []
    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().split(' ', 2)
            if len(parts) >= 3:
                timestamp_str = parts[0] + ' ' + parts[1]
                level = parts[2].strip('[]').split(']')[0]
                message = parts[2].split(']', 1)[1].strip() if ']' in parts[2] else ''
                
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    logs.append({
                        'timestamp': timestamp,
                        'level': level,
                        'message': message
                    })
                except ValueError:
                    continue
    
    return logs

# Analyze logs
def analyze_logs(logs):
    total = len(logs)
    level_counts = Counter(log['level'] for log in logs)
    
    # Percentage of each level
    level_percentages = {level: (count / total * 100) for level, count in level_counts.items()}
    
    # Errors per hour
    errors_per_hour = defaultdict(int)
    for log in logs:
        if log['level'] in ['ERROR', 'CRITICAL']:
            hour_key = log['timestamp'].strftime('%Y-%m-%d %H:00')
            errors_per_hour[hour_key] += 1
    
    # Most common error messages
    error_messages = [log['message'] for log in logs if log['level'] in ['ERROR', 'CRITICAL']]
    common_errors = Counter(error_messages).most_common(10)
    
    # All critical errors
    critical_logs = [log for log in logs if log['level'] == 'CRITICAL']
    
    return {
        'total_logs': total,
        'level_counts': dict(level_counts),
        'level_percentages': level_percentages,
        'errors_per_hour': dict(sorted(errors_per_hour.items())),
        'common_errors': common_errors,
        'critical_logs': [{
            'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'message': log['message']
        } for log in critical_logs],
        'all_logs': [{
            'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'level': log['level'],
            'message': log['message']
        } for log in logs]
    }

# HTML Dashboard
def get_dashboard_html():
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }
        
        .stat {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .chart-container {
            width: 100%;
            height: 300px;
            overflow-x: auto;
        }
        
        svg {
            display: block;
        }
        
        .error-list {
            list-style: none;
        }
        
        .error-item {
            padding: 10px;
            margin-bottom: 8px;
            background: #f8f9fa;
            border-left: 4px solid #dc3545;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .error-message {
            flex: 1;
            color: #333;
        }
        
        .error-count {
            background: #dc3545;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .filter-controls {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            background: #e9ecef;
            color: #333;
        }
        
        .filter-btn.active {
            background: #667eea;
            color: white;
        }
        
        .search-box {
            width: 100%;
            padding: 10px;
            border: 2px solid #e9ecef;
            border-radius: 6px;
            font-size: 1em;
            margin-bottom: 15px;
        }
        
        .search-box:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .table-container {
            overflow-x: auto;
            max-height: 500px;
            overflow-y: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #e9ecef;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .level-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        .level-INFO { background: #17a2b8; color: white; }
        .level-WARN { background: #ffc107; color: #333; }
        .level-ERROR { background: #dc3545; color: white; }
        .level-CRITICAL { background: #6f42c1; color: white; }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: white;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Log Analytics Dashboard</h1>
        
        <div id="loading" class="loading">Loading analytics...</div>
        
        <div id="content" style="display: none;">
            <div class="dashboard">
                <div class="card">
                    <h2>📈 Log Level Distribution</h2>
                    <div class="stat-grid" id="stats"></div>
                </div>
                
                <div class="card">
                    <h2>📉 Errors Over Time</h2>
                    <div class="chart-container" id="timeline-chart"></div>
                </div>
                
                <div class="card">
                    <h2>🔥 Top Error Messages</h2>
                    <ul class="error-list" id="error-list"></ul>
                </div>
            </div>
            
            <div class="card">
                <h2>🔍 Log Browser</h2>
                <div class="filter-controls">
                    <button class="filter-btn active" data-level="ALL">All Logs</button>
                    <button class="filter-btn" data-level="INFO">INFO</button>
                    <button class="filter-btn" data-level="WARN">WARN</button>
                    <button class="filter-btn" data-level="ERROR">ERROR</button>
                    <button class="filter-btn" data-level="CRITICAL">CRITICAL</button>
                </div>
                <input type="text" class="search-box" id="search-box" placeholder="Search logs...">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Level</th>
                                <th>Message</th>
                            </tr>
                        </thead>
                        <tbody id="log-table"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let analyticsData = null;
        let currentFilter = 'ALL';
        let searchTerm = '';
        
        // Fetch analytics data
        async function loadAnalytics() {
            try {
                const response = await fetch('/api/analytics');
                analyticsData = await response.json();
                renderDashboard();
                document.getElementById('loading').style.display = 'none';
                document.getElementById('content').style.display = 'block';
            } catch (error) {
                console.error('Error loading analytics:', error);
            }
        }
        
        function renderDashboard() {
            renderStats();
            renderTimeline();
            renderTopErrors();
            renderLogTable();
        }
        
        function renderStats() {
            const statsContainer = document.getElementById('stats');
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            
            statsContainer.innerHTML = levels.map(level => {
                const count = analyticsData.level_counts[level] || 0;
                const percentage = analyticsData.level_percentages[level] || 0;
                return `
                    <div class="stat">
                        <div class="stat-label">${level}</div>
                        <div class="stat-value">${percentage.toFixed(1)}%</div>
                        <div class="stat-label">${count} logs</div>
                    </div>
                `;
            }).join('');
        }
        
        function renderTimeline() {
            const container = document.getElementById('timeline-chart');
            const data = analyticsData.errors_per_hour;
            const entries = Object.entries(data);
            
            if (entries.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #999;">No error data available</p>';
                return;
            }
            
            const width = Math.max(600, entries.length * 40);
            const height = 250;
            const padding = { top: 20, right: 20, bottom: 60, left: 50 };
            
            const maxValue = Math.max(...Object.values(data));
            const chartWidth = width - padding.left - padding.right;
            const chartHeight = height - padding.top - padding.bottom;
            
            let svg = `<svg width="${width}" height="${height}" style="min-width: 100%;">`;
            
            // Grid lines
            for (let i = 0; i <= 5; i++) {
                const y = padding.top + (chartHeight / 5) * i;
                const value = Math.round(maxValue * (1 - i / 5));
                svg += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="#e9ecef" stroke-width="1"/>`;
                svg += `<text x="${padding.left - 10}" y="${y + 5}" text-anchor="end" font-size="12" fill="#666">${value}</text>`;
            }
            
            // Bars
            const barWidth = chartWidth / entries.length * 0.8;
            entries.forEach(([hour, count], index) => {
                const x = padding.left + (chartWidth / entries.length) * index + (chartWidth / entries.length - barWidth) / 2;
                const barHeight = (count / maxValue) * chartHeight;
                const y = padding.top + chartHeight - barHeight;
                
                svg += `<rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" fill="#dc3545" opacity="0.8"/>`;
                svg += `<text x="${x + barWidth / 2}" y="${y - 5}" text-anchor="middle" font-size="12" font-weight="bold" fill="#dc3545">${count}</text>`;
            });
            
            // X-axis labels
            entries.forEach(([hour, count], index) => {
                const x = padding.left + (chartWidth / entries.length) * (index + 0.5);
                const label = hour.split(' ')[1].substring(0, 5);
                svg += `<text x="${x}" y="${height - padding.bottom + 20}" text-anchor="middle" font-size="11" fill="#666" transform="rotate(-45 ${x} ${height - padding.bottom + 20})">${label}</text>`;
            });
            
            svg += '</svg>';
            container.innerHTML = svg;
        }
        
        function renderTopErrors() {
            const list = document.getElementById('error-list');
            const errors = analyticsData.common_errors.slice(0, 10);
            
            list.innerHTML = errors.map(([message, count]) => `
                <li class="error-item">
                    <span class="error-message">${message}</span>
                    <span class="error-count">${count}</span>
                </li>
            `).join('');
        }
        
        function renderLogTable() {
            const tbody = document.getElementById('log-table');
            const logs = analyticsData.all_logs.filter(log => {
                const matchesLevel = currentFilter === 'ALL' || log.level === currentFilter;
                const matchesSearch = !searchTerm || 
                    log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    log.timestamp.includes(searchTerm);
                return matchesLevel && matchesSearch;
            });
            
            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td>${log.timestamp}</td>
                    <td><span class="level-badge level-${log.level}">${log.level}</span></td>
                    <td>${log.message}</td>
                </tr>
            `).join('');
        }
        
        // Event listeners
        document.addEventListener('DOMContentLoaded', () => {
            loadAnalytics();
            
            // Filter buttons
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active');
                    currentFilter = e.target.dataset.level;
                    renderLogTable();
                });
            });
            
            // Search box
            document.getElementById('search-box').addEventListener('input', (e) => {
                searchTerm = e.target.value;
                renderLogTable();
            });
        });
    </script>
</body>
</html>
'''

# Custom HTTP Request Handler
class LogAnalyticsHandler(http.server.SimpleHTTPRequestHandler):
    analytics_data = None
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(get_dashboard_html().encode())
        elif self.path == '/api/analytics':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self.analytics_data).encode())
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def main():
    LOG_FILE = 'server.log'
    PORT = 8000
    
    print("\n" + "="*60)
    print("🚀 Log Analytics Dashboard Starting...")
    print("="*60 + "\n")
    
    # Check if log file exists, generate if not
    if not os.path.exists(LOG_FILE):
        print(f"📝 Log file '{LOG_FILE}' not found. Generating fake data...")
        generate_fake_logs(LOG_FILE, 1000)
    else:
        print(f"✅ Found existing log file: {LOG_FILE}")
    
    # Parse and analyze logs
    print("🔍 Parsing logs...")
    logs = parse_logs(LOG_FILE)
    print(f"✅ Parsed {len(logs)} log entries")
    
    print("📊 Analyzing logs...")
    analytics_data = analyze_logs(logs)
    
    # Print summary
    print("\n" + "-"*60)
    print("📈 Log Summary:")
    print(f"   Total Logs: {analytics_data['total_logs']}")
    for level, count in analytics_data['level_counts'].items():
        percentage = analytics_data['level_percentages'][level]
        print(f"   {level}: {count} ({percentage:.1f}%)")
    print(f"   Critical Errors: {len(analytics_data['critical_logs'])}")
    print("-"*60 + "\n")
    
    # Set analytics data on handler class
    LogAnalyticsHandler.analytics_data = analytics_data
    
    # Start server
    with socketserver.TCPServer(("", PORT), LogAnalyticsHandler) as httpd:
        print("="*60)
        print(f"🎉 Dashboard is LIVE!")
        print(f"🌐 Open your browser: http://localhost:{PORT}")
        print("="*60)
        print("\n💡 Press Ctrl+C to stop the server\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n" + "="*60)
            print("🛑 Shutting down server...")
            print("👋 Goodbye!")
            print("="*60 + "\n")

if __name__ == '__main__':
    main()