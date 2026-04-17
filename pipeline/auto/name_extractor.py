"""Auto-extract character names and relationships from text using regex patterns.
Priority: auto-extraction first, hardcoded data overrides where needed."""

import os
import re

from pipeline.config import NUM_VOLUMES


# Words that look like names but aren't characters
SKIP_WORDS = {
    'the','that','this','these','those','which','where','when','what','also',
    'here','there','thus','hence','therefore','however','since','with','from',
    'into','onto','about','above','below','between','through','during','before',
    'after','meaning','means','called','known','because','although','though',
    'only','even','just','more','very','much','many','some','most','other',
    'each','every','been','being','having','would','could','should','might',
    'shall','will','can','may','must','used','one','two','three','four','five',
    'not','but','and','for','are','was','were','has','had','his','her','its',
    'who','whom','why','how','all','any','few','own','same','such','than',
    'too','according','refers','reference','literally','translated','been',
    'another','sometimes','generally','probably','perhaps','certain','various',
    'different','several','among','usually','often','name','word','text',
    'section','chapter','volume','parva','still','like','described',
    'mentioned','simply','particularly','especially','speci',
    'tell','listen','look','behold','hear','please','both','together',
    'today','whether','wishing','desiring','knowing','seeing','hearing',
    'thinking','following','using','depending','surrounded','otherwise',
    'swiftly','instead','thereafter','thereupon','despite','overcome',
    'oppressed','driven','struck','protected','arise','accept','give',
    'take','come','make','show','kill','protect','your','down',
}

# Capitalized words that appear in text but are not character names
NOISE_WORDS = {
    'Accept','Action','Agreeable','Aimed','Alas','Always','Among','Animals',
    'Arise','Associated','Behold','Bengal','Birth','Blossoms','Both','Bought',
    'Bright','Come','Commodity','Completed','Conduct','Confused','Consciousness',
    'Contentment','Cold','Dark','Death','Depending','Desiring','Despite',
    'Dice','District','Divine','Driven','During','Easy','Elephants',
    'Embryo','Extremely','Festival','Fire','Follow','Food','Forgiveness',
    'Fortunate','Fruit','Garment','Ghee','Give','Given','Gold','Great',
    'Hair','Have','Hear','Hearing','Heaven','Honey','Immobile','Immutable',
    'Impossible','Important','Incognito','Indestructible','Instead','Island',
    'Kill','Killing','King','Know','Knowing','Knowledge','Large','Learned',
    'Less','Life','Like','Listen','Long','Look','Love','Made','Make',
    'Meditation','Metals','Mortar','Mount','Necessary','Nothing','Observed',
    'Offered','Oppressed','Otherwise','Overcome','Parva','People','Performed',
    'Permanent','Person','Pillar','Please','Plough','Practices','Protect',
    'Protected','Properties','Prosperity','Rathas','Renunciation','Relatives',
    'Sages','Seat','Seed','Seeing','Shame','She','Shed','Show','Shloka',
    'Sound','Space','Species','Spots','Spring','Status','Stone','Struck',
    'Suggestion','Surrounded','Swiftly','Symmetric','Take','Taking','Tell',
    'Thereafter','Thereupon','Thinking','Thousands','Thrown','Today','Touch',
    'Towards','Tradition','Tree','Truth','True','Under','Victory','Voice',
    'Water','Weapon','West','Whether','Wishing','Wombs','Worst','Your',
    'Adharma','Adityas','Ahamkara','Amlavetasa','Andhakas','Artha',
    'Bharatas','Brahmana','Brahmanas','Chedis','Chhanda','Chapter',
    'Divyastras','Edukas','FLowers','Ganas','Gangasagar','Girivraja',
    'Himalayas','India','Indras','Kekayas','Kouravas','Krishnas',
    'Kshatriyas','Kunapa','Kupya','Lokapalas','Maharatha','Maruts',
    'Matsyas','Miscegenation','Nagakeshara','Nakshatras','Nirgundi',
    'Padma','Pamshu','Panchalas','Pandaveyas','Pandavas','Pandus',
    'Parthas','Piyala','Pleiades','Pranayama','Preceptor','Principle',
    'Pushya','Prakriti','Purusha','Rain','Rajagriha','Red','Rudras',
    'Sabhasada','Sadhyas','Samskara','Sarisrikva','Saturn','Sattva',
    'Shvetakakiya','Six','Snayu','Somakas','Srinjayas','Sushumna',
    'Tamas-type','Tamarind','Trigarta','Trigartas','Twelve','Undesir-',
    'Varga','Varuthas','Vedangas','Venus','Vishvadevas','Vrishnis',
    'Yugas','Adarshana','Vinasana','Stambamitra','Prana','Satya','Sama',
    'Kurus','Brother','Mother','Father','Son','Something','Every',
    'Earlier','Everyone','Everything','Metaphorically','Others','Their',
    'Then','They','Time','Whatever','While','Without','You','Suta',
    'Mani','Maniman','Manovaha','Paka','Battle','Down',
    'Gandiva','Vidarbha','Sacriﬁce',
    'Difﬁcult','Near','Lineage','Once','Maha','Veda','Vedas',
    'Vasus',
    'blossoms','tree','love','she','district','properties','Kama',
    'Apaya','nagakeshara','piyala','nirgundi','Poulomi',
    'Pluto','Pandava',
}


