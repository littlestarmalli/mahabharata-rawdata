"""
Mahabharata PDF Extraction Pipeline
====================================
Single script that does everything:
  1. Extract PDF -> toc, chapters, footnotes per volume
  2. Add section headers to footnotes
  3. Verify footnote ref/def matching
  4. Build character database (characters.json)

Usage: python mahabharata.py <path_to_pdf>
"""

import fitz
import re
import os
import sys
import io
import json
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ================================================================
# CONFIG
# ================================================================
VOLUME_START_PAGES = {
    1: 0, 2: 275, 3: 548, 4: 879, 5: 1185,
    6: 1496, 7: 1767, 8: 2253, 9: 2988, 10: 3356,
}

# ================================================================
# STEP 1: PDF EXTRACTION
# ================================================================

def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def ends_mid_sentence(text):
    t = re.sub(r'\d+$', '', text.rstrip())
    if not t:
        return False
    return t[-1] not in '.!?\u2019\u201d\'\"):'


def fix_footnote_refs(text):
    text = re.sub(
        r'([a-zA-Z\)])([.,;:!?\x27\x22\u2018\u2019\u201c\u201d\)]*?)(\d{1,4})(?=[\s.,;:!?\x27\x22\u2018\u2019\u201c\u201d\)]|$)',
        lambda m: f"{m.group(1)}{{{m.group(3)}}}{m.group(2)}",
        text
    )
    text = re.sub(
        r'([a-zA-Z])([.,;:!?\x27\x22\u2018\u2019\u201c\u201d])\s+(\d{1,4})(?=\s[A-Z\x27\x22\u2018\u201c])',
        lambda m: f"{m.group(1)}{{{m.group(3)}}}{m.group(2)} ",
        text
    )
    return text


def join_block_lines(raw_text):
    lines = [norm(l) for l in raw_text.split('\n') if norm(l)]
    result = ""
    for line in lines:
        if not result:
            result = line
        elif result.endswith('-'):
            result = result[:-1] + line
        else:
            result += " " + line
    return result


