"""Generate dialog_viewer.html from output/dialogs/ JSON files.

Uses depth-based coloring:
  depth 0: author (grey)
  depth 1: ' frame — Vaishampayana / Souti (blue)
  depth 2: " frame — character dialog (green)
  depth 3+: ' nested speech (amber/orange/deeper)

Each paragraph is a <p> with background color based on depth.
Inline segments get <span> coloring for speech vs narration.
"""
import json, os, html

DIALOGS_DIR = 'output/dialogs'
OUTPUT_FILE = 'output/web/dialog_viewer.html'
INDEX_FILE  = 'output/json/index.json'

# Depth-based colors: (text_color, bg_color_at_40%)
DEPTH_COLORS = [
    ('#555555', 'rgba(85,85,85,0.08)'),      # 0: author/top-level
    ('#7EB8F7', 'rgba(126,184,247,0.12)'),    # 1: ' frame (Vaishampayana)
    ('#2D6A4F', 'rgba(45,106,79,0.10)'),      # 2: " frame (character narration)
    ('#E07A5F', 'rgba(224,122,95,0.12)'),      # 3: ' speech (character speaks)
    ('#6C5CE7', 'rgba(108,92,231,0.12)'),      # 4: " deeper speech
    ('#D62828', 'rgba(214,40,40,0.12)'),       # 5: ' even deeper
    ('#F77F00', 'rgba(247,127,0,0.12)'),       # 6+
]

def get_colors(depth):
    idx = min(depth, len(DEPTH_COLORS) - 1)
    return DEPTH_COLORS[idx]


def render_segment(seg):
    """Render a single segment as HTML."""
    t = html.escape(seg['text'])
    depth = seg.get('depth', 0)
    text_color, _ = get_colors(depth)

    if seg['type'] == 'speech':
        return f'<span style="color:{text_color};font-weight:500">{t}</span>'
    elif seg['type'] == 'narration':
        # narration is slightly muted
        return f'<span style="color:{text_color};opacity:0.75">{t}</span>'
    elif seg['type'] == 'close':
        return f'<span style="color:{text_color};opacity:0.5">{t}</span>'
    return t


def render_chapter(chapter_data):
    """Render a chapter as HTML paragraphs."""
    ch = chapter_data['chapter']
    local = chapter_data['local']
    shlokas = chapter_data.get('shlokas', 0)
    parts = []
    parts.append(f'<div class="chapter" id="ch-{ch}">')
    parts.append(f'<h3>Chapter {ch} (local {local}) [{shlokas} shlokas]</h3>')

    for para in chapter_data['paragraphs']:
        depth = para['depth']
        _, bg = get_colors(depth)
        indent = depth * 16

        segs_html = ''.join(render_segment(s) for s in para['segments'])

        parts.append(
            f'<p class="d{depth}" style="background:{bg};'
            f'border-left:{max(2, depth*3)}px solid {get_colors(depth)[0]};'
            f'padding:6px 10px 6px {indent + 10}px;'
            f'margin:2px 0">'
            f'{segs_html}</p>'
        )

    parts.append('</div>')
    return '\n'.join(parts)


def build_nav(volumes):
    """Build volume/chapter navigation sidebar."""
    nav = ['<div id="nav">']
    for vol_num, chapters in sorted(volumes.items()):
        nav.append(f'<div class="vol-group">')
        nav.append(f'<h4 onclick="toggleVol(this)">Volume {vol_num} ({len(chapters)} ch)</h4>')
        nav.append(f'<div class="ch-list" style="display:none">')
        for ch in chapters:
            nav.append(f'<a href="#ch-{ch}" onclick="loadChapter({vol_num},{ch})">{ch}</a>')
        nav.append('</div></div>')
    nav.append('</div>')
    return '\n'.join(nav)


