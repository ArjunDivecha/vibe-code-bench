import os
import sys
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import re
import random

LOG_FILE = "server.log"
PORT = 8000

def generate_fake_log_data():
    """Generate 1000 lines of fake log data if log file doesn't exist."""
    if os.path.exists(LOG_FILE):
        return

    print(f"Log file '{LOG_FILE}' not found. Generating fake log data...")
    log_levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    # Weighted choice: more INFO, fewer CRITICAL
    weights = [0.6, 0.25, 0.1, 0.05]
    
    start_time = datetime.now() - timedelta(hours=24)  # logs from last 24 hours
    
    with open(LOG_FILE, "w") as f:
        for _ in range(1000):
            level = random.choices(log_levels, weights=weights)[0]
            timestamp = start_time + timedelta(seconds=random.randint(0, 24*60*60))
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            # Common error messages
            messages = {
                "INFO": [
                    "User logged in", "User logged out", "File uploaded", 
                    "Backup completed", "System check OK"
                ],
                "WARN": [
                    "Disk usage high", "Memory usage approaching limit", 
                    "Deprecated API call", "Connection timeout", "Retry attempt"
                ],
                "ERROR": [
                    "Database connection failed", "File not found", 
                    "Permission denied", "Timeout exceeded", "Invalid input"
                ],
                "CRITICAL": [
                    "System crash", "Data corruption detected", 
                    "Security breach detected", "Service unavailable", 
                    "Hardware failure"
                ]
            }
            
            msg = random.choice(messages[level])
            user_id = random.randint(1000, 9999)
            f.write(f"{formatted_time} [{level}] User:{user_id} - {msg}\n")
    
    print(f"Generated {LOG_FILE} with 1000 log entries.")

def parse_log_file():
    """Parse log file and extract analytics."""
    if not os.path.exists(LOG_FILE):
        return {}, {}, []

    log_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(INFO|WARN|ERROR|CRITICAL)\].* - (.+)")
    
    log_counts = Counter()
    hourly_errors = defaultdict(int)
    critical_errors = []

    with open(LOG_FILE, "r") as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                log_counts[level] += 1
                
                if level in ["ERROR", "CRITICAL"]:
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    hourly_errors[hour_key] += 1
                
                if level == "CRITICAL":
                    critical_errors.append({
                        "timestamp": timestamp_str,
                        "message": message
                    })

    # Sort hourly errors by time
    sorted_hourly = sorted(hourly_errors.items())
    
    return log_counts, sorted_hourly, critical_errors

def create_svg_bar_chart(data, width=600, height=200, color="#3498db"):
    """Create an SVG bar chart from data."""
    if not data:
        return '<text x="10" y="20" font-size="14" fill="#555">No data available</text>'
    
    max_value = max(y for x, y in data)
    bar_width = (width - 60) / len(data) - 5
    chart_height = height - 40
    
    svg = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']
    
    for i, (label, value) in enumerate(data):
        x = 60 + i * (bar_width + 5)
        bar_height = (value / max_value) * chart_height if max_value > 0 else 0
        y = height - 20 - bar_height
        
        svg.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" />')
        svg.append(f'<text x="{x + bar_width/2}" y="{height - 5}" font-size="10" text-anchor="middle" fill="#555">{label.split(" ")[-1]}</text>')
    
    # Y-axis
    svg.append(f'<line x1="50" y1="20" x2="50" y1="{height-20}" stroke="#000" />')
    # X-axis
    svg.append(f'<line x1="50" y1="{height-20}" x2="{width}" y2="{height-20}" stroke="#000" />')
    
    # Y-axis labels
    for i in range(5):
        y = height - 20 - i * (chart_height / 4)
        value = int(max_value * i / 4)
        svg.append(f'<text x="45" y="{y + 5}" font-size="10" text-anchor="end" fill="#555">{value}</text>')
        svg.append(f'<line x1="48" y1="{y}" x2="52" y2="{y}" stroke="#000" />')
    
    svg.append('</svg>')
    return "\n".join(svg)

