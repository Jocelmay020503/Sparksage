#!/usr/bin/env python
"""Test plugin installation workflow."""
import sys
sys.path.insert(0, '.')

from api.routes.plugins import _install_plugin_from_zip
from pathlib import Path
import shutil

# Clean up any existing hello_test plugin
test_plugin_dir = Path('plugins/hello_test')
if test_plugin_dir.exists():
    shutil.rmtree(test_plugin_dir)
    print(f"✓ Cleaned up existing {test_plugin_dir}")

# Test installation
print("\n🔄 Testing plugin installation from HTTP server...")
success, message, status_code = _install_plugin_from_zip(
    "http://localhost:8001/hello_test.zip",
    "hello_test"
)

print(f"Result: {message}")
print(f"Success: {success}")
print(f"Status code: {status_code}")

# Verify installation
if test_plugin_dir.exists():
    print(f"✅ Plugin directory created: {test_plugin_dir}")
    manifest = test_plugin_dir / "hello_test" / "manifest.json"
    if manifest.exists():
        print(f"✅ Manifest found: {manifest}")
    cog = test_plugin_dir / "hello_test" / "hello_test.py"
    if cog.exists():
        print(f"✅ Cog file found: {cog}")
else:
    print(f"❌ Plugin directory NOT created")
