#!/usr/bin/env python3
"""
build_characters.py — Single-file character extraction pipeline (debug)

Extracts all character names from Mahabharata volumes, classifies them,
groups variants, builds a character JSON with aliases, counts, appearances,
and removes non-character entries (English words, modern terms, etc.).

Pipeline steps:
  1. Extract all capitalized words from 10 volumes (chapters + footnotes)
  2. Classify as real names vs English words using heuristics + word lists
  3. Filter remaining English, group plurals/double-vowels, find edit-distance pairs
  4. Build character entries with aliases using union-find + existing DB
  5. Add Count (total mentions) and Appearance (per-volume chapter list)
  6. Remove non-character entries (English words, modern places, generic terms)

Usage:
    python debug/build_characters.py

Output:
    debug/characters_debug.json
"""

import os
import re
import json
from collections import Counter, defaultdict

# ─── Paths ───────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOLUMES_DIR = os.path.join(BASE_DIR, 'output', 'volumes')
CHAR_DB_FILE = os.path.join(BASE_DIR, 'output', 'json', 'characters.json')
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'characters_debug.json')
NUM_VOLUMES = 10


# =====================================================================
# ENGLISH WORD LISTS (for filtering non-character names)
# =====================================================================

# Common English words that appear capitalized at sentence starts
ENGLISH_WORDS = {
    'The','That','This','These','Those','Which','Where','When','What','Also',
    'Here','There','Thus','Hence','Therefore','However','Since','With','From',
    'Into','Onto','About','Above','Below','Between','Through','During','Before',
    'After','But','And','For','Are','Was','Were','Has','Had','His','Her','Its',
    'Who','Whom','Why','How','All','Any','Few','Own','Same','Such','Than',
    'Too','Not','Both','Together','Today','Whether','While','Without','You',
    'They','Their','Then','Every','Everyone','Everything','Others','Your',
    'She','Can','May','Must','Would','Could','Should','Might','Shall','Will',
    'One','Two','Three','Four','Five','Six','Ten','Eight','Nine','Seven',
    'Twelve','Twenty','Thirty','Eleven','Thirteen','Hundred','Thousand',
    'Another','Among','Amongst','Some','Most','More','Many','Much','Each',
    'Other','Still','Just','Even','Only','Very',
    'Accept','Achieve','Act','Add','Agree','Allow','Appear','Apply','Arise',
    'Arrange','Ask','Avoid','Awake','Bear','Beat','Become','Begin','Believe',
    'Belong','Bend','Bind','Bite','Blaze','Bless','Blow','Boast','Bow','Break',
    'Bring','Build','Burn','Call','Care','Carry','Cast','Catch','Cause','Cease',
    'Challenge','Change','Chase','Check','Choose','Claim','Climb','Close',
    'Collect','Come','Command','Compare','Complete','Compose','Confront',
    'Conquer','Consider','Construct','Consult','Control','Convey','Cook',
    'Count','Cover','Create','Cross','Crush','Cry','Curse','Cut','Deal',
    'Decide','Declare','Defeat','Deliver','Depart','Depend','Descend',
    'Describe','Design','Desire','Desist','Destroy','Determine','Devise',
    'Die','Discover','Display','Do','Draw','Dress','Drive','Drop','Dwell',
    'Eat','Embrace','Emerge','Employ','Encounter','Encourage','Enjoy',
    'Enter','Escape','Establish','Examine','Exchange','Exclaim','Exhibit',
    'Exist','Expand','Explain','Express','Extend','Face','Fall','Fast',
    'Fear','Feed','Feel','Fight','Fill','Find','Fix','Flee','Float','Flow',
    'Follow','Forget','Forgive','Form','Free','Gain','Gather','Get','Give',
    'Go','Grant','Grasp','Greet','Grieve','Grip','Grow','Guard','Guess',
    'Guide','Happen','Hate','Have','Hear','Help','Hide','Hit','Hold','Honor',
    'Hope','Hurt','Ignore','Imagine','Immerse','Increase','Indicate','Inform',
    'Inhabit','Inspire','Instruct','Intend','Introduce','Invade','Invite',
    'Issue','Join','Judge','Jump','Keep','Kill','Know','Lack','Laugh','Lay',
    'Lead','Learn','Leave','Lie','Lift','Light','Listen','Live','Look','Lose',
    'Love','Make','Mark','Mean','Measure','Meet','Mention','Mind','Miss','Mix',
    'Modify','Move','Need','Observe','Obtain','Occupy','Offer','Open','Oppose',
    'Order','Overcome','Overlook','Owe','Pardon','Pass','Pay','Perform',
    'Permit','Pick','Place','Plan','Play','Please','Point','Possess','Pour',
    'Praise','Pray','Prepare','Present','Preserve','Press','Prevent','Produce',
    'Promise','Promote','Protect','Prove','Provide','Pull','Punish','Purchase',
    'Pursue','Push','Put','Raise','Reach','Read','Realize','Receive',
    'Recognize','Recommend','Reduce','Reflect','Refuse','Regard','Reject',
    'Release','Remain','Remember','Remove','Repeat','Replace','Reply','Report',
    'Request','Require','Rescue','Resist','Respect','Rest','Restore','Result',
    'Retain','Retire','Return','Reveal','Ride','Rise','Roam','Rob','Roll',
    'Rule','Run','Rush','Save','Say','Scatter','Search','See','Seek','Seem',
    'Seize','Select','Send','Separate','Serve','Set','Settle','Shake','Share',
    'Shed','Shine','Shoot','Show','Shrink','Shut','Sing','Sit','Sleep','Smile',
    'Sound','Speak','Spend','Spread','Stand','Start','Stay','Steal','Step',
    'Stop','Store','Strike','Struggle','Study','Subject','Succeed','Suffer',
    'Suggest','Support','Suppose','Surround','Survive','Suspect','Take',
    'Teach','Tell','Tend','Test','Think','Throw','Touch','Trade','Train',
    'Travel','Treat','Tremble','Trust','Try','Turn','Understand','Unite',
    'Use','Utter','Visit','Wait','Wake','Walk','Wander','Want','Warn','Wash',
    'Watch','Wear','Weep','Welcome','Win','Wish','Withdraw','Wonder','Work',
    'Worry','Worship','Write','Yield',
    # Common nouns
    'Absence','Act','Action','Actions','Advice','Age','Aim','Air','All',
    'Allies','Anger','Animal','Animals','Answer','Arm','Arms','Army',
    'Armour','Arrow','Arrows','Array','Attack','Attempt','Attention',
    'Back','Base','Battle','Battles','Beauty','Beds','Beginning','Beings',
    'Bells','Benefit','Bird','Birds','Birth','Blood','Blow','Blows',
    'Bodies','Body','Bolts','Bonds','Bones','Book','Books','Boons','Bow',
    'Bows','Branches','Breath','Bridge','Brother','Brothers','Bull','Bulls',
    'Business','Camp','Camps','Capital','Care','Cattle','Cavalry','Cave',
    'Ceremony','Chains','Challenge','Chance','Change','Chapter','Chapters',
    'Chariot','Charioteer','Charioteers','Chariots','Charity','Chief',
    'Children','Choice','Circle','Cities','Citizens','City','Clan','Clans',
    'Class','Club','Clubs','Cold','Collection','Colour','Command','Commander',
    'Compassion','Conduct','Confusion','Conquest','Consequence','Contact',
    'Contentment','Control','Conviction','Cook','Country','Countries',
    'Courage','Course','Cows','Creation','Creator','Creatures','Crimes',
    'Crops','Crowds','Curse','Danger','Dark','Darkness','Daughter',
    'Daughters','Dawn','Day','Days','Dead','Deal','Death','Debts','Decay',
    'Deceit','Decree','Deeds','Deep','Deer','Defeat','Deity','Delight',
    'Delusion','Demon','Demoness','Demons','Descendant','Description',
    'Design','Desire','Destination','Destiny','Destruction','Devotion',
    'Dice','Direction','Directions','Disease','Disguise','Dispute',
    'Distance','District','Dominion','Donation','Door','Doubt','Dream',
    'Dreams','Dress','Drink','Drums','Dust','Duty','Ear','Earth','East',
    'Elements','Elephant','Elephants','Embryo','Emperor','End','Enemies',
    'Enemy','Energy','Essence','Evening','Event','Evil','Excellence','Eyes',
    'Face','Fame','Family','Fate','Father','Fear','Feast','Feather','Feet',
    'Female','Festival','Field','Fields','Fight','Fire','Fish','Flag',
    'Flags','Flesh','Flood','Floor','Flower','Flowers','Flute','Food',
    'Foot','Force','Forest','Forests','Forgiveness','Form','Forms',
    'Fortune','Fountain','Freedom','Friend','Friends','Fruit','Fruits',
    'Funeral','Future','Gain','Game','Garden','Garland','Garlands',
    'Garment','Garments','Gate','Gates','Gems','Gift','Gifts','Glory',
    'Goat','Goats','God','Gods','Gold','Good','Grace','Grain','Grass',
    'Grave','Great','Greed','Grief','Ground','Group','Groups','Guard',
    'Guest','Guests','Guide','Guilt','Hair','Hands','Happiness','Harm',
    'Harvest','Hate','Head','Health','Heart','Heat','Heaven','Heavens',
    'Hell','Help','Herbs','Hermit','Hermitage','Hero','Heroes','Hill',
    'Hills','History','Home','Honey','Honor','Honour','Hope','Horizon',
    'Horse','Horses','House','Houses','Human','Humans','Hunger','Hunt',
    'Hunter','Hymn','Hymns','Ice','Idea','Ignorance','Illness','Image',
    'Importance','Incognito','Infant','Inhabitants','Injuries','Injury',
    'Innocence','Insects','Insight','Intelligence','Intention','Interest',
    'Iron','Island','Islands','Jewel','Jewels','Joy','Justice','Kill',
    'Killing','Kind','King','Kingdom','Kingdoms','Kings','Kinsmen',
    'Knowledge','Labour','Lake','Lakes','Land','Lands','Language','Leader',
    'Leaders','Left','Legs','Lesson','Liberation','Life','Light','Limbs',
    'Lineage','Lion','Lions','Lotus','Luck','Luxuries','Magic','Maid',
    'Maiden','Male','Man','Mankind','Manner','Mark','Marriage','Master',
    'Matter','Meal','Meaning','Means','Measure','Meat','Medicine',
    'Meditation','Men','Merchant','Merchants','Mercy','Merit','Merits',
    'Message','Messenger','Metal','Metals','Method','Mind','Minister',
    'Ministers','Miracle','Mirror','Misery','Mission','Moment','Money',
    'Month','Months','Moon','Morning','Mother','Mountain','Mountains',
    'Mouth','Music','Name','Names','Nature','Neck','Net','Night','Nights',
    'Noble','Noise','Noon','North','Nothing','Number','Numbers','Oath',
    'Object','Objects','Ocean','Offering','Offerings','Offspring','Oil',
    'Omen','Omens','Opinion','Opponent','Opportunity','Order','Origin',
    'Ornament','Ornaments','Outcome','Owner','Pace','Pain','Palace','Part',
    'Parts','Past','Path','Paths','Patience','Peace','Peak','Pearls',
    'Penance','People','Period','Permission','Person','Persons','Picture',
    'Pillar','Pilgrimage','Place','Places','Plain','Plains','Plan',
    'Planet','Planets','Plants','Pleasure','Pledge','Plough','Poem',
    'Poetry','Poison','Policy','Pool','Poor','Position','Possessions',
    'Post','Pot','Poverty','Power','Powers','Practice','Practices',
    'Praise','Prayer','Prayers','Presence','Present','Priest','Priests',
    'Prince','Princess','Principles','Prison','Prisoner','Procession',
    'Promise','Property','Prophecy','Prosperity','Protection','Protector',
    'Provisions','Punishment','Pupils','Purpose','Pursuit','Quality',
    'Queen','Quest','Question','Questions','Race','Rage','Rain','Rains',
    'Rank','Reason','Reasons','Region','Regions','Relatives','Relief',
    'Religion','Remedies','Renunciation','Report','Reputation','Request',
    'Residence','Resolution','Resources','Rest','Result','Results',
    'Return','Revenge','Reward','Riches','Rider','Riders','Right','Rights',
    'Rise','Rites','Ritual','Rituals','River','Rivers','Road','Roads',
    'Robe','Robes','Rock','Rocks','Roles','Roof','Room','Root','Roots',
    'Rope','Ruin','Rule','Ruler','Rules','Sacrifice','Sacrifices','Sage',
    'Sages','Salt','Salvation','Sanctuaries','Sanctuary','Satisfaction',
    'Science','Scripture','Scriptures','Sea','Season','Seasons','Seat',
    'Secret','Secrets','Seed','Seeds','Self','Sense','Senses','Servant',
    'Servants','Service','Shadow','Shame','Shape','Shelter','Shield',
    'Shore','Sight','Sign','Signs','Silence','Silver','Sin','Sins',
    'Sister','Skill','Skills','Skin','Sky','Slave','Slaves','Sleep',
    'Smell','Smile','Smoke','Snake','Snakes','Soil','Soldier','Soldiers',
    'Son','Song','Songs','Sons','Soul','Souls','Sound','Source','South',
    'Space','Spear','Species','Speech','Speed','Spirit','Spirits','Spot',
    'Spots','Spring','Staff','Stage','Star','Stars','State','Status',
    'Stem','Stone','Stones','Strength','String','Study','Subject',
    'Substance','Success','Suggestion','Sun','Support','Surface',
    'Surprise','Surrender','Survivors','Sword','Swords','Symbol','Taste',
    'Teacher','Teachers','Teeth','Temple','Temples','Terror','Test',
    'Text','Texts','Thanks','Things','Thirst','Thought','Thoughts',
    'Thousands','Throne','Tiger','Timber','Time','Times','Tongue','Top',
    'Torment','Tower','Town','Towns','Trade','Tradition','Traditions',
    'Trap','Travel','Treasure','Treasures','Treaty','Tree','Trees',
    'Tribe','Tribes','Tribute','Troops','Trouble','Trust','Truth','Turn',
    'Type','Umbrella','Understanding','Union','Universe','Valley','Valour',
    'Value','Vapour','Vehicle','Venture','Vice','Victory','View','Village',
    'Villages','Violence','Virtue','Virtues','Vision','Voice','Vow','Vows',
    'Vultures','Wages','Waist','Wall','Walls','War','Warrior','Warriors',
    'Wars','Waste','Water','Waters','Waves','Way','Weakness','Wealth',
    'Weapon','Weapons','Weather','Week','Weight','Well','West','Wheel',
    'Wheels','Wife','Wind','Winds','Wine','Wisdom','Wish','Wishes',
    'Witness','Woman','Women','Wombs','Wonder','Wood','Woods','Word',
    'Words','Work','Works','World','Worlds','Worship','Worst','Worth',
    'Wound','Wounds','Wrath','Wrestler','Writing','Wrong','Year','Years',
    'Youth',
    # Adjectives
    'Able','Abundant','Accurate','Active','Actual','Additional','Afraid',
    'Ancient','Angry','Anxious','Appropriate','Auspicious','Bad','Base',
    'Beautiful','Best','Better','Big','Bitter','Black','Blessed','Blind',
    'Blue','Bold','Born','Brave','Bright','Brilliant','Broad','Broken',
    'Brown','Burning','Calm','Capable','Careful','Celestial','Certain',
    'Cheerful','Cheerless','Chief','Clean','Clear','Clever','Cold',
    'Complete','Constant','Cool','Correct','Countless','Cruel','Curious',
    'Dangerous','Dark','Dead','Dear','Deep','Delighted','Delightful',
    'Dense','Desperate','Devoted','Different','Difficult','Direct',
    'Divine','Double','Dreadful','Dry','Eastern','Easy','Effective',
    'Eldest','Elegant','Empty','Enormous','Entire','Equal','Essential',
    'Eternal','Excellent','Excessive','Extreme','Extremely','Fair',
    'Faithful','False','Familiar','Famous','Fast','Fearful','Fearless',
    'Female','Fierce','Final','Fine','First','Fixed','Flat','Fond',
    'Foolish','Foreign','Former','Fortunate','Free','Fresh','Full',
    'Future','General','Generous','Gentle','Giant','Glad','Glorious',
    'Golden','Good','Grand','Grateful','Great','Green','Grey','Guilty',
    'Half','Happy','Hard','Harsh','Healthy','Heavy','Hidden','High',
    'Holy','Honest','Horrible','Hot','Huge','Humble','Hungry','Identical',
    'Ignorant','Ill','Illustrious','Immobile','Immovable','Immutable',
    'Impenetrable','Important','Impossible','Impure','Indestructible',
    'Inferior','Infinite','Innocent','Intelligent','Invisible','Invincible',
    'Just','Keen','Kind','Large','Last','Late','Lazy','Left','Less',
    'Light','Little','Living','Long','Loud','Low','Lovely','Loyal',
    'Lucky','Mad','Magnificent','Main','Major','Male','Massive','Middle',
    'Mighty','Minor','Mobile','Modern','Modest','Moral','Mortal','Most',
    'Much','Multiple','Mysterious','Naked','Narrow','Natural','Near',
    'Necessary','New','Next','Nice','Noble','Normal','Northern','Numerous',
    'Obvious','Odd','Old','Open','Opposite','Ordinary','Original','Own',
    'Pale','Particular','Past','Patient','Perfect','Permanent','Personal',
    'Physical','Plain','Pleasant','Pleased','Plentiful','Poisonous','Poor',
    'Popular','Possible','Powerful','Precious','Present','Previous',
    'Private','Proper','Prosperous','Proud','Public','Pure','Quick',
    'Quiet','Rare','Raw','Ready','Real','Red','Regular','Religious',
    'Remote','Resident','Rich','Right','Righteous','Rigid','Rising',
    'Rough','Round','Royal','Rude','Sacred','Sad','Safe','Satisfied',
    'Savage','Scared','Secret','Senior','Separate','Serious','Seven',
    'Several','Severe','Sharp','Short','Silent','Silver','Similar',
    'Simple','Single','Slain','Slender','Slight','Slow','Small','Smooth',
    'Soft','Solar','Sole','Solid','Sorry','Southern','Special','Splendid',
    'Steady','Steep','Still','Straight','Strange','Strict','Strong',
    'Stupid','Subtle','Successful','Sudden','Sufficient','Superior',
    'Supreme','Sure','Sweet','Swift','Tall','Terrible','Thick','Thin',
    'Third','Thorough','Tight','Tiny','Tired','Total','Tough',
    'Traditional','Tremendous','Troubled','True','Ugly','Unable','Under',
    'Unfortunate','Unhappy','United','Universal','Unknown','Unmatched',
    'Upper','Useful','Usual','Utter','Vast','Violent','Visible','Vital',
    'Vivid','Warm','Weak','Wealthy','Western','White','Whole','Wicked',
    'Wide','Wild','Willing','Wise','Wonderful','Wooden','Worthy','Wrong',
    'Yellow','Young',
    # Adverbs
    'According','Accordingly','Actually','Again','Ago','Ahead','Almost',
    'Already','Always','Apparently','Away','Badly','Barely','Basically',
    'Besides','Briefly','Carefully','Certainly','Cheerfully','Clearly',
    'Closely','Commonly','Completely','Consequently','Constantly',
    'Continuously','Correctly','Critically','Currently','Deeply',
    'Definitely','Deliberately','Desperately','Despite','Directly',
    'Down','Earlier','Easily','Effectively','Either','Elsewhere',
    'Entirely','Equally','Especially','Essentially','Eventually','Ever',
    'Everywhere','Evidently','Exactly','Finally','Firmly','Firstly',
    'Fondly','Forcefully','Formally','Formerly','Fortunately','Frankly',
    'Freely','Frequently','Gently','Generally','Gladly','Gradually',
    'Greatly','Happily','Hardly','Heavily','Hence','Honestly','Hopefully',
    'However','Immediately','Indeed','Instead','Interestingly',
    'Invariably','Just','Largely','Later','Literally','Mainly',
    'Meanwhile','Merely','Moreover','Mostly','Much','Naturally','Nearly',
    'Necessarily','Nevertheless','Normally','Now','Nowadays','Obviously',
    'Occasionally','Often','Once','Otherwise','Overall','Particularly',
    'Partly','Perhaps','Personally','Plainly','Possibly','Presumably',
    'Previously','Primarily','Probably','Properly','Purely','Quickly',
    'Quietly','Quite','Rapidly','Rather','Really','Recently','Repeatedly',
    'Respectively','Seemingly','Separately','Seriously','Similarly',
    'Simply','Simultaneously','Slowly','Sometimes','Somewhere','Somewhat',
    'Soon','Specifically','Strictly','Subsequently','Suddenly',
    'Sufficiently','Surely','Swiftly','Temporarily','Thereafter',
    'Thereby','Thereupon','Thoroughly','Traditionally','Truly','Typically',
    'Ultimately','Undoubtedly','Unfortunately','Usually','Virtually',
    'Widely',
    # Participles / -ing / -ed
    'Abandoned','Abandoning','Accompanied','Achieved','Addressed',
    'Adorned','Adorning','Advancing','Afflicted','Aged','Agitated',
    'Agreed','Alarmed','Amazed','Approaching','Appointed','Arranged',
    'Armed','Arrayed','Arriving','Ashamed','Asked','Assembled',
    'Associated','Assuming','Astounded','Attached','Attacked','Attained',
    'Attended','Awakened','Banished','Based','Bearing','Bedecked',
    'Beholding','Being','Believing','Belonging','Bewildered','Binding',
    'Blazing','Blessed','Blinded','Bowing','Brandishing','Bringing',
    'Broken','Brought','Burning','Burnt','Calling','Captured','Carried',
    'Carrying','Casting','Causing','Censured','Chanting','Chased',
    'Choosing','Clad','Clasping','Cleansed','Climbing','Collected',
    'Comforted','Coming','Commanded','Composed','Concerned','Condemned',
    'Confronted','Confused','Connected','Conquered','Considering',
    'Consoled','Consumed','Controlled','Covered','Created','Crossed',
    'Crushed','Crying','Cursed','Darkening','Dazzling','Deceived',
    'Declaring','Decorated','Defeated','Deformed','Delighted','Deluded',
    'Departed','Departing','Deprived','Descended','Described','Deserted',
    'Desiring','Destroyed','Destroying','Determined','Devoted',
    'Devoured','Disguised','Dispatched','Displayed','Distressed',
    'Disturbed','Divided','Drawn','Dressed','Driven','Dwelling','Earned',
    'Eating','Embraced','Embracing','Emerged','Employed','Enchanted',
    'Encountered','Encouraged','Endowed','Engaged','Enraged','Entered',
    'Entering','Equipped','Escaped','Established','Examining','Excited',
    'Exclaimed','Exiled','Expressing','Extending','Facing','Failed',
    'Fainted','Fallen','Falling','Fashioned','Felled','Filled','Fired',
    'Flaming','Fleeing','Floating','Flowing','Followed','Following',
    'Forced','Forgiving','Formed','Frightened','Fulfilled','Gaining',
    'Garlanded','Gathered','Gathering','Gifted','Giving','Going',
    'Governed','Granted','Granting','Grasping','Greeted','Grieving',
    'Gripped','Guarded','Guarding','Hearing','Heated','Helped','Hidden',
    'Hitting','Holding','Honoured','Hoping','Hurled','Hurling',
    'Identified','Imagined','Immersed','Inclined','Increased','Inflamed',
    'Inflicted','Informed','Inhabited','Injured','Inspired','Instructed',
    'Intending','Interested','Invited','Invoked','Joined','Joining',
    'Killed','Killing','Knowing','Known','Lacking','Laid','Lamenting',
    'Laughing','Launched','Leading','Leaping','Learned','Learning',
    'Leaving','Living','Located','Looking','Losing','Lost','Lying',
    'Managing','Manifested','Married','Measuring','Meeting','Mentioned',
    'Mounted','Mourning','Moving','Named','Nourished','Obtained',
    'Observed','Observing','Occupied','Offered','Offering','Opening',
    'Opposed','Oppressed','Ordered','Overcome','Overwhelmed','Performed',
    'Performing','Permitted','Pierced','Piercing','Placed','Placing',
    'Pleased','Praising','Praying','Prepared','Preparing','Presented',
    'Preserved','Prevented','Proceeding','Produced','Promised',
    'Pronounced','Propitiated','Proposed','Prospered','Protected',
    'Protecting','Proved','Provided','Punished','Purified','Pursued',
    'Questioned','Quoted','Raised','Raising','Reached','Reaching',
    'Received','Receiving','Recognized','Reduced','Reflected','Refused',
    'Regarding','Rejoiced','Rejoicing','Related','Released','Remaining',
    'Remembered','Removed','Renowned','Repeated','Reported','Requested',
    'Rescued','Resembling','Residing','Respected','Restrained',
    'Restored','Resting','Returned','Returning','Revealed','Roaming',
    'Roaring','Rolling','Ruled','Running','Rushing','Sacrificed',
    'Scared','Scattered','Scorched','Searching','Seated','Secured',
    'Seeing','Seeking','Seized','Selected','Sent','Separated','Served',
    'Settled','Setting','Shaking','Shaped','Sharing','Shattered',
    'Shining','Shooting','Showing','Shrieking','Sitting','Skilled',
    'Slaughtered','Sleeping','Sliced','Smeared','Smiling','Smitten',
    'Speaking','Spoken','Standing','Started','Stationed','Stayed',
    'Stolen','Stopped','Strewn','Stricken','Striking','Striving',
    'Struck','Submitted','Suffering','Summoned','Supported','Surrounded',
    'Survived','Suspended','Taking','Terrified','Thinking','Thrown',
    'Tied','Told','Tormented','Torn','Touched','Trained','Trapped',
    'Trembling','Troubled','Trusted','Turned','Turning','Twisted',
    'Undergoing','Understood','United','Urged','Using','Vanquished',
    'Visited','Waiting','Wandering','Warned','Washed','Watching',
    'Wearing','Weeping','Welcomed','Wishing','Withdrawn','Wondering',
    'Working','Worried','Worshipped','Wounded','Yielding',
    # Other
    'Alas','Although','Announced','Bliss','Bumpers','Confession',
    'Continued','Conversation','Critical','Dominated','Embarrassed',
    'Endless','Entitled','Equivalent','Exhausted','Expected','Extensive',
    'Ferocious','Fierce','Foolish','Greater','Gruesome','Handsome',
    'Hanging','Haste','Himself','Hostile','Household','Identical',
    'Indifferent','Inferior','Intense','Intoxicated','Irrelevant',
    'Isolated','Jointly','Junior','Knowledgeable','Lacking','Lament',
    'Limitless','Literary','Maintenance','Manuscripts','Material',
    'Metaphor','Misfortune','Multiple','Natural','Neutral','Notable',
    'Objective','Obliged','Obscure','Official','Operative','Parallel',
    'Peculiar','Persistent','Pledge','Polluted','Popular','Positive',
    'Precious','Predominance','Progressive','Prominent','Provincial',
    'Reaction','Readily','Reconciliation','Regular','Reluctant',
    'Resemblance','Restoration','Reverence','Sacred','Shifted','Simile',
    'Solemn','Soothing','Sorrowful','Sovereign','Spiritual','Splendour',
    'Stable','Steadfast','Stranger','Structural','Substantial','Subtle',
    'Sympathy','Tender','Territorial','Throughout','Tolerance',
    'Transformation','Tremendous','Universal','Unprecedented',
    'Unwilling','Valuable','Various','Vigorous','Visible','Voluntary',
    'Wandered','Widely','Wonderful','Worried',
    # Sentence starters / misc overlooked
    'Because','Let','Like','Neither','Nor','Per','Rather','Unto','Upon',
    'Via','Yet','Did','Does','Got','Put','Ran','Sat','Set','Sir',
    'Towards','Across','Against','Beyond','Except',
    # Non-character proper nouns
    'Sanskrit','Mahabharata','Austerities',
    # Misc
    'Abandon','Abide','Ablutions','Abode','Absolute','Accomplish','Accord',
    'Accounts','Actors','Adhere','Adopt','Advance','Aide','Alms','Aloe',
    'Along','Alter','Amidst','Amuse','Anyone','Anything','Ape','Archery',
    'Architect','Area','Ash','Ashes','Aside','Assemble','Assembly','Asses',
    'Assurance','Astride','Atone','Awoken','Bandits','Banish','Banyan',
    'Bashful','Bay','Beggars','Bellows','Beloved','Bestow','Bipeds',
    'Bloodless','Boar','Boastful','Boats','Boswellia','Boxers','Boys',
    'Bracelets','Breadfruit','Calves','Cane','Carnivorous','Cashew',
    'Cedar','Celibate','Censure','Clash','Cleanse','Clouds','Coastal',
    'Coconut','Collyrium','Comfort','Conch','Conches','Content','Copper',
    'Coral','Cowherds','Cowrie','Cowards','Cranes','Cream','Crows',
    'Cubits','Cuckoos','Cultivate','Curiosity','Cymbals','Dacoits',
    'Dancer','Dancers','Date','Dexterity','Distant','Ghee','Mace',
    'Regardless','Sunday',
    'Aldebaran','Arcturus','Bactria','Denebola','Pleiades','Pluto',
    'Saturn','Venus','Mars','Antioch',
    'January','February','March','April','May','June','July','August',
    'September','October','November','December',
    'Ascend','Ascent','Ascetic','Ascetics',
    'Acts','Artisans','Bees','Bestow','Borne',
    'Affectionate','Agriculture','Alongside','Ancestors','Anxiety','Apart',
    'Appoint','Approach','Approve','Assure','Attain','Attend','Autumn',
    'Bathe','Behave','Benevolent','Beyond','Bitten','Capture','China',
    'Counter','Devote','Discard','Dish','Dispel','Distinct','Distribute',
    'Diverse','Donate','Duel','Dusk','Eager','Eloquent','Endeavour',
    'Engage','Enterprise','Entertain','Erect','Exert','Exile','External',
    'Fasten','Fetch','Fever','Foam','Formula','Forsake','Frenzy','Glance',
    'Guardian','Guild','Hardship','Hasten','Homage','Impart','Impatient',
    'Incense','Inquire','Instant','Intellect','Javelin','Kindle','Lean',
    'Lord','Malice','Manifest','Meditate','Mild','Nimble','Nurture',
    'Ominous','Oppress','Penetrate','Pierce','Pine','Pride','Prior',
    'Proceed','Pronounce','Proof','Prosper','Prowess','Recite','Refuge',
    'Rejoice','Render','Renounce','Repulse','Resort','Restrain','Retreat',
    'Ripe','Salute','Scent','Serene','Serpent','Sever','Shade','Slaughter',
    'Slavery','Slay','Slayer','Solitary','Stock','Strife','Strive',
    'Subsequent','Summon','Suppress','Survey','Sustain','Synonym',
    'Tranquil','Transcend','Triumph','Turbulent','Ultimate','Unity',
    'Vain','Vanquish','Woe','Yoke','Volume',
}

