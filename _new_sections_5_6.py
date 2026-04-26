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
    r"([A-Z][A-Za-z\-']{0,25}(?:\s+[A-Za-z][A-Za-z\-']{0,20}){0,3})"
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
    """
    candidates = [before]
    for sep in (". ", "! ", "? "):
        idx = before.rfind(sep)
        if idx >= 0:
            candidates.append(before[idx + 2:])

    for fragment in candidates:
        m = _ATTRIB_VERB_RE.search(fragment.rstrip())
        if not m:
            continue
        raw_name = m.group(1).strip()
        if raw_name.lower() in _NON_NAME_WORDS:
            continue
        offset      = before.rfind(fragment)
        narr_prefix = before[:offset + m.start()].rstrip()
        attrib_text = before[offset + m.start():].rstrip()
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
