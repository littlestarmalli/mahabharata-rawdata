"""
build_bori_and_translation.py
Generates two JSON files:
  1. output/json/bori_official.json  — BORI Critical Edition data from the book introductions
  2. output/json/translation_data.json — Actual extracted counts from Bibek Debroy translation
Also updates output/json/introduction.json to remove all null values.

Sources used:
  - BORI table: Introduction of Volume 1 (Complete_text_mahabharat.txt ~offset 17898)
  - Section headers in each volume text (e.g. "Section Eight Jatugriha-daha Parva\nThis parva has 373 shlokas")
  - Parva totals minus sum of known sub-parvas (for deterministic computation)
  - Story JSON files: output/json/story/parva_NN_*.json

Notes on resolved nulls:
  sp8  (Jatugriha-daha) shlokas=373  — from section header; 373+82=455=7202-6747(BORI sum of others) ✓
  sp15 (Rajya-labha)    adhyayas=1   — computed: 225-224=1
  sp18 (Harana-harika)  shlokas=82   — from section header text "eighty-two shlokas"
  sp64 (Bhishma-vadha)  shlokas=3947 — from section header (minor 4-shloka discrepancy with BORI total)
  sp77 (Gada-yuddha)    shlokas=546  — from section header (minor 1-shloka discrepancy with BORI total)
  sp85 (Apad-dharma)    shlokas=1560 — computed: 13006-4511-6935=1560 (OCR read "1,560" as "7,560")
  sp86 (Moksha-dharma)  shlokas=6935 — from section header (consistent with BORI total ✓)
"""

import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
STORY_DIR = os.path.join(BASE, "output", "json", "story")
JSON_DIR = os.path.join(BASE, "output", "json")

