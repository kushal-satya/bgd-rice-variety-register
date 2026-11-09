"""F3I: institute and CGIAR sources, all rice varieties -> 04_working/evidence_F3I.csv (long format, Phase 2 columns).

Inputs (all local, already in 02_raw / 03_extracted):
  ADC 2025 Table 1 + Table 2, BRRI Rice Profile (99 pages), SPIA 2025 T27, TRIVSA (xlsx), HarvestPlus BCR,
  BRRI site season lists + 2026 new-variety page, BRRI fact sheets dhan109-118 / hybrid 9-10 (OCR, visually checked,
  transcriptions in phase3_F3I_factsheet_data.py), BINA at-a-glance table + per-variety pages, IAEA MVD (Bangladesh),
  GAU dhan3 paper (Banglajol ABA 84826), GAU research-achievement PDF, ACI page (BAU dhan3).
CGIAR lineage is computed in phase3_F3I_lineage.py from documented pedigrees only (see decisions_F3I.md).
Re-runnable; no network access."""
import csv, pathlib, re, sys, json, unicodedata
from collections import Counter, defaultdict
import pandas as pd
from bs4 import BeautifulSoup
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_keys import make_key

ROOT = pathlib.Path(__file__).resolve().parents[1]
T = ROOT / "03_extracted/tables"
HDR = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file",
       "page", "locator", "method", "validation", "confidence", "notes"]
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
NFC = lambda s: unicodedata.normalize("NFC", s or "")
rows = []

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
    "BRRILIST": ("RB-S08", "brri.gov.bd variety list pages (aus/aman/boro/hybrid; index 'সর্বমোট ১২৭')", "3_institute_page", None),
    "BRRINEW": ("RB-S08", "brri.gov.bd page: ব্রি উদ্ভাবিত নতুন বোরো ধানের জাতসমূহ (2026)", "3_institute_page",
                "02_raw/brri/brri_gov_new_varieties_2026_page.html"),
    "FS": ("RB-S04", "BRRI variety fact sheet (brri.gov.bd)", "3_institute_page", None),
    "BINAG": ("RB-S12", "BINA এক নজরে বিনা উদ্ভাবিত উন্নত জাত/প্রযুক্তি", "3_institute_page",
              "02_raw/bina/bina_at_a_glance_varieties.html"),
    "BINAV": ("RB-S13", "BINA per-variety page (bina.gov.bd)", "3_institute_page", None),
    "MVD": ("RB-S22", "IAEA/FAO Mutant Variety Database (nucleus.iaea.org/sites/mvd), list MutantVariety, Bangladesh", "6_secondary",
            "02_raw/iaea/mvd_MutantVariety_BGD.xml"),
    "ABA": ("F3I-ABA84826", "Ali et al. 2026, Ann. Bangladesh Agric. 29(2):125-140 (GAU dhan3)", "5_peer_reviewed",
            "02_raw/literature/banglajol_ABA_84826_gau_aromatic_biofortified.html"),
    "GAU": ("RB-S19", "GAU (ex-BSMRAU) Research achievement (short), Nov 2025", "3_institute_page",
            "02_raw/gau/gau_research_achievement_short_2025-11.pdf"),
    "ACI": ("F3I-ACI", "ACI news page 'PPP Breeding Is The Future For Rice' (BAU dhan3)", "6_secondary",
            "02_raw/news/aci_ppp_breeding_future_rice_bau_dhan3.html"),
}


def add(pk, field, value, raw, src, page="", loc="", method="pdf_text", val="unvalidated", conf="high", notes="", lf=None):
    s = SRC[src]
    if value is None or str(value).strip() in ("", "nan", "NA", "-"):
        return
    rows.append({"pilot_key": pk, "field": field, "value": str(value).strip(), "value_raw": str(raw).strip(),
                 "source_id": s[0], "source_title": s[1], "authority_rank": s[2], "local_file": lf or s[3],
                 "page": page, "locator": loc, "method": method, "validation": val, "confidence": conf, "notes": notes})


SEASON_EN = {"বোরো": "Boro", "আউশ": "Aus", "আমন": "Aman", "রোপা আমন": "T. Aman", "বোনা আমন": "B. Aman",
             "রোপা আউশ": "T. Aus", "বোনা আউশ": "B. Aus", "নাবী বোরো": "late Boro", "বোরো/আউশ": "Boro; Aus"}
TRAIT_TAGS = [(r"লবণ|লবন", "salt tolerant"), (r"খরা", "drought tolerant"), (r"জলমগ্ন", "submergence tolerant"),
              (r"জলাবদ্ধ", "stagnant-flood tolerant"), (r"সুগন্ধ", "aromatic"), (r"জিংক|জিঙ্ক", "zinc enriched"),
              (r"ঠান্ডা", "cold tolerant"), (r"বাদামি গাছ ফড়িং", "BPH resistant"), (r"পোড়া রোগ|BLB|Xa", "BLB resistant"),
              (r"জিআই|গস্নাইসেমিক|গ্লাইসেমিক", "low GI"), (r"হাওর|হাওড়", "haor-adapted"), (r"জোয়ার", "tidal areas"),
              (r"আগাম|স্বল্প জীবনকাল|স্বল্পমেয়াদ|স্বল্প মেয়াদ", "early/short duration"), (r"নাবি|নাবী", "late-planting"),
              (r"প্রোটিন", "protein content stated"), (r"শিলাবৃষ্টি", "hail-prone areas"), (r"ব্লাস্ট", "blast resistant"),
              (r"আলোক অসংবেদনশীল|আলোকঅসংবেদনশীল", "photoperiod insensitive"), (r"রপ্তানি", "export quality"),
              (r"প্রিমিয়াম", "premium quality"), (r"লালচে|লাল", "red pericarp")]


