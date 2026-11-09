"""F4: crop page regions around OCR lines matching a keyword (from lib_ocr TSV) for visual checks.
Usage: python phase3_F4_crops.py <ocr_dir_stem> <page1> <keyword> <out_name> [lines_before] [lines_after]"""
import sys, csv, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import crop, ROOT
stem, page, kw, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
b = int(sys.argv[5]) if len(sys.argv) > 5 else 1; a = int(sys.argv[6]) if len(sys.argv) > 6 else 1
d = ROOT / "03_extracted/text/ocr" / stem
rows = list(csv.DictReader(open(d / f"p{page:03d}_psm6.tsv", encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
lines = {}
for r in rows:
    if r["level"] != "5": continue
    k = (r["block_num"], r["par_num"], r["line_num"]); L = lines.setdefault(k, {"t": [], "box": []})
    L["t"].append(r["text"]); L["box"].append(tuple(int(r[x]) for x in ("left", "top", "width", "height")))
keys = sorted(lines, key=lambda k: min(bx[1] for bx in lines[k]["box"]))
hit = [i for i, k in enumerate(keys) if kw in " ".join(lines[k]["t"])]
if not hit: sys.exit("no hit")
i0, i1 = max(0, hit[0] - b), min(len(keys) - 1, hit[0] + a)
bx = [x for k in keys[i0:i1 + 1] for x in lines[k]["box"]]
top = min(x[1] for x in bx) - 15; bot = max(x[1] + x[3] for x in bx) + 15
o = ROOT / "04_working/crops/F4" / out
crop(str(d / f"p{page:03d}.png"), (0, top, 2600, bot - top), str(o)); print(o)
