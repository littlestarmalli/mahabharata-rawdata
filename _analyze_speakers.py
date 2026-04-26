"""Analyze depth-0 attributions: speech vs bare, and narrator frame transitions."""
import re, os, json

attr_re = re.compile(r'^(\w[\w\s]*?)\s+(said|continued|asked|replied|spoke|resumed|answered),\s*', re.IGNORECASE)

patterns = {}  # speaker -> {has_speech, bare_only, examples}

for v in range(1, 11):
    d = os.path.join('output', 'dialogs', f'volume_{v}')
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.json'): continue
        data = json.load(open(os.path.join(d, fname), encoding='utf-8'))
        for para in data['paragraphs']:
            segs = para['segments']
            for i, seg in enumerate(segs):
                if seg.get('depth', 0) != 0: continue
                m = attr_re.match(seg['text'])
                if not m: continue
                speaker = m.group(1).strip()
                if speaker not in patterns:
                    patterns[speaker] = {'has_speech': 0, 'bare_only': 0, 'examples': []}
                # Check if next segment goes deeper
                has_deeper = any(s.get('depth', 0) > 0 for s in segs[i+1:])
                if has_deeper:
                    patterns[speaker]['has_speech'] += 1
                else:
                    patterns[speaker]['bare_only'] += 1
                    if len(patterns[speaker]['examples']) < 3:
                        ch = data['chapter']
                        txt = seg['text'][:80].encode('ascii', 'replace').decode()
                        patterns[speaker]['examples'].append(f'ch{ch}: {txt}')

print('=== Depth-0 attribution analysis ===')
print(f'{"Speaker":25s}  {"Speech":>6s}  {"Bare":>6s}')
print('-' * 50)
for sp, info in sorted(patterns.items(), key=lambda x: -(x[1]['has_speech']+x[1]['bare_only'])):
    hs = info['has_speech']
    bo = info['bare_only']
    print(f'  {sp:25s}  {hs:6d}  {bo:6d}')
    for ex in info['examples']:
        print(f'    bare: {ex}')

# Also check: what narrators appear at each depth level
print('\n=== Attributions by depth level ===')
depth_speakers = {}
for v in range(1, 11):
    d = os.path.join('output', 'dialogs', f'volume_{v}')
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.json'): continue
        data = json.load(open(os.path.join(d, fname), encoding='utf-8'))
        for para in data['paragraphs']:
            for seg in para['segments']:
                depth = seg.get('depth', 0)
                m = attr_re.match(seg['text'])
                if m:
                    speaker = m.group(1).strip()
                    key = (depth, speaker)
                    depth_speakers[key] = depth_speakers.get(key, 0) + 1

for depth in sorted(set(k[0] for k in depth_speakers)):
    print(f'\n  Depth {depth}:')
    speakers_at_d = {k[1]: v for k, v in depth_speakers.items() if k[0] == depth}
    for sp, cnt in sorted(speakers_at_d.items(), key=lambda x: -x[1])[:10]:
        print(f'    {sp:30s} {cnt:5d}')
