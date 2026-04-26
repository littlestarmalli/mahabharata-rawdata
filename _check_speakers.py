"""Check speaker attribution for Vaishampayana said at depth 0."""
import json, os

found = 0
for v in range(1, 11):
    d = os.path.join('output', 'dialogs', f'volume_{v}')
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.json'): continue
        data = json.load(open(os.path.join(d, fname), encoding='utf-8'))
        for para in data['paragraphs']:
            for seg in para['segments']:
                if seg.get('depth') == 0 and 'Vaishampayana' in seg.get('text', '')[:30]:
                    sp = seg.get('speaker', '?')
                    intro = seg.get('introduces', '')
                    ch = data['chapter']
                    d1_speakers = set()
                    for s2 in para['segments']:
                        if s2.get('depth') == 1:
                            d1_speakers.add(s2.get('speaker', '?'))
                    txt = seg['text'][:60].encode('ascii', 'replace').decode()
                    print(f'ch {ch}: d0_speaker={sp}  introduces={intro}  d1={d1_speakers}')
                    print(f'  {txt}')
                    found += 1
                    if found >= 10:
                        raise SystemExit()
