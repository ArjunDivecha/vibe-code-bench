import os
import random
import datetime
import json
import http.server
import socketserver
import urllib.parse
from collections import Counter, defaultdict

# Generate fake log data
def generate_log_data(filename="server.log", num_lines=1000):
    if os.path.exists(filename):
        return
    
    log_levels = ["INFO", "WARN", "ERROR", "CRITICAL"]
    log_messages = {
        "INFO": [
            "User logged in", 
            "File uploaded successfully", 
            "Database connection established",
            "Cache cleared"
        ],
        "WARN": [
            "Deprecated API usage", 
            "Low disk space", 
            "Memory usage high",
            "Slow response time"
        ],
        "ERROR": [
            "Database connection failed", 
            "Invalid user input", 
            "File not found", 
            "Permission denied"
        ],
        "CRITICAL": [
            "System crash", 
            "Security breach detected", 
            "Database corruption", 
            "Service unavailable"
        ]
    }
    
    with open(filename, "w") as f:
        start_time = datetime.datetime.now() - datetime.timedelta(hours=num_lines//60)
        for i in range(num_lines):
            timestamp = start_time + datetime.timedelta(minutes=i)
            level = random.choices(log_levels, weights=[50, 30, 15, 5])[0]
            message = random.choice(log_messages[level])
            f.write(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}\n")

# Parse log file
def parse_log_file(filename="server.log"):
    log_levels = Counter()
    errors_per_hour = defaultdict(int)
    critical_errors = []
    
    with open(filename, "r") as f:
        for line in f:
            parts = line.split(" ", 3)
            if len(parts) < 4:
                continue
                
            timestamp_str = parts[0] + " " + parts[1]
            level = parts[2][1:-1]  # Remove brackets
            message = parts[3].strip()
            
            # Count log levels
            log_levels[level] += 1
            
            # Parse timestamp for errors per hour
            try:
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                
                if level in ["ERROR", "CRITICAL"]:
                    errors_per_hour[hour_key] += 1
                    
                # Collect critical errors
                if level == "CRITICAL":
                    critical_errors.append({
                        "timestamp": timestamp_str,
                        "message": message
                    })
            except ValueError:
                continue
    
    # Calculate percentages
    total_logs = sum(log_levels.values())
    log_percentages = {level: (count / total_logs) * 100 for level, count in log_levels.items()}
    
    return {
        "log_percentages": log_percentages,
        "errors_per_hour": dict(errors_per_hour),
        "critical_errors": critical_errors
    }

# HTTP request handler
class LogDashboardHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # Serve the main dashboard
        if parsed_path.path == "/" or parsed_path.path == "/index.html":
            self.serve_dashboard()
        # Serve data API
        elif parsed_path.path == "/api/data":
            self.serve_data()
        # Serve filtered critical errors
        elif parsed_path.path == "/api/critical-errors":
            level_filter = query_params.get("level", ["All"])[0]
            self.serve_critical_errors(level_filter)
        else:
            self.send_error(404, "File not found")
    
    def serve_dashboard(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background-color: #fff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .card h2 {
            margin-top: 0;
            color: #555;
        }
        .log-levels {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .log-level {
            display: flex;
            justify-content: space-between;
        }
        .bar-container {
            width: 70%;
            background-color: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
        }
        .bar {
            height: 20px;
            background-color: #4CAF50;
        }
        .chart-container {
            width: 100%;
            height: 300px;
            position: relative;
        }
        .error-chart {
            width: 100%;
            height: 100%;
        }
        .controls {
            margin: 20px 0;
            display: flex;
            gap: 10px;
        }
        select, input {
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        button {
            padding: 8px 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
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
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .error {
            color: #d32f2f;
        }
        .critical {
            color: #f57c00;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Log Analytics Dashboard</h1>
        
        <div class="dashboard">
            <div class="card">
                <h2>Log Level Distribution</h2>
                <div class="log-levels" id="logLevels">
                    <!-- Log level bars will be inserted here by JS -->
                </div>
            </div>
            
            <div class="card">
                <h2>Errors Per Hour</h2>
                <div class="chart-container">
                    <svg class="error-chart" id="errorChart"></svg>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Critical Errors</h2>
            <div class="controls">
                <select id="levelFilter">
                    <option value="All">All</option>
                    <option value="ERROR">Error</option>
                    <option value="CRITICAL">Critical</option>
                </select>
                <input type="text" id="searchInput" placeholder="Search messages...">
                <button id="searchButton">Search</button>
            </div>
            <div id="criticalErrorsTable">
                <!-- Table will be populated by JS -->
            </div>
        </div>
    </div>

    <script>
        // Fetch and display log data
        async function loadDashboard() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                
                // Display log level distribution
                displayLogLevels(data.log_percentages);
                
                // Display errors per hour chart
                displayErrorsPerHour(data.errors_per_hour);
            } catch (error) {
                console.error('Error loading dashboard:', error);
            }
        }
        
        // Display log level distribution
        function displayLogLevels(logPercentages) {
            const container = document.getElementById('logLevels');
            container.innerHTML = '';
            
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const colors = {
                'INFO': '#4CAF50',
                'WARN': '#FFC107',
                'ERROR': '#FF9800',
                'CRITICAL': '#F44336'
            };
            
            levels.forEach(level => {
                const percentage = logPercentages[level] || 0;
                const levelDiv = document.createElement('div');
                levelDiv.className = 'log-level';
                levelDiv.innerHTML = `
                    <span>${level}</span>
                    <div class="bar-container">
                        <div class="bar" style="width: ${percentage}%; background-color: ${colors[level]}"></div>
                    </div>
                    <span>${percentage.toFixed(1)}%</span>
                `;
                container.appendChild(levelDiv);
            });
        }
        
        // Display errors per hour chart
        function displayErrorsPerHour(errorsPerHour) {
            const svg = document.getElementById('errorChart');
            svg.innerHTML = '';
            
            const entries = Object.entries(errorsPerHour);
            if (entries.length === 0) return;
            
            // Sort by time
            entries.sort((a, b) => new Date(a[0]) - new Date(b[0]));
            
            const margin = { top: 20, right: 30, bottom: 40, left: 50 };
            const width = svg.clientWidth - margin.left - margin.right;
            const height = svg.clientHeight - margin.top - margin.bottom;
            
            // Create SVG elements
            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('transform', `translate(${margin.left},${margin.top})`);
            svg.appendChild(g);
            
            // Find max value for scaling
            const maxValue = Math.max(...entries.map(([_, value]) => value), 1);
            
            // Create scales
            const xScale = width / (entries.length - 1 || 1);
            const yScale = height / maxValue;
            
            // Create bars
            entries.forEach((entry, i) => {
                const [time, value] = entry;
                const x = i * xScale;
                const barHeight = value * yScale;
                const y = height - barHeight;
                
                // Bar
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', x);
                rect.setAttribute('y', y);
                rect.setAttribute('width', Math.max(2, xScale - 2));
                rect.setAttribute('height', barHeight);
                rect.setAttribute('fill', '#FF9800');
                g.appendChild(rect);
                
                // Label
                if (i % Math.ceil(entries.length / 10) === 0) {
                    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    text.setAttribute('x', x);
                    text.setAttribute('y', height + 20);
                    text.setAttribute('font-size', '10');
                    text.setAttribute('text-anchor', 'middle');
                    text.textContent = time.split(' ')[1].substring(0, 5); // Show only hour
                    g.appendChild(text);
                }
            });
            
            // Y-axis labels
            for (let i = 0; i <= 5; i++) {
                const value = Math.round((i / 5) * maxValue);
                const y = height - (i / 5) * height;
                
                // Line
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', -5);
                line.setAttribute('y1', y);
                line.setAttribute('x2', width);
                line.setAttribute('y2', y);
                line.setAttribute('stroke', '#ccc');
                line.setAttribute('stroke-width', '0.5');
                g.appendChild(line);
                
                // Label
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', -10);
                text.setAttribute('y', y + 4);
                text.setAttribute('font-size', '10');
                text.setAttribute('text-anchor', 'end');
                text.textContent = value;
                g.appendChild(text);
            }
        }
        
        // Load critical errors table
        async function loadCriticalErrors(filter = 'All', search = '') {
            try {
                const response = await fetch(`/api/critical-errors?level=${filter}&search=${encodeURIComponent(search)}`);
                const errors = await response.json();
                
                const tableContainer = document.getElementById('criticalErrorsTable');
                if (errors.length === 0) {
                    tableContainer.innerHTML = '<p>No critical errors found</p>';
                    return;
                }
                
                let tableHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Level</th>
                                <th>Message</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                errors.forEach(error => {
                    const levelClass = error.level === 'CRITICAL' ? 'critical' : 'error';
                    tableHTML += `
                        <tr>
                            <td>${error.timestamp}</td>
                            <td class="${levelClass}">${error.level}</td>
                            <td>${error.message}</td>
                        </tr>
                    `;
                });
                
                tableHTML += `
                        </tbody>
                    </table>
                `;
                
                tableContainer.innerHTML = tableHTML;
            } catch (error) {
                console.error('Error loading critical errors:', error);
            }
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', () => {
            loadDashboard();
            loadCriticalErrors();
            
            // Setup event listeners
            document.getElementById('levelFilter').addEventListener('change', function() {
                loadCriticalErrors(this.value, document.getElementById('searchInput').value);
            });
            
            document.getElementById('searchButton').addEventListener('click', function() {
                loadCriticalErrors(document.getElementById('levelFilter').value, document.getElementById('searchInput').value);
            });
            
            document.getElementById('searchInput').addEventListener('keyup', function(event) {
                if (event.key === 'Enter') {
                    loadCriticalErrors(document.getElementById('levelFilter').value, this.value);
                }
            });
        });
    </script>
</body>
</html>
        """
        
        self.wfile.write(html_content.encode())

    def serve_data(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        
        # Parse the log file to get data
        data = parse_log_file()
        self.wfile.write(json.dumps(data).encode())

    def serve_critical_errors(self, level_filter):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        
        # Get all critical errors
        data = parse_log_file()
        errors = data["critical_errors"]
        
        # Convert to the format expected by the frontend
        formatted_errors = []
        for error in errors:
            formatted_errors.append({
                "timestamp": error["timestamp"],
                "level": "CRITICAL",
                "message": error["message"]
            })
            
        # Add some ERROR level entries for demonstration
        log_data = parse_log_file()
        error_entries = []
        with open("server.log", "r") as f:
            for line in f:
                parts = line.split(" ", 3)
                if len(parts) >= 4:
                    level = parts[2][1:-1]
                    if level == "ERROR":
                        error_entries.append({
                            "timestamp": parts[0] + " " + parts[1],
                            "level": "ERROR",
                            "message": parts[3].strip()
                        })
        
        # Add a sample of ERROR entries
        formatted_errors.extend(error_entries[:20])
        
        # Apply filters
        if level_filter != "All":
            formatted_errors = [e for e in formatted_errors if e["level"] == level_filter]
            
        # For simplicity, we're not implementing search on the server side
        # In a real application, you would filter by the search term here
        
        self.wfile.write(json.dumps(formatted_errors).encode())

# Main function
def main():
    # Generate log data if needed
    generate_log_data()
    
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