def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Collect all volumes and chapters
    volumes = {}
    for vol in range(1, 11):
        vol_dir = os.path.join(DIALOGS_DIR, f'volume_{vol}')
        if not os.path.exists(vol_dir):
            continue
        chapters = []
        for fn in sorted(os.listdir(vol_dir)):
            if fn.endswith('.json'):
                with open(os.path.join(vol_dir, fn), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                chapters.append(data)
        volumes[vol] = chapters

    # Pre-render all chapters into JS data
    all_chapters = {}
    for vol_num, chapters in volumes.items():
        for ch_data in chapters:
            key = f'{vol_num}_{ch_data["chapter"]}'
            all_chapters[key] = render_chapter(ch_data)

    # Build the full HTML
    depth_legend_items = [
        ('#555555','rgba(85,85,85,0.08)','D0'), ('#8B7355','rgba(139,115,85,0.08)','D0b'),
        ('#7EB8F7','rgba(126,184,247,0.12)','D1'), ('#B088D4','rgba(176,136,212,0.12)','D1b'),
        ('#2D6A4F','rgba(45,106,79,0.10)','D2'), ('#8B6914','rgba(139,105,20,0.10)','D2b'),
        ('#E07A5F','rgba(224,122,95,0.12)','D3'), ('#C4785A','rgba(196,120,90,0.12)','D3b'),
    ]
    depth_legend = ''.join(
        f'<span class="legend-item" style="color:{c};background:{b};'
        f'padding:2px 8px;border-radius:3px;margin:0 2px">'
        f'{lbl}</span>'
        for c, b, lbl in depth_legend_items
    )

    # Build volume nav
    vol_nav = {}
    for vol_num, chapters in volumes.items():
        vol_nav[vol_num] = [ch['chapter'] for ch in chapters]

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mahabharata Dialog Viewer</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: Georgia, 'Times New Roman', serif; background: #faf8f5; color: #333; }}
#layout {{ display: flex; height: 100vh; }}
#nav {{
  width: 220px; min-width: 220px; background: #2c2c3a; color: #ccc;
  overflow-y: auto; padding: 10px; font-family: system-ui, sans-serif;
  font-size: 13px;
}}
#nav h3 {{ color: #E8B86D; margin: 0 0 10px; font-size: 15px; }}
.vol-group h4 {{
  cursor: pointer; padding: 5px 8px; margin: 2px 0; border-radius: 4px;
  background: #3a3a4f; color: #ddd; font-size: 12px;
}}
.vol-group h4:hover {{ background: #4a4a6f; }}
.ch-list {{ display: flex; flex-wrap: wrap; gap: 2px; padding: 4px; }}
.ch-list a {{
  display: inline-block; padding: 2px 6px; color: #9db8d4; text-decoration: none;
  font-size: 11px; border-radius: 3px;
}}
.ch-list a:hover {{ background: #4a4a6f; color: #fff; }}
.ch-list a.active {{ background: #E8B86D; color: #2c2c3a; }}
#content {{
  flex: 1; overflow-y: auto; padding: 20px 40px;
  max-width: 900px; margin: 0 auto;
}}
#legend {{
  position: sticky; top: 0; background: #faf8f5; padding: 10px 0 8px;
  border-bottom: 1px solid #e0d8ce; margin-bottom: 16px; z-index: 10;
  font-family: system-ui, sans-serif; font-size: 12px;
}}
.chapter h3 {{
  font-size: 16px; color: #666; margin: 24px 0 12px;
  border-bottom: 1px solid #e0d8ce; padding-bottom: 6px;
}}
.chapter p {{ font-size: 15px; line-height: 1.65; border-radius: 3px; }}
.chapter p span {{ transition: opacity 0.15s; }}
#vol-select, #ch-prev, #ch-next {{
  font-family: system-ui, sans-serif; font-size: 13px; padding: 4px 10px;
  border: 1px solid #ccc; border-radius: 4px; cursor: pointer; margin: 0 2px;
}}
#ch-nav {{ margin: 6px 0; }}
</style>
</head>
<body>
<div id="layout">
<div id="nav">
  <h3>Mahabharata Dialogs</h3>
  <div id="nav-volumes"></div>
