import glob
import re as _re

# Volume 1 and 2 are manually edited — skip them in all dirs
SKIP_VOLUMES = {1, 2}

dirs = [
    'output/volumes',
    'text_to_volumes/output',
]

import re as _re

# Volume 1 and 2 are manually edited — skip them in all dirs
SKIP_VOLUMES = {1, 2}

for d in dirs:
    for path in sorted(glob.glob(f'{d}/*_chapters.txt')):
        m = _re.search(r'volume_(\d+)_chapters', path)
        if m and int(m.group(1)) in SKIP_VOLUMES:
            print(f'Skipped (manual) {path}')
            continue
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Remove empty lines
        lines = [l for l in lines if l.strip()]

        # Join lines starting with lowercase to the previous line
        result = []
        for line in lines:
            stripped = line.rstrip('\n')
            if result and stripped and stripped[0].islower():
                prev = result[-1].rstrip('\n')
                if prev.startswith('---'):
                    # Never merge onto a chapter header line
                    result.append(line)
                elif prev.endswith('-'):
                    # hyphenated word split — remove hyphen, join directly
                    result[-1] = prev[:-1] + stripped + '\n'
                elif prev and prev[-1].isalpha():
                    # mid-word split — join directly, no space
                    result[-1] = prev + stripped + '\n'
                else:
                    # continuation after punctuation — add space
                    result[-1] = prev + ' ' + stripped + '\n'
            else:
                result.append(line)

        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(result)
        print(f'Cleaned {path}: {len(lines)} -> {len(result)} lines')
