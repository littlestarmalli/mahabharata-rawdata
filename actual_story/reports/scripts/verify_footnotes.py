"""
verify_footnotes.py

Cross-check footnote {N} references in chapter files against footnote
definitions (lines starting with "N text") in footnotes files.

IMPORTANT: Footnote numbering restarts from 1 for each sub-parva section.
The analysis is therefore done SECTION BY SECTION using the section structure
in the footnotes file.

For each section in each volume, reports:
  CASE A: local {N} in chapter  →  N NOT defined in that section's footnotes
  CASE B: N defined in section  →  {N} NOT found in any chapter of that section
  CASE C: sequence gaps in section's footnotes definitions
  CASE D: sequence gaps in section's chapter references

Then:
  - Inserts 'N [MISSING FOOTNOTE]' placeholder in footnotes for CASE A items
  - Marks orphan footnotes with '  # ORPHAN: not referenced in chapters' for CASE B
  - Writes per-volume reports to output/footnotes_reports/
"""

import re
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

BASE = os.path.dirname(os.path.abspath(__file__))
VOL_DIR = os.path.join(BASE, "output", "volumes")
REPORT_DIR = os.path.join(BASE, "output", "footnotes_reports")
os.makedirs(REPORT_DIR, exist_ok=True)

# ── regex patterns ────────────────────────────────────────────────────────────
REF_RE      = re.compile(r'\{(\d+)\}')
SECTION_HDR = re.compile(r'^________\s+(.+?)\s+\[(\d+)\]')       # ________ Name [N] ____...
CHAPTER_HDR = re.compile(r'^--- Chapter (\d+)(?:\(\d+\))?')       # --- Chapter N ...
RANGE_RE    = re.compile(r'^--- Chapters (\d+)(?:\(\d+\))? to (\d+)(?:\(\d+\))?')  # chapter range


@dataclass
class Section:
    name: str
    global_num: int           # e.g. [60] from ________ Name [60] ____
    ch_start: int             # global chapter start
    ch_end: int               # global chapter end
    fn_line_start: int        # first footnote line index in footnotes file
    fn_line_end: int          # exclusive end line index
    fn_defs: dict = field(default_factory=dict)   # local_N -> line_index


# ── parse footnotes file into sections ────────────────────────────────────────

def parse_footnotes_file(vol: int) -> tuple[list[Section], list[str]]:
    """Parse the footnotes file and return (sections, raw_lines)."""
    path = os.path.join(VOL_DIR, f"volume_{vol}_footnotes.txt")
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    sections: list[Section] = []
    current: Optional[Section] = None
    pending_range: Optional[tuple[int,int]] = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # New section header  ________ Name [N] ____
        m = SECTION_HDR.match(stripped)
        if m:
            if current is not None:
                current.fn_line_end = i
                _fill_defs(current, lines)
                sections.append(current)
            name = m.group(1).strip()
            gnum = int(m.group(2))
            current = Section(name=name, global_num=gnum,
                              ch_start=0, ch_end=0,
                              fn_line_start=i+1, fn_line_end=len(lines))
            pending_range = None
            continue

        # Chapter range line  --- Chapters A to B ---
        if current is not None:
            mr = RANGE_RE.match(stripped)
            if mr:
                a, b = int(mr.group(1)), int(mr.group(2))
                if current.ch_start == 0:
                    current.ch_start = a
                current.ch_end = b      # keep updating to last range in section
                current.fn_line_start = i + 1   # footnotes start after range line
                continue

    # Finalize last section
    if current is not None:
        current.fn_line_end = len(lines)
        _fill_defs(current, lines)
        sections.append(current)

    return sections, lines


def _fill_defs(sec: Section, lines: list[str]):
    """Fill sec.fn_defs with {local_N: line_index} for lines in sec's range."""
    for i in range(sec.fn_line_start, sec.fn_line_end):
        m = re.match(r'^(\d+)\s+\S', lines[i])
        if m:
            n = int(m.group(1))
            if n not in sec.fn_defs:
                sec.fn_defs[n] = i


# ── load chapter refs per chapter ─────────────────────────────────────────────

