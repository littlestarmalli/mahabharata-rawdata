"""TXT text extraction for the Mahabharata Complete_text_mahabharat.txt.

Produces output that mirrors the PDF pipeline format:
    - volume_N_chapters.txt : '--- Chapter N ---' markers + one paragraph per line
    - volume_N_footnotes.txt: '--- Section N ---' and '--- Chapters X to Y ---' markers
    - volume_N_toc.txt      : section list + per-section parva description

Chapter numbers are sequential across the whole book (Vol 1 = Chapter 1..N,
Vol 2 continues the count, etc.), matching the PDF output.
"""

import re
import os
from text_to_volumes.config import TXT_FILENAME, NUM_VOLUMES


# ---------------------------------------------------------------------------
# Legitimate-hyphen whitelist
# ---------------------------------------------------------------------------
# Intra-word hyphens in the source TXT have two causes:
#   1. Real compound words (great-souled, twice-born, evil-minded, ...).
#   2. OCR line-wrap artifacts that survived flattening (be-ing, wor-shipped,
#      ele-gant, begin-ning, ...).
# The PDF reference at output/volumes/*.txt preserves only the legitimate
# compounds, so we use it as the ground-truth whitelist.  Anything not in
# that whitelist is assumed to be an OCR break and its hyphen is stripped.
_HYPHEN_WHITELIST_PATH = os.path.join(
    os.path.dirname(__file__), 'hyphen_whitelist.txt'
)
try:
    with open(_HYPHEN_WHITELIST_PATH, 'r', encoding='utf-8') as _wf:
        _HYPHEN_WHITELIST = {
            w.strip().lower() for w in _wf if w.strip()
        }
except FileNotFoundError:
    _HYPHEN_WHITELIST = set()

# Suffix morphemes that ALWAYS indicate a legitimate compound even if the
# specific word is not in the corpus whitelist.  Example: "silver-hued" may
# appear only once and not be in the sampled whitelist, but "-hued" is a
# recognisable compound suffix and the hyphen must be kept.
_COMPOUND_SUFFIXES = {
    'souled', 'armed', 'born', 'minded', 'hearted', 'eyed', 'waisted',
    'controlled', 'stricken', 'like', 'tipped', 'pointed', 'lived',
    'handed', 'footed', 'mouthed', 'headed', 'chested', 'shouldered',
    'legged', 'winged', 'haired', 'skinned', 'nosed', 'cheeked',
    'bodied', 'faced', 'hued', 'shaped', 'sighted', 'spoken',
    'wishers', 'wisher', 'in-law', 'law', 'dwelling', 'dwellers',
    'dweller', 'smiling', 'smelling', 'looking', 'stricken', 'bearing',
    'grandfather', 'grandmother', 'grandchild', 'grandchildren',
    'grandson', 'granddaughter',
}

# Prefix morphemes that always indicate a legitimate compound.
_COMPOUND_PREFIXES = {
    'great', 'mighty', 'twice', 'self', 'evil', 'sweet', 'slender',
    'god', 'lotus', 'black', 'white', 'red', 'gold', 'silver', 'iron',
    'grief', 'non', 'un', 're', 'co', 'well', 'ill', 'pre', 'sub',
    'super', 'semi', 'ex', 'anti', 'pro', 'inter', 'intra', 'fore',
    'large', 'small', 'long', 'short', 'tall', 'high', 'low', 'broad',
    'narrow', 'deep', 'soft', 'hard', 'pure', 'first', 'last', 'new',
    'old', 'half', 'full', 'sharp', 'smoke', 'water', 'fire', 'wind',
    'cloud', 'heaven', 'earth', 'forest', 'mountain', 'sea', 'river',
    'man', 'men', 'woman', 'women', 'horse', 'lion', 'tiger', 'bull',
    'daughter', 'daughters', 'son', 'sons', 'brother', 'brothers',
    'sister', 'sisters', 'mother', 'mothers', 'father', 'fathers',
    'thousand', 'hundred', 'twenty', 'thirty', 'forty', 'fifty',
    'sixty', 'seventy', 'eighty', 'ninety', 'twelve', 'thirteen',
    'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen',
    'nineteen', 'twenty-one', 'single', 'double', 'triple',
    'ever', 'never', 'peace', 'war', 'arm', 'hand', 'foot', 'heart',
    'soul', 'mind', 'life', 'death', 'far', 'near',
}


def _preserve_hyphen(left, right):
    """Return True if ``left-right`` should keep its hyphen."""
    lw = left.lower()
    rw = right.lower()
    full = f"{lw}-{rw}"
    if full in _HYPHEN_WHITELIST:
        return True
    if lw in _COMPOUND_PREFIXES:
        return True
    if rw in _COMPOUND_SUFFIXES:
        return True
    # Plural variants like "great-souled" vs "great-souleds" should match
    # via the whitelist; no extra rule needed here.
    return False


_INTRAWORD_HYPHEN_RE = re.compile(r'([A-Za-z]+)-([A-Za-z]+)')


