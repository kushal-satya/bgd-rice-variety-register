"""F4 builder: fish/aquaculture central-control register.
Writes 04_working/evidence_F4.csv (long format) and 05_output/final/bgd_fish_approvals.csv (one row per act).
All local files are in the manifest (02_raw/manifest.csv or 02_raw/_manifest_parts/*.csv); source_url is taken
from the manifest row (every manifest row written by lib_fetch.fetch() had HTTP 200: fetch() calls raise_for_status()).
Page numbers for text PDFs are located from the quoted phrase where possible (find_page)."""
import csv, glob, pathlib, re, sys
import fitz
from bijoy2unicode import converter

ROOT = pathlib.Path(__file__).resolve().parents[1]
C = converter.Unicode()

# ---------------------------------------------------------------- manifest lookup
MAN = {}
for f in [ROOT / "02_raw/manifest.csv"] + [pathlib.Path(p) for p in glob.glob(str(ROOT / "02_raw/_manifest_parts/*.csv"))]:
    if f.exists():
        for r in csv.DictReader(open(f, encoding="utf-8-sig", newline="")):
            MAN.setdefault(r["file_path"].replace("\\", "/"), r["source_url"])


def url_of(lf):
    u = MAN.get(lf)
    if u is None:
        sys.exit(f"NOT IN MANIFEST: {lf}")
    return u


_pages = {}


def page_texts(lf):
    if lf not in _pages:
        out = []
        d = fitz.open(ROOT / lf)
        stem = pathlib.Path(lf).stem
        for i, pg in enumerate(d):
            t = pg.get_text()
            try:
                u = "\n".join(C.convertBijoyToUnicode(l + "  ") for l in t.splitlines())
            except Exception:
                u = ""
            o = ROOT / "03_extracted/text/ocr" / stem / f"p{i+1:03d}_psm6.txt"
            ocr = o.read_text(encoding="utf-8", errors="replace") if o.exists() else ""
            out.append(re.sub(r"\s+", " ", t + " " + u + " " + ocr))
        _pages[lf] = out
    return _pages[lf]


def find_page(lf, phrase):
    if not lf.lower().endswith(".pdf"):
        return ""
    ph = re.sub(r"\s+", " ", phrase)
    for i, t in enumerate(page_texts(lf)):
        if ph in t:
            return str(i + 1)
    return ""


# ---------------------------------------------------------------- files
F = dict(
    sub_gaz="02_raw/fish_governance/bgpress_weekly/weekly_2021-10-21_partI_41574_42679.pdf",
    sub_mofl="02_raw/mofl/mofl_prajnapan22_subarno_rui_naming_2021-08-04.pdf",
    sub_ren="02_raw/mofl/mofl_prajnapan17_bfri_subarno_rui_renaming_2022-04-11.pdf",
    sub_leaf="02_raw/bfri/bfri_subarna_rui_page_img1.jpg",
    tvc="02_raw/bfri/bfri_technologies_list_attachment_2026.pdf",
    bfri_glance="02_raw/bfri/pages/static-pages_6922ded5933eb65569e1db71.html",
    fil_dof="02_raw/fishinnovationlab/fil_2023-05_cgip_shares_g3_with_dof.html",
    fil_bfri="02_raw/fishinnovationlab/fil_2023-08_cgip_shares_g3_with_bfri.html",
    g3brood="02_raw/fish_governance/dof/dof_notice_2024-11-26_china_carp_wf_g3_rohu_brood_info.pdf",
    pcf_cust="02_raw/fish_governance/customs/protection_conservation_fish_rules_1985_customs_copy.pdf",
    piranha25="02_raw/fish_governance/dof/dof_notice_2025-05-08_piranha_banned_action.pdf",
    sro98="02_raw/fish_governance/bgpress/mofl_10-Jun-2014_10936_32577.pdf",
    aziz="02_raw/fish_governance/fao/fao_y3994e11_bangladesh_aquatic_animal_health.htm",
    sucker21="02_raw/fish_governance/dof/dof_notice_2021-12-12_sucker_fish_action.pdf",
    sro296="02_raw/fish_governance/bgpress/mofl_29-Sep-2022_46222_79213.pdf",
    sro06="02_raw/fish_governance/bgpress/mofl_15-Jan-2023_47502_48209.pdf",
    fe2021="02_raw/fish_governance/news/fe_2021-09_hope_high_vannamei.html",
    fe2019="02_raw/fish_governance/news/fe_2019-02_govt_decides_pilot_vannamei.html",
    fe2022="02_raw/fish_governance/news/fe_2022-02_two_more_entities_vannamei_trial.html",
    vann="02_raw/fish_governance/dof/dof_notice_2023-04-05_vannamei_commercial_approval_letter.pdf",
    qr2024="02_raw/fish_governance/bgpress/mofl_22-Sep-2024_55874_62529.pdf",
    hr2011="02_raw/mofl/fish_hatchery_rules_2011_bn.pdf",
    sro307="02_raw/fish_governance/bgpress/mofl_19-Nov-2020_37843_81963.pdf",
    bb2020="02_raw/fish_governance/dof/dof_notice_2020-01-13_broodbank_china_carp_restocking.pdf",
    bbcom="02_raw/fish_governance/dof/dof_notice_2020-01-29_china_carp_supervision_committee.pdf",
    halda20="02_raw/fish_governance/bgpress/mofl_21-Dec-2020_38171_83208.pdf",
    halda25="02_raw/fish_governance/bgpress/mofl_05-Nov-2025_59163_84628.pdf",
    shrimp14="02_raw/fish_governance/bgpress/mofl_27-Aug-2014_11457_61175.pdf",
    nfp="02_raw/fish_governance/dof/national_fisheries_policy_1998_en.pdf",
    hact="02_raw/bdlaws/act-details-1042_fish_hatchery_act_2010.html",
    qact="02_raw/bdlaws/act-details-1281_fish_quarantine_act_2018.html",
    bfriact="02_raw/bdlaws/act-details-1282_bfri_act_2018.html",
    noc26="02_raw/fish_governance/dof/dof_notice_2026-04-08_live_fish_import_noc.pdf",
    impid25="02_raw/fish_governance/dof/dof_notice_2025-12-01_import_species_identification_quarantine.pdf",
    yb="02_raw/fish_governance/dof/dof_yearbook_fisheries_statistics_2023-24.pdf",
)
for k, v in F.items():
    if not (ROOT / v).exists():
        sys.exit(f"missing file {k}: {v}")
    url_of(v)

ACTS = []


def act(**kw):
    base = dict(act_id="", key="", level="species", species_common_en="", species_scientific="", species_bn="",
                strain_name="", approval_type="", approving_body="", approval_date="", gazette_date="",
                approval_reference="", gazette_reference="", legal_basis="", scope_conditions="", status="",
                local_file="", page="", locator="", quote="", method="", validation="unvalidated",
                confidence="medium", release_ladder="", notes="")
    base.update(kw)
    if base["local_file"] and not base["page"]:
        base["page"] = find_page(base["local_file"], kw.get("_find", base["quote"][:40]))
    base.pop("_find", None)
    base["source_url"] = url_of(base["local_file"])
    ACTS.append(base)


