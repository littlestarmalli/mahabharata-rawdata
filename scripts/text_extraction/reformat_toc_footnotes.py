"""
Reformat volume_N_toc.txt and volume_N_footnotes.txt to align with
the header format established in volume_N_chapters.txt:
  Parva:   ======= Parva Name [N] ==== [sub] ==== [total_ch] ==== [total_sl] =======
  Section: ________ Section Name [N] ____ [ch_count] ____ [total_sl] ________
  Chapter: --- Chapter N(M) [sl] ---
"""
import re, sys

W2N = {
    'ONE':1,'TWO':2,'THREE':3,'FOUR':4,'FIVE':5,'SIX':6,'SEVEN':7,'EIGHT':8,'NINE':9,'TEN':10,
    'ELEVEN':11,'TWELVE':12,'THIRTEEN':13,'FOURTEEN':14,'FIFTEEN':15,'SIXTEEN':16,'SEVENTEEN':17,
    'EIGHTEEN':18,'NINETEEN':19,'TWENTY':20,'TWENTY-ONE':21,'TWENTY-TWO':22,'TWENTY-THREE':23,
    'TWENTY-FOUR':24,'TWENTY-FIVE':25,'TWENTY-SIX':26,'TWENTY-SEVEN':27,'TWENTY-EIGHT':28,
    'TWENTY-NINE':29,'THIRTY':30,'THIRTY-ONE':31,'THIRTY-TWO':32,'THIRTY-THREE':33,
    'THIRTY-FOUR':34,'THIRTY-FIVE':35,'THIRTY-SIX':36,'THIRTY-SEVEN':37,'THIRTY-EIGHT':38,
    'THIRTY-NINE':39,'FORTY':40,'FORTY-ONE':41,'FORTY-TWO':42,'FORTY-THREE':43,'FORTY-FOUR':44,
    'FORTY-FIVE':45,'FORTY-SIX':46,'FORTY-SEVEN':47,'FORTY-EIGHT':48,'FORTY-NINE':49,'FIFTY':50,
    'FIFTY-ONE':51,'FIFTY-TWO':52,'FIFTY-THREE':53,'FIFTY-FOUR':54,'FIFTY-FIVE':55,'FIFTY-SIX':56,
    'FIFTY-SEVEN':57,'FIFTY-EIGHT':58,'FIFTY-NINE':59,'SIXTY':60,'SIXTY-ONE':61,'SIXTY-TWO':62,
    'SIXTY-THREE':63,'SIXTY-FOUR':64,'SIXTY-FIVE':65,'SIXTY-SIX':66,'SIXTY-SEVEN':67,
    'SIXTY-EIGHT':68,'SIXTY-NINE':69,'SEVENTY':70,'SEVENTY-ONE':71,'SEVENTY-TWO':72,
    'SEVENTY-THREE':73,'SEVENTY-FOUR':74,'SEVENTY-FIVE':75,'SEVENTY-SIX':76,'SEVENTY-SEVEN':77,
    'SEVENTY-EIGHT':78,'SEVENTY-NINE':79,'EIGHTY':80,'EIGHTY-ONE':81,'EIGHTY-TWO':82,
    'EIGHTY-THREE':83,'EIGHTY-FOUR':84,'EIGHTY-FIVE':85,'EIGHTY-SIX':86,'EIGHTY-SEVEN':87,
    'EIGHTY-EIGHT':88,'EIGHTY-NINE':89,'NINETY':90,'NINETY-ONE':91,'NINETY-TWO':92,
    'NINETY-THREE':93,'NINETY-FOUR':94,'NINETY-FIVE':95,
}

