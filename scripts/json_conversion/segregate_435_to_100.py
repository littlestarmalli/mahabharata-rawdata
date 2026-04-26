"""
Segregate the 435 ITRANS section headers into:
  - The 100 canonical sub-parvas (Souti's list, shlokas 34-69)
  - upAkhyAnas (named sub-stories)
  - Battle-day markers
  - Other internal sections
Output: output/json/mahabharata_sections.json
"""
import json

# ─────────────────────────────────────────────────────────────────────────────
# EXACT LOOKUP: (parva_number, itrans_name) → souti_number
# Built from actual ITRANS section names verified from the JSON files
# ─────────────────────────────────────────────────────────────────────────────
EXACT_MAP = {
    # ── ADI PARVA (1) ──
    (1, 'anukramaNIparva'):           1,
    (1, 'parvasa.ngrahaparva'):       2,
    (1, 'pauShyaparva'):              3,
    (1, 'paulomaparva'):              4,
    (1, 'AstIkaparva'):               5,
    (1, 'Adiva.nshAvataraNaparva'):   6,
    (1, 'sa.nbhavaparva'):            7,
    (1, 'jatugRRihadAhaparva'):       8,
    (1, 'hiDimbavadhaparva'):         9,
    (1, 'bakavadhaparva'):           10,
    (1, 'chaitrarathaparva'):        11,
    (1, 'draupadIsvaya.nvaraparva'): 12,
    (1, 'vaivAhikaparva'):           13,
    (1, 'vidurAgamanaparva'):        14,
    (1, 'rAjyAlambhaparva'):         15,
    (1, 'arjunavanavAsaparva'):      16,
    (1, 'subhadrAharaNaparva'):      17,
    (1, 'haraNahArikaparva'):        18,
    (1, 'khANDavadAhaparva'):        19,
    # SP 20 mayadarshanam – merged with khANDavadAha, no separate BORI header
    # ── SABHA PARVA (2) ──
    (2, 'sabhAparva'):               21,
    (2, 'mantraparva'):              22,
    (2, 'jarAsa.ndhaparva'):         23,
    (2, 'digvijayaparva'):           24,
    (2, 'rAjasUyaparva'):            25,
    (2, 'arghAbhiharaNaparva'):      26,
    (2, 'shishupAlavadhaparva'):     27,
    (2, 'dyUtaparva'):               28,
    (2, 'anudyUtaparva'):            29,
    # ── ARANYAKA / VANA PARVA (3) ──
    (3, 'AraNyakaparva'):            30,
    (3, 'kirmIravadhaparva'):        31,
    (3, 'kairAtaparva'):             32,
    (3, 'indralokAbhigamanaparva'):  33,
    (3, 'tIrthayAtrAparva'):         34,
    (3, 'jaTAsurabadhaparva'):       35,
    (3, 'yakShayuddhaparva'):        36,
    (3, 'Ajagaraparva'):             37,
    (3, 'mArkaNDeyasamAsyAparva'):   38,
    (3, 'draupadisatyabhAmAsa.nvAdaparva'): 39,
    (3, 'ghoShayAtrAparva'):         40,
    (3, 'mRRigasvapnabhayaparva'):   41,
    (3, 'vrIhidrauNikaparva'):       42,
    (3, 'draupadIharaNaparva'):      43,
    (3, 'kuNDalAharaNaparva'):       44,
    (3, 'AraNeyaparva'):             45,
    # ── VIRATA PARVA (4) ──
    (4, 'vairATaparva'):             46,
    (4, 'kIchakavadhaparva'):        47,
    (4, 'gograhaNaparva'):           48,
    (4, 'vaivAhikaparva'):           49,
    # ── UDYOGA PARVA (5) ──
    (5, 'udyogaparva'):              50,
    (5, 'sa.njayayAnaparva'):        51,
    (5, 'prajAgaraparva'):           52,
    (5, 'sanatsujAtaparva'):         53,
    (5, 'yAnasa.ndhiparva'):         54,
    (5, 'bhagavadyAnaparva'):        54,   # subsection of yAnasandhi
    (5, 'karNopanivAdaparva'):       55,
    (5, 'abhiniryANaparva'):         56,
    (5, 'rathAtirathasa.nkhyAnaparva'): 57,
    (5, 'ulUkayAnaparva'):           58,
    (5, 'ambopAkhyAnaparva'):        59,
    (5, 'bhIShmAbhiShechanaparva'):  60,   # boundary Udyoga/Bhishma
    # ── BHISHMA PARVA (6) ──
    (6, 'jambUkhaNDavinirmANaparva'): 61,
    (6, 'bhUmiparva'):               62,
    (6, 'bhagavadgItAparva'):        63,
    # SP 64 bhIShmavadha – covered by the 10 battle-day sections (no single header)
    # ── DRONA PARVA (7) ──
    (7, 'droNAbhiShekaparva'):       65,
    (7, 'sa.nshaptakavadhaparva'):   66,
    (7, 'abhimanyuvadhaparva'):      67,
    (7, 'pratij~nAparva'):           68,
    (7, 'jayadrathavadhaparva'):     69,
    (7, 'ghaTotkachavadhaparva'):    70,
    (7, 'droNavadhaparva'):          71,
    (7, 'nArAyaNAstramokShaparva'):  72,
    # SP 73 karNam – entire P08, no explicit section header
    # ── SHALYA PARVA (9) ──
    (9, 'shalyavadhaparva'):         74,
    (9, 'hradapraveshaparva'):       75,
    (9, 'gadAyuddhaparva'):          76,
    (9, 'tIrthayAtrAparva'):         77,   # sArasvatam tIrtha-yAtrA section
    # SP 78 sauptikam – opening of P10 without explicit header
    # ── SAUPTIKA PARVA (10) ──
    (10, 'aiShIkaparva'):            79,
    # ── STRI PARVA (11) ──
    (11, 'jalapradAnikaparva'):      80,
    (11, 'strIparva'):               81,
    (11, 'shrAddhaparva'):           82,
    # SP 83-85 AbhiShechanika/chArvAka/pravibhAga – opening of P12, no headers
    # ── SHANTI PARVA (12) ──
    (12, 'rAjadharmaparva'):         86,   # shAnti / rAjadharmAnukIrtana
    (12, 'Apaddharmaparva'):         87,
    # SP 88 mokShaDharma – large middle section of P12, no single header
    # SP 89-90 AnushAsana / svargArohaNika-bhIShma – entire P13, no headers
    # ── ASHVAMEDHIKA PARVA (14) ──
    (14, 'anugItA'):                 92,
    # SP 91 ashvamedhika – most of P14, no "ashvamedhikaparva" header
    # ── ASHRAMAVASIKA PARVA (15) ──
    (15, 'putradarshanaparva'):      94,
    # SP 93 AshramavAsa, 95 nAradAgamana – no separate headers in P15
    # ── MAUSALA PARVA (16) ──
    (16, 'mausalaparva'):            96,
    # SP 97 mahAprasthAnika – entire P17, no header
    # SP 98 svargArohaNa – entire P18, no header
    # SP 99-100 hariva.nsha / bhaviShyat – not in the 18 ITRANS files
}