# ================================================================ STRAIN LEVEL
SUB = dict(key="FISH_BFRI_SUBARNA_RUI_G4", level="strain", species_common_en="Rohu", species_scientific="Labeo rohita",
           species_bn="রুই")
act(act_id="F4-A001", **SUB, strain_name="সুবর্ণ রুই (Subarno Rui)", approval_type="strain_naming",
    approving_body="MoFL, Fisheries-05 Branch (রাষ্ট্রপতির আদেশক্রমে)", approval_date="2021-08-04", gazette_date="2021-10-21",
    approval_reference="প্রজ্ঞাপন নং ৩৩.০০.০০০০.১৩০.৯৯.০২৭.১৯-২২ (20 Srabon 1428 / 04 Aug 2021)",
    gazette_reference="Bangladesh Gazette (weekly), Part I, 21 Oct 2021, p. 607",
    legal_basis="none cited in the notice (executive order of the President); no statute provides for strain naming",
    scope_conditions="Names BFRI's 4th-generation rohu (polymorphic loci 15; gene diversity 0.271±0.190; 20.12% more productive) for the 50th anniversary of independence",
    status="superseded by renaming of 2022-04-11", local_file=F["sub_gaz"], locator="MoFL Matsya-05 প্রজ্ঞাপন block, right column",
    quote="জাতটিকে সুবর্ণ রুই (Subarno Rui) নামকরণ করা হইল", _find="Subarno Rui",
    method="bijoy2unicode", validation="two_source", confidence="high", release_ladder="R1_statutory",
    notes="NEW: gazette printing found (P2F listed it as a gap). Second source: MoFL PDF 02_raw/mofl/mofl_prajnapan22_subarno_rui_naming_2021-08-04.pdf (P2F visual_check). Text layer SutonnyMJ; converted line by line.")
act(act_id="F4-A002", **SUB, strain_name="বিএফআরআই সুবর্ণ রুই [BFRI Subarno Rui]", approval_type="strain_naming",
    approving_body="MoFL, Fisheries-5 Branch", approval_date="2022-04-11",
    approval_reference="প্রজ্ঞাপন নম্বর ৩৩.০০.০০০০.১৩০.৯৯.০২৭.১৯.১৭ (renaming; cites 04.08.2021 notice)",
    gazette_reference="not found in weekly Gazette Part I, 14 Apr - 29 Dec 2022 (38 issues text-searched)",
    legal_basis="none cited", scope_conditions="Renames 'সুবর্ণ রুই' to 'বিএফআরআই সুবর্ণ রুই'", status="current name",
    local_file=F["sub_ren"], quote="“বিএফআরআই সুবর্ণ রুই” [BFRI Subarno Rui] হিসেবে পুনঃ নামকরণ করা হলো", _find="BFRI",
    method="pdf_text", validation="two_source", confidence="high", release_ladder="R1_statutory",
    notes="Born-digital PDF from mofl.gov.bd. Also listed on MoFL notifications page (P2F).")
act(act_id="F4-A003", **SUB, strain_name="বিএফআরআই সুবর্ণ রুই", approval_type="strain_release",
    approving_body="BFRI (institute declaration and release)", approval_date="2021-06-10",
    approval_reference="BFRI leaflet no. 95 (2022), panel 'প্রযুক্তি অবমুক্তকরণ ও আনুষ্ঠানিকতা'", legal_basis="BFRI Act 2018 s.15 (BFRI controls transfer of its technologies)",
    scope_conditions="Declared and released at a BFRI event", status="released", local_file=F["sub_leaf"], page="1",
    locator="right panel 'প্রযুক্তি অবমুক্তকরণ ও আনুষ্ঠানিকতা'", quote="ঘোষণা ও অবমুক্ত", method="visual_check",
    validation="two_source", confidence="high", release_ladder="R2_institute_release",
    notes="From P2F evidence (FS009, visual_check; second source FIL news 2023-08). Date precedes the MoFL naming by 8 weeks.")

TVC = [("7", "FISH_BFRI_GIFT", "Nile tilapia", "Oreochromis niloticus", "তেলাপিয়া", "বিএফআরআই সুপার তেলাপিয়া (family selection GIFT)", "Widely disseminated in the field"),
       ("18", "FISH_BFRI_ROHU_F1_2009", "Rohu", "Labeo rohita", "রুই", "রুই মাছের উন্নত জাত (১৬% বেশী উৎপাদনশীল)", "Widely disseminated in the field"),
       ("19", "FISH_BFRI_TILAPIA_IMPROVED_50PCT", "Nile tilapia", "Oreochromis niloticus", "তেলাপিয়া", "তেলাপিয়ার উন্নত জাত (প্রায় ৫০% বেশী)", "Widely disseminated in the field"),
       ("20", "FISH_BFRI_RAJPUTI", "Silver barb", "Systomus sarana (as printed by TVC)", "রাজপুঁটি", "রাজপুঁটির উন্নত জাত (প্রায় ৩৫% বেশী)", "Less widely disseminated"),
       ("21", "FISH_BFRI_VIETNAMESE_KOI", "Climbing perch", "Anabas testudineus", "কৈ", "থাই কৈ মাছের জাত উন্নয়ন (TVC wording)", "Less widely disseminated"),
       ("22", "FISH_BFRI_RED_TILAPIA", "Red tilapia", "Oreochromis sp.", "লাল তেলাপিয়া", "লাল তেলাপিয়া (Red tilapia) জাত উন্নয়ন", "Less widely disseminated"),
       ("41", "FISH_BFRI_HYBRID_MAGUR", "Hybrid magur", "", "মাগুর (hybrid)", "উন্নত জাতের হাইব্রিড মাগুর", "Not functional at present"),
       ("51", "FISH_BFRI_SUBARNA_RUI_G4", "Rohu", "Labeo rohita", "রুই", "অধিক উৎপাদনশীল বিএফআরআই সুবর্ণ রুই", "Widely disseminated in the field")]
for i, (row, key, en, sc, bn, name, st) in enumerate(TVC):
    act(act_id=f"F4-A{10+i:03d}", key=key, level="strain", species_common_en=en, species_scientific=sc, species_bn=bn,
        strain_name=name, approval_type="technology_validation_listing",
        approving_body="BFRI প্রযুক্তি যাচাই কমিটি (Technology Validation Committee), 4th meeting 01-06-2025",
        approval_date="2025-06-18", approval_reference="BFRI memo ৩৩.০৪.০০০০.০০০.১০৬.২৪.০০০১.২৫.৬১ dated 18-06-2025 (list of 87 উদ্ভাবিত প্রযুক্তি)",
        legal_basis="BFRI internal procedure; BFRI Act 2018 s.15", scope_conditions=f"Listed as technology no. {row}; no year of release or DoF transfer given for any strain row",
        status=st, local_file=F["tvc"], page="3" if row in ("41", "51") else "2", locator=f"সারণি row {row}", quote=name,
        method="visual_check", validation="visual_check", confidence="high", release_ladder="R2_institute_release",
        notes="Values from P2F evidence (crops 04_working/crops/P2F/). The TVC list is a status inventory, not a dated release decision.")

