import json

def show(file, para_idx=0):
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    p = data['paragraphs'][para_idx]
    ch = data['chapter']
    print(f'=== Chapter {ch}, Para {p["p"]} ({len(p["segments"])} segments) ===')
    for s in p['segments']:
        indent = '  ' * s['depth']
        print(f'{indent}{s["type"]:10} d{s["depth"]}  {s["text"][:80]}')
    print()

# Chapter 44 - the one with nested Jaratkaru speech
show('output/dialogs/volume_1/chapter_0044.json', 0)

# Chapter 3 - verify basic case still works
show('output/dialogs/volume_1/chapter_0003.json', 0)

# Chapter 3 para 3 - Janamejaya/sage dialog
show('output/dialogs/volume_1/chapter_0003.json', 2)
