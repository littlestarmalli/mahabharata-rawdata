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
