"""Cross-link the 3 JSON files: add Events_Occurred to locations,
Major_Events to characters, from the timeline."""

import json


def crosslink(output, out_path, loc_output, loc_path, tl_output):
    """Add event cross-references between characters, locations, and timeline.

    Args:
        output: characters dict (modified in-place and re-saved)
        out_path: path to characters.json
        loc_output: locations dict (modified in-place and re-saved)
        loc_path: path to locations.json
        tl_output: timeline dict (read-only)
    """
    # Add Events_Occurred to locations from timeline
    for evt_key, evt in tl_output.items():
        loc_ref = evt.get("Location", "")
        if loc_ref.startswith("@"):
            loc_id = loc_ref[1:]
            if f"@{loc_id}" in loc_output:
                loc_entry = loc_output[f"@{loc_id}"]
                if "Events_Occurred" not in loc_entry:
                    loc_entry["Events_Occurred"] = []
                loc_entry["Events_Occurred"].append({"Event": evt_key})

    # Re-save locations with events
    with open(loc_path, 'w', encoding='utf-8') as f:
        json.dump(loc_output, f, ensure_ascii=False, indent=2)

    # Add Major_Events to characters from timeline
    char_events = {}
    for evt_key, evt in tl_output.items():
        for p in evt.get("Participants", []):
            if p.startswith("@"):
                ck = p[1:]
                char_events.setdefault(ck, []).append(evt_key)

    for char_key, evt_keys in char_events.items():
        full_key = f"@{char_key}"
        if full_key in output:
            output[full_key]["Major_Events"] = evt_keys

    # Re-save characters with events
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
