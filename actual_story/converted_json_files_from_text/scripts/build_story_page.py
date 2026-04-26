"""Generate a single continuous story page — no headings, no chapters.
Nested boxes colored by SPEAKER (from characters.json display.color).
Nesting depth tracks quote structure; color tracks who is speaking."""

import json, os, html


def load_speaker_colors():
    """Load speaker @id → {color, label} from characters.json."""
    chars_path = os.path.join('output', 'json', 'characters.json')
    colors = {}
    if os.path.exists(chars_path):
        chars = json.load(open(chars_path, encoding='utf-8'))
        for cid, info in chars.items():
            if not cid.startswith('@'):
                continue
            disp = info.get('display', {})
            color = disp.get('color', '')
            if color:
                colors[cid] = {
                    'color': color,
                    'label': disp.get('label', info.get('Name', cid))
                }
    return colors


# Fallback color for speakers not in characters.json
FALLBACK_COLOR = '#B0B0B0'

# Depth-based background colors (kept from original)
MAX_DEPTH = 7
DEPTH_BG = [
    '#f5f5f5',   # 0: gray
    '#e3f2fd',   # 1: blue
    '#e8f5e9',   # 2: green
    '#fff3e0',   # 3: orange
    '#fce4ec',   # 4: pink
    '#ede7f6',   # 5: purple
    '#e0f7fa',   # 6: cyan
    '#fff9c4',   # 7: yellow
]
DEPTH_TEXT = [
    '#616161',   # 0: dark gray
    '#1565c0',   # 1: dark blue
    '#2e7d32',   # 2: dark green
    '#e65100',   # 3: dark orange
    '#c62828',   # 4: dark red
    '#4527a0',   # 5: dark purple
    '#00695c',   # 6: dark teal
    '#f57f17',   # 7: dark amber
]


def speaker_style(speaker_id, speaker_colors):
    """Get (bg_color, border_color, label) for a speaker."""
    info = speaker_colors.get(speaker_id)
    if info:
        c = info['color']
        label = info['label']
    else:
        c = FALLBACK_COLOR
        label = speaker_id.replace('@', '').replace('_', ' ').title() if speaker_id else 'Unknown'
    # Background is speaker color at 15% opacity, border at full
    return c, label


def hex_to_rgba(hex_color, alpha):
    """Convert #RRGGBB to rgba(r,g,b,a)."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


def load_all_chapters():
    """Load all chapter JSONs in global chapter order."""
    chapters = []
    for v in range(1, 11):
        d = os.path.join('output', 'dialogs', f'volume_{v}')
        files = sorted(f for f in os.listdir(d) if f.endswith('.json'))
        for fname in files:
            data = json.load(open(os.path.join(d, fname), encoding='utf-8'))
            chapters.append(data)
    # Sort by global chapter number
    chapters.sort(key=lambda c: c['chapter'])
    return chapters


def generate_html(chapters, speaker_colors):
    """Generate one continuous nested HTML stream with speaker-based coloring."""
    parts = []

    cur_depth = -1  # tracks current open nesting level
    cur_speaker_at = {}  # depth -> speaker_id of open container
    need_pbreak = False  # insert line break between paragraphs

    for ch in chapters:
        for para in ch['paragraphs']:
            is_first_seg = True
            for seg in para['segments']:
                d = seg.get('depth', 0)
                speaker = seg.get('speaker', '@ugrasrava')

                # Close deeper containers
                while cur_depth > d:
                    parts.append('</div>')
                    cur_speaker_at.pop(cur_depth, None)
                    cur_depth -= 1

                # If same depth but speaker changed, close and reopen
                if cur_depth == d and cur_speaker_at.get(d) != speaker:
                    parts.append('</div>')
                    cur_depth -= 1

                # Open containers to reach target depth
                while cur_depth < d:
                    cur_depth += 1
                    # Use the speaker for the target depth
                    sp = speaker if cur_depth == d else cur_speaker_at.get(cur_depth, speaker)
                    color, label = speaker_style(sp, speaker_colors)
                    bg = hex_to_rgba(color, 0.12)
                    parts.append(
                        f'<div class="nest" style="background:{bg};'
                        f'border-left:4px solid {color}"'
                        f' data-speaker="{html.escape(sp)}"'
                        f' data-label="{html.escape(label)}">'
                    )
                    cur_speaker_at[cur_depth] = sp

                # Paragraph break: new line between paragraphs
                if is_first_seg and need_pbreak:
                    parts.append('<br>')
                is_first_seg = False

                # Render the text segment
                text = html.escape(seg['text'])
                stype = seg.get('type', 'narration')
                color, label = speaker_style(speaker, speaker_colors)
                depth_color = DEPTH_TEXT[min(d, MAX_DEPTH)]

                introduces = seg.get('introduces', '')
                intro_label = seg.get('introduces_label', '')

                if stype == 'close':
                    parts.append(f'<span class="seg close">{text}</span>')
                elif introduces and intro_label:
                    # Attribution: "X said," — show speaker label
                    parts.append(
                        f'<span class="seg attr" style="color:{depth_color}">'
                        f'<b>{html.escape(intro_label)}</b>'
                        f'{text[len(intro_label):]}</span>'
                    )
                elif stype == 'speech':
                    parts.append(f'<span class="seg speech" style="color:{depth_color}">{text}</span>')
                else:
                    parts.append(f'<span class="seg narration" style="color:{depth_color}">{text}</span>')

            need_pbreak = True  # after each paragraph, next one gets a line break

    # Close all remaining open containers
    while cur_depth >= 0:
        parts.append('</div>')
        cur_depth -= 1

    return '\n'.join(parts)


def main():
    print("Loading speaker colors...")
    speaker_colors = load_speaker_colors()
    print(f"Loaded {len(speaker_colors)} speaker colors")

    print("Loading all chapters...")
    chapters = load_all_chapters()
    print(f"Loaded {len(chapters)} chapters")

    print("Generating continuous HTML...")
    story_html = generate_html(chapters, speaker_colors)

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>The Mahabharata — Continuous Story</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: Georgia, 'Times New Roman', serif;
  background: #fafafa; color: #222;
  padding: 8px 4px;
}}
#story {{
  width: 100%; margin: 0; padding: 0;
}}
.nest {{
  border-radius: 0;
  padding: 0 0 0 8px;
  margin: 0;
}}
.seg {{
  font-size: 15px; line-height: 1.6;
}}
.seg.speech {{ font-weight: 500; }}
.seg.attr {{ font-weight: 500; }}
.seg.attr b {{ font-weight: 700; }}
.seg.narration {{ opacity: 0.85; }}
.seg.close {{ opacity: 0.4; font-size: 13px; }}

/* Scroll to top */
#scroll-top {{
  position: fixed; bottom: 24px; right: 24px; z-index: 200;
  width: 44px; height: 44px; border-radius: 50%;
  background: #2c2c3a; color: #E8B86D; border: 2px solid #E8B86D;
  font-size: 20px; cursor: pointer; display: none;
  align-items: center; justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}}
#scroll-top:hover {{ background: #4a4a6a; }}
</style>
</head>
<body>

<div id="story">
{story_html}
</div>

<button id="scroll-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">&#9650;</button>
<script>
window.addEventListener('scroll', function() {{
  document.getElementById('scroll-top').style.display = window.scrollY > 400 ? 'flex' : 'none';
}});
</script>
</body>
</html>'''

    out_path = os.path.join('output', 'web', 'mahabharata_story.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(page)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Written to {out_path} ({size_mb:.1f} MB)")


if __name__ == '__main__':
    main()
