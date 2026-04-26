"""Count unresolved attributions - segments with 'said/replied/etc' but no 'introduces'."""
import json, os, re

ATTR_LOOSE = re.compile(
    r'^\s*[^\w]*(\w[\w\s\'-]*?)\s+'
    r'(said|continued|asked|replied|spoke|resumed|answered|exclaimed),',
    re.IGNORECASE
)

missed = {}
total_intros = 0
for v in range(1, 11):
    d = os.path.join('output', 'dialogs', f'volume_{v}')
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.json'): continue
        data = json.load(open(os.path.join(d, fname), encoding='utf-8'))
        for para in data['paragraphs']:
            for seg in para['segments']:
                if seg.get('introduces'):
                    total_intros += 1
                    continue
                text = seg['text']
                m = ATTR_LOOSE.match(text)
                if m:
                    speaker = m.group(1).strip()
                    verb = m.group(2)
                    depth = seg.get('depth', 0)
                    key = (speaker, verb, depth)
                    if key not in missed:
                        missed[key] = {'count': 0, 'example': ''}
                    missed[key]['count'] += 1
                    if not missed[key]['example']:
                        missed[key]['example'] = repr(text[:60].encode('ascii','replace').decode())

print(f'Total segments with introduces: {total_intros}')
print(f'Missed attributions (loose regex finds, current regex misses): {sum(v["count"] for v in missed.values())}')
print()
for key, info in sorted(missed.items(), key=lambda x: -x[1]['count']):
    speaker, verb, depth = key
    print(f'  d={depth} {speaker:30s} {verb:12s} count={info["count"]:4d}')
    print(f'    example: {info["example"]}')
