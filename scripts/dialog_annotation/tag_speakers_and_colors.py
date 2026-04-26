"""
tag_speakers_and_colors.py
--------------------------
Step 1 — Assign a unique 'display' color to every character in characters.json.
         Priority characters get hand-picked semantic colors.
         All remaining characters get auto-generated unique colors via
         golden-ratio HSL spacing (deterministic, reproducible).

Step 2 — Parse every subparva JSON in output/json/story/parva_*/
         and write a *_tagged.json alongside it.
         Each paragraph is expanded into:
           {
             "raw": "original text",
             "frame": <int>,
             "speaker": "@character_id",   ← who says/narrates this paragraph
             "speaker_name": "Display Name",
             "color": "#RRGGBB",
             "segments": [
               {"type": "attribution", "speaker": "@id", "text": "Souti said, "},
               {"type": "speech",      "speaker": "@id", "text": "'...'"},
               {"type": "narration",   "speaker": "@id", "text": "..."}
             ]
           }

Usage:
    python tag_speakers_and_colors.py            # process all parvas
    python tag_speakers_and_colors.py --colors-only   # only add colors, skip parsing
    python tag_speakers_and_colors.py --parva 1  # only process parva 1
"""

import json
import os
import re
import colorsys
import argparse
import glob
from pathlib import Path

BASE = Path(__file__).parent
CHARS_FILE  = BASE / "output" / "json" / "characters.json"
STORY_DIR   = BASE / "output" / "json" / "story"

# ---------------------------------------------------------------------------
# 1. PRIORITY COLOR MAP
#    Hand-picked semantic colors for key characters / narrators.
#    Format: "@id" -> (hex_light, hex_dark, label)
# ---------------------------------------------------------------------------
PRIORITY_COLORS = {
    # ── Narrators / frame anchors ──────────────────────────────────────────
    "@author":           ("#C8B8A2", "#8A7A68", "Author"),
    "@sages":            ("#B8D4C8", "#7AA898", "The Sages"),
    "@ugrasrava":        ("#E8B86D", "#C9973E", "Souti"),
    "@vaishampayana":    ("#7EB8F7", "#4E88CC", "Vaishampayana"),
    "@sanjaya":          ("#A8D5A2", "#6BAD64", "Sanjaya"),

    # ── Pandavas ───────────────────────────────────────────────────────────
    "@yudhishthira":     ("#F4D35E", "#C9A82E", "Yudhishthira"),
    "@arjuna":           ("#5BA4CF", "#3A7FAA", "Arjuna"),
    "@bhima":            ("#E07A5F", "#B84E35", "Bhima"),
    "@nakula":           ("#81B29A", "#4E8C72", "Nakula"),
    "@sahadeva":         ("#6BAB8A", "#3E7C5C", "Sahadeva"),
    "@kunti":            ("#E9C46A", "#C49A30", "Kunti"),
    "@draupadi":         ("#E84393", "#B5166A", "Draupadi"),
    "@subhadra":         ("#A29BFE", "#7A6FD0", "Subhadra"),

    # ── Krishna / Yadavas ─────────────────────────────────────────────────
    "@krishna":          ("#6C5CE7", "#4835C0", "Krishna"),
    "@balarama":         ("#00B4D8", "#007EA0", "Balarama"),
    "@satyaki":          ("#22D3EE", "#0891B2", "Satyaki"),

    # ── Kauravas ──────────────────────────────────────────────────────────
    "@duryodhana":       ("#D62828", "#A01818", "Duryodhana"),
    "@duhshasana":       ("#C1121F", "#8B0D15", "Duhshasana"),
    "@dhritarashtra":    ("#9B8BB4", "#6B5B8E", "Dhritarashtra"),
    "@gandhari":         ("#B5838D", "#8A5560", "Gandhari"),
    "@shakuni":          ("#8B4513", "#5C2A00", "Shakuni"),
    "@karna":            ("#F77F00", "#C05A00", "Karna"),

    # ── Elders / Preceptors ───────────────────────────────────────────────
    "@bhishma":          ("#457B9D", "#2B5F80", "Bhishma"),
    "@drona":            ("#2D6A4F", "#1A4530", "Drona"),
    "@kripa":            ("#40916C", "#2D6A4F", "Kripa"),
    "@vidura":           ("#52796F", "#354F52", "Vidura"),
    "@ashvatthama":      ("#8B5E3C", "#5C3A1E", "Ashvatthama"),
    "@vyasa":            ("#FFBF69", "#C47800", "Vyasa"),
    "@parashurama":      ("#4A7C59", "#2D5240", "Parashurama"),

    # ── Other key characters ──────────────────────────────────────────────
    "@abhimanyu":        ("#F2CC8F", "#C9943A", "Abhimanyu"),
    "@janamejaya":       ("#C77DFF", "#9B4DCA", "Janamejaya"),
    "@parikshit":        ("#B7D7E8", "#6FA8C5", "Parikshit"),
    "@pandu":            ("#D4E09B", "#9DB84A", "Pandu"),
    "@shantanu":         ("#8ECAE6", "#3A8BB4", "Shantanu"),
    "@satyavati":        ("#FF9F1C", "#C07000", "Satyavati"),
    "@narada":           ("#CBF3F0", "#5BBAB5", "Narada"),
    "@indra":            ("#FFD60A", "#C9A800", "Indra"),
    "@shiva":            ("#CDB4DB", "#9B6DB4", "Shiva"),
    "@yama":             ("#6B4226", "#3E2010", "Yama"),
    "@drupada":          ("#4CC9F0", "#1A9EC0", "Drupada"),
    "@dhrishtadyumna":   ("#4361EE", "#1A3DBB", "Dhrishtadyumna"),
    "@shikhandi":        ("#7209B7", "#4A0078", "Shikhandi"),
    "@uttara":           ("#FCA311", "#B37200", "Uttara"),
    "@virata":           ("#70D6FF", "#3A9AC5", "Virata"),
    "@kichaka":          ("#9D0208", "#6A0104", "Kichaka"),
    "@jayadratha":       ("#6A0572", "#3D0040", "Jayadratha"),
    "@ghatotkacha":      ("#3A5A40", "#1B3020", "Ghatotkacha"),
    "@hidimba":          ("#588157", "#2D5227", "Hidimba"),
    "@eklavya":          ("#BC6C25", "#7A3A00", "Eklavya"),
    "@kripacharya":      ("#40916C", "#1B5E3A", "Kripacharya"),
}

