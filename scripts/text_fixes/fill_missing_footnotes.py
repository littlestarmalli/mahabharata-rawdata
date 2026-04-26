"""
fill_missing_footnotes.py

For each volume_N_footnotes.txt, finds lines like:
    N [MISSING FOOTNOTE — referenced in: ...]
and looks up the actual footnote text from Complete_text_mahabharat.txt
by matching the section's existing footnotes against input file blocks.

Replaces the placeholder with the actual text when found.
"""
import re, os

BASE    = os.path.dirname(os.path.abspath(__file__))
INPUT   = os.path.join(BASE, "input", "Complete_text_mahabharat.txt")
VOL_DIR = os.path.join(BASE, "output", "volumes")

FN_RE      = re.compile(r'^\s*(\d+)\s+(.+)')
MISSING_RE = re.compile(r'^(\d+)\s+\[MISSING FOOTNOTE')
SECTION_RE = re.compile(r'^________\s+(.+?)\s+\[')
RANGE_RE   = re.compile(r'^--- Chapters')


# ── build all real blocks from input file ────────────────────────────────────
def load_input_blocks():
    with open(INPUT, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    blocks = []
    cur = {}
    prev_n = 0
    prev_li = -1
    for i, l in enumerate(lines):
        stripped = l.rstrip()
        if stripped.startswith('[MISSING'):
            continue
        m = FN_RE.match(stripped)
        if m:
            n, text = int(m.group(1)), m.group(2).strip()
            if cur and (n < prev_n - 5 or i - prev_li > 10):
                blocks.append(cur)
                cur = {}
            cur[n] = text
            prev_n = n
            prev_li = i
    if cur:
        blocks.append(cur)
    return [b for b in blocks if len(b) >= 3]


# ── find the best matching block for a section ───────────────────────────────
def find_best_block(existing: dict, blocks: list) -> dict:
    """existing = {fn_num: text_snippet} — from the volume footnotes section.
    Returns the input block that has the most matching fn_num:text pairs."""
    if not existing:
        return {}
    best_score = 0
    best_block = {}
    check_nums = list(existing.keys())[:8]  # compare first 8 entries
    for block in blocks:
        score = 0
        for n in check_nums:
            if n in block and existing[n][:20] in block[n]:
                score += 1
        if score > best_score:
            best_score = score
            best_block = block
    return best_block if best_score >= 1 else {}


# ── process one volume footnotes file ────────────────────────────────────────
def process_volume(vol: int, blocks: list) -> tuple[int, int]:
    path = os.path.join(VOL_DIR, f"volume_{vol}_footnotes.txt")
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    filled = 0
    not_found = 0

    # Parse into sections; for each section collect existing fns then fill missing
    # We do two passes: pass 1 - collect existing fns per section range
    # pass 2 - replace MISSING lines using best matched block

    # Identify section boundaries
    sec_starts = []  # list of (line_idx_of_section_header)
    for i, l in enumerate(lines):
        if SECTION_RE.match(l.strip()):
            sec_starts.append(i)
    sec_starts.append(len(lines))  # sentinel

    result = list(lines)
    offset = 0  # cumulative insertion offset

    for s_idx in range(len(sec_starts) - 1):
        s_start = sec_starts[s_idx] + offset
        s_end   = sec_starts[s_idx + 1] + offset

        # Collect existing fn defs in this section (non-missing)
        existing = {}
        for i in range(s_start, s_end):
            l = result[i].rstrip()
            if MISSING_RE.match(l):
                continue
            m = FN_RE.match(l)
            if m:
                n, text = int(m.group(1)), m.group(2).strip()
                existing[n] = text

        best_block = find_best_block(existing, blocks)

        # Build a fallback lookup: for any fn_num, collect from ALL blocks
        # (used when the primary block doesn't have the fn_num)
        fallback: dict[int, str] = {}
        for b in blocks:
            for n, text in b.items():
                if n not in fallback or len(text) > len(fallback[n]):
                    fallback[n] = text  # prefer longer text

        # Now replace MISSING lines in this section
        i = s_start
        while i < s_end:
            l = result[i].rstrip()
            mm = MISSING_RE.match(l)
            if mm:
                n = int(mm.group(1))
                if n in best_block:
                    result[i] = f"{n} {best_block[n]}\n"
                    filled += 1
                elif n in fallback:
                    result[i] = f"{n} {fallback[n]}\n"
                    filled += 1
                else:
                    not_found += 1
            i += 1

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(result)

    return filled, not_found


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    print("Loading input blocks...")
    blocks = load_input_blocks()
    print(f"  {len(blocks)} blocks loaded")

    total_filled = total_not_found = 0
    for vol in range(1, 11):
        filled, not_found = process_volume(vol, blocks)
        total_filled += filled
        total_not_found += not_found
        print(f"  Vol {vol}: filled={filled}, still_missing={not_found}")

    print(f"\nTotal filled: {total_filled},  still missing: {total_not_found}")

if __name__ == "__main__":
    main()
