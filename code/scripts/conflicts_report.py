"""Summarise disagreements between sources (05_output/final/bgd_conflicts.csv) for the fields that matter for research.

Outputs
- 05_output/final/bgd_conflicts_summary.csv: one row per (variety, field) with the chosen value and source, every alternative,
  and a classification: formatting_only | date_same_year | date_1_year | date_2plus_years | substantive.
- 06_validation/conflicts_report.md: counts by field and class, which sources disagree with which, systematic patterns,
  and every substantive date/breeding-line/pedigree/category disagreement listed.
"""
import re
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
C = pd.read_csv(ROOT / "05_output/final/bgd_conflicts.csv", dtype=str).fillna("")
FIELDS = ["approval_date", "gazette_date", "breeding_line", "pedigree", "release_category", "origin_country",
          "season", "duration_days", "yield_t_ha", "release_date", "generation"]
C = C[C.field.isin(FIELDS)]
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
SRC = [(r"nsb_minutes|nsb_|tc_0", "NSB minutes"), (r"approved_crop_varieties|registered_hybrid", "SCA annual list"),
       (r"approved_varieties_notified_crops", "SCA compendium 2016"), (r"hybrid_rice_(varieties_)?list|item4_crop", "MoA hybrid list"),
       (r"gazette|bgpress|release_gazette", "Bangladesh Gazette"), (r"adc|adhunik", "BRRI handbook (ADC)"), (r"riceprofile", "BRRI Rice Profile"),
       (r"brri", "BRRI other"), (r"bina|iaea", "BINA / IAEA"), (r"spia", "SPIA 2025"), (r"trivsa", "TRIVSA"), (r"harvestplus", "HarvestPlus"),
       (r"glomip", "GloMIP"), (r"dikitanan|villanueva|kretzschmar|raitzer|cgiar_lit", "CGIAR papers"), (r"literature|crossref|openalex|banglajol", "Literature"),
       (r"cgiar_web|irri", "CGIAR websites"), (r"bfri|worldfish|mofl|dof|fish", "Fish sources")]


def src_label(f):
    f = (f or "").lower()
    for pat, lab in SRC:
        if re.search(pat, f):
            return lab
    return "Other"


def norm(v):
    v = str(v).translate(BN).lower()
    v = v.replace("×", "x").replace(" x ", "/")
    return re.sub(r"[^a-z0-9ঀ-৿]", "", v)


TR = {"ভারত": "india", "চীন": "china", "গণচীন": "china", "বাংলাদেশ": "bangladesh", "ফিলিপাইন": "philippines", "ইরি": "irri",
      "থাইল্যান্ড": "thailand", "ভিয়েতনাম": "vietnam", "পাকিস্তান": "pakistan", "বোরো": "boro", "আমন": "aman", "আউশ": "aus",
      "রোপা": "t", "বোনা": "b", "t.aman": "aman", "t. aman": "aman", "transplanted aman": "aman"}


def tokens(v):
    v = str(v).lower()
    for k, t in TR.items():
        v = v.replace(k, " " + t + " ")
    v = v.translate(BN)
    return {t for t in re.split(r"[^a-z0-9.]+", v) if t and t not in {"and", "o", "ও", "season", "only", "hybrid", "rice"}}


def nums(v):
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(v).translate(BN))]


def compatible(field, a, b):
    """True when two versions do not contradict: translation, subset, overlapping numeric range, or code suffix."""
    if norm(a) == norm(b):
        return True
    if field in ("breeding_line", "pedigree", "generation"):
        na, nb = norm(a), norm(b)
        if na and nb and (na in nb or nb in na):
            return True
        ca = {t for t in tokens(a) if re.search(r"\d", t)}; cb = {t for t in tokens(b) if re.search(r"\d", t)}
        return bool(ca) and bool(cb) and (ca <= cb or cb <= ca)
    if field in ("season", "origin_country"):
        ta, tb = tokens(a), tokens(b)
        return bool(ta) and bool(tb) and (ta <= tb or tb <= ta)
    if field in ("yield_t_ha", "duration_days"):
        xa, xb = nums(a), nums(b)
        if not xa or not xb:
            return False
        return not (max(xa) < min(xb) or max(xb) < min(xa))      # ranges overlap
    return False


rows = []
for (key, field), g in C.groupby(["key", "field"]):
    ch = g[g.chosen == "yes"]
    ch = ch.iloc[0] if len(ch) else g.iloc[0]
    others = g[g.index != ch.name].drop_duplicates("value")
    if field in ("approval_date", "gazette_date", "release_date"):
        alts = others[others.value != ch.value]
        y0 = re.match(r"(\d{4})", ch.value)
        ys = [(int(m.group(1)), src_label(f)) for m, f in ((re.match(r"(\d{4})", v), f) for v, f in zip(alts.value, alts.local_file)) if m]
        d = max((abs(y - int(y0.group(1))) for y, _ in ys), default=0) if y0 else 0
        later_only = y0 and ys and all(y > int(y0.group(1)) for y, _ in ys)
        if field == "gazette_date" and later_only:
            cls = "later_notification"            # reprint or re-notification after the first gazette
        elif field == "approval_date" and later_only and all(sl in ("NSB minutes", "MoA hybrid list", "SCA annual list") for _, sl in ys) and d >= 1:
            cls = "later_decision"                 # extension, re-registration or full release after a provisional one
        else:
            cls = "date_same_year" if d == 0 else ("date_1_year" if d == 1 else "date_2plus_years")
    else:
        alts = others[[not compatible(field, ch.value, v) for v in others.value]]
        if alts.empty:
            cls = "compatible" if others.value.map(norm).nunique() > (1 if norm(ch.value) in set(others.value.map(norm)) else 0) else "formatting_only"
            alts = others[others.value.map(norm) != norm(ch.value)]
            if alts.empty: cls = "formatting_only"
        else:
            cls = "substantive"
    rows.append(dict(variety_id="RICE-" + key if not key.startswith("FISH") else "FISH-" + key[5:], field=field, classification=cls,
                     chosen_value=ch.value, chosen_source=src_label(ch.local_file), chosen_file=ch.local_file, chosen_page=ch.page,
                     n_versions=g.value.nunique(),
                     alternatives=" | ".join(f"{a.value} ({src_label(a.local_file)}, {a.local_file} p.{a.page})" for a in alts.drop_duplicates("value").itertuples()),
                     dissenting_sources="; ".join(sorted({src_label(f) for f in alts.local_file}))))
