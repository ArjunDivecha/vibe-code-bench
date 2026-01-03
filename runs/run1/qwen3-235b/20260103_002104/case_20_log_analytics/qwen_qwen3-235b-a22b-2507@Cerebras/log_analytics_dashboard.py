import os
import sys
import json
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import re

LOG_FILE = "server.log"
PORT = 8000

# Log levels to generate and analyze
LOG_LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]
COMMON_ERRORS = [
    "Connection timeout",
    "Database unreachable",
    "Authentication failed",
    "Permission denied",
    "Invalid input",
    "Resource not found",
    "Server overload",
    "Configuration error"
]

def generate_fake_log():
    """Generate 1000 lines of fake log data if log file doesn't exist"""
    if os.path.exists(LOG_FILE):
        return
    
    print(f"{LOG_FILE} not found. Generating fake log data...")
    with open(LOG_FILE, "w") as f:
        current_time = datetime.now() - timedelta(hours=24)
        
        for _ in range(1000):
            # Randomly adjust time (mostly forward, sometimes back)
            current_time += timedelta(minutes=random.randint(-5, 30))
            timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Higher chance of INFO, decreasing for higher severity
            level = random.choices(LOG_LEVELS, weights=[60, 25, 10, 5])[0]
            
            # Generate message based on level
            if level in ["ERROR", "CRITICAL"]:
                message = random.choice(COMMON_ERRORS)
                if random.random() > 0.5:
                    message += f" on module {random.randint(1, 10)}"
            else:
                message = f"Operation {random.randint(1000, 9999)} completed successfully"
            
            # Add some variation
            if random.random() > 0.7:
                message += f" [PID:{random.randint(1000, 9999)}]"
                
            log_line = f"{timestamp} [{level}] {message}\n"
            f.write(log_line)
    
    print(f"Generated {LOG_FILE} with 1000 log entries.")

