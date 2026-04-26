#!/usr/bin/env python3
"""
organize_to_actual_story.py
---------------------------
Organize ALL source files into a clean actual_story/ folder structure.
DOES NOT delete originals — only copies.

Structure:
  actual_story/
    inputs/
      text_based/
        story/          <- volume_N_chapters.txt (the main story text)
        toc/            <- volume_N_toc.txt
        footnote/       <- volume_N_footnotes.txt
        combined/       <- volume_N_combined.txt (merged chapters+headers+footnotes)
      scripts/          <- scripts that PRODUCED the text files from raw input

    converted_json_files_from_text/
      actual_json/      <- flat parva JSONs + footnote JSONs + index + characters etc.
      parva_classification/   <- parva folder structure (main parva + subparva JSONs)
      chapter_classification/ <- chapter-level JSONs (inside subparva folders)
      tagged/           <- *_tagged.json files (speaker-annotated)
      dialogs/          <- volume-based dialog JSONs (from build_dialog_tree.py)
      scripts/          <- scripts that PRODUCED the JSON files

    reports/            <- verification/comparison reports
    web/                <- HTML viewers (copy of output/web/)
"""

import shutil
import os
from pathlib import Path

ROOT = Path(__file__).parent
DEST = ROOT / "actual_story"

# ── Source directories ──
VOL_DIR   = ROOT / "output" / "volumes"
JSON_DIR  = ROOT / "output" / "json"
STORY_DIR = JSON_DIR / "story"
FN_DIR    = JSON_DIR / "footnotes"
BORI_DIR  = JSON_DIR / "bori_text"
DIALOG_DIR = ROOT / "output" / "dialogs"
WEB_DIR   = ROOT / "output" / "web"
REPORT_DIR = ROOT / "output" / "reports"
FN_REPORT_DIR = ROOT / "output" / "footnotes_reports"

def ensure(path):
    path.mkdir(parents=True, exist_ok=True)
    return path

def copy_file(src, dst_dir, label=""):
    dst = dst_dir / src.name
    if src.exists():
        shutil.copy2(src, dst)
        return True
    else:
        print(f"  SKIP (not found): {src}")
        return False

def copy_tree(src_dir, dst_dir, label=""):
    """Copy entire directory tree."""
    if src_dir.exists():
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)
        n = sum(1 for _ in dst_dir.rglob('*') if _.is_file())
        print(f"  {label}: {n} files -> {dst_dir.relative_to(DEST)}")
    else:
        print(f"  SKIP (not found): {src_dir}")

