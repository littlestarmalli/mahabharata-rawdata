import sys; sys.path.insert(0, '.')
from build_combined_chapters import get_toc_info, get_fn_section_ranges

fn_secs = get_fn_section_ranges(1)
toc_secs = get_toc_info(1)

print("=== First 8 TOC sections ===")
for s in toc_secs[:8]:
    main = repr(s['main_parva_hdr'][:50]) if s['main_parva_hdr'] else 'None'
    sub  = s['subparva_hdr'][:65]
    note = repr(s['note'][:60])
    print(f"  main={main}")
    print(f"  sub ={sub!r}")
    print(f"  note={note}")
    print()

print("=== ch_to_info (first 5 entries) ===")
import re
ch_to_info = {}
for sec in toc_secs:
    sub_hdr = sec['subparva_hdr']
    m = re.search(r'\[(\d+)\]', sub_hdr)
    if not m: continue
    gnum = int(m.group(1))
    fn_info = fn_secs.get(gnum)
    if fn_info and fn_info['ch_start'] is not None:
        ch_start = fn_info['ch_start']
    elif sec['toc_chapters']:
        ch_start = sec['toc_chapters'][0]
    else:
        continue
    ch_to_info[ch_start] = (sec['main_parva_hdr'], sub_hdr, sec['note'])

for ch_start in sorted(list(ch_to_info.keys()))[:10]:
    main_hdr, sub_hdr, note = ch_to_info[ch_start]
    main = repr(main_hdr[:40]) if main_hdr else 'None'
    print(f"  ch {ch_start}: main={main}, sub={sub_hdr[:50]!r}")
