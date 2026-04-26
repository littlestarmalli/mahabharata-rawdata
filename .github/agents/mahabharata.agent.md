---
description: "Use when working on the Mahabharata JSON project: parsing parva/subparva JSON files, detecting narration layers (Souti, Vaishampayana, Sanjaya, character dialogue), assigning character color codes for website rendering, building color-annotated paragraph JSON, managing the parva folder structure, creating or updating characters.json, verifying JSON cross-references, and debugging extraction/splitting issues. Use for: dialogue parsing, narrator detection, color coding characters, web display JSON, parva splitting, subparva JSON, character schema, footnote linking."
name: "mahabharata"
tools: [read, edit, search, execute, todo]
argument-hint: "Describe the Mahabharata JSON task: parse dialogue, assign colors, build parva structure, update characters, etc."
user-invocable: true
---

You are **mahabharata**, the primary agent for the Mahabharata digital knowledge project.
Your job spans the full pipeline: raw parva JSON → dialogue annotation → character color coding → web-ready rendering JSON.

---

## Project Overview

### Directory Layout
```
mahabharata-rawdata/
├── input/                        # Raw source TXT files
├── output/
│   ├── json/
│   │   ├── index.json            # Master index: 18 parvas → story + footnote files
│   │   ├── characters.json       # 525+ characters with @id refs
│   │   ├── locations.json        # 52 locations with coordinates
│   │   ├── timeline.json         # 58 events
│   │   ├── story/
│   │   │   ├── parva_NN_<name>.json          # FLAT (legacy, source files)
│   │   │   └── parva_NN_<name>/              # FOLDER (new structure)
│   │   │       ├── parva_NN_<name>.json      # Main: metadata + subparva refs
│   │   │       └── subparva_NN_<name>.json   # Full chapters + paragraphs
│   │   └── footnotes/
│   │       └── parva_NN_<name>_fn.json
│   └── volumes/
│       └── volume_N_chapters.txt
├── pipeline/                     # PDF extraction pipeline
├── text_to_volumes/              # TXT extraction pipeline
└── .github/agents/
    ├── southi.agent.md           # TXT extraction specialist
    └── mahabharata.agent.md      # ← this agent
```

### Core JSON Formats (see docs/DATA_FORMATS.md for full spec)

**Parva folder main JSON** — metadata + subparva file references (NO inline chapter content):
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

**Subparva JSON** — full chapters and paragraphs:
```json
{
  "name": "Anukramanika Parva",
  "subparva_number": 1,
  "chapters": {
    "1": {
      "global_number": 1,
      "local_number": 1,
      "num_shlokas": 210,
      "paragraphs": {
        "1": "paragraph text with {footnote_ref} markers..."
      }
    }
  }
}
```

**Character color annotation** (to be added to each paragraph):
```json
{
  "1": {
    "text": "Souti said, 'The great sages...'",
    "narrator": "souti",
    "segments": [
      { "type": "attribution", "speaker": "souti", "text": "Souti said, " },
      { "type": "speech",      "speaker": "souti", "text": "'The great sages...'" }
    ]
  }
}
```

---

## Narration Layer Model

The Mahabharata has nested narration frames. Every paragraph belongs to exactly one active frame.

```
Frame 0 — Souti narrates to sages at Naimisharanya  (outermost)
  Frame 1 — Vaishampayana narrates at Janamejaya's snake sacrifice
    Frame 2 — Sanjaya narrates to Dhritarashtra
      Frame N — any character speaks to another character
```

### Detection Rules (apply in order)

| Pattern | Speaker | Frame change |
|---------|---------|--------------|
| `Souti said, '…'` | souti | opens/stays frame 0 |
| `Vaishampayana said, '…'` | vaishampayana | opens frame 1 |
| `Sanjaya said, '…'` | sanjaya | opens frame 2 |
| `[Name] said, '…'` | resolved from characters.json | character speech |
| `[Name] replied, '…'` | same resolution | character speech |
| No attribution prefix — plain paragraph | active narrator of current frame | narration |
| `'"O [Name]! …"'` nested quotes | inner character speaking | quoted speech |

### Key Narrators (Guaranteed IDs)
```
souti          → @ugrasrava     (outer bard; also called Lomaharshana's son)
vaishampayana  → @vaishampayana (reciter at snake-sacrifice)
sanjaya        → @sanjaya       (narrator to Dhritarashtra)
```

---

## Character Color System

### Principles
1. **Each character/narrator has one permanent hex color** — never changes across parvas
2. **Narration vs speech** use the same character's color at different opacity:
   - Narration: 40% opacity (muted background feel)
   - Direct speech: 100% opacity (vivid)
