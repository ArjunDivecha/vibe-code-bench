import os
import random
import datetime
import json
import collections
import http.server
import socketserver
import urllib.parse
import re
import html

# Generate fake log data
def generate_log_data():
    log_levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL']
    components = ['Database', 'Auth', 'API', 'Frontend', 'Backend', 'Cache']
    messages = {
        'INFO': ['User logged in', 'Data retrieved successfully', 'Cache updated', 'Request processed'],
        'WARN': ['Deprecated API usage', 'High memory usage detected', 'Slow response time', 'Retry attempt'],
        'ERROR': ['Connection timeout', 'Failed to parse JSON', 'Database connection failed', 'Invalid input'],
        'CRITICAL': ['System crash', 'Data corruption detected', 'Security breach attempt', 'Service unavailable']
    }
    
    with open('server.log', 'w') as f:
        for _ in range(1000):
            timestamp = datetime.datetime.now() - datetime.timedelta(
                hours=random.randint(0, 24),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            level = random.choices(log_levels, weights=[50, 25, 20, 5])[0]
            component = random.choice(components)
            message = random.choice(messages[level])
            log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {component}: {message}\n"
            f.write(log_line)

# Parse log file
def parse_log_file():
    if not os.path.exists('server.log'):
        generate_log_data()
    
    log_levels = collections.defaultdict(int)
    errors_per_hour = collections.defaultdict(int)
    error_messages = collections.defaultdict(int)
    critical_errors = []
    
    with open('server.log', 'r') as f:
        for line in f:
            # Extract timestamp, level, and message
            match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (.+)', line)
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                # Count log levels
                log_levels[level] += 1
                
                # Count errors per hour
                if level in ['ERROR', 'CRITICAL']:
                    hour = timestamp.replace(minute=0, second=0, microsecond=0)
                    errors_per_hour[hour] += 1
                    
                    # Track error messages
                    error_messages[message] += 1
                    
                    # Store critical errors
                    if level == 'CRITICAL':
                        critical_errors.append({
                            'timestamp': timestamp_str,
                            'message': message
                        })
    
    # Calculate percentages
    total_logs = sum(log_levels.values())
    level_percentages = {level: (count / total_logs) * 100 for level, count in log_levels.items()}
    
    # Sort error messages by frequency
    common_errors = sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'level_percentages': level_percentages,
        'errors_per_hour': errors_per_hour,
        'common_errors': common_errors,
        'critical_errors': critical_errors
    }