def extract_volume(doc, vol, start_page, end_page):
    pw = doc[start_page].rect.width

    # PHASE 1: Scan pages for expected chapters and TOC
    expected_chapters = set()
    toc_lines = []
    content_start_page = None

    for p in range(start_page, end_page):
        text = doc[p].get_text()
        normalized = norm(text)

        for line in text.split('\n'):
            ln = norm(line)
            if re.match(r'^Section\s+[A-Z][a-z]', ln):
                if content_start_page is None:
                    content_start_page = p
                toc_lines.append("")
                toc_lines.append(ln)
            elif re.match(r'^SECTION\s+[A-Z]{3,}', ln):
                toc_lines.append("")
                toc_lines.append(ln)

        for m in re.finditer(r'Chapter\s+(\d+(?:\(\d+\))?)\s*:', normalized):
            ch_id = m.group(1)
            expected_chapters.add(ch_id)
            bare = re.match(r'^(\d+)', ch_id)
            if bare:
                expected_chapters.add(bare.group(1))

        for line in text.split('\n'):
            ln = norm(line)
            if re.match(r'^Chapter\s+\d+(\(\d+\))?\s*:', ln):
                toc_lines.append(ln)
            elif re.match(r'^This parva has\s+', ln):
                toc_lines.append(ln)
            elif re.match(r'^[A-Z].*[Pp]arva\s*$', ln) and len(ln) < 80:
                toc_lines.append(ln)
            elif re.match(r'^[A-Z]{2,}[\s-]+[A-Z]{2,}.*PARVA', ln):
                toc_lines.append(ln)

    if content_start_page is None:
        for p in range(start_page, min(start_page + 50, end_page)):
            text = doc[p].get_text()
            for line in text.split('\n'):
                ln = norm(line)
                if re.match(r'^Chapter\s+\d+\(\d+\)\s*:', ln):
                    content_start_page = p
                    break
            if content_start_page:
                break
    if content_start_page is None:
        content_start_page = start_page + 15

    # PHASE 2: Find Acknowledgements and Footnotes boundaries
    vol_midpoint = start_page + (end_page - start_page) // 2
    ack_page = None
    for p in range(vol_midpoint, end_page):
        blocks = doc[p].get_text('blocks')
        text_blocks = [norm(b[4]) for b in blocks if b[6] == 0 and norm(b[4])]
        for i, tb in enumerate(text_blocks):
            if re.match(r'^Acknowledgements?$', tb) and i <= 2:
                ack_page = p
                break
        if ack_page:
            break

    footnotes_start_page = None

    def _search_fn_pages(from_p, to_p):
        for p in range(from_p, to_p):
            text = doc[p].get_text()
            lines = [norm(l) for l in text.split('\n') if norm(l)]
            if not lines:
                continue
            if lines[0] == 'Footnotes':
                return p
            if re.match(r'^Section\s+', lines[0]):
                fn_lines = sum(1 for l in lines if re.match(r'^\d+\s*\S', l))
                if fn_lines >= 2:
                    return p
            fn_lines = sum(1 for l in lines if re.match(r'^\d+\s*[A-Za-z]', l))
            if fn_lines >= 3 and fn_lines >= len(lines) * 0.5:
                return p
        return None

    if ack_page:
        footnotes_start_page = _search_fn_pages(ack_page + 1, end_page)

    if not footnotes_start_page and ack_page:
        vol_half = (end_page - start_page) // 2
        search_from = max(content_start_page, ack_page - vol_half)
        footnotes_start_page = _search_fn_pages(search_from, ack_page)

    if not footnotes_start_page and not ack_page:
        search_from = end_page - max(1, (end_page - start_page) // 5)
        footnotes_start_page = _search_fn_pages(search_from, end_page)

    if footnotes_start_page:
        text = doc[footnotes_start_page].get_text()
        lines = [norm(l) for l in text.split('\n') if norm(l)]
        if len(lines) <= 3 and any('Footnotes' in l for l in lines):
            footnotes_start_page += 1

    body_end = end_page
    if ack_page:
        body_end = min(body_end, ack_page)
    if footnotes_start_page and footnotes_start_page < body_end:
        body_end = footnotes_start_page

    print(f"  Vol {vol}: content={content_start_page+1}, body_end={body_end}, "
          f"ack={ack_page+1 if ack_page else 'N/A'}, "
          f"fn={footnotes_start_page+1 if footnotes_start_page else 'N/A'}, "
          f"expected_ch={len(expected_chapters)}")

    # PHASE 3: Extract chapter text
    chapter_paragraphs = []
    prev_paragraph = ""
    in_section_header = False
    past_first_section = False
    for p in range(content_start_page, body_end):
        page = doc[p]
        raw_blocks = page.get_text('blocks')

        text_blocks = [b for b in raw_blocks if b[6] == 0]
        text_blocks.sort(key=lambda b: (b[1], b[0]))

        merged_blocks = []
        dropcap_indices = set()
        for i, b in enumerate(text_blocks):
            t = norm(b[4])
            if re.match(r'^[\u2018\u2019\u201c\u201d\'\"\u2029\s]*[A-Z][\u2018\u2019\u201c\u201d\'\"\u2029\s]*$', t) and b[0] < 100:
                best_j = None
                best_y0 = 99999
                for j in range(max(0, i - 3), min(i + 4, len(text_blocks))):
                    if j == i or j in dropcap_indices:
                        continue
                    nxt = text_blocks[j]
                    nt = norm(nxt[4])
                    dy = abs(nxt[1] - b[1])
                    if dy < 25 and nt and nt[0].islower() and nxt[1] < best_y0:
                        best_j = j
                        best_y0 = nxt[1]
                if best_j is not None:
                    nxt = text_blocks[best_j]
                    new_text = t + nxt[4].lstrip()
                    text_blocks[best_j] = (nxt[0], nxt[1], nxt[2], nxt[3], new_text, nxt[5], nxt[6])
                dropcap_indices.add(i)

        for i, b in enumerate(text_blocks):
            if i not in dropcap_indices:
                merged_blocks.append(b)

        blocks = merged_blocks

        for b in blocks:
            if b[6] != 0:
                continue
            raw_text = b[4]
            text = norm(raw_text)
            if not text:
                continue
            x0 = b[0]

            if len(text) < 80 and 'mahabharata' in text.lower():
                continue

            is_mixed_section = re.match(r'^Section\s+[A-Z][a-z]', text)
            is_allcaps_section = re.match(r'^SECTION\s+[A-Z]{3,}', text)
            if is_mixed_section or is_allcaps_section:
                if prev_paragraph:
                    chapter_paragraphs.append(prev_paragraph)
                    prev_paragraph = ""
                in_section_header = True
                if is_mixed_section:
                    past_first_section = True
                continue

            if in_section_header:
                if re.match(r'^[A-Z].*[Pp]arva', text) and len(text) < 120:
                    continue
                if re.match(r'^[A-Z]{2,}[\s-]+[A-Z]{2,}.*PARVA', text):
                    continue
                if re.match(r'^This parva has', text):
                    continue
                if re.match(r'^Chapter\s+\d+.*:\s+\d+\s+shlokas', text):
                    continue
                is_bare = re.match(r'^\d+$', text)
                is_paren = re.match(r'^\d+\s*\(\d+\)\s*\d*$', text)
                is_chapter_body = re.match(r'^(CHAPTER|Chapter)\s+\d+(\(\d+\))?\s*$', text)
                if not is_bare and not is_paren and not is_chapter_body:
                    if len(text) < 400 and text[0] not in ("'", '"'):
                        continue
                in_section_header = False

            is_bare = re.match(r'^\d+$', text)
            is_paren = re.match(r'^(\d+)\s*\((\d+)\)\s*\d*$', text)
            is_allcaps_ch = re.match(r'^CHAPTER\s+(\d+(?:\(\d+\))?)$', text)
            is_mixed_ch = re.match(r'^Chapter\s+(\d+(?:\(\d+\))?)$', text)

            ch_id = None
            if is_allcaps_ch:
                ch_id = is_allcaps_ch.group(1)
                past_first_section = True
            elif is_mixed_ch:
                ch_id = is_mixed_ch.group(1)
                past_first_section = True
            elif (is_bare or is_paren) and x0 >= 200 and past_first_section:
                ch_id = f"{is_paren.group(1)}({is_paren.group(2)})" if is_paren else text

            if ch_id:
                if prev_paragraph:
                    chapter_paragraphs.append(prev_paragraph)
                    prev_paragraph = ""
                chapter_paragraphs.append(f"--- Chapter {ch_id} ---")
                in_section_header = False
                continue
            elif is_allcaps_ch or is_mixed_ch:
                cid = (is_allcaps_ch or is_mixed_ch).group(1)
                if prev_paragraph:
                    chapter_paragraphs.append(prev_paragraph)
                    prev_paragraph = ""
                chapter_paragraphs.append(f"--- Chapter {cid} ---")
                in_section_header = False
                continue

            block_text = join_block_lines(raw_text)
            if not block_text:
                continue

            if prev_paragraph:
                first_char = block_text[0] if block_text else ''
                if prev_paragraph.endswith('-'):
                    prev_paragraph = prev_paragraph[:-1] + block_text
                    continue
                elif first_char.islower() or first_char == '(':
                    prev_paragraph += " " + block_text
                    continue
                elif ends_mid_sentence(prev_paragraph):
                    prev_paragraph += " " + block_text
                    continue
                else:
                    chapter_paragraphs.append(prev_paragraph)
                    prev_paragraph = block_text
            else:
                prev_paragraph = block_text

    if prev_paragraph:
        chapter_paragraphs.append(prev_paragraph)

    # PHASE 4: Extract footnotes
    footnote_lines = []
    if footnotes_start_page:
        current_footnote = ""
        last_fn_num = 0
        for p in range(footnotes_start_page, end_page):
            page_text = doc[p].get_text()
            if re.search(r'\bAcknowledgements?\b', norm(page_text)):
                continue
            if any(skip in page_text for skip in ['Let the conversation begin', 'PENGUIN', 'ISBN', 'Copyright', 'THE BEGINNING']):
                continue

            blocks = doc[p].get_text('blocks')
            for b in blocks:
                if b[6] != 0:
                    continue
                raw_text = b[4]
                text = norm(raw_text)
                if not text:
                    continue

                if len(text) < 80 and 'mahabharata' in text.lower():
                    continue

                ch_match = re.match(r'^Chapter\s+(\d+(?:\(\d+\))?)\s*$', text)
                if ch_match:
                    if current_footnote:
                        footnote_lines.append(current_footnote)
                        current_footnote = ""
                    footnote_lines.append(f"--- Chapter {ch_match.group(1)} ---")
                    last_fn_num = 0
                    continue

                if re.match(r'^Section\s+', text) and len(text) < 80:
                    if current_footnote:
                        footnote_lines.append(current_footnote)
                        current_footnote = ""
                    footnote_lines.append("")
                    footnote_lines.append(f"[{text}]")
                    continue

                if re.match(r'^[A-Z].*[Pp]arva', text) and len(text) < 80:
                    footnote_lines.append(f"[{text}]")
                    continue

                if text in ('Footnotes', 'Introduction'):
                    continue

                raw_lines = raw_text.split('\n')
                for raw_line in raw_lines:
                    line = norm(raw_line).strip()
                    if not line:
                        continue
                    fn_match = re.match(r'^(\d+)\s*[A-Za-z]', line)
                    if fn_match:
                        fn_num = int(fn_match.group(1))
                        if last_fn_num > 0 and fn_num != 1 and (fn_num > last_fn_num + 50 or fn_num < last_fn_num):
                            if current_footnote:
                                current_footnote += " " + line
                            else:
                                footnote_lines.append(line)
                            continue
                        if fn_num == 1 and last_fn_num > 1:
                            if current_footnote:
                                footnote_lines.append(current_footnote)
                                current_footnote = ""
                            footnote_lines.append("--- Chapter ---")
                        if current_footnote:
                            footnote_lines.append(current_footnote)
                        embed = re.search(r'([.!?])\s+(' + str(fn_num + 1) + r')\s+(\S)', line)
                        if embed:
                            before = line[:embed.start() + 1]
                            after = line[embed.start() + 2:]
                            current_footnote = before.strip()
                            footnote_lines.append(current_footnote)
                            current_footnote = after.strip()
                            last_fn_num = fn_num + 1
                        else:
                            current_footnote = line
                            last_fn_num = fn_num
                    else:
                        if current_footnote:
                            next_match = re.match(r'^(\d+)\s', line)
                            if next_match and int(next_match.group(1)) == last_fn_num + 1:
                                footnote_lines.append(current_footnote)
                                current_footnote = line
                                last_fn_num = int(next_match.group(1))
                            else:
                                embed = re.search(r'([.!?])\s+(' + str(last_fn_num + 1) + r')\s+(\S)', line)
                                if embed:
                                    before = line[:embed.start() + 1]
                                    after = line[embed.start() + 2:]
                                    current_footnote += " " + before.strip()
                                    footnote_lines.append(current_footnote)
                                    current_footnote = after.strip()
                                    last_fn_num = int(embed.group(2))
                                else:
                                    current_footnote += " " + line
                        else:
                            footnote_lines.append(line)

        if current_footnote:
            footnote_lines.append(current_footnote)

    first_ch = next((i for i, l in enumerate(footnote_lines) if l.startswith('--- Chapter')), 0)
    footnote_lines = footnote_lines[first_ch:]

    merged = []
    for line in footnote_lines:
        if line.startswith('--- Chapter') and merged:
            prev_ch_idx = None
            def_count = 0
            for j in range(len(merged) - 1, -1, -1):
                if merged[j].startswith('--- Chapter'):
                    prev_ch_idx = j
                    break
                elif re.match(r'^\d+\s', merged[j].strip()):
                    def_count += 1
            if prev_ch_idx is not None and def_count <= 1:
                defs_between = merged[prev_ch_idx + 1:]
                merged = merged[:prev_ch_idx]
                merged.append(line)
                merged.extend(defs_between)
                continue
        merged.append(line)
    footnote_lines = merged

    return toc_lines, chapter_paragraphs, footnote_lines


def clean_paragraphs(paragraphs):
    result = []
    i = 0
    while i < len(paragraphs):
        line = paragraphs[i]
        if line.startswith('--- Chapter'):
            result.append(line)
            i += 1
            continue
        stripped = line.strip()
        if re.match(r'^[\u2018\u2019\u201c\u201d\'\"\s]*[A-Z][\u2018\u2019\u201c\u201d\'\"\s]*$', stripped) and i + 1 < len(paragraphs):
            nxt = paragraphs[i + 1]
            if not nxt.startswith('--- Chapter'):
                result.append(stripped + nxt.lstrip())
                i += 2
                continue
        result.append(line)
        i += 1

    final = []
    for line in result:
        if line.startswith('--- Chapter'):
            final.append(line)
            continue
        if final and not final[-1].startswith('--- Chapter'):
            fc = line[0] if line else ''
            if fc.islower() or fc == '(':
                final[-1] += " " + line
                continue
            if ends_mid_sentence(final[-1]):
                final[-1] += " " + line
                continue
        final.append(line)

    first_ch = next((i for i, l in enumerate(final) if l.startswith('--- Chapter')), 0)
    final = final[first_ch:]

    seen_chapters = set()
    for i, line in enumerate(final):
        m = re.match(r'^--- Chapter (.+) ---$', line)
        if m:
            ch_id = m.group(1)
            if '(' in ch_id:
                if ch_id in seen_chapters:
                    cut = i
                    while cut > 0 and not final[cut - 1].startswith('--- Chapter'):
                        prev = final[cut - 1].strip()
                        if prev.upper().startswith('INTRODUCTION') or prev.startswith('Introduction'):
                            cut -= 1
                        else:
                            break
                    final = final[:cut]
                    break
                seen_chapters.add(ch_id)

    return final


def step1_extract(pdf_path, base_dir):
    """Extract PDF into toc, chapters, footnotes per volume."""
    print("=" * 60)
    print("STEP 1: Extracting PDF")
    print("=" * 60)

    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    for vol in range(1, 11):
        start_page = VOLUME_START_PAGES[vol]
        end_page = VOLUME_START_PAGES[vol + 1] if vol < 10 else total_pages

        print(f"\nProcessing Volume {vol}...")
        toc, chapters, footnotes = extract_volume(doc, vol, start_page, end_page)
        chapters = clean_paragraphs(chapters)

        ch_ids = [re.search(r'Chapter (.+) ---', l).group(1)
                  for l in chapters if l.startswith('--- Chapter')]
        ch_idx = 0
        for i, line in enumerate(footnotes):
            if line == '--- Chapter ---':
                if ch_idx < len(ch_ids):
                    footnotes[i] = f"--- Chapter {ch_ids[ch_idx]} ---"
                ch_idx += 1

        toc_path = os.path.join(base_dir, f'volume_{vol}_toc.txt')
        with open(toc_path, 'w', encoding='utf-8') as f:
            for line in toc:
                f.write(line + '\n')

        ch_path = os.path.join(base_dir, f'volume_{vol}_chapters.txt')
        with open(ch_path, 'w', encoding='utf-8') as f:
            for line in chapters:
                line = line.strip()
                if not line.startswith('--- Chapter'):
                    line = fix_footnote_refs(line)
                f.write(line + '\n')

        fn_path = os.path.join(base_dir, f'volume_{vol}_footnotes.txt')
        with open(fn_path, 'w', encoding='utf-8') as f:
            for line in footnotes:
                line = re.sub(r'^(\d+)([A-Za-z])', r'\1 \2', line)
                f.write(line + '\n')

        ch_count = sum(1 for l in chapters if l.startswith('--- Chapter'))
        para_count = sum(1 for l in chapters if l.strip() and not l.startswith('--- Chapter'))
        fn_count = sum(1 for l in footnotes if l.strip() and not l.startswith('['))
        print(f"  TOC: {len([l for l in toc if l.strip()])} lines")
        print(f"  Chapters: {ch_count} chapters, {para_count} paragraphs")
        print(f"  Footnotes: {fn_count} notes")

    doc.close()


# ================================================================
# STEP 1B: MANUAL FIXES FOR KNOWN OCR ISSUES
# ================================================================

def step1b_manual_fixes(base_dir):
    """Apply known manual fixes for OCR edge cases."""
    print("\n" + "=" * 60)
    print("STEP 1B: Applying manual fixes")
    print("=" * 60)

    fixes = 0

    # Vol 10 footnotes fix 1: duplicate "275" should be "276"
    # In Section 1, there are two lines starting with "275". The second one is OCR for "276".
    v10_fn = os.path.join(base_dir, 'volume_10_footnotes.txt')
    fn_text = open(v10_fn, encoding='utf-8').read()
    old_dup = "275 Each brahmana.\n275 There is a typo"
    new_dup = "275 Each brahmana.\n276 There is a typo"
    if old_dup in fn_text:
        fn_text = fn_text.replace(old_dup, new_dup)
        open(v10_fn, 'w', encoding='utf-8').write(fn_text)
        fixes += 1
        print("  Vol 10 footnotes: duplicate 275 -> 276")

    # Vol 10 footnotes fix 2: "l6For" should be split into separate def "16 For"
    old_fn = '15 Described in Section 60 (Volume 5). l6For the princesses of Kashi, Amba, Ambika and Ambalika. This has been described in Sec- tion 60.'
    new_fn = '15 Described in Section 60 (Volume 5).\n16 For the princesses of Kashi, Amba, Ambika and Ambalika. This has been described in Section 60.'
    if old_fn in fn_text:
        fn_text = fn_text.replace(old_fn, new_fn)
        open(v10_fn, 'w', encoding='utf-8').write(fn_text)
        fixes += 1
        print("  Vol 10 footnotes: split l6 -> 16, fix Sec- tion -> Section")

    # Vol 5 footnotes: def 12 and 13 are merged on one line in Section 2
    # "12 The text does not explicitly state...quotation marks. 13'Khatakhata'..."
    v5_fn = os.path.join(base_dir, 'volume_5_footnotes.txt')
    v5_text = open(v5_fn, encoding='utf-8').read()
    old_v5 = "quotation marks. 13\u2018Khatakhata\u2019"
    if old_v5 in v5_text:
        v5_text = v5_text.replace(old_v5, "quotation marks.\n13 \u2018Khatakhata\u2019")
        open(v5_fn, 'w', encoding='utf-8').write(v5_text)
        fixes += 1
        print("  Vol 5 footnotes: split def 12/13")
    else:
        # Try ASCII apostrophe variant
        old_v5_alt = "quotation marks. 13'Khatakhata'"
        if old_v5_alt in v5_text:
            v5_text = v5_text.replace(old_v5_alt, "quotation marks.\n13 'Khatakhata'")
            open(v5_fn, 'w', encoding='utf-8').write(v5_text)
            fixes += 1
            print("  Vol 5 footnotes: split def 12/13")

    print(f"  Applied {fixes} fixes")


# ================================================================
# STEP 2: ADD SECTION HEADERS TO FOOTNOTES
# ================================================================

def step2_add_sections(base_dir):
    """Add --- Section N --- and --- Chapters X to Y --- headers to footnotes."""
    print("\n" + "=" * 60)
    print("STEP 2: Adding section headers to footnotes")
    print("=" * 60)

    for v in range(1, 11):
        fn_lines = open(os.path.join(base_dir, f'volume_{v}_footnotes.txt'), encoding='utf-8').readlines()
        ch_lines = open(os.path.join(base_dir, f'volume_{v}_chapters.txt'), encoding='utf-8').readlines()

        # Build def-runs (split when number resets to 1)
        runs = []
        cur = []
        prev_max = 0
        for line in fn_lines:
            if line.startswith('---'):
                continue
            m = re.match(r'^(\d+)\s', line.strip())
            if m:
                d = int(m.group(1))
                if d == 1 and prev_max >= 10 and cur:
                    runs.append(cur)
                    cur = []
                    prev_max = 0
                cur.append(d)
                prev_max = max(prev_max, d)
        if cur:
            runs.append(cur)

        # Build chapter list with refs
        ch_list = []
        cur_ch = None
        cur_refs = []
        for line in ch_lines:
            m2 = re.match(r'^--- Chapter (.+?) ---', line.strip())
            if m2:
                if cur_ch is not None:
                    ch_list.append((cur_ch, cur_refs))
                cur_ch = m2.group(1)
                cur_refs = []
            elif cur_ch:
                cur_refs.extend(int(x) for x in re.findall(r'\{(\d+)\}', line))
        if cur_ch:
            ch_list.append((cur_ch, cur_refs))

        # Find ref-run boundaries
        best_bds = None
        best_diff = 999
        for threshold in [2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 50, 100]:
            bds = [0]
            rm = 0
            for i, (ch, refs) in enumerate(ch_list):
                if refs:
                    rmin = min(refs)
                    if rmin <= 3 and rm >= threshold and i > 0:
                        bds.append(i)
                        rm = 0
                    rm = max(rm, max(refs))
            diff = abs(len(bds) - len(runs))
            if diff < best_diff:
                best_diff = diff
                best_bds = bds
            if diff == 0:
                break

        # Chapter range per run
        run_headers = []
        for ri in range(len(best_bds)):
            si = best_bds[ri]
            ei = best_bds[ri + 1] if ri + 1 < len(best_bds) else len(ch_list)
            chs = [ch_list[i][0] for i in range(si, ei)]
            sec_num = ri + 1
            if chs:
                run_headers.append((f'--- Section {sec_num} ---',
                                    f'--- Chapters {chs[0]} to {chs[-1]} ---'))
            else:
                run_headers.append((f'--- Section {sec_num} ---', ''))

        # Rewrite footnotes file
        new_lines = []
        run_idx = 0
        prev_max_d = 0
        started = False
        written = [False] * len(runs)

        for line in fn_lines:
            if line.startswith('---'):
                continue
            m = re.match(r'^(\d+)\s', line.strip())
            if m:
                d = int(m.group(1))
                if d == 1 and prev_max_d >= 10 and started:
                    run_idx += 1
                ri = min(run_idx, len(run_headers) - 1)
                if not written[ri]:
                    if new_lines and new_lines[-1].strip():
                        new_lines.append('\n')
                    sec_hdr, ch_hdr = run_headers[ri]
                    new_lines.append(sec_hdr + '\n')
                    if ch_hdr:
                        new_lines.append(ch_hdr + '\n')
                    written[ri] = True
                    if d == 1:
                        prev_max_d = 0
                started = True
                prev_max_d = max(prev_max_d, d)
            new_lines.append(line)

        with open(os.path.join(base_dir, f'volume_{v}_footnotes.txt'), 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        print(f"  Vol {v}: {len(run_headers)} sections")


# ================================================================
# STEP 3: VERIFY FOOTNOTE MATCHING
# ================================================================

def step3_verify(base_dir):
    """Verify all {N} refs in chapters match defs in footnotes."""
    print("\n" + "=" * 60)
    print("STEP 3: Verifying footnote matching")
    print("=" * 60)

    all_ok = True
    total_refs_all = 0
    total_matched_all = 0

    for v in range(1, 11):
        fn_lines = open(os.path.join(base_dir, f'volume_{v}_footnotes.txt'), encoding='utf-8').readlines()
        ch_lines = open(os.path.join(base_dir, f'volume_{v}_chapters.txt'), encoding='utf-8').readlines()

        # Parse defs
        all_defs = []
        for line in fn_lines:
            if line.startswith('--- '):
                continue
            m = re.match(r'^(\d+)\s', line.strip())
            if m:
                all_defs.append(int(m.group(1)))

        # Parse refs
        ch_list = []
        cur_ch = None
        cur_refs = []
        for line in ch_lines:
            m = re.match(r'^--- Chapter (.+?) ---', line.strip())
            if m:
                if cur_ch is not None:
                    ch_list.append((cur_ch, cur_refs))
                cur_ch = m.group(1)
                cur_refs = []
            elif cur_ch:
                cur_refs.extend(int(x) for x in re.findall(r'\{(\d+)\}', line))
        if cur_ch is not None:
            ch_list.append((cur_ch, cur_refs))

        # Build def-runs and ref-run boundaries (adaptive threshold)
        best_def_runs = None
        best_boundaries = None
        best_diff = 999
        for threshold in [2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 50, 100]:
            # def-runs
            dr = []
            cur_set = set()
            pm = 0
            for d in all_defs:
                if d == 1 and pm >= threshold and cur_set:
                    dr.append(cur_set)
                    cur_set = set()
                    pm = 0
                cur_set.add(d)
                pm = max(pm, d)
            if cur_set:
                dr.append(cur_set)
            # ref-run boundaries
            bds = [0]
            rm = 0
            for i, (ch, refs) in enumerate(ch_list):
                if refs:
                    rmin = min(refs)
                    rmax = max(refs)
                    if rmin <= 3 and rm >= threshold and i > 0:
                        bds.append(i)
                        rm = 0
                    rm = max(rm, rmax)
            diff = abs(len(dr) - len(bds))
            if diff < best_diff:
                best_diff = diff
                best_def_runs = dr
                best_boundaries = bds
            if diff == 0:
                break

        def_runs = best_def_runs
        boundaries = best_boundaries

        # Map chapters to runs
        ch_to_run = [0] * len(ch_list)
        for i in range(len(ch_list)):
            run_idx = 0
            for bi, b in enumerate(boundaries):
                if b <= i:
                    run_idx = bi
                else:
                    break
            ch_to_run[i] = min(run_idx, len(def_runs) - 1)

        # Check unmatched
        unmatched = []
        for i, (ch, refs) in enumerate(ch_list):
            di = ch_to_run[i]
            defs = def_runs[di]
            for r in refs:
                if r not in defs:
                    unmatched.append((ch, r))

        total_refs = sum(len(r) for _, r in ch_list)
        total_defs = sum(len(d) for d in def_runs)
        matched = total_refs - len(unmatched)
        pct = f'{matched/total_refs*100:.1f}%' if total_refs else '0%'

        total_refs_all += total_refs
        total_matched_all += matched

        status = "OK" if not unmatched else "MISMATCH"
        if unmatched:
            all_ok = False
        print(f"  Vol {v}: {matched}/{total_refs} ({pct}) {status}")

    print(f"\n  Total: {total_matched_all}/{total_refs_all} matched")
    return all_ok


# ================================================================
# STEP 4: BUILD CHARACTER DATABASE
# ================================================================

def step4_characters(base_dir):
    """Extract characters with relationships, write characters.json."""
    print("\n" + "=" * 60)
    print("STEP 4: Building character knowledge graph")
    print("=" * 60)

    # ── Data model ──────────────────────────────────────────────
    chars = {}  # key -> dict

    def _key(name):
        return name.strip().lower().replace(' ', '_')

    def add(primary, *, aliases=None, father=None, mother=None,
            siblings=None, spouse=None, gender=None,
            caste=None, duty=None, dynasty=None, status=None):
        """spouse: list of strings OR list of (name, relation) tuples.
           Plain strings default to relation 'Wife'/'Husband' based on gender."""
        k = _key(primary)
        if k not in chars:
            chars[k] = {'name': primary.strip(), 'aliases': set(),
                        'father': None, 'mother': None,
                        'siblings': set(), 'spouse': [],
                        'gender': 'Unknown',
                        'caste': '', 'duty': '', 'dynasty': '', 'status': ''}
        c = chars[k]
        if aliases:
            for a in aliases:
                a = a.strip()
                if a and a != c['name']:
                    c['aliases'].add(a)
        if father:
            c['father'] = _key(father)
        if mother:
            c['mother'] = _key(mother)
        if siblings:
            for s in siblings:
                c['siblings'].add(_key(s))
        if spouse:
            for sp in spouse:
                if isinstance(sp, tuple):
                    sp_name, sp_rel = sp
                else:
                    sp_name, sp_rel = sp, None  # resolve later
                sk = _key(sp_name)
                # Check if already present
                existing = [i for i, (s, r) in enumerate(c['spouse']) if s == sk]
                if existing:
                    # Update relation if was None
                    if sp_rel and not c['spouse'][existing[0]][1]:
                        c['spouse'][existing[0]] = (sk, sp_rel)
                else:
                    c['spouse'].append((sk, sp_rel))
        if gender and gender != 'Unknown':
            c['gender'] = gender
        if caste and not c['caste']:
            c['caste'] = caste
        if duty and not c['duty']:
            c['duty'] = duty
        if dynasty and not c['dynasty']:
            c['dynasty'] = dynasty
        if status and not c['status']:
            c['status'] = status

    def _spouse_keys(c):
        """Return list of spouse keys from the (key, relation) tuple list."""
        return [s for s, r in c['spouse']]

    _alias_map = {}

    def _rebuild_alias_map():
        _alias_map.clear()
        for k, c in chars.items():
            for a in c['aliases']:
                ak = _key(a)
                if ak != k:
                    _alias_map[ak] = k

    def ensure(name, gender=None):
        k = _key(name)
        if k in _alias_map:
            parent = _alias_map[k]
            if gender and gender != 'Unknown' and parent in chars:
                if chars[parent]['gender'] == 'Unknown':
                    chars[parent]['gender'] = gender
            return parent
        if k not in chars:
            chars[k] = {'name': name.strip(), 'aliases': set(),
                        'father': None, 'mother': None,
                        'siblings': set(), 'spouse': [],
                        'gender': gender or 'Unknown',
                        'caste': '', 'duty': '', 'dynasty': '', 'status': ''}
        elif gender and gender != 'Unknown' and chars[k]['gender'] == 'Unknown':
            chars[k]['gender'] = gender
        return k

    # ── Phase 1: Core characters with full relationships ────────
    # Pandavas
    add("Yudhishthira", aliases=["Dharmaraja","Dharmaputra","Ajatashatru",
        "Bharata","Kouravya","Pandaveya"],
        father="Pandu", mother="Kunti",
        siblings=["Bhima","Arjuna","Nakula","Sahadeva"],
        spouse=["Draupadi"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Alive")
    add("Bhima", aliases=["Bhimasena","Vrikodara"],
        father="Pandu", mother="Kunti",
        siblings=["Yudhishthira","Arjuna","Nakula","Sahadeva"],
        spouse=[("Draupadi","Wife"),("Hidimba","Gandharva marriage")], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Alive")
    add("Arjuna", aliases=["Partha","Dhananjaya","Savyasachi","Gudakesha",
        "Phalguna","Kiriti","Bibhatsu","Vijaya","Shvetavahana","Jishnu",
        "Kaunteya","Kounteya","Gandivadhanva"],
        father="Pandu", mother="Kunti",
        siblings=["Yudhishthira","Bhima","Nakula","Sahadeva"],
        spouse=[("Draupadi","Wife"),("Subhadra","Wife"),("Ulupi","Wife"),("Chitrangada_manipura","Wife")], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Alive")
    add("Nakula", father="Pandu", mother="Madri",
        siblings=["Yudhishthira","Bhima","Arjuna","Sahadeva"],
        spouse=["Draupadi"], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Alive")
    add("Sahadeva", father="Pandu", mother="Madri",
        siblings=["Yudhishthira","Bhima","Arjuna","Nakula"],
        spouse=["Draupadi"], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Alive")

    # Kauravas - 100 sons of Gandhari + 1 daughter (Duhshala) + Yuyutsu from Sughada
    # Birth order per Adi Parva Ch.108
    _kaurava_sons = [
        "Duryodhana","Duhshasana","Duhsaha","Jalasandha","Sama_kaurava","Saha",
        "Vinda","Anuvinda","Durdharsha","Subahu","Dushpradharshana",
        "Durmarshana","Durmukha","Dushkarma","Karna_kaurava","Vivimshati",
        "Vikarna","Sulochana","Chitra","Upachitra","Chitraksha",
        "Charuchitra","Sharasana","Durmada","Dushpragaha","Vivitsu",
        "Vikata","Urnanabha","Sunabha","Nanda_kaurava","Upanandaka","Senapati",
        "Sushena","Kundodara","Mahodara","Chitrabana","Chitravarma",
        "Suvarma","Durvimochana","Ayobahu","Mahabahu_kaurava","Chitranga",
        "Chitrakundala","Bhimavega","Bhimabala","Balaki","Balavardhana",
        "Ugrayudha","Bhimakarma","Kanakayu","Dridhayudha","Dridhavarma",
        "Dridhakshatra","Somakirti","Anudara","Dridhasandha","Jarasandha_kaurava",
        "Satyasandha","Sadahsuvak","Ugrashrava","Ashvasena_kaurava","Senani",
        "Dushparajaya","Aparajita","Panditaka","Vishalaksha","Duravara",
        "Dridhahasta","Suhasta","Vatavega","Suvarcha","Adityaketu",
        "Bahvashi","Nagadanta","Ugrayayi","Kavachi","Nishangi","Pashi_kaurava",
        "Dandadhara_kaurava","Dhanurgraha","Ugra_kaurava","Bhimaratha","Vira_kaurava",
        "Virabahu","Alolupa","Abhaya","Roudrakarma","Dridharatha",
        "Anadhrishya","Kundabhedi","Viravi","Dirghalochana","Dirghabahu",
        "Mahabahu_kaurava2","Vyudhoru","Kanakadhvaja","Kundashi","Viraja",
        "Chitrasena_kaurava",
    ]
    # Key named Kauravas with extra detail
    add("Duryodhana", aliases=["Suyodhana"],
        father="Dhritarashtra", mother="Gandhari",
        spouse=["Bhanumati"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased")
    add("Duhshasana", aliases=["Duhshaasana"],
        father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Vikarna", father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Vivimshati", father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Durmukha", father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Chitrasena_kaurava", aliases=["Chitrasena"],
        father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Karna_kaurava", aliases=["Karna (Kaurava)"],
        father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Sama_kaurava", aliases=["Sama"],
        father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    # All remaining Kaurava sons
    for name in _kaurava_sons:
        k = name.lower().replace(' ', '_')
        if k not in chars:
            add(name, father="Dhritarashtra", mother="Gandhari",
                gender="Male", caste="Kshatriya", duty="Prince",
                dynasty="Kuru", status="Deceased")
    # Set siblings: all Kauravas are siblings of each other
    all_kaurava_keys = [_key(n) for n in _kaurava_sons] + [_key("Duhshala"), _key("Yuyutsu")]
    for kk in all_kaurava_keys:
        if kk in chars:
            chars[kk]['siblings'] = {s for s in all_kaurava_keys if s != kk and s in chars}
    # Daughter
    add("Duhshala", father="Dhritarashtra", mother="Gandhari",
        spouse=["Jayadratha"], gender="Female",
        caste="Kshatriya", duty="Princess", dynasty="Kuru")
    # Yuyutsu - from Sughada (concubine)
    add("Yuyutsu", father="Dhritarashtra", mother="Sughada",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru")
    add("Chitrasena_gandharva", aliases=["Chitrasena","gandharva king"],
        gender="Male", caste="Gandharva", duty="King")
    add("Lakshmana_kaurava", aliases=["Lakshmana"],
        father="Duryodhana", gender="Male",
        caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Bhanumati", spouse=["Duryodhana"], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru")

    # Kuru elders
    add("Dhritarashtra", aliases=["Dhritarasthra","Dritarashtra","Dhritrarashtra"],
        father="Vichitravirya", mother="Ambika",
        spouse=[("Gandhari","Wife"), ("Sughada","Concubine")],
        siblings=["Pandu","Vidura"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased")
    add("Sughada", aliases=["Vaishya maid","Vaishya woman"],
        spouse=[("Dhritarashtra","Concubine")], gender="Female",
        caste="Vaishya", dynasty="Kuru")
    add("Pandu", father="Vichitravirya", mother="Ambalika",
        spouse=[("Kunti","Wife"),("Madri","Wife")],
        siblings=["Dhritarashtra","Vidura"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased")
    add("Vidura", aliases=["Kshatta"],
        siblings=["Dhritarashtra","Pandu"], gender="Male",
        caste="Kshatriya", duty="Minister", dynasty="Kuru", status="Deceased")
    add("Kunti", aliases=["Pritha"],
        father="Shurasena",
        spouse=[("Pandu","Husband"),("Surya","Divine boon"),("Yama","Divine boon"),("Vayu","Divine boon"),("Indra","Divine boon")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru", status="Deceased")
    add("Madri", spouse=[("Pandu","Husband"),("Ashvins","Divine boon")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru", status="Deceased")
    add("Gandhari", father="Subala",
        spouse=[("Dhritarashtra","Husband")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru", status="Deceased")

    # Bhishma's line
    add("Bhishma", aliases=["Devavrata","Gangeya","Shantanava"],
        father="Shantanu", mother="Ganga", gender="Male",
        caste="Kshatriya", duty="Regent", dynasty="Kuru", status="Deceased")
    add("Shantanu", aliases=["king of Hastinapura"],
        spouse=[("Ganga","Wife"),("Satyavati","Wife")],
        father="Pratipa", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased")
    add("Ganga", aliases=["Bhagirathi","Jahnavi"],
        spouse=["Shantanu"], gender="Female",
        duty="River goddess", status="Immortal")
    add("Satyavati", aliases=["Matsyagandha","Kali"],
        spouse=[("Shantanu","Husband"),("Parashara","Pre-marital union")], gender="Female",
        duty="Queen", dynasty="Kuru", status="Deceased")
    add("Vichitravirya",
        father="Shantanu", mother="Satyavati",
        siblings=["Chitrangada_kuru"],
        spouse=[("Ambika","Wife"),("Ambalika","Wife")], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased")
    add("Chitrangada_kuru", aliases=["Chitrangada"],
        father="Shantanu", mother="Satyavati",
        siblings=["Vichitravirya"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased")
    add("Ambika", spouse=[("Vichitravirya","Husband"),("Vyasa","Niyoga")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru")
    add("Ambalika", spouse=[("Vichitravirya","Husband"),("Vyasa","Niyoga")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru")
    add("Amba", gender="Female", caste="Kshatriya", duty="Princess")

    # Vyasa
    add("Vyasa", aliases=["Krishna Dvaipayana","Vedavyasa","Dvaipayana"],
        father="Parashara", mother="Satyavati",
        spouse=[("Ambika","Niyoga"),("Ambalika","Niyoga")],
        gender="Male",
        caste="Brahmin", duty="Sage", status="Immortal")
    add("Parashara", spouse=[("Satyavati","Pre-marital union")],
        gender="Male", caste="Brahmin", duty="Sage")
    add("Shuka", aliases=["son of Vyasa"],
        father="Vyasa", gender="Male",
        caste="Brahmin", duty="Sage")

    # Krishna's family
    add("Krishna", aliases=["Vasudeva","Vaasudeva","Keshava","Govinda","Madhava",
        "Janardana","Achyuta","Hari","Hrishikesha","Madhusudana","Damodara",
        "Vrishni","Varshneya","Dasharha","Pundarikaksha","Shouri","Purushottama"],
        father="Vasudeva_father", mother="Devaki",
        siblings=["Balarama","Subhadra"],
        spouse=[("Rukmini","Wife"),("Satyabhama","Wife"),("Jambavati","Wife")], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Yadava", status="Deceased")
    add("Balarama", aliases=["Baladeva","Halayudhu","Haladhara","Sankarshana"],
        father="Vasudeva_father", mother="Rohini",
        siblings=["Krishna","Subhadra"],
        spouse=["Revati"], gender="Male",
        caste="Kshatriya", duty="Prince", dynasty="Yadava", status="Deceased")
    add("Subhadra",
        father="Vasudeva_father",
        siblings=["Krishna","Balarama"],
        spouse=["Arjuna"], gender="Female",
        caste="Kshatriya", duty="Princess", dynasty="Yadava")
    add("Vasudeva_father", aliases=["Vasudeva","Anakadundubhi"],
        father="Shurasena",
        spouse=[("Devaki","Wife"),("Rohini","Wife")], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Yadava")
    add("Devaki", spouse=["Vasudeva_father"], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Yadava")
    add("Rohini", spouse=["Vasudeva_father"], gender="Female",
        caste="Kshatriya", dynasty="Yadava")
    add("Rukmini", aliases=["daughter of Bhishmaka"],
        father="Bhishmaka",
        spouse=["Krishna"], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Yadava")
    add("Satyabhama", spouse=["Krishna"], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Yadava")
    add("Jambavati", spouse=["Krishna"], gender="Female",
        duty="Queen", dynasty="Yadava")
    add("Pradyumna", father="Krishna", mother="Rukmini", gender="Male",
        caste="Kshatriya", duty="Prince", dynasty="Yadava")
    add("Samba", father="Krishna", mother="Jambavati", gender="Male",
        caste="Kshatriya", duty="Prince", dynasty="Yadava")
    add("Revati", spouse=["Balarama"], gender="Female",
        duty="Queen", dynasty="Yadava")

    # Karna's family
    add("Karna", aliases=["Radheya","Vasusena","Anga-raja","Vrisha","Vaikartana"],
        mother="Kunti", father="Surya",
        spouse=[("Vrushali","Wife")], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Anga", status="Deceased")
    add("Vrishasena", father="Karna", mother="Vrushali", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Anga", status="Deceased")
    add("Vrishaketu", father="Karna", mother="Vrushali", gender="Male",
        caste="Kshatriya", dynasty="Anga")
    add("Radha", aliases=["Karna's foster mother"],
        spouse=["Adhiratha"], gender="Female",
        caste="Suta")
    add("Adhiratha", spouse=["Radha"], gender="Male",
        caste="Suta", duty="Charioteer")
    add("Vrushali", spouse=["Karna"], gender="Female")

    # Next generation - Upapandavas (Draupadi's 5 sons, one from each Pandava)
    add("Prativindhya", father="Yudhishthira", mother="Draupadi", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased")
    add("Sutasoma", father="Bhima", mother="Draupadi", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased")
    add("Shrutakirti", father="Arjuna", mother="Draupadi", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased")
    add("Shatanika", father="Nakula", mother="Draupadi", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased")
    add("Shrutasena", father="Sahadeva", mother="Draupadi", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased")
    # Other children
    add("Abhimanyu", aliases=["Soubhadra"],
        father="Arjuna", mother="Subhadra",
        spouse=["Uttaraa"], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased")
    add("Ghatotkacha", father="Bhima", mother="Hidimba", gender="Male",
        caste="Rakshasa", duty="Warrior", status="Deceased")
    add("Parikshit", father="Abhimanyu", mother="Uttaraa", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru")
    add("Babhruvahana", father="Arjuna", mother="Chitrangada_manipura",
        gender="Male", caste="Kshatriya", duty="King")
    add("Iravan", father="Arjuna", mother="Ulupi", gender="Male",
        caste="Kshatriya", duty="Warrior", status="Deceased")
    add("Uttaraa", spouse=["Abhimanyu"], gender="Female",
        caste="Kshatriya", duty="Princess", dynasty="Matsya")

    # Drona's family
    add("Drona", aliases=["Dronacharya","preceptor","acharya"],
        father="Bharadvaja",
        spouse=["Kripi"], gender="Male",
        caste="Brahmin", duty="Teacher", dynasty="Kuru", status="Deceased")
    add("Ashvatthama", aliases=["Dronaputra"],
        father="Drona", mother="Kripi", gender="Male",
        caste="Brahmin", duty="Warrior", dynasty="Kuru", status="Immortal")
    add("Bharadvaja", gender="Male", caste="Brahmin", duty="Sage")
    add("Kripi", aliases=["Sharadvati"],
        father="Sharadvat",
        siblings=["Kripa"],
        spouse=["Drona"], gender="Female",
        caste="Brahmin")
    add("Kripa", aliases=["Kripacharya","Sharadvata","Goutama"],
        father="Sharadvat",
        siblings=["Kripi"], gender="Male",
        caste="Brahmin", duty="Teacher", dynasty="Kuru", status="Immortal")
    add("Sharadvat", gender="Male", caste="Brahmin", duty="Sage")

    # Drupada's family
    add("Drupada", aliases=["Yajnasena","Parshata"],
        father="Prishata", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Panchala", status="Deceased")
    add("Draupadi", aliases=["Droupadi","Panchali","Krishnaa","Yajnaseni"],
        father="Drupada",
        siblings=["Dhrishtadyumna","Shikhandi"],
        spouse=[("Yudhishthira","Husband"),("Bhima","Husband"),("Arjuna","Husband"),("Nakula","Husband"),("Sahadeva","Husband")],
        gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Panchala")
    add("Dhrishtadyumna", aliases=["Panchala prince"],
        father="Drupada",
        siblings=["Draupadi","Shikhandi"], gender="Male",
        caste="Kshatriya", duty="Commander", dynasty="Panchala", status="Deceased")
    add("Shikhandi", father="Drupada",
        siblings=["Draupadi","Dhrishtadyumna"], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Panchala", status="Deceased")
    add("Prishata", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Panchala", status="Deceased")

    # Other key characters
    add("Jayadratha", aliases=["Saindhava","king of Sindhu"],
        spouse=["Duhshala"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Sindhu", status="Deceased")
    add("Shakuni", aliases=["Soubala"],
        father="Subala", siblings=["Gandhari"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Gandhara", status="Deceased")
    add("Subala", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Gandhara", status="Deceased")
    add("Shalya", aliases=["king of Madra","Madra king"],
        siblings=["Madri"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Madra", status="Deceased")
    add("Ekalavya", aliases=["Nishada prince"], gender="Male",
        caste="Nishada", duty="Warrior")
    add("Shishupala", aliases=["king of Chedi","Chedi king"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Chedi", status="Deceased")
    add("Jarasandha", aliases=["king of Magadha"],
        father="Brihadratha", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Magadha", status="Deceased")
    add("Virata", aliases=["king of Matsya"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Matsya", status="Deceased")
    add("Kritavarma", aliases=["Hardikya"],
        father="Hridika", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Yadava")
    add("Satyaki", aliases=["Yuyudhana","Satvata"], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Yadava")
    add("Bhagadatta", aliases=["king of Pragjyotisha"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Pragjyotisha", status="Deceased")
    add("Bhurishrava", father="Somadatta", gender="Male",
        caste="Kshatriya", duty="Warrior", status="Deceased")
    add("Susharma", aliases=["king of Trigarta"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Trigarta")
    add("Dhrishtaketu", aliases=["king of Chedi"],
        father="Shishupala", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Chedi", status="Deceased")
    add("Sanjaya", aliases=["Dhritarashtra's aide"],
        father="Gavalgana", gender="Male",
        caste="Suta", duty="Charioteer", dynasty="Kuru")
    add("Hidimba", spouse=[("Bhima","Gandharva marriage")], gender="Female",
        caste="Rakshasa")
    add("Chitrangada_manipura", aliases=["Chitrangada"],
        spouse=["Arjuna"], gender="Female",
        caste="Kshatriya", duty="Princess", dynasty="Manipura")

    # Gods / divine
    add("Indra", aliases=["Shatakratu","Shakra","Purandara","Vasava",
        "Maghavan","lord of the gods","king of the gods"],
        spouse=[("Kunti","Divine boon")],
        gender="Male",
        caste="Deva", duty="King of gods", status="Immortal")
    add("Brahma", aliases=["Prajapati","Pitamaha","creator"], gender="Male",
        caste="Deva", duty="Creator", status="Immortal")
    add("Vishnu", aliases=["Narayana","Preserver"], gender="Male",
        caste="Deva", duty="Preserver", status="Immortal")
    add("Shiva", aliases=["Mahadeva","Maheshvara","Rudra","Pashupati","Bhava",
        "Hara","Tryambaka","Shankar","Shankara","Pinaka","Sthanu"], gender="Male",
        caste="Deva", duty="Destroyer", status="Immortal")
    add("Yama", aliases=["Dharma","god of death","lord of the dead"],
        spouse=[("Kunti","Divine boon")],
        gender="Male",
        caste="Deva", duty="God of death", status="Immortal")
    add("Vayu", aliases=["wind-god"],
        spouse=[("Kunti","Divine boon")],
        gender="Male",
        caste="Deva", duty="Wind god", status="Immortal")
    add("Surya", aliases=["sun-god","Aditya","Vivasvat","Vivasvata"],
        spouse=[("Kunti","Divine boon")],
        gender="Male",
        caste="Deva", duty="Sun god", status="Immortal")
    add("Agni", aliases=["fire-god","Pavaka","Hutashana"], gender="Male",
        caste="Deva", duty="Fire god", status="Immortal")
    add("Ashvins", aliases=["Ashwini Kumaras","Nasatya","Dasra"],
        spouse=[("Madri","Divine boon")],
        gender="Male",
        caste="Deva", duty="Divine physicians", status="Immortal")
    add("Varuna", aliases=["lord of the waters","water-god"], gender="Male",
        caste="Deva", duty="Water god", status="Immortal")
    add("Kubera", aliases=["Vaishravana","Dhanada","god of wealth"],
        father="Vishrava", gender="Male",
        caste="Deva", duty="God of wealth", status="Immortal")
    add("Kartikeya", aliases=["Skanda","Kumara","Subrahmanya"],
        father="Shiva", mother="Parvati", gender="Male",
        caste="Deva", duty="God of war", status="Immortal")
    add("Lakshmi", aliases=["Shri"], spouse=["Vishnu"], gender="Female",
        caste="Deva", duty="Goddess of fortune", status="Immortal")
    add("Parvati", aliases=["Uma"], spouse=["Shiva"], gender="Female",
        caste="Deva", duty="Goddess", status="Immortal")
    add("Sarasvati", aliases=["goddess of learning"],
        spouse=["Brahma"], gender="Female",
        caste="Deva", duty="Goddess of learning", status="Immortal")

    # Narrators / sages
    add("Ugrasrava", aliases=["Souti"],
        father="Lomaharshana", gender="Male",
        caste="Suta", duty="Narrator")
    add("Vaishampayana", aliases=["narrator"], gender="Male",
        caste="Brahmin", duty="Sage")
    add("Janamejaya", father="Parikshit", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru")
    add("Narada", aliases=["divine sage","Devarshi"], gender="Male",
        caste="Deva", duty="Sage", status="Immortal")
    add("Parashurama", aliases=["Bhargava","Rama"],
        father="Jamadagni", mother="Renuka", gender="Male",
        caste="Brahmin", duty="Warrior sage", status="Immortal")
    add("Hanuman", father="Vayu", mother="Anjana", gender="Male",
        caste="Vanara", duty="Warrior", status="Immortal")

    # Epic / embedded story characters
    add("Nala", aliases=["Nishadha","Punyashloka","Bahuka","king of Nishadha"],
        spouse=["Damayanti"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Nishadha")
    add("Damayanti", father="Bhima_vidarbha", spouse=["Nala"], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Vidarbha")
    add("Bhima_vidarbha", aliases=["king of Vidarbha"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Vidarbha")
    add("Savitri", spouse=["Satyavan"], gender="Female",
        caste="Kshatriya", duty="Princess")
    add("Satyavan", spouse=["Savitri"], gender="Male",
        caste="Kshatriya")
    add("Ravana", aliases=["king of Lanka","Rakshasa king"], gender="Male",
        caste="Rakshasa", duty="King", dynasty="Lanka", status="Deceased")
    add("Sugriva", aliases=["monkey king"], gender="Male",
        caste="Vanara", duty="King")
    add("Prahlada", father="Hiranyakashipu", gender="Male",
        caste="Daitya")
    add("Hiranyakashipu", gender="Male",
        caste="Daitya", duty="King", status="Deceased")

    # More warriors / kings
    add("Bahlika", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased")
    add("Bhagiratha", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Ikshvaku")
    add("Rituparna", aliases=["king of Ayodhya"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Ikshvaku")
    add("Marutta", father="Avikshit", gender="Male",
        caste="Kshatriya", duty="King")
    add("Brihadbala", gender="Male",
        caste="Kshatriya", duty="Warrior", status="Deceased")
    add("Chekitana", gender="Male",
        caste="Kshatriya", duty="Warrior")
    add("Somadatta", gender="Male",
        caste="Kshatriya", duty="King")
    add("Hridika", gender="Male",
        caste="Kshatriya", dynasty="Yadava")
    add("Gavalgana", gender="Male", caste="Suta")
    add("Lomaharshana", gender="Male", caste="Suta", duty="Narrator")
    add("Bhishmaka", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Vidarbha")
    add("Shurasena", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Yadava")
    add("Pratipa", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased")
    add("Brihadratha", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Magadha", status="Deceased")
    add("Vishrava", gender="Male", caste="Brahmin", duty="Sage")
    add("Jamadagni", gender="Male", caste="Brahmin", duty="Sage")
    add("Renuka", gender="Female")
    add("Anjana", gender="Female", caste="Vanara")
    add("Avikshit", gender="Male", caste="Kshatriya", duty="King")
    add("Ulupi", spouse=["Arjuna"], gender="Female",
        caste="Naga", duty="Princess")
    add("Uttara", father="Virata", gender="Male",
        caste="Kshatriya", duty="Prince", dynasty="Matsya", status="Deceased")

    # Sages
    add("Agastya", aliases=["Agasti"], gender="Male",
        caste="Brahmin", duty="Sage")
    add("Vasishtha", aliases=["Vashishtha"], gender="Male",
        caste="Brahmin", duty="Sage")
    add("Galava", gender="Male", caste="Brahmin", duty="Sage")
    add("Ashtavakra", gender="Male", caste="Brahmin", duty="Sage")
    add("Kapila", gender="Male", caste="Brahmin", duty="Sage")
    add("Devala", gender="Male", caste="Brahmin", duty="Sage")
    add("Ushanas", aliases=["Shukra","Shukracharya","preceptor of the demons"],
        gender="Male", caste="Brahmin", duty="Sage", status="Immortal")
    add("Matali", aliases=["Indra's charioteer"], gender="Male",
        caste="Deva", duty="Charioteer")
    add("Vritra", aliases=["demon"], gender="Male",
        caste="Asura", status="Deceased")
    add("Nara", gender="Male", caste="Deva", duty="Sage")
    add("Daruka", aliases=["Krishna's charioteer"], gender="Male",
        duty="Charioteer", dynasty="Yadava")
    add("Manu", aliases=["Vaivasvata"], gender="Male",
        duty="Progenitor")

    # Remaining core
    add("Aditi", gender="Female", caste="Deva", duty="Mother of gods")
    add("Daksha", aliases=["Prajapati"], gender="Male",
        caste="Deva", duty="Prajapati")
    add("Kashyapa", gender="Male", caste="Brahmin", duty="Sage")
    add("Soma", gender="Male", caste="Deva")
    add("Takshaka", gender="Male", caste="Naga", duty="King")
    add("Vinata", gender="Female")
    add("Kadru", gender="Female")
    add("Garuda", aliases=["Suparna"], mother="Vinata", gender="Male",
        duty="Mount of Vishnu")
    add("Yadu", gender="Male",
        caste="Kshatriya", dynasty="Yadava")
    add("Puru", gender="Male",
        caste="Kshatriya", dynasty="Puru")
    add("Sagara", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Ikshvaku")
    add("Mandhata", aliases=["Mandhatar"], father="Yuvanashva", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Ikshvaku")
    add("Muchukunda", gender="Male",
        caste="Kshatriya", duty="King")
    add("Samvarana", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru")
    add("Rishyashringa", gender="Male",
        caste="Brahmin", duty="Sage")
    add("Svayambhu", gender="Male")

    # Build alias lookup from hardcoded characters
    _rebuild_alias_map()

    # ── Phase 2: Auto-extraction from text ──────────────────────
    SKIP = {'the','that','this','these','those','which','where','when','what','also',
            'here','there','thus','hence','therefore','however','since','with','from',
            'into','onto','about','above','below','between','through','during','before',
            'after','meaning','means','called','known','because','although','though',
            'only','even','just','more','very','much','many','some','most','other',
            'each','every','been','being','having','would','could','should','might',
            'shall','will','can','may','must','used','one','two','three','four','five',
            'not','but','and','for','are','was','were','has','had','his','her','its',
            'who','whom','why','how','all','any','few','own','same','such','than',
            'too','according','refers','reference','literally','translated','been',
            'another','sometimes','generally','probably','perhaps','certain','various',
            'different','several','among','usually','often','name','word','text',
            'section','chapter','volume','parva','still','like','described',
            'mentioned','simply','particularly','especially','speci',
            'tell','listen','look','behold','hear','please','both','together',
            'today','whether','wishing','desiring','knowing','seeing','hearing',
            'thinking','following','using','depending','surrounded','otherwise',
            'swiftly','instead','thereafter','thereupon','despite','overcome',
            'oppressed','driven','struck','protected','arise','accept','give',
            'take','come','make','show','kill','protect','your','down'}

    NOISE_WORDS = {
        'Accept','Action','Agreeable','Aimed','Alas','Always','Among','Animals',
        'Arise','Associated','Behold','Bengal','Birth','Blossoms','Both','Bought',
        'Bright','Come','Commodity','Completed','Conduct','Confused','Consciousness',
        'Contentment','Cold','Dark','Death','Depending','Desiring','Despite',
        'Dice','District','Divine','Driven','During','Easy','Elephants',
        'Embryo','Extremely','Festival','Fire','Follow','Food','Forgiveness',
        'Fortunate','Fruit','Garment','Ghee','Give','Given','Gold','Great',
        'Hair','Have','Hear','Hearing','Heaven','Honey','Immobile','Immutable',
        'Impossible','Important','Incognito','Indestructible','Instead','Island',
        'Kill','Killing','King','Know','Knowing','Knowledge','Large','Learned',
        'Less','Life','Like','Listen','Long','Look','Love','Made','Make',
        'Meditation','Metals','Mortar','Mount','Necessary','Nothing','Observed',
        'Offered','Oppressed','Otherwise','Overcome','Parva','People','Performed',
        'Permanent','Person','Pillar','Please','Plough','Practices','Protect',
        'Protected','Properties','Prosperity','Rathas','Renunciation','Relatives',
        'Sages','Seat','Seed','Seeing','Shame','She','Shed','Show','Shloka',
        'Sound','Space','Species','Spots','Spring','Status','Stone','Struck',
        'Suggestion','Surrounded','Swiftly','Symmetric','Take','Taking','Tell',
        'Thereafter','Thereupon','Thinking','Thousands','Thrown','Today','Touch',
        'Towards','Tradition','Tree','Truth','True','Under','Victory','Voice',
        'Water','Weapon','West','Whether','Wishing','Wombs','Worst','Your',
        'Adharma','Adityas','Ahamkara','Amlavetasa','Andhakas','Artha',
        'Bharatas','Brahmana','Brahmanas','Chedis','Chhanda','Chapter',
        'Divyastras','Edukas','FLowers','Ganas','Gangasagar','Girivraja',
        'Himalayas','India','Indras','Kekayas','Kouravas','Krishnas',
        'Kshatriyas','Kunapa','Kupya','Lokapalas','Maharatha','Maruts',
        'Matsyas','Miscegenation','Nagakeshara','Nakshatras','Nirgundi',
        'Padma','Pamshu','Panchalas','Pandaveyas','Pandavas','Pandus',
        'Parthas','Piyala','Pleiades','Pranayama','Preceptor','Principle',
        'Pushya','Prakriti','Purusha','Rain','Rajagriha','Red','Rudras',
        'Sabhasada','Sadhyas','Samskara','Sarisrikva','Saturn','Sattva',
        'Shvetakakiya','Six','Snayu','Somakas','Srinjayas','Sushumna',
        'Tamas-type','Tamarind','Trigarta','Trigartas','Twelve','Undesir-',
        'Varga','Varuthas','Vedangas','Venus','Vishvadevas','Vrishnis',
        'Yugas','Adarshana','Vinasana','Stambamitra','Prana','Satya','Sama',
        'Kurus','Brother','Mother','Father','Son','Something','Every',
        'Earlier','Everyone','Everything','Metaphorically','Others','Their',
        'Then','They','Time','Whatever','While','Without','You','Suta',
        'Mani','Maniman','Manovaha','Paka','Battle','Down',
        'Gandiva','Vidarbha','Sacriﬁce',
        'Difﬁcult','Near','Lineage','Once','Maha','Veda','Vedas',
        'Vasus',
        # Lowercase noise caught from output
        'blossoms','tree','love','she','district','properties','Kama',
        'Apaya','nagakeshara','piyala','nirgundi','Poulomi',
        'Pluto','Pandava',
    }

    def is_valid_name(n):
        return (n and len(n) >= 3 and n not in NOISE_WORDS
                and n.lower() not in SKIP and not n.endswith('-'))

    # Load all text
    all_ch_text = ''
    all_fn_text = ''
    for v in range(1, 11):
        all_ch_text += open(os.path.join(base_dir, f'volume_{v}_chapters.txt'),
                            encoding='utf-8').read()
        all_fn_text += open(os.path.join(base_dir, f'volume_{v}_footnotes.txt'),
                            encoding='utf-8').read()

    # --- Extract names from footnotes ---
    fn_entries = re.findall(r'(?:^|\n)(\d+)\s+((?:(?!\n\d+\s).)*)', all_fn_text, re.S)
    for num, text in fn_entries:
        text = re.sub(r'\s+', ' ', text).strip()
        # "Name. He/She..." pattern
        m = re.match(r'^([A-Z][\w-]+)\.\s+(?:He|She|It|The|This|One|A )', text)
        if m and is_valid_name(m.group(1)):
            g = 'Female' if '. She ' in text[:50] else ('Male' if '. He ' in text[:50] else None)
            ensure(m.group(1), g)
        # "X's son/daughter/wife..." pattern
        for pm in re.finditer(r"([A-Z][\w'-]+)\u2019s\s+(?:son|daughter|wife|brother|sister|father|mother|husband)", text):
            if is_valid_name(pm.group(1)):
                ensure(pm.group(1))
        # "son/daughter/wife of X"
        for pm in re.finditer(r"(?:son|daughter|wife|brother|sister) of\s+([A-Z][\w'-]+)", text):
            if is_valid_name(pm.group(1)):
                ensure(pm.group(1))
        # "King/Queen X of Y"
        m2 = re.match(r'^([A-Z][\w-]+),?\s+(?:the\s+)?(?:king|queen|prince|princess|ruler|chief) of\s+([A-Z][\w-]+)', text)
        if m2:
            if is_valid_name(m2.group(1)):
                ensure(m2.group(1), 'Male' if 'king' in text[:40].lower() else None)
        # "also known as" / "also called"
        for m3 in re.finditer(r"([A-Z][\w-]+)[\s,]+(?:is\s+)?also\s+(?:known|called)\s+as\s+([A-Z][\w-]+)", text, re.I):
            a, b = m3.group(1), m3.group(2)
            if is_valid_name(a) and is_valid_name(b):
                # Resolve through alias map
                ka = _alias_map.get(_key(a), _key(a))
                kb = _alias_map.get(_key(b), _key(b))
                if ka in chars:
                    chars[ka]['aliases'].add(b)
                elif kb in chars:
                    chars[kb]['aliases'].add(a)
                else:
                    resolved = ensure(a)
                    chars[resolved]['aliases'].add(b)

    # --- Extract names from chapters ---
    # Speech: 'Name said/spoke/asked/...'
    said_names = re.findall(
        r"[\u2018\u2019']([A-Z][a-z]{2,})\s+(?:said|spoke|asked|replied|answered|told|addressed|continued|recounted)",
        all_ch_text)
    for n in set(said_names):
        if is_valid_name(n):
            ensure(n)

    # Vocative: "O Name!" (count >= 5)
    voc_counts = {}
    for n in re.findall(r"O\s+([A-Z][a-z]{2,})!", all_ch_text):
        voc_counts[n] = voc_counts.get(n, 0) + 1
    for n, c in voc_counts.items():
        if c >= 5 and is_valid_name(n):
            ensure(n)

    # Titled: "King/Prince/Sage Name" (count >= 3)
    titled_counts = {}
    for n in re.findall(r"(?:King|Prince|Sage|Rishi|Queen|Princess|Maharaja)\s+([A-Z][a-z]{2,})", all_ch_text):
        titled_counts[n] = titled_counts.get(n, 0) + 1
    for n, c in titled_counts.items():
        if c >= 3 and is_valid_name(n):
            g = 'Female' if re.search(r"(?:Queen|Princess)\s+" + re.escape(n), all_ch_text) else 'Male'
            ensure(n, g)

    # Relationship from chapters: "Name's son/daughter/wife..." (count >= 3)
    ch_rel_counts = {}
    for n in re.findall(r"([A-Z][a-z]{2,})\u2019s\s+(?:son|daughter|wife|brother|sister|father|mother|husband)", all_ch_text):
        ch_rel_counts[n] = ch_rel_counts.get(n, 0) + 1
    for n, c in ch_rel_counts.items():
        if c >= 3 and is_valid_name(n):
            ensure(n)

    # High-frequency proper nouns (>= 50 occurrences)
    caps_counts = {}
    for n in re.findall(r'\b([A-Z][a-z]{3,})\b', all_ch_text):
        caps_counts[n] = caps_counts.get(n, 0) + 1
    for n, c in caps_counts.items():
        if c >= 50 and is_valid_name(n):
            ensure(n)

    # --- Extract relationships from chapter text ---
    # "X, the son/daughter of Y" or "X, Y's son/daughter"
    for m in re.finditer(r"([A-Z][a-z]{2,}),?\s+(?:the\s+)?son\s+of\s+([A-Z][a-z]{2,})", all_ch_text):
        child, parent = m.group(1), m.group(2)
        if is_valid_name(child) and is_valid_name(parent):
            ck = ensure(child, 'Male')
            pk = ensure(parent, 'Male')
            if not chars[ck]['father']:
                chars[ck]['father'] = pk

    for m in re.finditer(r"([A-Z][a-z]{2,}),?\s+(?:the\s+)?daughter\s+of\s+([A-Z][a-z]{2,})", all_ch_text):
        child, parent = m.group(1), m.group(2)
        if is_valid_name(child) and is_valid_name(parent):
            ck = ensure(child, 'Female')
            pk = ensure(parent)
            if not chars[ck]['father']:
                chars[ck]['father'] = pk

    # "X's wife Y" / "wife of X"
    for m in re.finditer(r"([A-Z][a-z]{2,})\u2019s\s+wife,?\s+([A-Z][a-z]{2,})", all_ch_text):
        husband, wife = m.group(1), m.group(2)
        if is_valid_name(husband) and is_valid_name(wife):
            hk = ensure(husband, 'Male')
            wk = ensure(wife, 'Female')
            if wk not in _spouse_keys(chars[hk]):
                chars[hk]['spouse'].append((wk, 'Wife'))
            if hk not in _spouse_keys(chars[wk]):
                chars[wk]['spouse'].append((hk, 'Husband'))

    # "X's brother Y"
    for m in re.finditer(r"([A-Z][a-z]{2,})\u2019s\s+brother,?\s+([A-Z][a-z]{2,})", all_ch_text):
        a, b = m.group(1), m.group(2)
        if is_valid_name(a) and is_valid_name(b):
            ak = ensure(a, 'Male')
            bk = ensure(b, 'Male')
            chars[ak]['siblings'].add(bk)
            chars[bk]['siblings'].add(ak)

    # "X's sister Y"
    for m in re.finditer(r"([A-Z][a-z]{2,})\u2019s\s+sister,?\s+([A-Z][a-z]{2,})", all_ch_text):
        a, b = m.group(1), m.group(2)
        if is_valid_name(a) and is_valid_name(b):
            ak = ensure(a)
            bk = ensure(b, 'Female')
            chars[ak]['siblings'].add(bk)
            chars[bk]['siblings'].add(ak)

    # "X's mother Y" / "X's father Y"
    for m in re.finditer(r"([A-Z][a-z]{2,})\u2019s\s+mother,?\s+([A-Z][a-z]{2,})", all_ch_text):
        child, mother = m.group(1), m.group(2)
        if is_valid_name(child) and is_valid_name(mother):
            ck = ensure(child)
            mk = ensure(mother, 'Female')
            if not chars[ck]['mother']:
                chars[ck]['mother'] = mk

    for m in re.finditer(r"([A-Z][a-z]{2,})\u2019s\s+father,?\s+([A-Z][a-z]{2,})", all_ch_text):
        child, father = m.group(1), m.group(2)
        if is_valid_name(child) and is_valid_name(father):
            ck = ensure(child)
            fk = ensure(father, 'Male')
            if not chars[ck]['father']:
                chars[ck]['father'] = fk

    # --- Extract relationships from footnotes ---
    for num, text in fn_entries:
        text = re.sub(r'\s+', ' ', text).strip()
        # "X was the son of Y" / "X was Y's son"
        for m in re.finditer(r"([A-Z][a-z]{2,})\s+was\s+(?:the\s+)?(?:son|child)\s+of\s+([A-Z][a-z]{2,})", text):
            child, parent = m.group(1), m.group(2)
            if is_valid_name(child) and is_valid_name(parent):
                ck = ensure(child, 'Male')
                pk = ensure(parent)
                if not chars[ck]['father']:
                    chars[ck]['father'] = pk
        # "X was the daughter of Y"
        for m in re.finditer(r"([A-Z][a-z]{2,})\s+was\s+(?:the\s+)?daughter\s+of\s+([A-Z][a-z]{2,})", text):
            child, parent = m.group(1), m.group(2)
            if is_valid_name(child) and is_valid_name(parent):
                ck = ensure(child, 'Female')
                pk = ensure(parent)
                if not chars[ck]['father']:
                    chars[ck]['father'] = pk
        # "X was the wife of Y" / "X was Y's wife"
        for m in re.finditer(r"([A-Z][a-z]{2,})\s+was\s+(?:the\s+)?wife\s+of\s+([A-Z][a-z]{2,})", text):
            wife, husband = m.group(1), m.group(2)
            if is_valid_name(wife) and is_valid_name(husband):
                wk = ensure(wife, 'Female')
                hk = ensure(husband, 'Male')
                if hk not in _spouse_keys(chars[wk]):
                    chars[wk]['spouse'].append((hk, 'Husband'))
                if wk not in _spouse_keys(chars[hk]):
                    chars[hk]['spouse'].append((wk, 'Wife'))
        # "X's son Y" in footnotes
        for m in re.finditer(r"([A-Z][a-z]{2,})\u2019s\s+son,?\s+([A-Z][a-z]{2,})", text):
            parent, child = m.group(1), m.group(2)
            if is_valid_name(parent) and is_valid_name(child):
                pk = ensure(parent)
                ck = ensure(child, 'Male')
                if not chars[ck]['father']:
                    chars[ck]['father'] = pk

    # ── Phase 3: Merge & Resolve ────────────────────────────────
    MERGE = {
        'bhisma': 'bhishma', 'dhritarasthra': 'dhritarashtra',
        'dritarashtra': 'dhritarashtra', 'dhritrarashtra': 'dhritarashtra',
        'dhritrashtra': 'dhritarashtra',
        'droupadi': 'draupadi', 'kounteya': 'arjuna',
        'krisha': 'krishna', 'kourava': 'duryodhana',
        'yudhisthira': 'yudhishthira', 'yarkandeya': 'markandeya',
        'baladeva': 'balarama', 'bhimasena': 'bhima',
        'govinda': 'krishna', 'maheshvara': 'shiva',
        'bhagavan': 'krishna', 'hutashana': 'agni',
        'sthanu': 'shiva', 'rudra': 'shiva',
        'pritha': 'kunti', 'saindhava': 'jayadratha',
        'souti': 'ugrasrava',
        'vasudeva': 'krishna', 'vaishravana': 'kubera',
        'vaivasvata': 'manu', 'vivasvata': 'surya',
        'madhusudana': 'krishna', 'vaasudeva': 'krishna',
        'krishnaa': 'draupadi', 'sharadvata': 'kripa',
        'goutama': 'kripa', 'mithila': 'janaka',
        'vashishtha': 'vasishtha', 'hardikya': 'kritavarma',
        'yuyudhana': 'satyaki', 'satvata': 'satyaki',
        'vaikartana': 'karna', 'varshneya': 'krishna',
        'dasharha': 'krishna', 'pundarikaksha': 'krishna',
        'shouri': 'krishna', 'purushottama': 'krishna',
        'maghavan': 'indra', 'shankara': 'shiva',
        'parshata': 'drupada', 'dvaipayana': 'vyasa',
        'nishadha': 'nala', 'punyashloka': 'nala',
        'bahuka': 'nala', 'mandhatar': 'mandhata',
        'agasti': 'agastya', 'kushika': 'vishvamitra',
        'kouravya': 'yudhishthira',
        'pandaveya': 'yudhishthira',
        'anakadundubhi': 'vasudeva_father',
        # Disambiguated keys
        'chitrangada': 'chitrangada_kuru',
        'lakshmana': 'lakshmana_kaurava',
        'prishata': 'prishata',
    }

    for old_k, new_k in MERGE.items():
        if old_k in chars and new_k in chars and old_k != new_k:
            chars[new_k]['aliases'].add(chars[old_k]['name'])
            chars[new_k]['aliases'].update(chars[old_k]['aliases'])
            if not chars[new_k]['father'] and chars[old_k]['father']:
                chars[new_k]['father'] = chars[old_k]['father']
            if not chars[new_k]['mother'] and chars[old_k]['mother']:
                chars[new_k]['mother'] = chars[old_k]['mother']
            chars[new_k]['siblings'].update(chars[old_k]['siblings'])
            # Merge spouse lists preserving order
            for sp_tuple in chars[old_k]['spouse']:
                if sp_tuple[0] not in _spouse_keys(chars[new_k]):
                    chars[new_k]['spouse'].append(sp_tuple)
            if chars[new_k]['gender'] == 'Unknown':
                chars[new_k]['gender'] = chars[old_k]['gender']
            if not chars[new_k]['caste'] and chars[old_k]['caste']:
                chars[new_k]['caste'] = chars[old_k]['caste']
            if not chars[new_k]['duty'] and chars[old_k]['duty']:
                chars[new_k]['duty'] = chars[old_k]['duty']
            if not chars[new_k]['dynasty'] and chars[old_k]['dynasty']:
                chars[new_k]['dynasty'] = chars[old_k]['dynasty']
            if not chars[new_k]['status'] and chars[old_k]['status']:
                chars[new_k]['status'] = chars[old_k]['status']
            for k, c in chars.items():
                if c['father'] == old_k:
                    c['father'] = new_k
                if c['mother'] == old_k:
                    c['mother'] = new_k
                if old_k in c['siblings']:
                    c['siblings'].discard(old_k)
                    if k != new_k:
                        c['siblings'].add(new_k)
                if old_k in _spouse_keys(c):
                    c['spouse'] = [(new_k, r) if s == old_k else (s, r) for s, r in c['spouse']]
                    if k == new_k:
                        c['spouse'] = [(s, r) for s, r in c['spouse'] if s != new_k]
            del chars[old_k]

    # Remove noise entries
    for k in list(chars.keys()):
        if (chars[k]['name'] in NOISE_WORDS
            or chars[k]['name'].lower() in NOISE_WORDS
            or not is_valid_name(chars[k]['name'])):
            for k2, c2 in chars.items():
                if c2['father'] == k:
                    c2['father'] = None
                if c2['mother'] == k:
                    c2['mother'] = None
                c2['siblings'].discard(k)
                c2['spouse'] = [(s, r) for s, r in c2['spouse'] if s != k]
            del chars[k]

    # Clean self-references and aliases
    for k, c in chars.items():
        c['siblings'].discard(k)
        c['spouse'] = [(s, r) for s, r in c['spouse'] if s != k]
        if c['father'] == k:
            c['father'] = None
        if c['mother'] == k:
            c['mother'] = None
        c['aliases'].discard(c['name'])
        c['aliases'] = {a for a in c['aliases'] if is_valid_name(a)}

    # Validate references: remove dangling keys
    all_keys = set(chars.keys())
    for k, c in chars.items():
        if c['father'] and c['father'] not in all_keys:
            c['father'] = None
        if c['mother'] and c['mother'] not in all_keys:
            c['mother'] = None
        c['siblings'] = {s for s in c['siblings'] if s in all_keys}
        c['spouse'] = [(s, r) for s, r in c['spouse'] if s in all_keys]

    # Remove spouse links that conflict with parent-child
    for k, c in chars.items():
        bad_spouses = set()
        for sp, _rel in c['spouse']:
            if sp in chars and (chars[sp]['father'] == k or chars[sp]['mother'] == k):
                bad_spouses.add(sp)
            if c['father'] == sp or c['mother'] == sp:
                bad_spouses.add(sp)
        c['spouse'] = [(s, r) for s, r in c['spouse'] if s not in bad_spouses]
        for sp in bad_spouses:
            if sp in chars:
                chars[sp]['spouse'] = [(s, r) for s, r in chars[sp]['spouse'] if s != k]

    # Remove circular parent references (A father of B and B father of A)
    for k, c in chars.items():
        if c['father'] and c['father'] in chars:
            if chars[c['father']]['father'] == k:
                chars[c['father']]['father'] = None
        if c['mother'] and c['mother'] in chars:
            if chars[c['mother']]['mother'] == k:
                chars[c['mother']]['mother'] = None

    # ── Phase 3b: Auto-extract Duty/Caste from text patterns ────
    # "King X" / "Queen X" / "Sage X" / "Prince X" etc.
    duty_patterns = [
        (r"\bKing\s+([A-Z][a-z]{2,})", "King", "Kshatriya"),
        (r"\bQueen\s+([A-Z][a-z]{2,})", "Queen", "Kshatriya"),
        (r"\bPrince\s+([A-Z][a-z]{2,})", "Prince", "Kshatriya"),
        (r"\bPrincess\s+([A-Z][a-z]{2,})", "Princess", "Kshatriya"),
        (r"\bSage\s+([A-Z][a-z]{2,})", "Sage", "Brahmin"),
        (r"\bRishi\s+([A-Z][a-z]{2,})", "Sage", "Brahmin"),
        (r"\bMaharaja\s+([A-Z][a-z]{2,})", "King", "Kshatriya"),
    ]
    for pat, duty_val, caste_val in duty_patterns:
        for m in re.finditer(pat, all_ch_text):
            name = m.group(1)
            k = _alias_map.get(_key(name), _key(name))
            if k in chars:
                if not chars[k]['duty']:
                    chars[k]['duty'] = duty_val
                if not chars[k]['caste']:
                    chars[k]['caste'] = caste_val

    # "king of X" -> dynasty extraction
    for m in re.finditer(r"([A-Z][a-z]{2,}),?\s+(?:the\s+)?king\s+of\s+([A-Z][a-z]{2,})", all_ch_text):
        name, place = m.group(1), m.group(2)
        k = _alias_map.get(_key(name), _key(name))
        if k in chars and not chars[k]['dynasty'] and is_valid_name(place):
            chars[k]['dynasty'] = place

    # ── Phase 4: Output ─────────────────────────────────────────
    # Derive children from father/mother references, preserving insertion order
    children_map = {}
    for k, c in chars.items():
        if c['father'] and c['father'] in chars:
            children_map.setdefault(c['father'], [])
            if k not in children_map[c['father']]:
                children_map[c['father']].append(k)
        if c['mother'] and c['mother'] in chars:
            children_map.setdefault(c['mother'], [])
            if k not in children_map[c['mother']]:
                children_map[c['mother']].append(k)

    output = {}
    for k in sorted(chars.keys()):
        c = chars[k]
        entry = {
            "Name": c['name'],
            "Alias_names": sorted(c['aliases']),
            "Gender": c['gender'],
        }
        if c['father']:
            entry["Father"] = f"@{c['father']}"
        if c['mother']:
            entry["Mother"] = f"@{c['mother']}"
        if c['spouse']:
            # Build spouse→children mapping for this character
            # For each child, find which spouse is the other parent
            my_children = children_map.get(k, [])
            spouse_keys = _spouse_keys(c)
            spouse_children = {}  # spouse_key -> [child_keys]
            unattributed = []     # children not linked to any spouse
            for ch in my_children:
                ch_data = chars.get(ch, {})
                # Determine the other parent
                other = None
                if ch_data.get('father') == k:
                    other = ch_data.get('mother')
                elif ch_data.get('mother') == k:
                    other = ch_data.get('father')
                # Check both directions for ambiguous gender
                if other is None:
                    if ch_data.get('father') and ch_data['father'] != k and ch_data['father'] in spouse_keys:
                        other = ch_data['father']
                    elif ch_data.get('mother') and ch_data['mother'] != k and ch_data['mother'] in spouse_keys:
                        other = ch_data['mother']
                if other and other in spouse_keys:
                    spouse_children.setdefault(other, []).append(ch)
                else:
                    unattributed.append(ch)

            # Preserve spouse order; each entry includes Relation and Children
            seen = set()
            spouse_list = []
            for s, rel in c['spouse']:
                if s not in seen:
                    # Resolve default relation based on genders
                    if not rel:
                        s_gender = chars[s]['gender'] if s in chars else 'Unknown'
                        if s_gender == 'Female':
                            rel = 'Wife'
                        elif s_gender == 'Male':
                            rel = 'Husband'
                        else:
                            rel = 'Spouse'
                    s_entry = {f"@{s}": {
                        "Relation": rel,
                        "Children": [f"@{ch}" for ch in spouse_children.get(s, [])]
                    }}
                    spouse_list.append(s_entry)
                    seen.add(s)
            entry["Spouse"] = spouse_list

            # Children not attributable to any spouse
            if unattributed:
                entry["Children"] = [f"@{ch}" for ch in unattributed]
        else:
            # No spouse but may have children
            if k in children_map:
                entry["Children"] = [f"@{ch}" for ch in children_map[k]]
        if c['caste']:
            entry["Caste"] = c['caste']
        if c['duty']:
            entry["Duty"] = c['duty']
        if c['dynasty']:
            entry["Dynasty"] = c['dynasty']
        if c['status']:
            entry["Status"] = c['status']
        output[f"@{k}"] = entry

    out_path = os.path.join(os.path.dirname(base_dir), 'characters.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Stats
    total = len(output)
    with_aliases = sum(1 for v in output.values() if v.get('Alias_names'))
    with_father = sum(1 for v in output.values() if 'Father' in v)
    with_mother = sum(1 for v in output.values() if 'Mother' in v)
    with_spouse = sum(1 for v in output.values() if 'Spouse' in v)
    with_children = sum(1 for v in output.values()
                       if 'Children' in v
                       or any(ch for sp in v.get('Spouse', []) if isinstance(sp, dict)
                              for sd in sp.values() if isinstance(sd, dict)
                              for ch in sd.get('Children', [])))
    with_caste = sum(1 for v in output.values() if 'Caste' in v)
    with_duty = sum(1 for v in output.values() if 'Duty' in v)
    with_dynasty = sum(1 for v in output.values() if 'Dynasty' in v)
    with_status = sum(1 for v in output.values() if 'Status' in v)
    males = sum(1 for v in output.values() if v['Gender'] == 'Male')
    females = sum(1 for v in output.values() if v['Gender'] == 'Female')
    unknowns = sum(1 for v in output.values() if v['Gender'] == 'Unknown')
    print(f"  Total characters: {total}")
    print(f"  With aliases: {with_aliases}")
    print(f"  With Father: {with_father}, Mother: {with_mother}")
    print(f"  With Spouse: {with_spouse}")
    print(f"  With Children: {with_children}")
    print(f"  With Caste: {with_caste}, Duty: {with_duty}")
    print(f"  With Dynasty: {with_dynasty}, Status: {with_status}")
    print(f"  Gender - Male: {males}, Female: {females}, Unknown: {unknowns}")
    print(f"  Saved to characters.json")


# ================================================================
# MAIN
# ================================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python mahabharata.py <path_to_pdf> [output_dir]")
        sys.exit(1)

    pdf_path = os.path.abspath(sys.argv[1])
    if not os.path.isfile(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        base_dir = os.path.abspath(sys.argv[2])
    else:
        base_dir = os.path.join(os.path.dirname(pdf_path), 'volumes')
    os.makedirs(base_dir, exist_ok=True)

    step1_extract(pdf_path, base_dir)
    step1b_manual_fixes(base_dir)
    step2_add_sections(base_dir)
    ok = step3_verify(base_dir)
    step4_characters(base_dir)

    print("\n" + "=" * 60)
    if ok:
        print("ALL DONE - 100% footnote matching across all volumes")
    else:
        print("DONE - some footnote mismatches detected (check above)")
    print("=" * 60)
