"""P2B: build 04_working/evidence_P2B.csv (long format, one row per pilot_key x field x source).
Inputs: the P2B extracted tables (ADC 2025 Table 1, SPIA 2025 T27, Rice Profile, HarvestPlus BD) plus TRIVSA
(xlsx) and a small number of hand-transcribed prose statements (fact sheets, ADC prose, BINA pages, IAEA),
each with its locator and the crop used for the visual check."""
import csv, pathlib, re
import pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
T = ROOT / "03_extracted/tables"
HDR = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file",
       "page", "locator", "method", "validation", "confidence", "notes"]
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
rows = []


def add(pk, field, value, raw, src, page="", loc="", method="pdf_text", val="unvalidated", conf="high", notes=""):
    s = SRC[src]
    rows.append({"pilot_key": pk, "field": field, "value": value, "value_raw": raw, "source_id": s[0],
                 "source_title": s[1], "authority_rank": s[2], "local_file": s[3], "page": page,
                 "locator": loc, "method": method, "validation": val, "confidence": conf, "notes": notes})


SRC = {
    "ADC": ("RB-S01", "BRRI Adhunik Dhaner Chash, 25th ed. (June 2025)", "3_institute_page",
            "02_raw/brri/brri_adhunik_dhaner_chash_2025_adc2025.pdf"),
    "SPIA": ("DS-S01", "SPIA Bangladesh Study 2025, Appendix B Table 27", "4_cgiar_record",
             "02_raw/spia_cgspace/SPIA_Bangladesh_Study_2025.pdf"),
    "TRIVSA": ("DS-S04", "TRIVSA rice data (IRRI/ASTI), sheet Releases", "4_cgiar_record",
               "02_raw/asti_trivsa/TRIVSA-Rice-Data.xlsx"),
    "RP": ("DS-S07", "BRRI Rice Profile (riceprofile.brri.gov.bd)", "3_institute_page", None),
    "HP": ("DS-S06", "HarvestPlus BCR API details_varieties_released", "4_cgiar_record",
           "02_raw/harvestplus/bcr_details_varieties_released.json"),
    "FS118": ("RB-S04", "BRRI fact sheet BRRI dhan118 (Jan 2026)", "3_institute_page",
              "02_raw/brri/brri_variety_BRRIdhan118_2026-01.pdf"),
    "FSBR1": ("RB-S04", "BRRI fact sheet BR1 (Dec 2024)", "3_institute_page", "02_raw/brri/brri_variety_BR1_aus_2024-12.pdf"),
    "FSH1": ("RB-S04", "BRRI fact sheet BRRI hybrid dhan1 (Dec 2024)", "3_institute_page",
             "02_raw/brri/brri_variety_BRRIhybriddhan1_2024-12.pdf"),
    "BRRINEW": ("RB-S08", "brri.gov.bd page: ব্রি উদ্ভাবিত নতুন ০৬টি জাত", "3_institute_page",
                "02_raw/brri/brri_gov_new_varieties_2026_page.html"),
    "BINAG": ("RB-S12", "BINA এক নজরে বিনা উদ্ভাবিত উন্নত জাত/প্রযুক্তি", "3_institute_page",
              "02_raw/bina/bina_at_a_glance_varieties.html"),
    "BINA7": ("RB-S13", "BINA per-variety page বিনাধান-৭", "3_institute_page", "02_raw/bina/bina_rice_variety_index.html"),
    "IAEA": ("P2B-IAEA58", "IAEA Bulletin 58-2 (2017) 60 Years: Contributing to Development", "6_secondary",
             "02_raw/iaea/iaea_bulletin_58-2_2017_60years_5821415.pdf"),
}
PILOT_ADC = {"BR1": "BR1", "BR11": "BR11", "BRRI dhan28": "BRRI_DHAN28", "BRRI dhan29": "BRRI_DHAN29",
             "BRRI dhan47": "BRRI_DHAN47", "BRRI dhan52": "BRRI_DHAN52", "BRRI dhan56": "BRRI_DHAN56",
             "BRRI dhan62": "BRRI_DHAN62", "BRRI dhan89": "BRRI_DHAN89", "BRRI hybrid dhan1": "BRRI_HYBRID1",
             "BRRI dhan71": "IRRI_DIRECT"}
# rows visually confirmed against renders (04_working/crops/P2B/adc_*.png)
ADC_VISUAL = {"BR1": "adc_p9_top.png", "BR11": "adc_p9_top.png", "BRRI dhan28": "adc_p9_bottom.png",
              "BRRI dhan29": "adc_p9_bottom.png", "BRRI dhan47": "adc_BRRI_dhan47.png", "BRRI dhan52": "adc_p10_mid.png",
              "BRRI dhan56": "adc_pilot_rows_b.png", "BRRI dhan62": "adc_pilot_rows_b.png",
              "BRRI dhan71": "adc_pilot_rows_b.png", "BRRI dhan89": "adc_pilot_rows_b.png",
              "BRRI hybrid dhan1": "adc_pilot_rows_b.png"}
# ---- other-source pedigrees to name in two_source notes
TRIV_NAME = {"BR 1": "BR1", "BR 11": "BR11", "BRRI dhan 28": "BRRI_DHAN28", "BRRI dhan 29": "BRRI_DHAN29",
             "BRRI dhan 47": "BRRI_DHAN47", "BRRI dhan 52": "BRRI_DHAN52", "BRRI hybrid dhan 1": "BRRI_HYBRID1",
             "Bina dhan 7": "BINADHAN7", "IR 8": "IR8", "BRRI dhan 51": "IRRI_DIRECT_ALT_dhan51"}
