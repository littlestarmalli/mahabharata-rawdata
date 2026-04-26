import difflib, re

fa = open('output/volumes/volume_5_chapters.txt', encoding='utf-8').readlines()
fb = open('text_to_volumes/output/volume_5_chapters.txt', encoding='utf-8').readlines()

def norm(l):
    s = l.strip()
    s = re.sub(r'(--- Chapter \d+)\(\d+\)', r'\1', s)
    # normalize all quote chars to single quote
    for c in ['\u201c', '\u201d', '\u2018', '\u2019', '"']:
        s = s.replace(c, "'")
    return s.lower()

na = [norm(l) for l in fa]
nb = [norm(l) for l in fb]

matcher = difflib.SequenceMatcher(None, na, nb, autojunk=False)
extra_a = 0
for tag, i1, i2, j1, j2 in matcher.get_opcodes():
    if tag == 'equal':
        continue
    diff = (i2 - i1) - (j2 - j1)
    if diff > 0:
        extra_a += diff
        print(f'A[{i1+1}-{i2}]({i2-i1} lines) -> B[{j1+1}-{j2}]({j2-j1} lines)  +{diff} extra in A')
        for l in fa[i1:i2]:
            print(f'  A: {l.rstrip()[:120]}')
        for l in fb[j1:j2]:
            print(f'  B: {l.rstrip()[:120]}')
        print()

print(f'Total extra lines in A: {extra_a}')