# ---------------------------------------------------------------------------
# BORI official sub-parva data — sourced from book introductions
# ---------------------------------------------------------------------------
BORI_PARVAS = [
    {
        "number": 1,
        "name": "Adi Parva",
        "bori_adhyayas": 225,
        "bori_shlokas": 7202,
        "sub_parvas": [
            # Source: BORI table in Volume 1 introduction
            {"number":  1, "name": "Anukramanika",          "adhyayas": 1,  "shlokas": 210,  "source": "bori_table"},
            {"number":  2, "name": "Parvasamgraha",         "adhyayas": 1,  "shlokas": 243,  "source": "bori_table"},
            {"number":  3, "name": "Poushya",               "adhyayas": 1,  "shlokas": 195,  "source": "bori_table"},
            {"number":  4, "name": "Pouloma",               "adhyayas": 9,  "shlokas": 153,  "source": "bori_table"},
            {"number":  5, "name": "Astika",                "adhyayas": 41, "shlokas": 1025, "source": "bori_table"},
            {"number":  6, "name": "Adi-vamshavatarana",    "adhyayas": 5,  "shlokas": 257,  "source": "bori_table"},
            {"number":  7, "name": "Sambhava",              "adhyayas": 65, "shlokas": 2394, "source": "bori_table"},
            # sp8: BORI table gives adhyayas=15 only; shlokas=373 from volume section header
            # Verified: 373+82=455 = 7202 - sum_of_others(6747)
            {"number":  8, "name": "Jatugriha-daha",        "adhyayas": 15, "shlokas": 373,
             "shlokas_note": "Not in BORI table; sourced from Section Eight header in volume text; consistent with parva total"},
            {"number":  9, "name": "Hidimba-vadha",         "adhyayas": 6,  "shlokas": 169,  "source": "bori_table"},
            {"number": 10, "name": "Baka-vadha",            "adhyayas": 8,  "shlokas": 206,  "source": "bori_table"},
            {"number": 11, "name": "Chaitraratha",          "adhyayas": 21, "shlokas": 557,  "source": "bori_table"},
            {"number": 12, "name": "Droupadi-svayamvara",   "adhyayas": 12, "shlokas": 263,  "source": "bori_table"},
            {"number": 13, "name": "Vaivahika",             "adhyayas": 6,  "shlokas": 155,  "source": "bori_table"},
            {"number": 14, "name": "Viduragamana",          "adhyayas": 7,  "shlokas": 174,  "source": "bori_table"},
            # sp15: BORI table gives shlokas=50 only; adhyayas=1 computed (225 - sum_of_others=224)
            {"number": 15, "name": "Rajya-labha",           "adhyayas": 1,  "shlokas": 50,
             "adhyayas_note": "Not in BORI table; computed as parva_total(225) minus sum_of_other_subparvas(224)"},
            {"number": 16, "name": "Arjuna-vanavasa",       "adhyayas": 11, "shlokas": 295,  "source": "bori_table"},
            {"number": 17, "name": "Subhadra-harana",       "adhyayas": 2,  "shlokas": 57,   "source": "bori_table"},
            # sp18: BORI table gives adhyayas=1 only; shlokas=82 from volume section header
            # Verified: 373+82=455 = 7202 - sum_of_others(6747)
            {"number": 18, "name": "Harana-harika",         "adhyayas": 1,  "shlokas": 82,
             "shlokas_note": "Not in BORI table; sourced from Section Eighteen header in volume text ('eighty-two shlokas'); consistent with parva total"},
            {"number": 19, "name": "Khandava-daha",         "adhyayas": 12, "shlokas": 344,  "source": "bori_table"},
        ]
    },
    {
        "number": 2,
        "name": "Sabha Parva",
        "bori_adhyayas": 72,
        "bori_shlokas": 2387,
        "sub_parvas": [
            {"number": 20, "name": "Sabha",            "adhyayas": 11, "shlokas": 429, "source": "bori_table"},
            {"number": 21, "name": "Mantra",           "adhyayas": 6,  "shlokas": 222, "source": "bori_table"},
            {"number": 22, "name": "Jarasandha-vadha", "adhyayas": 5,  "shlokas": 195, "source": "bori_table"},
            {"number": 23, "name": "Digvijaya",        "adhyayas": 7,  "shlokas": 188, "source": "bori_table"},
            {"number": 24, "name": "Rajasuya",         "adhyayas": 3,  "shlokas": 97,  "source": "bori_table"},
            {"number": 25, "name": "Arghabhirana",     "adhyayas": 4,  "shlokas": 99,  "source": "bori_table"},
            {"number": 26, "name": "Shishupala-vadha", "adhyayas": 6,  "shlokas": 191, "source": "bori_table"},
            {"number": 27, "name": "Dyuta",            "adhyayas": 23, "shlokas": 734, "source": "bori_table"},
            {"number": 28, "name": "Anudyuta",         "adhyayas": 7,  "shlokas": 232, "source": "bori_table"},
        ]
    },
    {
        "number": 3,
        "name": "Aranyaka Parva",
        "bori_adhyayas": 299,
        "bori_shlokas": 10239,
        "sub_parvas": [
            {"number": 29, "name": "Aranyaka",                    "adhyayas": 11, "shlokas": 327,  "source": "bori_table"},
            {"number": 30, "name": "Kirmira-vadha",               "adhyayas": 1,  "shlokas": 75,   "source": "bori_table"},
            {"number": 31, "name": "Kairata",                     "adhyayas": 30, "shlokas": 1158, "source": "bori_table"},
            {"number": 32, "name": "Indralokabhigamana",          "adhyayas": 37, "shlokas": 1157, "source": "bori_table"},
            {"number": 33, "name": "Tirtha-yatra",                "adhyayas": 74, "shlokas": 2422, "source": "bori_table"},
            {"number": 34, "name": "Jatasura-vadha",              "adhyayas": 1,  "shlokas": 61,   "source": "bori_table"},
            {"number": 35, "name": "Yaksha-yuddha",               "adhyayas": 18, "shlokas": 710,  "source": "bori_table"},
            {"number": 36, "name": "Ajagara",                     "adhyayas": 6,  "shlokas": 201,  "source": "bori_table"},
            {"number": 37, "name": "Markandeya-samasya",          "adhyayas": 43, "shlokas": 1656, "source": "bori_table"},
            {"number": 38, "name": "Droupadi-Satyabhama-sambada", "adhyayas": 3,  "shlokas": 88,   "source": "bori_table"},
            {"number": 39, "name": "Ghosha-yatra",                "adhyayas": 19, "shlokas": 519,  "source": "bori_table"},
            {"number": 40, "name": "Mriga-svapna-bhaya",          "adhyayas": 1,  "shlokas": 16,   "source": "bori_table"},
            {"number": 41, "name": "Vrihi-drounika",              "adhyayas": 3,  "shlokas": 117,  "source": "bori_table"},
            {"number": 42, "name": "Droupadi-harana",             "adhyayas": 36, "shlokas": 1247, "source": "bori_table"},
            {"number": 43, "name": "Kundala-harana",              "adhyayas": 11, "shlokas": 294,  "source": "bori_table"},
            {"number": 44, "name": "Araneya",                     "adhyayas": 5,  "shlokas": 191,  "source": "bori_table"},
        ]
    },
    {
        "number": 4,
        "name": "Virata Parva",
        "bori_adhyayas": 67,
        "bori_shlokas": 1736,
        "sub_parvas": [
            {"number": 45, "name": "Vairata",       "adhyayas": 12, "shlokas": 271, "source": "bori_table"},
            {"number": 46, "name": "Kichaka-vadha", "adhyayas": 11, "shlokas": 353, "source": "bori_table"},
            {"number": 47, "name": "Go-grahana",    "adhyayas": 39, "shlokas": 933, "source": "bori_table"},
            {"number": 48, "name": "Vaivahika",     "adhyayas": 5,  "shlokas": 179, "source": "bori_table"},
        ]
    },
    {
        "number": 5,
        "name": "Udyoga Parva",
        "bori_adhyayas": 197,
        "bori_shlokas": 6001,
        "sub_parvas": [
            {"number": 49, "name": "Udyoga",               "adhyayas": 21, "shlokas": 575,  "source": "bori_table"},
            {"number": 50, "name": "Sanjaya-yana",         "adhyayas": 11, "shlokas": 274,  "source": "bori_table"},
            {"number": 51, "name": "Prajagara",            "adhyayas": 9,  "shlokas": 541,  "source": "bori_table"},
            {"number": 52, "name": "Sanatsujata",          "adhyayas": 4,  "shlokas": 121,  "source": "bori_table"},
            {"number": 53, "name": "Yana-sandhi",          "adhyayas": 24, "shlokas": 709,  "source": "bori_table"},
            {"number": 54, "name": "Bhagavad-dhyana",      "adhyayas": 65, "shlokas": 2053, "source": "bori_table"},
            {"number": 55, "name": "Kamopani-vadha",       "adhyayas": 14, "shlokas": 351,  "source": "bori_table"},
            {"number": 56, "name": "Abhiniryana",          "adhyayas": 4,  "shlokas": 169,  "source": "bori_table"},
            {"number": 57, "name": "Bhishmabhishechana",   "adhyayas": 4,  "shlokas": 122,  "source": "bori_table"},
            {"number": 58, "name": "Uluka-yana",           "adhyayas": 4,  "shlokas": 100,  "source": "bori_table"},
            {"number": 59, "name": "Rathatiratha-sankhyana","adhyayas": 9, "shlokas": 231,  "source": "bori_table"},
            {"number": 60, "name": "Ambopakhyana",         "adhyayas": 28, "shlokas": 755,  "source": "bori_table"},
        ]
    },
    {
        "number": 6,
        "name": "Bhishma Parva",
        "bori_adhyayas": 117,
        "bori_shlokas": 5381,
        "sub_parvas": [
            {"number": 61, "name": "Jambukhanda-vinirmana", "adhyayas": 11, "shlokas": 377,  "source": "bori_table"},
            {"number": 62, "name": "Bhumi",                 "adhyayas": 2,  "shlokas": 87,   "source": "bori_table"},
            {"number": 63, "name": "Bhagavad-gita",         "adhyayas": 27, "shlokas": 974,  "source": "bori_table"},
            # sp64: BORI table gives adhyayas=77 only; shlokas=3947 from section header
            # Note: 377+87+974+3947=5385 vs BORI total 5381 (4-shloka discrepancy in source)
            {"number": 64, "name": "Bhishma-vadha",         "adhyayas": 77, "shlokas": 3947,
             "shlokas_note": "Not in BORI table; sourced from Section Sixty-Four header in volume text; minor 4-shloka discrepancy with parva total (5385 vs 5381)"},
        ]
    },
    {
        "number": 7,
        "name": "Drona Parva",
        "bori_adhyayas": 173,
        "bori_shlokas": 8069,
        "sub_parvas": [
            {"number": 65, "name": "Dronabhisheka",         "adhyayas": 15, "shlokas": 634,  "source": "bori_table"},
            {"number": 66, "name": "Samshaptaka-vadha",     "adhyayas": 16, "shlokas": 717,  "source": "bori_table"},
            {"number": 67, "name": "Abhimanyu-vadha",       "adhyayas": 20, "shlokas": 640,  "source": "bori_table"},
            {"number": 68, "name": "Pratijna",              "adhyayas": 9,  "shlokas": 365,  "source": "bori_table"},
            {"number": 69, "name": "Jayadratha-vadha",      "adhyayas": 61, "shlokas": 2834, "source": "bori_table"},
            {"number": 70, "name": "Ghatotkacha-vadha",     "adhyayas": 33, "shlokas": 1645, "source": "bori_table"},
            {"number": 71, "name": "Drona-vadha",           "adhyayas": 11, "shlokas": 692,  "source": "bori_table"},
            {"number": 72, "name": "Narayanaastra-moksha",  "adhyayas": 8,  "shlokas": 542,  "source": "bori_table"},
        ]
    },
    {
        "number": 8,
        "name": "Karna Parva",
        "bori_adhyayas": 69,
        "bori_shlokas": 3870,
        "sub_parvas": [
            {"number": 73, "name": "Karna-vadha", "adhyayas": 69, "shlokas": 3870, "source": "bori_table"},
        ]
    },
    {
        "number": 9,
        "name": "Shalya Parva",
        "bori_adhyayas": 64,
        "bori_shlokas": 3541,
        "sub_parvas": [
            {"number": 74, "name": "Shalya-vadha",   "adhyayas": 16, "shlokas": 1074, "source": "bori_table"},
            {"number": 75, "name": "Hrada-pravesha", "adhyayas": 12, "shlokas": 664,  "source": "bori_table"},
            {"number": 76, "name": "Tirtha-yatra",   "adhyayas": 25, "shlokas": 1258, "source": "bori_table"},
            # sp77: BORI table gives adhyayas=11 only; shlokas=546 from section header
            # Note: 1074+664+1258+546=3542 vs BORI total 3541 (1-shloka discrepancy in source)
            {"number": 77, "name": "Gada-yuddha",    "adhyayas": 11, "shlokas": 546,
             "shlokas_note": "Not in BORI table; sourced from Section Seventy-Seven header in volume text; minor 1-shloka discrepancy with parva total (3542 vs 3541)"},
        ]
    },
    {
        "number": 10,
        "name": "Sauptika Parva",
        "bori_adhyayas": 18,
        "bori_shlokas": 771,
        "sub_parvas": [
            {"number": 78, "name": "Souptika", "adhyayas": 9, "shlokas": 514, "source": "bori_table"},
            {"number": 79, "name": "Aishika",  "adhyayas": 9, "shlokas": 257, "source": "bori_table"},
        ]
    },
    {
        "number": 11,
        "name": "Stri Parva",
        "bori_adhyayas": 27,
        "bori_shlokas": 713,
        "sub_parvas": [
            {"number": 80, "name": "Vishoka",        "adhyayas": 8,  "shlokas": 177, "source": "bori_table"},
            {"number": 81, "name": "Stri-vilapa",    "adhyayas": 17, "shlokas": 468, "source": "bori_table"},
            {"number": 82, "name": "Shraddha",       "adhyayas": 1,  "shlokas": 44,  "source": "bori_table"},
            {"number": 83, "name": "Jala-pradanika", "adhyayas": 1,  "shlokas": 24,  "source": "bori_table"},
        ]
    },
    {
        "number": 12,
        "name": "Shanti Parva",
        "bori_adhyayas": 353,
        "bori_shlokas": 13006,
        "sub_parvas": [
            {"number": 84, "name": "Raja-dharma",   "adhyayas": 128, "shlokas": 4511, "source": "bori_table"},
            # sp85: BORI table gives adhyayas=39 only; shlokas=1560 computed from parva total
            # Section header OCR read "1,560" as "7,560" — discrepancy with total confirms OCR error
            # Verified: 4511+1560+6935=13006 ✓
            {"number": 85, "name": "Apad-dharma",   "adhyayas": 39,  "shlokas": 1560,
             "shlokas_note": "Not in BORI table; computed as parva_total(13006) minus Raja-dharma(4511) minus Moksha-dharma(6935)=1560; section header OCR erroneously shows 7,560"},
            # sp86: BORI table gives adhyayas=186 only; shlokas=6935 from section header
            # Section header shows "786 chapters" (OCR error for 186)
            # Verified: 4511+1560+6935=13006 ✓
            {"number": 86, "name": "Moksha-dharma", "adhyayas": 186, "shlokas": 6935,
             "shlokas_note": "Not in BORI table; sourced from Section Eighty-Six header in volume text (section header OCR shows '786 chapters' as error for 186); consistent with parva total"},
        ]
    },
    {
        "number": 13,
        "name": "Anushasana Parva",
        "bori_adhyayas": 154,
        "bori_shlokas": 6493,
        "sub_parvas": [
            {"number": 87, "name": "Dana-dharma",          "adhyayas": 152, "shlokas": 6409, "source": "bori_table"},
            {"number": 88, "name": "Bhishma-svargarohana", "adhyayas": 2,   "shlokas": 84,   "source": "bori_table"},
        ]
    },
    {
        "number": 14,
        "name": "Ashvamedhika Parva",
        "bori_adhyayas": 96,
        "bori_shlokas": 2741,
        "sub_parvas": [
            {"number": 89, "name": "Ashvamedha", "adhyayas": 96, "shlokas": 2741, "source": "bori_table"},
        ]
    },
    {
        "number": 15,
        "name": "Ashramavasika Parva",
        "bori_adhyayas": 47,
        "bori_shlokas": 1061,
        "sub_parvas": [
            {"number": 90, "name": "Ashrama-vasa",   "adhyayas": 35, "shlokas": 736, "source": "bori_table"},
            # sp91: BORI table OCR printed '134'; corrected to 234
            # Section header says 234; verified: 736+234+91=1061=Ashramavasika_total ✓
            {"number": 91, "name": "Putra-darshana", "adhyayas": 9,  "shlokas": 234,
             "shlokas_note": "BORI table OCR printed '134'; corrected to 234 — section header says 234; verified: 736+234+91=1061=parva_total"},
            {"number": 92, "name": "Naradagamana",   "adhyayas": 3,  "shlokas": 91,  "source": "bori_table"},
        ]
    },
    {
        "number": 16,
        "name": "Mausala Parva",
        "bori_adhyayas": 9,
        "bori_shlokas": 273,
        "sub_parvas": [
            {"number": 93, "name": "Mausala", "adhyayas": 9, "shlokas": 273, "source": "bori_table"},
        ]
    },
    {
        "number": 17,
        "name": "Mahaprasthanika Parva",
        "bori_adhyayas": 3,
        "bori_shlokas": 106,
        "sub_parvas": [
            {"number": 94, "name": "Mahaprasthanika", "adhyayas": 3, "shlokas": 106, "source": "bori_table"},
        ]
    },
    {
        "number": 18,
        "name": "Svargarohana Parva",
        "bori_adhyayas": 5,
        "bori_shlokas": 194,
        "sub_parvas": [
            {"number": 95, "name": "Svargarohana", "adhyayas": 5, "shlokas": 194, "source": "bori_table"},
        ]
    },
]

