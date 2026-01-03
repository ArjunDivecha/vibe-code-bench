import http.server
import json

class LogHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/log':
            level = self.path.split('?level=')[1]
            with open('server.log', 'r') as f:
                logs = []
                for line in f:
                    timestamp, log_level, message = line.strip().split(' ', 2)
                    if log_level == level or level == 'All':
                        logs.append({'timestamp': timestamp, 'level': log_level, 'message': message})
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(logs).encode())
        elif self.path == '/levels':
            with open('server.log', 'r') as f:
                logs = []
                for line in f:
                    timestamp, log_level, message = line.strip().split(' ', 2)
                    logs.append(log_level)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({level: logs.count(level) for level in set(logs)}).encode())
        elif self.path == '/errors':
            with open('server.log', 'r') as f:
                logs = {}
                for line in f:
                    timestamp, log_level, message = line.strip().split(' ', 2)
                    if log_level == 'ERROR':
                        hour = int(timestamp[:11])
                        logs[hour] = logs.get(hour, 0) + 1
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(logs).encode())
        elif self.path == '/criticals':
            with open('server.log', 'r') as f:
                logs = []
                for line in f:
                    timestamp, log_level, message = line.strip().split(' ', 2)
                    if log_level == 'CRITICAL':
                        logs.append(message)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(logs).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    with http.server.HTTPServer(('localhost', 8000), LogHandler) as httpd:
        print('Log server running at http://localhost:8000')
        httpd.serve_forever()