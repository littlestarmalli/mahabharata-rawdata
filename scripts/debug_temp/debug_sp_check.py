import json, os

# Check Shanti Parva sp84/85 boundary
fname = [x for x in os.listdir('output/json/story') if 'parva_12' in x and not x.endswith('_fn.json')][0]
d = json.load(open('output/json/story/' + fname, encoding='utf-8'))
print('Parva:', d['name'])
for spk in sorted(d['subparvas'], key=int):
    sp = d['subparvas'][spk]
    chs = sorted(sp['chapters'].keys(), key=int)
    print(f"  sp{spk}: {sp['name']} -- chapters: {len(chs)}, range: {chs[0]}-{chs[-1]}")

print()
# Check sp74 Shalya-vadha in Shalya parva
fname9 = [x for x in os.listdir('output/json/story') if 'parva_09' in x and not x.endswith('_fn.json')][0]
d9 = json.load(open('output/json/story/' + fname9, encoding='utf-8'))
print('Parva:', d9['name'])
for spk in sorted(d9['subparvas'], key=int):
    sp = d9['subparvas'][spk]
    chs = sorted(sp['chapters'].keys(), key=int)
    total_sh = sum(sp['chapters'][c].get('num_shlokas') or 0 for c in chs)
    print(f"  sp{spk}: {sp['name']} -- chapters: {len(chs)}, range: {chs[0]}-{chs[-1]}, shlokas: {total_sh}")

print()
# Check sp91 Putra-darshana in Ashramavasika parva
fname15 = [x for x in os.listdir('output/json/story') if 'parva_15' in x and not x.endswith('_fn.json')][0]
d15 = json.load(open('output/json/story/' + fname15, encoding='utf-8'))
print('Parva:', d15['name'])
for spk in sorted(d15['subparvas'], key=int):
    sp = d15['subparvas'][spk]
    chs = sorted(sp['chapters'].keys(), key=int)
    total_sh = sum(sp['chapters'][c].get('num_shlokas') or 0 for c in chs)
    print(f"  sp{spk}: {sp['name']} -- chapters: {len(chs)}, range: {chs[0]}-{chs[-1]}, shlokas: {total_sh}")
    # Print each chapter shloka for sp91
    if int(spk) == 91:
        for c in chs:
            print(f"      ch{c}: {sp['chapters'][c].get('num_shlokas')}")
