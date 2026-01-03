import os
import re
import json
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from functools import lru_cache

LOG_FILE = "server.log"
PORT = 8000

# Log level definitions
LOG_LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]

# Generate fake log data
def generate_log_data(lines=1000):
    templates = {
        "INFO": [
            "User {user} logged in successfully",
            "Connection established to {service}",
            "Backup completed for {service}",
            "Service {service} started",
        ],
        "WARN": [
            "High memory usage detected: {mem}%",
            "Disk space low on {disk}",
            "Connection timeout to {service}",
            "Deprecated API call by {user}",
        ],
        "ERROR": [
            "Failed to connect to database: {error}",
            "Permission denied for user {user}",
            "File not found: {file}",
            "Timeout waiting for {service}",
        ],
        "CRITICAL": [
            "Database connection lost!",
            "Authentication server offline",
            "Critical security vulnerability detected",
            "System overload - shutting down services",
        ]
    }

    users = ["alice", "bob", "charlie", "david", "eve"]
    services = ["auth", "database", "cache", "api", "storage", "web"]
    errors = ["ConnectionRefused", "Timeout", "AuthFailed", "NotFound"]
    disks = ["C:", "/home", "/var", "D:"]

    with open(LOG_FILE, "w") as f:
        current_time = datetime.now() - timedelta(hours=24)
        
        for _ in range(lines):
            level = random.choices(LOG_LEVELS, weights=[50, 30, 15, 5])[0]
            template = random.choice(templates[level])
            
            message = template.format(
                user=random.choice(users),
                service=random.choice(services),
                error=random.choice(errors),
                file=f"/path/to/file_{random.randint(1,100)}.log",
                mem=random.randint(80, 99),
                disk=random.choice(disks)
            )
            
            log_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{log_time}] {level}: {message}\n")
            
            # Randomly advance time (mostly by seconds, sometimes by minutes)
            current_time += timedelta(seconds=random.randint(1, 300))