def is_valid_name(n):
    """Check if a string is likely a character name (not a common word)."""
    return (n and len(n) >= 3 and n not in NOISE_WORDS
            and n.lower() not in SKIP_WORDS and not n.endswith('-'))


def extract_names_and_relationships(db, base_dir):
    """Auto-extract character names and relationships from extracted text.

    Args:
        db: CharacterDB instance
        base_dir: path to output/volumes/ directory
    """
    chars = db.chars

    # Load all text
    all_ch_text = ''
    all_fn_text = ''
    for v in range(1, NUM_VOLUMES + 1):
        all_ch_text += open(os.path.join(base_dir, f'volume_{v}_chapters.txt'),
                            encoding='utf-8').read()
        all_fn_text += open(os.path.join(base_dir, f'volume_{v}_footnotes.txt'),
                            encoding='utf-8').read()

    # --- Extract names from footnotes ---
    fn_entries = re.findall(r'(?:^|\n)(\d+)\s+((?:(?!\n\d+\s).)*)', all_fn_text, re.S)
    for num, text in fn_entries:
        text = re.sub(r'\s+', ' ', text).strip()
        # "Name. He/She..." pattern
        m = re.match(r'^([A-Z][\w-]+)\.\s+(?:He|She|It|The|This|One|A )', text)
        if m and is_valid_name(m.group(1)):
            g = 'Female' if '. She ' in text[:50] else ('Male' if '. He ' in text[:50] else None)
            db.ensure(m.group(1), g)
        # "X's son/daughter/wife..." pattern
        for pm in re.finditer(r"([A-Z][\w'-]+)\u2019s\s+(?:son|daughter|wife|brother|sister|father|mother|husband)", text):
            if is_valid_name(pm.group(1)):
                db.ensure(pm.group(1))
        # "son/daughter/wife of X"
        for pm in re.finditer(r"(?:son|daughter|wife|brother|sister) of\s+([A-Z][\w'-]+)", text):
            if is_valid_name(pm.group(1)):
                db.ensure(pm.group(1))
        # "King/Queen X of Y"
        m2 = re.match(r'^([A-Z][\w-]+),?\s+(?:the\s+)?(?:king|queen|prince|princess|ruler|chief) of\s+([A-Z][\w-]+)', text)
        if m2:
            if is_valid_name(m2.group(1)):
                db.ensure(m2.group(1), 'Male' if 'king' in text[:40].lower() else None)
        # "also known as" / "also called"
        for m3 in re.finditer(r"([A-Z][\w-]+)[\s,]+(?:is\s+)?also\s+(?:known|called)\s+as\s+([A-Z][\w-]+)", text, re.I):
            a, b = m3.group(1), m3.group(2)
            if is_valid_name(a) and is_valid_name(b):
                ka = db._alias_map.get(db._key(a), db._key(a))
                kb = db._alias_map.get(db._key(b), db._key(b))
                if ka in chars:
                    chars[ka]['aliases'].add(b)
                elif kb in chars:
                    chars[kb]['aliases'].add(a)
                else:
                    resolved = db.ensure(a)
                    chars[resolved]['aliases'].add(b)

    # --- Extract names from chapters ---
    # Speech: 'Name said/spoke/asked/...'
    said_names = re.findall(
        r"[\u2018\u2019']([A-Z][a-z]{2,})\s+(?:said|spoke|asked|replied|answered|told|addressed|continued|recounted)",
        all_ch_text)
    for n in set(said_names):
        if is_valid_name(n):
            db.ensure(n)

    # Vocative: "O Name!" (count >= 5)
    voc_counts = {}
    for n in re.findall(r"O\s+([A-Z][a-z]{2,})!", all_ch_text):
        voc_counts[n] = voc_counts.get(n, 0) + 1
    for n, c in voc_counts.items():
        if c >= 5 and is_valid_name(n):
            db.ensure(n)

    # Titled: "King/Prince/Sage Name" (count >= 3)
    titled_counts = {}
    for n in re.findall(r"(?:King|Prince|Sage|Rishi|Queen|Princess|Maharaja)\s+([A-Z][a-z]{2,})", all_ch_text):
        titled_counts[n] = titled_counts.get(n, 0) + 1
    for n, c in titled_counts.items():
        if c >= 3 and is_valid_name(n):
            g = 'Female' if re.search(r"(?:Queen|Princess)\s+" + re.escape(n), all_ch_text) else 'Male'
            db.ensure(n, g)

    # Relationship from chapters: "Name's son/daughter/wife..."
    ch_rel_counts = {}
    for n in re.findall(r"([A-Z][a-z]{2,})\u2019s\s+(?:son|daughter|wife|brother|sister|father|mother|husband)", all_ch_text):
        ch_rel_counts[n] = ch_rel_counts.get(n, 0) + 1
    for n, c in ch_rel_counts.items():
        if c >= 3 and is_valid_name(n):
            db.ensure(n)

    # High-frequency proper nouns (>= 50 occurrences)
    caps_counts = {}
    for n in re.findall(r'\b([A-Z][a-z]{3,})\b', all_ch_text):
        caps_counts[n] = caps_counts.get(n, 0) + 1
    for n, c in caps_counts.items():
        if c >= 50 and is_valid_name(n):
            db.ensure(n)

    # --- Extract relationships from chapter text ---
    # "X, the son/daughter of Y"
    for m in re.finditer(r"([A-Z][a-z]{2,}),?\s+(?:the\s+)?son\s+of\s+([A-Z][a-z]{2,})", all_ch_text):
        child, parent = m.group(1), m.group(2)
        if is_valid_name(child) and is_valid_name(parent):
            ck = db.ensure(child, 'Male')
            pk = db.ensure(parent, 'Male')
            if not chars[ck]['father']:
                chars[ck]['father'] = pk

    for m in re.finditer(r"([A-Z][a-z]{2,}),?\s+(?:the\s+)?daughter\s+of\s+([A-Z][a-z]{2,})", all_ch_text):
        child, parent = m.group(1), m.group(2)
        if is_valid_name(child) and is_valid_name(parent):
            ck = db.ensure(child, 'Female')
            pk = db.ensure(parent)
            if not chars[ck]['father']:
                chars[ck]['father'] = pk

    # "X's wife Y"
    for m in re.finditer(r"([A-Z][a-z]{2,})\u2019s\s+wife,?\s+([A-Z][a-z]{2,})", all_ch_text):
        husband, wife = m.group(1), m.group(2)
        if is_valid_name(husband) and is_valid_name(wife):
            hk = db.ensure(husband, 'Male')
            wk = db.ensure(wife, 'Female')
            if wk not in db.spouse_keys(chars[hk]):
                chars[hk]['spouse'].append((wk, 'Wife'))
            if hk not in db.spouse_keys(chars[wk]):
                chars[wk]['spouse'].append((hk, 'Husband'))

    # "X's brother Y"
    for m in re.finditer(r"([A-Z][a-z]{2,})\u2019s\s+brother,?\s+([A-Z][a-z]{2,})", all_ch_text):
        a, b = m.group(1), m.group(2)
        if is_valid_name(a) and is_valid_name(b):
            ak = db.ensure(a, 'Male')
            bk = db.ensure(b, 'Male')
            chars[ak]['siblings'].add(bk)
            chars[bk]['siblings'].add(ak)

    # "X's sister Y"
    for m in re.finditer(r"([A-Z][a-z]{2,})\u2019s\s+sister,?\s+([A-Z][a-z]{2,})", all_ch_text):
        a, b = m.group(1), m.group(2)
        if is_valid_name(a) and is_valid_name(b):
            ak = db.ensure(a)
            bk = db.ensure(b, 'Female')
            chars[ak]['siblings'].add(bk)
            chars[bk]['siblings'].add(ak)

    # "X's mother Y" / "X's father Y"
    for m in re.finditer(r"([A-Z][a-z]{2,})\u2019s\s+mother,?\s+([A-Z][a-z]{2,})", all_ch_text):
        child, mother = m.group(1), m.group(2)
        if is_valid_name(child) and is_valid_name(mother):
            ck = db.ensure(child)
            mk = db.ensure(mother, 'Female')
            if not chars[ck]['mother']:
                chars[ck]['mother'] = mk

    for m in re.finditer(r"([A-Z][a-z]{2,})\u2019s\s+father,?\s+([A-Z][a-z]{2,})", all_ch_text):
        child, father = m.group(1), m.group(2)
        if is_valid_name(child) and is_valid_name(father):
            ck = db.ensure(child)
            fk = db.ensure(father, 'Male')
            if not chars[ck]['father']:
                chars[ck]['father'] = fk

    # --- Extract relationships from footnotes ---
    for num, text in fn_entries:
        text = re.sub(r'\s+', ' ', text).strip()
        for m in re.finditer(r"([A-Z][a-z]{2,})\s+was\s+(?:the\s+)?(?:son|child)\s+of\s+([A-Z][a-z]{2,})", text):
            child, parent = m.group(1), m.group(2)
            if is_valid_name(child) and is_valid_name(parent):
                ck = db.ensure(child, 'Male')
                pk = db.ensure(parent)
                if not chars[ck]['father']:
                    chars[ck]['father'] = pk
        for m in re.finditer(r"([A-Z][a-z]{2,})\s+was\s+(?:the\s+)?daughter\s+of\s+([A-Z][a-z]{2,})", text):
            child, parent = m.group(1), m.group(2)
            if is_valid_name(child) and is_valid_name(parent):
                ck = db.ensure(child, 'Female')
                pk = db.ensure(parent)
                if not chars[ck]['father']:
                    chars[ck]['father'] = pk
        for m in re.finditer(r"([A-Z][a-z]{2,})\s+was\s+(?:the\s+)?wife\s+of\s+([A-Z][a-z]{2,})", text):
            wife, husband = m.group(1), m.group(2)
            if is_valid_name(wife) and is_valid_name(husband):
                wk = db.ensure(wife, 'Female')
                hk = db.ensure(husband, 'Male')
                if hk not in db.spouse_keys(chars[wk]):
                    chars[wk]['spouse'].append((hk, 'Husband'))
                if wk not in db.spouse_keys(chars[hk]):
                    chars[hk]['spouse'].append((wk, 'Wife'))
        for m in re.finditer(r"([A-Z][a-z]{2,})\u2019s\s+son,?\s+([A-Z][a-z]{2,})", text):
            parent, child = m.group(1), m.group(2)
            if is_valid_name(parent) and is_valid_name(child):
                pk = db.ensure(parent)
                ck = db.ensure(child, 'Male')
                if not chars[ck]['father']:
                    chars[ck]['father'] = pk

    return all_ch_text  # return for duty_extractor use


