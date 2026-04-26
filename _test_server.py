"""Quick test: fetch from local server and verify content."""
import urllib.request, json

# Fetch the HTML page
html = urllib.request.urlopen('http://127.0.0.1:8080/web/dialog_viewer.html').read().decode()
# Check the renderChapter function
idx = html.find("seg.type === 'speech'")
print('=== Render code for speech ===')
print(html[idx:idx+250])
print()

# Fetch chapter 3 JSON
data = json.loads(urllib.request.urlopen('http://127.0.0.1:8080/dialogs/volume_1/chapter_0003.json').read())
p1 = data['paragraphs'][0]
segs = p1['segments']
print(f'Para 1 has {len(segs)} segments:')
for s in segs:
    print(f'  {s["type"]:10} d{s["depth"]}  {s["text"][:70]}')
