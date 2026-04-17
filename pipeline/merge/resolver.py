"""Merge duplicate characters, resolve conflicts, clean references.
Hardcoded merge map for known spelling variants and aliases."""

from pipeline.auto.name_extractor import is_valid_name, NOISE_WORDS


# Known spelling variants / aliases -> canonical key
# Format: { misspelling_key: correct_key }
MERGE_MAP = {
    'bhisma': 'bhishma', 'dhritarasthra': 'dhritarashtra',
    'dritarashtra': 'dhritarashtra', 'dhritrarashtra': 'dhritarashtra',
    'dhritrashtra': 'dhritarashtra',
    'droupadi': 'draupadi', 'kounteya': 'arjuna',
    'krisha': 'krishna', 'kourava': 'duryodhana',
    'yudhisthira': 'yudhishthira', 'yarkandeya': 'markandeya',
    'baladeva': 'balarama', 'bhimasena': 'bhima',
    'govinda': 'krishna', 'maheshvara': 'shiva',
    'bhagavan': 'krishna', 'hutashana': 'agni',
    'sthanu': 'shiva', 'rudra': 'shiva',
    'pritha': 'kunti', 'saindhava': 'jayadratha',
    'souti': 'ugrasrava',
    'vasudeva': 'krishna', 'vaishravana': 'kubera',
    'vaivasvata': 'manu', 'vivasvata': 'surya',
    'madhusudana': 'krishna', 'vaasudeva': 'krishna',
    'krishnaa': 'draupadi', 'sharadvata': 'kripa',
    'goutama': 'kripa', 'mithila': 'janaka',
    'vashishtha': 'vasishtha', 'hardikya': 'kritavarma',
    'yuyudhana': 'satyaki', 'satvata': 'satyaki',
    'vaikartana': 'karna', 'varshneya': 'krishna',
    'dasharha': 'krishna', 'pundarikaksha': 'krishna',
    'shouri': 'krishna', 'purushottama': 'krishna',
    'maghavan': 'indra', 'shankara': 'shiva',
    'parshata': 'drupada', 'dvaipayana': 'vyasa',
    'nishadha': 'nala', 'punyashloka': 'nala',
    'bahuka': 'nala', 'mandhatar': 'mandhata',
    'agasti': 'agastya', 'kushika': 'vishvamitra',
    'kouravya': 'yudhishthira',
    'pandaveya': 'yudhishthira',
    'anakadundubhi': 'vasudeva_father',
    # Disambiguated keys
    'chitrangada': 'chitrangada_kuru',
    'lakshmana': 'lakshmana_kaurava',
    'prishata': 'prishata',
}


def merge_and_resolve(db):
    """Phase 3: Merge duplicate characters, remove noise, clean references."""
    chars = db.chars

    for old_k, new_k in MERGE_MAP.items():
        if old_k in chars and new_k in chars and old_k != new_k:
            chars[new_k]['aliases'].add(chars[old_k]['name'])
            chars[new_k]['aliases'].update(chars[old_k]['aliases'])
            if not chars[new_k]['father'] and chars[old_k]['father']:
                chars[new_k]['father'] = chars[old_k]['father']
            if not chars[new_k]['mother'] and chars[old_k]['mother']:
                chars[new_k]['mother'] = chars[old_k]['mother']
            chars[new_k]['siblings'].update(chars[old_k]['siblings'])
            for sp_tuple in chars[old_k]['spouse']:
                if sp_tuple[0] not in db.spouse_keys(chars[new_k]):
                    chars[new_k]['spouse'].append(sp_tuple)
            if chars[new_k]['gender'] == 'Unknown':
                chars[new_k]['gender'] = chars[old_k]['gender']
            if not chars[new_k]['caste'] and chars[old_k]['caste']:
                chars[new_k]['caste'] = chars[old_k]['caste']
            if not chars[new_k]['duty'] and chars[old_k]['duty']:
                chars[new_k]['duty'] = chars[old_k]['duty']
            if not chars[new_k]['dynasty'] and chars[old_k]['dynasty']:
                chars[new_k]['dynasty'] = chars[old_k]['dynasty']
            if not chars[new_k]['status'] and chars[old_k]['status']:
                chars[new_k]['status'] = chars[old_k]['status']
            # Update all references pointing to old key
            for k, c in chars.items():
                if c['father'] == old_k:
                    c['father'] = new_k
                if c['mother'] == old_k:
                    c['mother'] = new_k
                if old_k in c['siblings']:
                    c['siblings'].discard(old_k)
                    if k != new_k:
                        c['siblings'].add(new_k)
                if old_k in db.spouse_keys(c):
                    c['spouse'] = [(new_k, r) if s == old_k else (s, r) for s, r in c['spouse']]
                    if k == new_k:
                        c['spouse'] = [(s, r) for s, r in c['spouse'] if s != new_k]
            del chars[old_k]

    # Remove noise entries
    for k in list(chars.keys()):
        if (chars[k]['name'] in NOISE_WORDS
            or chars[k]['name'].lower() in NOISE_WORDS
            or not is_valid_name(chars[k]['name'])):
            for k2, c2 in chars.items():
                if c2['father'] == k:
                    c2['father'] = None
                if c2['mother'] == k:
                    c2['mother'] = None
                c2['siblings'].discard(k)
                c2['spouse'] = [(s, r) for s, r in c2['spouse'] if s != k]
            del chars[k]

    # Clean self-references and aliases
    for k, c in chars.items():
        c['siblings'].discard(k)
        c['spouse'] = [(s, r) for s, r in c['spouse'] if s != k]
        if c['father'] == k:
            c['father'] = None
        if c['mother'] == k:
            c['mother'] = None
        c['aliases'].discard(c['name'])
        c['aliases'] = {a for a in c['aliases'] if is_valid_name(a)}

    # Validate references: remove dangling keys
    all_keys = set(chars.keys())
    for k, c in chars.items():
        if c['father'] and c['father'] not in all_keys:
            c['father'] = None
        if c['mother'] and c['mother'] not in all_keys:
            c['mother'] = None
        c['siblings'] = {s for s in c['siblings'] if s in all_keys}
        c['spouse'] = [(s, r) for s, r in c['spouse'] if s in all_keys]

    # Remove spouse links that conflict with parent-child
    for k, c in chars.items():
        bad_spouses = set()
        for sp, _rel in c['spouse']:
            if sp in chars and (chars[sp]['father'] == k or chars[sp]['mother'] == k):
                bad_spouses.add(sp)
            if c['father'] == sp or c['mother'] == sp:
                bad_spouses.add(sp)
        c['spouse'] = [(s, r) for s, r in c['spouse'] if s not in bad_spouses]
        for sp in bad_spouses:
            if sp in chars:
                chars[sp]['spouse'] = [(s, r) for s, r in chars[sp]['spouse'] if s != k]

    # Remove circular parent references
    for k, c in chars.items():
        if c['father'] and c['father'] in chars:
            if chars[c['father']]['father'] == k:
                chars[c['father']]['father'] = None
        if c['mother'] and c['mother'] in chars:
            if chars[c['mother']]['mother'] == k:
                chars[c['mother']]['mother'] = None
