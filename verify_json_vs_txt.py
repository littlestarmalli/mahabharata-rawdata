#!/usr/bin/env python3
"""
verify_json_vs_txt.py  –  Full integrity check: TXT source vs Story JSON

Checks (in order):
  1. Every chapter number present in txt exists in JSON and vice versa
  2. num_shlokas header value matches JSON details.num_shlokas per chapter
  3. Paragraph count and content match byte-for-byte per chapter
  4. Sub-parva details.num_chapters matches actual chapter count in JSON
  5. Parva details.num_chapters / num_shlokas / num_subparvas match JSON
  6. Global chapter numbering is contiguous (flags known gaps vs new gaps)

Outputs a report to stdout and writes verify_report.txt.
"""

import re
import json
import os
from pathlib import Path
from collections import OrderedDict

ROOT       = Path(__file__).parent
VOL_DIR    = ROOT / "output" / "volumes"
STORY_DIR  = ROOT / "output" / "json" / "story"
REPORT_OUT = ROOT / "verify_report.txt"

KNOWN_MISSING = set()   # no known OCR gaps after parser fix (was {309,451,541,1091,1149})

MAIN_RE = re.compile(
    r'^={5,}\s+(.+?)\s+\[(\d+)\]\s+={2,}\s+\[(\d+)\]\s+={2,}\s+\[(\d+)\]\s+={2,}\s+\[(\d+)\]\s+={5,}\s*$'
)
SUB_RE = re.compile(
    r'^_{4,}\s+(.+?)\s+\[(\d+)\]\s+_{2,}\s+\[(\d+)\]\s+_{2,}\s+\[(\d+)\]\s+_{4,}\s*$'
)
CH_RE = re.compile(
    r'^---\s+Chapter\s+(\d+)(?:\((\d+)\))?\s*(?:\[(\d+|\?)\])?\s*---\s*$'
)


def split_paragraphs(text: str) -> list:
    return [l.strip() for l in text.splitlines() if l.strip()]


# ─────────────────────────────────────────────
# 1.  Parse ALL txt source files into a flat dict
#     txt_data[global_ch] = {shlokas, paragraphs: list[str], subparva, parva_num}
# ─────────────────────────────────────────────
def parse_txt_source():
    txt_data = {}          # global_ch → {shlokas, paras, subparva_num, parva_num}
    parva_headers   = {}   # parva_num → {name, n_sub, n_ch, n_sh}
    subparva_headers= {}   # subparva_num → {name, n_ch, n_sh, parva_num}

    cur_parva    = None
    cur_subparva = None
    cur_ch_global= None
    cur_ch_local = None
    cur_ch_shlokas = None
    ch_buf       = []

    def flush():
        nonlocal cur_ch_global, cur_ch_local, cur_ch_shlokas, ch_buf
        if cur_ch_global is None:
            return
        paras = split_paragraphs("".join(ch_buf))
        txt_data[cur_ch_global] = {
            "shlokas":      cur_ch_shlokas,
            "paragraphs":   paras,
            "subparva_num": cur_subparva,
            "parva_num":    cur_parva,
        }
        cur_ch_global = None
        ch_buf = []

    for vol in range(1, 11):
        cpath = VOL_DIR / f"volume_{vol}_chapters.txt"
        if not cpath.exists():
            continue
        for line in open(cpath, encoding="utf-8"):
            s = line.rstrip("\n")

            m = MAIN_RE.match(s)
            if m:
                flush()
                pnum = int(m.group(2))
                parva_headers[pnum] = {
                    "name":  m.group(1), "n_sub": int(m.group(3)),
                    "n_ch":  int(m.group(4)), "n_sh": int(m.group(5))
                }
                cur_parva    = pnum
                cur_subparva = None
                continue

            m = SUB_RE.match(s)
            if m:
                flush()
                snum = int(m.group(2))
                subparva_headers[snum] = {
                    "name": m.group(1), "n_ch": int(m.group(3)),
                    "n_sh": int(m.group(4)), "parva_num": cur_parva
                }
                cur_subparva = snum
                continue

            m = CH_RE.match(s)
            if m:
                flush()
                cur_ch_global  = int(m.group(1))
                cur_ch_local   = int(m.group(2)) if m.group(2) else cur_ch_global
                cur_ch_shlokas = int(m.group(3)) if (m.group(3) and m.group(3) != '?') else None
                continue

            if cur_ch_global is not None:
                ch_buf.append(line)

    flush()
    return txt_data, parva_headers, subparva_headers


