"""Final release: 05_output/final/ with clean CSVs, a data dictionary, an Excel workbook (README sheet first)
and the JSON that feeds the visual page. Derived columns (documented in DATA_DICTIONARY.md):
developer_group, rice_type, approval_year. Nothing else is changed from 05_output/*.csv."""
import json, re, pathlib, datetime, unicodedata
import pandas as pd


def nfc(d):
    """REV2 (v1.2, A4-15): every text cell in Unicode NFC, so precomposed and decomposed য়/ড়/ঢ় match."""
    return d.map(lambda v: unicodedata.normalize("NFC", v) if isinstance(v, str) else v)

ROOT = pathlib.Path(__file__).resolve().parents[1]
O = ROOT / "05_output"; F = O / "final"; F.mkdir(exist_ok=True)
r = pd.read_csv(O / "rice_varieties.csv", dtype=str).fillna("")
k = r.variety_id.str.replace("RICE-", "", regex=False)


def group(key):
    if re.match(r"^(BR\d+|BRRI_DHAN\d+|OLD_BRISHAIL)$", key): return "BRRI"
    if key.startswith("BRRI_HYBRID"): return "BRRI"
    if re.match(r"^(BINADHAN|IRATOM|BINASHAIL|BINA_HYBRID)", key): return "BINA"
    if re.match(r"^(BU_|BAU_|GAU_|OLD_BAU63)", key): return "University"
    if key == "PVT_RABI_DHAN1": return "University"          # RU dhan1: University of Rajshahi (with ACI)
    if key.startswith("BRAC_DHAN") or key.startswith("PVT_"): return "Private or NGO inbred"
    if key.startswith("HYB_BADC") or key == "HYB_SL8H": return "BADC (public corporation)"   # SL-8H = BADC hybrid dhan1 (NSB 84 rename)
    if key.startswith("HYB_"): return "Private company"
    if re.match(r"^(IR\d+|OLD_PAJAM|OLD_PURBACHI)$", key): return "Introduction (pre-BRRI)"
    return "Other"


r.insert(2, "developer_group", k.map(group))
r.insert(3, "sector", r.developer_group.map(lambda g: "private" if g in ("Private company", "Private or NGO inbred") else "public"))
r.insert(4, "rice_type", r["type"].str.lower().map(lambda t: "hybrid" if "hybrid" in t else ("inbred" if t else ""))
         .where(lambda s: s != "", k.map(lambda x: "hybrid" if "HYBRID" in x or x.startswith("HYB_") else "inbred")))
r.insert(5, "approval_year", r.approval_date.str[:4])
import sys as _s; _s.path.insert(0, str(ROOT / "scripts")); import link_fixes as LF
import feature_tags as FT
r = FT.add(r)
import derive_covariates as DC
r = DC.add(r)
# REV2 (v1.2, A2-13): sector follows the standardised developer type, so a public body is never 'private'
PUBLIC_TYPES = {"public research institute", "university", "public seed agency", "foreign public", "introduction"}
r["sector"] = r.developer_type.map(lambda t: "public" if t in PUBLIC_TYPES else ("private" if t else "")).where(
    r.developer_type.ne(""), r.sector)
# legal status and pedigree depth come from tables built from this register on the previous pass (rebuild_all.sh runs make_final twice)
for fn, cols in [("bgd_variety_status.csv", {"status_as_of_2026": "status_as_of_2026", "legal_status_2026": "legal_status_2026",
                                              "basis": "status_basis", "hybrid_seed_source": "hybrid_seed_source",
                                              "hybrid_seed_source_evidence": "hybrid_seed_source_evidence"}),
                 ("bgd_pedigree_summary.csv", {"depth_to_cgiar": "depth_to_cgiar", "nearest_cgiar_ancestor": "nearest_cgiar_ancestor"})]:
    fp = F / fn
    if fp.exists():
        t = pd.read_csv(fp, dtype=str).fillna("").set_index("variety_id")
        for src, dst in cols.items():
            if src in t:
                r[dst] = r.variety_id.map(t[src]).fillna("")
# REV2 (v1.2, A2-06/A4-02, G): how the variety descends from CGIAR germplasm, from cgiar_role, depth and breeding method
def _derivation(x):
    role, depth, bm = x.cgiar_role, x.get("depth_to_cgiar", ""), x.get("breeding_method", "")
    if role == "1":
        if re.search(r"mutation|somaclonal", bm) or re.search(r"mutant|irradiat|somaclon", x.pedigree, re.I):
            return "mutant/somaclone"
        if "selection" in bm or re.search(r"selection|selected", x.pedigree, re.I):
            return "selection"
        return "direct line"
    if role == "2":
        if depth == "1": return "cross with CGIAR parent"
        if depth.isdigit() and int(depth) >= 2: return "ancestor"
        return "ancestor" if "grandparent" in x.cgiar_lineage else "cross with CGIAR parent"
    return {"3": "collaboration", "4": "none", "5": "unknown"}.get(role, "")


