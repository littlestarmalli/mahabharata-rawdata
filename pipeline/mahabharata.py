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

def step4_characters(base_dir, json_dir):
    """Extract characters with relationships, write characters.json, locations.json, timeline.json."""
    print("\n" + "=" * 60)
    print("STEP 4: Building character knowledge graph")
    print("=" * 60)

    # ── Data model ──────────────────────────────────────────────
    chars = {}  # key -> dict

    def _key(name):
        return name.strip().lower().replace(' ', '_')

    def add(primary, *, aliases=None, father=None, mother=None,
            siblings=None, spouse=None, gender=None,
            caste=None, duty=None, dynasty=None, status=None,
            kingdom=None, political_role=None,
            skills=None, divine_weapons=None, titles=None,
            traits=None, character_arc=None,
            key_relationships=None, important_locations=None):
        """spouse: list of strings OR list of (name, relation) tuples.
           Plain strings default to relation 'Wife'/'Husband' based on gender."""
        k = _key(primary)
        if k not in chars:
            chars[k] = {'name': primary.strip(), 'aliases': set(),
                        'father': None, 'mother': None,
                        'siblings': set(), 'spouse': [],
                        'gender': 'Unknown',
                        'caste': '', 'duty': '', 'dynasty': '', 'status': '',
                        'kingdom': '', 'political_role': '',
                        'skills': [], 'divine_weapons': [], 'titles': [],
                        'traits': [], 'character_arc': [],
                        'key_relationships': [], 'important_locations': []}
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
        if kingdom and not c['kingdom']:
            c['kingdom'] = kingdom
        if political_role and not c['political_role']:
            c['political_role'] = political_role
        if skills:
            c['skills'] = list(dict.fromkeys(c['skills'] + skills))
        if divine_weapons:
            c['divine_weapons'] = list(dict.fromkeys(c['divine_weapons'] + divine_weapons))
        if titles:
            c['titles'] = list(dict.fromkeys(c['titles'] + titles))
        if traits:
            c['traits'] = list(dict.fromkeys(c['traits'] + traits))
        if character_arc:
            c['character_arc'] = list(dict.fromkeys(c['character_arc'] + character_arc))
        if key_relationships:
            existing_pairs = {(kr['With'], kr['Type']) for kr in c['key_relationships']}
            for kr in key_relationships:
                pair = (kr['With'], kr['Type'])
                if pair not in existing_pairs:
                    c['key_relationships'].append(kr)
                    existing_pairs.add(pair)
        if important_locations:
            c['important_locations'] = list(dict.fromkeys(c['important_locations'] + important_locations))

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
                        'caste': '', 'duty': '', 'dynasty': '', 'status': '',
                        'kingdom': '', 'political_role': '',
                        'skills': [], 'divine_weapons': [], 'titles': [],
                        'traits': [], 'character_arc': [],
                        'key_relationships': [], 'important_locations': []}
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
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Alive",
        kingdom="indraprastha", political_role="Emperor",
        skills=["Dharma","Spear combat","Dice","Statecraft","Diplomacy"],
        divine_weapons=["Spear of Dharma"],
        titles=["Dharmaraja","Ajatashatru","Emperor of Indraprastha"],
        traits=["Righteous","Truthful","Just","Compassionate","Overly virtuous"],
        character_arc=["Born to Kunti via Yama (Dharma)","Heir apparent to Hastinapura",
            "Rajasuya Yajna - crowned emperor","Lost kingdom in dice game",
            "13 years of exile","Led Pandavas in Kurukshetra War",
            "Crowned King of Hastinapura after war","Retired to forest","Ascended to Svarga"],
        key_relationships=[
            {"With":"@krishna","Type":"Guide"},
            {"With":"@duryodhana","Type":"Rival"},
            {"With":"@vidura","Type":"Guide"},
            {"With":"@draupadi","Type":"Spouse"},
            {"With":"@bhima","Type":"Brother"},
            {"With":"@arjuna","Type":"Brother"}],
        important_locations=["hastinapura","indraprastha","kamyaka_forest","kurukshetra","svarga"])
    add("Bhima", aliases=["Bhimasena","Vrikodara"],
        father="Pandu", mother="Kunti",
        siblings=["Yudhishthira","Arjuna","Nakula","Sahadeva"],
        spouse=[("Draupadi","Wife"),("Hidimba","Gandharva marriage")], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Alive",
        kingdom="indraprastha", political_role="Prince",
        skills=["Mace combat","Wrestling","Immense strength","Cooking"],
        titles=["Vrikodara","Ballava"],
        traits=["Fierce","Loyal","Wrathful","Protective","Gluttonous"],
        character_arc=["Born to Kunti via Vayu","Poisoned by Duryodhana - survived",
            "Killed Bakasura at Ekachakra","Killed Hidimba - married Hidimba (sister)",
            "Killed Jarasandha in wrestling duel","Served as cook Ballava in Virata",
            "Vowed to kill all 100 Kauravas","Killed Duhshasana - drank his blood",
            "Killed Duryodhana in mace duel","Ascended to Svarga"],
        key_relationships=[
            {"With":"@duryodhana","Type":"Enemy"},
            {"With":"@duhshasana","Type":"Enemy"},
            {"With":"@hanuman","Type":"Brother"},
            {"With":"@draupadi","Type":"Spouse"},
            {"With":"@ghatotkacha","Type":"Father"}],
        important_locations=["hastinapura","indraprastha","ekachakra","kamyaka_forest","viratanagara","kurukshetra"])
    add("Arjuna", aliases=["Partha","Dhananjaya","Savyasachi","Gudakesha",
        "Phalguna","Kiriti","Bibhatsu","Vijaya","Shvetavahana","Jishnu",
        "Kaunteya","Kounteya","Gandivadhanva"],
        father="Pandu", mother="Kunti",
        siblings=["Yudhishthira","Bhima","Nakula","Sahadeva"],
        spouse=[("Draupadi","Wife"),("Subhadra","Wife"),("Ulupi","Wife"),("Chitrangada_manipura","Wife")], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Alive",
        kingdom="indraprastha", political_role="Prince",
        skills=["Archery","Sword combat","Celestial weapons mastery","Dance","Music"],
        divine_weapons=["Gandiva bow","Pashupatastra","Brahmastra","Aindraastra",
            "Varunastra","Agneyastra","Vayavyastra","Narayanastra"],
        titles=["Partha","Savyasachi","Dhananjaya","Gudakesha","Kiriti","Bibhatsu",
            "Vijaya","Shvetavahana","Jishnu","Phalguna","Brihannala"],
        traits=["Skilled","Disciplined","Devoted","Courageous","Self-doubting"],
        character_arc=["Born to Kunti via Indra","Trained under Drona - best archer",
            "Won Draupadi at Swayamvara","Burned Khandava forest with Krishna",
            "Exile - penance to Shiva (Pashupatastra)","Trained in Svarga under Indra",
            "Lived as Brihannala in Virata","Received Bhagavad Gita from Krishna",
            "Fought and won Kurukshetra War","Killed Karna","Ashvamedha Yajna",
            "Ascended to Svarga"],
        key_relationships=[
            {"With":"@krishna","Type":"Friend"},
            {"With":"@drona","Type":"Guru"},
            {"With":"@karna","Type":"Rival"},
            {"With":"@subhadra","Type":"Spouse"},
            {"With":"@draupadi","Type":"Spouse"},
            {"With":"@abhimanyu","Type":"Father"},
            {"With":"@indra","Type":"Divine father"}],
        important_locations=["hastinapura","indraprastha","khandava_forest","svarga",
            "viratanagara","kurukshetra","manipura","dvaraka"])
    add("Nakula", father="Pandu", mother="Madri",
        siblings=["Yudhishthira","Bhima","Arjuna","Sahadeva"],
        spouse=["Draupadi"], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Alive",
        kingdom="indraprastha", political_role="Prince",
        skills=["Sword combat","Horse keeping","Ayurveda","Handsome appearance"],
        titles=["Granthika"],
        traits=["Handsome","Skilled horseman","Loyal","Humble"],
        character_arc=["Born to Madri via Ashvins","Trained under Drona",
            "Served as horse-keeper Granthika in Virata",
            "Fought in Kurukshetra War","Ascended to Svarga"],
        key_relationships=[
            {"With":"@sahadeva","Type":"Twin brother"},
            {"With":"@draupadi","Type":"Spouse"}],
        important_locations=["hastinapura","indraprastha","viratanagara","kurukshetra"])
    add("Sahadeva", father="Pandu", mother="Madri",
        siblings=["Yudhishthira","Bhima","Arjuna","Nakula"],
        spouse=["Draupadi"], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Alive",
        kingdom="indraprastha", political_role="Prince",
        skills=["Sword combat","Astrology","Cattle keeping","Intelligence"],
        titles=["Tantipala"],
        traits=["Wise","Knowledgeable","Modest","Loyal"],
        character_arc=["Born to Madri via Ashvins","Trained under Drona",
            "Served as cowherd Tantipala in Virata",
            "Fought in Kurukshetra War","Fell during Mahaprasthana"],
        key_relationships=[
            {"With":"@nakula","Type":"Twin brother"},
            {"With":"@draupadi","Type":"Spouse"}],
        important_locations=["hastinapura","indraprastha","viratanagara","kurukshetra"])

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
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="Crown Prince",
        skills=["Mace combat","Statecraft","Leadership"],
        titles=["Suyodhana","King of Hastinapura"],
        traits=["Ambitious","Jealous","Brave","Loyal to friends","Wrathful","Proud"],
        character_arc=["Born first among 100 Kauravas","Jealous of Pandavas from childhood",
            "Poisoned Bhima as youth","Conspired lac palace (Lakshagriha)",
            "Orchestrated dice game - humiliated Draupadi","Refused to return kingdom after exile",
            "Rejected Krishna's peace offer","Led Kaurava army in Kurukshetra War",
            "Last Kaurava standing","Killed by Bhima in mace duel on Day 18"],
        key_relationships=[
            {"With":"@karna","Type":"Friend"},
            {"With":"@shakuni","Type":"Guide"},
            {"With":"@bhima","Type":"Rival"},
            {"With":"@yudhishthira","Type":"Rival"},
            {"With":"@drona","Type":"Guru"},
            {"With":"@balarama","Type":"Guru"}],
        important_locations=["hastinapura","kurukshetra"])
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
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="King",
        skills=["Immense physical strength","Statecraft"],
        titles=["King of Hastinapura","Blind King"],
        traits=["Blind","Indecisive","Partial to sons","Grieving father","Weak-willed"],
        character_arc=["Born blind via Niyoga from Vyasa","Passed over for throne due to blindness",
            "Became regent after Pandu's death","Failed to restrain Duryodhana",
            "Approved dice game","Witnessed war through Sanjaya's narration",
            "Lost all 100 sons in war","Retired to forest with Gandhari","Died in forest fire"],
        key_relationships=[
            {"With":"@gandhari","Type":"Spouse"},
            {"With":"@duryodhana","Type":"Father"},
            {"With":"@vidura","Type":"Brother"},
            {"With":"@sanjaya","Type":"Adviser"},
            {"With":"@pandu","Type":"Brother"}],
        important_locations=["hastinapura"])
    add("Sughada", aliases=["Vaishya maid","Vaishya woman"],
        spouse=[("Dhritarashtra","Concubine")], gender="Female",
        caste="Vaishya", dynasty="Kuru")
    add("Pandu", father="Vichitravirya", mother="Ambalika",
        spouse=[("Kunti","Wife"),("Madri","Wife")],
        siblings=["Dhritarashtra","Vidura"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="King",
        skills=["Archery","Warfare","Conquest"],
        titles=["Pandu the Pale","King of Hastinapura"],
        traits=["Valiant","Cursed","Remorseful","Expansionist"],
        character_arc=["Born to Ambalika via Niyoga from Vyasa","Crowned king (Dhritarashtra blind)",
            "Conquered many kingdoms","Cursed by sage Kindama","Retired to forest",
            "Sons born via divine boons of Kunti and Madri","Died from curse when approaching Madri"],
        key_relationships=[
            {"With":"@kunti","Type":"Spouse"},
            {"With":"@madri","Type":"Spouse"},
            {"With":"@dhritarashtra","Type":"Brother"}],
        important_locations=["hastinapura","shatashriga"])
    add("Vidura", aliases=["Kshatta"],
        siblings=["Dhritarashtra","Pandu"], gender="Male",
        caste="Kshatriya", duty="Minister", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="Prime Minister",
        skills=["Diplomacy","Dharma","Statecraft","Wisdom"],
        titles=["Kshatta","Dharma incarnation"],
        traits=["Wise","Righteous","Impartial","Courageous speaker of truth"],
        character_arc=["Born to maid via Niyoga from Vyasa","Served as minister of Hastinapura",
            "Warned Pandavas of Lakshagriha plot","Opposed dice game",
            "Counseled Dhritarashtra for peace","Left court in disgust","Died during forest retirement"],
        key_relationships=[
            {"With":"@yudhishthira","Type":"Guide"},
            {"With":"@dhritarashtra","Type":"Brother"},
            {"With":"@kunti","Type":"Ally"}],
        important_locations=["hastinapura"])
    add("Kunti", aliases=["Pritha"],
        father="Shurasena",
        spouse=[("Pandu","Husband"),("Surya","Divine boon"),("Yama","Divine boon"),("Vayu","Divine boon"),("Indra","Divine boon")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="Queen Mother",
        skills=["Divine invocation mantra","Devotion","Endurance"],
        titles=["Pritha","Queen Mother"],
        traits=["Devoted mother","Strong","Secretive","Sacrificing","Resilient"],
        character_arc=["Born as Pritha - adopted by Kuntibhoja","Received divine mantra from Durvasa",
            "Invoked Surya - bore Karna (abandoned)","Married Pandu",
            "Bore Yudhishthira (Yama), Bhima (Vayu), Arjuna (Indra)",
            "Shared mantra with Madri for Nakula & Sahadeva",
            "Raised Pandavas in Hastinapura after Pandu's death",
            "Revealed Karna's identity before war","Retired to forest","Died in forest fire"],
        key_relationships=[
            {"With":"@karna","Type":"Secret mother"},
            {"With":"@yudhishthira","Type":"Mother"},
            {"With":"@vidura","Type":"Ally"},
            {"With":"@pandu","Type":"Spouse"},
            {"With":"@draupadi","Type":"Mother-in-law"}],
        important_locations=["hastinapura","kunti_kingdom","indraprastha"])
    add("Madri", spouse=[("Pandu","Husband"),("Ashvins","Divine boon")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru", status="Deceased")
    add("Gandhari", father="Subala",
        spouse=[("Dhritarashtra","Husband")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="Queen",
        skills=["Austerity","Divine powers from tapas"],
        titles=["Queen of Hastinapura","Blindfolded Queen"],
        traits=["Devoted wife","Strong-willed","Blind devotion","Grieving mother","Powerful"],
        character_arc=["Born princess of Gandhara","Blindfolded herself after marrying blind Dhritarashtra",
            "Mother of 100 sons and 1 daughter","Cursed Krishna for not preventing war",
            "Lost all sons in war","Retired to forest","Died in forest fire"],
        key_relationships=[
            {"With":"@dhritarashtra","Type":"Spouse"},
            {"With":"@duryodhana","Type":"Mother"},
            {"With":"@shakuni","Type":"Brother"},
            {"With":"@krishna","Type":"Adversary"},
            {"With":"@kunti","Type":"Rival"}],
        important_locations=["hastinapura","gandhara"])

    # Bhishma's line
    add("Bhishma", aliases=["Devavrata","Gangeya","Shantanava"],
        father="Shantanu", mother="Ganga", gender="Male",
        caste="Kshatriya", duty="Regent", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="Regent and Grand-sire",
        skills=["Archery","All weapons mastery","Statecraft","Celibacy vow"],
        divine_weapons=["Brahmastra","Prasvapana"],
        titles=["Devavrata","Gangeya","Pitamaha","Grand-sire of Kuru"],
        traits=["Vow-keeper","Invincible","Wise","Tragic","Bound by duty"],
        character_arc=["Born to Shantanu and Ganga - 8th Vasu","Took vow of celibacy (Bhishma Pratigya)",
            "Abducted Amba, Ambika, Ambalika for Vichitravirya",
            "Served as regent of Hastinapura across generations",
            "Became Kaurava commander (Days 1-10)","Shot by Arjuna using Shikhandi as shield",
            "Lay on bed of arrows","Taught Shanti Parva wisdom","Died on Uttarayana"],
        key_relationships=[
            {"With":"@arjuna","Type":"Grandfather figure"},
            {"With":"@duryodhana","Type":"Grandfather figure"},
            {"With":"@drona","Type":"Ally"},
            {"With":"@shikhandi","Type":"Adversary"},
            {"With":"@amba","Type":"Adversary"},
            {"With":"@parashurama","Type":"Guru"}],
        important_locations=["hastinapura","kurukshetra"])
    add("Shantanu", aliases=["king of Hastinapura"],
        spouse=[("Ganga","Wife"),("Satyavati","Wife")],
        father="Pratipa", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="King",
        traits=["Romantic","Generous","Just"],
        important_locations=["hastinapura"])
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
        caste="Brahmin", duty="Sage", status="Immortal",
        skills=["Vedic knowledge","Authorship","Prophecy","Niyoga"],
        titles=["Vedavyasa","Krishna Dvaipayana","Chiranjivi"],
        traits=["Wise","Omniscient narrator","Dark-complexioned","Detached"],
        character_arc=["Born to Parashara and Satyavati on island","Compiled the Vedas",
            "Authored the Mahabharata","Fathered Dhritarashtra, Pandu, Vidura via Niyoga",
            "Witnessed and narrated the great war","Immortal sage"],
        key_relationships=[
            {"With":"@dhritarashtra","Type":"Father (Niyoga)"},
            {"With":"@pandu","Type":"Father (Niyoga)"},
            {"With":"@satyavati","Type":"Mother"},
            {"With":"@vaishampayana","Type":"Disciple"}],
        important_locations=["hastinapura","badarikashrama"])
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
        caste="Kshatriya", duty="King", dynasty="Yadava", status="Deceased",
        kingdom="dvaraka", political_role="King of Dvaraka",
        skills=["Diplomacy","Statecraft","Charioteer","Divine knowledge","Sudarshana Chakra","Flute"],
        divine_weapons=["Sudarshana Chakra","Kaumodaki mace","Sharnga bow","Nandaka sword"],
        titles=["Vasudeva","Keshava","Govinda","Madhava","Janardana","Purushottama",
            "Lord of Dvaraka","Yogeshvara","Parthasarathi"],
        traits=["Wise","Strategic","Divine","Playful","Just","Compassionate","Pragmatic"],
        character_arc=["Born to Devaki and Vasudeva in prison","Grew up in Gokula/Vrindavana",
            "Killed Kamsa","Built Dvaraka","Befriended Arjuna",
            "Burned Khandava forest with Arjuna","Killed Shishupala at Rajasuya",
            "Peace ambassador to Kauravas (failed)","Charioteer of Arjuna in war",
            "Delivered Bhagavad Gita","Guided Pandavas to victory","Cursed by Gandhari",
            "Yadava civil war (Mausala)","Shot by hunter Jara","Left mortal world"],
        key_relationships=[
            {"With":"@arjuna","Type":"Friend"},
            {"With":"@yudhishthira","Type":"Guide"},
            {"With":"@draupadi","Type":"Friend"},
            {"With":"@duryodhana","Type":"Adversary"},
            {"With":"@karna","Type":"Adversary"},
            {"With":"@balarama","Type":"Brother"},
            {"With":"@subhadra","Type":"Sister"},
            {"With":"@bhishma","Type":"Respected elder"}],
        important_locations=["dvaraka","mathura","vrindavana","hastinapura","indraprastha",
            "kurukshetra","khandava_forest"])
    add("Balarama", aliases=["Baladeva","Halayudhu","Haladhara","Sankarshana"],
        father="Vasudeva_father", mother="Rohini",
        siblings=["Krishna","Subhadra"],
        spouse=["Revati"], gender="Male",
        caste="Kshatriya", duty="Prince", dynasty="Yadava", status="Deceased",
        kingdom="dvaraka", political_role="Prince of Dvaraka",
        skills=["Mace combat","Plough weapon"],
        divine_weapons=["Plough (Hala)","Mace (Saunanda)"],
        titles=["Baladeva","Halayudha","Sankarshana"],
        traits=["Strong","Hot-tempered","Neutral in war","Fond of Duryodhana"],
        character_arc=["Born to Rohini (transferred from Devaki)","Trained Duryodhana and Bhima in mace",
            "Refused to fight in war (neutral)","Went on pilgrimage during war",
            "Angered at Bhima's foul blow to Duryodhana","Died during Mausala"],
        key_relationships=[
            {"With":"@krishna","Type":"Brother"},
            {"With":"@duryodhana","Type":"Guru"},
            {"With":"@bhima","Type":"Guru"}],
        important_locations=["dvaraka","mathura"])
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
        caste="Kshatriya", duty="King", dynasty="Anga", status="Deceased",
        kingdom="anga", political_role="King of Anga",
        skills=["Archery","Generosity","Chariot warfare"],
        divine_weapons=["Vijaya bow","Shakti weapon (from Indra)","Brahmastra",
            "Bhargavastra","Nagastra"],
        titles=["Radheya","Vasusena","Anga-raja","Danveer Karna","Vaikartana"],
        traits=["Generous","Loyal","Brave","Tragic","Cursed","Honorable"],
        character_arc=["Born to Kunti via Surya - abandoned at birth",
            "Raised by charioteer Adhiratha and Radha","Trained under Parashurama - cursed",
            "Humiliated at tournament - befriended by Duryodhana",
            "Made King of Anga by Duryodhana","Gave away Kavacha-Kundala to Indra",
            "Learned true identity from Kunti before war","Fought as Kaurava commander",
            "Killed by Arjuna on Day 17"],
        key_relationships=[
            {"With":"@duryodhana","Type":"Friend"},
            {"With":"@arjuna","Type":"Rival"},
            {"With":"@parashurama","Type":"Guru"},
            {"With":"@kunti","Type":"Mother"},
            {"With":"@indra","Type":"Adversary"},
            {"With":"@krishna","Type":"Adversary"}],
        important_locations=["hastinapura","anga","kurukshetra","champapuri"])
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
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased",
        kingdom="indraprastha", political_role="Prince",
        skills=["Archery","Chakravyuha penetration","Chariot warfare"],
        titles=["Soubhadra"],
        traits=["Brave","Young","Fearless","Tragic"],
        character_arc=["Born to Arjuna and Subhadra","Learned Chakravyuha entry in the womb",
            "Married Uttaraa of Matsya","Entered Chakravyuha on Day 13",
            "Killed treacherously by 7 warriors"],
        key_relationships=[
            {"With":"@arjuna","Type":"Father"},
            {"With":"@krishna","Type":"Uncle"},
            {"With":"@jayadratha","Type":"Enemy"},
            {"With":"@drona","Type":"Enemy"}],
        important_locations=["dvaraka","indraprastha","viratanagara","kurukshetra"])
    add("Ghatotkacha", father="Bhima", mother="Hidimba", gender="Male",
        caste="Rakshasa", duty="Warrior", status="Deceased",
        skills=["Shape-shifting","Sorcery","Aerial combat","Immense strength"],
        traits=["Brave","Devoted to father","Fierce","Selfless"],
        character_arc=["Born to Bhima and Hidimba in forest","Grew up among Rakshasas",
            "Joined Pandava army in war","Wreaked havoc on Kaurava forces at night",
            "Killed by Karna's Shakti weapon on Day 14"],
        key_relationships=[
            {"With":"@bhima","Type":"Father"},
            {"With":"@karna","Type":"Enemy"}],
        important_locations=["kurukshetra"])
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
        caste="Brahmin", duty="Teacher", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="Royal preceptor",
        skills=["All weapons mastery","Teaching","Archery","Brahmastra"],
        divine_weapons=["Brahmastra","Brahmashira","Agneyastra","Varunastra"],
        titles=["Dronacharya","Acharya","Guru of princes"],
        traits=["Greatest teacher","Partial to Arjuna","Vengeful","Tragic"],
        character_arc=["Born from pot (drona) to sage Bharadvaja","Trained under Parashurama",
            "Humiliated by Drupada","Became teacher of Kuru princes",
            "Favored Arjuna as best student","Demanded Ekalavya's thumb",
            "Captured Drupada - took half his kingdom","Fought for Kauravas",
            "Became commander after Bhishma fell (Days 11-15)",
            "Killed by Dhrishtadyumna after Ashvatthama deception"],
        key_relationships=[
            {"With":"@arjuna","Type":"Guru"},
            {"With":"@ashvatthama","Type":"Father"},
            {"With":"@drupada","Type":"Rival"},
            {"With":"@ekalavya","Type":"Guru"},
            {"With":"@parashurama","Type":"Guru"},
            {"With":"@dhrishtadyumna","Type":"Enemy"}],
        important_locations=["hastinapura","panchala","kurukshetra"])
    add("Ashvatthama", aliases=["Dronaputra"],
        father="Drona", mother="Kripi", gender="Male",
        caste="Brahmin", duty="Warrior", dynasty="Kuru", status="Immortal",
        skills=["All weapons mastery","Brahmastra","Narayanastra"],
        divine_weapons=["Narayanastra","Brahmashira","Brahmastra","Agneyastra"],
        titles=["Dronaputra","Chiranjivi"],
        traits=["Wrathful","Vengeful","Cursed","Immortal"],
        character_arc=["Son of Drona and Kripi","Grew up in poverty",
            "Trained alongside Kuru princes","Fought for Kauravas",
            "Attacked Pandava camp at night (Sauptika)","Killed Upapandavas in sleep",
            "Launched Brahmashira at Pandavas","Cursed by Krishna to wander 3000 years"],
        key_relationships=[
            {"With":"@drona","Type":"Father"},
            {"With":"@duryodhana","Type":"Friend"},
            {"With":"@arjuna","Type":"Rival"},
            {"With":"@dhrishtadyumna","Type":"Enemy"},
            {"With":"@krishna","Type":"Adversary"}],
        important_locations=["hastinapura","kurukshetra"])
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
        caste="Kshatriya", duty="Queen", dynasty="Panchala",
        kingdom="indraprastha", political_role="Queen",
        skills=["Statesmanship","Devotion","Endurance"],
        titles=["Panchali","Krishnaa","Yajnaseni","Queen of Indraprastha"],
        traits=["Fiery","Beautiful","Vengeful","Devoted","Proud","Resilient"],
        character_arc=["Born from sacrificial fire of Drupada","Won by Arjuna at Swayamvara",
            "Married all 5 Pandavas","Queen of Indraprastha",
            "Humiliated in dice game - vowed vengeance","13 years of exile",
            "Served as Sairandhri in Virata","Witnessed vengeance in war",
            "Lost all 5 sons (Upapandavas)","Fell during Mahaprasthana"],
        key_relationships=[
            {"With":"@krishna","Type":"Friend"},
            {"With":"@bhima","Type":"Spouse"},
            {"With":"@arjuna","Type":"Spouse"},
            {"With":"@duhshasana","Type":"Enemy"},
            {"With":"@duryodhana","Type":"Enemy"},
            {"With":"@kunti","Type":"Mother-in-law"}],
        important_locations=["panchala","hastinapura","indraprastha","kamyaka_forest","viratanagara","kurukshetra"])
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
        caste="Kshatriya", duty="King", dynasty="Sindhu", status="Deceased",
        kingdom="sindhu", political_role="King of Sindhu",
        skills=["Warfare","Boon of Shiva (hold Pandavas)"],
        traits=["Arrogant","Lustful","Cowardly"],
        character_arc=["King of Sindhu kingdom","Married Duhshala (Kaurava sister)",
            "Tried to abduct Draupadi in forest","Received boon from Shiva",
            "Blocked Pandavas from saving Abhimanyu (Day 13)",
            "Killed by Arjuna before sunset on Day 14"],
        key_relationships=[
            {"With":"@arjuna","Type":"Enemy"},
            {"With":"@abhimanyu","Type":"Enemy"},
            {"With":"@duryodhana","Type":"Ally"},
            {"With":"@duhshala","Type":"Spouse"}],
        important_locations=["sindhu","kurukshetra","kamyaka_forest"])
    add("Shakuni", aliases=["Soubala"],
        father="Subala", siblings=["Gandhari"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Gandhara", status="Deceased",
        kingdom="gandhara", political_role="King of Gandhara",
        skills=["Dice","Deception","Manipulation"],
        titles=["Soubala","Master of dice"],
        traits=["Cunning","Manipulative","Vengeful","Scheming"],
        character_arc=["Prince of Gandhara","Vowed revenge against Kuru (for Gandhari's marriage)",
            "Mastermind of dice game","Manipulated Duryodhana against Pandavas",
            "Fought in war","Killed by Sahadeva on Day 18"],
        key_relationships=[
            {"With":"@duryodhana","Type":"Guide"},
            {"With":"@gandhari","Type":"Brother"},
            {"With":"@yudhishthira","Type":"Enemy"},
            {"With":"@sahadeva","Type":"Enemy"}],
        important_locations=["hastinapura","gandhara","kurukshetra"])
    add("Subala", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Gandhara", status="Deceased")
    add("Shalya", aliases=["king of Madra","Madra king"],
        siblings=["Madri"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Madra", status="Deceased",
        kingdom="madra", political_role="King of Madra",
        skills=["Chariot warfare","Mace combat"],
        traits=["Honorable","Tricked into fighting for Kauravas"],
        character_arc=["Uncle of Pandavas (Madri's brother)","Tricked by Duryodhana into joining Kauravas",
            "Served as Karna's charioteer (to demoralize)","Became last Kaurava commander on Day 18",
            "Killed by Yudhishthira"],
        key_relationships=[
            {"With":"@yudhishthira","Type":"Nephew/Enemy"},
            {"With":"@karna","Type":"Antagonist (charioteer)"},
            {"With":"@duryodhana","Type":"Ally"}],
        important_locations=["madra","kurukshetra"])
    add("Ekalavya", aliases=["Nishada prince"], gender="Male",
        caste="Nishada", duty="Warrior",
        skills=["Archery","Self-taught mastery"],
        traits=["Devoted","Self-taught","Tragic","Humble"],
        character_arc=["Nishada prince","Rejected by Drona as student",
            "Built clay idol of Drona and self-trained","Surpassed Arjuna in archery",
            "Cut off his thumb as guru-dakshina to Drona"],
        key_relationships=[
            {"With":"@drona","Type":"Guru"},
            {"With":"@arjuna","Type":"Rival"}])
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
        if c.get('kingdom'):
            entry["Kingdom"] = f"@{c['kingdom']}"
        if c.get('political_role'):
            entry["Political_Role"] = c['political_role']
        if c.get('skills'):
            entry["Skills"] = c['skills']
        if c.get('divine_weapons'):
            entry["Divine_Weapons"] = c['divine_weapons']
        if c.get('titles'):
            entry["Titles"] = c['titles']
        if c.get('traits'):
            entry["Traits"] = c['traits']
        if c.get('character_arc'):
            entry["Character_Arc"] = c['character_arc']
        if c.get('key_relationships'):
            entry["Key_Relationships"] = c['key_relationships']
        if c.get('important_locations'):
            entry["Important_Locations"] = [f"@{loc}" for loc in c['important_locations']]
        # Auto-derive Lineage from father chain
        lineage = {}
        if c['father'] and c['father'] in chars:
            gf = chars[c['father']].get('father')
            if gf and gf in chars:
                lineage["Grandfather"] = f"@{gf}"
                ggf = chars[gf].get('father')
                if ggf and ggf in chars:
                    lineage["Great_Grandfather"] = f"@{ggf}"
        if lineage:
            entry["Lineage"] = lineage
        output[f"@{k}"] = entry

    out_path = os.path.join(json_dir, 'characters.json')
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
    with_kingdom = sum(1 for v in output.values() if 'Kingdom' in v)
    with_skills = sum(1 for v in output.values() if 'Skills' in v)
    with_weapons = sum(1 for v in output.values() if 'Divine_Weapons' in v)
    with_traits = sum(1 for v in output.values() if 'Traits' in v)
    with_arc = sum(1 for v in output.values() if 'Character_Arc' in v)
    with_lineage = sum(1 for v in output.values() if 'Lineage' in v)
    with_key_rel = sum(1 for v in output.values() if 'Key_Relationships' in v)
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
    print(f"  With Kingdom: {with_kingdom}, Skills: {with_skills}")
    print(f"  With Weapons: {with_weapons}, Traits: {with_traits}")
    print(f"  With Arc: {with_arc}, Lineage: {with_lineage}")
    print(f"  With Key Relationships: {with_key_rel}")
    print(f"  Gender - Male: {males}, Female: {females}, Unknown: {unknowns}")
    print(f"  Saved to characters.json")

    # ── Phase 5: Locations ──────────────────────────────────────
    locations = {
        # ─── Kingdoms ───
        "hastinapura": {
            "Name": "Hastinapura", "Type": "Kingdom",
            "Region": "Bharata",
            "Sub_Locations": ["@indraprastha"],
            "Ruler": "@dhritarashtra",
            "Famous_For": ["Capital of Kuru dynasty","Dice game","Court of Kauravas"],
            "Residents": ["@dhritarashtra","@gandhari","@duryodhana","@bhishma","@drona","@vidura","@kunti"],
            "Geography": {"Terrain": "Plains along Ganga","Climate": "Temperate"},
            "Modern_Equivalent": "Hastinapur, Meerut district, Uttar Pradesh",
            "Coordinates": {"lat": 29.1604, "lng": 78.0180},
            "Notes": "Primary capital of the Kuru kingdom. Archaeological site at Hastinapur village, Meerut."
        },
        "indraprastha": {
            "Name": "Indraprastha", "Type": "City",
            "Parent_Kingdom": "@hastinapura",
            "Region": "Bharata",
            "Ruler": "@yudhishthira",
            "Famous_For": ["Maya Sabha","Rajasuya Yajna","Pandava capital"],
            "Residents": ["@yudhishthira","@bhima","@arjuna","@nakula","@sahadeva","@draupadi"],
            "Geography": {"Terrain": "Plains along Yamuna","Climate": "Temperate"},
            "Modern_Equivalent": "Purana Qila area, Delhi",
            "Coordinates": {"lat": 28.6095, "lng": 77.2425},
            "Notes": "Built by Maya Danava for Pandavas on Khandava land. Identified with Purana Qila, Delhi."
        },
        "panchala": {
            "Name": "Panchala", "Type": "Kingdom",
            "Region": "Bharata",
            "Ruler": "@drupada",
            "Famous_For": ["Draupadi Swayamvara","Birth of Dhrishtadyumna","Allied with Pandavas"],
            "Residents": ["@drupada","@draupadi","@dhrishtadyumna","@shikhandi"],
            "Geography": {"Terrain": "Gangetic plains","Climate": "Temperate"},
            "Modern_Equivalent": "Ahichchhatra (North Panchala), Kampilya (South Panchala), Uttar Pradesh",
            "Coordinates": {"lat": 28.3670, "lng": 79.4304},
            "Notes": "Divided into North Panchala (capital Ahichchhatra) and South Panchala (capital Kampilya). Archaeological ruins at both sites."
        },
        "dvaraka": {
            "Name": "Dvaraka", "Type": "Kingdom",
            "Region": "Western Bharata",
            "Ruler": "@krishna",
            "Famous_For": ["Krishna's capital","Golden city","Submerged by sea"],
            "Residents": ["@krishna","@balarama","@rukmini","@satyabhama","@pradyumna"],
            "Geography": {"Terrain": "Coastal island city","Climate": "Tropical maritime"},
            "Modern_Equivalent": "Dwarka, Gujarat",
            "Coordinates": {"lat": 22.2442, "lng": 68.9685},
            "Notes": "Built by Vishwakarma; sank into sea after Mausala. Underwater ruins found by ASI off Dwarka coast."
        },
        "magadha": {
            "Name": "Magadha", "Type": "Kingdom",
            "Region": "Eastern Bharata",
            "Sub_Locations": ["@girivraja"],
            "Ruler": "@jarasandha",
            "Famous_For": ["Jarasandha's fortress","Wrestling duel with Bhima"],
            "Residents": ["@jarasandha"],
            "Geography": {"Terrain": "Hills and plains","Climate": "Subtropical"},
            "Modern_Equivalent": "Rajgir/Patna region, Bihar",
            "Coordinates": {"lat": 25.0283, "lng": 85.4218},
            "Notes": "Powerful eastern kingdom opposing Yadavas. Capital at Rajgir (Girivraja)."
        },
        "girivraja": {
            "Name": "Girivraja", "Type": "City",
            "Parent_Kingdom": "@magadha",
            "Region": "Eastern Bharata",
            "Famous_For": ["Jarasandha's capital","Surrounded by five hills"],
            "Geography": {"Terrain": "Hill-girt city","Climate": "Subtropical"},
            "Modern_Equivalent": "Rajgir, Bihar",
            "Coordinates": {"lat": 25.0268, "lng": 85.4210}
        },
        "kashi": {
            "Name": "Kashi", "Type": "Kingdom",
            "Region": "Bharata",
            "Famous_For": ["Swayamvara of princesses","Abduction by Bhishma","Sacred city"],
            "Geography": {"Terrain": "Banks of Ganga","Climate": "Subtropical"},
            "Modern_Equivalent": "Varanasi, Uttar Pradesh",
            "Coordinates": {"lat": 25.3176, "lng": 82.9739},
            "Notes": "Princesses Amba, Ambika, Ambalika abducted from here by Bhishma"
        },
        "chedi": {
            "Name": "Chedi", "Type": "Kingdom",
            "Region": "Central Bharata",
            "Ruler": "@shishupala",
            "Famous_For": ["Shishupala killed by Krishna at Rajasuya"],
            "Residents": ["@shishupala","@dhrishtaketu"],
            "Geography": {"Terrain": "Central Indian plateau","Climate": "Subtropical"},
            "Modern_Equivalent": "Banda/Sagar region, Madhya Pradesh",
            "Coordinates": {"lat": 25.4760, "lng": 80.3319},
            "Notes": "Capital identified with Suktimati or Sothivatinagara."
        },
        "anga": {
            "Name": "Anga", "Type": "Kingdom",
            "Region": "Eastern Bharata",
            "Ruler": "@karna",
            "Famous_For": ["Karna's kingdom","Given by Duryodhana"],
            "Residents": ["@karna","@vrishasena"],
            "Geography": {"Terrain": "Gangetic plains","Climate": "Subtropical"},
            "Modern_Equivalent": "Bhagalpur region, Bihar",
            "Coordinates": {"lat": 25.2425, "lng": 86.9842},
            "Notes": "Duryodhana crowned Karna king of Anga. Capital at Champa (modern Bhagalpur)."
        },
        "gandhara": {
            "Name": "Gandhara", "Type": "Kingdom",
            "Region": "Northwestern Bharata",
            "Ruler": "@shakuni",
            "Famous_For": ["Shakuni's kingdom","Gandhari's homeland"],
            "Residents": ["@shakuni","@subala"],
            "Geography": {"Terrain": "Mountain valleys","Climate": "Continental"},
            "Modern_Equivalent": "Peshawar valley / Taxila region, Pakistan",
            "Coordinates": {"lat": 34.0151, "lng": 71.5249},
            "Notes": "Capital at Takshashila (Taxila). One of the sixteen Mahajanapadas."
        },
        "sindhu": {
            "Name": "Sindhu", "Type": "Kingdom",
            "Region": "Western Bharata",
            "Ruler": "@jayadratha",
            "Famous_For": ["Jayadratha's kingdom","Blocked Pandavas in Chakravyuha day"],
            "Residents": ["@jayadratha","@duhshala"],
            "Geography": {"Terrain": "Indus river basin","Climate": "Arid"},
            "Modern_Equivalent": "Sindh, Pakistan",
            "Coordinates": {"lat": 25.3960, "lng": 68.3578}
        },
        "madra": {
            "Name": "Madra", "Type": "Kingdom",
            "Region": "Northwestern Bharata",
            "Ruler": "@shalya",
            "Famous_For": ["Shalya's kingdom","Madri's homeland"],
            "Residents": ["@shalya"],
            "Geography": {"Terrain": "Punjab plains","Climate": "Subtropical"},
            "Modern_Equivalent": "Sialkot region, Punjab",
            "Coordinates": {"lat": 32.4945, "lng": 74.5229}
        },
        "matsya": {
            "Name": "Matsya", "Type": "Kingdom",
            "Region": "Bharata",
            "Sub_Locations": ["@viratanagara"],
            "Ruler": "@virata",
            "Famous_For": ["Pandavas' incognito year","Uttara Gograhana battle"],
            "Residents": ["@virata","@uttaraa"],
            "Geography": {"Terrain": "Arid plains","Climate": "Semi-arid"},
            "Modern_Equivalent": "Jaipur/Bairat region, Rajasthan",
            "Coordinates": {"lat": 27.3117, "lng": 76.1775}
        },
        "viratanagara": {
            "Name": "Viratanagara", "Type": "City",
            "Parent_Kingdom": "@matsya",
            "Region": "Bharata",
            "Famous_For": ["Pandavas served in disguise for one year"],
            "Modern_Equivalent": "Bairat (Viratnagar), Rajasthan",
            "Coordinates": {"lat": 27.0238, "lng": 76.3817},
            "Notes": "Archaeological remains found at Bairat. Circular temple and Ashokan edict."
        },
        "pragjyotisha": {
            "Name": "Pragjyotisha", "Type": "Kingdom",
            "Region": "Eastern Bharata",
            "Ruler": "@bhagadatta",
            "Famous_For": ["Bhagadatta's elephant army","Naraka dynasty"],
            "Residents": ["@bhagadatta"],
            "Geography": {"Terrain": "Brahmaputra valley","Climate": "Subtropical humid"},
            "Modern_Equivalent": "Guwahati, Assam",
            "Coordinates": {"lat": 26.1445, "lng": 91.7362}
        },
        "manipura": {
            "Name": "Manipura", "Type": "Kingdom",
            "Region": "Eastern Bharata",
            "Ruler": "@chitrangada_manipura",
            "Famous_For": ["Arjuna married princess Chitrangada here"],
            "Residents": ["@chitrangada_manipura","@babhruvahana"],
            "Geography": {"Terrain": "Hills and valleys","Climate": "Subtropical"},
            "Modern_Equivalent": "Imphal, Manipur",
            "Coordinates": {"lat": 24.8170, "lng": 93.9368}
        },
        "trigarta": {
            "Name": "Trigarta", "Type": "Kingdom",
            "Region": "Northern Bharata",
            "Ruler": "@susharma",
            "Famous_For": ["Susharma's alliance with Kauravas","Attack on Matsya"],
            "Residents": ["@susharma"],
            "Geography": {"Terrain": "Foothills between three rivers","Climate": "Continental"},
            "Modern_Equivalent": "Jalandhar, Punjab",
            "Coordinates": {"lat": 31.3260, "lng": 75.5762},
            "Notes": "Name means 'land between three rivers' (Ravi, Beas, Sutlej)."
        },
        "koshala": {
            "Name": "Koshala", "Type": "Kingdom",
            "Region": "Bharata",
            "Famous_For": ["Ancient kingdom","Rama's kingdom"],
            "Geography": {"Terrain": "Gangetic plains","Climate": "Subtropical"},
            "Modern_Equivalent": "Ayodhya/Faizabad region, Uttar Pradesh",
            "Coordinates": {"lat": 26.7922, "lng": 82.1998}
        },
        "vidarbha": {
            "Name": "Vidarbha", "Type": "Kingdom",
            "Region": "Central Bharata",
            "Famous_For": ["Rukmini's homeland","Nala-Damayanti story"],
            "Residents": ["@rukmini","@damayanti","@bhima_vidarbha"],
            "Geography": {"Terrain": "Deccan plateau","Climate": "Tropical"},
            "Modern_Equivalent": "Nagpur/Amravati region, Maharashtra",
            "Coordinates": {"lat": 21.1458, "lng": 79.0882},
            "Notes": "Capital identified with Kundina (modern Kaundinyapur near Amravati)."
        },
        "nishadha": {
            "Name": "Nishadha", "Type": "Kingdom",
            "Region": "Bharata",
            "Ruler": "@nala",
            "Famous_For": ["Nala-Damayanti love story"],
            "Residents": ["@nala"],
            "Geography": {"Terrain": "Plains","Climate": "Subtropical"},
            "Modern_Equivalent": "Narwar/Gwalior region, Madhya Pradesh",
            "Coordinates": {"lat": 25.6400, "lng": 77.9100}
        },
        "kalinga": {
            "Name": "Kalinga", "Type": "Kingdom",
            "Region": "Eastern Bharata",
            "Famous_For": ["Participated in Kurukshetra War"],
            "Geography": {"Terrain": "Coastal","Climate": "Tropical"},
            "Modern_Equivalent": "Bhubaneswar/Puri region, Odisha",
            "Coordinates": {"lat": 20.2961, "lng": 85.8245}
        },
        "vanga": {
            "Name": "Vanga", "Type": "Kingdom",
            "Region": "Eastern Bharata",
            "Famous_For": ["Eastern kingdom","Participated in war"],
            "Geography": {"Terrain": "Delta region","Climate": "Tropical"},
            "Modern_Equivalent": "Bengal (West Bengal/Bangladesh)",
            "Coordinates": {"lat": 22.5726, "lng": 88.3639}
        },
        "kunti_kingdom": {
            "Name": "Kunti", "Type": "Kingdom",
            "Region": "Bharata",
            "Famous_For": ["Kunti's adoptive homeland","Kuntibhoja's kingdom"],
            "Modern_Equivalent": "Kota/Bundi region, Rajasthan",
            "Coordinates": {"lat": 25.2138, "lng": 75.8648},
            "Notes": "Kingdom of Kuntibhoja where Pritha (Kunti) grew up. Identified with area around Bundi."
        },
        "champapuri": {
            "Name": "Champapuri", "Type": "City",
            "Parent_Kingdom": "@anga",
            "Region": "Eastern Bharata",
            "Famous_For": ["Capital of Anga kingdom","Karna's capital"],
            "Modern_Equivalent": "Champanagar near Bhagalpur, Bihar",
            "Coordinates": {"lat": 25.2440, "lng": 87.0010}
        },
        # ─── Battlefield ───
        "kurukshetra": {
            "Name": "Kurukshetra", "Type": "Battlefield",
            "Region": "Bharata",
            "Famous_For": ["18-day Mahabharata War","Bhagavad Gita delivered here"],
            "Geography": {"Terrain": "Sacred plains","Climate": "Semi-arid"},
            "Modern_Equivalent": "Kurukshetra, Haryana",
            "Coordinates": {"lat": 29.9695, "lng": 76.8783},
            "Notes": "Dharmakshetra - field of righteousness. Jyotisar - exact spot of Gita Upadesh."
        },
        # ─── Forests ───
        "khandava_forest": {
            "Name": "Khandava Forest", "Type": "Forest",
            "Region": "Bharata",
            "Famous_For": ["Burned by Arjuna and Krishna","Indraprastha built on its land"],
            "Nearby_Locations": ["@indraprastha"],
            "Modern_Equivalent": "South Delhi / Faridabad region",
            "Coordinates": {"lat": 28.5000, "lng": 77.3000},
            "Notes": "Agni consumed this forest with help of Arjuna and Krishna. Region south of Indraprastha."
        },
        "kamyaka_forest": {
            "Name": "Kamyaka Forest", "Type": "Forest",
            "Region": "Bharata",
            "Famous_For": ["Pandavas' exile forest","Nala-Damayanti story told here"],
            "Modern_Equivalent": "Near Kurukshetra/Sarasvati river bank, Haryana",
            "Coordinates": {"lat": 29.5500, "lng": 76.9000},
            "Notes": "Main forest during Pandavas' 12-year exile. Identified near banks of old Sarasvati."
        },
        "dvaitavana": {
            "Name": "Dvaitavana", "Type": "Forest",
            "Region": "Bharata",
            "Famous_For": ["Pandavas' exile","Near a lake","Duryodhana captured by Gandharvas here"],
            "Modern_Equivalent": "Near Sthaneshwar (Thanesar), Haryana",
            "Coordinates": {"lat": 29.9700, "lng": 76.8200},
            "Notes": "Forest of exile near a sacred lake. Located close to Kurukshetra."
        },
        "naimisha_forest": {
            "Name": "Naimisha Forest", "Type": "Forest",
            "Region": "Bharata",
            "Famous_For": ["Ugrasrava narrated Mahabharata here","Sacred to sages"],
            "Modern_Equivalent": "Nimsar (Naimisharanya), Uttar Pradesh",
            "Coordinates": {"lat": 26.7460, "lng": 80.4530},
            "Notes": "Where the outer frame story of Mahabharata is set. Active pilgrimage site today."
        },
        "dandaka_forest": {
            "Name": "Dandaka Forest", "Type": "Forest",
            "Region": "Central Bharata",
            "Famous_For": ["Rama's exile in Ramayana","Dense ancient forest"],
            "Geography": {"Terrain": "Dense tropical forest","Climate": "Tropical"},
            "Modern_Equivalent": "Dandakaranya, Chhattisgarh/Maharashtra border",
            "Coordinates": {"lat": 19.5000, "lng": 80.0000}
        },
        # ─── Rivers (representative point along the river) ───
        "ganga_river": {
            "Name": "Ganga", "Type": "River",
            "Region": "Bharata",
            "Famous_For": ["Sacred river","Shantanu met Ganga here","Bhishma's mother"],
            "Geography": {"Terrain": "Major river flowing east to Bay of Bengal","Climate": "Varied"},
            "Modern_Equivalent": "Ganga at Haridwar (origin to plains)",
            "Coordinates": {"lat": 29.9457, "lng": 78.1642},
            "Notes": "Personified as goddess Ganga, mother of Bhishma. Shantanu met her near Hastinapura."
        },
        "yamuna_river": {
            "Name": "Yamuna", "Type": "River",
            "Region": "Bharata",
            "Famous_For": ["Flows past Indraprastha","Krishna's childhood river"],
            "Geography": {"Terrain": "Tributary of Ganga","Climate": "Temperate"},
            "Modern_Equivalent": "Yamuna at Delhi (flows past Purana Qila/Indraprastha)",
            "Coordinates": {"lat": 28.6100, "lng": 77.2500},
            "Notes": "Also known as Kalindi. Flows past Indraprastha (Delhi), Mathura, and Vrindavana."
        },
        "sarasvati_river": {
            "Name": "Sarasvati", "Type": "River",
            "Region": "Bharata",
            "Famous_For": ["Sacred river","Pilgrimage sites along banks","Balarama's pilgrimage"],
            "Geography": {"Terrain": "Dried up in places","Climate": "Semi-arid"},
            "Modern_Equivalent": "Dried Sarasvati channel near Kurukshetra/Pehowa, Haryana",
            "Coordinates": {"lat": 29.9800, "lng": 76.5800},
            "Notes": "Mentioned as flowing near Kurukshetra. Dried channel identified via satellite imagery."
        },
        "sindhu_river": {
            "Name": "Sindhu (Indus)", "Type": "River",
            "Region": "Northwestern Bharata",
            "Famous_For": ["Western boundary of Bharata","Major river of west"],
            "Geography": {"Terrain": "Large river flowing south","Climate": "Arid to semi-arid"},
            "Modern_Equivalent": "Indus River at Attock, Pakistan",
            "Coordinates": {"lat": 33.7740, "lng": 72.3609}
        },
        "godavari_river": {
            "Name": "Godavari", "Type": "River",
            "Region": "Southern Bharata",
            "Famous_For": ["Sacred southern river","Pilgrimage sites"],
            "Geography": {"Terrain": "Major peninsular river","Climate": "Tropical"},
            "Modern_Equivalent": "Godavari at Nashik (source), Maharashtra",
            "Coordinates": {"lat": 19.9975, "lng": 73.7898}
        },
        "narmada_river": {
            "Name": "Narmada", "Type": "River",
            "Region": "Central Bharata",
            "Famous_For": ["Sacred river","Boundary between north and south"],
            "Geography": {"Terrain": "Flows westward through central India","Climate": "Tropical"},
            "Modern_Equivalent": "Narmada at Jabalpur, Madhya Pradesh",
            "Coordinates": {"lat": 23.1815, "lng": 79.9864}
        },
        # ─── Mountains ───
        "himalayas": {
            "Name": "Himalayas", "Type": "Mountain",
            "Region": "Northern Bharata",
            "Famous_For": ["Abode of gods","Arjuna's penance for Pashupatastra",
                "Pandavas' final journey (Mahaprasthana)","Shiva's abode"],
            "Geography": {"Terrain": "Highest mountain range","Climate": "Alpine/glacial"},
            "Modern_Equivalent": "Kedarnath/Badrinath region, Uttarakhand",
            "Coordinates": {"lat": 30.7346, "lng": 79.0669},
            "Notes": "Site of Arjuna's tapas, Pandavas' ascent in Mahaprasthanika Parva"
        },
        "meru": {
            "Name": "Mount Meru", "Type": "Mountain",
            "Region": "Cosmic center",
            "Famous_For": ["Center of universe","Abode of gods","Golden mountain"],
            "Geography": {"Terrain": "Mythical golden peak","Climate": "Divine"},
            "Mythical": True,
            "Notes": "Cosmic mountain at center of universe in Hindu cosmology. No physical location."
        },
        "gandhamadana": {
            "Name": "Gandhamadana", "Type": "Mountain",
            "Region": "Northern Bharata",
            "Famous_For": ["Bhima met Hanuman here","Fragrant herbs","Kubera's garden"],
            "Geography": {"Terrain": "Fragrant mountain","Climate": "Alpine"},
            "Modern_Equivalent": "Near Badrinath, Uttarakhand / Kailash range",
            "Coordinates": {"lat": 30.7500, "lng": 79.5000},
            "Notes": "Bhima encountered Hanuman while searching for Saugandhika lotus"
        },
        "kailasa": {
            "Name": "Kailasa", "Type": "Mountain",
            "Region": "Northern Bharata",
            "Famous_For": ["Abode of Shiva and Parvati","Kubera's residence"],
            "Geography": {"Terrain": "Sacred peak","Climate": "Alpine/glacial"},
            "Modern_Equivalent": "Mount Kailash, Tibet (China)",
            "Coordinates": {"lat": 31.0672, "lng": 81.3119},
            "Notes": "Mount Kailash - sacred abode of Lord Shiva. Active pilgrimage destination."
        },
        "vindhya": {
            "Name": "Vindhya", "Type": "Mountain",
            "Region": "Central Bharata",
            "Famous_For": ["Divides north and south India","Ancient mountain range"],
            "Geography": {"Terrain": "Old mountain range","Climate": "Tropical"},
            "Modern_Equivalent": "Vindhya Range, Madhya Pradesh",
            "Coordinates": {"lat": 24.0000, "lng": 80.5000}
        },
        # ─── Celestial / Divine (no physical coordinates) ───
        "svarga": {
            "Name": "Svarga", "Type": "Celestial",
            "Region": "Cosmic",
            "Ruler": "@indra",
            "Famous_For": ["Heaven of gods","Arjuna trained here","Pandavas ascended here"],
            "Residents": ["@indra"],
            "Mythical": True,
            "Notes": "Indra's heaven; Arjuna spent time here learning weapons and dance"
        },
        "brahmaloka": {
            "Name": "Brahmaloka", "Type": "Celestial",
            "Region": "Cosmic",
            "Ruler": "@brahma",
            "Famous_For": ["Highest heaven","Abode of Brahma"],
            "Mythical": True,
            "Notes": "The highest celestial realm"
        },
        "patala": {
            "Name": "Patala", "Type": "Celestial",
            "Region": "Cosmic",
            "Famous_For": ["Underworld","Realm of Nagas","Arjuna visited Ulupi here"],
            "Mythical": True,
            "Notes": "Subterranean realm of Nagas"
        },
        "amaravati": {
            "Name": "Amaravati", "Type": "Celestial",
            "Region": "Cosmic",
            "Ruler": "@indra",
            "Famous_For": ["Capital of Svarga","Indra's court"],
            "Mythical": True,
            "Notes": "City of the gods in Indra's heaven"
        },
        # ─── Other cities/places ───
        "ekachakra": {
            "Name": "Ekachakra", "Type": "Village",
            "Region": "Bharata",
            "Famous_For": ["Bhima killed Bakasura here","Pandavas lived in disguise"],
            "Modern_Equivalent": "Arrah/Chakranagar, Bihar",
            "Coordinates": {"lat": 25.5549, "lng": 84.6634},
            "Notes": "Pandavas stayed here as Brahmins after Lakshagriha escape"
        },
        "upaplavya": {
            "Name": "Upaplavya", "Type": "City",
            "Parent_Kingdom": "@matsya",
            "Region": "Bharata",
            "Famous_For": ["Pandava war camp","Alliance meetings before war"],
            "Modern_Equivalent": "Near Bairat, Rajasthan",
            "Coordinates": {"lat": 27.0500, "lng": 76.4000},
            "Notes": "City in Matsya where Pandavas gathered allies before war"
        },
        "mathura": {
            "Name": "Mathura", "Type": "City",
            "Region": "Bharata",
            "Famous_For": ["Krishna's birthplace","Kamsa's capital"],
            "Geography": {"Terrain": "Banks of Yamuna","Climate": "Subtropical"},
            "Modern_Equivalent": "Mathura, Uttar Pradesh",
            "Coordinates": {"lat": 27.4924, "lng": 77.6737},
            "Notes": "Krishna was born here in Kamsa's prison. Keshava Deo temple at birthplace."
        },
        "vrindavana": {
            "Name": "Vrindavana", "Type": "Village",
            "Region": "Bharata",
            "Famous_For": ["Krishna's childhood","Gokula nearby"],
            "Nearby_Locations": ["@mathura"],
            "Geography": {"Terrain": "Banks of Yamuna","Climate": "Subtropical"},
            "Modern_Equivalent": "Vrindavan, Uttar Pradesh",
            "Coordinates": {"lat": 27.5830, "lng": 77.7013}
        },
        "shatashriga": {
            "Name": "Shatashriga", "Type": "Mountain",
            "Region": "Northern Bharata",
            "Famous_For": ["Pandu's death","Pandavas' early childhood"],
            "Modern_Equivalent": "Near Haridwar/Rishikesh foothills, Uttarakhand",
            "Coordinates": {"lat": 30.0869, "lng": 78.2676},
            "Notes": "Mountain where Pandu lived in exile and died. Identified with Shivalik foothills."
        },
        "badarikashrama": {
            "Name": "Badarikashrama", "Type": "Hermitage",
            "Region": "Northern Bharata",
            "Famous_For": ["Vyasa's ashram","Nara-Narayana tapas"],
            "Geography": {"Terrain": "Himalayan valley","Climate": "Alpine"},
            "Modern_Equivalent": "Badrinath, Uttarakhand",
            "Coordinates": {"lat": 30.7433, "lng": 79.4938}
        },
        "lakshagriha": {
            "Name": "Lakshagriha", "Type": "City",
            "Region": "Bharata",
            "Famous_For": ["House of lac","Duryodhana's plot to burn Pandavas"],
            "Modern_Equivalent": "Barnawa (Varanavata), Baghpat district, Uttar Pradesh",
            "Coordinates": {"lat": 29.0700, "lng": 77.3800},
            "Notes": "Also called Varanavata; trap set for Pandavas. Lacquer mound (Laksha ka Tila) survives at Barnawa."
        },
    }

    # Compute distances between locations using haversine formula
    import math
    def _haversine(lat1, lng1, lat2, lng2):
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # For each location with coordinates, find nearby locations (within 500 km)
    # and compute distances to ALL other coordinate-bearing locations
    coord_locs = {lid: loc for lid, loc in locations.items() if loc.get("Coordinates")}
    for lid, loc in coord_locs.items():
        c1 = loc["Coordinates"]
        nearby = []
        for other_id, other_loc in coord_locs.items():
            if other_id == lid:
                continue
            c2 = other_loc["Coordinates"]
            dist = round(_haversine(c1["lat"], c1["lng"], c2["lat"], c2["lng"]))
            if dist <= 500:
                nearby.append({"To": f"@{other_id}", "Name": other_loc["Name"], "km": dist})
        # Sort by distance
        nearby.sort(key=lambda x: x["km"])
        if nearby:
            loc["Nearby_Distances_km"] = nearby

    # Build locations output
    loc_output = {}
    for loc_id, loc in locations.items():
        entry = {"Name": loc["Name"], "Type": loc["Type"]}
        if loc.get("Parent_Kingdom"):
            entry["Parent_Kingdom"] = loc["Parent_Kingdom"]
        entry["Region"] = loc.get("Region", "Bharata")
        if loc.get("Sub_Locations"):
            entry["Sub_Locations"] = loc["Sub_Locations"]
        if loc.get("Nearby_Locations"):
            entry["Nearby_Locations"] = loc["Nearby_Locations"]
        if loc.get("Ruler"):
            entry["Ruler"] = loc["Ruler"]
        if loc.get("Famous_For"):
            entry["Famous_For"] = loc["Famous_For"]
        if loc.get("Residents"):
            entry["Residents"] = loc["Residents"]
        if loc.get("Geography"):
            entry["Geography"] = loc["Geography"]
        if loc.get("Coordinates"):
            entry["Coordinates"] = loc["Coordinates"]
        if loc.get("Mythical"):
            entry["Mythical"] = True
        if loc.get("Modern_Equivalent"):
            entry["Modern_Equivalent"] = loc["Modern_Equivalent"]
        if loc.get("Nearby_Distances_km"):
            entry["Nearby_Distances_km"] = loc["Nearby_Distances_km"]
        if loc.get("Notes"):
            entry["Notes"] = loc["Notes"]
        loc_output[f"@{loc_id}"] = entry

    loc_path = os.path.join(json_dir, 'locations.json')
    with open(loc_path, 'w', encoding='utf-8') as f:
        json.dump(loc_output, f, ensure_ascii=False, indent=2)
    print(f"\n  LOCATIONS: {len(loc_output)} locations saved to locations.json")
    with_coords = sum(1 for v in loc_output.values() if 'Coordinates' in v)
    mythical = sum(1 for v in loc_output.values() if v.get('Mythical'))
    with_distances = sum(1 for v in loc_output.values() if 'Nearby_Distances_km' in v)
    print(f"    With coordinates: {with_coords}, Mythical: {mythical}")
    print(f"    With nearby distances: {with_distances}")
    type_counts = {}
    for v in loc_output.values():
        t = v['Type']
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, c in sorted(type_counts.items()):
        print(f"    {t}: {c}")

    # ── Phase 6: Timeline ───────────────────────────────────────
    timeline = [
        # ─── Pre-War Era ───
        {"Order":1, "Year":-80, "Era":"Pre-War",
         "Event_Name":"Birth of Bhishma",
         "Description":"Devavrata born to King Shantanu and goddess Ganga, the eighth Vasu incarnate.",
         "Location":"@hastinapura", "Participants":["@bhishma","@shantanu","@ganga"],
         "Outcome":"Ganga returns to heaven after giving Devavrata to Shantanu",
         "Consequences":["Bhishma raised as crown prince of Hastinapura"]},

        {"Order":2, "Year":-78, "Era":"Pre-War",
         "Event_Name":"Bhishma's Vow of Celibacy",
         "Description":"Devavrata takes terrible vow of lifelong celibacy so Shantanu can marry Satyavati.",
         "Location":"@hastinapura", "Participants":["@bhishma","@shantanu","@satyavati"],
         "Outcome":"Shantanu marries Satyavati; Devavrata becomes Bhishma",
         "Consequences":["Kuru succession crisis in future","Bhishma can never be king"]},

        {"Order":3, "Year":-60, "Era":"Pre-War",
         "Event_Name":"Niyoga - Birth of Dhritarashtra, Pandu, Vidura",
         "Description":"Vyasa fathers Dhritarashtra (from Ambika), Pandu (from Ambalika), and Vidura (from maid) through Niyoga at Satyavati's request.",
         "Location":"@hastinapura", "Participants":["@vyasa","@ambika","@ambalika","@satyavati"],
         "Outcome":"Three sons born to continue Kuru line",
         "Consequences":["Dhritarashtra born blind","Pandu born pale","Vidura born wise"]},

        {"Order":4, "Year":-40, "Era":"Pre-War",
         "Event_Name":"Pandu Crowned King",
         "Description":"Pandu crowned king of Hastinapura as Dhritarashtra is blind.",
         "Location":"@hastinapura", "Participants":["@pandu","@dhritarashtra","@bhishma"],
         "Outcome":"Pandu becomes king, conquers many kingdoms",
         "Consequences":["Dhritarashtra passed over due to blindness"]},

        {"Order":5, "Year":-38, "Era":"Pre-War",
         "Event_Name":"Pandu's Curse by Kindama",
         "Description":"Pandu accidentally kills sage Kindama in deer form; cursed to die if he approaches a woman.",
         "Location":"@shatashriga", "Participants":["@pandu"],
         "Outcome":"Pandu retires to forest with Kunti and Madri",
         "Consequences":["Sons born through divine invocation instead"]},

        {"Order":6, "Year":-36, "Era":"Pre-War",
         "Event_Name":"Karna Born and Abandoned",
         "Description":"Kunti invokes Surya using Durvasa's mantra; Karna born with divine armor (Kavacha-Kundala). Kunti abandons infant in river.",
         "Location":"@hastinapura", "Participants":["@kunti","@surya","@karna"],
         "Outcome":"Karna found and raised by charioteer Adhiratha and Radha",
         "Consequences":["Karna's identity unknown until before war","Source of epic tragedy"]},

        {"Order":7, "Year":-35, "Era":"Pre-War",
         "Event_Name":"Birth of Yudhishthira",
         "Description":"Kunti invokes Yama (Dharma); Yudhishthira born as eldest Pandava.",
         "Location":"@shatashriga", "Participants":["@kunti","@yama","@yudhishthira"],
         "Outcome":"Eldest Pandava born"},

        {"Order":8, "Year":-34, "Era":"Pre-War",
         "Event_Name":"Birth of Bhima",
         "Description":"Kunti invokes Vayu; Bhima born with immense strength.",
         "Location":"@shatashriga", "Participants":["@kunti","@vayu","@bhima"],
         "Outcome":"Second Pandava born"},

        {"Order":9, "Year":-33, "Era":"Pre-War",
         "Event_Name":"Birth of 100 Kauravas",
         "Description":"Gandhari gives birth to a mass of flesh; Vyasa divides it into 101 pots. 100 sons and 1 daughter (Duhshala) born. Duryodhana is firstborn.",
         "Location":"@hastinapura", "Participants":["@gandhari","@vyasa","@duryodhana","@duhshala"],
         "Outcome":"100 Kaurava sons and Duhshala born",
         "Consequences":["Omens at Duryodhana's birth - jackals howled"]},

        {"Order":10, "Year":-33, "Era":"Pre-War",
         "Event_Name":"Birth of Arjuna",
         "Description":"Kunti invokes Indra; Arjuna born as third Pandava.",
         "Location":"@shatashriga", "Participants":["@kunti","@indra","@arjuna"],
         "Outcome":"Greatest archer born"},

        {"Order":11, "Year":-32, "Era":"Pre-War",
         "Event_Name":"Birth of Nakula and Sahadeva",
         "Description":"Madri invokes Ashvins using Kunti's mantra; twin sons Nakula and Sahadeva born.",
         "Location":"@shatashriga", "Participants":["@madri","@ashvins","@nakula","@sahadeva"],
         "Outcome":"Twin Pandavas born"},

        {"Order":12, "Year":-30, "Era":"Pre-War",
         "Event_Name":"Death of Pandu",
         "Description":"Pandu approaches Madri despite the curse and dies. Madri commits sati.",
         "Location":"@shatashriga", "Participants":["@pandu","@madri"],
         "Outcome":"Pandu and Madri die; Kunti brings Pandavas to Hastinapura",
         "Consequences":["Pandavas raised in Hastinapura","Dhritarashtra becomes king"]},

        {"Order":13, "Year":-22, "Era":"Pre-War",
         "Event_Name":"Education under Drona",
         "Description":"Drona becomes teacher of Kuru princes. Arjuna proves best student.",
         "Location":"@hastinapura", "Participants":["@drona","@arjuna","@bhima","@yudhishthira","@duryodhana","@karna","@ashvatthama"],
         "Outcome":"Princes trained in warfare",
         "Consequences":["Arjuna becomes greatest archer","Rivalry between Pandavas and Kauravas deepens"]},

        {"Order":14, "Year":-21, "Era":"Pre-War",
         "Event_Name":"Ekalavya's Thumb",
         "Description":"Ekalavya, self-taught archer, gives his thumb as guru-dakshina to Drona.",
         "Participants":["@ekalavya","@drona","@arjuna"],
         "Outcome":"Ekalavya can no longer shoot as well",
         "Consequences":["Arjuna's supremacy in archery preserved"]},

        {"Order":15, "Year":-20, "Era":"Pre-War",
         "Event_Name":"Tournament and Karna's Appearance",
         "Description":"Kuru princes display skills. Karna arrives and challenges Arjuna. Duryodhana crowns Karna king of Anga.",
         "Location":"@hastinapura", "Participants":["@karna","@arjuna","@duryodhana","@drona"],
         "Outcome":"Karna-Duryodhana friendship formed",
         "Consequences":["Karna becomes king of Anga","Lifetime rivalry with Arjuna begins"]},

        {"Order":16, "Year":-18, "Era":"Pre-War",
         "Event_Name":"Lakshagriha (House of Lac)",
         "Description":"Duryodhana plots to burn Pandavas in house of lac at Varanavata. Vidura warns them; they escape through tunnel.",
         "Location":"@lakshagriha", "Participants":["@duryodhana","@yudhishthira","@vidura","@bhima"],
         "Outcome":"Pandavas escape; world believes them dead",
         "Consequences":["Pandavas live in hiding","Bhima kills Bakasura"]},

        {"Order":17, "Year":-17, "Era":"Pre-War",
         "Event_Name":"Bhima Kills Bakasura",
         "Description":"While hiding at Ekachakra, Bhima kills the demon Bakasura terrorizing the village.",
         "Location":"@ekachakra", "Participants":["@bhima"],
         "Outcome":"Bakasura killed; village freed"},

        {"Order":18, "Year":-16, "Era":"Pre-War",
         "Event_Name":"Draupadi Swayamvara",
         "Description":"Arjuna (disguised as Brahmin) strings the bow and wins Draupadi. Kunti says share; Draupadi marries all five Pandavas.",
         "Location":"@panchala", "Participants":["@arjuna","@draupadi","@drupada","@kunti","@yudhishthira","@bhima","@nakula","@sahadeva","@karna"],
         "Outcome":"Draupadi marries all five Pandavas",
         "Consequences":["Pandavas revealed alive","Alliance with Panchala"]},

        {"Order":19, "Year":-15, "Era":"Pre-War",
         "Event_Name":"Indraprastha Built",
         "Description":"Pandavas receive Khandavaprastha, clear land; Maya Danava builds magnificent palace of Indraprastha.",
         "Location":"@indraprastha", "Participants":["@yudhishthira","@arjuna","@krishna"],
         "Outcome":"Pandavas establish their own kingdom",
         "Consequences":["Pandava power grows","Duryodhana's jealousy intensifies"]},

        {"Order":20, "Year":-14, "Era":"Pre-War",
         "Event_Name":"Burning of Khandava Forest",
         "Description":"Arjuna and Krishna help Agni burn Khandava forest. Arjuna receives Gandiva bow.",
         "Location":"@khandava_forest", "Participants":["@arjuna","@krishna","@agni","@indra"],
         "Outcome":"Forest burned; Maya Danava saved; Gandiva obtained by Arjuna",
         "Consequences":["Arjuna gets Gandiva bow","Maya builds Sabha for Pandavas","Takshaka's enmity"]},

        {"Order":21, "Year":-10, "Era":"Pre-War",
         "Event_Name":"Rajasuya Yajna",
         "Description":"Yudhishthira performs Rajasuya Yajna and is crowned emperor. Shishupala killed by Krishna.",
         "Location":"@indraprastha", "Participants":["@yudhishthira","@krishna","@shishupala","@bhima","@arjuna"],
         "Outcome":"Yudhishthira crowned emperor; Shishupala slain by Krishna's Sudarshana Chakra",
         "Consequences":["Duryodhana humiliated at Maya Sabha","Seeds of dice game"]},

        {"Order":22, "Year":-10, "Era":"Pre-War",
         "Event_Name":"Bhima Kills Jarasandha",
         "Description":"Before Rajasuya, Krishna, Arjuna, and Bhima go to Magadha. Bhima kills Jarasandha in wrestling duel.",
         "Location":"@girivraja", "Participants":["@bhima","@krishna","@arjuna","@jarasandha"],
         "Outcome":"Jarasandha killed; imprisoned kings freed",
         "Consequences":["Obstacle to Rajasuya removed","Magadha weakened"]},

        {"Order":23, "Year":-8, "Era":"Pre-War",
         "Event_Name":"The Dice Game",
         "Description":"Shakuni defeats Yudhishthira in rigged dice game. Pandavas lose kingdom, wealth, Draupadi. Draupadi humiliated in court (vastraharan).",
         "Location":"@hastinapura", "Participants":["@yudhishthira","@shakuni","@duryodhana","@duhshasana","@draupadi","@dhritarashtra","@vidura","@bhishma","@karna"],
         "Outcome":"Pandavas lose everything; Draupadi disrobed; Krishna saves her",
         "Consequences":["Pandavas exiled 13 years (12 forest + 1 incognito)","Draupadi vows vengeance","War becomes inevitable"]},

        {"Order":24, "Year":-8, "Era":"Pre-War",
         "Event_Name":"Second Dice Game",
         "Description":"Called back for second dice game; Pandavas lose again. Sentenced to 12 years forest exile + 1 year incognito.",
         "Location":"@hastinapura", "Participants":["@yudhishthira","@shakuni"],
         "Outcome":"Pandavas begin exile"},

        # ─── Exile Era ───
        {"Order":25, "Year":-8, "Era":"Exile",
         "Event_Name":"Pandavas Enter Forest Exile",
         "Description":"Pandavas depart Hastinapura for 12-year forest exile. Citizens follow them.",
         "Location":"@kamyaka_forest", "Participants":["@yudhishthira","@bhima","@arjuna","@nakula","@sahadeva","@draupadi"],
         "Outcome":"Pandavas begin forest wandering"},

        {"Order":26, "Year":-7, "Era":"Exile",
         "Event_Name":"Arjuna's Penance for Pashupatastra",
         "Description":"Arjuna travels to Himalayas, performs severe penance. Shiva (as Kirata hunter) grants Pashupatastra after combat.",
         "Location":"@himalayas", "Participants":["@arjuna","@shiva"],
         "Outcome":"Arjuna receives Pashupatastra",
         "Consequences":["Arjuna receives other divine weapons from gods"]},

        {"Order":27, "Year":-6, "Era":"Exile",
         "Event_Name":"Arjuna in Svarga",
         "Description":"Arjuna taken to Indra's heaven. Trains under Indra and celestial warriors. Cursed by Urvashi (becomes eunuch for one year).",
         "Location":"@svarga", "Participants":["@arjuna","@indra"],
         "Outcome":"Arjuna masters celestial weapons",
         "Consequences":["Urvashi's curse useful during incognito year as Brihannala"]},

        {"Order":28, "Year":-5, "Era":"Exile",
         "Event_Name":"Jayadratha Abducts Draupadi",
         "Description":"Jayadratha attempts to abduct Draupadi while Pandavas are away. Captured and humiliated by Bhima.",
         "Location":"@kamyaka_forest", "Participants":["@jayadratha","@draupadi","@bhima","@arjuna","@yudhishthira"],
         "Outcome":"Jayadratha defeated and shamed",
         "Consequences":["Jayadratha performs penance to Shiva","Gets boon to hold 4 Pandavas (except Arjuna)"]},

        {"Order":29, "Year":-4, "Era":"Exile",
         "Event_Name":"Bhima Meets Hanuman",
         "Description":"While searching for Saugandhika lotus for Draupadi, Bhima meets his brother Hanuman in Gandhamadana.",
         "Location":"@gandhamadana", "Participants":["@bhima","@hanuman"],
         "Outcome":"Hanuman blesses Bhima and promises to be on Arjuna's flag",
         "Consequences":["Hanuman present on Arjuna's chariot banner in war"]},

        {"Order":30, "Year":-3, "Era":"Exile",
         "Event_Name":"Nala-Damayanti Story",
         "Description":"Sage Brihadarva narrates story of Nala and Damayanti to comfort Yudhishthira during exile.",
         "Location":"@kamyaka_forest", "Participants":["@yudhishthira","@nala","@damayanti"],
         "Outcome":"Yudhishthira consoled"},

        {"Order":31, "Year":-2, "Era":"Exile",
         "Event_Name":"Duryodhana Captured by Gandharvas",
         "Description":"Duryodhana goes to forest to mock Pandavas; captured by Gandharva Chitrasena. Pandavas rescue him.",
         "Location":"@dvaitavana", "Participants":["@duryodhana","@chitrasena_gandharva","@arjuna","@yudhishthira"],
         "Outcome":"Duryodhana rescued by Pandavas",
         "Consequences":["Duryodhana humiliated","Deepens his hatred"]},

        {"Order":32, "Year":-1, "Era":"Exile",
         "Event_Name":"Incognito Year at Virata",
         "Description":"Pandavas live incognito in King Virata's court: Yudhishthira as Brahmin Kanka, Bhima as cook Ballava, Arjuna as eunuch Brihannala, Nakula as horse-keeper, Sahadeva as cowherd, Draupadi as Sairandhri.",
         "Location":"@viratanagara", "Participants":["@yudhishthira","@bhima","@arjuna","@nakula","@sahadeva","@draupadi","@virata"],
         "Outcome":"Pandavas complete 13th year without detection"},

        {"Order":33, "Year":-1, "Era":"Exile",
         "Event_Name":"Kichaka Killed by Bhima",
         "Description":"Kichaka, Virata's commander, harasses Draupadi. Bhima kills him secretly.",
         "Location":"@viratanagara", "Participants":["@bhima","@draupadi"],
         "Outcome":"Kichaka killed",
         "Consequences":["Suspicion arises that Pandavas are hidden in Virata"]},

        {"Order":34, "Year":-1, "Era":"Exile",
         "Event_Name":"Uttara Gograhana - Arjuna Reveals Identity",
         "Description":"Kauravas attack Virata to steal cattle and expose Pandavas. Arjuna (as Brihannala) single-handedly defeats entire Kaurava army.",
         "Location":"@viratanagara", "Participants":["@arjuna","@duryodhana","@bhishma","@drona","@karna"],
         "Outcome":"Pandavas revealed; incognito period completed",
         "Consequences":["Abhimanyu married to Uttaraa","War preparations begin"]},

        # ─── Pre-War Diplomacy ───
        {"Order":35, "Year":-1, "Era":"Pre-War",
         "Event_Name":"Krishna's Peace Mission",
         "Description":"Krishna goes as peace ambassador to Hastinapura. Shows Vishvarupa. Duryodhana refuses to give even 5 villages.",
         "Location":"@hastinapura", "Participants":["@krishna","@duryodhana","@dhritarashtra","@gandhari","@vidura","@karna","@bhishma"],
         "Outcome":"Peace negotiations fail completely",
         "Consequences":["War becomes certain","Krishna reveals divine form","Karna learns his true identity from Kunti"]},

        {"Order":36, "Year":-1, "Era":"Pre-War",
         "Event_Name":"Karna Rejects Kunti's Appeal",
         "Description":"Kunti reveals to Karna that he is her firstborn. Asks him to join Pandavas. Karna refuses but promises he will not kill any Pandava except Arjuna.",
         "Location":"@hastinapura", "Participants":["@karna","@kunti"],
         "Outcome":"Karna remains loyal to Duryodhana",
         "Consequences":["Karna promises Kunti she will still have 5 sons after war"]},

        {"Order":37, "Year":0, "Era":"Pre-War",
         "Event_Name":"Bhagavad Gita",
         "Description":"On the battlefield, Arjuna refuses to fight seeing kinsmen. Krishna delivers the Bhagavad Gita - discourse on duty, dharma, and paths to liberation.",
         "Location":"@kurukshetra", "Participants":["@krishna","@arjuna"],
         "Outcome":"Arjuna resolves to fight",
         "Consequences":["Most sacred text of Hinduism delivered","War begins"]},

        # ─── War Era (18 days) ───
        {"Order":38, "Year":0, "Era":"War",
         "Event_Name":"War Day 1 - War Begins",
         "Description":"Kurukshetra War begins. Bhishma is Kaurava commander. Pandava army led by Dhrishtadyumna.",
         "Location":"@kurukshetra", "Participants":["@bhishma","@dhrishtadyumna","@arjuna","@duryodhana"],
         "Outcome":"First day of battle",
         "Consequences":["Massive casualties on both sides"]},

        {"Order":39, "Year":0, "Era":"War",
         "Event_Name":"War Day 10 - Fall of Bhishma",
         "Description":"Arjuna uses Shikhandi as shield. Bhishma refuses to fight Shikhandi (former Amba). Arjuna pierces Bhishma with arrows. Bhishma falls on bed of arrows.",
         "Location":"@kurukshetra", "Participants":["@bhishma","@arjuna","@shikhandi","@duryodhana"],
         "Outcome":"Bhishma falls; lies on bed of arrows awaiting Uttarayana",
         "Consequences":["Drona becomes next Kaurava commander"]},

        {"Order":40, "Year":0, "Era":"War",
         "Event_Name":"War Day 13 - Death of Abhimanyu",
         "Description":"Abhimanyu enters Chakravyuha but cannot exit. Jayadratha blocks other Pandavas. Seven warriors kill Abhimanyu treacherously.",
         "Location":"@kurukshetra", "Participants":["@abhimanyu","@jayadratha","@drona","@karna","@duhshasana","@duryodhana"],
         "Outcome":"Abhimanyu killed",
         "Consequences":["Arjuna vows to kill Jayadratha before next sunset or self-immolate"]},

        {"Order":41, "Year":0, "Era":"War",
         "Event_Name":"War Day 14 - Arjuna Kills Jayadratha",
         "Description":"Arjuna fights through entire Kaurava army. Krishna creates artificial sunset. Jayadratha emerges; Krishna reveals sun. Arjuna beheads Jayadratha.",
         "Location":"@kurukshetra", "Participants":["@arjuna","@krishna","@jayadratha"],
         "Outcome":"Jayadratha killed; Arjuna's vow fulfilled",
         "Consequences":["Ghatotkacha fights night battle"]},

        {"Order":42, "Year":0, "Era":"War",
         "Event_Name":"War Day 14 Night - Death of Ghatotkacha",
         "Description":"Ghatotkacha wreaks havoc on Kaurava army at night using powers. Karna uses Shakti weapon (meant for Arjuna) to kill Ghatotkacha.",
         "Location":"@kurukshetra", "Participants":["@ghatotkacha","@karna"],
         "Outcome":"Ghatotkacha killed by Shakti weapon",
         "Consequences":["Karna loses his one-use weapon meant for Arjuna","Krishna rejoices"]},

        {"Order":43, "Year":0, "Era":"War",
         "Event_Name":"War Day 15 - Death of Drona",
         "Description":"Ashvatthama elephant killed. Yudhishthira says 'Ashvatthama is dead' (the elephant). Drona lays down arms in grief. Dhrishtadyumna beheads Drona.",
         "Location":"@kurukshetra", "Participants":["@drona","@dhrishtadyumna","@yudhishthira","@ashvatthama"],
         "Outcome":"Drona killed through deception",
         "Consequences":["Karna becomes next commander","Ashvatthama vows revenge"]},

        {"Order":44, "Year":0, "Era":"War",
         "Event_Name":"War Day 16 - Karna Becomes Commander",
         "Description":"Karna appointed Kaurava commander. Fierce battles continue.",
         "Location":"@kurukshetra", "Participants":["@karna","@duryodhana","@arjuna","@shalya"],
         "Outcome":"Karna leads Kaurava army",
         "Consequences":["Shalya appointed as Karna's charioteer to demoralize him"]},

        {"Order":45, "Year":0, "Era":"War",
         "Event_Name":"War Day 17 - Karna Kills Duhshasana... Karna Killed by Arjuna",
         "Description":"Karna and Arjuna duel. Karna's chariot wheel sinks. While trying to lift it, Arjuna kills Karna on Krishna's urging. Earlier, Bhima kills Duhshasana and drinks his blood.",
         "Location":"@kurukshetra", "Participants":["@karna","@arjuna","@krishna","@bhima","@duhshasana","@shalya"],
         "Outcome":"Karna killed; Duhshasana killed by Bhima",
         "Consequences":["Draupadi's vow partly fulfilled","Shalya becomes last commander"]},

        {"Order":46, "Year":0, "Era":"War",
         "Event_Name":"War Day 18 - Duryodhana Falls",
         "Description":"Shalya killed by Yudhishthira. Shakuni killed by Sahadeva. Duryodhana hides in lake. Called out; mace duel with Bhima. Bhima strikes below belt. Duryodhana falls.",
         "Location":"@kurukshetra", "Participants":["@duryodhana","@bhima","@shalya","@yudhishthira","@shakuni","@sahadeva","@balarama","@krishna"],
         "Outcome":"Duryodhana mortally wounded; war effectively ends",
         "Consequences":["Balarama furious at Bhima's foul blow","Ashvatthama plans night raid"]},

        # ─── Post-War Era ───
        {"Order":47, "Year":0, "Era":"Post-War",
         "Event_Name":"Sauptika - Night Massacre",
         "Description":"Ashvatthama, Kripacharya, and Kritavarma attack sleeping Pandava camp at night. Ashvatthama kills all Upapandavas (Draupadi's five sons) and Dhrishtadyumna.",
         "Location":"@kurukshetra", "Participants":["@ashvatthama","@kripa","@kritavarma","@dhrishtadyumna"],
         "Outcome":"Upapandavas, Dhrishtadyumna, and others killed in sleep",
         "Consequences":["Ashvatthama launches Brahmashira","Cursed by Krishna to wander 3000 years"]},

        {"Order":48, "Year":0, "Era":"Post-War",
         "Event_Name":"Ashvatthama's Brahmashira and Curse",
         "Description":"Ashvatthama launches Brahmashira astra at Pandavas. Arjuna counters. Vyasa intervenes. Ashvatthama redirects weapon at Uttaraa's womb. Krishna saves Parikshit. Ashvatthama cursed to wander 3000 years.",
         "Location":"@kurukshetra", "Participants":["@ashvatthama","@arjuna","@krishna","@vyasa"],
         "Outcome":"Ashvatthama stripped of gem; cursed by Krishna",
         "Consequences":["Parikshit saved in womb","Ashvatthama immortally cursed"]},

        {"Order":49, "Year":0, "Era":"Post-War",
         "Event_Name":"Stri Parva - Lament of Women",
         "Description":"Women of both sides mourn the dead. Gandhari curses Krishna that Yadavas will destroy themselves. Dhritarashtra tries to crush Bhima (Krishna substitutes iron statue).",
         "Location":"@kurukshetra", "Participants":["@gandhari","@krishna","@dhritarashtra","@kunti","@draupadi"],
         "Outcome":"Gandhari's curse on Krishna accepted",
         "Consequences":["Yadava destruction foreshadowed"]},

        {"Order":50, "Year":0, "Era":"Post-War",
         "Event_Name":"Bhishma's Teachings (Shanti & Anushashana Parva)",
         "Description":"Bhishma, lying on bed of arrows, teaches Yudhishthira about dharma, governance, and philosophy over many days.",
         "Location":"@kurukshetra", "Participants":["@bhishma","@yudhishthira","@krishna"],
         "Outcome":"Comprehensive teachings on kingship and dharma delivered"},

        {"Order":51, "Year":0, "Era":"Post-War",
         "Event_Name":"Death of Bhishma",
         "Description":"On Uttarayana (sun's northward journey), Bhishma gives up his life. Body cremated on the banks of Ganga.",
         "Location":"@kurukshetra", "Participants":["@bhishma","@yudhishthira","@krishna"],
         "Outcome":"Bhishma dies on chosen day"},

        {"Order":52, "Year":1, "Era":"Post-War",
         "Event_Name":"Yudhishthira Crowned King",
         "Description":"Yudhishthira crowned king of Hastinapura. Rules with dharma.",
         "Location":"@hastinapura", "Participants":["@yudhishthira","@krishna","@bhima","@arjuna","@vidura","@dhritarashtra"],
         "Outcome":"Pandavas rule Hastinapura"},

        {"Order":53, "Year":2, "Era":"Post-War",
         "Event_Name":"Ashvamedha Yajna",
         "Description":"Yudhishthira performs Ashvamedha (horse sacrifice) to establish sovereignty. Arjuna follows the horse and fights various kings including his son Babhruvahana.",
         "Location":"@hastinapura", "Participants":["@yudhishthira","@arjuna","@babhruvahana"],
         "Outcome":"Ashvamedha completed successfully"},

        {"Order":54, "Year":15, "Era":"Post-War",
         "Event_Name":"Dhritarashtra, Gandhari, Kunti Retire to Forest",
         "Description":"After 15 years of Pandava rule, Dhritarashtra, Gandhari, Kunti, Vidura, and Sanjaya retire to forest.",
         "Location":"@hastinapura", "Participants":["@dhritarashtra","@gandhari","@kunti","@vidura","@sanjaya"],
         "Outcome":"Elders leave for forest life"},

        {"Order":55, "Year":18, "Era":"Post-War",
         "Event_Name":"Death of Dhritarashtra, Gandhari, Kunti",
         "Description":"Forest fire kills Dhritarashtra, Gandhari, and Kunti. Sanjaya survives.",
         "Participants":["@dhritarashtra","@gandhari","@kunti","@sanjaya"],
         "Outcome":"Three elders perish in forest fire"},

        {"Order":56, "Year":36, "Era":"Post-War",
         "Event_Name":"Mausala Parva - Destruction of Yadavas",
         "Description":"Gandhari's curse fulfilled. Yadavas fight among themselves with iron pestles grown from eraka grass. Krishna's sons, Pradyumna, Samba die. Balarama dies. Krishna shot by hunter Jara.",
         "Location":"@dvaraka", "Participants":["@krishna","@balarama","@pradyumna","@samba"],
         "Outcome":"Yadava dynasty destroyed; Krishna dies; Dvaraka sinks into sea",
         "Consequences":["Arjuna fails to protect Yadava women","Pandavas decide to renounce"]},

        {"Order":57, "Year":36, "Era":"Post-War",
         "Event_Name":"Mahaprasthanika - Great Journey",
         "Description":"Pandavas renounce kingdom, crown Parikshit. Walk towards Himalayas. One by one, Draupadi, Sahadeva, Nakula, Arjuna, Bhima fall. Only Yudhishthira reaches summit with a dog (Yama in disguise).",
         "Location":"@himalayas", "Participants":["@yudhishthira","@bhima","@arjuna","@nakula","@sahadeva","@draupadi"],
         "Outcome":"All Pandavas except Yudhishthira fall on the journey",
         "Consequences":["Yudhishthira tested by Yama"]},

        {"Order":58, "Year":36, "Era":"Post-War",
         "Event_Name":"Svargarohanika - Ascent to Heaven",
         "Description":"Yudhishthira reaches heaven. Sees Duryodhana in heaven, Pandavas in hell (illusion). After test, all united in Svarga.",
         "Location":"@svarga", "Participants":["@yudhishthira","@indra","@yama"],
         "Outcome":"Yudhishthira passes final test; all heroes united in heaven",
         "Consequences":["Epic concludes"]},
    ]

    # Build timeline output
    tl_output = {}
    for evt in timeline:
        evt_id = f"evt_{evt['Order']:03d}"
        entry = {
            "Order": evt["Order"],
            "Year": evt["Year"],
            "Era": evt["Era"],
            "Event_Name": evt["Event_Name"],
            "Description": evt["Description"],
        }
        if evt.get("Location"):
            entry["Location"] = evt["Location"]
        if evt.get("Participants"):
            entry["Participants"] = evt["Participants"]
        if evt.get("Outcome"):
            entry["Outcome"] = evt["Outcome"]
        if evt.get("Consequences"):
            entry["Consequences"] = evt["Consequences"]
        if evt.get("Related_Events"):
            entry["Related_Events"] = evt["Related_Events"]
        if evt.get("Sources"):
            entry["Sources"] = evt["Sources"]
        tl_output[f"@{evt_id}"] = entry

    tl_path = os.path.join(json_dir, 'timeline.json')
    with open(tl_path, 'w', encoding='utf-8') as f:
        json.dump(tl_output, f, ensure_ascii=False, indent=2)
    print(f"\n  TIMELINE: {len(tl_output)} events saved to timeline.json")
    era_counts = {}
    for v in tl_output.values():
        e = v['Era']
        era_counts[e] = era_counts.get(e, 0) + 1
    for e, c in sorted(era_counts.items()):
        print(f"    {e}: {c}")

    # ── Phase 7: Cross-linking ──────────────────────────────────
    # Add Events_Occurred to locations from timeline
    for evt_key, evt in tl_output.items():
        loc_ref = evt.get("Location", "")
        if loc_ref.startswith("@"):
            loc_id = loc_ref[1:]  # remove @
            if f"@{loc_id}" in loc_output:
                loc_entry = loc_output[f"@{loc_id}"]
                if "Events_Occurred" not in loc_entry:
                    loc_entry["Events_Occurred"] = []
                loc_entry["Events_Occurred"].append({"Event": evt_key})

    # Re-save locations with events
    with open(loc_path, 'w', encoding='utf-8') as f:
        json.dump(loc_output, f, ensure_ascii=False, indent=2)

    # Add Major_Events to characters from timeline
    char_events = {}  # char_key -> [evt_keys]
    for evt_key, evt in tl_output.items():
        for p in evt.get("Participants", []):
            if p.startswith("@"):
                ck = p[1:]
                char_events.setdefault(ck, []).append(evt_key)

    for char_key, evt_keys in char_events.items():
        full_key = f"@{char_key}"
        if full_key in output:
            output[full_key]["Major_Events"] = evt_keys

    # Re-save characters with events
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # ── Phase 8: Validation ─────────────────────────────────────
    print("\n  VALIDATION:")
    errors = 0
    # Check character refs in timeline
    for evt_key, evt in tl_output.items():
        for p in evt.get("Participants", []):
            if p.startswith("@") and p not in output:
                print(f"    WARNING: Timeline {evt_key} references unknown character {p}")
                errors += 1
        loc = evt.get("Location", "")
        if loc.startswith("@") and loc not in loc_output:
            print(f"    WARNING: Timeline {evt_key} references unknown location {loc}")
            errors += 1

    # Check location refs in characters
    for ck, cv in output.items():
        kingdom = cv.get("Kingdom", "")
        if kingdom.startswith("@") and kingdom not in loc_output:
            print(f"    WARNING: Character {ck} Kingdom references unknown location {kingdom}")
            errors += 1
        for loc in cv.get("Important_Locations", []):
            if loc.startswith("@") and loc not in loc_output:
                print(f"    WARNING: Character {ck} Important_Locations references unknown location {loc}")
                errors += 1

    # Check location cross-refs
    for lk, lv in loc_output.items():
        ruler = lv.get("Ruler", "")
        if ruler.startswith("@") and ruler not in output:
            print(f"    WARNING: Location {lk} Ruler references unknown character {ruler}")
            errors += 1
        for r in lv.get("Residents", []):
            if r.startswith("@") and r not in output:
                print(f"    WARNING: Location {lk} Residents references unknown character {r}")
                errors += 1

    # Timeline order validation
    orders = [v['Order'] for v in tl_output.values()]
    if orders != list(range(1, len(orders) + 1)):
        print(f"    WARNING: Timeline order is not continuous 1..{len(orders)}")
        errors += 1
    years = [v['Year'] for v in tl_output.values()]
    for i in range(1, len(years)):
        if years[i] < years[i-1]:
            print(f"    WARNING: Timeline year goes backward at Order {i+1}: {years[i-1]} -> {years[i]}")
            errors += 1

    if errors == 0:
        print("    All cross-references valid!")
    else:
        print(f"    {errors} validation warnings found")

    print(f"\n  SUMMARY:")
    print(f"    characters.json: {len(output)} characters")
    print(f"    locations.json:  {len(loc_output)} locations")
    print(f"    timeline.json:   {len(tl_output)} events")

if __name__ == '__main__':
    # Resolve project root from script location: pipeline/ -> project root
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

    # Fixed paths — this script is specific to this PDF
    PDF_NAME = 'The Mahabharata Set of 10 Volumes.pdf'
    pdf_path = os.path.join(PROJECT_ROOT, 'input', PDF_NAME)
    volumes_dir = os.path.join(PROJECT_ROOT, 'output', 'volumes')
    json_dir = os.path.join(PROJECT_ROOT, 'output', 'json')

    if not os.path.isfile(pdf_path):
        print(f"Error: PDF not found at: {pdf_path}")
        print(f"Place '{PDF_NAME}' in the input/ folder.")
        sys.exit(1)

    os.makedirs(volumes_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)

    print(f"Project root : {PROJECT_ROOT}")
    print(f"PDF input    : {pdf_path}")
    print(f"Volumes dir  : {volumes_dir}")
    print(f"JSON dir     : {json_dir}")

    step1_extract(pdf_path, volumes_dir)
    step1b_manual_fixes(volumes_dir)
    step2_add_sections(volumes_dir)
    ok = step3_verify(volumes_dir)
    step4_characters(volumes_dir, json_dir)

    print("\n" + "=" * 60)
    if ok:
        print("ALL DONE - 100% footnote matching across all volumes")
    else:
        print("DONE - some footnote mismatches detected (check above)")
    print(f"Output: {json_dir}")
    print("=" * 60)
