"""F6G: OCR every page of the scanned pre-2009 MoA extraordinary SROs (3 tesseract workers; cached by lib_ocr).
Progress -> logs/ocr_F6G.log. Usage: python phase3_F6G_ocr_sros.py [first_page_only]"""
import sys, glob, pathlib, datetime
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import ocr_pages, ROOT
import fitz

def job(a):
    pdf, p = a
    ocr_pages(pdf, [p], psm=6)
    return pdf, p

def main():
    first = "first" in sys.argv
    jobs = []
    for f in sorted(glob.glob(str(ROOT / "02_raw/bgpress/moa_extra_*.pdf"))):
        name = pathlib.Path(f).name
        yr = int(name.split("_")[2][-4:])
        if yr >= 2009: continue
        d = fitz.open(f)
        if ("--all" not in sys.argv) and sum(len(pg.get_text().strip()) for pg in d) > 200: continue  # text layer (garbled pre-2009 fonts: use --all)
        rel = str(pathlib.Path(f).relative_to(ROOT))
        jobs += [(rel, p) for p in (range(1) if first else range(d.page_count))]
    log = open(ROOT / "logs/ocr_F6G.log", "a", encoding="utf-8")
    log.write(f"{datetime.datetime.now()} start {len(jobs)} pages\n"); log.flush()
    with ProcessPoolExecutor(3) as ex:
        for i, (pdf, p) in enumerate(ex.map(job, jobs)):
            log.write(f"{datetime.datetime.now()} {i+1}/{len(jobs)} {pdf} p{p+1}\n"); log.flush()
    log.write(f"{datetime.datetime.now()} done\n")

if __name__ == "__main__":
    main()
