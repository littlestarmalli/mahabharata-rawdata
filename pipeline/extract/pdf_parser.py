"""PDF text extraction for the Mahabharata 10-volume PDF.
Handles chapter detection, footnote extraction, drop-caps, and multi-column layouts."""

import fitz
import re
import os

from pipeline.config import VOLUME_START_PAGES, NUM_VOLUMES


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

    for vol in range(1, NUM_VOLUMES + 1):
        start_page = VOLUME_START_PAGES[vol]
        end_page = VOLUME_START_PAGES[vol + 1] if vol < NUM_VOLUMES else total_pages

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
