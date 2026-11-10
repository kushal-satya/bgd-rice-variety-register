"""Assemble main tables from long-format evidence (04_working/evidence_*.csv).

Rules (crawl_plan.md section 3; decisions_log incl. "PI decisions after the pilot"):
- A value is ELIGIBLE if it came from a text method (html, pdf_text, bijoy2unicode, api_json,
  xlsx) or its validation is two_source / key_check / visual_check. Unvalidated OCR never enters.
- The winner per (key, field) follows a field-specific authority-rank order, then validation
  strength, then confidence. Every distinct eligible value goes to conflicts.csv, and the main
  row carries a short `conflict_note`.
- cgiar_role = strongest documented link among eligible rows (1 > 2 > 3 > 4; 5 only if nothing
  else). `cgiar_lineage` lists every documented link (e.g. "IRRI grandparent: ..."). SPIA T27
  flags stay in `cgiar_spia_flags`.
- gazette_date = earliest gazette; later gazettes are listed in conflict_note.
- breeding_line prefers a coded designation; descriptive labels go to `aliases`.
- Fish germplasm transfers, introductions and planned generations go to fish_events.csv.
- Rows with no official (rank 1-2) evidence are flagged institute_claim_only.
- Rows lacking source_url or local_file go to failures.csv; UNMATCHED evidence goes to
  04_working/unmatched_names.csv for resolution.

    python scripts/assemble.py --stage pilot   # 05_output/*_pilot.csv
    python scripts/assemble.py --stage full    # 05_output/*.csv
"""
import argparse, glob, pathlib, re, sys
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPH_END = re.compile(r"([ক-হড়ঢ়য়])র্(?=[\s,।)\]]|$)")


def fix_reph(v):
    """bijoy2unicode sometimes puts the reph (র্) after the consonant it belongs before; a word-final reph is never
    valid Bangla, so move it before that consonant: 'ফামর্' -> 'ফার্ম'."""
    return REPH_END.sub(lambda m: "র্" + m.group(1), v) if isinstance(v, str) and "র্" in v else v


def no_reph(v):
    return str(v).replace("র্", "")


ap = argparse.ArgumentParser(); ap.add_argument("--stage", default="pilot"); a = ap.parse_args()
SUF = "_pilot" if a.stage == "pilot" else ""
OUT = ROOT / "05_output"

files = [f for f in glob.glob(str(ROOT / "04_working/evidence_*.csv"))
         if not re.search(r"evidence_(corrections|attendance)", f)]   # corrections are read below; attendance is personal data, never evidence
if a.stage == "pilot":
    files = [f for f in files if re.search(r"evidence_(P2|COORD)", f)]
ev = pd.concat([pd.read_csv(p, dtype=str, keep_default_na=False).assign(agent=pathlib.Path(p).stem.split("_", 1)[1])
                for p in files], ignore_index=True)
ev.columns = [c.strip() for c in ev.columns]
for c in ["value", "value_raw", "notes", "locator", "page", "validation", "method", "confidence", "authority_rank"]:
    if c not in ev: ev[c] = ""
    ev[c] = ev[c].fillna("")
ev = ev[~((ev.pilot_key == "IRRI_DIRECT") & ev.value.str.startswith("candidates"))]
COR = pd.concat([pd.read_csv(f, dtype=str).fillna("") for f in glob.glob(str(ROOT / "04_working/evidence_corrections*.csv"))])
if "new_value" not in COR: COR["new_value"] = ""
for c in COR.itertuples():
    # a correction written by a reviewer (agent REV*) applies to the value whichever extraction agent recorded it
    by_agent = (ev.agent == c.agent) | c.agent.startswith("REV")
    m = by_agent & (ev.pilot_key == c.pilot_key) & (ev.field == c.field) & (ev.value == c.value)
    if c.action == "replace" and c.value == "" and not m.any():
        # a reviewer adds a value no source row carried; the reason (with file and page) is kept in notes
        ev = pd.concat([ev, pd.DataFrame([{"pilot_key": c.pilot_key, "field": c.field, "value": c.new_value, "agent": c.agent,
                                           "method": "review", "validation": "visual_check", "authority_rank": "7_reviewer_synthesis",
                                           "notes": "[reviewer addition: " + c.reason + "]"}])], ignore_index=True).fillna("")
        continue
    if c.action == "drop":
        ev = ev[~m]
    elif c.action == "replace":
        ev.loc[m, "value"] = c.new_value
        ev.loc[m, "notes"] = ev.loc[m, "notes"] + " [coordinator correction: " + c.reason + "]"
    elif c.action == "refield":
        ev.loc[m, "field"] = c.new_field
        ev.loc[m, "notes"] = ev.loc[m, "notes"] + " [coordinator correction: " + c.reason + "]"
REMAP = pd.read_csv(ROOT / "04_working/key_remap.csv", dtype=str).set_index("old_key")["new_key"].to_dict()
ev["pilot_key"] = ev["pilot_key"].replace(REMAP)
ev.loc[(ev.field == "cgiar_role") & ev.value.str.startswith("spia_"), "field"] = "cgiar_spia_flags"
# REV2 (v1.2): the NSB 'yield advantage' value is the registration criterion met (e.g. 20% over the check), not a measured gain
ev.loc[ev.field.eq("yield_advantage_pct"), "field"] = "yield_criterion_pct"
# F6G: gazette dates quoted in NSB minutes are reports, not gazette copies; keep them out of gazette_date
_f6 = ev.agent.eq("F6G")
ev.loc[_f6 & ev.field.eq("gazette_date"), "field"] = "gazette_date_reported"
ev.loc[_f6 & ev.field.eq("gazette_reference"), "field"] = "gazette_status_note"
ev["rank"] = ev["authority_rank"].str.extract(r"^(\d)")[0].fillna("9").astype(int)
TEXT_METHODS = {"html", "pdf_text", "bijoy2unicode", "api_json", "xlsx"}
VAL_W = {"two_source": 0, "key_check": 1, "visual_check": 1}
ev.loc[ev.method.eq("bijoy2unicode"), "value"] = ev.loc[ev.method.eq("bijoy2unicode"), "value"].map(fix_reph)
# REV4 (E1, round-3 error sweep): OCR / Bijoy garble in identity fields is corrected where the reading is unambiguous and
# otherwise rejected (made ineligible), and line codes printed in Bangla script are transliterated before they compete.
BN_CH = re.compile(r"[ঀ-৿]")
BN_LET = r"[ঀ-০৲-৿]"                          # Bangla letters and signs (not the digits ০-৯)
BN_DIG = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
# fixed Bijoy artefacts seen in the archive (applied to the identity fields only): 've' is the Bijoy key sequence for 'াব' (NSB 72: স্বর্ণা সাব-১ read as 'স্বর্ণা সve-১');
# 'বর্যাক' is ব্র্যাক with the first hasanta lost in conversion (BRAC in NSB 64-75)
GARBLE_FIX = {"সve": "সাব", "বর্যাক": "ব্র্যাক",
              "ণড়ঁ": "You", "(ছ ১০৮)": "(Q 108)"}   # Latin typed in a Bijoy font: China King-2 'LE You5178', Nafco-108 'Q 108' (NSB 59-75)
