"""
fix_apostrophes.py
Replace curly quotes used as apostrophes with straight quote (')
so curly quotes are only used for dialog markers.

Pattern: [a-zA-Z]\u2019[a-zA-Z] or [a-zA-Z]\u2019[ ] (possessive after s)
Replace the \u2019 with straight '
"""

import re
from pathlib import Path

VOL_DIR = Path("output/volumes")

# letter-'-letter  (don't, wasn't, Pandu's, he'd)
# letter-'-space   (Pandavas' fame) — only after 's'
APOSTROPHE_RE = re.compile(r"(?<=[a-zA-Z])\u2019(?=[a-zA-Z])")
POSSESSIVE_RE = re.compile(r"(?<=s)\u2019(?=[\s,;:.!?\)\]\}])")

total_replacements = 0

for f in sorted(VOL_DIR.glob("*_chapters.txt")):
    text = f.read_text(encoding="utf-8")
    new_text, n1 = APOSTROPHE_RE.subn("'", text)
    new_text, n2 = POSSESSIVE_RE.subn("'", new_text)
    n = n1 + n2
    if n:
        f.write_text(new_text, encoding="utf-8")
        total_replacements += n
        print(f"  {f.name}: {n} replacements")

print(f"\nDone. {total_replacements} apostrophes fixed.")
