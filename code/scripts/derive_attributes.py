"""Variety attributes in the column set of the BAU stocktake (round 3, agent E2), read only from our own archived sources.

Two entry points
----------------
python scripts/derive_attributes.py --build
    Reads the extracted tables of our archive and writes one evidence row per reading to 04_working/evidence_ATTR.csv
    (standard evidence columns). Sources, in the order they are preferred when the register value is chosen:
      1 official lists  05_output/final/bgd_official_list_rows_full.csv (gazettes, SCA annual lists and compendium,
                        MoA hybrid lists; every cell transcribed by eye from page crops, validation visual_check)
      2 NSB decisions   05_output/final/bgd_nsb_decisions_full.csv (amylose, protein, zinc, iron, L/B ratio, grain
                        type, trial duration and yield per decision; numbers checked by eye, val_* columns)
      3 BRRI ADC 2025   03_extracted/tables/adc2025_table2.csv (Adhunik Dhaner Chash 2025, Table 2: season,
                        plant height, duration, grain description, yield; SutonnyMJ text layer)
      4 BRRI Rice Profile 03_extracted/tables/brri_riceprofile.csv (riceprofile.brri.gov.bd variety pages)
      5 BINA pages      02_raw/bina/varieties/*.html (bina.gov.bd per-variety pages) and the BINA 'at a glance' table
                        02_raw/bina/bina_at_a_glance_varieties.html (season, average yield, duration split by '/')
    For the agronomic numbers (yield, duration, plant height) the order is 1, 3, 4, 5, 2: the developer's published
    description comes before the Board's trial mean. For grain chemistry (amylose, protein, zinc, iron) the order is 1, 2,
    3, 4, 5.
    BAU stocktake values are NOT read here (PI ruling 2026-11-10: BAU is used only for comparison, see
    scripts/bau_compare.py and 06_validation/bau_comparison.md).

add(df) -> df
    Called by make_final.py after derive_covariates.add. Pure function: never changes an existing column; appends the
    attribute columns below, each group followed by its *_source column, filled from 04_working/evidence_ATTR.csv
    (chosen by the source order above) and from register columns that already carry the information
    (type, origin_statement/origin_country, ecosystem_std). A blank cell means no archived source states the value.

Rules
-----
* A value is written to a season column only when the same source names the season for that value: a season label next
  to the number ('130-135 (আউশ)', 'বোরো মওসুমে ১৪০ দিন'), or a source row whose season cell names exactly one season.
  Numbers without a season in a multi-season row are recorded in the evidence (field *_unseasoned) but not used.
* Numbers are copied as printed (Bangla digits converted, ranges kept as 'a-b'); nothing is averaged or converted,
  except yields printed per acre, which are kept out (not t/ha).
* Grain description: grain_size_text is the phrase as printed (Bangla); grain_type is its English class
  (long/medium/short x slender/bold) by the same word list as derive_covariates.grain_class; aleurone_colour is the
  colour of the milled grain as stated (চাল সাদা = white, লাল = red, বাদামী = brown); a white belly
  ('পেটে সাদা দাগ', chalkiness) is not a colour statement.
* variety_type is the register's type (hybrid / inbred / inbred (mutant)); no source in the archive states 'HYV',
  'local improved' or 'OPV' per variety in a way that could be attributed without inference.
* germplasm_origin is the origin as printed (official list origin cell, NSB germplasm source), with an English gloss in
  front ('China (চীন)'); otherwise the register's origin_statement or origin_country.
* first_year_of_adoption, on_farm_yield_*, dissemination_notes and cgiar_projects stay blank unless a source states them;
  no archived source states a first year of adoption, and cgiar_projects is filled later by the coordinator.
"""
import pathlib, re, sys, unicodedata, html as _html
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
F = ROOT / "05_output/final"
EVF = ROOT / "04_working/evidence_ATTR.csv"
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
SEASONS = ("aus", "aman", "boro")
SEASON_WORDS = [("aus", r"আউশ|আউস|Aus\b|AUS\b"), ("aman", r"আমন|Aman\b|AMAN\b"), ("boro", r"বোরো|বোর\b|Boro\b|BORO\b")]
NUM = r"\d+(?:\.\d+)?"
RNG = rf"{NUM}(?:\s*[-–—]\s*{NUM})?"
EVCOLS = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file", "page",
          "locator", "method", "validation", "confidence", "notes"]