act(act_id="F4-A020", key="FISH_WF_G3_ROHU", level="strain", species_common_en="Rohu", species_scientific="Labeo rohita", species_bn="রুই",
    strain_name="WorldFish G3 rohu", approval_type="technology_transfer", approving_body="WorldFish -> DoF (handover ceremony)",
    approval_date="2023-05-09", approval_reference="Fish Innovation Lab news, May 2023", legal_basis="none (programme handover)",
    scope_conditions="'Technology sharing' of G3 rohu with DoF; no DoF approval instrument found", status="disseminated",
    local_file=F["fil_dof"], quote="(see P2F evidence FS023)", method="html", confidence="medium", release_ladder="R3_cgiar_release",
    notes="Not an approval. From P2F evidence.")
act(act_id="F4-A021", key="FISH_WF_G3_ROHU", level="strain", species_common_en="Rohu", species_scientific="Labeo rohita", species_bn="রুই",
    strain_name="WorldFish G3 rohu", approval_type="technology_transfer", approving_body="WorldFish -> BFRI (handover ceremony)",
    approval_date="2023-08-08", approval_reference="Fish Innovation Lab news, Aug 2023", legal_basis="none (programme handover)",
    scope_conditions="Handover of G3 rohu technology to BFRI", status="disseminated", local_file=F["fil_bfri"],
    quote="(see P2F evidence FS023)", method="html", confidence="medium", release_ladder="R3_cgiar_release", notes="Not an approval. From P2F evidence.")
act(act_id="F4-A022", key="FISH_WF_G3_ROHU", level="strain", species_common_en="Rohu", species_scientific="Labeo rohita", species_bn="রুই",
    strain_name="ওয়াল্ডফিস হতে প্রাপ্ত জি-থ্রি রুই", approval_type="brood_bank_supply",
    approving_body="DoF (Aquaculture wing) data call to government seed multiplication farms", approval_date="2024-11-24",
    approval_reference="DoF memo ৩৩.০২.০০০০.১২২.১০.০০৯.১৯-৯১০ (০৯ অগ্রহায়ণ ১৪৩১ / ২৪ নভেম্বর ২০২৪)",
    legal_basis="none cited (administrative)", scope_conditions="Government fish seed farms hold G3 rohu brood from WorldFish alongside China-imported silver, grass and bighead carp; farms asked to report stock by sex and weight",
    status="G3 rohu brood held in DoF farms", local_file=F["g3brood"], page="1",
    quote="ওয়াল্ডফিস হতে প্রাপ্ত জি-থ্রি রুই মাছের ব্রুড", method="ocr", validation="unvalidated", confidence="medium",
    release_ladder="R4_dissemination_only", notes="Shows DoF uptake of a CGIAR strain into its brood stock, without any approval instrument. Date read by OCR (not cropped).")

# ================================================================ SPECIES: BANS
act(act_id="F4-B001", key="SPECIES_PIRANHA", species_common_en="Piranha (all species of the piranha group)", species_scientific="piranha group (Serrasalmidae, as printed: 'piranha group')",
    species_bn="পিরানহা", approval_type="ban", approving_body="MoFL (Government) under Protection and Conservation of Fish Act 1950 s.3",
    approval_date="2008-02-20", gazette_date="2008-02-24", approval_reference="S.R.O. No. 41-Law/2008 inserting rule 16 in Protection and Conservation of Fish Rules 1985",
    gazette_reference="Bangladesh Gazette Extraordinary, 24 Feb 2008 (per compiled-copy footnote; not in dpp.gov.bd MoFL index)",
    legal_basis="Protection and Conservation of Fish Act 1950 s.3; PCF Rules 1985 r.16", scope_conditions="No person shall import, carry, breed, culture, sell, receive, market, expose or possess any species of the piranha group",
    status="in force (DoF enforcement notice 06/05/2025)", local_file=F["pcf_cust"], quote="Importation, sale, etc., of fish piranha group prohibited",
    method="pdf_text", validation="unvalidated", confidence="medium",
    notes="Source is a consolidated copy 'as modified up to 2nd October 2011' hosted by Bangladesh Customs; footnote 7 gives SRO and dates. Original gazette not retrieved (not listed in bgpress MoFL extraordinary index).")
act(act_id="F4-B002", key="SPECIES_PIRANHA", species_common_en="Piranha / pacu (piranha group)", species_bn="পিরানহা; পিরানহা গোত্রের পাকু মাছ",
    approval_type="enforcement_directive", approving_body="DoF, Fisheries Resource Conservation Branch", approval_date="2025-05-06",
    approval_reference="DoF memo ৩৩.০২.০০০০.১২১.০৬.০০৪.১৮.০৬৭ dated ০৬/০৫/২০২৫", legal_basis="Protection and Conservation of Fish Act 1950",
    scope_conditions="Directs divisional directors to act on press report (Prothom Alo 29/04/2025) of banned piranha farmed in Gaibandha and pacu sold in Dhaka markets",
    status="ban in force", local_file=F["piranha25"], page="1", quote="নিষিদ্ধ হলেও চাষ হচ্ছে পিরানহা", method="ocr", validation="visual_check",
    confidence="high", notes="Header date and subject checked on crop 04_working/crops/F4/piranha2025_sucker2021_headers.png. Notice treats pacu as part of the piranha group.")
act(act_id="F4-B003", key="SPECIES_AFRICAN_MAGUR", species_common_en="African catfish (African magur)", species_scientific="Clarias gariepinus", species_bn="আফ্রিকান মাগুর",
    approval_type="ban", approving_body="Government (reported)", approval_date="", approval_reference="instrument not identified",
    legal_basis="unknown", scope_conditions="Paper by MoFL and BFRI officers (FAO, c.2003) states African catfish introduced 1987-88 'is banned'",
    status="superseded by SRO 98-Law/2014", local_file=F["aziz"], quote="African catfish introduced to Bangladesh during 1987-88 has already earned a bad name and thus is banned",
    method="html", confidence="low", notes="Pre-2014 ban claimed without an instrument. Kept as separate row (do not reconcile).")
act(act_id="F4-B004", key="SPECIES_AFRICAN_MAGUR", species_common_en="African catfish (African magur)", species_scientific="Clarias gariepinus", species_bn="আফ্রিকান মাগুর",
    approval_type="ban_proposal", approving_body="MoFL", approval_date="2013-04-07", approval_reference="S.R.O. No. 92-Law/2013 (pre-publication, 24 Choitro 1419 / 7 Apr 2013)",
    legal_basis="PCF Act 1950 s.3(5)", scope_conditions="Pre-publication of amendments inviting objections for 2 months", status="finalised by SRO 98-Law/2014",
    local_file=F["sro98"], quote="7 GwcÖj, 2013", _find="2013", locator="recital of SRO 98-Law/2014", method="pdf_text", confidence="medium",
    notes="Known only from the recital of SRO 98/2014; the bgpress file for SRO 92/2013 is served as a 0-byte file (logged).")
