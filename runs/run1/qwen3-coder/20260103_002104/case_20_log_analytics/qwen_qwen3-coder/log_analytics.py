import os
import random
import datetime
import json
import http.server
import socketserver
import urllib.parse
import collections
import re
from collections import defaultdict, Counter

# Generate fake log data
def generate_log_data():
    log_levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL']
    log_messages = {
        'INFO': ['User logged in', 'Data processed successfully', 'Cache updated', 'New connection established'],
        'WARN': ['Deprecated API usage', 'Low disk space', 'High memory usage', 'Connection timeout warning'],
        'ERROR': ['Database connection failed', 'Invalid user input', 'File not found', 'Permission denied'],
        'CRITICAL': ['System crash', 'Data corruption detected', 'Security breach attempt', 'Service unavailable']
    }
    
    with open('server.log', 'w') as f:
        start_time = datetime.datetime.now() - datetime.timedelta(days=7)
        for i in range(1000):
            timestamp = start_time + datetime.timedelta(minutes=random.randint(0, 7*24*60))
            level = random.choices(log_levels, weights=[50, 25, 20, 5])[0]
            message = random.choice(log_messages[level])
            f.write(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}\n")

# Parse log file
def parse_log_file():
    if not os.path.exists('server.log'):
        generate_log_data()
    
    with open('server.log', 'r') as f:
        lines = f.readlines()
    
    # Count log levels
    level_counts = defaultdict(int)
    errors_per_hour = defaultdict(int)
    critical_errors = []
    error_messages = []
    
    for line in lines:
        # Extract timestamp, level and message
        match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (.*)', line)
        if match:
            timestamp_str, level, message = match.groups()
            timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            level_counts[level] += 1
            
            if level in ['ERROR', 'CRITICAL']:
                hour_bucket = timestamp.replace(minute=0, second=0)
                errors_per_hour[hour_bucket] += 1
                error_messages.append(message)
                
                if level == 'CRITICAL':
                    critical_errors.append({
                        'timestamp': timestamp_str,
                        'message': message
                    })
    
    total_logs = sum(level_counts.values())
    level_percentages = {level: (count / total_logs) * 100 for level, count in level_counts.items()}
    
    # Get most common error messages
    common_errors = Counter(error_messages).most_common(10)
    
    return {
        'level_percentages': level_percentages,
        'errors_per_hour': dict(errors_per_hour),
        'common_errors': common_errors,
        'critical_errors': critical_errors
    }