def tags(t):
    out = [en for pat, en in TRAIT_TAGS if re.search(pat, t or "")]
    return "; ".join(dict.fromkeys(out))


def words25(s):
    w = str(s).split()
    return " ".join(w[:24]) + (" ..." if len(w) > 24 else "")


# ============================================================ ADC 2025 Table 1
POP_FIX = {"বিপস্নব": ("বিপ্লব", "bijoy2unicode misplaced the conjunct (বিপস্নব); Rice Profile id 14 spells বিপ্লব"),
           "বির্রশাইল": ("ব্রিশাইল", "bijoy2unicode misplaced the reph (বির্রশাইল); Rice Profile id 15 spells ব্রিশাইল")}
ADC_VISUAL = {"BR1": "adc_p9_top.png", "BR11": "adc_p9_top.png", "BRRI dhan28": "adc_p9_bottom.png",
              "BRRI dhan29": "adc_p9_bottom.png", "BRRI dhan47": "adc_BRRI_dhan47.png", "BRRI dhan52": "adc_p10_mid.png",
              "BRRI dhan56": "adc_pilot_rows_b.png", "BRRI dhan62": "adc_pilot_rows_b.png",
              "BRRI dhan71": "adc_pilot_rows_b.png", "BRRI dhan89": "adc_pilot_rows_b.png",
              "BRRI hybrid dhan1": "adc_pilot_rows_b.png"}
adc_rows = list(csv.DictReader(open(T / "adc2025_table1.csv", encoding="utf-8")))
ADC = {}
for r in adc_rows:
    pk = make_key(r["variety_bn"])
    ADC[pk] = r
    pg = r["pdf_page"]
    vis = ADC_VISUAL.get(r["variety_en"])
    # F3I visual batch check of every ADC page (crops 04_working/crops/F3I/adc_t1_p*.png) -> see notes_F3I.md
    vcrop = f"04_working/crops/F3I/adc_t1_p{pg}_a.png + _b.png"
    val = "visual_check" if vis or (ROOT / f"04_working/crops/F3I/adc_t1_p{pg}_a.png").exists() else "unvalidated"
    vnote = f"visual check: 04_working/crops/P2B/{vis}" if vis else (f"visual check (page render): {vcrop}" if val == "visual_check" else "")
    loc = f"Table 1 (সারণী ১), row {r['variety_bn']}"
    add(pk, "official_name_bn", r["variety_bn"], r["variety_bn"], "ADC", pg, loc, "bijoy2unicode", val, "high",
        f"bijoy ASCII: {r['bijoy_ascii_row'].split(' | ')[0]}; {vnote}")
    if r["popular_name_bn"]:
        v, why = POP_FIX.get(r["popular_name_bn"], (r["popular_name_bn"], ""))
        add(pk, "popular_name", v, r["popular_name_bn"], "ADC", pg, loc + " (bracketed name)", "bijoy2unicode", val, "high",
            "; ".join(x for x in (why, vnote) if x))
    add(pk, "station_no", r["station_no"], r["station_no_raw"], "ADC", pg, loc + ", col স্টেশন নম্বর", "bijoy2unicode", val,
        "high", "Latin form transliterated by token table (phase2_P2B_adc_parse.py); " + vnote)
    add(pk, "breeding_line", r["breeding_line_clean"], r["breeding_line_raw"], "ADC", pg, loc + ", col কৌলিক সারি",
        "bijoy2unicode", val, "high", "Latin form transliterated by token table; " + vnote)
    pn = "Latin form transliterated by token table; " + vnote
    if pk == "BRRI_DHAN47":
        pn += "; text layer reads আইআর৫১৫১১১ (IR515111); SPIA T27 and TRIVSA give IR 51511-B-B-34-B: probable typo in ADC"
    add(pk, "pedigree", r["parentage_clean"], r["parentage_raw"], "ADC", pg, loc + ", col প্যারেন্টেজ", "bijoy2unicode",
        val, "high", pn)
    add(pk, "approval_date", r["release_year"], r["bijoy_ascii_row"].split(" | ")[-1], "ADC", pg, loc + ", col অবমুক্তির বছর",
        "pdf_text", val, "medium", "institute-stated release year (অবমুক্তির বছর, rank 3), not an NSB meeting date; " + vnote)
    add(pk, "developer", "BRRI", "ব্রি উদ্ভাবিত", "ADC", pg, "Table 1 title: ব্রি উদ্ভাবিত উফশী ধানের তালিকা ও বংশগতি ধারা",
        "bijoy2unicode", "unvalidated", "medium", "developer as claimed by the institute table")
    add(pk, "type", "hybrid" if r["block"] == "hybrid" else "inbred",
        "হাইব্রিড ধানের জাত" if r["block"] == "hybrid" else "ইনব্রেড ধানের জাত", "ADC", pg, "Table 1 block header",
        "bijoy2unicode", "unvalidated", "high", "")

