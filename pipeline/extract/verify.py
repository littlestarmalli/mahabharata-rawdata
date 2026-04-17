"""Verify that every footnote reference {N} in chapter text
has a matching definition N in the footnote files."""

import os
import re

from pipeline.config import NUM_VOLUMES


def step3_verify(base_dir):
    """Verify all {N} refs in chapters match defs in footnotes."""
    print("\n" + "=" * 60)
    print("STEP 3: Verifying footnote matching")
    print("=" * 60)

    all_ok = True
    total_refs_all = 0
    total_matched_all = 0

    for v in range(1, NUM_VOLUMES + 1):
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
