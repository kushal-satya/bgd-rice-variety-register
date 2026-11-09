"""F4: OCR (lib_ocr, cached) for scanned/garbled fish-governance PDFs. Usage: python phase3_F4_ocr.py <pdf_rel> [maxpages]"""
import sys, pathlib, fitz
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import ocr_pages, ROOT
pdf = sys.argv[1]; mx = int(sys.argv[2]) if len(sys.argv) > 2 else 999
n = min(fitz.open(ROOT / pdf).page_count, mx)
res = ocr_pages(pdf, list(range(n)), psm=6)
out = ROOT / "03_extracted/text/F4/ocr" / (pathlib.Path(pdf).stem + ".txt"); out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(f"=== page {p+1}\n{r['text']}" for p, r in sorted(res.items())), encoding="utf-8")
print(pdf, n, "pages ->", out)