# ============================================================ ADC 2025 Table 2
for r in csv.DictReader(open(T / "adc2025_table2.csv", encoding="utf-8")):
    pk = r["key"]; pg = r["pdf_page"]; loc = f"Table 2 (সারণী ২), row {r['variety_bn']}"
    if r["season_bn"]:
        add(pk, "season", "; ".join(SEASON_EN.get(s.strip(), s.strip()) for s in r["season_bn"].split(";")), r["season_bn"],
            "ADC", pg, loc + ", col মওসুম", "bijoy2unicode", "unvalidated", "high", "parsed by x-band (phase3_F3I_adc_table2.py)")
    if r["traits_bn"]:
        tg = tags(r["traits_bn"])
        add(pk, "key_traits", tg or r["traits_bn"], r["traits_bn"], "ADC", pg, loc + ", col জাতের বৈশিষ্ট্য", "bijoy2unicode",
            "unvalidated", "medium", ("English tags derived by keyword from the Bangla text; " if tg else "")
            + f"height {r['height_cm']} cm; duration {r['duration_days']} d; yield {r['yield_t_ha']} t/ha (as parsed)")

# ADC prose on IR8 (p.7)
add("IR8", "approval_date", "1968", "১৯৬৮ সালে আন্তর্জাতিক ধান গবেষণা ইনস্টিটিউট (ইরি) থেকে প্রথম উফশী জাতের ধান (আইআর৮) মাঠ পর্যায়ে চাষাবাদ শুরু হয়",
    "ADC", 7, "ভূমিকা, para 2", "bijoy2unicode", "unvalidated", "medium",
    "year field cultivation began, not an approval; pre-NSB (TRIVSA gives 1967)")

# ============================================================ BRRI site lists (127)
from phase3_F3I_fetch_brri import links  # parses the saved list pages only (no network)
BRRI_SITE = defaultdict(set)
LISTFILE = {"aus": "brri_gov_variety_list_aus.html", "aman": "brri_gov_variety_list_aman.html",
            "boro": "brri_gov_variety_list_boro.html", "hybrid": "brri_gov_variety_list_hybrid.html",
            "new2026": "brri_gov_new_varieties_2026_page.html"}
for f, sea in (("brri_gov_variety_list_aman.html", "aman"),):  # BR4, BR5 rows link 'not_found.jpg' (no fact sheet)
    s = BeautifulSoup((ROOT / "02_raw/brri" / f).read_text(encoding="utf-8"), "html.parser")
    for t in s.find_all("table"):
        for tr in t.find_all("tr"):
            c = [x.get_text(" ", strip=True) for x in tr.find_all("td")]
            if c and make_key(c[0]) in ("BR4", "BR5"):
                BRRI_SITE[make_key(c[0])].add(("aman", c[0]))
for sea, name, pk, url in links():
    BRRI_SITE[pk].add((sea, name))
SEAS = {"aus": "Aus", "aman": "Aman", "boro": "Boro"}
for pk, ss in BRRI_SITE.items():
    for sea, name in sorted(ss):
        lf = "02_raw/brri/" + LISTFILE[sea]
        if sea in SEAS:
            add(pk, "season", SEAS[sea], f"{name} (listed under {sea} page)", "BRRILIST", "", f"{sea} list page, row '{name}'",
                "html", "unvalidated", "medium", "season = the brri.gov.bd season list the variety appears on", lf=lf)
    nm = sorted(ss)[0][1]
    nm = re.sub(r"(?<=[০-৯])\s+(?=[০-৯])", "", nm)
    add(pk, "official_name_bn", nm, sorted(ss)[0][1], "BRRILIST", "", f"variety list row '{sorted(ss)[0][1]}'", "html",
        "unvalidated", "high", "brri.gov.bd index states total 127 (সর্বমোট ১২৭)", lf="02_raw/brri/" + LISTFILE[sorted(ss)[0][0]])
s = BeautifulSoup((ROOT / "02_raw/brri/brri_gov_new_varieties_2026_page.html").read_text(encoding="utf-8"), "html.parser")
for tr in s.find_all("tr"):
    c = [x.get_text(" ", strip=True) for x in tr.find_all("td")]
    if len(c) >= 3 and make_key(c[2]):
        add(make_key(c[2]), "official_name_en", c[2], c[2], "BRRINEW", "", f"table row {c[0]} col বিস্তারিত (link text)", "html",
            "unvalidated", "high", "English name printed by the institute")

