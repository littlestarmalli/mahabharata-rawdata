"""
extract_parva_notes.py

Extracts full parva notes from Complete_text_mahabharat.txt and embeds them
into the volume_N_combined.txt files.

Structure in Complete_text (two variants):
  A) Section <Ordinal> <Parva Name>          ← name in header
     This parva has N shlokas...             ← note starts here
     Chapter N: N shlokas                   ← listing
     ...
     <more note text>                        ← note continues
     Chapter NNNN(N)                         ← actual content (no colon)

  B) Section <Ordinal>                       ← name NOT in header
     PARVA NAME IN CAPS                      ← name on first line
     This section has N shlokas...           ← note starts here
     Chapter NNNN(N): N shlokas             ← listing
     ...
     Maha means great...                     ← note continues
     Chapter NNNN(N)                         ← actual content
"""

import re, os
from collections import OrderedDict

BASE    = os.path.dirname(os.path.abspath(__file__))
VOL_DIR = os.path.join(BASE, "output", "volumes")


# ── Step 1: Extract all parva notes from Complete_text ───────────────────────

def extract_all_notes(txt_path):
    with open(txt_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Split on "\nSection <ordinal> [optional parva name]\n"
    SECT_SPLIT = re.compile(r'\nSection\s+([\w][\w\-\s]*?)\s*\n(?=\s*\n|\s*[A-Z])')
    parts = SECT_SPLIT.split(content)
    # parts = [prefix, header1, block1, header2, block2, ...]

    notes = {}   # _norm(parva_name) -> note_text

    for i in range(1, len(parts), 2):
        section_hdr = parts[i].strip()   # e.g. "One Anukramanika Parva" or "Ninety-Four"
        block       = parts[i+1] if i+1 < len(parts) else ''

        # ── Extract parva name ──────────────────────────────────────────────
        # Try from header first: "One Anukramanika Parva" → "Anukramanika Parva"
        m = re.search(r'([A-Z][a-z\-]+(?:\s+[A-Za-z\-]+)*\s+Parva)', section_hdr)
        if m:
            parva_name = m.group(1).strip()
        else:
            # Take from first all-caps line in block: "MAHA-PRASTHANIKA PARVA"
            parva_name = ''
            for line in block.split('\n')[:5]:
                s = line.strip()
                if not s:
                    continue
                if re.match(r'^[A-Z][A-Z\s\-]+PARVA\s*$', s):
                    # Convert "MAHA-PRASTHANIKA PARVA" → "Maha-Prasthanika Parva"
                    parva_name = s.title().replace(' Parva', ' Parva')
                    break
                # Spaced: "M A H A - P R A S T H A N I K A  PA RVA" → skip, try next
                if re.match(r'^([A-Z]\s){2,}', s):
                    continue
                # Regular Parva Name
                if re.search(r'Parva', s, re.IGNORECASE) and len(s) < 60 and not re.match(r'^(This |Chapter |\d)', s):
                    parva_name = s.strip()
                    break

        if not parva_name:
            continue

        # ── Extract note text ───────────────────────────────────────────────
        # Collect all lines in block that are not:
        # - the parva name (caps or regular)
        # - chapter listing: "Chapter N: N shlokas"
        # - spaced-out title
        # Stop when we hit actual chapter content: "Chapter NNNN(N)" with no colon,
        # or a bare "NNNN(N)" line, or a quoted line starting the story.

        note_lines = []
        for line in block.split('\n'):
            s = line.strip()
            if not s:
                if note_lines:
                    note_lines.append('')
                continue

            # Stop at actual chapter content
            if re.match(r'^Chapter\s+\d+\(\d+\)\s*$', s):
                break
            if re.match(r'^\d+\(\d+\)\s*$', s):
                break
            # Stop at quoted speech (chapter text begins)
            if s[:1] in ('\u2018', "'", '"', '\u201c'):
                break
            # Stop at bare standalone number (chapter number)
            if re.match(r'^\d+\s*$', s):
                break

            # Skip chapter listing lines (Chapter N: N shlokas)
            if re.match(r'^Chapter\s+\d+.*:\s*\d+\s*shlokas', s, re.IGNORECASE):
                continue
            # Skip spaced-out OCR titles
            if re.match(r'^([A-Z]\s){3,}', s):
                continue
            # Skip the parva name line itself (if it appears in block)
            if re.search(r'Parva', s, re.IGNORECASE) and len(s) < 60 and not re.match(r'^(This |In the)', s, re.IGNORECASE):
                # Likely the parva name header — skip
                if _norm(s) == _norm(parva_name):
                    continue

            note_lines.append(s)

        # Clean up blank lines at edges
        while note_lines and not note_lines[0]:
            note_lines.pop(0)
        while note_lines and not note_lines[-1]:
            note_lines.pop()

        # Remove pure chapter listing lines ("Chapter N: N shlokas")
        # Keep "This parva has..." lines that contain actual description (not just counts)
        clean_lines = []
        for l in note_lines:
            if re.match(r'^Chapter\s+\d+.*:\s*\d+\s*shlokas', l, re.IGNORECASE):
                continue
            # "This parva/section has N shlokas and N chapters." — pure stat → strip
            # "This parva/section has N shlokas and N chapters. <description>" → keep description part
            m_stat = re.match(
                r'^(This\s+(?:parva|section)\s+has[\w\s,\-\.]+?chapters?\.?)\s*(.*)',
                l, re.IGNORECASE | re.DOTALL
            )
            if m_stat:
                remainder = m_stat.group(2).strip()
                if remainder:
                    clean_lines.append(remainder)
                # else: pure stat line, skip
            else:
                clean_lines.append(l)
        note_lines = clean_lines

        note = ' '.join(l for l in note_lines if l)
        # Strip any remaining chapter listing fragments that were on mixed lines
        note = re.sub(r'Chapter\s+\d+\(\d+\):\s*\d+\s*shlokas\s*', '', note)
        note = re.sub(r'\bTt\b', 'It', note)
        note = re.sub(r'\bTn\b', 'In', note)
        note = re.sub(r'(\w)-\s+(\w)', r'\1\2', note)
        note = re.sub(r' {2,}', ' ', note).strip()

        if note and len(note) > 20:
            key = _norm(parva_name)
            if key not in notes:   # first occurrence wins (avoid duplicates)
                notes[key] = note

    return notes


def _norm(name: str) -> str:
    return re.sub(r'[^a-z0-9]', ' ', name.lower()).strip()


def _compact(name: str) -> str:
    """Normalize to no-space, no-hyphen lowercase for loose matching."""
    return re.sub(r'[^a-z0-9]', '', name.lower())


def match_note(sub_hdr: str, notes: dict) -> str:
    """Find the best note for a sub-parva header like '________ Name [N] ____'"""
    m = re.search(r'________\s+(.+?)\s+\[', sub_hdr)
    if not m:
        return ""
    raw_name = m.group(1).strip()
    key = _norm(raw_name)
    if key in notes:
        return notes[key]
    # Compact match: strip all non-alphanumeric and compare (handles Maha-Prasthanika vs Mahaprasthanika)
    compact_key = _compact(raw_name)
    for nk, nv in notes.items():
        if _compact(nk) == compact_key:
            return nv
    # Fuzzy match on significant words
    key_words = set(w for w in key.split() if len(w) > 2)
    best_key, best_score = None, 0
    for nk in notes:
        shared = len(key_words & set(w for w in nk.split() if len(w) > 2))
        if shared > best_score and shared >= max(1, len(key_words) - 1):
            best_score = shared
            best_key   = nk
    return notes[best_key] if best_key else ""



MAIN_HDR_RE = re.compile(r'^(=======.+?=======)\s*$')
SUB_HDR_RE  = re.compile(r'^(________\s+(.+?)\s+\[(\d+)\].+?________)\s*$')
CH_HDR_RE   = re.compile(r'^--- Chapter (\d+)')
STRIP_HDR   = re.compile(r'(?m)^(?:={5,}.+={5,}|_{4,}.+_{4,})\s*\n?')

FN_SECT_RE  = re.compile(r'^________\s+(.+?)\s+\[(\d+)\]')
FN_RANGE_RE = re.compile(r'^--- Chapters (\d+)(?:\(\d+\))? to (\d+)(?:\(\d+\))?')
TOC_CH_RE   = re.compile(r'^--- Chapter (\d+)(?:\(\d+\))?\s*\[')


def get_fn_section_ranges(vol):
    from collections import OrderedDict
    path = os.path.join(VOL_DIR, f"volume_{vol}_footnotes.txt")
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    result = OrderedDict()
    cur = None
    for line in lines:
        s = line.strip()
        m = FN_SECT_RE.match(s)
        if m:
            if cur and cur["ch_start"] is not None:
                result[cur["gnum"]] = cur
            cur = {"name": m.group(1).strip(), "gnum": int(m.group(2)),
                   "ch_start": None, "ch_end": None}
            continue
        if cur:
            mr = FN_RANGE_RE.match(s)
            if mr:
                a, b = int(mr.group(1)), int(mr.group(2))
                if cur["ch_start"] is None:
                    cur["ch_start"] = a
                cur["ch_end"] = b
    if cur and cur["ch_start"] is not None:
        result[cur["gnum"]] = cur
    return result


def get_toc_sections(vol):
    """Return list of {gnum, sub_hdr, main_hdr, toc_ch_start}."""
    path = os.path.join(VOL_DIR, f"volume_{vol}_toc.txt")
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    sections = []
    pending_main  = None
    cur_sub_main  = None
    seen_main     = set()
    cur_sub       = None
    toc_chs       = []
    in_toc        = False

    def flush():
        if cur_sub is None:
            return
        m = re.search(r'\[(\d+)\]', cur_sub)
        gnum = int(m.group(1)) if m else -1
        emit_main = cur_sub_main if (cur_sub_main and cur_sub_main not in seen_main) else None
        if emit_main:
            seen_main.add(emit_main)
        sections.append({
            "gnum": gnum,
            "sub_hdr": cur_sub,
            "main_hdr": emit_main,
            "toc_chapters": list(toc_chs),
        })

    for line in lines:
        s = line.strip()
        if MAIN_HDR_RE.match(s):
            flush()
            pending_main = s; cur_sub = None; cur_sub_main = None; toc_chs = []; in_toc = False
            continue
        ms = SUB_HDR_RE.match(s)
        if ms:
            flush()
            cur_sub_main = pending_main; pending_main = None
            cur_sub = s; toc_chs = []; in_toc = True
            continue
        mc = TOC_CH_RE.match(s)
        if mc:
            toc_chs.append(int(mc.group(1))); in_toc = False

    flush()
    return sections


def build_combined_vol(vol, notes):
    fn_secs   = get_fn_section_ranges(vol)
    toc_secs  = get_toc_sections(vol)

    ch_to_info = {}
    for sec in toc_secs:
        gnum    = sec["gnum"]
        fn_info = fn_secs.get(gnum)
        if fn_info and fn_info["ch_start"] is not None:
            ch_start = fn_info["ch_start"]
        elif sec["toc_chapters"]:
            ch_start = sec["toc_chapters"][0]
        else:
            continue

        note = match_note(sec["sub_hdr"], notes)
        ch_to_info[ch_start] = (sec["main_hdr"], sec["sub_hdr"], note)

    ch_path = os.path.join(VOL_DIR, f"volume_{vol}_chapters.txt")
    with open(ch_path, encoding="utf-8") as f:
        ch_content = f.read()

    segments = re.split(r"(?=--- Chapter \d+)", ch_content)

    out_parts = []
    for seg in segments:
        seg_clean = STRIP_HDR.sub('', seg)
        m = CH_HDR_RE.match(seg_clean.strip())
        if not m:
            if seg_clean.strip():
                out_parts.append(seg_clean)
            continue
        ch_num = int(m.group(1))
        if ch_num in ch_to_info:
            main_hdr, sub_hdr, note = ch_to_info[ch_num]
            if main_hdr:
                out_parts.append(f"\n\n{main_hdr}\n")
            out_parts.append(f"\n{sub_hdr}\n")
            if note:
                out_parts.append(f"\n{note}\n")
            out_parts.append("\n")
        out_parts.append(seg_clean)

    out_path = os.path.join(VOL_DIR, f"volume_{vol}_combined.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(out_parts))
    return out_path, len(ch_to_info)


def main():
    txt = os.path.join(BASE, "input", "Complete_text_mahabharat.txt")
    print("Extracting parva notes from Complete_text...")
    notes = extract_all_notes(txt)
    print(f"  {len(notes)} notes extracted")

    for vol in range(1, 11):
        try:
            path, n = build_combined_vol(vol, notes)
            print(f"Vol {vol:>2}: {n} sections → {os.path.basename(path)}")
        except Exception as e:
            import traceback
            print(f"Vol {vol:>2}: ERROR - {e}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
