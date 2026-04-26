# Mahabharata Project — Data Formats Reference

## 1. Source Text Files

### `input/The Mahabharata Set of 10 Volumes.txt`
Raw extracted text from the 57 MB, 3,723-page PDF (10 volumes).  
Processed by `text_to_volumes/` pipeline.

### `input/Complete_text_mahabharat.txt`
Alternate source used by the `southi` TXT pipeline.

---

## 2. Volume Text Outputs (`output/volumes/`)

Three files per volume, produced by `pipeline/extract/pdf_parser.py`:

| File | Content |
|------|---------|
| `volume_N_chapters.txt` | Chapter paragraphs, one `--- Chapter N ---` header per chapter |
| `volume_N_footnotes.txt` | Raw footnote text blocks |
| `volume_N_toc.txt` | Table of contents text |

Paragraph format inside `volume_N_chapters.txt`:
```
--- Chapter 1 ---
'Jaya{1}' must be recited after having bowed in obeisance...

The great sages, performers of difficult austerities...
```

Footnote reference markers in text: `{N}` (e.g., `Narayana{1}`, `Nara{2}`).

---

## 3. Core Knowledge Graph JSON (`output/json/`)

### 3a. `characters.json`

Key: `@character_id` (all lowercase, e.g. `@arjuna`, `@abhimanyu`).

```json
"@arjuna": {
  "Name": "Arjuna",
  "Alias_names": ["Partha", "Phalguna", "Dhananjaya", "Savyasachi", "Kiriti"],
  "Gender": "Male",
  "Father": "@pandu",
  "Mother": "@kunti",
  "Siblings": ["@yudhishthira", "@bhima", "@nakula", "@sahadeva"],
  "Spouse": [
    { "@draupadi": { "Relation": "Wife", "Children": [] } },
    { "@subhadra":  { "Relation": "Wife", "Children": ["@abhimanyu"] } }
  ],
  "Caste": "Kshatriya",
  "Duty": "Warrior",
  "Dynasty": "Kuru",
  "Status": "Deceased",
  "Kingdom": "@indraprastha",
  "Political_Role": "Prince / Commander",
  "Skills": ["Archery", "Gandiva bow", "Celestial weapons"],
  "Titles": ["Best archer", "Conqueror of enemies"],
  "Traits": ["Brave", "Disciplined", "Pious"],
  "Timeline": [
    {
      "Stage": "Birth",
      "Event": "Born to Kunti by Indra's blessing",
      "Location": "@hastinapura",
      "Related_Characters": ["@kunti", "@pandu"],
      "Timeline_Ref": "@event_pandava_birth"
    }
  ],
  "Major_Events": ["@event_kurukshetra_war"],
  "display": {
    "color": "#5BA4CF",
    "color_dark": "#3A7FAA",
    "opacity_narration": 0.4,
    "opacity_speech": 1.0,
    "label": "Arjuna"
  }
}
```

**Rules:**
- All cross-references use `@id` format — never raw names
- `display.color` is the character's permanent web color
- `Alias_names` must include every name variant used in the text (needed for dialogue attribution)

---

### 3b. `locations.json`

Key: `@location_id`.

```json
"@kurukshetra": {
  "Name": "Kurukshetra",
  "Type": "Battlefield / Sacred land",
  "Modern_Name": "Kurukshetra, Haryana, India",
  "Coordinates": { "lat": 29.96, "lon": 76.85 },
  "Distance_km": {},
  "Description": "Site of the great Kurukshetra War",
  "Major_Events": ["@event_kurukshetra_war"]
}
```

---

### 3c. `timeline.json`

Key: `@event_id`.

```json
"@event_kurukshetra_war": {
  "Name": "Kurukshetra War",
  "Era": "Dvapara Yuga",
  "Sequence": 45,
  "Description": "18-day war between Pandavas and Kauravas",
  "Location": "@kurukshetra",
  "Key_Characters": ["@arjuna", "@krishna", "@duryodhana", "@bhishma"],
  "Duration": "18 days",
  "Outcome": "Pandava victory"
}
```

