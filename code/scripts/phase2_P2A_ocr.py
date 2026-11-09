"""P2A: OCR a list of PDFs (all pages or a page range) with lib_ocr (cached, resumable).
Usage: python phase2_P2A_ocr.py <pdf_rel>[:a-b] ...   (pages 1-based inclusive)"""
import sys, pathlib, fitz, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import ocr_pages, ROOT
for arg in sys.argv[1:]:
    pdf, _, rng = arg.partition(":")
    n = fitz.open(ROOT / pdf).page_count
    a, b = (int(x) for x in rng.split("-")) if rng else (1, n)
    for p in range(a - 1, min(b, n)):
        t = time.time(); ocr_pages(pdf, [p], psm=6)
        print(pdf, p + 1, round(time.time() - t, 1), flush=True)