# Custom HTTP handler
class LogDashboardHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.serve_dashboard()
        elif path == '/api/data':
            self.serve_api_data()
        elif path == '/api/critical':
            self.serve_critical_errors()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Log Analytics Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .dashboard {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .chart-container {
            height: 300px;
            position: relative;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .filters {
            margin: 20px 0;
            display: flex;
            gap: 10px;
        }
        button {
            padding: 8px 16px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button.active {
            background-color: #0056b3;
        }
        input[type="text"] {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            flex-grow: 1;
        }
        .search-container {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Log Analytics Dashboard</h1>
        
        <div class="dashboard">
            <div class="card">
                <h2>Log Level Distribution</h2>
                <div class="chart-container">
                    <svg id="levelChart" width="100%" height="100%"></svg>
                </div>
            </div>
            
            <div class="card">
                <h2>Errors Over Time</h2>
                <div class="chart-container">
                    <svg id="errorChart" width="100%" height="100%"></svg>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Most Common Error Messages</h2>
            <table id="commonErrorsTable">
                <thead>
                    <tr>
                        <th>Message</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody id="commonErrorsBody">
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>Critical Errors</h2>
            
            <div class="search-container">
                <input type="text" id="searchInput" placeholder="Search critical errors...">
                <button onclick="searchCriticalErrors()">Search</button>
            </div>
            
            <div class="filters">
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="error">Error</button>
                <button class="filter-btn" data-filter="alert">Alert</button>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody id="criticalErrorsBody">
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Global data storage
        let dashboardData = {};
        let filteredCriticalErrors = [];
        
        // Fetch data from API
        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                dashboardData = await response.json();
                renderLevelChart();
                renderErrorChart();
                renderCommonErrors();
                
                // Load critical errors
                const criticalResponse = await fetch('/api/critical');
                const criticalData = await criticalResponse.json();
                dashboardData.criticalErrors = criticalData;
                filteredCriticalErrors = criticalData;
                renderCriticalErrors();
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }
        
        // Render log level distribution chart
        function renderLevelChart() {
            const svg = document.getElementById('levelChart');
            svg.innerHTML = '';
            
            const levels = Object.keys(dashboardData.level_percentages);
            const percentages = Object.values(dashboardData.level_percentages);
            
            const width = svg.clientWidth;
            const height = svg.clientHeight;
            const barWidth = width / levels.length * 0.6;
            const maxPercentage = Math.max(...percentages);
            
            const colors = {
                'INFO': '#28a745',
                'WARN': '#ffc107',
                'ERROR': '#dc3545',
                'CRITICAL': '#dc3545'
            };
            
            levels.forEach((level, i) => {
                const percentage = dashboardData.level_percentages[level];
                const barHeight = (percentage / maxPercentage) * (height - 50);
                const x = (width / levels.length) * i + (width / levels.length - barWidth) / 2;
                const y = height - barHeight - 30;
                
                // Bar
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', x);
                rect.setAttribute('y', y);
                rect.setAttribute('width', barWidth);
                rect.setAttribute('height', barHeight);
                rect.setAttribute('fill', colors[level] || '#007bff');
                svg.appendChild(rect);
                
                // Label
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', x + barWidth / 2);
                text.setAttribute('y', height - 10);
                text.setAttribute('text-anchor', 'middle');
                text.textContent = level;
                svg.appendChild(text);
                
                // Percentage
                const pctText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                pctText.setAttribute('x', x + barWidth / 2);
                pctText.setAttribute('y', y - 5);
                pctText.setAttribute('text-anchor', 'middle');
                pctText.textContent = percentage.toFixed(1) + '%';
                svg.appendChild(pctText);
            });
        }
        
        // Render errors over time chart
        function renderErrorChart() {
            const svg = document.getElementById('errorChart');
            svg.innerHTML = '';
            
            const entries = Object.entries(dashboardData.errors_per_hour);
            if (entries.length === 0) return;
            
            entries.sort((a, b) => new Date(a[0]) - new Date(b[0]));
            
            const timestamps = entries.map(e => new Date(e[0]));
            const counts = entries.map(e => e[1]);
            
            const width = svg.clientWidth;
            const height = svg.clientHeight;
            const padding = 40;
            
            const xMin = Math.min(...timestamps);
            const xMax = Math.max(...timestamps);
            const yMax = Math.max(...counts);
            
            // Create scales
            const xScale = (x) => padding + ((x - xMin) / (xMax - xMin)) * (width - padding * 2);
            const yScale = (y) => padding + (1 - y / yMax) * (height - padding * 2);
            
            // Draw axes
            const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            xAxis.setAttribute('x1', padding);
            xAxis.setAttribute('y1', height - padding);
            xAxis.setAttribute('x2', width - padding);
            xAxis.setAttribute('y2', height - padding);
            xAxis.setAttribute('stroke', '#000');
            svg.appendChild(xAxis);
            
            const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            yAxis.setAttribute('x1', padding);
            yAxis.setAttribute('y1', padding);
            yAxis.setAttribute('x2', padding);
            yAxis.setAttribute('y2', height - padding);
            yAxis.setAttribute('stroke', '#000');
            svg.appendChild(yAxis);
            
            // Draw line
            if (entries.length > 1) {
                const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
                const points = entries.map(([time, count]) => 
                    `${xScale(new Date(time))},${yScale(count)}`
                ).join(' ');
                polyline.setAttribute('points', points);
                polyline.setAttribute('fill', 'none');
                polyline.setAttribute('stroke', '#007bff');
                polyline.setAttribute('stroke-width', '2');
                svg.appendChild(polyline);
                
                // Draw points
                entries.forEach(([time, count], i) => {
                    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                    circle.setAttribute('cx', xScale(new Date(time)));
                    circle.setAttribute('cy', yScale(count));
                    circle.setAttribute('r', 4);
                    circle.setAttribute('fill', '#007bff');
                    svg.appendChild(circle);
                });
            }
            
            // Draw labels
            // X-axis labels (dates)
            const formatDate = (date) => {
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            };
            
            const xLabel1 = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            xLabel1.setAttribute('x', padding);
            xLabel1.setAttribute('y', height - 5);
            xLabel1.textContent = formatDate(xMin);
            svg.appendChild(xLabel1);
            
            const xLabel2 = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            xLabel2.setAttribute('x', width - padding);
            xLabel2.setAttribute('y', height - 5);
            xLabel2.setAttribute('text-anchor', 'end');
            xLabel2.textContent = formatDate(xMax);
            svg.appendChild(xLabel2);
            
            // Y-axis labels
            const yLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            yLabel.setAttribute('x', 5);
            yLabel.setAttribute('y', padding + 5);
            yLabel.textContent = yMax;
            svg.appendChild(yLabel);
        }
        
        // Render common errors table
        function renderCommonErrors() {
            const tbody = document.getElementById('commonErrorsBody');
            tbody.innerHTML = '';
            
            dashboardData.common_errors.forEach(([message, count]) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${message}</td>
                    <td>${count}</td>
                `;
                tbody.appendChild(row);
            });
        }
        
        // Render critical errors table
        function renderCriticalErrors() {
            const tbody = document.getElementById('criticalErrorsBody');
            tbody.innerHTML = '';
            
            filteredCriticalErrors.forEach(error => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${error.timestamp}</td>
                    <td>${error.message}</td>
                `;
                tbody.appendChild(row);
            });
        }
        
        // Search critical errors
        function searchCriticalErrors() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            if (!searchTerm) {
                filteredCriticalErrors = dashboardData.criticalErrors;
            } else {
                filteredCriticalErrors = dashboardData.criticalErrors.filter(error =>
                    error.message.toLowerCase().includes(searchTerm)
                );
            }
            renderCriticalErrors();
        }
        
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(button => {
            button.addEventListener('click', function() {
                document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                // In a real implementation, this would filter the data
                // For now, we'll just show all data regardless of filter
            });
        });
        
        // Initialize dashboard
        fetchData();
    </script>
</body>
</html>
        '''
        
        self.wfile.write(html.encode())
    
    def serve_api_data(self):
        data = parse_log_file()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def serve_critical_errors(self):
        data = parse_log_file()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data['critical_errors']).encode())

# Main function
def main():
    # Parse log file and generate data
    print("Parsing log data...")
    data = parse_log_file()
    
    # Start HTTP server
    port = 8000
    with socketserver.TCPServer(("", port), LogDashboardHandler) as httpd:
        print(f"Log Analytics Dashboard running at http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()