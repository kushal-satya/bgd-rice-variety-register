"""P2A: locate an OCR line by regex in the cached Tesseract TSV and save a crop of that line band
(full page width by default) into 04_working/crops/P2A/. Usage:
  python phase2_P2A_crop.py <pdf_stem> <page1> <regex> <out_name> [up_px] [down_px] [x0] [x1]"""
import sys, re, csv, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import crop, OCR, ROOT
csv.field_size_limit(10**8)
import subprocess
from lib_ocr import TESS, TD
def lines(stem, page):
    tsv = OCR / stem / f"p{page:03d}_psm6.tsv"
    if not tsv.exists():  # lib_ocr's 'tsv' config is not found in tools/tessdata (no configs dir): make it here
        png = OCR / stem / f"p{page:03d}.png"
        subprocess.run([TESS, str(png), str(tsv.with_suffix("")), "--tessdata-dir", TD, "-l", "ben+eng",
                        "--psm", "6", "-c", "tessedit_create_tsv=1"], capture_output=True)
    rows = list(csv.DictReader(open(tsv, encoding="utf-8", errors="replace"), delimiter="\t", quoting=csv.QUOTE_NONE))
    L = {}
    for r in rows:
        if r["level"] != "5" or not r["text"].strip(): continue
        k = (r["block_num"], r["par_num"], r["line_num"])
        L.setdefault(k, []).append(r)
    out = []
    for k, ws in L.items():
        l = min(int(w["left"]) for w in ws); t = min(int(w["top"]) for w in ws)
        rgt = max(int(w["left"]) + int(w["width"]) for w in ws); b = max(int(w["top"]) + int(w["height"]) for w in ws)
        out.append((t, l, rgt, b, " ".join(w["text"] for w in ws)))
    return sorted(out)
def find_crop(stem, page, rx, name, up=30, down=60, x0=None, x1=None, nth=0):
    hits = [x for x in lines(stem, page) if re.search(rx, x[4])]
    if not hits: return None
    t, l, r, b, txt = hits[min(nth, len(hits) - 1)]
    import fitz
    png = OCR / stem / f"p{page:03d}.png"
    W = fitz.Pixmap(str(png)).width
    X0 = 0 if x0 is None else x0; X1 = W if x1 is None else x1
    out = ROOT / "04_working/crops/P2A" / f"{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    crop(str(png), (X0, max(0, t - up), X1 - X0, (b - t) + up + down), str(out))
    return str(out.relative_to(ROOT)), txt, (X0, max(0, t - up), X1 - X0, (b - t) + up + down)
if __name__ == "__main__":
    a = sys.argv
    print(find_crop(a[1], int(a[2]), a[3], a[4], *(int(x) for x in a[5:])))
