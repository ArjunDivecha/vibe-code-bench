import os
import random
import re
import json
import collections
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import webbrowser
import threading
import time

# Generate fake log data
def generate_log_data():
    log_levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL']
    log_messages = {
        'INFO': ['User logged in', 'Data processed successfully', 'Cache updated', 'Backup completed'],
        'WARN': ['Deprecated API usage', 'Low disk space', 'High memory usage', 'Slow response time'],
        'ERROR': ['Database connection failed', 'Invalid user input', 'File not found', 'Permission denied'],
        'CRITICAL': ['System crash', 'Security breach detected', 'Database corruption', 'Service unavailable']
    }
    
    # Generate 1000 log entries
    log_entries = []
    start_time = datetime.now() - timedelta(hours=24)
    
    for i in range(1000):
        # Random timestamp within the last 24 hours
        timestamp = start_time + timedelta(minutes=random.randint(0, 24*60))
        level = random.choices(log_levels, weights=[50, 30, 15, 5])[0]  # Weighted random selection
        message = random.choice(log_messages[level])
        log_entries.append(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {level}: {message}")
    
    # Sort by timestamp
    log_entries.sort()
    
    # Write to file
    with open('server.log', 'w') as f:
        f.write('\n'.join(log_entries))
    
    print("Generated server.log with 1000 entries")

# Parse log file
def parse_log_file():
    if not os.path.exists('server.log'):
        generate_log_data()
    
    with open('server.log', 'r') as f:
        lines = f.readlines()
    
    # Initialize counters
    level_counts = collections.defaultdict(int)
    errors_per_hour = collections.defaultdict(int)
    error_messages = collections.defaultdict(int)
    critical_errors = []
    
    # Regex pattern to extract timestamp and log level
    pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (INFO|WARN|ERROR|CRITICAL): (.+)'
    
    for line in lines:
        match = re.match(pattern, line.strip())
        if match:
            timestamp_str, level, message = match.groups()
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Count log levels
            level_counts[level] += 1
            
            # Count errors per hour
            if level in ['ERROR', 'CRITICAL']:
                hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                errors_per_hour[hour_key] += 1
                
                # Track error messages
                error_messages[message] += 1
                
                # Collect critical errors
                if level == 'CRITICAL':
                    critical_errors.append({
                        'timestamp': timestamp_str,
                        'message': message
                    })
    
    # Calculate percentages
    total_entries = sum(level_counts.values())
    level_percentages = {level: (count / total_entries) * 100 for level, count in level_counts.items()}
    
    # Fill in missing hours with zero counts
    if errors_per_hour:
        start_hour = min(datetime.strptime(t, '%Y-%m-%d %H:00') for t in errors_per_hour.keys())
        end_hour = max(datetime.strptime(t, '%Y-%m-%d %H:00') for t in errors_per_hour.keys())
        
        current_hour = start_hour
        while current_hour <= end_hour:
            hour_key = current_hour.strftime('%Y-%m-%d %H:00')
            if hour_key not in errors_per_hour:
                errors_per_hour[hour_key] = 0
            current_hour += timedelta(hours=1)
    
    return {
        'level_percentages': level_percentages,
        'errors_per_hour': dict(sorted(errors_per_hour.items())),
        'top_errors': dict(sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[:10]),
        'critical_errors': critical_errors
    }

# Custom HTTP request handler
class LogDashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_dashboard()
        elif self.path == '/data':
            self.serve_data()
        elif self.path == '/search':
            self.serve_search()
        else:
            super().do_GET()
    
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
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            margin: 0;
            font-size: 2.5rem;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }
        .card h2 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .chart-container {
            height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .log-levels {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .level-bar {
            display: flex;
            align-items: center;
        }
        .level-name {
            width: 100px;
            font-weight: bold;
        }
        .bar-container {
            flex-grow: 1;
            height: 20px;
            background-color: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
        }
        .bar-fill {
            height: 100%;
            border-radius: 10px;
        }
        .info { background-color: #3498db; }
        .warn { background-color: #f39c12; }
        .error { background-color: #e74c3c; }
        .critical { background-color: #9b59b6; }
        .percentage {
            width: 50px;
            text-align: right;
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
            background-color: #f2f2f2;
            position: sticky;
            top: 0;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        select, input {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        button {
            padding: 10px 20px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #2980b9;
        }
        #errorChart {
            width: 100%;
            height: 300px;
        }
        .hidden {
            display: none;
        }
        footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Log Analytics Dashboard</h1>
            <p>Real-time analysis of server log data</p>
        </header>
        
        <div class="dashboard">
            <div class="card">
                <h2>Log Level Distribution</h2>
                <div class="log-levels" id="levelBars">
                    <!-- Level bars will be inserted here by JavaScript -->
                </div>
            </div>
            
            <div class="card">
                <h2>Error Trends Over Time</h2>
                <div class="chart-container">
                    <svg id="errorChart" width="100%" height="100%"></svg>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Critical Errors</h2>
            <div class="controls">
                <select id="filterLevel">
                    <option value="all">All Levels</option>
                    <option value="error">Error</option>
                    <option value="critical">Critical</option>
                </select>
                <input type="text" id="searchInput" placeholder="Search messages...">
                <button id="searchButton">Search</button>
            </div>
            <div id="criticalErrorsTable">
                <!-- Table will be inserted here by JavaScript -->
            </div>
        </div>
        
        <div class="card">
            <h2>Top Error Messages</h2>
            <div class="log-levels" id="topErrors">
                <!-- Top errors will be inserted here by JavaScript -->
            </div>
        </div>
    </div>
    
    <footer>
        <p>Log Analytics Dashboard &copy; 2023</p>
    </footer>

    <script>
        // Fetch data from server
        async function fetchData() {
            const response = await fetch('/data');
            return await response.json();
        }
        
        // Render level distribution bars
        function renderLevelBars(data) {
            const container = document.getElementById('levelBars');
            container.innerHTML = '';
            
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const colors = {
                'INFO': '#3498db',
                'WARN': '#f39c12',
                'ERROR': '#e74c3c',
                'CRITICAL': '#9b59b6'
            };
            
            levels.forEach(level => {
                const percentage = data.level_percentages[level] || 0;
                const bar = document.createElement('div');
                bar.className = 'level-bar';
                bar.innerHTML = `
                    <div class="level-name">${level}</div>
                    <div class="bar-container">
                        <div class="bar-fill ${level.toLowerCase()}" style="width: ${percentage}%"></div>
                    </div>
                    <div class="percentage">${percentage.toFixed(1)}%</div>
                `;
                container.appendChild(bar);
            });
        }
        
        // Render error trend chart
        function renderErrorChart(data) {
            const svg = document.getElementById('errorChart');
            svg.innerHTML = '';
            
            const entries = Object.entries(data.errors_per_hour);
            if (entries.length === 0) return;
            
            const margin = {top: 20, right: 30, bottom: 50, left: 60};
            const width = svg.clientWidth - margin.left - margin.right;
            const height = svg.clientHeight - margin.top - margin.bottom;
            
            // Create SVG group
            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('transform', `translate(${margin.left},${margin.top})`);
            svg.appendChild(g);
            
            // Get min and max values
            const values = entries.map(([_, count]) => count);
            const maxCount = Math.max(...values, 1);
            const minDate = new Date(entries[0][0]);
            const maxDate = new Date(entries[entries.length-1][0]);
            
            // Create scales
            const xScale = (dateStr) => {
                const date = new Date(dateStr);
                return ((date - minDate) / (maxDate - minDate)) * width;
            };
            
            const yScale = (count) => height - (count / maxCount) * height;
            
            // Create line path
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            let pathData = "M";
            
            entries.forEach(([dateStr, count], i) => {
                const x = xScale(dateStr);
                const y = yScale(count);
                pathData += `${x},${y} `;
            });
            
            path.setAttribute('d', pathData.trim());
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke', '#e74c3c');
            path.setAttribute('stroke-width', '2');
            g.appendChild(path);
            
            // Create points
            entries.forEach(([dateStr, count]) => {
                const x = xScale(dateStr);
                const y = yScale(count);
                
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', x);
                circle.setAttribute('cy', y);
                circle.setAttribute('r', '4');
                circle.setAttribute('fill', '#e74c3c');
                g.appendChild(circle);
            });
            
            // Add axes
            const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            xAxis.setAttribute('x1', 0);
            xAxis.setAttribute('y1', height);
            xAxis.setAttribute('x2', width);
            xAxis.setAttribute('y2', height);
            xAxis.setAttribute('stroke', '#000');
            g.appendChild(xAxis);
            
            const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            yAxis.setAttribute('x1', 0);
            yAxis.setAttribute('y1', 0);
            yAxis.setAttribute('x2', 0);
            yAxis.setAttribute('y2', height);
            yAxis.setAttribute('stroke', '#000');
            g.appendChild(yAxis);
            
            // Add labels
            const xAxisLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            xAxisLabel.setAttribute('x', width / 2);
            xAxisLabel.setAttribute('y', height + 40);
            xAxisLabel.setAttribute('text-anchor', 'middle');
            xAxisLabel.textContent = 'Time';
            g.appendChild(xAxisLabel);
            
            const yAxisLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            yAxisLabel.setAttribute('x', -height/2);
            yAxisLabel.setAttribute('y', -40);
            yAxisLabel.setAttribute('transform', 'rotate(-90)');
            yAxisLabel.setAttribute('text-anchor', 'middle');
            yAxisLabel.textContent = 'Error Count';
            g.appendChild(yAxisLabel);
        }
        
        // Render critical errors table
        function renderCriticalErrors(data, filter = 'all', searchTerm = '') {
            const container = document.getElementById('criticalErrorsTable');
            
            // Filter data
            let filteredErrors = data.critical_errors;
            if (filter !== 'all') {
                filteredErrors = filteredErrors.filter(error => 
                    filter === 'error' ? true : error.message.toLowerCase().includes(searchTerm.toLowerCase())
                );
            }
            
            if (searchTerm) {
                filteredErrors = filteredErrors.filter(error => 
                    error.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    error.timestamp.includes(searchTerm)
                );
            }
            
            // Create table
            let tableHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            filteredErrors.forEach(error => {
                tableHTML += `
                    <tr>
                        <td>${error.timestamp}</td>
                        <td>${error.message}</td>
                    </tr>
                `;
            });
            
            tableHTML += `
                    </tbody>
                </table>
            `;
            
            container.innerHTML = tableHTML;
        }
        
        // Render top errors
        function renderTopErrors(data) {
            const container = document.getElementById('topErrors');
            container.innerHTML = '';
            
            Object.entries(data.top_errors).forEach(([message, count]) => {
                const bar = document.createElement('div');
                bar.className = 'level-bar';
                
                // Calculate percentage based on max count
                const maxCount = Math.max(...Object.values(data.top_errors));
                const percentage = (count / maxCount) * 100;
                
                bar.innerHTML = `
                    <div class="level-name">${count}</div>
                    <div class="bar-container">
                        <div class="bar-fill error" style="width: ${percentage}%"></div>
                    </div>
                    <div class="percentage" style="width: 300px; text-align: left; margin-left: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${message}</div>
                `;
                container.appendChild(bar);
            });
        }
        
        // Initialize dashboard
        async function initDashboard() {
            const data = await fetchData();
            renderLevelBars(data);
            renderErrorChart(data);
            renderCriticalErrors(data);
            renderTopErrors(data);
            
            // Set up event listeners
            document.getElementById('filterLevel').addEventListener('change', (e) => {
                renderCriticalErrors(data, e.target.value, document.getElementById('searchInput').value);
            });
            
            document.getElementById('searchButton').addEventListener('click', () => {
                renderCriticalErrors(data, document.getElementById('filterLevel').value, document.getElementById('searchInput').value);
            });
            
            document.getElementById('searchInput').addEventListener('keyup', (e) => {
                if (e.key === 'Enter') {
                    renderCriticalErrors(data, document.getElementById('filterLevel').value, document.getElementById('searchInput').value);
                }
            });
        }
        
        // Load dashboard when page loads
        document.addEventListener('DOMContentLoaded', initDashboard);
    </script>
</body>
</html>
        '''
        
        self.wfile.write(html_content.encode())
    
    def serve_data(self):
        # Parse log data
        data = parse_log_file()
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def serve_search(self):
        # Get query parameters
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Get search term
        search_term = query_params.get('q', [''])[0]
        
        # Parse log data
        data = parse_log_file()
        
        # Filter critical errors based on search term
        filtered_errors = [
            error for error in data['critical_errors'] 
            if search_term.lower() in error['message'].lower() or search_term in error['timestamp']
        ]
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'critical_errors': filtered_errors}).encode())

# Main function
def main():
    # Parse log file and generate data
    print("Parsing log data...")
    data = parse_log_file()
    
    # Start HTTP server
    port = 8000
    server = HTTPServer(('localhost', port), LogDashboardHandler)
    
    print(f"\nLog Analytics Dashboard is running at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    # Open browser in a separate thread
    def open_browser():
        time.sleep(1)  # Give server a moment to start
        webbrowser.open(f'http://localhost:{port}')
    
    threading.Thread(target=open_browser).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == '__main__':
    main()