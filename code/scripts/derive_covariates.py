"""Analysis-ready English covariates derived from the rice register (bgd_rice_varieties.csv).

Entry point: add(df) -> df. A pure function: it takes the register as an all-string DataFrame, never changes an existing
column, and returns a copy with the new columns inserted right after the column they are derived from. Nothing is read
or written at import time; `python scripts/derive_covariates.py` only prints a coverage table for the current register.

General conventions
-------------------
* Bangla digits are converted to ASCII before any number is parsed. All matching is case-insensitive. Text is Unicode
  NFC-normalised first, so precomposed and decomposed য়/ড়/ঢ় match the same patterns.
* GloMIP `market_segment` is not used: segments group many varieties and can contradict the variety (BRRI dhan84, a
  Boro variety, sits in a 'Lowlands; Drought Prone | Transplanted; Rainfed' segment). GloMIP `product_profile`, which
  positions the individual variety, is used for ecosystem and establishment.
* Blank ('') always means "not stated in the register text"; it never means "no" or "zero".
* Multi-valued cells are joined with '; ' in a fixed order (the order of the category lists below).
* A free-text cell that describes several varieties at once (two or more variety names such as 'ব্রিধান ৬৫ ... ব্রিধান ৬৬'
  in one recommended_region cell, copied from a compendium sentence) is not used for season or establishment, because the
  text cannot be attributed to one variety. It is still used for the region columns (the region applies to all of them).

Columns and rules
-----------------
season_aus, season_aman, season_boro, season_std   (inserted after `season`)
    Sources: `season` (Aus / Aman / T. Aman / Boro, any combination), the season labels inside `duration_days` and
    `yield_t_ha` (e.g. '130-135 (আউশ)'), and Bangla or English season words in `ecosystem`, `recommended_region`,
    `region_scope`, `special_traits_official`, `identifying_traits_official`, `stress_tolerance` when they appear as a
    season statement: '<season> মৌসুম', 'রোপা/বোনা <season>', '<season> ও <season> (উভয়) মৌসুমে'. A season word followed
    within 40 characters by a comparison word (চেয়ে, তুলনায়, অপেক্ষা, চেক, check, than) is ignored, because it names the season
    of a check variety. A flag is 1 when the season is named by any source; when at least one season is known the
    others are 0; when no source names a season all three are blank. season_std lists the seasons as 'aus; aman; boro'.

duration_min_days, duration_max_days, duration_by_season   (after `duration_days`)
    Every number or range in `duration_days` is read ('130-135', '155±5' = 150-160, '135.140' = 135-140). Values outside
    60-220 days are OCR noise ('034-154' keeps only 154) and are dropped. min/max are taken over all values in the cell,
    including condition-specific ones ('145 (জলমগ্ন না হলে); 155 (14 দিন জলমগ্ন থাকলে)' gives 145-155) and alternative
    printings ('132 (also printed 128-131)' gives 132 only: numbers inside a label are not values). When a value carries a
    season label (আউশ/আমন/বোরো or Aus/Aman/Boro) it is also written to duration_by_season, e.g. 'aus=130-135; aman=140-150'.

yield_min_t_ha, yield_max_t_ha, yield_by_season   (after `yield_t_ha`)
    Same parser as duration, with the unit text ('টন/হেঃ') removed and a plausible range of 1.5-15 t/ha (a lone '1' is
    dropped). Labels such as 'লবণাক্ত জমি', 'on-farm', 'drought' count toward min/max but are not seasons.

ecosystem_std, ecosystem_text_en, establishment, photoperiod   (after `ecosystem`)
    ecosystem_std: categories irrigated; rainfed lowland; upland; tidal; deepwater/haor; saline coastal; favourable.
      irrigated       : 'সেচ' or 'irrigated' in `ecosystem`, 'Irrigated lowland: Recommended' in product_profile,
                        'haor (Boro, irrigated)'.
      rainfed lowland : 'rainfed lowland' / 'Rainfed lowland: Recommended' (product_profile), a bare
                        'Rainfed' in `ecosystem` for an Aman-only variety, and flood- or submergence-prone areas
                        (বন্যা প্রবণ, আকস্মিক বন্যা, flash-flood, flood-prone) named as the target area.
      upland          : the English word 'upland' (`ecosystem`, or product_profile 'Upland: Recommended').
                        Bangla 'উঁচু জমি' is a land-elevation class (high land), not the upland rice ecosystem, so it is
                        kept in ecosystem_text_en only.
      tidal           : জোয়ার-ভাটা / জোয়ার / tidal in ecosystem or region text.
      deepwater/haor  : হাওর / হাওড় / haor / deepwater / গভীর পানি in ecosystem or region text.
      saline coastal  : a saline or coastal target area (লবণাক্ত/লবনাক্ত/উপকূলীয় + এলাকা/অঞ্চল/জমি, 'saline areas',
                        'coastal saline') in ecosystem, region or official trait text; 'অলবনাক্ত' (non-saline) never counts.
                        A salt-tolerance trait alone is not an ecosystem statement.
      favourable      : অনুকূল / favourable / favorable.
      No ecosystem is inferred from the season (Boro is irrigated in practice, but that is left to the analyst).
    ecosystem_text_en: a short English gloss of `ecosystem` ('irrigated; high, medium-high and medium-low land'), with
      the region-text ecosystem phrases appended (tidal areas, haor areas, saline areas, flood-prone areas).
    establishment: transplanted (রোপা, T. Aman, 'transplant', 'PTR: Recommended') and/or direct-seeded (বোনা, ছিটিয়ে,
      'direct-seeded', 'broadcast', 'DSR: Recommended'); 'both' when both are stated. Sources: season, ecosystem,
      recommended_region, region_scope, official trait text, key_traits, product_profile.
    photoperiod: 'sensitive' for আলোক সংবেদনশীল / সংবেদণশীল, 'photoperiod-sensitive' (including 'weakly', 'somewhat',
      স্বল্প, কিছুটা, and TRIVSA 'Photoperiod Sensitivity: High/Low'); 'insensitive' for আলোক অসংবেদনশীল, আলোক নিরপেক্ষ,
      'photoperiod insensitive'. Only explicit statements count. If both are stated for the same variety (a shared
      compendium cell) the value is blank.

grain_class   (after `quality_traits`)
    Read from grain phrases only, so plant height ('গাছ লম্বা') never counts: the grain_type= value in quality_traits, and
    phrases that start with চাল / চালের / দানা / grain (up to the next sentence break) in identifying_traits_official,
    special_traits_official and key_traits; and English 'long slender', 'medium bold' etc. anywhere in key_traits.
    Length: 'মাঝারি লম্বা' -> medium; লম্বা/লম্বাটে/long -> long; মাঝারি/মাঝারী/মধ্যম/medium -> medium;
            খাটো/ছোট/গোলাকার/short/round -> short.
    Shape : চিকন/সরু/slender/fine -> slender; মোটা/bold/coarse/গোলাকার/round -> bold.
    Result: '<length> <shape>' (long slender, medium slender, short bold, medium bold, long bold, short slender), or a
    partial value 'slender (length not stated)' / 'long (shape not stated)' when only one dimension is given. Sources are
    tried in the order above and the first complete class wins; a partial class is used only if no source is complete.

breeding_method   (after `pedigree_note`)
    Sources: pedigree, pedigree_note, origin_statement, type, developer_group. Values (several can apply, '; ' joined):
      introduction : developer_group 'Introduction (pre-BRRI)', or 'line collected from', 'collected from IRRI',
                     'IRRI line', 'obtained under ... collaboration'. Introduction is exclusive: a line bred abroad and
                     introduced is not also coded 'cross'. 'introduced as F4' after a written cross stays 'cross'.
      selection    : pure-line selection, 'selection from', বিশুদ্ধ কৌলিক সারি, 'local collection' (only when no cross).
      cross        : a cross is written ('/', ' x ', '×', '*n' backcross notation, 'cross', 'segregating population').
      mutation     : irradiation / mutant / গামা / কার্বন আয়ন / রশ্মি / মিউট্যান্ট, or type 'inbred (mutant)'.
      somaclonal   : 'somaclonal' or tissue-culture variant.
      biotech      : anther culture / doubled haploid / marker-assisted selection or backcross (MAS, MABC).
      hybrid (CMS 3-line): a hybrid whose stated parents include an A (CMS) line ('IR58025A/...', 'BRRI72A x ...',
                     'CMS'); hybrid (2-line): TGMS/PGMS/EGMS/'two-line' stated; hybrid (system not stated): any other
                     registered hybrid. Hybrid values are exclusive.
    Blank when the pedigree is empty or only names a single parent without saying how it was used.

region_divisions, region_nationwide   (after `recommended_region`)
    Text: recommended_region + region_scope. A clause marked '(discussion)' is dropped (the decision clause is kept).
    Nationwide: সারা দেশ / সারাদেশ / সমগ্র বাংলাদেশ / সারা বাংলাদেশ / (দেশের) সকল অঞ্চল / nationwide / whole country /
      all regions / all areas / all Bangladesh / all over -> region_nationwide = 1 and region_divisions = all eight
      divisions minus any division named in an exception clause ('except Khulna and Barisal', '(... ব্যতীত)').
      Exceptions by agro-ecological zone (AEZ) remove no division.
    Otherwise each district or division name (English, old and new spellings, Bangla with common OCR variants; table
      DISTRICTS below, 64 districts + upazila Sonagazi) is mapped to its BBS division (8 divisions, Mymensingh as a
      separate division since 2015). Hybrid registrations name SCA trial regions after their headquarters town
      (Comilla, Jessore, Dinajpur ...); these are mapped through the town's district, so 'Jessore' -> Khulna division.
      region_nationwide = 0 when divisions or a specific target area (এলাকা, অঞ্চল, area, region, AEZ) are named.
    Blank when neither field names a place (e.g. 'বোরো মৌসুমে চাষাবাদযোগ্য').

developer_std, developer_type, developer_country_of_origin   (after `developer`)
    developer_std: canonical English name from the DEVELOPERS table (BRRI, BINA, BAU, BSMRAU, BADC, University of
      Rajshahi, BRAC, and cleaned company names). Bangla names and spelling variants map to one name. Legally separate
      firms of one group stay separate (ACI Limited, ACI Formulations, ACI Agrolink). Gazipur Agricultural University is
      the 2024 name of BSMRAU and is coded BSMRAU. A name not in the table falls back to the cleaned original
      (legal suffixes such as Ltd/Limited/লিঃ removed). When `developer` is blank, developer_group BRRI/BINA/BADC is used.
    developer_type: public research institute (BRRI, BINA), university, public seed agency (BADC), NGO (BRAC and its
      seed enterprise, Ayesha Abed Foundation), foreign public (IRRI), otherwise private company.
    developer_country_of_origin: only from what the register states in origin_country / origin_statement (the import or
      germplasm origin recorded in NSB minutes, e.g. 'China', 'India', 'Philippines (IRRI)'); 'China (as corrected by
      NSB 91 ...)' -> China. origin_country wins over origin_statement when both are filled (Partex hybrid dhan5 and
      Petrochem hybrid dhan4 keep the NSB 91 correction). Never inferred from the company's nationality.

Version 1.2 changes (REV2, 2026-11-10; reviews A1/A2/A4 of November 2026)
------------------------------------------------------------------------
* season flags: the season labels inside duration_days / yield_t_ha are used only when `season` itself is blank, so a
  duration printed for another season ('Boro: 145 d' for an Aman variety) no longer adds that season (GAU dhan3, Binadhan-17).
* region: region_scope (the English controlled summary taken from the approving decision or official list) decides the
  region when it names one; recommended_region is used only when region_scope is blank or names no place. region_nationwide
  is 1 only when the whole country is covered: a nationwide statement with an exception that removes a division
  ('except Khulna and Barisal', BRRI dhan37 and 38 at NSB 41) gives region_nationwide = 0 and the remaining divisions.
* developer_std for the five pre-BRRI introductions is the breeding institution, not BRRI: IRRI (IR5, IR8, IR20, foreign
  public), 'introduction (Malaysia)' (Pajam, a Mahsuri selection) and 'introduction (China)' (Purbachi), developer_type
  'introduction' for the last two. The `developer` column still shows the source text (BRRI as the introducing agency).
* yield_basis (after yield_by_season): what the yield figure is, from the source of the winning yield value
  (yield_source_id, written by assemble.py): 'NSB trial mean' (NSB decision: mean of the Board's multi-location trials),
  'official list' (SCA annual list, compendium or MoA hybrid list, which copy trial or applicant figures), 'gazette notice',
  'institute (advertised)' (BRRI/BINA fact sheets and web pages: average or potential yield as the institute advertises it),
  'other' (CGIAR or secondary sources). Yields of different bases are not comparable.
"""
import re
import unicodedata