# ─────────────────────────────────────────────────────────────────────────────
# 100 canonical sub-parvas from Souti's parvasa.ngrahaparva (shlokas 34-69)
# (number, souti_name, main_parva, note)
# ─────────────────────────────────────────────────────────────────────────────
CANONICAL_100 = [
    # ── ADI PARVA (1) ──
    (1,  "parvAnukramaNI",              1,  "anukramaNIparva"),
    (2,  "parvasa~NgrahaH",             1,  "parvasa.ngrahaparva"),
    (3,  "pauShyam",                    1,  "pauShyaparva"),
    (4,  "paulomam",                    1,  "paulomaparva"),
    (5,  "AstIkam",                     1,  "AstIkaparva"),
    (6,  "AdIva.nshAvatAraNam",         1,  "Adiva.nshAvataraNaparva"),
    (7,  "sambhavam",                   1,  "sa.nbhavaparva"),
    (8,  "jatugRRihadAham",             1,  "jatugRRihadAhaparva"),
    (9,  "haiDimbam",                   1,  "hiDimbavadhaparva"),
    (10, "bakavadham",                  1,  "bakavadhaparva"),
    (11, "chaitraratham",               1,  "chaitrarathaparva"),
    (12, "svaya.nvaram",                1,  "draupadIsvaya.nvaraparva"),
    (13, "vaivAhikam (pANDava)",        1,  "vaivAhikaparva"),
    (14, "vidurAgamanam",               1,  "vidurAgamanaparva"),
    (15, "rAjyalambham",                1,  "rAjyAlambhaparva"),
    (16, "arjunavanavAsam",             1,  "arjunavanavAsaparva"),
    (17, "subhadrAharaNam",             1,  "subhadrAharaNaparva"),
    (18, "haraNahArikam",               1,  "haraNahArikaparva"),
    (19, "khANDavadAham",               1,  "khANDavadAhaparva"),
    (20, "mayadarshanam",               1,  None),  # merged with khANDavadAha in BORI CE
    # ── SABHA PARVA (2) ──
    (21, "sabhAH",                      2,  "sabhAparva"),
    (22, "mantraH",                     2,  "mantraparva"),
    (23, "jarAsandhavadham",            2,  "jarAsa.ndhaparva"),
    (24, "digvijayam",                  2,  "digvijayaparva"),
    (25, "rAjasUyikam",                 2,  "rAjasUyaparva"),
    (26, "arghAbhiharaNam",             2,  "arghAbhiharaNaparva"),
    (27, "shishupAlavadham",            2,  "shishupAlavadhaparva"),
    (28, "dyUtam",                      2,  "dyUtaparva"),
    (29, "anudyUtam",                   2,  "anudyUtaparva"),
    # ── ARANYAKA / VANA PARVA (3) ──
    (30, "AraNyakam",                   3,  "AraNyakaparva"),
    (31, "kirmIravadham",               3,  "kirmIravadhaparva"),
    (32, "kairAtam",                    3,  "kairAtaparva"),
    (33, "indralokAbhigamanam",         3,  "indralokAbhigamanaparva"),
    (34, "tIrthayAtrA",                 3,  "tIrthayAtrAparva"),
    (35, "jaTAsuravadham",              3,  "jaTAsurabadhaparva"),
    (36, "yakShayuddham",               3,  "yakShayuddhaparva"),
    (37, "Ajagaram",                    3,  "Ajagaraparva"),
    (38, "mArkaNDeyasamasyA",           3,  "mArkaNDeyasamAsyAparva"),
    (39, "draupadI-satyabhAmA-sa.nvAdaH",3,"draupadisatyabhAmAsa.nvAdaparva"),
    (40, "ghoShayAtrA",                 3,  "ghoShayAtrAparva"),
    (41, "mRRigasvapnam",               3,  "mRRigasvapnabhayaparva"),
    (42, "vrIhidrauNikam",              3,  "vrIhidrauNikaparva"),
    (43, "draupadIharaNam",             3,  "draupadIharaNaparva"),
    (44, "kuNDalAharaNam",              3,  "kuNDalAharaNaparva"),
    (45, "AraNeyam",                    3,  "AraNeyaparva"),
    # ── VIRATA PARVA (4) ──
    (46, "vairATam",                    4,  "vairATaparva"),
    (47, "kIchakavadham",               4,  "kIchakavadhaparva"),
    (48, "gograhaNam",                  4,  "gograhaNaparva"),
    (49, "vaivAhikam (abhimanyu)",      4,  "vaivAhikaparva"),
    # ── UDYOGA PARVA (5) ──
    (50, "udyogam",                     5,  "udyogaparva"),
    (51, "sa~njayAnam",                 5,  "sa.njayayAnaparva"),
    (52, "prajAgaram",                  5,  "prajAgaraparva"),
    (53, "sAnatsujAtam",                5,  "sanatsujAtaparva"),
    (54, "yAnasandhiH + bhagavadyAnam", 5,  "yAnasa.ndhiparva"),
    (55, "vivAdaH (karNa)",             5,  "karNopanivAdaparva"),
    (56, "niryANam",                    5,  "abhiniryANaparva"),
    (57, "rathAtirathasa~NkhyA",        5,  "rathAtirathasa.nkhyAnaparva"),
    (58, "ulUkadUtAgamanam",            5,  "ulUkayAnaparva"),
    (59, "ambopAkhyAnam",               5,  "ambopAkhyAnaparva"),
    # ── BHISHMA PARVA (6) — note SP60 appears at end of P05 ITRANS ──
    (60, "bhIShmAbhiShecanam",          6,  "bhIShmAbhiShechanaparva"),
    (61, "jambUkhaNDavinirmANam",       6,  "jambUkhaNDavinirmANaparva"),
    (62, "bhUmiH",                      6,  "bhUmiparva"),
    (63, "bhagavadgItA",                6,  "bhagavadgItAparva"),
    (64, "bhIShmavadham",               6,  None),  # covered by 10 battle-day sections
    # ── DRONA PARVA (7) ──
    (65, "droNAbhiShekaH",              7,  "droNAbhiShekaparva"),
    (66, "sa.nshaptakavadham",          7,  "sa.nshaptakavadhaparva"),
    (67, "abhimanyuvadham",             7,  "abhimanyuvadhaparva"),
    (68, "pratij~nA",                   7,  "pratij~nAparva"),
    (69, "jayadrathavadham",            7,  "jayadrathavadhaparva"),
    (70, "ghaTotkachavadham",           7,  "ghaTotkachavadhaparva"),
    (71, "droNavadham",                 7,  "droNavadhaparva"),
    (72, "nArAyaNAstramokShaH",         7,  "nArAyaNAstramokShaparva"),
    # ── KARNA PARVA (8) — entire P08 is this sub-parva, no section header ──
    (73, "karNam",                      8,  None),
    # ── SHALYA PARVA (9) ──
    (74, "shalyam",                     9,  "shalyavadhaparva"),
    (75, "hradapraveshanam",            9,  "hradapraveshaparva"),
    (76, "gadAyuddham",                 9,  "gadAyuddhaparva"),
    (77, "sArasvatam",                  9,  "tIrthayAtrAparva"),  # Sarasvata tIrtha section
    # ── SAUPTIKA PARVA (10) ──
    (78, "sauptikam",                  10,  None),    # opening of P10, no header
    (79, "aiShIkam",                   10,  "aiShIkaparva"),
    # ── STRI PARVA (11) ──
    (80, "jalapradAnikam",             11,  "jalapradAnikaparva"),
    (81, "strIH",                      11,  "strIparva"),
    (82, "shrAddham",                  11,  "shrAddhaparva"),
    # ── SHANTI PARVA (12) ──
    (83, "AbhiShecanikam",             12,  None),    # opening of P12, no header
    (84, "chArvAkanigrahaH",           12,  None),    # opening of P12, no header
    (85, "pravibhAgaH",                12,  None),    # opening of P12, no header
    (86, "shAntiH (rAjadharmAH)",      12,  "rAjadharmaparva"),
    (87, "ApadDharmaH",                12,  "Apaddharmaparva"),
    (88, "mokShaDharmaH",              12,  None),    # large middle section, no single header
    # ── ANUSHASANA PARVA (13) — entire P13, no section headers ──
    (89, "AnushAsanam",                13,  None),
    (90, "svargArohaNikam (bhIShmA)",  13,  None),
    # ── ASHVAMEDHIKA PARVA (14) ──
    (91, "ashvamedhikam",              14,  None),    # main content of P14, no header
    (92, "anugItA",                    14,  "anugItA"),
    # ── ASHRAMAVASIKA PARVA (15) ──
    (93, "AshramavAsam",               15,  None),    # main content, no header
    (94, "putradarshanam",             15,  "putradarshanaparva"),
    (95, "nAradAgamanam",              15,  None),    # no explicit header in P15
    # ── MAUSALA PARVA (16) ──
    (96, "mausalam",                   16,  "mausalaparva"),
    # ── MAHAPRASTHANIKA PARVA (17) — entire P17, no header ──
    (97, "mahAprasthAnikam",           17,  None),
    # ── SVARGAROHANA PARVA (18) — entire P18, no header ──
    (98, "svargArohaNam",              18,  None),
    # ── KHILA (appendix) — not in the 18 ITRANS files ──
    (99,  "hariva.nshaH",              None, None),
    (100, "bhaviShyat",                None, None),
]

