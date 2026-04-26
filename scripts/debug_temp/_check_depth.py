"""Quick check for deep nesting in dialog files."""
import json, os

def max_depth(node, d=0):
    if isinstance(node, str):
        return d
    if isinstance(node, dict):
        return max((max_depth(c, d+1) for c in node['c']), default=d+1)
    if isinstance(node, list):
        return max((max_depth(c, d) for c in node), default=d)
    return d

for vol in range(1, 11):
    vol_dir = f'output/dialogs/volume_{vol}'
    for fn in sorted(os.listdir(vol_dir)):
        path = os.path.join(vol_dir, fn)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        d = max_depth(data['dialog'])
        if d > 10:
            ch = data.get('chapter', '?')
            print(f"V{vol} ch {ch}: depth {d}")
