"""Manual fixes for known OCR errors in extracted text.
These are specific to 'The Mahabharata Set of 10 Volumes.pdf'
and fix edge cases that break footnote matching."""

import os


# Each fix: (volume, file_type, old_text, new_text, description)
OCR_FIXES = [
    (10, 'footnotes',
     "275 Each brahmana.\n275 There is a typo",
     "275 Each brahmana.\n276 There is a typo",
     "duplicate 275 -> 276"),

    (10, 'footnotes',
     '15 Described in Section 60 (Volume 5). l6For the princesses of Kashi, Amba, Ambika and Ambalika. This has been described in Sec- tion 60.',
     '15 Described in Section 60 (Volume 5).\n16 For the princesses of Kashi, Amba, Ambika and Ambalika. This has been described in Section 60.',
     "split l6 -> 16, fix Sec- tion -> Section"),

    (5, 'footnotes',
     "quotation marks. 13\u2018Khatakhata\u2019",
     "quotation marks.\n13 \u2018Khatakhata\u2019",
     "split def 12/13"),

    # Alternative with ASCII apostrophes
    (5, 'footnotes',
     "quotation marks. 13'Khatakhata'",
     "quotation marks.\n13 'Khatakhata'",
     "split def 12/13 (ASCII variant)"),
]


def step1b_manual_fixes(base_dir):
    """Apply known manual fixes for OCR edge cases."""
    print("\n" + "=" * 60)
    print("STEP 1B: Applying manual fixes")
    print("=" * 60)

    fixes = 0

    # Group fixes by (volume, file_type)
    fix_groups = {}
    for vol, ftype, old, new, desc in OCR_FIXES:
        fix_groups.setdefault((vol, ftype), []).append((old, new, desc))

    for (vol, ftype), group in fix_groups.items():
        path = os.path.join(base_dir, f'volume_{vol}_{ftype}.txt')
        text = open(path, encoding='utf-8').read()
        changed = False

        for old, new, desc in group:
            if old in text:
                text = text.replace(old, new)
                changed = True
                fixes += 1
                print(f"  Vol {vol} {ftype}: {desc}")

        if changed:
            open(path, 'w', encoding='utf-8').write(text)

    print(f"  Applied {fixes} fixes")


def normalize_plural_possessives(base_dir):
    """Replace plural-possessive \u2019 with plain apostrophe (') in chapter files.

    Patterns like Pandavas\u2019 fame, sisters\u2019 sons, lions\u2019 are
    plural possessives where the right-single-quote should NOT be treated as
    a closing dialog quote.  Replacing with U+0027 makes them invisible to
    smart-quote-based dialog detection.

    To avoid false positives (e.g. 'alms\u2019 which is a real closing
    quote), we scan backward up to 50 chars for an unmatched opening
    \u2018.  If one is found, the mark is a closing quote and is kept.
    """
    print("\n" + "=" * 60)
    print("STEP 1C: Normalizing plural possessive apostrophes")
    print("=" * 60)

    OQ_S = '\u2018'
    CQ_S = '\u2019'
    total = 0

    for vol in range(1, 11):
        path = os.path.join(base_dir, f'volume_{vol}_chapters.txt')
        if not os.path.exists(path):
            continue
        text = open(path, encoding='utf-8').read()
        chars = list(text)
        fixes = 0

        for i, ch in enumerate(chars):
            if ch != CQ_S:
                continue
            prev = chars[i - 1] if i > 0 else ''
            nxt = chars[i + 1] if i + 1 < len(chars) else ''

            # Only target: alpha + s + \u2019 + non-alpha
            if prev != 's' or nxt.isalpha():
                continue
            prev2 = chars[i - 2] if i > 1 else ''
            if not prev2.isalpha():
                continue

            # Scan backward up to 50 chars for an unmatched opening '
            is_closing = False
            depth = 0
            for j in range(i - 1, max(0, i - 50) - 1, -1):
                c = chars[j]
                if c == CQ_S:
                    depth += 1
                elif c == OQ_S:
                    if depth > 0:
                        depth -= 1
                    else:
                        is_closing = True
                        break

            if not is_closing:
                chars[i] = "'"   # plain apostrophe U+0027
                fixes += 1

        if fixes > 0:
            open(path, 'w', encoding='utf-8').write(''.join(chars))
        print(f"  Vol {vol}: {fixes} plural possessives normalized")
        total += fixes

    print(f"  Total: {total} plural possessives normalized")
