#!/usr/bin/env python3
"""
organize_scripts.py — Move all root-level .py scripts into categorized folders.
Creates a scripts/ folder with subfolders by purpose.
Uses shutil.move (not copy) to clean up root.
"""
import shutil
import os
from pathlib import Path

ROOT = Path(__file__).parent
SCRIPTS = ROOT / "scripts"

# ── Categories ──────────────────────────────────────────────────────

categories = {
    # Text extraction & input preparation
    "text_extraction": [
        "build_combined_chapters.py",
        "build_headers.py",
        "run_extraction.py",
        "remove_empty_lines.py",
        "extract_parva_notes.py",
        "reformat_toc_footnotes.py",
    ],

    # Text fixes (fixing content in volume TXT files)
    "text_fixes": [
        "fix_chapter_fn_refs.py",
        "fix_missing_footnotes_input.py",
        "fix_poushya_range.py",
        "fill_missing_footnotes.py",
        "fix_emphasis_quotes.py",
        "fix_apostrophes.py",
    ],

    # JSON conversion (TXT → JSON pipeline)
    "json_conversion": [
        "txt_to_json.py",
        "split_parva_to_folders.py",
        "split_subparvas_to_chapters.py",
        "itrans_to_json.py",
        "segregate_435_to_100.py",
        "build_bori_and_translation.py",
    ],

    # Dialog & speaker annotation
    "dialog_annotation": [
        "build_dialog_tree.py",
        "tag_speakers_and_colors.py",
        "rewrite_parser.py",
        "add_nesting_markers.py",
        "add_character_colors.py",
    ],

    # Viewer & HTML generation
    "viewer_generation": [
        "build_story_page.py",
        "build_dialog_viewer.py",
        "generate_viewer.py",
    ],

    # Verification & comparison
    "verification": [
        "verify_footnotes.py",
        "verify_json_vs_txt.py",
        "verify_fixes.py",
        "verify_tagged.py",
        "compare_chapters.py",
        "compare_bori_vs_translation.py",
        "compare_skt_eng.py",
        "compare_v5.py",
        "watch_compare.py",
    ],

    # Debug & temporary scripts (prefixed with _ or debug_)
    "debug_temp": [
        "_analyze_deep.py",
        "_analyze_source.py",
        "_analyze_speakers.py",
        "_analyze_speakers2.py",
        "_check_1865.py",
        "_check_1865b.py",
        "_check_ch59.py",
        "_check_deep_chapters.py",
        "_check_depth.py",
        "_check_disk.py",
        "_check_fields.py",
        "_check_last2.py",
        "_check_missed_attr.py",
        "_check_missed_summary.py",
        "_check_missed_top.py",
        "_check_ranges.py",
        "_check_speaker_colors.py",
        "_check_speakers.py",
        "_debug_bad_ids.py",
        "_debug_trailing.py",
        "_find_and.py",
        "_find_term_quotes.py",
        "_find_term_quotes2.py",
        "_fix_term_quotes.py",
        "_inspect_ch.py",
        "_new_sections_5_6.py",
        "_show_tree.py",
        "_test_seg.py",
        "_test_server.py",
        "_tmp_list95.py",
        "_verify_fix.py",
        "check_html.py",
        "check_para.py",
        "check_poushya.py",
        "debug_combined.py",
        "debug_fix_check.py",
        "debug_poushya_refs.py",
        "debug_quotes.py",
        "debug_sp_check.py",
        "debug_v3.py",
        "debug_v3b.py",
        "show_parvagraha.py",
        "print_itrans_table.py",
    ],

    # Organization utility
    "utils": [
        "organize_to_actual_story.py",
        # organize_scripts.py itself will stay at root until done
    ],
}

def main():
    moved = 0
    skipped = []

    for category, files in categories.items():
        dest = SCRIPTS / category
        dest.mkdir(parents=True, exist_ok=True)

        for fname in files:
            src = ROOT / fname
            if src.exists():
                shutil.move(str(src), str(dest / fname))
                moved += 1
            else:
                skipped.append(fname)

    # Check for any remaining .py files at root (besides this script)
    remaining = [f.name for f in ROOT.glob("*.py") if f.name != "organize_scripts.py"]

    print(f"Moved {moved} scripts into scripts/")
    if skipped:
        print(f"Skipped (not found): {len(skipped)}")
        for s in skipped:
            print(f"  - {s}")
    if remaining:
        print(f"\nRemaining at root ({len(remaining)}):")
        for r in remaining:
            print(f"  - {r}")
    else:
        print("\nRoot is clean — no .py files remaining.")

    # Print summary
    print("\nscripts/ structure:")
    for category in sorted(categories.keys()):
        d = SCRIPTS / category
        n = len(list(d.glob("*.py"))) if d.exists() else 0
        print(f"  {category}/  ({n} scripts)")

if __name__ == "__main__":
    main()