def _dehyphenate(text):
    """Strip OCR line-wrap hyphens from merged paragraphs.

    Runs AFTER paragraph reconstruction so that the whole hyphenated token
    is visible.  Preserves legitimate compounds via the whitelist and the
    morpheme fallback rules.
    """
    def _replace(m):
        left, right = m.group(1), m.group(2)
        if _preserve_hyphen(left, right):
            return f"{left}-{right}"
        return f"{left}{right}"
    # Apply twice to handle chains like "di-vi-sions" (rare but possible).
    text = _INTRAWORD_HYPHEN_RE.sub(_replace, text)
    text = _INTRAWORD_HYPHEN_RE.sub(_replace, text)
    return text


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Volume marker line. Accepts:
#   "Volume 3"
#   "Volume 8 (Sections 78 to 86)"   <- trailing parenthetical
# The stripped line must START with "Volume N" where the only thing that may
# follow is whitespace + "(...)".  We refuse matches where more free-form
# prose follows (those are in-text mentions, not volume headers).
VOLUME_LINE_RE = re.compile(r'^Volume (\d{1,2})(?:\s*\(.*\))?\s*$')

# Some volume headers are OCR-corrupted: "Volume 10" comes through as
# "Volume 70" because the leading '1' is mis-read as '7'.  We translate
# that single case on the fly (only when we have not yet captured vol 10).
_OCR_VOLUME_MAP = {70: 10}

# Section header patterns.  Two forms appear in the source:
#   1) Title case with parva name on the same line (volumes 1-6):
#          "Section Sixty-One Jambukhanda-Vinirmana Parva"
#   2) ALL CAPS form, often without a parva name on the same line (volumes 7+):
#          "SECTION SEVENTY-THREE"
#          "SECTION SEVENTY-THREE KARNA-VADHA PARVA"
#      The parva name, when absent, appears one or two lines later, often
#      badly OCR-mangled ("K A R N A - VA D H A  PA RVA").  We accept the
#      header line by itself for these.
#
# We try the title-case pattern first.  Only if a volume yields no chapters
# under that pattern do we fall back to the ALL-CAPS pattern, because the
# ALL-CAPS form is also used in front-matter tables of contents in
# volumes 3-6 and would cause false-positive section headers there.
SECTION_WORDS = (
    r'One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|'
    r'Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|'
    r'Twenty|Thirty|Forty|Fifty|Sixty|Seventy|Eighty|Ninety|Hundred'
)
SECTION_HEADER_TITLECASE_RE = re.compile(
    rf'^Section\s+((?:{SECTION_WORDS})(?:[- ](?:{SECTION_WORDS}))?)\s+(.+?Parva.*)$'
)
_SECTION_WORDS_UPPER = SECTION_WORDS.upper()
SECTION_HEADER_UPPER_RE = re.compile(
    rf'^SECTION\s+((?:{_SECTION_WORDS_UPPER})(?:[- ](?:{_SECTION_WORDS_UPPER}))?)'
    rf'(?::?\s+(.+?PARVA.*))?$'
)

# Standalone chapter number line.  Forms seen in the source:
#   Volumes 1-2 : just a number, e.g. "41"
#   Volumes 3-4 : number plus parva-relative number in parens, e.g. "377(80)"
#   Volumes 5-6 : same as above, but prefixed with "CHAPTER ", e.g. "CHAPTER 861(1)"
#   Volumes 7+  : prefixed with title-case "Chapter ", e.g. "Chapter 1579(251)".
#                 (The all-caps "CHAPTER" form does not appear there.)
# The "Chapter N(M): K shlokas" variant is a TOC / metadata line, not a
# chapter start -- the trailing ":" / " shlokas" distinguishes it.
# Also tolerate OCR/layout variants:
#   "226 (1)"       -- whitespace between number and paren
#   "272(47)48"     -- trailing footnote-ref digits fused after the paren
CHAPTER_NUM_RE = re.compile(
    r'^(?:CHAPTER\s+|Chapter\s+)?(\d{1,4})(?:\s*\(\d{1,4}\)\d{0,4})?$'
)

# Shloka-count metadata line in section descriptions, e.g.
#   "Chapter 377(80): 733 shlokas"
# These are noise and must be removed (spec Step 2 / Step 13).
SHLOKA_COUNT_RE = re.compile(
    r'^Chapter\s+\d+(?:\(\d+\))?:\s+\d+\s+shlokas\.?$',
    re.IGNORECASE,
)

# Volume boundary: everything after "Acknowledgements" belongs to back matter
# (copyright, praise, credits) and must not be treated as story content
# (spec Step 3).
ACKNOWLEDGEMENTS_RE = re.compile(r'^\s*acknowledg(?:e)?ments\s*$', re.IGNORECASE)

# Another back-matter boundary used in volumes 7-10: the story body ends
# with a line like "This ends Shalya Parva." / "This ends the Souptika
# Parva.", after which the source dumps a footnote definition block that
# re-lists every chapter header.  Treating that block as story would double
# every chapter, so we truncate there too.
PARVA_END_RE = re.compile(
    r'^\s*This ends(?:\s+the)?\s+[A-Z][A-Za-z -]*Parva\s*\.?\s*$'
)

# Inline footnote reference: a digit (1-3) directly attached to a word or
# punctuation, not preceded or followed by another digit / comma-digit.
FOOTNOTE_REF_RE = re.compile(
    r'(?<![\d,])'
    r'([A-Za-z\u2018\u2019\u201c\u201d\)\].,;:!\?])'
    r'(\d{1,3})'
    r'(?![\d,])'
)

