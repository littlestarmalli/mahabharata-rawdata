"""Quick inspect dialog JSON for a chapter."""
import json, sys

ch = int(sys.argv[1]) if len(sys.argv) > 1 else 59
vol = 1
if ch > 199: vol = 2
if ch > 376: vol = 3
if ch > 596: vol = 4
if ch > 832: vol = 5
if ch > 1008: vol = 6
if ch > 1150: vol = 7
if ch > 1283: vol = 8
if ch > 1527: vol = 9
if ch > 1737: vol = 10

path = f'output/dialogs/volume_{vol}/chapter_{ch:04d}.json'
data = json.load(open(path, encoding='utf-8'))

limit = int(sys.argv[2]) if len(sys.argv) > 2 else 15

for para in data['paragraphs'][:limit]:
    for seg in para['segments']:
        sp = seg.get('speaker', '?')
        intro = seg.get('introduces', '')
        d = seg['depth']
        prefix = seg['text'][:100].replace('\n', ' ')
        src = 'ATTR' if intro else 'inh.'
        print(f"  p{para['p']:2d} d{d} [{seg['type']:9s}] sp={sp:25s} [{src:5s}] {prefix}")
    print()
