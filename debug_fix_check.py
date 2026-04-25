import re

# Check ch 1 fn18
with open('output/volumes/volume_1_chapters.txt', encoding='utf-8') as f:
    ch1 = f.read()
segs = re.split(r'(?=--- Chapter \d+)', ch1)
for seg in segs:
    if seg.startswith('--- Chapter 1(1)'):
        m = re.search(r'vijnana.{0,5}18.{0,10}|18.{0,10}were', seg)
        if m:
            print('Ch 1 fn18:', repr(m.group()))
        else:
            print('Ch 1: searching for plain 18...')
            # find any occurrence of {18}
            m2 = re.search(r'\{18\}', seg)
            if m2:
                start = max(0, m2.start()-40)
                print('Ch 1 fn{18} context:', repr(seg[start:m2.end()+40]))
        break

# Check ch 5 (Pouloma) fn 4
for seg in segs:
    if seg.startswith('--- Chapter 5(5)'):
        m = re.search(r'\{4\}', seg)
        if m:
            start = max(0, m.start()-50)
            print('Ch 5 fn{4}:', repr(seg[start:m.end()+30]))
        else:
            print('Ch 5: {4} NOT found')
        break

# Check vol 5 BG fn 3
with open('output/volumes/volume_5_chapters.txt', encoding='utf-8') as f:
    ch5 = f.read()
segs5 = re.split(r'(?=--- Chapter \d+)', ch5)
for seg in segs5:
    if seg.startswith('--- Chapter 874'):
        m = re.search(r'\{3\}', seg)
        if m:
            start = max(0, m.start()-40)
            print('Ch 874 fn{3}:', repr(seg[start:m.end()+40]))
        else:
            print('Ch 874: {3} NOT found')
        break
