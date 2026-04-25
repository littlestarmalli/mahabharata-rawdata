"""
build_combined_chapters.py

Produces output/volumes/volume_N_combined.txt for each volume.
Merges chapter text with parva and sub-parva headers + notes from the TOC files,
using the footnotes files as the authoritative source for chapter ranges.

Output format:
    ======= Main Parva [N] ... =======

    ________ Sub-Parva [N] ... ________
    Note text...

    --- Chapter N(N) [shlokas] ---
    Chapter text...

    ________ Next Sub-Parva ...
    ...
"""

import re
import os
from collections import OrderedDict

BASE    = os.path.dirname(os.path.abspath(__file__))
VOL_DIR = os.path.join(BASE, "output", "volumes")

MAIN_HDR_RE = re.compile(r'^(=======.+?=======)\s*$')
SUB_HDR_RE  = re.compile(r'^(________\s+(.+?)\s+\[(\d+)\].+?________)\s*$')
TOC_CH_RE   = re.compile(r'^--- Chapter (\d+)(?:\(\d+\))?\s*\[')
FN_SECT_RE  = re.compile(r'^________\s+(.+?)\s+\[(\d+)\]')
FN_RANGE_RE = re.compile(r'^--- Chapters (\d+)(?:\(\d+\))? to (\d+)(?:\(\d+\))?')
CH_HDR_RE   = re.compile(r'^--- Chapter (\d+)')


def get_fn_section_ranges(vol):
    """Parse footnotes file. Returns OrderedDict: global_num -> {name, ch_start, ch_end}."""
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


def get_toc_info(vol):
    """
    Parse the TOC file.
    Returns a list of dicts (in TOC order):
      {main_parva_hdr, subparva_hdr, note, toc_chapters}
    main_parva_hdr is set only for the FIRST sub-parva under each main parva.
    """
    path = os.path.join(VOL_DIR, f"volume_{vol}_toc.txt")
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    sections     = []
    pending_main = None   # main parva header seen, to attach to the NEXT sub-parva
    cur_sub_main = None   # main parva header belonging to cur_sub
    seen_main    = set()  # main parva headers already emitted
    cur_sub      = None
    note_lines   = []
    toc_chs      = []
    in_note      = False

    def _flush_sub():
        """Append current sub-parva to sections list."""
        if cur_sub is None:
            return
        emit_main = cur_sub_main if (cur_sub_main and cur_sub_main not in seen_main) else None
        if emit_main:
            seen_main.add(emit_main)
        sections.append({
            "main_parva_hdr": emit_main,
            "subparva_hdr":   cur_sub,
            "note":           " ".join(note_lines).strip(),
            "toc_chapters":   list(toc_chs),
        })

    for line in lines:
        s = line.strip()

        # Main parva header  ======= ... =======
        if MAIN_HDR_RE.match(s):
            _flush_sub()
            pending_main = s
            cur_sub      = None
            cur_sub_main = None
            note_lines   = []
            toc_chs      = []
            in_note      = False
            continue

        # Sub-parva header  ________ ... ________
        ms = SUB_HDR_RE.match(s)
        if ms:
            _flush_sub()
            # Attach pending main parva to this (new) sub-parva
            cur_sub_main = pending_main
            pending_main = None
            cur_sub      = s
            note_lines   = []
            toc_chs      = []
            in_note      = True
            continue

        # Chapter line  --- Chapter N(N) [shlokas] ---
        mc = TOC_CH_RE.match(s)
        if mc:
            toc_chs.append(int(mc.group(1)))
            in_note = False
            continue

        # Note text (anything between sub-parva header and first chapter)
        if cur_sub and in_note and s and not s.startswith("---"):
            note_lines.append(s)

    _flush_sub()
    return sections


def build_combined(vol):
    fn_secs    = get_fn_section_ranges(vol)  # gnum -> {name, ch_start, ch_end}
    toc_secs   = get_toc_info(vol)           # ordered list of section dicts

    # Build ch_start -> (main_parva_hdr, subparva_hdr, note)
    ch_to_info = {}

    for sec in toc_secs:
        sub_hdr = sec["subparva_hdr"]
        m = re.search(r'\[(\d+)\]', sub_hdr)
        if not m:
            continue
        gnum = int(m.group(1))

        # Authoritative ch_start: footnotes file first, then TOC chapter list
        fn_info  = fn_secs.get(gnum)
        if fn_info and fn_info["ch_start"] is not None:
            ch_start = fn_info["ch_start"]
        elif sec["toc_chapters"]:
            ch_start = sec["toc_chapters"][0]
        else:
            continue  # can't determine first chapter

        ch_to_info[ch_start] = (
            sec["main_parva_hdr"],
            sub_hdr,
            sec["note"],
        )

    # Read chapters file and split into chapter segments
    ch_path = os.path.join(VOL_DIR, f"volume_{vol}_chapters.txt")
    with open(ch_path, encoding="utf-8") as f:
        ch_content = f.read()

    segments = re.split(r"(?=--- Chapter \d+)", ch_content)

    # Strip all embedded parva/sub-parva header lines from chapter segments.
    # These will be regenerated with proper notes by the combined builder.
    STRIP_HDR = re.compile(
        r'(?m)^(?:={5,}.+={5,}|_{4,}.+_{4,})\s*\n?'
    )

    out_parts = []
    for seg in segments:
        # Clean embedded headers from this segment
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
    total_secs = 0
    for vol in range(1, 11):
        try:
            path, n_secs = build_combined(vol)
            print(f"Vol {vol:>2}: {n_secs} sections inserted → {os.path.basename(path)}")
            total_secs += n_secs
        except Exception as e:
            import traceback
            print(f"Vol {vol:>2}: ERROR - {e}")
            traceback.print_exc()
    print(f"\nTotal sections inserted across all volumes: {total_secs}")


if __name__ == "__main__":
    main()