act(act_id="F4-B005", key="SPECIES_AFRICAN_MAGUR", species_common_en="African catfish (African magur)", species_scientific="Clarias gariepinus", species_bn="আফ্রিকান মাগুর",
    approval_type="ban", approving_body="MoFL, Fisheries-2 and Law Branch", approval_date="2014-05-29", gazette_date="2014-06-10",
    approval_reference="S.R.O. No. 98-Law/2014 (15 Joishtho 1421 / 29 May 2014) adding rule 18 to PCF Rules 1985",
    gazette_reference="Bangladesh Gazette Extraordinary, 10 Jun 2014, pp. 14787-14789", legal_basis="PCF Act 1950 s.3; PCF Rules 1985 r.18",
    scope_conditions="No person shall import, breed, culture, carry, sell, receive, market, stock, expose or possess Clarias gariepinus",
    status="re-enacted as r.18(1) by SRO 06-Law/2023", local_file=F["sro98"], quote="gariepinus prohibited", method="pdf_text", validation="unvalidated",
    confidence="high", notes="Born-digital text; English rule text read directly.")
act(act_id="F4-B006", key="SPECIES_SUCKERMOUTH_CATFISH", species_common_en="Suckermouth catfish and sailfin catfish (plecos)",
    species_scientific="Hypostomus plecostomus; Pterygoplichthys pardalis (as named in DoF notice)", species_bn="সাকার ফিশ",
    approval_type="enforcement_directive", approving_body="DoF (Deputy Director, Aquaculture)", approval_date="2021-12-09",
    approval_reference="DoF memo ৩৩.০২.০০০০.১২২.১০.০১৯.২১-৯২৯ dated ০৯/১২/২০২১", legal_basis="none cited (administrative, before the legal ban)",
    scope_conditions="Destroy suckermouth fish found in open or culture waters; stop hatchery breeding and rearing for ornamental sale; awareness campaign",
    status="superseded by statutory ban (SRO 06-Law/2023)", local_file=F["sucker21"], page="1", quote="সাকার ফিশ (Sucker fish) এর বিষয়ে ব্যবস্থা গ্রহণ",
    method="ocr", validation="visual_check", confidence="high", notes="Header checked on crop piranha2025_sucker2021_headers.png; memo serial is handwritten (read as ৯২৯, low certainty).")
act(act_id="F4-B007", key="SPECIES_SUCKERMOUTH_CATFISH", species_common_en="Suckermouth catfish group", species_bn="সাকার মাউথ ক্যাটফিশ",
    approval_type="ban_proposal", approving_body="MoFL, Law Wing", approval_date="2022-09-25", gazette_date="2022-09-29",
    approval_reference="S.R.O. No. 296-Law/2022 (10 Ashwin 1429 / 25 Sep 2022), pre-publication of new rule 18",
    gazette_reference="Bangladesh Gazette Extraordinary, 29 Sep 2022, p. 15781", legal_basis="PCF Act 1950 s.3(5)",
    scope_conditions="Proposed r.18(1) African magur and r.18(2) any species of the 'Sucker mouth cat fish' group; 2 months for objections",
    status="finalised by SRO 06-Law/2023", local_file=F["sro296"], page="1", quote="any species of fish of ‘Sucker mouth cat fish’ group",
    method="ocr", validation="visual_check", confidence="high", notes="Date line checked on crop halda2025_sro296_headers.png.")
act(act_id="F4-B008", key="SPECIES_SUCKERMOUTH_CATFISH", species_common_en="Suckermouth catfish group", species_bn="সাকার মাউথ ক্যাটফিশ",
    approval_type="ban", approving_body="MoFL, Law Wing", approval_date="2023-01-11", gazette_date="2023-01-15",
    approval_reference="S.R.O. No. 06-Law/2023 (27 Poush 1429 / 11 Jan 2023) substituting rule 18 of PCF Rules 1985",
    gazette_reference="Bangladesh Gazette Extraordinary, 15 Jan 2023, pp. 983-984", legal_basis="PCF Act 1950 s.3; PCF Rules 1985 r.18(2)",
    scope_conditions="No person shall import, breed, culture, carry, sell, receive, market, stock, expose or possess any species of the 'Sucker mouth catfish' group",
    status="in force", local_file=F["sro06"], quote="Sucker mouth catfish", method="pdf_text", confidence="high")
act(act_id="F4-B009", key="SPECIES_AFRICAN_MAGUR", species_common_en="African catfish (African magur)", species_scientific="Clarias gariepinus", species_bn="আফ্রিকান মাগুর",
    approval_type="ban", approving_body="MoFL, Law Wing", approval_date="2023-01-11", gazette_date="2023-01-15",
    approval_reference="S.R.O. No. 06-Law/2023, rule 18(1) (re-enactment)", gazette_reference="Bangladesh Gazette Extraordinary, 15 Jan 2023, p. 984",
    legal_basis="PCF Act 1950 s.3; PCF Rules 1985 r.18(1)", scope_conditions="Same prohibition as 2014, restated",
    status="in force", local_file=F["sro06"], quote="African Magur", method="pdf_text", confidence="high")

# ================================================================ SPECIES: VANNAMEI
V = dict(key="SPECIES_VANNAMEI", species_common_en="Whiteleg shrimp (vannamei)", species_scientific="Litopenaeus vannamei", species_bn="ভেনামি চিংড়ি")
act(act_id="F4-C001", **V, approval_type="introduction_approval", approving_body="Government (technical committee on vannamei feasibility; DoF)",
    approval_date="2019-02", approval_reference="decision reported by The Financial Express, 17 Feb 2019", legal_basis="Fish Hatchery Act 2010 s.8 (import) implied; not stated",
    scope_conditions="Pilot farming on 10-20 acres in Cox's Bazar and Khulna; initially two entrepreneurs; SPF vannamei fry production also suggested",
    status="superseded by commercial approval 2023", local_file=F["fe2019"], quote="Initially two entrepreneurs will get permission to launch the farming",
    method="html", confidence="medium", notes="Press report; the government instrument was not found online.")
act(act_id="F4-C002", **V, approval_type="introduction_approval", approving_body="DoF", approval_date="2019",
    approval_reference="reported by The Financial Express, 26 Sep 2021", legal_basis="not stated",
    scope_conditions="Two pilot projects allowed: M.U. Sea Foods Ltd (BFRI saline water centre, Paikgachha, Khulna; stocked 31 Mar 2021) and Agribusiness Enterprise Development and Services (Cox's Bazar; not started)",
    status="trial", local_file=F["fe2021"], quote="the Department of Fisheries (DoF) allowed two pilot projects in 2019 on vannamei-variety shrimp culture",
    method="html", confidence="medium", notes="Press report quoting DoF. Guideline (F4-C004) confirms trials began 2018 under DoF supervision.")
act(act_id="F4-C003", **V, approval_type="introduction_approval", approving_body="DoF", approval_date="2022-01",
    approval_reference="reported by The Financial Express, 09 Feb 2022 ('decisions came from the fisheries department last month')",
    legal_basis="not stated", scope_conditions="One-year trials for Growtech Aquaculture Ltd (Paikgachha) and Fahim Seafood Ltd (Batiaghata, Khulna); further trial for M.U. Sea Foods Ltd",
    status="trial", local_file=F["fe2022"], quote="Both the decisions came from the fisheries department last month", method="html", confidence="medium",
    notes="Press report. Month only (Jan 2022) inferred from 'last month' in a 9 Feb 2022 article; flagged.")
