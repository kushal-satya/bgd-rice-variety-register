"""F6G: crop the lines of a rendered OCR page that match a regex (from the lib_ocr TSV), with context lines,
into 04_working/crops/F6G/<name>.png. Usage: python phase3_F6G_crop.py <ocr_stem> <page1> <regex> <name> [ctx_lines]
If regex is 'FULL' the whole page is saved at reduced size; 'Y:top:bottom' crops a pixel band."""
import sys, csv, re, pathlib, unicodedata
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import crop, ROOT, OCR
import fitz
sys.stdout.reconfigure(encoding="utf-8")
stem, page, rx, name = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
ctx = int(sys.argv[5]) if len(sys.argv) > 5 else 1
png = OCR / stem / f"p{page:03d}.png"
out = ROOT / f"04_working/crops/F6G/{name}.png"
pm = fitz.Pixmap(str(png))
if rx.startswith("Y:"):
    _, a, b = rx.split(":"); crop(png, (0, int(a), pm.width, int(b) - int(a)), str(out)); print(out); sys.exit()
rows = list(csv.DictReader(open(OCR / stem / f"p{page:03d}_psm6.tsv", encoding="utf-8", errors="replace"), delimiter="\t", quoting=csv.QUOTE_NONE))
lines = {}
for r in rows:
    if r.get("level") != "5": continue
    k = (r["block_num"], r["par_num"], r["line_num"])
    L = lines.setdefault(k, {"t": [], "top": 10**9, "bot": 0})
    L["t"].append(r["text"]); L["top"] = min(L["top"], int(r["top"])); L["bot"] = max(L["bot"], int(r["top"]) + int(r["height"]))
keys = sorted(lines, key=lambda k: lines[k]["top"])
N = lambda s: unicodedata.normalize("NFD", s)
hit = [i for i, k in enumerate(keys) if re.search(N(rx), N(" ".join(lines[keys[i]]["t"])))]
if not hit: print("no match"); sys.exit(1)
a, b = max(0, min(hit) - ctx), min(len(keys) - 1, max(hit) + ctx)
top, bot = lines[keys[a]]["top"] - 15, lines[keys[b]]["bot"] + 15
crop(png, (0, top, pm.width, bot - top), str(out)); print(out, top, bot)
