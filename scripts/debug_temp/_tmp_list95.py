import json

bori = json.load(open('output/json/bori_official.json', encoding='utf-8'))
sects = json.load(open('output/json/mahabharata_sections.json', encoding='utf-8'))

sp_num = 0
for p in bori['parvas']:
    pn = p['number']
    pname = p['name']
    for sp in p['sub_parvas']:
        sp_num += 1
        print(f"{sp_num:3d}  P{pn:02d}  {pname:<25}  {sp['name']:<40}  ch={sp['adhyayas']:4d}  sh={sp['shlokas']:5d}")

print()
print(f"Total: {sp_num} sub-parvas")
