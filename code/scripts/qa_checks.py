"""Integrity checks on the final release (05_output/final). Writes 06_validation/qa_checks.md and exits non-zero on failure.
Each check reports PASS / WARN / FAIL with counts and examples."""
import hashlib
import json
import pathlib
import re
import sys
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
F = ROOT / "05_output/final"
R = pd.read_csv(F / "bgd_rice_varieties.csv", dtype=str).fillna("")
MAN = pd.read_csv(ROOT / "02_raw/manifest.csv", dtype=str).fillna("")
MAN["file_path"] = MAN.file_path.str.replace("\\", "/", regex=False)
KEY = pd.read_csv(ROOT / "04_working/nsb_meeting_key_resolved.csv", dtype=str, encoding="utf-8-sig").fillna("")
out = []


def check(name, ok, detail, warn=False):
    out.append((name, "PASS" if ok else ("WARN" if warn else "FAIL"), detail))


# 1 identifiers
check("variety_id unique", R.variety_id.is_unique, f"{len(R)} rows, {R.variety_id.nunique()} unique")
check("variety_name unique", R.variety_name.is_unique, f"duplicates: {R.variety_name[R.variety_name.duplicated()].tolist()[:5]}", warn=True)

# 2 required fields
for c in ["official_name_bn", "release_category", "approving_body", "approval_date", "source_url", "local_file", "rice_type", "sector", "developer_group"]:
    miss = R[R[c] == ""]
    check(f"required field: {c}", miss.empty, f"{len(miss)} missing" + (f": {miss.variety_id.tolist()[:6]}" if len(miss) else ""),
          warn=c in ("official_name_bn", "approving_body"))

# 3 dates
iso = R.approval_date.str.fullmatch(r"\d{4}(-\d{2}-\d{2})?")
check("approval_date ISO or year", iso.all(), f"bad: {R[~iso].approval_date.tolist()[:5]}")
g = R[R.gazette_date != ""]
check("gazette_date after approval_date", (g.gazette_date >= g.approval_date.str[:10]).all(),
      f"violations: {g[g.gazette_date < g.approval_date.str[:10]][['variety_id','approval_date','gazette_date']].values.tolist()[:5]}")
yrs = pd.to_numeric(R.approval_date.str[:4], errors="coerce")
check("approval year within 1966-2026", yrs.between(1966, 2026).all(), f"out of range: {R[~yrs.between(1966, 2026)].variety_id.tolist()[:5]}")

# 4 NSB meeting number vs meeting-date key
kv = {m: {d} for m, d in zip(KEY.meeting_no, KEY.meeting_date)}   # one resolved date per meeting
bad = []
for r in R.itertuples():
    m = re.search(r"NSB (\d+)", r.approval_reference)
    if m and len(r.approval_date) == 10 and m.group(1) in kv and r.approval_date not in kv[m.group(1)]:
        bad.append((r.variety_id, m.group(1), r.approval_date, sorted(kv[m.group(1)])))
check("approval_date matches NSB meeting-date key", not bad, f"{len(bad)} mismatches: {bad[:4]}")

# 5 sources: every local_file in the manifest, file exists, SHA-256 matches
lf = set(R.local_file) | set(pd.read_csv(F / "bgd_sources.csv", dtype=str).fillna("").local_file)
lf.discard("")
M = MAN.drop_duplicates("file_path").set_index("file_path")
notman = [f for f in lf if f.replace("\\", "/") not in M.index]
check("every cited file is in the manifest", not notman, f"{len(notman)} missing: {notman[:4]}")
shabad, missing = [], []
for f in sorted(lf):
    p = ROOT / f
    if not p.exists():
        missing.append(f); continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if f.replace("\\", "/") in M.index and M.loc[f.replace("\\", "/"), "sha256"] != h:
        shabad.append(f)
check("every cited file exists on disk", not missing, f"{len(missing)} missing: {missing[:4]}")
check("SHA-256 of cited files matches manifest", not shabad, f"{len(lf)} files hashed; {len(shabad)} mismatches: {shabad[:4]}")

