"""F3L: build evidence_F3L.csv, F3L_inbred_spine.csv, key_crosswalk_other.csv (append-only) and
nsb_meeting_key_additions_F3L.csv from the hand transcriptions in 04_working/F3L/*.tsv.

Every transcribed cell was read by eye from a page render / crop in 04_working/crops/F3L/ (Read tool),
so table values carry validation = visual_check. Gazette rows from SutonnyMJ text layers that were
also viewed are visual_check; the two not viewed page-by-page (2014-03-18 repeat, 2016 Part 6) are
bijoy2unicode text with two_source when the NSB meeting agrees with an SCA list.
Re-runnable: overwrites the F3L outputs; key_crosswalk_other.csv is append-only (skips keys present)."""
import csv, pathlib, re, sys
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_keys import make_key

ROOT = pathlib.Path(__file__).resolve().parents[1]
W = ROOT / "04_working"
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
COLS = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file",
        "page", "locator", "method", "validation", "confidence", "notes"]
rows = []


def add(key, field, value, raw, src, page, loc, method, val, conf="high", notes=""):
    if value is None or str(value).strip() in ("", "nan"):
        return
    s = SRC[src]
    rows.append(dict(pilot_key=key, field=field, value=str(value).strip(), value_raw=str(raw).strip(), source_id=src,
                     source_title=s["title"], authority_rank=s["rank"], local_file=s["file"], page=page,
                     locator=loc, method=method, validation=val, confidence=conf, notes=notes))


# ---------------- keys ----------------
OTHER = {  # name as printed -> key (names make_key cannot handle); written to key_crosswalk_other.csv
    "পাজাম": ("OLD_PAJAM", "Pajam; SCA compendium BRRI table row 02, year 1966, all other cells '-'"),
    "পূর্বাচী": ("OLD_PURBACHI", "Purbachi; compendium row 03 (origin China), 1968"),
    "বিএইউ-৬৩": ("OLD_BAU63", "BAU-63 'Bharosa' (ভরসা); compendium BAU table row 01, 1982; seasonal list on same page prints 'বাউ-৬৩'. Not BAU_DHAN63"),
    "রাবি ধান-১": ("OLD_RABI_DHAN1", "Rajshahi University (with ACI) inbred 'Rabi dhan-1', IR78581-12-3-2-2 (NSIC Rc222); NSB 99th"),
    "এসিআই ধান১": ("OLD_ACI_DHAN1", "ACI Limited private inbred 'ACI dhan1' (IR102481-BK-BK-ACI 28-3-1); NSB 110th. Inbred, not a hybrid"),
    "এসিআই ধান২": ("OLD_ACI_DHAN2", "ACI Limited private inbred 'ACI dhan2'; NSB 114th"),
    "এসিআই ধান৩": ("OLD_ACI_DHAN3", "ACI Limited private inbred 'ACI dhan3'; NSB 114th"),
    "সুপ্রীম ধান১": ("OLD_SUPREME_DHAN1", "Supreme Seed Co. private inbred 'Supreme dhan1'; NSB 113th. Inbred, not a hybrid"),
}


def norm(s):
    return re.sub(r"[\s\-]+", "", str(s))


OTHER_N = {norm(k): v for k, v in OTHER.items()}


def key_of(name):
    n = norm(name)
    for k, v in OTHER_N.items():
        if n.startswith(k):
            return v[0]
    if n.startswith("বঙ্গবন্ধুধান১০০"):
        return "BRRI_DHAN100"  # gazette 2025-04-17 (corrected notice) and SCA FY2020-21 list tie it to BRRI dhan100
    # spacing/hyphen variants of the series prefix seen in official cells ('ব্রি-ধান ৬৫', 'বি ইউ ধান-২')
    nm = re.sub(r"ব্রি\s*-\s*ধান", "ব্রি ধান", str(name)).replace("বি ইউ ধান", "বিইউ ধান")
    return make_key(nm) or "UNMATCHED"