IDF = ["breeding_line", "pedigree", "official_name_en", "official_name_bn", "popular_name", "aliases", "hybrid_parent_female",
       "hybrid_parent_male", "developer", "trial_codes", "station_no", "check_variety", "approval_reference"]


def degarble(v):
    """Return (value, status): status 'ok', 'fixed' (unambiguous repair) or 'garbled' (Latin letters inside a Bangla word)."""
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f�]", "", str(v))
    for a, b in GARBLE_FIX.items():
        s = s.replace(a, b)
    # Bangla digits inside a Latin token ('RN-০০১', 'Win-৯০২', 'Shakti৫') are ASCII digits printed in a Bangla font
    s = re.sub(r"[\w\-]*[A-Za-z][\w\-]*", lambda m: m.group(0).translate(BN_DIG), s)
    s = re.sub(r"(?<=[0-9])(?=" + BN_LET + r"{2,})", " ", s)        # 'BR7166-4-5-3এবং' -> 'BR7166-4-5-3 এবং'
    bad = (re.search(BN_LET + r"[A-Za-z]|[A-Za-z]" + BN_LET, s)
           or re.search(r"[0-9][০-৯]|[০-৯][0-9]", s)                       # one digit run in two scripts ('1২67423')
           or re.search(r"(?<![A-Za-z0-9])1[1Il][0-9০-৯]{5,}-", s))        # 'IR' read as '11' ('11২78581-12-3-2-2', Rabi dhan-1, NSB 99)
    return s, ("garbled" if bad else ("fixed" if s != v else "ok"))


ev["garbled"] = False
_idf = ev.field.isin(IDF)
_dg = ev.loc[_idf, "value"].map(degarble)
_fixed = _dg.map(lambda t: t[1] == "fixed")
ev.loc[_idf, "value"] = _dg.map(lambda t: t[0])
ev.loc[_fixed[_fixed].index, "notes"] = ev.loc[_fixed[_fixed].index, "notes"] + " [REV4: OCR/Bijoy garble repaired]"
_gb = _dg.map(lambda t: t[1] == "garbled")
ev.loc[_gb[_gb].index, "garbled"] = True
ev.loc[_gb[_gb].index, "notes"] = ev.loc[_gb[_gb].index, "notes"] + " [REV4: rejected, Latin letters inside a Bangla word (OCR garble)]"
BN_LAT = [("টিএনডিবি", "TNDB"), ("বিএআরডিসি", "BARDC"), ("বিআর", "BR"), ("বি আর", "BR"), ("আইআর", "IR"), ("আই আর", "IR"),
          ("বিজি", "BG"), ("বিইউ", "BU"), ("বাউ", "BAU"), ("এইচএইচজেড", "HHZ"), ("এইচআর", "HR"), ("এসসি", "SC"), ("এইচ", "H"),
          ("এস", "S"), ("বি", "B"), ("এ", "A"), ("আর", "R"), ("পি", "P"), ("এল", "L"), ("টি", "T"), ("সি", "C"), ("ডি", "D"),
          ("জি", "G"), ("এম", "M"), ("এন", "N"), ("কে", "K")]


def translit_code(v):
    """A Latin line code printed in Bangla script -> Latin ('বিআর ৫৮৭৭-২১-২-৩' -> 'BR 5877-21-2-3'); None if Bangla words remain."""
    s = str(v).translate(BN_DIG).replace("‌", "").replace("‍", "")
    for a, b in BN_LAT:
        s = s.replace(a, b)
    s = re.sub(r"^([A-Z]{2,4})\s+(?=\d)", r"\1", s.strip())       # 'বিআর ৫৮৭৭' -> BR5877 (the space is typographic)
    return None if BN_CH.search(s) else s


def code_norm(v):
    """Normal form for comparing line codes and pedigrees across sources (script, spacing, hyphens, case, O/0, * backcross marks)."""
    t = translit_code(v)
    s = (t if t is not None else str(v)).replace("*", "").replace("×", "/").replace(" x ", "/").lower()
    # letter and digit runs keep their boundaries, so BR5331-93-28-3 and BR5331-93-2-8-3 stay different while
    # 'IR 63307-4-B-4-3' and 'IR63307-4B-4-3' are the same code; a lone letter O is the digit 0
    return ".".join("0" if t == "o" else t for t in re.findall(r"[a-z]+|[0-9]+|[ঀ-৿]+|/+", s))


def clean_breeding_line(v):
    """Split a breeding_line reading into (code or '', [labels]): 'BR5331-93-28-3|বিআর৫৩৩১-৯৩-২৮-৩' -> code; 'IR-69690 (আইআর-৬৯৬৯০)'
    -> 'IR-69690'; 'Qyou 12 (নাফকো-১১২)' -> 'Qyou 12' + label; 'বিআর ৫৮৭৭-২১-২-৩' -> 'BR 5877-21-2-3'; 'স্বর্ণা সাব-১' -> label only."""
    parts, labels = [], []
    for p in (p.strip() for p in str(v).split("|")):
        m = re.fullmatch(r"(.*?)\s*\(([^()]*)\)\s*", p)
        if m and m.group(1) and bool(BN_CH.search(m.group(1))) != bool(BN_CH.search(m.group(2))):
            a, b = (m.group(1), m.group(2)) if not BN_CH.search(m.group(1)) else (m.group(2), m.group(1))
            parts.append(a); labels.append(b)                      # 'IR-69690 (আইআর-৬৯৬৯০)', 'Qyou 12 (নাফকো-১১২)'
        elif p:
            parts.append(p)
    lat = [p for p in parts if not BN_CH.search(p)]
    main = lat[0] if lat else ""
    for p in parts:
        if p in lat:
            continue
        t = translit_code(p)
        if t and re.search(r"[0-9]", t) and re.search(r"[A-Za-z]", t):
            main = main or t
            if code_norm(t) != code_norm(main):
                labels.append(p)
        else:
            labels.append(p)
    labels += [p for p in lat[1:]]
    keep = []
    for x in labels:
        nx = code_norm(x)
        if x and main and (nx in code_norm(main)):
            continue                                                # a Bangla rendering or fragment of the same code
        keep.append(x)
    return main, keep