# ============================================================ Rice Profile
rp = list(csv.DictReader(open(T / "brri_riceprofile.csv", encoding="utf-8")))
RP = {}
for r in rp:
    nm = NFC(r["name_bn"]).replace("বি আর", "বিআর")
    base = re.sub(r"\(.*?\)", "", nm).strip()
    pk = make_key(base)
    if not pk:
        print("RP unmatched", r["rp_id"], r["name_bn"]); continue
    RP[pk] = r
    lf, url = r["local_file"], r["source_url"]

    def a(field, value, raw, loc, conf="high", notes="", val="unvalidated"):
        add(pk, field, value, raw, "RP", "", loc, "html", val, conf, notes, lf=lf)
    a("official_name_bn", base, r["name_bn"], "<title>")
    a("source_url", url, url, "page URL")
    m = re.search(r"\((.+?)\)", nm)
    if m:
        a("aliases", m.group(1), r["name_bn"], "<title> bracketed name", "high", "renamed/alternative name printed in the institute title")
    a("season", SEASON_EN.get(r["season"], r["season"]), r["season"], "field মৌসুম")
    a("ecosystem", r["land_type"], r["land_type"], "field জমির ধরন", "medium", "land type as stated (Bangla); suitable area: " + r["suitable_area"][:200])
    if r["special"]:
        tg = tags(r["special"])
        a("key_traits", tg or words25(r["special"]), r["special"][:600], "section বিশেষ প্রয়োজনীয়তা", "medium",
          "English tags derived by keyword" if tg else "")
    intro = NFC(r["intro"])
    sents = [x.strip() for x in re.split(r"[।]", intro) if x.strip()]
    for snt in sents:
        ys = re.findall(r"(?<![০-৯\d])([১২][৯০][০-৯]{2})(?![০-৯\d])", snt)
        if not ys:
            continue
        if re.search(r"অনুমোদ|অনুমদন|অনোমদ|ছাড়করণ|ছাড়", snt):
            how = "approval/release sentence"; conf = "medium"
            if re.search(r"বীজ বোর্ড", snt):
                how += " (names the Seed Board)"
        elif re.search(r"উদ্ভাবন|উদ্ভবিত", snt) and not re.search(r"সংকর|সঙ্কর", snt):
            how = "DEVELOPMENT year (উদ্ভাবন), not an approval"; conf = "low"
        else:
            continue
        y = ys[-1].translate(BN)
        a("approval_date", y, snt, "জাত পরিচিতি: '" + words25(snt) + "'", conf,
          "institute-stated year (rank 3); " + how + (f"; other years in sentence: {[x.translate(BN) for x in ys]}" if len(ys) > 1 else ""))
    mp = re.search(r"জনপ্রি\S* নাম\s*([^।,]+)", intro)
    if mp:
        a("popular_name", mp.group(1).strip(), mp.group(0), "জাত পরিচিতি: '" + mp.group(0).strip() + "'", "high")
    for mb in re.finditer(r"([^\s।,]+)\s*নামে পরিচিত", intro + " । " + NFC(r["special"]) + " । " + NFC(r["traits"])):
        nm2 = mb.group(1).strip("‘’'")
        a("local_name", nm2, mb.group(0), "জাত পরিচিতি: '" + mb.group(0) + "'", "medium",
          "name by which farmers know the variety, as stated by the institute")
    for mb in re.finditer(r"^\S+\s?\S*?\s+বা\s+([^\s।,(]+)\s+(?:ব্রি|বাংলাদেশের|বন্যা)", intro):
        a("popular_name", mb.group(1), mb.group(0), "জাত পরিচিতি: '" + mb.group(0) + "'", "medium",
          "alternative name given as '<variety> বা <name>' by the institute")
    mc = re.search(r"কৌলিক সারি(?:\s*নং)?\s*[-:]?\s*([A-Za-z][^\s।]*(?:\s?[A-Za-z0-9()\-]+)*)", intro)
    if mc:
        bl = mc.group(1).strip()
        a("breeding_line", bl, mc.group(0), "জাত পরিচিতি: '" + words25(mc.group(0)) + "'", "high", "")
    for snt in sents:
        if re.search(r"সংকর|সঙ্কর|বিশুদ্ধ সারি|সোমাক্লো|এন্থার|পশ্চাৎ|Double Cross|cross", snt):
            a("pedigree", snt, snt, "জাত পরিচিতি: '" + words25(snt) + "'", "medium",
              "breeding history sentence as stated by the institute (Bangla, not reformatted)")
            break

# ============================================================ SPIA T27
FL = ["irri_direct", "indirect_ir_parent", "inger_entry", "in_reference_library", "sub1", "saline_tolerance",
      "drought_tolerance", "harvestplus"]
