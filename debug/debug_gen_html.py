#!/usr/bin/env python3
"""Generate HTML files with dialog highlighting from volume chapter text files."""

import os, re, html as html_mod

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL_DIR = os.path.join(BASE, 'output', 'volumes')
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html')
os.makedirs(OUT_DIR, exist_ok=True)

# Same 4 colors from TheMahabharata ReadingView.tsx
QUOTE_COLORS = ["#8ec8d8", "#e8c87a", "#b8d98a", "#d7a6ff"]

STYLE = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;width:100%}
body{font-family:Georgia,serif;margin:0;padding:30px 5vw;
line-height:1.9;color:#d4d0c8;background:#1a1a1a;font-size:1.1rem}
h1{color:#e8c87a;border-bottom:2px solid #e8c87a;padding-bottom:10px;margin-bottom:20px}
h2{color:#c8a96e;margin-top:50px;margin-bottom:10px;border-left:4px solid #c8a96e;padding-left:12px}
p{text-align:justify;margin:14px 0}
a{color:#e8c87a;text-decoration:none}a:hover{text-decoration:underline}
.nav{background:#2a2520;padding:12px 20px;border-radius:6px;margin:20px 0;
position:sticky;top:0;z-index:10;border:1px solid #3a342a}
.nav a{margin-right:18px;font-weight:600}
.idx-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;margin:24px 0}
.idx-card{background:#252220;border:1px solid #3a342a;border-radius:8px;padding:20px;
display:block;transition:box-shadow .2s}
.idx-card:hover{box-shadow:0 4px 16px rgba(0,0,0,0.4)}
.idx-card h3{margin:0 0 6px;color:#e8c87a}
.idx-card span{color:#888;font-size:0.9em}
.legend{background:#252220;border:1px solid #3a342a;border-radius:6px;
padding:10px 14px;margin:14px 0;font-size:0.85em;color:#aaa}
.legend .sw{display:inline-block;width:10px;height:10px;border-radius:2px;
margin:0 4px 0 12px;vertical-align:middle}
"""

# ─── Quote detection (ported from ReadingView.tsx) ───────────────────
OQ_S = '\u2018'  # '
CQ_S = '\u2019'  # '
OQ_D = '\u201C'  # "
CQ_D = '\u201D'  # "

def _is_apostrophe(text, i):
    prev = text[i-1] if i > 0 else ''
    nxt = text[i+1] if i+1 < len(text) else ''
    # don't, Krishna's, can't — letter on both sides
    if prev.isalpha() and nxt.isalpha():
        return True
    # Plural possessive: "Pandavas' fame", "sons' wealth" — ends with s'
    # followed by whitespace/punctuation.
    # BUT NOT a closing quote like 'alms' or 'this' — check for nearby
    # unmatched opening single quote within ~50 chars.
    if prev == 's' and not nxt.isalpha():
        prev2 = text[i-2] if i > 1 else ''
        if prev2.isalpha():
            # Scan backward up to 50 chars for an unmatched opening '
            depth = 0
            for j in range(i - 1, max(0, i - 50) - 1, -1):
                ch = text[j]
                if ch == CQ_S:
                    depth += 1  # another close consumes an open
                elif ch == OQ_S:
                    if depth > 0:
                        depth -= 1
                    else:
                        # Unmatched open found nearby → this is a closing quote
                        return False
            return True
    return False

def _is_para_leading(text, i):
    c = i - 1
    while c >= 0:
        ch = text[c]
        if ch in (' ', '\t', '\r'):
            c -= 1; continue
        if ch == '\n':
            return True
        if ch in (OQ_S, OQ_D, CQ_S, CQ_D):
            c -= 1; continue
        return False
    return True

def merge_continuation_lines(chapter_text):
    """Merge lines that are inside an open quote into one paragraph."""
    lines = chapter_text.split('\n')
    merged = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if merged:
            prev = merged[-1]
            # Count net open quotes in all merged text so far
            net_single = prev.count(OQ_S) - prev.count(CQ_S)
            net_double = prev.count(OQ_D) - prev.count(CQ_D)
            # Adjust for apostrophes in close-single count
            for i, ch in enumerate(prev):
                if ch == CQ_S and _is_apostrophe(prev, i):
                    net_single += 1  # undo the close count
            if net_single > 0 or net_double > 0:
                # Inside an open quote — merge with previous
                merged[-1] = prev + ' ' + stripped
                continue
        merged.append(stripped)
    return '\n'.join(merged)

def compute_depths(text):
    """Return list d where d[i] = quote-nesting depth effective at character i.

    Stack-based: every open smart-quote (single or double) pushes, every real
    close pops. Apostrophes (e.g. don't, Krishna's) do NOT pop. Paragraph-leading
    continuation opens (when a quote of the same kind is already open on the
    stack and the mark sits at the start of a paragraph) do NOT push.

    - Opening-quote chars receive the NEW (post-push) depth, so they appear
      inside the quoted span.
    - Closing-quote chars receive the depth BEFORE the pop, so the closing
      mark is still part of the quoted span.
    - Depth 0 means narration outside every quote → rendered with default
      body color (no <span>).
    """
    n = len(text)
    d = [0] * n
    stack = []  # list of 'single' | 'double'
    for i, ch in enumerate(text):
        if ch == OQ_S:
            if any(k == 'single' for k in stack) and _is_para_leading(text, i):
                d[i] = len(stack)  # continuation marker — ignore
                continue
            stack.append('single')
            d[i] = len(stack)
        elif ch == OQ_D:
            if any(k == 'double' for k in stack) and _is_para_leading(text, i):
                d[i] = len(stack)
                continue
            stack.append('double')
            d[i] = len(stack)
        elif ch == CQ_S:
            if _is_apostrophe(text, i):
                d[i] = len(stack)
                continue
            # Safety: if no matching open single on the stack, treat as apostrophe
            if not any(k == 'single' for k in stack):
                d[i] = len(stack)
                continue
            d[i] = len(stack)  # still inside
            for j in range(len(stack) - 1, -1, -1):
                if stack[j] == 'single':
                    stack.pop(j)
                    break
        elif ch == CQ_D:
            d[i] = len(stack)
            for j in range(len(stack) - 1, -1, -1):
                if stack[j] == 'double':
                    stack.pop(j)
                    break
        else:
            d[i] = len(stack)
    return d


def colorize_chapter(chapter_text):
    """Render a chapter as HTML with per-quote-nesting-level colors.

    - Depth 0 (outside all quotes) = default narration color (no span).
    - Depth 1..N (inside quotes) = QUOTE_COLORS[(depth-1) % 4].

    Works for arbitrary nesting of single and double smart quotes.
    """
    chapter_text = merge_continuation_lines(chapter_text)
    if not chapter_text:
        return ''
    depths = compute_depths(chapter_text)

    out = []
    offset = 0
    for para in chapter_text.split('\n'):
        ps = offset
        pe = offset + len(para)
        offset = pe + 1  # +1 for newline

        # strip leading/trailing whitespace from the paragraph
        s = 0
        while s < len(para) and para[s].isspace():
            s += 1
        e = len(para)
        while e > s and para[e - 1].isspace():
            e -= 1
        if s == e:
            continue

        # Group adjacent chars with same depth into runs
        parts = []
        cur_depth = depths[ps + s]
        buf_start = s
        for i in range(s + 1, e):
            di = depths[ps + i]
            if di != cur_depth:
                parts.append((cur_depth, para[buf_start:i]))
                buf_start = i
                cur_depth = di
        parts.append((cur_depth, para[buf_start:e]))

        html_parts = []
        for depth, txt in parts:
            esc = html_mod.escape(txt)
            if depth == 0:
                html_parts.append(esc)
            else:
                color = QUOTE_COLORS[(depth - 1) % len(QUOTE_COLORS)]
                html_parts.append(f'<span style="color:{color}">{esc}</span>')
        out.append(f'<p>{"".join(html_parts)}</p>')

    return '\n'.join(out) + '\n'

VOLUMES = {
    1: "Adi Parva", 2: "Sabha Parva", 3: "Vana Parva",
    4: "Virata & Udyoga Parva", 5: "Bhishma Parva",
    6: "Drona Parva", 7: "Karna & Shalya Parva",
    8: "Shanti Parva", 9: "Anushasana Parva",
    10: "Ashvamedhika to Svargarohana Parva"
}

def make_page(title, body, nav=''):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html_mod.escape(title)}</title><style>{STYLE}</style></head>
<body>{nav}{body}</body></html>"""

# Build volume pages
index_cards = []
for v in range(1, 11):
    text = open(os.path.join(VOL_DIR, f'volume_{v}_chapters.txt'), encoding='utf-8').read()
    parts = re.split(r'--- Chapter (\d+)(?:\(\d+\))? ---', text)
    name = VOLUMES[v]
    body = f'<h1>Volume {v}: {html_mod.escape(name)}</h1>\n'
    ch_count = 0
    for i in range(1, len(parts), 2):
        ch_num = parts[i]
        content = parts[i+1] if i+1 < len(parts) else ''
        body += f'<h2 id="ch{ch_num}">Chapter {ch_num}</h2>\n'
        body += colorize_chapter(content)
        ch_count += 1

    nav = f'<div class="nav"><a href="index.html">&larr; Index</a>'
    if v > 1: nav += f' <a href="volume_{v-1}.html">&laquo; Prev</a>'
    if v < 10: nav += f' <a href="volume_{v+1}.html">Next &raquo;</a>'
    nav += '</div>'
    legend = (
        '<div class="legend">Narration (default) &nbsp;·&nbsp; '
        f'<span class="sw" style="background:{QUOTE_COLORS[0]}"></span>Quote level 1 '
        f'<span class="sw" style="background:{QUOTE_COLORS[1]}"></span>level 2 '
        f'<span class="sw" style="background:{QUOTE_COLORS[2]}"></span>level 3 '
        f'<span class="sw" style="background:{QUOTE_COLORS[3]}"></span>level 4+'
        '</div>'
    )
    nav += legend

    fname = f'volume_{v}.html'
    with open(os.path.join(OUT_DIR, fname), 'w', encoding='utf-8') as f:
        f.write(make_page(f'Vol {v}: {name}', body, nav))
    print(f'  {fname}: {ch_count} chapters')
    index_cards.append((v, name, ch_count, fname))

# Build index
body = '<h1>The Mahabharata</h1>\n<p>Bibek Debroy translation &mdash; 10 Volumes</p>\n'
body += '<div class="idx-grid">\n'
for v, name, ch_count, fname in index_cards:
    body += f'<a href="{fname}" class="idx-card"><h3>Volume {v}</h3>{html_mod.escape(name)}<br><span>{ch_count} chapters</span></a>\n'
body += '</div>'
with open(os.path.join(OUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(make_page('The Mahabharata', body))
print('  index.html')
print('Done.')