# ---------------------------------------------------------------------------
# 2. AUTO-COLOR GENERATOR
#    Golden-ratio HSL spacing to fill remaining 450+ characters.
#    Skips hue ranges already claimed by priority colors.
# ---------------------------------------------------------------------------

def _hex_to_hsl(hex_color: str):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s * 100, l * 100

def _hsl_to_hex(h: float, s: float, l: float) -> str:
    h /= 360; s /= 100; l /= 100
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02X}{:02X}{:02X}".format(int(r*255), int(g*255), int(b*255))

def _darken(hex_color: str, factor: float = 0.75) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return "#{:02X}{:02X}{:02X}".format(
        int(r * factor), int(g * factor), int(b * factor))

def generate_auto_colors(char_ids: list[str]) -> dict[str, tuple[str, str]]:
    """Return {char_id: (hex_light, hex_dark)} for characters without priority colors."""
    GOLDEN = 0.61803398875
    claimed_hues = {_hex_to_hsl(c)[0] for c, _, _ in PRIORITY_COLORS.values()}

    results = {}
    hue = 37.0  # start offset
    for char_id in char_ids:
        # Advance by golden ratio until we find an un-claimed hue slot
        for _ in range(100):
            hue = (hue + GOLDEN * 360) % 360
            if all(abs(hue - ch) > 8 for ch in claimed_hues):
                break
        claimed_hues.add(hue)
        light = _hsl_to_hex(hue, 65, 58)
        dark  = _hsl_to_hex(hue, 65, 38)
        results[char_id] = (light, dark)
    return results

# ---------------------------------------------------------------------------
# 3. BUILD NAME → @ID MAP
# ---------------------------------------------------------------------------

