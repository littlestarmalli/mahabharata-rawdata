# Text to Volumes Pipeline

This folder contains scripts for extracting structured data from `input/Complete_text_mahabharat.txt` (plain text file) into organized volume files.

## Purpose

Unlike the `pipeline/` folder which extracts from PDF files, this pipeline works with pre-extracted TXT files. It handles:

- **Volume splitting**: Separates the single TXT file into 10 volumes
- **Chapter detection**: Identifies chapter boundaries and section headers
- **TOC removal**: Filters out table of contents and front matter
- **Footer cleanup**: Removes page numbers and artifacts
- **Paragraph formation**: Merges broken paragraphs and forms proper text blocks
- **Text normalization**: Cleans up unicode artifacts, normalizes quotes

## Structure

```
text_to_volumes/
├── __init__.py         # Package marker
├── config.py           # Configuration constants (volume markers, patterns)
├── txt_parser.py       # Main TXT extraction logic
├── text_fixes.py       # Text cleanup and normalization
├── run.py              # Main pipeline orchestrator
└── README.md           # This file
```

## Key Differences from PDF Pipeline

| Feature | PDF Pipeline | TXT Pipeline |
|---------|--------------|--------------|
| Input | PDF with OCR | Pre-extracted TXT |
| OCR Fixes | Extensive OCR error correction | Minimal (already extracted) |
| Page Detection | PDF page boundaries | Volume markers in text |
| Indentation | Uses x0 coordinates | Text-based patterns |
| Footnotes | Extracts from PDF blocks | Detects inline references |

## Usage

### Run the complete pipeline:

```bash
python text_to_volumes/run.py
```

### Run individual steps:

```python
# Extract volumes
from text_to_volumes.txt_parser import step1_extract_volumes
step1_extract_volumes()

# Clean up text
from text_to_volumes.text_fixes import run_all_fixes
run_all_fixes()
```

## Output

Creates files in `output/volumes/`:
- `volume_N_chapters.txt` - Extracted chapter text with markers
- `volume_N_footnotes.txt` - Footnote references (to be enhanced)
- `volume_N_toc.txt` - Table of contents for each volume

## Configuration

Edit `config.py` to adjust:
- Volume marker patterns
- TOC/footer detection patterns
- Section header regex
- Footnote reference patterns

## Patterns Adapted for TXT

### Volume Detection
```
"Volume 1", "Volume 2", etc. (instead of PDF page ranges)
```

### Section Headers
```
"Section One Anukramanika Parva"
"Section Nine Hidimba-vadha Parva"
```

### Chapter Markers
```
Standalone numbers: "131", "132", "133"
(becomes: "--- Chapter 131 ---")
```

### Footnote References
```
{40}, {41}, {42} (inline in text)
```

## Future Enhancements

- [ ] Enhance footnote extraction from inline text
- [ ] Add section header enrichment (map chapters to sections)
- [ ] Improve dialog detection and formatting
- [ ] Add character name extraction
- [ ] Integrate with existing JSON generation pipeline

## Related

- Main PDF pipeline: `pipeline/`
- Configuration: `pipeline/config.py`
- Original extraction docs: `docs/PROJECT_HANDOVER.md`