# After wrapping footnote digits in {N}, the reference may sit AFTER the
# sentence punctuation because the source places it there (e.g. "Nara,201").
# The PDF reference keeps the footnote BEFORE the punctuation ("Nara{201},").
# This rule swaps any "<punct>{<digits>}" into "{<digits>}<punct>".
FOOTNOTE_AFTER_PUNCT_RE = re.compile(r'([,.;:!?])(\{\d{1,3}\})')

# Similar swap for a closing quote that sits between the word and its
# footnote: "Jaya’{1}" -> "Jaya{1}’".  Matches PDF reference ordering.
FOOTNOTE_AFTER_QUOTE_RE = re.compile(r'([\u2019\u201d])(\{\d{1,3}\})')


def _normalize_footnote_refs(text):
    text = FOOTNOTE_REF_RE.sub(lambda m: f"{m.group(1)}{{{m.group(2)}}}", text)
    text = FOOTNOTE_AFTER_QUOTE_RE.sub(lambda m: f"{m.group(2)}{m.group(1)}", text)
    text = FOOTNOTE_AFTER_PUNCT_RE.sub(lambda m: f"{m.group(2)}{m.group(1)}", text)
    return text


def _normalize_line(line):
    """Step 1 (STRICT) text normalization.

    Allowed:
      - Context-aware replacement of U+FFFD ('\ufffd'):
          * letter + \ufffd + {s,t,d,m,ll,ve,re,S,T,D,M}  -> '\u2019 (possessive / contraction)
          * letter + \ufffd + letter (any other)          -> '\u2014 (em-dash)
          * (start|space) + \ufffd + UPPER                -> '\u2018 (opening quote)
          * \ufffd + (space|punct|EOL)                    -> '\u2019 (closing quote)
          * any remaining \ufffd                          -> '\u2019 (safe fallback)
      - Restoration of lost 'fl' ligature that the source encoded as '?'
        inside a word (e.g. '?owers' -> 'flowers', 'af?icted' -> 'afflicted').
        Only applied when '?' sits between word-internal positions so
        genuine question marks are never touched.
      - Collapse runs of spaces to a single space
      - Strip trailing whitespace

    NOT allowed: touching any other quote / apostrophe / punctuation.
    """
    # Context-aware U+FFFD fix.
    # 1. letter + � + contraction-suffix  -> ’ (U+2019) possessive / contraction.
    #    The suffix must be followed by a non-letter (punct, space, or even a
    #    footnote digit like "Pritha\ufffds28" -> "Pritha’s28").  We use
    #    (?![A-Za-z]) rather than \b so that a following digit still counts
    #    as the end of the contraction.
    line = re.sub(
        r'(\w)\ufffd(ll|ve|re|s|t|d|m|S|T|D|M)(?![A-Za-z])',
        '\\1\u2019\\2', line,
    )
    # 2. letter + � + letter (NOT a contraction, handled by rule 1)
    #    -> em-dash.  This captures "Pandavas\ufffdthe" -> "Pandavas—the",
    #    "ambrosia\ufffdlike" -> "ambrosia—like", etc.  Restricted to
    #    ASCII letters on both sides so that "Jaya\ufffd1" (closing quote
    #    followed by a footnote digit) does NOT turn into an em-dash.
    line = re.sub(r'([A-Za-z])\ufffd([A-Za-z])', '\\1\u2014\\2', line)
    # 3a. (opening single quote) + � + UPPERCASE  -> “ (U+201C) opening
    #     DOUBLE quote.  The outer speech uses a single curly quote, and a
    #     nested utterance opens with a double curly quote, so the correct
    #     restoration for "‘�O Sanjaya!" is "‘“O Sanjaya!", not "‘‘O".
    line = re.sub(r'(\u2018)\ufffd([A-Z])', '\\1\u201c\\2', line)
    # 3b. (start | whitespace | other quote | open-paren) + � + UPPERCASE
    #     -> ‘ (U+2018) opening nested quote.
    line = re.sub(
        r'(^|[\s\u2019\u201c\u201d\'"\(\[])\ufffd([A-Z])',
        '\\1\u2018\\2', line,
    )
    # 4. � + (space | EOL | punctuation)  -> ’ closing quote
    #     Special-case: � followed directly by the outer closing single
    #     quote ’ means the nested utterance is ending right before the
    #     outer one, so the nested close must be a double curly quote ”.
    line = re.sub(r'\ufffd(?=\u2019)', '\u201d', line)
    line = re.sub(r'\ufffd(\s|$|[.,!?;:\)\]])', '\u2019\\1', line)
    # 5. Safe fallback for any remaining � .
    line = line.replace('\ufffd', '\u2019')

    # Lost 'fl' ligature restoration.  The source encodes the Unicode 'ﬂ'
    # ligature (U+FB02) as literal '?', producing "?owers" / "af?icted" /
    # "in?uence" / "re?ecting".  A '?' that sits between letters (word-start
    # with a letter after, or a letter on both sides) is never a real
    # question mark in this corpus, so we rewrite it to "fl".
    # Word-start case:  ?owers -> flowers
    line = re.sub(r'(?<![A-Za-z0-9])\?(?=[a-z])', 'fl', line)
    # Mid-word case:    af?icted -> afflicted
    line = re.sub(r'(?<=[a-z])\?(?=[a-z])', 'fl', line)

    # Collapse multiple spaces (but preserve tabs).
    line = re.sub(r' {2,}', ' ', line)
    return line.rstrip()


