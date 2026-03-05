import zipfile
import os
from pathlib import Path

# Create plugins_downloads folder
Path('plugins_downloads').mkdir(exist_ok=True)

# Create ZIP of test plugin
with zipfile.ZipFile('plugins_downloads/hello_test.zip', 'w') as zf:
    zf.write('test_plugin_zip/hello_test/manifest.json', 'hello_test/manifest.json')
    zf.write('test_plugin_zip/hello_test/hello_test.py', 'hello_test/hello_test.py')

print('Created hello_test.zip')
print(f'Size: {os.path.getsize("plugins_downloads/hello_test.zip")} bytes')
