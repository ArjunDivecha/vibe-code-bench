import os
import http.server
import json
import collections
import random
import datetime

# Create log data if server.log doesn't exist
if not os.path.exists('server.log'):
    with open('server.log', 'w') as log_file:
        for i in range(1000):
            level = random.choice(['INFO', 'WARN', 'ERROR', 'CRITICAL'])
            timestamp = datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))
            log_file.write(f'{timestamp.isoformat()} - {level} - Example message\n')

# Parse log file
log_levels = collections.defaultdict(int)
errors_per_hour = collections.defaultdict(int)
critical_errors = collections.defaultdict(int)
with open('server.log', 'r') as log_file:
    for line in log_file:
        _, level, message = line.strip().split(' - ', 2)
        log_levels[level] += 1
        timestamp = datetime.datetime.fromisoformat(line.split(' - ', 1)[0])
        errors_per_hour[timestamp.hour] += 1
        if level == 'CRITICAL':
            critical_errors[random.choice([1, 2, 3])] += 1  # Random ID

# Calculate log level percentages
total_logs = sum(log_levels.values())
log_level_percentages = {level: int((count / total_logs) * 100) for level, count in log_levels.items()}

# Function to handle HTTP requests
class LogAnalyticsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(self.get_dashboard_html(), 'utf-8'))
        elif self.path.startswith('/static/'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(self.get_static_html(), 'utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not found')

    def get_dashboard_html(self):
        return f'''
            <html>
                <head>
                    <title>Log Analytics Dashboard</title>
                    <style>
                        /* Add some basic styling */
                        body {{ font-family: Arial, sans-serif; }}
                        h1 {{ font-size: 24px; }}
                    </style>
                </head>
                <body>
                    <h1>Log Analytics Dashboard</h1>
                    <div>
                        <h2>Log Level Percentages:</h2>
                        <ul>
                            {self.get_log_level_list_html(log_level_percentages)}
                        </ul>
                    </div>
                    <div>
                        <h2>Errors per Hour:</h2>
                        <svg id="errors-per-hour" width="800" height="200"></svg>
                    </div>
                    <div>
                        <h2>CRITICAL Errors:</h2>
                        <input id="search" type="search" placeholder="Search...">
                        <table id="critical-errors">
                            <tr>
                                <th>ID</th>
                                <th>Message</th>
                            </tr>
                            {self.get_critical_errors_html(critical_errors)}
                        </table>
                    </div>
                    <div>
                        <h2>Filter by Level:</h2>
                        <select id="level-filter">
                            <option value="all">All</option>
                            <option value="error">Error</option>
                            <option value="critical">Critical</option>
                        </select>
                    </div>
                </body>
            </html>
        '''

    def get_static_html(self):
        return '''
            <html>
                <head>
                    <title>Static Content</title>
                </head>
                <body>
                    <h1>Static Content</h1>
                </body>
            </html>
        '''

    def get_log_level_list_html(self, percentages):
        html = ''
        for level, percentage in percentages.items():
            html += f'<li>{level}: {percentage}%</li>'
        return html

    def get_critical_errors_html(self, critical_errors):
        html = ''
        for id in sorted(critical_errors.keys()):
            message = random.choice(['Error message 1', 'Error message 2', 'Error message 3'])
            html += f'<tr><td>{id}</td><td>{message}</td></tr>'
        return html

# Launch HTTP server
httpd = http.server.HTTPServer(('localhost', 8000), LogAnalyticsHandler)
print('Log Analytics Dashboard available at http://localhost:8000')
httpd.serve_forever()