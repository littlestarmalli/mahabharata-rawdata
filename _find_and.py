"""Find 'and' false positive in chapter 3."""
import json
d = json.load(open('output/dialogs/volume_1/chapter_0003.json', encoding='utf-8'))
for p in d['paragraphs']:
    for seg in p['segments']:
        if seg.get('introduces') == 'and':
            print(f"p{p['p']}: text=...{repr(seg['text'][-80:])}")
