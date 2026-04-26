"""
Watch both output folders and re-run compare_chapters.py whenever any
*_chapters.txt file changes. Refreshes every 500 ms.

Run:  python watch_compare.py
Output is written to compare_output.txt and also printed to console.
Open compare_output.txt in VS Code — it will auto-update (VS Code
detects file changes on disk and refreshes the editor view).
"""

import os
import time
import subprocess
import sys

WATCH_DIRS = [
    'output/volumes',
    'text_to_volumes/output',
]
INTERVAL = 0.5  # seconds

def get_mtimes():
    mtimes = {}
    for d in WATCH_DIRS:
        for f in os.listdir(d):
            if f.endswith('_chapters.txt'):
                p = os.path.join(d, f)
                mtimes[p] = os.path.getmtime(p)
    return mtimes

def run_compare():
    result = subprocess.run(
        [sys.executable, 'compare_chapters.py'],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    output = result.stdout + (result.stderr if result.stderr else '')
    with open('compare_output.txt', 'w', encoding='utf-8') as f:
        f.write(output)
    # Print a summary to console
    for line in output.splitlines():
        if any(x in line for x in ['Volume', 'Line diff', 'ONLY IN', 'structural', 'IDENTICAL', '===']):
            print(line)

prev_mtimes = {}
print('Watching for changes... (Ctrl+C to stop)')
print('Open compare_output.txt in VS Code to see live results.')
print()

while True:
    try:
        mtimes = get_mtimes()
        if mtimes != prev_mtimes:
            changed = [k for k in mtimes if mtimes[k] != prev_mtimes.get(k)]
            if changed:
                print(f'\n[{time.strftime("%H:%M:%S")}] Changed: {", ".join(os.path.basename(c) for c in changed)}')
            run_compare()
            prev_mtimes = mtimes
        time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print('\nStopped.')
        break