SPIA_VIS = (1, 3, 16, 30, 34, 36, 44, 52, 53, 60, 74, 115, 138)
SPIA_KEYFIX = {"Binasail": "BINASHAIL"}
SPIA = {}
for r in csv.DictReader(open(T / "spia2025_table27.csv", encoding="utf-8")):
    pk = SPIA_KEYFIX.get(r["variety"]) or make_key(r["variety"])
    if not pk:
        print("SPIA unmatched", r["variety"]); pk = "UNMATCHED"
    SPIA[pk] = r
    pg = r["pdf_page"]; loc = f"Table 27 row {r['row_no']} '{r['variety']}'"
    flags = "; ".join(f"{f}={r[f]}" for f in FL)
    sv = "visual_check" if int(r["row_no"]) in SPIA_VIS else "unvalidated"
    vn = "; crop 04_working/crops/P2B/spia_t27_check_[ab].png" if sv == "visual_check" else ""
    d, p = r["irri_inger_listed_released_directly"], r["irri_inger_entry_used_as_parents"]
    v = "spia_direct" if r["irri_direct"] == "Y" else "spia_indirect" if r["indirect_ir_parent"] == "Y" else "spia_none"
    add(pk, "cgiar_spia_flags", v, flags + f" | listed released directly: '{d}' | entry used as parent(s): '{p}'", "SPIA", pg, loc,
        "pdf_text", sv, "medium", "SPIA T27 flags: " + flags + f"; IRRI/INGER designation text: released-directly '{d}', parents '{p}'. "
        "SPIA's own definition (IRRI parents or grandparents); NOT our cgiar_role code" + vn)
    add(pk, "official_name_en", r["variety"], r["variety"], "SPIA", pg, loc, "pdf_text", sv, "medium", "SPIA spelling (CGIAR record)" + vn)
    add(pk, "approval_date", r["year"], r["year"], "SPIA", pg, loc + ", col Year released", "pdf_text", sv, "medium",
        "CGIAR-compiled release year (rank 4); not an NSB meeting date" + vn)
    if d and re.match(r"^(IR|BG|BW)\s?\d", d) and "/" not in d:
        add(pk, "breeding_line", d, d, "SPIA", pg, loc + ", col IRRI/INGER listed, released directly", "pdf_text", sv, "medium", "" + vn)
    ped = p if p else (d if "/" in d else "")
    if ped:
        add(pk, "pedigree", ped, ped, "SPIA", pg, loc + (", col IRRI/INGER entry used as parents" if p else ", col IRRI/INGER listed released directly (SPIA placement)"),
            "pdf_text", sv, "medium", ("not a cross formula; SPIA description" if "/" not in ped else "") + vn)
    t = [n for f, n in (("sub1", "Sub1"), ("saline_tolerance", "saline tolerant"), ("drought_tolerance", "drought tolerant"),
                        ("harvestplus", "HarvestPlus (biofortified)")) if r[f] == "Y"]
    if t:
        add(pk, "key_traits", "; ".join(t), flags, "SPIA", pg, loc, "pdf_text", sv, "medium", "" + vn)

# ============================================================ TRIVSA
trv = pd.read_excel(ROOT / SRC["TRIVSA"][3], "Releases")
trv["xlsx_row"] = trv.index + 2
trv = trv[trv["Country where the variety is released"].astype(str).str.contains("Bangladesh")]
TRIV = {}
OLDKEYS = {"Pajam": "OLD_PAJAM", "Purbachi": "OLD_PURBACHI", "BAU 63": "OLD_BAU63"}
nn = lambda x: "" if pd.isna(x) else str(x).strip()
for _, r in trv.iterrows():
    name = r["Release Name"]
    pk = OLDKEYS.get(name) or make_key(name)
    if not pk:
        print("TRIVSA unmatched", name); pk = "UNMATCHED"
    TRIV[pk] = r
    loc = f"sheet Releases, row {r['xlsx_row']} (Ref ID {r['Ref ID']})"

    def a(field, col, notes="", value=None, conf="medium"):
        raw = nn(r[col]) if col else ""
        add(pk, field, value if value is not None else raw, raw, "TRIVSA", "", loc + (f", col {col.strip()}" if col else ""),
            "xlsx", "unvalidated", conf, notes)
    a("official_name_en", "Release Name")
    alt = nn(r["Alternative Name"])
    if alt:
        if re.match(r"^IR\s?\d", alt) or re.match(r"^BAU\s?\d", alt):
            a("aliases", "Alternative Name", "official alternative designation listed by TRIVSA")
        else:
            a("popular_name", "Alternative Name")
    m = re.search(r"\((.+)\)", name)
    if m:
        add(pk, "popular_name", m.group(1), name, "TRIVSA", "", loc + ", col Release Name", "xlsx", "unvalidated", "medium", "bracketed name in TRIVSA Release Name")
    bl = nn(r["Original breeding line name "])
    if bl and bl not in ("Mutation",):
        a("breeding_line", "Original breeding line name ")
    a("pedigree", "Parents", f"Method: {nn(r['Method'])}; female parent '{nn(r['Female parent'])}', male parent '{nn(r['Male parent'])}'")
    a("approval_date", "Year of Release", "CGIAR-compiled year (rank 4)", value=str(r["Year of Release"]))
    a("developer", "Institution that developed the variety", f"Country of origin: {nn(r['Country of origin '])}; Method: {nn(r['Method'])}")
    a("ecosystem", "Recommended domain: Ecosystem")
    a("season", "Recommended domain: Season for cultivation")
    a("region_scope", "State/Province of release")
    meth = nn(r["Method"])
    if meth:
        typ = "hybrid" if nn(r["Hybrid varieties"]) else ("inbred (mutant)" if meth.startswith("Mutation") else "inbred")
        a("type", "Method", f"Method '{meth}'; Hybrid flag '{nn(r['Hybrid varieties'])}'", value=typ)

