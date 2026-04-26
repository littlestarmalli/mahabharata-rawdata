"""
Line-by-line comparison of chapter files (A vs B).
Shows exact line numbers and content where files differ.
Skips V1 and V2. Focuses on truly missing lines, not encoding differences.
"""
import difflib, re, unicodedata

SRC_A = 'output/volumes'
SRC_B = 'text_to_volumes/output'

def normalize(line):
    s = line.strip()
    # normalize chapter header: "--- Chapter 407(110) ---" -> "--- Chapter 407 ---"
    s = re.sub(r'(--- Chapter \d+)\(\d+\)', r'\1', s)
    # keep only letters, digits, spaces, footnote markers {N}, hyphens in headers
    # strip ALL punctuation/quotes so encoding differences vanish
    s = re.sub(r'\{[^}]*\}', '', s)      # remove footnotes like {1}
    # keep only alphanumeric + space + hyphens (for --- Chapter --- headers)
    s = re.sub(r"[^a-zA-Z0-9 '-]", '', s)
    s = s.lower()
    s = re.sub(r'\s+', ' ', s).strip()
    return s

for v in range(3, 11):
    path_a = f'{SRC_A}/volume_{v}_chapters.txt'
    path_b = f'{SRC_B}/volume_{v}_chapters.txt'

    try:
        lines_a = open(path_a, encoding='utf-8').readlines()
        lines_b = open(path_b, encoding='utf-8').readlines()
    except FileNotFoundError as e:
        print(f'V{v}: MISSING — {e}')
        continue

    norm_a = [normalize(l) for l in lines_a]
    norm_b = [normalize(l) for l in lines_b]

    chaps_a = sum(1 for l in lines_a if l.strip().startswith('--- Chapter'))
    chaps_b = sum(1 for l in lines_b if l.strip().startswith('--- Chapter'))

    print(f'\n{"="*70}')
    print(f'Volume {v}:')
    print(f'  A = {len(lines_a):5d} lines,  {chaps_a} chapters  [{path_a}]')
    print(f'  B = {len(lines_b):5d} lines,  {chaps_b} chapters  [{path_b}]')
    print(f'  Line diff = {len(lines_a) - len(lines_b):+d}')

    matcher = difflib.SequenceMatcher(None, norm_a, norm_b, autojunk=False)
    opcodes = [(tag, i1, i2, j1, j2)
               for tag, i1, i2, j1, j2 in matcher.get_opcodes()
               if tag != 'equal']

    if not opcodes:
        print('  >> IDENTICAL (after normalization)')
        continue

    # Only show truly missing lines (delete/insert), or replace blocks where
    # number of lines differs (real content missing, not just encoding change)
    real_diffs = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'delete':
            real_diffs.append((tag, i1, i2, j1, j2))
        elif tag == 'insert':
            real_diffs.append((tag, i1, i2, j1, j2))
        elif tag == 'replace':
            # only show if line counts differ (real missing content) OR
            # if a chapter header is involved
            a_lines = lines_a[i1:i2]
            b_lines = lines_b[j1:j2]
            has_chap = any(l.strip().startswith('--- Chapter') for l in a_lines + b_lines)
            if len(a_lines) != len(b_lines) or has_chap:
                real_diffs.append((tag, i1, i2, j1, j2))

    if not real_diffs:
        print('  >> Same structure — only encoding/quote differences')
        continue

    print(f'  {len(real_diffs)} structural differences:\n')

    for tag, i1, i2, j1, j2 in real_diffs:
        a_lines = lines_a[i1:i2]
        b_lines = lines_b[j1:j2]

        if tag == 'delete':
            for idx, l in enumerate(a_lines):
                print(f'  A line {i1+1+idx:5d} | ONLY IN A | {l.rstrip()[:120]}')

        elif tag == 'insert':
            for idx, l in enumerate(b_lines):
                print(f'  B line {j1+1+idx:5d} | ONLY IN B | {l.rstrip()[:120]}')

        elif tag == 'replace':
            max_len = max(len(a_lines), len(b_lines))
            for idx in range(max_len):
                al = a_lines[idx].rstrip()[:120] if idx < len(a_lines) else '<missing>'
                bl = b_lines[idx].rstrip()[:120] if idx < len(b_lines) else '<missing>'
                aln = str(i1+1+idx) if idx < len(a_lines) else '     '
                bln = str(j1+1+idx) if idx < len(b_lines) else '     '
                print(f'  A line {aln:5s} | {al}')
                print(f'  B line {bln:5s} | {bl}')
            print()