def build_name_map(chars: dict) -> dict[str, str]:
    """
    Returns lowercase_name -> @id for every Name and Alias in characters.json.
    Also adds common narrator nicknames.
    """
    name_map = {}
    for char_id, data in chars.items():
        # Primary name
        if data.get("Name"):
            name_map[data["Name"].lower()] = char_id
        # Aliases
        for alias in data.get("Alias_names", []):
            if alias:
                name_map[alias.lower()] = char_id

    # Hard-coded narrator aliases that may not appear in Alias_names
    overrides = {
        "souti":            "@ugrasrava",
        "lomaharshana's son": "@ugrasrava",
        "suta":             "@ugrasrava",
        "the suta":         "@ugrasrava",
        "the son of suta":  "@ugrasrava",
        "vaishampayana":    "@vaishampayana",
        "sanjaya":          "@sanjaya",
        "the son of gavalgana": "@sanjaya",
        "gavalgana's son":  "@sanjaya",
        "dvaipayana":       "@vyasa",
        "krishna dvaipayana": "@vyasa",
        "the author":       "@author",
        "vyasa":            "@vyasa",
        "sages":            "@sages",
        "the sages":        "@sages",
        "the hermits":      "@sages",
        "the rishis":       "@sages",
        "the brahmarshis":  "@sages",
        "the brahmins":     "@sages",
        "brahmarshis":      "@sages",
        "sarama":           "@sarama",
        "the mother":       "@sarama",  # context: dog story; acceptable alias
        "sarama's son":     "@sarama_son",
        "sarameyau":        "@sarama_son",
        "krishna":          "@krishna",
        "vasudeva":         "@krishna",
        "keshava":          "@krishna",
        "madhava":          "@krishna",
        "janardana":        "@krishna",
        "govinda":          "@krishna",
        "hrishikesha":      "@krishna",
        "shouri":           "@krishna",
        "partha":           "@arjuna",
        "dhananjaya":       "@arjuna",
        "phalguna":         "@arjuna",
        "savyasachi":       "@arjuna",
        "kiriti":           "@arjuna",
        "bibhatsu":         "@arjuna",
        "vrikodara":        "@bhima",
        "bhimasena":        "@bhima",
        "dharmaraja":       "@yudhishthira",
        "ajatashatru":      "@yudhishthira",
        "pandava":          "@yudhishthira",   # generic; context-dependent
        "radheya":          "@karna",
        "radha's son":      "@karna",
        "the son of a charioteer": "@karna",
        "suyodhana":        "@duryodhana",
        "kshatta":          "@vidura",
        "pitamaha":         "@bhishma",
        "shantanu's son":   "@bhishma",
        "pracheta":         "@yama",
        "acharya":          "@drona",
        "dronacharya":      "@drona",
        "the preceptor":    "@drona",
        "ashvatthaman":     "@ashvatthama",
        "the son of drona": "@ashvatthama",
        "yuyudhana":        "@satyaki",
    }
    name_map.update(overrides)
    return name_map

# ---------------------------------------------------------------------------
# 4. FRAME STACK — NARRATION LAYER MODEL
# ---------------------------------------------------------------------------

# Patterns that OPEN (or confirm) a specific narrator frame.
# Each entry: (compiled_regex, @narrator_id, frame_level)
FRAME_OPENERS = [
    (re.compile(r"^souti said",           re.I), "@ugrasrava",     0),
    (re.compile(r"^suta said",            re.I), "@ugrasrava",     0),
    (re.compile(r"^the suta said",        re.I), "@ugrasrava",     0),
    (re.compile(r"^the son of suta said", re.I), "@ugrasrava",     0),
    (re.compile(r"^the sages said",       re.I), "@sages",         0),
    (re.compile(r"^vaishampayana said",   re.I), "@vaishampayana", 1),
    (re.compile(r"^vaishampayana continued", re.I), "@vaishampayana", 1),
    (re.compile(r"^sanjaya said",         re.I), "@sanjaya",       2),
    (re.compile(r"^sanjaya continued",    re.I), "@sanjaya",       2),
]

DEFAULT_INITIAL_FRAME = ("@author", -1)   # Author/Vyasa is the outermost frame

# ---------------------------------------------------------------------------
# 5. QUOTE-TREE PARSER
#    Tokenises text into segments based on quote nesting depth.
#
#    Quote structure in Debroy translation:
#      No quotes        => @author voice (depth 0)
#      'single quotes'  => frame-narrator's narration (e.g. Souti's story)
#      "double quotes"  => character speech inside the current narrator's frame
#
#    Chapters are processed as a continuous stream so that unclosed single
#    quotes carry over across paragraph boundaries.
# ---------------------------------------------------------------------------

# Single-quote boundary chars (both curly and straight)
_SQ_CHARS = "\u2018\u2019'"

# Double-quote boundary chars
_DQ_OPEN_CHARS  = '\u201c"'
_DQ_CLOSE_CHARS = '\u201d"'

