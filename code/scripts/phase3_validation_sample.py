"""Draw the validation sample: 25 random rice rows (seed 20261006) + all fish strain and event rows.
For each sampled row, list the evidence behind the checked fields so a checker can open the page."""
import pandas as pd
r = pd.read_csv("05_output/rice_varieties.csv", dtype=str).fillna("")
f = pd.read_csv("05_output/fish_strains.csv", dtype=str).fillna("")
fe = pd.read_csv("05_output/fish_events.csv", dtype=str).fillna("")
ev = pd.read_csv("05_output/evidence_all.csv", dtype=str).fillna("")
s = r.sample(25, random_state=20261006)
CHECK_R = ["official_name_bn", "approval_date", "approval_reference", "breeding_line", "gazette_date", "developer", "cgiar_role"]
CHECK_F = ["strain_name", "release_date", "approval_or_release_mechanism", "releasing_body", "generation", "cgiar_role"]
rows = []
for _, x in s.iterrows():
    k = x.variety_id.replace("RICE-", "")
    for fld in CHECK_R:
        e = ev[(ev.pilot_key == k) & (ev.field == fld) & (ev.value == x[fld]) & ev.eligible.astype(str).eq("True")]
        e = e.iloc[0] if len(e) else None
        rows.append(dict(row_id=x.variety_id, field=fld, table_value=x[fld],
                         local_file="" if e is None else e.local_file, page="" if e is None else e.page,
                         locator="" if e is None else e.locator, value_raw="" if e is None else e.value_raw))
for df, idc in [(f, "strain_id"), (fe, "event_id")]:
    for _, x in df.iterrows():
        k = x[idc].replace("FISH-", "FISH_", 1)
        for fld in CHECK_F:
            if fld not in x or not x[fld]:
                continue
            e = ev[(ev.pilot_key == k) & (ev.field == fld) & (ev.value == x[fld])]
            e = e.iloc[0] if len(e) else None
            rows.append(dict(row_id=x[idc], field=fld, table_value=x[fld],
                             local_file="" if e is None else e.local_file, page="" if e is None else e.page,
                             locator="" if e is None else e.locator, value_raw="" if e is None else e.value_raw))
out = pd.DataFrame(rows)
out = out[out.table_value != ""]
out.to_csv("06_validation/spot_check_sample.csv", index=False, encoding="utf-8-sig")
print(len(s), "rice rows;", len(f) + len(fe), "fish rows;", len(out), "field checks")
print(s.variety_id.tolist())
