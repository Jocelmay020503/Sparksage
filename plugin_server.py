#!/usr/bin/env python
"""Simple HTTP server for plugin downloads testing."""
import http.server
import socketserver
import os
from pathlib import Path

# Change to plugins_downloads directory
os.chdir('plugins_downloads')

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[HTTP] {format % args}")

PORT = 8001
Handler = MyHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"🚀 Plugin download server running on http://localhost:{PORT}")
    print(f"📦 Serving plugins from: {Path('plugins_downloads').absolute()}")
    print("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped")