# Attribution verb pattern anchored at END of a text block (before a " opening)
_ATTRIB_VERB_RE = re.compile(
    r"((?:the\s+)?[A-Za-z][A-Za-z\-']{0,25}(?:\s+[A-Za-z][A-Za-z\-']{0,20}){0,3})"
    r"[^\"'\u201c\u201d]{0,80}?"
    r"\b(?:said|replied|answered|asked|told|spoke|addressed|exclaimed"
    r"|informed|called|shouted|whispered|continued|declared|narrated)\b"
    r"[^\"'\u201c\u201d]{0,40}?"
    r"\s*[,:.!?]?\s*$",
    re.UNICODE,
)

_NON_NAME_WORDS = frozenset({
    "then", "thus", "when", "while", "after", "before", "as", "on", "at",
    "having", "and", "but", "so", "since", "once", "now", "there", "here",
    "this", "that", "these", "those", "his", "her", "their", "its",
    "soon", "later", "earlier", "finally", "suddenly", "immediately",
})


def _resolve_speaker(raw_name: str, fallback: str, name_map: dict) -> str:
    sid = name_map.get(raw_name.lower())
    if sid:
        return sid
    slug = re.sub(r"[^a-z0-9]", "_", raw_name.lower()).strip("_")
    return "@" + slug if slug else fallback


def _find_attribution(before: str, narrator_id: str, name_map: dict):
    """
    Find a trailing attribution phrase at the very end of `before`.
    Returns (narr_prefix, speaker_id, attrib_text) or None.
    Try shortest fragment first (last sentence) so we don't grab the whole paragraph.
    """
    candidates = []
    # Strip trailing punctuation/whitespace for searching
    search_text = before.rstrip(" ,;:.!?")
    # Build candidates from shortest to longest (last sentence first)
    for sep in (", ", "; ", ". ", "! ", "? "):
        idx = search_text.rfind(sep)
        if idx >= 0:
            fragment = search_text[idx + len(sep):]
            if fragment.strip():
                candidates.append((idx + len(sep), fragment))
    # Full before text as last resort
    candidates.append((0, search_text))

    for start_offset, fragment in candidates:
        m = _ATTRIB_VERB_RE.search(fragment.rstrip())
        if not m:
            continue
        raw_name = m.group(1).strip()
        if raw_name.lower() in _NON_NAME_WORDS:
            continue
        # Reject if first word looks like a participle, conjunction or adverb
        first_word = raw_name.split()[0].lower()
        if first_word in _NON_NAME_WORDS or first_word.endswith("ing") or first_word.endswith("ed"):
            # Try stripping the first word(s) that are non-names
            words = raw_name.split()
            while words and (words[0].lower() in _NON_NAME_WORDS
                             or words[0].lower().endswith("ing")
                             or words[0].lower().endswith("ed")):
                words.pop(0)
            raw_name = " ".join(words)
            if not raw_name:
                continue
        # Reject pronoun attributions (He, She, They, etc.) — but allow "The X said"
        _PRONOUNS = frozenset({"he", "she", "they", "it", "we", "i", "one",
                                "this", "that", "his", "her", "their"})
        if raw_name.split()[0].lower() in _PRONOUNS:
            continue
        narr_prefix = before[:start_offset + m.start()].rstrip()
        attrib_text = search_text[start_offset + m.start():].rstrip()
        speaker_id  = _resolve_speaker(raw_name, narrator_id, name_map)
        return narr_prefix, speaker_id, attrib_text
    return None


class _Span:
    __slots__ = ("stype", "speaker", "text", "depth")
    def __init__(self, stype, speaker, text, depth):
        self.stype = stype
        self.speaker = speaker
        self.text = text
        self.depth = depth


