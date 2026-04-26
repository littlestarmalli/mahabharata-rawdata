"""
generate_viewer.py
------------------
Reads all *_tagged.json subparva files + characters.json and generates
a single self-contained HTML viewer at output/web/viewer.html

Usage:
    python generate_viewer.py              # build full viewer
    python generate_viewer.py --parva 1   # only parva 1 (faster for testing)
"""

import json
import glob
import argparse
import re
from pathlib import Path

BASE       = Path(__file__).parent
STORY_DIR  = BASE / "output" / "json" / "story"
CHARS_FILE = BASE / "output" / "json" / "characters.json"
OUT_FILE   = BASE / "output" / "web" / "viewer.html"

def slug_parva(folder_name: str) -> str:
    return folder_name  # keep as-is for JS keys

def load_all_tagged(parva_filter=None):
    """Return list of (parva_folder, subparva_stem, data_dict)."""
    pattern = str(STORY_DIR / "parva_*" / "subparva_*_tagged.json")
    files = sorted(glob.glob(pattern))
    results = []
    for f in files:
        p = Path(f)
        if parva_filter:
            if f"parva_{parva_filter:02d}_" not in p.parent.name:
                continue
        data = json.load(open(f, encoding="utf-8"))
        results.append((p.parent.name, p.stem.replace("_tagged", ""), data))
    return results

def build_nav_tree(entries):
    """Build {parva_folder: [subparva_stem, ...]} ordered dict."""
    tree = {}
    for parva_folder, sp_stem, _ in entries:
        tree.setdefault(parva_folder, []).append(sp_stem)
    return tree

def hex_to_rgba(hex_color: str, opacity: float) -> str:
    hx = hex_color.lstrip("#")
    r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
    return f"rgba({r},{g},{b},{opacity})"

def render_segment(seg: dict) -> str:
    """Return an HTML <span> for one segment."""
    stype   = seg.get("type", "narration")
    color   = seg.get("color", "#888888")
    opacity = seg.get("opacity", 0.4)
    speaker = seg.get("speaker", "")
    text    = seg.get("text", "")

    # Escape HTML
    text_esc = (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;"))

    # Replace {N} footnote markers with superscripts
    text_esc = re.sub(r"\{(\d+)\}", r"<sup class='fn'>\1</sup>", text_esc)

    bg   = hex_to_rgba(color, opacity * 0.35)
    fg   = color

    type_class = {
        "attribution": "seg-attr",
        "speech":      "seg-speech",
        "narration":   "seg-narr",
    }.get(stype, "seg-narr")

    title = f"{stype} · {speaker}"
    return (
        f'<span class="seg {type_class}" '
        f'style="color:{fg};background:{bg}" '
        f'data-speaker="{speaker}" data-type="{stype}" '
        f'title="{title}">'
        f'{text_esc}</span>'
    )

def render_paragraph(p_key: str, para: dict) -> str:
    speaker      = para.get("speaker", "")
    speaker_name = para.get("speaker_name", speaker.lstrip("@"))
    color        = para.get("color", "#888888")
    frame        = para.get("frame", 0)
    segments     = para.get("segments", [])

    badge_bg  = hex_to_rgba(color, 0.85)
    left_border = color

    seg_html = "".join(render_segment(s) for s in segments)

    frame_label = {
        -1: "Author",
         0: "Souti → Sages",
         1: "Vaishampayana → Janamejaya",
         2: "Sanjaya → Dhritarashtra",
    }.get(frame, f"Frame {frame}")

    return f"""
    <div class="para" data-speaker="{speaker}" data-frame="{frame}"
         style="border-left: 4px solid {left_border}">
      <div class="para-meta">
        <span class="badge" style="background:{badge_bg};color:#fff">{speaker_name}</span>
        <span class="frame-tag">frame {frame} · {frame_label}</span>
        <span class="para-num">§{p_key}</span>
      </div>
      <p class="para-text">{seg_html}</p>
    </div>"""

def render_chapter(ch_key: str, ch_data: dict) -> str:
    global_num = ch_data.get("global_number", ch_key)
    local_num  = ch_data.get("local_number", ch_key)
    shlokas    = ch_data.get("num_shlokas", "?")
    paras      = ch_data.get("paragraphs", {})

    para_html = "\n".join(
        render_paragraph(pk, pv)
        for pk, pv in sorted(paras.items(), key=lambda x: int(x[0]))
    )
    return f"""
  <div class="chapter" id="ch-{global_num}">
    <h3 class="ch-heading">Chapter {global_num}
      <small>(local {local_num} · {shlokas} shlokas)</small>
    </h3>
    {para_html}
  </div>"""

def render_subparva(sp_stem: str, data: dict) -> str:
    name       = data.get("name", sp_stem)
    sp_num     = data.get("subparva_number", "?")
    volume     = data.get("source_volume", "?")
    details    = data.get("details", {})
    note       = data.get("note", "")
    chapters   = data.get("chapters", {})
    translator = data.get("translator", "")

    ch_html = "\n".join(
        render_chapter(ck, cv)
        for ck, cv in sorted(chapters.items(), key=lambda x: int(x[0]))
    )

    note_html = f'<p class="note">{note}</p>' if note else ""
    return f"""
<div class="subparva" id="sp-{sp_stem}">
  <div class="sp-header">
    <h2>{sp_num}. {name}</h2>
    <div class="sp-meta">
      Volume {volume} &nbsp;·&nbsp;
      {details.get("num_chapters","?")} chapters &nbsp;·&nbsp;
      {details.get("num_shlokas","?")} shlokas &nbsp;·&nbsp;
      Translator: {translator}
    </div>
    {note_html}
  </div>
  {ch_html}
</div>"""

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mahabharata — Dialogue Viewer</title>
<style>
:root {{
  --bg: #0f0f1a;
  --bg2: #1a1a2e;
  --bg3: #16213e;
  --fg: #e0d9c8;
  --fg2: #a09880;
  --accent: #FFBF69;
  --border: #2a2a4a;
  --sidebar-w: 280px;
  --font: 'Georgia', serif;
  --mono: 'Consolas', monospace;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: var(--bg);
  color: var(--fg);
  font-family: var(--font);
  display: flex;
  height: 100vh;
  overflow: hidden;
}}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
#sidebar {{
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  background: var(--bg2);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}
#sidebar-title {{
  padding: 14px 16px;
  font-size: 13px;
  font-weight: bold;
  color: var(--accent);
  letter-spacing: 1px;
  border-bottom: 1px solid var(--border);
  text-transform: uppercase;
}}
#search-box {{
  margin: 10px;
  padding: 6px 10px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--fg);
  font-size: 13px;
  width: calc(100% - 20px);
}}
#search-box::placeholder {{ color: var(--fg2); }}
#nav {{
  flex: 1;
  overflow-y: auto;
  padding-bottom: 20px;
}}
.parva-group {{ margin-bottom: 4px; }}
.parva-btn {{
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  color: var(--fg2);
  font-size: 12px;
  padding: 7px 16px;
  cursor: pointer;
  font-family: var(--font);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}}