# Words that look English but ARE actual Mahabharata names - KEEP these
KEEP_AS_NAMES = {
    'Rig','Yajur','Atharva','Sama','Maya','Maha','Parva','Hari','Deva',
    'Guru','Raja','Rishi','Yuga','Dharma','Adharma','Karma','Moksha',
    'Agni','Vayu','Surya','Soma','Indra','Varuna','Yama','Kubera',
    'Kali','Uma','Ganga','Durga','Lakshmi',
}


def is_english_word(name):
    """Check if a capitalized word is likely English, not a character name."""
    if name in ENGLISH_WORDS:
        return True
    low = name.lower()
    if low.endswith('ly') and len(low) > 4:
        return True
    if low.endswith('ing') and len(low) > 5:
        return True
    if low.endswith(('tion', 'sion')) and len(low) > 5:
        return True
    if low.endswith('ness') and len(low) > 5:
        return True
    if low.endswith('ment') and len(low) > 5:
        return True
    if low.endswith('ed') and len(low) > 4 and low[-3] not in 'aeiou':
        return True
    return False


# Non-character entries to remove from final JSON (found during verification)
FINAL_REMOVE = {
    # English words
    "advisers","armies","avarice","barbarians","behind","benedictions",
    "buddhist","ceremonies","dogs","done","eighteen","eighty","enmity",
    "envy","exclamations","falsehood","fathers","foremost","fortitude",
    "fourth","fragrant","friendship","gigantic","granter","greedy","hawk",
    "heads","hermits","herons","hunters","husbands","immortal","infantry",
    "insolence","insolent","intolerant","kettledrums","led","line","lives",
    "lords","maces","marks","miserable","mothers","mythical","ninety",
    "pacify","palm","physician","pole","practise","preceptor","princes",
    "purify","purity","qualities","radiance","rebirth","recount","resin",
    "resplendent","rose","satisfy","second","semen","senseless","serpents",
    "servitude","sexual","shields","shops","shoulder","sixteen","sixty",
    "slander","slice","sorrow","sounds","spears","spies","sport",
    "standards","subjects","supervisor","swan","sweat","tasks","tawny",
    "tears","thighs","tonight","tranquility","tributary","truthful",
    "tuskers","twice","umbrellas","unassailable","unseen","upholder",
    "used","wives","yes","yours",
    # Modern places / social media
    "bangladesh","bihar","chambal","chenab","facebook","gujarat",
    "haridwar","hindu","india","jasmine","jhelum","jind","karnataka",
    "kashmir","kerala","maharashtra","majoris","nadu","pehowa","rajasthan",
    "rajgir","scythians","sec","srinivasan","sutlej","tamil","tibet",
    "twitter","udhampur","ujjain","uttarakhand","youtube","vedic",
    "bengal","baramula",
    # Generic Sanskrit terms (not character names)
    "agnihotra","akshouhinis","arghya","ashvamedha","atiratha","atma",
    "ayurveda","bhagavad","bhagavadgita","brahmachari","brahmacharya",
    "brahmi","buddhi","chakra","chaitya","dakshinayana","dharana",
    "dhriti","jnana","karma","kashtha","koustubha","krisara","kshetra",
    "kusha","loka","mantra","mlecchas","moksha","muhurta","nakshatra",
    "nidhi","nitya","niyata","nyagrodha","omkara","paksha","pashupata",
    "pranayama","putra","raja","raga","ratha","riddhi","rishi",
    "samvatsara","sankhya","sapta","shastra","shraddha","shuklapaksha",
    "siddha","svarga","svasti","tirtha","treta","tvam","udana",
    "upanishad","uttarayana","vaidurya","vaishnava","vaishya","varna",
    "vedanga","vidya","vijnana","vyakta","yuddha","vyavasaya","yajana",
    "yogi","yoni","sadasyas","samhrada","samgraha","sankalpa","senapati",
    "arya","parama","punya","prajapatya","sarpas","ratna","pramana",
    "sahya","sahasra","brah","tri","sri","avyaya","avyakta","anagha",
    "amogha","brihat","chatur","pravaha","vara","varcha","pravara",
    "samana","sahasraksha","adi","asi","apa","bho","vish","bahula",
    "rathantara","ruchiparva","uttama","shashvata","payasa","prayuta",
    "ayuta","skanna","sukshma","sthira","akritavarna","roudra","soumya",
    "souptika","sambhava","prasthanika","adbhuta","bhavishya","aindra",
    "agneya","vayavya","debroy","dasyus","mama","pan","tat","yud","haha",
    "sat",
    # English adjectives/participles/etc (round 2)
    "agreeable","alternative","arrogance","avaricious","believers",
    "carriers","compassionate","continuous","copious","deceitful",
    "desirious","desirous","destroyer","disasters","doing","dying",
    "embodied","equable","evildoers","expensive","extraordinary",
    "fishermen","followers","forceful","fourteen","freed","gamblers",
    "governance","gracious","guidance","headless","hopeless",
    "householders","immeasurable","impatience","imperishable",
    "inaccessible","inadvertence","inauspicious","incapable",
    "indifference","indomitable","indulgence","infallible","inheritance",
    "intolerance","irreproachable","irresistible","knowledgable",
    "lustrous","malevolent","meaningful","messengers","meteors",
    "mountainous","nonviolence","oleanders","omniscience","omniscient",
    "perceptible","perishable","perseverance","persians","pervasive",
    "pitiable","predators","rallied","reference","resilience","revilers",
    "revive","robbers","seniors","singers","studied","subterranean",
    "thunderous","travellers","tumultuous","unconscious","unmarried",
    "unworthy","useless","victorious","virtuous","woodpeckers",
    "worshippers","wrestlers",
    # Round 3
    "dishonest","due","fig","forbidden","forsaken","giver","henceforth",
    "hog","hum","humility","jay","kin","mar","nearby","par","rig","rod",
    "sub","tin","tip","wherever","circumambulate","consecrate",
    "extinguish","fifteen","gladden","gratify","heartbroken","immediate",
    "inappropriate","instate","liberate","logical","lordship","metrical",
    "mystical","prostrate","tolerate","adharma","roudrakarma","vamsha",
    "vasa",
}


