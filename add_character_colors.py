"""
add_character_colors.py
-----------------------
Adds 'display' color blocks to key characters in characters.json.
Safe to re-run: only adds the block if missing, never overwrites.
"""

import json, os

CHAR_FILE = os.path.join(os.path.dirname(__file__),
                         "output", "json", "characters.json")

# Priority color assignments
# Format: @id -> (hex_light, hex_dark, label)
COLOR_MAP = {
    # Narrators
    "@ugrasrava":       ("#E8B86D", "#C9973E", "Souti"),
    "@vaishampayana":   ("#7EB8F7", "#4E88CC", "Vaishampayana"),
    "@sanjaya":         ("#A8D5A2", "#6BAD64", "Sanjaya"),

    # Pandavas
    "@yudhishthira":    ("#F4D35E", "#C9A82E", "Yudhishthira"),
    "@arjuna":          ("#5BA4CF", "#3A7FAA", "Arjuna"),
    "@bhima":           ("#E07A5F", "#B84E35", "Bhima"),
    "@nakula":          ("#81B29A", "#4E8C72", "Nakula"),
    "@sahadeva":        ("#6BAB8A", "#3E7C5C", "Sahadeva"),
    "@kunti":           ("#E9C46A", "#C49A30", "Kunti"),
    "@draupadi":        ("#E84393", "#B5166A", "Draupadi"),

    # Krishna & Yadavas
    "@krishna":         ("#6C5CE7", "#4835C0", "Krishna"),
    "@subhadra":        ("#A29BFE", "#7A6FD0", "Subhadra"),
    "@balarama":        ("#00B4D8", "#007EA0", "Balarama"),

    # Kauravas
    "@duryodhana":      ("#D62828", "#A01818", "Duryodhana"),
    "@duhshasana":      ("#C1121F", "#8B0D15", "Duhshasana"),
    "@dhritarashtra":   ("#9B8BB4", "#6B5B8E", "Dhritarashtra"),
    "@gandhari":        ("#B5838D", "#8A5560", "Gandhari"),
    "@shakuni":         ("#6D4C41", "#3E2723", "Shakuni"),

    # Elders / Preceptors
    "@bhishma":         ("#457B9D", "#2B5F80", "Bhishma"),
    "@drona":           ("#2D6A4F", "#1A4530", "Drona"),
    "@kripa":           ("#40916C", "#2D6A4F", "Kripa"),
    "@vidura":          ("#52796F", "#354F52", "Vidura"),
    "@karna":           ("#F77F00", "#C05A00", "Karna"),
    "@ashvatthama":     ("#8B5E3C", "#5C3A1E", "Ashvatthama"),

    # Other key characters
    "@abhimanyu":       ("#F2CC8F", "#C9943A", "Abhimanyu"),
    "@janamejaya":      ("#C77DFF", "#9B4DCA", "Janamejaya"),
    "@parikshit":       ("#B7D7E8", "#6FA8C5", "Parikshit"),
    "@pandu":           ("#D4E09B", "#9DB84A", "Pandu"),
    "@shantanu":        ("#8ECAE6", "#3A8BB4", "Shantanu"),
    "@satyavati":       ("#FF9F1C", "#C07000", "Satyavati"),
    "@vyasa":           ("#FFBF69", "#C47800", "Vyasa"),
    "@narada":          ("#CBF3F0", "#5BBAB5", "Narada"),
    "@indra":           ("#FFD60A", "#C9A800", "Indra"),
    "@shiva":           ("#CDB4DB", "#9B6DB4", "Shiva"),
    "@yama":            ("#6B4226", "#3E2010", "Yama"),
    "@drupada":         ("#4CC9F0", "#1A9EC0", "Drupada"),
    "@dhrishtadyumna":  ("#4361EE", "#1A3DBB", "Dhrishtadyumna"),
    "@shikhandi":       ("#7209B7", "#4A0078", "Shikhandi"),
}

with open(CHAR_FILE, encoding="utf-8") as fh:
    chars = json.load(fh)

added = 0
skipped = 0

for char_id, (color, color_dark, label) in COLOR_MAP.items():
    if char_id not in chars:
        print(f"  WARN  {char_id} not found in characters.json")
        continue
    if "display" in chars[char_id]:
        skipped += 1
        continue
    chars[char_id]["display"] = {
        "color":              color,
        "color_dark":         color_dark,
        "opacity_narration":  0.4,
        "opacity_speech":     1.0,
        "label":              label,
    }
    added += 1

with open(CHAR_FILE, "w", encoding="utf-8") as fh:
    json.dump(chars, fh, ensure_ascii=False, indent=2)

print(f"\nDone. Added display colors: {added}, already had: {skipped}")