_bl = ev[ev.field.eq("breeding_line") & ~ev.garbled]
_new = []
for i, r in _bl.iterrows():
    code, labels = clean_breeding_line(r.value)
    if code != r.value:
        if code:
            ev.at[i, "value"] = code
            ev.at[i, "notes"] = r.notes + f" [REV4: breeding_line read as '{r.value}'; code kept, script/labels separated]"
        else:   # a name or prose (e.g. 'স্বর্ণা সাব-১', NSB 72) is never a line code
            ev.at[i, "field"] = "pedigree_note" if re.search(r"নং|সেশন|সারি|বাছাই|নির্বাচন|selection|accession", r.value, re.I) else "aliases"
            ev.at[i, "notes"] = r.notes + " [REV4: not a line code (name or prose); moved out of breeding_line]"
    for lab in labels if code else []:
        _new.append({**r.to_dict(), "field": "aliases", "value": lab, "notes": r.notes + " [REV4: label printed with the line code]"})
if _new:
    ev = pd.concat([ev, pd.DataFrame(_new)], ignore_index=True).fillna("")
    ev["garbled"] = ev["garbled"].astype(bool)
# 'pedigree' values that are not pedigrees: origin statements, SCA trial code numbers, vague notes
_ped = ev.field.eq("pedigree")
_pb = ev.field.isin(["pedigree", "breeding_line"])
_orig = ev.value.str.contains(r"^(origin\b|chinese origin|indian origin|imported|from .*(co\.|ltd|company|seed))", case=False, regex=True)
_trial = ev.value.str.fullmatch(r"\s*(?:[A-Za-z0-9 \-]+;\s*)?(?:H-?\s?\d+\s*[/,]\s*H?-?\s?\d+(?:\s*/\s*H?-?\s?\d+)*)\s*")
_vague = ev.value.str.fullmatch(r"\s*(?:\w+\s)?own development\s*", case=False)
ev.loc[_ped & _orig, "field"] = "origin_statement"
ev.loc[_pb & _trial.fillna(False), "field"] = "trial_codes"
ev.loc[_ped & _vague.fillna(False), "field"] = "pedigree_note"
# hybrids: a 'pedigree' that names no parents (trade name, trait, supplier) is a note, not a pedigree
_hyb = ev.pilot_key.str.startswith("HYB_") | ev.pilot_key.str.contains("HYBRID")
_named = ev.value.str.contains(r"/|\sx\s|×|\bA\b.*\bR\b", regex=True)
ev.loc[ev.field.eq("pedigree") & _hyb & ~_named, "field"] = "pedigree_note"
ev["eligible"] = ev["method"].isin(TEXT_METHODS) | ev["validation"].isin(VAL_W.keys())
ev["eligible"] &= ev["value"].str.strip() != ""
ev["eligible"] &= ~ev["garbled"].astype(bool)          # REV4: garbled readings never enter the register
ev["vw"] = ev["validation"].map(VAL_W).fillna(2)
ev["cw"] = ev["confidence"].map({"high": 0, "medium": 1, "low": 2}).fillna(3)

# fish governance acts (species- and framework-level keys from agent F4) live in bgd_fish_approvals.csv, not here
ev = ev[~ev.pilot_key.str.match(r"^(SPECIES|FRAMEWORK)_")]
unmatched = ev[ev.pilot_key.isin(["UNMATCHED", ""])]
unmatched.to_csv(ROOT / f"04_working/unmatched_names{SUF}.csv", index=False, encoding="utf-8-sig")
ev = ev[~ev.pilot_key.isin(["UNMATCHED", ""])]

man = pd.read_csv(ROOT / "02_raw/manifest.csv", dtype=str, keep_default_na=False)
man["file_path"] = man["file_path"].str.replace("\\", "/", regex=False)
MAN = man.drop_duplicates("file_path").set_index("file_path")

DEFAULT = [1, 2, 3, 4, 5, 6]
ORDER = {
    "official_name_en": [3, 1, 2, 4, 5, 6],
    "breeding_line": [1, 3, 2, 4, 5, 6],
    "pedigree": [1, 3, 2, 4, 5, 6],
    "station_no": [3, 1, 2, 4, 5, 6],
    "popular_name": [3, 2, 1, 4, 5, 6],
    "season": [2, 1, 3, 4, 5, 6],
    "ecosystem": [2, 1, 3, 4, 5, 6],
    "key_traits": [2, 1, 3, 4, 5, 6],
    "cgiar_center": [1, 3, 2, 4, 5, 6],
    "generation": [3, 4, 1, 2, 5, 6],
    "release_date": [1, 2, 4, 3, 5, 6],
}
LISTY = {"origin_statement", "trial_codes", "pedigree_note", "special_traits_official", "identifying_traits_official", "quality_traits", "stress_tolerance", "decision_conditions", "dus_result", "vcu_sites", "doi_key_paper", "key_traits", "aliases", "cgiar_lineage", "cgiar_independent", "adoption", "market_segment", "product_profile", "local_name", "cgiar_evidence", "source_url", "cgiar_spia_flags"}
CODE_RX = re.compile(r"[A-Za-z]{1,6}[\s(]*[A-Za-z]*\)?[\s-]*\d{2,}[\w\-/()* ]*")


PROSE = re.compile(r"selection|irradiat|mutant|collected|introduc|cross|variety|local|rice|from|under|with|seed", re.I)


# mutant-line designations that contain slashes but are not crosses (REV2, A4-05: NERICA-10 / 350 Gy / plant selection)
CODED_LINES = {"N10/350/P-5-4"}


def is_code(v):
    """A breeding-line designation: short, letters+digits, no cross symbol, no prose words (BN-P-318, IR 5-47-2,
    HHZ5-DT20-DT2-DT1, BR-SF(Rang)-PL1-B). Descriptive labels like 'BR11-Sub1' are aliases, not codes."""
    v = str(v).strip()
    if v in CODED_LINES:
        return True
    if not v or len(v) > 45 or len(v.split()) > 4: return False
    if BN_CH.search(v): return False            # REV4: Bangla script is never a line code (its digits matched \d before)
    if not (re.search(r"[0-9]", v) and re.search(r"[A-Za-z]", v)): return False
    if "/" in v or re.search(r"\sx\s|×", v) or PROSE.search(v): return False
    return not re.search(r"sub\d?$", v, re.I)


def is_label(v):
    """Worth keeping as an alias: code-like token that lost the breeding_line slot, or a label such as BR11-Sub1."""
    v = str(v).strip()
    return bool(v) and len(v) <= 45 and bool(re.search(r"\d", v)) and "/" not in v and not PROSE.search(v)


def norm(v):
    return re.sub(r"[\s\-–_.,;:()]+", "", str(v)).lower()


