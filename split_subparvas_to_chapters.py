"""
split_subparvas_to_chapters.py
Splits each subparva JSON into:
  subparva_NN_name/
    subparva_NN_name.json          — metadata + chapter file refs
    chapter_NNN.json               — one per chapter (raw paragraphs)
    chapter_NNN_tagged.json        — one per chapter (tagged paragraphs)

Also updates the parva main JSON to point to folder structure.
"""

import json, os, sys
from pathlib import Path

STORY_DIR = Path("output/json/story")


def split_one_subparva(sp_path: Path, is_tagged: bool):
    """Split a subparva JSON into per-chapter files inside a folder."""
    with open(sp_path, encoding="utf-8") as f:
        sp = json.load(f)

    chapters = sp.pop("chapters", {})
    if not chapters:
        print(f"  SKIP {sp_path.name} (no chapters)")
        return None

    # Determine folder name (strip _tagged suffix for folder)
    base_name = sp_path.stem
    if is_tagged:
        base_name = base_name.replace("_tagged", "")
    folder = sp_path.parent / base_name
    folder.mkdir(exist_ok=True)

    suffix = "_tagged" if is_tagged else ""

    # Write each chapter
    chapter_refs = {}
    for ch_key, ch_data in sorted(chapters.items(), key=lambda x: int(x[0])):
        ch_num = int(ch_key)
        ch_filename = f"chapter_{ch_num:03d}{suffix}.json"
        ch_path = folder / ch_filename

        ch_out = {
            "chapter_number": ch_num,
            "global_number": ch_data.get("global_number"),
            "local_number": ch_data.get("local_number"),
            "num_shlokas": ch_data.get("num_shlokas"),
            "paragraphs": ch_data.get("paragraphs", {}),
        }

        with open(ch_path, "w", encoding="utf-8") as f:
            json.dump(ch_out, f, ensure_ascii=False, indent=2)

        chapter_refs[ch_key] = {
            "chapter_number": ch_num,
            "global_number": ch_data.get("global_number"),
            "local_number": ch_data.get("local_number"),
            "num_shlokas": ch_data.get("num_shlokas"),
            "file": f"{base_name}/{ch_filename}",
        }

    # Write main subparva JSON (metadata + chapter refs, no inline content)
    sp["chapters"] = chapter_refs
    main_filename = f"{base_name}{suffix}.json"
    main_path = folder / main_filename
    with open(main_path, "w", encoding="utf-8") as f:
        json.dump(sp, f, ensure_ascii=False, indent=2)

    return base_name, main_filename


def update_parva_json(parva_json_path: Path, subparva_folder_map: dict):
    """Update parva main JSON with new subparva file paths pointing to folders."""
    with open(parva_json_path, encoding="utf-8") as f:
        parva = json.load(f)

    parva_folder = parva_json_path.parent.name

    for sp_key, sp_data in parva.get("subparvas", {}).items():
        old_file = sp_data.get("file", "")
        # Extract base name from old path: parva_01_adi_parva/subparva_01_xxx.json
        old_basename = Path(old_file).stem
        if old_basename in subparva_folder_map:
            new_main = subparva_folder_map[old_basename]
            sp_data["file"] = f"{parva_folder}/{new_main}"

    with open(parva_json_path, "w", encoding="utf-8") as f:
        json.dump(parva, f, ensure_ascii=False, indent=2)


def main():
    parva_filter = None
    if "--parva" in sys.argv:
        idx = sys.argv.index("--parva")
        parva_filter = int(sys.argv[idx + 1])

    parva_dirs = sorted(STORY_DIR.glob("parva_*"))
    if not parva_dirs:
        print("No parva directories found.")
        return

    total_chapters = 0

    for parva_dir in parva_dirs:
        if not parva_dir.is_dir():
            continue
        parva_num = int(parva_dir.name.split("_")[1])
        if parva_filter and parva_num != parva_filter:
            continue

        print(f"\n=== {parva_dir.name} ===")
        subparva_folder_map = {}  # base_name -> folder/main_filename

        # Process raw subparva files
        raw_files = sorted(parva_dir.glob("subparva_*[!d].json"))  # exclude _tagged
        raw_files = [f for f in raw_files if "_tagged" not in f.name]
        for sp_file in raw_files:
            result = split_one_subparva(sp_file, is_tagged=False)
            if result:
                base_name, main_filename = result
                n_chapters = len(list((parva_dir / base_name).glob("chapter_*[!d].json")))
                n_chapters = len([f for f in (parva_dir / base_name).glob("chapter_*.json") if "_tagged" not in f.name])
                total_chapters += n_chapters
                subparva_folder_map[base_name] = f"{base_name}/{main_filename}"
                print(f"  OK  {base_name}/ ({n_chapters} chapters)")

        # Process tagged subparva files
        tagged_files = sorted(parva_dir.glob("subparva_*_tagged.json"))
        for sp_file in tagged_files:
            result = split_one_subparva(sp_file, is_tagged=True)
            if result:
                base_name, main_filename = result
                n_tagged = len([f for f in (parva_dir / base_name).glob("chapter_*_tagged.json")])
                print(f"  OK  {base_name}/ (+{n_tagged} tagged)")

        # Update parva main JSON
        parva_json = parva_dir / f"{parva_dir.name}.json"
        if parva_json.exists() and subparva_folder_map:
            update_parva_json(parva_json, subparva_folder_map)
            print(f"  Updated {parva_json.name}")

    print(f"\nDone. Split {total_chapters} total chapter files.")


if __name__ == "__main__":
    main()
