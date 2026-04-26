import json, re

src = json.load(open(
    "output/json/story/parva_01_adi_parva/subparva_03_poushya_parva.json",
    encoding="utf-8"))
text = src["chapters"]["3"]["paragraphs"]["1"]

# Show the actual characters in the speech body
print("Para 1 first 200 chars repr:")
print(repr(text[:200]))
print()

# Check what quote characters exist
found_quotes = set(c for c in text if c in '""\u201c\u201d\u0022')
print("Quote chars in text:", {repr(c): hex(ord(c)) for c in found_quotes})

# Show para 2
text2 = src["chapters"]["3"]["paragraphs"]["2"]
print("\nPara 2 first 200 chars repr:")
print(repr(text2[:200]))
found_quotes2 = set(c for c in text2 if c in '""\u201c\u201d\u0022')
print("Quote chars in para 2:", {repr(c): hex(ord(c)) for c in found_quotes2})