r.insert(r.columns.get_loc("cgiar_role") + 1, "cgiar_derivation", r.apply(_derivation, axis=1))
r = r.drop(columns=[c for c in ("status",) if c in r])   # REV2 (A1-20): the legacy source 'status' contradicted legal_status_2026
r = LF.apply(r, ("source_url", "archived_url", "cgiar_evidence_url"))
r["doi_key_paper"] = r["doi_key_paper"].map(lambda v: " | ".join(LF.clean_doi(x) for x in v.split(" | ")) if v else v)
r["doi_key_paper_status"] = r["doi_key_paper"].map(lambda v: "; ".join(LF.status("https://doi.org/" + x) for x in v.split(" | ")) if v else "")
r = nfc(r)
r.to_csv(F / "bgd_rice_varieties.csv", index=False, encoding="utf-8-sig")
tabs = {"rice_varieties": r}
FISH_NAMES = {"FISH-BFRI_GIFT": "BFRI Super GIFT tilapia", "FISH-BFRI_HYBRID_MAGUR": "BFRI improved hybrid magur",
              "FISH-BFRI_RAJPUTI": "BFRI improved rajputi (silver barb)", "FISH-BFRI_RED_TILAPIA": "BFRI red tilapia",
              "FISH-BFRI_ROHU_F1_2009": "BFRI improved rohu (F1, 2009)", "FISH-BFRI_SUBARNA_RUI_G4": "BFRI Subarno Rui (G4 rohu)",
              "FISH-BFRI_TILAPIA_IMPROVED_50PCT": "BFRI improved tilapia (about 50% higher yield)",
              "FISH-BFRI_VIETNAMESE_KOI": "BFRI improved koi (Thai / Vietnamese koi line)", "FISH-WF_G3_ROHU": "WorldFish G3 rohu"}
GOV_ACT = {"FISH-BFRI_SUBARNA_RUI_G4": "MoFL naming notification 04 Aug 2021 (Gazette Part I, 21 Oct 2021, p. 607); renamed by MoFL notification 11 Apr 2022",
           "FISH-BFRI_HYBRID_MAGUR": "none found (Hatchery Act 2010 s.6(2) requires DG DoF approval for hybrid release; no approval on record)"}
RB = {"R1": "R1 ministerial naming", "R2": "R2 institute release", "R3": "R3 CGIAR release", "R4": "R4 dissemination only"}


def fish_std(d):
    d = d.copy()
    d.insert(1, "strain_name_std", d.strain_id.map(FISH_NAMES).fillna(d.get("strain_name", "")))
    code = d.approval_or_release_mechanism.str.extract(r"^(R\d)")[0].fillna("")
    d.insert(2, "release_basis", code.map(RB).fillna(""))
    d.insert(3, "government_act", d.strain_id.map(GOV_ACT).fillna("none found"))
    d["approval_or_release_mechanism"] = d.approval_or_release_mechanism.str.replace("R1_statutory", "R1_ministerial_naming", regex=False)
    return d


for name in ["rice_not_approved_or_unresolved", "local_names", "fish_strains", "fish_events", "conflicts", "sources", "failures"]:
    d = pd.read_csv(O / f"{name}.csv", dtype=str).fillna("")
    if name == "fish_strains":
        d = fish_std(d)
    d = nfc(LF.apply(d))
    d.to_csv(F / f"bgd_{name}.csv", index=False, encoding="utf-8-sig"); tabs[name] = d
IDMAP = {"RICE-" + o: "RICE-" + n for o, n in pd.read_csv(ROOT / "04_working/key_remap.csv", dtype=str).fillna("")[["old_key", "new_key"]].values}
for name in ["conflicts_summary", "official_list_rows_full", "nsb_decisions_full", "cgiar_sources", "cgiar_statements", "literature", "publications", "variety_people", "institutions", "ocr_audit"]:   # built by L1 / ocr_confidence.py
    fp = F / f"bgd_{name}.csv"
    if fp.exists():
        tabs[name] = LF.apply(pd.read_csv(fp, dtype=str).fillna(""), ())
        if "variety_id" in tabs[name]:   # merged keys (key_remap.csv) also apply to tables built outside assemble.py
            tabs[name]["variety_id"] = tabs[name].variety_id.replace(IDMAP)
        if name in ("literature", "publications"):
            tabs[name] = LF.apply_literature(tabs[name])
        tabs[name] = nfc(tabs[name])
        tabs[name].to_csv(fp, index=False, encoding="utf-8-sig")

