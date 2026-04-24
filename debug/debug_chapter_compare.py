"""
Accurate per-chapter PDF vs Extracted paragraph comparison.
Uses identical chapter detection logic as pipeline/extract/pdf_parser.py.
"""
import fitz
import re
import os
import csv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(PROJECT_ROOT, 'input', 'The Mahabharata Set of 10 Volumes.pdf')

VOLUME_RANGES = {
    1: (26, 227), 2: (301, 489), 3: (576, 816), 4: (907, 1133), 5: (1208, 1436),
    6: (1522, 1726), 7: (1769, 2108), 8: (2283, 2739), 9: (3013, 3288), 10: (3383, 3670),
}

THRESHOLD = 80.0
SENT_END = set('.!?\u2019\u201d\'"):')


def norm(s):
    return re.sub(r'\s+', ' ', s.replace('\u2029', ' ')).strip()


def count_pdf_per_chapter(start, end, doc, ext_chapter_ids):
    """Count PDF paragraphs per chapter.

    Paragraph detection mirrors debug_compare_accurate.py exactly (line-level indentation
    + sentence-end detection). Chapter assignment is done as a side-check: when a
    line matches a chapter marker, switch the active chapter.

    Starts with current = first extracted chapter id so content before the first
    detected chapter marker is attributed to Ch 1 (handles Section One layout).
    """
    chapters = []
    current = ext_chapter_ids[0] if ext_chapter_ids else '1'
    count = 0
    prev_line_text = ""
    past_first_section = True  # start enabled - volumes begin within Section One

    for p in range(start, end):
        d = doc[p].get_text('dict')
        for block in d.get('blocks', []):
            if block.get('type') != 0:
                continue
            for line in block.get('lines', []):
                spans = line.get('spans', [])
                if not spans:
                    continue
                raw = ''.join(s['text'] for s in spans)
                line_text = norm(raw)
                if not line_text or len(line_text) < 2:
                    continue
                if 'mahabharata' in line_text.lower() and len(line_text) < 80:
                    continue

                x0 = line['bbox'][0]

                # Section header detection (sets flag, clears prev)
                if re.match(r'^(SECTION|Section)\s+', line_text):
                    past_first_section = True
                    prev_line_text = ""
                    continue

                # Chapter marker detection
                ch_id = None
                m_chap = re.match(r'^(CHAPTER|Chapter)\s+(\d+(?:\(\d+\))?)\s*$', line_text)
                if m_chap:
                    ch_id = m_chap.group(2)
                    past_first_section = True
                elif past_first_section and x0 >= 200:
                    m_paren = re.match(r'^(\d+)\s*\((\d+)\)\s*\d*$', line_text)
                    m_bare = re.match(r'^(\d+)$', line_text)
                    if m_paren:
                        ch_id = f"{m_paren.group(1)}({m_paren.group(2)})"
                    elif m_bare:
                        ch_id = m_bare.group(1)

                if ch_id:
                    chapters.append((current, count))
                    current = ch_id
                    count = 0
                    prev_line_text = ""
                    continue

                # Paragraph counting (identical to debug_compare_accurate.py)
                if x0 >= THRESHOLD:
                    prev_stripped = prev_line_text.rstrip()
                    if not prev_stripped or prev_stripped[-1] in SENT_END:
                        count += 1
                prev_line_text = line_text

    chapters.append((current, count))
    return chapters


def count_extracted_per_chapter(vol):
    path = os.path.join(PROJECT_ROOT, 'output', 'volumes', f'volume_{vol}_chapters.txt')
    chapters = []
    current = None
    count = 0
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()
            m = re.match(r'^---\s*Chapter\s+(.+?)\s*---\s*$', line)
            if m:
                if current is not None:
                    chapters.append((current, count))
                current = m.group(1).strip()
                count = 0
                continue
            if current is None:
                continue
            if line.strip():
                count += 1
    if current is not None:
        chapters.append((current, count))
    return chapters


def main():
    doc = fitz.open(PDF)
    out_csv = os.path.join(PROJECT_ROOT, 'output', 'chapter_paragraph_comparison.csv')

    grand = {'pdf': 0, 'ext': 0}
    with open(out_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Volume', 'Chapter', 'PDF_Paragraphs', 'Extracted_Paragraphs',
                         'Difference', 'Match_Percent'])

        print(f"\n{'Vol':>4} {'PDF':>6} {'Ext':>6} {'Diff':>6} {'Match':>8} "
              f"{'Chaps':>6} {'OK':>5} {'Over':>5} {'Under':>5}")
        print('-' * 65)

        for vol in range(1, 11):
            start, end = VOLUME_RANGES[vol]
            print(f"Vol {vol}...", end=' ', flush=True)
            ext_chs = count_extracted_per_chapter(vol)
            ext_chapter_ids = [c for c, _ in ext_chs]
            pdf_chs = count_pdf_per_chapter(start, end, doc, ext_chapter_ids)

            # Merge duplicate chapter ids in pdf_chs (same id can recur)
            pdf_map = {}
            for k, v in pdf_chs:
                pdf_map[k] = pdf_map.get(k, 0) + v
            ext_map = dict(ext_chs)
            all_ch = []
            seen = set()
            for k, _ in ext_chs:
                if k not in seen:
                    all_ch.append(k); seen.add(k)
            for k, _ in pdf_chs:
                if k not in seen:
                    all_ch.append(k); seen.add(k)

            vol_pdf = vol_ext = 0
            perfect = over = under = 0
            for ch in all_ch:
                pc = pdf_map.get(ch, 0)
                ec = ext_map.get(ch, 0)
                diff = pc - ec
                pct = round(100 * ec / pc, 1) if pc > 0 else 0.0
                writer.writerow([vol, ch, pc, ec, diff, pct])
                vol_pdf += pc
                vol_ext += ec
                if diff == 0: perfect += 1
                elif diff < 0: over += 1
                else: under += 1

            match = round(100 * vol_ext / vol_pdf, 1) if vol_pdf else 0
            print(f"PDF={vol_pdf} Ext={vol_ext} Match={match}%")
            grand['pdf'] += vol_pdf
            grand['ext'] += vol_ext

        print('-' * 65)
        gmatch = round(100 * grand['ext'] / grand['pdf'], 1) if grand['pdf'] else 0
        print(f"TOTAL PDF={grand['pdf']} Ext={grand['ext']} Match={gmatch}%")

    print(f"\nCSV saved: {out_csv}")


if __name__ == '__main__':
    main()
