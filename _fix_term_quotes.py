"""Fix curly double quotes around cited terms → straight double quotes.
These are NOT dialogue — they're term citations like saying "asti", the syllable "Om", etc."""
import re, os

# Term citation patterns: prefix + curly-quoted term
TERM_PATTERNS = [
    r'saying\s+',
    r'the\s+syllable\s+(?:of\s+)?',
    r'exclamations?\s+of\s+',
    r'the\s+word[s]?\s+',
    r'called\s+',
    r'known\s+as\s+',
    r'the\s+name\s+(?:of\s+)?',
    r'means?\s+',
    r'meaning\s+',
    r'termed?\s+',
    r'entitled\s+',
    r'uttered?\s+(?:the\s+)?(?:word[s]?\s+)?',
    r'cry\s+of\s+',
    r'sound\s+of\s+',
    r'mantra\s+',
    r'hymn\s+',
    r'chant(?:ing)?\s+',
    r'in\s+the\s+name\s+of\s+',
    r'the\s+(?:ﬁrst\s+)?sound\s+of\s+',
]

# Also handle: exclamations of "X" and "Y" — the "Y" part
# We'll handle "and "eat"" separately

combined = re.compile(
    r'(' + '|'.join(TERM_PATTERNS) + r')\u201c([^\u201d]{1,60})\u201d',
    re.IGNORECASE
)

vol_dir = 'output/volumes'
total_fixes = 0

for fname in sorted(os.listdir(vol_dir)):
    if not fname.endswith('_chapters.txt'):
        continue
    fpath = os.path.join(vol_dir, fname)
    with open(fpath, encoding='utf-8') as f:
        content = f.read()

    new_content = content

    # Fix term citations: replace curly with straight
    def replace_term(m):
        prefix = m.group(1)
        inner = m.group(2)
        return f'{prefix}"{inner}"'

    new_content = combined.sub(replace_term, new_content)

    # Special case: 'and "eat"' following exclamations of "give"
    # Pattern: and "eat" where "give" was already on the same context
    new_content = new_content.replace(
        '\u201cgive\u201d and \u201ceat\u201d',
        '"give" and "eat"'
    )
    if '"give" and "eat"' in new_content and '\u201cgive\u201d and \u201ceat\u201d' not in new_content:
        pass  # already fixed by combined pattern or this replace

    if new_content != content:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {fname}")
        total_fixes += 1

    # Also fix the _combined.txt version
    combined_fname = fname.replace('_chapters.txt', '_combined.txt')
    combined_fpath = os.path.join(vol_dir, combined_fname)
    if os.path.exists(combined_fpath):
        with open(combined_fpath, encoding='utf-8') as f:
            cc = f.read()
        new_cc = combined.sub(replace_term, cc)
        new_cc = new_cc.replace(
            '\u201cgive\u201d and \u201ceat\u201d',
            '"give" and "eat"'
        )
        if new_cc != cc:
            with open(combined_fpath, 'w', encoding='utf-8') as f:
                f.write(new_cc)
            print(f"Fixed {combined_fname}")

print(f"\nDone. Fixed {total_fixes} volume files.")