SPIA_NAME = {"BR1": "BR1", "BR11": "BR11", "BRRI dhan28": "BRRI_DHAN28", "BRRI dhan29": "BRRI_DHAN29",
             "BRRI dhan47": "BRRI_DHAN47", "BRRI dhan52": "BRRI_DHAN52", "BRRI dhan56": "BRRI_DHAN56",
             "BRRI dhan62": "BRRI_DHAN62", "BRRI dhan89": "BRRI_DHAN89", "BRRI hybrid 1": "BRRI_HYBRID1",
             "Binadhan-7": "BINADHAN7", "BRRI dhan71": "IRRI_DIRECT"}
norm = lambda s: re.sub(r"[\s\-]", "", str(s)).upper()

adc = {r["variety_en"]: r for r in csv.DictReader(open(T / "adc2025_table1.csv", encoding="utf-8"))}
spia = {r["variety"]: r for r in csv.DictReader(open(T / "spia2025_table27.csv", encoding="utf-8"))}
trv = pd.read_excel(ROOT / SRC["TRIVSA"][3], "Releases")
trv["xlsx_row"] = trv.index + 2
trv = trv[trv["Country where the variety is released"].astype(str).str.contains("Bangladesh")]
triv = {TRIV_NAME[r["Release Name"]]: r for _, r in trv.iterrows() if r["Release Name"] in TRIV_NAME}
spia_by_pk = {SPIA_NAME[k]: v for k, v in spia.items() if k in SPIA_NAME}

# ===================== ADC 2025 Table 1 =====================
CGIAR_ADC = {  # pilot_key: (code, rule note)
    "BR1": ("1", "breeding line is an IR code (IR532-1-176)"),
    "BR11": ("2", "pedigree IR20/IR5-47-2: both parents IR-designated; breeding line BR52-87-1-HR88 is a BRRI line"),
    "BRRI_DHAN28": ("2", "pedigree BR6 (IR28)/Purbachi: parent BR6 written as IR28 in the pedigree; ADC row BR6 breeding line IR2061-214-3-8-2"),
    "BRRI_DHAN29": ("4", "pedigree BG90-2/BR51-46-5: no IR-designated parent; IR element only at grandparent level (BR51-46-5 = IR20/IR5-114-3-1 per ADC rows BR4/BR10); flag ir_ancestor_grandparent"),
    "BRRI_DHAN47": ("1", "breeding line is an IR code (IR63307-4B-4-3)"),
    "BRRI_DHAN52": ("1", "breeding line is an IR code (IR85260-66-654-Gaz2)"),
    "BRRI_DHAN56": ("1", "breeding line is an IR code (IR74371-70-1-1)"),
    "BRRI_DHAN62": ("4", "pedigree Jirakatari/BRRI dhan39: no IR-designated parent in ADC; see HarvestPlus row for code 3"),
    "BRRI_DHAN89": ("2", "pedigree BRRI dhan29*3/Oryza rufipogon (IRGC acc. no. 103404): donor is an IRRI genebank (IRGC) accession = CGIAR-designated parent"),
    "BRRI_HYBRID1": ("1", "breeding line is an IR code (IR69690H); female parent IR58025A"),
    "IRRI_DIRECT": ("1", "breeding line is an IR code (IR82589-B-B-84-3); parents IR55423-01 (NSIC Rc 9)/IRRI148"),
}
for name, pk in PILOT_ADC.items():
    r = adc[name]
    pg = r["pdf_page"]
    vis = ADC_VISUAL.get(name)
    vnote = f"visual check: 04_working/crops/P2B/{vis}" if vis else ""
    val = "visual_check" if vis else "unvalidated"
    loc = f"Table 1 (সারণী ১), row {r['variety_bn']}"
    add(pk, "official_name_bn", r["variety_bn"], r["variety_bn"], "ADC", pg, loc, "bijoy2unicode", val, "high",
        f"bijoy ASCII: {r['bijoy_ascii_row'].split(' | ')[0]}; {vnote}")
    if r["popular_name_bn"]:
        add(pk, "popular_name", r["popular_name_bn"], r["popular_name_bn"], "ADC", pg, loc + " (bracketed name)",
            "bijoy2unicode", val, "high", vnote)
    add(pk, "station_no", r["station_no"], r["station_no_raw"], "ADC", pg, loc + ", col স্টেশন নম্বর",
        "bijoy2unicode", val, "high", "Latin form transliterated by token table in phase2_P2B_adc_parse.py; " + vnote)
    add(pk, "breeding_line", r["breeding_line_clean"], r["breeding_line_raw"], "ADC", pg, loc + ", col কৌলিক সারি",
        "bijoy2unicode", val, "high", "Latin form transliterated by token table; " + vnote)
    pnote = "Latin form transliterated by token table; " + vnote
    if name == "BRRI dhan47":
        pnote += "; text layer reads আইআর৫১৫১১১ (IR515111); SPIA T27 and TRIVSA give IR 51511-B-B-34-B: probable typo in ADC"
    add(pk, "pedigree", r["parentage_clean"], r["parentage_raw"], "ADC", pg, loc + ", col প্যারেন্টেজ",
        "bijoy2unicode", val, "high", pnote)
    add(pk, "approval_date", r["release_year"], r["release_year"] and r["bijoy_ascii_row"].split(" | ")[-1],
        "ADC", pg, loc + ", col অবমুক্তির বছর", "pdf_text", val, "medium",
        "institute-stated release year (অবমুক্তির বছর), not an NSB meeting date; " + vnote)
    add(pk, "developer", "BRRI", "ব্রি উদ্ভাবিত", "ADC", pg, "Table 1 title: ব্রি উদ্ভাবিত উফশী ধানের তালিকা ও বংশগতি ধারা",
        "bijoy2unicode", "unvalidated", "medium",
        "developer as claimed by the institute table; for IR-code lines the cross was made at IRRI (see cgiar_role)")
    add(pk, "type", "hybrid" if r["block"] == "hybrid" else "inbred",
        "হাইব্রিড ধানের জাত" if r["block"] == "hybrid" else "ইনব্রেড ধানের জাত", "ADC", pg,
        "Table 1 block header", "bijoy2unicode", "unvalidated", "high", "")
    code, why = CGIAR_ADC[pk]
    add(pk, "cgiar_role", code, r["breeding_line_raw"] + " || " + r["parentage_raw"], "ADC", pg, loc,
        "bijoy2unicode", val, "high" if code in ("1", "2") else "medium", "candidate per crawl_plan 3a: " + why)
    add(pk, "cgiar_evidence", f"ADC 2025 p.{pg} (printed {r['printed_page']}) Table 1 {name}: breeding line {r['breeding_line_clean']}; parentage {r['parentage_clean']}",
        r["breeding_line_raw"] + " || " + r["parentage_raw"], "ADC", pg, loc, "bijoy2unicode", val, "high", why)