</div>
<div id="content">
  <div id="legend">
    <div>{depth_legend}</div>
    <div id="ch-nav" style="margin-top:8px">
      <select id="vol-select" onchange="onVolChange()"></select>
      <select id="ch-select" onchange="onChChange()"></select>
      <button id="ch-prev" onclick="prevCh()">&larr;</button>
      <button id="ch-next" onclick="nextCh()">&rarr;</button>
    </div>
  </div>
  <div id="chapter-content">
    <p style="color:#999;text-align:center;margin-top:100px">Select a chapter from the sidebar or dropdowns above.</p>
  </div>
</div>
</div>
<script>
const VOL_CHAPTERS = {json.dumps(vol_nav)};

let currentVol = null;
let currentIdx = -1;
let chapterCache = {{}};

// Build nav sidebar
const navEl = document.getElementById('nav-volumes');
for (const [vol, chs] of Object.entries(VOL_CHAPTERS)) {{
  const grp = document.createElement('div');
  grp.className = 'vol-group';
  const h = document.createElement('h4');
  h.textContent = 'Volume ' + vol + ' (' + chs.length + ' ch)';
  h.onclick = function() {{
    const list = this.nextElementSibling;
    list.style.display = list.style.display === 'none' ? 'flex' : 'none';
  }};
  grp.appendChild(h);
  const list = document.createElement('div');
  list.className = 'ch-list';
  list.style.display = 'none';
  for (const ch of chs) {{
    const a = document.createElement('a');
    a.href = '#';
    a.textContent = ch;
    a.onclick = function(e) {{ e.preventDefault(); loadChapter(parseInt(vol), ch); }};
    list.appendChild(a);
  }}
  grp.appendChild(list);
  navEl.appendChild(grp);
}}

// Populate dropdowns
const volSel = document.getElementById('vol-select');
for (const vol of Object.keys(VOL_CHAPTERS)) {{
  const o = document.createElement('option');
  o.value = vol; o.textContent = 'Volume ' + vol;
  volSel.appendChild(o);
}}

function onVolChange() {{
  const vol = parseInt(volSel.value);
  populateChSelect(vol);
}}

function populateChSelect(vol) {{
  const chSel = document.getElementById('ch-select');
  chSel.innerHTML = '';
  const chs = VOL_CHAPTERS[vol] || [];
  for (const ch of chs) {{
    const o = document.createElement('option');
    o.value = ch; o.textContent = 'Ch ' + ch;
    chSel.appendChild(o);
  }}
}}

function onChChange() {{
  const vol = parseInt(volSel.value);
  const ch = parseInt(document.getElementById('ch-select').value);
  loadChapter(vol, ch);
}}

function prevCh() {{
  if (!currentVol) return;
  const chs = VOL_CHAPTERS[currentVol];
  if (currentIdx > 0) loadChapter(currentVol, chs[currentIdx - 1]);
}}

function nextCh() {{
  if (!currentVol) return;
  const chs = VOL_CHAPTERS[currentVol];
  if (currentIdx < chs.length - 1) loadChapter(currentVol, chs[currentIdx + 1]);
}}

async function loadChapter(vol, ch) {{
  currentVol = vol;
  const chs = VOL_CHAPTERS[vol];
  currentIdx = chs.indexOf(ch);
  volSel.value = vol;
  populateChSelect(vol);
  document.getElementById('ch-select').value = ch;

  const key = vol + '_' + ch;
  const el = document.getElementById('chapter-content');

  if (chapterCache[key]) {{
    el.innerHTML = chapterCache[key];
    el.scrollTop = 0;
    return;
  }}

  el.innerHTML = '<p style="color:#999;text-align:center">Loading...</p>';

  try {{
    const pad = String(ch).padStart(4, '0');
    const resp = await fetch('../dialogs/volume_' + vol + '/chapter_' + pad + '.json');
    const data = await resp.json();
    const html = renderChapter(data);
    chapterCache[key] = html;
    el.innerHTML = html;
    el.scrollTop = 0;
  }} catch(e) {{
    el.innerHTML = '<p style="color:red">Error loading chapter: ' + e.message + '</p>';
  }}
}}

