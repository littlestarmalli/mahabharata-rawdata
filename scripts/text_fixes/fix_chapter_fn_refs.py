"""
fix_chapter_fn_refs.py

Fixes dropped OCR footnote reference markers ({N}) in chapter files.

The OCR sometimes lost the superscript footnote marker, leaving a bare number
in the text. This script identifies candidates using the footnotes cross-check
(orphan defs that are also ref-sequence gaps) and recovers them using
OCR drop patterns:

  Pattern 1: word + N + em/en dash       e.g. 'vijnana18—'  → 'vijnana{18}—'
  Pattern 2: punct + N + uppercase/space e.g. 'Pavaka!4Tell' → 'Pavaka!{4}Tell'
  Pattern 3: space + N + space (space-isolated, used for dense-orphan sections
             like Bhagavad Gita)         e.g. 'father 3 has' → 'father{3} has'

Only fn numbers that are BOTH orphaned (defined but unreferenced) AND fall in a
ref sequence gap are treated as dropped OCR markers.

After fixing, re-runs verify_footnotes.py to update the reports.
"""

import re
import os
import sys

BASE    = os.path.dirname(os.path.abspath(__file__))
VOL_DIR = os.path.join(BASE, "output", "volumes")
sys.path.insert(0, BASE)

from verify_footnotes import (
    parse_footnotes_file,
    load_chapter_refs_by_chapter,
    analyze_section,
)

CH_HDR_RE = re.compile(r"^--- Chapter (\d+)")


# ── OCR pattern repair ────────────────────────────────────────────────────────

def try_fix_bare(text: str, n: int, use_space_isolated: bool = False):
    """
    Search text for bare occurrence of n matching an OCR drop pattern.
    Returns (new_text, fixes_applied).
    Stops at the first pattern that matches (most specific first).
    """
    ns = str(n)

    # Pattern 1: word char immediately before N, em/en dash immediately after
    #   'sons3—'  →  'sons{3}—'
    p1 = re.compile(r"(?<=[a-zA-Z])" + re.escape(ns) + r"(?=[—–])")
    new, c = p1.subn("{" + ns + "}", text, count=1)
    if c:
        return new, c

    # Pattern 2: punctuation before N, uppercase letter or newline immediately after
    #   '!4Tell'  →  '!{4}Tell'
    p2 = re.compile(r"(?<=[!?:,;.])" + re.escape(ns) + r"(?=[A-Z\n])")
    new, c = p2.subn("{" + ns + "}", text, count=1)
    if c:
        return new, c

    # Pattern 3: space-isolated — 'word N word' → 'word{N} word'
    # Only used for sections with many orphans (e.g. Bhagavad Gita) where
    # OCR consistently dropped the marker leaving spaces around the number.
    if use_space_isolated:
        p3 = re.compile(r"(?<=[a-zA-Z,;.!?]) " + re.escape(ns) + r" (?=[a-zA-Z])")
        new, c = p3.subn("{" + ns + "} ", text, count=1)
        if c:
            return new, c

    return text, 0


# ── per-volume fix ────────────────────────────────────────────────────────────

def fix_chapters_vol(vol: int):
    """
    Fix dropped fn refs in the chapter file for one volume.
    Returns (fixed_count, not_found_count).
    """
    sections, _ = parse_footnotes_file(vol)
    ch_refs      = load_chapter_refs_by_chapter(vol)

    ch_path = os.path.join(VOL_DIR, f"volume_{vol}_chapters.txt")
    with open(ch_path, encoding="utf-8") as f:
        ch_content = f.read()

    # Split into individual chapter segments (split at each chapter header)
    segments = re.split(r"(?=--- Chapter \d+)", ch_content)

    # Build chapter_num → segment_index
    ch_to_idx: dict[int, int] = {}
    for i, seg in enumerate(segments):
        m = CH_HDR_RE.match(seg.strip())
        if m:
            ch_to_idx[int(m.group(1))] = i

    fixed_total = 0
    not_found   = 0

    for sec in sections:
        result     = analyze_section(sec, ch_refs)
        orphan_set = set(result["orphan_defs"])
        gap_set    = set(result["ref_gaps"])

        # Only fix numbers that are both defined (orphan) and missing from the
        # ref sequence (gap) — strongest signal that the marker was dropped.
        candidates = sorted(orphan_set & gap_set)
        if not candidates:
            continue

        # Sections with many orphans likely had systematic space-isolated drops
        use_space_iso = len(orphan_set) > 50

        for n in candidates:
            found = False
            for ch in range(sec.ch_start, sec.ch_end + 1):
                idx = ch_to_idx.get(ch)
                if idx is None:
                    continue
                new_seg, c = try_fix_bare(segments[idx], n, use_space_iso)
                if c:
                    segments[idx]  = new_seg
                    fixed_total   += c
                    found          = True
                    break           # found in one chapter; move to next fn

            if not found:
                not_found += 1

    with open(ch_path, "w", encoding="utf-8") as f:
        f.write("".join(segments))

    return fixed_total, not_found


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    grand_fixed = 0
    grand_miss  = 0
    for vol in range(1, 11):
        try:
            f, n = fix_chapters_vol(vol)
            print(f"Vol {vol:>2}: fixed={f:>4}, not_found={n:>3}")
            grand_fixed += f
            grand_miss  += n
        except Exception as e:
            import traceback
            print(f"Vol {vol:>2}: ERROR - {e}")
            traceback.print_exc()

    print(f"\nTotal fixed: {grand_fixed},  still not found: {grand_miss}")

    # Re-run verify_footnotes to update reports
    print("\nRe-running footnote cross-check to update reports...")
    import verify_footnotes
    verify_footnotes.main()


if __name__ == "__main__":
    main()