# ---- ADC Table 2 (season, traits); text transcribed from the bijoy2unicode text layer
T2 = {"BR1": (13, "বোরো; আউশ", "চাল খাটো, মোটা"), "BR11": (13, "আমন", "চাল মাঝারি মোটা"),
      "BRRI_DHAN28": (14, "বোরো", "চাল মাঝারি চিকন ও সাদা"), "BRRI_DHAN29": (14, "বোরো", "চাল মাঝারি চিকন ও সাদা"),
      "BRRI_DHAN47": (14, "বোরো", "চাল মাঝারি মোটা, চারা অবস্থায় লবণাক্ততা সহনশীলতা (১২-১৪ ডিএস/মিটার) এবং সারা জীবনকাল ৬ ডিএস/মি"),
      "BRRI_DHAN52": (15, "রোপা আমন", "চাল মাঝারি মোটা, জলমগ্নতা সহনশীল"),
      "BRRI_DHAN56": (15, "রোপা আমন", "চাল লম্বা মোটা, সাদা, খরা সহিষ্ণু"),
      "BRRI_DHAN62": (15, "রোপা আমন", "চাল লম্বা, সরম্ন এবং সাদা, মধ্যম মাত্রার জিংক সমৃদ্ধ এবং আগাম জাত"),
      "BRRI_DHAN89": (16, "বোরো", "চাল মাঝারি মোটা ও সাদা"),
      "BRRI_HYBRID1": (17, "বোরো", "চাল মাঝারি চিকন, স্বচ্ছ ও সাদা"),
      "IRRI_DIRECT": (15, "রোপা আমন", "চাল লম্বা মোটা এবং রং সাদা")}
SEASON_EN = {"বোরো": "Boro", "আউশ": "Aus", "আমন": "Aman", "রোপা আমন": "T. Aman"}
TRAIT_EN = {"BRRI_DHAN47": "salt tolerant (seedling 12-14 dS/m; whole life 6 dS/m); medium bold grain",
            "BRRI_DHAN52": "submergence tolerant; medium bold grain", "BRRI_DHAN56": "drought tolerant; long bold white grain",
            "BRRI_DHAN62": "medium zinc-enriched; early; long slender white grain", "BR1": "short bold grain",
            "BR11": "medium bold grain", "BRRI_DHAN28": "medium slender white grain", "BRRI_DHAN29": "medium slender white grain",
            "BRRI_DHAN89": "medium bold white grain", "BRRI_HYBRID1": "medium slender, translucent white grain",
            "IRRI_DIRECT": "long bold white grain"}
for pk, (pg, sea, tr) in T2.items():
    add(pk, "season", "; ".join(SEASON_EN[s] for s in sea.split("; ")), sea, "ADC", pg,
        "Table 2 (সারণী ২), col মওসুম", "bijoy2unicode", "unvalidated", "high", "")
    add(pk, "key_traits", TRAIT_EN[pk], tr, "ADC", pg, "Table 2 (সারণী ২), col জাতের বৈশিষ্ট্য", "bijoy2unicode",
        "unvalidated", "high", "")
# ADC prose on IR8 (p.7, printed 5)
add("IR8", "approval_date", "1968", "১৯৬৮ সালে আন্তর্জাতিক ধান গবেষণা ইনস্টিটিউট (ইরি) থেকে প্রথম উফশী জাতের ধান (আইআর৮) মাঠ পর্যায়ে চাষাবাদ শুরু হয়",
    "ADC", 7, "ভূমিকা, para 2: '১৯৬৮ সালে ... (আইআর৮) মাঠ পর্যায়ে চাষাবাদ শুরু হয়'", "bijoy2unicode", "unvalidated", "medium",
    "year field cultivation began in Bangladesh, not a release/approval decision; pre-NSB (TRIVSA gives 1967)")
add("IR8", "cgiar_role", "1", "আন্তর্জাতিক ধান গবেষণা ইনস্টিটিউট (ইরি) থেকে ... (আইআর৮)", "ADC", 7, "ভূমিকা, para 2",
    "bijoy2unicode", "unvalidated", "high", "IRRI variety introduced as is; institute text states it came from IRRI")
add("IR8", "cgiar_evidence", "ADC 2025 p.7 (printed 5) introduction: IR8 introduced from IRRI (ইরি) in 1968",
    "(ইরি) থেকে প্রথম উফশী জাতের ধান (আইআর৮)", "ADC", 7, "ভূমিকা, para 2", "bijoy2unicode", "unvalidated", "high", "")

# ===================== SPIA T27 =====================
FL = ["irri_direct", "indirect_ir_parent", "inger_entry", "in_reference_library", "sub1", "saline_tolerance",
      "drought_tolerance", "harvestplus"]