# =====================================================================
# HELPER: Edit distance
# =====================================================================

def edit_distance(a, b):
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[n]


# =====================================================================
# STEP 1: Extract all names from volumes
# =====================================================================

def extract_all_names():
    """Extract all capitalized words (3+ chars) from chapters + footnotes."""
    print("Step 1: Extracting names from all volumes...")
    fn_counts = Counter()
    ch_counts = Counter()
    for v in range(1, NUM_VOLUMES + 1):
        fn_text = open(os.path.join(VOLUMES_DIR, f'volume_{v}_footnotes.txt'), encoding='utf-8').read()
        ch_text = open(os.path.join(VOLUMES_DIR, f'volume_{v}_chapters.txt'), encoding='utf-8').read()
        for n in re.findall(r'\b([A-Z][a-z]{2,})\b', fn_text):
            fn_counts[n] += 1
        for n in re.findall(r'\b([A-Z][a-z]{2,})\b', ch_text):
            ch_counts[n] += 1

    all_names = {}
    for name in set(fn_counts.keys()) | set(ch_counts.keys()):
        fn = fn_counts.get(name, 0)
        ch = ch_counts.get(name, 0)
        all_names[name] = (fn, ch, fn + ch)

    print(f"  Total unique words: {len(all_names)}")
    return all_names


