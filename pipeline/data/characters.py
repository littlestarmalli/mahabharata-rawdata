"""Hardcoded character definitions for the Mahabharata knowledge graph.
These are manually verified entries that override auto-extraction."""


def register_characters(add, chars, _key):
    # ── Phase 1: Core characters with full relationships ────────
    # Pandavas
    add("Yudhishthira", aliases=["Dharmaraja","Dharmaputra","Ajatashatru",
        "Bharata","Kouravya","Pandaveya"],
        father="Pandu", mother="Kunti",
        siblings=["Bhima","Arjuna","Nakula","Sahadeva"],
        spouse=["Draupadi"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Alive",
        kingdom="indraprastha", political_role="Emperor",
        skills=["Dharma","Spear combat","Dice","Statecraft","Diplomacy"],
        divine_weapons=["Spear of Dharma"],
        titles=["Dharmaraja","Ajatashatru","Emperor of Indraprastha"],
        traits=["Righteous","Truthful","Just","Compassionate","Overly virtuous"],
        character_arc=["Born to Kunti via Yama (Dharma)","Heir apparent to Hastinapura",
            "Rajasuya Yajna - crowned emperor","Lost kingdom in dice game",
            "13 years of exile","Led Pandavas in Kurukshetra War",
            "Crowned King of Hastinapura after war","Retired to forest","Ascended to Svarga"],
        key_relationships=[
            {"With":"@krishna","Type":"Guide"},
            {"With":"@duryodhana","Type":"Rival"},
            {"With":"@vidura","Type":"Guide"},
            {"With":"@draupadi","Type":"Spouse"},
            {"With":"@bhima","Type":"Brother"},
            {"With":"@arjuna","Type":"Brother"}],
        important_locations=["hastinapura","indraprastha","kamyaka_forest","kurukshetra","svarga"])
    add("Bhima", aliases=["Bhimasena","Vrikodara"],
        father="Pandu", mother="Kunti",
        siblings=["Yudhishthira","Arjuna","Nakula","Sahadeva"],
        spouse=[("Draupadi","Wife"),("Hidimba","Gandharva marriage")], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Alive",
        kingdom="indraprastha", political_role="Prince",
        skills=["Mace combat","Wrestling","Immense strength","Cooking"],
        titles=["Vrikodara","Ballava"],
        traits=["Fierce","Loyal","Wrathful","Protective","Gluttonous"],
        character_arc=["Born to Kunti via Vayu","Poisoned by Duryodhana - survived",
            "Killed Bakasura at Ekachakra","Killed Hidimba - married Hidimba (sister)",
            "Killed Jarasandha in wrestling duel","Served as cook Ballava in Virata",
            "Vowed to kill all 100 Kauravas","Killed Duhshasana - drank his blood",
            "Killed Duryodhana in mace duel","Ascended to Svarga"],
        key_relationships=[
            {"With":"@duryodhana","Type":"Enemy"},
            {"With":"@duhshasana","Type":"Enemy"},
            {"With":"@hanuman","Type":"Brother"},
            {"With":"@draupadi","Type":"Spouse"},
            {"With":"@ghatotkacha","Type":"Father"}],
        important_locations=["hastinapura","indraprastha","ekachakra","kamyaka_forest","viratanagara","kurukshetra"])
    add("Arjuna", aliases=["Partha","Dhananjaya","Savyasachi","Gudakesha",
        "Phalguna","Kiriti","Bibhatsu","Vijaya","Shvetavahana","Jishnu",
        "Kaunteya","Kounteya","Gandivadhanva"],
        father="Pandu", mother="Kunti",
        siblings=["Yudhishthira","Bhima","Nakula","Sahadeva"],
        spouse=[("Draupadi","Wife"),("Subhadra","Wife"),("Ulupi","Wife"),("Chitrangada_manipura","Wife")], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Alive",
        kingdom="indraprastha", political_role="Prince",
        skills=["Archery","Sword combat","Celestial weapons mastery","Dance","Music"],
        divine_weapons=["Gandiva bow","Pashupatastra","Brahmastra","Aindraastra",
            "Varunastra","Agneyastra","Vayavyastra","Narayanastra"],
        titles=["Partha","Savyasachi","Dhananjaya","Gudakesha","Kiriti","Bibhatsu",
            "Vijaya","Shvetavahana","Jishnu","Phalguna","Brihannala"],
        traits=["Skilled","Disciplined","Devoted","Courageous","Self-doubting"],
        character_arc=["Born to Kunti via Indra","Trained under Drona - best archer",
            "Won Draupadi at Swayamvara","Burned Khandava forest with Krishna",
            "Exile - penance to Shiva (Pashupatastra)","Trained in Svarga under Indra",
            "Lived as Brihannala in Virata","Received Bhagavad Gita from Krishna",
            "Fought and won Kurukshetra War","Killed Karna","Ashvamedha Yajna",
            "Ascended to Svarga"],
        key_relationships=[
            {"With":"@krishna","Type":"Friend"},
            {"With":"@drona","Type":"Guru"},
            {"With":"@karna","Type":"Rival"},
            {"With":"@subhadra","Type":"Spouse"},
            {"With":"@draupadi","Type":"Spouse"},
            {"With":"@abhimanyu","Type":"Father"},
            {"With":"@indra","Type":"Divine father"}],
        important_locations=["hastinapura","indraprastha","khandava_forest","svarga",
            "viratanagara","kurukshetra","manipura","dvaraka"])
    add("Nakula", father="Pandu", mother="Madri",
        siblings=["Yudhishthira","Bhima","Arjuna","Sahadeva"],
        spouse=["Draupadi"], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Alive",
        kingdom="indraprastha", political_role="Prince",
        skills=["Sword combat","Horse keeping","Ayurveda","Handsome appearance"],
        titles=["Granthika"],
        traits=["Handsome","Skilled horseman","Loyal","Humble"],
        character_arc=["Born to Madri via Ashvins","Trained under Drona",
            "Served as horse-keeper Granthika in Virata",
            "Fought in Kurukshetra War","Ascended to Svarga"],
        key_relationships=[
            {"With":"@sahadeva","Type":"Twin brother"},
            {"With":"@draupadi","Type":"Spouse"}],
        important_locations=["hastinapura","indraprastha","viratanagara","kurukshetra"])
    add("Sahadeva", father="Pandu", mother="Madri",
        siblings=["Yudhishthira","Bhima","Arjuna","Nakula"],
        spouse=["Draupadi"], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Alive",
        kingdom="indraprastha", political_role="Prince",
        skills=["Sword combat","Astrology","Cattle keeping","Intelligence"],
        titles=["Tantipala"],
        traits=["Wise","Knowledgeable","Modest","Loyal"],
        character_arc=["Born to Madri via Ashvins","Trained under Drona",
            "Served as cowherd Tantipala in Virata",
            "Fought in Kurukshetra War","Fell during Mahaprasthana"],
        key_relationships=[
            {"With":"@nakula","Type":"Twin brother"},
            {"With":"@draupadi","Type":"Spouse"}],
        important_locations=["hastinapura","indraprastha","viratanagara","kurukshetra"])

    # Kauravas - 100 sons of Gandhari + 1 daughter (Duhshala) + Yuyutsu from Sughada
    # Birth order per Adi Parva Ch.108
    _kaurava_sons = [
        "Duryodhana","Duhshasana","Duhsaha","Jalasandha","Sama_kaurava","Saha",
        "Vinda","Anuvinda","Durdharsha","Subahu","Dushpradharshana",
        "Durmarshana","Durmukha","Dushkarma","Karna_kaurava","Vivimshati",
        "Vikarna","Sulochana","Chitra","Upachitra","Chitraksha",
        "Charuchitra","Sharasana","Durmada","Dushpragaha","Vivitsu",
        "Vikata","Urnanabha","Sunabha","Nanda_kaurava","Upanandaka","Senapati",
        "Sushena","Kundodara","Mahodara","Chitrabana","Chitravarma",
        "Suvarma","Durvimochana","Ayobahu","Mahabahu_kaurava","Chitranga",
        "Chitrakundala","Bhimavega","Bhimabala","Balaki","Balavardhana",
        "Ugrayudha","Bhimakarma","Kanakayu","Dridhayudha","Dridhavarma",
        "Dridhakshatra","Somakirti","Anudara","Dridhasandha","Jarasandha_kaurava",
        "Satyasandha","Sadahsuvak","Ugrashrava","Ashvasena_kaurava","Senani",
        "Dushparajaya","Aparajita","Panditaka","Vishalaksha","Duravara",
        "Dridhahasta","Suhasta","Vatavega","Suvarcha","Adityaketu",
        "Bahvashi","Nagadanta","Ugrayayi","Kavachi","Nishangi","Pashi_kaurava",
        "Dandadhara_kaurava","Dhanurgraha","Ugra_kaurava","Bhimaratha","Vira_kaurava",
        "Virabahu","Alolupa","Abhaya","Roudrakarma","Dridharatha",
        "Anadhrishya","Kundabhedi","Viravi","Dirghalochana","Dirghabahu",
        "Mahabahu_kaurava2","Vyudhoru","Kanakadhvaja","Kundashi","Viraja",
        "Chitrasena_kaurava",
    ]
    # Key named Kauravas with extra detail
    add("Duryodhana", aliases=["Suyodhana"],
        father="Dhritarashtra", mother="Gandhari",
        spouse=["Bhanumati"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="Crown Prince",
        skills=["Mace combat","Statecraft","Leadership"],
        titles=["Suyodhana","King of Hastinapura"],
        traits=["Ambitious","Jealous","Brave","Loyal to friends","Wrathful","Proud"],
        character_arc=["Born first among 100 Kauravas","Jealous of Pandavas from childhood",
            "Poisoned Bhima as youth","Conspired lac palace (Lakshagriha)",
            "Orchestrated dice game - humiliated Draupadi","Refused to return kingdom after exile",
            "Rejected Krishna's peace offer","Led Kaurava army in Kurukshetra War",
            "Last Kaurava standing","Killed by Bhima in mace duel on Day 18"],
        key_relationships=[
            {"With":"@karna","Type":"Friend"},
            {"With":"@shakuni","Type":"Guide"},
            {"With":"@bhima","Type":"Rival"},
            {"With":"@yudhishthira","Type":"Rival"},
            {"With":"@drona","Type":"Guru"},
            {"With":"@balarama","Type":"Guru"}],
        important_locations=["hastinapura","kurukshetra"])
    add("Duhshasana", aliases=["Duhshaasana"],
        father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Vikarna", father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Vivimshati", father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Durmukha", father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Chitrasena_kaurava", aliases=["Chitrasena"],
        father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Karna_kaurava", aliases=["Karna (Kaurava)"],
        father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Sama_kaurava", aliases=["Sama"],
        father="Dhritarashtra", mother="Gandhari",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    # All remaining Kaurava sons
    for name in _kaurava_sons:
        k = name.lower().replace(' ', '_')
        if k not in chars:
            add(name, father="Dhritarashtra", mother="Gandhari",
                gender="Male", caste="Kshatriya", duty="Prince",
                dynasty="Kuru", status="Deceased")
    # Set siblings: all Kauravas are siblings of each other
    all_kaurava_keys = [_key(n) for n in _kaurava_sons] + [_key("Duhshala"), _key("Yuyutsu")]
    for kk in all_kaurava_keys:
        if kk in chars:
            chars[kk]['siblings'] = {s for s in all_kaurava_keys if s != kk and s in chars}
    # Daughter
    add("Duhshala", father="Dhritarashtra", mother="Gandhari",
        spouse=["Jayadratha"], gender="Female",
        caste="Kshatriya", duty="Princess", dynasty="Kuru")
    # Yuyutsu - from Sughada (concubine)
    add("Yuyutsu", father="Dhritarashtra", mother="Sughada",
        gender="Male", caste="Kshatriya", duty="Prince", dynasty="Kuru")
    add("Chitrasena_gandharva", aliases=["Chitrasena","gandharva king"],
        gender="Male", caste="Gandharva", duty="King")
    add("Lakshmana_kaurava", aliases=["Lakshmana"],
        father="Duryodhana", gender="Male",
        caste="Kshatriya", duty="Prince", dynasty="Kuru", status="Deceased")
    add("Bhanumati", spouse=["Duryodhana"], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru")

    # Kuru elders
    add("Dhritarashtra", aliases=["Dhritarasthra","Dritarashtra","Dhritrarashtra"],
        father="Vichitravirya", mother="Ambika",
        spouse=[("Gandhari","Wife"), ("Sughada","Concubine")],
        siblings=["Pandu","Vidura"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="King",
        skills=["Immense physical strength","Statecraft"],
        titles=["King of Hastinapura","Blind King"],
        traits=["Blind","Indecisive","Partial to sons","Grieving father","Weak-willed"],
        character_arc=["Born blind via Niyoga from Vyasa","Passed over for throne due to blindness",
            "Became regent after Pandu's death","Failed to restrain Duryodhana",
            "Approved dice game","Witnessed war through Sanjaya's narration",
            "Lost all 100 sons in war","Retired to forest with Gandhari","Died in forest fire"],
        key_relationships=[
            {"With":"@gandhari","Type":"Spouse"},
            {"With":"@duryodhana","Type":"Father"},
            {"With":"@vidura","Type":"Brother"},
            {"With":"@sanjaya","Type":"Adviser"},
            {"With":"@pandu","Type":"Brother"}],
        important_locations=["hastinapura"])
    add("Sughada", aliases=["Vaishya maid","Vaishya woman"],
        spouse=[("Dhritarashtra","Concubine")], gender="Female",
        caste="Vaishya", dynasty="Kuru")
    add("Pandu", father="Vichitravirya", mother="Ambalika",
        spouse=[("Kunti","Wife"),("Madri","Wife")],
        siblings=["Dhritarashtra","Vidura"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="King",
        skills=["Archery","Warfare","Conquest"],
        titles=["Pandu the Pale","King of Hastinapura"],
        traits=["Valiant","Cursed","Remorseful","Expansionist"],
        character_arc=["Born to Ambalika via Niyoga from Vyasa","Crowned king (Dhritarashtra blind)",
            "Conquered many kingdoms","Cursed by sage Kindama","Retired to forest",
            "Sons born via divine boons of Kunti and Madri","Died from curse when approaching Madri"],
        key_relationships=[
            {"With":"@kunti","Type":"Spouse"},
            {"With":"@madri","Type":"Spouse"},
            {"With":"@dhritarashtra","Type":"Brother"}],
        important_locations=["hastinapura","shatashriga"])
    add("Vidura", aliases=["Kshatta"],
        siblings=["Dhritarashtra","Pandu"], gender="Male",
        caste="Kshatriya", duty="Minister", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="Prime Minister",
        skills=["Diplomacy","Dharma","Statecraft","Wisdom"],
        titles=["Kshatta","Dharma incarnation"],
        traits=["Wise","Righteous","Impartial","Courageous speaker of truth"],
        character_arc=["Born to maid via Niyoga from Vyasa","Served as minister of Hastinapura",
            "Warned Pandavas of Lakshagriha plot","Opposed dice game",
            "Counseled Dhritarashtra for peace","Left court in disgust","Died during forest retirement"],
        key_relationships=[
            {"With":"@yudhishthira","Type":"Guide"},
            {"With":"@dhritarashtra","Type":"Brother"},
            {"With":"@kunti","Type":"Ally"}],
        important_locations=["hastinapura"])
    add("Kunti", aliases=["Pritha"],
        father="Shurasena",
        spouse=[("Pandu","Husband"),("Surya","Divine boon"),("Yama","Divine boon"),("Vayu","Divine boon"),("Indra","Divine boon")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="Queen Mother",
        skills=["Divine invocation mantra","Devotion","Endurance"],
        titles=["Pritha","Queen Mother"],
        traits=["Devoted mother","Strong","Secretive","Sacrificing","Resilient"],
        character_arc=["Born as Pritha - adopted by Kuntibhoja","Received divine mantra from Durvasa",
            "Invoked Surya - bore Karna (abandoned)","Married Pandu",
            "Bore Yudhishthira (Yama), Bhima (Vayu), Arjuna (Indra)",
            "Shared mantra with Madri for Nakula & Sahadeva",
            "Raised Pandavas in Hastinapura after Pandu's death",
            "Revealed Karna's identity before war","Retired to forest","Died in forest fire"],
        key_relationships=[
            {"With":"@karna","Type":"Secret mother"},
            {"With":"@yudhishthira","Type":"Mother"},
            {"With":"@vidura","Type":"Ally"},
            {"With":"@pandu","Type":"Spouse"},
            {"With":"@draupadi","Type":"Mother-in-law"}],
        important_locations=["hastinapura","kunti_kingdom","indraprastha"])
    add("Madri", spouse=[("Pandu","Husband"),("Ashvins","Divine boon")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru", status="Deceased")
    add("Gandhari", father="Subala",
        spouse=[("Dhritarashtra","Husband")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="Queen",
        skills=["Austerity","Divine powers from tapas"],
        titles=["Queen of Hastinapura","Blindfolded Queen"],
        traits=["Devoted wife","Strong-willed","Blind devotion","Grieving mother","Powerful"],
        character_arc=["Born princess of Gandhara","Blindfolded herself after marrying blind Dhritarashtra",
            "Mother of 100 sons and 1 daughter","Cursed Krishna for not preventing war",
            "Lost all sons in war","Retired to forest","Died in forest fire"],
        key_relationships=[
            {"With":"@dhritarashtra","Type":"Spouse"},
            {"With":"@duryodhana","Type":"Mother"},
            {"With":"@shakuni","Type":"Brother"},
            {"With":"@krishna","Type":"Adversary"},
            {"With":"@kunti","Type":"Rival"}],
        important_locations=["hastinapura","gandhara"])

    # Bhishma's line
    add("Bhishma", aliases=["Devavrata","Gangeya","Shantanava"],
        father="Shantanu", mother="Ganga", gender="Male",
        caste="Kshatriya", duty="Regent", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="Regent and Grand-sire",
        skills=["Archery","All weapons mastery","Statecraft","Celibacy vow"],
        divine_weapons=["Brahmastra","Prasvapana"],
        titles=["Devavrata","Gangeya","Pitamaha","Grand-sire of Kuru"],
        traits=["Vow-keeper","Invincible","Wise","Tragic","Bound by duty"],
        character_arc=["Born to Shantanu and Ganga - 8th Vasu","Took vow of celibacy (Bhishma Pratigya)",
            "Abducted Amba, Ambika, Ambalika for Vichitravirya",
            "Served as regent of Hastinapura across generations",
            "Became Kaurava commander (Days 1-10)","Shot by Arjuna using Shikhandi as shield",
            "Lay on bed of arrows","Taught Shanti Parva wisdom","Died on Uttarayana"],
        key_relationships=[
            {"With":"@arjuna","Type":"Grandfather figure"},
            {"With":"@duryodhana","Type":"Grandfather figure"},
            {"With":"@drona","Type":"Ally"},
            {"With":"@shikhandi","Type":"Adversary"},
            {"With":"@amba","Type":"Adversary"},
            {"With":"@parashurama","Type":"Guru"}],
        important_locations=["hastinapura","kurukshetra"])
    add("Shantanu", aliases=["king of Hastinapura"],
        spouse=[("Ganga","Wife"),("Satyavati","Wife")],
        father="Pratipa", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="King",
        traits=["Romantic","Generous","Just"],
        important_locations=["hastinapura"])
    add("Ganga", aliases=["Bhagirathi","Jahnavi"],
        spouse=["Shantanu"], gender="Female",
        duty="River goddess", status="Immortal")
    add("Satyavati", aliases=["Matsyagandha","Kali"],
        spouse=[("Shantanu","Husband"),("Parashara","Pre-marital union")], gender="Female",
        duty="Queen", dynasty="Kuru", status="Deceased")
    add("Vichitravirya",
        father="Shantanu", mother="Satyavati",
        siblings=["Chitrangada_kuru"],
        spouse=[("Ambika","Wife"),("Ambalika","Wife")], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased")
    add("Chitrangada_kuru", aliases=["Chitrangada"],
        father="Shantanu", mother="Satyavati",
        siblings=["Vichitravirya"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased")
    add("Ambika", spouse=[("Vichitravirya","Husband"),("Vyasa","Niyoga")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru")
    add("Ambalika", spouse=[("Vichitravirya","Husband"),("Vyasa","Niyoga")], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Kuru")
    add("Amba", gender="Female", caste="Kshatriya", duty="Princess")

    # Vyasa
    add("Vyasa", aliases=["Krishna Dvaipayana","Vedavyasa","Dvaipayana"],
        father="Parashara", mother="Satyavati",
        spouse=[("Ambika","Niyoga"),("Ambalika","Niyoga")],
        gender="Male",
        caste="Brahmin", duty="Sage", status="Immortal",
        skills=["Vedic knowledge","Authorship","Prophecy","Niyoga"],
        titles=["Vedavyasa","Krishna Dvaipayana","Chiranjivi"],
        traits=["Wise","Omniscient narrator","Dark-complexioned","Detached"],
        character_arc=["Born to Parashara and Satyavati on island","Compiled the Vedas",
            "Authored the Mahabharata","Fathered Dhritarashtra, Pandu, Vidura via Niyoga",
            "Witnessed and narrated the great war","Immortal sage"],
        key_relationships=[
            {"With":"@dhritarashtra","Type":"Father (Niyoga)"},
            {"With":"@pandu","Type":"Father (Niyoga)"},
            {"With":"@satyavati","Type":"Mother"},
            {"With":"@vaishampayana","Type":"Disciple"}],
        important_locations=["hastinapura","badarikashrama"])
    add("Parashara", spouse=[("Satyavati","Pre-marital union")],
        gender="Male", caste="Brahmin", duty="Sage")
    add("Shuka", aliases=["son of Vyasa"],
        father="Vyasa", gender="Male",
        caste="Brahmin", duty="Sage")

    # Krishna's family
    add("Krishna", aliases=["Vasudeva","Vaasudeva","Keshava","Govinda","Madhava",
        "Janardana","Achyuta","Hari","Hrishikesha","Madhusudana","Damodara",
        "Vrishni","Varshneya","Dasharha","Pundarikaksha","Shouri","Purushottama"],
        father="Vasudeva_father", mother="Devaki",
        siblings=["Balarama","Subhadra"],
        spouse=[("Rukmini","Wife"),("Satyabhama","Wife"),("Jambavati","Wife")], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Yadava", status="Deceased",
        kingdom="dvaraka", political_role="King of Dvaraka",
        skills=["Diplomacy","Statecraft","Charioteer","Divine knowledge","Sudarshana Chakra","Flute"],
        divine_weapons=["Sudarshana Chakra","Kaumodaki mace","Sharnga bow","Nandaka sword"],
        titles=["Vasudeva","Keshava","Govinda","Madhava","Janardana","Purushottama",
            "Lord of Dvaraka","Yogeshvara","Parthasarathi"],
        traits=["Wise","Strategic","Divine","Playful","Just","Compassionate","Pragmatic"],
        character_arc=["Born to Devaki and Vasudeva in prison","Grew up in Gokula/Vrindavana",
            "Killed Kamsa","Built Dvaraka","Befriended Arjuna",
            "Burned Khandava forest with Arjuna","Killed Shishupala at Rajasuya",
            "Peace ambassador to Kauravas (failed)","Charioteer of Arjuna in war",
            "Delivered Bhagavad Gita","Guided Pandavas to victory","Cursed by Gandhari",
            "Yadava civil war (Mausala)","Shot by hunter Jara","Left mortal world"],
        key_relationships=[
            {"With":"@arjuna","Type":"Friend"},
            {"With":"@yudhishthira","Type":"Guide"},
            {"With":"@draupadi","Type":"Friend"},
            {"With":"@duryodhana","Type":"Adversary"},
            {"With":"@karna","Type":"Adversary"},
            {"With":"@balarama","Type":"Brother"},
            {"With":"@subhadra","Type":"Sister"},
            {"With":"@bhishma","Type":"Respected elder"}],
        important_locations=["dvaraka","mathura","vrindavana","hastinapura","indraprastha",
            "kurukshetra","khandava_forest"])
    add("Balarama", aliases=["Baladeva","Halayudhu","Haladhara","Sankarshana"],
        father="Vasudeva_father", mother="Rohini",
        siblings=["Krishna","Subhadra"],
        spouse=["Revati"], gender="Male",
        caste="Kshatriya", duty="Prince", dynasty="Yadava", status="Deceased",
        kingdom="dvaraka", political_role="Prince of Dvaraka",
        skills=["Mace combat","Plough weapon"],
        divine_weapons=["Plough (Hala)","Mace (Saunanda)"],
        titles=["Baladeva","Halayudha","Sankarshana"],
        traits=["Strong","Hot-tempered","Neutral in war","Fond of Duryodhana"],
        character_arc=["Born to Rohini (transferred from Devaki)","Trained Duryodhana and Bhima in mace",
            "Refused to fight in war (neutral)","Went on pilgrimage during war",
            "Angered at Bhima's foul blow to Duryodhana","Died during Mausala"],
        key_relationships=[
            {"With":"@krishna","Type":"Brother"},
            {"With":"@duryodhana","Type":"Guru"},
            {"With":"@bhima","Type":"Guru"}],
        important_locations=["dvaraka","mathura"])
    add("Subhadra",
        father="Vasudeva_father",
        siblings=["Krishna","Balarama"],
        spouse=["Arjuna"], gender="Female",
        caste="Kshatriya", duty="Princess", dynasty="Yadava")
    add("Vasudeva_father", aliases=["Vasudeva","Anakadundubhi"],
        father="Shurasena",
        spouse=[("Devaki","Wife"),("Rohini","Wife")], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Yadava")
    add("Devaki", spouse=["Vasudeva_father"], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Yadava")
    add("Rohini", spouse=["Vasudeva_father"], gender="Female",
        caste="Kshatriya", dynasty="Yadava")
    add("Rukmini", aliases=["daughter of Bhishmaka"],
        father="Bhishmaka",
        spouse=["Krishna"], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Yadava")
    add("Satyabhama", spouse=["Krishna"], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Yadava")
    add("Jambavati", spouse=["Krishna"], gender="Female",
        duty="Queen", dynasty="Yadava")
    add("Pradyumna", father="Krishna", mother="Rukmini", gender="Male",
        caste="Kshatriya", duty="Prince", dynasty="Yadava")
    add("Samba", father="Krishna", mother="Jambavati", gender="Male",
        caste="Kshatriya", duty="Prince", dynasty="Yadava")
    add("Revati", spouse=["Balarama"], gender="Female",
        duty="Queen", dynasty="Yadava")

    # Karna's family
    add("Karna", aliases=["Radheya","Vasusena","Anga-raja","Vrisha","Vaikartana"],
        mother="Kunti", father="Surya",
        spouse=[("Vrushali","Wife")], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Anga", status="Deceased",
        kingdom="anga", political_role="King of Anga",
        skills=["Archery","Generosity","Chariot warfare"],
        divine_weapons=["Vijaya bow","Shakti weapon (from Indra)","Brahmastra",
            "Bhargavastra","Nagastra"],
        titles=["Radheya","Vasusena","Anga-raja","Danveer Karna","Vaikartana"],
        traits=["Generous","Loyal","Brave","Tragic","Cursed","Honorable"],
        character_arc=["Born to Kunti via Surya - abandoned at birth",
            "Raised by charioteer Adhiratha and Radha","Trained under Parashurama - cursed",
            "Humiliated at tournament - befriended by Duryodhana",
            "Made King of Anga by Duryodhana","Gave away Kavacha-Kundala to Indra",
            "Learned true identity from Kunti before war","Fought as Kaurava commander",
            "Killed by Arjuna on Day 17"],
        key_relationships=[
            {"With":"@duryodhana","Type":"Friend"},
            {"With":"@arjuna","Type":"Rival"},
            {"With":"@parashurama","Type":"Guru"},
            {"With":"@kunti","Type":"Mother"},
            {"With":"@indra","Type":"Adversary"},
            {"With":"@krishna","Type":"Adversary"}],
        important_locations=["hastinapura","anga","kurukshetra","champapuri"])
    add("Vrishasena", father="Karna", mother="Vrushali", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Anga", status="Deceased")
    add("Vrishaketu", father="Karna", mother="Vrushali", gender="Male",
        caste="Kshatriya", dynasty="Anga")
    add("Radha", aliases=["Karna's foster mother"],
        spouse=["Adhiratha"], gender="Female",
        caste="Suta")
    add("Adhiratha", spouse=["Radha"], gender="Male",
        caste="Suta", duty="Charioteer")
    add("Vrushali", spouse=["Karna"], gender="Female")

    # Next generation - Upapandavas (Draupadi's 5 sons, one from each Pandava)
    add("Prativindhya", father="Yudhishthira", mother="Draupadi", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased")
    add("Sutasoma", father="Bhima", mother="Draupadi", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased")
    add("Shrutakirti", father="Arjuna", mother="Draupadi", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased")
    add("Shatanika", father="Nakula", mother="Draupadi", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased")
    add("Shrutasena", father="Sahadeva", mother="Draupadi", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased")
    # Other children
    add("Abhimanyu", aliases=["Soubhadra"],
        father="Arjuna", mother="Subhadra",
        spouse=["Uttaraa"], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Kuru", status="Deceased",
        kingdom="indraprastha", political_role="Prince",
        skills=["Archery","Chakravyuha penetration","Chariot warfare"],
        titles=["Soubhadra"],
        traits=["Brave","Young","Fearless","Tragic"],
        character_arc=["Born to Arjuna and Subhadra","Learned Chakravyuha entry in the womb",
            "Married Uttaraa of Matsya","Entered Chakravyuha on Day 13",
            "Killed treacherously by 7 warriors"],
        key_relationships=[
            {"With":"@arjuna","Type":"Father"},
            {"With":"@krishna","Type":"Uncle"},
            {"With":"@jayadratha","Type":"Enemy"},
            {"With":"@drona","Type":"Enemy"}],
        important_locations=["dvaraka","indraprastha","viratanagara","kurukshetra"])
    add("Ghatotkacha", father="Bhima", mother="Hidimba", gender="Male",
        caste="Rakshasa", duty="Warrior", status="Deceased",
        skills=["Shape-shifting","Sorcery","Aerial combat","Immense strength"],
        traits=["Brave","Devoted to father","Fierce","Selfless"],
        character_arc=["Born to Bhima and Hidimba in forest","Grew up among Rakshasas",
            "Joined Pandava army in war","Wreaked havoc on Kaurava forces at night",
            "Killed by Karna's Shakti weapon on Day 14"],
        key_relationships=[
            {"With":"@bhima","Type":"Father"},
            {"With":"@karna","Type":"Enemy"}],
        important_locations=["kurukshetra"])
    add("Parikshit", father="Abhimanyu", mother="Uttaraa", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru")
    add("Babhruvahana", father="Arjuna", mother="Chitrangada_manipura",
        gender="Male", caste="Kshatriya", duty="King")
    add("Iravan", father="Arjuna", mother="Ulupi", gender="Male",
        caste="Kshatriya", duty="Warrior", status="Deceased")
    add("Uttaraa", spouse=["Abhimanyu"], gender="Female",
        caste="Kshatriya", duty="Princess", dynasty="Matsya")

    # Drona's family
    add("Drona", aliases=["Dronacharya","preceptor","acharya"],
        father="Bharadvaja",
        spouse=["Kripi"], gender="Male",
        caste="Brahmin", duty="Teacher", dynasty="Kuru", status="Deceased",
        kingdom="hastinapura", political_role="Royal preceptor",
        skills=["All weapons mastery","Teaching","Archery","Brahmastra"],
        divine_weapons=["Brahmastra","Brahmashira","Agneyastra","Varunastra"],
        titles=["Dronacharya","Acharya","Guru of princes"],
        traits=["Greatest teacher","Partial to Arjuna","Vengeful","Tragic"],
        character_arc=["Born from pot (drona) to sage Bharadvaja","Trained under Parashurama",
            "Humiliated by Drupada","Became teacher of Kuru princes",
            "Favored Arjuna as best student","Demanded Ekalavya's thumb",
            "Captured Drupada - took half his kingdom","Fought for Kauravas",
            "Became commander after Bhishma fell (Days 11-15)",
            "Killed by Dhrishtadyumna after Ashvatthama deception"],
        key_relationships=[
            {"With":"@arjuna","Type":"Guru"},
            {"With":"@ashvatthama","Type":"Father"},
            {"With":"@drupada","Type":"Rival"},
            {"With":"@ekalavya","Type":"Guru"},
            {"With":"@parashurama","Type":"Guru"},
            {"With":"@dhrishtadyumna","Type":"Enemy"}],
        important_locations=["hastinapura","panchala","kurukshetra"])
    add("Ashvatthama", aliases=["Dronaputra"],
        father="Drona", mother="Kripi", gender="Male",
        caste="Brahmin", duty="Warrior", dynasty="Kuru", status="Immortal",
        skills=["All weapons mastery","Brahmastra","Narayanastra"],
        divine_weapons=["Narayanastra","Brahmashira","Brahmastra","Agneyastra"],
        titles=["Dronaputra","Chiranjivi"],
        traits=["Wrathful","Vengeful","Cursed","Immortal"],
        character_arc=["Son of Drona and Kripi","Grew up in poverty",
            "Trained alongside Kuru princes","Fought for Kauravas",
            "Attacked Pandava camp at night (Sauptika)","Killed Upapandavas in sleep",
            "Launched Brahmashira at Pandavas","Cursed by Krishna to wander 3000 years"],
        key_relationships=[
            {"With":"@drona","Type":"Father"},
            {"With":"@duryodhana","Type":"Friend"},
            {"With":"@arjuna","Type":"Rival"},
            {"With":"@dhrishtadyumna","Type":"Enemy"},
            {"With":"@krishna","Type":"Adversary"}],
        important_locations=["hastinapura","kurukshetra"])
    add("Bharadvaja", gender="Male", caste="Brahmin", duty="Sage")
    add("Kripi", aliases=["Sharadvati"],
        father="Sharadvat",
        siblings=["Kripa"],
        spouse=["Drona"], gender="Female",
        caste="Brahmin")
    add("Kripa", aliases=["Kripacharya","Sharadvata","Goutama"],
        father="Sharadvat",
        siblings=["Kripi"], gender="Male",
        caste="Brahmin", duty="Teacher", dynasty="Kuru", status="Immortal")
    add("Sharadvat", gender="Male", caste="Brahmin", duty="Sage")

    # Drupada's family
    add("Drupada", aliases=["Yajnasena","Parshata"],
        father="Prishata", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Panchala", status="Deceased")
    add("Draupadi", aliases=["Droupadi","Panchali","Krishnaa","Yajnaseni"],
        father="Drupada",
        siblings=["Dhrishtadyumna","Shikhandi"],
        spouse=[("Yudhishthira","Husband"),("Bhima","Husband"),("Arjuna","Husband"),("Nakula","Husband"),("Sahadeva","Husband")],
        gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Panchala",
        kingdom="indraprastha", political_role="Queen",
        skills=["Statesmanship","Devotion","Endurance"],
        titles=["Panchali","Krishnaa","Yajnaseni","Queen of Indraprastha"],
        traits=["Fiery","Beautiful","Vengeful","Devoted","Proud","Resilient"],
        character_arc=["Born from sacrificial fire of Drupada","Won by Arjuna at Swayamvara",
            "Married all 5 Pandavas","Queen of Indraprastha",
            "Humiliated in dice game - vowed vengeance","13 years of exile",
            "Served as Sairandhri in Virata","Witnessed vengeance in war",
            "Lost all 5 sons (Upapandavas)","Fell during Mahaprasthana"],
        key_relationships=[
            {"With":"@krishna","Type":"Friend"},
            {"With":"@bhima","Type":"Spouse"},
            {"With":"@arjuna","Type":"Spouse"},
            {"With":"@duhshasana","Type":"Enemy"},
            {"With":"@duryodhana","Type":"Enemy"},
            {"With":"@kunti","Type":"Mother-in-law"}],
        important_locations=["panchala","hastinapura","indraprastha","kamyaka_forest","viratanagara","kurukshetra"])
    add("Dhrishtadyumna", aliases=["Panchala prince"],
        father="Drupada",
        siblings=["Draupadi","Shikhandi"], gender="Male",
        caste="Kshatriya", duty="Commander", dynasty="Panchala", status="Deceased")
    add("Shikhandi", father="Drupada",
        siblings=["Draupadi","Dhrishtadyumna"], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Panchala", status="Deceased")
    add("Prishata", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Panchala", status="Deceased")

    # Other key characters
    add("Jayadratha", aliases=["Saindhava","king of Sindhu"],
        spouse=["Duhshala"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Sindhu", status="Deceased",
        kingdom="sindhu", political_role="King of Sindhu",
        skills=["Warfare","Boon of Shiva (hold Pandavas)"],
        traits=["Arrogant","Lustful","Cowardly"],
        character_arc=["King of Sindhu kingdom","Married Duhshala (Kaurava sister)",
            "Tried to abduct Draupadi in forest","Received boon from Shiva",
            "Blocked Pandavas from saving Abhimanyu (Day 13)",
            "Killed by Arjuna before sunset on Day 14"],
        key_relationships=[
            {"With":"@arjuna","Type":"Enemy"},
            {"With":"@abhimanyu","Type":"Enemy"},
            {"With":"@duryodhana","Type":"Ally"},
            {"With":"@duhshala","Type":"Spouse"}],
        important_locations=["sindhu","kurukshetra","kamyaka_forest"])
    add("Shakuni", aliases=["Soubala"],
        father="Subala", siblings=["Gandhari"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Gandhara", status="Deceased",
        kingdom="gandhara", political_role="King of Gandhara",
        skills=["Dice","Deception","Manipulation"],
        titles=["Soubala","Master of dice"],
        traits=["Cunning","Manipulative","Vengeful","Scheming"],
        character_arc=["Prince of Gandhara","Vowed revenge against Kuru (for Gandhari's marriage)",
            "Mastermind of dice game","Manipulated Duryodhana against Pandavas",
            "Fought in war","Killed by Sahadeva on Day 18"],
        key_relationships=[
            {"With":"@duryodhana","Type":"Guide"},
            {"With":"@gandhari","Type":"Brother"},
            {"With":"@yudhishthira","Type":"Enemy"},
            {"With":"@sahadeva","Type":"Enemy"}],
        important_locations=["hastinapura","gandhara","kurukshetra"])
    add("Subala", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Gandhara", status="Deceased")
    add("Shalya", aliases=["king of Madra","Madra king"],
        siblings=["Madri"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Madra", status="Deceased",
        kingdom="madra", political_role="King of Madra",
        skills=["Chariot warfare","Mace combat"],
        traits=["Honorable","Tricked into fighting for Kauravas"],
        character_arc=["Uncle of Pandavas (Madri's brother)","Tricked by Duryodhana into joining Kauravas",
            "Served as Karna's charioteer (to demoralize)","Became last Kaurava commander on Day 18",
            "Killed by Yudhishthira"],
        key_relationships=[
            {"With":"@yudhishthira","Type":"Nephew/Enemy"},
            {"With":"@karna","Type":"Antagonist (charioteer)"},
            {"With":"@duryodhana","Type":"Ally"}],
        important_locations=["madra","kurukshetra"])
    add("Ekalavya", aliases=["Nishada prince"], gender="Male",
        caste="Nishada", duty="Warrior",
        skills=["Archery","Self-taught mastery"],
        traits=["Devoted","Self-taught","Tragic","Humble"],
        character_arc=["Nishada prince","Rejected by Drona as student",
            "Built clay idol of Drona and self-trained","Surpassed Arjuna in archery",
            "Cut off his thumb as guru-dakshina to Drona"],
        key_relationships=[
            {"With":"@drona","Type":"Guru"},
            {"With":"@arjuna","Type":"Rival"}])
    add("Shishupala", aliases=["king of Chedi","Chedi king"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Chedi", status="Deceased")
    add("Jarasandha", aliases=["king of Magadha"],
        father="Brihadratha", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Magadha", status="Deceased")
    add("Virata", aliases=["king of Matsya"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Matsya", status="Deceased")
    add("Kritavarma", aliases=["Hardikya"],
        father="Hridika", gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Yadava")
    add("Satyaki", aliases=["Yuyudhana","Satvata"], gender="Male",
        caste="Kshatriya", duty="Warrior", dynasty="Yadava")
    add("Bhagadatta", aliases=["king of Pragjyotisha"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Pragjyotisha", status="Deceased")
    add("Bhurishrava", father="Somadatta", gender="Male",
        caste="Kshatriya", duty="Warrior", status="Deceased")
    add("Susharma", aliases=["king of Trigarta"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Trigarta")
    add("Dhrishtaketu", aliases=["king of Chedi"],
        father="Shishupala", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Chedi", status="Deceased")
    add("Sanjaya", aliases=["Dhritarashtra's aide"],
        father="Gavalgana", gender="Male",
        caste="Suta", duty="Charioteer", dynasty="Kuru")
    add("Hidimba", spouse=[("Bhima","Gandharva marriage")], gender="Female",
        caste="Rakshasa")
    add("Chitrangada_manipura", aliases=["Chitrangada"],
        spouse=["Arjuna"], gender="Female",
        caste="Kshatriya", duty="Princess", dynasty="Manipura")

    # Gods / divine
    add("Indra", aliases=["Shatakratu","Shakra","Purandara","Vasava",
        "Maghavan","lord of the gods","king of the gods"],
        spouse=[("Kunti","Divine boon")],
        gender="Male",
        caste="Deva", duty="King of gods", status="Immortal")
    add("Brahma", aliases=["Prajapati","Pitamaha","creator"], gender="Male",
        caste="Deva", duty="Creator", status="Immortal")
    add("Vishnu", aliases=["Narayana","Preserver"], gender="Male",
        caste="Deva", duty="Preserver", status="Immortal")
    add("Shiva", aliases=["Mahadeva","Maheshvara","Rudra","Pashupati","Bhava",
        "Hara","Tryambaka","Shankar","Shankara","Pinaka","Sthanu"], gender="Male",
        caste="Deva", duty="Destroyer", status="Immortal")
    add("Yama", aliases=["Dharma","god of death","lord of the dead"],
        spouse=[("Kunti","Divine boon")],
        gender="Male",
        caste="Deva", duty="God of death", status="Immortal")
    add("Vayu", aliases=["wind-god"],
        spouse=[("Kunti","Divine boon")],
        gender="Male",
        caste="Deva", duty="Wind god", status="Immortal")
    add("Surya", aliases=["sun-god","Aditya","Vivasvat","Vivasvata"],
        spouse=[("Kunti","Divine boon")],
        gender="Male",
        caste="Deva", duty="Sun god", status="Immortal")
    add("Agni", aliases=["fire-god","Pavaka","Hutashana"], gender="Male",
        caste="Deva", duty="Fire god", status="Immortal")
    add("Ashvins", aliases=["Ashwini Kumaras","Nasatya","Dasra"],
        spouse=[("Madri","Divine boon")],
        gender="Male",
        caste="Deva", duty="Divine physicians", status="Immortal")
    add("Varuna", aliases=["lord of the waters","water-god"], gender="Male",
        caste="Deva", duty="Water god", status="Immortal")
    add("Kubera", aliases=["Vaishravana","Dhanada","god of wealth"],
        father="Vishrava", gender="Male",
        caste="Deva", duty="God of wealth", status="Immortal")
    add("Kartikeya", aliases=["Skanda","Kumara","Subrahmanya"],
        father="Shiva", mother="Parvati", gender="Male",
        caste="Deva", duty="God of war", status="Immortal")
    add("Lakshmi", aliases=["Shri"], spouse=["Vishnu"], gender="Female",
        caste="Deva", duty="Goddess of fortune", status="Immortal")
    add("Parvati", aliases=["Uma"], spouse=["Shiva"], gender="Female",
        caste="Deva", duty="Goddess", status="Immortal")
    add("Sarasvati", aliases=["goddess of learning"],
        spouse=["Brahma"], gender="Female",
        caste="Deva", duty="Goddess of learning", status="Immortal")

    # Narrators / sages
    add("Ugrasrava", aliases=["Souti"],
        father="Lomaharshana", gender="Male",
        caste="Suta", duty="Narrator")
    add("Vaishampayana", aliases=["narrator"], gender="Male",
        caste="Brahmin", duty="Sage")
    add("Janamejaya", father="Parikshit", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru")
    add("Narada", aliases=["divine sage","Devarshi"], gender="Male",
        caste="Deva", duty="Sage", status="Immortal")
    add("Parashurama", aliases=["Bhargava","Rama"],
        father="Jamadagni", mother="Renuka", gender="Male",
        caste="Brahmin", duty="Warrior sage", status="Immortal")
    add("Hanuman", father="Vayu", mother="Anjana", gender="Male",
        caste="Vanara", duty="Warrior", status="Immortal")

    # Epic / embedded story characters
    add("Nala", aliases=["Nishadha","Punyashloka","Bahuka","king of Nishadha"],
        spouse=["Damayanti"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Nishadha")
    add("Damayanti", father="Bhima_vidarbha", spouse=["Nala"], gender="Female",
        caste="Kshatriya", duty="Queen", dynasty="Vidarbha")
    add("Bhima_vidarbha", aliases=["king of Vidarbha"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Vidarbha")
    add("Savitri", spouse=["Satyavan"], gender="Female",
        caste="Kshatriya", duty="Princess")
    add("Satyavan", spouse=["Savitri"], gender="Male",
        caste="Kshatriya")
    add("Ravana", aliases=["king of Lanka","Rakshasa king"], gender="Male",
        caste="Rakshasa", duty="King", dynasty="Lanka", status="Deceased")
    add("Sugriva", aliases=["monkey king"], gender="Male",
        caste="Vanara", duty="King")
    add("Prahlada", father="Hiranyakashipu", gender="Male",
        caste="Daitya")
    add("Hiranyakashipu", gender="Male",
        caste="Daitya", duty="King", status="Deceased")

    # More warriors / kings
    add("Bahlika", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased")
    add("Bhagiratha", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Ikshvaku")
    add("Rituparna", aliases=["king of Ayodhya"], gender="Male",
        caste="Kshatriya", duty="King", dynasty="Ikshvaku")
    add("Marutta", father="Avikshit", gender="Male",
        caste="Kshatriya", duty="King")
    add("Brihadbala", gender="Male",
        caste="Kshatriya", duty="Warrior", status="Deceased")
    add("Chekitana", gender="Male",
        caste="Kshatriya", duty="Warrior")
    add("Somadatta", gender="Male",
        caste="Kshatriya", duty="King")
    add("Hridika", gender="Male",
        caste="Kshatriya", dynasty="Yadava")
    add("Gavalgana", gender="Male", caste="Suta")
    add("Lomaharshana", gender="Male", caste="Suta", duty="Narrator")
    add("Bhishmaka", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Vidarbha")
    add("Shurasena", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Yadava")
    add("Pratipa", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru", status="Deceased")
    add("Brihadratha", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Magadha", status="Deceased")
    add("Vishrava", gender="Male", caste="Brahmin", duty="Sage")
    add("Jamadagni", gender="Male", caste="Brahmin", duty="Sage")
    add("Renuka", gender="Female")
    add("Anjana", gender="Female", caste="Vanara")
    add("Avikshit", gender="Male", caste="Kshatriya", duty="King")
    add("Ulupi", spouse=["Arjuna"], gender="Female",
        caste="Naga", duty="Princess")
    add("Uttara", father="Virata", gender="Male",
        caste="Kshatriya", duty="Prince", dynasty="Matsya", status="Deceased")

    # Sages
    add("Agastya", aliases=["Agasti"], gender="Male",
        caste="Brahmin", duty="Sage")
    add("Vasishtha", aliases=["Vashishtha"], gender="Male",
        caste="Brahmin", duty="Sage")
    add("Galava", gender="Male", caste="Brahmin", duty="Sage")
    add("Ashtavakra", gender="Male", caste="Brahmin", duty="Sage")
    add("Kapila", gender="Male", caste="Brahmin", duty="Sage")
    add("Devala", gender="Male", caste="Brahmin", duty="Sage")
    add("Ushanas", aliases=["Shukra","Shukracharya","preceptor of the demons"],
        gender="Male", caste="Brahmin", duty="Sage", status="Immortal")
    add("Matali", aliases=["Indra's charioteer"], gender="Male",
        caste="Deva", duty="Charioteer")
    add("Vritra", aliases=["demon"], gender="Male",
        caste="Asura", status="Deceased")
    add("Nara", gender="Male", caste="Deva", duty="Sage")
    add("Daruka", aliases=["Krishna's charioteer"], gender="Male",
        duty="Charioteer", dynasty="Yadava")
    add("Manu", aliases=["Vaivasvata"], gender="Male",
        duty="Progenitor")

    # Remaining core
    add("Aditi", gender="Female", caste="Deva", duty="Mother of gods")
    add("Daksha", aliases=["Prajapati"], gender="Male",
        caste="Deva", duty="Prajapati")
    add("Kashyapa", gender="Male", caste="Brahmin", duty="Sage")
    add("Soma", gender="Male", caste="Deva")
    add("Takshaka", gender="Male", caste="Naga", duty="King")
    add("Vinata", gender="Female")
    add("Kadru", gender="Female")
    add("Garuda", aliases=["Suparna"], mother="Vinata", gender="Male",
        duty="Mount of Vishnu")
    add("Yadu", gender="Male",
        caste="Kshatriya", dynasty="Yadava")
    add("Puru", gender="Male",
        caste="Kshatriya", dynasty="Puru")
    add("Sagara", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Ikshvaku")
    add("Mandhata", aliases=["Mandhatar"], father="Yuvanashva", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Ikshvaku")
    add("Muchukunda", gender="Male",
        caste="Kshatriya", duty="King")
    add("Samvarana", gender="Male",
        caste="Kshatriya", duty="King", dynasty="Kuru")
    add("Rishyashringa", gender="Male",
        caste="Brahmin", duty="Sage")
    add("Svayambhu", gender="Male")
