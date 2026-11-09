"""F3M: OCR every page of the NSB minutes (except the 058-075 text-layer bundle) with lib_ocr,
3 tesseract processes in parallel, cached and resumable. Also makes the TSV for pages whose
txt was cached by P2A without a TSV (needed for line crops). Progress -> logs/ocr_F3M.log.
Usage: python phase3_F3M_ocr.py
"""
import sys, pathlib, time, glob, subprocess
from multiprocessing import Pool
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fitz
from lib_ocr import ocr_pages, render, ROOT, OCR, TESS, TD

LOG = ROOT / "logs/ocr_F3M.log"


def job(args):
    pdf, p = args
    t = time.time()
    stem = pathlib.Path(pdf).stem
    base = OCR / stem / f"p{p+1:03d}_psm6"
    try:
        if not base.with_suffix(".txt").exists():
            ocr_pages(pdf, [p], psm=6)
        if not base.with_suffix(".tsv").exists():
            png = render(pdf, p)
            subprocess.run([TESS, str(png), str(base), "--tessdata-dir", TD, "-l", "ben+eng",
                            "--psm", "6", "-c", "tessedit_create_tsv=1", "-c", "tessedit_create_txt=0"],
                           capture_output=True)
        msg = f"{time.strftime('%H:%M:%S')} {stem} p{p+1} {time.time()-t:.0f}s"
    except Exception as e:
        msg = f"{time.strftime('%H:%M:%S')} {stem} p{p+1} ERROR {e}"
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(msg + "\n")
    return msg


if __name__ == "__main__":
    jobs = []
    files = sorted(glob.glob(str(ROOT / "02_raw/sca/nsb_minutes_*.pdf")))
    # singles first (most decisions in recent meetings), then bundles
    files = [f for f in files if "-" not in pathlib.Path(f).stem.split("_")[-1]] + \
            [f for f in files if "-" in pathlib.Path(f).stem.split("_")[-1]]
    for f in files:
        rel = str(pathlib.Path(f).relative_to(ROOT)).replace("\\", "/")
        n = fitz.open(f).page_count
        if "058-075" in rel:
            for p in range(n):
                render(rel, p)  # text layer bundle: only renders, for visual checks
            continue
        for p in range(n):
            stem = pathlib.Path(f).stem
            base = OCR / stem / f"p{p+1:03d}_psm6"
            if base.with_suffix(".txt").exists() and base.with_suffix(".tsv").exists():
                continue
            jobs.append((rel, p))
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(f"start {time.strftime('%Y-%m-%d %H:%M:%S')} jobs={len(jobs)}\n")
    with Pool(3) as pool:
        for m in pool.imap_unordered(job, jobs):
            pass
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(f"done {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
