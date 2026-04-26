import json
with open('output/dialogs/volume_1/chapter_0003.json','r',encoding='utf-8') as f:
    data = json.load(f)
p1 = data['paragraphs'][0]
segs = p1['segments']
print(f'Segments: {len(segs)}')
for s in segs:
    print(f'  {s["type"]:10} d{s["depth"]}  {s["text"][:80]}')
