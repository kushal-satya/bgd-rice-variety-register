"""Coordinator rule (crawl_plan 3a, code 3 = co-development documented in a CGIAR report/statement):
turn explicit CGIAR-original collaboration statements into cgiar_role 3 evidence. Applied only where the
statement names the variety and states joint development/release; generic or unnamed claims stay as flags."""
import pandas as pd
e = pd.read_csv("04_working/evidence_F3W.csv", dtype=str).fillna("")
RULES = {  # key: (source_id, code, center, lineage)
    "BRRI_DHAN33": ("F3W-W28", "3", "IRRI", "IRRI collaboration (stated by IRRI News: 'jointly invented in 1997 and validated by BRRI and IRRI')"),
    "BINADHAN17": ("F3W-W28", "3", "IRRI", "IRRI collaboration: Green Super Rice variety (GSR project, CAAS-IRRI), per IRRI News and CGIAR Rice MELIA 2019"),
}
out = []
for k, (sid, code, cen, lin) in RULES.items():
    r = e[(e.pilot_key == k) & (e.source_id == sid) & (e.field == "cgiar_independent")].iloc[0].copy()
    for f, v in [("cgiar_role", code), ("cgiar_center", cen), ("cgiar_lineage", lin)]:
        o = r.copy(); o["field"], o["value"] = f, v
        o["notes"] = "coordinator rule (code 3 = collaboration documented in a CGIAR report) from F3W cgiar_independent row"
        out.append(o)
pd.DataFrame(out).to_csv("04_working/evidence_COORD2.csv", index=False, encoding="utf-8")
print(len(out))
