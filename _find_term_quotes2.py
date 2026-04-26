"""Find curly-double-quoted TERMS (not dialogue) in source files.
These are quoted words/terms that should use straight quotes."""
import re, os

# Patterns that indicate a quoted TERM, not dialogue
TERM_PATTERNS = [
    r'saying\s+\u201c',
    r'the\s+syllable\s+(?:of\s+)?\u201c',
    r'exclamations?\s+of\s+\u201c',
    r'the\s+word[s]?\s+\u201c',
    r'called\s+\u201c',
    r'known\s+as\s+\u201c',
    r'the\s+name\s+(?:of\s+)?\u201c',
    r'means?\s+\u201c',
    r'meaning\s+\u201c',
    r'termed?\s+\u201c',
    r'entitled\s+\u201c',
    r'uttered?\s+(?:the\s+)?(?:word[s]?\s+)?\u201c',
    r'cry\s+of\s+\u201c',
    r'sound\s+of\s+\u201c',
    r'mantra\s+\u201c',
    r'hymn\s+\u201c',
    r'chant(?:ing)?\s+\u201c',
]

combined = re.compile('(' + '|'.join(TERM_PATTERNS) + r')([^\u201d]{1,60})\u201d', re.IGNORECASE)

vol_dir = 'output/volumes'
results = []

for fname in sorted(os.listdir(vol_dir)):
    if not fname.endswith('_chapters.txt'):
        continue
    fpath = os.path.join(vol_dir, fname)
    with open(fpath, encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            for m in combined.finditer(line):
                prefix = m.group(1)
                inner = m.group(2)
                ctx_start = max(0, m.start() - 20)
                ctx_end = min(len(line), m.end() + 20)
                ctx = line[ctx_start:ctx_end].replace('\n', ' ').strip()
                results.append((fname, i, m.start(), prefix, inner, ctx))

with open('_term_quotes_report2.txt', 'w', encoding='utf-8') as out:
    out.write(f"Found {len(results)} term-quoted segments to fix:\n\n")
    for fname, line, pos, prefix, inner, ctx in results:
        out.write(f"{fname}:{line}:{pos}  \u201c{inner}\u201d\n")
        out.write(f"  CTX: ...{ctx}...\n\n")

print(f"Found {len(results)} term citations to fix")