def load_chapter_refs_by_chapter(vol: int) -> dict[int, set[int]]:
    """Return dict: global_ch_num -> set of local {N} refs in that chapter."""
    path = os.path.join(VOL_DIR, f"volume_{vol}_chapters.txt")
    ch_refs: dict[int, set[int]] = {}
    cur_ch = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = CHAPTER_HDR.match(line.strip())
            if m:
                cur_ch = int(m.group(1))
                if cur_ch not in ch_refs:
                    ch_refs[cur_ch] = set()
            if cur_ch is not None:
                for r in REF_RE.findall(line):
                    ch_refs[cur_ch].add(int(r))
    return ch_refs


# ── section-level analysis ────────────────────────────────────────────────────

def analyze_section(sec: Section, ch_refs: dict[int, set[int]]) -> dict:
    """Compare a section's footnote defs with its chapters' refs."""
    # Collect all local refs from chapters in this section's range
    section_refs: dict[int, list[int]] = {}  # local_N -> [chs that use it]
    for ch in range(sec.ch_start, sec.ch_end + 1):
        for n in ch_refs.get(ch, set()):
            section_refs.setdefault(n, []).append(ch)

    ref_set = set(section_refs.keys())
    def_set = set(sec.fn_defs.keys())

    missing_defs = sorted(ref_set - def_set)   # CASE A
    orphan_defs  = sorted(def_set - ref_set)   # CASE B

    def_sorted = sorted(def_set)
    def_gaps = []
    for a, b in zip(def_sorted, def_sorted[1:]):
        if b - a > 1:
            def_gaps.extend(range(a + 1, b))

    ref_sorted = sorted(ref_set)
    ref_gaps = []
    for a, b in zip(ref_sorted, ref_sorted[1:]):
        if b - a > 1:
            ref_gaps.extend(range(a + 1, b))

    return {
        "section": sec,
        "ref_count": len(ref_set),
        "def_count": len(def_set),
        "section_refs": section_refs,
        "missing_defs": missing_defs,
        "orphan_defs": orphan_defs,
        "def_gaps": def_gaps,
        "ref_gaps": ref_gaps,
    }


# ── apply fixes to footnotes file ────────────────────────────────────────────

def apply_fixes(vol: int, section_results: list[dict]) -> tuple[int, int]:
    """
    Insert [MISSING FOOTNOTE] placeholders and mark orphans.
    Returns (inserted_count, marked_count).
    """
    path = os.path.join(VOL_DIR, f"volume_{vol}_footnotes.txt")
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    # Collect all insertions: {line_idx: [new_lines_to_insert]}
    insertions: dict[int, list[str]] = {}
    orphan_lines: set[int] = set()  # line indices to mark

    for res in section_results:
        sec = res["section"]
        def_map = sec.fn_defs
        def_sorted = sorted(def_map.keys())

        # CASE A: insert placeholders for missing defs
        for n in res["missing_defs"]:
            chs = res["section_refs"].get(n, [])
            chs_str = ", ".join(f"ch{c}" for c in sorted(chs))
            placeholder = f"{n} [MISSING FOOTNOTE — referenced in: {chs_str}]\n"
            # Insert before the next higher def, or at section end
            next_def = next((d for d in def_sorted if d > n), None)
            if next_def is not None:
                insert_at = def_map[next_def]
            else:
                insert_at = sec.fn_line_end
            insertions.setdefault(insert_at, []).append(placeholder)

        # CASE B: mark orphans
        for n in res["orphan_defs"]:
            if n in def_map:
                orphan_lines.add(def_map[n])

    # Apply insertions (reverse order to preserve indices)
    result = list(lines)
    offset = 0  # track cumulative insertion offset

    inserted = 0
    sorted_inserts = sorted(insertions.keys())
    for idx in sorted_inserts:
        to_insert = sorted(insertions[idx], key=lambda l: int(l.split()[0]))
        actual_idx = idx + offset
        for line in reversed(to_insert):
            result.insert(actual_idx, line)
            inserted += 1
        offset += len(to_insert)

    # Mark orphan lines (indices may have shifted)
    # Rebuild orphan line set relative to shifted indices
    marked = 0
    orphan_idx_shifted = set()
    offset = 0
    sorted_inserts_idxs = sorted(insertions.keys())
    ins_ptr = 0
    for orig_idx in sorted(orphan_lines):
        while ins_ptr < len(sorted_inserts_idxs) and sorted_inserts_idxs[ins_ptr] <= orig_idx:
            offset += len(insertions[sorted_inserts_idxs[ins_ptr]])
            ins_ptr += 1
        orphan_idx_shifted.add(orig_idx + offset)

    for i in sorted(orphan_idx_shifted):
        if i < len(result):
            line = result[i].rstrip('\n')
            if '# ORPHAN' not in line and '[MISSING' not in line:
                result[i] = line + '  # ORPHAN: not referenced in chapters\n'
                marked += 1

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(result)

    return inserted, marked