PARVA_NAMES = {
    1:"Adi Parva", 2:"Sabha Parva", 3:"Aranyaka (Vana) Parva",
    4:"Virata Parva", 5:"Udyoga Parva", 6:"Bhishma Parva",
    7:"Drona Parva", 8:"Karna Parva", 9:"Shalya Parva",
    10:"Sauptika Parva", 11:"Stri Parva", 12:"Shanti Parva",
    13:"Anushasana Parva", 14:"Ashvamedhika Parva",
    15:"Ashramavasika Parva", 16:"Mausala Parva",
    17:"Mahaprasthanika Parva", 18:"Svargarohana Parva",
}

FNAMES = [
    "parva_01_adi","parva_02_sabha","parva_03_vana","parva_04_virata",
    "parva_05_udyoga","parva_06_bhishma","parva_07_drona","parva_08_karna",
    "parva_09_shalya","parva_10_sauptika","parva_11_stri","parva_12_shanti",
    "parva_13_anushasana","parva_14_ashvamedhika","parva_15_ashramavasika",
    "parva_16_mausala","parva_17_mahaprasthanika","parva_18_svargarohana",
]

# ─────────────────────────────────────────────────────────────────────────────
# Load all 435 ITRANS sections
# ─────────────────────────────────────────────────────────────────────────────
all_sections = []  # (parva_num, itrans_name, start_ch, end_ch, num_ch, num_sh)
for i, fn in enumerate(FNAMES, 1):
    d = json.load(open(f"output/json/bori_text/{fn}_bori_text.json", encoding="utf-8"))
    for sp in d["subparvas"].values():
        name = sp.get("name", "")
        if name:
            all_sections.append({
                "parva_number": i,
                "itrans_name": name,
                "start_chapter": sp.get("start_chapter"),
                "end_chapter":   sp.get("end_chapter"),
                "num_chapters":  sp["details"]["num_chapters"],
                "num_shlokas":   sp["details"]["num_shlokas"],
            })

