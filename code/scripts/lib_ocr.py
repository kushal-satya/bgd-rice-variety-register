"""Free OCR helpers (Tesseract 5.4 + tessdata_best ben/eng), cached and resumable.

    from lib_ocr import ocr_pages, norm_digits, bn2int
    res = ocr_pages("02_raw/sca/nsb_minutes_115.pdf", [3, 4], psm=6)  # 0-based pages
    res[3]["text"], res[3]["tsv"], res[3]["png"]

Outputs are cached in 03_extracted/text/ocr/<pdf-stem>/p<NNN>_psm<k>.{txt,tsv} and the
300-dpi render in .../p<NNN>.png, so re-running is free. Crop helper for the review queue.
"""
import os, pathlib, shutil, subprocess, re
import fitz

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESS = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract") or __import__("os").path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe")
TD = str(ROOT / "tools/tessdata")
OCR = ROOT / "03_extracted/text/ocr"

BN = "০১২৩৪৫৬৭৮৯"
_bn2lat = str.maketrans(BN, "0123456789")


def render(pdf, page, dpi=300):
    out = OCR / pathlib.Path(pdf).stem / f"p{page+1:03d}.png"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(ROOT / pdf if not pathlib.Path(pdf).is_absolute() else pdf)
        doc[page].get_pixmap(dpi=dpi).save(out)
    return out


def ocr_pages(pdf, pages=None, psm=6, lang="ben+eng"):
    doc = fitz.open(ROOT / pdf if not pathlib.Path(pdf).is_absolute() else pdf)
    pages = range(doc.page_count) if pages is None else pages
    res = {}
    for p in pages:
        png = render(pdf, p)
        base = png.with_name(f"p{p+1:03d}_psm{psm}")
        if not base.with_suffix(".txt").exists():
            subprocess.run([TESS, str(png), str(base), "--tessdata-dir", TD, "-l", lang,
                            "--psm", str(psm), "txt", "tsv"], capture_output=True, check=True)   # an OCR failure stops the run
        res[p] = {"png": str(png.relative_to(ROOT)),
                  "text": base.with_suffix(".txt").read_text(encoding="utf-8", errors="replace"),
                  "tsv": str(base.with_suffix(".tsv").relative_to(ROOT))}
    return res


def norm_digits(s):
    """Bangla digits -> Latin. Does NOT touch OCR confusables; see fix_confusables."""
    return s.translate(_bn2lat)


def fix_confusables(s):
    """Candidate repair for numeric context: Latin '8' inside Bangla-digit runs is usually ৪,
    '¢' is usually ৫. Return the repaired string; callers must still validate the value."""
    return s.replace("¢", "৫").replace("8", "৪")


def bn2int(s):
    d = re.sub(r"\D", "", norm_digits(s))
    return int(d) if d else None


def crop(png, bbox, out):
    """Save a crop (left, top, width, height) of a rendered page for the review queue."""
    src = fitz.Pixmap(str(ROOT / png) if not pathlib.Path(png).is_absolute() else png)
    l, t, w, h = [int(v) for v in bbox]
    irect = fitz.IRect(l, t, l + w, t + h) & src.irect
    dst = fitz.Pixmap(src.colorspace, irect, src.alpha)
    dst.copy(src, irect)
    dst.set_origin(0, 0)
    dst.save(out)
    return out