import pandas as pd

BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
SEASONS = ["aus", "aman", "boro"]
SEASON_WORDS = {"aus": r"আউশ|\baus\b", "aman": r"আমন|\baman\b", "boro": r"বোরো|\bboro\b"}
DIVISIONS = ["Barishal", "Chattogram", "Dhaka", "Khulna", "Mymensingh", "Rajshahi", "Rangpur", "Sylhet"]

# district (English spellings | Bangla spellings incl. OCR variants) -> division
DISTRICTS = {
    "Barishal": [("Barguna", "বরগুনা"), ("Barishal|Barisal", "বরিশাল"), ("Bhola", "ভোলা"),
                 ("Jhalokati|Jhalakati", "ঝালকাঠি"), ("Patuakhali", "পটুয়াখালী|পটুয়াখালি"), ("Pirojpur", "পিরোজপুর")],
    "Chattogram": [("Bandarban", "বান্দরবান"), ("Brahmanbaria|B\\.? ?Baria", "ব্রাহ্মণবাড়িয়া|বি\\.? ?বাড়িয়া"),
                   ("Chandpur", "চাঁদপুর"), ("Chattogram|Chittagong", "চট্টগ্রাম|চট্রগ্রাম|চট্ট্রগ্রাম"),
                   ("Cumilla|Comilla", "কুমিল্লা|কুমিলা"), ("Cox'?s ?Bazar", "কক্সবাজার"), ("Feni|Sonagazi", "ফেনী|সোনাগাজী"),
                   ("Khagrachhari|Khagrachari", "খাগড়াছড়ি"), ("Lakshmipur|Laxmipur", "লক্ষ্মীপুর"),
                   ("Noakhali", "নোয়াখালী|নোয়াখালি"), ("Rangamati", "রাঙ্গামাটি|রাঙামাটি")],
    "Dhaka": [("Dhaka", "ঢাকা"), ("Faridpur", "ফরিদপুর"), ("Gazipur", "গাজীপুর"), ("Gopalganj", "গোপালগঞ্জ"),
              ("Kishoreganj", "কিশোরগঞ্জ"), ("Madaripur", "মাদারীপুর"), ("Manikganj", "মানিকগঞ্জ"),
              ("Munshiganj", "মুন্সীগঞ্জ|মুন্সিগঞ্জ"), ("Narayanganj", "নারায়ণগঞ্জ|নারায়ণগঞ্জ"), ("Narsingdi", "নরসিংদী"),
              ("Rajbari", "রাজবাড়ী"), ("Shariatpur", "শরীয়তপুর"), ("Tangail", "টাঙ্গাইল")],
    "Khulna": [("Bagerhat", "বাগেরহাট"), ("Chuadanga", "চুয়াডাঙ্গা|চুয়াডাংগা"), ("Jashore|Jessore", "যশোর"),
               ("Jhenaidah", "ঝিনাইদহ"), ("Khulna", "খুলনা"), ("Kushtia", "কুষ্টিয়া"), ("Magura", "মাগুরা"),
               ("Meherpur", "মেহেরপুর"), ("Narail", "নড়াইল"), ("Satkhira", "সাতক্ষীরা")],
    "Mymensingh": [("Jamalpur", "জামালপুর"), ("Mymensingh", "ময়মনসিংহ|ময়মনসিংহ|মংমনসিংহ|ময়মনসিং"),
                   ("Netrokona|Netrakona", "নেত্রকোনা"), ("Sherpur", "শেরপুর")],
    "Rajshahi": [("Bogura|Bogra", "বগুড়া"), ("Joypurhat|Jaipurhat", "জয়পুরহাট"), ("Naogaon", "নওগাঁ"),
                 ("Natore", "নাটোর"), ("Chapai ?Nawabganj", "চাঁপাইনবাবগঞ্জ"), ("Pabna", "পাবনা"),
                 ("Rajshahi", "রাজশাহী"), ("Sirajganj", "সিরাজগঞ্জ")],
    "Rangpur": [("Dinajpur", "দিনাজপুর"), ("Gaibandha", "গাইবান্ধা"), ("Kurigram", "কুড়িগ্রাম"),
                ("Lalmonirhat", "লালমনিরহাট"), ("Nilphamari", "নীলফামারী"), ("Panchagarh", "পঞ্চগড়"),
                ("Rangpur", "রংপুর"), ("Thakurgaon", "ঠাকুরগাঁও")],
    "Sylhet": [("Habiganj", "হবিগঞ্জ"), ("Moulvibazar|Maulvibazar", "মৌলভীবাজার"), ("Sunamganj", "সুনামগঞ্জ"),
               ("Sylhet", "সিলেট")],
}
_DIST_RX = [(div, re.compile(rf"\b({en})\b", re.I), re.compile(bn)) for div, lst in DISTRICTS.items() for en, bn in lst]