# HTTP request handler
class LogDashboardHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)
        
        if path == '/':
            self.serve_dashboard()
        elif path == '/api/data':
            self.serve_api_data()
        elif path == '/api/critical-errors':
            self.serve_critical_errors(query)
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html_content = '''
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
            background-color: #f5f7fa;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #ddd;
        }
        h1 {
            color: #2c3e50;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .card h2 {
            margin-top: 0;
            color: #3498db;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .chart-container {
            height: 300px;
            position: relative;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        tr:hover {
            background-color: #f5f7fa;
        }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .filter-control {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        select, input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            padding: 8px 15px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #2980b9;
        }
        .error-table-container {
            max-height: 500px;
            overflow-y: auto;
        }
        .bar {
            fill: #3498db;
        }
        .bar:hover {
            fill: #2980b9;
        }
        .axis {
            stroke: #333;
            stroke-width: 1;
        }
        .axis-label {
            font-size: 12px;
            fill: #666;
        }
        .pie-slice {
            stroke: white;
            stroke-width: 2;
        }
        .legend {
            font-size: 12px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        .legend-color {
            width: 15px;
            height: 15px;
            margin-right: 8px;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Log Analytics Dashboard</h1>
        </header>
        
        <div class="dashboard">
            <div class="card">
                <h2>Log Level Distribution</h2>
                <div class="chart-container">
                    <svg id="pie-chart" width="100%" height="100%"></svg>
                </div>
            </div>
            
            <div class="card">
                <h2>Errors Over Time</h2>
                <div class="chart-container">
                    <svg id="bar-chart" width="100%" height="100%"></svg>
                </div>
            </div>
            
            <div class="card">
                <h2>Most Common Errors</h2>
                <table id="common-errors-table">
                    <thead>
                        <tr>
                            <th>Error Message</th>
                            <th>Count</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
        
        <div class="card">
            <h2>Critical Errors</h2>
            <div class="controls">
                <div class="filter-control">
                    <label for="level-filter">Level:</label>
                    <select id="level-filter">
                        <option value="all">All</option>
                        <option value="ERROR">Error</option>
                        <option value="CRITICAL">Critical</option>
                    </select>
                </div>
                <div class="filter-control">
                    <label for="search-input">Search:</label>
                    <input type="text" id="search-input" placeholder="Search messages...">
                </div>
                <button id="apply-filters">Apply Filters</button>
            </div>
            <div class="error-table-container">
                <table id="critical-errors-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Fetch data from API
        async function fetchData() {
            const response = await fetch('/api/data');
            return await response.json();
        }
        
        // Fetch critical errors with filters
        async function fetchCriticalErrors(level = 'all', search = '') {
            const response = await fetch(`/api/critical-errors?level=${level}&search=${encodeURIComponent(search)}`);
            return await response.json();
        }
        
        // Render pie chart
        function renderPieChart(data) {
            const svg = document.getElementById('pie-chart');
            svg.innerHTML = '';
            
            const width = svg.clientWidth;
            const height = svg.clientHeight;
            const radius = Math.min(width, height) / 2 - 20;
            
            const colors = {
                'INFO': '#2ecc71',
                'WARN': '#f39c12',
                'ERROR': '#e74c3c',
                'CRITICAL': '#8e44ad'
            };
            
            const total = Object.values(data).reduce((sum, val) => sum + val, 0);
            let startAngle = 0;
            
            // Add legend
            const legend = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            legend.setAttribute('transform', `translate(${width - 150}, 20)`);
            
            Object.entries(data).forEach(([level, percentage], index) => {
                // Draw slice
                const angle = (percentage / 100) * 2 * Math.PI;
                const endAngle = startAngle + angle;
                
                const x1 = width/2 + radius * Math.cos(startAngle);
                const y1 = height/2 + radius * Math.sin(startAngle);
                const x2 = width/2 + radius * Math.cos(endAngle);
                const y2 = height/2 + radius * Math.sin(endAngle);
                
                const largeArcFlag = angle > Math.PI ? 1 : 0;
                
                const pathData = [
                    `M ${width/2} ${height/2}`,
                    `L ${x1} ${y1}`,
                    `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
                    'Z'
                ].join(' ');
                
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', pathData);
                path.setAttribute('class', 'pie-slice');
                path.setAttribute('fill', colors[level]);
                svg.appendChild(path);
                
                // Add legend item
                const legendItem = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                legendItem.setAttribute('transform', `translate(0, ${index * 20})`);
                
                const legendColor = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                legendColor.setAttribute('x', 0);
                legendColor.setAttribute('y', 0);
                legendColor.setAttribute('width', 15);
                legendColor.setAttribute('height', 15);
                legendColor.setAttribute('fill', colors[level]);
                
                const legendText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                legendText.setAttribute('x', 20);
                legendText.setAttribute('y', 12);
                legendText.setAttribute('class', 'legend');
                legendText.textContent = `${level}: ${percentage.toFixed(1)}%`;
                
                legendItem.appendChild(legendColor);
                legendItem.appendChild(legendText);
                legend.appendChild(legendItem);
                
                startAngle = endAngle;
            });
            
            svg.appendChild(legend);
        }
        
        // Render bar chart
        function renderBarChart(data) {
            const svg = document.getElementById('bar-chart');
            svg.innerHTML = '';
            
            const width = svg.clientWidth;
            const height = svg.clientHeight;
            const margin = { top: 20, right: 20, bottom: 50, left: 50 };
            const chartWidth = width - margin.left - margin.right;
            const chartHeight = height - margin.top - margin.bottom;
            
            // Create chart group
            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('transform', `translate(${margin.left}, ${margin.top})`);
            
            // Parse data
            const entries = Object.entries(data).map(([date, count]) => ({
                date: new Date(date),
                count: count
            })).sort((a, b) => a.date - b.date);
            
            if (entries.length === 0) return;
            
            // Scales
            const xMax = entries.length - 1;
            const yMax = Math.max(...entries.map(d => d.count));
            
            // Draw bars
            const barWidth = chartWidth / entries.length - 2;
            
            entries.forEach((d, i) => {
                const x = (i * chartWidth / entries.length);
                const barHeight = (d.count / yMax) * chartHeight;
                const y = chartHeight - barHeight;
                
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', x);
                rect.setAttribute('y', y);
                rect.setAttribute('width', barWidth);
                rect.setAttribute('height', barHeight);
                rect.setAttribute('class', 'bar');
                g.appendChild(rect);
                
                // Add date label
                if (i % Math.ceil(entries.length / 10) === 0) {
                    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    text.setAttribute('x', x + barWidth / 2);
                    text.setAttribute('y', chartHeight + 20);
                    text.setAttribute('text-anchor', 'middle');
                    text.setAttribute('class', 'axis-label');
                    text.textContent = d.date.getHours() + ':00';
                    g.appendChild(text);
                }
            });
            
            // Draw axes
            const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            xAxis.setAttribute('x1', 0);
            xAxis.setAttribute('y1', chartHeight);
            xAxis.setAttribute('x2', chartWidth);
            xAxis.setAttribute('y2', chartHeight);
            xAxis.setAttribute('class', 'axis');
            g.appendChild(xAxis);
            
            const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            yAxis.setAttribute('x1', 0);
            yAxis.setAttribute('y1', 0);
            yAxis.setAttribute('x2', 0);
            yAxis.setAttribute('y2', chartHeight);
            yAxis.setAttribute('class', 'axis');
            g.appendChild(yAxis);
            
            // Y-axis labels
            for (let i = 0; i <= 5; i++) {
                const y = chartHeight - (i * chartHeight / 5);
                const value = Math.round(i * yMax / 5);
                
                const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                tick.setAttribute('x1', -5);
                tick.setAttribute('y1', y);
                tick.setAttribute('x2', 0);
                tick.setAttribute('y2', y);
                tick.setAttribute('class', 'axis');
                g.appendChild(tick);
                
                const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                label.setAttribute('x', -10);
                label.setAttribute('y', y + 5);
                label.setAttribute('text-anchor', 'end');
                label.setAttribute('class', 'axis-label');
                label.textContent = value;
                g.appendChild(label);
            }
            
            svg.appendChild(g);
        }
        
        // Render common errors table
        function renderCommonErrors(data) {
            const tbody = document.querySelector('#common-errors-table tbody');
            tbody.innerHTML = '';
            
            data.forEach(([message, count]) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${htmlEscape(message)}</td>
                    <td>${count}</td>
                `;
                tbody.appendChild(row);
            });
        }
        
        // Render critical errors table
        function renderCriticalErrors(data) {
            const tbody = document.querySelector('#critical-errors-table tbody');
            tbody.innerHTML = '';
            
            data.forEach(error => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${htmlEscape(error.timestamp)}</td>
                    <td>${htmlEscape(error.message)}</td>
                `;
                tbody.appendChild(row);
            });
        }
        
        // Utility function for escaping HTML
        function htmlEscape(str) {
            return str.replace(/&/g, '&amp;')
                     .replace(/</g, '&lt;')
                     .replace(/>/g, '&gt;')
                     .replace(/"/g, '&quot;')
                     .replace(/'/g, '&#39;');
        }
        
        // Initialize dashboard
        async function initDashboard() {
            const data = await fetchData();
            renderPieChart(data.level_percentages);
            renderBarChart(data.errors_per_hour);
            renderCommonErrors(data.common_errors);
            renderCriticalErrors(data.critical_errors);
            
            // Set up event listeners for filters
            document.getElementById('apply-filters').addEventListener('click', async () => {
                const level = document.getElementById('level-filter').value;
                const search = document.getElementById('search-input').value;
                const errors = await fetchCriticalErrors(level, search);
                renderCriticalErrors(errors);
            });
            
            // Allow Enter key to trigger search
            document.getElementById('search-input').addEventListener('keyup', (e) => {
                if (e.key === 'Enter') {
                    document.getElementById('apply-filters').click();
                }
            });
        }
        
        // Start the dashboard
        document.addEventListener('DOMContentLoaded', initDashboard);
    </script>
</body>
</html>
        '''
        
        self.wfile.write(html_content.encode())
    
    def serve_api_data(self):
        data = parse_log_file()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def serve_critical_errors(self, query):
        # Get all data
        data = parse_log_file()
        errors = data['critical_errors'].copy()
        
        # Apply filters
        level_filter = query.get('level', ['all'])[0]
        search_filter = query.get('search', [''])[0]
        
        if level_filter != 'all':
            # In this implementation, all critical errors are CRITICAL level
            # For a real implementation with mixed levels, we'd filter here
            pass
            
        if search_filter:
            errors = [e for e in errors if search_filter.lower() in e['message'].lower()]
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(errors, default=str).encode())

# Main function
def main():
    # Parse log file and generate data
    print("Parsing log data...")
    data = parse_log_file()
    
    # Start HTTP server
    port = 8000
    handler = LogDashboardHandler
    httpd = socketserver.TCPServer(("", port), handler)
    
    print(f"Log Analytics Dashboard running at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == "__main__":
    main()