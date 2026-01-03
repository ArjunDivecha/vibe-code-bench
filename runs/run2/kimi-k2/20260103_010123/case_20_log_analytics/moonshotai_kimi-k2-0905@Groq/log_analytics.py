#!/usr/bin/env python3
import os
import json
import random
import datetime
import collections
import http.server
import socketserver
import threading
import urllib.parse
import re
from datetime import datetime, timedelta

class LogGenerator:
    def __init__(self, filename="server.log"):
        self.filename = filename
        self.levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
        self.messages = {
            "INFO": ["Server started", "Request processed", "Connection established", 
                    "Cache cleared", "Service running", "Health check passed"],
            "WARN": ["High memory usage", "Slow response time", "Connection timeout",
                    "Deprecated API usage", "Low disk space"],
            "ERROR": ["Database connection failed", "File not found", "Permission denied",
                     "Invalid request format", "Service unavailable"],
            "CRITICAL": ["System crash", "Data corruption", "Security breach",
                        "Complete service failure", "Hardware failure"]
        }
    
    def generate_logs(self, count=1000):
        """Generate fake log data"""
        with open(self.filename, 'w') as f:
            current_time = datetime.now() - timedelta(hours=24)
            
            for i in range(count):
                # Random level distribution
                level = random.choices(
                    self.levels, 
                    weights=[60, 25, 12, 3]  # INFO most common, CRITICAL least
                )[0]
                
                # Random message for level
                message = random.choice(self.messages[level])
                
                # Add some variation to make errors more interesting
                if level in ["ERROR", "CRITICAL"]:
                    message += f" on component {random.randint(1,5)}"
                
                # Random time increment
                current_time += timedelta(seconds=random.randint(1, 120))
                
                # Write log line
                log_line = f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} - {level} - {message}\n"
                f.write(log_line)