# every file cited by a released table belongs in bgd_sources.csv, not only files with eligible evidence (A3-07, I4)
_man = pd.read_csv(ROOT / "02_raw/manifest.csv", dtype=str).fillna("")
_man["file_path"] = _man.file_path.str.replace("\\", "/", regex=False)
_man = _man.drop_duplicates("file_path").set_index("file_path")
_evs = pd.read_csv(O / "evidence_all.csv", dtype=str, usecols=["source_id", "source_title", "authority_rank", "local_file"]).fillna("")
_evs = _evs.drop_duplicates("local_file").set_index("local_file")
_fa = pd.read_csv(F / "bgd_fish_approvals.csv", dtype=str).fillna("") if (F / "bgd_fish_approvals.csv").exists() else pd.DataFrame()
_cited = {}
for _name, _t in list(tabs.items()) + ([("fish_approvals", _fa)] if len(_fa) else []):
    if _name == "sources" or "local_file" not in _t:
        continue
    for _r in _t.itertuples():
        _lf = str(_r.local_file).replace("\\", "/")
        if _lf.startswith("02_raw/") and _lf not in set(tabs["sources"].local_file):
            _cited.setdefault(_lf, (_name, _r))
_RANK = {"fish_approvals": "1_primary_legal", "institutions": "3_institute_page", "local_names": "4_cgiar_record"}
_add = []
for _lf, (_name, _r) in sorted(_cited.items()):
    if _lf in _evs.index:
        _sid, _tit, _rk = _evs.loc[_lf, ["source_id", "source_title", "authority_rank"]]
    elif _name == "fish_approvals":
        _sid = _r.act_id
        _tit = ", ".join(x for x in [_r.approving_body, _r.approval_reference] if x)
        _rk = _RANK[_name]
    else:
        _sid, _tit, _rk = f"{_name.upper()}:{pathlib.Path(_lf).stem}", "", _RANK.get(_name, "")
    _m = _man.loc[_lf] if _lf in _man.index else pd.Series(dtype=str)
    _add.append(dict(source_id=_sid, source_title=_tit, authority_rank=_rk, local_file=_lf,
                     source_url=_m.get("source_url", ""), archived_url=_m.get("archived_url", ""),
                     download_date=_m.get("download_date", ""), sha256=_m.get("sha256", "")))
if _add:
    _base = [c for c in tabs["sources"].columns if not c.endswith("_status")]
    tabs["sources"] = LF.apply(pd.concat([tabs["sources"][_base], pd.DataFrame(_add)[_base]], ignore_index=True))
    tabs["sources"].to_csv(F / "bgd_sources.csv", index=False, encoding="utf-8-sig")
    print(f"bgd_sources.csv: {len(_add)} files cited only by other tables added")
# ---------------------------------------------------------------------------------------------------------------------

