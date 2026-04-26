"""
fix_missing_footnotes_input.py

Finds gaps in footnote number sequences in Complete_text_mahabharat.txt and
inserts   N [MISSING FOOTNOTE]   placeholders immediately before the next
higher footnote line.

Footnote blocks are groups of consecutive lines starting with "N text".
A new block starts when the number resets to a lower value or there is a
gap of >10 lines between consecutive footnote lines.
"""
import re, os

INPUT  = os.path.join(os.path.dirname(__file__), "input", "Complete_text_mahabharat.txt")
OUTPUT = INPUT  # in-place

FN_RE = re.compile(r'^(\d+)\s+\S')

with open(INPUT, encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

# ── collect all footnote line positions ──────────────────────────────────────
fn_positions = []  # (line_idx, fn_num)
for i, l in enumerate(lines):
    m = FN_RE.match(l)
    if m:
        fn_positions.append((i, int(m.group(1))))

# ── group into blocks ─────────────────────────────────────────────────────────
blocks = []
cur_block = []
for idx, (li, n) in enumerate(fn_positions):
    if cur_block:
        prev_li, prev_n = cur_block[-1]
        if n < prev_n - 5 or li - prev_li > 10:
            blocks.append(cur_block)
            cur_block = []
    cur_block.append((li, n))
if cur_block:
    blocks.append(cur_block)

# ── find gaps and build insertions {line_idx: [placeholder_lines]} ────────────
insertions: dict[int, list[str]] = {}
total_gaps = 0

for block in blocks:
    for (li_a, n_a), (li_b, n_b) in zip(block, block[1:]):
        if n_b - n_a > 1:
            for miss in range(n_a + 1, n_b):
                placeholder = f"{miss} [MISSING FOOTNOTE]\n"
                # Insert immediately before li_b
                insertions.setdefault(li_b, []).append(placeholder)
                total_gaps += 1

# ── apply insertions (reverse order to keep indices stable) ──────────────────
result = list(lines)
for idx in sorted(insertions.keys(), reverse=True):
    to_insert = sorted(insertions[idx], key=lambda l: int(l.split()[0]))
    for line in reversed(to_insert):
        result.insert(idx, line)

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.writelines(result)

print(f"Done. Inserted {total_gaps} [MISSING FOOTNOTE] placeholders.")
print(f"File: {OUTPUT}  ({len(lines)} → {len(result)} lines)")
