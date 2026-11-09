"""Phase 1 feasibility test: render sample pages at 300 dpi and OCR with free Tesseract (ben+eng)."""
import fitz, subprocess, pathlib, sys
TESS = __import__("os").path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe")
TD = "tools/tessdata"
OUT = pathlib.Path("logs/ocr_test")
tests = [("02_raw/sca/approved_varieties_notified_crops_bangladesh_2016.pdf", [2, 3]),
         ("02_raw/moa/hybrid_rice_varieties_list_2026-02-05.pdf", [0]),
         ("02_raw/sca/approved_crop_varieties_2014-15.pdf", [0]),
         ("02_raw/sca/nsb_minutes_115.pdf", [3])]
for f, pages in tests:
    doc = fitz.open(f)
    print(f, "pages:", doc.page_count)
    for p in pages:
        if p >= doc.page_count: continue
        stem = OUT / f"{pathlib.Path(f).stem}_p{p+1}"
        doc[p].get_pixmap(dpi=300).save(f"{stem}.png")
        for psm in ("6",):
            subprocess.run([TESS, f"{stem}.png", f"{stem}_psm{psm}", "--tessdata-dir", TD,
                            "-l", "ben+eng", "--psm", psm], capture_output=True)