HARI_VAMSHA = {
    "note": "Regarded as a khila (supplement/epilogue) to the Mahabharata. Included by BORI in the critical edition in a separate volume. Included in Bibek Debroy's translation.",
    "sub_parvas": [
        {"number": 96, "name": "Hari-vamsha", "adhyayas": 45, "shlokas": 2442, "source": "bori_table"},
        {"number": 97, "name": "Vishnu",      "adhyayas": 68, "shlokas": 3426, "source": "bori_table"},
        {"number": 98, "name": "Bhavishya",   "adhyayas": 5,  "shlokas": 205,  "source": "bori_table"},
    ],
    "total_adhyayas": 118,
    "total_shlokas": 6073,
}


def build_bori_official():
    """Build bori_official.json — clean BORI data from book introductions, no nulls."""
    doc = {
        "_source": (
            "BORI Critical Edition (Bhandarkar Oriental Research Institute, Pune). "
            "Data extracted from the Introduction of Bibek Debroy's 10-volume unabridged "
            "translation of the Mahabharata (Penguin Books). "
            "Sub-parva shloka counts not listed in the BORI table are sourced from the "
            "per-section headers in the volume texts, or computed from parva totals minus "
            "known sub-parva totals. No null values — all fields are filled."
        ),
        "_null_resolution": {
            "sp8_Jatugriha-daha_shlokas": "373 — from 'Section Eight' header in volume text; verified: 373+82=455=Adi_total(7202)-sum_others(6747)",
            "sp15_Rajya-labha_adhyayas": "1 — computed: Adi_adhyayas(225) - sum_other_subparvas(224)",
            "sp18_Harana-harika_shlokas": "82 — from 'Section Eighteen' header in volume text ('eighty-two shlokas'); verified with sp8",
            "sp64_Bhishma-vadha_shlokas": "3947 — from 'Section Sixty-Four' header in volume text; minor 4-shloka discrepancy with BORI parva total",
            "sp77_Gada-yuddha_shlokas": "546 — from 'Section Seventy-Seven' header in volume text; minor 1-shloka discrepancy with BORI parva total",
            "sp85_Apad-dharma_shlokas": "1560 — computed: Shanti_total(13006)-Raja-dharma(4511)-Moksha-dharma(6935); section header OCR misread as 7,560",
            "sp86_Moksha-dharma_shlokas": "6935 — from 'Section Eighty-Six' header in volume text; section header OCR misread adhyayas as 786 (should be 186)",
        },
        "institution": "Bhandarkar Oriental Research Institute (BORI), Pune",
        "edition": "Critical Edition",
        "period": "1919–1966 (without Hari Vamsha); completed with Hari Vamsha by 1970",
        "totals": {
            "parvas_18": 18,
            "sub_parvas_98": 95,
            "adhyayas": 1995,
            "shlokas": 73784,
            "with_hari_vamsha": {
                "sub_parvas": 98,
                "adhyayas": 2113,
                "shlokas": 79857,
            }
        },
        "parvas": BORI_PARVAS,
        "hari_vamsha": HARI_VAMSHA,
    }
    out = os.path.join(JSON_DIR, "bori_official.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out}")
    # Verify: count nulls
    null_count = sum(
        1 for p in BORI_PARVAS for sp in p["sub_parvas"]
        if sp.get("adhyayas") is None or sp.get("shlokas") is None
    )
    print(f"  Null fields in sub_parvas: {null_count}  (should be 0)")
    # Sub-parva count
    total_sp = sum(len(p["sub_parvas"]) for p in BORI_PARVAS)
    print(f"  Sub-parvas: {total_sp}")
    total_ch = sum(p["bori_adhyayas"] for p in BORI_PARVAS)
    total_sh = sum(p["bori_shlokas"] for p in BORI_PARVAS)
    print(f"  Parva sum adhyayas: {total_ch}  (BORI says 1995)")
    print(f"  Parva sum shlokas:  {total_sh}  (BORI says 73784)")


