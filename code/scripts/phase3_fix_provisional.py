"""Inbreds released provisionally and later fully released: approval_date must be the full release.
For each key in the NSB decision register with decision_type 'release_provisional' AND a later 'release',
move the provisional meeting's approval_date/approval_reference evidence to provisional_release_* fields.
(Hybrid 'registration_provisional' is the approval event itself and is not touched.)"""
import pandas as pd
d = pd.read_csv("04_working/F3M_decisions_index.csv", dtype=str).fillna("")
ev = pd.read_csv("04_working/evidence_F3M.csv", dtype=str).fillna("")
out = []
for key, g in d.groupby("pilot_key"):
    prov = g[g.decision_type == "release_provisional"]
    full = g[g.decision_type == "release"]
    if prov.empty or full.empty:
        continue
    for _, p in prov.iterrows():
        if full.meeting_date.max() <= p.meeting_date:
            continue
        rows = ev[(ev.pilot_key == key) & (ev.field.isin(["approval_date", "approval_reference"]))
                  & ev.value.str.contains(p.meeting_date if True else "") | ((ev.pilot_key == key) & (ev.field == "approval_reference")
                  & ev.value.str.contains(rf"NSB {p.meeting_no}(?:st|nd|rd|th) meeting"))]
        rows = rows[rows.pilot_key == key]
        for _, r in rows.iterrows():
            if r.field == "approval_date" and r.value != p.meeting_date:
                continue
            out.append(dict(agent="F3M", pilot_key=key, field=r.field, value=r.value, action="refield",
                            new_field="provisional_release_date" if r.field == "approval_date" else "provisional_release_reference",
                            new_value="", reason=f"NSB {p.meeting_no} was a provisional release; full release at a later meeting (decision register)"))
pd.DataFrame(out).drop_duplicates().to_csv("04_working/evidence_corrections_provisional.csv", index=False, encoding="utf-8")
print(len(out), "rows moved;", sorted({o['pilot_key'] for o in out}))