PARVA_DATA = [
    ('Adi Parva',              1,    1,  225, 19,  7202,  1, 19),
    ('Sabha Parva',            2,  226,  297,  9,  2387, 20, 28),
    ('Vana Parva',             3,  298,  596, 16, 10239, 29, 44),
    ('Virata Parva',           4,  597,  663,  4,  1736, 45, 48),
    ('Udyoga Parva',           5,  664,  860, 12,  6001, 49, 60),
    ('Bhishma Parva',          6,  861,  977,  4,  5381, 61, 64),
    ('Drona Parva',            7,  978, 1150,  8,  8069, 65, 72),
    ('Karna Parva',            8, 1151, 1219,  1,  3870, 73, 73),
    ('Shalya Parva',           9, 1220, 1283,  4,  3541, 74, 77),
    ('Sauptika Parva',        10, 1284, 1301,  2,   771, 78, 79),
    ('Stri Parva',            11, 1302, 1328,  4,   713, 80, 83),
    ('Shanti Parva',          12, 1329, 1681,  3, 13006, 84, 86),
    ('Anushasana Parva',      13, 1682, 1835,  2,  6493, 87, 88),
    ('Ashvamedhika Parva',    14, 1836, 1931,  1,  2741, 89, 89),
    ('Ashramavasa Parva',     15, 1932, 1978,  3,  1061, 90, 92),
    ('Mausala Parva',         16, 1979, 1987,  1,   273, 93, 93),
    ('Mahaprasthanika Parva', 17, 1988, 1990,  1,   106, 94, 94),
    ('Svargarohana Parva',    18, 1991, 1995,  1,   194, 95, 95),
]

SECTION_NAMES = {
    1:'Anukramanika Parva', 2:'Parvasamgraha Parva', 3:'Poushya Parva',
    4:'Pouloma Parva', 5:'Astika Parva', 6:'Adi-vamshavatarana Parva',
    7:'Sambhava Parva', 8:'Jatugriha-daha Parva', 9:'Hidimba-vadha Parva',
    10:'Baka-vadha Parva', 11:'Chaitraratha Parva', 12:'Swayamvara Parva',
    13:'Vaivahika Parva', 14:'Viduragamana Parva', 15:'Rajya-labha Parva',
    16:'Arjuna-vanavasa Parva', 17:'Subhadra-harana Parva', 18:'Harana-harika Parva',
    19:'Khandava-daha Parva', 20:'Sabha Parva', 21:'Mantra Parva',
    22:'Jarasandha-vadha Parva', 23:'Digvijaya Parva', 24:'Rajasuya Parva',
    25:'Arghabhiharana Parva', 26:'Shishupala-vadha Parva', 27:'Dyuta Parva',
    28:'Anudyuta Parva', 29:'Aranyaka Parva', 30:'Kirmira-vadha Parva',
    31:'Kairata Parva', 32:'Indralokabhigamana Parva', 33:'Tirtha-yatra Parva',
    34:'Jatasura-vadha Parva', 35:'Yaksha-yuddha Parva', 36:'Ajagara Parva',
    37:'Markandeya Samasya Parva', 38:'Droupadi-Satyabhama Parva',
    39:'Ghoshayatra Parva', 40:'Mriga-Svapna-Bhaya Parva', 41:'Vrihi-Drounika Parva',
    42:'Droupadi-harana Parva', 43:'Kundala-aharana Parva', 44:'Aranyaka-parvan Parva',
    45:'Vairata Parva', 46:'Kichaka-vadha Parva', 47:'Go-Grahana Parva',
    48:'Vaivahika Parva', 49:'Udyoga Parva', 50:'Sanjaya-Yana Parva',
    51:'Prajagara Parva', 52:'Sanatsujata Parva', 53:'Yana-Sandhi Parva',
    54:'Bhagavat-Yana Parva', 55:'Karna-Upanivada Parva', 56:'Sainya-Niryayana Parva',
    57:'Bhishma-Abhishechana Parva', 58:'Uluka-Yana Parva', 59:'Aindrya Parva',
    60:'Amba-Upakhyana Parva', 61:'Jambukhanda-Vinirmana Parva', 62:'Bhumi Parva',
    63:'Bhagavad Gita Parva', 64:'Bhishma-vadha Parva', 65:'Dronabhisheka Parva',
    66:'Samshaptaka-vadha Parva', 67:'Abhimanyu-vadha Parva', 68:'Pratijna Parva',
    69:'Jayadratha-vadha Parva', 70:'Ghatotkacha-vadha Parva', 71:'Drona-vadha Parva',
    72:'Narayana-astra-moksana Parva', 73:'Karna-vadha Parva',
    74:'Shalya-vadha Parva', 75:'Hrada-pravesha Parva',
    76:'Tirtha-yatra Parva', 77:'Gada-yuddha Parva',
    78:'Souptika Parva', 79:'Aishika Parva',
    80:'Stri Parva', 81:'Stri-vilapa Parva', 82:'Shraddha Parva',
    83:'Jala-pradanika Parva', 84:'Raja Dharma Parva', 85:'Apaddharma Parva',
    86:'Moksha Dharma Parva', 87:'Dana Dharma Parva',
    88:'Bhishma-Svargarohana Parva', 89:'Ashvamedhika Parva',
    90:'Ashrama-Vasa Parva', 91:'Putra Darshana Parva', 92:'Naradagamana Parva',
    93:'Mausala Parva', 94:'Mahaprasthanika Parva', 95:'Svargarohana Parva',
}