DICT = [
 ("rice_varieties", "variety_id", "Stable ID: RICE-<key>. Keys: BR<n>, BRRI_DHAN<n>, BRRI_HYBRID<n>, BINADHAN<n>, HYB_<trade name> (private hybrids), PVT_ (private inbreds), OLD_ (old names)."),
 ("all tables", "DELIMITERS", "Multi-valued cells use ' | ' between items (aliases, key_traits, cgiar_lineage, cgiar_independent, cgiar_source_urls, conflict_note). Lists of field names (conflict_fields) and validation_summary use '; '. Nothing else is packed into a cell; long-format detail is in conflicts and evidence."),
 ("rice_varieties", "variety_name", "UNIFORM display name generated from the key (BRRI dhan29, BR11, Binadhan-7, BRRI hybrid dhan1, Partex hybrid dhan6 (HR-30)). Use this for joining and display; official spellings stay in official_name_en / official_name_bn."),
 ("rice_varieties", "developer_group", "DERIVED from the key: BRRI, BINA, University, Private or NGO inbred, Private company (hybrids), BADC, Introduction (pre-BRRI)."),
 ("rice_varieties", "sector", "DERIVED: public (BRRI, BINA, universities, BADC, pre-BRRI introductions) or private (seed companies and NGOs such as BRAC). Independent of rice_type: hybrids can be public or private."),
 ("rice_varieties", "rice_type", "DERIVED: hybrid or inbred."),
 ("rice_varieties", "approval_year", "DERIVED: first 4 characters of approval_date."),
 ("rice_varieties", "official_name_en / official_name_bn", "Name exactly as printed by the institute (English) or the official document (Bangla)."),
 ("rice_varieties", "popular_name, aliases", "Popular name (e.g. Chandina); aliases = labels used instead of codes, renamings, trade names."),
 ("rice_varieties", "breeding_line, pedigree", "Pre-release line code and parentage as printed (NSB minutes preferred, then BRRI/BINA sources)."),
 ("rice_varieties", "release_category", "NSB_release (ছাড়করণ), NSB_registration (নিবন্ধন, hybrids), pre_NSB_recommended (before the NSB, 1966-73)."),
 ("rice_varieties", "approval_date / approval_reference", "Date and number of the National Seed Board meeting that approved it (ISO; year only when that is all the record gives)."),
 ("rice_varieties", "provisional_release_date / _reference", "Earlier provisional release, when the full release came later (e.g. BRRI dhan40/41)."),
 ("rice_varieties", "gazette_date / gazette_reference", "Earliest Bangladesh Gazette notification found in an archived gazette copy; later gazettes listed in conflict_note."),
 ("rice_varieties", "gazette_status, gazette_date_reported, gazette_status_note", "Gazette situation for every variety: notified (gazette in archive); notified per NSB minutes (date as reported, no copy found); sent to Government Press, publication not confirmed; not gazetted (hybrid registrations); not applicable (before the Seeds Ordinance 1977); not yet published (2026); not found (no weekly gazettes online before 2013)."),
 ("rice_varieties", "season, ecosystem, region_scope, duration_days, yield_t_ha, key_traits", "As stated in official lists, gazettes or institute sources."),
 ("rice_varieties", "status_as_of_2026, legal_status_2026", "Legal status from the NSB decisions; legal_status_2026 in words (active; active, withdrawal proposed 2021 and deferred; time-limited registration, renewal not recorded; seed multiplication suspended; suspended). Legal status says nothing about seed supply or cultivation."),
 ("rice_varieties", "cgiar_role", "1 CGIAR line released directly; 2 CGIAR parent or grandparent; 3 collaboration or funding only; 4 pedigree known, no CGIAR element; 5 unknown (incl. private hybrids with no published pedigree). Strongest documented link."),
 ("rice_varieties", "cgiar_center, cgiar_lineage, cgiar_evidence", "Centre named (IRRI, AfricaRice, HarvestPlus); the documented link in words (e.g. 'IRRI grandparent: IR20 via BR10'); the quote and file behind it."),
 ("rice_varieties", "cgiar_evidence_quote, cgiar_evidence_source, cgiar_evidence_url", "Exact quote behind cgiar_evidence (original language), the archived file and page, and the original public URL of that document."),
 ("rice_varieties", "cgiar_source_urls", "Direct links to every CGIAR-produced source that mentions the variety (DOI / Europe PMC / CGSpace / IRRI / SPIA pages), ' | ' separated."),
 ("rice_varieties", "validation_summary", "How the key values were verified: field=check (extraction method). Checks: key_check (matched the NSB meeting-date key), visual_check (read by eye on the page image), two_source (two independent sources agree), unvalidated/text (machine-readable text layer). See bgd_ocr_audit.csv for OCR word confidence per page."),
 ("rice_varieties", "conflict_fields", "Substantive fields where sources disagree ('; ' separated); full detail in the conflicts table."),
 ("rice_varieties", "cgiar_spia_flags", "SPIA 2025 Table 27 flags (IRRI direct/indirect, INGER, Sub1, saline, drought, HarvestPlus), kept separate from cgiar_role."),
 ("rice_varieties", "cgiar_independent", "What CGIAR's own publications and websites say (Dikitanan 2022, Villanueva 2022, Raitzer 2015, Kretzschmar 2018, CGSpace records, IRRI, HarvestPlus, STRASA). Cross-check only."),
 ("rice_varieties", "source_url, archived_url, local_file, source_type, retrieved_at", "Main source of the approval record: original URL, Wayback copy (where archived), file in 02_raw, authority rank, download date."),
 ("rice_varieties", "n_sources, flags, conflict_note, notes", "Independent sources behind the row; quality flags (year_only, date_single_source, has_conflicts:<fields>, institute_claim_only...); one-line summary per disagreeing field (' | ' separated); coordinator notes."),
 ("ocr_audit", "all", "One row per OCR'd page that supplied values: Tesseract mean/median word confidence (0-100), share of words below 60, and how many values from that page passed key_check / visual_check."),
 ("rice_varieties", "feature_tags, feature_evidence", "DERIVED tags from the trait text (salt, submergence, drought, cold, heat tolerance; tidal/deepwater/haor; zinc; high protein; aromatic; fine/premium grain; short duration; blast, bacterial blight and lodging resistance; low GI). A stress tag needs a tolerance word next to the stress term, a resistance tag a resistance word; SPIA flags count only when Y and TRIVSA screening codes only when T/R. feature_evidence names the column(s) whose text matched. Rules in scripts/feature_tags.py."),
 ("rice_varieties", "developer_division", "Breeding division named by the institute page or the key paper's author affiliation (e.g. BRRI Plant Breeding Division)."),
 ("rice_varieties", "adoption, market_segment, product_profile", "Adoption shares as reported (TRIVSA/ASTI, SPIA, study-area papers - scope stated in the text); CGIAR GloMIP market segment and product profile."),
 ("rice_varieties", "doi_key_paper", "DOI of the release/description paper or main reference for the variety (see literature table)."),
 ("cgiar_sources", "all", "One row per CGIAR-produced source used (SPIA, IRRI, HarvestPlus, WorldFish, GloMIP, ASTI/TRIVSA, CGSpace records, CGIAR papers): centre, title, DOI, original URL, Wayback copy, local file in 02_raw, SHA-256, number of varieties mentioned, fields taken from it."),
 ("cgiar_statements", "all", "One row per (variety, CGIAR source, field): the value, the exact quote or table cell, page/locator, how it was read and checked, and links to the source."),
 ("official_list_rows_full", "all", "Every printed cell of every official list (SCA 2016 compendium, SCA annual inbred and hybrid lists, MoA hybrid list 1998-2016, 2018, 2020, 2026 editions, Bangladesh Gazette release notices), one row per cell: list, edition, file, page, row, column header as printed and in English, cell text verbatim, normalised value, validation, source URL."),
 ("nsb_decisions_full", "all", "Every National Seed Board decision on rice (578): meeting, date, agenda item, decision type, full verbatim text and raw OCR text, plus every stated attribute in its own column (breeding line, pedigree, origin, DUS and VCU results, check variety, yield and advantage, duration, quality, stress tolerance, conditions, CGIAR mentions), with validation per number."),
 ("ocr_pages", "all", "The OCR corpus: one row per page of every official document (1,925 pages), with full OCR text, Tesseract word confidence, and the text layer where the PDF has one."),
 ("literature", "all", "One row per (variety, publication): type, is_key_paper, title, authors, year, venue, DOI, URL, open-access URL, source API, match_basis (title/abstract), abstract snippet."),
 ("publications", "all", "One row per unique publication with full API metadata (authors, affiliations, citations, keywords, funders, licence, OA status, abstract, CGSpace handle)."),
 ("variety_people", "all", "Authors of key papers and breeders named in official or publication sources, with role and affiliation as stated, ORCID where available, and professional contact only (institutional work e-mail / office phone from the official directory, or corresponding-author e-mail printed in a paper), each with its source URL."),
 ("institutions", "all", "Developing institutes and divisions with official website and office contact from the institution's own contact page."),
 ("local_names", "all", "One row per alias, with source and source_type (official / survey / DNA fingerprinting study / news / other). Market labels such as Miniket are flagged, never forced onto a variety."),
 ("fish_strains", "all", "Released improved fish strains. strain_name_std = uniform English name; strain_name = as printed. release_basis: R1 ministerial naming (MoFL notification), R2 institute release (BFRI announcement or validated-technology list), R3 CGIAR release (WorldFish-documented release of a named generation), R4 dissemination only. government_act: the government instrument found, or 'none found'. Bangladesh has no statutory release system for fish strains (see 06_validation/fish_governance_memo.md)."),
 ("fish_approvals", "all", "Register of 183 government acts on fish and shrimp: species hatcheries may produce, species allowed for import (incl. 92 ornamentals), bans, the vannamei introduction, strain naming, BFRI listings, brood-bank supply, policies and legal powers; each with body, date, reference, legal basis, quote and source."),
 ("fish_events", "all", "Germplasm transfers, introductions and planned generations (kept apart from released strains)."),
 ("pedigree_ancestors", "all", "Every documented ancestor of each variety up to five generations, with path and nominal genetic share."),
 ("pedigree_founders", "all", "Each breeding line with the number of approved varieties descending from it, by decade."),
 ("conflicts", "all", "Every disagreeing value between sources, with file, page and which one was chosen."),
 ("sources", "all", "Every file used: URL, Wayback URL, SHA-256."),
 ("rice_not_approved_or_unresolved", "all", "Names with an NSB decision but no approval through NSB 115 (Jirashail refused 2022; Mallika Basmati-1 and six hybrids deferred and never registered)."),
]
dd = pd.DataFrame(DICT, columns=["table", "column", "meaning"])
md = ["# Data dictionary: Bangladesh rice varieties and fish strains archive", "",
      f"Built {datetime.date.today().isoformat()}. Every value traces to a page of a file in `02_raw/` (see `bgd_sources.csv`).", ""]
