import json
data = json.load(open('output/dialogs/volume_1/chapter_0059.json', encoding='utf-8'))
for para in data['paragraphs']:
    for seg in para['segments']:
        if 'Vaishampayana' in seg.get('text', '')[:30] and seg.get('depth') == 0:
            t = seg['text'][:80].encode('ascii','replace').decode()
            print(repr(t))
            sp = seg.get('speaker', 'NONE')
            intro = seg.get('introduces', 'NONE')
            print(f'  speaker={sp} introduces={intro}')