def build_translation_data():
    """Build translation_data.json from extracted story JSON files."""
    files = sorted(f for f in os.listdir(STORY_DIR) if f.endswith(".json") and not f.endswith("_fn.json"))
    parvas = []
    total_chapters = 0
    total_shlokas = 0

    for fname in files:
        fpath = os.path.join(STORY_DIR, fname)
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)

        pnum = data["parva_number"]
        pname = data["name"]
        pdetails = data.get("details", {})
        sub_parvas_raw = data.get("subparvas", {})

        sub_parvas_out = []
        parva_ch_count = 0
        parva_sh_count = 0

        for spkey in sorted(sub_parvas_raw.keys(), key=lambda x: int(x)):
            sp = sub_parvas_raw[spkey]
            sp_num = int(spkey)
            sp_name = sp.get("name", "")
            chapters_raw = sp.get("chapters", {})
            ch_count = len(chapters_raw)
            sh_count = sum(
                (ch.get("num_shlokas") or 0) for ch in chapters_raw.values()
            )
            ch_with_shlokas = sum(
                1 for ch in chapters_raw.values() if ch.get("num_shlokas") is not None
            )
            ch_missing_shlokas = ch_count - ch_with_shlokas

            sub_parvas_out.append({
                "number": sp_num,
                "name": sp_name,
                "source_volume": sp.get("source_volume"),
                "chapters": ch_count,
                "shlokas_from_headers": sh_count,
                "chapters_with_shloka_count": ch_with_shlokas,
                "chapters_missing_shloka_count": ch_missing_shlokas,
            })
            parva_ch_count += ch_count
            parva_sh_count += sh_count

        parva_entry = {
            "number": pnum,
            "name": pname,
            "chapters": parva_ch_count,
            "shlokas_from_headers": parva_sh_count,
            "sub_parvas": sub_parvas_out,
        }
        parvas.append(parva_entry)
        total_chapters += parva_ch_count
        total_shlokas += parva_sh_count

    doc = {
        "_source": (
            "Bibek Debroy's unabridged English translation of the Mahabharata (Penguin Books, 10 volumes). "
            "Counts are extracted from OCR'd chapter headers in the text. "
            "'shlokas_from_headers' counts only shlokas explicitly given in chapter headers "
            "(headers with missing counts — marked [?] in the OCR — contribute 0 to the sum). "
            "This differs from the BORI Critical Edition counts in bori_official.json."
        ),
        "translator": "Bibek Debroy",
        "publisher": "Penguin Books",
        "num_volumes": 10,
        "total_chapters": total_chapters,
        "total_shlokas_from_headers": total_shlokas,
        "note_on_shlokas": (
            "5 chapter headers have [?] shloka counts (chapters 309, 451, 541, 1091, 1149). "
            "Their shlokas are not included in 'shlokas_from_headers' totals."
        ),
        "parvas": parvas,
    }
    out = os.path.join(JSON_DIR, "translation_data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out}")
    print(f"  Total chapters: {total_chapters}  (should be 1995)")
    print(f"  Total shlokas from headers: {total_shlokas}")


