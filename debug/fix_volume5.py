"""Remove preview paragraph from volume 5 chapters."""
from pathlib import Path

file_path = Path('output/volumes/volume_5_chapters.txt')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and remove the preview paragraph
idx = content.rfind(' The sixth volume completes')
if idx > 0:
    new_content = content[:idx].rstrip() + '\n'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✓ Removed preview paragraph from volume 5 chapters")
else:
    print("Preview paragraph not found")