# Parse log file
@lru_cache(maxsize=1)
def parse_logs():
    if not os.path.exists(LOG_FILE):
        generate_log_data()
    
    log_pattern = re.compile(r'\[(.*?)\] (INFO|WARN|ERROR|CRITICAL): (.*)')
    
    logs = []
    level_counts = Counter()
    hourly_errors = defaultdict(int)
    error_messages = Counter()
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    log_entry = {
                        "timestamp": timestamp_str,
                        "level": level,
                        "message": message,
                        "hour": timestamp.strftime("%Y-%m-%d %H:00")
                    }
                    logs.append(log_entry)
                    level_counts[level] += 1
                    
                    if level in ["ERROR", "CRITICAL"]:
                        hourly_errors[log_entry["hour"]] += 1
                        if level == "ERROR" or level == "CRITICAL":
                            error_messages[message] += 1
                except ValueError:
                    continue  # Skip malformed timestamp lines
    
    # Calculate percentages
    total_logs = sum(level_counts.values())
    level_percentages = {
        level: (count / total_logs) * 100 if total_logs > 0 else 0
        for level, count in level_counts.items()
    }
    
    # Prepare hourly data for timeline (ensure all hours in range are represented)
    if hourly_errors:
        start_hour = min(hourly_errors.keys())
        end_hour = max(hourly_errors.keys())
        current = datetime.strptime(start_hour, "%Y-%m-%d %H:00")
        end = datetime.strptime(end_hour, "%Y-%m-%d %H:00")
        
        full_hourly = {}
        while current <= end:
            hour_key = current.strftime("%Y-%m-%d %H:00")
            full_hourly[hour_key] = hourly_errors.get(hour_key, 0)
            current += timedelta(hours=1)
    else:
        full_hourly = {}
    
    # Get most common error messages (top 10)
    common_errors = [{"message": msg, "count": count} 
                     for msg, count in error_messages.most_common(10)]
    
    # Filter critical errors for table
    critical_errors = [
        {"timestamp": log["timestamp"], "message": log["message"]}
        for log in logs if log["level"] == "CRITICAL"
    ]
    
    return {
        "levelPercentages": level_percentages,
        "hourlyErrors": full_hourly,
        "commonErrors": common_errors,
        "criticalErrors": critical_errors
    }

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self.get_html().encode())
        elif self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            data = parse_logs()
            self.wfile.write(json.dumps(data).encode())
        elif self.path.startswith("/api/critical?"):
            # Handle search query for critical errors
            query = parse_qs(self.path.split("?", 1)[1])
            search_term = query.get("q", [""])[0].lower()
            
            critical_errors = parse_logs()["criticalErrors"]
            filtered = [err for err in critical_errors 
                       if search_term in err["message"].lower()]
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(filtered).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def get_html(self):
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log Analytics Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            margin: 0;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-title {
            font-size: 16px;
            color: #7f8c8d;
            margin: 0 0 10px 0;
        }
        .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .chart-title {
            margin: 0 0 20px 0;
            color: #2c3e50;
        }
        .chart {
            width: 100%;
            height: 300px;
        }
        .search-container {
            display: flex;
            margin-bottom: 20px;
        }
        #searchInput {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px 0 0 4px;
            font-size: 16px;
        }
        #searchButton {
            padding: 10px 15px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
            font-size: 16px;
        }
        #searchButton:hover {
            background: #2980b9;
        }
        .filter-container {
            margin-bottom: 20px;
            text-align: right;
        }
        .filter-btn {
            margin-left: 10px;
            padding: 8px 16px;
            background: #ecf0f1;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .filter-btn.active {
            background: #3498db;
            color: white;
            border-color: #3498db;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #34495e;
            color: white;
            font-weight: 600;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .log-critical {
            color: #e74c3c;
            font-weight: 500;
        }
        .no-results {
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
        }
        .pie-chart {
            width: 200px;
            height: 200px;
            position: relative;
            margin: 0 auto;
        }
        .pie-slice {
            position: absolute;
            width: 100%;
            height: 100%;
            clip: rect(0px, 200px, 200px, 100px);
            -webkit-transform-origin: 100% 100%;
            transform-origin: 100% 100%;
            border-radius: 100%;
        }
        .legend {
            display: flex;
            justify-content: center;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin: 0 10px;
        }
        .legend-color {
            width: 12px;
            height: 12px;
            margin-right: 5px;
            border-radius: 2px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Log Analytics Dashboard</h1>
            <p>Real-time analysis of server logs</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">Total Logs</div>
                <div id="totalLogs" class="stat-value">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Errors Today</div>
                <div id="errorCount" class="stat-value">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Critical Issues</div>
                <div id="criticalCount" class="stat-value">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Most Active Hour</div>
                <div id="peakHour" class="stat-value">--:00</div>
            </div>
        </div>

        <div class="chart-container">
            <h2 class="chart-title">Log Level Distribution</h2>
            <div class="pie-chart" id="levelChart"></div>
            <div class="legend" id="levelLegend"></div>
        </div>

        <div class="chart-container">
            <h2 class="chart-title">Errors Over Time (Last 24 Hours)</h2>
            <div class="chart">
                <svg id="timelineChart" width="100%" height="100%">
                    <g id="chart-lines"></g>
                    <g id="chart-bars"></g>
                    <g id="chart-labels"></g>
                </svg>
            </div>
        </div>

        <div class="chart-container">
            <h2 class="chart-title">Most Common Error Messages</h2>
            <ul id="commonErrorsList"></ul>
        </div>

        <div class="chart-container">
            <h2 class="chart-title">Critical Errors</h2>
            <div class="search-container">
                <input type="text" id="searchInput" placeholder="Search critical errors...">
                <button id="searchButton">Search</button>
            </div>
            <div class="filter-container">
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="error">Errors</button>
                <button class="filter-btn" data-filter="critical">Critical</button>
            </div>
            <table id="criticalTable">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Error Message</th>
                    </tr>
                </thead>
                <tbody id="criticalTbody">
                    <tr><td colspan="2" class="no-results">Loading critical errors...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Colors for log levels
        const levelColors = {
            'INFO': '#3498db',
            'WARN': '#f39c12',
            'ERROR': '#e74c3c',
            'CRITICAL': '#c0392b'
        };

        // Fetch data from API
        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                return await response.json();
            } catch (error) {
                console.error('Error fetching data:', error);
                return null;
            }
        }

        // Update summary statistics
        function updateStats(data) {
            const total = Object.values(data.levelPercentages).reduce((a, b) => a + b, 0);
            document.getElementById('totalLogs').textContent = Math.round(total);
            
            const errorCount = (data.levelPercentages.ERROR || 0) + (data.levelPercentages.CRITICAL || 0);
            document.getElementById('errorCount').textContent = Math.round(errorCount);
            
            document.getElementById('criticalCount').textContent = data.criticalErrors.length;
            
            // Find peak hour
            const hourlyEntries = Object.entries(data.hourlyErrors);
            if (hourlyEntries.length > 0) {
                const peak = hourlyEntries.reduce((a, b) => a[1] > b[1] ? a : b);
                document.getElementById('peakHour').textContent = peak[0].substr(-5);
            }
        }

        // Create pie chart for log levels
        function createPieChart(data) {
            const chart = document.getElementById('levelChart');
            const legend = document.getElementById('levelLegend');
            chart.innerHTML = '';
            legend.innerHTML = '';
            
            const total = Object.values(data.levelPercentages).reduce((a, b) => a + b, 0);
            if (total === 0) return;
            
            let cumulativePercent = 0;
            
            Object.entries(data.levelPercentages).forEach(([level, percent]) => {
                if (percent <= 0) return;
                
                const startAngle = cumulativePercent * 360;
                const endAngle = (cumulativePercent + (percent/total)) * 360;
                cumulativePercent += (percent/total);
                
                // Convert to radians
                const startRad = (startAngle - 90) * Math.PI / 180;
                const endRad = (endAngle - 90) * Math.PI / 180;
                
                // Calculate points
                const x1 = 100 + 100 * Math.cos(startRad);
                const y1 = 100 + 100 * Math.sin(startRad);
                const x2 = 100 + 100 * Math.cos(endRad);
                const y2 = 100 + 100 * Math.sin(endRad);
                
                // Determine if the slice is more than half the circle
                const largeArc = (endAngle - startAngle) > 180 ? 1 : 0;
                
                // Create SVG path
                const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                path.setAttribute("d", [
                    "M 100 100", // Move to center
                    "L", x1, y1, // Line to start point
                    "A 100 100 0", largeArc, "1", x2, y2, // Arc to end point
                    "Z" // Close path
                ].join(' '));
                path.setAttribute("fill", levelColors[level] || "#95a5a6");
                path.setAttribute("stroke", "white");
                path.setAttribute("stroke-width", "2");
                chart.appendChild(path);
                
                // Add legend item
                const legendItem = document.createElement('div');
                legendItem.className = 'legend-item';
                legendItem.innerHTML = `
                    <div class="legend-color" style="background-color: ${levelColors[level] || "#95a5a6"}"></div>
                    ${level} (${percent.toFixed(1)}%)
                `;
                legend.appendChild(legendItem);
            });
        }

        // Create timeline chart for hourly errors
        function createTimelineChart(data) {
            const svg = document.getElementById('timelineChart');
            const lines = document.getElementById('chart-lines');
            const bars = document.getElementById('chart-bars');
            const labels = document.getElementById('chart-labels');
            
            lines.innerHTML = '';
            bars.innerHTML = '';
            labels.innerHTML = '';
            
            const width = svg.clientWidth;
            const height = 250;
            const padding = 50;
            
            const hours = Object.keys(data.hourlyErrors);
            if (hours.length === 0) return;
            
            const maxErrors = Math.max(...Object.values(data.hourlyErrors), 1);
            
            // Scale factors
            const xScale = (width - 2 * padding) / Math.max(hours.length - 1, 1);
            const yScale = (height - 2 * padding) / maxErrors;
            
            // Draw axes
            const xAxis = document.createElementNS("http://www.w3.org/2000/svg", "line");
            xAxis.setAttribute("x1", padding);
            xAxis.setAttribute("y1", height - padding);
            xAxis.setAttribute("x2", width - padding);
            xAxis.setAttribute("y2", height - padding);
            xAxis.setAttribute("stroke", "#95a5a6");
            lines.appendChild(xAxis);
            
            const yAxis = document.createElementNS("http://www.w3.org/2000/svg", "line");
            yAxis.setAttribute("x1", padding);
            yAxis.setAttribute("y1", padding);
            yAxis.setAttribute("x2", padding);
            yAxis.setAttribute("y2", height - padding);
            yAxis.setAttribute("stroke", "#95a5a6");
            lines.appendChild(yAxis);
            
            // Draw bars and labels
            hours.forEach((hour, i) => {
                const x = padding + i * xScale;
                const errors = data.hourlyErrors[hour];
                const barHeight = errors * yScale;
                
                // Bar
                const bar = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                bar.setAttribute("x", x - 10);
                bar.setAttribute("y", height - padding - barHeight);
                bar.setAttribute("width", 20);
                bar.setAttribute("height", barHeight);
                bar.setAttribute("fill", "#3498db");
                bars.appendChild(bar);
                
                // Label
                if (i % Math.ceil(hours.length / 10) === 0 || i === hours.length - 1) {
                    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
                    label.setAttribute("x", x);
                    label.setAttribute("y", height - padding + 20);
                    label.setAttribute("text-anchor", "middle");
                    label.setAttribute("font-size", "12");
                    label.setAttribute("fill", "#666");
                    label.textContent = hour.substr(-5);  // HH:00
                    labels.appendChild(label);
                }
            });
            
            // Y-axis labels
            for (let i = 0; i <= 5; i++) {
                const value = Math.round((maxErrors * i) / 5);
                const y = height - padding - (value * yScale);
                
                const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                line.setAttribute("x1", padding - 5);
                line.setAttribute("y1", y);
                line.setAttribute("x2", padding);
                line.setAttribute("y2", y);
                line.setAttribute("stroke", "#95a5a6");
                lines.appendChild(line);
                
                const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
                label.setAttribute("x", padding - 10);
                label.setAttribute("y", y + 4);
                label.setAttribute("text-anchor", "end");
                label.setAttribute("font-size", "12");
                label.setAttribute("fill", "#666");
                label.textContent = value;
                labels.appendChild(label);
            }
        }

        // Update common errors list
        function updateCommonErrors(data) {
            const list = document.getElementById('commonErrorsList');
            list.innerHTML = '';
            
            data.commonErrors.forEach(item => {
                const li = document.createElement('li');
                li.style.padding = '8px 0';
                li.style.borderBottom = '1px solid #eee';
                li.innerHTML = `<strong>${item.count}</strong> occurrences: ${item.message}`;
                list.appendChild(li);
            });
            
            if (data.commonErrors.length === 0) {
                const li = document.createElement('li');
                li.style.padding = '15px';
                li.style.color = '#7f8c8d';
                li.style.textAlign = 'center';
                li.textContent = 'No common errors found';
                list.appendChild(li);
            }
        }

        // Update critical errors table
        function updateCriticalTable(errors) {
            const tbody = document.getElementById('criticalTbody');
            
            if (errors.length === 0) {
                tbody.innerHTML = '<tr><td colspan="2" class="no-results">No critical errors found</td></tr>';
                return;
            }
            
            tbody.innerHTML = '';
            errors.forEach(error => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${error.timestamp}</td>
                    <td class="log-critical">${error.message}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // Search critical errors
        async function searchCriticalErrors(query) {
            try {
                const response = await fetch(`/api/critical?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                updateCriticalTable(data);
            } catch (error) {
                console.error('Error searching critical errors:', error);
            }
        }

        // Initialize dashboard
        async function initDashboard() {
            const data = await fetchData();
            if (!data) return;
            
            updateStats(data);
            createPieChart(data);
            createTimelineChart(data);
            updateCommonErrors(data);
            updateCriticalTable(data.criticalErrors);
            
            // Setup search
            document.getElementById('searchButton').addEventListener('click', () => {
                const query = document.getElementById('searchInput').value;
                searchCriticalErrors(query);
            });
            
            document.getElementById('searchInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const query = document.getElementById('searchInput').value;
                    searchCriticalErrors(query);
                }
            });
            
            // Setup filters
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    // Remove active class from all buttons
                    document.querySelectorAll('.filter-btn').forEach(b => {
                        b.classList.remove('active');
                    });
                    
                    // Add active class to clicked button
                    btn.classList.add('active');
                    
                    const filter = btn.getAttribute('data-filter');
                    let filteredData = data.criticalErrors;
                    
                    // In a real app, we'd have more filter types
                    // For now, just show all critical errors
                    updateCriticalTable(filteredData);
                });
            });
        }

        // Refresh data periodically
        function startAutoRefresh() {
            initDashboard();
            setInterval(() => {
                fetchData().then(data => {
                    if (data) {
                        updateStats(data);
                        createPieChart(data);
                        createTimelineChart(data);
                    }
                });
            }, 30000); // Refresh every 30 seconds
        }

        // Start the dashboard when page loads
        window.onload = startAutoRefresh;
    </script>
</body>
</html>
        """

def main():
    # Check if log file exists, generate if not
    if not os.path.exists(LOG_FILE):
        print(f"{LOG_FILE} not found. Generating fake log data...")
        generate_log_data(1000)
        print(f"Generated {LOG_FILE} with 1000 lines of fake log data.")
    
    # Start HTTP server
    server = HTTPServer(('', PORT), DashboardHandler)
    print(f"\nLog Analytics Dashboard started!")
    print(f"Server running on http://localhost:{PORT}")
    print(f"Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == "__main__":
    main()