def _is_section_header(line, pattern):
    return pattern.match(line.strip())


def _is_chapter_number(line):
    return CHAPTER_NUM_RE.match(line.strip())


# ---------------------------------------------------------------------------
# Volume splitting
# ---------------------------------------------------------------------------

def split_volumes(input_path):
    """Split the source TXT into per-volume line lists.

    Strict whole-line match ``Volume N`` so we never swallow prose that
    mentions "Volume 7" or treat "Volume 1" as a prefix of "Volume 10".
    Each volume number is captured at most once.
    """
    print("=" * 60)
    print("STEP 1: Splitting text into volumes")
    print("=" * 60)

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    volumes = {}
    current_vol = None
    current_lines = []

    for line in lines:
        m = VOLUME_LINE_RE.match(line.strip())
        if m:
            vol_num = int(m.group(1))
            # Handle OCR-mangled numbers (e.g. 70 -> 10) only if target slot
            # is still empty and we have not yet reached that slot.
            if vol_num in _OCR_VOLUME_MAP:
                mapped = _OCR_VOLUME_MAP[vol_num]
                if mapped not in volumes and mapped != current_vol:
                    vol_num = mapped
            if vol_num in volumes or vol_num == current_vol:
                continue
            if current_vol is not None:
                volumes[current_vol] = current_lines
            current_vol = vol_num
            current_lines = []
            print(f"  Found Volume {vol_num}")
            continue
        if current_vol is not None:
            current_lines.append(line)

    if current_vol is not None and current_vol not in volumes:
        volumes[current_vol] = current_lines

    print(f"  Split into {len(volumes)} volumes")
    return volumes


# ---------------------------------------------------------------------------
# Paragraph formation (semantic reconstruction, spec Steps 4-14)
# ---------------------------------------------------------------------------

# A line that starts with a typical dialogue tag such as
#   'Sanjaya said,
#   "Dhritarashtra said,
#    Souti said,
# must stay on its own line (spec Step 11).  Source page breaks sometimes
# drop the leading indent from such lines, so we also use this pattern as a
# fall-back paragraph-start signal.
_DIALOGUE_TAG_RE = re.compile(
    r'^[\u2018\u2019\u201c\u201d\'"]*'
    r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+'
    r'(?:said|replied|asked|continued|answered|spoke|told|exclaimed|declared|cried|retorted)'
    r'\s*[,:]'
)

# Characters that legitimately end a sentence (used only by the dialogue-tag
# fall-back to decide whether an un-indented "Name said," line is a page-break
# paragraph boundary -- NOT used as a general paragraph splitter).
_SENT_END_CHARS = '.!?\u2019\u201d\'"'

# Paragraph-start indent in the source TXT.  Empirically the file uses a
# 2-space indent for the vast majority of paragraph starts, but volumes 7-10
# also use a 1-space indent (244 lines) for nested-quote continuations like
# " '‘O great king! ...".  Of the 244 one-space lines, 238 begin with an
# opening-quote character and are genuine paragraph starts; the remaining
# 6 are front-matter junk that gets truncated anyway.  Accept either.
_PARA_INDENT_RE = re.compile(r'^(?:\t|[ \u00A0]+)\S')

# Nested-quote paragraph start: a line that begins with TWO OR MORE
# consecutive opening-quote characters (e.g.  '‘'O extender of... )
# indicates a new paragraph at a deeper quotation level.  The source
# sometimes drops the leading indent for such paragraphs at page
# boundaries (we see both indent=0 and indent=2 variants of identical
# patterns in e.g. V3 ch 378).  Accept this as a paragraph-start signal.
_NESTED_QUOTE_START_RE = re.compile(
    r'^[\u2018\u2019\u201c\u201d\'"]{2,}(?=[A-Z]|\u2018|\u201c|\'|")'
)


def _is_shloka_count(line):
    return bool(SHLOKA_COUNT_RE.match(line.strip()))