NATIONWIDE = re.compile(r"সারা ?দেশ|সমগ্র বাংলাদেশ|সারা বাংলাদেশ|সকল অঞ্চল|nationwide|whole country|all regions|all areas"
                        r"|all bangladesh|all over", re.I)

# (pattern on the raw developer text, canonical name, type)
PUB, UNI, AGY, NGO, FOR, PVT = ("public research institute", "university", "public seed agency", "NGO",
                                "foreign public", "private company")
DEVELOPERS = [
    (r"^BRRI$|ব্রি\b|^ব্রি$|ধান গবেষণা ইনস্টিটিউট", "BRRI", PUB),
    (r"^BINA$|বিনা|পরমাণু|পরমানু", "BINA", PUB),
    (r"^BAU$|বাংলাদেশ কৃষি বিশ্ববিদ্যালয়", "BAU", UNI),
    (r"BSMRAU|বঙ্গবন্ধু শেখ মুজিবুর রহমান কৃষি|Gazipur Agricultural University|গাজীপুর কৃষি বিশ্ববিদ্যালয়", "BSMRAU", UNI),
    (r"রাজশাহী বিশ্ববিদ্যালয়|University of Rajshahi", "University of Rajshahi", UNI),
    (r"^BADC$|কৃষি উন্নয়ন কর্পোরেশন", "BADC", AGY),
    (r"\bIRRI\b", "IRRI", FOR),
    (r"Ayesha Abed|আয়শা আবেদ|আয়শা আবেদ", "Ayesha Abed Foundation", NGO),
    (r"BRAC|বর্যাক|ব্র্যাক|ব্রাক", "BRAC", NGO),
    (r"Supreme Seed|সুপ্রিম সীড|সুপ্রীম সীড", "Supreme Seed Company", PVT),
    (r"ACI Formulations|ফরমোলেশন", "ACI Formulations", PVT),
    (r"ACI Agrolink", "ACI Agrolink", PVT),
    (r"এসিআই এগ্রো কেমিক্যালস", "ACI Agrochemicals", PVT),
    (r"^ACI\b|এসিআই|এ সি আই", "ACI Limited", PVT),
    (r"Mahyco|মাহিকো", "Mahyco Bangladesh", PVT),
    (r"Partex", "Partex Agro", PVT),
    (r"Bayer|বায়ার|বায়ার", "Bayer CropScience Bangladesh", PVT),
    (r"Aftab|আফতাব", "Aftab Bahumukhi Farms", PVT),
    (r"North South Seed", "North South Seed", PVT),
    (r"Three S Agro", "Three S Agro Services", PVT),
    (r"VNR", "VNR Seeds Bangladesh", PVT),
    (r"ইস্পাহানী মার্[শস]েল", "Ispahani Marshall", PVT),
    (r"Ispahani Foods", "Ispahani Foods", PVT),
    (r"Ispahani", "Ispahani Agro", PVT),
    (r"Syngenta|সিনজেন্টা|সিনজেনটা", "Syngenta Bangladesh", PVT),
    (r"Win ?all Hi-Tech", "Winall Hi-Tech Seed Co.", PVT),
    (r"National Agri ?Care|ন্যাশনাল এগ্রি ?কেয়ার", "National Agri Care Import and Export", PVT),
    (r"Mitali Enterprise", "Mitali Enterprise", PVT),
    (r"Mitali Agro|মিতালী এগ্রো", "Mitali Agro Seed Industries", PVT),
    (r"Petrochem|পেট্রোকেম", "Petrochem Agro Industries", PVT),
    (r"Metal Agro", "Metal Agro", PVT),
    (r"মেটাল সীড", "Metal Seed Co.", PVT),
    (r"Tinpata", "Tinpata Quality Seeds Bangladesh", PVT),
    (r"Lal Teer|লাল তীর", "Lal Teer Seed", PVT),
    (r"ইউনাইটেড সীড", "United Seed Store", PVT),
    (r"Mallika|মল্লিকা", "Mallika Seed Company", PVT),
    (r"নর্দান সীড", "Northern Seed", PVT),
    (r"নদার্ন এগ্রিকালচারাল", "Northern Agricultural and Industrial Co.", PVT),
    (r"হিমাদ্রী", "Himadri Ltd", PVT),
    (r"Golden Barn", "Golden Barn Kingdom Bangladesh", PVT),
    (r"East ?-?West Seed", "East-West Seed Bangladesh", PVT),
    (r"Babylon", "Babylon Agriscience", PVT),
    (r"এনার্জি প্যাক|Energy ?pac", "Energypac", PVT),
    (r"Krishibid", "Krishibid Farm", PVT),
    (r"Masud Seed", "Masud Seed Co.", PVT),
    (r"Vision Agro", "Vision Agro", PVT),
    (r"ন্যাশনাল সীড", "National Seed Co.", PVT),
    (r"Raisco", "Raisco International Bangladesh", PVT),
    (r"Surovi|সুরভী", "Surovi Agro Industries", PVT),
    (r"আলমগীর সীড", "Alamgir Seed Co.", PVT),
    (r"American Advanced Agro", "American Advanced Agro", PVT),
    (r"Amin Agro", "Amin Agro Services", PVT),
    (r"Auto ?crop|অটো ক্রপ", "Autocrop Care", PVT),
    (r"Aus-Bangla", "Aus-Bangla Agro", PVT),
    (r"ট্রপিকেল এগ্রোটেক", "Tropical Agrotech", PVT),
    (r"Lily|লিলি", "Lily and Co.", PVT),
    (r"Krishi Banijya", "Krishi Banijya Protishthan", PVT),
    (r"মুক্তারপুর", "Muktarpur Bhandar", PVT),
    (r"Getco Agro ?Vision|Getco Agrovision", "Getco Agro Vision", PVT),
    (r"Getco", "Getco Agri Technologies", PVT),
    (r"Giant Agro", "Giant Agro Processing", PVT),
    (r"আলফা সীড|Alpha Seed", "Alpha Seed International", PVT),
    (r"কানের্ল ইন্টারন্যাশনাল|Kernel International", "Kernel International", PVT),
    (r"Explore", "Explore Business", PVT),
    (r"ডুপন্ট|DuPont", "DuPont Bangladesh", PVT),
    (r"Farmers Seed", "Farmers Seed Company", PVT),
    (r"Ganges Development", "Ganges Development Corporation", PVT),
    (r"বেলী এগ্রো", "Beli Agro", PVT),
    (r"Bagro|ব্যাগরো", "Bagro Company", PVT),
    (r"Blessing Agrovet", "Blessing Agrovet Industries", PVT),
    (r"নিপা ট্রেডিং", "Nipa Trading International", PVT),
    (r"Quality Seed|কোয়ালিটি সীড|কোয়ালিটি সীড", "Quality Seed Co.", PVT),
    (r"ষ্টার পা", "Star Particle Board", PVT),
    (r"Nilsagar", "Nilsagar Seed and Tissue Culture", PVT),
    (r"NAFCO|নাফকো", "NAFCO", PVT),
    (r"সী ট্রেড", "Sea Trade Fertilizer", PVT),
    (r"McDonald|ম্যাকডোনাল্ড", "McDonald Seeds", PVT),
    (r"মালিক এন্ড মালিক", "Malik and Malik Seed Co.", PVT),
    (r"সিদ্দিকী সীড", "Siddiqui Seeds Co.", PVT),
    (r"এফেক্স ক্রাপ্ট", "Afex Craft", PVT),
    (r"কামাল সীড", "Kamal Seed Co.", PVT),
    (r"Sabuj Bangla", "Sabuj Bangla Agro", PVT),
    (r"Chens", "Chens Crop Science Bangladesh", PVT),
    (r"Rising Sun|Super Seed", "Rising Sun Seed Company", PVT),
]
_DEV_RX = [(re.compile(p, re.I), name, typ) for p, name, typ in DEVELOPERS]

