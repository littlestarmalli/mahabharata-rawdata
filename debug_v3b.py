"""Trace exactly what step1_extract_volumes produces for V3."""
import sys, re
sys.path.insert(0, '.')

# Patch parse_volume to capture V3 result
import text_to_volumes.txt_parser as p

_orig_parse = p.parse_volume
_v3_result = [None]

def _patched_parse(volume_lines, starting_chapter):
    result = _orig_parse(volume_lines, starting_chapter)
    # Detect V3 by chapter range
    if result[0] and result[0][0][0] in range(370, 400):
        _v3_result[0] = result
        nums = [c[0] for c in result[0]]
        print(f"[PATCH] parse_volume called for V3: {len(result[0])} chapters")
        print(f"  Around 405-412: {[n for n in nums if 404<=n<=413]}")
        print(f"  Around 494-499: {[n for n in nums if 493<=n<=500]}")
    return result

p.parse_volume = _patched_parse

# Run the actual pipeline
p.step1_extract_volumes(input_dir='input', output_dir='text_to_volumes/output')

# Count chapters in written file
with open('text_to_volumes/output/volume_3_chapters.txt', encoding='utf-8') as f:
    lines = f.readlines()
nums = [int(re.search(r'\d+', l).group()) for l in lines if l.startswith('--- Chapter')]
print(f"\nFinal V3 file: {len(nums)} chapters")
print(f"  Around 405-412: {[n for n in nums if 404<=n<=413]}")
