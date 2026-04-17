"""
Mahabharata PDF Extraction Pipeline
====================================
Complete pipeline for "The Mahabharata Set of 10 Volumes" PDF.
This script is specific to this PDF and its structure.

Steps:
  1. Extract PDF -> toc, chapters, footnotes per volume  (output/volumes/)
  1b. Apply hardcoded OCR fixes
  2. Add section headers to footnotes
  3. Verify footnote ref/def matching (16,734 footnotes)
  4. Build knowledge graph: characters, locations, timeline (output/json/)

Usage:
  cd mahabharata-rawdata
  python pipeline/run.py

Folder structure:
  input/                - Source PDF
  pipeline/             - This script and all modules
  pipeline/data/        - Hardcoded character, location, timeline data
  pipeline/extract/     - PDF parsing, section headers, verification
  pipeline/fixes/       - OCR error fixes
  pipeline/auto/        - Regex-based auto-extraction from text
  pipeline/model/       - Character data model (add/ensure)
  pipeline/merge/       - Duplicate resolution and cleanup
  pipeline/output/      - JSON builders, cross-linking, validation
  output/volumes/       - Extracted text (10 volumes x 3 files)
  output/json/          - characters.json, locations.json, timeline.json
  output/web/           - map.html (interactive map)
  docs/                 - Handover docs, schema spec
"""

import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Resolve project root from script location: pipeline/ -> project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Add project root to path so imports work
sys.path.insert(0, PROJECT_ROOT)

from pipeline.config import PDF_FILENAME
from pipeline.extract.pdf_parser import step1_extract
from pipeline.fixes.ocr_fixes import step1b_manual_fixes
from pipeline.extract.section_headers import step2_add_sections
from pipeline.extract.verify import step3_verify
from pipeline.model.character_model import CharacterDB
from pipeline.data.characters import register_characters
from pipeline.data.locations import get_locations, compute_distances
from pipeline.data.timeline import get_timeline
from pipeline.auto.name_extractor import extract_names_and_relationships, extract_duty_caste
from pipeline.merge.resolver import merge_and_resolve
from pipeline.output.builder import build_character_output, build_location_output, build_timeline_output
from pipeline.output.crosslink import crosslink
from pipeline.output.validator import validate


def main():
    # Fixed paths — this script is specific to this PDF
    pdf_path = os.path.join(PROJECT_ROOT, 'input', PDF_FILENAME)
    volumes_dir = os.path.join(PROJECT_ROOT, 'output', 'volumes')
    json_dir = os.path.join(PROJECT_ROOT, 'output', 'json')

    if not os.path.isfile(pdf_path):
        print(f"Error: PDF not found at: {pdf_path}")
        print(f"Place '{PDF_FILENAME}' in the input/ folder.")
        sys.exit(1)

    os.makedirs(volumes_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)

    print(f"Project root : {PROJECT_ROOT}")
    print(f"PDF input    : {pdf_path}")
    print(f"Volumes dir  : {volumes_dir}")
    print(f"JSON dir     : {json_dir}")

    # ── Step 1: Extract PDF ─────────────────────────────────────
    step1_extract(pdf_path, volumes_dir)

    # ── Step 1b: Fix known OCR errors ───────────────────────────
    step1b_manual_fixes(volumes_dir)

    # ── Step 2: Add section headers ─────────────────────────────
    step2_add_sections(volumes_dir)

    # ── Step 3: Verify footnote matching ────────────────────────
    ok = step3_verify(volumes_dir)

    # ── Step 4: Build knowledge graph ───────────────────────────
    print("\n" + "=" * 60)
    print("STEP 4: Building character knowledge graph")
    print("=" * 60)

    # Phase 1: Load hardcoded characters
    db = CharacterDB()
    register_characters(db.add, db.chars, db._key)
    db.rebuild_alias_map()

    # Phase 2: Auto-extract names and relationships from text
    all_ch_text = extract_names_and_relationships(db, volumes_dir)

    # Phase 3: Merge duplicates and resolve conflicts
    merge_and_resolve(db)

    # Phase 3b: Auto-extract duty/caste from text patterns
    extract_duty_caste(db, all_ch_text)

    # Phase 4: Build characters.json
    output, out_path = build_character_output(db, json_dir)

    # Phase 5: Build locations.json
    locations = get_locations()
    compute_distances(locations)
    loc_output, loc_path = build_location_output(locations, json_dir)

    # Phase 6: Build timeline.json
    timeline = get_timeline()
    tl_output, tl_path = build_timeline_output(timeline, json_dir)

    # Phase 7: Cross-link all three files
    crosslink(output, out_path, loc_output, loc_path, tl_output)

    # Phase 8: Validate all cross-references
    validate(output, loc_output, tl_output)

    print(f"\n  SUMMARY:")
    print(f"    characters.json: {len(output)} characters")
    print(f"    locations.json:  {len(loc_output)} locations")
    print(f"    timeline.json:   {len(tl_output)} events")

    # ── Done ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if ok:
        print("ALL DONE - 100% footnote matching across all volumes")
    else:
        print("DONE - some footnote mismatches detected (check above)")
    print(f"Output: {json_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()
