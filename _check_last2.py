import json

for vol, ch in [(10, 1814), (10, 1863)]:
    data = json.load(open(f'output/dialogs/volume_{vol}/chapter_{ch:04d}.json', encoding='utf-8'))
    print(f"\nChapter {ch}:")
    for p in data['paragraphs']:
        for seg in p['segments']:
            d = seg.get('depth', 0)
            if d > 5:
                t = seg['text'][:80].encode('ascii', 'replace').decode()
                print(f"  p{p['p']} d={d} {seg['type']:10s} {t}")
