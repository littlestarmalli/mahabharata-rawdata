#!/usr/bin/env python3
"""
txt_to_json.py  –  Convert Mahabharata combined text + footnote files to
structured JSON, organized by Main Parva (not volume).

Outputs
-------
  output/json/story/parva_{N:02d}_{slug}.json        – one per main parva
  output/json/footnotes/parva_{N:02d}_{slug}_fn.json – one per main parva
  output/json/index.json                             – master index
"""

import re
import json
import os
from pathlib import Path
from collections import OrderedDict

ROOT      = Path(__file__).parent
VOL_DIR   = ROOT / "output" / "volumes"
OUT_STORY = ROOT / "output" / "json" / "story"
OUT_FN    = ROOT / "output" / "json" / "footnotes"
OUT_IDX   = ROOT / "output" / "json" / "index.json"
COMPLETE_TEXT = ROOT / "input" / "Complete_text_mahabharat.txt"

# ── Header patterns ──────────────────────────────────────────────────────────
# ======= Name [num] ==== [subparvas] ==== [chapters] ==== [shlokas] =======
MAIN_RE = re.compile(
    r'^={5,}\s+(.+?)\s+\[(\d+)\]\s+={2,}\s+\[(\d+)\]\s+={2,}\s+\[(\d+)\]\s+={2,}\s+\[(\d+)\]\s+={5,}\s*$'
)
# ________ Name [num] ____ [chapters] ____ [shlokas] ________
SUB_RE = re.compile(
    r'^_{4,}\s+(.+?)\s+\[(\d+)\]\s+_{2,}\s+\[(\d+)\]\s+_{2,}\s+\[(\d+)\]\s+_{4,}\s*$'
)
# --- Chapter global(local) [shlokas] ---
CH_RE = re.compile(
    r'^---\s+Chapter\s+(\d+)(?:\((\d+)\))?\s*(?:\[(\d+)\])?\s*---\s*$'
)

# ── Footnote patterns ─────────────────────────────────────────────────────────
FN_MAIN_RE  = re.compile(
    r'^={5,}\s+(.+?)\s+\[(\d+)\].*={5,}\s*$'
)
FN_SUB_RE   = re.compile(
    r'^_{4,}\s+(.+?)\s+\[(\d+)\]\s+_{2,}'
)
FN_RANGE_RE = re.compile(
    r'^---\s+Chapters\s+(\d+)(?:\(\d+\))?\s+to\s+(\d+)(?:\(\d+\))?\s+---'
)
FN_LINE_RE  = re.compile(r'^(\d+)\s+(.*)')


