"""
Accurate PDF paragraph counter matching the extraction logic.
A paragraph starts at an indented line whose PRECEDING line ended
with sentence-terminating punctuation.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import fitz, os, re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(PROJECT_ROOT, 'input', 'The Mahabharata Set of 10 Volumes.pdf')

VOLUME_RANGES = {
    1: (26, 227), 2: (301, 489), 3: (576, 816), 4: (907, 1133), 5: (1208, 1436),
    6: (1522, 1726), 7: (1769, 2108), 8: (2283, 2739), 9: (3013, 3288), 10: (3383, 3670),
}

THRESHOLD = 80.0
SENT_END = '.!?\u2019\u201d\'\"):'


def count_extracted(vol):
    path = os.path.join(PROJECT_ROOT, 'output/volumes', f'volume_{vol}_chapters.txt')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    count = 0
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('---'):
            continue
        count += 1
    return count


def count_pdf_paragraphs(doc, start, end):
    total = 0
    prev_line_text = ""
    for page_num in range(start, end):
        d = doc[page_num].get_text('dict')
        for block in d.get('blocks', []):
            if block.get('type') != 0:
                continue
            for line in block.get('lines', []):
                spans = line.get('spans', [])
                if not spans:
                    continue
                raw = ''.join(s['text'] for s in spans)
                line_text = re.sub(r'\s+', ' ', raw.replace('\u2029', ' ')).strip()
                if not line_text or len(line_text) < 2:
                    continue
                # Skip running headers
                if 'mahabharata' in line_text.lower() and len(line_text) < 80:
                    continue
                # Skip chapter headers
                if re.match(r'^Chapter\s+\d+(?:\(\d+\))?\s*$', line_text):
                    prev_line_text = ""
                    continue
                if re.match(r'^(SECTION|Section)\s+', line_text):
                    prev_line_text = ""
                    continue
                x0 = line['bbox'][0]
                is_indented = x0 >= THRESHOLD

                if is_indented:
                    # New paragraph iff prev line ended a sentence (or no prev)
                    prev_stripped = prev_line_text.rstrip()
                    if not prev_stripped or (prev_stripped and prev_stripped[-1] in SENT_END):
                        total += 1
                    # Else: dropcap continuation, don't count
                prev_line_text = line_text
    return total


doc = fitz.open(PDF_PATH)

print(f"{'Vol':>3} {'PDF':>6} {'Extr':>6} {'Diff':>6} {'Match%':>7}")
print("-" * 40)
tot_pdf = tot_ext = 0
for vol in range(1, 11):
    s, e = VOLUME_RANGES[vol]
    pdf_n = count_pdf_paragraphs(doc, s, e)
    ext = count_extracted(vol)
    diff = pdf_n - ext
    match = 100*ext/pdf_n if pdf_n else 0
    tot_pdf += pdf_n; tot_ext += ext
    print(f"{vol:>3} {pdf_n:>6} {ext:>6} {diff:>6} {match:>6.1f}%")

print("-" * 40)
m = 100*tot_ext/tot_pdf if tot_pdf else 0
print(f"{'TOT':>3} {tot_pdf:>6} {tot_ext:>6} {tot_pdf-tot_ext:>6} {m:>6.1f}%")
doc.close()
