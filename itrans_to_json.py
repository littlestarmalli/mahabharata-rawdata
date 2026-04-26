"""
itrans_to_json.py

Parse the 18 BORI ITRANS text files (mbh01.itx–mbh18.itx) into structured JSON.

Source: BORI Critical Edition Sanskrit text, ITRANS 5.3 transliteration,
        Prof. Tokunaga / proofread by BORI team. Via sanskritdocuments.org.

File format:
  - Chapter boundaries: \\hrule
  - Chapter header after \\hrule:
      \\medskip
      [              subparvaName      ]   <- 14-space indent, present only when sub-parva changes
                        chapterNumber      <- 18-space indent
      \\medskip
  - First chapter (no preceding \\hrule):
                anukramaNIparva
                    1
      \\medskip
  - Shloka end:  || N||   (verse number N)
  - Prose end:   | NNN |  (prose/compound section)
  - Speaker:     name uvAcha||  (no number → not a shloka marker)
"""

import re
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ITRANS_DIR = os.path.join(BASE, "itrans_text")
OUT_DIR = os.path.join(BASE, "output", "json", "bori_text")
os.makedirs(OUT_DIR, exist_ok=True)

SOURCE_NOTE = (
    "BORI Critical Edition Sanskrit text in ITRANS 5.3 transliteration. "
    "Transliterated by Prof. Muneo Tokunaga; proofread by BORI team. "
    "Via sanskritdocuments.org."
)

PARVA_NAMES = {
    1:  "Adi Parva",
    2:  "Sabha Parva",
    3:  "Vana Parva",
    4:  "Virata Parva",
    5:  "Udyoga Parva",
    6:  "Bhishma Parva",
    7:  "Drona Parva",
    8:  "Karna Parva",
    9:  "Shalya Parva",
    10: "Sauptika Parva",
    11: "Stri Parva",
    12: "Shanti Parva",
    13: "Anushasana Parva",
    14: "Ashvamedhika Parva",
    15: "Ashramavasika Parva",
    16: "Mausala Parva",
    17: "Mahaprasthanika Parva",
    18: "Svargarohana Parva",
}

FILE_NAMES = {
    1:  "parva_01_adi",
    2:  "parva_02_sabha",
    3:  "parva_03_vana",
    4:  "parva_04_virata",
    5:  "parva_05_udyoga",
    6:  "parva_06_bhishma",
    7:  "parva_07_drona",
    8:  "parva_08_karna",
    9:  "parva_09_shalya",
    10: "parva_10_sauptika",
    11: "parva_11_stri",
    12: "parva_12_shanti",
    13: "parva_13_anushasana",
    14: "parva_14_ashvamedhika",
    15: "parva_15_ashramavasika",
    16: "parva_16_mausala",
    17: "parva_17_mahaprasthanika",
    18: "parva_18_svargarohana",
}

# Regex for shloka end markers
# Group 1: verse  || N||
# Group 2: prose  | N | (not preceded or followed by |)
SHLOKA_MARKER = re.compile(r'\|\|\s*(\d+)\s*\|\||\|(?!\|)\s*(\d+)\s*\|(?!\|)')


def clean_shloka_text(text):
    """Remove LaTeX formatting commands from shloka text, keeping Sanskrit content."""
    # Remove \word{...} LaTeX commands (e.g. \engtitle{...})
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
    # Remove bare \word LaTeX commands (e.g. \medskip, \bg, \hrule, \endtitles)
    text = re.sub(r'\\[a-zA-Z]+\b', '', text)
    # Remove ##  markers from title lines
    text = re.sub(r'##', '', text)
    # Collapse resulting multiple whitespace/blank lines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n', text)
    return text.strip()


def extract_shlokas(body_text):
    """
    Extract shlokas from chapter body text.
    Returns dict: {num_str: cleaned_text}

    Handles:
    - Regular verse ending with || N||
    - Prose section ending with | N | (three-digit-padded)
    - Split shlokas: same shloka number appears twice (e.g. a triplet verse)
      → concatenated with a newline
    - Ignores text after the last marker (footnotes/commentary)
    """
    shlokas = {}
    pos = 0

    for m in SHLOKA_MARKER.finditer(body_text):
        chunk = body_text[pos:m.start()]
        num_str = m.group(1) if m.group(1) is not None else m.group(2)

        # Clean the chunk: remove LaTeX commands, collapse whitespace
        chunk = clean_shloka_text(chunk)

        if num_str is not None:
            if num_str in shlokas:
                # Same number again (triplet / split verse): append
                if chunk:
                    shlokas[num_str] = shlokas[num_str] + '\n' + chunk
            else:
                shlokas[num_str] = chunk

        pos = m.end()

    return shlokas



