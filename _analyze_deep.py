"""Analyze the exact quote pattern at paragraph boundaries for chapters with depth > 6."""
import json, os, re

# Unicode quote chars
OQ1, CQ1 = '\u2018', '\u2019'  # ' '
OQ2, CQ2 = '\u201c', '\u201d'  # " "

def analyze_chapter(vol, ch_num):
    fpath = f'output/dialogs/volume_{vol}/chapter_{ch_num:04d}.json'
    data = json.load(open(fpath, encoding='utf-8'))
    
    max_d = max(seg.get('depth', 0) for p in data['paragraphs'] for seg in p['segments'])
    print(f"\n{'='*80}")
    print(f"Chapter {data['chapter']} (Volume {vol}) — max_depth={max_d}")
    print(f"{'='*80}")
    
    for p in data['paragraphs']:
        text = p['text']
        # Show first 40 chars to see the opening quote pattern
        opening = text[:40].replace(OQ1, "['").replace(CQ1, "']").replace(OQ2, '["').replace(CQ2, '"]')
        # Show last 40 chars to see closing pattern
        closing = text[-40:].replace(OQ1, "['").replace(CQ1, "']").replace(OQ2, '["').replace(CQ2, '"]')
        
        # ASCII-safe
        opening = opening.encode('ascii', 'replace').decode()
        closing = closing.encode('ascii', 'replace').decode()
        
        print(f"\n  Para {p['p']} | stack={p['stack']} depth={p['depth']}")
        print(f"    START: {opening}")
        print(f"    END:   {closing}")
        
        # Count opens vs closes
        opens = sum(1 for c in text if c in (OQ1, OQ2))
        closes = sum(1 for c in text if c in (CQ1, CQ2))
        if opens != closes:
            print(f"    *** MISMATCH: {opens} opens vs {closes} closes ***")

# Check worst offenders
bad_chapters = [
    (10, 1865),  # max=81
    (3, 431),    # max=39
    (7, 1174),   # max=30
    (10, 1845),  # max=23
    (3, 487),    # max=12
]

for vol, ch in bad_chapters:
    analyze_chapter(vol, ch)