# ============================================================ HarvestPlus BCR (rice rows)
HP = {}
for r in csv.DictReader(open(T / "harvestplus_bd.csv", encoding="utf-8")):
    if r["crop_name"] != "Rice":
        continue
    pk = make_key(r["variety_name"])
    HP[pk] = r
    loc = f"result.data[{r['json_index']}] id_variety {r['id_variety']}"
    add(pk, "official_name_en", r["variety_name"].strip(), r["variety_name"], "HP", "", loc + " variety_name", "api_json", "unvalidated", "medium", "")
    add(pk, "approval_date", r["realease_year"], r["realease_year"], "HP", "", loc + " realease_year", "api_json", "unvalidated", "medium",
        "HarvestPlus BCR release year (rank 4)")
    add(pk, "key_traits", f"zinc biofortified ({r['nutrition_content']} ppm Zn)", f"display_name={r['display_name']}; nutrition_content={r['nutrition_content']}",
        "HP", "", loc + " nutrition_content", "api_json", "unvalidated", "medium", "")
    ln = r["local_name"].replace("​", "").strip()
    if ln and ln != "NA":
        note = "HarvestPlus 'local_name' field holds a breeding-line code, recorded as breeding_line"
        if pk == "BRRI_DHAN101":
            note += "; CONFLICT: ADC 2025 gives dhan101 = BR8938-19-4-3-1-1-P2-HR3 and IR99285-1-1-1-P2 = dhan102"
        add(pk, "breeding_line", ln, r["local_name"], "HP", "", loc + " local_name", "api_json", "unvalidated", "low" if pk == "BRRI_DHAN101" else "medium", note)
    add(pk, "developer", r["breeder_organization"], f"breeder_organization={r['breeder_organization']}; variety_breeder={r['variety_breeder']}; funded_by={r['funded_by']}",
        "HP", "", loc + " breeder_organization", "api_json", "unvalidated", "low", "HarvestPlus field; 'BRII' = BRRI (typo in source)")

# ============================================================ BRRI fact sheets (gap set, OCR + visual check)
from phase3_F3I_factsheet_data import FS  # list of dicts, transcribed after visual check
for d in FS:
    add(d["pk"], d["field"], d["value"], d["raw"], "FS", d.get("page", 1), d["loc"], "ocr", d["val"], d.get("conf", "high"),
        d.get("notes", ""), lf=d["lf"])

# ============================================================ BINA at-a-glance
s = BeautifulSoup((ROOT / SRC["BINAG"][3]).read_text(encoding="utf-8"), "html.parser")
tab = s.find_all("table")[0]
crop = None; BINAG = {}
for i, tr in enumerate(tab.find_all("tr")[1:], start=2):
    c = [x.get_text(" ", strip=True) for x in tr.find_all("td")]
    if len(c) < 7:
        continue
    if c[0]:
        crop = c[0]
    if crop != "ধান":
        continue
    name, yr, sea, yld, dur, tr_ = c[1:7]
    pk = make_key(name)
    note = ""
    if pk == "BINADHAN7" and yr.translate(BN) == "2015":
        pk = "BINADHAN17"
        note = ("row printed 'বিনাধান-৭ | ২০১৫' is a second Binadhan-7 row; keyed to Binadhan-17 (typo): Binadhan-17 is otherwise absent "
                "from the table, the per-variety menu lists বিনাধান-১৭, SPIA T27 row 93 gives Binadhan-17 = 2015, and the traits differ from the 2007 row")
    BINAG.setdefault(pk, []).append(c)
    loc = f"table row {i} ধান / {name}"
    conf = "medium" if note else "high"
    add(pk, "official_name_bn", "বিনাধান-১৭" if note else name, name, "BINAG", "", loc, "html", "unvalidated", conf, note)
    add(pk, "approval_date", yr.translate(BN), yr, "BINAG", "", loc + ", col অনুমোদনের বছর", "html", "unvalidated", "medium",
        "institute-stated approval year (অনুমোদনের বছর, rank 3); " + note)
    add(pk, "season", "; ".join(SEASON_EN.get(x, x) for x in sea.split("/")), sea, "BINAG", "", loc + ", col চাষাবাদের মৌসুম", "html",
        "unvalidated", conf, note)
    tg = tags(tr_)
    add(pk, "key_traits", tg or tr_, tr_, "BINAG", "", loc + ", col বিশেষ বৈশিষ্ট্য", "html", "unvalidated", conf,
        f"yield {yld} t/ha; duration {dur} d" + ("; English tags by keyword" if tg else "") + ("; " + note if note else ""))
    add(pk, "developer", "BINA", "বিনা উদ্ভাবিত", "BINAG", "", "page title", "html", "unvalidated", "high", "")