def parse_itx_file(parva_num):
    """
    Parse mbhNN.itx and return a structured dict with sub-parvas and shlokas.

    Chapter-boundary strategy:
      Primary pattern: a line with ≥16 spaces of indentation containing only digits,
      immediately followed by \\medskip.  This uniquely identifies a chapter-number line
      in the ITRANS format.  The optional line immediately before (with 10–16 spaces,
      starting with a letter) is the sub-parva name.

      This is more robust than splitting by \\hrule because some chapter boundaries
      (e.g. pauShyaparva→paulomaparva in Adi Parva) use a \\medskip boundary rather
      than a \\hrule.
    """
    itx_filename = f"mbh{parva_num:02d}.itx"
    filepath = os.path.join(ITRANS_DIR, itx_filename)

    if not os.path.exists(filepath):
        print(f"  WARNING: {itx_filename} not found, skipping.")
        return None

    txt = open(filepath, encoding='utf-8', errors='replace').read()

    # Find content start (after \endtitles ## line)
    endtitles_match = re.search(r'\\endtitles\s*##', txt)
    if endtitles_match:
        content = txt[endtitles_match.end():]
    else:
        content = re.sub(r'^%[^\n]*\n', '', txt, flags=re.MULTILINE)

    # ── Find all chapter headers ──────────────────────────────────────────────
    # Pattern:
    #   Optional sub-parva name line: 10–16 spaces + letter-starting word(s)
    #   Chapter number line         : ≥16 spaces    + pure digits
    #   \\medskip                   : signals end of chapter header / start of body
    #
    # The sub-parva name MUST be on the line immediately above the chapter number
    # (no blank lines in between), and must start with a letter (not \ or %).
    CHAPTER_HEADER = re.compile(
        r'(?:^|(?<=\n))'                       # start of line
        r'([ \t]{10,16}[a-zA-Z][^\n]*\n)?'    # optional sub-parva name (group 1)
        r'([ \t]{16,})(\d+)\n'                 # chapter number line (group 3)
        r'\\medskip'                            # trailing \medskip
    )

    matches = list(CHAPTER_HEADER.finditer(content))

    # ── Extract chapter blocks ────────────────────────────────────────────────
    parsed_chapters = []

    for i, m in enumerate(matches):
        sp_name_raw = m.group(1)          # e.g. "              pauShyaparva\n" or None
        ch_num = int(m.group(3))

        # Clean the sub-parva name
        if sp_name_raw:
            sp_name = sp_name_raw.strip()
            # Reject if it looks like a LaTeX command or comment
            if sp_name.startswith('\\') or sp_name.startswith('%'):
                sp_name = None
        else:
            sp_name = None

        # Body: from end of this match to start of next match
        body_start = m.end()
        if i + 1 < len(matches):
            # End body before the optional sub-parva name of the next chapter header
            next_m = matches[i + 1]
            body_end = next_m.start()
        else:
            body_end = len(content)

        body_text = content[body_start:body_end]

        # Strip chapter-separator commands from body edges
        body_text = re.sub(r'\\hrule\s*', '', body_text)
        body_text = body_text.strip()

        shlokas = extract_shlokas(body_text)

        parsed_chapters.append({
            'sp_name': sp_name,
            'ch_num': ch_num,
            'shlokas': shlokas,
        })

    if not parsed_chapters:
        print(f"  WARNING: No chapters parsed from {itx_filename}")
        return None

    # ── Group chapters into sub-parvas ────────────────────────────────────────
    subparvas_list = []   # ordered list of sub-parva dicts
    current_sp = None     # current sub-parva dict (being built)
    sp_counter = 0
    local_ch_counter = 0  # local chapter number within sub-parva

    for entry in parsed_chapters:
        ch_num = entry['ch_num']
        sp_name = entry['sp_name']
        shlokas = entry['shlokas']

        # New sub-parva?
        if sp_name is not None and (current_sp is None or sp_name != current_sp['name']):
            if current_sp is not None:
                subparvas_list.append(current_sp)
            sp_counter += 1
            local_ch_counter = 0
            current_sp = {
                'number': sp_counter,
                'name': sp_name,
                'start_chapter': ch_num,
                'end_chapter': ch_num,
                'chapters': {},
            }
        elif current_sp is None:
            # First chapter has no sub-parva name? Shouldn't happen, but handle gracefully.
            sp_counter += 1
            local_ch_counter = 0
            current_sp = {
                'number': sp_counter,
                'name': f'unknown_sp_{sp_counter}',
                'start_chapter': ch_num,
                'end_chapter': ch_num,
                'chapters': {},
            }

        local_ch_counter += 1
        current_sp['end_chapter'] = ch_num
        current_sp['chapters'][str(ch_num)] = {
            'chapter_number': ch_num,
            'local_number': local_ch_counter,
            'num_shlokas': len(shlokas),
            'shlokas': shlokas,
        }

    # Append final sub-parva
    if current_sp is not None:
        subparvas_list.append(current_sp)

    # ── Build final subparvas dict with details ───────────────────────────────
    subparvas_out = {}
    total_shlokas = 0

    for sp in subparvas_list:
        sp_total_sh = sum(ch['num_shlokas'] for ch in sp['chapters'].values())
        total_shlokas += sp_total_sh
        subparvas_out[str(sp['number'])] = {
            'number': sp['number'],
            'name': sp['name'],
            'start_chapter': sp['start_chapter'],
            'end_chapter': sp['end_chapter'],
            'details': {
                'num_chapters': len(sp['chapters']),
                'num_shlokas': sp_total_sh,
            },
            'chapters': sp['chapters'],
        }

    total_chapters = sum(len(sp['chapters']) for sp in subparvas_list)

    return {
        '_source': SOURCE_NOTE,
        'parva_number': parva_num,
        'name': PARVA_NAMES[parva_num],
        'file': itx_filename,
        'details': {
            'num_subparvas': len(subparvas_list),
            'num_chapters': total_chapters,
            'num_shlokas': total_shlokas,
        },
        'subparvas': subparvas_out,
    }