def create_svg_pie_chart(percentages, width=300, height=300):
    """Create an SVG pie chart from percentages."""
    if not percentages:
        return '<text x="10" y="20" font-size="14" fill="#555">No data available</text>'
    
    colors = {
        "CRITICAL": "#e74c3c",
        "ERROR": "#f39c12",
        "WARN": "#f1c40f",
        "INFO": "#2ecc71"
    }
    
    cx, cy, r = width // 2, height // 2, min(width, height) // 2 - 20
    svg = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']
    
    total = sum(percentages.values())
    start_angle = 0
    
    for level, percent in percentages.items():
        angle = 360 * (percent / total) if total > 0 else 0
        
        # Convert to radians
        start_rad = start_angle * 3.14159 / 180
        end_rad = (start_angle + angle) * 3.14159 / 180
        
        # Calculate points
        x1 = cx + r * 0.8 * (3.14159 * 2)
        y1 = cy + r * 0.8 * (3.14159 * 2)
        x2 = cx + r * 0.8 * (3.14159 * 2)
        y2 = cy + r * 0.8 * (3.14159 * 2)
        
        # Large arc flag
        large_arc_flag = 1 if angle >= 180 else 0
        
        path = f'M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc_flag} 1 {x2} {y2} Z'
        
        svg.append(f'<path d="{path}" fill="{colors.get(level, "#ccc")}" />')
        
        # Add label
        label_angle = start_angle + angle / 2
        label_x = cx + (r + 30) * 0.8 * (3.14159 * 2)
        label_y = cy + (r + 30) * 0.8 * (3.14159 * 2)
        
        svg.append(f'<text x="{label_x}" y="{label_y}" font-size="12" text-anchor="middle" fill="#333">{level}</text>')
        
        start_angle += angle
    
    svg.append('</svg>')
    return "\n".join(svg)

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            log_counts, hourly_errors, critical_errors = parse_log_file()
            
            # Calculate percentages
            total_logs = sum(log_counts.values())
            percentages = {level: count for level, count in log_counts.items()}
            
            # Prepare data for charts
            error_trend_data = hourly_errors[-24:]  # Last 24 hours
            
            # Create pie chart
            pie_chart = create_svg_pie_chart(percentages)
            
            # Create bar chart
            bar_chart = create_svg_bar_chart(error_trend_data, color="#e74c3c")
            
            # Create critical errors table rows
            critical_rows = ""
            for error in critical_errors:
                critical_rows += f"""
                <tr>
                    <td>{error['timestamp']}</td>
                    <td>{error['message']}</td>
                </tr>
                """
            
            html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Log Analytics Dashboard</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .stats-grid {{
                        display: grid;
                        grid-template-columns: repeat(4, 1fr);
                        gap: 20px;
                        margin-bottom: 30px;
                    }}
                    .stat-card {{
                        background-color: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        text-align: center;
                    }}
                    .stat-value {{
                        font-size: 2em;
                        font-weight: bold;
                        color: #3498db;
                    }}
                    .chart-container {{
                        background-color: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        margin-bottom: 30px;
                    }}
                    .chart-title {{
                        margin-top: 0;
                        color: #333;
                    }}
                    .table-container {{
                        background-color: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    th, td {{
                        padding: 12px;
                        text-align: left;
                        border-bottom: 1px solid #ddd;
                    }}
                    th {{
                        background-color: #f8f9fa;
                        font-weight: bold;
                    }}
                    tr:hover {{
                        background-color: #f5f5f5;
                    }}
                    .filter-container {{
                        margin-bottom: 20px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }}
                    .search-box {{
                        padding: 8px;
                        width: 300px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                    }}
                    .filter-select {{
                        padding: 8px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Log Analytics Dashboard</h1>
                        <p>Real-time monitoring and analysis of server logs</p>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">{total_logs}</div>
                            <div class="stat-label">Total Logs</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" style="color: #e74c3c;">{log_counts['CRITICAL']}</div>
                            <div class="stat-label">Critical Errors</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" style="color: #f39c12;">{log_counts['ERROR']}</div>
                            <div class="stat-label">Errors</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" style="color: #f1c40f;">{log_counts['WARN']}</div>
                            <div class="stat-label">Warnings</div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h2 class="chart-title">Log Level Distribution</h2>
                        {pie_chart}
                    </div>
                    
                    <div class="chart-container">
                        <h2 class="chart-title">Errors Per Hour (Last 24 Hours)</h2>
                        {bar_chart}
                    </div>
                    
                    <div class="table-container">
                        <div class="filter-container">
                            <h2 class="chart-title">Critical Errors</h2>
                            <div>
                                <input type="text" id="search" class="search-box" placeholder="Search messages...">
                                <select id="level-filter" class="filter-select">
                                    <option value="all">All Levels</option>
                                    <option value="CRITICAL">Critical Only</option>
                                    <option value="ERROR">Errors & Critical</option>
                                </select>
                            </div>
                        </div>
                        <table id="error-table">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Message</th>
                                </tr>
                            </thead>
                            <tbody>
                                {critical_rows}
                            </tbody>
                        </table>
                    </div>
                </div>

                <script>
                    // Simple client-side filtering
                    document.getElementById('search').addEventListener('input', filterTable);
                    document.getElementById('level-filter').addEventListener('change', filterTable);
                    
                    function filterTable() {{
                        const searchValue = document.getElementById('search').value.toLowerCase();
                        const filterValue = document.getElementById('level-filter').value;
                        const table = document.getElementById('error-table').getElementsByTagName('tbody')[0];
                        const rows = table.getElementsByTagName('tr');
                        
                        for (let i = 0; i < rows.length; i++) {{
                            const messageCell = rows[i].getElementsByTagName('td')[1];
                            if (messageCell) {{
                                const message = messageCell.textContent.toLowerCase();
                                const matchesSearch = message.includes(searchValue);
                                const matchesFilter = true; // In a real app, this would filter by log level
                                
                                if (matchesSearch && matchesFilter) {{
                                    rows[i].style.display = '';
                                }} else {{
                                    rows[i].style.display = 'none';
                                }}
                            }}
                        }}
                    }}
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

def main():
    generate_fake_log_data()
    
    server = HTTPServer(("", PORT), DashboardHandler)
    print(f"Log Analytics Dashboard running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == "__main__":
    main()