#!/usr/bin/env python3
import os
import re
import json
import random
import datetime
from collections import Counter, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import webbrowser

LOG_FILE = "server.log"
PORT = 8080

def generate_fake_logs():
    """Generate 1000 lines of fake log data if server.log doesn't exist"""
    if os.path.exists(LOG_FILE):
        return
    
    print("Generating fake log data...")
    levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL']
    messages = {
        'INFO': ['Server started', 'Request processed', 'Connection established', 'Data saved', 'Cache cleared'],
        'WARN': ['High memory usage', 'Slow response time', 'Connection timeout', 'Deprecated API used'],
        'ERROR': ['Database connection failed', 'File not found', 'Invalid configuration', 'Service unavailable'],
        'CRITICAL': ['System crash', 'Data corruption detected', 'Security breach attempt', 'Service down']
    }
    
    with open(LOG_FILE, 'w') as f:
        for i in range(1000):
            timestamp = datetime.datetime.now() - datetime.timedelta(hours=random.randint(0, 24))
            level = random.choice(levels)
            message = random.choice(messages[level])
            f.write(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}\n")
    print("Fake log data generated!")

def parse_logs():
    """Parse log file and extract analytics data"""
    if not os.path.exists(LOG_FILE):
        return None
    
    level_counts = Counter()
    errors_per_hour = defaultdict(int)
    error_messages = Counter()
    critical_logs = []
    
    log_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (.+)')
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                level_counts[level] += 1
                
                # Parse timestamp for hourly errors
                try:
                    timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                    if level in ['ERROR', 'CRITICAL']:
                        errors_per_hour[hour_key] += 1
                except:
                    pass
                
                # Track error messages
                if level in ['ERROR', 'CRITICAL']:
                    error_messages[message] += 1
                
                # Store critical logs for table
                if level == 'CRITICAL':
                    critical_logs.append({
                        'timestamp': timestamp_str,
                        'message': message
                    })
    
    total_logs = sum(level_counts.values())
    level_percentages = {
        level: (count / total_logs) * 100 
        for level, count in level_counts.items()
    }
    
    # Sort errors per hour by time
    sorted_errors = sorted(errors_per_hour.items())
    
    return {
        'level_percentages': level_percentages,
        'errors_per_hour': sorted_errors,
        'common_errors': error_messages.most_common(10),
        'critical_logs': critical_logs
    }