for pk, r in spia_by_pk.items():
    pg = r["pdf_page"]; loc = f"Table 27 row {r['row_no']} '{r['variety']}'"
    flags = "; ".join(f"{f}={r[f]}" for f in FL)
    paren = (r["irri_inger_listed_released_directly"] + " || " + r["irri_inger_entry_used_as_parents"]).strip(" |")
    v = "spia_direct" if r["irri_direct"] == "Y" else "spia_indirect" if r["indirect_ir_parent"] == "Y" else \
        "spia_inger" if r["inger_entry"] == "Y" else "spia_none"
    sv = "visual_check" if int(r["row_no"]) in (1, 3, 16, 30, 34, 36, 44, 52, 53, 60, 74, 115, 138) else "unvalidated"
    add(pk, "cgiar_role", v, flags + " | IRRI/INGER listed released directly: " + r["irri_inger_listed_released_directly"]
        + " | IRRI/INGER entry used as parent(s): " + r["irri_inger_entry_used_as_parents"], "SPIA", pg, loc, "pdf_text",
        sv, "medium", "SPIA T27 flags: " + flags + f"; IRRI/INGER designation text: '{paren}'. SPIA definition (report p.46 printed): lower bound = IRRI parents or grandparents; not our 1-5 code; flag cgiar_spia_only unless pedigree agrees"
        + ("; crop 04_working/crops/P2B/spia_t27_check_[ab].png" if sv == "visual_check" else ""))
    add(pk, "approval_date", r["year"], r["year"], "SPIA", pg, loc + ", col Year released", "pdf_text", sv, "medium",
        "CGIAR-compiled release year (rank 4); not an NSB meeting date")
    add(pk, "official_name_en", r["variety"], r["variety"], "SPIA", pg, loc, "pdf_text", sv, "medium",
        "SPIA spelling (CGIAR record), not an institute English page")
    if r["irri_inger_entry_used_as_parents"] or r["irri_inger_listed_released_directly"]:
        add(pk, "cgiar_evidence", f"SPIA 2025 Table 27 p.{pg}: {paren}", paren, "SPIA", pg, loc, "pdf_text", sv, "medium",
            "IRRI/INGER designation as printed by SPIA")
    if r["sub1"] == "Y" or r["saline_tolerance"] == "Y" or r["drought_tolerance"] == "Y" or r["harvestplus"] == "Y":
        t = [n for f, n in (("sub1", "Sub1"), ("saline_tolerance", "saline tolerant"), ("drought_tolerance", "drought tolerant"),
                            ("harvestplus", "HarvestPlus")) if r[f] == "Y"]
        add(pk, "key_traits", "; ".join(t), flags, "SPIA", pg, loc, "pdf_text", sv, "medium", "")

# ===================== TRIVSA =====================
for pk, r in triv.items():
    if pk.endswith("dhan51"):
        continue
    loc = f"sheet Releases, row {r['xlsx_row']} (Ref ID {r['Ref ID']})"
    add(pk, "official_name_en", r["Release Name"], r["Release Name"], "TRIVSA", "", loc, "xlsx", "unvalidated", "medium", "")
    if pd.notna(r["Alternative Name"]):
        add(pk, "popular_name", r["Alternative Name"], r["Alternative Name"], "TRIVSA", "", loc + ", col Alternative Name",
            "xlsx", "unvalidated", "medium", "")
    if pd.notna(r["Original breeding line name "]):
        add(pk, "breeding_line", r["Original breeding line name "], r["Original breeding line name "], "TRIVSA", "",
            loc + ", col Original breeding line name", "xlsx", "unvalidated", "medium", "")
    if pd.notna(r["Parents"]):
        add(pk, "pedigree", r["Parents"], r["Parents"], "TRIVSA", "", loc + ", col Parents", "xlsx", "unvalidated", "medium",
            f"Method: {r['Method']}")
    add(pk, "approval_date", str(r["Year of Release"]), str(r["Year of Release"]), "TRIVSA", "", loc + ", col Year of Release",
        "xlsx", "unvalidated", "medium", "CGIAR-compiled year (rank 4)")
    add(pk, "developer", r["Institution that developed the variety"], r["Institution that developed the variety"], "TRIVSA", "",
        loc + ", col Institution that developed the variety", "xlsx", "unvalidated", "medium",
        f"Country of origin: {r['Country of origin ']}; Method: {r['Method']}")
    add(pk, "ecosystem", r["Recommended domain: Ecosystem"], r["Recommended domain: Ecosystem"], "TRIVSA", "",
        loc + ", col Recommended domain: Ecosystem", "xlsx", "unvalidated", "medium", "")
    add(pk, "season", r["Recommended domain: Season for cultivation"], r["Recommended domain: Season for cultivation"], "TRIVSA", "",
        loc + ", col Recommended domain: Season", "xlsx", "unvalidated", "medium", "")
    inst = str(r["Institution that developed the variety"])
    if str(r["Method"]).startswith("Introduction") or inst == "IRRI":
        add(pk, "cgiar_role", "1", f"Method={r['Method']}; Institution={inst}; Country of origin={r['Country of origin ']}",
            "TRIVSA", "", loc, "xlsx", "unvalidated", "medium",
            "TRIVSA records the variety as an IRRI introduction (IRRI-bred line released in Bangladesh)")
        add(pk, "cgiar_evidence", f"TRIVSA {loc}: Method '{r['Method']}', Institution '{inst}', origin '{r['Country of origin ']}'",
            f"{r['Method']} | {inst}", "TRIVSA", "", loc, "xlsx", "unvalidated", "medium", "")

# ===================== Rice Profile =====================
RP_PK = {7: "BR1", 23: "BR11", 1: "BRRI_DHAN28", 40: "BRRI_DHAN29", 58: "BRRI_DHAN47", 61: "BRRI_DHAN52",
         65: "BRRI_DHAN56", 71: "BRRI_DHAN62", 5: "BRRI_DHAN89", 80: "IRRI_DIRECT"}
