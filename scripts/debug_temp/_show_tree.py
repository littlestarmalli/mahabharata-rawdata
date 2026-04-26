"""Show dialog tree structure for a chapter."""
import json, sys

path = sys.argv[1] if len(sys.argv) > 1 else 'output/dialogs/volume_1/chapter_0072.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

def show(node, indent=0):
    if isinstance(node, str):
        txt = node[:70] + ('...' if len(node) > 70 else '')
        print(' ' * indent + 'TEXT: ' + txt)
    elif isinstance(node, dict):
        q = node.get('q', '?')
        print(' ' * indent + 'SPEECH q=' + q + ':')
        for c in node['c']:
            show(c, indent + 2)
    elif isinstance(node, list):
        for c in node:
            show(c, indent)

print(f"Chapter {data['chapter']} (local {data['local']})")
print('=' * 60)
show(data['dialog'])