def main():
    print("=" * 70)
    print("Organizing files into actual_story/")
    print("=" * 70)

    # ═══════════════════════════════════════════════════════════════════
    # 1. INPUTS / TEXT_BASED
    # ═══════════════════════════════════════════════════════════════════
    print("\n── 1. Text-based inputs ──")

    story_dir = ensure(DEST / "inputs" / "text_based" / "story")
    toc_dir   = ensure(DEST / "inputs" / "text_based" / "toc")
    fn_dir    = ensure(DEST / "inputs" / "text_based" / "footnote")
    comb_dir  = ensure(DEST / "inputs" / "text_based" / "combined")

    for vol in range(1, 11):
        copy_file(VOL_DIR / f"volume_{vol}_chapters.txt", story_dir)
        copy_file(VOL_DIR / f"volume_{vol}_toc.txt", toc_dir)
        copy_file(VOL_DIR / f"volume_{vol}_footnotes.txt", fn_dir)
        copy_file(VOL_DIR / f"volume_{vol}_combined.txt", comb_dir)

    n_story = len(list(story_dir.glob("*.txt")))
    n_toc   = len(list(toc_dir.glob("*.txt")))
    n_fn    = len(list(fn_dir.glob("*.txt")))
    n_comb  = len(list(comb_dir.glob("*.txt")))
    print(f"  story: {n_story}, toc: {n_toc}, footnote: {n_fn}, combined: {n_comb}")

    # Scripts that produced text files
    input_scripts_dir = ensure(DEST / "inputs" / "scripts")
    input_script_files = [
        "text_to_volumes/run.py",
        "text_to_volumes/txt_parser.py",
        "text_to_volumes/config.py",
        "text_to_volumes/text_fixes.py",
        "text_to_volumes/__init__.py",
        "build_combined_chapters.py",
        "build_headers.py",
        "run_extraction.py",
        "remove_empty_lines.py",
        "fix_chapter_fn_refs.py",
        "fix_missing_footnotes_input.py",
        "fix_poushya_range.py",
        "fill_missing_footnotes.py",
        "fix_emphasis_quotes.py",
        "reformat_toc_footnotes.py",
        "extract_parva_notes.py",
    ]
    copied = 0
    for sf in input_script_files:
        src = ROOT / sf
        if src.exists():
            # Preserve subdirectory for text_to_volumes
            if "/" in sf:
                sub = ensure(input_scripts_dir / Path(sf).parent)
                shutil.copy2(src, sub / Path(sf).name)
            else:
                shutil.copy2(src, input_scripts_dir / src.name)
            copied += 1
    print(f"  input scripts: {copied} files")

    # ═══════════════════════════════════════════════════════════════════
    # 2. CONVERTED JSON FILES FROM TEXT
    # ═══════════════════════════════════════════════════════════════════
    print("\n── 2. Converted JSON files ──")

    # 2a. actual_json — flat parva JSONs, footnote JSONs, index, characters, etc.
    actual_json_dir = ensure(DEST / "converted_json_files_from_text" / "actual_json")

    # Top-level JSON files
    top_jsons = [
        "index.json", "characters.json", "locations.json",
        "timeline.json", "introduction.json", "mahabharata_sections.json",
        "bori_official.json", "translation_data.json",
    ]
    for jf in top_jsons:
        src = JSON_DIR / jf
        if src.exists():
            shutil.copy2(src, actual_json_dir / jf)

    # Flat parva JSONs (legacy, the originals)
    for f in sorted(STORY_DIR.glob("parva_*.json")):
        if f.is_file():
            shutil.copy2(f, actual_json_dir / f.name)

    # Footnote JSONs
    fn_json_dir = ensure(actual_json_dir / "footnotes")
    if FN_DIR.exists():
        for f in sorted(FN_DIR.glob("*.json")):
            shutil.copy2(f, fn_json_dir / f.name)

    # BORI text JSONs
    bori_json_dir = ensure(actual_json_dir / "bori_text")
    if BORI_DIR.exists():
        for f in sorted(BORI_DIR.glob("*.json")):
            shutil.copy2(f, bori_json_dir / f.name)

    n_actual = sum(1 for _ in actual_json_dir.rglob("*.json"))
    print(f"  actual_json: {n_actual} JSON files")

    # 2b. parva_classification — parva folder main JSONs + subparva JSONs
    parva_dir = ensure(DEST / "converted_json_files_from_text" / "parva_classification")
    for pf in sorted(STORY_DIR.glob("parva_*")):
        if pf.is_dir():
            dst_parva = ensure(parva_dir / pf.name)
            # Copy parva main JSON from inside folder
            main_json = pf / f"{pf.name}.json"
            if main_json.exists():
                shutil.copy2(main_json, dst_parva / main_json.name)
            # Copy subparva JSONs (NOT tagged, NOT folders)
            for sp in sorted(pf.glob("subparva_*.json")):
                if "_tagged" not in sp.name:
                    shutil.copy2(sp, dst_parva / sp.name)

    n_parva = sum(1 for _ in parva_dir.rglob("*.json"))
    print(f"  parva_classification: {n_parva} JSON files")

    # 2c. chapter_classification — chapter-level JSONs from subparva folders
    ch_dir = ensure(DEST / "converted_json_files_from_text" / "chapter_classification")
    for pf in sorted(STORY_DIR.glob("parva_*")):
        if pf.is_dir():
            for sp_folder in sorted(pf.glob("subparva_*")):
                if sp_folder.is_dir():
                    dst_sp = ensure(ch_dir / pf.name / sp_folder.name)
                    # Copy subparva main JSON inside folder
                    for f in sorted(sp_folder.glob("*.json")):
                        if "_tagged" not in f.name:
                            shutil.copy2(f, dst_sp / f.name)

    n_ch = sum(1 for _ in ch_dir.rglob("*.json"))
    print(f"  chapter_classification: {n_ch} JSON files")

    # 2d. tagged — all *_tagged.json files (speaker-annotated)
    tagged_dir = ensure(DEST / "converted_json_files_from_text" / "tagged")
    for pf in sorted(STORY_DIR.glob("parva_*")):
        if pf.is_dir():
            dst_tagged_parva = ensure(tagged_dir / pf.name)
            # Subparva-level tagged
            for f in sorted(pf.glob("*_tagged.json")):
                shutil.copy2(f, dst_tagged_parva / f.name)
            # Chapter-level tagged (inside subparva folders)
            for sp_folder in sorted(pf.glob("subparva_*")):
                if sp_folder.is_dir():
                    dst_sp = ensure(dst_tagged_parva / sp_folder.name)
                    for f in sorted(sp_folder.glob("*_tagged.json")):
                        shutil.copy2(f, dst_sp / f.name)

    n_tagged = sum(1 for _ in tagged_dir.rglob("*.json"))
    print(f"  tagged: {n_tagged} JSON files")

    # 2e. dialogs — volume-based dialog JSONs (from build_dialog_tree.py)
    if DIALOG_DIR.exists():
        copy_tree(DIALOG_DIR, DEST / "converted_json_files_from_text" / "dialogs", "dialogs")

    # JSON conversion scripts
    json_scripts_dir = ensure(DEST / "converted_json_files_from_text" / "scripts")
    json_script_files = [
        "txt_to_json.py",
        "split_parva_to_folders.py",
        "split_subparvas_to_chapters.py",
        "tag_speakers_and_colors.py",
        "build_dialog_tree.py",
        "build_story_page.py",
        "generate_viewer.py",
        "build_bori_and_translation.py",
        "rewrite_parser.py",
        "add_nesting_markers.py",
        "itrans_to_json.py",
        "segregate_435_to_100.py",
    ]
    copied = 0
    for sf in json_script_files:
        src = ROOT / sf
        if src.exists():
            shutil.copy2(src, json_scripts_dir / src.name)
            copied += 1
    print(f"  json scripts: {copied} files")

    # ═══════════════════════════════════════════════════════════════════
    # 3. REPORTS
    # ═══════════════════════════════════════════════════════════════════
    print("\n── 3. Reports ──")

    reports_dst = ensure(DEST / "reports")
    # output/reports/
    if REPORT_DIR.exists():
        for f in REPORT_DIR.glob("*"):
            if f.is_file():
                shutil.copy2(f, reports_dst / f.name)
    # output/footnotes_reports/
    if FN_REPORT_DIR.exists():
        fn_rep_dst = ensure(reports_dst / "footnotes_reports")
        for f in FN_REPORT_DIR.glob("*"):
            if f.is_file():
                shutil.copy2(f, fn_rep_dst / f.name)
    # Root-level reports
    for rpt in ROOT.glob("*.txt"):
        if "report" in rpt.name.lower() or "compare" in rpt.name.lower() or "status" in rpt.name.lower():
            shutil.copy2(rpt, reports_dst / rpt.name)
    # CSV reports
    for rpt in (ROOT / "output").glob("*.csv"):
        shutil.copy2(rpt, reports_dst / rpt.name)

    # Verification scripts
    verify_dir = ensure(reports_dst / "scripts")
    verify_scripts = [
        "verify_footnotes.py", "verify_json_vs_txt.py", "verify_fixes.py",
        "verify_tagged.py", "compare_chapters.py", "compare_bori_vs_translation.py",
        "compare_skt_eng.py", "compare_v5.py",
    ]
    for sf in verify_scripts:
        src = ROOT / sf
        if src.exists():
            shutil.copy2(src, verify_dir / src.name)

    n_reports = sum(1 for _ in reports_dst.rglob("*") if _.is_file())
    print(f"  reports: {n_reports} files")

    # ═══════════════════════════════════════════════════════════════════
    # 4. WEB VIEWERS
    # ═══════════════════════════════════════════════════════════════════
    print("\n── 4. Web viewers ──")
    if WEB_DIR.exists():
        copy_tree(WEB_DIR, DEST / "web", "web")

    # ═══════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════
    total = sum(1 for _ in DEST.rglob("*") if _.is_file())
    print("\n" + "=" * 70)
    print(f"DONE — {total} total files organized into actual_story/")
    print("=" * 70)
    print()
    print("Structure:")
    print("  actual_story/")
    print("    inputs/")
    print("      text_based/")
    print(f"        story/     <- {n_story} volume chapter files")
    print(f"        toc/       <- {n_toc} volume TOC files")
    print(f"        footnote/  <- {n_fn} volume footnote files")
    print(f"        combined/  <- {n_comb} merged files")
    print(f"      scripts/     <- {copied} extraction scripts")
    print("    converted_json_files_from_text/")
    print(f"      actual_json/            <- {n_actual} flat JSONs")
    print(f"      parva_classification/   <- {n_parva} parva-level JSONs")
    print(f"      chapter_classification/ <- {n_ch} chapter-level JSONs")
    print(f"      tagged/                 <- {n_tagged} tagged JSONs")
    print(f"      dialogs/                <- dialog JSONs")
    print(f"      scripts/                <- conversion scripts")
    print(f"    reports/                   <- {n_reports} report files")
    print(f"    web/                       <- HTML viewers")

if __name__ == "__main__":
    main()