# =====================================================================
# STEP 2: Classify names (real vs English)
# =====================================================================

def classify_names(all_names):
    """Separate real names from English words."""
    print("Step 2: Classifying names...")
    real = {}
    removed = 0
    for name, freqs in all_names.items():
        if name in KEEP_AS_NAMES:
            real[name] = freqs
        elif is_english_word(name):
            removed += 1
        else:
            real[name] = freqs
    print(f"  English words removed: {removed}")
    print(f"  Real names remaining: {len(real)}")
    return real


# =====================================================================
# STEP 3: Group variants (plurals, double-vowels)
# =====================================================================

def group_variants(names):
    """Group safe variants: plurals (-s) and double vowels (-aa)."""
    print("Step 3: Grouping variants...")
    name_set = set(names.keys())
    parent = {}

    # Plural: Arjunas -> Arjuna
    for name in list(name_set):
        if name.endswith('s') and len(name) > 3:
            base = name[:-1]
            if base in name_set:
                parent[name] = base

    # Double vowels: Krishnaa -> Krishna
    for name in list(name_set):
        if len(name) > 3 and name[-1] == name[-2] and name[-1] in 'aeiou':
            base = name[:-1]
            if base in name_set and name not in parent:
                parent[name] = base

    def resolve(name):
        seen = {name}
        current = name
        while current in parent:
            current = parent[current]
            if current in seen:
                break
            seen.add(current)
        return current

    for name in list(parent.keys()):
        parent[name] = resolve(name)

    groups = {}
    for name, freqs in names.items():
        canonical = resolve(name)
        if canonical not in groups:
            groups[canonical] = {'total': 0, 'variants': []}
        groups[canonical]['total'] += freqs[2]
        if name != canonical:
            groups[canonical]['variants'].append((name, freqs[2]))

    # Find edit-distance-1 pairs
    canonicals = sorted(groups.keys())
    prefix_index = defaultdict(list)
    for name in canonicals:
        prefix_index[name[:2].lower()].append(name)

    spelling_pairs = []
    seen_pairs = set()
    for name in canonicals:
        if len(name) < 5:
            continue
        key = name[:2].lower()
        candidates = set()
        for k, v in prefix_index.items():
            if k[0] == key[0]:
                candidates.update(v)
        for other in candidates:
            if other == name or len(other) < 5:
                continue
            pair = tuple(sorted([name, other]))
            if pair in seen_pairs:
                continue
            if abs(len(name) - len(other)) <= 1:
                d = edit_distance(name, other)
                if d == 1:
                    seen_pairs.add(pair)
                    f1, f2 = groups[name]['total'], groups[other]['total']
                    if max(f1, f2) >= 3:
                        if f1 >= f2:
                            spelling_pairs.append((name, f1, other, f2))
                        else:
                            spelling_pairs.append((other, f2, name, f1))

    spelling_pairs.sort(key=lambda x: -x[1])
    multi = sum(1 for g in groups.values() if g['variants'])
    print(f"  Unique names (groups): {len(groups)}")
    print(f"  Groups with variants: {multi}")
    print(f"  Edit-distance-1 pairs: {len(spelling_pairs)}")
    return groups, spelling_pairs


