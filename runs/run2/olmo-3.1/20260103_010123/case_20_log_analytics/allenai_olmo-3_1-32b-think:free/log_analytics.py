import os
import json
import random
import datetime
import http.server
import socketserver
from collections import Counter

def generate_fake_log():
    levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL']
    weights = [50, 25, 15, 10]
    total = sum(weights)
    rand = random.randint(1, total)
    for i, w in enumerate(weights):
        if rand <= w:
            level = levels[i]
            break
    else:
        level = 'INFO'
    
    now = datetime.datetime.now()
    delta = datetime.timedelta(seconds=random.randint(0, 86400))
    timestamp = now - delta
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    if level in ['ERROR', 'CRITICAL']:
        error_msgs = [
            "Database connection failed", 
            "File not found", 
            "Invalid input", 
            "Timeout occurred",
            "Permission denied",
            "Resource unavailable"
        ]
        msg = random.choice(error_msgs)
        if level == 'CRITICAL':
            msg += " - CRITICAL"
    elif level == 'WARN':
        warn_msgs = [
            "Deprecated function called",
            "Deprecated method used",
            "Potential security issue",
            "Configuration warning"
        ]
        msg = random.choice(warn_msgs)
    else:
        info_msgs = [
            "System started", 
            "User logged in", 
            "Page loaded", 
            "Operation completed successfully",
            "Connection established"
        ]
        msg = random.choice(info_msgs)
    
    return f"{timestamp_str} [{level}] {msg}"

def parse_log(file_path):
    logs = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('[', 1)
            if len(parts) < 2:
                continue
            timestamp_part = parts[0].strip()
            level_and_rest = parts[1]
            try:
                level_part, message_part = level_and_rest.split(']', 1)
            except ValueError:
                continue
            level = level_part.strip()
            message_part = message_part.strip()
            if level == 'CRITICAL' and message_part.endswith(' - CRITICAL'):
                message = message_part[:-12].strip()
            else:
                message = message_part
            try:
                time_part = timestamp_part.split(' ')[1]
                hour = time_part.split(':')[0]
            except (IndexError, ValueError):
                hour = '00'
            logs.append({
                'timestamp': timestamp_part,
                'level': level,
                'message': message,
                'hour': hour
            })
    return logs

def get_top_errors(logs):
    error_msgs = [log['message'] for log in logs if log['level'] in ('ERROR', 'CRITICAL')]
    if not error_msgs:
        return []
    counter = Counter(error_msgs)
    return counter.most_common(5)

