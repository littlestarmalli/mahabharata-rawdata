"""Analyze the EXACT opening quote sequences at paragraph start for all chapters with depth > 6.
Goal: find the common pattern to fix the parser."""
import json, os

OQ1, CQ1 = '\u2018', '\u2019'
OQ2, CQ2 = '\u201c', '\u201d'

vol_dir = 'output/volumes'

# For each volume, find the raw paragraphs and track quote balance
for v in range(1, 11):
    fname = f'volume_{v}_chapters.txt'
    fpath = os.path.join(vol_dir, fname)
    with open(fpath, encoding='utf-8') as f:
        lines = f.readlines()
    
    # Track quote balance across paragraphs within each chapter
    in_chapter = False
    ch_num = 0
    ch_stack = []  # running quote stack
    ch_mismatches = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.rstrip('\n')
        
        # Chapter header
        if line.startswith('CHAPTER '):
            if ch_mismatches and len(ch_mismatches) > 2:
                pass  # will print below
            in_chapter = True
            ch_num += 1 if not line.split() else int(line.split()[1]) if len(line.split()) > 1 else ch_num + 1
            ch_stack = []
            ch_mismatches = []
            continue
        
        if not line.strip():
            continue
            
        # Count opens and closes in this paragraph
        opens = 0
        closes = 0
        for c in line:
            if c in (OQ1, OQ2):
                opens += 1
            elif c in (CQ1, CQ2):
                closes += 1
        
        diff = opens - closes
        if diff != 0:
            ch_mismatches.append((line_num, diff, opens, closes))

# Instead, let's just look at the source text for ch 1865
print("=== Volume 10, looking for chapter 1865 paragraphs ===\n")
fpath = os.path.join(vol_dir, 'volume_10_chapters.txt')
with open(fpath, encoding='utf-8') as f:
    lines = f.readlines()

in_target = False
para_count = 0
for i, line in enumerate(lines):
    line = line.rstrip('\n')
    if 'CHAPTER 1865' in line:
        in_target = True
        print(f"--- {line} ---")
        continue
    if in_target and line.startswith('CHAPTER '):
        break
    if in_target and line.strip():
        para_count += 1
        # Count quote balance
        opens = sum(1 for c in line if c in (OQ1, OQ2))
        closes = sum(1 for c in line if c in (CQ1, CQ2))
        
        # Get opening sequence
        opening_seq = []
        for c in line:
            if c in (OQ1, OQ2):
                opening_seq.append("'" if c == OQ1 else '"')
            else:
                break
        
        # Get closing sequence (from end)
        closing_seq = []
        for c in reversed(line):
            if c in (CQ1, CQ2):
                closing_seq.append("'" if c == CQ1 else '"')
            else:
                break
        
        text_preview = line[:60].encode('ascii', 'replace').decode()
        
        print(f"  P{para_count:2d} opens={opens} closes={closes} diff={opens-closes:+d}")
        print(f"       open_seq={opening_seq}  close_seq={closing_seq}")
        print(f"       {text_preview}...")
        print()