.parva-btn:hover {{ color: var(--accent); }}
.parva-btn.active {{ color: var(--accent); font-weight: bold; }}
.sp-list {{ display: none; padding-left: 8px; }}
.sp-list.open {{ display: block; }}
.sp-btn {{
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  color: var(--fg);
  font-size: 12px;
  padding: 5px 16px 5px 24px;
  cursor: pointer;
  font-family: var(--font);
  border-left: 2px solid transparent;
}}
.sp-btn:hover {{ color: var(--accent); border-left-color: var(--accent); }}
.sp-btn.active {{
  color: var(--accent);
  border-left-color: var(--accent);
  background: rgba(255,191,105,0.06);
}}

/* ── Legend ──────────────────────────────────────────────────────────── */
#legend {{
  border-top: 1px solid var(--border);
  padding: 10px 14px;
  font-size: 11px;
  color: var(--fg2);
  line-height: 1.8;
}}
.leg-item {{ display: flex; align-items: center; gap: 6px; margin-bottom: 2px; }}
.leg-dot {{
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}}

/* ── Filters toolbar ─────────────────────────────────────────────────── */
#toolbar {{
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 10px 20px;
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}}
.filter-btn {{
  padding: 4px 12px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--bg3);
  color: var(--fg2);
  cursor: pointer;
  font-size: 12px;
  font-family: var(--font);
  transition: all 0.15s;
}}
.filter-btn.on {{
  background: var(--accent);
  color: #111;
  border-color: var(--accent);
  font-weight: bold;
}}
#frame-filter {{
  margin-left: auto;
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 12px;
  color: var(--fg2);
}}
#frame-filter select {{
  background: var(--bg3);
  border: 1px solid var(--border);
  color: var(--fg);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
}}

/* ── Main content ────────────────────────────────────────────────────── */
#main {{
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}
#content {{
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}}
#content-placeholder {{
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--fg2);
  font-size: 16px;
  letter-spacing: 1px;
}}

/* ── Subparva / chapter ──────────────────────────────────────────────── */
.subparva {{ max-width: 820px; }}
.sp-header {{
  margin-bottom: 24px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}}