act(act_id="F4-C004", **V, approval_type="introduction_approval",
    approving_body="MoFL, Fisheries-05 Branch (on DoF letter 33.02.0000.120.06.003.23-107 of 05-03-2023, recommended by technical committee)",
    approval_date="2023-03-29", approval_reference="MoFL memo নং ৩৩.০০.০০০০.১৩০.১৫.০১৭.১৯-(খন্ড-২)-৮৭ (১৫ চৈত্র ১৪২৯ / ২৯ মার্চ ২০২৩); attached 'বাংলাদেশে বাণিজ্যিকভিত্তিতে ভেনামি চিংড়ি চাষ নির্দেশিকা' (DoF, March 2023)",
    legal_basis="Guideline s.5 lists: Fish Hatchery Act 2010, Hatchery Rules 2011, Fish Quarantine Act 2018, Fish Feed Act 2010, Fish Feed Rules 2011",
    scope_conditions="Commercial vannamei culture approved, initially in coastal areas; each farm needs a DG DoF permit after field-committee inspection; only semi-intensive/intensive culture; SPF/SPR PL only; PL import needs DG DoF NOC with health certificate and 'documents on history of strain development'; own quarantine facility until a government station exists",
    status="in force", local_file=F["vann"], page="3", quote="বাংলাদেশে বাণিজ্যিক ভিত্তিতে ভেনামী চিংড়ি চাষ প্রবর্তন",
    method="ocr", validation="visual_check", confidence="high",
    notes="Memo number and date checked on crop 04_working/crops/F4/vannamei_mofl_letter_header.png (received stamp '30 MAR 2023'). Same guideline is 02_raw/dof/dof_vannamei_guideline_2023.pdf (P2F, different scan).")
act(act_id="F4-C005", **V, approval_type="implementation_circular", approving_body="DoF, Deputy Director (Aquaculture)", approval_date="2023-04-05",
    approval_reference="DoF memo ৩৩.০২.০০০০.১২০.০৬.০০৩.২২.২৯ dated ০৫ এপ্রিল ২০২৩", legal_basis="as F4-C004",
    scope_conditions="Circulates the MoFL approval to all DoF field offices, BFRI DG, hatchery managers", status="in force",
    local_file=F["vann"], page="1", quote="ভেনামি চিংড়ি চাষ প্রবর্তন", method="pdf_text", confidence="high",
    notes="Page 1 text layer is broken-font Unicode; date read from the text layer and from the DoF notices listing (5/4/2023).")
act(act_id="F4-C006", **V, approval_type="farm_permit_procedure", approving_body="DG, DoF (permit per farm, after field committee incl. BFRI)",
    approval_date="2023-03-29", approval_reference="Guideline s.9 'ভেনামি চিংড়ি চাষের অনুমোদন প্রক্রিয়া'", legal_basis="Guideline approved by MoFL",
    scope_conditions="Permit valid only for the named farm; no transfer of stock without DoF permission; imported PL/PPL only to the farm named in the import permit; permit cancellable",
    status="in force; list of permitted farms not published online", local_file=F["vann"], page="10",
    quote="মহাপরিচালক, মৎস্য অধিদপ্তর কর্তৃক অফিস আদেশ বা পত্র জারীর মাধ্যমে অনুমতি প্রদান করা হবে", _find="অফিস",
    method="ocr", confidence="high", notes="Individual farm permits (office orders) not found on fisheries.gov.bd.")

# ================================================================ SPECIES: QUARANTINE RULES 2024 SCHEDULE 1
QR = dict(approval_type="import_approval", approving_body="MoFL (Fish Quarantine Rules 2024); import permit by DG DoF",
          approval_date="2024-09-15", gazette_date="2024-09-22",
          approval_reference="S.R.O. No. 311-Law/2024 (31 Bhadro 1431 / 15 Sep 2024), Fish Quarantine Rules 2024, Schedule 1 [rule 3(1)]",
          gazette_reference="Bangladesh Gazette Extraordinary, 22 Sep 2024, p. 26593",
          legal_basis="Fish Quarantine Act 2018 s.9 and s.32; Rules r.3(1)",
          scope_conditions="Broodstock, fry, spawn, shrimp PL/PPL, fertilised eggs, ova, sperm, tissue or cryopreserved material may be imported for registered hatcheries or recognised education/research institutions; species not on the list need a recommendation from the r.3(2) committee (convened by ADG DoF)",
          status="in force", local_file=F["qr2024"], method="pdf_text", confidence="high")
for i, (en, sc, bn, key) in enumerate([("Nile tilapia", "Oreochromis niloticus", "তেলাপিয়া", "SPECIES_NILE_TILAPIA"),
                                       ("Pangas", "Pangasius pangasius (as printed)", "পাঙ্গাস", "SPECIES_PANGAS"),
                                       ("Black tiger shrimp", "Penaeus monodon", "বাগদা চিংড়ি", "SPECIES_BAGDA"),
                                       ("Vannamei shrimp", "Litopenaeus vannamei", "ভেনামি চিংড়ি", "SPECIES_VANNAMEI"),
                                       ("Asian sea-bass / coral", "Lates calcarifer", "ভেটকি", "SPECIES_SEABASS")]):
    act(act_id=f"F4-D{i+1:03d}", key=key, species_common_en=en, species_scientific=sc, species_bn=bn, quote=sc.split(" (")[0],
        page="11", locator="তফসিল-১ (gazette p. 26593)", notes="Schedule 1 has only these 5 species. 'Pangasius pangasius' is printed although the cultured pangas is Pangasianodon hypophthalmus (not corrected).", **QR)

# Schedule 3 ornamental (parsed from the text layer)
raw = (ROOT / "03_extracted/text/F4/mofl_22-Sep-2024_55874_62529.txt").read_text(encoding="utf-8").splitlines()
L = [l.strip() for l in raw[470:794] if l.strip()]
orn, i = [], 0
while i < len(L):
    m = re.fullmatch(r"(\d+)\|", L[i])
    if m and i + 2 < len(L):
        orn.append((int(m.group(1)), L[i + 1], L[i + 2])); i += 3
    else:
        i += 1
assert len(orn) == 92, len(orn)
for n, en, sc in orn:
    act(act_id=f"F4-E{n:03d}", key=f"SPECIES_ORNAMENTAL_S3_{n:02d}", species_common_en=en, species_scientific=sc,
        approval_type="import_approval_ornamental", approving_body="MoFL (Fish Quarantine Rules 2024); import permit by DG DoF",
        approval_date="2024-09-15", gazette_date="2024-09-22",
        approval_reference=f"S.R.O. No. 311-Law/2024, Schedule 3 [rule 4(2)] serial {n}",
        gazette_reference="Bangladesh Gazette Extraordinary, 22 Sep 2024, pp. 26595-26598", legal_basis="Fish Quarantine Act 2018; Rules r.4",
        scope_conditions="Ornamental fish; max 200 brood fish per species per import permit; only registered hatcheries may import for seed production; release into rivers/canals prohibited; fish not on Schedule 3 to be seized and destroyed",
        status="in force", local_file=F["qr2024"], quote=f"{n}| {en} {sc}", _find=sc[:12], method="pdf_text", confidence="high",
        notes="Names as printed (spacing errors kept). Includes Cyprinus carpio as 'Koi Carp' and Carassius auratus varieties.")

