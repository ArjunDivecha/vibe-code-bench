import os
import random
import datetime
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from collections import Counter, defaultdict
import threading

LOG_FILE = 'server.log'
LOG_LEVELS = ['INFO', 'WARN', 'ERROR', 'CRITICAL']
ERROR_LEVELS = {'ERROR', 'CRITICAL'}
ERROR_MESSAGES = [
    'Database connection failed',
    'User authentication failed',
    'File not found',
    'Timeout occurred',
    'Null pointer exception',
    'Index out of bounds',
    'Service unavailable',
    'Permission denied',
    'Syntax error detected',
    'Disk quota exceeded',
]

def generate_fake_logs():
    now = datetime.datetime.now()
    with open(LOG_FILE, 'w') as f:
        for _ in range(1000):
            delta_minutes = random.randint(0, 60 * 24 * 7)  # within the last week
            log_time = now - datetime.timedelta(minutes=delta_minutes)
            timestamp = log_time.strftime('%Y-%m-%d %H:%M:%S')
            level = random.choices(LOG_LEVELS, weights=[0.5, 0.2, 0.2, 0.1])[0]
            if level in ERROR_LEVELS:
                message = random.choice(ERROR_MESSAGES)
            else:
                message = random.choice([
                    'Operation completed successfully',
                    'User logged in',
                    'Cache refreshed',
                    'Heartbeat received',
                    'Scheduled task executed',
                ])
            line = f"{timestamp} [{level}] {message}\n"
            f.write(line)

def parse_logs():
    level_counts = Counter()
    error_per_hour = defaultdict(int)
    error_messages = Counter()
    critical_errors = []

    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()

    all_logs = []

    for line in lines:
        try:
            timestamp_str, rest = line.strip().split(' [', 1)
            level, message = rest.split('] ', 1)
            dt = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            level = level.strip().upper()
            level_counts[level] += 1
            if level in ERROR_LEVELS:
                hour = dt.strftime('%Y-%m-%d %H:00')
                error_per_hour[hour] += 1
                error_messages[message] += 1
            if level == 'CRITICAL':
                critical_errors.append({'time': timestamp_str, 'message': message})
            all_logs.append({'time': timestamp_str, 'level': level, 'message': message})
        except Exception as e:
            continue  # skip malformed lines

    total = sum(level_counts.values())
    level_percentages = {lvl: round((count / total) * 100, 2) for lvl, count in level_counts.items()}

    sorted_error_timeline = sorted(error_per_hour.items())
    sorted_common_errors = error_messages.most_common(10)

    return {
        'level_percentages': level_percentages,
        'error_per_hour': sorted_error_timeline,
        'common_errors': sorted_common_errors,
        'critical_errors': critical_errors,
        'all_logs': all_logs,
    }

def write_dashboard_data(data):
    with open('dashboard_data.json', 'w') as f:
        json.dump(data, f)

def write_dashboard_html():
    with open('index.html', 'w') as f:
        f.write(DASHBOARD_HTML)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Log Analytics Dashboard</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f4f4f4; }
        h1 { text-align: center; }
        .chart { margin: 20px 0; }
        svg { width: 100%; height: 300px; background: #fff; border: 1px solid #ccc; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #fff; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background: #eee; }
        .filter { margin: 10px 0; }
        input[type="text"] { width: 300px; padding: 5px; }
    </style>
</head>
<body>
<h1>Log Analytics Dashboard</h1>

<div class="chart">
    <h2>Log Level Percentages</h2>
    <svg id="levelChart"></svg>
</div>

<div class="chart">
    <h2>Errors Per Hour</h2>
    <svg id="errorTimeline"></svg>
</div>

<div class="chart">
    <h2>Most Common Error Messages</h2>
    <ul id="commonErrors"></ul>
</div>

<div class="filter">
    <label for="search">Search CRITICAL Messages:</label>
    <input type="text" id="search" placeholder="Search...">
</div>

<table id="criticalTable">
    <thead>
        <tr><th>Time</th><th>Message</th></tr>
    </thead>
    <tbody></tbody>
</table>

<script>
    let data = {};

    fetch('dashboard_data.json')
        .then(res => res.json())
        .then(d => {
            data = d;
            drawLevelChart();
            drawErrorTimeline();
            drawCommonErrors();
            populateCriticalTable();
        });

    function drawLevelChart() {
        const svg = document.getElementById('levelChart');
        const levels = Object.entries(data.level_percentages);
        const maxVal = Math.max(...levels.map(x => x[1]));
        const barWidth = 100;
        svg.innerHTML = '';
        levels.forEach((item, i) => {
            const [label, val] = item;
            const height = (val / maxVal) * 200;
            const x = i * (barWidth + 10) + 50;
            const y = 250 - height;
            svg.innerHTML += `
                <rect x="${x}" y="${y}" width="${barWidth}" height="${height}" fill="#4CAF50"></rect>
                <text x="${x + barWidth/2}" y="270" text-anchor="middle">${label}</text>
                <text x="${x + barWidth/2}" y="${y - 5}" text-anchor="middle">${val}%</text>
            `;
        });
    }

    function drawErrorTimeline() {
        const svg = document.getElementById('errorTimeline');
        const items = data.error_per_hour;
        const maxVal = Math.max(...items.map(x => x[1]));
        const width = svg.clientWidth;
        const height = 250;
        const xStep = width / items.length;
        svg.innerHTML = '';
        items.forEach((item, i) => {
            const [label, val] = item;
            const barHeight = (val / maxVal) * height;
            const x = i * xStep + 10;
            const y = height - barHeight;
            svg.innerHTML += `
                <rect x="${x}" y="${y}" width="${xStep - 2}" height="${barHeight}" fill="#f44336"></rect>
            `;
        });
    }

    function drawCommonErrors() {
        const ul = document.getElementById('commonErrors');
        ul.innerHTML = '';
        data.common_errors.forEach(item => {
            const [msg, count] = item;
            const li = document.createElement('li');
            li.textContent = `${msg} (${count})`;
            ul.appendChild(li);
        });
    }

    function populateCriticalTable() {
        const tbody = document.querySelector('#criticalTable tbody');
        const searchInput = document.getElementById('search');
        function renderTable() {
            const query = searchInput.value.toLowerCase();
            tbody.innerHTML = '';
            data.critical_errors.forEach(item => {
                if (item.message.toLowerCase().includes(query)) {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${item.time}</td><td>${item.message}</td>`;
                    tbody.appendChild(tr);
                }
            });
        }
        searchInput.addEventListener('input', renderTable);
        renderTable();
    }
</script>
</body>
</html>
"""

class DashboardServer(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return  # silence log messages

def run_server():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, DashboardServer)
    print("Serving dashboard at http://localhost:8000")
    httpd.serve_forever()

def main():
    if not os.path.exists(LOG_FILE):
        print("Generating fake log file...")
        generate_fake_logs()
    print("Parsing logs...")
    data = parse_logs()
    write_dashboard_data(data)
    write_dashboard_html()
    print("Starting server...")
    run_server()

if __name__ == '__main__':
    main()