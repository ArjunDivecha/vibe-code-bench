import os
import http.server
import socketserver
import json
import collections
import random
from datetime import datetime, timedelta

# Generate fake log data if server.log doesn't exist
if not os.path.exists('server.log'):
    with open('server.log', 'w') as f:
        for _ in range(1000):
            timestamp = (datetime.now() - timedelta(days=random.randint(0, 10))).isoformat() + 'Z'
            level = random.choice(['INFO', 'WARN', 'ERROR', 'CRITICAL'])
            message = f'Random {level} message: {random.randint(1000, 9999)}'
            f.write(f'{timestamp} {level} {message}\n')

class LogAnalyzer(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        with open('index.html') as f:
            self.wfile.write(f.read().encode())

class LogServer(socketserver.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        socketserver.TCPServer.server_bind(self)
        self.server_address

def parse_log(filename):
    levels = collections.Counter()
    errors = collections.defaultdict(int)
    criticals = []

    with open(filename, 'r') as f:
        for line in f:
            timestamp, level, message = line.strip().split(' ', 2)
            levels[level] += 1
            if level == 'CRITICAL':
                criticals.append(f'{timestamp} {level} {message}')
            elif level == 'ERROR':
                hour = int(timestamp[:11])
                errors[hour] += 1

    return levels, errors, criticals

def main():
    print('Log Analytics Dashboard')
    print('-------------------------')
    levels, errors, criticals = parse_log('server.log')

    print('Levels:')
    for level, count in levels.items():
        print(f'{level}: {count * 100 / sum(levels.values()):.2f}%')

    print('Errors per hour:')
    for hour, count in errors.items():
        print(f'{hour}: {count}')

    print('Most common error messages:')
    criticals.sort()
    for message in criticals[:10]:
        print(message)

    with LogServer(('localhost', 8000), LogAnalyzer) as httpd:
        print('Server running at http://localhost:8000')
        httpd.serve_forever()

if __name__ == '__main__':
    main()