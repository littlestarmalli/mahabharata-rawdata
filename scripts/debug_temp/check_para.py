import json
data = json.load(open("output/json/story/parva_01_adi_parva/subparva_01_anukramanika_parva_tagged.json", encoding="utf-8"))
paras = data["chapters"]["1"]["paragraphs"]
for k in ["7", "8", "9", "20", "21"]:
    p = paras[k]
    print("=== Para %s | speaker=%s (%s) | frame=%d ===" % (k, p["speaker"], p["speaker_name"], p["frame"]))
    for seg in p["segments"]:
        print("  [%s] [%s]  %s" % (seg["type"].ljust(12), seg["speaker"], seg["text"][:90]))
    print()