def _form_paragraphs(block_lines):
    """Rebuild paragraphs from a block of source lines.

    Paragraph boundaries come from POSITION, not text case.  Only two things
    start a new paragraph inside a chapter body:

        1. The first non-blank line of the block (i.e. the line immediately
           after a chapter marker -- spec Step 5, first-paragraph override).
        2. A line whose raw form starts with a tab OR two or more spaces
           (spec Rule 2 -- explicit indentation).

    Every other non-blank line is a WRAPPED CONTINUATION of the previous
    paragraph and is merged into it with a single space (or without a space
    for hyphenated word-breaks and split contractions).  Uppercase first
    letters, opening quotes, and apparent sentence boundaries are NEVER used
    to split paragraphs -- the OCR/PDF source does not preserve that signal
    reliably.
    """
    paragraphs = []

    for raw in block_lines:
        raw_no_nl = raw.rstrip('\n\r')
        if not raw_no_nl.strip():
            continue  # blank line -- ignore, do not break paragraph

        starts_new_para = bool(_PARA_INDENT_RE.match(raw_no_nl))

        line = _normalize_line(raw_no_nl)
        stripped = line.strip()
        if not stripped:
            continue
        if _is_shloka_count(stripped):
            continue  # Step 13: drop shloka-count noise

        # Nested-quote lines (`'‘'O king! ...`) are paragraph starts even
        # when the source dropped the leading indent at a page break.
        if not starts_new_para and _NESTED_QUOTE_START_RE.match(stripped):
            starts_new_para = True

        if not paragraphs:
            # First line of the chapter body always starts a paragraph
            # (spec Step 5, first-paragraph override).
            paragraphs.append(stripped)
            continue

        # Page-break fall-back: if the source lost the leading indent at a
        # page boundary, a line that begins with a dialogue tag
        # ("Souti said,", "Sanjaya said,", ...) and follows a paragraph that
        # ended with a sentence-terminating character is still a paragraph
        # boundary.  This is NOT a case-based heuristic: it keys on the
        # structural dialogue-tag pattern (spec Step 11).
        if not starts_new_para and _DIALOGUE_TAG_RE.match(stripped):
            prev_last = paragraphs[-1].rstrip()[-1:]
            if prev_last in _SENT_END_CHARS:
                starts_new_para = True

        if starts_new_para:
            paragraphs.append(stripped)
            continue

        # --- Continuation: merge with previous paragraph ------------------

        prev = paragraphs[-1]

        # Hyphenated word-break across lines: "commit-\ntee" -> "committee".
        if prev.endswith('-') and not prev.endswith(' -'):
            paragraphs[-1] = prev[:-1] + stripped
            continue

        # Split contraction / possessive: prev ends in a letter, curr starts
        # with 's, 't, 'd, 'm, 'll, 've, 're -> join with no space.
        if re.match(r'^[\u2019\u2018\'](ll|ve|re|s|t|d|m)\b', stripped) \
                and prev[-1:].isalpha():
            paragraphs[-1] = prev + stripped
            continue

        paragraphs[-1] = prev.rstrip() + ' ' + stripped

    # Post-process: strip OCR line-wrap hyphens from the fully assembled
    # paragraphs (spec: a hyphen that is neither at a line end nor part of a
    # known compound is an OCR artifact).
    paragraphs = [_dehyphenate(p) for p in paragraphs]
    # Post-split: when the source lost a line break between two dialogue
    # turns, they end up concatenated on a single line, e.g.
    #     ... I have won.'  'Yudhishthira replied, 'O Soubala! ...
    # Split such paragraphs at the boundary: a sentence-terminating character
    # followed by optional close-quotes, whitespace, an opening-quote, and a
    # capitalised dialogue tag (Name1 (Name2)? said/replied/asked/...).
    paragraphs = _split_merged_dialogue(paragraphs)
    return paragraphs


# Boundary marker for merged dialogue turns (see _split_merged_dialogue).
# Matches a sentence-ending character followed by whitespace and an
# attribution tag.  The speaker must be from a fixed whitelist of named
# characters / deities (to avoid false-positive splits on generic
# "the king said" mid-sentence).  Opening quotes before the name are
# accepted but not required (dialogue turns in this text sometimes appear
# without a leading open-quote).
_DIALOGUE_SPEAKER_ALT = (
    r'(?:Vaishampayana|Sanjaya|Souti|Ugrashrava|Suta|Shounaka|Saunaka|'
    r'Yudhishthira|Yudhisthira|Dharmaraja|Shakuni|Arjuna|Bhima|'
    r'Bhimasena|Nakula|Sahadeva|Draupadi|Droupadi|Panchali|Krishna|'
    r'Dhritarashtra|Duryodhana|Duhshasana|Vidura|Vasudeva|Karna|Drona|'
    r'Bhishma|Kripa|Ashwatthama|Ashvatthama|Dhrishtadyumna|Janamejaya|'
    r'Vyasa|Narada|Indra|Brihaspati|Brahma|Shiva|Vishnu|Agni|Yama|Varuna|'
    r'Kuvera|Surya|Shakra|Maghavan|Rudra|Parvati|Uma|Skanda|Kartikeya|'
    r'Ganesha|Hanuman|Rama|Lakshmana|Sita|Ravana|Pulastya|Markandeya|'
    r'Lomasha|Parashurama|Parashara|Vasishtha|Vishvamitra|Bharadvaja|'
    r'Atri|Kashyapa|Angirasa|Gautama|Goutama|Agastya|Shandilya|Dhaumya|'
    r'Galava|Utanka|Uttanka|Jaigishavya|Asita|Devala|Jamadagni|Chyavana|'
    r'Durvasa|Mandavya|Hidimba|Hidimbi|Ghatotkacha|Jarasandha|Kamsa|'
    r'Pradyumna|Aniruddha|Satyaki|Virata|Drupada|Shalya|Bhurishrava|'
    r'Jayadratha|Shikhandi|Kunti|Madri|Gandhari|Subhadra|Uttara|'
    r'Abhimanyu|Ulupi|Chitrangada|Bhagadatta|Shishupala|Ekalavya|'
    r'Brihadashva|Shringi|Shamika|Krisha|Brihannada|Sairandhri|Sudeshna|'
    r'Arjuna|Phalguna|Dhananjaya|Keshava|Hari|Janardana|Madhusudana|'
    r'Partha|Kounteya|Kaunteya|Prahlada|Virochana|Sudhanva|Sanatsujata|'
    r'Yajnavalkya|Jaratkaru|The lord|The king|The suta|The rishi|'
    r'The brahmana|The ascetic|The god|The goddess)'
)

