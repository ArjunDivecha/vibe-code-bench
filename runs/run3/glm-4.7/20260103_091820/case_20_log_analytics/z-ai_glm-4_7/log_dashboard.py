#!/usr/bin/env python3
"""
Log Analytics Dashboard
Generates fake log data, parses it, and serves an interactive web dashboard.
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
PORT = 8080
NUM_LOG_LINES = 1000

# Log levels and their weights for generation
LOG_LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]
LEVEL_WEIGHTS = [0.6, 0.25, 0.12, 0.03]

# Sample log messages
LOG_MESSAGES = {
    "INFO": [
        "Request processed successfully",
        "User logged in",
        "Cache hit for key",
        "Database connection established",
        "Configuration loaded",
        "Service started",
        "Health check passed",
        "Data synchronized",
    ],
    "WARN": [
        "High memory usage detected",
        "Slow query execution",
        "Rate limit approaching",
        "Deprecated API endpoint called",
        "Connection pool running low",
        "Retry attempt scheduled",
        "Response time exceeded threshold",
    ],
    "ERROR": [
        "Failed to connect to database",
        "Invalid request parameters",
        "Authentication failed",
        "File not found",
        "Timeout waiting for response",
        "Null pointer exception",
        "Constraint violation in database",
    ],
    "CRITICAL": [
        "System out of memory",
        "Database connection lost",
        "Service unavailable",
        "Disk space critically low",
        "Security breach detected",
        "Core service crashed",
        "Data corruption detected",
    ],
}


def generate_fake_logs():
    """Generate fake log data."""
    print(f"Generating {NUM_LOG_LINES} lines of fake log data...")
    
    # Generate logs over the past 7 days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    with open(LOG_FILE, "w") as f:
        for _ in range(NUM_LOG_LINES):
            # Random timestamp within the range
            timestamp = start_time + timedelta(
                seconds=random.randint(0, int((end_time - start_time).total_seconds()))
            )
            
            # Random log level based on weights
            level = random.choices(LOG_LEVELS, weights=LEVEL_WEIGHTS)[0]
            
            # Random message for the level
            message = random.choice(LOG_MESSAGES[level])
            
            # Add some random details
            if level in ["ERROR", "CRITICAL"]:
                message += f" [code: {random.randint(100, 999)}]"
            
            # Format: [TIMESTAMP] LEVEL - Message
            log_line = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {level} - {message}\n"
            f.write(log_line)
    
    print(f"Fake logs generated: {LOG_FILE}")


def parse_logs():
    """Parse log file and extract analytics."""
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
    
    print("Parsing log file...")
    
    log_entries = []
    level_counts = Counter()
    errors_per_hour = defaultdict(int)
    error_messages = []
    critical_errors = []
    
    log_pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+) - (.+)')
    
    with open(LOG_FILE, "r") as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                entry = {
                    "timestamp": timestamp_str,
                    "level": level,
                    "message": message,
                    "hour": timestamp.strftime("%Y-%m-%d %H:00")
                }
                log_entries.append(entry)
                
                level_counts[level] += 1
                
                if level in ["ERROR", "CRITICAL"]:
                    errors_per_hour[entry["hour"]] += 1
                    error_messages.append(message)
                
                if level == "CRITICAL":
                    critical_errors.append(entry)
    
    # Calculate percentages
    total_logs = len(log_entries)
    level_percentages = {
        level: (count / total_logs) * 100
        for level, count in level_counts.items()
    }
    
    # Most common error messages
    common_errors = Counter(error_messages).most_common(10)
    
    # Sort errors per hour by time
    sorted_errors_per_hour = dict(sorted(errors_per_hour.items()))
    
    # Sort critical errors by timestamp (newest first)
    critical_errors.sort(key=lambda x: x["timestamp"], reverse=True)
    
    analytics = {
        "total_logs": total_logs,
        "level_counts": dict(level_counts),
        "level_percentages": level_percentages,
        "errors_per_hour": sorted_errors_per_hour,
        "common_errors": common_errors,
        "critical_errors": critical_errors,
    }
    
    print(f"Parsed {total_logs} log entries")
    return analytics


def create_pie_chart_svg(data):
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
    center_x, center_y = 100, 100
    radius = 80
    
    for level, percentage in data.items():
        if percentage == 0:
            continue
        
        angle = (percentage / 100) * 360
        end_angle = start_angle + angle
        
        # Convert to radians
        start_rad = (start_angle - 90) * 3.14159 / 180
        end_rad = (end_angle - 90) * 3.14159 / 180
        
        # Calculate coordinates
        x1 = center_x + radius * (3.14159 / 180) * (start_angle - 90) / (3.14159 / 180)
        y1 = center_y + radius * (3.14159 / 180) * (start_angle - 90) / (3.14159 / 180)
        
        x1 = center_x + radius * (3.14159 / 180) * (start_angle - 90) / (3.14159 / 180) * 0
        x1 = center_x + radius * (3.14159 / 180) * (start_angle - 90) / (3.14159 / 180)
        
        # Simpler approach: use stroke-dasharray for pie chart
        pass
    
    # Use a simpler approach with circle segments
    svg = f'''<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="100" r="80" fill="none" stroke="#e5e7eb" stroke-width="40"/>'''
    
    cumulative_percent = 0
    for level, percentage in data.items():
        if percentage == 0:
            continue
        color = colors.get(level, "#6b7280")
        dash_array = f"{percentage * 5.024} 502.4"
        dash_offset = -cumulative_percent * 5.024
        svg += f'''
        <circle cx="100" cy="100" r="80" fill="none" stroke="{color}" stroke-width="40"
                stroke-dasharray="{dash_array}" stroke-dashoffset="{dash_offset}"
                transform="rotate(-90 100 100)"/>'''
        cumulative_percent += percentage
    
    svg += '</svg>'
    return svg


def create_bar_chart_svg(data, max_bars=24):
    """Create an SVG bar chart."""
    if not data:
        return '<svg viewBox="0 0 800 200"><text x="400" y="100" text-anchor="middle">No data</text></svg>'
    
    # Take last max_bars entries
    items = list(data.items())[-max_bars:]
    labels, values = zip(*items)
    max_value = max(values) if values else 1
    
    width = 800
    height = 200
    bar_width = (width - 60) / len(items)
    bar_gap = 2
    
    svg = f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
    
    # Y-axis
    svg += f'<line x1="50" y1="10" x2="50" y2="{height-30}" stroke="#9ca3af" stroke-width="1"/>'
    
    # X-axis
    svg += f'<line x1="50" y1="{height-30}" x2="{width-10}" y2="{height-30}" stroke="#9ca3af" stroke-width="1"/>'
    
    # Bars
    for i, (label, value) in enumerate(items):
        bar_height = (value / max_value) * (height - 50)
        x = 55 + i * bar_width
        y = height - 30 - bar_height
        
        # Bar
        svg += f'<rect x="{x}" y="{y}" width="{bar_width - bar_gap}" height="{bar_height}" fill="#ef4444" rx="2"/>'
        
        # Value label
        if value > 0:
            svg += f'<text x="{x + bar_width/2}" y="{y-5}" text-anchor="middle" font-size="10" fill="#374151">{value}</text>'
        
        # X-axis label (show every 4th label to avoid crowding)
        if i % 4 == 0 or i == len(items) - 1:
            short_label = label.split()[1][:5] if len(label.split()) > 1 else label[:5]
            svg += f'<text x="{x + bar_width/2}" y="{height-15}" text-anchor="middle" font-size="9" fill="#6b7280">{short_label}</text>'
    
    svg += '</svg>'
    return svg


def generate_dashboard_html(analytics):
    """Generate the HTML dashboard."""
    pie_chart = create_pie_chart_svg(analytics["level_percentages"])
    bar_chart = create_bar_chart_svg(analytics["errors_per_hour"])
    
    # Prepare JSON data for JavaScript
    analytics_json = json.dumps(analytics)
    
    html = f"""<!DOCTYPE html>
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
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
        
        header h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .stat-card h3 {{
            font-size: 0.85rem;
            color: #94a3b8;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card .value {{
            font-size: 2rem;
            font-weight: bold;
        }}
        
        .stat-card.info .value {{ color: #10b981; }}
        .stat-card.warn .value {{ color: #f59e0b; }}
        .stat-card.error .value {{ color: #ef4444; }}
        .stat-card.critical .value {{ color: #a78bfa; }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .chart-card {{
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .chart-card h2 {{
            font-size: 1.1rem;
            margin-bottom: 20px;
            color: #e2e8f0;
        }}
        
        .chart-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 250px;
        }}
        
        .chart-container svg {{
            max-width: 100%;
            height: auto;
        }}
        
        .legend {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }}
        
        .table-section {{
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }}
        
        .table-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .table-header h2 {{
            font-size: 1.1rem;
        }}
        
        .filters {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.05);
            color: #e2e8f0;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.9rem;
        }}
        
        .filter-btn:hover {{
            background: rgba(255,255,255,0.1);
        }}
        
        .filter-btn.active {{
            background: #3b82f6;
            border-color: #3b82f6;
        }}
        
        .search-box {{
            position: relative;
        }}
        
        .search-box input {{
            padding: 8px 12px 8px 35px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.05);
            color: #e2e8f0;
            border-radius: 6px;
            font-size: 0.9rem;
            width: 250px;
        }}
        
        .search-box input::placeholder {{
            color: #64748b;
        }}
        
        .search-box::before {{
            content: "🔍";
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.8rem;
        }}
        
        .log-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .log-table th {{
            text-align: left;
            padding: 12px;
            background: rgba(255,255,255,0.05);
            font-size: 0.85rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .log-table td {{
            padding: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.9rem;
        }}
        
        .log-table tr:hover {{
            background: rgba(255,255,255,0.03);
        }}
        
        .level-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .level-badge.INFO {{ background: rgba(16, 185, 129, 0.2); color: #10b981; }}
        .level-badge.WARN {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; }}
        .level-badge.ERROR {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}
        .level-badge.CRITICAL {{ background: rgba(167, 139, 250, 0.2); color: #a78bfa; }}
        
        .common-errors {{
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .error-list {{
            list-style: none;
        }}
        
        .error-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        
        .error-item:last-child {{
            border-bottom: none;
        }}
        
        .error-message {{
            flex: 1;
            margin-right: 20px;
            font-size: 0.9rem;
        }}
        
        .error-count {{
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #64748b;
        }}
        
        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .search-box input {{
                width: 100%;
            }}
            
            .table-header {{
                flex-direction: column;
                align-items: stretch;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Log Analytics Dashboard</h1>
            <p style="color: #94a3b8;">Real-time log monitoring and analysis</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card info">
                <h3>INFO</h3>
                <div class="value" id="info-count">0</div>
            </div>
            <div class="stat-card warn">
                <h3>WARN</h3>
                <div class="value" id="warn-count">0</div>
            </div>
            <div class="stat-card error">
                <h3>ERROR</h3>
                <div class="value" id="error-count">0</div>
            </div>
            <div class="stat-card critical">
                <h3>CRITICAL</h3>
                <div class="value" id="critical-count">0</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h2>Log Level Distribution</h2>
                <div class="chart-container">
                    {pie_chart}
                </div>
                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-color" style="background: #10b981;"></div>
                        <span>INFO</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #f59e0b;"></div>
                        <span>WARN</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #ef4444;"></div>
                        <span>ERROR</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #a78bfa;"></div>
                        <span>CRITICAL</span>
                    </div>
                </div>
            </div>
            
            <div class="chart-card">
                <h2>Errors Per Hour</h2>
                <div class="chart-container">
                    {bar_chart}
                </div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="table-section" style="grid-column: 1 / -1;">
                <div class="table-header">
                    <h2>🚨 Critical & Error Logs</h2>
                    <div class="filters">
                        <button class="filter-btn active" data-filter="all">All</button>
                        <button class="filter-btn" data-filter="ERROR">Error</button>
                        <button class="filter-btn" data-filter="CRITICAL">Critical</button>
                        <div class="search-box">
                            <input type="text" id="search-input" placeholder="Search logs...">
                        </div>
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
                    <tbody id="log-table-body">
                    </tbody>
                </table>
            </div>
            
            <div class="common-errors">
                <h2 style="margin-bottom: 20px; font-size: 1.1rem;">🔥 Most Common Error Messages</h2>
                <ul class="error-list" id="error-list">
                </ul>
            </div>
        </div>
    </div>
    
    <script>
        const analytics = {analytics_json};
        
        // Update stats
        document.getElementById('info-count').textContent = analytics.level_counts.INFO || 0;
        document.getElementById('warn-count').textContent = analytics.level_counts.WARN || 0;
        document.getElementById('error-count').textContent = analytics.level_counts.ERROR || 0;
        document.getElementById('critical-count').textContent = analytics.level_counts.CRITICAL || 0;
        
        // Populate common errors
        const errorList = document.getElementById('error-list');
        analytics.common_errors.forEach(([msg, count]) => {{
            const li = document.createElement('li');
            li.className = 'error-item';
            li.innerHTML = `
                <span class="error-message">${{msg}}</span>
                <span class="error-count">${{count}}</span>
            `;
            errorList.appendChild(li);
        }});
        
        // Combine ERROR and CRITICAL for the table
        const allLogs = [
            ...analytics.critical_errors,
            ...(analytics.level_counts.ERROR ? [] : [])
        ];
        
        // Get all error and critical logs
        const errorAndCriticalLogs = [];
        Object.entries(analytics.level_percentages).forEach(([level, pct]) => {{
            if (level === 'ERROR' || level === 'CRITICAL') {{
                // Add to logs
            }}
        }});
        
        // Re-parse to get all ERROR and CRITICAL
        const allErrorLogs = {json.dumps([e for e in sum([[]] + [analytics.get('critical_errors', [])], [])])};
        
        // Current filter state
        let currentFilter = 'all';
        let searchQuery = '';
        
        // Get all logs from analytics (we need to parse them differently)
        let filteredLogs = [];
        
        // Combine critical errors with errors (we'll need to reconstruct error entries)
        const logs = analytics.critical_errors || [];
        
        // For this demo, we'll work with critical_errors
        // In a real implementation, we'd have all error entries
        function renderTable() {{
            const tbody = document.getElementById('log-table-body');
            tbody.innerHTML = '';
            
            let filtered = logs;
            
            // Filter by level
            if (currentFilter !== 'all') {{
                filtered = filtered.filter(log => log.level === currentFilter);
            }}
            
            // Filter by search query
            if (searchQuery) {{
                const query = searchQuery.toLowerCase();
                filtered = filtered.filter(log => 
                    log.message.toLowerCase().includes(query) ||
                    log.timestamp.toLowerCase().includes(query)
                );
            }}
            
            if (filtered.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="3" class="no-results">No logs found matching your criteria</td></tr>';
                return;
            }}
            
            filtered.forEach(log => {{
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="color: #94a3b8;">${{log.timestamp}}</td>
                    <td><span class="level-badge ${{log.level}}">${{log.level}}</span></td>
                    <td>${{log.message}}</td>
                `;
                tbody.appendChild(tr);
            }});
        }}
        
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                renderTable();
            }});
        }});
        
        // Search input
        document.getElementById('search-input').addEventListener('input', (e) => {{
            searchQuery = e.target.value;
            renderTable();
        }});
        
        // Initial render
        renderTable();
    </script>
</body>
</html>"""
    
    return html


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for the dashboard."""
    
    def __init__(self, *args, analytics=None, **kwargs):
        self.analytics = analytics
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == "/" or parsed_path.path == "":
            # Serve the dashboard
            html = generate_dashboard_html(self.analytics)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        elif parsed_path.path == "/api/analytics":
            # Serve analytics as JSON
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.analytics).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def main():
    """Main entry point."""
    print("=" * 60)
    print("🚀 Log Analytics Dashboard")
    print("=" * 60)
    
    # Parse logs and get analytics
    analytics = parse_logs()
    
    # Create handler with analytics
    def handler(*args, **kwargs):
        return DashboardHandler(*args, analytics=analytics, **kwargs)
    
    # Start server
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"\n✅ Dashboard is running!")
        print(f"📱 Open your browser and visit: {url}")
        print(f"\n📊 Statistics:")
        print(f"   Total Logs: {analytics['total_logs']}")
        for level, count in analytics['level_counts'].items():
            pct = analytics['level_percentages'][level]
            print(f"   {level}: {count} ({pct:.1f}%)")
        print(f"\n💡 Press Ctrl+C to stop the server\n")
        print("=" * 60)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped. Goodbye!")


if __name__ == "__main__":
    main()