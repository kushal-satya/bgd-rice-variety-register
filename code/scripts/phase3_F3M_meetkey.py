"""F3M: extend 04_working/nsb_meeting_key.csv (owned by F3M in Phase 3) with the meeting dates read from the
minutes' opening text (04_working/_F3M_meetings.tsv, each crop-checked) and merge any
04_working/nsb_meeting_key_additions_*.csv from other agents. Existing rows are kept; exact duplicates dropped.
Conflicting dates stay as separate rows. Re-runnable."""
import csv, glob, pathlib, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from phase3_F3M_build import src_info, tsv
W = pathlib.Path(__file__).resolve().parents[1] / "04_working"
COLS = ["meeting_no", "meeting_date", "source_file", "page", "method", "validation", "notes", "kind"]
rows = list(csv.DictReader(open(W / "nsb_meeting_key.csv", encoding="utf-8")))
seen = {(r["meeting_no"], r["meeting_date"], r["source_file"], str(r["page"]), r["kind"]) for r in rows}
added = 0
def add(r):
    global added
    k = (r["meeting_no"], r["meeting_date"], r["source_file"], str(r["page"]), r["kind"])
    if k in seen:
        for old in rows:
            ok = (old["meeting_no"], old["meeting_date"], old["source_file"], str(old["page"]), old["kind"])
            if ok == k and old["validation"] == "unvalidated" and r["validation"] != "unvalidated":
                old.update(r); added += 1
        return
    seen.add(k); rows.append(r); added += 1
for m in tsv(W / "_F3M_meetings.tsv"):
    stem = src_info(m["src"])[0]
    add({"meeting_no": m["mtg"], "meeting_date": m["date_iso"], "source_file": f"02_raw/sca/{stem}.pdf", "page": m["page"],
         "method": "bijoy2unicode" if m["src"] == "B5" else "ocr", "validation": m["validation"],
         "notes": f"F3M: minutes opening '{m['printed']}'; crop 04_working/crops/F3M/{m['crop']}" + (f"; {m['note']}" if m["note"] else ""),
         "kind": m["kind"]})
for f in sorted(glob.glob(str(W / "nsb_meeting_key_additions_*.csv"))):
    for r in csv.DictReader(open(f, encoding="utf-8")):
        r = {c: r.get(c, "") for c in COLS}
        r["notes"] = (r["notes"] + f" [merged from {pathlib.Path(f).name}]").strip()
        add(r)
rows.sort(key=lambda r: (int(r["meeting_no"]), r["meeting_date"]))
with open(W / "nsb_meeting_key.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
have = {int(r["meeting_no"]) for r in rows if r["validation"] in ("visual_check", "two_source") and r["kind"].startswith("minutes")}
print("rows", len(rows), "added", added, "meetings with validated minutes date:", len(have))
print("missing validated:", [m for m in range(1, 116) if m not in have])
