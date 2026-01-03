#!/usr/bin/env python3
"""
Log Analytics Dashboard
A self-contained log analysis tool with an interactive web dashboard.
"""

import http.server
import socketserver
import json
import os
import random
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from urllib.parse import urlparse, parse_qs

PORT = 8000
LOG_FILE = "server.log"

# Fake log data templates
LOG_TEMPLATES = {
    "INFO": [
        "User {user} logged in successfully",
        "Database connection established",
        "Cache cleared for user {user}",
        "Session started for {user}",
        "API request processed in {ms}ms",
        "File uploaded: {file}",
        "Backup completed successfully",
        "Service health check passed",
        "Configuration reloaded",
        "Cache warming completed"
    ],
    "WARN": [
        "High memory usage detected: {percent}%",
        "Slow query detected: {ms}ms",
        "Rate limit approaching for {user}",
        "Disk space low: {percent}% free",
        "Connection pool near capacity",
        "Deprecated API endpoint accessed",
        "Retry attempt {attempt} for {user}",
        "Token expiring soon for {user}"
    ],
    "ERROR": [
        "Failed to connect to database: {error}",
        "Authentication failed for {user}",
        "Timeout waiting for {service}",
        "Invalid request from {ip}: {error}",
        "Failed to process payment for {user}: {error}",
        "External API error: {error}",
        "File not found: {file}",
        "Permission denied for {user}",
        "Serialization error: {error}",
        "Connection refused: {host}:{port}"
    ],
    "CRITICAL": [
        "System out of memory - OOM killer activated",
        "Database cluster failover initiated",
        "Primary server unreachable",
        "Disk failure predicted on {disk}",
        "Security breach detected from {ip}",
        "Service mesh failure - cascading errors",
        "SSL certificate expired",
        "Data corruption detected in {table}",
        "Kernel panic on server {server}",
        "Backup failure - critical data at risk"
    ]
}

USERS = ["alice", "bob", "charlie", "david", "eve", "frank", "grace", "henry"]
FILES = ["config.json", "data.csv", "image.png", "document.pdf", "backup.zip"]
IPS = ["192.168.1.100", "10.0.0.50", "172.16.0.25", "8.8.8.8", "203.0.113.50"]
SERVICES = ["auth-service", "payment-gateway", "email-service", "cache-layer"]
HOSTS = ["db-primary", "cache-server", "api-gateway"]
DISKS = ["/dev/sda", "/dev/sdb", "/dev/nvme0n1"]
TABLES = ["users", "orders", "transactions", "sessions"]
SERVERS = ["web-01", "web-02", "app-01"]


def generate_fake_logs(filename, num_lines=1000):
    """Generate fake log data with realistic patterns."""
    logs = []
    start_time = datetime.now() - timedelta(days=7)
    
    for i in range(num_lines):
        # Weighted random for more realistic distribution
        weights = [0.5, 0.3, 0.15, 0.05]  # INFO, WARN, ERROR, CRITICAL
        level = random.choices(["INFO", "WARN", "ERROR", "CRITICAL"], weights=weights)[0]
        
        # Time distribution - more errors during business hours
        hour_offset = random.gauss(84, 48)  # Spread over ~7 days
        timestamp = start_time + timedelta(hours=hour_offset)
        
        # Adjust error probability based on hour (more errors during peak hours)
        hour = timestamp.hour
        if 9 <= hour <= 17:
            level = random.choices(["INFO", "WARN", "ERROR", "CRITICAL"], weights=[0.4, 0.35, 0.2, 0.05])[0]
        
        # Get template and fill placeholders
        template = random.choice(LOG_TEMPLATES[level])
        log_entry = template.format(
            user=random.choice(USERS),
            file=random.choice(FILES),
            ip=random.choice(IPS),
            ms=random.randint(1, 5000),
            percent=random.randint(5, 95),
            error=random.choice(["Connection refused", "Timeout", "Authentication error", "Permission denied", "Invalid data"]),
            service=random.choice(SERVICES),
            host=random.choice(HOSTS),
            port=random.randint(1, 65535),
            disk=random.choice(DISKS),
            table=random.choice(TABLES),
            server=random.choice(SERVERS),
            attempt=random.randint(1, 5)
        )
        
        ts_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        logs.append("[" + ts_str + "] [" + level + "] " + log_entry)
    
    # Sort by timestamp
    logs.sort(key=lambda x: datetime.strptime(x.split("]")[0].lstrip("["), "%Y-%m-%d %H:%M:%S"))
    
    with open(filename, 'w') as f:
        f.write('\n'.join(logs))
    
    print("Generated " + str(num_lines) + " log entries in " + filename)