# =====================================================================
# STEP 4: Build character JSON with aliases
# =====================================================================

def load_character_db():
    """Load existing 525-entry character DB."""
    with open(CHAR_DB_FILE, encoding='utf-8') as f:
        data = json.load(f)
    name_to_key = {}
    alias_to_key = {}
    for key, val in data.items():
        name = val.get('Name', '')
        name_to_key[name] = key
        for alias in val.get('Alias_names', []):
            alias_to_key[alias] = key
    return data, name_to_key, alias_to_key


def build_characters(groups, spelling_pairs, db, name_to_key, alias_to_key):
    """Build character entries with union-find for spelling merges."""
    print("Step 4: Building character entries...")

    # Union-Find
    uf_parent = {}
    freq_map = {}

    def find(x):
        if x not in uf_parent:
            uf_parent[x] = x
        while uf_parent[x] != x:
            uf_parent[x] = uf_parent[uf_parent[x]]
            x = uf_parent[x]
        return x

    def union(a, b, fa, fb):
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if fa >= fb:
            uf_parent[rb] = ra
        else:
            uf_parent[ra] = rb

    for canonical, info in groups.items():
        uf_parent[canonical] = canonical
        freq_map[canonical] = info['total']

    # Merge spelling pairs (strict: low<=3, high>=20, len>=7)
    merged = 0
    for name1, freq1, name2, freq2 in spelling_pairs:
        if name1 in freq_map and name2 in freq_map:
            high = max(freq1, freq2)
            low = min(freq1, freq2)
            low_name = name2 if freq1 >= freq2 else name1
            if low <= 3 and high >= 20 and len(low_name) >= 7:
                union(name1, name2, freq1, freq2)
                merged += 1
    print(f"  Spelling pairs auto-merged: {merged}")

    # Build groups by root
    char_groups = defaultdict(set)
    for name in groups:
        char_groups[find(name)].add(name)

    # Build final entries
    characters = {}
    for root, members in char_groups.items():
        best_name = max(members, key=lambda x: groups[x]['total'])
        all_aliases = set()
        total_freq = 0

        for member in members:
            info = groups[member]
            total_freq += info['total']
            if member != best_name:
                all_aliases.add(member)
            for variant, vfreq in info['variants']:
                if variant != best_name:
                    all_aliases.add(variant)

        # Check existing DB
        db_key = None
        db_entry = None
        for check_name in [best_name] + list(all_aliases):
            if check_name in name_to_key:
                db_key = name_to_key[check_name]
                db_entry = db[db_key]
                break
            if check_name in alias_to_key:
                db_key = alias_to_key[check_name]
                db_entry = db[db_key]
                break

        if db_entry:
            key = db_key
            db_canonical = db_entry.get('Name', best_name)
            if best_name != db_canonical:
                all_aliases.add(best_name)
            best_name = db_canonical
            all_aliases |= set(db_entry.get('Alias_names', []))
        else:
            key = '@' + best_name.lower()

        all_aliases.discard(best_name)
        # Remove plural aliases where base exists
        to_remove = set()
        name_set = all_aliases | {best_name}
        for alias in list(all_aliases):
            if alias.endswith('s') and alias[:-1] in name_set:
                to_remove.add(alias)
        all_aliases -= to_remove

        entry = {'Name': best_name}
        if all_aliases:
            entry['Alias_names'] = sorted(all_aliases)
        characters[key] = entry

    print(f"  Total characters: {len(characters)}")
    return characters