# ---------------------------------------------------------------- columns written by add()
GROUPS = [
    ("variety_type", ["variety_type"]),
    ("germplasm_origin", ["germplasm_origin"]),
    ("yield_potential", [f"yield_potential_{s}_t_ha" for s in SEASONS]),
    ("on_farm_yield", [f"on_farm_yield_{s}_t_ha" for s in SEASONS]),
    ("duration", [f"duration_{s}_days" for s in SEASONS]),
    ("plant_height", [f"plant_height_{s}_cm" for s in SEASONS]),
    ("grain", ["grain_type", "grain_length_mm", "grain_breadth_mm", "lb_ratio", "grain_size_text", "aleurone_colour"]),
    ("grain_quality", ["amylose_pct", "protein_pct", "zinc_mg_kg", "iron_mg_kg", "glycemic_index"]),
    ("target_ecosystem", ["target_ecosystem"]),
    ("first_year_of_adoption", ["first_year_of_adoption"]),
    ("cgiar_projects", ["cgiar_projects"]),
    ("dissemination_notes", ["dissemination_notes"]),
]
NEW_COLS = [c for g, cols in GROUPS for c in cols + [f"{g}_source"]]
AGRO = {c for g, cols in GROUPS if g in ("yield_potential", "on_farm_yield", "duration", "plant_height") for c in cols}
ORDER_AGRO = {"official": 1, "adc": 2, "profile": 3, "bina": 4, "nsb": 5}
ORDER_CHEM = {"official": 1, "nsb": 2, "adc": 3, "profile": 4, "bina": 5}


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def a(s):
    """Bangla digits to ASCII, Unicode NFC, unify dashes and the Bangla colon used as a period."""
    return re.sub(r"[–—]", "-", nfc(s).translate(BN))


def rng(s):
    return re.sub(r"\s*-\s*", "-", s.strip())


def seasons_in(text):
    t = a(text)
    return [s for s, p in SEASON_WORDS if re.search(p, t)]


def labelled(text, unit_re=""):
    """'130-135 (আউশ) 170-175 (বোরো)' or 'বোরো মওসুমে ১৪০ দিন' -> [(season, value)]."""
    t = a(text); out = []
    for m in re.finditer(rf"({RNG})\s*{unit_re}\s*\(([^)]*)\)", t):
        ss = seasons_in(m.group(2))
        if len(ss) == 1: out.append((ss[0], rng(m.group(1))))
    for m in re.finditer(rf"(আউশ|আমন|বোরো)\s*(?:মওসুমে|মৌসুমে|মওসুম|মৌসুম)[^\d।;]{{0,40}}?({RNG})", t):
        out.append((seasons_in(m.group(1))[0], rng(m.group(2))))
    return list(dict.fromkeys(out))


def plain_numbers(text, lo, hi):
    t = a(text)
    vals = [rng(m.group(0)) for m in re.finditer(RNG, t)]
    return [v for v in vals if all(lo <= float(x) <= hi for x in v.split("-"))]


# ---------------------------------------------------------------- grain and chemistry phrases
GRAIN_START = r"(?:চালের আকার আকৃতি|চালের আকার|চাল|দানা|ধানের দানা|grain|Grain)"
SIZE_W = r"লম্বা|লম্বাটে|চিকন|সরু|মোটা|মাঝারি|মাঝারী|মধ্যম|খাটো|ছোট|গোল|long|slender|bold|medium|short|fine|coarse"


def grain_phrase(text):
    t = nfc(text)
    for m in re.finditer(rf"{GRAIN_START}[^।;|•\n]{{0,70}}", t):
        ph = m.group(0).strip(" ,.")
        if re.search(SIZE_W, ph) and not re.match(r"দানার?\s*(?:ওজন|রং|রঙ)", ph.split(" ", 1)[-1]):
            return ph
    return ""


