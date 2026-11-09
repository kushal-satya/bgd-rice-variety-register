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
    if not (re.search(r"\d", v) and re.search(r"[A-Za-z]", v)): return False
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


def pick(df, field):
    order = ORDER.get(field, DEFAULT)
    d = df[df.eligible].copy()
    if d.empty:
        return None, d
    d["ro"] = d["rank"].map(lambda r: order.index(r) if r in order else 99)
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
    d = d.sort_values(["ro", "vw", "cw"])
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
    else:
        distinct = d["value"].map(norm).nunique() > 1
    if not distinct:
        return []
    return [dict(key=key, field=field, value=r.value, value_raw=r.value_raw, source_id=r.source_id,
                 source_title=r.source_title, authority_rank=r.authority_rank, local_file=r.local_file,
                 page=r.page, locator=r.locator, method=r.method, validation=r.validation,
                 chosen="yes" if i == 0 else "no") for i, r in enumerate(d.itertuples())]


def short_conflict(field, d, chosen):
    others = d[d.value.map(norm) != norm(chosen)].drop_duplicates("value")
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
print(f"rice {len(rice_df)} (not approved/unresolved {int(na.sum())})  fish {len(fish)}  fish_events {len(events)}  conflicts {len(c1+c2)}  "
      f"failures {len(f1+f2)}  sources {len(used)}  unmatched {len(unmatched)}")