NEW_COLS = {
    "season": ["season_aus", "season_aman", "season_boro", "season_std"],
    "duration_days": ["duration_min_days", "duration_max_days", "duration_by_season"],
    "yield_t_ha": ["yield_min_t_ha", "yield_max_t_ha", "yield_by_season", "yield_basis"],
    "ecosystem": ["ecosystem_std", "ecosystem_text_en", "establishment", "photoperiod"],
    "quality_traits": ["grain_class"],
    "pedigree_note": ["breeding_method"],
    "recommended_region": ["region_divisions", "region_nationwide"],
    "developer": ["developer_std", "developer_type", "developer_country_of_origin"],
}


def _bn(s):
    return (s or "").translate(BN_DIGITS)


def _multi_variety(text):
    """True when a cell names two or more varieties (a compendium sentence covering several releases)."""
    return len(re.findall(r"ধান\s*-?\s*[0-9০-৯]+", text)) >= 2


def _season_of_label(label):
    hits = [s for s in SEASONS if re.search(SEASON_WORDS[s], label, re.I)]
    return hits[0] if len(hits) == 1 else ""


# --------------------------------------------------------------------------------------------- numbers by season
NUM_RX = re.compile(r"(\d+(?:\.\d+)?)(?:\s*[-–]\s*(\d+(?:\.\d+)?))?\s*(?:\(([^)]*)\))?")