def grain_class(ph):
    if not ph: return ""
    p = ph.lower()
    length = ("medium" if re.search(r"মাঝারি লম্বা|মাঝারী লম্বা|medium long", p) else
              "long" if re.search(r"লম্বা|লম্বাটে|\blong", p) else
              "medium" if re.search(r"মাঝারি|মাঝারী|মধ্যম|medium", p) else
              "short" if re.search(r"খাটো|ছোট|গোল|short|round", p) else "")
    shape = ("slender" if re.search(r"চিকন|সরু|slender|fine", p) else
             "bold" if re.search(r"মোটা|bold|coarse|গোল|round", p) else "")
    if length and shape: return f"{length} {shape}"
    if shape: return f"{shape} (length not stated)"
    if length: return f"{length} (shape not stated)"
    return ""


def colour(ph_or_text):
    t = nfc(ph_or_text)
    m = re.search(r"চাল[^।;|•]{0,40}", t)
    seg = m.group(0) if m else ""
    seg = re.sub(r"পেটে\s*সাদা\s*দাগ|সাদা\s*দাগ", "", seg)
    if re.search(r"লাল", seg): return "red"
    if re.search(r"বাদামী|বাদামি", seg): return "brown"
    if re.search(r"সাদা", seg): return "white"
    return ""


CHEM = {
    "amylose_pct": (r"(?:অ্যামাইলোজ|অ্যামাইলোজের|এ্যামাইলোজ|এমাইলোজ|আমাইলোজ|amylose)[^\d%]{0,25}?(" + RNG + r")\s*(?:%|শতাংশ|ভাগ)", 5, 35),
    "protein_pct": (r"(?:প্রোটিন|প্রোটিনের|protein)[^\d%]{0,25}?(" + RNG + r")\s*(?:%|শতাংশ|ভাগ)", 4, 15),
    "zinc_mg_kg": (r"(?:জিংক|জিঙ্ক|জিংকের|দস্তা|zinc)[^\d]{0,25}?(" + RNG + r")\s*(?:মি\.?\s*গ্রা|মিলিগ্রাম|mg|পিপিএম|ppm)", 5, 60),
    "iron_mg_kg": (r"(?:আয়রন|আয়রণ|লৌহ|iron)[^\d]{0,25}?(" + RNG + r")\s*(?:মি\.?\s*গ্রা|মিলিগ্রাম|mg|পিপিএম|ppm)", 2, 60),
    "glycemic_index": (r"(?:গ্লাইসেমিক|গ্লাইসিমিক|glycemic|জিআই)[^\d]{0,30}?(" + RNG + ")", 20, 100),
    "grain_length_mm": (r"চালের\s*দৈর্ঘ্য\s*(?:প্রায়\s*)?(" + NUM + r")\s*(?:মি\.?\s*মি|মিলিমিটার|mm)", 3, 12),
    "grain_breadth_mm": (r"চালের\s*প্রস্থ\s*(?:প্রায়\s*)?(" + NUM + r")\s*(?:মি\.?\s*মি|মিলিমিটার|mm)", 1, 4),
    "lb_ratio": (r"(?:দৈর্ঘ্য\s*(?:ও|-|:)?\s*প্রস্থের\s*অনুপাত|দৈর্ঘ্য-প্রস্থ অনুপাত|L\s*/\s*B(?:\s*ratio)?)[^\d]{0,12}(" + NUM + ")", 1.5, 5),
}
HEIGHT = rf"(?:গাছ(?:ের)?\s*(?:এর\s*)?(?:গড়\s*)?(?:লম্বায়|উচ্চতা|দৈর্ঘ্য)|উচ্চতা|গাছ\s*লম্বা)[^\d]{{0,25}}?({RNG})\s*(?:সে\.?\s*:?\s*মি|সেন্টিমিটার|সেমি|cm)"


def chem_values(text):
    t = a(text).replace("সে:মি:", "সে.মি.")
    out = []
    for f, (pat, lo, hi) in CHEM.items():
        for m in re.finditer(pat, t, flags=re.I):
            v = rng(m.group(1))
            if all(lo <= float(x) <= hi for x in v.split("-")):
                out.append((f, v, m.group(0)[:120])); break
    return out


def heights(text):
    t = a(text).replace("সে:মি:", "সে.মি.")
    return [(rng(m.group(1)), m.group(0)[:120]) for m in re.finditer(HEIGHT, t)
            if all(50 <= float(x) <= 220 for x in rng(m.group(1)).split("-"))]


