"""Replace curly quotes with straight quotes for emphasis/term words (not dialog)."""
import re

# Each entry: (volume, line_number, quoted_text)
# These are words/terms being *mentioned*, not spoken dialog.
EMPHASIS = [
    # Confirmed emphasis/terms
    (1, 591, 'Bhoja{157}'),
    (3, 50, 'OM'),
    (3, 589, 'Nau-bandhana{65}'),
    (3, 594, 'bho'),
    (3, 594, 'arya{77}'),
    (3, 704, 'Great'),
    (4, 913, 'Jaya{314}'),
    (5, 282, 'A'),
    (8, 982, 'welfare'),
    (8, 1108, 'tvam{118}'),
    (9, 33, 'who'),
    (9, 33, 'I'),
    (9, 184, 'dead'),
    (9, 358, 'free'),
    (9, 512, 'Bho{1086}'),
    (9, 523, 'Om'),
    (9, 567, 'Hum'),
    (9, 590, 'Om'),  # two on same line
    (9, 603, 'Bho{1350}'),
    (9, 856, 'svadha'),
    (9, 856, 'Om'),
    (10, 714, 'I am'),
    # From unclear -> emphasis
    (1, 16, 'Jaya{1}'),
    (1, 1109, 'father'),
    (5, 137, 'khatakhata'),
    (5, 766, 'shame'),
    (7, 49, 'Array, yoke,'),
    (8, 292, 'Mama'),
    (8, 292, 'na mama'),
    (8, 968, 'thief'),  # two on same line
    (9, 512, 'Bho'),    # two more on V9:512
]

total = 0
for vol in range(1, 11):
    path = f'output/volumes/volume_{vol}_chapters.txt'
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    changed = 0
    targets = [(ln, txt) for v, ln, txt in EMPHASIS if v == vol]
    for ln, txt in targets:
        old = '\u2018' + txt + '\u2019'
        new = "'" + txt + "'"
        idx = ln - 1
        if old in lines[idx]:
            lines[idx] = lines[idx].replace(old, new, 1)
            changed += 1
        else:
            print(f'  WARNING: not found in V{vol}:{ln}: {old!r}')

    if changed:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f'V{vol}: {changed} replacements')
        total += changed

print(f'\nTotal: {total} curly-quote emphasis words replaced with straight quotes')
