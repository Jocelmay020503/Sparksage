#!/usr/bin/env python3
from api.main import create_app

app = create_app()
print("Checking for /upload route...")
for route in app.routes:
    path = getattr(route, 'path', '')
    if '/upload' in path:
        methods = getattr(route, 'methods', set())
        print(f"Found: {path} -> {methods}")