ORIGIN_EN = [("চায়না", "China"), ("চীন", "China"), ("ভারত", "India"), ("বাংলাদেশ", "Bangladesh"), ("ফিলিপাইন", "Philippines"),
             ("পাকিস্তান", "Pakistan"), ("থাইল্যান্ড", "Thailand"), ("ভিয়েতনাম", "Vietnam"), ("নিজস্ব", "own development"),
             ("ব্রি", "BRRI"), ("ইরি", "IRRI")]


def gloss(v):
    """English gloss in front of the printed origin, e.g. 'China (চীন)'; the printed text is always kept."""
    v = nfc(v)
    if re.search(r"[A-Za-z]", v): return v
    en = [e for b, e in ORIGIN_EN if b in v]
    return f"{'; '.join(dict.fromkeys(en))} ({v})" if en else v


# ---------------------------------------------------------------- builders
def _meta():
    ev = pd.read_csv(ROOT / "05_output/evidence_all.csv", dtype=str, keep_default_na=False,
                     usecols=["pilot_key", "field", "source_id", "source_title", "authority_rank", "local_file", "locator"])
    ev["local_file"] = ev.local_file.str.replace("\\", "/", regex=False)
    m = ev.drop_duplicates("local_file").set_index("local_file")
    return ev, m


def build():
    ev, META = _meta()
    rows = []

    def add_row(cls, key, field, value, raw, lf, page, loc, method, val, conf="high", notes=""):
        lf = lf.replace("\\", "/")
        sid, st, ar = (META.loc[lf, ["source_id", "source_title", "authority_rank"]] if lf in META.index else ("", "", ""))
        rows.append(dict(pilot_key=key, field=field, value=value, value_raw=nfc(raw)[:300], source_id=sid, source_title=st,
                         authority_rank=ar, local_file=lf, page=str(page), locator=loc, method=method, validation=val,
                         confidence=conf, notes=(f"E2 attributes ({cls}). " + notes).strip()))

    def season_fields(cls, key, base, unit_cols, text, single_season, lf, page, loc, method, val, lo, hi, unit_re=""):
        lab = labelled(text, unit_re)
        if lab:
            for s, v in lab:
                if all(lo <= float(x) <= hi for x in v.split("-")):
                    add_row(cls, key, unit_cols[s], v, text, lf, page, loc, method, val, notes="season label printed next to the value")
            return
        vals = plain_numbers(re.sub(r"\([^)]*\)", "", a(text)), lo, hi)
        if not vals: return
        if single_season and len(vals) == 1:
            add_row(cls, key, unit_cols[single_season], vals[0], text, lf, page, loc, method, val,
                    notes="season from the season cell of the same source row")
        else:
            add_row(cls, key, f"{base}_unseasoned", "; ".join(vals), text, lf, page, loc, method, val,
                    conf="medium", notes="no season attributable in the source row; not used in the register")

    def cols(base, unit):
        return {s: f"{base}_{s}_{unit}" for s in SEASONS}

    def text_attrs(cls, key, text, lf, page, loc, method, val, single_season=None, grain=True):
        if not text.strip(): return
        if grain:
            ph = grain_phrase(text)
            if ph:
                add_row(cls, key, "grain_size_text", ph, text, lf, page, loc, method, val)
                gc = grain_class(ph)
                if gc: add_row(cls, key, "grain_type", gc, ph, lf, page, loc, method, val, notes="English class of the printed phrase")
            c = colour(text)
            if c: add_row(cls, key, "aleurone_colour", c, text, lf, page, loc, method, val, conf="medium",
                          notes="colour of the milled grain as stated")
        for f, v, raw in chem_values(text):
            add_row(cls, key, f, v, raw, lf, page, loc, method, val)
        for v, raw in heights(text):
            if single_season:
                add_row(cls, key, f"plant_height_{single_season}_cm", v, raw, lf, page, loc, method, val,
                        notes="season from the season statement of the same source row")
            else:
                add_row(cls, key, "plant_height_unseasoned_cm", v, raw, lf, page, loc, method, val, conf="medium",
                        notes="no single season in the source row; not used in the register")

    # 1 official lists ---------------------------------------------------------
    o = pd.read_csv(F / "bgd_official_list_rows_full.csv", dtype=str, keep_default_na=False)
    o = o[o.variety_id.ne("")]
    for (lid, pg, rn, vid), g in o.groupby(["list_id", "page", "row_no", "variety_id"], sort=False):
        key = vid[5:]; lf = g.source_file.iloc[0]
        cell = lambda k: " ".join((g.loc[g.column_kind.eq(k), "cell_value_normalised"].where(lambda s: s.ne(""),
                                   g.loc[g.column_kind.eq(k), "cell_text_verbatim"])).tolist())
        loc_of = lambda k: "; ".join(g.loc[g.column_kind.eq(k), "locator"].tolist()) or f"{lid} p.{pg} row {rn}"
        ss = seasons_in(cell("season") + " " + cell("remarks"))
        single = ss[0] if len(ss) == 1 else None
        method = "visual_check"; val = "visual_check"
        loc = lambda k: f"{lid}, row {rn}, column {k}; crop {loc_of(k)}"
        y = cell("yield")
        if y and not re.search(r"একর|acre", y):
            season_fields("official list", key, "yield_potential", cols("yield_potential", "t_ha"), y, single, lf, pg, loc("yield"), method, val, 1.5, 16)
        d = cell("duration")
        if d: season_fields("official list", key, "duration", cols("duration", "days"), d, single, lf, pg, loc("duration"), method, val, 60, 220)
        tr = (cell("identifying_traits") + " । " + cell("special_traits")).strip(" ।")
        text_attrs("official list", key, tr, lf, pg, loc("traits"), method, val, single)
        org = cell("origin")
        if org.strip() and org.strip() not in ("-", "ঐ"):
            add_row("official list", key, "germplasm_origin", gloss(org.strip()), org, lf, pg, loc("origin"), method, val, conf="medium",
                    notes="origin cell as printed (hybrid lists: country of origin)")

    # 2 NSB decisions ----------------------------------------------------------
    d = pd.read_csv(F / "bgd_nsb_decisions_full.csv", dtype=str, keep_default_na=False)
    d = d[d.variety_id.ne("")]
    for _, r in d.iterrows():
        key = r.variety_id[5:]; lf = r.source_file; pg = r.pages
        loc = f"NSB {r.meeting_no} ({r.meeting_date}), {r.agenda_item}, decision {r.dec_id}"
        meth = "pdf_text" if r.text_source == "text_layer" else "ocr"
        ss = seasons_in(r.season); single = ss[0] if len(ss) == 1 else None
        for f in ["amylose_pct", "protein_pct", "zinc_mg_kg", "iron_mg_kg", "lb_ratio"]:
            v = r[f].strip()
            if v and re.match(r"^[<>]?\s*\d", v):
                v2 = re.match(rf"^([<>]?\s*{RNG})", a(v)).group(1).replace(" ", "")
                add_row("NSB decision", key, f, v2, v, lf, pg, loc + f", column {f}", "visual_check" if r.get("val_" + f) == "visual_check" else meth,
                        r.get("val_" + f) or "unvalidated", notes=("value with qualifier: " + v) if v2 != v else "")
        if r.grain_type.strip():
            gt = nfc(r.grain_type.strip())
            add_row("NSB decision", key, "grain_size_text", gt, gt, lf, pg, loc + ", grain type", meth, "unvalidated")
            gc = grain_class("চাল " + gt)
            if gc: add_row("NSB decision", key, "grain_type", gc, gt, lf, pg, loc + ", grain type", meth, "unvalidated",
                           notes="English class of the printed phrase")
        for f, base, unit, lo, hi in [("yield_t_ha", "yield_potential", "t_ha", 1.5, 16), ("duration_days", "duration", "days", 60, 220)]:
            v = r[f].strip()
            if not v: continue
            note = "Board trial mean (VCU/field evaluation) for the season of the decision"
            vv = plain_numbers(v, lo, hi)
            if single and len(vv) == 1:
                add_row("NSB decision", key, f"{base}_{single}_{unit}", vv[0], v, lf, pg, loc + f", column {f}",
                        "visual_check" if r.get("val_" + f) == "visual_check" else meth, r.get("val_" + f) or "unvalidated", notes=note)
            elif vv:
                add_row("NSB decision", key, f"{base}_unseasoned", "; ".join(vv), v, lf, pg, loc, meth, "unvalidated", conf="medium",
                        notes=note + "; season not single, not used")
        seg = " । ".join([r.variety_segment_verbatim, r.special_traits_official, r.identifying_traits_official])
        text_attrs("NSB decision", key, seg, lf, pg, loc + ", variety passage", meth, "unvalidated", single, grain=False)
        if r.germplasm_source.strip():
            add_row("NSB decision", key, "germplasm_origin", gloss(nfc(r.germplasm_source.strip())), r.germplasm_source, lf, pg,
                    loc + ", germplasm source", meth, "unvalidated", conf="medium")

    # 3 BRRI ADC 2025 Table 2 --------------------------------------------------
    t = pd.read_csv(ROOT / "03_extracted/tables/adc2025_table2.csv", dtype=str, keep_default_na=False)
    lf = "02_raw/brri/brri_adhunik_dhaner_chash_2025_adc2025.pdf"
    for _, r in t.iterrows():
        if not r.key: continue
        ss = [seasons_in(x) for x in r.season_bn.split(";")]
        loc = f"Table 2 (সারণী ২), row {nfc(r.variety_bn)}"
        for col, base, unit, lo, hi in [("height_cm", "plant_height", "cm", 50, 220), ("duration_days", "duration", "days", 60, 220),
                                        ("yield_t_ha", "yield_potential", "t_ha", 1.5, 16)]:
            parts = [p.strip() for p in r[col].split(";")]
            if len(parts) == len(ss):
                for s, p in zip(ss, parts):
                    if len(s) == 1 and re.fullmatch(RNG, rng(a(p))) and all(lo <= float(x) <= hi for x in rng(a(p)).split("-")):
                        add_row("ADC 2025", r.key, f"{base}_{s[0]}_{unit}", rng(a(p)), f"{r.season_bn} | {r[col]}", lf, r.pdf_page,
                                loc + f", col {col}", "bijoy2unicode", "unvalidated", notes="season from the মওসুম column of the same row")
            elif r[col].strip():
                add_row("ADC 2025", r.key, f"{base}_unseasoned", r[col], f"{r.season_bn} | {r[col]}", lf, r.pdf_page, loc,
                        "bijoy2unicode", "unvalidated", conf="medium", notes="season and value counts differ; not used")
        single = ss[0][0] if len(ss) == 1 and len(ss[0]) == 1 else None
        text_attrs("ADC 2025", r.key, r.traits_bn, lf, r.pdf_page, loc + ", col জাতের বৈশিষ্ট্য", "bijoy2unicode", "unvalidated", single)

    # 4 BRRI Rice Profile ------------------------------------------------------
    p = pd.read_csv(ROOT / "03_extracted/tables/brri_riceprofile.csv", dtype=str, keep_default_na=False)
    rk = ev[ev.local_file.str.contains("brri_riceprofile/variety_")].groupby("local_file").pilot_key.agg(lambda s: s.mode().iloc[0])
    for _, r in p.iterrows():
        lfp = r.local_file.replace("\\", "/"); key = rk.get(lfp, "")
        if not key: continue
        ss = seasons_in(r.season); single = ss[0] if len(ss) == 1 else None
        loc = f"riceprofile.brri.gov.bd/varieties/{r.rp_id}"
        season_fields("Rice Profile", key, "duration", cols("duration", "days"), r.duration, single, lfp, "", loc + ", জীবনকাল", "html", "unvalidated", 60, 220)
        if not re.search(r"একর", r["yield"]):
            season_fields("Rice Profile", key, "yield_potential", cols("yield_potential", "t_ha"), r["yield"], single, lfp, "", loc + ", ফলন",
                          "html", "unvalidated", 1.5, 16)
        text_attrs("Rice Profile", key, r.traits + " । " + r.special, lfp, "", loc + ", বৈশিষ্ট্য", "html", "unvalidated", single)

    # 5 BINA per-variety pages ---------------------------------------------------
    for fp in sorted((ROOT / "02_raw/bina/varieties").glob("*.html")):
        key = fp.stem
        raw = fp.read_text(encoding="utf-8", errors="ignore")
        raw = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
        tx = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", raw)))
        m = re.search(r"জাতের বৈশিষ্ট্য\s*ঃ?:?(.*?)(?:জমি তৈরী|জমি তৈরি|বপণের সময়|বপনের সময়|সার ও প্রয়োগ|$)", tx)
        if not m: continue
        body = m.group(1)[:2500]
        lfb = "02_raw/bina/varieties/" + fp.name
        ss = seasons_in(body); single = ss[0] if len(ss) == 1 else None
        loc = "bina.gov.bd variety page, section জাতের বৈশিষ্ট্য"
        dur = re.search(rf"জীবনকাল[^\d]{{0,20}}({RNG})\s*দিন", a(body))
        if dur and single:
            add_row("BINA page", key, f"duration_{single}_days", rng(dur.group(1)), dur.group(0), lfb, "", loc, "html", "unvalidated",
                    notes="season from the only season named in the section")
        yl = re.search(rf"ফলন[^\d।]{{0,40}}({RNG})\s*(?:মে\.?\s*)?টন", a(body))
        if yl and single and not re.search(r"একর", yl.group(0)):
            add_row("BINA page", key, f"yield_potential_{single}_t_ha", rng(yl.group(1)), yl.group(0), lfb, "", loc, "html", "unvalidated",
                    notes="season from the only season named in the section")
        text_attrs("BINA page", key, body, lfb, "", loc, "html", "unvalidated", single)

    # 6 BINA 'at a glance' table (season / yield / duration split by '/') --------
    lfg = "02_raw/bina/bina_at_a_glance_varieties.html"
    g = pd.read_html(ROOT / lfg)[0].fillna("")
    gk = ev[ev.local_file.eq(lfg) & ev.field.eq("official_name_bn")][["pilot_key", "locator"]].drop_duplicates()
    for key, loc0 in gk.itertuples(index=False):
        mrow = re.match(r"table row (\d+)", loc0)
        if not mrow: continue
        i = int(mrow.group(1)) - 1
        if i >= len(g): continue
        r = g.iloc[i]
        ss = [seasons_in(x) for x in str(r[3]).split("/")]
        loc = f"table row {i + 1} {nfc(str(r[1]))}"
        for col, base, unit, lo, hi in [(4, "yield_potential", "t_ha", 1.5, 16), (5, "duration", "days", 60, 220)]:
            parts = str(r[col]).split("/")
            if len(parts) == len(ss):
                for s, p in zip(ss, parts):
                    v = rng(a(p))
                    if len(s) == 1 and re.fullmatch(RNG, v) and all(lo <= float(x) <= hi for x in v.split("-")):
                        add_row("BINA page", key, f"{base}_{s[0]}_{unit}", v, f"{r[3]} | {r[col]}", lfg, "", loc + f", col {col}",
                                "html", "unvalidated", notes="BINA 'at a glance' table; season from the মৌসুম column of the same row")
            elif str(r[col]).strip():
                add_row("BINA page", key, f"{base}_unseasoned", nfc(str(r[col])), f"{r[3]} | {r[col]}", lfg, "", loc, "html",
                        "unvalidated", conf="medium", notes="BINA 'at a glance' table; season and value counts differ; not used")
        single = ss[0][0] if len(ss) == 1 and len(ss[0]) == 1 else None
        text_attrs("BINA page", key, str(r[6]), lfg, "", loc + ", col বিশেষ বৈশিষ্ট্য", "html", "unvalidated", single)

    out = pd.DataFrame(rows, columns=EVCOLS).drop_duplicates(["pilot_key", "field", "value", "local_file", "page", "locator"])
    # only varieties of the register (a key outside it would create a new row in assemble.py)
    reg = set(pd.read_csv(F / "bgd_rice_varieties.csv", dtype=str, usecols=["variety_id"]).variety_id.str[5:])
    out = out[out.pilot_key.isin(reg)]
    # two independent files agreeing on the same reading -> two_source
    nfile = out.groupby(["pilot_key", "field", "value"]).local_file.transform("nunique")
    out.loc[(nfile >= 2) & out.validation.eq("unvalidated"), "validation"] = "two_source"
    out.to_csv(EVF, index=False, encoding="utf-8-sig")
    print(f"wrote {EVF.relative_to(ROOT)}: {len(out)} rows, {out.pilot_key.nunique()} varieties")
    print(out.field.value_counts().to_string())
    return out


