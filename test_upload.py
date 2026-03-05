#!/usr/bin/env python3
"""Quick test to verify /api/plugins/upload endpoint is registered."""
import sys
sys.path.insert(0, '.')

from api.main import create_app

app = create_app()

print("=" * 60)
print("Checking registered routes for /plugins/upload:")
print("=" * 60)

upload_found = False
for route in app.routes:
    if hasattr(route, 'path') and '/upload' in route.path:
        methods = getattr(route, 'methods', set())
        print(f"✓ Found: {route.path} -> Methods: {methods}")
        if 'POST' in methods:
            upload_found = True

if upload_found:
    print("\n✅ POST /api/plugins/upload is properly registered!")
else:
    print("\n❌ POST /api/plugins/upload NOT FOUND in routes!")
    print("\nAll plugin routes:")
    for route in app.routes:
        if hasattr(route, 'path') and '/api/plugins' in route.path:
            methods = getattr(route, 'methods', set())
            print(f"  {route.path} -> {methods}")