# =====================================================================
# STEP 5: Add Count and Appearance
# =====================================================================

def add_count_and_appearance(characters):
    """Add Count (total mentions) and Appearance (per-volume chapters)."""
    print("Step 5: Adding Count and Appearance...")

    # Build name -> character key lookup
    name_to_keys = defaultdict(set)
    for key, val in characters.items():
        name_to_keys[val['Name']].add(key)
        for alias in val.get('Alias_names', []):
            name_to_keys[alias].add(key)

    # Initialize
    for key in characters:
        characters[key]['Count'] = 0
        characters[key]['_vol_chs'] = defaultdict(set)

    word_re = re.compile(r'\b([A-Z][a-z]{2,})\b')

    # Scan all volumes
    for v in range(1, NUM_VOLUMES + 1):
        print(f"  Scanning volume {v}...")
        # Chapters
        ch_text = open(os.path.join(VOLUMES_DIR, f'volume_{v}_chapters.txt'), encoding='utf-8').read()
        ch_parts = re.split(r'--- Chapter (\d+)(?:\(\d+\))? ---', ch_text)
        for i in range(1, len(ch_parts), 2):
            ch_num = int(ch_parts[i])
            ch_content = ch_parts[i + 1] if i + 1 < len(ch_parts) else ''
            for m in word_re.finditer(ch_content):
                word = m.group(1)
                if word in name_to_keys:
                    for key in name_to_keys[word]:
                        characters[key]['Count'] += 1
                        characters[key]['_vol_chs'][v].add(ch_num)

        # Footnotes
        fn_text = open(os.path.join(VOLUMES_DIR, f'volume_{v}_footnotes.txt'), encoding='utf-8').read()
        for m in word_re.finditer(fn_text):
            word = m.group(1)
            if word in name_to_keys:
                for key in name_to_keys[word]:
                    characters[key]['Count'] += 1

    # Convert _vol_chs to Appearance
    for key, val in characters.items():
        vol_chs = val.pop('_vol_chs', {})
        appearance = []
        for v in sorted(vol_chs.keys()):
            chs = sorted(vol_chs[v])
            ch_str = ','.join(str(c) for c in chs)
            appearance.append(f"Vol{v}:ch{ch_str}")
        val['Appearance'] = appearance

    top = sorted(characters.items(), key=lambda x: -x[1].get('Count', 0))[:10]
    print(f"  Top 10: {', '.join(f'{v["Name"]}({v["Count"]})' for k,v in top)}")
    return characters


