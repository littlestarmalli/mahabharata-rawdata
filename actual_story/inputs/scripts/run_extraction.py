"""
Direct volume extraction bypassing step1_extract_volumes.
Calls parse_volume directly for each volume and writes output.
"""
import sys, re, io
sys.path.insert(0, '.')

# Suppress noisy import prints
old = sys.stdout; sys.stdout = io.StringIO()
import text_to_volumes.txt_parser as p
from text_to_volumes.config import NUM_VOLUMES
sys.stdout = old

print("Splitting volumes...")
old = sys.stdout; sys.stdout = io.StringIO()
vols = p.split_volumes('input/Complete_text_mahabharat.txt')
sys.stdout = old
print(f"Got {len(vols)} volumes")

import os
out_dir = 'text_to_volumes/output'
os.makedirs(out_dir, exist_ok=True)

chap_counter = 1
for vol_num in range(1, NUM_VOLUMES + 1):
    if vol_num not in vols:
        print(f"V{vol_num}: MISSING"); continue

    old = sys.stdout; sys.stdout = io.StringIO()
    chapters, sections, chap_counter = p.parse_volume(vols[vol_num], chap_counter)
    sys.stdout = old

    nums = [c[0] for c in chapters]
    first = nums[0] if nums else '-'
    last = nums[-1] if nums else '-'
    print(f"V{vol_num}: {len(chapters)} chapters (#{first}..#{last})")

    # Write chapters file
    path = os.path.join(out_dir, f'volume_{vol_num}_chapters.txt')
    p._write_chapters(path, chapters)

    # Verify what was written
    with open(path, encoding='utf-8') as f:
        written = f.readlines()
    written_nums = [int(re.search(r'\d+', l).group()) for l in written if l.startswith('--- Chapter')]
    if len(written_nums) != len(chapters):
        print(f"  WARNING: wrote {len(written_nums)} but parsed {len(chapters)}!")

    p._write_footnotes(os.path.join(out_dir, f'volume_{vol_num}_footnotes.txt'), sections)
    p._write_toc(os.path.join(out_dir, f'volume_{vol_num}_toc.txt'), sections)

print("\nDone.")