for t, g in dd.groupby("table", sort=False):
    md += [f"## {t}", "", "| column | meaning |", "|---|---|"] + [f"| {c} | {m} |" for c, m in zip(g.column, g.meaning)] + [""]
(F / "DATA_DICTIONARY.md").write_text("\n".join(md), encoding="utf-8")

readme = pd.DataFrame({"Bangladesh rice varieties and fish strains archive": [
    f"Built {datetime.date.today().isoformat()}.",
    f"rice_varieties: {len(r)} officially approved rice varieties (NSB releases, hybrid registrations, pre-NSB introductions), CGIAR-linked or not.",
    "Dates are National Seed Board decision dates; gazette dates are separate. CGIAR codes: see the dictionary sheet.",
    "Every row links to its source file (local_file in 02_raw) and original URL; conflicts sheet keeps every disagreeing value.",
    "Sheets: rice_varieties, rice_not_approved, local_names, fish_strains, fish_events, conflicts, sources, failures, dictionary."]})
with pd.ExcelWriter(F / "bgd_variety_archive.xlsx", engine="openpyxl") as xw:
    readme.to_excel(xw, sheet_name="README", index=False)
    dd.to_excel(xw, sheet_name="dictionary", index=False)
    for name, d in tabs.items():
        sh = {"rice_not_approved_or_unresolved": "rice_not_approved"}.get(name, name)
        d.to_excel(xw, sheet_name=sh, index=False)
        ws = xw.sheets[sh]; ws.freeze_panes = "B2"; ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(40, max(9, max(len(str(c.value or "")) for c in col[:60]) * 0.9))
    for sh in ("README", "dictionary"):
        xw.sheets[sh].column_dimensions["A"].width = 110 if sh == "README" else 22
        if sh == "dictionary":
            xw.sheets[sh].column_dimensions["B"].width = 45; xw.sheets[sh].column_dimensions["C"].width = 120