# ================================================================ HATCHERY RULES 2011 SCHEDULE 8
S8 = ["রুই", "কাতলা", "মৃগেল", "কালবাউস", "সিলভারকার্প", "গ্রাস কার্প", "মিরর কার্প", "বিগহেড", "ব্ল্যাক কার্প", "মহাশোল", "কার্পিও", "সরপুটি", "রাজপুটি",
      "শিং", "মাগুর", "কৈ", "পাবদা", "গুলশা", "আইর", "পাঙ্গাস", "শোল", "চিতল", "বাগদা চিংড়ি", "গলদা চিংড়ি", "তেলাপিয়া", "ভেটকি", "অন্যান্য (যদি থাকে প্রজাতির নাম উল্লেখ করতে হবে)"]
S8EN = ["Rohu", "Catla", "Mrigal", "Kalibaus", "Silver carp", "Grass carp", "Mirror carp", "Bighead carp", "Black carp", "Mahseer (mahashol)", "Common carp (carpio)",
        "Sarputi (olive barb)", "Rajputi (silver barb)", "Stinging catfish (shing)", "Walking catfish (magur)", "Climbing perch (koi)", "Pabda", "Gulsha", "Long-whiskered catfish (ayre)",
        "Pangas", "Snakehead (shol)", "Chital (clown knifefish)", "Black tiger shrimp (bagda)", "Giant freshwater prawn (golda)", "Tilapia", "Asian sea-bass (bhetki)", "Others (species to be named)"]
for n, (bn, en) in enumerate(zip(S8, S8EN), start=1):
    act(act_id=f"F4-H{n:03d}", key=f"SPECIES_HATCHERY_S8_{n:02d}", species_common_en=en, species_bn=bn,
        approval_type="hatchery_permitted_species", approving_body="MoFL (Fish Hatchery Rules 2011); species written into each hatchery's registration certificate by the DoF registration officer",
        approval_date="2011-07-07", gazette_date="2011-07-12",
        approval_reference=f"S.R.O. No. 242-Law/2011 (23 Asharh 1418 / 7 Jul 2011), Fish Hatchery Rules 2011, Schedule 8 [rule 9] serial {n}",
        gazette_reference="Bangladesh Gazette Extraordinary, 12 Jul 2011, p. 32 of the rules",
        legal_basis="Fish Hatchery Act 2010 s.9 (only fry approved in the registration certificate may be produced); Rules r.9(1)",
        scope_conditions="Species-level list of producible fry; names no strains; African magur absent",
        status="in force (no amendment of Schedule 8 found; SRO 307/2020 amends other parts)", local_file=F["hr2011"], page="32",
        quote=f"{n}. {bn}", method="visual_check", validation="visual_check", confidence="high",
        notes="Bangla names only in source; English names are the archive's gloss. Whole schedule checked on crop 04_working/crops/F4/hatchery_rules_2011_schedule8.png.")

# ================================================================ HATCHERY INPUTS / HEALTH
act(act_id="F4-H101", key="SPECIES_NILE_TILAPIA", species_common_en="Tilapia (monosex)", species_scientific="Oreochromis spp.", species_bn="মনোসেক্স তেলাপিয়া",
    approval_type="hatchery_permitted_input", approving_body="MoFL", approval_date="2020-11-11", gazette_date="2020-11-19",
    approval_reference="S.R.O. No. 307-Law/2020 (26 Kartik 1427 / 11 Nov 2020) amending Fish Hatchery Rules 2011, Schedule 3 Group C (f) item 5",
    gazette_reference="Bangladesh Gazette Extraordinary, 19 Nov 2020, pp. 11851-11853", legal_basis="Fish Hatchery Act 2010 s.11 and s.25",
    scope_conditions="Adds 17-alpha methyltestosterone (sex-reversal hormone used for monosex tilapia) to substances permitted in hatcheries; also creates hatchery category 4 'monosex tilapia hatchery' in the fee table",
    status="in force", local_file=F["sro307"], quote="১৭-আলফা মিথাইলটেস্টোস্টেরণ", _find="17-Avjdv", method="bijoy2unicode", confidence="high",
    notes="Technology permission, not a strain approval.")
act(act_id="F4-H102", key="FRAMEWORK_HATCHERY_VIRUS_FREE", level="framework", species_common_en="Fry, spawn, nauplii and PL (all species)",
    approval_type="health_certification_requirement", approving_body="MoFL", approval_date="2020-11-11", gazette_date="2020-11-19",
    approval_reference="S.R.O. No. 307-Law/2020, new rule 9(4)-(5) of Fish Hatchery Rules 2011",
    legal_basis="Fish Hatchery Act 2010 s.25", scope_conditions="Government to gazette a list of harmful viruses; hatcheries must test fry/PL in a government-recognised lab and declare them virus-free in writing before sale",
    status="in force (no gazetted virus list found)", local_file=F["sro307"], page="3", quote="ভাইরাসমুক্ত", method="bijoy2unicode", confidence="high",
    notes="Health certification of seed lots, the nearest thing to seed certification for fish; covers pathogens, not genetics.")

# ================================================================ BROOD BANK
act(act_id="F4-G001", key="SPECIES_CHINESE_CARPS_BROODBANK", species_common_en="Silver carp, bighead carp, grass carp (imported from China)",
    species_scientific="Hypophthalmichthys molitrix; H. nobilis; Ctenopharyngodon idella", species_bn="সিলভার কার্প, বিগহেড, গ্রাস কার্প",
    approval_type="brood_bank_supply", approving_body="DoF, Brood Bank Establishment Project (3rd phase) (ব্রুড ব্যাংক স্থাপন প্রকল্প, ৩য় পর্যায়)",
    approval_date="2019-06-13", approval_reference="DoF memo ৩৩.০২.০০০০.১২২.০১.০৩৮.৯৭-০৫ dated ১২.০১.২০২০ (reports the 13 June 2019 stocking)",
    legal_basis="DoF development project; NFP 1998 s.7.12 (brood banks in government farms)",
    scope_conditions="38,460 fingerlings of 3-4 g (12,820 each species) imported from China stocked in 8 project farms (one per division) and 3 other government seed farms; 26,988 surviving redistributed at about 10 per decimal (Dec 2019 decision)",
    status="completed project; brood held in government farms (see F4-A022)", local_file=F["bb2020"], page="1",
    quote="ব্রুড ব্যাংক স্থাপন প্রকল্প (৩য় পর্যায়) এর আওতায় চীন থেকে আমদানিকৃত", method="ocr", validation="visual_check", confidence="high",
    notes="Dates and counts checked on crops broodbank_2020_header.png and broodbank_2020_para.png. A DoF office order (Jan 2020, 02_raw/fish_governance/dof/dof_notice_2020-01-29_china_carp_supervision_committee.pdf) set up committees to keep these carps from mixing with other Chinese carp on the farms. Import approval instrument for the 2019 consignment not found.")