rp = {int(r["rp_id"]): r for r in csv.DictReader(open(T / "brri_riceprofile.csv", encoding="utf-8"))}
YEAR_SENT = {  # exact approval/development sentence quoted from the intro (<25 words) and how it is phrased
    7: ("1970", "বাংলাদেশ ধান গবেষণা ইন্সটিটিউট ১৯৭০ সালে এ জাতটি উদ্ভাবন করেছে", "development year (উদ্ভাবন), not approval"),
    23: ("1980", "বাংলাদেশ ধান গবেষণা ইন্সটিটিউট ১৯৮০ সালে এ জাতটি উদ্ভাবন করেছে", "development year (উদ্ভাবন), not approval"),
    1: ("1994", "১৯৯৪ সালে এই জাতটি বীজ বোর্ড কর্তৃক চাষাবাদের জন্য অনুমোদিত হয়", "states Seed Board approval"),
    40: ("1994", "১৯৯৪ সালে বাণিজ্যিক ভিত্তিতে চাষাবাদের জন্য অনুমোদিত হয়", "approval; body not named"),
    58: ("2006", "জাতটি ২০০৬ সালে জাতীয় বীজ বোর্ড থেকে অনুমোদিত হয়", "states NSB approval; conflicts with ADC/SPIA/TRIVSA 2007"),
    61: ("2010", "এটিকে জাত হিসেবে ২০১০ সালে চুড়ান্তভাবে ছাড়করণ করা", "release (ছাড়করণ)"),
    65: ("2011", "বীজ বোর্ড জাতটিকে ২০১১ সালে অনুমোদন দেয়", "states Seed Board approval; 2009 and 2010 are trial years"),
    71: ("2013", "জাতটি ২০১৩ সালে জাতীয় বীজ বোর্ড কর্তৃক বোরো মৌসুমে জন্য অনুমোদন লাভ করে",
         "states NSB approval; says Boro season although every other source (incl. this page's own season field) gives Aman: probable error"),
    5: ("2018", "জাতীয় বীজ বোর্ড কর্তৃক ২০১৮ সালে ব্রি ধান ৮৯ জাত হিসেবে অনুমোদন পায়", "states NSB approval"),
    80: ("2014", "বীজ বোর্ড জাতটিকে ২০১৪ সালে কৃষক পর্যায়ে চাষাবাদের অনুমোদিত করে", "states Seed Board approval; conflicts with ADC/SPIA 2015"),
}
for rid, pk in RP_PK.items():
    r = rp[rid]; lf = r["local_file"]; url = r["source_url"]
    def addrp(field, value, raw, loc, conf="high", notes=""):
        add(pk, field, value, raw, "RP", "", loc, "html", "unvalidated", conf, notes)
        rows[-1]["local_file"] = lf
    addrp("official_name_bn", r["name_bn"], r["name_bn"], "<title>")
    addrp("source_url", url, url, "page URL")
    y, sent, how = YEAR_SENT[rid]
    addrp("approval_date", y, sent, "জাত পরিচিতি: " + sent, "medium", "institute-stated year; " + how)
    addrp("season", SEASON_EN.get(r["season"], r["season"]), r["season"], "field মৌসুম")
    addrp("ecosystem", r["land_type"], r["land_type"], "field জমির ধরন", "medium", "land type as stated (Bangla); suitable area: " + r["suitable_area"])
    addrp("key_traits", r["special"][:300], r["special"], "section বিশেষ প্রয়োজনীয়তা", "medium", "")
    if r["intro_codes"]:
        for code in r["intro_codes"].split(";"):
            if pk in ("BRRI_DHAN89", "BRRI_DHAN62", "IRRI_DIRECT") and code == r["intro_codes"].split(";")[0]:
                addrp("breeding_line", code, code, "জাত পরিচিতি: কৌলিক সারি", "high",
                      "matches ADC 2025 Table 1 breeding line" if True else "")
                rows[-1]["validation"] = "two_source"
                rows[-1]["notes"] = "matches ADC 2025 Table 1 breeding line (independent BRRI publication)"
# Rice Profile special statements
add("BR1", "popular_name", "চান্দিনা", "বিআর১ এর জনপ্রিয় নাম চান্দিনা", "RP", "", "জাত পরিচিতি", "html", "two_source", "high",
    "matches ADC 2025 Table 1 bracketed name and BR1 fact sheet")
rows[-1]["local_file"] = rp[7]["local_file"]
add("BR11", "popular_name", "মুক্তা", "বিআর ১১ বা মুক্তা বাংলাদেশের জনপ্রিয় জাগত", "RP", "", "জাত পরিচিতি", "html", "two_source", "high",
    "matches ADC 2025 Table 1 bracketed name and TRIVSA 'Mukta'")
rows[-1]["local_file"] = rp[23]["local_file"]
add("BR11", "local_name", "মুক্তা", "যা ‘মুক্তা’নামে পরিচিত", "RP", "", "বিশেষ প্রয়োজনীয়তা: 'যা ‘মুক্তা’নামে পরিচিত'", "html",
    "unvalidated", "medium", "page says farmers know BR11 as Mukta; also called a mega-variety (মেগা জাত)")
rows[-1]["local_file"] = rp[23]["local_file"]
add("BRRI_DHAN52", "cgiar_role", "3", "বাংলাদেশ ধান গবেষণা ইনষ্টিটিউট ও আর্ন্তজাতিক ধান গবেষণা ইনষ্টিটিউটের যৌথ সহযোগিতায় এই জাতটি উদ্ভাবন করে",
    "RP", "", "জাত পরিচিতি, sentence 1", "html", "unvalidated", "high",
    "institute states BRRI-IRRI joint development (code 3 evidence); ADC breeding line IR85260-66-654-Gaz2 supports code 1")
