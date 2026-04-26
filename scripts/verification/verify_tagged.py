import json

f = "output/json/story/parva_01_adi_parva/subparva_14_viduragamana_parva_tagged.json"
data = json.load(open(f, encoding="utf-8"))

ch = data["chapters"]["192"]["paragraphs"]
for k in ["1", "2", "3", "4", "5"]:
    p = ch[k]
    print("--- Para %s | speaker=%s (%s) | color=%s | frame=%d" % (
        k, p["speaker"], p["speaker_name"], p["color"], p["frame"]))
    for seg in p["segments"]:
        print("    [%s] [%s] opacity=%.1f | %s" % (
            seg["type"].ljust(12), seg["speaker"], seg["opacity"], seg["text"][:90]))
    print()

# Also check characters.json color coverage
chars = json.load(open("output/json/characters.json", encoding="utf-8"))
total = len(chars)
has_color = sum(1 for v in chars.values() if "display" in v)
print("Characters with display/color: %d / %d" % (has_color, total))

# Show a few auto-generated ones
no_priority = [(k, v["display"]["color"]) for k,v in chars.items() 
               if "display" in v and k not in ["@arjuna","@krishna","@bhima","@yudhishthira"]][:8]
print("\nSample auto-colored characters:")
for cid, col in no_priority:
    print("  %s -> %s (%s)" % (cid, col, chars[cid].get("Name","")))