# one resolved date per NSB meeting (04_working/nsb_meeting_key_resolved.csv; conflicting readings settled in 06_validation/identity_fixes_memo.md)
_KEY = pd.read_csv(ROOT / "04_working/nsb_meeting_key_resolved.csv", dtype=str, encoding="utf-8-sig").fillna("")
_KEYD = {m: {d} for m, d in zip(_KEY.meeting_no, _KEY.meeting_date)}


def ref_matches(ref, date):
    """True if an approval_reference names an NSB meeting whose (validated) date equals the chosen approval_date."""
    m = re.search(r"NSB (\d+)", ref)
    return bool(m) and date in _KEYD.get(m.group(1), set())


# REV2 (v1.2, data audit A4-01): numbers measured in the Board's trials come from the decision itself. For these fields the
# order is NSB decision > SCA annual list > gazette notice > compendium and MoA lists > everything else (by authority rank).
# A gazette can copy the check variety's yield (BRRI dhan107: gazette 7.00 = BRRI dhan50; NSB 111 and SCA list 8.19).
TRIAL_NUM = {"yield_t_ha", "duration_days", "yield_criterion_pct"}


def trial_class(sid):
    if re.match(r"NSB_", sid): return 0
    if re.match(r"SCA_FY|SCA_HYB", sid): return 1
    if re.match(r"GA?Z_", sid): return 2
    if re.match(r"SCA|MOA", sid): return 3
    return 4


def family(sid):
    """REV4: independent source families for support counts. NSB minutes and TC records are one body; SCA lists one; MoA lists
    one; gazettes one; BRRI's handbook, fact sheets and Rice Profile one (institute); GloMIP product-catalogue entries are
    supplied by the national programme, so they count with the institute; TRIVSA and SPIA Table 27 (which repeat each
    other's readings, misprints included) one; every other source is its own family."""
    if re.match(r"(NSB|TC)_", sid): return "NSB"
    if re.match(r"SCA", sid): return "SCA"
    if re.match(r"MOA", sid): return "MOA"
    if re.match(r"GA?Z_", sid): return "GAZ"
    if re.match(r"RB-S(0[1-9]|1[0-9]|2[01])$|DS-S07$|L2-S06$", sid): return "INST"
    if sid in ("DS-S01", "DS-S04"): return "TRIVSA_SPIA"
    return sid


# REV4: reasoned choices between eligible readings that support counts cannot settle (file + page evidence in the reason)
_ADJ = pd.read_csv(ROOT / "04_working/adjudications_rev4.csv", dtype=str).fillna("") if (ROOT / "04_working/adjudications_rev4.csv").exists() \
    else pd.DataFrame(columns=["pilot_key", "field", "value", "reason"])
ADJ = {(r.pilot_key, r.field): r.value for r in _ADJ.itertuples()}
SUPPORT_LOG = []


def parents(v):
    return [code_norm(p) for p in re.split(r"\s*(?:/+|\sx\s|×)\s*", str(v)) if p.strip()]


def variant_of(a, b):
    """Two pedigree readings are variants of one pedigree when they name the same number of parents and differ only in
    a few characters (BR24/BR21 vs BR14/BR21; IR515111-... vs IR51511-...)."""
    import difflib
    pa, pb = parents(a), parents(b)
    return len(pa) == len(pb) >= 2 and difflib.SequenceMatcher(None, "/".join(pa), "/".join(pb)).ratio() >= 0.85


def by_support(d, key, field, groupkey):
    """Choose among readings by the number of independent source families behind each normal form; a reading carried by
    the NSB minutes wins ties; then the field's authority order. Logs every choice that overrides the authority order."""
    d = d.copy()
    d["g"] = d["value"].map(groupkey)
    sup = d.groupby("g").source_id.apply(lambda s: len({family(x) for x in s}))
    prim = d.groupby("g")["rank"].min().eq(1)
    d = d.sort_values(["ro", "vw", "cw"])
    pos = {g: i for i, g in reversed(list(enumerate(d.g)))}          # position of each group's best reading in the authority order
    gs = sorted(sup.index, key=lambda g: (-sup[g], -int(prim[g]), pos[g]))
    win = gs[0]
    first = d.iloc[0]
    if first.g != win:
        SUPPORT_LOG.append(dict(key=key, field=field, authority_choice=first.value, support_choice=d[d.g == win].sort_values(["ro", "vw", "cw"]).iloc[0].value,
                                families_authority=sup[first.g], families_support=sup[win]))
    d["gw"] = (d.g != win).astype(int)
    d["tl"] = d.notes.str.contains("REV4: breeding_line read as", regex=False).astype(int)   # show the code as printed in Latin when a source does
    d["sp"] = (d.value.str.contains(r"^[A-Za-z]+\s+\d|--|\s-|-\s")).astype(int)            # and 'BR5877-...' before 'BR 5877-...' or 'B--7'
    return d.sort_values(["gw", "sp", "tl", "ro", "vw", "cw"]).drop(columns=["g", "gw", "tl", "sp"])


