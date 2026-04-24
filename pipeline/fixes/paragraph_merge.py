"""Merge broken paragraph lines in chapter text files.

OCR page-breaks sometimes split a paragraph mid-sentence across two lines.
This step detects lines where a smart-quote is still open at the end and
the next line continues with plain text (not re-opening a quote), then
merges them into a single paragraph.

Runs after OCR fixes (step 1b) and before section header enrichment (step 2).
"""

import os
import re

from pipeline.config import NUM_VOLUMES

OQ_S = '\u2018'  # '
CQ_S = '\u2019'  # '
OQ_D = '\u201C'  # "
CQ_D = '\u201D'  # "
QUOTE_CHARS = {OQ_S, CQ_S, OQ_D, CQ_D}
CHAP_RE = re.compile(r'^--- Chapter .+ ---$')


def _is_apostrophe(text, i):
    prev = text[i - 1] if i > 0 else ''
    nxt = text[i + 1] if i + 1 < len(text) else ''
    return prev.isalpha() and nxt.isalpha()


def _has_recent_unclosed_quote(line, tail_chars=300):
    """Check if the line has unclosed quotes opened within the last `tail_chars`."""
    stack = []
    for i, ch in enumerate(line):
        if ch == OQ_S:
            stack.append(('s', i))
        elif ch == CQ_S:
            if not _is_apostrophe(line, i):
                for j in range(len(stack) - 1, -1, -1):
                    if stack[j][0] == 's':
                        stack.pop(j)
                        break
        elif ch == OQ_D:
            stack.append(('d', i))
        elif ch == CQ_D:
            for j in range(len(stack) - 1, -1, -1):
                if stack[j][0] == 'd':
                    stack.pop(j)
                    break

    if not stack:
        return False

    threshold = len(line) - tail_chars
    return any(pos >= threshold for _, pos in stack)


def _merge_chapter_breaks(text):
    """Merge continuation lines in a volume text file. Returns (fixed_text, merge_count)."""
    raw_lines = text.split('\n')
    result_lines = []
    merge_count = 0

    cur_para = None
    cur_has_recent = False

    def flush_para():
        nonlocal cur_para, cur_has_recent
        if cur_para is not None:
            result_lines.append(cur_para)
            cur_para = None
            cur_has_recent = False

    for line in raw_lines:
        line = line.rstrip('\r')

        if CHAP_RE.match(line.strip()):
            flush_para()
            result_lines.append(line)
            continue

        if not line.strip():
            flush_para()
            result_lines.append(line)
            continue

        stripped = line.strip()
        starts_with_quote = stripped[0] in QUOTE_CHARS if stripped else False

        should_merge = (cur_para is not None
                        and cur_has_recent
                        and not starts_with_quote)

        if should_merge:
            cur_para = cur_para + ' ' + stripped
            cur_has_recent = _has_recent_unclosed_quote(cur_para)
            merge_count += 1
        else:
            flush_para()
            cur_para = stripped
            cur_has_recent = _has_recent_unclosed_quote(stripped)

    flush_para()
    return '\n'.join(result_lines), merge_count


def step1c_merge_paragraphs(volumes_dir):
    """Merge broken paragraph lines across all volume chapter files."""
    print("\n" + "=" * 60)
    print("STEP 1c: Merge broken paragraph lines")
    print("=" * 60)

    total = 0
    for vol in range(1, NUM_VOLUMES + 1):
        path = os.path.join(volumes_dir, f'volume_{vol}_chapters.txt')
        if not os.path.isfile(path):
            continue

        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()

        fixed, count = _merge_chapter_breaks(text)

        if count > 0:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(fixed)
            print(f"  Volume {vol:2d}: merged {count} broken paragraph(s)")
        else:
            print(f"  Volume {vol:2d}: OK")
        total += count

    print(f"  Total: {total} paragraph merges")
