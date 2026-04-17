"""Character data model — the add()/ensure() functions and internal state.
This is the core data structure that all phases write into."""


class CharacterDB:
    """In-memory character database with add/ensure/merge operations."""

    def __init__(self):
        self.chars = {}  # key -> dict
        self._alias_map = {}

    def _key(self, name):
        return name.strip().lower().replace(' ', '_')

    def add(self, primary, *, aliases=None, father=None, mother=None,
            siblings=None, spouse=None, gender=None,
            caste=None, duty=None, dynasty=None, status=None,
            kingdom=None, political_role=None,
            skills=None, divine_weapons=None, titles=None,
            traits=None, character_arc=None,
            key_relationships=None, important_locations=None):
        """Add or update a character entry.
        spouse: list of strings OR list of (name, relation) tuples.
        Plain strings default to relation 'Wife'/'Husband' based on gender."""
        k = self._key(primary)
        if k not in self.chars:
            self.chars[k] = {
                'name': primary.strip(), 'aliases': set(),
                'father': None, 'mother': None,
                'siblings': set(), 'spouse': [],
                'gender': 'Unknown',
                'caste': '', 'duty': '', 'dynasty': '', 'status': '',
                'kingdom': '', 'political_role': '',
                'skills': [], 'divine_weapons': [], 'titles': [],
                'traits': [], 'character_arc': [],
                'key_relationships': [], 'important_locations': [],
            }
        c = self.chars[k]
        if aliases:
            for a in aliases:
                a = a.strip()
                if a and a != c['name']:
                    c['aliases'].add(a)
        if father:
            c['father'] = self._key(father)
        if mother:
            c['mother'] = self._key(mother)
        if siblings:
            for s in siblings:
                c['siblings'].add(self._key(s))
        if spouse:
            for sp in spouse:
                if isinstance(sp, tuple):
                    sp_name, sp_rel = sp
                else:
                    sp_name, sp_rel = sp, None
                sk = self._key(sp_name)
                existing = [i for i, (s, r) in enumerate(c['spouse']) if s == sk]
                if existing:
                    if sp_rel and not c['spouse'][existing[0]][1]:
                        c['spouse'][existing[0]] = (sk, sp_rel)
                else:
                    c['spouse'].append((sk, sp_rel))
        if gender and gender != 'Unknown':
            c['gender'] = gender
        if caste and not c['caste']:
            c['caste'] = caste
        if duty and not c['duty']:
            c['duty'] = duty
        if dynasty and not c['dynasty']:
            c['dynasty'] = dynasty
        if status and not c['status']:
            c['status'] = status
        if kingdom and not c['kingdom']:
            c['kingdom'] = kingdom
        if political_role and not c['political_role']:
            c['political_role'] = political_role
        if skills:
            c['skills'] = list(dict.fromkeys(c['skills'] + skills))
        if divine_weapons:
            c['divine_weapons'] = list(dict.fromkeys(c['divine_weapons'] + divine_weapons))
        if titles:
            c['titles'] = list(dict.fromkeys(c['titles'] + titles))
        if traits:
            c['traits'] = list(dict.fromkeys(c['traits'] + traits))
        if character_arc:
            c['character_arc'] = list(dict.fromkeys(c['character_arc'] + character_arc))
        if key_relationships:
            existing_pairs = {(kr['With'], kr['Type']) for kr in c['key_relationships']}
            for kr in key_relationships:
                pair = (kr['With'], kr['Type'])
                if pair not in existing_pairs:
                    c['key_relationships'].append(kr)
                    existing_pairs.add(pair)
        if important_locations:
            c['important_locations'] = list(dict.fromkeys(
                c['important_locations'] + important_locations))

    def spouse_keys(self, c):
        """Return list of spouse keys from the (key, relation) tuple list."""
        return [s for s, r in c['spouse']]

    def rebuild_alias_map(self):
        """Rebuild the alias->primary key lookup."""
        self._alias_map.clear()
        for k, c in self.chars.items():
            for a in c['aliases']:
                ak = self._key(a)
                if ak != k:
                    self._alias_map[ak] = k

    def ensure(self, name, gender=None):
        """Ensure a character exists (create minimal stub if not).
        Returns the resolved key."""
        k = self._key(name)
        if k in self._alias_map:
            parent = self._alias_map[k]
            if gender and gender != 'Unknown' and parent in self.chars:
                if self.chars[parent]['gender'] == 'Unknown':
                    self.chars[parent]['gender'] = gender
            return parent
        if k not in self.chars:
            self.chars[k] = {
                'name': name.strip(), 'aliases': set(),
                'father': None, 'mother': None,
                'siblings': set(), 'spouse': [],
                'gender': gender or 'Unknown',
                'caste': '', 'duty': '', 'dynasty': '', 'status': '',
                'kingdom': '', 'political_role': '',
                'skills': [], 'divine_weapons': [], 'titles': [],
                'traits': [], 'character_arc': [],
                'key_relationships': [], 'important_locations': [],
            }
        elif gender and gender != 'Unknown' and self.chars[k]['gender'] == 'Unknown':
            self.chars[k]['gender'] = gender
        return k
