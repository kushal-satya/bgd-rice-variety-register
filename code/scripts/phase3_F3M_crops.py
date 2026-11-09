"""F3M batch crops for visual checks. A spec file (TSV: label, src, page, regex[, nth]) lists the lines to check.
Without a Tesseract TSV the vertical position is estimated from the line's index in the page text, so each
crop is a generous band (default 14% of page height) centred on that estimate; with a TSV (if cached) the
band is tight. Crops are stacked 4 per image with a label bar: 04_working/crops/F3M/<prefix>_NN.png.
Usage: python phase3_F3M_crops.py <spec.tsv> <prefix> [per_image] [band_frac]"""
import sys, re, csv, pathlib
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import phase3_F3M_build as B
from lib_ocr import OCR, render
ROOT = B.ROOT
OUT = ROOT / "04_working/crops/F3M"; OUT.mkdir(parents=True, exist_ok=True)
csv.field_size_limit(10**8)
try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
except Exception:
    FONT = ImageFont.load_default()


def png_for(src, page):
    stem = B.src_info(src)[0]
    p = OCR / stem / f"p{page:03d}.png"
    if not p.exists():
        render(f"02_raw/sca/{stem}.pdf", page - 1)
    return p


def tsv_lines(stem, page):
    t = OCR / stem / f"p{page:03d}_psm6.tsv"
    if not t.exists():
        return None
    L = {}
    for r in csv.DictReader(open(t, encoding="utf-8", errors="replace"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if r["level"] != "5" or not (r["text"] or "").strip():
            continue
        L.setdefault((r["block_num"], r["par_num"], r["line_num"]), []).append(r)
    out = []
    for ws in L.values():
        t0 = min(int(w["top"]) for w in ws); b0 = max(int(w["top"]) + int(w["height"]) for w in ws)
        out.append((t0, b0, " ".join(w["text"] for w in ws)))
    return sorted(out)


def text_lines(im):
    """Detect text lines by horizontal ink projection; returns [(top, bottom)]."""
    import numpy as np
    g = np.asarray(im.convert("L"), dtype=np.uint8)
    W = g.shape[1]
    ink = (g < 140)[:, int(W * 0.06):int(W * 0.94)].sum(axis=1)
    rows = ink > max(8, W * 0.004)
    runs, start = [], None
    for y, v in enumerate(rows):
        if v and start is None:
            start = y
        elif not v and start is not None:
            runs.append([start, y]); start = None
    if start is not None:
        runs.append([start, len(rows)])
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] < 10:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [(a, b) for a, b in merged if 18 <= b - a <= 200]


_RAW = None


def b5_bbox(page, rxn, nth):
    """Use the Bijoy text layer: find the unicode line, take the aligned raw line and search it on the PDF page."""
    global _RAW
    import fitz
    R = ROOT / "03_extracted/text/P2A"
    if _RAW is None:
        uni = (R / "nsb_058-075_unicode.txt").read_text(encoding="utf-8").splitlines()
        raw = (R / "nsb_058-075_raw.txt").read_text(encoding="utf-8", errors="replace").splitlines()
        _RAW = (uni, raw)
    uni, raw = _RAW
    pg, hits = 0, []
    for u, r in zip(uni, raw):
        m = re.match(r"=== page (\d+)", u)
        if m:
            pg = int(m.group(1)); continue
        if pg == page and rxn.search(B.norm(u)):
            hits.append(r)
    if not hits:
        return None
    r = hits[min(nth, len(hits) - 1)].strip()
    doc = fitz.open(ROOT / "02_raw/sca/nsb_minutes_058-075.pdf")
    pdfp = doc[page - 1]
    sc = 842.0 / pdfp.rect.height
    for k in (40, 25, 15, 8):
        q = r[:k].strip()
        if len(q) < 4:
            continue
        rs = pdfp.search_for(q)
        if rs:
            return rs[0].y0 * sc, rs[0].y1 * sc + 40
    return None


def band(src, page, rx, nth=0, frac=0.14):
    png = png_for(src, page)
    im = Image.open(png)
    W, H = im.size
    stem = B.src_info(src)[0]
    rxn = re.compile(B.norm(rx))
    T = tsv_lines(stem, page) if src != "B5" else None
    if T:
        hits = [x for x in T if rxn.search(B.norm(x[2]))]
        if hits:
            t0, b0, _ = hits[min(nth, len(hits) - 1)]
            return im.crop((0, max(0, t0 - 70), W, min(H, b0 + 90))), "tsv"
    if src == "B5":
        r = b5_bbox(page, rxn, nth)
        if r:
            y0, y1 = r
            sc = H / 842.0
            return im.crop((0, max(0, int(y0 * sc) - 90), W, min(H, int(y1 * sc) + 90))), "pdf"
    L = [u for u in B.pages_of(src).get(page, []) if u.strip()]
    idx = [i for i, u in enumerate(L) if rxn.search(u)]
    if not idx:
        return None, "nohit"
    i = idx[min(nth, len(idx) - 1)]
    bands = text_lines(im)
    if src != "B5" and abs(len(bands) - len(L)) <= max(2, len(L) // 8):
        j = min(i, len(bands) - 1)
        t0 = bands[max(0, j - 1)][0]; b0 = bands[min(len(bands) - 1, j + 1)][1]
        return im.crop((0, max(0, t0 - 20), W, min(H, b0 + 20))), f"proj{len(bands)}/{len(L)}"
    y = 0.06 * H + (i + 0.5) / max(1, len(L)) * 0.88 * H
    h = frac * H
    return im.crop((0, int(max(0, y - h / 2)), W, int(min(H, y + h / 2)))), "est"


def main():
    spec, prefix = sys.argv[1], sys.argv[2]
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    frac = float(sys.argv[4]) if len(sys.argv) > 4 else 0.14
    rows = [l.rstrip("\n").split("\t") for l in open(spec, encoding="utf-8") if l.strip() and not l.startswith("#")]
    tiles = []
    for r in rows:
        label, src, page, rx = r[:4]
        nth = int(r[4]) if len(r) > 4 and r[4] else 0
        im, how = band(src, int(page), rx, nth, frac)
        if im is None:
            print("MISS", label, src, page, rx); continue
        tiles.append((f"{label}  [{src} p{page} {how}]", im))
    n = 0
    for k in range(0, len(tiles), per):
        grp = tiles[k:k + per]
        Wm = max(t[1].size[0] for t in grp)
        Ht = sum(t[1].size[1] + 50 for t in grp)
        canvas = Image.new("RGB", (Wm, Ht), "white")
        y = 0
        d = ImageDraw.Draw(canvas)
        for lab, im in grp:
            d.rectangle((0, y, Wm, y + 48), fill=(255, 230, 150))
            d.text((10, y + 4), lab, fill="black", font=FONT)
            canvas.paste(im.convert("RGB"), (0, y + 50))
            y += im.size[1] + 50
        n += 1
        out = OUT / f"{prefix}_{n:02d}.png"
        canvas.save(out)
        print(out.relative_to(ROOT), " | ".join(t[0] for t in grp))


if __name__ == "__main__":
    main()