_MERGED_DIALOGUE_RE = re.compile(
    # Only split at a quote boundary: previous utterance ends with a
    # close-quote (typically after a sentence-terminator) AND the next
    # attribution starts with an open-quote.  This fires on dialogue-turn
    # transitions like `... I have won.' 'Yudhishthira replied, ...`
    # but NOT on single inline tags like `Drona said, 'Give me your thumb.'`
    # which PDF keeps inside the surrounding narrative paragraph.
    # Use only the curly close-quotes (U+2019 / U+201D) in the lookbehind --
    # including ASCII apostrophe would spuriously match the leading `'` of
    # a paragraph opener like `' 'Krishna replied, ...`.
    r'(?<=[\u2019\u201d])'                          # prev ends with close-quote
    r'(\s+)'                                        # whitespace
    r'(?=[\u2018\u201c\'"]{1,3}'                    # REQUIRED opening quote(s)
    + _DIALOGUE_SPEAKER_ALT +
    r'(?:\u2019s|\'s)?'                             # optional possessive
    r'\s+(?:said|replied|asked|answered|continued|spoke|told|exclaimed|'
    r'declared|cried|retorted|enquired|observed|remarked|began)'
    r'\s*[,:])'
)


def _split_merged_dialogue(paragraphs):
    out = []
    for p in paragraphs:
        # Find all split positions
        positions = [m.start(1) for m in _MERGED_DIALOGUE_RE.finditer(p)]
        if not positions:
            out.append(p)
            continue
        pieces = []
        prev = 0
        for pos in positions:
            pieces.append(p[prev:pos].rstrip())
            # consume the whitespace captured in group 1
            m = _MERGED_DIALOGUE_RE.match(p, pos - 1) if pos > 0 else None
            # simpler: skip whitespace manually
            j = pos
            while j < len(p) and p[j] in ' \t\u00A0':
                j += 1
            prev = j
        pieces.append(p[prev:])
        out.extend(x for x in pieces if x.strip())
    return out


# ---------------------------------------------------------------------------
# Per-volume parsing
# ---------------------------------------------------------------------------

def _find_story_start(volume_lines, first_section_idx, section_pattern):
    """Find the index of the section header that starts the real story body.

    For volumes 7-10 the source interleaves a long table of contents between
    the first section header and the actual narrative.  The ToC contains
    section headers and "Chapter N(M)" lines identical in form to real
    chapter markers.  The reliable distinguishing feature is that a REAL
    chapter marker is followed (after blanks) by a substantive narrative
    line -- one that is NOT another chapter marker / section header / shloka
    count and that is long enough (> 60 chars) to be real prose.  Body text
    may or may not carry the 2-space paragraph indent at the first line of a
    new chapter (page-break artefact), so we do NOT require indentation here
    -- length + "not a structural marker" is enough.
    """
    n = len(volume_lines)
    last_section = first_section_idx
    i = first_section_idx
    # Volumes whose section headers are ALL-CAPS (V5-V10) always use the
    # "CHAPTER N(M)" or "Chapter N(M)" style for real chapter markers;
    # bare numeric lines are front-matter junk (family-tree labels, TOC
    # row cells, etc.) and must NOT trigger story-start detection.
    # Only V1 uses bare numeric chapter markers, and it uses title-case
    # section headers, so we tighten only for the UPPER pattern.
    upper_only = (section_pattern is SECTION_HEADER_UPPER_RE)
    strict_cm = re.compile(
        r'^(?:CHAPTER\s+|Chapter\s+)?\d{1,4}\s*\(\d{1,4}\)\d{0,4}$'
    )
    while i < n:
        line = volume_lines[i]
        if _is_section_header(line, section_pattern):
            last_section = i
        is_cm = _is_chapter_number(line) and not _is_shloka_count(line)
        if is_cm and upper_only and not strict_cm.match(line.strip()):
            is_cm = False  # reject bare numeric in upper-case volumes
        if is_cm:
            j = i + 1
            while j < n and not volume_lines[j].strip():
                j += 1
            if j < n:
                nxt = volume_lines[j]
                nxt_s = nxt.strip()
                # Next non-blank: if it is a structural marker (another
                # chapter marker, section header, shloka count, or a line
                # that STARTS with a chapter-marker token even if it has
                # extra trailing junk like "Acknowledgements Follow ..."),
                # or a very short metadata-style line, we are still inside
                # the ToC and keep walking.  Otherwise it is narrative prose.
                looks_like_chapter_line = bool(re.match(
                    r'^(?:CHAPTER|Chapter)\s+\d+', nxt_s
                ))
                if (not _is_chapter_number(nxt)
                        and not looks_like_chapter_line
                        and not _is_section_header(nxt, section_pattern)
                        and not _is_shloka_count(nxt)
                        and len(nxt_s) > 60):
                    # If the nearest preceding section header is far away
                    # (>= 30 lines back), the run of section headers we
                    # saw was part of the front-matter ToC and the real
                    # narrative has no repeating section headers before
                    # it.  In that case start the body at the chapter
                    # marker itself so we skip the ToC block.
                    if i - last_section >= 30:
                        return i
                    return last_section
        i += 1
    return first_section_idx