def slugify(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


def split_paragraphs(text: str) -> list:
    """
    Split chapter text into paragraphs.
    Each non-empty line is a paragraph (speech turn or narrative block).
    Blank lines that separate sections are stripped.
    """
    lines = text.splitlines()
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            result.append(stripped)
    return result


def load_parva_notes() -> dict:
    """Load full parva notes from Complete_text using extract_parva_notes module."""
    try:
        import sys
        sys.path.insert(0, str(ROOT))
        from extract_parva_notes import extract_all_notes
        if COMPLETE_TEXT.exists():
            return extract_all_notes(str(COMPLETE_TEXT))
    except Exception as e:
        print(f"  WARNING: Could not load parva notes: {e}")
    return {}


def match_subparva_note(name: str, notes: dict) -> str:
    """Fuzzy match a sub-parva name against extracted notes."""
    try:
        from extract_parva_notes import match_note
        fake_hdr = f"________ {name} [0] ____ [0] ____ [0] ________"
        return match_note(fake_hdr, notes)
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
# STORY PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def parse_combined_files(parva_notes: dict):
    """
    Parse all volume_N_chapters.txt files (vol 1-10) sequentially.
    Uses chapters files (correct header structure) rather than combined files.
    Notes are injected from Complete_text via parva_notes dict.
    Builds a parva-keyed OrderedDict:
      parvas[parva_num] = {
        "name", "parva_number", "details": {num_subparvas, num_chapters, num_shlokas},
        "subparvas": {
          subparva_num: {
            "name", "subparva_number", "source_volume", "file_path",
            "details": {num_chapters, num_shlokas},
            "note",
            "chapters": {
              global_ch_num: {
                "global_number", "local_number", "num_shlokas",
                "paragraphs": {1: text, 2: text, ...}
              }
            }
          }
        }
      }
    """
    parvas       = OrderedDict()   # parva_num → parva dict
    # Lookup: subparva_num → parva_num (to handle sub-parvas before main header)
    sub_to_parva = {}

    cur_parva    = None   # int
    cur_subparva = None   # int
    cur_chapter  = None   # dict with global_number, local_number, num_shlokas
    ch_text_buf  = []     # lines of current chapter body

    def flush_chapter():
        nonlocal cur_chapter, ch_text_buf
        if cur_chapter is None or cur_parva is None or cur_subparva is None:
            return
        parva = parvas.get(cur_parva)
        if parva is None:
            return
        sp = parva["subparvas"].get(cur_subparva)
        if sp is None:
            return
        text = "".join(ch_text_buf)
        paras = split_paragraphs(text)
        gnum = cur_chapter["global_number"]
        sp["chapters"][gnum] = {
            "global_number": cur_chapter["global_number"],
            "local_number":  cur_chapter["local_number"],
            "num_shlokas":   cur_chapter["num_shlokas"],
            "paragraphs":    {str(i + 1): p for i, p in enumerate(paras)},
        }
        cur_chapter = None
        ch_text_buf = []

    def save_note():
        pass  # Notes are now injected at sub-parva creation time from Complete_text

    for vol in range(1, 11):
        cpath = VOL_DIR / f"volume_{vol}_chapters.txt"   # ← chapters file (correct headers)
        if not cpath.exists():
            print(f"  WARNING: {cpath} not found, skipping")
            continue
        vol_file = f"output/volumes/volume_{vol}_chapters.txt"

        with open(cpath, encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            s = line.rstrip("\n")

            # ── Main parva header
            m = MAIN_RE.match(s)
            if m:
                flush_chapter()
                save_note()
                name   = m.group(1)
                pnum   = int(m.group(2))
                n_sub  = int(m.group(3))
                n_ch   = int(m.group(4))
                n_sh   = int(m.group(5))
                if pnum not in parvas:
                    parvas[pnum] = {
                        "name":         name,
                        "parva_number": pnum,
                        "details": {
                            "num_subparvas": n_sub,
                            "num_chapters":  n_ch,
                            "num_shlokas":   n_sh,
                        },
                        "subparvas": OrderedDict(),
                    }
                cur_parva    = pnum
                cur_subparva = None
                continue

            # ── Sub-parva header
            m = SUB_RE.match(s)
            if m:
                flush_chapter()
                save_note()
                name  = m.group(1)
                snum  = int(m.group(2))
                n_ch  = int(m.group(3))
                n_sh  = int(m.group(4))

                # If this sub-parva was already registered (multi-volume parva),
                # resolve its parent parva from the lookup table
                if snum in sub_to_parva:
                    cur_parva = sub_to_parva[snum]
                elif cur_parva is None:
                    # Sub-parva before any main-parva header in this volume – skip
                    cur_subparva = None
                    in_note = False
                    continue

                pobj = parvas.get(cur_parva)
                if pobj is None:
                    cur_subparva = None
                    in_note = False
                    continue

                if snum not in pobj["subparvas"]:
                    note = match_subparva_note(name, parva_notes)
                    pobj["subparvas"][snum] = {
                        "name":             name,
                        "subparva_number":  snum,
                        "source_volume":    vol,
                        "file_path":        vol_file,
                        "details": {
                            "num_chapters": n_ch,
                            "num_shlokas":  n_sh,
                        },
                        "note":     note,
                        "chapters": OrderedDict(),
                    }
                    sub_to_parva[snum] = cur_parva

                cur_subparva = snum
                continue

            # ── Chapter header
            m = CH_RE.match(s)
            if m:
                flush_chapter()
                save_note()
                g_num   = int(m.group(1))
                l_num   = int(m.group(2)) if m.group(2) else g_num
                shlokas = int(m.group(3)) if m.group(3) else 0
                cur_chapter = {
                    "global_number": g_num,
                    "local_number":  l_num,
                    "num_shlokas":   shlokas,
                }
                continue

            # ── Body line
            if cur_chapter is not None:
                ch_text_buf.append(line)  # keep newlines for paragraph splitting

    # Flush last chapter
    flush_chapter()
    return parvas


# ═══════════════════════════════════════════════════════════════════════════════
# FOOTNOTE PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def parse_footnote_files():
    """
    Parse all volume_N_footnotes.txt files.
    Returns: { parva_num: { subparva_num: { "chapter_range", "footnotes": {N: text} } } }
    A sub-parva may have multiple chapter-range sections; they are stored as a list.
    """
    fn_data = {}   # parva_num → { subparva_num → { "sections": [{chapter_range, footnotes}] } }

    for vol in range(1, 11):
        fpath = VOL_DIR / f"volume_{vol}_footnotes.txt"
        if not fpath.exists():
            continue

        with open(fpath, encoding="utf-8") as f:
            lines = f.readlines()

        cur_parva    = None
        cur_subparva = None
        cur_section  = None   # {"chapter_range": str, "footnotes": OrderedDict}
        cur_fn_num   = None
        cur_fn_lines = []

        def _commit_fn():
            nonlocal cur_fn_num, cur_fn_lines
            if cur_fn_num is not None and cur_section is not None:
                cur_section["footnotes"][cur_fn_num] = " ".join(cur_fn_lines).strip()
            cur_fn_num   = None
            cur_fn_lines = []

        def _commit_section():
            nonlocal cur_section
            _commit_fn()
            if cur_section is not None and cur_parva is not None and cur_subparva is not None:
                fn_data.setdefault(cur_parva, {}) \
                       .setdefault(cur_subparva, {"sections": []}) \
                       ["sections"].append(cur_section)
            cur_section = None

        for line in lines:
            s = line.rstrip("\n")

            # Main parva header
            m = FN_MAIN_RE.match(s)
            if m:
                _commit_section()
                cur_parva    = int(m.group(2))
                cur_subparva = None
                continue

            # Sub-parva header
            m = FN_SUB_RE.match(s)
            if m:
                _commit_section()
                cur_subparva = int(m.group(2))
                continue

            # Chapter range
            m = FN_RANGE_RE.match(s)
            if m:
                _commit_section()
                cur_section = {
                    "chapter_range": f"{m.group(1)}-{m.group(2)}",
                    "footnotes":     OrderedDict(),
                }
                continue

            # Footnote definition line  "N text..."
            m = FN_LINE_RE.match(s)
            if m:
                _commit_fn()
                cur_fn_num   = int(m.group(1))
                cur_fn_lines = [m.group(2).strip()]
                continue

            # Continuation (non-empty line not matching any header)
            if cur_fn_num is not None and s.strip() and not s.startswith("---"):
                cur_fn_lines.append(s.strip())

        _commit_section()  # flush last section in file

    return fn_data


# ═══════════════════════════════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

def write_outputs(parvas, fn_data):
    OUT_STORY.mkdir(parents=True, exist_ok=True)
    OUT_FN.mkdir(parents=True, exist_ok=True)

    index = []

    for pnum in sorted(parvas.keys()):
        parva = parvas[pnum]
        slug  = slugify(parva["name"])
        story_fname = f"parva_{pnum:02d}_{slug}.json"
        fn_fname    = f"parva_{pnum:02d}_{slug}_fn.json"

        # ── Story JSON
        out_subparvas = {}
        for snum, sp in parva["subparvas"].items():
            out_chapters = {}
            for cnum, ch in sp["chapters"].items():
                out_chapters[str(cnum)] = {
                    "global_number": ch["global_number"],
                    "local_number":  ch["local_number"],
                    "num_shlokas":   ch["num_shlokas"],
                    "paragraphs":    ch["paragraphs"],
                }
            out_subparvas[str(snum)] = {
                "name":            sp["name"],
                "subparva_number": sp["subparva_number"],
                "source_volume":   sp["source_volume"],
                "file_path":       sp["file_path"],
                "details":         sp["details"],
                "note":            sp["note"],
                "chapters":        out_chapters,
            }

        story_obj = {
            "name":         parva["name"],
            "parva_number": pnum,
            "details":      parva["details"],
            "subparvas":    out_subparvas,
        }
        with open(OUT_STORY / story_fname, "w", encoding="utf-8") as f:
            json.dump(story_obj, f, ensure_ascii=False, indent=2)

        # ── Footnotes JSON
        fn_parva = fn_data.get(pnum, {})
        fn_subparvas = {}
        for snum, sp_fn in fn_parva.items():
            sp_name = parva["subparvas"].get(snum, {}).get("name", f"Subparva {snum}")
            # Flatten: if only one section, use chapter_range directly; else list
            sections = sp_fn.get("sections", [])
            if len(sections) == 1:
                fn_subparvas[str(snum)] = {
                    "name":            sp_name,
                    "subparva_number": snum,
                    "chapter_range":   sections[0]["chapter_range"],
                    "footnotes":       {str(k): v for k, v in sections[0]["footnotes"].items()},
                }
            else:
                fn_subparvas[str(snum)] = {
                    "name":            sp_name,
                    "subparva_number": snum,
                    "sections": [
                        {
                            "chapter_range": sec["chapter_range"],
                            "footnotes":     {str(k): v for k, v in sec["footnotes"].items()},
                        }
                        for sec in sections
                    ],
                }

        fn_obj = {
            "parva_name":   parva["name"],
            "parva_number": pnum,
            "subparvas":    fn_subparvas,
        }
        with open(OUT_FN / fn_fname, "w", encoding="utf-8") as f:
            json.dump(fn_obj, f, ensure_ascii=False, indent=2)

        total_chapters  = sum(len(sp["chapters"]) for sp in parva["subparvas"].values())
        total_subparvas = len(parva["subparvas"])
        total_fn        = sum(
            sum(len(sec["footnotes"]) for sec in sp_fn.get("sections", []))
            for sp_fn in fn_parva.values()
        )

        index.append({
            "parva_number":    pnum,
            "name":            parva["name"],
            "details":         parva["details"],
            "chapters_loaded": total_chapters,
            "story_file":      f"story/{story_fname}",
            "footnotes_file":  f"footnotes/{fn_fname}",
        })
        print(
            f"  Parva {pnum:2d}: {parva['name']:<42s} "
            f"{total_subparvas} sub-parvas, {total_chapters} chapters, {total_fn} footnotes"
        )

    with open(OUT_IDX, "w", encoding="utf-8") as f:
        json.dump({"total_parvas": len(parvas), "parvas": index}, f, ensure_ascii=False, indent=2)

    print(f"\n  {len(parvas)} story files  → {OUT_STORY}")
    print(f"  {len(parvas)} footnote files → {OUT_FN}")
    print(f"  Index           → {OUT_IDX}")


def main():
    print("Loading parva notes from Complete_text...")
    parva_notes = load_parva_notes()
    print(f"  {len(parva_notes)} notes loaded\n")

    print("Parsing chapters text files...")
    parvas = parse_combined_files(parva_notes)
    print(f"  {len(parvas)} main parvas found\n")

    print("Parsing footnote files...")
    fn_data = parse_footnote_files()

    print("\nWriting JSON output...")
    write_outputs(parvas, fn_data)
    print("\nDone.")


if __name__ == "__main__":
    main()