def pick(df, field):
    order = ORDER.get(field, DEFAULT)
    d = df[df.eligible].copy()
    if d.empty:
        return None, d
    d["ro"] = d["rank"].map(lambda r: order.index(r) if r in order else 99)
    key = str(df.pilot_key.iloc[0])
    if (key, field) in ADJ:                      # REV4 adjudication (04_working/adjudications_rev4.csv)
        hit = d.value.map(code_norm).eq(code_norm(ADJ[(key, field)]))
        if hit.any():
            d["adj"] = (~hit).astype(int)
            d = d.sort_values(["adj", "ro", "vw", "cw"]).drop(columns="adj"); return d.iloc[0], d
    if field == "breeding_line":
        coded = d[d.value.map(is_code)]
        if len(coded):                           # REV4: coded readings compete by independent support, NSB wins ties
            d = pd.concat([by_support(coded, key, field, code_norm), d[~d.index.isin(coded.index)].sort_values(["ro", "vw", "cw"])])
            return d.iloc[0], d
    if field == "pedigree":
        d = d.sort_values(["ro", "vw", "cw"])
        w = d.iloc[0]
        var = d[d.value.map(lambda v: not BN_CH.search(v) and (code_norm(v) == code_norm(w.value) or variant_of(v, w.value)))]
        if not BN_CH.search(w.value) and var.value.map(code_norm).nunique() > 1:   # REV4: variant readings of one cross compete by independent support
            d = pd.concat([by_support(var, key, field, code_norm), d[~d.index.isin(var.index)]])
        return d.iloc[0], d
    if field == "season" and re.search(r"^HYB_|HYBRID", key):
        # REV4: a hybrid's seasons are those named by its NSB registration decision(s), plus any season that two independent
        # official families (SCA, MoA, gazette) agree on. The MoA 2026 list's row cells and its p.12 seasonal summary
        # disagree with NSB 86 (BADC hybrid dhan3: Boro) and NSB 113 (Bayer hybrid dhan9: Aman).
        off = d[d["rank"] <= 2]
        if (off.source_id.str.match(r"NSB_")).any():
            S = {"Aus": r"aus|আউশ", "Aman": r"aman|আমন", "Boro": r"boro|বোরো"}
            fam = {s: {family(x) for x, v in zip(off.source_id, off.value) if re.search(rx, v, re.I)} for s, rx in S.items()}
            keep = [s for s in ("Boro", "Aus", "Aman") if "NSB" in fam[s] or len(fam[s] - {"NSB"}) >= 2]
            if keep:
                val = "; ".join(keep)
                cur = d.sort_values(["ro", "vw", "cw"]).iloc[0]
                d = d.sort_values(["ro", "vw", "cw"])
                d["mv"] = d.value.map(lambda v: 0 if set(re.findall(r"Aus|Aman|Boro", v.title())) == set(keep) else 1)
                d = d.sort_values(["mv", "ro", "vw", "cw"]).drop(columns="mv")
                w = d.iloc[0].copy()
                if set(re.findall(r"Aus|Aman|Boro", w.value.title())) != set(keep):
                    w["value"] = val
                if w.value != cur.value:
                    SUPPORT_LOG.append(dict(key=key, field=field, authority_choice=cur.value, support_choice=w.value,
                                            families_authority="", families_support="NSB decision"))
                return w, d
    if field in ("official_name_bn", "official_name_en"):
        # REV4: an agent annotation ('(proposed)') is not part of the name when a clean reading exists
        d["ann"] = d.value.str.contains(r"\bproposed\b", regex=True).astype(int)
    if field in TRIAL_NUM:
        d["tc"] = d["source_id"].map(trial_class)
        d = d.sort_values(["tc", "ro", "vw", "cw"]); return d.iloc[0], d
    if field == "release_category" and re.search(r"^HYB_|HYBRID", str(df.pilot_key.iloc[0])):
        # REV3 (round-2 review V2-05): for a hybrid the approving NSB decision settles the route. The gazette notices of
        # 2013-15 print BRRI hybrid dhan3 and dhan4 in a table of released varieties, but NSB 70 and NSB 72 (agenda
        # 'নিবন্ধিকরণ') registered them, as the MoA hybrid lists and the SCA compendium also record.
        d["tc"] = d["source_id"].str.match(r"NSB_").map({True: 0, False: 1})
        d = d.sort_values(["tc", "ro", "vw", "cw"]); return d.iloc[0], d
    if field == "gazette_date":
        d = d.sort_values(["value", "ro"]); return d.iloc[0], d
    if field == "release_date":
        d = d.sort_values(["ro", "vw", "value"]); return d.iloc[0], d
    if field == "cgiar_role":
        d["code"] = pd.to_numeric(d["value"], errors="coerce").fillna(9)
        d.loc[d.code == 5, "code"] = 8          # 'unknown' only if nothing else
        d = d.sort_values(["code", "ro", "vw"]); return d.iloc[0], d
    if field == "breeding_line":
        d["coded"] = d["value"].map(lambda v: 0 if is_code(v) else 1)
        d = d.sort_values(["coded", "ro", "vw", "cw"]); return d.iloc[0], d
    if field == "approval_date":
        d["prec"] = d["value"].str.len().map(lambda n: 0 if n >= 10 else (1 if n >= 7 else 2))
        d = d.sort_values(["ro", "prec", "value", "vw", "cw"]); return d.iloc[0], d
    d = d.sort_values((["ann"] if "ann" in d else []) + ["ro", "vw", "cw"])
    w = d.iloc[0]
    if w.method == "bijoy2unicode" and "র্" in w.value:      # prefer a hand-checked spelling of the same text
        alt = d[(d.method != "bijoy2unicode") & (d.value.map(no_reph) == no_reph(w.value)) & (d.value != w.value)]
        if len(alt):
            w = alt.iloc[0]
    return w, d


def conflicts_for(key, field, d):
    if field in LISTY or field == "cgiar_role":
        return []
    if field in ("approval_date", "release_date", "gazette_date"):
        distinct = d["value"].str[:4].nunique() > 1 or d[d["value"].str.len() >= 10]["value"].nunique() > 1
    elif field in ("breeding_line", "pedigree"):     # REV4: BR5331-93-28-3 and BR5331-93-2-8-3 are different readings
        distinct = d["value"].map(code_norm).nunique() > 1
    else:
        distinct = d["value"].map(norm).nunique() > 1
    if not distinct:
        return []
    return [dict(key=key, field=field, value=r.value, value_raw=r.value_raw, source_id=r.source_id,
                 source_title=r.source_title, authority_rank=r.authority_rank, local_file=r.local_file,
                 page=r.page, locator=r.locator, method=r.method, validation=r.validation,
                 chosen="yes" if i == 0 else "no") for i, r in enumerate(d.itertuples())]


def short_conflict(field, d, chosen):
    nf = code_norm if field in ("breeding_line", "pedigree") else norm
    others = d[d.value.map(nf) != nf(chosen)].drop_duplicates("value")
    if others.empty:
        return ""
    alt = "; ".join(f"{r.value} ({r.source_id})" for r in others.head(4).itertuples())
    return f"{field}: chose {chosen}; also {alt}"


