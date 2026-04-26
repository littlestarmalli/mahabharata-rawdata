"""Check speaker coverage and color availability."""
import json, os

# Get all speakers used in dialogs and their counts
speakers = {}
for v in range(1, 11):
    d = os.path.join('output', 'dialogs', f'volume_{v}')
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.json'): continue
        data = json.load(open(os.path.join(d, fname), encoding='utf-8'))
        for para in data['paragraphs']:
            for seg in para['segments']:
                sp = seg.get('speaker', '?')
                speakers[sp] = speakers.get(sp, 0) + 1

# Load character colors
chars = json.load(open('output/json/characters.json', encoding='utf-8'))

print(f'Total unique speakers: {len(speakers)}')
print()

has_color_count = 0
no_color_count = 0
no_color_segs = 0

for sp, cnt in sorted(speakers.items(), key=lambda x: -x[1])[:40]:
    color = ''
    label = sp
    if sp in chars:
        disp = chars[sp].get('display', {})
        color = disp.get('color', '')
        label = disp.get('label', chars[sp].get('Name', sp))
    if color:
        has_color_count += 1
        print(f'  {sp:35s}  segs={cnt:6d}  color={color}  ({label})')
    else:
        no_color_count += 1
        no_color_segs += cnt
        print(f'  {sp:35s}  segs={cnt:6d}  NO COLOR  ({label})')

print(f'\nWith color: {has_color_count}  Without: {no_color_count} ({no_color_segs} segments)')
