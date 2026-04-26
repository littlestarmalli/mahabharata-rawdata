import json, os

# Volume chapter ranges
for v in range(1, 11):
    d = f'output/dialogs/volume_{v}'
    files = [f for f in os.listdir(d) if f.endswith('.json')]
    nums = sorted([int(f.replace('chapter_','').replace('.json','')) for f in files])
    print(f'Volume {v}: chapters {nums[0]}-{nums[-1]} ({len(nums)} chapters)')

print()

# Parva chapter ranges
idx = json.load(open('output/json/index.json', encoding='utf-8'))
ch = 1
for p in idx['parvas']:
    n = p['details']['num_chapters']
    name = p['name']
    pnum = p['parva_number']
    print(f'Parva {pnum:2d} {name:25s}: chapters {ch}-{ch+n-1} ({n})')
    ch += n
