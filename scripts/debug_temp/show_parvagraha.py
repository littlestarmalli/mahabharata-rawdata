import json

d = json.load(open("output/json/bori_text/parva_01_adi_bori_text.json", encoding="utf-8"))

for sp_k, sp in d["subparvas"].items():
    if "parvasa" in sp["name"] or "graha" in sp["name"]:
        print(f"Sub-Parva: {sp['name']}  (SP {sp['number']})")
        ch = list(sp["chapters"].values())[0]
        print(f"Chapter {ch['chapter_number']}  |  {ch['num_shlokas']} shlokas")
        print()
        for num, text in ch["shlokas"].items():
            # clean up newlines for display
            clean = text.replace("\n", " | ")
            print(f"[{int(num):>3}]  {clean}")