# ---------------- sources ----------------
SRC = {
    "SCA_COMP": dict(title="SCA, 'বাংলাদেশের নোটিফাইড ফসলের অনুমোদিত জাত' (approved varieties of notified crops; imprint 2014, posted 2016)",
                     rank="2_official_list", file="02_raw/sca/approved_varieties_notified_crops_bangladesh_2016.pdf"),
}
for fy in ["2014-15", "2015-16", "2016-17", "2017-18", "2018-19", "2019-20", "2020-21", "2021-22", "2022-23",
           "2023-24", "2024-25", "2025-26"]:
    SRC[f"SCA_FY{fy}"] = dict(title=f"SCA, list of inbred varieties of notified crops released by the NSB, FY{fy}",
                             rank="2_official_list", file=f"02_raw/sca/approved_crop_varieties_{fy}.pdf")
# gazette metadata (read from the page masthead and notice heading)
GZ = {
    "2007-04-16": dict(file="02_raw/moa/release_gazette_nsb62_2007.pdf", issue="Extraordinary", pages="5491",
                       memo="কৃষি/বীজ উইং/বীজ প্র-৭(২)/৯৩/৪৮", memo_date="2007-03-18", basis="Seeds Ordinance 1977 s.5",
                       meetings="62", method="visual_check", crop="gz_2007nsb62_p1.png"),
    "2009-07-21": dict(file="02_raw/moa_wayback/gazette_nsb68_2009-07-21.pdf", issue="Extraordinary", pages="5831",
                       memo="কৃষি/বীজ উইং/বীজ প্রশা-৩২/০৮/১৭৯", memo_date="2008-12-31", basis="Seeds Ordinance 1977 s.5",
                       meetings="68", method="visual_check", crop="gz_2009nsb68_zoom.png"),
    "2013-12-02": dict(file="02_raw/bgpress/moa_extra_02-Dec-2013_8154_27389.pdf", issue="Extraordinary", pages="10261-10262",
                       memo="১২.০৯৭.০২২.০২.০০.০৩২.২০০৮-১২৬", memo_date="2013-11-20", basis="Seeds Ordinance 1977 s.5",
                       meetings="70-80", method="bijoy2unicode", crop="gz_2013-12-02_both.png"),
    "2014-03-18": dict(file="02_raw/bgpress/release_notification_2014-03-18.pdf", issue="Extraordinary", pages="10577-10578",
                       memo="১২.০৯৭.০২২.০২.০০.০৩২.২০০৮-১২৬", memo_date="2013-11-20", basis="Seeds Ordinance 1977 s.5",
                       meetings="70-80", method="bijoy2unicode", crop="gz_2014-03-18_both.png",
                       note="re-publication of the same notice first gazetted 2013-12-02 (same memo no. and date); p.1 masthead prints the year as ২০১৮"),
    "2015-01-22": dict(file="02_raw/bgpress/moa_extra_22-Jan-2015_12441_44845.pdf", issue="Extraordinary", pages="493-495",
                       memo="১২.০৯৭.০২২.০২.০০.০৩২.২০০৮-৪৮৬", memo_date="2014-12-24", basis="Seeds Ordinance 1977 s.5",
                       meetings="70-83", method="bijoy2unicode", crop="gz_2015-01-22_all.png"),
    "2016-06-02": dict(file="02_raw/sca_laws/hybrid_rice_evaluation_registration_revised_procedure_gazette.pdf", issue="Part 6 (weekly)",
                       pages="710", memo="১২.০০.০০০০.০৯৭.২৯.০২৯.০৪-৩৫৮", memo_date="2016-05-17", basis="Seeds Ordinance 1977 s.5",
                       meetings="85, 87", method="bijoy2unicode", crop="gz_2016-06-02_p2.png",
                       note="found inside the SCA copy of the Part 6 issue that also carries the hybrid procedure (memo ...-৩৫৯); text layer and page image checked"),
    "2016-11-07": dict(file="02_raw/bgpress/moa_extra_07-Nov-2016_18866_13961.pdf", issue="Extraordinary", pages="15979-15980",
                       memo="১২.০০.০০০০.০৯৭.২৯.০২৯.০৪-৬৬২", memo_date="2016-10-31", basis="Seeds Ordinance 1977 s.5",
                       meetings="81, 89, 90", method="bijoy2unicode", crop="gz_2016-2018_rice.png"),
    "2017-04-27": dict(file="02_raw/bgpress/moa_extra_27-Apr-2017_21223_67595.pdf", issue="Extraordinary", pages="4113-4114",
                       memo="১২.০০.০০০০.০৯৮.১৭.০০১.০৪.৪০৭", memo_date="2017-04-25", basis="Seeds Ordinance 1977 s.5",
                       meetings="91, 92", method="bijoy2unicode", crop="gz_2016-2018_rice.png"),
    "2018-01-10": dict(file="02_raw/bgpress/moa_extra_10-Jan-2018_24293_98386.pdf", issue="Extraordinary", pages="207-208",
                       memo="১২.০০.০০০০.০৯৮.১৭.০০১.০৪.০৫", memo_date="2018-01-02", basis="Seeds Ordinance 1977 s.5",
                       meetings="93, 94", method="bijoy2unicode", crop="gz_2016-2018_rice.png"),
    "2019-12-11": dict(file="02_raw/bgpress/moa_extra_11-Dec-2019_34659_83539.pdf", issue="Extraordinary", pages="25625-25626",
                       memo="১২.০০.০০০০.০৯৮.১৭.০০১.০৪.১২০০", memo_date="2019-12-05", basis="Seed Act 2018 s.7(3)",
                       meetings="95-101", method="visual_check", crop="gz_2019-12-11_both.png"),
    "2021-08-25": dict(file="02_raw/bgpress/release_notification_2021-08-25.pdf", issue="Extraordinary", pages="12771-12772",
                       memo="১২.০০.০০০০.০৯৭.০২.০০৩.২১.৫৪২", memo_date="2021-08-23", basis="Seed Act 2018 s.7",
                       meetings="102-105", method="visual_check", crop="gz_2021-08-25_both.png",
                       note="this notice was cancelled and re-issued by the corrected notice of 13 Apr 2025 (gazette 2025-04-17), which renames 'বঙ্গবন্ধু ধান১০০' to 'ব্রি ধান১০০'"),
    "2022-06-08": dict(file="02_raw/bgpress/moa_extra_08-Jun-2022_44797_55779.pdf", issue="Extraordinary", pages="9825",
                       memo="১২.০০.০০০০.০৯৮.১৭.০০১.১৮.১৫৬", memo_date="2022-05-31", basis="Seed Act 2018 s.7",
                       meetings="103, 106", method="visual_check", crop="gz_2022-06-08_p1.png"),
    "2025-04-17": dict(file="02_raw/bgpress/moa_extra_17-Apr-2025_57313_27596.pdf", issue="Extraordinary", pages="3607-3608",
                       memo="১২.০০.০০০০.০৯৮.১৭.০০১.১৮.৬০", memo_date="2025-04-13", basis="Seed Act 2018 s.7; NSB 113th decision",
                       meetings="102-105", method="visual_check", crop="gz_2025-04-17_both.png",
                       note="'সংশোধিত প্রজ্ঞাপন' (corrected notice) cancelling memo ...২১.৫৪২ of 25 Aug 2021"),
    "2025-07-19": dict(file="02_raw/bgpress/release_notification_2025-07-19.pdf", issue="Extraordinary", pages="7393-7395",
                       memo="১২.০০.০০০০.০৯৮.১৭.০০১.১৮.১০৬", memo_date="2025-07-13", basis="Seed Act 2018 s.7",
                       meetings="108-114", method="visual_check", crop="gz_2025-07-19_p1_rice.png / gz_2025-07-19_p2_rice.png"),
}
for g, m in GZ.items():
    SRC[f"GAZ_{g}"] = dict(title=f"Bangladesh Gazette {m['issue']}, {g}, MoA Seed Wing notification no. {m['memo']} dated {m['memo_date']}",
                           rank="1_primary_legal", file=m["file"])