.sp-header h2 {{
  font-size: 22px;
  color: var(--accent);
  margin-bottom: 6px;
}}
.sp-meta {{
  font-size: 12px;
  color: var(--fg2);
  font-family: var(--mono);
  margin-bottom: 6px;
}}
.note {{
  font-size: 13px;
  color: var(--fg2);
  font-style: italic;
  line-height: 1.6;
  padding: 8px 12px;
  border-left: 3px solid var(--border);
  margin-top: 10px;
}}
.chapter {{ margin-bottom: 36px; }}
.ch-heading {{
  font-size: 14px;
  color: var(--fg2);
  font-family: var(--mono);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 16px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}}
.ch-heading small {{ font-size: 11px; opacity: 0.7; }}

/* ── Paragraph ───────────────────────────────────────────────────────── */
.para {{
  display: block;
  margin-bottom: 14px;
  padding: 10px 14px;
  border-radius: 4px;
  background: rgba(255,255,255,0.02);
  transition: background 0.15s;
}}
.para:hover {{ background: rgba(255,255,255,0.05); }}
.para-meta {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 7px;
  flex-wrap: wrap;
}}
.badge {{
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  font-family: var(--mono);
  letter-spacing: 0.5px;
  text-transform: uppercase;
  font-weight: bold;
}}
.frame-tag {{
  font-size: 10px;
  color: var(--fg2);
  font-family: var(--mono);
}}
.para-num {{
  font-size: 10px;
  color: var(--fg2);
  font-family: var(--mono);
  margin-left: auto;
  opacity: 0.5;
}}
.para-text {{
  line-height: 1.85;
  font-size: 15px;
}}

/* ── Segments ─────────────────────────────────────────────────────────── */
.seg {{
  border-radius: 3px;
  padding: 1px 3px;
  cursor: default;
  transition: filter 0.1s;
}}
.seg:hover {{ filter: brightness(1.3); }}
.seg-attr {{
  font-style: italic;
  font-size: 0.9em;
  opacity: 0.85;
}}
.seg-speech {{ font-weight: 400; }}
.seg-narr {{ font-style: italic; }}

/* ── Footnote superscripts ─────────────────────────────────────────────── */
.fn {{
  font-size: 0.65em;
  color: var(--accent);
  opacity: 0.8;
  vertical-align: super;
  cursor: help;
}}

/* ── Paragraph hidden (filter) ─────────────────────────────────────────── */
.para.hidden {{ display: none; }}

/* ── Scrollbar ────────────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg2); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
</style>
</head>
<body>

<div id="sidebar">
  <div id="sidebar-title">Mahabharata</div>
  <input id="search-box" type="search" placeholder="Search subparva…">
  <div id="nav">__NAV__</div>
  <div id="legend">
    <div class="leg-item"><span class="leg-dot" style="background:#C8B8A2"></span> Author (frame −1)</div>
    <div class="leg-item"><span class="leg-dot" style="background:#E8B86D"></span> Souti (frame 0)</div>
    <div class="leg-item"><span class="leg-dot" style="background:#7EB8F7"></span> Vaishampayana (frame 1)</div>
    <div class="leg-item"><span class="leg-dot" style="background:#A8D5A2"></span> Sanjaya (frame 2)</div>
    <div class="leg-item"><span class="leg-dot" style="background:#9B8BB4"></span> Dhritarashtra</div>
    <div class="leg-item"><span class="leg-dot" style="background:#6C5CE7"></span> Krishna</div>
    <div class="leg-item"><span class="leg-dot" style="background:#F4D35E"></span> Yudhishthira</div>
    <hr style="border-color:#2a2a4a;margin:6px 0">
    <div style="font-size:10px;opacity:0.7">Hover segments for type &amp; speaker</div>
  </div>
</div>

<div id="main">
  <div id="toolbar">
    <span style="font-size:12px;color:var(--fg2);margin-right:4px">Show:</span>
    <button class="filter-btn on" data-type="narration">Narration</button>
    <button class="filter-btn on" data-type="attribution">Attribution</button>
    <button class="filter-btn on" data-type="speech">Speech</button>
    <div id="frame-filter">
      Frame:
      <select id="frame-select">
        <option value="all">All</option>
        <option value="-1">−1 Author</option>
        <option value="0">0 Souti</option>
        <option value="1">1 Vaishampayana</option>
        <option value="2">2 Sanjaya</option>
      </select>
    </div>
  </div>
  <div id="content">
    <div id="content-placeholder">← Select a subparva to begin</div>
  </div>
</div>

<script>
const DATA = __DATA__;

/* ── Navigation ──────────────────────────────────────────────────────── */
function showSubparva(spKey) {
  const html = DATA[spKey];
  document.getElementById('content').innerHTML = html || '<em>Not found</em>';
  applyFilters();

  document.querySelectorAll('.sp-btn').forEach(b => b.classList.remove('active'));
  const btn = document.querySelector('.sp-btn[data-key="'+spKey+'"]');
  if (btn) {
    btn.classList.add('active');
    // Open parent parva group
    btn.closest('.sp-list').classList.add('open');
    btn.closest('.parva-group').querySelector('.parva-btn').classList.add('active');
  }
  // Scroll content to top
  document.getElementById('content').scrollTop = 0;
}

