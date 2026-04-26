"""
Compare parvasamgraha counts:
  1. Sanskrit ITRANS (shloka-by-shloka number words decoded)
  2. English translation (volume_1_chapters.txt - what Souti says)
  3. BORI CE actual (bori_official.json)
  4. ITRANS actual parsed (bori_text JSONs)
"""
import json, re, os

# ── Sanskrit ITRANS stated counts (decoded from shlokas 95-232) ─────────────
itrans_stated = {
    1:  ("Adi Parva",              218,  7984),
    2:  ("Sabha Parva",             72,  2511),
    3:  ("Aranyaka Parva",         269, 11664),
    4:  ("Virata Parva",            67,  2050),
    5:  ("Udyoga Parva",           186,  6698),
    6:  ("Bhishma Parva",          117,  5884),
    7:  ("Drona Parva",            170,  8909),
    8:  ("Karna Parva",             69,  4900),
    9:  ("Shalya Parva",            59,  3220),
    10: ("Souptika Parva",          18,   870),
    11: ("Stri Parva",              27,   775),
    12: ("Shanti Parva",           339, 14525),
    13: ("Anushasana Parva",       146,  6700),
    14: ("Ashvamedhika Parva",     133,  3320),
    15: ("Ashramavasika Parva",     42,  1506),
    16: ("Mausala Parva",            8,   300),
    17: ("Mahaprasthanika Parva",    3,   120),
    18: ("Svargarohana Parva",       5,   200),
}

# ── English translation stated counts (from volume_1 Parvasamgraha text) ────
eng_stated = {
    1:  ("Adi Parva",              218,  7984),
    2:  ("Sabha Parva",             72,  2511),
    3:  ("Aranyaka Parva",         269, 11664),
    4:  ("Virata Parva",            67,  2050),
    5:  ("Udyoga Parva",           186,  6696),  # English says 6696
    6:  ("Bhishma Parva",          117,  5884),
    7:  ("Drona Parva",            170,  8909),
    8:  ("Karna Parva",             69,  4900),
    9:  ("Shalya Parva",            59,  3220),
    10: ("Souptika Parva",          18,   870),
    11: ("Stri Parva",              27,    75),  # English says 75 (should be 775)
    12: ("Shanti Parva",           339, 14525),
    13: ("Anushasana Parva",       146,  6700),
    14: ("Ashvamedhika Parva",     133,  3320),
    15: ("Ashramavasika Parva",     42,  1506),
    16: ("Mausala Parva",            8,   300),
    17: ("Mahaprasthanika Parva",    3,   120),
    18: ("Svargarohana Parva",       5,   200),
}

# ── BORI CE official ─────────────────────────────────────────────────────────
bori = json.load(open("output/json/bori_official.json", encoding="utf-8"))
bori_actual = {}
for p in bori["parvas"]:
    pn = p["number"]
    bori_actual[pn] = (p["name"], p["bori_adhyayas"], p["bori_shlokas"])

# ── ITRANS actual parsed ──────────────────────────────────────────────────────
fnames = [
    "parva_01_adi","parva_02_sabha","parva_03_vana","parva_04_virata",
    "parva_05_udyoga","parva_06_bhishma","parva_07_drona","parva_08_karna",
    "parva_09_shalya","parva_10_sauptika","parva_11_stri","parva_12_shanti",
    "parva_13_anushasana","parva_14_ashvamedhika","parva_15_ashramavasika",
    "parva_16_mausala","parva_17_mahaprasthanika","parva_18_svargarohana",
]
itrans_actual = {}
for i, fn in enumerate(fnames, 1):
    d = json.load(open(f"output/json/bori_text/{fn}_bori_text.json", encoding="utf-8"))
    itrans_actual[i] = (d["name"], d["details"]["num_chapters"], d["details"]["num_shlokas"])

# ── Print comparison ──────────────────────────────────────────────────────────
H1 = "─" * 130
print(f"\n{'#':>2}  {'Parva':<25}  {'SANSKRIT stated':>18}  {'ENGLISH stated':>18}  {'BORI CE official':>18}  {'ITRANS parsed':>18}  Notes")
print(f"{'':>2}  {'':25}  {'Ch':>6} {'Sh':>10}  {'Ch':>6} {'Sh':>10}  {'Ch':>6} {'Sh':>10}  {'Ch':>6} {'Sh':>10}")
print(H1)

for pn in range(1, 19):
    name = itrans_stated[pn][0]
    s_ch, s_sh = itrans_stated[pn][1], itrans_stated[pn][2]
    e_ch, e_sh = eng_stated[pn][1], eng_stated[pn][2]
    b_ch, b_sh = bori_actual[pn][1], bori_actual[pn][2]
    i_ch, i_sh = itrans_actual[pn][1], itrans_actual[pn][2]

    notes = []
    if s_sh != e_sh:
        notes.append(f"Eng sh={e_sh}≠Skt {s_sh}")
    if s_ch != e_ch:
        notes.append(f"Eng ch={e_ch}≠Skt {s_ch}")

    print(f"{pn:2d}  {name:<25}  {s_ch:6d} {s_sh:10d}  {e_ch:6d} {e_sh:10d}  {b_ch:6d} {b_sh:10d}  {i_ch:6d} {i_sh:10d}  {'  '.join(notes)}")

print(H1)
tot = lambda d, idx: sum(d[p][idx] for p in d)
print(f"{'TOT':<29}  {tot(itrans_stated,1):6d} {tot(itrans_stated,2):10d}  {tot(eng_stated,1):6d} {tot(eng_stated,2):10d}  {tot(bori_actual,1):6d} {tot(bori_actual,2):10d}  {tot(itrans_actual,1):6d} {tot(itrans_actual,2):10d}")

print()
print("Legend:")
print("  SANSKRIT stated  = numbers Souti recites in Sanskrit ITRANS (decoded from shlokas 95-232)")
print("  ENGLISH stated   = numbers in the English translation text (Bibek Debroy)")
print("  BORI CE official = counts in BORI introduction table (bori_official.json)")
print("  ITRANS parsed    = actual chapters/shlokas parsed from mbh01..mbh18.itx files")
