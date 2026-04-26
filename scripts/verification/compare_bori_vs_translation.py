import json

bori = json.load(open('output/json/bori_official.json', encoding='utf-8'))
trans = json.load(open('output/json/translation_data.json', encoding='utf-8'))

# Build lookups
bori_sp = {}
bori_parva = {}
for p in bori['parvas']:
    bori_parva[p['number']] = {'adhyayas': p['bori_adhyayas'], 'shlokas': p['bori_shlokas'], 'name': p['name']}
    for sp in p['sub_parvas']:
        bori_sp[sp['number']] = {'adhyayas': sp['adhyayas'], 'shlokas': sp['shlokas'], 'name': sp['name'], 'parva': p['number']}

trans_sp = {}
trans_parva = {}
for p in trans['parvas']:
    trans_parva[p['number']] = {'chapters': p['chapters'], 'shlokas': p['shlokas_from_headers'], 'name': p['name']}
    for sp in p['sub_parvas']:
        trans_sp[sp['number']] = {
            'chapters': sp['chapters'],
            'shlokas': sp['shlokas_from_headers'],
            'name': sp['name'],
            'missing': sp['chapters_missing_shloka_count'],
        }

# Check for missing sub-parvas in translation
trans_sp_numbers = set(trans_sp.keys())
bori_sp_numbers = set(bori_sp.keys())
missing_in_trans = bori_sp_numbers - trans_sp_numbers
extra_in_trans = trans_sp_numbers - bori_sp_numbers

print("=== PARVA-LEVEL COMPARISON ===")
print(f"{'#':>3}  {'Parva':<25}  {'BORI Ch':>7}  {'Trans Ch':>8}  {'Ch Diff':>7}  | {'BORI Sh':>7}  {'Trans Sh':>8}  {'Sh Diff':>7}")
for pn in sorted(bori_parva):
    b = bori_parva[pn]
    t = trans_parva.get(pn, {})
    cdiff = t.get('chapters', 0) - b['adhyayas']
    sdiff = t.get('shlokas', 0) - b['shlokas']
    flag = "  <-- DIFF" if sdiff != 0 else ""
    print(f"  {pn:>2}  {b['name']:<25}  {b['adhyayas']:>7}  {t.get('chapters', '?'):>8}  {cdiff:>+7}  | {b['shlokas']:>7}  {t.get('shlokas', '?'):>8}  {sdiff:>+7}{flag}")

print()
if missing_in_trans:
    print(f"MISSING sub-parvas in translation_data: {sorted(missing_in_trans)}")
if extra_in_trans:
    print(f"EXTRA sub-parvas in translation_data (not in BORI): {sorted(extra_in_trans)}")
print()

print("=== SUB-PARVA DIFFERENCES (only rows with differences) ===")
print(f"{'SP':>4}  {'Name':<38}  {'BORI Ch':>7}  {'Trans Ch':>8}  {'Ch Diff':>7}  | {'BORI Sh':>7}  {'Trans Sh':>8}  {'Sh Diff':>7}  Notes")
any_diff = False
for spn in sorted(bori_sp):
    b = bori_sp[spn]
    t = trans_sp.get(spn)
    if t is None:
        print(f"  {spn:>3}  {b['name']:<38}  MISSING in translation_data!")
        any_diff = True
        continue
    cdiff = t['chapters'] - b['adhyayas']
    sdiff = t['shlokas'] - b['shlokas']
    missing = t['missing']
    if sdiff != 0 or cdiff != 0 or missing > 0:
        notes = "[?] chapter(s) in OCR" if missing > 0 else ""
        print(f"  {spn:>3}  {t['name']:<38}  {b['adhyayas']:>7}  {t['chapters']:>8}  {cdiff:>+7}  | {b['shlokas']:>7}  {t['shlokas']:>8}  {sdiff:>+7}  {notes}")
        any_diff = True

if not any_diff:
    print("  All sub-parvas match!")

print()
print("=== SUMMARY ===")
total_sdiff = sum(
    trans_parva.get(pn, {}).get('shlokas', 0) - bori_parva[pn]['shlokas']
    for pn in bori_parva
)
print(f"Total BORI shlokas:        73784")
print(f"Total translation shlokas: {trans['total_shlokas_from_headers']}")
print(f"Overall difference:        {trans['total_shlokas_from_headers'] - 73784:+d}")