def build(keys_mask, fields, id_prefix):
    rows, conf, fails = [], [], []
    idcol = "variety_id" if id_prefix == "RICE" else "strain_id"
    for key, g in ev[keys_mask].groupby("pilot_key"):
        row = {idcol: f"{id_prefix}-{key}"}
        flags, cnotes, extra_aliases = [], [], []
        for f in fields:
            sub = g[g.field == f]
            if f == "approval_reference" and len(row.get("approval_date", "")) == 10:
                tied = sub[sub.value.map(lambda v: ref_matches(v, row["approval_date"]))]
                if len(tied):                      # keep the reference of the meeting whose date is in the register
                    sub = pd.concat([tied, sub[~sub.index.isin(tied.index)]])
                    w, d = pick(tied, f)
                    d = pd.concat([d, pick(sub, f)[1]]).drop_duplicates()
                else:
                    w, d = pick(sub, f)
            else:
                w, d = pick(sub, f)
            if w is None:
                row[f] = ""
                if (g.field == f).any():
                    flags.append(f"{f}_unvalidated_only")
                continue
            if f in LISTY - {"cgiar_evidence", "cgiar_spia_flags"}:
                row[f] = " | ".join(dict.fromkeys(v.strip() for v in d["value"] if v.strip()))
            elif f == "cgiar_spia_flags":
                row[f] = w.value + " | " + w.notes.split(". SPIA definition")[0]
            elif f == "cgiar_evidence":
                row[f] = w.value
                row["cgiar_evidence_quote"] = w.value_raw[:200]
                row["cgiar_evidence_source"] = f"{w.local_file}, p. {w.page}" if w.page else w.local_file
            else:
                row[f] = w.value
            if f == "yield_t_ha":       # REV2: unit words are not part of the value ('8.5 টন/হেঃ'); per-acre figures keep their text
                if "একর" not in row[f]:
                    row[f] = re.sub(r"\s*(মে\.?\s*)*(মেট্রিক\s*)?টন\s*(/\s*হে[ঃ.]?|/\s*হেক্টর)?|\s*t/ha", "", row[f]).strip()
                row["yield_source_id"] = w.source_id
            c = conflicts_for(key, f, d)
            conf += c
            if c:
                cnotes.append(short_conflict(f, d, w.value))
            if f == "breeding_line":   # non-coded labels from any source become aliases
                extra_aliases += [v for v in d.value if norm(v) != norm(w.value) and is_label(v)]
            if f == "gazette_date" and d.value.nunique() > 1:
                cnotes.append("later gazette(s): " + ", ".join(sorted(set(d.value) - {w.value})))
            if f in ("approval_date", "release_date"):
                if len(w.value) == 4: flags.append("year_only")
                if d["source_id"].nunique() == 1 and w.validation != "two_source": flags.append("date_single_source")
        bl = row.get("breeding_line", "")
        if bl and not is_code(bl):   # descriptive text (e.g. 'pure line selection', 'Mahsuri') is not a line code
            is_hyb = key.startswith("HYB_") or "HYBRID" in key
            if is_hyb and not re.search(r"/|\sx\s|×", bl):          # hybrid trade names or codes are not pedigrees
                row["pedigree_note"] = " | ".join(x for x in [row.get("pedigree_note", ""), bl] if x)
            elif not row.get("pedigree"):
                row["pedigree"] = bl
            elif is_label(bl):
                extra_aliases.append(bl)
            row["breeding_line"] = ""
            flags.append("breeding_line_not_a_code_moved")
        if "aliases" in row:
            row["aliases"] = " | ".join(dict.fromkeys([x for x in row["aliases"].split(" | ") if x] + extra_aliases))
        if id_prefix == "RICE":
            if not (g.eligible & (g["rank"] <= 2)).any():
                flags.append("institute_claim_only")
            if not row.get("cgiar_role"):
                ped = " ".join([row.get("pedigree", ""), row.get("hybrid_parent_female", ""), row.get("hybrid_parent_male", "")]).strip()
                named = bool(re.search(r"/|\sx\s|×|\bcross\b|selection|mutant|irradiat|somaclon|backcross", ped, re.I))
                if ped and named and not re.search(r"\bIR|IRRI|ইরি|NERICA|IRGC|AfricaRice|HarvestPlus|INGER", ped, re.I):
                    row["cgiar_role"] = "4"; flags.append("cgiar_role_4_pedigree_documented_no_cgiar_element")
                else:
                    row["cgiar_role"] = "5"; flags.append("cgiar_role_default_unknown_no_pedigree" if not ped else "cgiar_role_5_pedigree_needs_review")
            if row.get("cgiar_role") in ("1", "2", "3") and not row.get("cgiar_center"):
                flags.append("cgiar_center_missing")
        main_f = "approval_date" if "approval_date" in fields else "release_date"
        w, _ = pick(g[g.field == main_f], main_f)
        if w is None:
            e = g[g.eligible].sort_values("rank")
            w = e.iloc[0] if len(e) else None
        if w is not None and w.local_file.replace("\\", "/") in MAN.index:
            m = MAN.loc[w.local_file.replace("\\", "/")]
            row.update(source_url=m["source_url"], archived_url=m["archived_url"], local_file=w.local_file,
                       source_type=w.authority_rank, retrieved_at=m["download_date"])
        else:
            row.update(source_url="", archived_url="", local_file=(w.local_file if w is not None else ""),
                       source_type=(w.authority_rank if w is not None else ""), retrieved_at="")
        row["n_sources"] = g[g.eligible].source_id.nunique()
        cg = g[g.eligible & (g["rank"] == 4) & g.field.isin(["cgiar_independent", "cgiar_role", "cgiar_lineage",
                                                             "cgiar_spia_flags", "cgiar_evidence", "cgiar_source_url"])]
        urls = []
        for lf, v, fld in zip(cg.local_file, cg.value, cg.field):
            if fld == "cgiar_source_url" and v.startswith("http"):
                urls.append(v); continue
            lf = lf.replace("\\", "/")
            if lf in MAN.index and MAN.loc[lf, "source_url"].startswith("http"):
                urls.append(MAN.loc[lf, "source_url"])
        def landing(u, lf=""):
            import urllib.parse as _up
            m = re.search(r"static-content\.springer\.com/esm/art%3A([^/]+)/", u)
            if m:
                return "https://doi.org/" + _up.unquote(m.group(1))
            m = re.search(r"PMC(\d+)", u + " " + lf)
            if m and ("europepmc" in u or "ncbi" in u or "pmc" in lf.lower()):
                return f"https://europepmc.org/article/PMC/PMC{m.group(1)}"
            return u
        urls = [landing(u) for u in urls]
        row["cgiar_source_urls"] = " | ".join(dict.fromkeys(urls))
        ce = g[g.eligible & (g.field == "cgiar_evidence")]
        ce_url = ""
        if len(ce):
            lf0 = ce.sort_values("rank").iloc[0].local_file.replace("\\", "/")
            if lf0 in MAN.index:
                ce_url = landing(MAN.loc[lf0, "source_url"], lf0)
        row["cgiar_evidence_url"] = ce_url
        vs = []
        for fld in ("approval_date", "breeding_line", "gazette_date", "cgiar_role"):
            wv, _ = pick(g[g.field == fld], fld)
            if wv is not None:
                vs.append(f"{fld}={wv.validation or 'text'} ({wv.method})")
        row["validation_summary"] = "; ".join(vs)
        subst = {"approval_date", "gazette_date", "breeding_line", "pedigree", "release_category", "origin_country",
                 "release_date", "generation", "approval_or_release_mechanism"}
        hit = sorted({c["field"] for c in conf if c["key"] == key} & subst)
        if hit: flags.append("has_conflicts:" + ",".join(hit))
        unv = g[~g.eligible]
        if len(unv): flags.append(f"unvalidated_values={len(unv)}")
        row["flags"] = ";".join(dict.fromkeys(flags))
        row["conflict_fields"] = "; ".join(sorted({c["field"] for c in conf if c["key"] == key} & subst))
        row["conflict_note"] = " | ".join(n.replace(" | ", " / ") for n in cnotes)
        row["notes"] = ""
        rows.append(row)
        if not row["source_url"] or not row["local_file"]:
            fails.append({"id": row[idcol], "reason": "missing source_url or local_file (not in manifest)",
                          "local_file": row["local_file"]})
    return rows, conf, fails