# JSON for the visual page (compact; long text truncated)
keep = ["variety_id", "variety_name", "developer_group", "sector", "rice_type", "approval_year", "official_name_en", "official_name_bn", "popular_name",
        "developer", "release_category", "approval_date", "approval_reference", "gazette_date", "breeding_line", "pedigree",
        "season", "cgiar_role", "cgiar_center", "cgiar_lineage", "cgiar_independent", "cgiar_source_urls", "cgiar_evidence_url", "source_url_status", "archived_url_status", "adoption", "market_segment", "product_profile",
        "validation_summary", "conflict_fields", "feature_tags", "feature_evidence", "duration_days", "yield_t_ha",
        "yield_criterion_pct", "yield_basis", "check_variety", "ecosystem", "region_scope", "recommended_region", "special_traits_official",
        "identifying_traits_official", "quality_traits", "stress_tolerance", "dus_result", "vcu_sites", "gazette_status", "source_url", "archived_url", "local_file", "flags",
        "conflict_note", "trait_text_available", "season_std", "ecosystem_std", "grain_class", "breeding_method", "developer_std", "developer_type",
        "duration_min_days", "duration_max_days", "status_as_of_2026", "legal_status_2026", "status_basis", "hybrid_seed_source", "cgiar_derivation", "depth_to_cgiar", "nearest_cgiar_ancestor", "photoperiod", "establishment", "region_divisions", "region_nationwide", "developer_country_of_origin", "aliases", "n_sources"]
v = r[[c for c in keep if c in r]].copy()
# key papers from the literature table (L1), if present
if "literature" in tabs and len(tabs["literature"]):
    L = tabs["literature"]
    L = L[L.get("is_key_paper", "").astype(str).str.lower().eq("yes")] if "is_key_paper" in L else L
    doi_ok = L.doi.ne("") & (L["doi_status"] if "doi_status" in L else pd.Series("ok", index=L.index)).isin(["ok", "unchecked", "blocked_to_bots", ""])
    kp = (L.assign(u=("https://doi.org/" + L.doi).where(doi_ok, L.url))   # registered DOI, else the publisher page
           .groupby("variety_id").u.apply(lambda s: " | ".join(dict.fromkeys(x for x in s if x))))
    v["key_papers"] = v.variety_id.map(kp).fillna("")
else:
    v["key_papers"] = ""
for c in ["adoption", "market_segment", "product_profile"]:
    v[c] = v[c].str.slice(0, 300)
