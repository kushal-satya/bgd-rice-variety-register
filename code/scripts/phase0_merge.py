"""Merge per-agent Phase 0 part files into the 01_discovery deliverables and
append agent manifest rows to 02_raw/manifest.csv (deduplicated by file_path)."""
import csv, glob, os, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PARTS = ROOT / "01_discovery/_parts"
RANK_ORDER = ["1_primary_legal", "2_official_list", "3_institute_page",
              "4_cgiar_record", "5_peer_reviewed", "6_secondary"]


def read_parts(suffix):
    rows, header = [], None
    for p in sorted(glob.glob(str(PARTS / f"*_{suffix}.csv"))):
        with open(p, encoding="utf-8-sig", newline="") as f:
            r = csv.DictReader(f)
            header = header or r.fieldnames
            for row in r:
                row.setdefault("agent", os.path.basename(p).split("_")[0])
                rows.append(row)
    return header, rows


def write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{path.relative_to(ROOT)}: {len(rows)} rows")


h, rows = read_parts("search_log")
write(ROOT / "01_discovery/search_log.csv", h, rows)

h, rows = read_parts("existing_datasets")
order = {"high": 0, "medium": 1, "low": 2, "none": 3}
rows.sort(key=lambda r: order.get(r.get("backbone_potential", "").split()[0].lower()
                                  if r.get("backbone_potential") else "", 9))
write(ROOT / "01_discovery/existing_datasets.csv", h, rows)

h, rows = read_parts("sources_inventory")
rows.sort(key=lambda r: (RANK_ORDER.index(r["authority_rank"])
                         if r.get("authority_rank") in RANK_ORDER else 9, r.get("publisher", "")))
write(ROOT / "01_discovery/sources_inventory.csv", h, rows)

man = ROOT / "02_raw/manifest.csv"
with open(man, encoding="utf-8") as f:
    r = csv.DictReader(f)
    mh = r.fieldnames
    existing = list(r)
seen = {x["file_path"] for x in existing}
_, new = read_parts("manifest")
added = [x for x in new if x["file_path"] not in seen and not seen.add(x["file_path"])]
write(man, mh, existing + added)