# ---------------- helpers ----------------
SEASON = [("বোনা আউশ", "Aus (direct-seeded)"), ("রোপা আউশ", "Aus (transplanted)"), ("রোপা আমন", "T. Aman"),
          ("আউশ", "Aus"), ("আমন", "Aman"), ("বোরো", "Boro"), ("রোরো", "Boro")]


def season_en(raw):
    out, s = [], str(raw)
    for bn, en in SEASON:
        if bn in s:
            out.append(en); s = s.replace(bn, "")
    seen = []
    for o in out:
        if o not in seen and not any(o in x for x in seen):
            seen.append(o)
    return "; ".join(seen)


REGION = {"সমগ্র বাংলাদেশ": "nationwide", "লবনাক্ত এলাকা": "saline areas", "লবণাক্ত এলাকা": "saline areas",
          "উত্তরাঞ্চল": "northern region"}


def region_en(raw):
    raw = str(raw).strip()
    if raw in REGION: return REGION[raw]
    if "সারা দেশে" in raw or "সারাদেশে" in raw: return "nationwide"
    if raw.startswith("সমগ্র বাংলাদেশ") and "ব্যতীত" in raw:
        return "nationwide except AEZ " + ",".join(re.findall(r"\d+", raw.translate(BN)))
    if "হাওড়" in raw: return "haor areas (Habiganj and Sunamganj)"
    return raw.translate(BN)


