"""Show top missed attribution patterns."""
import json, os, re

ATTR_LOOSE = re.compile(
    r'^\s*[\u2018\u201c]*\s*(\w[\w\s\'-]*?)\s+'
    r'(said|continued|asked|replied|spoke|resumed|answered|exclaimed),',
    re.IGNORECASE
)

missed = {}
for v in range(1, 11):
    d = os.path.join('output', 'dialogs', f'volume_{v}')
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.json'): continue
        data = json.load(open(os.path.join(d, fname), encoding='utf-8'))
        for para in data['paragraphs']:
            for seg in para['segments']:
                if seg.get('introduces'):
                    continue
                text = seg['text']
                m = ATTR_LOOSE.match(text)
                if m:
                    depth = seg.get('depth', 0)
                    speaker = m.group(1).strip()
                    key = speaker.lower()
                    if key not in missed:
                        missed[key] = {'count': 0, 'name': speaker, 'example': '', 'depths': set()}
                    missed[key]['count'] += 1
                    missed[key]['depths'].add(depth)
                    if not missed[key]['example']:
                        ch = data['chapter']
                        t = text[:80].encode('ascii','replace').decode()
                        missed[key]['example'] = f'ch{ch} d{depth}: {repr(t)}'

print(f'Top missed speakers (by count):')
for key, info in sorted(missed.items(), key=lambda x: -x[1]['count'])[:30]:
    ds = ','.join(str(d) for d in sorted(info['depths']))
    print(f'  {info["name"]:35s} count={info["count"]:4d}  depths=[{ds}]')
    print(f'    {info["example"]}')