def extract_duty_caste(db, all_ch_text):
    """Auto-extract Duty and Caste from 'King X', 'Sage X' patterns."""
    chars = db.chars

    duty_patterns = [
        (r"\bKing\s+([A-Z][a-z]{2,})", "King", "Kshatriya"),
        (r"\bQueen\s+([A-Z][a-z]{2,})", "Queen", "Kshatriya"),
        (r"\bPrince\s+([A-Z][a-z]{2,})", "Prince", "Kshatriya"),
        (r"\bPrincess\s+([A-Z][a-z]{2,})", "Princess", "Kshatriya"),
        (r"\bSage\s+([A-Z][a-z]{2,})", "Sage", "Brahmin"),
        (r"\bRishi\s+([A-Z][a-z]{2,})", "Sage", "Brahmin"),
        (r"\bMaharaja\s+([A-Z][a-z]{2,})", "King", "Kshatriya"),
    ]
    for pat, duty_val, caste_val in duty_patterns:
        for m in re.finditer(pat, all_ch_text):
            name = m.group(1)
            k = db._alias_map.get(db._key(name), db._key(name))
            if k in chars:
                if not chars[k]['duty']:
                    chars[k]['duty'] = duty_val
                if not chars[k]['caste']:
                    chars[k]['caste'] = caste_val

    # "king of X" -> dynasty extraction
    for m in re.finditer(r"([A-Z][a-z]{2,}),?\s+(?:the\s+)?king\s+of\s+([A-Z][a-z]{2,})", all_ch_text):
        name, place = m.group(1), m.group(2)
        k = db._alias_map.get(db._key(name), db._key(name))
        if k in chars and not chars[k]['dynasty'] and is_valid_name(place):
            chars[k]['dynasty'] = place
