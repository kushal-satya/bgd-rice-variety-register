"""F3I: crop the 'জাত পরিচিতি' (introduction) block of each OCR'd BRRI fact sheet for visual checking.
Block = from the line containing 'পরিচিতি' down to the line containing 'বৈশিষ্ট্য' (psm4 TSV), full width."""
import pathlib, sys, csv, glob
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import crop
ROOT = pathlib.Path(__file__).resolve().parents[1]
O = ROOT / "03_extracted/text/ocr"
for d in sorted(O.glob("BRRI_*")) + [O / "brri_variety_BRRIdhan115_2026-01"]:
    tsv = d / "p001_psm4.tsv"
    if not tsv.exists():
        continue
    rs = [r for r in csv.DictReader(open(tsv, encoding="utf-8", errors="replace"), delimiter="\t", quoting=csv.QUOTE_NONE) if r.get("text")]
    top = next((int(r["top"]) for r in rs if "পরিচিতি" in r["text"]), 200)
    hits = [int(r["top"]) for r in rs if any(k in r["text"] for k in ("ছাড়করণ", "ছাড়করণ", "অবমুক্ত", "অনুমোদন")) and int(r["top"]) > top]
    bot = (min(hits) + 90) if hits else top + 1400
    out = ROOT / f"04_working/crops/F3I/fs_{d.name.split('_')[0]}_{d.name.split('_')[1]}_{d.name.split('_')[2] if d.name.count('_')>1 else ''}_intro.png"
    out = ROOT / f"04_working/crops/F3I/fs_{d.name[:16]}_intro.png"
    crop(str(d / "p001.png"), (60, max(0, top - 30), 2420, bot - top + 40), str(out))
    print(out.name, top, bot)
