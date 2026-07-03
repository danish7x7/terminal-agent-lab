#!/usr/bin/env python3
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler

CORRECT_USER = 'admin'
CORRECT_PASS = 'sunshine'

class AuthHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass
    def do_GET(self):
        if self.path != '/secret':
            self.send_response(404)
            self.end_headers()
            return
        auth = self.headers.get('Authorization', '')
        if auth.startswith('Basic '):
            try:
                decoded = base64.b64decode(auth[6:]).decode()
                user, pwd = decoded.split(':', 1)
                if user == CORRECT_USER and pwd == CORRECT_PASS:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'OK')
                    return
            except Exception:
                pass
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="secret"')
        self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 7777), AuthHandler)
    server.serve_forever()
