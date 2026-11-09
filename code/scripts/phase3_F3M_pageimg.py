"""Save a reduced full-page image (for reading matrix-format minutes by eye) into 04_working/crops/F3M/.
Usage: python phase3_F3M_pageimg.py <nnn> <page> [top_frac bottom_frac scale]"""
import sys, pathlib
from PIL import Image
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import OCR, render
n, p = sys.argv[1], int(sys.argv[2])
a, b, s = (float(x) for x in (sys.argv[3:6] if len(sys.argv) > 5 else (0.03, 0.97, 0.6)))
stem = f"nsb_minutes_{n}"
png = OCR / stem / f"p{p:03d}.png"
if not png.exists():
    render(f"02_raw/sca/{stem}.pdf", p - 1)
im = Image.open(png); W, H = im.size
out = pathlib.Path(__file__).resolve().parents[1] / "04_working/crops/F3M" / f"s{n}_p{p}_{int(a*100)}.png"
im.crop((0, int(H * a), W, int(H * b))).resize((int(W * s), int(H * (b - a) * s))).save(out)
print(out.name)