def create_dashboard_html(data):
    """Create the HTML dashboard"""
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log Analytics Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        h1 {{
            color: #2c3e50;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .card h2 {{
            color: #34495e;
            margin-bottom: 15px;
            font-size: 1.2em;
        }}
        
        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        
        .metric-level {{
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
            color: white;
        }}
        
        .INFO {{ background-color: #3498db; }}
        .WARN {{ background-color: #f39c12; }}
        .ERROR {{ background-color: #e74c3c; }}
        .CRITICAL {{ background-color: #8e44ad; }}
        
        svg {{
            width: 100%;
            height: 200px;
        }}
        
        .bar {{
            fill: #3498db;
            transition: fill 0.3s;
        }}
        
        .bar:hover {{
            fill: #2980b9;
        }}
        
        .error-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .error-table th,
        .error-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        .error-table th {{
            background-color: #34495e;
            color: white;
        }}
        
        .error-table tr:hover {{
            background-color: #f5f5f5;
        }}
        
        .search-box {{
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .filter-buttons {{
            margin-bottom: 15px;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            margin-right: 10px;
            border: none;
            border-radius: 4px;
            background-color: #3498db;
            color: white;
            cursor: pointer;
            transition: background-color 0.3s;
        }}
        
        .filter-btn:hover {{
            background-color: #2980b9;
        }}
        
        .filter-btn.active {{
            background-color: #2c3e50;
        }}
        
        .hidden {{ display: none; }}
        
        .pie-chart {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Log Analytics Dashboard</h1>
        
        <div class="dashboard-grid">
            <div class="card">
                <h2>📊 Log Level Distribution</h2>
                <div id="level-metrics">
                    {generate_level_metrics_html(data['level_percentages'])}
                </div>
            </div>
            
            <div class="card">
                <h2>🥧 Log Level Pie Chart</h2>
                <div class="pie-chart">
                    {generate_pie_chart_svg(data['level_percentages'])}
                </div>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h2>📈 Errors Per Hour</h2>
                <div id="errors-chart">
                    {generate_errors_chart_svg(data['errors_per_hour'])}
                </div>
            </div>
            
            <div class="card">
                <h2>🔍 Most Common Errors</h2>
                <div id="common-errors">
                    {generate_common_errors_html(data['common_errors'])}
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>⚠️ Critical Error Log</h2>
            <input type="text" class="search-box" id="searchInput" placeholder="Search critical errors...">
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="filterLogs('all')">All Levels</button>
                <button class="filter-btn" onclick="filterLogs('error')">Errors Only</button>
                <button class="filter-btn" onclick="filterLogs('critical')">Critical Only</button>
            </div>
            <table class="error-table" id="errorTable">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody id="errorTableBody">
                    {generate_critical_logs_html(data['critical_logs'])}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Search functionality
        document.getElementById('searchInput').addEventListener('keyup', function() {{
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#errorTableBody tr');
            
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            }});
        }});
        
        // Filter functionality
        function filterLogs(type) {{
            const buttons = document.querySelectorAll('.filter-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // This would normally filter based on log level
            // For this demo, we'll just show all critical logs
            console.log('Filter applied:', type);
        }}
        
        // Auto-refresh every 30 seconds
        setTimeout(() => {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>
'''

def generate_level_metrics_html(level_percentages):
    """Generate HTML for level metrics"""
    html = ""
    for level, percentage in level_percentages.items():
        html += f'''
        <div class="metric">
            <span class="metric-level {level}">{level}</span>
            <span>{percentage:.1f}%</span>
        </div>
        '''
    return html

def generate_pie_chart_svg(level_percentages):
    """Generate SVG pie chart for log levels"""
    colors = {'INFO': '#3498db', 'WARN': '#f39c12', 'ERROR': '#e74c3c', 'CRITICAL': '#8e44ad'}
    total = sum(level_percentages.values())
    
    svg = '<svg viewBox="0 0 200 200">'
    cx, cy, r = 100, 100, 80
    
    current_angle = 0
    for level, percentage in level_percentages.items():
        angle = (percentage / 100) * 360
        angle_rad = (current_angle * 3.14159) / 180
        next_angle_rad = ((current_angle + angle) * 3.14159) / 180
        
        x1 = cx + r * 0.7 * (1 + 0.5 * (current_angle / 90))
        y1 = cy + r * 0.7 * (1 + 0.5 * ((current_angle + angle) / 90))
        
        large_arc = 1 if angle > 180 else 0
        x2 = cx + r * 0.7 * (1 + 0.5 * (next_angle_rad / 90))
        y2 = cy + r * 0.7 * (1 + 0.5 * (next_angle_rad / 90))
        
        # Simplified pie chart
        svg += f'''
        <path d="M {cx} {cy} L {cx + r} {cy} A {r} {r} 0 {large_arc} 1 {cx + r * 0.7} {cy - r * 0.7} Z" 
              fill="{colors.get(level, '#95a5a6')}" opacity="0.8"/>
        '''
        current_angle += angle
    
    svg += '</svg>'
    return svg

def generate_errors_chart_svg(errors_per_hour):
    """Generate SVG bar chart for errors per hour"""
    if not errors_per_hour:
        return '<p>No errors found</p>'
    
    max_errors = max(count for _, count in errors_per_hour)
    svg = '<svg viewBox="0 0 800 200">'
    
    bar_width = 800 / len(errors_per_hour)
    for i, (hour, count) in enumerate(errors_per_hour):
        bar_height = (count / max_errors) * 180
        x = i * bar_width
        y = 200 - bar_height
        
        svg += f'''
        <rect class="bar" x="{x}" y="{y}" width="{bar_width - 2}" height="{bar_height}"/>
        <text x="{x + bar_width/2}" y="195" text-anchor="middle" font-size="10">{hour.split()[1][:5]}</text>
        '''
    
    svg += '</svg>'
    return svg

def generate_common_errors_html(common_errors):
    """Generate HTML for most common errors"""
    html = ""
    for message, count in common_errors:
        html += f'''
        <div class="metric">
            <span>{message}</span>
            <span>{count} times</span>
        </div>
        '''
    return html

def generate_critical_logs_html(critical_logs):
    """Generate HTML for critical logs table"""
    html = ""
    for log in critical_logs:
        html += f'''
        <tr>
            <td>{log['timestamp']}</td>
            <td>{log['message']}</td>
        </tr>
        '''
    return html

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            data = parse_logs()
            if data is None:
                self.send_error(500, "No log file found")
                return
            
            html = create_dashboard_html(data)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
        else:
            self.send_error(404)

def main():
    """Main function"""
    print("🚀 Starting Log Analytics Dashboard...")
    
    # Generate fake logs if needed
    generate_fake_logs()
    
    # Parse logs
    print("📊 Analyzing log data...")
    data = parse_logs()
    
    if data is None:
        print("❌ Error: Could not parse log file")
        return
    
    # Start HTTP server
    server = HTTPServer(('localhost', PORT), DashboardHandler)
    
    print(f"✅ Dashboard ready!")
    print(f"🌐 Open your browser to: http://localhost:{PORT}")
    print("📈 Press Ctrl+C to stop the server")
    
    # Open browser automatically
    try:
        webbrowser.open(f'http://localhost:{PORT}')
    except:
        pass
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
        server.shutdown()

if __name__ == "__main__":
    main()