# =====================================================================
# STEP 6: Remove non-character entries
# =====================================================================

def remove_non_characters(characters):
    """Remove English words, modern places, generic terms from final JSON."""
    print("Step 6: Removing non-character entries...")
    removed = 0
    cleaned = {}
    for key, val in characters.items():
        name = key.lstrip('@')
        if name.lower() in FINAL_REMOVE:
            removed += 1
        else:
            cleaned[key] = val
    print(f"  Removed: {removed}")
    print(f"  Remaining: {len(cleaned)}")
    return cleaned


# =====================================================================
# MAIN
# =====================================================================

def main():
    print("=" * 60)
    print("Character Extraction Pipeline (Debug)")
    print("=" * 60)

    # Step 1: Extract names
    all_names = extract_all_names()

    # Step 2: Classify
    real_names = classify_names(all_names)

    # Step 3: Group variants
    groups, spelling_pairs = group_variants(real_names)

    # Step 4: Build characters
    db, name_to_key, alias_to_key = load_character_db()
    print(f"  DB entries: {len(db)}")
    characters = build_characters(groups, spelling_pairs, db, name_to_key, alias_to_key)

    # Step 5: Count + Appearance
    characters = add_count_and_appearance(characters)

    # Step 6: Remove non-characters
    characters = remove_non_characters(characters)

    # Write output
    print(f"\nWriting output to {OUTPUT_FILE}...")
    output = {}
    for key in sorted(characters.keys()):
        val = characters[key]
        entry = {'Name': val['Name']}
        if 'Alias_names' in val:
            entry['Alias_names'] = val['Alias_names']
        entry['Count'] = val.get('Count', 0)
        entry['Appearance'] = val.get('Appearance', [])
        output[key] = entry

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Summary
    total = len(output)
    with_aliases = sum(1 for v in output.values() if 'Alias_names' in v)
    print(f"\n{'=' * 60}")
    print(f"DONE — {total} characters written to {OUTPUT_FILE}")
    print(f"  With aliases: {with_aliases}")
    top = sorted(output.items(), key=lambda x: -x[1].get('Count', 0))[:20]
    print(f"  Top 20:")
    for k, v in top:
        print(f"    {v['Name']:25s} Count={v['Count']}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
