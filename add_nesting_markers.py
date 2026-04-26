#!/usr/bin/env python3
"""
add_nesting_markers.py  (v2)
Replace Unicode quote characters with nesting brackets in chapter JSON files.

  Opening \u2018 (\u2018) \u2192 {    Closing \u2019 (\u2019) \u2192 }
  Opening \u201c (\u201c) \u2192 [    Closing \u201d (\u201d) \u2192 ]

Key behaviours:
  - Apostrophes (letter-\u2019-letter) are preserved as-is
  - Multi-paragraph continuation: re-opening \u2018 or \u201c at paragraph start
    when already inside a frame stays at the SAME depth (no extra nesting)
  - Depth carries across paragraphs within one chapter; resets per chapter
  - Reads from original flat subparva JSONs, writes to chapter folder files
"""

import json, sys
from pathlib import Path

STORY_DIR = Path("output/json/story")

SQ_OPEN  = '\u2018'
SQ_CLOSE = '\u2019'
DQ_OPEN  = '\u201c'
DQ_CLOSE = '\u201d'


def _is_apostrophe(text, i):
    """Detect apostrophes: letter-'-letter (don't, Pandu's) or s-'- (Pandavas')."""
    if i <= 0:
        return False
    prev = text[i - 1]
    nxt = text[i + 1] if i + 1 < len(text) else ''
    # Standard apostrophe: letter-'-letter
    if prev.isalpha() and nxt.isalpha():
        return True
    # Possessive after s: ...s'-  (Pandavas' fame)
    if prev == 's' and (not nxt or nxt in ' \t,;:.!?)]}'):
        return True
    return False


def process_chapter_paragraphs(paras_dict):
    """
    Process all paragraphs of one chapter sequentially.
    Track sq_depth / dq_depth across paragraph boundaries.
    Returns dict of paragraph key -> new text.
    """
    keys = sorted(paras_dict, key=lambda k: int(k))
    sq_depth = 0
    dq_depth = 0
    new_paras = {}

    for k in keys:
        text = paras_dict[k]
        if not isinstance(text, str):
            new_paras[k] = text
            continue

        chars = list(text)
        n = len(chars)
        i = 0
        at_para_start = True  # True while in leading whitespace / quote-opens

        while i < n:
            ch = chars[i]

            # --- Curly single-quote OPEN (U+2018) ---
            if ch == SQ_OPEN:
                if at_para_start and sq_depth > 0:
                    chars[i] = '{'          # continuation — no depth change
                else:
                    chars[i] = '{'
                    sq_depth += 1
                # keep at_para_start True so next char can also be continuation
                i += 1
                continue

            # --- Curly single-quote CLOSE (U+2019) ---
            if ch == SQ_CLOSE:
                if _is_apostrophe(text, i):
                    if ch not in (' ', '\t'):
                        at_para_start = False
                    i += 1
                    continue
                chars[i] = '}'
                sq_depth = max(0, sq_depth - 1)
                at_para_start = False
                i += 1
                continue

            # --- Curly double-quote OPEN (U+201C) ---
            if ch == DQ_OPEN:
                if at_para_start and dq_depth > 0:
                    chars[i] = '['          # continuation
                else:
                    chars[i] = '['
                    dq_depth += 1
                i += 1
                continue

            # --- Curly double-quote CLOSE (U+201D) ---
            if ch == DQ_CLOSE:
                chars[i] = ']'
                dq_depth = max(0, dq_depth - 1)
                at_para_start = False
                i += 1
                continue

            # --- Straight single quote ---
            if ch == "'":
                if _is_apostrophe(text, i):
                    at_para_start = False
                    i += 1
                    continue
                prev = text[i - 1] if i > 0 else ''
                if not prev or prev in ' \t\n({[,;:.!?':
                    # Treat as open
                    if at_para_start and sq_depth > 0:
                        chars[i] = '{'
                    else:
                        chars[i] = '{'
                        sq_depth += 1
                else:
                    # Treat as close
                    chars[i] = '}'
                    sq_depth = max(0, sq_depth - 1)
                at_para_start = False
                i += 1
                continue

            # --- Straight double quote ---
            if ch == '"':
                prev = text[i - 1] if i > 0 else ''
                if not prev or prev in ' \t\n({[,;:.!?':
                    if at_para_start and dq_depth > 0:
                        chars[i] = '['
                    else:
                        chars[i] = '['
                        dq_depth += 1
                else:
                    chars[i] = ']'
                    dq_depth = max(0, dq_depth - 1)
                at_para_start = False
                i += 1
                continue

            # Non-whitespace clears para-start mode
            if ch not in (' ', '\t'):
                at_para_start = False
            i += 1

        new_paras[k] = ''.join(chars)

    return new_paras


def main():
    pf = None
    if '--parva' in sys.argv:
        pf = int(sys.argv[sys.argv.index('--parva') + 1])

    total_ch, total_p = 0, 0

    for parva_dir in sorted(STORY_DIR.glob('parva_*')):
        if not parva_dir.is_dir():
            continue
        pnum = int(parva_dir.name.split('_')[1])
        if pf and pnum != pf:
            continue

        print(f'\n=== {parva_dir.name} ===')

        # Iterate flat subparva JSONs (originals with Unicode quotes)
        for sp_file in sorted(parva_dir.glob('subparva_*.json')):
            if '_tagged' in sp_file.name:
                continue
            if sp_file.parent != parva_dir:
                continue

            with open(sp_file, encoding='utf-8') as f:
                sp = json.load(f)

            chapters = sp.get('chapters', {})
            if not chapters:
                continue

            base_name = sp_file.stem
            ch_folder = parva_dir / base_name
            if not ch_folder.is_dir():
                print(f'  SKIP {base_name} (no chapter folder)')
                continue

            ch_count = 0
            for ch_key, ch_data in sorted(chapters.items(), key=lambda x: int(x[0])):
                paras = ch_data.get('paragraphs', {})
                if not paras:
                    continue

                new_paras = process_chapter_paragraphs(paras)

                ch_num = int(ch_key)
                ch_path = ch_folder / f'chapter_{ch_num:03d}.json'

                ch_out = {
                    "chapter_number": ch_num,
                    "global_number": ch_data.get("global_number"),
                    "local_number": ch_data.get("local_number"),
                    "num_shlokas": ch_data.get("num_shlokas"),
                    "paragraphs": new_paras,
                }

                with open(ch_path, 'w', encoding='utf-8') as f:
                    json.dump(ch_out, f, ensure_ascii=False, indent=2)

                total_ch += 1
                total_p += len(new_paras)
                ch_count += 1

            if ch_count:
                print(f'  {base_name}/ ({ch_count} chapters)')

    print(f'\nDone. {total_ch} chapters, {total_p} paragraphs.')


if __name__ == '__main__':
    main()