def parse_log_file(filename):
    """Parse log file and extract statistics."""
    log_pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\] (.+)')
    
    levels = []
    errors_by_hour = defaultdict(list)
    error_messages = []
    all_logs = []
    critical_logs = []
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            match = log_pattern.match(line)
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                log_entry = {
                    "timestamp": timestamp_str,
                    "level": level,
                    "message": message
                }
                
                all_logs.append(log_entry)
                levels.append(level)
                
                if level in ["ERROR", "CRITICAL"]:
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    errors_by_hour[hour_key].append(log_entry)
                    
                    if level == "CRITICAL":
                        critical_logs.append(log_entry)
                
                if level == "ERROR":
                    # Extract base error type
                    base_error = message.split(":")[0] if ":" in message else message
                    error_messages.append(base_error)
    
    return {
        "level_counts": dict(Counter(levels)),
        "errors_by_hour": dict(errors_by_hour),
        "common_errors": Counter(error_messages).most_common(10),
        "all_logs": all_logs,
        "critical_logs": critical_logs
    }


def calculate_percentages(level_counts):
    """Calculate percentage distribution of log levels."""
    total = sum(level_counts.values())
    return {level: (count / total * 100, count) for level, count in level_counts.items()}


def prepare_chart_data(stats):
    """Prepare data for SVG charts."""
    # Pie chart data
    percentages = calculate_percentages(stats["level_counts"])
    
    # Timeline data - errors per hour
    sorted_hours = sorted(stats["errors_by_hour"].keys())
    timeline_data = [(hour, len(errors)) for hour, errors in stats["errors_by_hour"].items()]
    
    return {
        "percentages": percentages,
        "timeline": timeline_data,
        "common_errors": stats["common_errors"]
    }


def generate_pie_svg(percentages):
    """Generate SVG pie chart segments."""
    if not percentages:
        return '<circle cx="100" cy="100" r="80" fill="#333"/>'
    
    colors = {"INFO": "#4CAF50", "WARN": "#FF9800", "ERROR": "#F44336", "CRITICAL": "#9C27B0"}
    
    total = sum(pct for pct, _ in percentages.values())
    if total == 0:
        return '<circle cx="100" cy="100" r="80" fill="#333"/>'
    
    segments = []
    start_angle = -90  # Start from top
    
    for level in ["INFO", "WARN", "ERROR", "CRITICAL"]:
        if level not in percentages:
            continue
            
        pct, count = percentages[level]
        angle = (pct / 100) * 360
        
        if angle == 0:
            continue
            
        end_angle = start_angle + angle
        
        r = 80
        cx, cy = 100, 100
        
        # Handle large angles
        if angle >= 180:
            segments.append('<path d="M ' + str(cx) + ',' + str(cy) + ' L ' + str(cx) + ',' + str(cy-r) + ' A ' + str(r) + ',' + str(r) + ' 0 1,1 ' + str(cx) + ',' + str(cy+r) + ' Z" fill="' + colors[level] + '" />')
        else:
            # Simplified arc for visualization
            segments.append('<circle cx="' + str(cx) + '" cy="' + str(cy) + '" r="' + str(r/2) + '" fill="' + colors[level] + '" opacity="0.8"/>')
            segments.append('<circle cx="' + str(cx) + '" cy="' + str(cy) + '" r="' + str(r) + '" fill="none" stroke="' + colors[level] + '" stroke-width="' + str(r/2) + '" stroke-dasharray="' + str(pct/100 * 2 * 3.14159 * r) + ' ' + str(2 * 3.14159 * r) + '" transform="rotate(' + str(start_angle + 90) + ', ' + str(cx) + ', ' + str(cy) + ')"/>')
        
        start_angle = end_angle
    
    return '<circle cx="100" cy="100" r="40" fill="#16213e"/>' + ''.join(segments)