def _parse_ranges(text, lo, hi, kind):
    t = _bn(text)
    t = re.sub(r"টন/হেঃ?|t/ha|দিন|days?", " ", t)
    t = re.sub(r"(\d+)\s*±\s*(\d+)", lambda m: f"{int(m.group(1)) - int(m.group(2))}-{int(m.group(1)) + int(m.group(2))}", t)
    if kind == "duration":
        t = re.sub(r"(?<=\b\d{3})\.(?=\d{3}\b)", "-", t)
    vals, by_season = [], {}
    for a, b, label in NUM_RX.findall(t):
        nums = [float(x) for x in (a, b) if x]
        nums = [x for x in nums if lo <= x <= hi]
        if not nums:
            continue
        vals += nums
        s = _season_of_label(label or "")
        if s:
            by_season.setdefault(s, []).extend(nums)
    return vals, by_season


def _fmt(x, kind):
    return str(int(round(x))) if kind == "duration" else f"{x:g}"


def _range_cols(text, lo, hi, kind):
    vals, by = _parse_ranges(text, lo, hi, kind)
    if not vals:
        return "", "", ""
    seg = []
    for s in SEASONS:
        if s in by:
            a, b = min(by[s]), max(by[s])
            seg.append(f"{s}={_fmt(a, kind)}" + (f"-{_fmt(b, kind)}" if b != a else ""))
    return _fmt(min(vals), kind), _fmt(max(vals), kind), "; ".join(seg)


# --------------------------------------------------------------------------------------------- season
SEASON_TEXT_COLS = ["ecosystem", "recommended_region", "region_scope", "special_traits_official",
                    "identifying_traits_official", "stress_tolerance"]
COMPARE = r"[^।|;]{0,40}(চেয়ে|চেয়ে|তুলনায়|অপেক্ষা|চেক|check|than)"


