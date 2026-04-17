"""Validate all cross-references across characters, locations, and timeline.
Checks: every @reference resolves, timeline order is continuous, years are monotonic."""


def validate(output, loc_output, tl_output):
    """Run all validation checks. Returns True if no errors found."""
    print("\n  VALIDATION:")
    errors = 0

    # Check character refs in timeline
    for evt_key, evt in tl_output.items():
        for p in evt.get("Participants", []):
            if p.startswith("@") and p not in output:
                print(f"    WARNING: Timeline {evt_key} references unknown character {p}")
                errors += 1
        loc = evt.get("Location", "")
        if loc.startswith("@") and loc not in loc_output:
            print(f"    WARNING: Timeline {evt_key} references unknown location {loc}")
            errors += 1

    # Check location refs in characters
    for ck, cv in output.items():
        kingdom = cv.get("Kingdom", "")
        if kingdom.startswith("@") and kingdom not in loc_output:
            print(f"    WARNING: Character {ck} Kingdom references unknown location {kingdom}")
            errors += 1
        for loc in cv.get("Important_Locations", []):
            if loc.startswith("@") and loc not in loc_output:
                print(f"    WARNING: Character {ck} Important_Locations references unknown location {loc}")
                errors += 1

    # Check location cross-refs
    for lk, lv in loc_output.items():
        ruler = lv.get("Ruler", "")
        if ruler.startswith("@") and ruler not in output:
            print(f"    WARNING: Location {lk} Ruler references unknown character {ruler}")
            errors += 1
        for r in lv.get("Residents", []):
            if r.startswith("@") and r not in output:
                print(f"    WARNING: Location {lk} Residents references unknown character {r}")
                errors += 1

    # Timeline order validation
    orders = [v['Order'] for v in tl_output.values()]
    if orders != list(range(1, len(orders) + 1)):
        print(f"    WARNING: Timeline order is not continuous 1..{len(orders)}")
        errors += 1
    years = [v['Year'] for v in tl_output.values()]
    for i in range(1, len(years)):
        if years[i] < years[i-1]:
            print(f"    WARNING: Timeline year goes backward at Order {i+1}: {years[i-1]} -> {years[i]}")
            errors += 1

    if errors == 0:
        print("    All cross-references valid!")
    else:
        print(f"    {errors} validation warnings found")

    return errors == 0