/* ── Filters ─────────────────────────────────────────────────────────── */
const activeTypes = new Set(['narration','attribution','speech']);
let activeFrame = 'all';

function applyFilters() {
  document.querySelectorAll('.para').forEach(paraEl => {
    const frame = paraEl.dataset.frame;
    const frameOk = activeFrame === 'all' || frame === activeFrame;
    if (!frameOk) { paraEl.classList.add('hidden'); return; }
    paraEl.classList.remove('hidden');
    // Show/hide individual segment spans
    paraEl.querySelectorAll('.seg').forEach(seg => {
      seg.style.display = activeTypes.has(seg.dataset.type) ? '' : 'none';
    });
  });
}

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const t = btn.dataset.type;
    if (activeTypes.has(t)) { activeTypes.delete(t); btn.classList.remove('on'); }
    else                    { activeTypes.add(t);    btn.classList.add('on'); }
    applyFilters();
  });
});

document.getElementById('frame-select').addEventListener('change', e => {
  activeFrame = e.target.value;
  applyFilters();
});

/* ── Search ──────────────────────────────────────────────────────────── */
document.getElementById('search-box').addEventListener('input', function() {
  const q = this.value.toLowerCase();
  document.querySelectorAll('.sp-btn').forEach(btn => {
    const match = btn.textContent.toLowerCase().includes(q);
    btn.style.display = match ? '' : 'none';
    if (match && q) btn.closest('.sp-list').classList.add('open');
  });
  if (!q) document.querySelectorAll('.sp-list').forEach(l => l.classList.remove('open'));
});

/* ── Parva toggle ─────────────────────────────────────────────────────── */
document.querySelectorAll('.parva-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const list = btn.nextElementSibling;
    list.classList.toggle('open');
  });
});

/* ── Auto-open first subparva ──────────────────────────────────────────── */
const firstKey = Object.keys(DATA)[0];
if (firstKey) showSubparva(firstKey);
</script>
</body>
</html>
"""

def build_nav_html(tree):
    parts = []
    for parva_folder, sp_stems in tree.items():
        # Parva display name: e.g. "parva_01_adi_parva" -> "01 Adi Parva"
        m = re.match(r"parva_(\d+)_(.*)", parva_folder)
        if m:
            num  = m.group(1)
            name = m.group(2).replace("_", " ").title()
            display = f"{num}. {name}"
        else:
            display = parva_folder

        sp_btns = ""
        for sp_stem in sp_stems:
            sm = re.match(r"subparva_(\d+)_(.*)", sp_stem)
            if sm:
                sn   = sm.group(1)
                sname = sm.group(2).replace("_", " ").title()
                sp_display = f"{sn}. {sname}"
            else:
                sp_display = sp_stem
            sp_btns += (
                f'<button class="sp-btn" data-key="{sp_stem}" '
                f'onclick="showSubparva(\'{sp_stem}\')">{sp_display}</button>\n'
            )

        parts.append(f"""
<div class="parva-group">
  <button class="parva-btn">{display}</button>
  <div class="sp-list">
    {sp_btns}
  </div>
</div>""")
    return "\n".join(parts)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parva", type=int, default=None)
    args = parser.parse_args()

    print("Loading characters…")
    chars = json.load(open(CHARS_FILE, encoding="utf-8"))

    print("Loading tagged subparvas…")
    entries = load_all_tagged(args.parva)
    print(f"  {len(entries)} subparva files")

    tree = build_nav_tree(entries)

    # Build per-subparva HTML snippets stored in a JS object
    data_js_parts = []
    for parva_folder, sp_stem, data in entries:
        html_snippet = render_subparva(sp_stem, data)
        # Escape for JS string (backtick template)
        safe = html_snippet.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        data_js_parts.append(f'  "{sp_stem}": `{safe}`')

    data_js = "{\n" + ",\n".join(data_js_parts) + "\n}"
    nav_html = build_nav_html(tree)

    html = HTML_TEMPLATE.replace("__NAV__", nav_html).replace("__DATA__", data_js)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(html, encoding="utf-8")
    size_kb = OUT_FILE.stat().st_size // 1024
    print(f"  Written -> {OUT_FILE}  ({size_kb} KB)")

if __name__ == "__main__":
    main()