---

### 3d. `index.json`

Master index — one entry per parva, pointing to story + footnote files.

```json
{
  "total_parvas": 18,
  "parvas": [
    {
      "parva_number": 1,
      "name": "Adi Parva",
      "details": { "num_subparvas": 19, "num_chapters": 225, "num_shlokas": 7205 },
      "chapters_loaded": 225,
      "story_file": "story/parva_01_adi_parva.json",
      "footnotes_file": "footnotes/parva_01_adi_parva_fn.json"
    }
  ]
}
```

> **Note**: `story_file` currently points to the legacy flat JSON. After folder split, it can point to `story/parva_01_adi_parva/parva_01_adi_parva.json`.

---

## 4. Story JSON — Parva Folder Structure (new, post-split)

After running `split_parva_to_folders.py`, each parva lives in its own folder.

### 4a. Main Parva JSON (`parva_NN_<name>/parva_NN_<name>.json`)

Metadata + subparva file references. **No inline chapter content.**

```json
{
  "name": "Adi Parva",
  "parva_number": 1,
  "details": { "num_subparvas": 19, "num_chapters": 225, "num_shlokas": 7205 },
  "subparvas": {
    "1": {
      "subparva_number": 1,
      "name": "Anukramanika Parva",
      "source_volume": 1,
      "details": { "num_chapters": 1, "num_shlokas": 210 },
      "note": "...",
      "file": "parva_01_adi_parva/subparva_01_anukramanika_parva.json"
    }
  }
}
```

### 4b. Subparva JSON (`subparva_NN_<name>.json`)

Full chapter + paragraph content.

```json
{
  "name": "Anukramanika Parva",
  "subparva_number": 1,
  "source_volume": 1,
  "file_path": "output/volumes/volume_1_chapters.txt",
  "details": { "num_chapters": 1, "num_shlokas": 210 },
  "note": "...",
  "chapters": {
    "1": {
      "global_number": 1,
      "local_number": 1,
      "num_shlokas": 210,
      "paragraphs": {
        "1": "'Jaya{1}' must be recited after having bowed in obeisance before Narayana...",
        "2": "The great sages, performers of difficult austerities..."
      }
    }
  }
}
```

**Chapter numbering:**
- `global_number`: chapter number across the whole Mahabharata (1–2,100+)
- `local_number`: chapter number within the subparva
- Footnote refs: `{N}` inline in paragraph text → links to `footnotes/parva_NN_*_fn.json`

---

## 5. Annotated Story JSON (dialogue layer — planned)

Written as `subparva_NN_<name>_annotated.json` alongside the source. **Never overwrites source.**

```json
{
  "name": "Anukramanika Parva",
  "subparva_number": 1,
  "chapters": {
    "1": {
      "global_number": 1,
      "paragraphs": {
        "1": {
          "raw": "'Jaya{1}' must be recited...",
          "frame": 0,
          "narrator": "@ugrasrava",
          "segments": [
            {
              "type": "narration",
              "speaker": "@ugrasrava",
              "text": "'Jaya{1}' must be recited...",
              "color": "#E8B86D",
              "opacity": 0.4
            }
          ]
        },
        "7": {
          "raw": "Souti said: '...'",
          "frame": 0,
          "narrator": "@ugrasrava",
          "segments": [
            { "type": "attribution", "speaker": "@ugrasrava", "text": "Souti said: " },
            { "type": "speech",      "speaker": "@ugrasrava", "text": "'...'", "color": "#E8B86D", "opacity": 1.0 }
          ]
        }
      }
    }
  }
}
```

### Segment Types

| type | Meaning |
|------|---------|
| `narration` | Plain narration by active frame's narrator |
| `attribution` | `"[Name] said, "` prefix text |
| `speech` | Direct speech content inside quotes |
| `nested_speech` | Speech quoted inside another speech (double nested) |

