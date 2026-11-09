"""Write 05_output/final/bgd_evidence.csv: the long-format evidence behind every register value, for publication.

    python scripts/build_evidence_public.py

Input: 05_output/evidence_all.csv (written by scripts/assemble.py), the released register tables in 05_output/final and
04_working/key_remap.csv. Output columns:
  variety_id, field, value, value_raw, source_title, authority_rank, local_file, page, locator, method, validation, chosen, notes

variety_id is RICE-<key> for rice and FISH-<key> for fish strains and events, as in the register. chosen = Y marks the row
that set the published value of that field: the row the conflicts table records as chosen where sources disagree; otherwise
the eligible row (text layer or validated reading) whose value equals the published value, the highest-authority one if
several do; for list fields (aliases, key_traits, lineage...) every eligible row whose value appears in the published list.
All other rows are N. Every text cell passes through redact_personal.text(), which removes mobile numbers, e-mail addresses
other than institutional office addresses, and mailto= parameters.
"""
import pathlib
import re
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import redact_personal as RP

ROOT = pathlib.Path(__file__).resolve().parents[1]
F = ROOT / "05_output/final"
OUT = F / "bgd_evidence.csv"
COLS = ["variety_id", "field", "value", "value_raw", "source_title", "authority_rank", "local_file", "page", "locator",
        "method", "validation", "chosen", "notes"]


def norm(v):   # as scripts/assemble.py norm()
    return re.sub(r"[\s\-–_.,;:()]+", "", str(v)).lower()


def vid(key):
    return "FISH-" + key[5:] if key.startswith("FISH_") else "RICE-" + key


def main():
    ev = pd.read_csv(ROOT / "05_output/evidence_all.csv", dtype=str, keep_default_na=False)
    remap = pd.read_csv(ROOT / "04_working/key_remap.csv", dtype=str, keep_default_na=False)
    ev["pilot_key"] = ev.pilot_key.replace(dict(zip(remap.old_key, remap.new_key)))
    ev["variety_id"] = ev.pilot_key.map(vid)
    ev["local_file"] = ev.local_file.str.replace("\\", "/", regex=False)
    ev["rank_n"] = pd.to_numeric(ev.authority_rank.str.extract(r"^(\d)")[0], errors="coerce").fillna(9)
    ev["vw"] = ev.validation.map({"two_source": 0, "key_check": 1, "visual_check": 1}).fillna(2)
    ev["cw"] = ev.confidence.map({"high": 0, "medium": 1, "low": 2}).fillna(3)
    elig = ev.eligible.astype(str).str.lower().eq("true")

    # published values: {(id, field): cell}
    pub = {}
    for name, idc in [("bgd_rice_varieties.csv", "variety_id"), ("bgd_rice_not_approved_or_unresolved.csv", "variety_id"),
                      ("bgd_fish_strains.csv", "strain_id"), ("bgd_fish_events.csv", "event_id")]:
        d = pd.read_csv(F / name, dtype=str, keep_default_na=False)
        for c in d.columns:
            if c not in (idc, "source_url"):   # the register's source_url is the main source's address, not the evidence field
                for i, v in zip(d[idc], d[c]):
                    if v.strip():
                        pub[(i, c)] = v
    chosen = pd.Series("N", index=ev.index)

    # 1. where sources disagree, the conflicts table records the chosen row
    cf = pd.read_csv(F / "bgd_conflicts.csv", dtype=str, keep_default_na=False)
    cf = cf[cf.chosen.eq("yes")]
    cf_key = set()
    idx = ev.assign(_k=list(zip(ev.pilot_key, ev.field, ev.local_file, ev.value, ev.page)))
    first = idx[elig].drop_duplicates("_k").set_index("_k").index
    pos = dict(zip(first, idx[elig].drop_duplicates("_k").index))
    for r in cf.itertuples():
        k = (r.key, r.field, r.local_file.replace("\\", "/"), r.value, r.page)
        if k in pos:
            chosen[pos[k]] = "Y"; cf_key.add((vid(r.key), r.field))

    # 2. otherwise, rows whose value is the published value
    for (i, f), g in ev[elig].groupby(["variety_id", "field"]):
        if (i, f) in cf_key or (i, f) not in pub:
            continue
        cell = pub[(i, f)]
        items = [x for x in cell.split(" | ") if x.strip()]
        nitems = {norm(x) for x in items} | {norm(cell)}
        m = g[g.value.map(norm).isin(nitems)]
        if m.empty:
            continue
        if len(items) > 1:
            chosen[m.index] = "Y"
        else:
            chosen[m.sort_values(["rank_n", "vw", "cw"]).index[0]] = "Y"
    ev["chosen"] = chosen

    out = ev[COLS].copy()
    for c in COLS:
        if c not in ("variety_id", "field", "chosen", "local_file"):
            out[c] = out[c].map(RP.text)
    out = out.sort_values(["variety_id", "field", "chosen"], ascending=[True, True, False], kind="stable")
    out.to_csv(OUT, index=False, encoding="utf-8-sig")
    n_pub = sum(1 for k in pub if k[1] in set(ev.field))
    covered = out[out.chosen == "Y"].groupby(["variety_id", "field"]).ngroups
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out):,} rows, {out.variety_id.nunique()} ids, {out.local_file.nunique()} files; "
          f"chosen=Y {int((out.chosen == 'Y').sum()):,} rows covering {covered:,} of {n_pub:,} published (id, field) cells that have evidence fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())
