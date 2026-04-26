"""Find examples of false-positive speaker IDs."""
import json, os

bad_ids = {'been_thus', 'and', 'i', 'janamejaya_then'}
bad = {k: [] for k in bad_ids}

for v in range(1, 11):
    d = f'output/dialogs/volume_{v}'
    if not os.path.isdir(d): continue
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.json'): continue
        data = json.load(open(os.path.join(d, fn), encoding='utf-8'))
        ch = data['chapter']
        for para in data['paragraphs']:
            for seg in para['segments']:
                sp = seg.get('introduces', '')
                if sp in bad and len(bad[sp]) < 5:
                    txt = seg['text'][:100]
                    bad[sp].append(f"Ch{ch} p{para['p']}: {txt}")

for sp, exs in bad.items():
    print(f"--- {sp} ({len(exs)} examples) ---")
    for ex in exs:
        print(f"  {ex}")
    print()