# ---------------------------------------------------------------- add()
def _cls(notes):
    m = re.match(r"E2 attributes \(([^)]+)\)", notes)
    return {"official list": "official", "NSB decision": "nsb", "ADC 2025": "adc", "Rice Profile": "profile",
            "BINA page": "bina"}.get(m.group(1) if m else "", "zz")


def _src(r):
    p = f", p. {r.page}" if r.page else ""
    return f"{r.local_file}{p} ({r.locator})"


def add(df):
    """Append the attribute columns; df is the register as an all-string DataFrame. Returns a copy."""
    df = df.copy()
    for c in NEW_COLS:
        df[c] = ""
    if not EVF.exists():
        return df
    e = pd.read_csv(EVF, dtype=str, keep_default_na=False)
    e = e[~e.field.str.contains("unseasoned")]
    e["cls"] = e.notes.map(_cls)
    e["vw"] = e.validation.map({"visual_check": 0, "two_source": 0, "key_check": 1}).fillna(2)
    e["vid"] = "RICE-" + e.pilot_key
    best, chosen_gt = {}, {}
    for (vid, f), g in e.groupby(["vid", "field"]):
        order = ORDER_AGRO if f in AGRO else ORDER_CHEM
        if f == "grain_type" and (~g.value.str.contains("not stated")).any():   # a complete class beats a partial one
            g = g[~g.value.str.contains("not stated")]
        g = g.assign(o=g.cls.map(order).fillna(9)).sort_values(["o", "vw"], kind="stable")
        top = g[g.o.eq(g.o.iloc[0])]
        v = top.value.mode().iloc[0] if top.value.nunique() > 1 else top.value.iloc[0]
        w = top[top.value.eq(v)].iloc[0]
        others = sorted(set(g.value) - {v})
        best[(vid, f)] = (v, _src(w) + (f"; other readings: {', '.join(others[:4])}" if others else ""))
        if f == "grain_type":
            chosen_gt[vid] = (w.local_file, w.locator)
    # the printed grain phrase comes from the same source reading as the grain class
    gs = e[e.field.eq("grain_size_text")]
    for vid, (lf, loc) in chosen_gt.items():
        m = gs[gs.vid.eq(vid) & gs.local_file.eq(lf) & gs.locator.eq(loc)]
        if len(m):
            best[(vid, "grain_size_text")] = (m.value.iloc[0], _src(m.iloc[0]))
    idx = dict(zip(df.variety_id, df.index))
    for (vid, f), (v, s) in best.items():
        if vid in idx and f in df.columns:
            df.at[idx[vid], f] = v
    # register columns that already carry the information
    hyb = df.get("rice_type", pd.Series("", index=df.index)).eq("hybrid")
    vt = df.variety_type.where(df.variety_type.ne(""), df["type"].str.lower())
    df["variety_type"] = vt.where(~hyb, "hybrid")
    if "origin_statement" in df:
        go = df.germplasm_origin
        df["germplasm_origin"] = go.where(go.ne(""), df.origin_statement).where(lambda s: s.ne(""), df.get("origin_country", ""))
    if "ecosystem_std" in df:
        df["target_ecosystem"] = df.ecosystem_std
    # sources per group
    for g, cols in GROUPS:
        def srcs(row, cols=cols, g=g):
            parts = []
            for c in cols:
                if not row[c]: continue
                if (row.variety_id, c) in best and best[(row.variety_id, c)][0] == row[c]:
                    parts.append(f"{c}: {best[(row.variety_id, c)][1]}")
                elif c == "variety_type":
                    parts.append("variety_type: register column type (rice_type)")
                elif c == "germplasm_origin":
                    parts.append("germplasm_origin: register column origin_statement or origin_country")
                elif c == "target_ecosystem":
                    parts.append("target_ecosystem: register column ecosystem_std (derive_covariates)")
            return " | ".join(parts)
        df[f"{g}_source"] = df.apply(srcs, axis=1)
    return df


if __name__ == "__main__":
    if "--build" in sys.argv:
        build()
    else:
        r = pd.read_csv(F / "bgd_rice_varieties.csv", dtype=str, keep_default_na=False)
        x = add(r)
        print(pd.DataFrame({t: x[x.rice_type.eq(t)][[c for c in NEW_COLS if not c.endswith("_source")]].ne("").mean().round(2)
                            for t in ("inbred", "hybrid")}).to_string())
