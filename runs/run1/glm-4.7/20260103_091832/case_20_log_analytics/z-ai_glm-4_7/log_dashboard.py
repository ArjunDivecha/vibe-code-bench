#!/usr/bin/env python3
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

# Sample messages for different log levels
LOG_MESSAGES = {
    "INFO": [
        "Server started successfully",
        "Connection established from {ip}",
        "Request processed in {ms}ms",
        "User {user} logged in",
        "Cache hit for key: {key}",
        "Database connection pool initialized",
        "Configuration loaded from file",
        "Health check passed",
    ],
    "WARN": [
        "High memory usage detected: {percent}%",
        "Slow query detected: {ms}ms",
        "Rate limit approaching for {ip}",
        "Deprecated API endpoint called: {endpoint}",
        "Disk space low: {space}GB remaining",
        "Connection pool nearly exhausted",
        "Response size exceeds recommended limit",
    ],
    "ERROR": [
        "Failed to connect to database: {error}",
        "Timeout while waiting for {service}",
        "Invalid request payload: {reason}",
        "Authentication failed for user {user}",
        "File not found: {path}",
        "Unable to parse JSON response",
        "External service unavailable: {service}",
    ],
    "CRITICAL": [
        "System out of memory - shutting down",
        "Database connection lost permanently",
        "Security breach detected from {ip}",
        "Corrupted data detected in {table}",
        "Primary server unresponsive",
        "Disk failure imminent - backup required",
        "SSL certificate expired",
    ]
}

def generate_fake_logs(num_lines=1000):
    """Generate fake log data with realistic distribution."""
    print(f"Generating {num_lines} lines of fake log data...")
    
    levels = ["INFO"] * 60 + ["WARN"] * 25 + ["ERROR"] * 12 + ["CRITICAL"] * 3
    start_time = datetime.now() - timedelta(hours=24)
    
    with open(LOG_FILE, "w") as f:
        for i in range(num_lines):
            level = random.choice(levels)
            timestamp = start_time + timedelta(
                seconds=random.randint(0, 86400),
                milliseconds=random.randint(0, 999)
            )
            
            template = random.choice(LOG_MESSAGES[level])
            
            # Fill in placeholders
            ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            message = template.format(
                ip=ip,
                ms=random.randint(10, 5000),
                user=f"user_{random.randint(1, 100)}",
                key=f"cache_{random.randint(1, 1000)}",
                percent=random.randint(70, 95),
                endpoint=f"/api/v{random.randint(1,3)}/{random.choice(['users', 'posts', 'comments'])}",
                space=random.randint(1, 10),
                service=random.choice(["auth", "database", "cache", "payment"]),
                error=random.choice(["timeout", "connection refused", "invalid credentials"]),
                reason=random.choice(["missing field", "invalid type", "too large"]),
                path=f"/var/data/{random.choice(['config', 'logs', 'cache'])}/{random.randint(1,100)}.dat",
                table=random.choice(["users", "transactions", "sessions"])
            )
            
            log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | {level:8} | {message}"
            f.write(log_line + "\n")
    
    print(f"Generated {LOG_FILE}")

def parse_logs():
    """Parse log file and extract analytics."""
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
    
    level_counts = Counter()
    errors_by_hour = defaultdict(int)
    critical_errors = []
    error_messages = Counter()
    
    log_pattern = re.compile(
        r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \| (\w+) \| (.*)$'
    )
    
    with open(LOG_FILE, "r") as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                
                level_counts[level] += 1
                
                if level in ["ERROR", "CRITICAL"]:
                    hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                    errors_by_hour[hour_key] += 1
                    error_messages[message] += 1
                
                if level == "CRITICAL":
                    critical_errors.append({
                        "timestamp": timestamp_str,
                        "message": message
                    })
    
    total = sum(level_counts.values())
    level_percentages = {
        level: (count / total * 100) if total > 0 else 0
        for level, count in level_counts.items()
    }
    
    # Sort errors by hour
    sorted_hours = sorted(errors_by_hour.keys())
    errors_timeline = [
        {"hour": hour, "count": errors_by_hour[hour]}
        for hour in sorted_hours
    ]
    
    # Get top error messages
    top_errors = [
        {"message": msg, "count": count}
        for msg, count in error_messages.most_common(10)
    ]
    
    return {
        "level_percentages": level_percentages,
        "errors_timeline": errors_timeline,
        "top_errors": top_errors,
        "critical_errors": critical_errors,
        "total_logs": total
    }