RICE_FIELDS = ["official_name_en", "official_name_bn", "popular_name", "aliases", "breeding_line", "pedigree", "hybrid_parent_female", "hybrid_parent_male",
               "type", "developer", "developer_division", "origin_country", "origin_statement", "trial_codes", "pedigree_note", "release_category", "approving_body", "approval_date",
               "approval_reference", "provisional_release_date", "provisional_release_reference", "gazette_date", "gazette_date_reported", "gazette_status_note",
               "gazette_reference", "season", "ecosystem", "region_scope",
               "duration_days", "yield_t_ha", "yield_criterion_pct", "check_variety", "recommended_region", "release_year_official",
               "special_traits_official", "identifying_traits_official", "quality_traits", "stress_tolerance", "dus_result", "vcu_sites",
               "decision_conditions", "key_traits", "adoption", "market_segment", "product_profile", "status", "cgiar_role", "cgiar_center", "cgiar_lineage", "cgiar_evidence",
               "cgiar_spia_flags", "cgiar_independent", "doi_key_paper"]
FISH_FIELDS = ["species_common_en", "species_scientific", "species_bn", "strain_name", "developer",
               "cgiar_role", "cgiar_center", "approval_or_release_mechanism", "releasing_body",
               "release_date", "generation", "key_traits", "distribution_channel", "status"]
# PI 2026-10-06: GIFT transfers/introductions and planned generations go to a separate table
FISH_EVENTS = {"FISH_WF_GIFT_INTRO_1994": "germplasm transfer (WorldFish -> BFRI)",
               "FISH_WF_GIFT_AIN_NUCLEI": "germplasm dissemination (WorldFish breeding nuclei)",
               "FISH_WF_GIFT_G19_EON_2025": "germplasm transfer (WorldFish -> private company)",
               "FISH_WF_G5_ROHU": "planned generation release",
               "FISH_WF_G4_SILVER_CARP": "planned generation release",
               "FISH_WF_G3_CATLA": "planned generation release"}


def planned(rows):
    for r in rows:
        txt = (r.get("approval_or_release_mechanism", "") + " " + r.get("status", "")).lower()
        if "pending" in txt or "planned" in txt or "none yet" in txt:
            if r.get("release_date"):
                r["notes"] = (r.get("notes", "") + f" planned release {r['release_date']} per source").strip()
            r["release_date"] = ""
            r["status"] = "planned_not_yet_released"
            r["flags"] = ";".join(x for x in (r["flags"] + ";planned_not_released").split(";") if x and x != "year_only")
    return rows


is_fish = ev["pilot_key"].str.startswith("FISH")
rice, c1, f1 = build(~is_fish & (ev.field != "local_name"), RICE_FIELDS, "RICE")
fish, c2, f2 = build(is_fish & (ev.field != "local_name"), FISH_FIELDS, "FISH")
fish = planned(fish)
events = []
for r in fish:
    k = r["strain_id"].replace("FISH-", "", 1)
    r["strain_id"] = r["strain_id"].replace("FISH-FISH_", "FISH-")
    if k in FISH_EVENTS:
        r["event_type"] = FISH_EVENTS[k]; events.append(r)
fish = [r for r in fish if "event_type" not in r]
RN = pd.read_csv(ROOT / "04_working/row_notes.csv", dtype=str).fillna("")
RN = RN.groupby("id")["note"].apply(" | ".join).to_dict()
for lst, idc in [(rice, "variety_id"), (fish, "strain_id"), (events, "strain_id")]:
    for r in lst:
        if r[idc] in RN:
            r["notes"] = (r.get("notes", "") + " " + RN[r[idc]]).strip()
OUT.mkdir(exist_ok=True)
rice_df = pd.DataFrame(rice).sort_values("variety_id")
import sys as _sys; _sys.path.insert(0, str(ROOT / "scripts"))
from lib_names import variety_name as _vname
_xw = pd.read_csv(ROOT / "04_working/hybrid_key_crosswalk.csv", dtype=str).fillna("").drop_duplicates("key").set_index("key")["code"]
rice_df.insert(1, "variety_name", [_vname(k, _xw.get(k, "")) for k in rice_df.variety_id.str[5:]])
_front = ["variety_id", "variety_name"]
_cg = ["cgiar_role", "cgiar_center", "cgiar_lineage", "cgiar_evidence", "cgiar_evidence_quote", "cgiar_evidence_source", "cgiar_evidence_url",
       "cgiar_spia_flags", "cgiar_independent", "cgiar_source_urls"]
_tail = ["source_url", "archived_url", "local_file", "source_type", "retrieved_at", "n_sources", "validation_summary",
         "flags", "conflict_fields", "conflict_note", "notes"]
_mid = [c for c in rice_df.columns if c not in _front + _cg + _tail]
rice_df = rice_df[_front + _mid + [c for c in _cg if c in rice_df] + [c for c in _tail if c in rice_df]]


def ordinal(m):
    n = int(m.group(1))
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


rice_df["cgiar_center"] = rice_df["cgiar_center"].str.replace(r"\s*\(CGIAR\)", "", regex=True)
for c in ("approval_reference", "gazette_reference", "conflict_note"):
    rice_df[c] = rice_df[c].fillna("").str.replace(r"\b(\d+)(?:st|nd|rd|th)\b", ordinal, regex=True)
# gazette status for every variety, stated explicitly
def _gstat(r):
    if r.gazette_date:
        return "notified (gazette in archive)"
    if r.get("gazette_date_reported", ""):
        return "notified per NSB minutes (gazette copy not found)"
    n = r.get("gazette_status_note", "").upper()
    if "REPORTED ISSUED" in n:
        return "notified per NSB minutes (date not stated)"
    if any(t in n for t in ("NOT CONFIRMED", "SENT FOR GAZETTING", "NOT YET PUBLISHED")):
        return "sent to Government Press; publication not confirmed"
    if r.release_category == "NSB_registration":
        return "not gazetted (hybrid registrations are not gazetted)"
    if r.release_category == "pre_NSB_recommended" or r.approval_date[:10] < "1977-07-19":
        return "not applicable (before the Seeds Ordinance 1977)"
    if r.approval_date[:4] == "2026":
        return "not yet published (weekly and extraordinary gazettes checked to 1 Oct 2026)"
    return "not found (dpp.gov.bd holds no weekly gazettes before 2013)"


rice_df["gazette_status"] = rice_df.apply(_gstat, axis=1)