def nums(raw):
    return str(raw).translate(BN)


kv = pd.read_csv(W / "nsb_meeting_key.csv", dtype=str)
KEYOK = set(zip(kv[kv.validation != "unvalidated"].meeting_no, kv[kv.validation != "unvalidated"].meeting_date))
spine = {}


def sp(key, name, src, extra=""):
    d = spine.setdefault(key, dict(names=set(), sources=[], dev=set()))
    d["names"].add(name); d["sources"].append(src + (f" [{extra}]" if extra else ""))


# ---------------- compendium ----------------
DEV = {"BRRI": ("BRRI", "প্রতিষ্ঠান ঃ বাংলাদেশ ধান গবেষণা ইনস্টিটিউট (বিআরআরআই)"),
       "BINA": ("BINA", "section heading: BINA (বাংলাদেশ পরমাণু কৃষি গবেষণা ইনস্টিটিউট)"),
       "BAU": ("BAU", "প্রতিষ্ঠান ঃ বাংলাদেশ কৃষি বিশ্ববিদ্যালয় (বাকৃবি)"),
       "BSMRAU": ("BSMRAU", "section heading: BSMRAU (বঙ্গবন্ধু শেখ মুজিবুর রহমান কৃষি বিশ্ববিদ্যালয়)")}
c = pd.read_csv(W / "F3L/compendium_transcription.tsv", sep="\t", dtype=str).fillna("")
for r in c.itertuples():
    k = key_of(r.name_bn); src = "SCA_COMP"; pg = int(r.page)
    loc = f"compendium {r.institute} rice table row {r.serial}; crop cmp_p{pg:03d}.png"
    V = ("visual_check", "visual_check")
    note = r.notes
    add(k, "official_name_bn", r.name_bn, r.name_bn, src, pg, loc, *V, notes=note)
    if r.popular_bn: add(k, "popular_name", r.popular_bn, r.popular_bn, src, pg, loc, *V)
    add(k, "developer", DEV[r.institute][0], DEV[r.institute][1], src, pg, loc, *V)
    if r.season_bn not in ("", "-"): add(k, "season", season_en(r.season_bn), r.season_bn, src, pg, loc, *V)
    if r.duration_raw not in ("", "-"): add(k, "duration_days", nums(r.duration_raw), r.duration_raw, src, pg, loc, *V)
    if r.yield_raw not in ("", "-"): add(k, "yield_t_ha", nums(r.yield_raw), r.yield_raw, src, pg, loc, *V)
    yr = int(r.year)
    add(k, "approval_date", str(yr), f"ছাড়করণের সময় {yr}", src, pg, loc, *V,
        notes="year only: compendium column 'ছাড়করণের সময়' (release time); no NSB meeting given in the inbred tables")
    cat = "pre_NSB_recommended" if yr <= 1973 else "NSB_release"
    add(k, "release_category", cat, f"ছাড়করণের সময় {yr}", src, pg, loc, *V,
        notes="year <= 1973 precedes the NSB (first meeting 18.01.1974)" if yr <= 1973 else "listed in the official compendium of approved (released) varieties")
    if yr > 1973: add(k, "approving_body", "NSB", "জাতীয় বীজ বোর্ড (compendium of NSB-approved varieties)", src, pg, loc, *V, conf="medium")
    if r.region_bn not in ("", "-"): add(k, "region_scope", region_en(r.region_bn), r.region_bn, src, pg, loc, *V)
    if r.traits_en not in ("", "-"): add(k, "key_traits", r.traits_en, "special/identifying traits columns (translated)", src, pg, loc, *V, conf="medium")
    if "গণচীন" in note or "China" in note: add(k, "origin_country", "China", "(উৎসঃ গণচীন)", src, pg, loc, *V)
    sp(k, r.name_bn, f"SCA_COMP p{pg}", f"year {yr}")
    if k == "BR6": add(k, "aliases", "IR28", "আইআর -২৮ (popular-name cell)", src, pg, loc, *V, conf="medium",
                       notes="the compendium prints IR28 in BR6's popular-name cell; read as the IRRI line released as BR6")

