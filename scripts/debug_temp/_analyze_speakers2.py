"""Full speaker analysis at all depths, including inside quoted frames."""
import re, os, json

attr_re = re.compile(r'^(\w[\w\s]*?)\s+(said|continued|asked|replied|spoke|resumed|answered),\s*', re.IGNORECASE)

depth_speakers = {}

for v in range(1, 11):
    d = os.path.join('output', 'dialogs', f'volume_{v}')
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.json'): continue
        data = json.load(open(os.path.join(d, fname), encoding='utf-8'))
        for para in data['paragraphs']:
            for seg in para['segments']:
                depth = seg.get('depth', 0)
                text = seg['text']
                # Check both start of segment and within
                m = attr_re.match(text)
                if m:
                    speaker = m.group(1).strip()
                    key = (depth, speaker)
                    depth_speakers[key] = depth_speakers.get(key, 0) + 1

for depth in sorted(set(k[0] for k in depth_speakers)):
    speakers_at_d = {k[1]: v for k, v in depth_speakers.items() if k[0] == depth}
    total = sum(speakers_at_d.values())
    print(f'\nDepth {depth} ({total} attributions):')
    for sp, cnt in sorted(speakers_at_d.items(), key=lambda x: -x[1])[:15]:
        print(f'  {sp:35s} {cnt:5d}')
    remaining = len(speakers_at_d) - 15
    if remaining > 0:
        print(f'  ... and {remaining} more speakers')

# Summary
print('\n=== FRAME MODEL SUMMARY ===')
print('Depth 0 = "Author" level (actually Souti narrating, but quotes missing)')
print('  -> Souti said / Shounaka said = outermost frame')  
print('  -> Vaishampayana said / Janamejaya said = should be inside Souti frame')
print()

# Count total segments by depth
depth_counts = {}
for v in range(1, 11):
    d = os.path.join('output', 'dialogs', f'volume_{v}')
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.json'): continue
        data = json.load(open(os.path.join(d, fname), encoding='utf-8'))
        for para in data['paragraphs']:
            for seg in para['segments']:
                depth = seg.get('depth', 0)
                stype = seg.get('type', 'narration')
                key = (depth, stype)
                depth_counts[key] = depth_counts.get(key, 0) + 1

print('\n=== SEGMENT COUNTS BY DEPTH AND TYPE ===')
for depth in sorted(set(k[0] for k in depth_counts)):
    types = {k[1]: v for k, v in depth_counts.items() if k[0] == depth}
    parts = ', '.join(f'{t}={c}' for t, c in sorted(types.items(), key=lambda x: -x[1]))
    print(f'  depth {depth}: {parts}  (total={sum(types.values())})')