# ================================================================ GENETIC RESOURCE PROTECTION
H = dict(key="SPECIES_HALDA_CARP_STOCK", species_common_en="Indian major carps of the Halda river (রুইজাতীয় মাছ)", species_bn="রুইজাতীয় মাছ",
         approval_type="genetic_resource_protection", legal_basis="none cited in the notice")
act(act_id="F4-K001", **H, approving_body="MoFL, Fisheries-2 Branch", approval_date="2020-12-13", gazette_date="2020-12-21",
    approval_reference="প্রজ্ঞাপন নং ৩৩.০০.০০০০.১২৭.২৩.০০১.২০-৩৪৩ (২৮ অগ্রহায়ণ ১৪২৭ / ১৩ ডিসেম্বর ২০২০)",
    gazette_reference="Bangladesh Gazette Extraordinary, 21 Dec 2020, pp. 13901-", scope_conditions="Halda river and 23,422.28 acres of riverside land declared 'বঙ্গবন্ধু মৎস্য হেরিটেজ'; notice states the Halda carp stock is genetically pure",
    status="renamed 2025", local_file=F["halda20"], page="1", quote="রুইজাতীয় মাছের স্টক কৌলিতাত্ত্বিকভাবে (Genetically) বিশুদ্ধ",
    method="ocr", validation="visual_check", confidence="high", notes="Crop halda_2020_header.png.")
act(act_id="F4-K002", **H, approving_body="MoFL, Fisheries-2 Branch", approval_date="2025-10-29", gazette_date="2025-11-05",
    approval_reference="প্রজ্ঞাপন নং ৩৩.০০.০০০০.১২৭.২৩.০০১.২০-৩৯৮ (১৩ কার্তিক ১৪৩২ / ২৯ অক্টোবর ২০২৫)",
    gazette_reference="Bangladesh Gazette Extraordinary, 05 Nov 2025, pp. 11469-11471", scope_conditions="Same area re-declared as 'হালদা নদী মৎস্য হেরিটেজ'",
    status="in force", local_file=F["halda25"], page="1", quote="হালদা নদী মৎস্য হেরিটেজ", method="ocr", validation="visual_check", confidence="high",
    notes="Crop halda2025_sro296_headers.png.")

# ================================================================ POLICY ACTS
act(act_id="F4-P001", key="FRAMEWORK_NFP_1998", level="framework", species_common_en="exotic species; brood fish", approval_type="policy",
    approving_body="MoFL (National Fisheries Policy)", approval_date="1998", approval_reference="National Fisheries Policy 1998, s.7.1 and s.7.12",
    legal_basis="policy (no statutory force)", scope_conditions="s.7.1 proper studies of exotic fish before introduction; s.7.12 brood banks in government farms to supply improved brood fish to private hatcheries",
    status="in force (revision under way per WorldFish)", local_file=F["nfp"], quote="Proper studies will be made for exotic fish, before introduction", _find="exotic fish, before introduction",
    method="pdf_text", confidence="high", notes="Retrieved from fisheries.gov.bd (the file-rajshahi.portal.gov.bd copy timed out twice).")
act(act_id="F4-P002", key="SPECIES_BAGDA", species_common_en="Black tiger shrimp and other shrimp", species_scientific="Penaeus monodon", species_bn="বাগদা চিংড়ি",
    approval_type="policy", approving_body="Government (approved 18 Aug 2014); MoFL notification", approval_date="2014-08-18", gazette_date="2014-08-27",
    approval_reference="MoFL notification নং ৩৩.০১.০০০০.১২৭.০২.০০৩.১৩(অংশ-১)-১৮৭ dated ২৪ আগস্ট ২০১৪, 'জাতীয় চিংড়ি নীতিমালা-২০১৪'",
    gazette_reference="Bangladesh Gazette Extraordinary, 27 Aug 2014, pp. 17097-17108", legal_basis="policy",
    scope_conditions="s.5.5.2 introduce a Shrimp Seed Certification system and ensure supply of Specific Pathogen Free (SPF) PL; objective (gha)(2) SPF broodstock for disease-free PL",
    status="policy; no shrimp seed certification instrument found", local_file=F["shrimp14"], quote="সংক্রমণমুক্ত চিংড়ি/পোনা সরবরাহ নিশ্চিত করার লÿ্যে",
    _find="Shrimp Seed", method="bijoy2unicode", confidence="high")

# ================================================================ FRAMEWORK INSTRUMENTS (legal powers; not decisions)
FW = [("F4-L001", "FRAMEWORK_HATCHERY_ACT_S6", "Fish Hatchery Act 2010 s.6(2); Rules 2011 r.7", "DG DoF",
       "Hybrid strains developed by a recognised institute may not be released for production or culture without DG DoF approval (decision within 30 days)",
       F["hact"], "সংকরায়ন জাতের মাছ উৎপাদন বা চাষের জন্য অবমুক্ত করা যাইবে না", "No approval under s.6(2) found for any hybrid (incl. BFRI hybrid magur)."),
      ("F4-L002", "FRAMEWORK_HATCHERY_ACT_S8", "Fish Hatchery Act 2010 s.8; Rules 2011 r.8", "DG DoF",
       "No live fish, spawn, fry or PL may be imported without prior DG approval", F["hact"], "বিদেশ হইতে কোন জীবিত মৎস্য, রেণু, পোনা বা পিএল আমদানী করিতে পারিবে না",
       "Individual import approvals are not published; since July 2025 NOCs are issued online via Bangladesh Single Window (DoF notice 06-04-2026)."),
      ("F4-L003", "FRAMEWORK_HATCHERY_ACT_S9", "Fish Hatchery Act 2010 s.9", "DG DoF / registration officer",
       "A hatchery may produce only the fry approved in its registration certificate", F["hact"], "নিবন্ধন সনদে উল্লিখিত অনুমোদিত পোনা ব্যতীত অন্য কোন পোনা উৎপাদন করা যাইবে না", "Species-level control; see Schedule 8 rows."),
      ("F4-L004", "FRAMEWORK_QUARANTINE_ACT_S9", "Fish Quarantine Act 2018 s.9-10", "DG DoF (Fish Quarantine Authority)",
       "No fish, fish product or probiotic may be imported without an import permit", F["qact"], "আমদানি অনুমতিপত্র ব্যতিরেকে কোনো আমদানিকারক", ""),
      ("F4-L005", "FRAMEWORK_QUARANTINE_ACT_S17", "Fish Quarantine Act 2018 s.17", "Government, by gazette",
       "Power to prohibit or restrict entry, introduction, sale, culture, breeding or transport of GMOs, LMOs, alien invasive species and germplasm",
       F["qact"], "জেনেটিক্যালি মডিফাইড অর্গানিজমস্", "No s.17 notification found in the MoFL extraordinary gazette index (2018-2026)."),
      ("F4-L006", "FRAMEWORK_QUARANTINE_RULES_R3_COMMITTEE", "Fish Quarantine Rules 2024 r.3(2)-(4)", "Committee convened by ADG DoF (members: DLS, BFRI, a public university, a registered hatchery owner; DD Aquaculture as secretary)",
       "Recommends adding to Schedule 1 any species or strain (জাত বা প্রজাতি) not cultured in Bangladesh", F["qr2024"], "আমদানির জন্য সুপারিশ প্রদানের জন্য নিম্নবণির্ত সদস্য সমন্বয়ে একটি কমিটি থাকিবে",
       "The only standing committee in fish law whose remit names 'জাত' (strain); no recommendation or Schedule 1 amendment found."),
      ("F4-L007", "FRAMEWORK_BFRI_ACT_S15", "BFRI Act 2018 s.15", "BFRI", "BFRI technologies are BFRI property and may not be transferred without the Institute's approval",
       F["bfriact"], "প্রযুক্তি", "Basis for BFRI's own release and TVC listing.")]