const COLORS_A = [
  ['#555555','rgba(85,85,85,0.08)'],
  ['#7EB8F7','rgba(126,184,247,0.12)'],
  ['#2D6A4F','rgba(45,106,79,0.10)'],
  ['#E07A5F','rgba(224,122,95,0.12)'],
  ['#6C5CE7','rgba(108,92,231,0.12)'],
  ['#D62828','rgba(214,40,40,0.12)'],
  ['#F77F00','rgba(247,127,0,0.12)'],
];
const COLORS_B = [
  ['#8B7355','rgba(139,115,85,0.08)'],
  ['#B088D4','rgba(176,136,212,0.12)'],
  ['#8B6914','rgba(139,105,20,0.10)'],
  ['#C4785A','rgba(196,120,90,0.12)'],
  ['#5CA7E7','rgba(92,167,231,0.12)'],
  ['#9B4A6A','rgba(155,74,106,0.12)'],
  ['#D4A017','rgba(212,160,23,0.12)'],
];

function getCol(depth, alt) {{
  const colors = alt ? COLORS_B : COLORS_A;
  return colors[Math.min(depth, colors.length-1)];
}}

function esc(s) {{
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}}

function renderChapter(data) {{
  let h = '<div class="chapter">';
  h += '<h3>Chapter ' + data.chapter + ' (local ' + data.local + ') [' + (data.shlokas||0) + ' shlokas]</h3>';

  let prevDepth = -1;
  let paraAlt = {{}};

  for (const para of data.paragraphs) {{
    const depth = para.depth;
    if (!(depth in paraAlt)) paraAlt[depth] = false;
    if (depth === prevDepth) {{
      paraAlt[depth] = !paraAlt[depth];
    }}

    const alt = paraAlt[depth];
    const [tc, bg] = getCol(depth, alt);
    const indent = depth * 16;
    const border = Math.max(2, depth * 3);
    h += '<p style="background:' + bg + ';border-left:' + border + 'px solid ' + tc +
         ';padding:6px 10px 6px ' + (indent+10) + 'px;margin:2px 0">';

    let speechCount = {{}};
    for (const seg of para.segments) {{
      const d = seg.depth || 0;
      if (!(d in speechCount)) speechCount[d] = 0;

      let segAlt;
      if (seg.type === 'speech') {{
        segAlt = (speechCount[d] % 2 === 0) ? alt : !alt;
        speechCount[d]++;
      }} else {{
        segAlt = alt;
      }}

      const [sc] = getCol(d, segAlt);
      if (seg.type === 'speech') {{
        h += '<span style="color:' + sc + ';font-weight:500">' + esc(seg.text) + '</span>';
      }} else if (seg.type === 'narration') {{
        h += '<span style="color:' + sc + ';opacity:0.75">' + esc(seg.text) + '</span>';
      }} else {{
        h += '<span style="color:' + sc + ';opacity:0.5">' + esc(seg.text) + '</span>';
      }}
    }}
    h += '</p>';
    prevDepth = depth;
  }}
  h += '</div>';
  return h;
}}

// Auto-load first chapter
populateChSelect(1);
</script>
</body>
</html>"""

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)

    total_ch = sum(len(chs) for chs in volumes.values())
    print(f'Generated {OUTPUT_FILE} ({total_ch} chapters across {len(volumes)} volumes)')
    print(f'Chapters loaded dynamically from output/dialogs/ via fetch()')


if __name__ == '__main__':
    main()
