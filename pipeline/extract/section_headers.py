"""Add section/chapter headers to extracted footnote files.
Maps footnote definition runs back to their source chapters."""

import os
import re

from pipeline.config import NUM_VOLUMES


def step2_add_sections(base_dir):
    """Add --- Section N --- and --- Chapters X to Y --- headers to footnotes."""
    print("\n" + "=" * 60)
    print("STEP 2: Adding section headers to footnotes")
    print("=" * 60)

    for v in range(1, NUM_VOLUMES + 1):
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
