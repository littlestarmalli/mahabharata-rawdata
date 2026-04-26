import json
data = json.load(open('output/dialogs/volume_10/chapter_1865.json', encoding='utf-8'))
ch = data['chapter']
depths = [seg.get('depth',0) for p in data['paragraphs'] for seg in p['segments']]
print(f"Chapter {ch}, max_depth={max(depths)}, paragraphs={len(data['paragraphs'])}")
print()
for p in data['paragraphs']:
    print(f"--- Para {p['p']} (depth={p['depth']}) ---")
    for i, seg in enumerate(p['segments']):
        d = seg.get('depth', 0)
        t = seg['text'][:70].replace('\n', ' ')
        print(f"  [{i}] d={d:2d} {seg['type']:10s} {t}")
