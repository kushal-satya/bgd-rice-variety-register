"""F3H: render the SCA annual hybrid-rice registration lists (02_raw/sca/registered_hybrid_rice_*.pdf)
with PyMuPDF and save horizontal strip crops (full table width, ~3-5 table rows each) for visual
transcription, into 04_working/crops/F3H/sca_lists/.

Strip boxes were laid out by eye on 100-dpi overview renders, so all coordinates below are in
100-dpi pixels of the displayed (rotation-applied) page and are scaled to DPI at crop time.
Wide tables (>760 px at 100 dpi) additionally get left/right half crops (suffix _L / _R) so that
Bangla digits stay legible after image-viewer downscaling.

Usage: python phase3_F3H_sca_crops.py            (all strips)
       python phase3_F3H_sca_crops.py zoom FY PAGE X0 Y0 X1 Y1 NAME   (one extra zoom crop, 100-dpi coords)
"""
import sys, pathlib
import fitz  # PyMuPDF
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "02_raw" / "sca"
OUT = ROOT / "04_working" / "crops" / "F3H" / "sca_lists"
DPI = 300
WIDE = 760

# fy -> page -> (x0, x1, [(row_from, row_to, y0, y1), ...])
LAYOUT = {
    "2014-15": {1: (55, 765, [(1, 4, 30, 342), (5, 8, 335, 570), (9, 12, 560, 790)])},
    "2015-16": {1: (110, 728, [(1, 3, 110, 356), (4, 6, 348, 536), (7, 9, 528, 740), (10, 12, 730, 970)]),
                2: (110, 728, [(13, 16, 108, 390), (17, 21, 380, 750)])},
    "2016-17": {1: (50, 795, [(1, 3, 85, 310), (4, 7, 300, 575), (8, 11, 565, 770), (12, 14, 760, 995)])},
    "2017-18": {1: (45, 780, [(1, 3, 60, 490), (4, 7, 480, 865)])},
    "2018-19": {1: (80, 795, [(1, 5, 80, 550)])},
    "2019-20": {1: (45, 1040, [(1, 4, 30, 305), (5, 8, 298, 470), (9, 13, 462, 670)]),
                2: (45, 1040, [(1, 5, 85, 400)])},
    "2021-22": {1: (50, 818, [(1, 3, 105, 322), (4, 6, 315, 552)])},
    "2022-23": {1: (80, 1030, [(1, 4, 45, 345), (5, 8, 338, 548), (9, 11, 540, 702)])},
    "2023-24": {1: (120, 1085, [(1, 4, 75, 345), (5, 8, 338, 492), (9, 11, 484, 608)])},
    "2024-25": {1: (100, 1085, [(1, 4, 140, 472)])},
    "2025-26": {1: (130, 1160, [(1, 3, 115, 356), (4, 6, 345, 516), (7, 9, 505, 677)]),
                2: (130, 1160, [(10, 13, 120, 340), (14, 17, 330, 526), (18, 21, 515, 707)]),
                3: (130, 1160, [(22, 27, 120, 428)])},
}


def render(fy, page):
    doc = fitz.open(RAW / f"registered_hybrid_rice_{fy}.pdf")
    pix = doc[page - 1].get_pixmap(dpi=DPI)  # rotation is applied by get_pixmap
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def box(img, x0, y0, x1, y1, name):
    s = DPI / 100
    c = img.crop((int(x0 * s), int(y0 * s), int(x1 * s), int(y1 * s)))
    c.save(OUT / name)
    return name


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "zoom":
        fy, page = sys.argv[2], int(sys.argv[3])
        x0, y0, x1, y1 = map(int, sys.argv[4:8])
        print(box(render(fy, page), x0, y0, x1, y1, sys.argv[8]))
        return
    for fy, pages in LAYOUT.items():
        for page, (x0, x1, strips) in pages.items():
            img = render(fy, page)
            for a, b, y0, y1 in strips:
                stem = f"sca_{fy}_p{page}_r{a:02d}-{b:02d}"
                print(box(img, x0, y0, x1, y1, stem + ".png"))
                if x1 - x0 > WIDE:
                    mid = (x0 + x1) // 2
                    print(box(img, x0, y0, mid + 40, y1, stem + "_L.png"))
                    print(box(img, mid - 40, y0, x1, y1, stem + "_R.png"))


if __name__ == "__main__":
    main()