def _seasons(row):
    found = set()
    for tok in re.split(r"[;,/]", row.get("season", "")):
        for s in SEASONS:
            if re.search(SEASON_WORDS[s], tok, re.I):
                found.add(s)
    for col in (("duration_days", "yield_t_ha") if not found else ()):
        for label in re.findall(r"\(([^)]*)\)", row.get(col, "")):
            s = _season_of_label(label)
            if s:
                found.add(s)
    for col in SEASON_TEXT_COLS:
        text = row.get(col, "")
        if not text or _multi_variety(text):
            continue
        for s in SEASONS:
            w = SEASON_WORDS[s]
            pats = [rf"(?:{w})\s*মৌসুম", rf"(রোপা|বোনা)\s*(?:{w})", rf"(?:{w})\s*(ও|এবং|,)\s*(আউশ|আমন|বোরো)[^।|;]{{0,12}}মৌসুম",
                    rf"(আউশ|আমন|বোরো)\s*(ও|এবং|,)\s*(?:{w})[^।|;]{{0,12}}মৌসুম", rf"\b(T\.|transplanted|direct-seeded)\s*(?:{w})",
                    rf"\(\s*(?:{w})\b"]
            for p in pats:
                for m in re.finditer(p, text, re.I):
                    if not re.match(COMPARE, text[m.end():], re.I):
                        found.add(s)
    if not found:
        return {"season_aus": "", "season_aman": "", "season_boro": "", "season_std": ""}
    out = {f"season_{s}": "1" if s in found else "0" for s in SEASONS}
    out["season_std"] = "; ".join(s for s in SEASONS if s in found)
    return out


# --------------------------------------------------------------------------------------------- ecosystem
ECO_ORDER = ["irrigated", "rainfed lowland", "upland", "tidal", "deepwater/haor", "saline coastal", "favourable"]
SALINE_AREA = r"(?<!অ)(লবণাক্ত|লবনাক্ত|উপকূলীয়)\S*\s*(এলাকা|অঞ্চল|জমি)|saline areas?|coastal saline|saline coastal"
FLOOD_AREA = r"বন্যা ?প্রবণ|আকস্মিক বন্যা|flash-?flood|flood-?prone|submergence\) prone"


def _ecosystem(row):
    eco = row.get("ecosystem", "")
    reg = row.get("recommended_region", "") + " | " + row.get("region_scope", "")
    trait = row.get("special_traits_official", "") + " | " + row.get("identifying_traits_official", "")
    pp = row.get("product_profile", "")
    found = set()
    if re.search(r"সেচ|irrigated", eco, re.I) or re.search(r"Irrigated lowland:\s*Recommended", pp, re.I):
        found.add("irrigated")
    if re.search(r"rainfed lowland", eco, re.I) or re.search(r"Rainfed lowland:\s*Recommended", pp, re.I) \
            or (re.search(r"rainfed", eco, re.I) and row.get("season", "").strip().lower().endswith("aman")
                and "aus" not in row.get("season", "").lower() and "boro" not in row.get("season", "").lower()):
        found.add("rainfed lowland")
    if re.search(FLOOD_AREA, eco + " " + reg, re.I):
        found.add("rainfed lowland")
    if re.search(r"Upland:\s*Recommended", pp, re.I) or re.search(r"\bupland\b", eco, re.I):
        found.add("upland")
    if re.search(r"জোয়ার|জোয়ার|tidal", eco + " " + reg, re.I):
        found.add("tidal")
    if re.search(r"হাওর|হাওড়|হাওড|haor|deep ?water|গভীর পানি", eco + " " + reg, re.I):
        found.add("deepwater/haor")
    if re.search(SALINE_AREA, eco + " " + reg + " " + trait, re.I):
        found.add("saline coastal")
    if re.search(r"অনুকূল|favou?rable", eco + " " + reg, re.I):
        found.add("favourable")
    return "; ".join(e for e in ECO_ORDER if e in found)


LAND = [("medium-high", r"(মধ্যম|মাঝারি|মাঝারী) উঁচু"), ("medium-low", r"(মধ্যম|মাঝারি|মাঝারী) নিচু"),
        ("high", r"(?<!মধ্যম )(?<!মাঝারি )(?<!মাঝারী )উঁচু"), ("low", r"(?<!মধ্যম )(?<!মাঝারি )(?<!মাঝারী )নিচু")]


def _ecosystem_gloss(row):
    eco = row.get("ecosystem", "")
    reg = row.get("recommended_region", "") + " | " + row.get("region_scope", "")
    parts = []
    if eco and not re.search(r"[ঀ-৿]", eco):
        parts.append(eco.strip().lower())
    elif eco:
        if "সেচ" in eco:
            parts.append("irrigated")
        lands = [en for en, p in LAND if re.search(p, eco)]
        order = ["high", "medium-high", "medium-low", "low"]
        lands = [x for x in order if x in lands]
        if lands:
            txt = lands[0] if len(lands) == 1 else ", ".join(lands[:-1]) + " and " + lands[-1]
            parts.append(txt + " land" + (" (step 2)" if "ধাপ-২" in eco else ""))
    extra = [("tidal areas", r"জোয়ার|জোয়ার|tidal"), ("haor areas", r"হাওর|হাওড়|হাওড|haor"),
             ("saline areas", SALINE_AREA), ("flood-prone areas", FLOOD_AREA)]
    for label, p in extra:
        if re.search(p, eco + " " + reg, re.I) and label not in parts:
            parts.append(label)
    return "; ".join(dict.fromkeys(p for p in parts if p))