h = pd.read_csv(W / "F3L/compendium_public_hybrids.tsv", sep="\t", dtype=str).fillna("")
for r in h.itertuples():
    k = key_of(r.name_bn); src = "SCA_COMP"; pg = int(r.page)
    loc = f"compendium hybrid table serial {r.serial}; crop cmp_p{pg:03d}.png"
    V = ("visual_check", "visual_check")
    add(k, "official_name_bn", r.name_bn, r.name_bn, src, pg, loc, *V)
    add(k, "official_name_en", r.name_en, r.name_en, src, pg, loc, *V)
    if r.breeding_line: add(k, "breeding_line", r.breeding_line, r.breeding_line, src, pg, loc, *V)
    add(k, "type", "hybrid (public)", "compendium hybrid table", src, pg, loc, *V)
    add(k, "developer", "BRRI", r.developer_bn, src, pg, loc, *V)
    add(k, "origin_country", "Bangladesh" if r.origin_bn == "বাংলাদেশ" else r.origin_bn, r.origin_bn, src, pg, loc, *V)
    add(k, "region_scope", r.region_bn, r.region_bn, src, pg, loc, *V)
    add(k, "season", season_en(r.season_bn), r.season_bn, src, pg, loc, *V)
    add(k, "duration_days", r.duration_raw, r.duration_raw, src, pg, loc, *V)
    add(k, "yield_t_ha", r.yield_raw, r.yield_raw, src, pg, loc, *V)
    val = "key_check" if (r.meeting, r.meeting_date) in KEYOK else "visual_check"
    add(k, "approval_date", r.meeting_date, f"{r.meeting} তম সভা {r.meeting_date_raw}", src, pg, loc, "visual_check", val)
    add(k, "approval_reference", f"NSB {r.meeting}th meeting", f"{r.meeting} তম সভা", src, pg, loc, "visual_check", val)
    sp(k, r.name_bn, f"SCA_COMP p{pg}", f"NSB {r.meeting}")

# ---------------- FY lists ----------------
f = pd.read_csv(W / "F3L/fy_lists_transcription.tsv", sep="\t", dtype=str).fillna("")
LABEL = {"Lata balam"}
for r in f.itertuples():
    k = key_of(r.name_bn); src = f"SCA_FY{r.fy}"; pg = int(r.page)
    if r.fy == "2024-25" and r.serial == "6":
        k = "UNMATCHED"
    loc = f"FY{r.fy} list rice row {r.serial}; crop {r.crop}"
    V = ("visual_check", "visual_check")
    note = r.notes
    raw_name = r.name_bn
    add(k, "official_name_bn", raw_name, raw_name, src, pg, loc, *V, notes=note)
    if r.breeding_line:
        if r.breeding_line in LABEL:
            add(k, "aliases", r.breeding_line, r.breeding_line, src, pg, loc, *V, notes="descriptive label printed in the breeding-line bracket")
        else:
            add(k, "breeding_line", r.breeding_line, r.breeding_line, src, pg, loc, *V)
    if k == "BRRI_DHAN100":
        add(k, "aliases", "বঙ্গবন্ধু ধান১০০ (Bangabandhu dhan100)", "(বঙ্গবন্ধু ধান১০০)", src, pg, loc, *V)
    if k == "OLD_RABI_DHAN1":
        add(k, "aliases", "NSIC Rc222", "(NSIC Rc222)", src, pg, loc, *V, notes="Philippine release name of IR78581-12-3-2-2")
    if r.developer: add(k, "developer", r.developer, r.developer, src, pg, loc, *V)
    add(k, "season", season_en(r.season_bn), r.season_bn, src, pg, loc, *V)
    add(k, "duration_days", re.sub(r"\s*\(.*", "", r.duration_raw), r.duration_raw, src, pg, loc, *V,
        notes=r.duration_raw if "(" in r.duration_raw else "")
    add(k, "yield_t_ha", r.yield_raw, r.yield_raw, src, pg, loc, *V)
    if r.traits_en: add(k, "key_traits", r.traits_en, "special/identifying traits columns (translated)", src, pg, loc, *V, conf="medium")
    val = "key_check" if (r.meeting, r.meeting_date) in KEYOK else "visual_check"
    add(k, "approval_date", r.meeting_date, f"NSB ({r.meeting}তম সভা) {r.meeting_date_raw}", src, pg, loc, "visual_check", val,
        notes="NSB meeting date as printed in the list")
    add(k, "approval_reference", f"NSB {r.meeting}th meeting", f"{r.meeting}তম সভা", src, pg, loc, "visual_check", val)
    add(k, "approving_body", "NSB", "জাতীয় বীজ বোর্ড কর্তৃক ছাড়কৃত", src, pg, loc, *V)
    add(k, "release_category", "NSB_release", "ছাড়করণের তারিখ (list of NSB-released inbred varieties)", src, pg, loc, *V)
    add(k, "type", "inbred", "ইনব্রিড জাতের তালিকা / ইনব্রেড ধান", src, pg, loc, *V)
    sp(k, raw_name, src, f"NSB {r.meeting} {r.meeting_date}")