def create_svg_pie_chart(data):
    """Create an SVG pie chart."""
    colors = {
        "INFO": "#10b981",
        "WARN": "#f59e0b",
        "ERROR": "#ef4444",
        "CRITICAL": "#7c3aed"
    }
    
    total = sum(data.values())
    if total == 0:
        return '<svg viewBox="0 0 200 200"><text x="100" y="100" text-anchor="middle">No data</text></svg>'
    
    svg_parts = []
    start_angle = 0
    cx, cy = 100, 100
    r = 80
    
    for level, percentage in data.items():
        if percentage == 0:
            continue
        
        angle = (percentage / 100) * 360
        end_angle = start_angle + angle
        
        # Calculate path coordinates
        x1 = cx + r * 0.5 * (1 if start_angle < 180 else -1)
        y1 = cy
        
        start_rad = (start_angle - 90) * 3.14159 / 180
        end_rad = (end_angle - 90) * 3.14159 / 180
        
        x1 = cx + r * 0.7 * (1 if start_angle < 180 else -1)
        y1 = cy
        
        x1 = cx + r * 0.5 * (1 if start_angle < 180 else -1)
        y1 = cy
        
        # Use arc path
        large_arc = 1 if angle > 180 else 0
        
        x_start = cx + r * 0.5 * (1 if start_angle < 180 else -1)
        y_start = cy
        
        x_start = cx + r * 0.5 * (1 if start_angle < 180 else -1)
        y_start = cy
        
        x_start = cx + r * 0.5 * (1 if start_angle < 180 else -1)
        y_start = cy
        
        x_start = cx + r * 0.5 * (1 if start_angle < 180 else -1)
        y_start = cy
        
        # Simpler approach: use stroke-dasharray
        circumference = 2 * 3.14159 * r
        dash_length = (percentage / 100) * circumference
        gap_length = circumference - dash_length
        
        svg_parts.append(f'''
            <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{colors[level]}" 
                    stroke-width="30" stroke-dasharray="{dash_length} {gap_length}" 
                    transform="rotate({start_angle - 90} {cx} {cy})" />
        ''')
        
        start_angle = end_angle
    
    legend = []
    for level, percentage in data.items():
        legend.append(f'''
            <rect x="10" y="{180 + list(data.keys()).index(level) * 20}" width="12" height="12" fill="{colors[level]}" rx="2"/>
            <text x="28" y="{190 + list(data.keys()).index(level) * 20}" font-size="11">{level}: {percentage:.1f}%</text>
        ''')
    
    return f'''
        <svg viewBox="0 0 200 280" xmlns="http://www.w3.org/2000/svg">
            {"".join(svg_parts)}
            <text x="100" y="105" text-anchor="middle" font-size="14" font-weight="bold">Log Levels</text>
            {"".join(legend)}
        </svg>
    '''