# REV4 (E1): the institute's own release year, kept beside the NSB approval date and never overwriting it. Only the
# institutes' publications count: BRRI Adhunik Dhaner Chash 2025 Table 1 ('অবমুক্তির বছর'), BINA at a glance, BRRI Rice
# Profile, BRRI fact sheets (in that order). The first that states a year is used; disagreements go to conflict_note.
INST_SRC = ["RB-S01", "RB-S12", "DS-S07", "RB-S04", "RB-S08"]
_iy = ev[ev.eligible & ev.field.eq("approval_date") & ev.source_id.isin(INST_SRC) & ev.value.str.match(r"^\d{4}")].copy()
# only an institute's statement about its own variety, and from the handbook only Table 1 (pp. 9-12, 'অবমুক্তির বছর');
# the handbook's prose on p.7 ('IR8 was first grown in 1968') is not a release year
_brri = _iy.pilot_key.str.match(r"^(BR\d|BRRI_)"); _bina = _iy.pilot_key.str.match(r"^(BINA|IRATOM)")
_iy = _iy[(_iy.source_id.isin(["RB-S01", "DS-S07", "RB-S04", "RB-S08"]) & _brri) | (_iy.source_id.eq("RB-S12") & _bina)]
_iy = _iy[~_iy.source_id.eq("RB-S01") | _iy.page.isin(["9", "10", "11", "12"])]
_iy["o"] = _iy.source_id.map(INST_SRC.index)
_iy = _iy.sort_values(["pilot_key", "o"])
_iyr, _iys, _iyc = {}, {}, {}
for k, g in _iy.groupby("pilot_key"):
    w = g.iloc[0]
    _iyr[k] = w.value[:4]
    _iys[k] = f"{w.source_title} ({w.source_id}{', p. ' + w.page if w.page else ''})"
    oth = g[g.value.str[:4] != w.value[:4]].drop_duplicates("source_id")
    if len(oth):
        _iyc[k] = f"institute_release_year: chose {w.value[:4]} ({w.source_id}); also " + "; ".join(f"{r.value[:4]} ({r.source_id})" for r in oth.itertuples())
_k = rice_df.variety_id.str[5:]
_pos = rice_df.columns.get_loc("approval_reference") + 1
rice_df.insert(_pos, "institute_release_year", _k.map(_iyr).fillna(""))
rice_df.insert(_pos + 1, "institute_release_year_source", _k.map(_iys).fillna(""))
_cn = _k.map(_iyc).fillna("")
rice_df["conflict_note"] = [" | ".join(x for x in (a, b) if x) for a, b in zip(rice_df.conflict_note, _cn)]

# parents that are register varieties: inherit CGIAR ancestry one generation (PI rule: grandparents count as code 2)
sys.path.insert(0, str(ROOT / "scripts"))
from lib_keys import make_key as _mk
_role = dict(zip(rice_df.variety_id.str[5:], rice_df.cgiar_role)); _lin = dict(zip(rice_df.variety_id.str[5:], rice_df.cgiar_lineage))
for i, r in rice_df[rice_df["flags"].str.contains("cgiar_role_4_pedigree")].iterrows():
    for part in re.split(r"[/;×]|\sx\s", r.pedigree):
        k = _mk(part.strip())
        if k and k in _role and _role[k] in ("1", "2"):
            via = "IRRI line" if _role[k] == "1" else "IRRI parent of " + k
            if _role[k] == "1" or "IRRI parent" in _lin.get(k, ""):
                rice_df.at[i, "cgiar_role"] = "2"; rice_df.at[i, "cgiar_center"] = "IRRI"
                rice_df.at[i, "cgiar_lineage"] = (f"IRRI {'parent' if _role[k] == '1' else 'grandparent'} via {k} (" + _lin.get(k, via)[:120] + ")").strip()
                rice_df.at[i, "flags"] = r["flags"].replace("cgiar_role_4_pedigree_documented_no_cgiar_element", "cgiar_role_2_via_parent_variety")
            else:
                rice_df.at[i, "notes"] = (r.notes + f" | parent {k} has CGIAR ancestry beyond its own parents (noted, not coded)").strip(" |")
            break
# approving body follows from the approval route when no source spells it out
_ab = rice_df.approving_body.eq("")
rice_df.loc[_ab & rice_df.release_category.str.startswith("NSB_"), "approving_body"] = "National Seed Board (NSB)"
rice_df.loc[_ab & rice_df.release_category.eq("pre_NSB_recommended"), "approving_body"] = "none: recommended before the NSB was constituted (1974)"
# a row belongs in the main table only if some eligible evidence records an approval event
na = rice_df["release_category"].eq("")
rice_df[na].to_csv(OUT / f"rice_not_approved_or_unresolved{SUF}.csv", index=False, encoding="utf-8-sig")
rice_df = rice_df[~na]
rice_df.to_csv(OUT / f"rice_varieties{SUF}.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(fish).to_csv(OUT / f"fish_strains{SUF}.csv", index=False, encoding="utf-8-sig")
ecols = ["strain_id", "event_type"] + [c for c in (pd.DataFrame(events).columns if events else []) if c not in ("strain_id", "event_type")]
pd.DataFrame(events, columns=ecols).rename(columns={"strain_id": "event_id"}).to_csv(OUT / f"fish_events{SUF}.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(c1 + c2).to_csv(OUT / f"conflicts{SUF}.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(f1 + f2, columns=["id", "reason", "local_file"]).to_csv(OUT / f"failures{SUF}.csv", index=False, encoding="utf-8-sig")
ln = ev[ev.field == "local_name"][["pilot_key", "value", "value_raw", "source_id", "source_title", "authority_rank",
                                   "local_file", "page", "locator", "confidence", "notes", "eligible"]]
ln.to_csv(OUT / f"local_names_from_sources{SUF}.csv", index=False, encoding="utf-8-sig")
used = ev[ev.eligible][["source_id", "source_title", "authority_rank", "local_file"]].drop_duplicates("local_file")
used = used.merge(man[["file_path", "source_url", "archived_url", "download_date", "sha256"]].drop_duplicates("file_path"),
                  left_on="local_file", right_on="file_path", how="left").drop(columns="file_path")
used.to_csv(OUT / f"sources{SUF}.csv", index=False, encoding="utf-8-sig")
ev.to_csv(OUT / f"evidence_all{SUF}.csv", index=False, encoding="utf-8-sig")
if not SUF:   # REV4: every choice where independent support or an NSB decision overrode the authority order
    pd.DataFrame(SUPPORT_LOG).drop_duplicates().to_csv(ROOT / "06_validation/precedence_support_log.csv", index=False, encoding="utf-8-sig")
print(f"rice {len(rice_df)} (not approved/unresolved {int(na.sum())})  fish {len(fish)}  fish_events {len(events)}  conflicts {len(c1+c2)}  "
      f"failures {len(f1+f2)}  sources {len(used)}  unmatched {len(unmatched)}")
