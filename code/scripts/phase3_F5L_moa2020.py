"""F5L: parse the MoA cumulative hybrid list edition '1998-16/03/2020' (02_raw/moa/item4_crop_varieties_page.pdf),
which no earlier agent parsed, with F3H's span/char-level parser (phase3_F3H_moa_spans.parse).
Writes 04_working/F5L/_F5L_moa2020_cells.csv. Values are text-layer parses (unvalidated unless key_check)."""
import csv, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from phase3_F3H_moa_spans import parse
rows = parse("02_raw/moa/item4_crop_varieties_page.pdf", "2020")
with open(ROOT / "04_working/F5L/_F5L_moa2020_cells.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
sers = [r["serial"] for r in rows]
print(len(rows), "max", max(sers), "missing", [s for s in range(1, max(sers) + 1) if s not in sers],
      "dups", sorted({s for s in sers if sers.count(s) > 1}), "nikosh", sum(1 for r in rows if r["nikosh_cols"]))