def create_svg_bar_chart(data):
    """Create an SVG bar chart for timeline data."""
    if not data:
        return '<svg viewBox="0 0 600 200"><text x="300" y="100" text-anchor="middle">No data</text></svg>'
    
    width = 600
    height = 200
    padding = 40
    bar_width = (width - 2 * padding) / len(data) - 4
    max_count = max(item["count"] for item in data) if data else 1
    
    bars = []
    for i, item in enumerate(data):
        x = padding + i * (bar_width + 4)
        bar_height = (item["count"] / max_count) * (height - 2 * padding)
        y = height - padding - bar_height
        
        # Color based on count
        color = "#10b981" if item["count"] < 5 else "#f59e0b" if item["count"] < 10 else "#ef4444"
        
        bars.append(f'''
            <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="2">
                <title>{item["hour"]}: {item["count"]} errors</title>
            </rect>
            <text x="{x + bar_width/2}" y="{y - 5}" text-anchor="middle" font-size="10">{item["count"]}</text>
        ''')
    
    return f'''
        <svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
            <text x="{width/2}" y="20" text-anchor="middle" font-size="14" font-weight="bold">Errors per Hour</text>
            <line x1="{padding}" y1="{height - padding}" x2="{width - padding}" y2="{height - padding}" stroke="#ccc" stroke-width="1"/>
            {"".join(bars)}
        </svg>
    '''

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            analytics = parse_logs()
            
            pie_chart = create_svg_pie_chart(analytics["level_percentages"])
            bar_chart = create_svg_bar_chart(analytics["errors_timeline"])
            
            html = f"""
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
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            min-height: 100vh;
            color: #e2e8f0;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #94a3b8;
            font-size: 0.9rem;
        }}
        .charts {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-card {{
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .chart-title {{
            font-size: 1.1rem;
            margin-bottom: 15px;
            color: #94a3b8;
        }}
        .chart-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 200px;
        }}
        svg {{
            max-width: 100%;
            height: auto;
        }}
        .table-section {{
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .table-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .filter-buttons {{
            display: flex;
            gap: 8px;
        }}
        .filter-btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            background: rgba(255,255,255,0.1);
            color: #e2e8f0;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .filter-btn:hover, .filter-btn.active {{
            background: #3b82f6;
        }}
        .search-input {{
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.1);
            color: #e2e8f0;
            min-width: 250px;
        }}
        .search-input:focus {{
            outline: none;
            border-color: #3b82f6;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{
            background: rgba(255,255,255,0.05);
            font-weight: 600;
            color: #94a3b8;
        }}
        tr:hover {{
            background: rgba(255,255,255,0.02);
        }}
        .level-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .level-info {{ background: #10b98133; color: #10b981; }}
        .level-warn {{ background: #f59e0b33; color: #f59e0b; }}
        .level-error {{ background: #ef444433; color: #ef4444; }}
        .level-critical {{ background: #7c3aed33; color: #7c3aed; }}
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #94a3b8;
        }}
        .top-errors {{
            display: grid;
            gap: 10px;
        }}
        .error-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: rgba(255,255,255,0.02);
            border-radius: 6px;
        }}
        .error-message {{
            flex: 1;
            margin-right: 15px;
            font-size: 0.9rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .error-count {{
            background: #3b82f6;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Log Analytics Dashboard</h1>
            <p style="color: #94a3b8;">Real-time server log monitoring and analysis</p>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" style="color: #60a5fa;">{analytics["total_logs"]}</div>
                <div class="stat-label">Total Log Entries</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #10b981;">{analytics["level_percentages"].get("INFO", 0):.1f}%</div>
                <div class="stat-label">INFO</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #f59e0b;">{analytics["level_percentages"].get("WARN", 0):.1f}%</div>
                <div class="stat-label">WARN</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #ef4444;">{analytics["level_percentages"].get("ERROR", 0):.1f}%</div>
                <div class="stat-label">ERROR</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #7c3aed;">{analytics["level_percentages"].get("CRITICAL", 0):.1f}%</div>
                <div class="stat-label">CRITICAL</div>
            </div>
        </div>
        
        <div class="charts">
            <div class="chart-card">
                <div class="chart-title">Log Level Distribution</div>
                <div class="chart-container">
                    {pie_chart}
                </div>
            </div>
            <div class="chart-card">
                <div class="chart-title">Errors Timeline (Last 24 Hours)</div>
                <div class="chart-container">
                    {bar_chart}
                </div>
            </div>
        </div>
        
        <div class="charts">
            <div class="chart-card" style="grid-column: 1 / -1;">
                <div class="chart-title">Top Error Messages</div>
                <div class="top-errors">
                    {"".join(f'''
                        <div class="error-item">
                            <div class="error-message" title="{e["message"]}">{e["message"][:80]}...</div>
                            <div class="error-count">{e["count"]}</div>
                        </div>
                    ''' for e in analytics["top_errors"])}
                </div>
            </div>
        </div>
        
        <div class="table-section">
            <div class="table-header">
                <h2 style="font-size: 1.2rem;">🚨 Critical Errors</h2>
                <div class="filter-buttons">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="error">Error</button>
                    <button class="filter-btn" data-filter="critical">Critical</button>
                </div>
                <input type="text" class="search-input" id="searchInput" placeholder="Search errors...">
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 180px;">Timestamp</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody id="errorTable">
                    {"".join(f'''
                        <tr data-level="critical">
                            <td style="color: #94a3b8; font-family: monospace;">{e["timestamp"]}</td>
                            <td>{e["message"]}</td>
                        </tr>
                    ''' for e in analytics["critical_errors"])}
                </tbody>
            </table>
            <div id="noResults" class="no-results" style="display: none;">
                No matching errors found
            </div>
        </div>
    </div>
    
    <script>
        const allErrors = {json.dumps(analytics["critical_errors"])};
        const currentFilter = 'all';
        
        document.querySelectorAll('.filter-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                filterErrors();
            }});
        }});
        
        document.getElementById('searchInput').addEventListener('input', filterErrors);
        
        function filterErrors() {{
            const filter = document.querySelector('.filter-btn.active').dataset.filter;
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            
            const filtered = allErrors.filter(error => {{
                const matchesFilter = filter === 'all' || error.level === filter;
                const matchesSearch = error.message.toLowerCase().includes(searchTerm) || 
                                     error.timestamp.toLowerCase().includes(searchTerm);
                return matchesFilter && matchesSearch;
            }});
            
            const tbody = document.getElementById('errorTable');
            const noResults = document.getElementById('noResults');
            
            if (filtered.length === 0) {{
                tbody.innerHTML = '';
                noResults.style.display = 'block';
            }} else {{
                noResults.style.display = 'none';
                tbody.innerHTML = filtered.map(error => `
                    <tr data-level="${{error.level}}">
                        <td style="color: #94a3b8; font-family: monospace;">${{error.timestamp}}</td>
                        <td>${{error.message}}</td>
                    </tr>
                `).join('');
            }}
        }}
        
        // Auto-refresh every 30 seconds
        setInterval(() => {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_error(404)

def main():
    # Ensure log file exists
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
    
    # Parse and show initial analytics
    analytics = parse_logs()
    print("\n" + "="*50)
    print("LOG ANALYTICS SUMMARY")
    print("="*50)
    print(f"Total log entries: {analytics['total_logs']}")
    print("\nLog Level Distribution:")
    for level, pct in analytics["level_percentages"].items():
        print(f"  {level:8}: {pct:5.1f}%")
    print(f"\nCritical errors: {len(analytics['critical_errors'])}")
    print("="*50 + "\n")
    
    # Start server
    handler = DashboardHandler
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"🚀 Dashboard running at: http://localhost:{PORT}")
        print(f"📁 Log file: {os.path.abspath(LOG_FILE)}")
        print("\nPress Ctrl+C to stop the server\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped.")

if __name__ == "__main__":
    main()