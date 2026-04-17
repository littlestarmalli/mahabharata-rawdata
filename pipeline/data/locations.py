"""Hardcoded location definitions for the Mahabharata knowledge graph.
Real-world coordinates based on archaeological/historical evidence."""

import math


def get_locations():
    """Return the complete locations dictionary (52 entries)."""
    locations = {
        # ─── Kingdoms ───
        "hastinapura": {
            "Name": "Hastinapura", "Type": "Kingdom",
            "Region": "Bharata",
            "Sub_Locations": ["@indraprastha"],
            "Ruler": "@dhritarashtra",
            "Famous_For": ["Capital of Kuru dynasty","Dice game","Court of Kauravas"],
            "Residents": ["@dhritarashtra","@gandhari","@duryodhana","@bhishma","@drona","@vidura","@kunti"],
            "Geography": {"Terrain": "Plains along Ganga","Climate": "Temperate"},
            "Modern_Equivalent": "Hastinapur, Meerut district, Uttar Pradesh",
            "Coordinates": {"lat": 29.1604, "lng": 78.0180},
            "Notes": "Primary capital of the Kuru kingdom. Archaeological site at Hastinapur village, Meerut."
        },
        "indraprastha": {
            "Name": "Indraprastha", "Type": "City",
            "Parent_Kingdom": "@hastinapura",
            "Region": "Bharata",
            "Ruler": "@yudhishthira",
            "Famous_For": ["Maya Sabha","Rajasuya Yajna","Pandava capital"],
            "Residents": ["@yudhishthira","@bhima","@arjuna","@nakula","@sahadeva","@draupadi"],
            "Geography": {"Terrain": "Plains along Yamuna","Climate": "Temperate"},
            "Modern_Equivalent": "Purana Qila area, Delhi",
            "Coordinates": {"lat": 28.6095, "lng": 77.2425},
            "Notes": "Built by Maya Danava for Pandavas on Khandava land. Identified with Purana Qila, Delhi."
        },
        "panchala": {
            "Name": "Panchala", "Type": "Kingdom",
            "Region": "Bharata",
            "Ruler": "@drupada",
            "Famous_For": ["Draupadi Swayamvara","Birth of Dhrishtadyumna","Allied with Pandavas"],
            "Residents": ["@drupada","@draupadi","@dhrishtadyumna","@shikhandi"],
            "Geography": {"Terrain": "Gangetic plains","Climate": "Temperate"},
            "Modern_Equivalent": "Ahichchhatra (North Panchala), Kampilya (South Panchala), Uttar Pradesh",
            "Coordinates": {"lat": 28.3670, "lng": 79.4304},
            "Notes": "Divided into North Panchala (capital Ahichchhatra) and South Panchala (capital Kampilya). Archaeological ruins at both sites."
        },
        "dvaraka": {
            "Name": "Dvaraka", "Type": "Kingdom",
            "Region": "Western Bharata",
            "Ruler": "@krishna",
            "Famous_For": ["Krishna's capital","Golden city","Submerged by sea"],
            "Residents": ["@krishna","@balarama","@rukmini","@satyabhama","@pradyumna"],
            "Geography": {"Terrain": "Coastal island city","Climate": "Tropical maritime"},
            "Modern_Equivalent": "Dwarka, Gujarat",
            "Coordinates": {"lat": 22.2442, "lng": 68.9685},
            "Notes": "Built by Vishwakarma; sank into sea after Mausala. Underwater ruins found by ASI off Dwarka coast."
        },
        "magadha": {
            "Name": "Magadha", "Type": "Kingdom",
            "Region": "Eastern Bharata",
            "Sub_Locations": ["@girivraja"],
            "Ruler": "@jarasandha",
            "Famous_For": ["Jarasandha's fortress","Wrestling duel with Bhima"],
            "Residents": ["@jarasandha"],
            "Geography": {"Terrain": "Hills and plains","Climate": "Subtropical"},
            "Modern_Equivalent": "Rajgir/Patna region, Bihar",
            "Coordinates": {"lat": 25.0283, "lng": 85.4218},
            "Notes": "Powerful eastern kingdom opposing Yadavas. Capital at Rajgir (Girivraja)."
        },
        "girivraja": {
            "Name": "Girivraja", "Type": "City",
            "Parent_Kingdom": "@magadha",
            "Region": "Eastern Bharata",
            "Famous_For": ["Jarasandha's capital","Surrounded by five hills"],
            "Geography": {"Terrain": "Hill-girt city","Climate": "Subtropical"},
            "Modern_Equivalent": "Rajgir, Bihar",
            "Coordinates": {"lat": 25.0268, "lng": 85.4210}
        },
        "kashi": {
            "Name": "Kashi", "Type": "Kingdom",
            "Region": "Bharata",
            "Famous_For": ["Swayamvara of princesses","Abduction by Bhishma","Sacred city"],
            "Geography": {"Terrain": "Banks of Ganga","Climate": "Subtropical"},
            "Modern_Equivalent": "Varanasi, Uttar Pradesh",
            "Coordinates": {"lat": 25.3176, "lng": 82.9739},
            "Notes": "Princesses Amba, Ambika, Ambalika abducted from here by Bhishma"
        },
        "chedi": {
            "Name": "Chedi", "Type": "Kingdom",
            "Region": "Central Bharata",
            "Ruler": "@shishupala",
            "Famous_For": ["Shishupala killed by Krishna at Rajasuya"],
            "Residents": ["@shishupala","@dhrishtaketu"],
            "Geography": {"Terrain": "Central Indian plateau","Climate": "Subtropical"},
            "Modern_Equivalent": "Banda/Sagar region, Madhya Pradesh",
            "Coordinates": {"lat": 25.4760, "lng": 80.3319},
            "Notes": "Capital identified with Suktimati or Sothivatinagara."
        },
        "anga": {
            "Name": "Anga", "Type": "Kingdom",
            "Region": "Eastern Bharata",
            "Ruler": "@karna",
            "Famous_For": ["Karna's kingdom","Given by Duryodhana"],
            "Residents": ["@karna","@vrishasena"],
            "Geography": {"Terrain": "Gangetic plains","Climate": "Subtropical"},
            "Modern_Equivalent": "Bhagalpur region, Bihar",
            "Coordinates": {"lat": 25.2425, "lng": 86.9842},
            "Notes": "Duryodhana crowned Karna king of Anga. Capital at Champa (modern Bhagalpur)."
        },
        "gandhara": {
            "Name": "Gandhara", "Type": "Kingdom",
            "Region": "Northwestern Bharata",
            "Ruler": "@shakuni",
            "Famous_For": ["Shakuni's kingdom","Gandhari's homeland"],
            "Residents": ["@shakuni","@subala"],
            "Geography": {"Terrain": "Mountain valleys","Climate": "Continental"},
            "Modern_Equivalent": "Peshawar valley / Taxila region, Pakistan",
            "Coordinates": {"lat": 34.0151, "lng": 71.5249},
            "Notes": "Capital at Takshashila (Taxila). One of the sixteen Mahajanapadas."
        },
        "sindhu": {
            "Name": "Sindhu", "Type": "Kingdom",
            "Region": "Western Bharata",
            "Ruler": "@jayadratha",
            "Famous_For": ["Jayadratha's kingdom","Blocked Pandavas in Chakravyuha day"],
            "Residents": ["@jayadratha","@duhshala"],
            "Geography": {"Terrain": "Indus river basin","Climate": "Arid"},
            "Modern_Equivalent": "Sindh, Pakistan",
            "Coordinates": {"lat": 25.3960, "lng": 68.3578}
        },
        "madra": {
            "Name": "Madra", "Type": "Kingdom",
            "Region": "Northwestern Bharata",
            "Ruler": "@shalya",
            "Famous_For": ["Shalya's kingdom","Madri's homeland"],
            "Residents": ["@shalya"],
            "Geography": {"Terrain": "Punjab plains","Climate": "Subtropical"},
            "Modern_Equivalent": "Sialkot region, Punjab",
            "Coordinates": {"lat": 32.4945, "lng": 74.5229}
        },
        "matsya": {
            "Name": "Matsya", "Type": "Kingdom",
            "Region": "Bharata",
            "Sub_Locations": ["@viratanagara"],
            "Ruler": "@virata",
            "Famous_For": ["Pandavas' incognito year","Uttara Gograhana battle"],
            "Residents": ["@virata","@uttaraa"],
            "Geography": {"Terrain": "Arid plains","Climate": "Semi-arid"},
            "Modern_Equivalent": "Jaipur/Bairat region, Rajasthan",
            "Coordinates": {"lat": 27.3117, "lng": 76.1775}
        },
        "viratanagara": {
            "Name": "Viratanagara", "Type": "City",
            "Parent_Kingdom": "@matsya",
            "Region": "Bharata",
            "Famous_For": ["Pandavas served in disguise for one year"],
            "Modern_Equivalent": "Bairat (Viratnagar), Rajasthan",
            "Coordinates": {"lat": 27.0238, "lng": 76.3817},
            "Notes": "Archaeological remains found at Bairat. Circular temple and Ashokan edict."
        },
        "pragjyotisha": {
            "Name": "Pragjyotisha", "Type": "Kingdom",
            "Region": "Eastern Bharata",
            "Ruler": "@bhagadatta",
            "Famous_For": ["Bhagadatta's elephant army","Naraka dynasty"],
            "Residents": ["@bhagadatta"],
            "Geography": {"Terrain": "Brahmaputra valley","Climate": "Subtropical humid"},
            "Modern_Equivalent": "Guwahati, Assam",
            "Coordinates": {"lat": 26.1445, "lng": 91.7362}
        },
        "manipura": {
            "Name": "Manipura", "Type": "Kingdom",
            "Region": "Eastern Bharata",
            "Ruler": "@chitrangada_manipura",
            "Famous_For": ["Arjuna married princess Chitrangada here"],
            "Residents": ["@chitrangada_manipura","@babhruvahana"],
            "Geography": {"Terrain": "Hills and valleys","Climate": "Subtropical"},
            "Modern_Equivalent": "Imphal, Manipur",
            "Coordinates": {"lat": 24.8170, "lng": 93.9368}
        },
        "trigarta": {
            "Name": "Trigarta", "Type": "Kingdom",
            "Region": "Northern Bharata",
            "Ruler": "@susharma",
            "Famous_For": ["Susharma's alliance with Kauravas","Attack on Matsya"],
            "Residents": ["@susharma"],
            "Geography": {"Terrain": "Foothills between three rivers","Climate": "Continental"},
            "Modern_Equivalent": "Jalandhar, Punjab",
            "Coordinates": {"lat": 31.3260, "lng": 75.5762},
            "Notes": "Name means 'land between three rivers' (Ravi, Beas, Sutlej)."
        },
        "koshala": {
            "Name": "Koshala", "Type": "Kingdom",
            "Region": "Bharata",
            "Famous_For": ["Ancient kingdom","Rama's kingdom"],
            "Geography": {"Terrain": "Gangetic plains","Climate": "Subtropical"},
            "Modern_Equivalent": "Ayodhya/Faizabad region, Uttar Pradesh",
            "Coordinates": {"lat": 26.7922, "lng": 82.1998}
        },
        "vidarbha": {
            "Name": "Vidarbha", "Type": "Kingdom",
            "Region": "Central Bharata",
            "Famous_For": ["Rukmini's homeland","Nala-Damayanti story"],
            "Residents": ["@rukmini","@damayanti","@bhima_vidarbha"],
            "Geography": {"Terrain": "Deccan plateau","Climate": "Tropical"},
            "Modern_Equivalent": "Nagpur/Amravati region, Maharashtra",
            "Coordinates": {"lat": 21.1458, "lng": 79.0882},
            "Notes": "Capital identified with Kundina (modern Kaundinyapur near Amravati)."
        },
        "nishadha": {
            "Name": "Nishadha", "Type": "Kingdom",
            "Region": "Bharata",
            "Ruler": "@nala",
            "Famous_For": ["Nala-Damayanti love story"],
            "Residents": ["@nala"],
            "Geography": {"Terrain": "Plains","Climate": "Subtropical"},
            "Modern_Equivalent": "Narwar/Gwalior region, Madhya Pradesh",
            "Coordinates": {"lat": 25.6400, "lng": 77.9100}
        },
        "kalinga": {
            "Name": "Kalinga", "Type": "Kingdom",
            "Region": "Eastern Bharata",
            "Famous_For": ["Participated in Kurukshetra War"],
            "Geography": {"Terrain": "Coastal","Climate": "Tropical"},
            "Modern_Equivalent": "Bhubaneswar/Puri region, Odisha",
            "Coordinates": {"lat": 20.2961, "lng": 85.8245}
        },
        "vanga": {
            "Name": "Vanga", "Type": "Kingdom",
            "Region": "Eastern Bharata",
            "Famous_For": ["Eastern kingdom","Participated in war"],
            "Geography": {"Terrain": "Delta region","Climate": "Tropical"},
            "Modern_Equivalent": "Bengal (West Bengal/Bangladesh)",
            "Coordinates": {"lat": 22.5726, "lng": 88.3639}
        },
        "kunti_kingdom": {
            "Name": "Kunti", "Type": "Kingdom",
            "Region": "Bharata",
            "Famous_For": ["Kunti's adoptive homeland","Kuntibhoja's kingdom"],
            "Modern_Equivalent": "Kota/Bundi region, Rajasthan",
            "Coordinates": {"lat": 25.2138, "lng": 75.8648},
            "Notes": "Kingdom of Kuntibhoja where Pritha (Kunti) grew up. Identified with area around Bundi."
        },
        "champapuri": {
            "Name": "Champapuri", "Type": "City",
            "Parent_Kingdom": "@anga",
            "Region": "Eastern Bharata",
            "Famous_For": ["Capital of Anga kingdom","Karna's capital"],
            "Modern_Equivalent": "Champanagar near Bhagalpur, Bihar",
            "Coordinates": {"lat": 25.2440, "lng": 87.0010}
        },
        # ─── Battlefield ───
        "kurukshetra": {
            "Name": "Kurukshetra", "Type": "Battlefield",
            "Region": "Bharata",
            "Famous_For": ["18-day Mahabharata War","Bhagavad Gita delivered here"],
            "Geography": {"Terrain": "Sacred plains","Climate": "Semi-arid"},
            "Modern_Equivalent": "Kurukshetra, Haryana",
            "Coordinates": {"lat": 29.9695, "lng": 76.8783},
            "Notes": "Dharmakshetra - field of righteousness. Jyotisar - exact spot of Gita Upadesh."
        },
        # ─── Forests ───
        "khandava_forest": {
            "Name": "Khandava Forest", "Type": "Forest",
            "Region": "Bharata",
            "Famous_For": ["Burned by Arjuna and Krishna","Indraprastha built on its land"],
            "Nearby_Locations": ["@indraprastha"],
            "Modern_Equivalent": "South Delhi / Faridabad region",
            "Coordinates": {"lat": 28.5000, "lng": 77.3000},
            "Notes": "Agni consumed this forest with help of Arjuna and Krishna. Region south of Indraprastha."
        },
        "kamyaka_forest": {
            "Name": "Kamyaka Forest", "Type": "Forest",
            "Region": "Bharata",
            "Famous_For": ["Pandavas' exile forest","Nala-Damayanti story told here"],
            "Modern_Equivalent": "Near Kurukshetra/Sarasvati river bank, Haryana",
            "Coordinates": {"lat": 29.5500, "lng": 76.9000},
            "Notes": "Main forest during Pandavas' 12-year exile. Identified near banks of old Sarasvati."
        },
        "dvaitavana": {
            "Name": "Dvaitavana", "Type": "Forest",
            "Region": "Bharata",
            "Famous_For": ["Pandavas' exile","Near a lake","Duryodhana captured by Gandharvas here"],
            "Modern_Equivalent": "Near Sthaneshwar (Thanesar), Haryana",
            "Coordinates": {"lat": 29.9700, "lng": 76.8200},
            "Notes": "Forest of exile near a sacred lake. Located close to Kurukshetra."
        },
        "naimisha_forest": {
            "Name": "Naimisha Forest", "Type": "Forest",
            "Region": "Bharata",
            "Famous_For": ["Ugrasrava narrated Mahabharata here","Sacred to sages"],
            "Modern_Equivalent": "Nimsar (Naimisharanya), Uttar Pradesh",
            "Coordinates": {"lat": 26.7460, "lng": 80.4530},
            "Notes": "Where the outer frame story of Mahabharata is set. Active pilgrimage site today."
        },
        "dandaka_forest": {
            "Name": "Dandaka Forest", "Type": "Forest",
            "Region": "Central Bharata",
            "Famous_For": ["Rama's exile in Ramayana","Dense ancient forest"],
            "Geography": {"Terrain": "Dense tropical forest","Climate": "Tropical"},
            "Modern_Equivalent": "Dandakaranya, Chhattisgarh/Maharashtra border",
            "Coordinates": {"lat": 19.5000, "lng": 80.0000}
        },
        # ─── Rivers (representative point along the river) ───
        "ganga_river": {
            "Name": "Ganga", "Type": "River",
            "Region": "Bharata",
            "Famous_For": ["Sacred river","Shantanu met Ganga here","Bhishma's mother"],
            "Geography": {"Terrain": "Major river flowing east to Bay of Bengal","Climate": "Varied"},
            "Modern_Equivalent": "Ganga at Haridwar (origin to plains)",
            "Coordinates": {"lat": 29.9457, "lng": 78.1642},
            "Notes": "Personified as goddess Ganga, mother of Bhishma. Shantanu met her near Hastinapura."
        },
        "yamuna_river": {
            "Name": "Yamuna", "Type": "River",
            "Region": "Bharata",
            "Famous_For": ["Flows past Indraprastha","Krishna's childhood river"],
            "Geography": {"Terrain": "Tributary of Ganga","Climate": "Temperate"},
            "Modern_Equivalent": "Yamuna at Delhi (flows past Purana Qila/Indraprastha)",
            "Coordinates": {"lat": 28.6100, "lng": 77.2500},
            "Notes": "Also known as Kalindi. Flows past Indraprastha (Delhi), Mathura, and Vrindavana."
        },
        "sarasvati_river": {
            "Name": "Sarasvati", "Type": "River",
            "Region": "Bharata",
            "Famous_For": ["Sacred river","Pilgrimage sites along banks","Balarama's pilgrimage"],
            "Geography": {"Terrain": "Dried up in places","Climate": "Semi-arid"},
            "Modern_Equivalent": "Dried Sarasvati channel near Kurukshetra/Pehowa, Haryana",
            "Coordinates": {"lat": 29.9800, "lng": 76.5800},
            "Notes": "Mentioned as flowing near Kurukshetra. Dried channel identified via satellite imagery."
        },
        "sindhu_river": {
            "Name": "Sindhu (Indus)", "Type": "River",
            "Region": "Northwestern Bharata",
            "Famous_For": ["Western boundary of Bharata","Major river of west"],
            "Geography": {"Terrain": "Large river flowing south","Climate": "Arid to semi-arid"},
            "Modern_Equivalent": "Indus River at Attock, Pakistan",
            "Coordinates": {"lat": 33.7740, "lng": 72.3609}
        },
        "godavari_river": {
            "Name": "Godavari", "Type": "River",
            "Region": "Southern Bharata",
            "Famous_For": ["Sacred southern river","Pilgrimage sites"],
            "Geography": {"Terrain": "Major peninsular river","Climate": "Tropical"},
            "Modern_Equivalent": "Godavari at Nashik (source), Maharashtra",
            "Coordinates": {"lat": 19.9975, "lng": 73.7898}
        },
        "narmada_river": {
            "Name": "Narmada", "Type": "River",
            "Region": "Central Bharata",
            "Famous_For": ["Sacred river","Boundary between north and south"],
            "Geography": {"Terrain": "Flows westward through central India","Climate": "Tropical"},
            "Modern_Equivalent": "Narmada at Jabalpur, Madhya Pradesh",
            "Coordinates": {"lat": 23.1815, "lng": 79.9864}
        },
        # ─── Mountains ───
        "himalayas": {
            "Name": "Himalayas", "Type": "Mountain",
            "Region": "Northern Bharata",
            "Famous_For": ["Abode of gods","Arjuna's penance for Pashupatastra",
                "Pandavas' final journey (Mahaprasthana)","Shiva's abode"],
            "Geography": {"Terrain": "Highest mountain range","Climate": "Alpine/glacial"},
            "Modern_Equivalent": "Kedarnath/Badrinath region, Uttarakhand",
            "Coordinates": {"lat": 30.7346, "lng": 79.0669},
            "Notes": "Site of Arjuna's tapas, Pandavas' ascent in Mahaprasthanika Parva"
        },
        "meru": {
            "Name": "Mount Meru", "Type": "Mountain",
            "Region": "Cosmic center",
            "Famous_For": ["Center of universe","Abode of gods","Golden mountain"],
            "Geography": {"Terrain": "Mythical golden peak","Climate": "Divine"},
            "Mythical": True,
            "Notes": "Cosmic mountain at center of universe in Hindu cosmology. No physical location."
        },
        "gandhamadana": {
            "Name": "Gandhamadana", "Type": "Mountain",
            "Region": "Northern Bharata",
            "Famous_For": ["Bhima met Hanuman here","Fragrant herbs","Kubera's garden"],
            "Geography": {"Terrain": "Fragrant mountain","Climate": "Alpine"},
            "Modern_Equivalent": "Near Badrinath, Uttarakhand / Kailash range",
            "Coordinates": {"lat": 30.7500, "lng": 79.5000},
            "Notes": "Bhima encountered Hanuman while searching for Saugandhika lotus"
        },
        "kailasa": {
            "Name": "Kailasa", "Type": "Mountain",
            "Region": "Northern Bharata",
            "Famous_For": ["Abode of Shiva and Parvati","Kubera's residence"],
            "Geography": {"Terrain": "Sacred peak","Climate": "Alpine/glacial"},
            "Modern_Equivalent": "Mount Kailash, Tibet (China)",
            "Coordinates": {"lat": 31.0672, "lng": 81.3119},
            "Notes": "Mount Kailash - sacred abode of Lord Shiva. Active pilgrimage destination."
        },
        "vindhya": {
            "Name": "Vindhya", "Type": "Mountain",
            "Region": "Central Bharata",
            "Famous_For": ["Divides north and south India","Ancient mountain range"],
            "Geography": {"Terrain": "Old mountain range","Climate": "Tropical"},
            "Modern_Equivalent": "Vindhya Range, Madhya Pradesh",
            "Coordinates": {"lat": 24.0000, "lng": 80.5000}
        },
        # ─── Celestial / Divine (no physical coordinates) ───
        "svarga": {
            "Name": "Svarga", "Type": "Celestial",
            "Region": "Cosmic",
            "Ruler": "@indra",
            "Famous_For": ["Heaven of gods","Arjuna trained here","Pandavas ascended here"],
            "Residents": ["@indra"],
            "Mythical": True,
            "Notes": "Indra's heaven; Arjuna spent time here learning weapons and dance"
        },
        "brahmaloka": {
            "Name": "Brahmaloka", "Type": "Celestial",
            "Region": "Cosmic",
            "Ruler": "@brahma",
            "Famous_For": ["Highest heaven","Abode of Brahma"],
            "Mythical": True,
            "Notes": "The highest celestial realm"
        },
        "patala": {
            "Name": "Patala", "Type": "Celestial",
            "Region": "Cosmic",
            "Famous_For": ["Underworld","Realm of Nagas","Arjuna visited Ulupi here"],
            "Mythical": True,
            "Notes": "Subterranean realm of Nagas"
        },
        "amaravati": {
            "Name": "Amaravati", "Type": "Celestial",
            "Region": "Cosmic",
            "Ruler": "@indra",
            "Famous_For": ["Capital of Svarga","Indra's court"],
            "Mythical": True,
            "Notes": "City of the gods in Indra's heaven"
        },
        # ─── Other cities/places ───
        "ekachakra": {
            "Name": "Ekachakra", "Type": "Village",
            "Region": "Bharata",
            "Famous_For": ["Bhima killed Bakasura here","Pandavas lived in disguise"],
            "Modern_Equivalent": "Arrah/Chakranagar, Bihar",
            "Coordinates": {"lat": 25.5549, "lng": 84.6634},
            "Notes": "Pandavas stayed here as Brahmins after Lakshagriha escape"
        },
        "upaplavya": {
            "Name": "Upaplavya", "Type": "City",
            "Parent_Kingdom": "@matsya",
            "Region": "Bharata",
            "Famous_For": ["Pandava war camp","Alliance meetings before war"],
            "Modern_Equivalent": "Near Bairat, Rajasthan",
            "Coordinates": {"lat": 27.0500, "lng": 76.4000},
            "Notes": "City in Matsya where Pandavas gathered allies before war"
        },
        "mathura": {
            "Name": "Mathura", "Type": "City",
            "Region": "Bharata",
            "Famous_For": ["Krishna's birthplace","Kamsa's capital"],
            "Geography": {"Terrain": "Banks of Yamuna","Climate": "Subtropical"},
            "Modern_Equivalent": "Mathura, Uttar Pradesh",
            "Coordinates": {"lat": 27.4924, "lng": 77.6737},
            "Notes": "Krishna was born here in Kamsa's prison. Keshava Deo temple at birthplace."
        },
        "vrindavana": {
            "Name": "Vrindavana", "Type": "Village",
            "Region": "Bharata",
            "Famous_For": ["Krishna's childhood","Gokula nearby"],
            "Nearby_Locations": ["@mathura"],
            "Geography": {"Terrain": "Banks of Yamuna","Climate": "Subtropical"},
            "Modern_Equivalent": "Vrindavan, Uttar Pradesh",
            "Coordinates": {"lat": 27.5830, "lng": 77.7013}
        },
        "shatashriga": {
            "Name": "Shatashriga", "Type": "Mountain",
            "Region": "Northern Bharata",
            "Famous_For": ["Pandu's death","Pandavas' early childhood"],
            "Modern_Equivalent": "Near Haridwar/Rishikesh foothills, Uttarakhand",
            "Coordinates": {"lat": 30.0869, "lng": 78.2676},
            "Notes": "Mountain where Pandu lived in exile and died. Identified with Shivalik foothills."
        },
        "badarikashrama": {
            "Name": "Badarikashrama", "Type": "Hermitage",
            "Region": "Northern Bharata",
            "Famous_For": ["Vyasa's ashram","Nara-Narayana tapas"],
            "Geography": {"Terrain": "Himalayan valley","Climate": "Alpine"},
            "Modern_Equivalent": "Badrinath, Uttarakhand",
            "Coordinates": {"lat": 30.7433, "lng": 79.4938}
        },
        "lakshagriha": {
            "Name": "Lakshagriha", "Type": "City",
            "Region": "Bharata",
            "Famous_For": ["House of lac","Duryodhana's plot to burn Pandavas"],
            "Modern_Equivalent": "Barnawa (Varanavata), Baghpat district, Uttar Pradesh",
            "Coordinates": {"lat": 29.0700, "lng": 77.3800},
            "Notes": "Also called Varanavata; trap set for Pandavas. Lacquer mound (Laksha ka Tila) survives at Barnawa."
        },
    }
    return locations


def compute_distances(locations):
    """Compute haversine distances between all coordinate-bearing locations.

    Adds 'Nearby_Distances_km' (within 500 km) to each location in-place.
    """
    def _haversine(lat1, lng1, lat2, lng2):
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
             * math.sin(dlng / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # For each location with coordinates, find nearby locations (within 500 km)
    # and compute distances to ALL other coordinate-bearing locations
    coord_locs = {lid: loc for lid, loc in locations.items() if loc.get("Coordinates")}
    for lid, loc in coord_locs.items():
        c1 = loc["Coordinates"]
        nearby = []
        for other_id, other_loc in coord_locs.items():
            if other_id == lid:
                continue
            c2 = other_loc["Coordinates"]
            dist = round(_haversine(c1["lat"], c1["lng"], c2["lat"], c2["lng"]))
            if dist <= 500:
                nearby.append({"To": f"@{other_id}", "Name": other_loc["Name"], "km": dist})
        # Sort by distance
        nearby.sort(key=lambda x: x["km"])
        if nearby:
            loc["Nearby_Distances_km"] = nearby