for c in ["pedigree", "cgiar_lineage", "cgiar_independent"]:
    v[c] = v[c].str.slice(0, 260)
fish = tabs["fish_strains"][["strain_id", "strain_name_std", "release_basis", "government_act", "strain_name", "species_scientific", "developer", "approval_or_release_mechanism",
                             "release_date", "generation", "cgiar_role", "cgiar_center", "status"]]
ev = tabs["fish_events"][[c for c in ["event_id", "event_type", "strain_name", "release_date", "developer", "notes"] if c in tabs["fish_events"]]]
fa_path = F / "bgd_fish_approvals.csv"
fa = pd.read_csv(fa_path, dtype=str).fillna("") if fa_path.exists() else pd.DataFrame()
if len(fa):
    tabs["fish_approvals"] = fa
    nm = next((c for c in ["strain_or_species", "name", "species_common_en", "strain_name"] if c in fa), None)
    fa = fa.assign(name=fa[nm] if nm else "")
    fa = fa[[c for c in ["name", "species_scientific", "approval_type", "approving_body", "approval_date", "approval_reference", "source_url"] if c in fa]]
qa = {}
if "ocr_audit" in tabs and len(tabs["ocr_audit"]):
    A = tabs["ocr_audit"].copy(); A["m"] = A.mean_word_conf.astype(float)
    qa["ocr_pages"] = int(len(A)); qa["ocr_mean_conf"] = round(float(A.m.mean()), 1)
    qa["ocr_bands"] = [[b, int(((A.m >= lo) & (A.m < hi)).sum()), int(A[(A.m >= lo) & (A.m < hi)].n_values.astype(int).sum())]
                       for b, lo, hi in [["90 or more", 90, 101], ["80 to 89", 80, 90], ["70 to 79", 70, 80], ["60 to 69", 60, 70], ["below 60", 0, 60]]]
EV = pd.read_csv(O / "evidence_all.csv", dtype=str, usecols=["method", "validation", "eligible"]).fillna("")
qa["evidence_rows"] = int(len(EV))
qa["by_check"] = EV.assign(c=EV.validation.where(EV.validation != "", "text")).groupby(["method", "c"]).size().reset_index().values.tolist()
qa["n_sources"] = int(len(tabs["sources"])); qa["n_conflicts"] = int(len(tabs["conflicts"]))
refs = pd.read_csv(ROOT / "04_working/references.csv", dtype=str).fillna("")
refs = LF.apply(refs, ("url", "archived_url"))
fa_all = tabs.get("fish_approvals", pd.DataFrame())
fa_groups = []
if len(fa_all):
    fa_groups = (fa_all.groupby("approval_type").agg(n=("act_id", "size"), bodies=("approving_body", lambda x: "; ".join(sorted(set(v for v in x if v))[:3])),
                 first=("approval_date", lambda x: min([v for v in x if v] or [""])), last=("approval_date", lambda x: max([v for v in x if v] or [""])))
                 .reset_index().sort_values("n", ascending=False).to_dict("records"))
key_types = {"strain_naming", "strain_release", "introduction_approval", "ban", "ban_proposal", "import_approval", "technology_transfer",
             "brood_bank_supply", "farm_permit_procedure", "implementation_circular", "genetic_resource_protection", "enforcement_directive"}
fa_key = fa_all[fa_all.approval_type.isin(key_types)] if len(fa_all) else pd.DataFrame()
if len(fa_key):
    fa_key = LF.apply(fa_key, ("source_url",))
    nm = fa_key.strain_name.where(fa_key.strain_name != "", fa_key.species_common_en)
    fa_key = fa_key.assign(name=nm)[["name", "species_scientific", "approval_type", "approving_body", "approval_date", "approval_reference", "source_url", "source_url_status"]]
dec_by = {}
dp = F / "bgd_nsb_decisions_full.csv"
if dp.exists():
    DD = pd.read_csv(dp, dtype=str).fillna("")
    DD = DD[DD.variety_id != ""].sort_values(["variety_id", "meeting_date"])
    for vid, g in DD.groupby("variety_id"):
        dec_by[vid] = [dict(m=x.meeting_no, d=x.meeting_date, t=x.decision_type, h=x.agenda_heading_verbatim,
                            p=(x.variety_passage_verbatim or x.variety_segment_verbatim or x.item_text_verbatim)[:6000],
                            dec=x.decision_text, src=x.source_url, pg=x.pages) for x in g.itertuples()]
