"""Fold 02_raw/_manifest_parts/*.csv into 02_raw/manifest.csv (dedupe by file_path)."""
import csv, glob, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
man = ROOT / "02_raw/manifest.csv"
rows = list(csv.DictReader(open(man, encoding="utf-8")))
h = list(rows[0].keys()); seen = {r["file_path"] for r in rows}; n = 0
for p in sorted(glob.glob(str(ROOT / "02_raw/_manifest_parts/*.csv"))):
    for r in csv.DictReader(open(p, encoding="utf-8")):
        if r["file_path"] not in seen:
            seen.add(r["file_path"]); rows.append(r); n += 1
with open(man, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=h); w.writeheader(); w.writerows(rows)
print("added", n, "total", len(rows))