# Parse chapter shlokas and section assignments (same logic as build_headers.py)
chapter_shlokas = {}
section_of_ch   = {}
for v in range(1, 11):
    lines = open(f'output/volumes/volume_{v}_toc.txt', encoding='utf-8').readlines()
    cur_sec = None
    for line in lines:
        s = line.strip()
        if not s: continue
        m = re.match(r'^(?:SECTION|Section)\s+([A-Za-z][A-Za-z\-]*)$', s)
        if m:
            w = m.group(1).upper()
            if w in W2N: cur_sec = W2N[w]; continue
        mc = re.match(r'^Chapter\s+(\d+)(?:\([^)]+\))?\s*:\s*(\d+)\s+shloka', s, re.IGNORECASE)
        if mc:
            ch_num = int(mc.group(1)); sl = int(mc.group(2))
            chapter_shlokas[ch_num] = sl
            if cur_sec: section_of_ch[ch_num] = cur_sec

# Apply same corrections as build_headers.py
chapter_shlokas[1126] = 37; chapter_shlokas[1226] = 44
section_of_ch[1126] = 70;   section_of_ch[1226] = 74
for ch in range(1151, 1220): section_of_ch[ch] = 73
for ch in range(1220, 1236): section_of_ch[ch] = 74
for ch in range(1236, 1248): section_of_ch[ch] = 75
for ch in range(1248, 1273): section_of_ch[ch] = 76
for ch in range(1273, 1284): section_of_ch[ch] = 77
MISSING_CH = {1:(1,210), 2:(2,243), 3:(3,195), 199:(15,50), 213:(18,82),
              219:(19,40), 309:(30,0), 451:(34,0), 541:(40,0), 1091:(69,0), 1149:(72,0)}
for ch, (sec, sl) in MISSING_CH.items():
    section_of_ch[ch] = sec; chapter_shlokas[ch] = sl

# Build section stats
section_data = {}
for sec in range(1, 96):
    section_data[sec] = {'name': SECTION_NAMES.get(sec, f'Section {sec}'),
                         'first_ch': None, 'last_ch': None, 'total_shlokas': 0}
for ch in range(1, 1996):
    sec = section_of_ch.get(ch)
    if sec is None: continue
    d = section_data[sec]
    sl = chapter_shlokas.get(ch, 0)
    if d['first_ch'] is None or ch < d['first_ch']: d['first_ch'] = ch
    if d['last_ch'] is None or ch > d['last_ch']:   d['last_ch'] = ch
    d['total_shlokas'] += sl

parva_of_ch = {}
for i, pd in enumerate(PARVA_DATA):
    for ch in range(pd[2], pd[3]+1): parva_of_ch[ch] = i
parva_total_shlokas = [
    sum(chapter_shlokas.get(c, 0) for c in range(pd[2], pd[3]+1))
    for pd in PARVA_DATA]

# Parva starts (first section of each parva)
parva_first_sec = {pd[6]: i for i, pd in enumerate(PARVA_DATA)}   # sec_start -> parva_idx

def parva_hdr(idx):
    pd = PARVA_DATA[idx]
    name, pnum, s_ch, e_ch, n_sub = pd[:5]
    total_ch = e_ch - s_ch + 1
    sl = parva_total_shlokas[idx]
    return f'======= {name} [{pnum}] ==== [{n_sub}] ==== [{total_ch}] ==== [{sl}] ======='