# ─────────────────────────────────────────────
# 2.  Load ALL story JSON files
# ─────────────────────────────────────────────
def load_json():
    json_data = {}   # global_ch → {shlokas, paragraphs: list[str], subparva_num, parva_num}
    parva_details = {}    # parva_num → details dict from JSON
    subparva_details = {} # subparva_num → details dict from JSON

    for fname in sorted(os.listdir(STORY_DIR)):
        if not fname.endswith(".json"):
            continue
        d = json.load(open(STORY_DIR / fname, encoding="utf-8"))
        pnum = d["parva_number"]
        parva_details[pnum] = d["details"]
        for spnum_str, sp in d["subparvas"].items():
            spnum = int(spnum_str)
            subparva_details[spnum] = sp["details"]
            for ch_str, ch in sp["chapters"].items():
                gnum = ch["global_number"]
                paras = [ch["paragraphs"][str(i+1)] for i in range(len(ch["paragraphs"]))]
                json_data[gnum] = {
                    "shlokas":      ch["num_shlokas"],
                    "paragraphs":   paras,
                    "subparva_num": spnum,
                    "parva_num":    pnum,
                }
    return json_data, parva_details, subparva_details


# ─────────────────────────────────────────────
# 3.  Run all checks
# ─────────────────────────────────────────────
def verify():
    lines = []
    def log(msg=""):
        print(msg)
        lines.append(msg)

    log("=" * 80)
    log("MAHABHARATA — TXT SOURCE vs STORY JSON VERIFICATION")
    log("=" * 80)

    log("\n[1/4] Parsing TXT source files ...")
    txt_data, parva_hdr, subparva_hdr = parse_txt_source()
    log(f"      TXT: {len(txt_data)} chapters, {len(parva_hdr)} parvas, {len(subparva_hdr)} sub-parvas")

    log("[2/4] Loading story JSON files ...")
    json_data, parva_det, subparva_det = load_json()
    log(f"      JSON: {len(json_data)} chapters, {len(parva_det)} parvas, {len(subparva_det)} sub-parvas")

    errors   = []
    warnings = []

    # ── Check 1: chapter presence ──────────────────────────────────────────
    log("\n[3/4] Cross-checking chapters ...")
    txt_set  = set(txt_data.keys())
    json_set = set(json_data.keys())

    in_txt_not_json = txt_set - json_set
    in_json_not_txt = json_set - txt_set

    if in_txt_not_json:
        errors.append(f"CHAPTERS IN TXT but NOT IN JSON ({len(in_txt_not_json)}): {sorted(in_txt_not_json)}")
    if in_json_not_txt:
        errors.append(f"CHAPTERS IN JSON but NOT IN TXT ({len(in_json_not_txt)}): {sorted(in_json_not_txt)}")

    # ── Check 2: global gap analysis ───────────────────────────────────────
    all_nums = txt_set | json_set
    if all_nums:
        full_range = set(range(1, max(all_nums) + 1))
        gaps = sorted(full_range - all_nums)
        new_gaps = [g for g in gaps if g not in KNOWN_MISSING]
        if new_gaps:
            errors.append(f"NEW (unexpected) GAPS in chapter numbering: {new_gaps}")
        else:
            log(f"      Chapter gaps: {sorted(gaps)} (all accounted for as known OCR gaps) OK")

    # ── Check 3: per-chapter deep comparison ───────────────────────────────
    log("[4/4] Per-chapter paragraph & shloka check ...")
    ch_para_diff   = []   # (ch, txt_count, json_count)
    ch_content_diff= []   # (ch, para_index, first_diff)
    ch_shloka_diff = []   # (ch, txt_val, json_val)

    common = sorted(txt_set & json_set)
    for ch in common:
        t = txt_data[ch]
        j = json_data[ch]

        # shloka header value
        if t["shlokas"] is not None and j["shlokas"] is not None:
            if t["shlokas"] != j["shlokas"]:
                ch_shloka_diff.append((ch, t["shlokas"], j["shlokas"]))

        # paragraph count
        t_paras = t["paragraphs"]
        j_paras = j["paragraphs"]
        if len(t_paras) != len(j_paras):
            ch_para_diff.append((ch, len(t_paras), len(j_paras)))
        else:
            # content match
            for idx, (tp, jp) in enumerate(zip(t_paras, j_paras)):
                if tp != jp:
                    # show first 80 chars of diff
                    ch_content_diff.append((ch, idx + 1, tp[:80], jp[:80]))
                    break  # one diff per chapter is enough

    # ── Check 4: sub-parva details.num_chapters ────────────────────────────
    sp_count_errors = []
    for snum, hdr in subparva_hdr.items():
        det = subparva_det.get(snum)
        if det is None:
            sp_count_errors.append(f"Sub-parva {snum} ({hdr['name']}): in TXT but not in JSON")
            continue
        # count actual chapters in json for this sub-parva
        actual = sum(1 for c in json_data.values() if c["subparva_num"] == snum)
        if det["num_chapters"] != actual:
            sp_count_errors.append(
                f"Sub-parva {snum} ({hdr['name']}): JSON details.num_chapters={det['num_chapters']} but actual={actual}"
            )

    # ── Check 5: parva details ─────────────────────────────────────────────
    parva_errors = []
    for pnum, hdr in parva_hdr.items():
        det = parva_det.get(pnum)
        if det is None:
            parva_errors.append(f"Parva {pnum} ({hdr['name']}): in TXT but not in JSON")
            continue
        actual_ch = sum(1 for c in json_data.values() if c["parva_num"] == pnum)
        if det["num_chapters"] != actual_ch:
            parva_errors.append(
                f"Parva {pnum} ({hdr['name']}): JSON details.num_chapters={det['num_chapters']} actual={actual_ch}"
            )
        if det["num_subparvas"] != hdr["n_sub"]:
            parva_errors.append(
                f"Parva {pnum} ({hdr['name']}): JSON details.num_subparvas={det['num_subparvas']} TXT header says {hdr['n_sub']}"
            )
        # shlokas from header (txt) vs parva sum from txt
        txt_shloka_sum = sum(
            (t["shlokas"] or 0) for t in txt_data.values() if t["parva_num"] == pnum
        )
        if hdr["n_sh"] != det["num_shlokas"]:
            parva_errors.append(
                f"Parva {pnum} ({hdr['name']}): TXT header shlokas={hdr['n_sh']} JSON details.num_shlokas={det['num_shlokas']}"
            )

    # ─────────────────────────────────────────────
    # Report
    # ─────────────────────────────────────────────
    log("\n" + "=" * 80)
    log("RESULTS")
    log("=" * 80)

    total_issues = 0

    if errors:
        log("\n--- ERRORS (critical) ---")
        for e in errors:
            log(f"  ERROR: {e}")
        total_issues += len(errors)

    if ch_shloka_diff:
        log(f"\n--- CHAPTER SHLOKA HEADER MISMATCHES ({len(ch_shloka_diff)}) ---")
        for ch, t, j in ch_shloka_diff:
            log(f"  ch {ch}: TXT header={t}  JSON={j}")
        total_issues += len(ch_shloka_diff)

    if ch_para_diff:
        log(f"\n--- CHAPTER PARAGRAPH COUNT MISMATCHES ({len(ch_para_diff)}) ---")
        for ch, t, j in ch_para_diff[:50]:
            log(f"  ch {ch}: TXT={t} paragraphs  JSON={j} paragraphs")
        if len(ch_para_diff) > 50:
            log(f"  ... and {len(ch_para_diff)-50} more")
        total_issues += len(ch_para_diff)

    if ch_content_diff:
        log(f"\n--- CHAPTER CONTENT MISMATCHES ({len(ch_content_diff)}) ---")
        for ch, pidx, tp, jp in ch_content_diff[:30]:
            log(f"  ch {ch} para {pidx}:")
            log(f"    TXT : {tp!r}")
            log(f"    JSON: {jp!r}")
        if len(ch_content_diff) > 30:
            log(f"  ... and {len(ch_content_diff)-30} more")
        total_issues += len(ch_content_diff)

    if sp_count_errors:
        log(f"\n--- SUB-PARVA DETAILS.NUM_CHAPTERS ISSUES ({len(sp_count_errors)}) ---")
        for e in sp_count_errors:
            log(f"  {e}")
        total_issues += len(sp_count_errors)

    if parva_errors:
        log(f"\n--- PARVA DETAILS ISSUES ({len(parva_errors)}) ---")
        for e in parva_errors:
            log(f"  {e}")
        total_issues += len(parva_errors)

    log("\n" + "=" * 80)
    if total_issues == 0:
        log("ALL CHECKS PASSED  ✓  TXT source and JSON are fully consistent.")
    else:
        log(f"TOTAL ISSUES: {total_issues}")
    log("=" * 80)

    # Summary table
    log("\n--- PER-PARVA SUMMARY ---")
    log(f"{'P':>2} {'Parva':<32} {'TXT_ch':>6} {'JSON_ch':>7} {'TXT_sh':>8} {'JSON_sh':>8} {'OK?':>5}")
    log("-" * 75)
    for pnum in sorted(parva_hdr.keys()):
        hdr = parva_hdr[pnum]
        det = parva_det.get(pnum, {})
        t_ch = sum(1 for c in txt_data.values() if c["parva_num"] == pnum)
        j_ch = det.get("num_chapters", "?")
        t_sh = hdr["n_sh"]
        j_sh = det.get("num_shlokas", "?")
        ok = "OK" if t_ch == j_ch and t_sh == j_sh else "DIFF"
        log(f"{pnum:>2} {hdr['name']:<32} {t_ch:>6} {j_ch:>7} {t_sh:>8,} {j_sh:>8,} {ok:>5}")
    log("-" * 75)
    t_total = len(txt_data)
    j_total = len(json_data)
    log(f"{'':>2} {'TOTAL':<32} {t_total:>6} {j_total:>7}")

    # Write report
    with open(REPORT_OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"\nReport written to: {REPORT_OUT}")

    return total_issues


if __name__ == "__main__":
    issues = verify()
    exit(0 if issues == 0 else 1)