rows[-1]["local_file"] = rp[61]["local_file"]
add("BRRI_DHAN56", "cgiar_evidence", "Rice Profile: line derived by crossing IRRI's IR55419-4 with Way Rarem, two backcrosses, pedigree selection",
    "কৌলিক সারিটি আন্তর্জাতিক ধান গবেষণা ইনষ্টিটিউট এর IR55419-4 এবং WAY RAREM নামক স্থানীয় খরাসহিষ্ণু জাতের সাথে দুইবার পশ্চাৎ সংকরায়ণ",
    "RP", "", "জাত পরিচিতি, sentence 1", "html", "unvalidated", "high", "the page does not say where the cross was made")
rows[-1]["local_file"] = rp[65]["local_file"]
add("BRRI_DHAN62", "pedigree", "Jirakateri x BRRI dhan39 (cross, 2x RGA, pedigree selection)",
    "Jirakateri এবং BRRI dhan39 এর সঙ্করাণের পর দুইবার র‍্যাপিড জেনারেশন এ্যাডভান্স (RGA)", "RP", "", "জাত পরিচিতি", "html",
    "two_source", "high", "matches ADC 2025 Table 1 (জিরাকাটারি/ব্রি ধান৩৯); spelling Jirakateri vs Jirakatari")
rows[-1]["local_file"] = rp[71]["local_file"]
add("BRRI_DHAN89", "pedigree", "", "", "RP", "", "জাত পরিচিতি", "html", "unvalidated", "low", "page gives breeding line only, no cross")
rows.pop()  # do not write empty values
add("IRRI_DIRECT", "official_name_bn", rp[80]["name_bn"], rp[80]["name_bn"], "RP", "", "<title>", "html", "unvalidated", "high", "")
rows.pop()  # already added above
add("IRRI_DIRECT", "pedigree", "IR55423-01 (NSIC Rc 9) x IRRI148, pedigree selection at IRRI Philippines",
    "আন্তর্জাতিক ধান গবেষনা ইনস্টিটিউট ফিলিপাইনে IR5542301 ( NSIC RC 9) এবং IRRI148 এর সাথে সংকরায়ন করে", "RP", "",
    "জাত পরিচিতি, sentence 2", "html", "two_source", "high", "matches ADC 2025 Table 1 parentage; RP writes IR5542301 without hyphen")
rows[-1]["local_file"] = rp[80]["local_file"]
add("IRRI_DIRECT", "cgiar_role", "1", "উক্ত কৌলিক সারিটি আন্তর্জাতিক ধান গবেষনা ইনস্টিটিউট ফিলিপাইনে ... সংকরায়ন করে বংশানুক্রম নির্বাচনের ... মাধ্যমে উদ্ভাবিত",
    "RP", "", "জাত পরিচিতি, sentence 2", "html", "two_source", "high",
    "institute states the line was bred at IRRI Philippines; agrees with ADC breeding line IR82589-B-B-84-3 and SPIA T27 irri_direct=Y. Variety = BRRI dhan71")
rows[-1]["local_file"] = rp[80]["local_file"]
add("IRRI_DIRECT", "cgiar_center", "IRRI", "আন্তর্জাতিক ধান গবেষনা ইনস্টিটিউট ফিলিপাইনে", "RP", "", "জাত পরিচিতি, sentence 2", "html",
    "two_source", "high", "BRRI dhan71; IR-prefix breeding line in ADC 2025")
rows[-1]["local_file"] = rp[80]["local_file"]
for pk in ("BR1", "BRRI_DHAN47", "BRRI_DHAN52", "BRRI_DHAN56", "BRRI_HYBRID1"):
    add(pk, "cgiar_center", "IRRI", adc[[k for k, v in PILOT_ADC.items() if v == pk][0]]["breeding_line_raw"], "ADC", "",
        "Table 1 breeding line (IR prefix)", "bijoy2unicode", "visual_check", "high", "IR-prefixed breeding line = IRRI designation")

# ===================== HarvestPlus =====================
for r in csv.DictReader(open(T / "harvestplus_bd.csv", encoding="utf-8")):
    if r["variety_name"].strip() == "BRRI Dhan62":
        loc = f"result.data[{r['json_index']}] id_variety {r['id_variety']}"
        add("BRRI_DHAN62", "official_name_en", "BRRI Dhan62", r["variety_name"], "HP", "", loc, "api_json", "unvalidated", "medium", "")
        add("BRRI_DHAN62", "approval_date", r["realease_year"], r["realease_year"], "HP", "", loc + " realease_year", "api_json",
            "two_source", "medium", "matches ADC 2025 Table 1 (2013); CGIAR-programme year")
        add("BRRI_DHAN62", "cgiar_role", "3", f"funded_by={r['funded_by']}; breeder_organization={r['breeder_organization']}; display_name={r['display_name']}",
            "HP", "", loc, "api_json", "unvalidated", "high",
            "HarvestPlus BCR lists it as a released Zinc Rice funded by HarvestPlus (code 3: funding/co-development documented); pedigree field NA")
        add("BRRI_DHAN62", "cgiar_center", "HarvestPlus (CGIAR)", r["funded_by"], "HP", "", loc + " funded_by", "api_json", "unvalidated", "high", "")
        add("BRRI_DHAN62", "cgiar_evidence", f"HarvestPlus BCR {loc}: Zinc Rice, funded_by HarvestPlus, release {r['realease_year']}",
            r["funded_by"], "HP", "", loc, "api_json", "unvalidated", "high", "")
        add("BRRI_DHAN62", "key_traits", f"zinc biofortified ({r['nutrition_content']} ppm Zn)", r["nutrition_content"], "HP", "",
            loc + " nutrition_content", "api_json", "unvalidated", "medium", "")