# ---------------- gazettes ----------------
g = pd.read_csv(W / "F3L/gazette_transcription.tsv", sep="\t", dtype=str).fillna("").rename(columns={"yield": "yld"})
fyk = {}  # key -> set of meetings from lists, for two_source
for r in f.itertuples(): fyk.setdefault(key_of(r.name_bn), set()).add(r.meeting)
for r in c.itertuples(): pass
seen_gz = {}
for r in g.itertuples():
    m = GZ[r.gz]; k = key_of(r.name_bn); src = f"GAZ_{r.gz}"; pg = int(r.pdf_page)
    method = m["method"]
    viewed = bool(m["crop"])
    loc = f"gazette {r.gz} table row '{r.name_bn}'" + (f"; crop {m['crop']}" if viewed else "")
    if viewed:
        val = "visual_check"
    elif r.meeting in fyk.get(k, set()):
        val = "two_source"
    else:
        val = "unvalidated"
    gnote = m.get("note", "")
    seen_gz.setdefault(k, []).append(r.gz)
    first = len(seen_gz[k]) == 1
    rep = "" if first else f"repeat gazette; earlier gazette(s): {', '.join(seen_gz[k][:-1])}"
    nts = "; ".join(x for x in [gnote, rep] if x)
    add(k, "official_name_bn", r.name_bn, r.name_bn, src, pg, loc, method, val)
    add(k, "gazette_date", r.gz, f"gazette issue date ({m['issue']})", src, pg, loc, method, val, notes=nts)
    add(k, "gazette_reference",
        f"Bangladesh Gazette {m['issue']} {r.gz}, p.{m['pages']}; MoA Seed Wing প্রজ্ঞাপন নং {m['memo']} dated {m['memo_date']}; {m['basis']}; NSB {r.meeting}th meeting",
        f"নং {m['memo']}; {r.meeting}তম সভা", src, pg, loc, method, val, notes=nts)
    add(k, "approval_reference", f"NSB {r.meeting}th meeting", f"{r.meeting}তম সভা (gazette)", src, pg, loc, method, val)
    add(k, "developer", r.developer_bn, r.developer_bn, src, pg, loc, method, val)
    add(k, "region_scope", region_en(r.remark_bn), r.remark_bn, src, pg, loc, method, val)
    s = season_en(r.remark_bn)
    if s: add(k, "season", s, r.remark_bn, src, pg, loc, method, val)
    if r.yld: add(k, "yield_t_ha", nums(r.yld), r.yld, src, pg, loc, method, val)
    add(k, "release_category", "NSB_release", "চাষাবাদের নিমিত্ত ছাড়করণ করা হলো", src, pg, loc, method, val)
    add(k, "approving_body", "NSB (approval); Government/MoA (notification)", "জাতীয় বীজ বোর্ডের ... সভায় অনুমোদনের প্রেক্ষিতে ... সরকার কর্তৃক", src, pg, loc, method, val)
    if "বাংলা মতি" in r.name_bn: add(k, "popular_name", "বাংলা মতি", "(বাংলা মতি)", src, pg, loc, method, val)
    if "বঙ্গবন্ধু" in r.name_bn: add(k, "aliases", "বঙ্গবন্ধু ধান১০০ (Bangabandhu dhan100)", r.name_bn, src, pg, loc, method, val,
                                    notes="name used in the 2021 notice; corrected to 'ব্রি ধান১০০' by the notice gazetted 2025-04-17")
    sp(k, r.name_bn, src, f"NSB {r.meeting}" + ("" if first else "; repeat"))