def parse_volume(volume_lines, starting_chapter):
    """Parse one volume.

    Tries the title-case section-header pattern first; if that produces no
    chapters, retries with the ALL-CAPS pattern (used in volumes 7-10 where
    the source has no title-case section headers).
    """
    for pattern in (SECTION_HEADER_TITLECASE_RE, SECTION_HEADER_UPPER_RE):
        chapters, sections, next_chap = _parse_volume_with(
            volume_lines, starting_chapter, pattern
        )
        if chapters:
            return chapters, sections, next_chap
    return [], [], starting_chapter


def _parse_volume_with(volume_lines, starting_chapter, section_pattern):
    """Parse one volume using a specific section-header pattern.

    Returns: (chapters, sections, next_chapter_counter)
        chapters: list of (chap_num, [paragraphs])
        sections: list of dicts {num, title, parva, description, first_chap, last_chap}
    """
    # Drop front matter before first section header
    first_idx = None
    for i, line in enumerate(volume_lines):
        if _is_section_header(line, section_pattern):
            first_idx = i
            break
    if first_idx is None:
        return [], [], starting_chapter

    # In volumes 7-10 the source interleaves a long table of contents
    # BETWEEN the first section header and the real story start.  The ToC
    # contains section headers AND bare "Chapter N(M)" lines that look
    # identical to real chapter markers but are not followed by any
    # narrative text.  We detect the true story-start by looking for the
    # first chapter marker whose next non-blank lines contain an indented
    # narrative paragraph (the PARA_INDENT pattern).  The body then starts
    # at the nearest section header at or before that chapter marker.
    story_idx = _find_story_start(volume_lines, first_idx, section_pattern)
    first_idx = story_idx

    body = volume_lines[first_idx:]

    # Step 3: truncate the volume at the "Acknowledgements" back-matter marker.
    for i, line in enumerate(body):
        if ACKNOWLEDGEMENTS_RE.match(line):
            body = body[:i]
            break

    # Volumes 7-10: also truncate at the LAST "This ends <X> Parva." line
    # that is followed by a footnote-definition block rather than another
    # parva.  The source re-dumps every chapter header after the last parva
    # as footnotes, which would double-count every chapter.  We recognise
    # the footnote block by an "Introduction" line or by a run of lines
    # beginning with "<digit> " (footnote definitions) within the next
    # ~20 non-blank lines after the parva-end marker.  A "This ends X
    # Parva." followed by another parva's content is NOT a truncation
    # boundary.
    truncate_at = None
    for i, line in enumerate(body):
        if PARVA_END_RE.match(line):
            # Peek forward up to 30 non-blank lines.
            probes = []
            j = i + 1
            while j < len(body) and len(probes) < 30:
                s = body[j].strip()
                if s:
                    probes.append(s)
                j += 1
            is_footnote_block = False
            # Heuristic 1: an "Introduction" header appears, or the word
            # "Footnotes" appears, in the peek window.
            for s in probes[:6]:
                if s.lower() in ('introduction', 'footnotes'):
                    is_footnote_block = True
                    break
            # Heuristic 2: many of the peek lines start with "<digit> " --
            # the footnote dump pattern ("1 Brahmana is ...").
            if not is_footnote_block and probes:
                digit_starts = sum(
                    1 for s in probes if re.match(r'^\d+\s+[A-Za-z]', s)
                )
                if digit_starts >= 3:
                    is_footnote_block = True
            if is_footnote_block:
                truncate_at = i + 1  # keep the parva-end line itself
    if truncate_at is not None:
        body = body[:truncate_at]

    # Volumes 8-10 additionally have a back-matter footnote block that is
    # NOT preceded by a "This ends <Parva>." line -- it just starts as a
    # run of "Introduction" / "<digit> <Cap>..." lines followed by a second
    # copy of every chapter header in ALL CAPS ("CHAPTER 1284(1)" etc.)
    # that is used as the footnote organisational headers.  Detect that
    # block directly and truncate.  The signature is: an "Introduction"
    # line, OR at least 5 lines in a 10-line window that start with
    # "<digit> <Capital letter>".
    for i, line in enumerate(body):
        s = line.strip()
        if s.lower() == 'introduction':
            # Require the following 20 non-blank lines to look like
            # footnote definitions (digit-prefix).
            probes = []
            j = i + 1
            while j < len(body) and len(probes) < 20:
                ss = body[j].strip()
                if ss:
                    probes.append(ss)
                j += 1
            digit_starts = sum(
                1 for ss in probes if re.match(r'^\d+\s+[A-Za-z]', ss)
            )
            if digit_starts >= 3:
                body = body[:i]
                break

    chapters = []
    sections = []
    section_idx = 0
    chap_counter = starting_chapter
    current_section = None
    mode = 'section_desc'
    pending_chapter = False  # saw a chapter-number line, waiting for body
    pending_chap_num = None  # source-derived chapter number for the pending CM
    block_lines = []

    def flush_block():
        nonlocal block_lines, chap_counter, pending_chapter, pending_chap_num
        if not block_lines:
            return
        paras = _form_paragraphs(block_lines)
        block_lines = []
        if not paras:
            return
        if mode == 'section_desc':
            if current_section is not None:
                prev = current_section.get('description') or ''
                sep = '\n' if prev else ''
                current_section['description'] = prev + sep + '\n'.join(paras)
        else:  # chapter_body
            if pending_chapter:
                if pending_chap_num is not None:
                    chap_num = pending_chap_num
                    chap_counter = chap_num + 1
                else:
                    chap_num = chap_counter
                    chap_counter += 1
                chapters.append((chap_num, paras))
                if current_section is not None:
                    if current_section['first_chap'] is None:
                        current_section['first_chap'] = chap_num
                    current_section['last_chap'] = chap_num
                pending_chapter = False
                pending_chap_num = None

    # Volumes that use UPPER-case section headers (V5-V10) only emit
    # chapters that use the `N(M)` paren format (optionally prefixed
    # with CHAPTER/Chapter).  Bare `N` lines in those volumes are
    # front-matter artefacts (family-tree labels, TOC cells) and must
    # not be treated as chapter markers.
    upper_only = (section_pattern is SECTION_HEADER_UPPER_RE)
    _STRICT_CM_RE = re.compile(
        r'^(?:CHAPTER\s+|Chapter\s+)?\d{1,4}\s*\(\d{1,4}\)\d{0,4}$'
    )

    def _accept_cm(line_stripped):
        if upper_only:
            return bool(_STRICT_CM_RE.match(line_stripped))
        return True

    for line in body:
        sec_m = _is_section_header(line, section_pattern)
        if sec_m:
            flush_block()
            section_idx += 1
            ordinal = sec_m.group(1)
            parva = (sec_m.group(2) or '').strip()
            title = f"Section {ordinal}"
            if parva:
                title = f"{title} {parva}"
            current_section = {
                'num': section_idx,
                'title': title,
                'parva': parva,
                'description': '',
                'first_chap': None,
                'last_chap': None,
            }
            sections.append(current_section)
            mode = 'section_desc'
            pending_chapter = False
            continue

        if _is_chapter_number(line) and _accept_cm(line.strip()):
            flush_block()
            # Capture the source-derived chapter number so our output aligns
            # with the PDF reference (which uses source numbers, not a
            # sequential counter).  Defer emission to flush time so that
            # false-positive "chapter" lines (shloka-count tables) which
            # have no following body do not consume a number.
            m = CHAPTER_NUM_RE.match(line.strip())
            pending_chap_num = int(m.group(1)) if m else None
            pending_chapter = True
            mode = 'chapter_body'
            continue

        block_lines.append(line)

    flush_block()
    return chapters, sections, chap_counter


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _write_chapters(path, chapters):
    with open(path, 'w', encoding='utf-8') as f:
        for chap_num, paras in chapters:
            f.write(f"--- Chapter {chap_num} ---\n")
            for p in paras:
                f.write(_normalize_footnote_refs(p) + '\n')


