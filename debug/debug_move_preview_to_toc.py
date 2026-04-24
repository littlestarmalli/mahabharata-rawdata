"""
Move volume preview paragraphs from chapters.txt to toc.txt files.

These paragraphs describe what the next volume will contain and are TOC/meta information,
not story content.
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.parent
VOLUMES_DIR = PROJECT_ROOT / 'output' / 'volumes'

# Map of volume number to a unique search phrase that identifies the preview paragraph
# We'll extract the full paragraph dynamically since files contain special Unicode characters
PREVIEW_MARKERS = {
    1: ("second volume will recount", "banishment of the Pandavas."),
    2: ("third volume will complete", "robbed of his earrings by Indra."),
    3: ("This ends Aranyaka Parva.", "preparations for the inevitable war."),
    4: ("fth volume will cover", "Abhimanyu is killed."),  # "ﬁfth" contains ligature
    5: ("sixth volume completes", "after Drona's death."),
    6: ("This concludes Drona Parva.", "100-parva classiﬁcation."),
    9: ("nal volume ends", "already there."),  # "ﬁnal" contains ligature
}


def extract_preview_paragraph(content, start_marker, end_marker):
    """Extract the preview paragraph between markers."""
    start_idx = content.find(start_marker)
    if start_idx == -1:
        return None
    
    # Find the beginning of the sentence (look back to find start after previous sentence/quote)
    # The preview usually starts with "The" or "This"
    search_start = max(0, start_idx - 100)
    before_text = content[search_start:start_idx]
    
    # Find last sentence ending before our marker
    sentence_breaks = [before_text.rfind('. '), before_text.rfind('.\' '), before_text.rfind('.â€™ ')]
    last_break = max(sentence_breaks)
    
    if last_break != -1:
        para_start = search_start + last_break + 2  # After ". " or ".â€™ "
        # Skip any whitespace or quote marks
        while para_start < start_idx and content[para_start] in ' \n\'"â€˜':
            para_start += 1
    else:
        para_start = start_idx
    
    # Find end
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        return None
    
    para_end = end_idx + len(end_marker)
    
    return content[para_start:para_end]


def move_preview_to_toc(volume_num):
    """Move preview paragraph from chapters to toc for a given volume."""
    
    if volume_num not in PREVIEW_MARKERS:
        print(f"Volume {volume_num}: No preview paragraph to move")
        return False
    
    chapters_file = VOLUMES_DIR / f'volume_{volume_num}_chapters.txt'
    toc_file = VOLUMES_DIR / f'volume_{volume_num}_toc.txt'
    
    if not chapters_file.exists():
        print(f"Volume {volume_num}: Chapters file not found!")
        return False
    
    if not toc_file.exists():
        print(f"Volume {volume_num}: TOC file not found!")
        return False
    
    start_marker, end_marker = PREVIEW_MARKERS[volume_num]
    
    # Read chapters file
    with open(chapters_file, 'r', encoding='utf-8') as f:
        chapters_content = f.read()
    
    # Extract the preview paragraph
    preview_text = extract_preview_paragraph(chapters_content, start_marker, end_marker)
    
    if not preview_text:
        print(f"Volume {volume_num}: Could not extract preview paragraph!")
        print(f"  Start marker: {start_marker[:50]}...")
        print(f"  End marker: {end_marker[:50]}...")
        return False
    
    print(f"Volume {volume_num}: Found preview ({len(preview_text)} chars)")
    print(f"  Preview starts: {preview_text[:60]}...")
    
    # Remove preview from chapters
    new_chapters_content = chapters_content.replace(preview_text, '').rstrip() + '\n'
    
    # Read TOC file
    with open(toc_file, 'r', encoding='utf-8') as f:
        toc_content = f.read()
    
    # Append preview to TOC
    new_toc_content = toc_content.rstrip() + '\n\n--- NEXT VOLUME PREVIEW ---\n\n' + preview_text + '\n'
    
    # Write updated files
    with open(chapters_file, 'w', encoding='utf-8') as f:
        f.write(new_chapters_content)
    
    with open(toc_file, 'w', encoding='utf-8') as f:
        f.write(new_toc_content)
    
    print(f"Volume {volume_num}: ✓ Moved preview paragraph from chapters to TOC")
    return True


def main():
    print("=" * 80)
    print("MOVING VOLUME PREVIEW PARAGRAPHS FROM CHAPTERS TO TOC")
    print("=" * 80)
    print()
    
    success_count = 0
    
    for vol_num in sorted(PREVIEW_MARKERS.keys()):
        if move_preview_to_toc(vol_num):
            success_count += 1
        print()
    
    print("=" * 80)
    print(f"SUMMARY: Moved {success_count}/{len(PREVIEW_MARKERS)} preview paragraphs")
    print("=" * 80)


if __name__ == '__main__':
    main()
