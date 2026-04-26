import re
with open('output/volumes/volume_1_chapters.txt', encoding='utf-8') as f:
    content = f.read()
segs = re.split(r'(?=--- Chapter \d+\b)', content)
hits = {}
for seg in segs:
    m = re.match(r'--- Chapter (\d+)', seg)
    if m:
        ch = int(m.group(1))
        if 3 <= ch <= 41:
            for fn_ref in re.findall(r'\{(\d+)\}', seg):
                n = int(fn_ref)
                if 37 <= n <= 134:
                    hits.setdefault(ch, []).append(n)
for ch in sorted(hits):
    ns = sorted(hits[ch])
    print(f'  ch{ch}: fns {ns[:8]}{"..." if len(ns)>8 else ""}')
print(f'Chapters using fn 37-134: {sorted(hits.keys())}')