class LogParser:
    def __init__(self, filename="server.log"):
        self.filename = filename
        self.log_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\w+) - (.+)')
        
    def parse_logs(self):
        """Parse log file and extract analytics"""
        if not os.path.exists(self.filename):
            generator = LogGenerator(self.filename)
            generator.generate_logs()
        
        logs = []
        level_counts = collections.Counter()
        error_timeline = collections.Counter()
        error_messages = collections.Counter()
        critical_logs = []
        
        with open(self.filename, 'r') as f:
            for line in f:
                match = self.log_pattern.match(line.strip())
                if match:
                    timestamp_str, level, message = match.groups()
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    
                    logs.append({
                        'timestamp': timestamp_str,
                        'level': level,
                        'message': message
                    })
                    
                    level_counts[level] += 1
                    
                    if level in ['ERROR', 'CRITICAL']:
                        hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                        error_timeline[hour_key] += 1
                        error_messages[message] += 1
                        
                        if level == 'CRITICAL':
                            critical_logs.append({
                                'timestamp': timestamp_str,
                                'message': message
                            })
        
        total_logs = len(logs)
        level_percentages = {
            level: (count / total_logs * 100) 
            for level, count in level_counts.items()
        }
        
        return {
            'level_percentages': level_percentages,
            'error_timeline': dict(error_timeline),
            'error_messages': dict(error_messages.most_common(10)),
            'critical_logs': critical_logs,
            'total_logs': total_logs
        }

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, parser=None, **kwargs):
        self.parser = parser
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.generate_dashboard().encode())
        
        elif self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            data = self.parser.parse_logs()
            self.wfile.write(json.dumps(data).encode())
        
        elif self.path.startswith('/api/filter'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            level = params.get('level', ['All'])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            data = self.parser.parse_logs()
            if level != 'All':
                filtered_critical = [
                    log for log in data['critical_logs'] 
                    if level == 'CRITICAL' or level in log['message']
                ]
                data['critical_logs'] = filtered_critical
            
            self.wfile.write(json.dumps(data).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def generate_dashboard(self):
        """Generate the HTML dashboard"""
        return """<!DOCTYPE html>
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .chart-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
        }
        
        .pie-chart {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 300px;
        }
        
        .timeline-chart {
            height: 300px;
            overflow-x: auto;
        }
        
        .bar {
            fill: #667eea;
        }
        
        .bar:hover {
            fill: #764ba2;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        th {
            background-color: #667eea;
            color: white;
            font-weight: bold;
        }
        
        tr:hover {
            background-color: #f8f9fa;
        }
        
        .search-box {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 16px;
        }
        
        .filter-buttons {
            margin-bottom: 20px;
        }
        
        .filter-btn {
            background-color: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            margin-right: 10px;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        
        .filter-btn:hover {
            background-color: #764ba2;
        }
        
        .filter-btn.active {
            background-color: #764ba2;
        }
        
        .critical {
            color: #dc3545;
            font-weight: bold;
        }
        
        .error {
            color: #fd7e14;
        }
        
        .warning {
            color: #ffc107;
        }
        
        .info {
            color: #17a2b8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Log Analytics Dashboard</h1>
            <p>Real-time log analysis and monitoring</p>
        </div>
        
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <div class="stat-value" id="totalLogs">-</div>
                <div>Total Log Entries</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="errorPercent">-</div>
                <div>Error Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="criticalCount">-</div>
                <div>Critical Issues</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="warnPercent">-</div>
                <div>Warning Rate</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Log Level Distribution</div>
            <div class="pie-chart" id="pieChart"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Error Timeline (Last 24 Hours)</div>
            <div class="timeline-chart" id="timelineChart"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Critical Errors</div>
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="filterLogs('All')">All</button>
                <button class="filter-btn" onclick="filterLogs('CRITICAL')">Critical Only</button>
                <button class="filter-btn" onclick="filterLogs('ERROR')">Errors Only</button>
            </div>
            <input type="text" class="search-box" placeholder="Search critical errors..." id="searchBox" onkeyup="searchTable()">
            <table id="criticalTable">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody id="criticalTableBody">
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        let logData = {};
        
        function loadData() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    logData = data;
                    updateStats();
                    drawPieChart();
                    drawTimeline();
                    updateCriticalTable();
                });
        }
        
        function updateStats() {
            document.getElementById('totalLogs').textContent = logData.total_logs;
            document.getElementById('errorPercent').textContent = 
                (logData.level_percentages.ERROR || 0).toFixed(1) + '%';
            document.getElementById('criticalCount').textContent = logData.critical_logs.length;
            document.getElementById('warnPercent').textContent = 
                (logData.level_percentages.WARN || 0).toFixed(1) + '%';
        }
        
        function drawPieChart() {
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('width', '300');
            svg.setAttribute('height', '300');
            
            const centerX = 150;
            const centerY = 150;
            const radius = 120;
            
            let total = 0;
            const colors = ['#17a2b8', '#ffc107', '#fd7e14', '#dc3545'];
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            
            levels.forEach(level => {
                total += logData.level_percentages[level] || 0;
            });
            
            let currentAngle = -90;
            
            levels.forEach((level, index) => {
                const percentage = logData.level_percentages[level] || 0;
                const angle = (percentage / 100) * 360;
                
                const x1 = centerX + radius * Math.cos(currentAngle * Math.PI / 180);
                const y1 = centerY + radius * Math.sin(currentAngle * Math.PI / 180);
                
                currentAngle += angle;
                
                const x2 = centerX + radius * Math.cos(currentAngle * Math.PI / 180);
                const y2 = centerY + radius * Math.sin(currentAngle * Math.PI / 180);
                
                const largeArcFlag = angle > 180 ? 1 : 0;
                
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`);
                path.setAttribute('fill', colors[index]);
                path.setAttribute('stroke', 'white');
                path.setAttribute('stroke-width', '2');
                
                // Add label
                const labelAngle = (currentAngle - angle/2) * Math.PI / 180;
                const labelX = centerX + (radius + 30) * Math.cos(labelAngle);
                const labelY = centerY + (radius + 30) * Math.sin(labelAngle);
                
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', labelX);
                text.setAttribute('y', labelY);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('font-size', '12');
                text.textContent = `${level} (${percentage.toFixed(1)}%)`;
                
                svg.appendChild(path);
                svg.appendChild(text);
            });
            
            document.getElementById('pieChart').innerHTML = '';
            document.getElementById('pieChart').appendChild(svg);
        }
        
        function drawTimeline() {
            const container = document.getElementById('timelineChart');
            const data = logData.error_timeline;
            const entries = Object.entries(data).sort();
            
            if (entries.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #666;">No errors in the last 24 hours</p>';
                return;
            }
            
            const maxValue = Math.max(...Object.values(data));
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('width', '100%');
            svg.setAttribute('height', '250');
            
            const barWidth = 800 / entries.length;
            const maxHeight = 200;
            
            entries.forEach((entry, index) => {
                const [time, count] = entry;
                const barHeight = (count / maxValue) * maxHeight;
                const x = index * barWidth;
                const y = 250 - barHeight - 30;
                
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', x);
                rect.setAttribute('y', y);
                rect.setAttribute('width', barWidth - 2);
                rect.setAttribute('height', barHeight);
                rect.setAttribute('fill', '#667eea');
                rect.setAttribute('class', 'bar');
                
                // Add time label
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', x + barWidth/2);
                text.setAttribute('y', 250 - 5);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('font-size', '10');
                text.setAttribute('transform', `rotate(-45, ${x + barWidth/2}, 250)`);
                text.textContent = time.split(' ')[1].substring(0, 5);
                
                // Add count label
                const countText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                countText.setAttribute('x', x + barWidth/2);
                countText.setAttribute('y', y - 5);
                countText.setAttribute('text-anchor', 'middle');
                countText.setAttribute('font-size', '10');
                countText.textContent = count;
                
                svg.appendChild(rect);
                svg.appendChild(text);
                svg.appendChild(countText);
            });
            
            container.innerHTML = '';
            container.appendChild(svg);
        }
        
        function updateCriticalTable() {
            const tbody = document.getElementById('criticalTableBody');
            tbody.innerHTML = '';
            
            logData.critical_logs.forEach(log => {
                const row = tbody.insertRow();
                row.insertCell(0).textContent = log.timestamp;
                row.insertCell(1).textContent = log.message;
                row.cells[1].className = 'critical';
            });
        }
        
        function searchTable() {
            const input = document.getElementById('searchBox');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('criticalTable');
            const tr = table.getElementsByTagName('tr');
            
            for (let i = 1; i < tr.length; i++) {
                const td = tr[i].getElementsByTagName('td')[1];
                if (td) {
                    const txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        tr[i].style.display = '';
                    } else {
                        tr[i].style.display = 'none';
                    }
                }
            }
        }
        
        function filterLogs(level) {
            // Update active button
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Fetch filtered data
            fetch(`/api/filter?level=${level}`)
                .then(response => response.json())
                .then(data => {
                    logData = data;
                    updateCriticalTable();
                });
        }
        
        // Load data on page load
        loadData();
        
        // Refresh data every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>"""
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_server(port=8080):
    """Run the HTTP server"""
    parser = LogParser()
    
    def handler(*args, **kwargs):
        return DashboardHandler(*args, parser=parser, **kwargs)
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"\n🚀 Log Analytics Dashboard running at: http://localhost:{port}")
        print("📊 Features:")
        print("   • Real-time log analysis")
        print("   • Interactive charts and graphs")
        print("   • Searchable critical error table")
        print("   • Filter by log level")
        print("   • Auto-refresh every 30 seconds")
        print("\nPress Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            httpd.shutdown()

if __name__ == "__main__":
    print("🔍 Checking for server.log file...")
    parser = LogParser()
    
    if not os.path.exists("server.log"):
        print("📄 Generating 1000 lines of fake log data...")
        generator = LogGenerator()
        generator.generate_logs()
        print("✅ Log data generated successfully!")
    
    print("📊 Parsing log file for analytics...")
    data = parser.parse_logs()
    print(f"✅ Found {data['total_logs']} log entries")
    
    # Start server in a separate thread to show URL immediately
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Keep main thread alive
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")