# ===================== fact sheets =====================
add("BRRI_DHAN118", "official_name_en", "BRRI dhan118", "BRRI dhan118", "BRRINEW", "", "table row 4, link text", "html", "unvalidated", "high", "")
add("BRRI_DHAN118", "official_name_bn", "ব্রি ধান১১৮", "ব্রি উদ্ভাবিত নতুন ধানের জাত ব্রি ধান১১৮", "BRRINEW", "", "table row 4", "html", "unvalidated", "high", "")
f = "factsheet_dhan118_intro.png"
add("BRRI_DHAN118", "breeding_line", "BR11894-R-R-R-R-169", "BR11894-R-R-R-R-169", "FS118", 1, "জাত পরিচিতি: 'জাতটির কৌলিক সারির নাম BR11894-R-R-R-R-169'",
    "ocr", "visual_check", "high", "crop 04_working/crops/P2B/" + f)
add("BRRI_DHAN118", "pedigree", "BRRI dhan28 x Bhutan (ভুটান, Bhutanese cold-tolerant rice); crossed 2014; SSD-based RGA, forward breeding",
    "২০১৪ সালে ব্রি ধান২৮ এর সাথে ভুটান নামক ভুটানি ঠান্ডা সহিষ্ণু ধানের সংকরায়ণের পর", "FS118", 1, "জাত পরিচিতি, sentence 3", "ocr",
    "visual_check", "high", "crop 04_working/crops/P2B/" + f)
add("BRRI_DHAN118", "approval_date", "2026-02-05", "৫ ফেব্রুয়ারী ২০২৬ তারিখে জাতীয় বীজ বোর্ডের ১১৫ তম সভায়", "FS118", 1,
    "জাত পরিচিতি, last sentence", "ocr", "key_check", "high",
    "NSB 115 = 05.02.2026 matches the meeting-to-date key in approval_systems_memo A2; also confirmed by eye (" + f + ")")
add("BRRI_DHAN118", "approval_reference", "NSB 115th meeting", "জাতীয় বীজ বোর্ডের ১১৫ তম সভায়", "FS118", 1, "জাত পরিচিতি, last sentence",
    "ocr", "key_check", "high", "")
add("BRRI_DHAN118", "approving_body", "NSB", "জাতীয় বীজ বোর্ড", "FS118", 1, "জাত পরিচিতি, last sentence", "ocr", "visual_check", "high", "")
add("BRRI_DHAN118", "release_category", "NSB_release", "অবমুক্ত করা হয়", "FS118", 1, "জাত পরিচিতি, last sentence", "ocr", "visual_check", "medium",
    "institute fact sheet; confirm in NSB 115 minutes")
add("BRRI_DHAN118", "season", "Boro", "বোরো মওসুমে", "FS118", 1, "জাত পরিচিতি, last sentence", "ocr", "visual_check", "high", "")
add("BRRI_DHAN118", "region_scope", "haor areas", "হাওড় অঞ্চলে চাষাবাদের জন্য অবমুক্ত", "FS118", 1, "জাত পরিচিতি, last sentence", "ocr",
    "visual_check", "high", "released for haor region (Kishoreganj, Habiganj, Netrokona, Sunamganj trial sites)")
add("BRRI_DHAN118", "ecosystem", "haor (Boro, irrigated)", "হাওর অঞ্চলের উপযোগী", "FS118", 1, "জাত পরিচিতি, sentence 1", "ocr", "visual_check", "medium", "")
add("BRRI_DHAN118", "key_traits", "cold tolerant at reproductive stage; haor-adapted; medium bold grain",
    "হাওর অঞ্চলের উপযোগী প্রজনন পর্যায়ে ঠান্ডা সহনশীল বোরো ধানের একটি জাত", "FS118", 1, "জাত পরিচিতি, sentence 1", "ocr", "visual_check", "high", "")
add("BRRI_DHAN118", "developer", "BRRI", "বাংলাদেশ ধান গবেষণা ইনস্টিটিউট (ব্রি) কর্তৃক", "FS118", 1, "জাত পরিচিতি, sentence 3", "ocr", "visual_check", "high", "")
add("BRRI_DHAN118", "type", "inbred", "", "FS118", 1, "derived: SSD/RGA forward breeding of a single cross", "ocr", "unvalidated", "medium", "")
rows[-1]["value_raw"] = "সিঙ্গেল সিড ডিসেন্ট ভিত্তিক র্যাপিড জেনারেশন এডভান্সমেন্ট"
add("BRRI_DHAN118", "cgiar_role", "4", "২০১৪ সালে ব্রি ধান২৮ এর সাথে ভুটান নামক ভুটানি ঠান্ডা সহিষ্ণু ধানের সংকরায়ণের পর", "FS118", 1,
    "জাত পরিচিতি, sentence 3", "ocr", "visual_check", "medium",
    "pedigree known; no IR/CGIAR-designated parent. IR element only at grandparent level (BRRI dhan28 = BR6 (IR28)/Purbachi per ADC); flag ir_ancestor_grandparent")
add("BRRI_DHAN118", "cgiar_evidence", "Fact sheet BRRI dhan118 p.1: BRRI dhan28 x Bhutan (BRRI cross, 2014); BR11894 line", "BR11894-R-R-R-R-169",
    "FS118", 1, "জাত পরিচিতি", "ocr", "visual_check", "medium", "")
add("BR1", "popular_name", "চান্দিনা", "বিআর১ এর জনপ্রিয় নাম চান্দিনা", "FSBR1", 1, "জাত পরিচিতি, sentence 3", "ocr", "visual_check", "high",
    "crop 04_working/crops/P2B/factsheet_BR1_intro.png")
add("BR1", "approval_date", "1970", "বাংলাদেশ ধান গবেষণা ইনস্টিটিউট ১৯৭০ সালে এ জাতটি উদ্ভাবন করেছে", "FSBR1", 1, "জাত পরিচিতি, sentence 2", "ocr",
    "visual_check", "medium", "development year (উদ্ভাবন), not approval; crop factsheet_BR1_intro.png")
