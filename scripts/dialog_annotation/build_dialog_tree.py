"""Build flat paragraph-based dialog structure from volume TXT files.

Each paragraph is annotated with its quote depth and inline speech segments.
Multi-paragraph continuations preserve depth across paragraphs.
Speaker attribution tracks who is narrating/speaking at each depth.

Output: output/dialogs/volume_N/chapter_NNNN.json

Paragraph format:
{
  "p": 1,
  "depth": 2,            // nesting depth: 0=top, 1=', 2=", 3=' etc.
  "stack": ["'", "\""],   // active quote stack entering this paragraph
  "text": "full paragraph text",
  "segments": [
    {"type": "narration", "depth": 2, "speaker": "@vaishampayana",
     "text": "The king said, "},
    {"type": "speech", "q": "'", "depth": 3, "speaker": "@yudhishthira",
     "text": "\u2018O lady!...\u2019"},
    {"type": "narration", "depth": 2, "speaker": "@vaishampayana",
     "text": " Having said this..."}
  ]
}
"""
import json, re, os

VOLUMES_DIR = 'output/volumes'
OUTPUT_DIR  = 'output/dialogs'

# Curly quote characters
OQ1 = '\u2018'   # ' opening single
CQ1 = '\u2019'   # ' closing single
OQ2 = '\u201c'   # " opening double
CQ2 = '\u201d'   # " closing double

CHAPTER_RE = re.compile(r'^--- Chapter (\d+)\((\d+)\) \[(\d+)\] ---$')
SECTION_RE = re.compile(r'^_{4,}')

# --- Speaker attribution ---
# Regex to detect "X said," / "X said:" / "X told him," etc.
# Allows leading whitespace and/or curly quotes before the speaker name
ATTR_RE = re.compile(
    r'^\s*[' + OQ1 + OQ2 + r']*\s*'    # optional leading whitespace/quotes
    r'([\w][\w\s\'-]*?)\s+'              # speaker name
    r'(said|told|continued|asked|replied|spoke|resumed|answered|exclaimed|retorted|addressed)'
    r'(?:\s+(?:(?:to|before)\s+)?(?:him|her|them|it|his\s+\w+|her\s+\w+|the\s+\w+))?'
    r'\s*[,:]',
    re.IGNORECASE
)

# False-positive attribution patterns to skip (must match FULL speaker name)
ATTR_SKIP = re.compile(
    r'^(thus|as|he did as he had been|when he thus|then [\w]+ saluted.*|having been thus|been thus)$',
    re.IGNORECASE
)

# Words that are NOT speaker names but may precede them
# "Then Utanka said," → strip "Then", resolve "Utanka"
ATTR_FIRST_SKIP = {
    'thus', 'then', 'having', 'being', 'been', 'on', 'after', 'before', 'when',
    'while', 'as', 'but', 'so', 'yet', 'also', 'however', 'saying',
    'in', 'at', 'with', 'from', 'into', 'through', 'since', 'once',
    'thereupon', 'thereafter', 'therefore', 'meanwhile', 'again',
    'and', 'or', 'nor',
}

# Pronouns that cannot be resolved to a character → mark as "unknown"
PRONOUN_SET = {'he', 'she', 'they', 'it', 'one', 'i', 'we',
               'the other', 'one of them'}

# Trailing attribution: "X said," / "X told him," at END of segment text
# Used when leading ATTR_RE doesn't match (attribution is mid-sentence)
TRAILING_ATTR_RE = re.compile(
    r'^((?:(?:the|his|her)\s+)?[\w][\w\'-]*(?:\s+[\w][\w\'-]*)?)\s+'
    r'(said|told|replied|asked|spoke|answered|exclaimed|continued|resumed|retorted|addressed)'
    r'(?:\s+(?:(?:to|before)\s+)?(?:him|her|them|it|his\s+[\w]+|her\s+[\w]+|the\s+[\w]+))?'
    r'\s*[,:]\s*$',
    re.IGNORECASE
)

# Known narrator name → @id mapping (canonical + variants)
NARRATOR_MAP = {
    'souti': '@ugrasrava',
    'suta': '@ugrasrava',
    'the suta': '@ugrasrava',
    'vaishampayana': '@vaishampayana',
    'vaishmapayana': '@vaishampayana',
    'vaisampayana': '@vaishampayana',
    'sanjaya': '@sanjaya',
    'janamejaya': '@janamejaya',
    'janemejaya': '@janamejaya',
    'shounaka': '@shounaka',
    'the sages': '@sages',
}

