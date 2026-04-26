import json, os

files = [
    ('parva_01_adi', 'Adi Parva', 1),
    ('parva_02_sabha', 'Sabha Parva', 2),
    ('parva_03_vana', 'Vana Parva', 3),
    ('parva_04_virata', 'Virata Parva', 4),
    ('parva_05_udyoga', 'Udyoga Parva', 5),
    ('parva_06_bhishma', 'Bhishma Parva', 6),
    ('parva_07_drona', 'Drona Parva', 7),
    ('parva_08_karna', 'Karna Parva', 8),
    ('parva_09_shalya', 'Shalya Parva', 9),
    ('parva_10_sauptika', 'Sauptika Parva', 10),
    ('parva_11_stri', 'Stri Parva', 11),
    ('parva_12_shanti', 'Shanti Parva', 12),
    ('parva_13_anushasana', 'Anushasana Parva', 13),
    ('parva_14_ashvamedhika', 'Ashvamedhika Parva', 14),
    ('parva_15_ashramavasika', 'Ashramavasika Parva', 15),
    ('parva_16_mausala', 'Mausala Parva', 16),
    ('parva_17_mahaprasthanika', 'Mahaprasthanika Parva', 17),
    ('parva_18_svargarohana', 'Svargarohana Parva', 18),
]

header = f"{'#':>2}  {'Parva':<25} {'SP#':>4}  {'Sub-Parva Name':<40} {'Ch':>4}  {'Shlokas':>7}"
sep    = "-" * len(header)

print(header)
print(sep)

total_sp = total_ch = total_sh = 0
prev_pnum = None

for fname, pname, pnum in files:
    path = os.path.join('output', 'json', 'bori_text', fname + '_bori_text.json')
    d = json.load(open(path, encoding='utf-8'))

    if prev_pnum is not None:
        print(sep)

    p_sp = p_ch = p_sh = 0
    for sp_k, sp in d['subparvas'].items():
        sp_num  = sp['number']
        sp_name = sp['name']
        ch      = sp['details']['num_chapters']
        sh      = sp['details']['num_shlokas']
        # only print parva name on first sub-parva row
        disp_pname = pname if sp_num == 1 else ''
        print(f"{pnum:2d}  {disp_pname:<25} {sp_num:4d}  {sp_name:<40} {ch:4d}  {sh:7d}")
        p_sp += 1; p_ch += ch; p_sh += sh

    print(f"{'':2}  {'PARVA TOTAL':<25} {p_sp:4d}  {'':40} {p_ch:4d}  {p_sh:7d}")
    total_sp += p_sp; total_ch += p_ch; total_sh += p_sh
    prev_pnum = pnum

print(sep)
print(f"{'':2}  {'GRAND TOTAL':<25} {total_sp:4d}  {'':40} {total_ch:4d}  {total_sh:7d}")
print()
print(f"BORI official: 1995 chapters, 73784 shlokas")
print(f"ITRANS parsed: {total_ch} chapters, {total_sh} shlokas")