add("BR1", "season", "Boro; Aus", "বোরো ও আউশ মৌসুমের একটি জাত", "FSBR1", 1, "জাত পরিচিতি, sentence 1", "ocr", "visual_check", "high", "")
f = "factsheet_hybrid1_intro.png"
add("BRRI_HYBRID1", "approval_date", "2001", "২০০১ সালে জাতীয় বীজ বোর্ড কর্তৃক অনুমোদন লাভ করে", "FSH1", 1, "জাত পরিচিতি", "ocr", "visual_check", "high",
    "OCR garbled; read by eye from crop " + f + "; agrees with ADC 2025, SPIA, TRIVSA (2001)")
add("BRRI_HYBRID1", "approving_body", "NSB", "জাতীয় বীজ বোর্ড কর্তৃক অনুমোদন", "FSH1", 1, "জাত পরিচিতি", "ocr", "visual_check", "high", "")
add("BRRI_HYBRID1", "region_scope", "Barishal and Jashore regions", "বরিশাল ও যশোহর অঞ্চলে চাষাবাদের জন্য", "FSH1", 1, "জাত পরিচিতি", "ocr",
    "visual_check", "high", "regional approval")
add("BRRI_HYBRID1", "developer", "BRRI", "বাংলাদেশ ধান গবেষণা ইনস্টিটিউট উদ্ভাবিত", "FSH1", 1, "জাত পরিচিতি", "ocr", "visual_check", "medium",
    "institute claim; ADC/TRIVSA breeding line IR69690H and TRIVSA 'Introduction, IRRI' indicate an IRRI hybrid combination")

# ===================== BINA =====================
add("BINADHAN7", "official_name_bn", "বিনাধান-৭", "বিনাধান-৭", "BINAG", "", "table row ধান / বিনাধান-৭ (first occurrence)", "html", "unvalidated", "high", "")
add("BINADHAN7", "approval_date", "2007", "২০০৭", "BINAG", "", "row বিনাধান-৭, col অনুমোদনের বছর", "html", "unvalidated", "medium",
    "institute-stated approval year. NB a second row 'বিনাধান-৭ | ২০১৫' on the same page is a typo for বিনাধান-১৭ (traits differ)")
add("BINADHAN7", "season", "Aman", "আমন", "BINAG", "", "row বিনাধান-৭, col চাষাবাদের মৌসুম", "html", "unvalidated", "high", "")
add("BINADHAN7", "key_traits", "early maturing, short plant, long slender grain", "আগাম পাকে, গাছ খাটো, চাল চিকন ও সরু ।", "BINAG", "",
    "row বিনাধান-৭, col বিশেষ বৈশিষ্ট্য", "html", "unvalidated", "high", "duration 115-120 days")
add("BINADHAN7", "developer", "BINA", "বিনা উদ্ভাবিত", "BINAG", "", "page title", "html", "unvalidated", "high", "")
add("BINADHAN7", "ecosystem", "T. Aman (transplanted)", "উচ্চ ফলনশীল ও উন্নত গুণাগুণ সম্পন্ন রোপা আমন জাত।", "BINA7", "", "জাতের বৈশিষ্ট্যঃ line 1",
    "html", "unvalidated", "high", "")
add("BINADHAN7", "type", "inbred (mutant)", "plant mutation breeding", "IAEA", 1, "'developed through a process which uses radiation, called plant mutation breeding'",
    "pdf_text", "unvalidated", "medium", "IAEA Bulletin narrative")
add("BINADHAN7", "approval_date", "2007", "Since its release in 2007", "IAEA", 2, "'Since its release in 2007, Binadhan-7 has helped...'", "pdf_text",
    "two_source", "medium", "matches BINA at-a-glance 2007; secondary source")
add("BINADHAN7", "developer", "BINA (with IAEA/FAO support)", "developed by scientists at the Bangladesh Institute of Nuclear Agriculture (BINA), with the support of the IAEA and the Food and Agriculture Organization",
    "IAEA", 1, "para on Binadhan-7", "pdf_text", "unvalidated", "medium", "")
add("BINADHAN7", "cgiar_role", "4", "Mutant of Tainguyen", "TRIVSA", "", "sheet Releases row 65 (Ref ID 63), col Parents", "xlsx", "unvalidated", "medium",
    "pedigree known (mutant of Vietnamese cultivar Tainguyen, per TRIVSA); no IRRI/CGIAR element found in P2B sources; SPIA T27 also irri_direct=N, indirect=N, inger=N")
rows[-1]["local_file"] = SRC["TRIVSA"][3]

# ===================== write =====================
out = ROOT / "04_working/evidence_P2B.csv"
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=HDR); w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), "rows"); print(Counter(r["pilot_key"] for r in rows))
for r in rows:
    if not r["local_file"]:
        print("MISSING local_file", r["pilot_key"], r["field"], r["source_id"])

# ---- post-pass: two_source where a non-ADC value equals the ADC value for the same pilot and field
def nz(s):
    return re.sub(r"[\s\-]", "", str(s)).upper().replace("DHAN", "DHAN")
adcv = {(r["pilot_key"], r["field"]): r["value"] for r in rows if r["source_id"] == "RB-S01"}
for r in rows:
    if r["source_id"] != "RB-S01" and r["field"] in ("breeding_line", "pedigree", "approval_date", "popular_name") \
            and r["validation"] == "unvalidated":
        a = adcv.get((r["pilot_key"], r["field"]))
        if a and nz(a) == nz(r["value"]):
            r["validation"] = "two_source"
            r["notes"] = (r["notes"] + "; " if r["notes"] else "") + "matches ADC 2025 Table 1 (independent BRRI source)"
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=HDR); w.writeheader(); w.writerows(rows)
print(Counter(r["validation"] for r in rows))