def fix_introduction_json():
    """Fix introduction.json by replacing all null values with the resolved values."""
    intro_path = os.path.join(JSON_DIR, "introduction.json")
    with open(intro_path, encoding="utf-8") as f:
        intro = json.load(f)

    # Map: (parva_number, sp_number) -> {field: value}
    fixes = {
        (1,  8):  {"shlokas": 373},
        (1, 15):  {"adhyayas": 1},
        (1, 18):  {"shlokas": 82},
        (6, 64):  {"shlokas": 3947},
        (9, 77):  {"shlokas": 546},
        (12, 85): {"shlokas": 1560},
        (12, 86): {"shlokas": 6935},
    }

    null_before = 0
    null_after = 0

    for parva in intro.get("parvas", []):
        pn = parva["number"]
        for sp in parva.get("sub_parvas", []):
            spn = sp["number"]
            # Count nulls before
            for k, v in sp.items():
                if v is None:
                    null_before += 1

            key = (pn, spn)
            if key in fixes:
                for field, val in fixes[key].items():
                    sp[field] = val

            # Count nulls after
            for k, v in sp.items():
                if v is None:
                    null_after += 1

    # Update the _notes field
    intro["_notes"] = (
        "Data sourced from the Introduction of Bibek Debroy's 10-volume unabridged translation "
        "of the Mahabharata (Penguin Books). Based on the BORI Critical Edition (Bhandarkar "
        "Oriental Research Institute, Pune). Sub-parva shloka counts not listed in the BORI "
        "table are sourced from the per-section headers in the volume texts, or computed from "
        "parva totals. See bori_official.json for full resolution notes."
    )

    with open(intro_path, "w", encoding="utf-8") as f:
        json.dump(intro, f, ensure_ascii=False, indent=2)
    print(f"Updated {intro_path}")
    print(f"  Null fields before: {null_before}")
    print(f"  Null fields after:  {null_after}  (should be 0)")


if __name__ == "__main__":
    print("=== Building BORI official JSON ===")
    build_bori_official()
    print()
    print("=== Building translation data JSON ===")
    build_translation_data()
    print()
    print("=== Fixing introduction.json ===")
    fix_introduction_json()
    print()
    print("Done.")