for aid, key, ref, body, scope, lf, q, note in FW:
    act(act_id=aid, key=key, level="framework", approval_type="framework_instrument", approving_body=body, approval_reference=ref, legal_basis=ref,
        scope_conditions=scope, status="in force", local_file=lf, quote=q, method="html" if lf.endswith(".html") else "bijoy2unicode", confidence="high", notes=note)

# ================================================================ RECORDED INTRODUCTIONS (no instrument)
INTRO = [("Common carp", "Cyprinus carpio var. communis", "China (1960) Vietnam (1995)", "SPECIES_COMMON_CARP"),
         ("Grass carp", "Ctenopharyngodon idella", "Hongkong (1966) Nepal (1974), Japan(1970)", "SPECIES_GRASS_CARP"),
         ("Silver carp", "Hypophthalmichthys molitrix", "Hongkong (1969)", "SPECIES_SILVER_CARP"),
         ("Bighead carp", "Aristichthys nobilis", "Nepal (1981)", "SPECIES_BIGHEAD_CARP"),
         ("Mirror carp", "C. carpio v ar. specularis", "Nepal (1974) Hungary (1996)", "SPECIES_MIRROR_CARP"),
         ("Black carp", "Mylopharyngodon piceus", "China (1983)", "SPECIES_BLACK_CARP"),
         ("Gold fish", "Cyprinus carpio", "Hongkong (1966)", "SPECIES_GOLDFISH"),
         ("Mahseer", "Tor putitora", "Nepal (1991)", "SPECIES_MAHSEER"),
         ("Silver barb", "Barbodes gonionotus", "Thailand (1987)", "SPECIES_SILVER_BARB"),
         ("Gurami", "Trichogaster pectoralis", "Thailand (1995)", "SPECIES_GURAMI"),
         ("African catfish", "Clarias gariepinus", "Thailand (1988)", "SPECIES_AFRICAN_MAGUR"),
         ("Pangash", "Pangasius sutchi", "Thailand (1985)", "SPECIES_PANGAS"),
         ("Tilapia", "Oreochromis mossambicus", "Thailand (1954)", "SPECIES_MOZAMBIQUE_TILAPIA"),
         ("Nilotica", "O. niloticus", "Thailand (1974,1986)", "SPECIES_NILE_TILAPIA"),
         ("Red strain of tilapia", "Mutant of O. niloticus x O. mossambicus", "Thailand (1988)", "SPECIES_RED_TILAPIA"),
         ("GIFT", "Genetically Improved Farmed Tilapia", "Philippines (1994)", "SPECIES_NILE_TILAPIA")]
for i, (en, sc, src, key) in enumerate(INTRO, start=1):
    yrs = re.findall(r"\((\d{4})", src) + re.findall(r",(\d{4})\)", src)
    act(act_id=f"F4-M{i:03d}", key=key, species_common_en=en, species_scientific=sc, approval_type="introduction_recorded",
        approving_body="not stated", approval_date=min(yrs) if yrs else "", approval_reference="Aziz (MoFL) & Hossain (BFRI), FAO paper c.2003, Table 2 'Freshwater fish introduced to Bangladesh during 1950-2000'",
        legal_basis="none stated", scope_conditions=f"From where introduced and when: {src}", status="introduced", local_file=F["aziz"],
        quote=f"{en} {sc} {src}", method="html", confidence="medium",
        notes="Introduction event, not an approval act; no import approval instrument found for any of these. Year = earliest year in the source cell.")

# ================================================================ WRITE REGISTER
OUTC = ["act_id", "key", "level", "species_common_en", "species_scientific", "species_bn", "strain_name", "approval_type", "approving_body",
        "approval_date", "gazette_date", "approval_reference", "gazette_reference", "legal_basis", "scope_conditions", "status", "release_ladder",
        "source_url", "local_file", "page", "locator", "quote", "method", "validation", "confidence", "notes"]
outp = ROOT / "05_output/final/bgd_fish_approvals.csv"
outp.parent.mkdir(parents=True, exist_ok=True)
with open(outp, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=OUTC); w.writeheader()
    for a in ACTS:
        w.writerow({k: a.get(k, "") for k in OUTC})

# ================================================================ EVIDENCE (long)
EVC = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file", "page", "locator", "method",
       "validation", "confidence", "notes"]
RANK = lambda a: ("1_primary_legal" if ("gazette" in a["local_file"] or "bgpress" in a["local_file"] or a["local_file"].startswith("02_raw/bdlaws")
                                        or "mofl" in a["local_file"] or "dof_notice" in a["local_file"] or "hatchery_rules" in a["local_file"])
                  else "2_official_list" if "bfri" in a["local_file"] or "yearbook" in a["local_file"] or "national_fisheries_policy" in a["local_file"]
                  else "5_news" if "/news/" in a["local_file"] else "4_cgiar_record" if "fishinnovationlab" in a["local_file"] else "3_secondary")
FIELDS = ["species_common_en", "species_scientific", "species_bn", "strain_name", "approval_type", "approving_body", "approval_date",
          "gazette_date", "approval_reference", "gazette_reference", "legal_basis", "scope_conditions", "status", "source_url"]
n = 0
with open(ROOT / "04_working/evidence_F4.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=EVC); w.writeheader()
    for a in ACTS:
        for f in FIELDS:
            v = a.get(f, "")
            if not v:
                continue
            val = a["validation"]
            # validation applies to dates/references only when the act's check covered them
            if f not in ("approval_date", "approval_reference", "gazette_date", "status", "species_bn", "strain_name") and val == "visual_check":
                val = "unvalidated" if a["method"] == "ocr" else val
            w.writerow(dict(pilot_key=a["key"], field=f, value=v, value_raw=a["quote"] if f in ("approval_type", "strain_name") else "",
                            source_id=a["act_id"], source_title=a["approval_reference"][:200], authority_rank=RANK(a), local_file=a["local_file"],
                            page=a["page"], locator=a["locator"] or a["quote"][:60], method=a["method"], validation=val,
                            confidence=a["confidence"], notes=a["notes"][:300]))
            n += 1
print(len(ACTS), "acts;", n, "evidence rows")
import collections
print(collections.Counter(a["approval_type"] for a in ACTS))
print("missing page:", [a["act_id"] for a in ACTS if a["local_file"].endswith(".pdf") and not a["page"]])
