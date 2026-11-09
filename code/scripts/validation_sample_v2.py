"""Second independent validation sample (seed 20261008): 25 random register rows (7 fields each), 15 random numeric attributes
from NSB decisions, 20 random official-list cells, 12 random fish government acts. Writes 06_validation/spot_check_sample_v2.csv."""
import pandas as pd
F = "05_output/final/"
S = 20261008
r = pd.read_csv(F + "bgd_rice_varieties.csv", dtype=str).fillna("")
ev = pd.read_csv("05_output/evidence_all.csv", dtype=str).fillna("")
rows = []
for _, x in r.sample(25, random_state=S).iterrows():
    k = x.variety_id[5:]
    for fld in ["official_name_bn", "approval_date", "approval_reference", "breeding_line", "gazette_date", "developer", "cgiar_role"]:
        if not x[fld]:
            continue
        e = ev[(ev.pilot_key == k) & (ev.field == fld) & (ev.value == x[fld]) & ev.eligible.astype(str).eq("True")]
        e = e.iloc[0] if len(e) else None
        rows.append(dict(part="register", row_id=x.variety_id, field=fld, table_value=x[fld], local_file=getattr(e, "local_file", ""),
                         page=getattr(e, "page", ""), locator=getattr(e, "locator", "")))
d = pd.read_csv(F + "bgd_nsb_decisions_full.csv", dtype=str).fillna("")
num = ["yield_t_ha", "yield_advantage_pct", "duration_days", "breeding_line", "check_variety", "dus_distinct_traits_n", "vcu_sites_n"]
long = d.melt(id_vars=["dec_id", "variety_id", "meeting_no", "source_file", "pages"], value_vars=[c for c in num if c in d], var_name="field", value_name="v")
long = long[long.v != ""].sample(15, random_state=S)
for x in long.itertuples():
    rows.append(dict(part="nsb_decision", row_id=f"{x.dec_id} {x.variety_id} NSB {x.meeting_no}", field=x.field, table_value=x.v, local_file=x.source_file, page=x.pages, locator=""))
o = pd.read_csv(F + "bgd_official_list_rows_full.csv", dtype=str).fillna("")
o = o[(o.cell_text_verbatim != "") & o.variety_id.ne("")].sample(20, random_state=S)
for x in o.itertuples():
    rows.append(dict(part="official_list_cell", row_id=f"{x.list_id} row {x.row_no} {x.variety_id}", field=x.column_header_as_printed,
                     table_value=x.cell_text_verbatim, local_file=x.source_file, page=x.page, locator=""))
a = pd.read_csv(F + "bgd_fish_approvals.csv", dtype=str).fillna("").sample(12, random_state=S)
for x in a.itertuples():
    for fld in ["approval_date", "approval_reference", "approval_type"]:
        rows.append(dict(part="fish_act", row_id=x.act_id, field=fld, table_value=getattr(x, fld), local_file=x.local_file, page=x.page, locator=x.quote[:150]))
out = pd.DataFrame(rows)
out.to_csv("06_validation/spot_check_sample_v2.csv", index=False, encoding="utf-8-sig")
print(out.part.value_counts().to_string(), len(out))