def tokenise_text(text, frame_narrator, init_sq_depth, init_dq_stack, name_map, chars):
    """
    Walk `text` character by character tracking single-quote and double-quote depth.

    Returns (spans, final_sq_depth, final_dq_stack).
    """
    sq_depth = init_sq_depth
    dq_stack = list(init_dq_stack)
    buf = []
    spans = []
    i = 0
    n = len(text)

    def current_narrator():
        return dq_stack[-1] if dq_stack else frame_narrator

    def flush(span_type, speaker):
        t = "".join(buf).strip()
        if t:
            spans.append(_Span(span_type, speaker, t, sq_depth + len(dq_stack)))
        buf.clear()

    while i < n:
        ch = text[i]
        prev_ch = text[i - 1] if i > 0 else " "
        next_ch = text[i + 1] if i + 1 < n else " "

        # Apostrophe guard: letter-apostrophe-letter is NOT a frame boundary
        is_apostrophe = (ch in _SQ_CHARS and prev_ch.isalpha() and next_ch.isalpha())

        if ch in _SQ_CHARS and not is_apostrophe and not dq_stack:
            if sq_depth == 0:
                # Opening single quote: flush author narration, enter narrator frame
                flush("narration", frame_narrator)
                sq_depth += 1
                buf.append(ch)
            else:
                # Closing single quote: include then flush narrator narration
                buf.append(ch)
                flush("narration", frame_narrator)
                sq_depth -= 1

        elif ch in _DQ_OPEN_CHARS:
            # Opening double quote: look back for attribution
            before = "".join(buf)
            attrib = _find_attribution(before, current_narrator(), name_map)
            if attrib:
                narr_prefix, speaker_id, attrib_text = attrib
                if narr_prefix.strip():
                    spans.append(_Span("narration", current_narrator(),
                                       narr_prefix.strip(), sq_depth + len(dq_stack)))
                spans.append(_Span("attribution", current_narrator(),
                                   attrib_text.strip(), sq_depth + len(dq_stack)))
                buf.clear()
                dq_stack.append(speaker_id)
            else:
                flush("narration", current_narrator())
                dq_stack.append(current_narrator())
            buf.append(ch)

        elif ch in _DQ_CLOSE_CHARS and dq_stack:
            buf.append(ch)
            speaker_id = dq_stack[-1]
            t = "".join(buf).strip()
            if t:
                spans.append(_Span("speech", speaker_id, t, sq_depth + len(dq_stack)))
            buf.clear()
            dq_stack.pop()

        else:
            buf.append(ch)

        i += 1

    # Flush remaining buffer
    if buf:
        t = "".join(buf).strip()
        if t:
            spans.append(_Span("narration", current_narrator(), t,
                               sq_depth + len(dq_stack)))

    return spans, sq_depth, dq_stack


def _get_display(speaker_id: str, chars: dict):
    """Return (color, opacity_speech, opacity_narration) for a speaker."""
    char = chars.get(speaker_id, {})
    disp = char.get("display", {})
    color  = disp.get("color", "#888888")
    op_sp  = disp.get("opacity_speech", 1.0)
    op_na  = disp.get("opacity_narration", 0.4)
    return color, op_sp, op_na


def spans_to_segments(spans, chars):
    result = []
    for sp in spans:
        color, op_speech, op_narr = _get_display(sp.speaker, chars)
        opacity = op_speech if sp.stype == "speech" else op_narr
        result.append({
            "type":    sp.stype,
            "speaker": sp.speaker,
            "text":    sp.text,
            "color":   color,
            "opacity": opacity,
            "depth":   sp.depth,
        })
    return result


# ---------------------------------------------------------------------------
# 6. PROCESS ONE SUBPARVA FILE
# ---------------------------------------------------------------------------

# Frame narrator lookup by @id
_FRAME_NARRATOR_LEVELS = {
    "@author":        -1,
    "@ugrasrava":      0,
    "@vaishampayana":  1,
    "@sanjaya":        2,
}


