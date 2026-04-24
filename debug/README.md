# Debug Scripts

This folder contains debugging and analysis tools for the Mahabharata extraction pipeline.

## Available Scripts

### `debug_compare_accurate.py`
**Purpose**: Baseline paragraph count comparison between PDF and extracted text.

**What it does**:
- Counts paragraphs in PDF using line-level indentation detection
- Counts paragraphs in extracted volume_*_chapters.txt files
- Provides per-volume and overall accuracy metrics

**Usage**:
```bash
python debug_compare_accurate.py
```

**Output**:
```
Vol    PDF   Extr   Diff  Match%
----------------------------------------
  1    952    972    -20  102.1%
  2    677    684     -7  101.0%
...
TOT   7082   7467   -385  105.4%
```

---

### `debug_chapter_compare.py`
**Purpose**: Per-chapter granular comparison of PDF vs extracted paragraphs.

**What it does**:
- Detects chapters in PDF using same logic as extraction pipeline
- Compares paragraph counts for each individual chapter
- Generates CSV with per-chapter details
- Identifies specific problematic chapters

**Usage**:
```bash
python debug_chapter_compare.py
```

**Output**:
- Console: Volume-level summary
- File: `output/chapter_paragraph_comparison.csv`

**CSV Format**:
```
Volume,Chapter,PDF_Paragraphs,Extracted_Paragraphs,Difference,Match_Percent
1,1,116,82,-34,70.7
1,2,25,26,-1,104.0
...
```

---

### `debug_summarize_comparison.py`
**Purpose**: Human-readable summary of chapter comparison results.

**What it does**:
- Reads `output/chapter_paragraph_comparison.csv`
- Groups mismatches by volume
- Identifies worst over-splits and under-splits
- Generates focused fix list

**Usage**:
```bash
python debug_summarize_comparison.py
```

**Output**:
- Console: Per-volume statistics and worst mismatches
- File: `output/chapters_to_fix.txt` (chapters with |diff| >= 2)

**Example Output**:
```
Volume 1:
  Total PDF: 766, Extracted: 968, Match: 126.4%
  Chapters: 198 total, 3 perfect match, 186 over-split, 9 under-split
  Worst over-splits:
    Ch 1: PDF=116 Ext=82 (missing 34 paragraphs)
```

---

### `debug_extract_dialogs.py`
**Purpose**: Extract and analyze dialog patterns from the text.

**What it does**:
- Identifies dialog lines (quotes, "said", etc.)
- Extracts speaker-dialog pairs
- Useful for character interaction analysis
- Generates dialog-specific datasets

**Usage**:
```bash
python debug_extract_dialogs.py
```

**Output**: Depends on implementation (likely JSON with dialog patterns)

---

### `debug_gen_html.py`
**Purpose**: Generate HTML visualizations of extracted content.

**What it does**:
- Creates readable HTML versions of volume chapters
- Adds formatting and navigation
- Outputs to `debug/html/` folder

**Usage**:
```bash
python debug_gen_html.py
```

**Output**: HTML files in `debug/html/` directory

---

## Output Folders

### `html/`
Contains generated HTML visualizations:
- `index.html` - Main navigation page
- `volume_1.html` through `volume_10.html` - Per-volume content pages

---

## Workflow

### To verify extraction accuracy:
1. Run main extraction: `cd pipeline && python run.py`
2. Check overall accuracy: `python debug_compare_accurate.py`
3. Identify problem chapters: `python debug_chapter_compare.py`
4. Review summary: `python debug_summarize_comparison.py`

### To generate visualizations:
1. Extract dialogs: `python debug_extract_dialogs.py`
2. Generate HTML: `python debug_gen_html.py`
3. Open `html/index.html` in browser

---

## Notes

- All debug scripts are **read-only** - they analyze existing output without modifying it
- Scripts use relative paths from `mahabharata-rawdata/` root
- Debug outputs go to `output/` directory or `debug/html/`
- Main extraction logic is in `pipeline/` - debug scripts only validate and visualize

---

## Removed Scripts

The following scripts were removed as their logic is now integrated into `pipeline/run.py` or were one-time debugging:

- `analyze_pdf_structure.py` - One-time PDF structure analysis
- `build_characters.py` - Logic now in `pipeline/model/character_model.py`
- `check_pdf_blocks.py` - One-time block structure check
- `compare_pdf_paragraphs.py` - Duplicate of `debug_compare_accurate.py`
- `count_paragraphs.py` - Duplicate functionality
- Various `diagnose_*.py`, `check_*.py`, `find_*.py` - Completed specific debugging tasks