# BINA per-variety pages
for f in sorted((ROOT / "02_raw/bina/varieties").glob("*.html")) + [ROOT / "02_raw/bina/bina_rice_variety_index.html"]:
    pk = f.stem if f.parent.name == "varieties" else "BINADHAN7"
    s = BeautifulSoup(f.read_text(encoding="utf-8"), "html.parser")
    t = s.find_all("table")
    if not t:
        continue
    cells = [x.get_text(" ", strip=True) for x in t[0].find_all("td")]
    lf = str(f.relative_to(ROOT)).replace("\\", "/")
    if len(cells) > 3:
        add(pk, "official_name_bn", cells[1], cells[1], "BINAV", "", "জাতের নামঃ", "html", "unvalidated", "high", "", lf=lf)
        tr_ = cells[3]
        add(pk, "key_traits", tags(tr_) or words25(tr_), tr_[:600], "BINAV", "", "জাতের বৈশিষ্ট্যঃ", "html", "unvalidated", "medium",
            "English tags by keyword" if tags(tr_) else "", lf=lf)
        if pk == "BINADHAN19":
            add(pk, "pedigree", "derived from NERICA-10 (খরা সহিষ্ণু নেরিকা-১০ জাত থেকে উদ্ভাবিত)", "খরা সহিষ্ণু নেরিকা-১০ জাত থেকে উদ্ভাবিত",
                "BINAV", "", "জাতের বৈশিষ্ট্যঃ sentence 1", "html", "unvalidated", "high", "IAEA MVD gives carbon-ion mutant of NERICA-10", lf=lf)

# ============================================================ IAEA MVD (Bangladesh rice)
MVDKEY = {"BINA dham 25": "BINADHAN25"}
MVD = {}
for r in csv.DictReader(open(T / "iaea_mvd_bgd.csv", encoding="utf-8")):
    if "ice" not in (r["common_name"] or ""):
        continue
    nm = r["variety_name"].strip()
    pk = MVDKEY.get(nm) or make_key(nm)
    note = "MVD spells 'BINA dham 25' (typo); keyed to Binadhan-25: registration 2022 and 'induced mutations of BRRI dhan 29' match BINA (2022) and SPIA T27 row 136 (parent BRRI Dhan 29)" if nm in MVDKEY else ""
    MVD.setdefault(pk, []).append(r)
    loc = f"MutantVariety list item {r['list_id']} (MVID {r['mvid']}) '{nm}'"
    yr = (r["national_reg_year"] or r["local_reg_year"] or r["registration"] or "").split(".")[0]
    add(pk, "official_name_en", nm, nm, "MVD", "", loc, "api_json", "unvalidated", "medium", note)
    add(pk, "approval_date", yr, f"NationalRegistrationYear={r['national_reg_year']}; LocalRegistrationYear={r['local_reg_year']}; Registration={r['registration']}",
        "MVD", "", loc + " registration year", "api_json", "unvalidated", "medium", "IAEA MVD registration/approval year (secondary); " + note)
    add(pk, "type", "inbred (mutant)", r["development_type"], "MVD", "", loc + " DevelopmentID", "api_json", "unvalidated", "high", f"MVD development type: {r['development_type']}")
    add(pk, "pedigree", words25(r["short_description"]) if len(r["short_description"].split()) > 60 else r["short_description"],
        r["short_description"], "MVD", "", loc + " ShortDescription", "api_json", "unvalidated", "medium",
        "mutant origin as described by IAEA MVD; " + note)

b20 = [r for r in MVD.get("BINADHAN20", [])]
if b20:
    add("BINADHAN20", "cgiar_evidence", "IAEA MVD: HarvestPlus promotes the variety and distributed 16.38 t of seed in 2020-21 (dissemination, not breeding/funding)",
        "HarvestPlus an organization under International Food Policy Research Institute has been promoting this variety", "MVD", "",
        f"MutantVariety list item {b20[0]['list_id']} ShortDescription", "api_json", "unvalidated", "medium",
        "not coded as cgiar_role 3: the text documents seed promotion, not co-development or funding of the variety; HarvestPlus BCR gives funded_by 'Country Initiative'")

# ============================================================ universities / others
add("GAU_DHAN3", "breeding_line", "BU-103-23-5-3", "the proposed genotype (BU-103-23-5-3)", "ABA", "", "Abstract", "html", "unvalidated", "high", "")
add("GAU_DHAN3", "pedigree", "ACC 34 x ACC 51", "derived from ACC 34 X ACC 51", "ABA", "", "Abstract", "html", "unvalidated", "high",
    "single cross, pedigree selection; parents are accession codes whose origin the abstract does not state")
add("GAU_DHAN3", "approving_body", "NSB", "the National Seed Board (NSB) approved the proposed genotype (BU-103-23-5-3) as GAU dhan 3",
    "ABA", "", "Abstract", "html", "unvalidated", "high", "no approval date given; PVT in Aman 2023")
add("GAU_DHAN3", "official_name_en", "GAU dhan 3", "as GAU dhan 3", "ABA", "", "Abstract", "html", "unvalidated", "high", "")
add("GAU_DHAN3", "season", "Aman (wet season)", "for commercial cultivation in the wet season", "ABA", "", "Abstract", "html", "unvalidated", "high", "")
add("GAU_DHAN3", "key_traits", "aromatic; zinc and iron biofortified (23.6 ppm Zn); long slender premium grain",
    "Zn and Fe biofortified aromatic rice containing 23.6 ppm of Zn", "ABA", "", "Abstract", "html", "unvalidated", "high", "")