# Frame-level default narrators
# depth 0 → Souti narrates to sages (even when his quotes are missing)
# depth 1 → usually Vaishampayana (set dynamically by attribution detection)
FRAME_DEFAULTS = {
    0: '@ugrasrava',   # Souti is the outer narrator
}

# Verb → alignment mapping for conversation-style rendering
# 'said' family → 'left' (initiating), 'replied' family → 'right' (responding)
VERB_ALIGNMENT = {
    'said': 'left', 'told': 'left', 'spoke': 'left', 'continued': 'left',
    'asked': 'left', 'exclaimed': 'left', 'resumed': 'left', 'addressed': 'left',
    'replied': 'right', 'answered': 'right', 'retorted': 'right',
}


def load_character_names():
    """Build lowercase name → @id map from characters.json."""
    chars_path = os.path.join('output', 'json', 'characters.json')
    if not os.path.exists(chars_path):
        return dict(NARRATOR_MAP)

    name_map = dict(NARRATOR_MAP)
    chars = json.load(open(chars_path, encoding='utf-8'))
    for cid, info in chars.items():
        if not cid.startswith('@'):
            continue
        name = info.get('Name', '')
        if name:
            name_map[name.lower()] = cid
        for alias in info.get('Alias_names', []):
            if alias:
                name_map[alias.lower()] = cid
    return name_map


def _clean_speaker_name(speaker_name):
    """Strip leading/trailing adverbs from speaker name: 'Then Utanka' → 'Utanka'."""
    words = speaker_name.split()
    # Strip leading skip words
    while words and words[0].lower() in ATTR_FIRST_SKIP:
        words = words[1:]
    # Strip trailing skip words: "Janamejaya then" → "Janamejaya"
    while words and words[-1].lower() in ATTR_FIRST_SKIP:
        words = words[:-1]
    return ' '.join(words) if words else ''


def resolve_speaker(text, name_map):
    """Extract speaker name from attribution text like 'Vaishampayana said,'
    Returns (@id_or_label, speaker_label, verb) or (None, None, None)."""
    m = ATTR_RE.match(text)
    if not m:
        return None, None, None
    speaker_name = m.group(1).strip()
    verb = m.group(2).lower()
    # Skip false positives like "Thus asked," "As asked,"
    if ATTR_SKIP.match(speaker_name):
        return None, None, None
    # Strip leading adverbs: "Then Utanka" → "Utanka"
    speaker_name = _clean_speaker_name(speaker_name)
    if not speaker_name:
        return None, None, None
    # Pronouns → unknown
    if speaker_name.lower() in PRONOUN_SET:
        return 'unknown', speaker_name, verb
    speaker_id = name_map.get(speaker_name.lower())
    if not speaker_id:
        # Use lowercase label as fallback ID for unresolved speakers
        speaker_id = speaker_name.lower().replace(' ', '_')
    return speaker_id, speaker_name, verb


def resolve_trailing_speaker(text, name_map):
    """Check if text ENDS with attribution like 'X said,' or 'the preceptor told him,'.
    Returns (@id_or_label, speaker_label, verb) or (None, None, None)."""
    text = text.rstrip()
    if not (text.endswith(',') or text.endswith(':')):
        return None, None, None

    # Extract the last clause: try progressively shorter tails
    # 1. After last sentence-ending punctuation
    tail = text
    for sep in ['. ', '! ', '? ', '; ']:
        idx = text.rfind(sep)
        if idx >= 0 and len(text) - idx > 10:
            tail = text[idx + len(sep):]
            break

    # 2. After last inner comma (skip the trailing comma itself)
    #    "Thus addressed, the preceptor replied," → "the preceptor replied,"
    trimmed = tail.rstrip(', :')
    cidx = trimmed.rfind(', ')
    if cidx >= 0:
        candidate = trimmed[cidx + 2:] + tail[len(trimmed):]
        if len(candidate.strip()) < 80:
            tail = candidate

    # 3. Also try after "and " for "stood before him and said,"
    and_idx = tail.lower().rfind(' and ')
    if and_idx >= 0:
        candidate = tail[and_idx + 5:]
        if candidate.strip():
            m2 = TRAILING_ATTR_RE.match(candidate.strip())
            if m2:
                tail = candidate

    tail = tail.strip()
    m = TRAILING_ATTR_RE.match(tail)
    if not m:
        return None, None, None

    speaker_name = m.group(1).strip()
    verb = m.group(2).lower()
    if ATTR_SKIP.match(speaker_name):
        return None, None, None
    speaker_name = _clean_speaker_name(speaker_name)
    if not speaker_name:
        return None, None, None
    if speaker_name.lower() in PRONOUN_SET:
        return 'unknown', speaker_name, verb
    speaker_id = name_map.get(speaker_name.lower())
    if not speaker_id:
        speaker_id = speaker_name.lower().replace(' ', '_')
    return speaker_id, speaker_name, verb


