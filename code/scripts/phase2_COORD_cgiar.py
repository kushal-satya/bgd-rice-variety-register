"""Coordinator rule: turn rank-1 cgiar_evidence rows (NSB minutes, MoA list, compendium) into
cgiar_role codes per crawl_plan 3a. Validation is inherited from the underlying evidence row,
so an unvalidated quote cannot produce an eligible code."""
import pandas as pd
e = pd.read_csv("04_working/evidence_P2A.csv", dtype=str, keep_default_na=False)
RULES = {  # pilot_key: (code, rule text), decided by reading the quoted evidence
    "IR8": ("1", "IRRI line (IR8) introduced directly; compendium labels it 'ইরি ধান'"),
    "BRRI_DHAN47": ("1", "NSB minutes: IRRI breeding line IR63307-4B-4-3 released as BRRI dhan47"),
    "BRRI_DHAN56": ("1", "NSB minutes: line derived at IRRI Philippines from IR 55419-4; released line IR74371-70-1-1"),
    "BINADHAN27": ("1", "NSB 115 minutes: line BN-P-318 collected from IRRI Philippines (IRRI-BINA collaboration)"),
    "BRRI_HYBRID1": ("1", "MoA cumulative hybrid list origin column 'ইরি' (IRRI)"),
    "BRRI_DHAN52": ("3", "NSB minutes: developed by BRRI in IRRI-BRRI collaboration"),
}
out = []
for _, r in e[e.field == "cgiar_evidence"].iterrows():
    if r.pilot_key not in RULES:
        continue
    code, rule = RULES[r.pilot_key]
    o = r.copy()
    o["field"], o["value"] = "cgiar_role", code
    o["method"] = r.method
    o["notes"] = f"coordinator rule from cgiar_evidence row: {rule}"
    out.append(o)
    c = r.copy(); c["field"], c["value"] = "cgiar_center", "IRRI"; c["notes"] = "from the same evidence row"
    out.append(c)
pd.DataFrame(out).to_csv("04_working/evidence_COORD.csv", index=False, encoding="utf-8")
print(len(out))