def generate_dashboard_html(stats, chart_data):
    """Generate the complete HTML dashboard."""
    percentages = chart_data["percentages"]
    timeline = chart_data["timeline"]
    common_errors = chart_data["common_errors"]
    critical_logs = stats["critical_logs"]
    
    # Calculate total logs for summary
    total_logs = sum(stats['level_counts'].values())
    
    # Find max errors for timeline scaling
    max_errors = max((count for _, count in timeline), default=1)
    
    # Generate timeline SVG
    timeline_svg = ""
    if timeline:
        hours = len(timeline)
        bar_width = max(10, (500 - 100) // max(10, hours))
        max_height = 150
        
        for i, (hour, count) in enumerate(sorted(timeline)):
            bar_height = (count / max_errors) * max_height
            x = 50 + i * (bar_width + 2)
            y = 200 - bar_height
            timeline_svg = timeline_svg + '<rect x="' + str(x) + '" y="' + str(y) + '" width="' + str(bar_width) + '" height="' + str(bar_height) + '" fill="#F44336" rx="2"><title>' + hour + ': ' + str(count) + ' errors</title></rect>'
            if hours <= 20:
                label_x = x + bar_width / 2
                label_hour = hour.split()[-1]
                timeline_svg = timeline_svg + '<text x="' + str(label_x) + '" y="220" font-size="8" text-anchor="middle" transform="rotate(45, ' + str(label_x) + ', 220)">' + label_hour + '</text>'
    
    # Generate legend HTML
    legend_html = ""
    for level, (pct, count) in sorted(percentages.items(), key=lambda x: -x[1][0]):
        colors = {"INFO": "#4CAF50", "WARN": "#FF9800", "ERROR": "#F44336", "CRITICAL": "#9C27B0"}
        legend_html = legend_html + '''
        <div class="legend-item">
            <span class="legend-color" style="background: ''' + colors.get(level, "#888") + '''"></span>
            <span class="legend-label">''' + level + '''</span>
            <span class="legend-value">''' + ("%.1f" % pct) + '% (' + str(count) + ''')</span>
        </div>
        '''
    
    # Generate common errors list
    errors_html = ""
    for error, count in common_errors[:10]:
        errors_html = errors_html + '<div class="error-item"><span class="error-count">' + str(count) + '</span><span class="error-msg">' + error + '</span></div>'
    
    # Generate critical logs table
    critical_rows = ""
    for log in critical_logs[:100]:  # Limit for performance
        critical_rows = critical_rows + '''
        <tr data-level="''' + log["level"] + '''">
            <td class="timestamp">''' + log["timestamp"] + '''</td>
            <td><span class="badge badge-critical">''' + log["level"] + '''</span></td>
            <td class="message">''' + log["message"] + '''</td>
        </tr>
        '''
    
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log Analytics Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #eee; min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header { text-align: center; padding: 30px 0; border-bottom: 1px solid #333; margin-bottom: 30px; }
        h1 { font-size: 2.5rem; margin-bottom: 10px; background: linear-gradient(90deg, #4CAF50, #2196F3); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { color: #888; font-size: 1.1rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: #16213e; border-radius: 12px; padding: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
        .card h2 { font-size: 1.2rem; margin-bottom: 20px; color: #aaa; border-bottom: 1px solid #333; padding-bottom: 10px; }
        
        /* Pie Chart */
        .pie-container { display: flex; align-items: center; gap: 30px; flex-wrap: wrap; }
        .pie-chart { position: relative; width: 200px; height: 200px; }
        .pie-chart svg { width: 100%; height: 100%; transform: rotate(-90deg); }
        .legend { flex: 1; min-width: 200px; }
        .legend-item { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #2a2a4a; }
        .legend-color { width: 16px; height: 16px; border-radius: 4px; }
        .legend-label { flex: 1; font-weight: 500; }
        .legend-value { color: #888; font-size: 0.9rem; }
        
        /* Timeline */
        .timeline-chart { width: 100%; overflow-x: auto; }
        .timeline-chart svg { min-width: 600px; }
        .axis-line { stroke: #444; stroke-width: 1; }
        .axis-label { fill: #888; font-size: 10px; }
        
        /* Errors List */
        .error-list { max-height: 300px; overflow-y: auto; }
        .error-item { display: flex; align-items: center; gap: 15px; padding: 10px; border-bottom: 1px solid #2a2a4a; }
        .error-count { background: #F44336; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
        .error-msg { color: #ccc; font-size: 0.9rem; }
        
        /* Filter Controls */
        .filter-controls { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; align-items: center; }
        .filter-btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.95rem; transition: all 0.2s; background: #2a2a4a; color: #aaa; }
        .filter-btn:hover { background: #3a3a5a; }
        .filter-btn.active { background: #4CAF50; color: white; }
        .search-input { padding: 10px 15px; border: 1px solid #333; border-radius: 6px; background: #2a2a4a; color: white; font-size: 0.95rem; width: 300px; max-width: 100%; }
        .search-input:focus { outline: none; border-color: #4CAF50; }
        
        /* Table */
        .table-container { max-height: 500px; overflow-y: auto; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #2a2a4a; }
        th { position: sticky; top: 0; background: #16213e; color: #888; font-weight: 500; font-size: 0.85rem; text-transform: uppercase; }
        tr:hover { background: #1f2f50; }
        .timestamp { color: #888; font-family: monospace; font-size: 0.9rem; }
        .badge { padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
        .badge-critical { background: #9C27B0; color: white; }
        .badge-error { background: #F44336; color: white; }
        .badge-warn { background: #FF9800; color: black; }
        .badge-info { background: #4CAF50; color: white; }
        .message { max-width: 500px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        /* Stats Summary */
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, #16213e, #1f2f50); padding: 20px; border-radius: 10px; text-align: center; }
        .stat-value { font-size: 2rem; font-weight: bold; color: #4CAF50; }
        .stat-label { color: #888; font-size: 0.9rem; margin-top: 5px; }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #1a1a2e; }
        ::-webkit-scrollbar-thumb { background: #444; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #555; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Log Analytics Dashboard</h1>
            <p class="subtitle">Real-time log analysis and visualization</p>
        </header>
        
        <div class="summary-grid">
            <div class="stat-card">
                <div class="stat-value">''' + str(total_logs) + '''</div>
                <div class="stat-label">Total Logs</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #F44336;">''' + str(percentages.get('ERROR', (0,0))[1]) + '''</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #9C27B0;">''' + str(percentages.get('CRITICAL', (0,0))[1]) + '''</div>
                <div class="stat-label">Critical</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #FF9800;">''' + str(percentages.get('WARN', (0,0))[1]) + '''</div>
                <div class="stat-label">Warnings</div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="card">
                <h2>Log Level Distribution</h2>
                <div class="pie-container">
                    <div class="pie-chart">
                        <svg viewBox="0 0 200 200">
                            ''' + generate_pie_svg(percentages) + '''
                        </svg>
                    </div>
                    <div class="legend">
                        ''' + legend_html + '''
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Errors Timeline (Last 7 Days)</h2>
                <div class="timeline-chart">
                    <svg viewBox="0 0 600 250" width="100%" height="250">
                        <line x1="50" y1="200" x2="580" y2="200" class="axis-line"/>
                        <line x1="50" y1="50" x2="50" y2="200" class="axis-line"/>
                        ''' + timeline_svg + '''
                    </svg>
                </div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="card">
                <h2>Most Common Error Messages</h2>
                <div class="error-list">
                    ''' + (errors_html if errors_html else '<p style="color: #888; padding: 20px;">No errors recorded</p>') + '''
                </div>
            </div>
            
            <div class="card" style="flex: 1.5;">
                <h2>Critical Errors Log</h2>
                <div class="filter-controls">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="ERROR">Errors</button>
                    <button class="filter-btn" data-filter="CRITICAL">Critical</button>
                    <input type="text" class="search-input" id="searchInput" placeholder="Search messages...">
                </div>
                <div class="table-container">
                    <table id="logTable">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Level</th>
                                <th>Message</th>
                            </tr>
                        </thead>
                        <tbody id="logTableBody">
                            ''' + (critical_rows if critical_rows else '<tr><td colspan="3" style="text-align: center; color: #888;">No critical errors found</td></tr>') + '''
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Filter functionality
        const filterBtns = document.querySelectorAll('.filter-btn');
        const searchInput = document.getElementById('searchInput');
        const logTableBody = document.getElementById('logTableBody');
        const rows = logTableBody.querySelectorAll('tr');
        
        let currentFilter = 'all';
        
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                applyFilters();
            });
        });
        
        searchInput.addEventListener('input', applyFilters);
        
        function applyFilters() {
            const searchTerm = searchInput.value.toLowerCase();
            
            rows.forEach(row => {
                const level = row.dataset.level;
                const message = row.querySelector('.message').textContent.toLowerCase();
                const matchesFilter = currentFilter === 'all' || level === currentFilter;
                const matchesSearch = searchTerm === '' || message.includes(searchTerm);
                
                row.style.display = (matchesFilter && matchesSearch) ? '' : 'none';
            });
        }
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    // Update critical logs table
                    let html = '';
                    data.critical_logs.forEach(log => {
                        html += '<tr data-level="' + log.level + '">' +
                            '<td class="timestamp">' + log.timestamp + '</td>' +
                            '<td><span class="badge badge-critical">' + log.level + '</span></td>' +
                            '<td class="message">' + log.message + '</td>' +
                            '</tr>';
                    });
                    logTableBody.innerHTML = html || '<tr><td colspan="3" style="text-align: center; color: #888;">No critical errors found</td></tr>';
                    applyFilters();
                })
                .catch(() => {});
        }, 30000);
    </script>
</body>
</html>'''
    return html


class LogDashboardHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for the dashboard."""
    
    def __init__(self, *args, **kwargs):
        self.stats = kwargs.pop('stats')
        self.chart_data = kwargs.pop('chart_data')
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = generate_dashboard_html(self.stats, self.chart_data)
            self.wfile.write(html.encode())
        elif parsed.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            data = {
                'critical_logs': self.stats['critical_logs'],
                'level_counts': self.stats['level_counts'],
                'common_errors': self.stats['common_errors']
            }
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Custom log format."""
        print("[" + datetime.now().strftime('%H:%M:%S') + "] " + args[0])


class ReusableTCPServer(socketserver.TCPServer):
    """TCP Server with address reuse enabled."""
    allow_reuse_address = True


def main():
    """Main entry point."""
    print("=" * 50)
    print("  Log Analytics Dashboard")
    print("=" * 50)
    
    # Check for or generate log file
    if not os.path.exists(LOG_FILE):
        print("\n" + LOG_FILE + " not found. Generating fake log data...")
        generate_fake_logs(LOG_FILE, 1000)
    else:
        print("\nFound existing " + LOG_FILE)
    
    # Parse log file
    print("Parsing log file...")
    stats = parse_log_file(LOG_FILE)
    chart_data = prepare_chart_data(stats)
    
    # Print summary
    print("\nLog Statistics:")
    total = sum(stats['level_counts'].values())
    for level, count in sorted(stats['level_counts'].items()):
        pct = count / total * 100
        print("   " + level.ljust(10) + ": " + str(count).rjust(5) + " (" + ("%.1f" % pct).rjust(5) + "%)")
    
    print("\nErrors by hour: " + str(len(chart_data['timeline'])) + " time periods")
    if chart_data['common_errors']:
        print("Most common error: " + str(chart_data['common_errors'][0]))
    else:
        print("Most common error: N/A")
    print("Critical entries: " + str(len(stats['critical_logs'])))
    
    # Start HTTP server
    print("\nStarting dashboard server...")
    print("   URL: http://localhost:" + str(PORT))
    print("   Press Ctrl+C to stop")
    print("=" * 50)
    
    handler = lambda *args, **kwargs: LogDashboardHandler(*args, stats=stats, chart_data=chart_data, **kwargs)
    
    with ReusableTCPServer(("", PORT), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            httpd.shutdown()


if __name__ == "__main__":
    main()