"""Find chapters with abnormally high depth — these have mismatched quotes."""
import json, os

print("Chapters with max depth > 6:\n")
print(f"{'Volume':>8} {'Chapter':>8} {'MaxDepth':>9} {'Segments':>9}  File")
print("-" * 70)

bad_chapters = []

for v in range(1, 11):
    d = f'output/dialogs/volume_{v}'
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.json'): continue
        data = json.load(open(os.path.join(d, fname), encoding='utf-8'))
        max_d = 0
        total_segs = 0
        for p in data['paragraphs']:
            for seg in p['segments']:
                dep = seg.get('depth', 0)
                if dep > max_d:
                    max_d = dep
                total_segs += 1
        if max_d > 6:
            ch = data['chapter']
            print(f"{v:>8} {ch:>8} {max_d:>9} {total_segs:>9}  {fname}")
            bad_chapters.append((v, ch, max_d, fname))

print(f"\nTotal bad chapters: {len(bad_chapters)}")
print(f"\nDepth stats for normal chapters (depth <= 6):")

# Count segments by depth excluding bad chapters
from collections import Counter
bad_set = set((b[0], b[3]) for b in bad_chapters)
depth_counts = Counter()
for v in range(1, 11):
    d = f'output/dialogs/volume_{v}'
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.json'): continue
        if (v, fname) in bad_set: continue
        data = json.load(open(os.path.join(d, fname), encoding='utf-8'))
        for p in data['paragraphs']:
            for seg in p['segments']:
                depth_counts[seg.get('depth', 0)] += 1

for dep in sorted(depth_counts):
    print(f"  depth {dep}: {depth_counts[dep]} segments")
