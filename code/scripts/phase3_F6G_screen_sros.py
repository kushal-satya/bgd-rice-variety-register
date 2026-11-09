"""F6G: screen every pre-2009 MoA extraordinary SRO (all pages, OCR cache) for seed/variety notifications.
Writes 04_working/F6G/sro_screen.csv (one row per SRO: date, SRO, pages, OCR pages, subject snippet, term hits)."""
import sys, glob, re, csv, pathlib, unicodedata
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import ROOT, OCR
import fitz
sys.stdout.reconfigure(encoding="utf-8")
N = lambda s: unicodedata.normalize("NFD", s)
TERMS = [r"Seeds? Ordinance", r"notified kinds?", r"\bvariet", r"\bpaddy\b", r"\brice\b", r"National Seed Board",
         "বীজ অধ্যাদেশ", "জাতীয় বীজ বোর্ড", "ধানের জাত", "ছাড়করণ", "ছাড়করন", "নোটিফাইড", "জাতসমূহ", r"বি,? ?আর[-– ]?\d"]
out = []
for f in sorted(glob.glob(str(ROOT / "02_raw/bgpress/moa_extra_*.pdf"))):
    name = pathlib.Path(f).stem; yr = int(name.split("_")[2][-4:])
    if yr >= 2009: continue
    d = fitz.open(f); txt = []; ocrp = 0
    for i in range(d.page_count):
        o = OCR / name / f"p{i+1:03d}_psm6.txt"
        if o.exists():
            ocrp += 1; txt.append(o.read_text(encoding="utf-8", errors="replace"))
        else:
            txt.append(d[i].get_text())
    full = N("\n".join(txt))
    hits = []
    for t in TERMS:
        n = len(re.findall(N(t), full, re.I))
        if n: hits.append(f"{t}:{n}")
    flat = re.sub(r"\s+", " ", unicodedata.normalize("NFC", full))
    m = re.search(r"(NOTIFICATION|প্রজ্ঞাপন|CORRIGENDUM)", flat)
    subj = flat[m.start(): m.start() + 300] if m else flat[:300]
    out.append(dict(file=f"02_raw/bgpress/{name}.pdf", date=name.split("_")[2], pages=d.page_count, ocr_pages=ocrp,
                    subject=subj, hits=";".join(hits)))
with open(ROOT / "04_working/F6G/sro_screen.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
for r in out: print(r["date"], r["pages"], r["ocr_pages"], "|", r["hits"], "|", r["subject"][:110])
