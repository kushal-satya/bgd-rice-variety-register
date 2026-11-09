"""F5M: ruled-table handling for OCR'd NSB minutes (the two-column 'আলোচনা | সিদ্ধান্ত' matrix of NSB 96+ and the
hybrid list tables), so table text is read cell by cell instead of being scrambled across columns.
  python phase3_F5M_tables.py grid  <stem> [<stem>...]   -> 03_extracted/text/F5M/grid/<stem>.json   (table rules per page)
  python phase3_F5M_tables.py cells <stem> [<stem>...]   -> 03_extracted/text/ocr_cells/<stem>/pNNN_tK_rR_cC.{txt,tsv,png}
Cell OCR = Tesseract ben+eng psm 6 on the cell crop (rules trimmed). Cached; re-runnable. Progress -> logs/ocr_F5M.log"""
import sys, json, pathlib, subprocess, time
import numpy as np
from PIL import Image
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import OCR, ROOT, TESS, TD
from phase3_F5M_grid import tables
Image.MAX_IMAGE_PIXELS = None
G = ROOT / "03_extracted/text/F5M/grid"; G.mkdir(parents=True, exist_ok=True)
CELLS = ROOT / "03_extracted/text/ocr_cells"
LOG = ROOT / "logs/ocr_F5M.log"


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def do_grid(stem):
    out = G / f"{stem}.json"
    res = json.loads(out.read_text()) if out.exists() else {}
    pngs = sorted((OCR / stem).glob("p[0-9][0-9][0-9].png"))
    for p in pngs:
        if p.name in res:
            continue
        res[p.name] = tables(p)
        out.write_text(json.dumps(res))
    log(f"grid {stem}: {len(pngs)} pages, {sum(1 for v in res.values() if v)} with tables")


def do_cells(stem):
    res = json.loads((G / f"{stem}.json").read_text())
    od = CELLS / stem; od.mkdir(parents=True, exist_ok=True)
    n = 0
    for pn, tabs in sorted(res.items()):
        if not tabs:
            continue
        im = None
        for k, t in enumerate(tabs):
            xs, ys = t["x"], t["y"]
            for r in range(len(ys) - 1):
                for c in range(len(xs) - 1):
                    base = od / f"{pn[:-4]}_t{k}_r{r:02d}_c{c}"
                    if base.with_suffix(".txt").exists():
                        continue
                    if im is None:
                        im = Image.open(OCR / stem / pn).convert("L")
                    box = (xs[c] + 7, ys[r] + 6, xs[c + 1] - 6, ys[r + 1] - 5)
                    if box[2] - box[0] < 25 or box[3] - box[1] < 20:
                        base.with_suffix(".txt").write_text("", encoding="utf-8"); continue
                    cr = im.crop(box)
                    if (np.asarray(cr) < 140).mean() < 0.002:
                        base.with_suffix(".txt").write_text("", encoding="utf-8"); continue
                    cr.save(base.with_suffix(".png"))
                    subprocess.run([TESS, str(base.with_suffix(".png")), str(base), "--tessdata-dir", TD, "-l", "ben+eng",
                                    "--psm", "6", "txt", "tsv"], capture_output=True, check=False)
                    n += 1
        log(f"cells {stem} {pn}: done")
    log(f"cells {stem}: {n} new cells OCR'd")


if __name__ == "__main__":
    mode = sys.argv[1]
    for stem in sys.argv[2:]:
        (do_grid if mode == "grid" else do_cells)(stem)