FILES = [
 ("bgd_rice_varieties.csv", "Register of officially approved rice varieties: identifiers, names, developer, approval route and NSB decision, gazette notification, pedigree, traits, CGIAR link with evidence, sources and quality flags", "Variety"),
 ("bgd_nsb_decisions_full.csv", "National Seed Board decisions on rice, with the full text of each agenda item and every attribute it states", "Board decision"),
 ("bgd_official_list_rows_full.csv", "Every printed cell of the official variety lists and gazette release notices, verbatim", "List cell"),
 ("bgd_cgiar_sources.csv", "CGIAR publications, databases and web pages used", "Source document"),
 ("bgd_cgiar_statements.csv", "Statements by CGIAR sources about individual varieties, with quotation and location", "Variety-source-field"),
 ("bgd_literature.csv", "Publications naming each variety, with type, DOI and how the match was made", "Variety-publication"),
 ("bgd_publications.csv", "Bibliographic records of those publications", "Publication"),
 ("bgd_variety_people.csv", "Authors and breeders named in key papers or official sources, with professional contact where published", "Variety-person"),
 ("bgd_institutions.csv", "Developing institutes and divisions with official contact details", "Institution"),
 ("bgd_local_names.csv", "Popular, survey and market names linked to varieties", "Variety-name"),
 ("bgd_fish_strains.csv", "Improved fish strains with release basis and government act", "Strain"),
 ("bgd_fish_events.csv", "Germplasm transfers and announced fish generations", "Event"),
 ("bgd_fish_approvals.csv", "Government acts on fish and shrimp species and strains", "Act"),
 ("bgd_conflicts.csv", "Every value on which sources disagree, with the value used", "Variety-field-source"),
 ("bgd_conflicts_summary.csv", "Disagreements classified by type for the analytically important fields", "Variety-field"),
 ("bgd_sources.csv", "Every source file used: URL, archived copy, SHA-256", "Source file"),
 ("bgd_ocr_pages.csv", "Full OCR text and text layer of every page of the official documents", "Page"),
 ("bgd_ocr_audit.csv", "OCR word confidence for pages that supplied values", "Page"),
 ("bgd_rice_not_approved_or_unresolved.csv", "Names with no documented approval", "Name"),
 ("bgd_variety_crosswalk.csv", "Rice variety codes in household surveys (BIHS 2011-12, 2015, 2018-19, 2024; MIXTAPE 2026 drafts) and the SPIA DNA reference library, matched to register identifiers by label", "Survey code"),
 ("bgd_pedigree_edges.csv", "Parent-child links parsed from the published pedigrees, with CGIAR lines marked", "Parent-child link"),
 ("bgd_pedigree_summary.csv", "Generations from each variety to its nearest documented CGIAR ancestor", "Variety"),
 ("bgd_pedigree_ancestors.csv", "Every documented ancestor of each variety up to five generations, with path and nominal genetic share", "Variety-ancestor path"),
 ("bgd_pedigree_founders.csv", "Each breeding line with the number of approved varieties descending from it, by decade", "Breeding line"),
 ("bgd_variety_events.csv", "Every NSB decision on a variety after its approval: extensions, suspensions, renames, deferred withdrawals", "Variety-decision"),
 ("bgd_variety_status.csv", "Legal status of each variety at February 2026, with the basis", "Variety"),
 ("bgd_variety_crosswalk_long.csv", "The survey crosswalk in long form, one row per survey, instrument version, variable and code: the file to merge on", "Survey code"),
 ("bgd_non_register_names.csv", "Widely grown variety names with no approval record (Swarna, Miniket, Haridhan...), with origin and CGIAR code where documented", "Name"),
 ("bgd_evidence.csv", "Every reading behind every register value: source file, page, quotation, method and check", "Evidence row")]
files = []
for fn, desc, unit in FILES:
    fp = F / fn
    if fp.exists():
        d = pd.read_csv(fp, dtype=str)
        files.append(dict(file=fn, desc=desc, unit=unit, rows=int(len(d)), cols=int(d.shape[1]), mb=round(fp.stat().st_size / 1e6, 1)))
(F / "viz_data.json").write_text(json.dumps({"files": files, "decisions": dec_by, "references": refs.to_dict("records"), "fish_groups": fa_groups,
                                             "fish_key_acts": fa_key.to_dict("records") if len(fa_key) else [], "qa": qa, "rice": v.to_dict("records"), "fish": fish.to_dict("records"),
                                             "fish_events": ev.to_dict("records"), "fish_approvals": fa.to_dict("records") if len(fa) else [],
                                             "built": datetime.date.today().isoformat()}, ensure_ascii=False), encoding="utf-8")
print(len(r), "rice;", r.developer_group.value_counts().to_dict()); print(r.rice_type.value_counts().to_dict())