def sec_hdr(sec):
    d = section_data[sec]
    fc, lc, sl, nm = d['first_ch'], d['last_ch'], d['total_shlokas'], d['name']
    ch_count = (lc - fc + 1) if fc and lc else 0
    return f'________ {nm} [{sec}] ____ [{ch_count}] ____ [{sl}] ________'

def ch_hdr(ch_num, local_m, sl):
    sl_str = str(sl) if sl else '?'
    return f'--- Chapter {ch_num}({local_m}) [{sl_str}] ---'

CH_RE  = re.compile(r'^Chapter\s+(\d+)(?:\((\d+)\))?\s*:\s*(\d+)\s+shloka', re.IGNORECASE)
# Match both mixed-case and ALL-CAPS Section headers, including fi/fl ligatures
SEC_RE = re.compile(r'^(?:SECTION|Section)\s+(.+)$')

LIGATURES = {'\ufb01': 'FI', '\ufb02': 'FL'}  # fi, fl ligatures from OCR
def normalize_word(w):
    for lig, rep in LIGATURES.items():
        w = w.replace(lig, rep)
    return w.upper().rstrip(':')

def next_nonblank(lines, i):
    j = i + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    return lines[j].strip() if j < len(lines) else ''

def is_index_section(lines, i):
    """True if this section header is an index entry (no content follows)."""
    nxt = next_nonblank(lines, i)
    # Index if next non-blank is another SECTION/Section header, or a SECTION: NAME combined line
    if re.match(r'^(?:SECTION|Section)\s+', nxt): return True
    # Index if next non-blank is empty (EOF)
    if not nxt: return True
    return False

# ═══════════════════════════════════════════════════════════
# REFORMAT TOC FILES
# ═══════════════════════════════════════════════════════════
print('=== Reformatting TOC files ===')
for v in range(1, 11):
    path = f'output/volumes/volume_{v}_toc.txt'
    raw = open(path, encoding='utf-8').readlines()

    lines = [l.rstrip('\n') for l in raw]
    out = []
    emitted_parvas = set()
    emitted_secs   = set()
    i = 0

    # If file already has formatted headers, still track which are emitted
    for l in lines:
        s = l.strip()
        # Track already-emitted sections from previous runs
        m_already = re.match(r'^________\s+.+\[(\d+)\]', s)
        if m_already:
            emitted_secs.add(int(m_already.group(1)))
        m_ap = re.match(r'^=======\s+.+\[(\d+)\]', s)
        if m_ap:
            emitted_parvas.add(int(m_ap.group(1)) - 1)  # parva_idx = pnum-1
    # Reset: we'll re-emit everything clean
    emitted_parvas = set()
    emitted_secs   = set()
    i = 0

    while i < len(lines):
        s = lines[i].strip()

        # Pass through already-formatted headers unchanged
        if s.startswith('________') or s.startswith('======='):
            out.append(lines[i])
            i += 1
            continue

        # Match "SECTION N: PARVA NAME" combined index format - skip entirely
        if re.match(r'^SECTION\s+[A-Z][A-Z\-]+:\s+', s):
            i += 1
            continue

        # Match Section/SECTION header
        m_sec = SEC_RE.match(s)
        if m_sec:
            # Normalize the captured word (handle ligatures, strip colon suffix)
            word = normalize_word(m_sec.group(1).split(':')[0].strip())
            if word in W2N:
                sec_num = W2N[word]

                # Skip index entries (not followed by actual content)
                if is_index_section(lines, i):
                    i += 1
                    continue

                # Skip if already emitted (duplicate summary block)
                if sec_num in emitted_secs:
                    i += 1
                    # Also skip the following parva-name lines
                    while i < len(lines):
                        nxt = lines[i].strip()
                        if re.search(r'Parva', nxt, re.IGNORECASE) \
                                and not re.match(r'^Chapter', nxt, re.IGNORECASE) \
                                and not re.search(r'has \d+ shlokas', nxt):
                            i += 1
                        else:
                            break
                    continue

                # Parva header if this is first section of a parva
                parva_idx = parva_first_sec.get(sec_num)
                if parva_idx is not None and parva_idx not in emitted_parvas:
                    out.append('')
                    out.append(parva_hdr(parva_idx))
                    out.append('')
                    emitted_parvas.add(parva_idx)

                # Emit section header
                out.append('')
                out.append(sec_hdr(sec_num))
                out.append('')
                emitted_secs.add(sec_num)
                i += 1

                # Skip ALL following sub-parva name lines (already in sec header)
                while i < len(lines):
                    nxt = lines[i].strip()
                    if re.search(r'Parva', nxt, re.IGNORECASE) \
                            and not re.match(r'^Chapter', nxt, re.IGNORECASE) \
                            and not re.search(r'has \d+ shlokas', nxt) \
                            and not re.search(r'shlokas and', nxt) \
                            and not re.match(r'^---', nxt):
                        i += 1
                    else:
                        break
                continue

        # Match chapter entry: "Chapter N: X shlokas" or "Chapter N(M): X shlokas"
        mc = CH_RE.match(s)
        if mc:
            ch_num  = int(mc.group(1))
            local_m = int(mc.group(2)) if mc.group(2) else None
            sl      = int(mc.group(3))
            if local_m is None:
                # compute local_m from parva
                pidx = parva_of_ch.get(ch_num)
                local_m = (ch_num - PARVA_DATA[pidx][2] + 1) if pidx is not None else ch_num
            out.append(ch_hdr(ch_num, local_m, sl))
            i += 1
            continue

        # Skip pure standalone parva-name lines (OCR/index lines between sections)
        # e.g. "Anushasana Parva", "Sabha Parva" on their own line between sections
        # Only skip if it looks like a lone parva name with no other content
        if re.match(r'^[A-Za-z\s\-]+Parva$', s) and len(s.split()) <= 4:
            # Keep it as a comment line
            out.append(s)
            i += 1
            continue

        # Keep everything else (description text, preview, blank lines)
        out.append(lines[i])
        i += 1

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
        if out: f.write('\n')
    print(f'  volume_{v}_toc.txt: {len(raw)} -> {len(out)} lines')

