#!/usr/bin/env python3
"""
Log Analytics Dashboard
A self-contained script that generates log data, analyzes it, and serves a web dashboard.
"""

import http.server
import json
import os
import random
import socketserver
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import re

PORT = 8000
LOG_FILE = "server.log"

# Log level configuration
LOG_LEVELS = ["INFO", "WARN", "ERROR", "CRITICAL"]
LOG_LEVEL_WEIGHTS = [0.5, 0.25, 0.15, 0.1]

# Error messages for each level
ERROR_MESSAGES = {
    "INFO": [
        "User logged in successfully", "Database connection established", "Cache cleared",
        "Backup completed", "Health check passed", "Session created", "API request processed",
        "File uploaded successfully", "Email sent to user", "Configuration reloaded",
        "Cache warmup completed", "Service initialization complete", "Queue processor started",
        "Cron job executed", "Metric collection successful"
    ],
    "WARN": [
        "High memory usage detected", "Slow database query detected", "Rate limit approaching",
        "Deprecated API endpoint accessed", "Disk space running low", "Connection pool nearly exhausted",
        "Token expiring soon", "Retry attempt failed", "Cache miss rate increasing",
        "Service latency above threshold", "Socket buffer nearly full", "Thread pool usage high",
        "Authentication retry needed", "Temporary network hiccup", "License expiring soon"
    ],
    "ERROR": [
        "Database connection failed", "Authentication service unreachable", "Payment gateway timeout",
        "Invalid input validation failed", "File not found exception", "Memory allocation error",
        "Network connection lost", "API rate limit exceeded", "Serialization error",
        "Configuration parsing failed", "External API call failed", "Query timeout expired",
        "Lock acquisition failed", "Disk I/O error", "Permission denied"
    ],
    "CRITICAL": [
        "System crash imminent", "Database corruption detected", "Security breach attempt",
        "Complete service outage", "Data integrity violation", "Hard disk failure predicted",
        "Critical security vulnerability", "Master database unavailable", "All nodes unresponsive",
        "Catastrophic failure", "Kernel panic", "Memory corruption detected", "RAID array degraded",
        "SSL certificate expired", "Firewall breach detected"
    ]
}

def generate_fake_logs():
    """Generate 1000 lines of fake log data if file doesn't exist."""
    print(f"Generating {LOG_FILE} with 1000 log entries...")
    
    # Generate timestamps over the last 7 days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    total_seconds = (end_time - start_time).total_seconds()
    
    logs = []
    for i in range(1000):
        # Random timestamp spread over 7 days
        random_seconds = random.randint(0, int(total_seconds))
        timestamp = start_time + timedelta(seconds=random_seconds)
        
        # Choose log level based on weights
        log_level = random.choices(LOG_LEVELS, weights=LOG_LEVEL_WEIGHTS)[0]
        
        # Choose random error message for the level
        message = random.choice(ERROR_MESSAGES[log_level])
        
        # Add some variation to messages
        if log_level in ["ERROR", "CRITICAL"] and random.random() < 0.3:
            message += f" - Resource: {random.choice(['/api/users', '/api/orders', '/api/payments', '/db/queries', '/cache'])}"
        
        log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {log_level:8} | {message}"
        logs.append(log_line)
    
    # Sort by timestamp
    logs.sort(key=lambda x: datetime.strptime(x.split(" | ")[0], '%Y-%m-%d %H:%M:%S'))
    
    with open(LOG_FILE, 'w') as f:
        f.write('\n'.join(logs))
    
    print(f"Generated {LOG_FILE} with {len(logs)} entries.")