def _establishment(row):
    texts = [row.get(c, "") for c in ("season", "ecosystem", "recommended_region", "region_scope",
                                      "special_traits_official", "identifying_traits_official", "key_traits")]
    texts = [t for t in texts if t and not _multi_variety(t)]
    t = " | ".join(texts)
    pp = row.get("product_profile", "")
    tp = bool(re.search(r"রোপা|\bT\. ?Aman|transplant", t, re.I) or re.search(r"PTR:\s*Recommended", pp))
    ds = bool(re.search(r"বোনা|ছিটিয়ে|direct[- ]?seed|broadcast", t, re.I) or re.search(r"DSR:\s*Recommended", pp))
    return "both" if tp and ds else "transplanted" if tp else "direct-seeded" if ds else ""


def _photoperiod(row):
    t = " | ".join(row.get(c, "") for c in ("special_traits_official", "identifying_traits_official",
                                             "stress_tolerance", "key_traits", "product_profile"))
    ins = re.search(r"আলোক[\s-]*অসংবেদ[নণ]শীল|আলোক[\s-]*নিরপেক্ষ|photo(period)?[\s-]*insensitiv", t, re.I)
    t2 = re.sub(r"আলোক[\s-]*অসংবেদ[নণ]শীল|photo(period)?[\s-]*insensitiv\w*", " ", t, flags=re.I)
    sen = re.search(r"আলোক[\s-]*সংবেদ[নণ]শীল|photo(period)?[\s-]*sensitiv|Photoperiod Sensitivity:\s*(High|Low)", t2, re.I)
    if ins and sen:
        return ""
    return "insensitive" if ins else "sensitive" if sen else ""


# --------------------------------------------------------------------------------------------- grain
def _grain_from(text):
    if not text:
        return "", ""
    t = text.lower()
    length = shape = ""
    if re.search(r"মাঝারি লম্বা|মাঝারী লম্বা|medium[- ]long", t):
        length = "medium"
    elif re.search(r"লম্বা|\blong\b|extra[- ]long", t):
        length = "long"
    elif re.search(r"মাঝারি|মাঝারী|মধ্যম|\bmedium\b", t):
        length = "medium"
    elif re.search(r"খাটো|ছোট|গোলাকার|\bshort\b|\bround", t):
        length = "short"
    if re.search(r"চিকন|সরু|slender|\bfine\b", t):
        shape = "slender"
    elif re.search(r"মোটা|\bbold\b|coarse|গোলাকার|\bround", t):
        shape = "bold"
    return length, shape


def _grain_phrases(row):
    out = []
    m = re.search(r"grain_type=([^;]*)", row.get("quality_traits", ""))
    if m:
        out.append(m.group(1))
    for col in ("identifying_traits_official", "special_traits_official", "key_traits"):
        text = row.get(col, "")
        for m in re.finditer(r"(চাল|দানা|grain)[^।|;•\n.]{0,40}", text, re.I):
            out.append(m.group(0))
        if col == "key_traits":
            for m in re.finditer(r"\b(long|medium|short)[\s-]+(slender|bold)\b", text, re.I):
                out.append(m.group(0))
    return out


def _grain_class(row):
    partial = ""
    for ph in _grain_phrases(row):
        length, shape = _grain_from(ph)
        if length and shape:
            return f"{length} {shape}"
        if not partial and (length or shape):
            partial = f"{shape} (length not stated)" if shape else f"{length} (shape not stated)"
    return partial


# --------------------------------------------------------------------------------------------- breeding method
def _breeding(row):
    ped = " | ".join(row.get(c, "") for c in ("pedigree", "pedigree_note", "origin_statement"))
    typ = row.get("type", "")
    if row.get("rice_type", "") == "hybrid" or typ.lower() == "hybrid":
        par = ped + " " + row.get("hybrid_parent_female", "") + " " + row.get("hybrid_parent_male", "")
        if re.search(r"TGMS|PGMS|EGMS|two[- ]line|2[- ]line|দ্বি-?লাইন", par, re.I):
            return "hybrid (2-line)"
        if re.search(r"\bCMS\b|\w*\dA\s*(/|x\b|×)|\bA[- ]line", par):
            return "hybrid (CMS 3-line)"
        return "hybrid (system not stated)"
    if not ped.strip(" |") and "mutant" not in typ.lower() and row.get("developer_group", "") != "Introduction (pre-BRRI)":
        return ""
    if row.get("developer_group", "") == "Introduction (pre-BRRI)" or re.search(
            r"line collected from|collected from IRRI|IRRI line|obtained under", ped, re.I):
        return "introduction"
    found = []
    is_cross = bool(re.search(r"/|\sx\s|×|\*\s*\d|\bcross|segregating population", ped, re.I))
    if not is_cross and re.search(r"pure-?\s?line selection|selection from|বিশুদ্ধ কৌলিক সারি|local collection", ped, re.I):
        found.append("selection")
    if is_cross:
        found.append("cross")
    if re.search(r"irradiat|mutant|mutation|gamma|গামা|কার্বন আয়ন|carbon[- ]ion|রশ্মি|মিউট্যান্ট", ped, re.I) \
            or "mutant" in typ.lower():
        found.append("mutation")
    if re.search(r"somaclonal|সোমাক্লোনাল|tissue culture", ped, re.I):
        found = [f for f in found if f != "mutation"] + ["somaclonal"]
    if re.search(r"anther culture|doubled haploid|marker[- ]assisted|\bMAS\b|\bMABC\b", ped, re.I):
        found.append("biotech")
    return "; ".join(dict.fromkeys(found))


# --------------------------------------------------------------------------------------------- region
def _divisions_in(text):
    hits = set()
    for div, en, bn in _DIST_RX:
        if en.search(text) or bn.search(text):
            hits.add(div)
    return hits


