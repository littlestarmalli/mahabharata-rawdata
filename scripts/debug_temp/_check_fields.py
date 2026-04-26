"""Check alignment + confirmation for a specific chapter/paragraph."""
import json, sys

ch = int(sys.argv[1]) if len(sys.argv) > 1 else 593
pi = int(sys.argv[2]) if len(sys.argv) > 2 else 5
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

for para in data['paragraphs']:
    if pi and para['p'] != pi:
        continue
    print(f"--- Paragraph {para['p']} ---")
    for seg in para['segments']:
        d = seg['depth']
        t = seg['type']
        al = seg.get('alignment', '?')
        conf = seg.get('speaker_confirmed', '?')
        sp = seg.get('speaker', '?')
        intro = seg.get('introduces', '')
        text = seg['text'][:80]
        flag = ' ATTR' if intro else ('  OK ' if conf else ' ??? ')
        print(f"  d{d} [{t:9s}] align={al:6s} conf={str(conf):5s} {flag} sp={sp:22s} {text}")