# ═══════════════════════════════════════════════════════════
# REFORMAT FOOTNOTES FILES
# ═══════════════════════════════════════════════════════════
print()
print('=== Reformatting footnotes files ===')

# Regex for footnotes section / chapter-range headers
FN_SEC_RE   = re.compile(r'^--- Section \d+ ---$')
FN_CHAP_RE  = re.compile(r'^--- Chapters (\d+)(?:\(\d+\))? to (\d+)(?:\(\d+\))? ---$')

for v in range(1, 11):
    path = f'output/volumes/volume_{v}_footnotes.txt'
    raw  = open(path, encoding='utf-8').readlines()
    lines = [l.rstrip('\n') for l in raw]
    out = []
    emitted_parvas = set()
    i = 0

    while i < len(lines):
        s = lines[i].strip()

        # Skip old section header (replaced by section+range combo below)
        if FN_SEC_RE.match(s):
            i += 1
            # Peek at next line for chapter range
            if i < len(lines) and FN_CHAP_RE.match(lines[i].strip()):
                m_rng = FN_CHAP_RE.match(lines[i].strip())
                first_ch = int(m_rng.group(1))
                last_ch  = int(m_rng.group(2))
                sec_num  = section_of_ch.get(first_ch)

                if sec_num is not None:
                    # Parva header if needed
                    parva_idx = parva_first_sec.get(sec_num)
                    if parva_idx is not None and parva_idx not in emitted_parvas:
                        out.append('')
                        out.append(parva_hdr(parva_idx))
                        out.append('')
                        emitted_parvas.add(parva_idx)
                    out.append('')
                    out.append(sec_hdr(sec_num))
                    out.append('')
                else:
                    # Fallback: keep original section header
                    out.append(s)
                    out.append('')

                # Keep the chapter range line as reference
                out.append(lines[i])
                i += 1
            continue

        # Keep all other lines (footnote text, blank lines)
        out.append(lines[i])
        i += 1

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
        if out: f.write('\n')
    print(f'  volume_{v}_footnotes.txt: {len(raw)} -> {len(out)} lines')

print('Done.')
