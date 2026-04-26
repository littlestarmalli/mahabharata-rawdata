"""Find short curly-double-quoted terms that are likely NOT dialogue."""
import re, os

pattern = re.compile(r'\u201c([^\u201d]{1,50})\u201d')
vol_dir = 'output/volumes'
results = []

for fname in sorted(os.listdir(vol_dir)):
    if not fname.endswith('_chapters.txt'):
        continue
    fpath = os.path.join(vol_dir, fname)
    with open(fpath, encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            for m in pattern.finditer(line):
                inner = m.group(1)
                words = inner.split()
                if len(words) > 8:
                    continue
                # Get context
                ctx_start = max(0, m.start() - 40)
                ctx_end = min(len(line), m.end() + 40)
                ctx = line[ctx_start:ctx_end].replace('\n', ' ').strip()
                results.append((fname, i, inner, ctx))

with open('_term_quotes_report.txt', 'w', encoding='utf-8') as out:
    out.write(f"Found {len(results)} short curly-quoted segments:\n\n")
    for fname, line, inner, ctx in results:
        out.write(f"{fname}:{line}  [{len(inner.split())}w] \u201c{inner}\u201d\n")
        out.write(f"  CTX: ...{ctx}...\n\n")

print(f"Found {len(results)} matches. Written to _term_quotes_report.txt")
