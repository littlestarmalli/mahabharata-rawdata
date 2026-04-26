"""
split_parva_to_folders.py
--------------------------
Reads each parva_XX_*.json in output/json/story/,
creates a sub-folder for every parva, writes one JSON per
sub-parva inside that folder, and rewrites the main parva
JSON with references (no inline chapter content).

Output layout:
  output/json/story/
    parva_01_adi_parva/
      parva_01_adi_parva.json        <- main, subparvas as refs
      subparva_01_anukramanika_parva.json
      subparva_02_parvasamgraha_parva.json
      ...
    parva_02_sabha_parva/
      ...
"""

import json
import os
import re

STORY_DIR = os.path.join(
    os.path.dirname(__file__),
    "output", "json", "story"
)


def slug(name: str) -> str:
    """Convert 'Anukramanika Parva' -> 'anukramanika_parva'."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def process_parva(json_path: str):
    with open(json_path, encoding="utf-8") as fh:
        parva = json.load(fh)

    # --- derive folder name from the file stem --------------------------
    filename = os.path.basename(json_path)          # parva_01_adi_parva.json
    stem = filename[:-5]                             # parva_01_adi_parva
    folder_path = os.path.join(STORY_DIR, stem)
    os.makedirs(folder_path, exist_ok=True)

    # --- split every sub-parva into its own file ------------------------
    subparvas_index = {}          # subparva_number -> lightweight ref dict

    for sp_key, sp_data in parva.get("subparvas", {}).items():
        sp_num = sp_data.get("subparva_number", sp_key)
        sp_name = sp_data.get("name", f"subparva_{sp_key}")

        sp_filename = f"subparva_{int(sp_num):02d}_{slug(sp_name)}.json"
        sp_rel_path = f"{stem}/{sp_filename}"
        sp_abs_path = os.path.join(folder_path, sp_filename)

        # write full sub-parva JSON
        with open(sp_abs_path, "w", encoding="utf-8") as fh:
            json.dump(sp_data, fh, ensure_ascii=False, indent=2)

        # build lightweight reference (no chapters inline)
        subparvas_index[sp_key] = {
            "subparva_number": sp_num,
            "name": sp_name,
            "source_volume": sp_data.get("source_volume"),
            "details": sp_data.get("details", {}),
            "note": sp_data.get("note", ""),
            "file": sp_rel_path,
        }

    # --- write main parva JSON (refs only, no chapter blobs) ------------
    main_parva = {
        "name": parva.get("name"),
        "parva_number": parva.get("parva_number"),
        "details": parva.get("details", {}),
        "subparvas": subparvas_index,
    }

    main_path = os.path.join(folder_path, filename)
    with open(main_path, "w", encoding="utf-8") as fh:
        json.dump(main_parva, fh, ensure_ascii=False, indent=2)

    sp_count = len(subparvas_index)
    print(f"  {stem}/  -> {sp_count} sub-parva file(s) + main JSON")


def main():
    parva_files = sorted(
        f for f in os.listdir(STORY_DIR)
        if f.startswith("parva_") and f.endswith(".json")
    )

    if not parva_files:
        print("No parva JSON files found in", STORY_DIR)
        return

    print(f"Found {len(parva_files)} parva files. Processing...\n")
    for fname in parva_files:
        process_parva(os.path.join(STORY_DIR, fname))

    print("\nDone.")


if __name__ == "__main__":
    main()
