import json

data = json.load(open('output/dialogs/volume_10/chapter_1865.json', encoding='utf-8'))
ch = data['chapter']
depths = [seg.get('depth', 0) for p in data['paragraphs'] for seg in p['segments']]
print(f"Chapter {ch}: max_depth={max(depths)}, paragraphs={len(data['paragraphs'])}, segments={len(depths)}")
print()
for p in data['paragraphs']:
    print(f"--- Para {p['p']} (depth={p['depth']}, stack_len={len(p['stack'])}) ---")
    for i, seg in enumerate(p['segments']):
        d = seg.get('depth', 0)
        t = seg['text'][:70].encode('ascii', 'replace').decode()
        print(f"  [{i}] d={d} {seg['type']:10s} {t}")