ev = pd.DataFrame(rows, columns=COLS)
ev.to_csv(W / "evidence_F3L.csv", index=False, encoding="utf-8")

# ---------------- spine ----------------
out = []
for k, d in sorted(spine.items()):
    srcs = d["sources"]
    out.append(dict(key=k, names_as_printed=" | ".join(sorted(d["names"])),
                    in_compendium="yes" if any(s.startswith("SCA_COMP") for s in srcs) else "no",
                    fy_lists=" | ".join(s for s in srcs if s.startswith("SCA_FY")),
                    gazettes=" | ".join(s for s in srcs if s.startswith("GAZ_")),
                    earliest_gazette=min([s[4:14] for s in srcs if s.startswith("GAZ_")], default=""),
                    n_sources=len(srcs)))
spd = pd.DataFrame(out)
spd.to_csv(W / "F3L_inbred_spine.csv", index=False, encoding="utf-8")

# ---------------- key_crosswalk_other (append-only) ----------------
kc = W / "key_crosswalk_other.csv"
have = set()
if kc.exists():
    have = set(pd.read_csv(kc, dtype=str).key)
new = not kc.exists()
with open(kc, "a", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    if new: w.writerow(["key", "name_as_printed", "source", "notes"])
    for nm, (k, nt) in OTHER.items():
        if k in have: continue
        srcs = [s for s in spine.get(k, {}).get("sources", [])]
        w.writerow([k, nm, "F3L: " + "; ".join(srcs), nt])

# ---------------- meeting-key additions ----------------
add_rows = []
seen = set()
for r in f.itertuples():
    t = (r.meeting, r.meeting_date)
    if t in seen: continue
    seen.add(t)
    add_rows.append(dict(meeting_no=r.meeting, meeting_date=r.meeting_date, source_file=SRC[f"SCA_FY{r.fy}"]["file"], page=r.page,
                         method="visual_check", validation="visual_check",
                         notes=f"SCA FY{r.fy} inbred list cell 'NSB ({r.meeting}তম সভা) {r.meeting_date_raw}' read by eye; crop 04_working/crops/F3L/{r.crop}"
                               + ("; agrees with a validated key row" if t in KEYOK else ""), kind="list_cell"))
for r in h.itertuples():
    t = (r.meeting, r.meeting_date)
    if t in seen: continue
    seen.add(t)
    add_rows.append(dict(meeting_no=r.meeting, meeting_date=r.meeting_date, source_file=SRC["SCA_COMP"]["file"], page=r.page,
                         method="visual_check", validation="visual_check",
                         notes=f"SCA compendium hybrid table cell '{r.meeting} তম সভা {r.meeting_date_raw}'; crop 04_working/crops/F3L/cmp_p{int(r.page):03d}.png", kind="list_cell"))
add_rows.append(dict(meeting_no="108", meeting_date="2023-12-26", source_file=SRC["SCA_FY2022-23"]["file"], page="2", method="visual_check",
                     validation="visual_check", notes="SCA FY2022-23 list p.2 wheat rows print '১০৮ তম সভা ২৬/১২/২০২৩'; p.1 rice rows print 26/12/2022 for the same meeting; 2023 is a typo (FY2022-23 list signed 26.07.2023). Kept as a conflicting row", kind="list_cell"))
pd.DataFrame(add_rows).to_csv(W / "nsb_meeting_key_additions_F3L.csv", index=False, encoding="utf-8")

print(len(ev), "evidence rows;", ev.pilot_key.nunique(), "keys;", len(spd), "spine keys")
print(ev.validation.value_counts().to_string())
print("UNMATCHED:", ev[ev.pilot_key == "UNMATCHED"].value_raw.unique()[:5])