# Build reverse lookup: souti_number → (souti_name, main_parva)
SOUTI_NAMES = {num: (name, mp) for num, name, mp, _ in CANONICAL_100}

# ─────────────────────────────────────────────────────────────────────────────
# Match each ITRANS section → canonical 100 entry (exact lookup)
# ─────────────────────────────────────────────────────────────────────────────
def match_canonical(parva_num, itrans_name):
    """Return (souti_number, souti_name) using exact EXACT_MAP lookup."""
    sn = EXACT_MAP.get((parva_num, itrans_name))
    if sn is None:
        return (None, None)
    return (sn, SOUTI_NAMES[sn][0])


def classify(itrans_name, souti_number):
    """Return type string."""
    nl = itrans_name.lower()
    if souti_number is not None:
        return "official_subparva"
    if "upAkhyAnam" in itrans_name:
        return "upakhyana"
    if "yuddhadivasaH" in itrans_name:
        return "battle_day"
    return "internal_section"


# ─────────────────────────────────────────────────────────────────────────────
# Build enriched sections list
# ─────────────────────────────────────────────────────────────────────────────
enriched = []
seq = 0
for s in all_sections:
    seq += 1
    sn, sname = match_canonical(s["parva_number"], s["itrans_name"])
    t = classify(s["itrans_name"], sn)
    enriched.append({
        "seq":            seq,
        "parva_number":   s["parva_number"],
        "parva_name":     PARVA_NAMES.get(s["parva_number"], "Khila"),
        "itrans_name":    s["itrans_name"],
        "type":           t,
        "souti_number":   sn,
        "souti_name":     sname,
        "start_chapter":  s["start_chapter"],
        "end_chapter":    s["end_chapter"],
        "num_chapters":   s["num_chapters"],
        "num_shlokas":    s["num_shlokas"],
    })