def process_subparva(sp_path: Path, chars: dict, name_map: dict):
    with open(sp_path, encoding="utf-8") as fh:
        sp = json.load(fh)

    tagged_chapters = {}

    frame_narrator, active_frame = DEFAULT_INITIAL_FRAME

    for ch_key, ch_data in sorted(sp.get("chapters", {}).items(), key=lambda x: int(x[0])):
        tagged_paragraphs = {}

        # Reset quote depth at each chapter start (chapters are independent units)
        sq_depth = 0
        dq_stack = []

        for p_key, p_text in sorted(ch_data.get("paragraphs", {}).items(), key=lambda x: int(x[0])):
            if not isinstance(p_text, str):
                continue

            # Check for frame opener (Souti said / Vaishampayana said / etc.)
            stripped = p_text.strip()
            for pattern, narrator_id, frame_level in FRAME_OPENERS:
                if pattern.match(stripped):
                    frame_narrator = narrator_id
                    active_frame   = frame_level
                    sq_depth       = 0
                    dq_stack       = []
                    break

            # Tokenise paragraph, carrying quote state from previous paragraph
            spans, sq_depth, dq_stack = tokenise_text(
                p_text, frame_narrator, sq_depth, dq_stack, name_map, chars)

            segments = spans_to_segments(spans, chars)

            para_speaker = frame_narrator
            char_data    = chars.get(para_speaker, {})
            label = char_data.get("display", {}).get(
                "label", char_data.get("Name", para_speaker.lstrip("@")))

            tagged_paragraphs[p_key] = {
                "raw":          p_text,
                "frame":        active_frame,
                "speaker":      para_speaker,
                "speaker_name": label,
                "color":        chars.get(para_speaker, {}).get(
                                    "display", {}).get("color", "#888888"),
                "segments":     segments,
            }

        tagged_chapters[ch_key] = {
            "global_number": ch_data.get("global_number"),
            "local_number":  ch_data.get("local_number"),
            "num_shlokas":   ch_data.get("num_shlokas"),
            "paragraphs":    tagged_paragraphs,
        }

    output = {
        "name":            sp.get("name"),
        "subparva_number": sp.get("subparva_number"),
        "source_volume":   sp.get("source_volume"),
        "details":         sp.get("details", {}),
        "note":            sp.get("note", ""),
        "work_author":     "@author",
        "translator":      "Bibek Debroy",
        "frame_model": {
            "min_frame": -1,
            "frame_map": {
                "-1": "@author",
                "0":  "@ugrasrava",
                "1":  "@vaishampayana",
                "2":  "@sanjaya"
            }
        },
        "chapters":        tagged_chapters,
    }

    out_path = sp_path.parent / (sp_path.stem + "_tagged.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)

    return out_path


# ---------------------------------------------------------------------------
# 7. MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--colors-only", action="store_true",
                        help="Only add colors to characters.json, skip parsing")
    parser.add_argument("--parva", type=int, default=None,
                        help="Only process this parva number (1-18)")
    args = parser.parse_args()

    # ── Load characters ──────────────────────────────────────────────────
    with open(CHARS_FILE, encoding="utf-8") as fh:
        chars = json.load(fh)

    # ── Step 1: Assign colors ────────────────────────────────────────────
    print("=== Step 1: Assigning colors ===")
    no_color_ids = [cid for cid, v in chars.items() if "display" not in v]
    print(f"  {len(PRIORITY_COLORS)} priority characters (manual colors)")
    print(f"  {len(no_color_ids)} characters need auto-generated colors")

    # Apply priority colors first
    added_priority = 0
    for char_id, (color, color_dark, label) in PRIORITY_COLORS.items():
        if char_id in chars and "display" not in chars[char_id]:
            chars[char_id]["display"] = {
                "color":             color,
                "color_dark":        color_dark,
                "opacity_narration": 0.4,
                "opacity_speech":    1.0,
                "label":             label,
            }
            added_priority += 1

    # Auto-generate for the rest
    remaining = [cid for cid in chars if "display" not in chars[cid]]
    auto_colors = generate_auto_colors(remaining)
    added_auto = 0
    for char_id, (color, color_dark) in auto_colors.items():
        name = chars[char_id].get("Name", char_id.lstrip("@").title())
        chars[char_id]["display"] = {
            "color":             color,
            "color_dark":        color_dark,
            "opacity_narration": 0.4,
            "opacity_speech":    1.0,
            "label":             name,
        }
        added_auto += 1

    with open(CHARS_FILE, "w", encoding="utf-8") as fh:
        json.dump(chars, fh, ensure_ascii=False, indent=2)

    print(f"  Added priority: {added_priority}, auto-generated: {added_auto}")
    print(f"  Saved -> {CHARS_FILE.name}\n")

    if args.colors_only:
        print("--colors-only flag set. Done.")
        return

    # ── Step 2: Build name → @id map ────────────────────────────────────
    name_map = build_name_map(chars)
    print(f"Name map built: {len(name_map)} entries\n")

    # ── Step 3: Process subparva files ───────────────────────────────────
    print("=== Step 2: Tagging dialogues ===")

    if args.parva:
        pattern = str(STORY_DIR / f"parva_{args.parva:02d}_*" / "subparva_*.json")
    else:
        pattern = str(STORY_DIR / "parva_*" / "subparva_*.json")

    subparva_files = sorted(
        p for p in glob.glob(pattern)
        if not p.endswith("_tagged.json")
    )

    print(f"  Found {len(subparva_files)} subparva file(s) to process")
    total_tagged = 0

    for sp_file in subparva_files:
        sp_path = Path(sp_file)
        out_path = process_subparva(sp_path, chars, name_map)
        rel = out_path.relative_to(BASE)
        print(f"  OK  {rel}")
        total_tagged += 1

    print(f"\nDone. Tagged {total_tagged} subparva files.")

if __name__ == "__main__":
    main()