def _region(row):
    scope = re.sub(r";[^;|]*\(discussion\)", "", row.get("region_scope", "")).strip()
    rec = row.get("recommended_region", "")
    names_place = bool(scope) and (NATIONWIDE.search(scope) or _divisions_in(scope))
    text = scope if names_place else (rec + " | " + scope)
    text = re.sub(r";[^;|]*\(discussion\)", "", text)
    if not text.strip(" |"):
        return "", ""
    excl_txt = " ".join(re.findall(r"except\s+([^;()|]*)", text, re.I) + re.findall(r"\(([^)]*)ব্যতীত", text))
    excluded = _divisions_in(excl_txt)
    main = re.sub(r"except\s+[^;()|]*", " ", text, flags=re.I)
    main = re.sub(r"\([^)]*ব্যতীত\)?", " ", main)
    if NATIONWIDE.search(main) or re.search(r"\ball\s+except\b", text, re.I):   # 'all except Khulna and Barisal' (NSB 41)
        return "; ".join(d for d in DIVISIONS if d not in excluded), "0" if excluded else "1"
    divs = _divisions_in(main)
    if divs:
        return "; ".join(d for d in DIVISIONS if d in divs), "0"
    if re.search(r"এলাকা|অঞ্চল|\barea|\bregion|AEZ|কৃষি পরিবেশ", main, re.I):
        return "", "0"
    return "", ""


# --------------------------------------------------------------------------------------------- developer
INTRODUCTIONS = {"RICE-IR5": ("IRRI", FOR), "RICE-IR8": ("IRRI", FOR), "RICE-IR20": ("IRRI", FOR),
                 "RICE-OLD_PAJAM": ("introduction (Malaysia)", "introduction"), "RICE-OLD_PURBACHI": ("introduction (China)", "introduction")}


def _developer(row):
    raw = row.get("developer", "").strip()
    if not raw and row.get("developer_group", "") in ("BRRI", "BINA"):
        raw = row["developer_group"]
    elif not raw and row.get("developer_group", "").startswith("BADC"):
        raw = "BADC"
    name, typ = "", ""
    if raw:
        for rx, n, t in _DEV_RX:
            if rx.search(raw):
                name, typ = n, t
                break
        if not name:
            name = re.sub(r"\s*(Ltd\.?|Limited|লিঃ|লিমিটেড|প্রাঃ|\(Pvt\.?\))\s*", " ", raw).strip()
            typ = PVT
    if row.get("variety_id", "") in INTRODUCTIONS:      # bred abroad; BRRI (or its predecessors) introduced them
        name, typ = INTRODUCTIONS[row["variety_id"]]
    origin = row.get("origin_country", "") or row.get("origin_statement", "")
    cs = []
    for label, p in [("Bangladesh", r"Bangladesh"), ("China", r"China|Chinese"), ("India", r"India"),
                     ("Philippines (IRRI)", r"Philippines|IRRI"), ("Vietnam", r"Vietnam")]:
        if re.search(p, re.sub(r"\(as corrected[^)]*\)", "", origin)):
            cs.append(label)
    return name, typ, "; ".join(cs)


def _yield_basis(row):
    if not row.get("yield_t_ha", "").strip():
        return ""
    sid = row.get("yield_source_id", "")
    if re.match(r"NSB_", sid): return "NSB trial mean"
    if re.match(r"SCA|MOA", sid): return "official list"
    if re.match(r"GA?Z_", sid): return "gazette notice"
    if re.match(r"RB-|DS-S07|BRRI|BINA", sid): return "institute (advertised)"
    return "other" if sid else ""


# --------------------------------------------------------------------------------------------- assembly
def add(df):
    """Return a copy of the register with the derived covariates inserted after their source columns."""
    df = df.copy()
    recs = []
    for row in df.fillna("").to_dict("records"):
        row = {k: unicodedata.normalize("NFC", str(v)) for k, v in row.items()}
        r = dict(_seasons(row))
        r["duration_min_days"], r["duration_max_days"], r["duration_by_season"] = \
            _range_cols(row.get("duration_days", ""), 60, 220, "duration")
        r["yield_min_t_ha"], r["yield_max_t_ha"], r["yield_by_season"] = \
            _range_cols(row.get("yield_t_ha", ""), 1.5, 15, "yield")
        r["yield_basis"] = _yield_basis(row)
        r["ecosystem_std"] = _ecosystem(row)
        r["ecosystem_text_en"] = _ecosystem_gloss(row)
        r["establishment"] = _establishment(row)
        r["photoperiod"] = _photoperiod(row)
        r["grain_class"] = _grain_class(row)
        r["breeding_method"] = _breeding(row)
        r["region_divisions"], r["region_nationwide"] = _region(row)
        r["developer_std"], r["developer_type"], r["developer_country_of_origin"] = _developer(row)
        recs.append(r)
    new = pd.DataFrame(recs, index=df.index).astype(str)
    cols = [c for c in df.columns if c not in new.columns]
    order = []
    for c in cols:
        order.append(c)
        order += NEW_COLS.get(c, [])
    for anchor, added in NEW_COLS.items():   # an anchor missing from the register: append at the end
        if anchor not in cols:
            order += added
    out = pd.concat([df[cols], new], axis=1)
    return out[order]


def coverage(df):
    """Share of non-blank values for every derived column, by rice_type (inbred / hybrid / all)."""
    cols = [c for v in NEW_COLS.values() for c in v]
    rows = []
    for c in cols:
        rec = {"column": c}
        for grp, sub in [("inbred", df[df.rice_type == "inbred"]), ("hybrid", df[df.rice_type == "hybrid"]), ("all", df)]:
            n = (sub[c].astype(str).str.strip() != "").sum()
            rec[f"{grp}_n"], rec[f"{grp}_pct"] = int(n), round(100 * n / max(len(sub), 1), 1)
        rows.append(rec)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    import pathlib
    import sys
    root = pathlib.Path(__file__).resolve().parents[1]
    reg = pd.read_csv(root / "05_output/final/bgd_rice_varieties.csv", dtype=str, keep_default_na=False)
    out = add(reg)
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"register {reg.shape} -> {out.shape}")
    print(coverage(out).to_string(index=False))
