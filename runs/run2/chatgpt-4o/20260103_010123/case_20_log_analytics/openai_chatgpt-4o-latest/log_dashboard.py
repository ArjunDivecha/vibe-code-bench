import os
import random
import datetime
import json
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from collections import defaultdict, Counter

LOG_FILE = 'server.log'
HTML_FILE = 'dashboard.html'

LOG_LEVELS = ['INFO', 'WARN', 'ERROR', 'CRITICAL']
ERROR_LEVELS = ['ERROR', 'CRITICAL']

SAMPLE_MESSAGES = {
    'INFO': [
        'User logged in successfully',
        'Connection established',
        'Background job started',
        'Cache refreshed',
        'Heartbeat received'
    ],
    'WARN': [
        'Disk usage above 80%',
        'Memory usage high',
        'Deprecated API used',
        'Slow response time',
        'Config value missing, using default'
    ],
    'ERROR': [
        'Failed to connect to database',
        'Unhandled exception occurred',
        'Service timeout',
        'Authentication failed',
        'File not found'
    ],
    'CRITICAL': [
        'System crash',
        'Data corruption detected',
        'Security breach detected',
        'Kernel panic',
        'Out of memory'
    ]
}


def generate_fake_logs():
    with open(LOG_FILE, 'w') as f:
        now = datetime.datetime.now()
        for _ in range(1000):
            delta = datetime.timedelta(seconds=random.randint(0, 3600*24))
            ts = now - delta
            level = random.choices(LOG_LEVELS, weights=[0.5, 0.2, 0.2, 0.1])[0]
            msg = random.choice(SAMPLE_MESSAGES[level])
            line = f"{ts.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {msg}\n"
            f.write(line)


def parse_logs():
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()

    level_counts = Counter()
    errors_by_hour = defaultdict(int)
    error_messages = Counter()
    critical_logs = []

    with open(LOG_FILE, 'r') as f:
        for line in f:
            try:
                parts = line.strip().split(' ', 2)
                timestamp = parts[0] + ' ' + parts[1]
                rest = parts[2]
                level_start = rest.find('[')
                level_end = rest.find(']')
                level = rest[level_start+1:level_end]
                message = rest[level_end+2:]

                level_counts[level] += 1

                if level in ERROR_LEVELS:
                    dt = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    hour = dt.replace(minute=0, second=0, microsecond=0)
                    errors_by_hour[hour.strftime('%Y-%m-%d %H:%M')] += 1
                    error_messages[message] += 1

                if level == 'CRITICAL':
                    critical_logs.append({
                        'timestamp': timestamp,
                        'message': message
                    })
            except Exception as e:
                continue

    total = sum(level_counts.values())
    level_percentages = {
        level: round((count / total) * 100, 2)
        for level, count in level_counts.items()
    }

    return {
        'level_percentages': level_percentages,
        'errors_by_hour': dict(sorted(errors_by_hour.items())),
        'common_errors': error_messages.most_common(10),
        'critical_logs': critical_logs
    }


def write_dashboard(data):
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Log Analytics Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            padding: 20px;
        }}
        h1 {{
            text-align: center;
        }}
        .chart {{
            margin: 20px 0;
        }}
        svg {{
            width: 100%;
            height: 300px;
            background: #f4f4f4;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background: #eee;
        }}
        input {{
            margin-bottom: 10px;
            padding: 5px;
            width: 300px;
        }}
    </style>
</head>
<body>
    <h1>Log Analytics Dashboard</h1>

    <h2>Log Level Distribution</h2>
    <div class="chart">
        <svg id="levelChart"></svg>
    </div>

    <h2>Errors Over Time</h2>
    <div class="chart">
        <svg id="errorTimeline"></svg>
    </div>

    <h2>Top Error Messages</h2>
    <ul>
        {''.join(f'<li>{msg} ({count})</li>' for msg, count in data['common_errors'])}
    </ul>

    <h2>CRITICAL Errors</h2>
    <input type="text" id="search" placeholder="Search messages...">
    <table>
        <thead>
            <tr><th>Timestamp</th><th>Message</th></tr>
        </thead>
        <tbody id="criticalTable">
            {''.join(f"<tr><td>{log['timestamp']}</td><td>{log['message']}</td></tr>" for log in data['critical_logs'])}
        </tbody>
    </table>

    <script>
        const levelData = {json.dumps(data['level_percentages'])};
        const errorTimeline = {json.dumps(data['errors_by_hour'])};

        function drawBarChart(data, svgId, maxVal=null) {{
            const svg = document.getElementById(svgId);
            while (svg.firstChild) svg.removeChild(svg.firstChild);

            const keys = Object.keys(data);
            const values = Object.values(data);
            const max = maxVal || Math.max(...values);
            const width = svg.clientWidth;
            const height = svg.clientHeight;
            const barWidth = width / keys.length;

            keys.forEach((key, i) => {{
                const val = data[key];
                const barHeight = (val / max) * (height - 20);
                const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                rect.setAttribute("x", i * barWidth);
                rect.setAttribute("y", height - barHeight);
                rect.setAttribute("width", barWidth - 2);
                rect.setAttribute("height", barHeight);
                rect.setAttribute("fill", "#3498db");
                svg.appendChild(rect);

                if (barWidth > 40) {{
                    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
                    label.setAttribute("x", i * barWidth + barWidth / 2);
                    label.setAttribute("y", height - 5);
                    label.setAttribute("text-anchor", "middle");
                    label.setAttribute("font-size", "10");
                    label.textContent = key;
                    svg.appendChild(label);
                }}
            }});
        }}

        drawBarChart(levelData, "levelChart", 100);
        drawBarChart(errorTimeline, "errorTimeline");

        document.getElementById('search').addEventListener('input', function() {{
            const filter = this.value.toLowerCase();
            const rows = document.querySelectorAll('#criticalTable tr');
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            }});
        }});
    </script>
</body>
</html>
"""
    with open(HTML_FILE, 'w') as f:
        f.write(html)


def start_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print("Serving dashboard at http://localhost:8000/dashboard.html")
    httpd.serve_forever()


if __name__ == '__main__':
    data = parse_logs()
    write_dashboard(data)
    start_server()