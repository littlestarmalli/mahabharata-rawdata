"""
Build new chapter file format with:
- Parva headers:     ======= Parva Name [N] ==== [sub-parvas] ==== [total_ch] ==== [total_shlokas] =======
- Sub-parva headers: ________ Sub-parva Name [section_N] ____ [ch_count] ____ [total_shlokas] ________
- Chapter headers:   --- Chapter N(M) [shlokas_in_chapter] ---
"""
import re, os

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

# Parse TOC files for chapter shlokas and section assignments
chapter_shlokas = {}
section_of_ch   = {}

for v in range(1, 11):
    lines = open(f'output/volumes/volume_{v}_toc.txt', encoding='utf-8').readlines()
    cur_sec = None
    for line in lines:
        s = line.strip()
        if not s:
            continue
        m_sec = re.match(r'^(?:SECTION|Section)\s+([A-Za-z][A-Za-z\-]*)$', s)
        if m_sec:
            word = m_sec.group(1).upper()
            if word in W2N:
                cur_sec = W2N[word]
                continue
        m_ch = re.match(r'^Chapter\s+(\d+)(?:\([^)]+\))?\s*:\s*(\d+)\s+shloka', s, re.IGNORECASE)
        if m_ch:
            ch_num = int(m_ch.group(1))
            sl = int(m_ch.group(2))
            chapter_shlokas[ch_num] = sl
            if cur_sec:
                section_of_ch[ch_num] = cur_sec

# Post-processing corrections
# Fix OCR error: ch 1126(7) in SHALYA-VADHA context (vol7 TOC) should be ch 1226
chapter_shlokas[1126] = 37   # restore from vol6 (Drona Parva ch 1126(149))
chapter_shlokas[1226] = 44   # correct value for ch 1226
section_of_ch[1126] = 70     # belongs to Ghatotkacha-vadha Parva (sec 70, Drona)
section_of_ch[1226] = 74     # belongs to Shalya-vadha Parva

# Fix Karna Parva: all ch 1151-1219 belong to sec 73
for ch in range(1151, 1220):
    section_of_ch[ch] = 73

# Fix Shalya Parva sections (override any wrong assignment from OCR errors above)
for ch in range(1220, 1236): section_of_ch[ch] = 74
for ch in range(1236, 1248): section_of_ch[ch] = 75
for ch in range(1248, 1273): section_of_ch[ch] = 76
for ch in range(1273, 1284): section_of_ch[ch] = 77

# Single-chapter sections missing from TOC chapter entries
MISSING_CH = {
    1: (1, 210), 2: (2, 243), 3: (3, 195),
    199: (15, 50), 213: (18, 82), 219: (19, 40),
    309: (30, 0), 451: (34, 0), 541: (40, 0),
    1091: (69, 0), 1149: (72, 0),
}
for ch, (sec, sl) in MISSING_CH.items():
    section_of_ch[ch] = sec
    chapter_shlokas[ch] = sl

# Build section data
section_data = {}
for sec in range(1, 96):
    section_data[sec] = {'name': SECTION_NAMES.get(sec, f'Section {sec}'),
                         'first_ch': None, 'last_ch': None, 'total_shlokas': 0}
for ch in range(1, 1996):
    sec = section_of_ch.get(ch)
    if sec is None:
        continue
    sl = chapter_shlokas.get(ch, 0)
    d = section_data[sec]
    if d['first_ch'] is None or ch < d['first_ch']:
        d['first_ch'] = ch
    if d['last_ch'] is None or ch > d['last_ch']:
        d['last_ch'] = ch
    d['total_shlokas'] += sl

# Parva lookup
parva_of_ch = {}
for i, pd in enumerate(PARVA_DATA):
    for ch in range(pd[2], pd[3]+1):
        parva_of_ch[ch] = i

parva_total_shlokas = [
    sum(chapter_shlokas.get(c, 0) for c in range(pd[2], pd[3]+1))
    for pd in PARVA_DATA
]

# Verification
print('=== Verification ===')
missing_ch = [c for c in range(1, 1996) if c not in chapter_shlokas]
print(f'chapter_shlokas: {len(chapter_shlokas)}, missing: {missing_ch}')
print()
print('Parva shloka check:')
for i, pd in enumerate(PARVA_DATA):
    name, pnum, s_ch, e_ch, n_sub, exp_sl = pd[:6]
    got = parva_total_shlokas[i]
    miss = [c for c in range(s_ch, e_ch+1) if c not in chapter_shlokas]
    status = 'OK' if got == exp_sl else f'DIFF(exp={exp_sl},got={got},miss={len(miss)}ch)'
    print(f'  P{pnum:2d} {name:25s}: {status}')

# Header builders
def parva_header(pd, i):
    name, pnum, s_ch, e_ch, n_sub, exp_sl = pd[:6]
    total_ch = e_ch - s_ch + 1
    sl = parva_total_shlokas[i]
    return f'======= {name} [{pnum}] ==== [{n_sub}] ==== [{total_ch}] ==== [{sl}] ======='

def section_header(sec):
    d = section_data[sec]
    fc, lc, sl, nm = d['first_ch'], d['last_ch'], d['total_shlokas'], d['name']
    ch_count = (lc - fc + 1) if fc and lc else 0
    return f'________ {nm} [{sec}] ____ [{ch_count}] ____ [{sl}] ________'

def chapter_header(ch_num, local_m, sl):
    sl_str = str(sl) if sl else '?'
    return f'--- Chapter {ch_num}({local_m}) [{sl_str}] ---'

# Rewrite volume chapter files
VOL_RANGES = [
    (1,   1,  199), (2, 200,  376), (3, 377,  596), (4, 597,  832),
    (5, 833, 1008), (6, 1009, 1150), (7, 1151, 1283), (8, 1284, 1527),
    (9, 1528, 1737), (10, 1738, 1995),
]

CH_RE = re.compile(r'^--- Chapter (\d+)\((\d+)\)(?:\s+\[.*?\])?\s*(?:---.*)?$')

print()
print('=== Rewriting files ===')
for vol, v_start, v_end in VOL_RANGES:
    path = f'output/volumes/volume_{vol}_chapters.txt'
    with open(path, encoding='utf-8') as f:
        orig_lines = f.readlines()

    out = []
    last_parva_idx = None
    last_section   = None

    for line in orig_lines:
        s = line.rstrip('\n')
        stripped = s.strip()

        # Skip old parva/section headers from previous runs
        if stripped.startswith('=======') or stripped.startswith('________'):
            continue

        m = CH_RE.match(stripped)
        if m:
            ch_num  = int(m.group(1))
            local_m = int(m.group(2))
            sl      = chapter_shlokas.get(ch_num, 0)
            sec     = section_of_ch.get(ch_num)
            p_idx   = parva_of_ch.get(ch_num)

            # Parva header at first chapter of parva
            if p_idx is not None and p_idx != last_parva_idx:
                pd = PARVA_DATA[p_idx]
                if ch_num == pd[2]:
                    out.append('')
                    out.append(parva_header(pd, p_idx))
                    out.append('')
                    last_parva_idx = p_idx
                    last_section   = None

            # Section header at first chapter of section
            if sec is not None and sec != last_section:
                d = section_data[sec]
                if d['first_ch'] == ch_num:
                    out.append('')
                    out.append(section_header(sec))
                    out.append('')
                    last_section = sec

            out.append(chapter_header(ch_num, local_m, sl))
        else:
            out.append(s)

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
        if out: f.write('\n')

    print(f'  volume_{vol}_chapters.txt: {len(orig_lines)} -> {len(out)} lines')

print('Done.')
