"""P2A: extract the SutonnyMJ text layer of a PDF page by page and convert to Unicode (bijoy2unicode).
Usage: python phase2_P2A_bijoy.py <pdf_rel> <out_stem>. Writes 03_extracted/text/P2A/<out_stem>_raw.txt and _unicode.txt"""
import sys, pathlib, fitz
from bijoy2unicode import converter
ROOT = pathlib.Path(__file__).resolve().parents[1]
c = converter.Unicode()
pdf, stem = sys.argv[1], sys.argv[2]
doc = fitz.open(ROOT / pdf)
raw, uni = [], []
for i, p in enumerate(doc):
    raw.append(f"=== page {i+1}"); uni.append(f"=== page {i+1}")
    for line in p.get_text().splitlines():
        raw.append(line)
        try:
            uni.append(c.convertBijoyToUnicode(line + "  ").rstrip())
        except Exception:
            uni.append("[[UNCONVERTED]] " + line)
out = ROOT / "03_extracted/text/P2A"; out.mkdir(parents=True, exist_ok=True)
(out / f"{stem}_raw.txt").write_text("\n".join(raw), encoding="utf-8")
(out / f"{stem}_unicode.txt").write_text("\n".join(uni), encoding="utf-8")