# ─────────────────────────────────────────────────────────────────────────────
# Build by-parva grouping
# ─────────────────────────────────────────────────────────────────────────────
by_parva = {}
for pn in range(1, 19):
    by_parva[str(pn)] = {
        "parva_number": pn,
        "parva_name": PARVA_NAMES[pn],
        "official_subparvas": [],
        "upakhyanas": [],
        "battle_days": [],
        "internal_sections": [],
    }

for s in enriched:
    pn = str(s["parva_number"])
    entry = {
        "seq":          s["seq"],
        "itrans_name":  s["itrans_name"],
        "num_chapters": s["num_chapters"],
        "num_shlokas":  s["num_shlokas"],
        "start_chapter":s["start_chapter"],
        "end_chapter":  s["end_chapter"],
    }
    if s["souti_number"]:
        entry["souti_number"] = s["souti_number"]
        entry["souti_name"]   = s["souti_name"]

    t = s["type"]
    if t == "official_subparva":
        by_parva[pn]["official_subparvas"].append(entry)
    elif t == "upakhyana":
        by_parva[pn]["upakhyanas"].append(entry)
    elif t == "battle_day":
        by_parva[pn]["battle_days"].append(entry)
    else:
        by_parva[pn]["internal_sections"].append(entry)

# Add counts
for pn in range(1, 19):
    g = by_parva[str(pn)]
    g["_count_official_subparvas"] = len(g["official_subparvas"])
    g["_count_upakhyanas"]         = len(g["upakhyanas"])
    g["_count_battle_days"]        = len(g["battle_days"])
    g["_count_internal_sections"]  = len(g["internal_sections"])
    g["_count_total"]              = (g["_count_official_subparvas"] +
                                      g["_count_upakhyanas"] +
                                      g["_count_battle_days"] +
                                      g["_count_internal_sections"])