def assign_speakers(paragraphs, name_map):
    """Post-process: assign speaker, alignment, and confirmation to every segment.

    Frame tracking:
    - depth 0 narrator = Souti (@ugrasrava) always
    - When we see "X said," at depth D, the next depth (D+1) has speaker X
    - The narrator at depth D is whoever was last set for that depth

    Alignment (for conversation-style rendering):
    - narration/close → 'center'
    - speech after 'said/spoke/asked/continued/exclaimed' → 'left'
    - speech after 'replied/answered' → 'right'

    Confirmation:
    - speaker_confirmed = True for narration (frame narrator always correct)
    - speaker_confirmed = True for speech if explicit attribution set the
      speaker at this depth and depth hasn't dropped below since
    - speaker_confirmed = False otherwise (inherited, may need manual review)
    """
    narrator_at = {0: FRAME_DEFAULTS.get(0, '@ugrasrava')}
    verb_at = {}        # depth → last verb used in attribution targeting that depth
    confirmed_at = {}   # depth → True while attribution is still fresh
    prev_depth = 0

    for para in paragraphs:
        for seg in para['segments']:
            d = seg.get('depth', 0)
            stype = seg.get('type', 'narration')

            # When depth drops, invalidate confirmation for all higher depths
            if d < prev_depth:
                for cd in list(confirmed_at):
                    if cd > d:
                        del confirmed_at[cd]

            # Determine the speaker for this segment
            if d in narrator_at:
                seg['speaker'] = narrator_at[d]
            elif d > 0:
                for check_d in range(d, -1, -1):
                    if check_d in narrator_at:
                        seg['speaker'] = narrator_at[check_d]
                        break
                else:
                    seg['speaker'] = '@ugrasrava'
            else:
                seg['speaker'] = '@ugrasrava'

            # Detect attribution: "X said," → sets narrator at (d+1)
            speaker_id, speaker_label, verb = resolve_speaker(seg['text'], name_map)
            if speaker_id:
                narrator_at[d + 1] = speaker_id
                seg['introduces'] = speaker_id
                seg['introduces_label'] = speaker_label
                if verb:
                    verb_at[d + 1] = verb
                confirmed_at[d + 1] = True

            # Check TRAILING attribution if no leading match
            if not speaker_id:
                t_id, t_label, t_verb = resolve_trailing_speaker(seg['text'], name_map)
                if t_id:
                    narrator_at[d + 1] = t_id
                    seg['introduces'] = t_id
                    seg['introduces_label'] = t_label
                    if t_verb:
                        verb_at[d + 1] = t_verb
                    confirmed_at[d + 1] = True

            # Alignment
            if stype in ('narration', 'close'):
                seg['alignment'] = 'center'
                seg['conversation'] = 'narration'
            elif stype == 'speech':
                v = verb_at.get(d, 'said')
                seg['alignment'] = VERB_ALIGNMENT.get(v, 'left')
                if v in ('replied', 'answered', 'retorted'):
                    seg['conversation'] = 'replied'
                else:
                    seg['conversation'] = 'said'

            # Speaker confirmation
            if seg.get('introduces'):
                seg['speaker_confirmed'] = True
            elif stype in ('narration', 'close'):
                seg['speaker_confirmed'] = True
            elif stype == 'speech':
                seg['speaker_confirmed'] = bool(confirmed_at.get(d))
            else:
                seg['speaker_confirmed'] = True

            prev_depth = d

    return paragraphs