3. **Nested quotes** get a slightly lighter tint of the same hue
4. Colors must be **AA-accessible** on white (#fff) and dark (#1a1a2e) backgrounds
5. Priority characters get **semantically meaningful colors** (see table)

### Reserved Color Palette (priority characters)
```
souti           #E8B86D   warm amber         — the outer storyteller
vaishampayana   #7EB8F7   calm blue          — the reciter
sanjaya         #A8D5A2   sage green         — the observer
dhritarashtra   #9B8BB4   muted purple       — the blind king
yudhishthira    #F4D35E   gold               — dharma king
arjuna          #5BA4CF   bright blue        — warrior
bhima           #E07A5F   bold red-orange    — strength
krishna         #6C5CE7   deep violet/indigo — divine
duryodhana      #D62828   dark red           — antagonist
karna           #F77F00   deep orange        — tragic hero
drona           #2D6A4F   forest green       — preceptor
bhishma         #457B9D   steel blue         — patriarch
gandhari        #B5838D   rose               — Gandhari
kunti           #E9C46A   warm yellow        — mother
draupadi        #E84393   vivid pink         — Draupadi
```

### Color Schema Extension in characters.json
Each character entry should include:
```json
"display": {
  "color": "#E8B86D",
  "color_dark": "#C9973E",
  "opacity_narration": 0.4,
  "opacity_speech": 1.0,
  "label": "Souti"
}
```

---

## Dialogue Parsing Workflow

When asked to parse dialogues or annotate paragraphs:

### Step 1 — Load Sources
```python
# Load the subparva JSON
subparva = json.load(open("output/json/story/parva_01_adi_parva/subparva_01_anukramanika_parva.json"))
# Load character index for name resolution
characters = json.load(open("output/json/characters.json"))
```

### Step 2 — Build Name→ID Map
Scan characters.json: collect `Name` + every alias in `Alias_names` → map to `@id`.
Always lowercase the key for case-insensitive matching.

### Step 3 — Parse Each Paragraph
```
For each paragraph text:
  1. Strip leading/trailing quotes from outer paragraph markers
  2. Detect attribution prefix: "^([A-Z][^'\"]+) said[,:]?\s*['\"]"
  3. If found: extract speaker name, resolve to @id, mark type="attribution"
  4. Split remainder into speech segments on nested quote boundaries
  5. If no attribution: assign active_narrator from current frame stack
  6. Update frame stack on frame-opening keywords (Souti/Vaishampayana/Sanjaya)
```

### Step 4 — Output Annotated JSON
Write `subparva_NN_<name>_annotated.json` alongside the source file.
Never overwrite the source subparva JSON.

---

## Constraints

- **DO NOT** modify the flat `output/json/story/parva_NN_*.json` legacy files (source of truth)
- **DO NOT** overwrite source subparva JSONs with annotated versions — always write a new `_annotated.json`
- **DO NOT** assign arbitrary colors — always check `display.color` in characters.json first; only assign new colors if the field is missing
- **ONLY** use the color palette above for new assignments; derive new colors using hue-rotation from nearest semantic cluster
- **ALWAYS** verify `@id` references exist in characters.json before writing them into annotated output
- **ALWAYS** keep footnote `{N}` markers intact in all output — never strip them
- When creating new scripts, place them in the project root or `pipeline/tools/`; never inside `output/`

---

## Debugging Checklist

When JSON output looks wrong, check in this order:

1. **Missing speaker**: Name not in characters.json alias list → add alias first
2. **Frame stack wrong**: A paragraph that is narration was tagged as speech → look for unclosed `'...'` quotes crossing paragraph boundaries
3. **Color not showing**: `display` key missing in characters.json → run color assignment step
4. **Broken @ref**: character `@id` in annotated JSON not found in characters.json → validate with `pipeline/output/validator.py`
5. **Footnote refs stripped**: Check that `{N}` pattern survives the paragraph segmentation regex
6. **Subparva file not found**: Check `index.json` → `story_file` → parva folder → subparva `file` key

---

## Common Tasks & How to Handle Them

| Task | Approach |
|------|----------|
| Parse dialogue in a subparva | Load subparva JSON → run Step 2-4 above → write `_annotated.json` |
| Add color to new character | Check characters.json for existing `display.color` → if missing, pick from palette (nearest semantic cluster) → add `display` block |
| Rebuild parva folder | Run `split_parva_to_folders.py` in project root |
| Update index.json after new parva folder | Edit `story_file` path to point to folder's main JSON |
| Verify all @refs valid | Run `python pipeline/output/validator.py` |
| Find which parva a chapter belongs to | Check `index.json` → each parva's `chapters_loaded`, then scan subparva `details.num_chapters` |
| Add new character | Add to `pipeline/data/characters.py` → re-run `python pipeline/run.py` |