def parse_logs():
    """Parse log file and extract analytics"""
    if not os.path.exists(LOG_FILE):
        return {}
    
    log_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(INFO|WARN|ERROR|CRITICAL)\] (.+)')
    
    logs = []
    level_counts = Counter()
    hourly_errors = defaultdict(int)
    error_messages = []
    
    with open(LOG_FILE, "r") as f:
        for line in f:
            match = log_pattern.match(line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                log_entry = {
                    "timestamp": timestamp_str,
                    "level": level,
                    "message": message
                }
                logs.append(log_entry)
                
                level_counts[level] += 1
                
                # Track errors by hour
                if level in ["ERROR", "CRITICAL"]:
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    hourly_errors[hour_key] += 1
                    if level == "CRITICAL":
                        error_messages.append(message)
    
    # Calculate percentages
    total_logs = sum(level_counts.values())
    level_percentages = {
        level: (count / total_logs) * 100 if total_logs > 0 else 0
        for level, count in level_counts.items()
    }
    
    # Most common error messages (CRITICAL only)
    common_errors = Counter(error_messages).most_common(10)
    
    # Prepare hourly timeline (last 24 hours)
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=23)
    timeline = []
    
    current = start_time
    while current <= end_time:
        hour_key = current.strftime("%Y-%m-%d %H:00")
        timeline.append({
            "time": hour_key,
            "count": hourly_errors.get(hour_key, 0)
        })
        current += timedelta(hours=1)
    
    # Filter CRITICAL logs for table
    critical_logs = [log for log in logs if log["level"] == "CRITICAL"]
    
    return {
        "levelPercentages": level_percentages,
        "errorTimeline": timeline,
        "commonErrors": [{"message": msg, "count": count} for msg, count in common_errors],
        "criticalLogs": critical_logs
    }

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        
        if self.path == "/":
            self.serve_dashboard()
        elif self.path == "/api/data":
            self.serve_api_data()
        elif self.path.startswith("/api/search"):
            self.serve_search_results(parsed_url)
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html = """
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
            padding: 20px 0;
            background-color: #2c3e50;
            color: white;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            margin: 0;
        }
        .controls {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .filter {
            display: flex;
            align-items: center;
        }
        .filter label {
            margin-right: 10px;
            font-weight: bold;
        }
        .filter select {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .search {
            display: flex;
            width: 40%;
        }
        .search input {
            flex-grow: 1;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px 0 0 4px;
            font-size: 14px;
        }
        .search button {
            padding: 8px 15px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
            font-size: 14px;
        }
        .search button:hover {
            background-color: #2980b9;
        }
        .dashboard {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            .controls {
                flex-direction: column;
            }
            .search {
                width: 100%;
                margin-top: 10px;
            }
        }
        .card {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card h2 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            font-size: 18px;
        }
        .pie-chart {
            width: 100%;
            height: 250px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .timeline {
            width: 100%;
            height: 250px;
        }
        .error-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .error-table th, .error-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .error-table th {
            background-color: #f2f2f2;
            font-weight: bold;
            color: #2c3e50;
        }
        .error-table tr:hover {
            background-color: #f5f5f5;
        }
        .common-errors-list {
            list-style: none;
            padding: 0;
        }
        .common-errors-list li {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
        }
        .common-errors-list li:last-child {
            border-bottom: none;
        }
        .count {
            background-color: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
        }
        .level-info { color: #16a085; }
        .level-warn { color: #f39c12; }
        .level-error { color: #e74c3c; }
        .level-critical { color: #c0392b; }
        .no-results {
            text-align: center;
            color: #7f8c8d;
            padding: 20px;
            font-style: italic;
        }
        footer {
            text-align: center;
            margin-top: 30px;
            color: #7f8c8d;
            font-size: 14px;
        }
        .legend {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 10px;
            gap: 15px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            font-size: 14px;
        }
        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 5px;
            display: inline-block;
        }
        .legend-info { background-color: #16a085; }
        .legend-warn { background-color: #f39c12; }
        .legend-error { background-color: #e74c3c; }
        .legend-critical { background-color: #c0392b; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Log Analytics Dashboard</h1>
            <p>Real-time analysis of server logs</p>
        </header>

        <div class="controls">
            <div class="filter">
                <label for="levelFilter">Filter by Level:</label>
                <select id="levelFilter">
                    <option value="All">All Levels</option>
                    <option value="INFO">INFO</option>
                    <option value="WARN">WARN</option>
                    <option value="ERROR">ERROR</option>
                    <option value="CRITICAL">CRITICAL</option>
                </select>
            </div>
            <div class="search">
                <input type="text" id="searchInput" placeholder="Search critical errors...">
                <button onclick="searchCriticalErrors()">Search</button>
            </div>
        </div>

        <div class="dashboard">
            <div class="card">
                <h2>Log Level Distribution</h2>
                <div class="pie-chart" id="pieChart">
                    <!-- Pie chart will be rendered here -->
                </div>
                <div class="legend">
                    <div class="legend-item"><span class="legend-color legend-info"></span> INFO</div>
                    <div class="legend-item"><span class="legend-color legend-warn"></span> WARN</div>
                    <div class="legend-item"><span class="legend-color legend-error"></span> ERROR</div>
                    <div class="legend-item"><span class="legend-color legend-critical"></span> CRITICAL</div>
                </div>
            </div>

            <div class="card">
                <h2>Errors per Hour (Last 24h)</h2>
                <svg class="timeline" id="timelineChart">
                    <!-- Timeline chart will be rendered here -->
                </svg>
            </div>

            <div class="card">
                <h2>Most Common Critical Errors</h2>
                <ul class="common-errors-list" id="commonErrorsList">
                    <!-- Will be populated by JS -->
                </ul>
            </div>

            <div class="card">
                <h2>Critical Errors Table</h2>
                <div id="criticalTableContainer">
                    <table class="error-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Message</th>
                            </tr>
                        </thead>
                        <tbody id="criticalErrorsBody">
                            <!-- Will be populated by JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <footer>
            <p>Log Analytics Dashboard &copy; <span id="currentYear"></span> | 
               Data updated: <span id="lastUpdated"></span></p>
        </footer>
    </div>

    <script>
        // Global variables
        let analyticsData = {};
        let filteredCriticalLogs = [];
        
        // Initialize the dashboard
        window.onload = function() {
            document.getElementById('currentYear').textContent = new Date().getFullYear();
            updateLastUpdated();
            fetchData();
            setInterval(fetchData, 30000); // Refresh data every 30 seconds
        };
        
        // Fetch analytics data from server
        function fetchData() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    analyticsData = data;
                    filteredCriticalLogs = data.criticalLogs || [];
                    renderDashboard();
                    updateLastUpdated();
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                });
        }
        
        // Update the last updated timestamp
        function updateLastUpdated() {
            const now = new Date();
            const options = { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            };
            document.getElementById('lastUpdated').textContent = now.toLocaleDateString('en-US', options);
        }
        
        // Render all dashboard components
        function renderDashboard() {
            renderPieChart();
            renderTimelineChart();
            renderCommonErrors();
            renderCriticalErrorsTable();
            setupEventListeners();
        }
        
        // Render pie chart using SVG
        function renderPieChart() {
            const container = document.getElementById('pieChart');
            const percentages = analyticsData.levelPercentages || {};
            
            const colors = {
                'INFO': '#16a085',
                'WARN': '#f39c12',
                'ERROR': '#e74c3c',
                'CRITICAL': '#c0392b'
            };
            
            // Clear previous chart
            container.innerHTML = '';
            
            if (Object.keys(percentages).length === 0) {
                container.innerHTML = '<p class="no-results">No data available</p>';
                return;
            }
            
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('width', '100%');
            svg.setAttribute('height', '100%');
            svg.setAttribute('viewBox', '0 0 100 100');
            
            let startAngle = 0;
            
            // Create pie slices
            Object.entries(percentages).forEach(([level, percentage]) => {
                if (percentage <= 0) return;
                
                const endAngle = startAngle + (percentage / 100) * 360;
                const largeArc = percentage > 50 ? 1 : 0;
                
                // Convert to radians
                const x1 = 50 + 40 * Math.cos(startAngle * Math.PI / 180);
                const y1 = 50 + 40 * Math.sin(startAngle * Math.PI / 180);
                const x2 = 50 + 40 * Math.cos(endAngle * Math.PI / 180);
                const y2 = 50 + 40 * Math.sin(endAngle * Math.PI / 180);
                
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', `M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`);
                path.setAttribute('fill', colors[level] || '#95a5a6');
                path.setAttribute('stroke', 'white');
                path.setAttribute('stroke-width', '2');
                
                // Add tooltip
                const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
                title.textContent = `${level}: ${percentage.toFixed(1)}%`;
                path.appendChild(title);
                
                svg.appendChild(path);
                
                startAngle = endAngle;
            });
            
            // Add center circle for donut effect
            const centerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            centerCircle.setAttribute('cx', '50');
            centerCircle.setAttribute('cy', '50');
            centerCircle.setAttribute('r', '25');
            centerCircle.setAttribute('fill', 'white');
            svg.appendChild(centerCircle);
            
            // Add total count in the center
            const totalCount = Object.values(percentages).reduce((a, b) => a + b, 0);
            if (totalCount > 0) {
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', '50');
                text.setAttribute('y', '55');
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('font-size', '8');
                text.setAttribute('fill', '#333');
                text.textContent = 'Logs';
                svg.appendChild(text);
            }
            
            container.appendChild(svg);
        }
        
        // Render timeline chart using SVG
        function renderTimelineChart() {
            const svg = document.getElementById('timelineChart');
            const data = analyticsData.errorTimeline || [];
            
            // Clear previous content
            svg.innerHTML = '';
            
            if (data.length === 0) {
                svg.parentElement.innerHTML = '<p class="no-results">No error data available</p>';
                return;
            }
            
            // Set up dimensions
            const width = svg.clientWidth || 600;
            const height = 200;
            const padding = { top: 20, right: 30, bottom: 40, left: 50 };
            const chartWidth = width - padding.left - padding.right;
            const chartHeight = height - padding.top - padding.bottom;
            
            // Find max value for scaling
            const maxErrors = Math.max(...data.map(d => d.count), 1);
            
            // Create scale functions
            const xScale = chartWidth / Math.max(data.length - 1, 1);
            const yScale = chartHeight / maxErrors;
            
            // Create the SVG element
            svg.setAttribute('width', width);
            svg.setAttribute('height', height);
            
            // Add axes
            const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            xAxis.setAttribute('transform', `translate(${padding.left}, ${padding.top + chartHeight})`);
            svg.appendChild(xAxis);
            
            const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            yAxis.setAttribute('transform', `translate(${padding.left}, ${padding.top})`);
            svg.appendChild(yAxis);
            
            // Add Y axis line
            const yAxisLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            yAxisLine.setAttribute('x1', '0');
            yAxisLine.setAttribute('y1', '0');
            yAxisLine.setAttribute('x2', '0');
            yAxisLine.setAttribute('y2', chartHeight);
            yAxisLine.setAttribute('stroke', '#ccc');
            yAxis.appendChild(yAxisLine);
            
            // Add X axis line
            const xAxisLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            xAxisLine.setAttribute('x1', '0');
            xAxisLine.setAttribute('y1', '0');
            xAxisLine.setAttribute('x2', chartWidth);
            xAxisLine.setAttribute('y2', '0');
            xAxisLine.setAttribute('stroke', '#ccc');
            xAxis.appendChild(xAxisLine);
            
            // Add Y axis ticks and labels
            const yTicks = 5;
            for (let i = 0; i <= yTicks; i++) {
                const y = chartHeight - (i * chartHeight / yTicks);
                const value = Math.round((i * maxErrors / yTicks));
                
                const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                tick.setAttribute('x1', '-5');
                tick.setAttribute('y1', y);
                tick.setAttribute('x2', '0');
                tick.setAttribute('y2', y);
                tick.setAttribute('stroke', '#ccc');
                yAxis.appendChild(tick);
                
                const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                label.setAttribute('x', '-10');
                label.setAttribute('y', y + 4);
                label.setAttribute('text-anchor', 'end');
                label.setAttribute('font-size', '10');
                label.setAttribute('fill', '#666');
                label.textContent = value;
                yAxis.appendChild(label);
            }
            
            // Format X axis labels (show only hours)
            const formatXLabel = (datetimeStr) => {
                const date = new Date(datetimeStr.replace(' ', 'T'));
                return date.getHours().toString().padStart(2, '0') + ':00';
            };
            
            // Add X axis ticks and labels (show every 3 hours)
            const step = Math.max(Math.floor(data.length / 8), 1);
            for (let i = 0; i < data.length; i += step) {
                const x = i * xScale;
                const label = formatXLabel(data[i].time);
                
                const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                tick.setAttribute('x1', x);
                tick.setAttribute('y1', '0');
                tick.setAttribute('x2', x);
                tick.setAttribute('y2', '5');
                tick.setAttribute('stroke', '#ccc');
                xAxis.appendChild(tick);
                
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', x);
                text.setAttribute('y', '20');
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('font-size', '10');
                text.setAttribute('fill', '#666');
                text.textContent = label;
                xAxis.appendChild(text);
            }
            
            // Create the line graph
            const lineGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            lineGroup.setAttribute('transform', `translate(${padding.left}, ${padding.top})`);
            svg.appendChild(lineGroup);
            
            // Create path for the line
            let pathData = '';
            data.forEach((point, index) => {
                const x = index * xScale;
                const y = chartHeight - (point.count * yScale);
                
                if (index === 0) {
                    pathData += `M ${x} ${y}`;
                } else {
                    pathData += ` L ${x} ${y}`;
                }
            });
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', pathData);
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke', '#3498db');
            path.setAttribute('stroke-width', '2');
            lineGroup.appendChild(path);
            
            // Add circles for each data point
            data.forEach((point, index) => {
                const x = index * xScale;
                const y = chartHeight - (point.count * yScale);
                
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', x);
                circle.setAttribute('cy', y);
                circle.setAttribute('r', '3');
                circle.setAttribute('fill', '#3498db');
                
                // Add tooltip
                const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
                title.textContent = `${point.time}: ${point.count} errors`;
                circle.appendChild(title);
                
                lineGroup.appendChild(circle);
            });
        }
        
        // Render common errors list
        function renderCommonErrors() {
            const list = document.getElementById('commonErrorsList');
            const errors = analyticsData.commonErrors || [];
            
            list.innerHTML = '';
            
            if (errors.length === 0) {
                const li = document.createElement('li');
                li.className = 'no-results';
                li.textContent = 'No common errors found';
                list.appendChild(li);
                return;
            }
            
            errors.forEach(item => {
                const li = document.createElement('li');
                const messageSpan = document.createElement('span');
                messageSpan.textContent = item.message;
                li.appendChild(messageSpan);
                
                const countSpan = document.createElement('span');
                countSpan.className = 'count';
                countSpan.textContent = item.count;
                li.appendChild(countSpan);
                
                list.appendChild(li);
            });
        }
        
        // Render critical errors table
        function renderCriticalErrorsTable() {
            const tbody = document.getElementById('criticalErrorsBody');
            tbody.innerHTML = '';
            
            if (filteredCriticalLogs.length === 0) {
                const tr = document.createElement('tr');
                const td = document.createElement('td');
                td.colSpan = 2;
                td.className = 'no-results';
                td.textContent = 'No critical errors found';
                tr.appendChild(td);
                tbody.appendChild(tr);
                return;
            }
            
            filteredCriticalLogs.forEach(log => {
                const tr = document.createElement('tr');
                
                const timestampTd = document.createElement('td');
                timestampTd.textContent = log.timestamp;
                timestampTd.className = 'level-critical';
                tr.appendChild(timestampTd);
                
                const messageTd = document.createElement('td');
                messageTd.textContent = log.message;
                tr.appendChild(messageTd);
                
                tbody.appendChild(tr);
            });
        }
        
        // Setup event listeners
        function setupEventListeners() {
            // Level filter change
            document.getElementById('levelFilter').onchange = function() {
                const filterValue = this.value;
                if (filterValue === 'All') {
                    fetchData();  // Reload all data
                } else {
                    // For other filters, we'd implement server-side filtering
                    // But for now, just reload
                    fetchData();
                }
            };
            
            // Search input - allow Enter key
            document.getElementById('searchInput').onkeypress = function(e) {
                if (e.key === 'Enter') {
                    searchCriticalErrors();
                }
            };
        }
        
        // Search critical errors
        function searchCriticalErrors() {
            const query = document.getElementById('searchInput').value.trim().toLowerCase();
            
            if (!query) {
                filteredCriticalLogs = analyticsData.criticalLogs || [];
                renderCriticalErrorsTable();
                return;
            }
            
            // Simple client-side search
            filteredCriticalLogs = (analyticsData.criticalLogs || []).filter(log => 
                log.message.toLowerCase().includes(query)
            );
            
            renderCriticalErrorsTable();
        }
        
        // Make functions available globally
        window.searchCriticalErrors = searchCriticalErrors;
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(html)))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def serve_api_data(self):
        """Serve analytics data as JSON"""
        data = parse_logs()
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def serve_search_results(self, parsed_url):
        """Serve search results for critical errors"""
        query_components = parse_qs(parsed_url.query)
        query = query_components.get('q', [''])[0].lower()
        
        all_critical_logs = parse_logs().get('criticalLogs', [])
        
        if query:
            filtered_logs = [
                log for log in all_critical_logs
                if query in log['message'].lower()
            ]
        else:
            filtered_logs = all_critical_logs
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(filtered_logs).encode('utf-8'))


def main():
    # Generate log file if it doesn't exist
    generate_fake_log()
    
    # Parse logs once to ensure file is readable
    analytics_data = parse_logs()
    print("Log analytics prepared.")
    
    # Start HTTP server
    server = HTTPServer(('localhost', PORT), DashboardHandler)
    print(f"\nLog Analytics Dashboard is running!")
    print(f"Access it at: http://localhost:{PORT}")
    print(f"Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == "__main__":
    main()