def _write_footnotes(path, sections):
    """Skeleton footnotes file matching PDF-pipeline shape.

    The plain-text source does not carry separate footnote definition blocks,
    so we emit only the section / chapter-range headers.
    """
    with open(path, 'w', encoding='utf-8') as f:
        for sec in sections:
            f.write(f"--- Section {sec['num']} ---\n")
            if sec['first_chap'] is not None:
                f.write(
                    f"--- Chapters {sec['first_chap']} to {sec['last_chap']} ---\n"
                )


_ORDINAL_WORDS = [
    'Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
    'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
    'Seventeen', 'Eighteen', 'Nineteen', 'Twenty',
]


def _ordinal_word(n):
    if 0 <= n < len(_ORDINAL_WORDS):
        return _ORDINAL_WORDS[n]
    return str(n)


def _write_toc(path, sections):
    with open(path, 'w', encoding='utf-8') as f:
        for sec in sections:
            f.write(f"SECTION {_ordinal_word(sec['num']).upper()}\n")
        f.write('\n')
        for sec in sections:
            f.write(f"{sec['title']}\n")
            if sec['description']:
                f.write(sec['description'].strip() + '\n')
            f.write('\n')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def step1_extract_volumes(input_dir='input', output_dir='text_to_volumes/output'):
    print("\n" + "=" * 60)
    print("TEXT EXTRACTION PIPELINE")
    print("=" * 60)

    input_path = os.path.join(input_dir, TXT_FILENAME)
    os.makedirs(output_dir, exist_ok=True)

    volumes = split_volumes(input_path)

    chap_counter = 1
    for vol_num in range(1, NUM_VOLUMES + 1):
        if vol_num not in volumes:
            print(f"\n  WARNING: Volume {vol_num} not found in text!")
            continue

        print(f"\n  Processing Volume {vol_num}...")
        chapters, sections, chap_counter = parse_volume(
            volumes[vol_num], chap_counter
        )

        _write_chapters(
            os.path.join(output_dir, f'volume_{vol_num}_chapters.txt'),
            chapters,
        )
        _write_footnotes(
            os.path.join(output_dir, f'volume_{vol_num}_footnotes.txt'),
            sections,
        )
        _write_toc(
            os.path.join(output_dir, f'volume_{vol_num}_toc.txt'),
            sections,
        )

        first_chap = chapters[0][0] if chapters else '-'
        last_chap = chapters[-1][0] if chapters else '-'
        print(
            f"    Sections: {len(sections)}  "
            f"Chapters: {len(chapters)} "
            f"(#{first_chap}..#{last_chap})"
        )

    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    step1_extract_volumes()