# 6 CGIAR coding consistency
check("cgiar_role in 1-5", R.cgiar_role.isin(list("12345")).all(), f"values: {sorted(R.cgiar_role.unique())}")
lin = R[R.cgiar_role.isin(["1", "2", "3"]) & (R.cgiar_lineage == "") & (R.cgiar_evidence == "")]
check("codes 1-3 carry lineage or evidence", lin.empty, f"{len(lin)} without: {lin.variety_id.tolist()[:6]}", warn=True)
cen = R[R.cgiar_role.isin(["1", "2", "3"]) & (R.cgiar_center == "")]
check("codes 1-3 name a CGIAR centre", cen.empty, f"{len(cen)} without centre: {cen.variety_id.tolist()[:6]}", warn=True)

# 7 text hygiene
allt = pd.concat([pd.read_csv(f, dtype=str).fillna("") for f in F.glob("bgd_*.csv") if f.stat().st_size < 30e6], ignore_index=True)
blob = "\n".join(allt.astype(str).agg(" ".join, axis=1))
check("no e-mail inside URLs (mailto=)", "mailto=" not in blob, f"occurrences: {blob.count('mailto=')}")
gar = re.findall(r"\([^()]*[ঐঘঝঞঊঈঔ][a-zA-Z]?[^()]*\)", " ".join(R.official_name_bn))
check("no Bijoy-garbled Latin codes in Bangla names", not gar, f"{len(gar)} suspicious: {gar[:4]}", warn=True)
txtcols = ["official_name_bn", "developer", "region_scope", "aliases", "popular_name"]
reph = [v for c in txtcols if c in R for v in R[c] if re.search(r"[ক-হ]র্(?=[\s,।)]|$)", v)]
check("no word-final reph (র্) in Bangla text", not reph, f"{len(reph)} found: {reph[:3]}")
ctrl = re.findall(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", blob)
check("no control characters", not ctrl, f"{len(ctrl)} found")

# 8 counts reconcile
t27 = pd.read_csv(ROOT / "03_extracted/tables/spia2025_table27.csv", dtype=str)
pub23 = R[(R.approval_date.str[:4] <= "2023") & ~R.variety_id.str.match(r"RICE-(HYB_|PVT_)")]
import sys as _sys; _sys.path.insert(0, str(ROOT / "scripts")); from lib_keys import make_key
_RM = pd.read_csv(ROOT / "04_working/key_remap.csv", dtype=str).set_index("old_key")["new_key"].to_dict()
_t27k = set(t27.variety.map(make_key).dropna().map(lambda k: _RM.get(k, k))); _ours = set(pub23.variety_id.str.replace("RICE-", "", regex=False))
_only_ours, _only_t27 = _ours - _t27k, _t27k - _ours
check("SPIA Table 27 reconciliation (ours - outside SPIA scope + SPIA-only = 139)", len(t27) == 139 and len(_ours) - len(_only_ours) + len(_only_t27) == 139,
      f"T27 rows {len(t27)}; ours {len(_ours)} - {len(_only_ours)} outside SPIA + {len(_only_t27)} SPIA-only = {len(_ours) - len(_only_ours) + len(_only_t27)}")
brri = R.variety_id.str.match(r"RICE-(BR\d+|BRRI_DHAN\d+|BRRI_HYBRID\d+)$").sum()
check("BRRI count = 127 (BRRI website, 23 Apr 2026)", brri == 127, f"ours {brri}")
hyb = (R.rice_type == "hybrid").sum()
check("hybrids = 279 (MoA 270 distinct + 9 not in MoA 2026)", hyb == 279, f"ours {hyb}")

# 10 version 1.2 checks (REV2, 2026-11-10; reviews A1, A2, A4)
import unicodedata
NA = pd.read_csv(F / "bgd_rice_not_approved_or_unresolved.csv", dtype=str).fillna("")
ST = pd.read_csv(F / "bgd_variety_status.csv", dtype=str).fillna("")
check("register has 444 varieties (443 of v1.1.1 + Iratom-38)", len(R) == 444, f"{len(R)} rows")
both = set(R.variety_id) & set(NA.variety_id)
check("register and not-approved file are disjoint", not both, f"in both: {sorted(both)[:5]}")
extra = set(ST.variety_id) - set(R.variety_id)
check("status file = register + names with NSB decisions outside it", set(R.variety_id) <= set(ST.variety_id) and extra <= set(NA.variety_id),
      f"status {len(ST)} rows; outside register: {sorted(extra)}")
LEG = {"active", "active, withdrawal proposed 2021 and deferred", "time-limited registration, renewal not recorded",
       "provisional, re-evaluation outcome not recorded", "seed multiplication suspended", "suspended",
       "recommended before the Board, no later decision"}
badl = R[~R.legal_status_2026.isin(LEG)]
check("legal_status_2026 in the documented vocabulary", badl.empty, f"{len(badl)} bad: {badl[['variety_id', 'legal_status_2026']].values.tolist()[:4]}")
check("legacy 'status' column not published", "status" not in R.columns, "dropped in v1.2")
# salt tag never rests on a non-saline statement (A1-01)
NONSAL = re.compile(r"অলবণাক্ত|অলবনাক্ত|অ-লবণাক্ত|অ-লবনাক্ত|non[- ]?saline", re.I)
EVA = pd.read_csv(ROOT / "05_output/evidence_all.csv", dtype=str, usecols=["pilot_key", "field", "value", "value_raw", "eligible"]).fillna("")
salty = set(R[R.feature_tags.str.contains("salt tolerant")].variety_id.str[5:])
bad_ev = EVA[EVA.pilot_key.isin(salty) & EVA.field.eq("key_traits") & EVA.eligible.eq("True")
             & EVA.value.str.contains(r"salt|salin", case=False) & EVA.value_raw.str.contains(NONSAL)
             & ~EVA.value.str.contains(NONSAL)]
check("no salt tag from an English gloss of a non-saline (অলবণাক্ত) text", bad_ev.empty, f"{len(bad_ev)}: {bad_ev.pilot_key.tolist()[:5]}")
SALTPOS = re.compile(r"(লবণ|লবন|salt|salin)", re.I)
bad_t = []
for r in R[R.feature_tags.str.contains("salt tolerant")].itertuples():
    ev = re.search(r"salt tolerant: ([^|]*)", r.feature_evidence)
    cols = [c.strip().split(" (")[0] for c in (ev.group(1).split(",") if ev else [])]
    clauses = [cl for c in cols if c in R.columns for cl in re.split(r"[।|;.\n]", getattr(r, c)) if SALTPOS.search(cl)]
    if clauses and all(NONSAL.search(cl) for cl in clauses):
        bad_t.append(r.variety_id)
check("no salt tag whose only salinity text says non-saline", not bad_t, f"{bad_t[:5]}")
spia_only = R[R.feature_evidence.str.contains(r"(?:salt|submergence|drought) tolerant: cgiar_spia_flags(?: \||$)")]
check("no stress tag resting on a SPIA flag alone", spia_only.empty, f"{spia_only.variety_id.tolist()[:5]}")
# CGIAR code against pedigree depth (A2-06, A4-02; coordinator ruling: a mutant, somaclone or selection of a CGIAR line is code 1)
dep = R[R.depth_to_cgiar.ne("")]
bad1 = dep[(dep.depth_to_cgiar == "0") & (dep.cgiar_role != "1")]
bad2 = dep[(dep.depth_to_cgiar != "0") & (dep.cgiar_role != "2")]
check("depth_to_cgiar 0 <=> cgiar_role 1; depth >= 1 => cgiar_role 2", bad1.empty and bad2.empty,
      f"depth 0 not code 1: {bad1.variety_id.tolist()[:5]}; depth>=1 not code 2: {bad2.variety_id.tolist()[:5]}")
c1 = R[(R.cgiar_role == "1") & (R.depth_to_cgiar.ne("0"))]
check("every code 1 has depth_to_cgiar 0 or no parsed pedigree", c1[c1.depth_to_cgiar.ne("")].empty, f"{c1[c1.depth_to_cgiar.ne('')].variety_id.tolist()[:5]}")
# regions (A2-11, A4-03, A4-04)
bn = R[R.region_scope.str.contains(r"[ঀ-৿]")]
check("region_scope is English (controlled summary)", bn.empty, f"{len(bn)} Bangla: {bn.variety_id.tolist()[:5]}")
nw = R[(R.region_nationwide == "1") & (R.region_divisions.str.count(";") != 7)]
check("region_nationwide = 1 implies all eight divisions", nw.empty, f"{nw.variety_id.tolist()[:5]}")
import derive_covariates as _DC   # an exception by agro-ecological zone removes no division (documented rule)
_ex = lambda t: " ".join(re.findall(r"except\s+([^;()|]*)", t, re.I) + re.findall(r"\(([^)]*)(?:ব্যতীত|ব্যাতিত)", t))
exc = R[(R.region_nationwide == "1") & (R.recommended_region + " | " + R.region_scope).map(lambda t: bool(_DC._divisions_in(_ex(t))))]
check("no nationwide flag where a division is excepted", exc.empty, f"{exc.variety_id.tolist()[:5]}")
sc = R[R.region_scope.ne("") & ~R.region_scope.str.contains(r"nationwide|whole country|all ", case=False) & (R.region_nationwide == "1")]
check("region_scope listing regions agrees with region_nationwide", sc.empty, f"{len(sc)}: {sc.variety_id.tolist()[:6]}", warn=True)
# season flags against the season column (A4-09)
miss, extra_s = [], []
for r in R[R.season.ne("")].itertuples():
    named = {x for x in ("aus", "aman", "boro") if re.search(x, r.season, re.I)}
    flagged = set(r.season_std.split("; ")) - {""}
    if named - flagged: miss.append(r.variety_id)
    if flagged - named: extra_s.append(r.variety_id)
check("every season named in season is flagged", not miss, f"{miss[:5]}")
check("no season flag beyond the season column", not extra_s, f"{len(extra_s)}: {extra_s[:6]} (season statements in official text)", warn=True)
# numeric text columns (A4-13)
unit = R[R.yield_t_ha.str.contains(r"টন|t/ha|মে\.", regex=True) & ~R.yield_t_ha.str.contains("একর")]
check("no unit text in yield_t_ha", unit.empty, f"{unit.variety_id.tolist()[:5]}")
dot = R[R.duration_days.str.contains(r"\b\d{3}\.\d{3}\b") & ~R.duration_days.str.contains("printed")]
check("no '135.140'-style typos in duration_days", dot.empty, f"{dot.variety_id.tolist()[:5]}")
mm = R[(pd.to_numeric(R.yield_min_t_ha, errors="coerce") > pd.to_numeric(R.yield_max_t_ha, errors="coerce"))
       | (pd.to_numeric(R.duration_min_days, errors="coerce") > pd.to_numeric(R.duration_max_days, errors="coerce"))]
check("min <= max for yield and duration", mm.empty, f"{mm.variety_id.tolist()[:5]}")
# Unicode NFC everywhere (A4-15)
# verbatim OCR / source text columns reproduce the source as read and are exempt; bgd_evidence.csv is written by
# scripts/build_evidence_public.py outside rebuild_all.sh and is reported separately
VERB = re.compile(r"raw|verbatim|full_ocr_text|text_layer")
nonfc = [(f.name, c) for f in F.glob("bgd_*.csv") if f.stat().st_size < 30e6 and "attendance" not in f.name
         for c, col in pd.read_csv(f, dtype=str).fillna("").items()
         if not VERB.search(c) and any(isinstance(v, str) and unicodedata.normalize("NFC", v) != v for v in col)]
main_nf = [x for x in nonfc if x[0] != "bgd_evidence.csv"]
check("all text in Unicode NFC (verbatim OCR columns exempt)", not main_nf, f"{len(main_nf)} columns not NFC: {main_nf[:5]}")
ev_nf = [x for x in nonfc if x[0] == "bgd_evidence.csv"]
check("bgd_evidence.csv text in Unicode NFC", not ev_nf, f"{len(ev_nf)} columns not NFC: {ev_nf[:5]}", warn=True)
crit = "yield_criterion_pct" in R.columns and "yield_advantage_pct" not in R.columns
check("yield_criterion_pct replaces yield_advantage_pct", crit, "renamed in v1.2")

# 9 page data
d = json.load(open(F / "viz_data.json", encoding="utf-8"))
check("page data has every register row", len(d["rice"]) == len(R), f"page {len(d['rice'])}, register {len(R)}")
html = (F / "rice_register_standalone.html").read_text(encoding="utf-8")
check("standalone page has no external requests", not re.search(r"<(script|link)[^>]+(src|href)=\"https?://", html), "checked script/link tags")

L = ["# Integrity checks", "", f"Run on the final release ({pd.Timestamp.today().date().isoformat()}).", "", "| check | result | detail |", "|---|---|---|"]
L += [f"| {n} | {s} | {str(dd).replace('|', '/')} |" for n, s, dd in out]
(ROOT / "06_validation/qa_checks.md").write_text("\n".join(L), encoding="utf-8")
for n, s, dd in out:
    print(f"{s:5} {n}: {dd}")
sys.exit(1 if any(s == "FAIL" for _, s, _ in out) else 0)
