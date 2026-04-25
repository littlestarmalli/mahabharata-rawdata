"""
Fix volume_1_footnotes.txt:
1. Change Poushya section range from "Chapters 3 to 41" to "Chapters 3 to 3"
2. Remove the 98 erroneous [MISSING FOOTNOTE] entries (fns 37-134)
   These were wrongly attributed to Poushya; they belong to Astika (ch 13-53).
"""
import re

path = 'output/volumes/volume_1_footnotes.txt'
with open(path, encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
removed = 0
for l in lines:
    # Fix the section header
    if l.strip() == '--- Chapters 3 to 41 ---':
        new_lines.append('--- Chapters 3 to 3 ---\n')
        continue
    # Remove MISSING FOOTNOTE entries (they were in Poushya fns 37-134)
    if '[MISSING FOOTNOTE' in l:
        removed += 1
        continue
    new_lines.append(l)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Fixed section header: 'Chapters 3 to 41' -> 'Chapters 3 to 3'")
print(f"Removed {removed} [MISSING FOOTNOTE] lines")
print(f"File: {len(lines)} lines -> {len(new_lines)} lines")