def main():
    if not os.path.exists('server.log'):
        with open('server.log', 'w') as f:
            for _ in range(1000):
                f.write(generate_fake_log() + '\n')
        print("Generated fake server.log with 1000 entries.")
    else:
        print("Using existing server.log.")
    
    logs = parse_log('server.log')
    top_errors = get_top_errors(logs)
    
    data_to_pass = {
        'logs': logs,
        'levels': ['INFO', 'WARN', 'ERROR', 'CRITICAL'],
        'top_errors': top_errors
    }
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Log Analytics Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; }
            #pieChart, #lineChart, #topErrors { border: 1px solid black; padding: 10px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid black; padding: 8px; text-align: left; }
        </style>
    </head>
    <body>
        <h1>Log Analytics Dashboard</h1>
        <select id="levelFilter">
            <option value="all">All</option>
            <option value="error">Error</option>
            <option value="alert">Alert</option>
        </select>
        <input type="text" id="searchInput" placeholder="Search critical errors...">
        
        <div id="pieChart"></div>
        <div id="lineChart"></div>
        <div id="topErrors">
            <h3>Top Error Messages</h3>
            <table>
                <thead><tr><th>Error Message</th><th>Count</th></tr></thead>
                <tbody id="topErrorsBody"></tbody>
            </table>
        </div>
        
        <table id="criticalTable">
            <thead><tr><th>Timestamp</th><th>Message</th></tr></thead>
            <tbody></tbody>
        </table>
        
        <script>
            const data = {{DATA}};
            
            function updateDashboard() {
                const selectedLevel = document.getElementById('levelFilter').value;
                const searchQuery = document.getElementById('searchInput').value.toLowerCase();
                
                let filteredLogs = data.logs;
                if (selectedLevel !== 'all') {
                    const includeLevels = selectedLevel === 'error' ? ['ERROR', 'CRITICAL'] : 
                                          selectedLevel === 'alert' ? ['CRITICAL'] : 
                                          ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
                    filteredLogs = data.logs.filter(log => includeLevels.includes(log.level));
                }
                
                const pieData = computePieChartData(filteredLogs);
                drawPieChart(pieData);
                
                const lineData = computeLineChartData(data.logs);
                drawLineChart(lineData);
                
                updateCriticalTable(searchQuery);
                updateTopErrors();
            }
            
            function computePieChartData(logs) {
                if (!logs.length) return {};
                const counts = {};
                logs.forEach(log => counts[log.level] = (counts[log.level]||0)+1);
                const total = Object.values(counts).reduce((a,b)=>a+b,0);
                return Object.entries(counts).map(([level, count]) => ({
                    level: level,
                    percent: (count/total*100).toFixed(1)
                }));
            }
            
            function computeLineChartData(allLogs) {
                const errors = allLogs.filter(log => log.level in ['ERROR', 'CRITICAL']);
                const hourly = {};
                errors.forEach(log => hourly[log.hour] = (hourly[log.hour]||0)+1);
                return Object.entries(hourly).map(([h,c]) => ({x: parseInt(h,10), y: c}));
            }
            
            function drawPieChart(data) {
                const svg = document.getElementById('pieChart');
                svg.innerHTML = '';
                if (!data.length) return;
                const total = data.reduce((sum, d)=>parseFloat(d.percent)+sum, 0);
                const radius = 100;
                const center = [150, 150];
                const svgNS = "http://www.w3.org/2000/svg";
                const svgElem = document.createElementNS(svgNS, 'svg');
                svgElem.setAttribute('width', '300');
                svgElem.setAttribute('height', '300');
                svg.appendChild(svgElem);
                
                let angle = 0;
                data.forEach(slice => {
                    const percent = parseFloat(slice.percent) / total * 2 * Math.PI;
                    const endAngle = angle + percent;
                    const path = `M ${center[0]} ${center[1]} ` +
                                `A ${radius} ${radius} 0 1 1 ${center[0] + radius * Math.cos(endAngle)} ${center[1] + radius * Math.sin(endAngle)} ` +
                                `Z`;
                    const pathElem = document.createElementNS(svgNS, 'path');
                    pathElem.setAttribute('d', path);
                    pathElem.setAttribute('fill', randomColor());
                    svgElem.appendChild(pathElem);
                    angle = endAngle;
                });
            }
            
            function drawLineChart(data) {
                const svg = document.getElementById('lineChart');
                svg.innerHTML = '';
                if (!data.length) return;
                const svgNS = "http://www.w3.org/2000/svg";
                const svgElem = document.createElementNS(svgNS, 'svg');
                svgElem.setAttribute('width', '500');
                svgElem.setAttribute('height', '200');
                svg.appendChild(svgElem);
                
                const maxCount = Math.max(...data.map(d=>d.y));
                const yScale = (y) => 200 - (y * 200 / maxCount);
                
                const line = document.createElementNS(svgNS, 'path');
                line.setAttribute('d', 'M ' + data.map(function(d) { return d.x*2 + ',' + yScale(d.y); }).join(' L ') + ' Z');
                line.setAttribute('stroke', 'steelblue');
                line.setAttribute('stroke-width', '2');
                svgElem.appendChild(line);
                
                data.forEach(point => {
                    const x = point.x * 2 + 10;
                    const y = 190;
                    const text = document.createElementNS(svgNS, 'text');
                    text.setAttribute('x', x);
                    text.setAttribute('y', y);
                    text.textContent = point.x;
                    svgElem.appendChild(text);
                });
            }
            
            function randomColor() {
                const [r, g, b] = Array(3).fill().map(() => Math.floor(Math.random()*256));
                return `rgb(${r}, ${g}, ${b})`;
            }
            
            function updateCriticalTable(query) {
                const tableBody = document.querySelector('#criticalTable tbody');
                tableBody.innerHTML = '';
                data.logs.filter(log => log.level === 'CRITICAL')
                    .forEach(log => {
                        if (log.message.toLowerCase().includes(query)) {
                            const row = document.createElement('tr');
                            row.innerHTML = `<td>${log.timestamp}</td><td>${log.message}</td>`;
                            tableBody.appendChild(row);
                        }
                    });
            }
            
            function updateTopErrors() {
                const topErrorsBody = document.getElementById('topErrorsBody');
                topErrorsBody.innerHTML = '';
                const errors = data.top_errors || [];
                errors.forEach(entry => {
                    const row = document.createElement('tr');
                    row.innerHTML = `<td>${entry[0]}</td><td>${entry[1]}</td>`;
                    topErrorsBody.appendChild(row);
                });
            }
            
            document.getElementById('levelFilter').onchange = updateDashboard;
            document.getElementById('searchInput').oninput = updateDashboard;
            updateDashboard();
        </script>
    </body>
    </html>
    """
    
    html_content = html_template.replace('{{DATA}}', json.dumps(data_to_pass))
    
    with open('index.html', 'w') as f:
        f.write(html_content)
    
    print("Dashboard available at http://localhost:8000")
    
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
    
if __name__ == '__main__':
    main()