def parse_log_file():
    """Parse the log file and extract structured data."""
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
    
    pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\|\s*(\w+)\s*\|\s*(.+)$')
    
    logs = []
    with open(LOG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if match:
                timestamp_str, level, message = match.groups()
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
                logs.append({
                    'timestamp': timestamp.isoformat(),
                    'level': level,
                    'message': message
                })
    
    return logs

def analyze_logs(logs):
    """Analyze log data and extract statistics."""
    if not logs:
        return {
            'level_percentages': {},
            'errors_per_hour': {},
            'top_errors': [],
            'total_count': 0
        }
    
    # Count log levels
    level_counts = Counter(log['level'] for log in logs)
    total = len(logs)
    level_percentages = {
        level: round((count / total) * 100, 2) 
        for level, count in level_counts.items()
    }
    
    # Errors per hour
    hourly_errors = defaultdict(int)
    for log in logs:
        if log['level'] in ['ERROR', 'CRITICAL']:
            timestamp = datetime.fromisoformat(log['timestamp'])
            hour_key = timestamp.strftime('%Y-%m-%d %H:00')
            hourly_errors[hour_key] += 1
    
    # Sort hours chronologically
    sorted_hours = sorted(hourly_errors.keys())
    errors_per_hour = {hour: hourly_errors[hour] for hour in sorted_hours}
    
    # Fill in missing hours with 0
    if sorted_hours:
        start_hour = datetime.strptime(sorted_hours[0], '%Y-%m-%d %H:%M')
        end_hour = datetime.strptime(sorted_hours[-1], '%Y-%m-%d %H:%M')
        current = start_hour
        while current <= end_hour:
            hour_key = current.strftime('%Y-%m-%d %H:00')
            if hour_key not in errors_per_hour:
                errors_per_hour[hour_key] = 0
            current += timedelta(hours=1)
    
    # Top error messages (ERROR and CRITICAL)
    error_logs = [log for log in logs if log['level'] in ['ERROR', 'CRITICAL']]
    error_messages = [log['message'] for log in error_logs]
    top_errors = Counter(error_messages).most_common(10)
    top_errors = [{'message': msg, 'count': count} for msg, count in top_errors]
    
    return {
        'level_percentages': level_percentages,
        'errors_per_hour': errors_per_hour,
        'top_errors': top_errors,
        'total_count': total
    }

def get_critical_errors(logs):
    """Extract all CRITICAL errors."""
    return [log for log in logs if log['level'] == 'CRITICAL']

# HTML Dashboard Template
DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log Analytics Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }
        
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }
        
        .stats-bar {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #00d4ff;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #888;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .card h2 {
            font-size: 1.2rem;
            margin-bottom: 15px;
            color: #00d4ff;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card h2::before {
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(180deg, #00d4ff, #7b2cbf);
            border-radius: 2px;
        }
        
        /* Level Percentages */
        .level-bars {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .level-bar {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .level-label {
            width: 80px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .level-track {
            flex: 1;
            height: 24px;
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            overflow: hidden;
            position: relative;
        }
        
        .level-fill {
            height: 100%;
            border-radius: 12px;
            transition: width 1s ease-out;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            font-size: 0.8rem;
            font-weight: bold;
            color: white;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }
        
        .level-fill.INFO { background: linear-gradient(90deg, #00b894, #00cec9); }
        .level-fill.WARN { background: linear-gradient(90deg, #fdcb6e, #f39c12); }
        .level-fill.ERROR { background: linear-gradient(90deg, #e17055, #d63031); }
        .level-fill.CRITICAL { background: linear-gradient(90deg, #6c5ce7, #a29bfe); }
        
        /* Timeline Chart */
        .timeline-container {
            width: 100%;
            height: 200px;
            position: relative;
        }
        
        #timeline-svg {
            width: 100%;
            height: 100%;
        }
        
        .timeline-bar {
            transition: opacity 0.3s ease;
        }
        
        .timeline-bar:hover {
            opacity: 0.8;
        }
        
        /* Top Errors */
        .top-errors {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .error-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            transition: background 0.3s ease;
        }
        
        .error-item:hover {
            background: rgba(255,255,255,0.1);
        }
        
        .error-count {
            min-width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #d63031, #e17055);
            border-radius: 8px;
            font-weight: bold;
            font-size: 0.9rem;
        }
        
        .error-message {
            flex: 1;
            font-size: 0.9rem;
            word-break: break-word;
        }
        
        /* Critical Errors Table */
        .critical-section {
            grid-column: 1 / -1;
        }
        
        .filter-bar {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .filter-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            background: rgba(255,255,255,0.1);
            color: #e0e0e0;
        }
        
        .filter-btn:hover {
            background: rgba(255,255,255,0.2);
        }
        
        .filter-btn.active {
            background: linear-gradient(135deg, #00d4ff, #7b2cbf);
            color: white;
        }
        
        .search-input {
            flex: 1;
            min-width: 200px;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            background: rgba(255,255,255,0.1);
            color: #e0e0e0;
            font-size: 1rem;
            transition: background 0.3s ease;
        }
        
        .search-input:focus {
            outline: none;
            background: rgba(255,255,255,0.15);
        }
        
        .search-input::placeholder {
            color: #888;
        }
        
        .table-container {
            overflow-x: auto;
            max-height: 500px;
            overflow-y: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        th {
            background: rgba(0,0,0,0.3);
            position: sticky;
            top: 0;
            font-weight: 600;
            color: #00d4ff;
        }
        
        tr:hover {
            background: rgba(255,255,255,0.05);
        }
        
        .level-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .level-badge.ERROR {
            background: rgba(214, 48, 49, 0.2);
            color: #ff7675;
        }
        
        .level-badge.CRITICAL {
            background: rgba(108, 92, 231, 0.2);
            color: #a29bfe;
        }
        
        .level-badge.ALERT {
            background: rgba(253, 203, 110, 0.2);
            color: #ffeaa7;
        }
        
        .timestamp-col {
            white-space: nowrap;
            font-family: monospace;
        }
        
        .message-col {
            max-width: 500px;
            word-break: break-word;
        }
        
        .no-results {
            text-align: center;
            padding: 40px;
            color: #888;
            font-size: 1.1rem;
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .card {
            animation: fadeIn 0.5s ease-out forwards;
        }
        
        .card:nth-child(2) { animation-delay: 0.1s; }
        .card:nth-child(3) { animation-delay: 0.2s; }
        .card:nth-child(4) { animation-delay: 0.3s; }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.05);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.2);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255,255,255,0.3);
        }
        
        @media (max-width: 768px) {
            h1 { font-size: 1.8rem; }
            .grid { grid-template-columns: 1fr; }
            .stats-bar { gap: 15px; }
            .stat-value { font-size: 1.5rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Log Analytics Dashboard</h1>
            <div class="stats-bar">
                <div class="stat-item">
                    <div class="stat-value" id="total-logs">-</div>
                    <div class="stat-label">Total Logs</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="total-errors">-</div>
                    <div class="stat-label">Errors & Critical</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="unique-errors">-</div>
                    <div class="stat-label">Unique Errors</div>
                </div>
            </div>
        </header>
        
        <div class="grid">
            <div class="card">
                <h2>Log Level Distribution</h2>
                <div class="level-bars" id="level-bars"></div>
            </div>
            
            <div class="card">
                <h2>Errors Timeline (Hourly)</h2>
                <div class="timeline-container">
                    <svg id="timeline-svg"></svg>
                </div>
            </div>
            
            <div class="card">
                <h2>Most Common Errors</h2>
                <div class="top-errors" id="top-errors"></div>
            </div>
        </div>
        
        <div class="card critical-section">
            <h2>⚠️ Critical Errors Log</h2>
            <div class="filter-bar">
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="ERROR">Error</button>
                <button class="filter-btn" data-filter="CRITICAL">Critical</button>
                <input type="text" class="search-input" id="search-input" placeholder="Search error messages...">
            </div>
            <div class="table-container">
                <table id="errors-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Level</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody id="errors-tbody"></tbody>
                </table>
            </div>
            <div class="no-results" id="no-results" style="display: none;">No matching errors found</div>
        </div>
    </div>
    
    <script>
        let allData = null;
        let filteredData = null;
        let currentFilter = 'all';
        let searchTerm = '';
        
        async function loadData() {
            try {
                const response = await fetch('/api/data');
                allData = await response.json();
                filteredData = allData.critical_errors;
                renderDashboard();
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }
        
        function renderDashboard() {
            renderStats();
            renderLevelBars();
            renderTimeline();
            renderTopErrors();
            renderErrorsTable();
        }
        
        function renderStats() {
            const analysis = allData.analysis;
            document.getElementById('total-logs').textContent = analysis.total_count.toLocaleString();
            
            const errors = (analysis.level_percentages['ERROR'] || 0) + (analysis.level_percentages['CRITICAL'] || 0);
            document.getElementById('total-errors').textContent = errors.toFixed(1) + '%';
            
            document.getElementById('unique-errors').textContent = analysis.top_errors.length;
        }
        
        function renderLevelBars() {
            const container = document.getElementById('level-bars');
            const percentages = allData.analysis.level_percentages;
            
            const levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL'];
            const labels = { 'INFO': 'Info', 'WARN': 'Warning', 'ERROR': 'Error', 'CRITICAL': 'Critical' };
            
            container.innerHTML = levels.map(level => {
                const value = percentages[level] || 0;
                return `
                    <div class="level-bar">
                        <span class="level-label">${labels[level]}</span>
                        <div class="level-track">
                            <div class="level-fill ${level}" style="width: 0%" data-width="${value}%">
                                ${value.toFixed(1)}%
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            
            // Animate bars
            setTimeout(() => {
                document.querySelectorAll('.level-fill').forEach(bar => {
                    bar.style.width = bar.dataset.width;
                });
            }, 100);
        }
        
        function renderTimeline() {
            const svg = document.getElementById('timeline-svg');
            const data = allData.analysis.errors_per_hour;
            const hours = Object.keys(data);
            const values = Object.values(data);
            
            if (hours.length === 0) {
                svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#888">No error data available</text>';
                return;
            }
            
            const maxValue = Math.max(...values, 1);
            const width = svg.clientWidth || 600;
            const height = svg.clientHeight || 200;
            const padding = { top: 20, right: 20, bottom: 40, left: 50 };
            const chartWidth = width - padding.left - padding.right;
            const chartHeight = height - padding.top - padding.bottom;
            
            const barWidth = Math.min(chartWidth / hours.length - 4, 50);
            const barSpacing = (chartWidth - (barWidth * hours.length)) / (hours.length + 1);
            
            let svgContent = '';
            
            // Y-axis grid lines
            const gridLines = 5;
            for (let i = 0; i <= gridLines; i++) {
                const y = padding.top + (chartHeight / gridLines) * i;
                const value = Math.round(maxValue * (gridLines - i) / gridLines);
                svgContent += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>`;
                svgContent += `<text x="${padding.left - 10}" y="${y + 4}" text-anchor="end" fill="#888" font-size="12">${value}</text>`;
            }
            
            // Bars
            hours.forEach((hour, index) => {
                const value = values[index];
                const barHeight = (value / maxValue) * chartHeight;
                const x = padding.left + barSpacing + index * (barWidth + barSpacing);
                const y = padding.top + chartHeight - barHeight;
                
                const gradientId = `bar-gradient-${index}`;
                svgContent += `
                    <defs>
                        <linearGradient id="${gradientId}" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" style="stop-color:#e17055"/>
                            <stop offset="100%" style="stop-color:#d63031"/>
                        </linearGradient>
                    </defs>
                `;
                
                svgContent += `
                    <rect class="timeline-bar" x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" 
                          fill="url(#${gradientId})" rx="4"
                          data-hour="${hour}" data-value="${value}">
                        <title>${hour}: ${value} errors</title>
                    </rect>
                `;
            });
            
            // X-axis labels (show every nth label based on available space)
            const labelStep = Math.ceil(hours.length / 10);
            hours.forEach((hour, index) => {
                if (index % labelStep === 0) {
                    const x = padding.left + barSpacing + index * (barWidth + barSpacing) + barWidth / 2;
                    const y = height - 10;
                    const displayHour = new Date(hour).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', hour12: false });
                    svgContent += `<text x="${x}" y="${y}" text-anchor="middle" fill="#888" font-size="10" transform="rotate(-45, ${x}, ${y})">${displayHour}</text>`;
                }
            });
            
            svg.innerHTML = svgContent;
        }
        
        function renderTopErrors() {
            const container = document.getElementById('top-errors');
            const errors = allData.analysis.top_errors.slice(0, 5);
            
            if (errors.length === 0) {
                container.innerHTML = '<p style="color: #888; text-align: center;">No errors recorded</p>';
                return;
            }
            
            container.innerHTML = errors.map(error => `
                <div class="error-item">
                    <div class="error-count">${error.count}</div>
                    <div class="error-message">${escapeHtml(error.message)}</div>
                </div>
            `).join('');
        }
        
        function renderErrorsTable() {
            const tbody = document.getElementById('errors-tbody');
            const noResults = document.getElementById('no-results');
            
            const filtered = filterErrors();
            
            if (filtered.length === 0) {
                tbody.innerHTML = '';
                noResults.style.display = 'block';
                return;
            }
            
            noResults.style.display = 'none';
            tbody.innerHTML = filtered.map(log => {
                const date = new Date(log.timestamp);
                const formattedDate = date.toLocaleString('en-US', {
                    year: 'numeric', month: 'short', day: '2-digit',
                    hour: '2-digit', minute: '2-digit', second: '2-digit'
                });
                return `
                    <tr data-level="${log.level}">
                        <td class="timestamp-col">${formattedDate}</td>
                        <td><span class="level-badge ${log.level}">${log.level}</span></td>
                        <td class="message-col">${escapeHtml(log.message)}</td>
                    </tr>
                `;
            }).join('');
        }
        
        function filterErrors() {
            return allData.critical_errors.filter(log => {
                const matchesFilter = currentFilter === 'all' || log.level === currentFilter;
                const matchesSearch = !searchTerm || 
                    log.message.toLowerCase().includes(searchTerm.toLowerCase());
                return matchesFilter && matchesSearch;
            });
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Event Listeners
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                renderErrorsTable();
            });
        });
        
        document.getElementById('search-input').addEventListener('input', (e) => {
            searchTerm = e.target.value;
            renderErrorsTable();
        });
        
        // Initialize
        loadData();
        
        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>'''

class LogDashboardHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for the dashboard."""
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode('utf-8'))
        
        elif path == '/api/data':
            # Generate fresh analysis
            logs = parse_log_file()
            analysis = analyze_logs(logs)
            critical_errors = get_critical_errors(logs)
            
            response_data = json.dumps({
                'logs': logs,
                'analysis': analysis,
                'critical_errors': critical_errors
            }, default=str)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response_data.encode('utf-8'))
        
        elif path == '/api/refresh':
            # Force log file regeneration
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
            logs = parse_log_file()
            analysis = analyze_logs(logs)
            critical_errors = get_critical_errors(logs)
            
            response_data = json.dumps({
                'logs': logs,
                'analysis': analysis,
                'critical_errors': critical_errors
            }, default=str)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(response_data.encode('utf-8'))
        
        elif path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
        
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP server for handling concurrent requests."""
    allow_reuse_address = True
    daemon_threads = True

def main():
    """Main entry point."""
    print("=" * 60)
    print("        Log Analytics Dashboard")
    print("=" * 60)
    print()
    
    # Check if log file exists, if not generate it
    if not os.path.exists(LOG_FILE):
        generate_fake_logs()
    else:
        print(f"Found existing {LOG_FILE}")
        line_count = sum(1 for _ in open(LOG_FILE))
        print(f"  - {line_count} log entries")
    print()
    
    # Parse and analyze logs
    print("Analyzing log data...")
    logs = parse_log_file()
    analysis = analyze_logs(logs)
    critical_count = len(get_critical_errors(logs))
    print(f"  - Total logs: {analysis['total_count']}")
    print(f"  - Critical errors: {critical_count}")
    print()
    
    # Start the server
    try:
        server = ThreadedHTTPServer(('0.0.0.0', PORT), LogDashboardHandler)
        print("-" * 60)
        print(f"  🚀 Dashboard running at:")
        print(f"     http://localhost:{PORT}")
        print(f"     http://127.0.0.1:{PORT}")
        print("-" * 60)
        print()
        print("  Press Ctrl+C to stop the server")
        print()
        
        # Keep the log file updated periodically
        def refresh_logs():
            while True:
                time.sleep(60)  # Refresh every minute
                if os.path.exists(LOG_FILE):
                    pass  # Logs are read fresh on each request
        
        refresh_thread = threading.Thread(target=refresh_logs, daemon=True)
        refresh_thread.start()
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n  Shutting down server...")
        server.shutdown()
        print("  Server stopped. Goodbye!")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"  Error: Port {PORT} is already in use")
            print(f"  Try stopping other processes using port {PORT}")
        raise

if __name__ == '__main__':
    main()