def parse_chapters_from_volume(vol_path):
    """Split a volume TXT file into chapters with their paragraphs."""
    chapters = []
    current = None
    with open(vol_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            m = CHAPTER_RE.match(line)
            if m:
                if current:
                    chapters.append(current)
                current = {
                    'global': int(m.group(1)),
                    'local':  int(m.group(2)),
                    'shlokas': int(m.group(3)),
                    'paragraphs': []
                }
            elif current is not None:
                if line.strip() and not SECTION_RE.match(line):
                    current['paragraphs'].append(line)
    if current:
        chapters.append(current)
    return chapters


def segment_paragraph(text, incoming_stack):
    """Parse a single paragraph into segments, tracking quote depth.

    Args:
        text: paragraph text
        incoming_stack: quote stack from previous paragraphs ["'", '"']

    Returns:
        (segments, outgoing_stack)
    """
    stack = list(incoming_stack)
    segments = []
    buf = []

    i = 0
    n = len(text)

    # Detect frame-establishing quotes at paragraph start.
    # Opening quotes at the very beginning re-declare the nesting frame.
    # Case 1: They match the incoming stack prefix → classic continuation.
    # Case 2: They DON'T match (accumulated stack drift) → RESET stack to
    #         these quotes. This fixes the depth-spiral bug in chapters like
    #         1865 where repeated close-reopen patterns across paragraphs
    #         cause the stack to grow unboundedly.
    j = 0
    cont = []
    while j < n and text[j] in (OQ1, OQ2):
        cont.append("'" if text[j] == OQ1 else '"')
        j += 1

    if cont:
        # Reset stack to the opening quote sequence (frame re-establishment)
        stack = list(cont)
        buf.extend(text[:j])
        i = j

    # Track which stack depths have an active speech opening.
    speech_depths = set()
    # All depths from stack (whether inherited or reset) are active speech
    for d in range(1, len(stack) + 1):
        speech_depths.add(d)

    while i < n:
        ch = text[i]

        # Opening quote — flush buffer, push new depth
        if ch in (OQ1, OQ2):
            t = ''.join(buf)
            if t:
                cur_depth = len(stack)
                if cur_depth in speech_depths:
                    segments.append({
                        'type': 'speech',
                        'q': stack[-1] if stack else '?',
                        'depth': cur_depth,
                        'text': t
                    })
                else:
                    segments.append({
                        'type': 'narration',
                        'depth': cur_depth,
                        'text': t
                    })
            buf = [ch]
            q = "'" if ch == OQ1 else '"'
            stack.append(q)
            speech_depths.add(len(stack))
            i += 1
            continue

        # Closing quote
        if ch in (CQ1, CQ2):
            buf.append(ch)
            t = ''.join(buf)
            cur_depth = len(stack)
            if t:
                if cur_depth in speech_depths:
                    segments.append({
                        'type': 'speech',
                        'q': stack[-1] if stack else '?',
                        'depth': cur_depth,
                        'text': t
                    })
                else:
                    # Closing a quote from previous paragraph/segment
                    pre = t[:-1]
                    if pre:
                        segments.append({
                            'type': 'narration',
                            'depth': cur_depth,
                            'text': pre
                        })
                    segments.append({
                        'type': 'close',
                        'depth': cur_depth,
                        'text': ch
                    })
            buf = []
            speech_depths.discard(cur_depth)
            if stack:
                stack.pop()
            i += 1
            continue

        buf.append(ch)
        i += 1

    # Flush remaining
    t = ''.join(buf)
    if t:
        cur_depth = len(stack)
        if cur_depth in speech_depths:
            segments.append({
                'type': 'speech',
                'q': stack[-1] if stack else '?',
                'depth': cur_depth,
                'text': t
            })
        else:
            segments.append({
                'type': 'narration',
                'depth': cur_depth,
                'text': t
            })

    # Merge adjacent segments of same type and depth
    merged = []
    for seg in segments:
        if (merged
                and merged[-1]['type'] == seg['type']
                and merged[-1]['depth'] == seg['depth']
                and merged[-1].get('q') == seg.get('q')):
            merged[-1]['text'] += seg['text']
        else:
            merged.append(seg)

    return merged, stack


def build_flat_paragraphs(paragraphs, name_map):
    """Parse all paragraphs into flat annotated list with depth and speaker tracking."""
    result = []
    stack = []  # carries across paragraphs

    for idx, text in enumerate(paragraphs):
        entry_stack = list(stack)
        segments, stack = segment_paragraph(text, stack)

        # Base depth = the incoming stack depth (context this paragraph lives in)
        base_depth = len(entry_stack)

        result.append({
            'p': idx + 1,
            'depth': base_depth,
            'stack': entry_stack,
            'text': text,
            'segments': segments
        })

    # Post-process: assign speakers to all segments
    assign_speakers(result, name_map)

    return result


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    total = 0

    # Load character name → @id mapping
    name_map = load_character_names()
    print(f'Loaded {len(name_map)} character name mappings')

    for vol in range(1, 11):
        vol_path = os.path.join(VOLUMES_DIR, f'volume_{vol}_chapters.txt')
        if not os.path.exists(vol_path):
            continue

        chapters = parse_chapters_from_volume(vol_path)
        vol_dir = os.path.join(OUTPUT_DIR, f'volume_{vol}')
        os.makedirs(vol_dir, exist_ok=True)

        for ch in chapters:
            paras = build_flat_paragraphs(ch['paragraphs'], name_map)

            out = {
                'chapter': ch['global'],
                'local':   ch['local'],
                'shlokas': ch['shlokas'],
                'paragraphs': paras
            }
            path = os.path.join(vol_dir, f'chapter_{ch["global"]:04d}.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            total += 1

        print(f'Volume {vol}: {len(chapters)} chapters')

    print(f'\nTotal: {total} dialog files -> {OUTPUT_DIR}/')

    # Generate unconfirmed speakers report
    generate_report(OUTPUT_DIR)


def generate_report(dialog_dir):
    """Generate report of unconfirmed speech segments for manual review."""
    report_dir = os.path.join('output', 'reports')
    os.makedirs(report_dir, exist_ok=True)

    lines = []
    unconfirmed = 0
    unresolved_ids = {}   # speaker_id (no @) → count
    chapter_stats = {}    # chapter → count of unconfirmed

    for vol in range(1, 11):
        vol_dir = os.path.join(dialog_dir, f'volume_{vol}')
        if not os.path.isdir(vol_dir):
            continue
        for fname in sorted(os.listdir(vol_dir)):
            if not fname.endswith('.json'):
                continue
            data = json.load(open(os.path.join(vol_dir, fname), encoding='utf-8'))
            ch = data['chapter']

            for para in data['paragraphs']:
                for seg in para['segments']:
                    sp = seg.get('speaker', '?')
                    stype = seg.get('type', 'narration')

                    # Track unresolved speaker IDs (no @ prefix)
                    if sp and not sp.startswith('@'):
                        unresolved_ids[sp] = unresolved_ids.get(sp, 0) + 1

                    # Collect unconfirmed speech segments
                    if stype == 'speech' and not seg.get('speaker_confirmed', True):
                        unconfirmed += 1
                        chapter_stats[ch] = chapter_stats.get(ch, 0) + 1
                        excerpt = seg['text'][:120].replace('\n', ' ')
                        lines.append(
                            f"Ch {ch:4d}  p{para['p']:3d}  d{seg['depth']}  "
                            f"[{seg.get('alignment', '?'):5s}]  "
                            f"speaker={sp:25s}  "
                            f"{excerpt}"
                        )

    # Write text report
    report_path = os.path.join(report_dir, 'unconfirmed_speakers.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Unconfirmed Speech Segments Report\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total unconfirmed speech segments: {unconfirmed}\n")
        f.write(f"Chapters with unconfirmed speech: {len(chapter_stats)}\n")
        f.write(f"Unresolved speaker IDs (not in characters.json): {len(unresolved_ids)}\n\n")

        f.write("These segments have speakers assigned by INHERITANCE from previous context.\n")
        f.write("The assigned speaker may be WRONG — review and fix manually.\n\n")

        if unresolved_ids:
            f.write("--- Unresolved Speaker IDs (need adding to characters.json) ---\n")
            for sp, cnt in sorted(unresolved_ids.items(), key=lambda x: -x[1]):
                f.write(f"  {sp:30s}  segments={cnt}\n")
            f.write("\n")

        f.write("--- Top Chapters by Unconfirmed Count ---\n")
        for ch, cnt in sorted(chapter_stats.items(), key=lambda x: -x[1])[:30]:
            f.write(f"  Chapter {ch:4d}: {cnt} unconfirmed speech segments\n")
        f.write("\n")

        f.write("--- All Unconfirmed Speech Segments ---\n")
        f.write("(Review each: the speaker may be wrong)\n\n")
        for line in lines:
            f.write(line + '\n')

    print(f"\nReport: {report_path}")
    print(f"  Unconfirmed speech: {unconfirmed}")
    print(f"  Unresolved IDs: {len(unresolved_ids)}")


if __name__ == '__main__':
    main()