# ─────────────────────────────────────────────────────────────────────────────
# Build canonical_100 list
# ─────────────────────────────────────────────────────────────────────────────
canon_list = []
for num, souti_name, sp_parva, hint in CANONICAL_100:
    matched_itrans = [s["itrans_name"] for s in enriched if s["souti_number"] == num]
    canon_list.append({
        "souti_number":  num,
        "souti_name":    souti_name,
        "main_parva":    sp_parva,
        "parva_name":    PARVA_NAMES.get(sp_parva, "Khila (appendix)") if sp_parva else "Khila (appendix)",
        "matched_itrans_names": matched_itrans,
        "found_in_text": len(matched_itrans) > 0,
    })

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
type_counts = {}
for s in enriched:
    type_counts[s["type"]] = type_counts.get(s["type"], 0) + 1

matched_count   = sum(1 for s in enriched if s["souti_number"] is not None)
unmatched_count = sum(1 for s in enriched if s["souti_number"] is None)
canon_found     = sum(1 for c in canon_list if c["found_in_text"])
canon_missing   = [c for c in canon_list if not c["found_in_text"]]

out = {
    "_description": (
        "Segregation of 435 ITRANS section headers into: "
        "the 100 canonical sub-parvas (Souti's list), upAkhyAnas, battle-day markers, "
        "and other internal sections."
    ),
    "_summary": {
        "total_itrans_sections": len(enriched),
        "by_type": type_counts,
        "matched_to_souti_100": matched_count,
        "not_matched_to_souti_100": unmatched_count,
        "canonical_100_found_in_text": canon_found,
        "canonical_100_missing_from_text": len(canon_missing),
        "canonical_100_missing_names": [c["souti_name"] for c in canon_missing],
    },
    "canonical_100": canon_list,
    "by_parva": by_parva,
    "all_435_flat": enriched,
}

out_path = "output/json/mahabharata_sections.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"Written: {out_path}")
print(f"\nSummary:")
print(f"  Total ITRANS sections : {len(enriched)}")
print(f"  By type:")
for k, v in sorted(type_counts.items()):
    print(f"    {k:<25} : {v}")
print(f"  Matched to Souti 100  : {matched_count}")
print(f"  Not matched           : {unmatched_count}")
print(f"  Canonical found       : {canon_found}/100")
print(f"  Canonical MISSING     : {len(canon_missing)}")
for c in canon_missing:
    print(f"    [{c['souti_number']:3d}] {c['souti_name']}  (parva {c['main_parva']})")

print("\nPer-parva breakdown:")
print(f"  {'Parva':<30} {'Official':>8} {'Upakh':>6} {'Battle':>6} {'Other':>6} {'Total':>6}")
print("  " + "─"*70)
for pn in range(1, 19):
    g = by_parva[str(pn)]
    print(f"  {g['parva_name']:<30} {g['_count_official_subparvas']:8d} "
          f"{g['_count_upakhyanas']:6d} {g['_count_battle_days']:6d} "
          f"{g['_count_internal_sections']:6d} {g['_count_total']:6d}")
