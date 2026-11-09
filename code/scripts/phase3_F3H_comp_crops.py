"""Phase 3 / F3H: render hybrid-rice table pages and save horizontal strip crops
for visual (by-eye) transcription.

Sources
  A. 02_raw/sca/approved_varieties_notified_crops_bangladesh_2016.pdf, PDF pp. 27-33
     (printed pp. 17-23, "হাইব্রিড ধানের নিবন্ধিত জাত"; vector page, no text layer).
     Table rules are detected automatically (clean vector render).
  B. 02_raw/moa_wayback/hybrid_rice_list_1998-2016.pdf, PDF pp. 1-6 (skewed scan).
     Rule detection is unreliable on the scan, so strip y-ranges were set by eye
     from 300-dpi renders with a pixel ruler (MOA_CUTS below; generous overlap).

Each strip = the page's header row + N body rows at full table width.
Strip names carry the serial range they are meant to cover (verified by eye).

Outputs
  04_working/crops/F3H/compendium/comp_p{pdfpage}_s{a:02d}-{b:02d}.png
  04_working/crops/F3H/moa2016/moa16_p{pdfpage}_s{a:02d}-{b:02d}.png
  plus *_full.png page renders and *_foot.png / *_summary.png extras.
"""
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "04_working" / "crops" / "F3H"
DPI = 300
COMP_PDF = ROOT / "02_raw/sca/approved_varieties_notified_crops_bangladesh_2016.pdf"
MOA_PDF = ROOT / "02_raw/moa_wayback/hybrid_rice_list_1998-2016.pdf"

# MoA 2016 list: (pdf_page, header_y0, header_y1, [(first_serial, last_serial, y0, y1), ...])
MOA_X = (230, 2265)
MOA_CUTS = [
    (1, 415, 540, [(1, 6, 530, 915), (7, 10, 900, 1400), (11, 15, 1385, 1895),
                   (16, 20, 1880, 2270), (21, 25, 2255, 2735), (26, 29, 2710, 3095)]),
    (2, 285, 405, [(30, 35, 395, 1040), (36, 41, 1020, 1645), (42, 47, 1625, 2245),
                   (48, 53, 2225, 2775), (54, 57, 2750, 3195)]),
    (3, 275, 400, [(58, 65, 390, 1065), (66, 73, 1045, 1505), (74, 79, 1485, 1895),
                   (80, 85, 1875, 2445), (86, 91, 2425, 2965), (92, 94, 2945, 3175)]),
    (4, 345, 460, [(95, 100, 450, 960), (101, 106, 945, 1550), (107, 112, 1530, 2170),
                   (113, 117, 2150, 2695), (118, 120, 2675, 3075)]),
    (5, 270, 385, [(121, 125, 375, 940), (126, 130, 925, 1505), (131, 136, 1485, 2015),
                   (137, 143, 1995, 2585), (144, 149, 2565, 3025)]),
    (6, 285, 405, [(150, 154, 395, 1030), (155, 158, 1010, 1555), (159, 161, 1535, 2015)]),
]


def render(pdf, pno, dpi=DPI):
    pix = fitz.open(pdf)[pno].get_pixmap(dpi=dpi)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def stack(header, body):
    canvas = Image.new("RGB", (body.width, header.height + body.height), "white")
    canvas.paste(header, (0, 0))
    canvas.paste(body, (0, header.height))
    return canvas


def comp_rules(img):
    """Horizontal rules of the clean vector table: rows >=80% dark across the table."""
    g = np.asarray(img.convert("L"))
    m = g < 150
    h, w = g.shape
    cf = m[:, 60:w - 60].mean(axis=0)
    xs = np.where(cf > 0.3)[0] + 60
    x0, x1 = int(xs.min()), int(xs.max())
    sm = m[:, x0:x1 + 1].copy()
    for k in (1, 2, 3, 4):
        sm[k:] |= m[:-k, x0:x1 + 1]
    ys = np.where(sm.mean(axis=1) > 0.8)[0]
    groups = []
    for y in ys:
        if groups and y - groups[-1][-1] <= 8:
            groups[-1].append(y)
        else:
            groups.append([y])
    lines = [int(np.mean(gp)) for gp in groups]
    # drop filled bars (e.g. the red title bar on p.27): gap interior mostly dark
    keep = []
    for i, y in enumerate(lines):
        if i + 1 < len(lines):
            inner = m[y + 8:lines[i + 1] - 8, x0:x1 + 1]
            if inner.size and inner.mean() > 0.5:
                continue
        above = m[max(y - 30, 0):max(y - 12, 0), x0:x1 + 1]
        if above.size and above.mean() > 0.5:  # bottom edge of a filled bar
            continue
        keep.append(y)
    return keep, x0, x1


def comp(per_strip=5):
    outdir = OUT / "compendium"
    outdir.mkdir(parents=True, exist_ok=True)
    serial = 0
    for pno in range(26, 33):
        img = render(COMP_PDF, pno)
        img.save(outdir / f"comp_p{pno + 1}_full.png")
        ys, x0, x1 = comp_rules(img)
        pad = 10
        X0, X1 = max(x0 - pad, 0), min(x1 + pad, img.width)
        header = img.crop((X0, ys[0] - pad, X1, ys[1] + pad))
        body = list(zip(ys[1:-1], ys[2:]))
        for i in range(0, len(body), per_strip):
            rows = body[i:i + per_strip]
            strip = img.crop((X0, rows[0][0] - pad, X1, rows[-1][1] + pad))
            a, b = serial + i + 1, serial + i + len(rows)
            stack(header, strip).save(outdir / f"comp_p{pno + 1}_s{a:02d}-{b:02d}.png")
        # page foot (printed page number) and anything above the table
        img.crop((0, ys[-1], img.width, img.height)).save(outdir / f"comp_p{pno + 1}_foot.png")
        img.crop((0, 0, img.width, ys[0] + pad)).save(outdir / f"comp_p{pno + 1}_top.png")
        print("comp", pno + 1, "body rows", len(body), "serials", serial + 1, "-", serial + len(body))
        serial += len(body)


def moa():
    outdir = OUT / "moa2016"
    outdir.mkdir(parents=True, exist_ok=True)
    X0, X1 = MOA_X
    for page, hy0, hy1, cuts in MOA_CUTS:
        img = render(MOA_PDF, page - 1)
        img.save(outdir / f"moa16_p{page}_full.png")
        header = img.crop((X0, hy0, X1, hy1))
        for a, b, y0, y1 in cuts:
            stack(header, img.crop((X0, y0, X1, y1))).save(outdir / f"moa16_p{page}_s{a:02d}-{b:02d}.png")
        if page == 1:
            img.crop((X0, 250, X1, 420)).save(outdir / "moa16_p1_title.png")
        img.crop((X0 - 100, cuts[-1][3] - 40, X1 + 100, img.height)).save(outdir / f"moa16_p{page}_foot.png")
        print("moa16", page, [(a, b) for a, b, _, _ in cuts])


if __name__ == "__main__":
    comp()
    moa()
