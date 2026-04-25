"""Debug script: trace why V3 gives 216 in pipeline but 220 direct."""
import sys, io, re
sys.path.insert(0, '.')
import text_to_volumes.txt_parser as p

# Suppress noisy output
old = sys.stdout; sys.stdout = io.StringIO()
vols = p.split_volumes('input/Complete_text_mahabharat.txt')
sys.stdout = old

# Simulate pipeline: parse V1, V2 first
sys.stdout = io.StringIO()
chaps1, _, chap = p.parse_volume(vols[1], 1)
chaps2, _, chap = p.parse_volume(vols[2], chap)
sys.stdout = old
print(f"After V1+V2: chap_counter={chap}")

# Now parse V3 using the _parse_volume_with directly to see which pattern it uses
v3 = vols[3]

# Try titlecase first
chaps_tc, secs_tc, _ = p._parse_volume_with(v3, chap, p.SECTION_HEADER_TITLECASE_RE)
nums_tc = [c[0] for c in chaps_tc]
print(f"Titlecase pattern: {len(chaps_tc)} chapters")
print(f"  Around 405-412: {[n for n in nums_tc if 404<=n<=413]}")
print(f"  Around 494-499: {[n for n in nums_tc if 493<=n<=500]}")

# Parse via parse_volume (which tries titlecase first then UPPER)
sys.stdout = io.StringIO()
chaps3, _, _ = p.parse_volume(v3, chap)
sys.stdout = old
nums3 = [c[0] for c in chaps3]
print(f"parse_volume: {len(chaps3)} chapters")
print(f"  Around 405-412: {[n for n in nums3 if 404<=n<=413]}")
print(f"  Around 494-499: {[n for n in nums3 if 493<=n<=500]}")

# Now write the chapters to a temp file and count them
import os
tmp = 'text_to_volumes/output/volume_3_chapters.txt'
p._write_chapters(tmp, chaps3)
with open(tmp, encoding='utf-8') as f:
    lines = f.readlines()
file_nums = [int(re.search(r'\d+', l).group()) for l in lines if l.startswith('--- Chapter')]
print(f"File has {len(file_nums)} chapters after _write_chapters")
print(f"  Around 405-412: {[n for n in file_nums if 404<=n<=413]}")