# ── report writer ─────────────────────────────────────────────────────────────

def write_report(vol: int, section_results: list[dict], total_ins: int, total_mark: int):
    path = os.path.join(REPORT_DIR, f"footnotes_report_vol{vol}.txt")

    total_a = sum(len(r["missing_defs"]) for r in section_results)
    total_b = sum(len(r["orphan_defs"]) for r in section_results)
    total_c = sum(len(r["def_gaps"]) for r in section_results)
    total_d = sum(len(r["ref_gaps"]) for r in section_results)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Volume {vol} Footnote Cross-Check Report (section-aware)\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"  Total CASE A (missing defs → placeholders inserted): {total_a}\n")
        f.write(f"  Total CASE B (orphan defs  → marked with comment):   {total_b}\n")
        f.write(f"  Total CASE C (def gaps):                              {total_c}\n")
        f.write(f"  Total CASE D (ref gaps):                              {total_d}\n\n")

        for res in section_results:
            sec = res["section"]
            if not (res["missing_defs"] or res["orphan_defs"] or
                    res["def_gaps"] or res["ref_gaps"]):
                continue  # skip clean sections in report

            f.write(f"\n{'─'*70}\n")
            f.write(f"Section [{sec.global_num}] {sec.name}  "
                    f"(chapters {sec.ch_start}–{sec.ch_end})\n")
            f.write(f"  Refs: {res['ref_count']}   Defs: {res['def_count']}\n")

            if res["missing_defs"]:
                f.write(f"\n  CASE A — {len(res['missing_defs'])} missing def(s):\n")
                for n in res["missing_defs"]:
                    chs = res["section_refs"].get(n, [])
                    f.write(f"    {{{n}}}  in ch: {chs}\n")

            if res["orphan_defs"]:
                f.write(f"\n  CASE B — {len(res['orphan_defs'])} orphan(s):\n")
                for n in res["orphan_defs"]:
                    f.write(f"    fn {n}\n")

            if res["def_gaps"]:
                f.write(f"\n  CASE C — def sequence gaps: {res['def_gaps']}\n")

            if res["ref_gaps"]:
                f.write(f"\n  CASE D — ref sequence gaps: {res['ref_gaps']}\n")

    return path


# ── main ──────────────────────────────────────────────────────────────────────

def analyze_volume(vol: int) -> tuple[list[dict], int, int]:
    sections, lines = parse_footnotes_file(vol)
    ch_refs = load_chapter_refs_by_chapter(vol)

    results = [analyze_section(sec, ch_refs) for sec in sections]
    inserted, marked = apply_fixes(vol, results)
    return results, inserted, marked


def main():
    vols = list(range(1, 11))
    if len(sys.argv) > 1:
        vols = [int(a) for a in sys.argv[1:]]

    grand_a = grand_b = grand_c = grand_d = 0

    print(f"{'Vol':>3}  {'Secs':>4}  {'CaseA':>6}  {'CaseB':>6}  {'CaseC':>6}  {'CaseD':>6}  {'Ins':>5}  {'Mark':>5}")
    print("-" * 60)

    for vol in vols:
        results, inserted, marked = analyze_volume(vol)

        total_a = sum(len(r["missing_defs"]) for r in results)
        total_b = sum(len(r["orphan_defs"])  for r in results)
        total_c = sum(len(r["def_gaps"])     for r in results)
        total_d = sum(len(r["ref_gaps"])     for r in results)

        write_report(vol, results, inserted, marked)

        grand_a += total_a
        grand_b += total_b
        grand_c += total_c
        grand_d += total_d

        print(f"{vol:>3}  {len(results):>4}  {total_a:>6}  {total_b:>6}  "
              f"{total_c:>6}  {total_d:>6}  {inserted:>5}  {marked:>5}")

    print("-" * 60)
    print(f"TOT       {grand_a:>6}  {grand_b:>6}  {grand_c:>6}  {grand_d:>6}")
    print(f"\nReports written to: {REPORT_DIR}")


if __name__ == "__main__":
    main()