### Frame Numbers

| Frame | Narrator | Context |
|-------|---------|---------|
| 0 | Souti (`@ugrasrava`) | Narrating to sages at Naimisharanya |
| 1 | Vaishampayana (`@vaishampayana`) | Reciting at Janamejaya's snake sacrifice |
| 2 | Sanjaya (`@sanjaya`) | Narrating to Dhritarashtra |
| N | Any character | Direct character dialogue within any frame |

---

## 6. Footnotes JSON (`output/json/footnotes/`)

One file per parva: `parva_NN_<name>_fn.json`.

```json
{
  "parva": 1,
  "footnotes": {
    "1": "Jaya means 'victory'. This is the title of the original 8,800-verse work...",
    "2": "Nara and Narayana are twin sages, human incarnations of Vishnu..."
  }
}
```

Footnote number in text `{1}` maps to key `"1"` in this file.

---

## 7. Character Color Palette (web display)

Characters are assigned permanent hex colors. Used across the website for text highlighting.

### Narrative Layer Colors
| Character | Role | Hex | Usage |
|-----------|------|-----|-------|
| Souti / Ugrasrava | Outer narrator | `#E8B86D` | Warm amber |
| Vaishampayana | Secondary narrator | `#7EB8F7` | Calm blue |
| Sanjaya | Tertiary narrator | `#A8D5A2` | Sage green |

### Principal Character Colors
| Character | Hex | Semantic meaning |
|-----------|-----|----------------|
| Krishna | `#6C5CE7` | Deep violet — divine |
| Yudhishthira | `#F4D35E` | Gold — dharma |
| Arjuna | `#5BA4CF` | Bright blue — warrior |
| Bhima | `#E07A5F` | Red-orange — strength |
| Draupadi | `#E84393` | Vivid pink |
| Duryodhana | `#D62828` | Dark red — antagonist |
| Karna | `#F77F00` | Deep orange — tragic hero |
| Bhishma | `#457B9D` | Steel blue — patriarch |
| Drona | `#2D6A4F` | Forest green — preceptor |
| Dhritarashtra | `#9B8BB4` | Muted purple — blind king |
| Gandhari | `#B5838D` | Rose |
| Kunti | `#E9C46A` | Warm yellow |

### Color Rules
- `display.color` — full opacity color for direct speech
- `display.color_dark` — darker shade for dark-mode websites
- `opacity_narration: 0.4` — when the character is the active narrator (not speaking)
- `opacity_speech: 1.0` — when the character is directly quoted

---

## 8. Summary: All Formats at a Glance

| File/Format | Purpose | Location |
|-------------|---------|----------|
| `volume_N_chapters.txt` | Raw paragraph text by volume | `output/volumes/` |
| `characters.json` | 525+ characters, @id cross-refs | `output/json/` |
| `locations.json` | 52 locations with coordinates | `output/json/` |
| `timeline.json` | 58 story events | `output/json/` |
| `index.json` | Master parva → file map | `output/json/` |
| `parva_NN_<name>.json` (flat) | Legacy full parva (source of truth) | `output/json/story/` |
| `parva_NN_<name>/parva_NN_<name>.json` | Parva metadata + subparva refs | `output/json/story/<folder>/` |
| `subparva_NN_<name>.json` | Full chapters + paragraphs | `output/json/story/<folder>/` |
| `subparva_NN_<name>_annotated.json` | Dialogue-annotated paragraphs + colors | `output/json/story/<folder>/` |
| `parva_NN_<name>_fn.json` | Footnote text by number | `output/json/footnotes/` |
| `bori_official.json` | BORI critical edition reference | `output/json/` |
| `introduction.json` | Translator's introduction | `output/json/` |
| `mahabharata_sections.json` | High-level section structure | `output/json/` |