def main():
    print("=== ITRANS to JSON Converter ===")
    print(f"Input : {ITRANS_DIR}")
    print(f"Output: {OUT_DIR}")
    print()

    summary_rows = []

    for parva_num in range(1, 19):
        itx_name = f"mbh{parva_num:02d}.itx"
        print(f"Parva {parva_num:2d}: {PARVA_NAMES[parva_num]:<35}", end=' ')
        sys.stdout.flush()

        data = parse_itx_file(parva_num)
        if data is None:
            print("SKIPPED")
            continue

        d = data['details']
        print(
            f"{d['num_subparvas']:3d} sub-parvas  "
            f"{d['num_chapters']:4d} chapters  "
            f"{d['num_shlokas']:6d} shlokas"
        )

        out_path = os.path.join(OUT_DIR, FILE_NAMES[parva_num] + "_bori_text.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        summary_rows.append((parva_num, PARVA_NAMES[parva_num], d['num_subparvas'],
                              d['num_chapters'], d['num_shlokas']))

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("=== SUMMARY ===")
    print(f"{'#':>3}  {'Parva':<35} {'SP':>4}  {'Ch':>5}  {'Shlokas':>8}")
    print("-" * 65)
    total_ch = total_sh = 0
    for row in summary_rows:
        pn, name, sp, ch, sh = row
        print(f"{pn:3d}  {name:<35} {sp:4d}  {ch:5d}  {sh:8d}")
        total_ch += ch
        total_sh += sh
    print("-" * 65)
    print(f"{'TOT':<40} {total_ch:5d}  {total_sh:8d}")
    print()
    print(f"BORI official totals: 1995 chapters, 73784 shlokas")
    print(f"ITRANS parsed totals: {total_ch} chapters, {total_sh} shlokas")
    print(f"Output files: {OUT_DIR}")


if __name__ == "__main__":
    main()
