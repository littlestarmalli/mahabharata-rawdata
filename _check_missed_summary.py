"""Count missed attributions by depth."""
import json, os, re

ATTR_LOOSE = re.compile(
    r'^\s*[\u2018\u201c]*\s*(\w[\w\s\'-]*?)\s+'
    r'(said|continued|asked|replied|spoke|resumed|answered|exclaimed),',
    re.IGNORECASE
)

total_intros = 0
missed_count = 0
missed_by_depth = {}
# Count "Vaishampayana said" specifically
vaish_at_d0_missed = 0

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
                    depth = seg.get('depth', 0)
                    speaker = m.group(1).strip()
                    missed_count += 1
                    missed_by_depth[depth] = missed_by_depth.get(depth, 0) + 1
                    if 'vaishampayana' in speaker.lower() and depth == 0:
                        vaish_at_d0_missed += 1

print(f'Segments WITH introduces: {total_intros}')
print(f'Segments MISSED (loose regex finds): {missed_count}')
print(f'  Vaishampayana at d0 missed: {vaish_at_d0_missed}')
print()
print('Missed by depth:')
for d in sorted(missed_by_depth):
    print(f'  depth {d}: {missed_by_depth[d]}')
