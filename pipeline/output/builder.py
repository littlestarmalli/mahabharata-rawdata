"""Build final JSON output for characters, locations, and timeline.
Derives children, lineage, and formats all cross-references with @ prefix."""

import json


def build_character_output(db, json_dir):
    """Build characters.json from the CharacterDB state.
    Returns (output_dict, out_path) for use by crosslinker."""
    chars = db.chars

    # Derive children from father/mother references
    children_map = {}
    for k, c in chars.items():
        if c['father'] and c['father'] in chars:
            children_map.setdefault(c['father'], [])
            if k not in children_map[c['father']]:
                children_map[c['father']].append(k)
        if c['mother'] and c['mother'] in chars:
            children_map.setdefault(c['mother'], [])
            if k not in children_map[c['mother']]:
                children_map[c['mother']].append(k)

    output = {}
    for k in sorted(chars.keys()):
        c = chars[k]
        entry = {
            "Name": c['name'],
            "Alias_names": sorted(c['aliases']),
            "Gender": c['gender'],
        }
        if c['father']:
            entry["Father"] = f"@{c['father']}"
        if c['mother']:
            entry["Mother"] = f"@{c['mother']}"
        if c['spouse']:
            my_children = children_map.get(k, [])
            spouse_keys = db.spouse_keys(c)
            spouse_children = {}
            unattributed = []
            for ch in my_children:
                ch_data = chars.get(ch, {})
                other = None
                if ch_data.get('father') == k:
                    other = ch_data.get('mother')
                elif ch_data.get('mother') == k:
                    other = ch_data.get('father')
                if other is None:
                    if ch_data.get('father') and ch_data['father'] != k and ch_data['father'] in spouse_keys:
                        other = ch_data['father']
                    elif ch_data.get('mother') and ch_data['mother'] != k and ch_data['mother'] in spouse_keys:
                        other = ch_data['mother']
                if other and other in spouse_keys:
                    spouse_children.setdefault(other, []).append(ch)
                else:
                    unattributed.append(ch)

            seen = set()
            spouse_list = []
            for s, rel in c['spouse']:
                if s not in seen:
                    if not rel:
                        s_gender = chars[s]['gender'] if s in chars else 'Unknown'
                        if s_gender == 'Female':
                            rel = 'Wife'
                        elif s_gender == 'Male':
                            rel = 'Husband'
                        else:
                            rel = 'Spouse'
                    s_entry = {f"@{s}": {
                        "Relation": rel,
                        "Children": [f"@{ch}" for ch in spouse_children.get(s, [])]
                    }}
                    spouse_list.append(s_entry)
                    seen.add(s)
            entry["Spouse"] = spouse_list

            if unattributed:
                entry["Children"] = [f"@{ch}" for ch in unattributed]
        else:
            if k in children_map:
                entry["Children"] = [f"@{ch}" for ch in children_map[k]]
        if c['caste']:
            entry["Caste"] = c['caste']
        if c['duty']:
            entry["Duty"] = c['duty']
        if c['dynasty']:
            entry["Dynasty"] = c['dynasty']
        if c['status']:
            entry["Status"] = c['status']
        if c.get('kingdom'):
            entry["Kingdom"] = f"@{c['kingdom']}"
        if c.get('political_role'):
            entry["Political_Role"] = c['political_role']
        if c.get('skills'):
            entry["Skills"] = c['skills']
        if c.get('divine_weapons'):
            entry["Divine_Weapons"] = c['divine_weapons']
        if c.get('titles'):
            entry["Titles"] = c['titles']
        if c.get('traits'):
            entry["Traits"] = c['traits']
        if c.get('character_arc'):
            entry["Character_Arc"] = c['character_arc']
        if c.get('key_relationships'):
            entry["Key_Relationships"] = c['key_relationships']
        if c.get('important_locations'):
            entry["Important_Locations"] = [f"@{loc}" for loc in c['important_locations']]
        # Auto-derive Lineage from father chain
        lineage = {}
        if c['father'] and c['father'] in chars:
            gf = chars[c['father']].get('father')
            if gf and gf in chars:
                lineage["Grandfather"] = f"@{gf}"
                ggf = chars[gf].get('father')
                if ggf and ggf in chars:
                    lineage["Great_Grandfather"] = f"@{ggf}"
        if lineage:
            entry["Lineage"] = lineage
        output[f"@{k}"] = entry

    import os
    out_path = os.path.join(json_dir, 'characters.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Stats
    total = len(output)
    with_aliases = sum(1 for v in output.values() if v.get('Alias_names'))
    with_father = sum(1 for v in output.values() if 'Father' in v)
    with_mother = sum(1 for v in output.values() if 'Mother' in v)
    with_spouse = sum(1 for v in output.values() if 'Spouse' in v)
    with_children = sum(1 for v in output.values()
                       if 'Children' in v
                       or any(ch for sp in v.get('Spouse', []) if isinstance(sp, dict)
                              for sd in sp.values() if isinstance(sd, dict)
                              for ch in sd.get('Children', [])))
    with_caste = sum(1 for v in output.values() if 'Caste' in v)
    with_duty = sum(1 for v in output.values() if 'Duty' in v)
    with_dynasty = sum(1 for v in output.values() if 'Dynasty' in v)
    with_status = sum(1 for v in output.values() if 'Status' in v)
    with_kingdom = sum(1 for v in output.values() if 'Kingdom' in v)
    with_skills = sum(1 for v in output.values() if 'Skills' in v)
    with_weapons = sum(1 for v in output.values() if 'Divine_Weapons' in v)
    with_traits = sum(1 for v in output.values() if 'Traits' in v)
    with_arc = sum(1 for v in output.values() if 'Character_Arc' in v)
    with_lineage = sum(1 for v in output.values() if 'Lineage' in v)
    with_key_rel = sum(1 for v in output.values() if 'Key_Relationships' in v)
    males = sum(1 for v in output.values() if v['Gender'] == 'Male')
    females = sum(1 for v in output.values() if v['Gender'] == 'Female')
    unknowns = sum(1 for v in output.values() if v['Gender'] == 'Unknown')
    print(f"  Total characters: {total}")
    print(f"  With aliases: {with_aliases}")
    print(f"  With Father: {with_father}, Mother: {with_mother}")
    print(f"  With Spouse: {with_spouse}")
    print(f"  With Children: {with_children}")
    print(f"  With Caste: {with_caste}, Duty: {with_duty}")
    print(f"  With Dynasty: {with_dynasty}, Status: {with_status}")
    print(f"  With Kingdom: {with_kingdom}, Skills: {with_skills}")
    print(f"  With Weapons: {with_weapons}, Traits: {with_traits}")
    print(f"  With Arc: {with_arc}, Lineage: {with_lineage}")
    print(f"  With Key Relationships: {with_key_rel}")
    print(f"  Gender - Male: {males}, Female: {females}, Unknown: {unknowns}")
    print(f"  Saved to characters.json")

    return output, out_path


def build_location_output(locations, json_dir):
    """Build locations.json from the locations dict.
    Returns (loc_output, loc_path) for use by crosslinker."""
    loc_output = {}
    for loc_id, loc in locations.items():
        entry = {"Name": loc["Name"], "Type": loc["Type"]}
        if loc.get("Region"):
            entry["Region"] = loc["Region"]
        if loc.get("Sub_Locations"):
            entry["Sub_Locations"] = loc["Sub_Locations"]
        if loc.get("Nearby_Locations"):
            entry["Nearby_Locations"] = loc["Nearby_Locations"]
        if loc.get("Ruler"):
            entry["Ruler"] = loc["Ruler"]
        if loc.get("Famous_For"):
            entry["Famous_For"] = loc["Famous_For"]
        if loc.get("Residents"):
            entry["Residents"] = loc["Residents"]
        if loc.get("Geography"):
            entry["Geography"] = loc["Geography"]
        if loc.get("Coordinates"):
            entry["Coordinates"] = loc["Coordinates"]
        if loc.get("Mythical"):
            entry["Mythical"] = True
        if loc.get("Modern_Equivalent"):
            entry["Modern_Equivalent"] = loc["Modern_Equivalent"]
        if loc.get("Nearby_Distances_km"):
            entry["Nearby_Distances_km"] = loc["Nearby_Distances_km"]
        if loc.get("Notes"):
            entry["Notes"] = loc["Notes"]
        loc_output[f"@{loc_id}"] = entry

    import os
    loc_path = os.path.join(json_dir, 'locations.json')
    with open(loc_path, 'w', encoding='utf-8') as f:
        json.dump(loc_output, f, ensure_ascii=False, indent=2)
    print(f"\n  LOCATIONS: {len(loc_output)} locations saved to locations.json")
    with_coords = sum(1 for v in loc_output.values() if 'Coordinates' in v)
    mythical = sum(1 for v in loc_output.values() if v.get('Mythical'))
    with_distances = sum(1 for v in loc_output.values() if 'Nearby_Distances_km' in v)
    print(f"    With coordinates: {with_coords}, Mythical: {mythical}")
    print(f"    With nearby distances: {with_distances}")
    types = {}
    for v in loc_output.values():
        t = v['Type']
        types[t] = types.get(t, 0) + 1
    for t in sorted(types):
        print(f"    {t}: {types[t]}")

    return loc_output, loc_path


def build_timeline_output(timeline, json_dir):
    """Build timeline.json from the timeline dict.
    Returns (tl_output, tl_path) for use by crosslinker."""
    tl_output = {}
    for evt_id, evt in timeline.items():
        entry = {
            "Order": evt["Order"],
            "Year": evt["Year"],
            "Era": evt["Era"],
            "Event_Name": evt["Event_Name"],
            "Description": evt["Description"],
        }
        if evt.get("Location"):
            entry["Location"] = evt["Location"]
        if evt.get("Participants"):
            entry["Participants"] = evt["Participants"]
        if evt.get("Outcome"):
            entry["Outcome"] = evt["Outcome"]
        if evt.get("Consequences"):
            entry["Consequences"] = evt["Consequences"]
        if evt.get("Related_Events"):
            entry["Related_Events"] = evt["Related_Events"]
        if evt.get("Sources"):
            entry["Sources"] = evt["Sources"]
        tl_output[f"@{evt_id}"] = entry

    import os
    tl_path = os.path.join(json_dir, 'timeline.json')
    with open(tl_path, 'w', encoding='utf-8') as f:
        json.dump(tl_output, f, ensure_ascii=False, indent=2)
    print(f"\n  TIMELINE: {len(tl_output)} events saved to timeline.json")
    era_counts = {}
    for v in tl_output.values():
        e = v['Era']
        era_counts[e] = era_counts.get(e, 0) + 1
    for e, c in sorted(era_counts.items()):
        print(f"    {e}: {c}")

    return tl_output, tl_path