S = pd.DataFrame(rows)
S.to_csv(ROOT / "05_output/final/bgd_conflicts_summary.csv", index=False, encoding="utf-8-sig")

# pairwise: chosen source vs dissenting source, substantive only
sub = S[S.classification.isin(["substantive", "date_1_year", "date_2plus_years"])]
pairs = (sub.assign(d=sub.dissenting_sources.str.split("; ")).explode("d")
         .groupby(["field", "chosen_source", "d"]).size().reset_index(name="n").sort_values("n", ascending=False))

# systematic year offsets per dissenting source for approval dates
off = []
for r in C[C.field == "approval_date"].groupby("key"):
    g = r[1]; ch = g[g.chosen == "yes"]
    if not len(ch): continue
    y0 = re.match(r"(\d{4})", ch.iloc[0].value)
    if not y0: continue
    for a in g[g.chosen != "yes"].itertuples():
        m = re.match(r"(\d{4})", a.value)
        if m:
            off.append((src_label(a.local_file), int(m.group(1)) - int(y0.group(1))))
O = pd.DataFrame(off, columns=["source", "offset"])
offs = (O.groupby("source").offset.agg(n="size", same=lambda x: (x == 0).sum(), minus1=lambda x: (x == -1).sum(),
                                        plus1=lambda x: (x == 1).sum(), beyond=lambda x: (x.abs() >= 2).sum()).reset_index()
        .sort_values("n", ascending=False))

L = ["# Disagreements between sources", "",
     "Built from `05_output/final/bgd_conflicts.csv` (every version of every value). This report covers the fields that matter for analysis; "
     "the full per-variety table is `05_output/final/bgd_conflicts_summary.csv`.", "",
     "**How to read it.** The value in the register comes from the most authoritative source (NSB minutes, then gazette, then official lists, "
     "then institute records, then CGIAR records and literature). *Formatting only* means the same value written differently "
     "(spacing, hyphens, Bangla vs Latin digits). *Substantive* means the sources actually differ.", "",
     "## 1. Counts by field", "",
     "*Compatible* = versions that do not contradict (translation, one is a subset of the other, overlapping numeric ranges, a code with or without a suffix). "
     "*Later decision / later notification* = a later NSB decision (extension, re-registration, full release after a provisional one) or a reprinted gazette, not a disagreement.", "",
     "| field | varieties with >1 version | formatting only | compatible | later decision / notification | dates same year | dates 1 year apart | dates 2+ years apart | substantive |",
     "|---|---|---|---|---|---|---|---|---|"]
for f in FIELDS:
    s = S[S.field == f]
    if s.empty: continue
    vc = s.classification.value_counts()
    L.append(f"| {f} | {len(s)} | {vc.get('formatting_only', 0)} | {vc.get('compatible', 0)} | {vc.get('later_decision', 0) + vc.get('later_notification', 0)} | {vc.get('date_same_year', 0)} | {vc.get('date_1_year', 0)} | {vc.get('date_2plus_years', 0)} | {vc.get('substantive', 0)} |")
L += ["", "## 2. Release years: how each source compares with the NSB decision date", "",
      "Offset = year in that source minus the year of the NSB decision used in the register.", "",
      "| source | comparisons | same year | 1 year earlier | 1 year later | 2+ years off |", "|---|---|---|---|---|---|"]
for r in offs.itertuples():
    L.append(f"| {r.source} | {r.n} | {r.same} | {r.minus1} | {r.plus1} | {r.beyond} |")
L += ["", "Reading: a source that is often one year off is usually recording a different event (Technical Committee recommendation, "
      "season of first cultivation, or the year a list was printed), not an error in the NSB date.", "",
      "## 3. Which sources disagree with the value used (substantive disagreements only)", "",
      "| field | value taken from | disagreeing source | varieties |", "|---|---|---|---|"]
for r in pairs.head(30).itertuples():
    L.append(f"| {r.field} | {r.chosen_source} | {r.d} | {r.n} |")
for f, title in [("approval_date", "Approval dates 2+ years apart"), ("duration_days", "Durations that do not overlap"), ("yield_t_ha", "Yields that do not overlap"), ("season", "Seasons that differ"), ("breeding_line", "Breeding lines that differ"),
                 ("pedigree", "Pedigrees that differ"), ("release_category", "Approval route (release vs registration) differs"),
                 ("origin_country", "Origin country differs")]:
    s = S[(S.field == f) & S.classification.isin(["date_2plus_years", "substantive"])]
    if s.empty: continue
    L += ["", f"## {title} ({len(s)})", "", "| variety | in register (source) | other versions |", "|---|---|---|"]
    for r in s.itertuples():
        alt = r.alternatives.replace("|", "<br>")
        L.append(f"| {r.variety_id.replace('RICE-', '')} | {r.chosen_value} ({r.chosen_source}) | {alt} |")
(ROOT / "06_validation/conflicts_report.md").write_text("\n".join(L), encoding="utf-8")
print(S.classification.value_counts().to_string())
print(offs.to_string(index=False))