add("GAU_DHAN3", "developer", "GAU (ex-BSMRAU)", "Ali, Haque, Maniruzzaman, Ivy (GAU)", "ABA", "", "author block", "html", "unvalidated", "medium", "")
add("GAU_DHAN3", "type", "inbred", "single crosses ... pedigree selection", "ABA", "", "Abstract", "html", "unvalidated", "high", "")
add("BU_DHAN1", "key_traits", "short duration (110-120 d); long grain; high amylose; monga mitigation", "Short duration (110 to 120 days) ... Early harvest during unavailability of rice (Monga mitigation)",
    "GAU", 1, "Variety Developed: BU dhan 1", "pdf_text", "unvalidated", "high", "")
add("BU_DHAN1", "developer", "BSMRAU (now GAU)", "Variety Developed BU dhan 1", "GAU", 1, "page 1 heading", "pdf_text", "unvalidated", "high", "")
add("BAU_DHAN3", "breeding_line", "IR 91820-25-BAY2-3-1", "an outstanding product of ACI (IR 91820-25-BAY2-3-1) has been released by BAU named BAU dhan3",
    "ACI", "", "para 'ACI has made MoU ...'", "html", "unvalidated", "medium", "company news page (rank 6)")
add("BAU_DHAN3", "developer", "BAU with ACI (line from IRRI via PPP)", "ACI and the Department of Genetics and Plant Breeding, Bangladesh Agricultural University (BAU) jointly developed it for Boro season",
    "ACI", "", "para 2", "html", "unvalidated", "medium", "")
add("BAU_DHAN3", "season", "Boro", "jointly developed it for Boro season", "ACI", "", "para 2", "html", "unvalidated", "medium", "")

add("OLD_RABI_DHAN1", "breeding_line", "IR78581-12-3-2-2", "For the development of Rabi dhan1, genetic row (IR78581-12-3-2-2) was collected from IRRI (Philippines)",
    "ACI", "", "para 'For the development of Rabi dhan1 ...'", "html", "unvalidated", "medium", "company news page (rank 6); key from key_crosswalk_other.csv (F3L)")
add("OLD_RABI_DHAN1", "developer", "Rajshahi University with ACI (line from IRRI via PPP)", "ACI has made MoU with ... Rajshahi University (Rajshahi Bishawbiddaloy = Rabi) in a PPP mode",
    "ACI", "", "para 'ACI has made MoU ...'", "html", "unvalidated", "medium", "")

# ============================================================ CGIAR lineage (computed)
import phase3_F3I_lineage as LIN
rows.extend(LIN.lineage_rows(rows, ADC, TRIV, SPIA, RP, HP, MVD, SRC))

# ============================================================ two_source post-pass
nz = lambda v: re.sub(r"[\s\-()]", "", unicodedata.normalize("NFD", str(v))).upper()
grp = defaultdict(list)
for r in rows:
    if r["field"] in ("breeding_line", "pedigree", "approval_date", "popular_name", "official_name_bn", "official_name_en", "station_no"):
        grp[(r["pilot_key"], r["field"])].append(r)
for (pk, f), rs in grp.items():
    for r in rs:
        if r["validation"] != "unvalidated":
            continue
        v = r["value"][:4] if f == "approval_date" else nz(r["value"])
        for o in rs:
            if o is r or o["source_id"] == r["source_id"]:
                continue
            ov = o["value"][:4] if f == "approval_date" else nz(o["value"])
            if v and v == ov:
                r["validation"] = "two_source"
                r["notes"] = (r["notes"] + "; " if r["notes"] else "") + f"agrees with {o['source_id']} ({o['source_title'][:60]})"
                break

# ============================================================ OLD_ keys crosswalk (append only)
cw = ROOT / "04_working/key_crosswalk_other.csv"
have = set()
if cw.exists():
    have = {r["key"] for r in csv.DictReader(open(cw, encoding="utf-8"))}
new = [("OLD_PAJAM", "Pajam", "TRIVSA Releases row 73", "TRIVSA: 1966, breeding line 'Mahsuri', origin Malaysia; F3I"),
       ("OLD_PURBACHI", "Purbachi", "TRIVSA Releases row 74", "TRIVSA: 1968, 'Chin-chu-ai', China; parent of BRRI dhan28; F3I"),
       ("OLD_BAU63", "BAU 63", "TRIVSA Releases row 60", "TRIVSA: alternative name 'Vorosha', 1983, BAU; advance line of IR 758-15-2; F3I")]
add_rows = [n for n in new if n[0] not in have]
if add_rows:
    newfile = not cw.exists()
    with open(cw, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if newfile:
            w.writerow(["key", "name_as_printed", "source", "notes"])
        w.writerows(add_rows)

# ============================================================ write
out = ROOT / "04_working/evidence_F3I.csv"
seen = set(); final = []
for r in rows:
    k = tuple(r[h] for h in HDR)
    if k not in seen:
        seen.add(k); final.append(r)
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=HDR); w.writeheader(); w.writerows(final)
print(len(final), "rows;", len({r['pilot_key'] for r in final}), "keys")
print(Counter(r["validation"] for r in final))
print(Counter(r["field"] for r in final).most_common())
miss = [r for r in final if not r["local_file"]]
print("missing local_file:", len(miss))
