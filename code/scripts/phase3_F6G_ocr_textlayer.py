"""F6G: OCR the pre-2009 MoA SROs whose text layer is garbled legacy font (sequential, logged)."""
import sys, glob, pathlib, datetime, fitz
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import ocr_pages, ROOT
log = open(ROOT / "logs/ocr_F6G_textlayer.log", "a", encoding="utf-8")
for f in sorted(glob.glob(str(ROOT / "02_raw/bgpress/moa_extra_*.pdf"))):
    name = pathlib.Path(f).name; yr = int(name.split("_")[2][-4:])
    if yr >= 2009: continue
    d = fitz.open(f)
    if sum(len(p.get_text().strip()) for p in d) <= 200: continue
    rel = str(pathlib.Path(f).relative_to(ROOT))
    for p in range(d.page_count):
        try:
            ocr_pages(rel, [p], psm=6); msg = "ok"
        except Exception as e:
            msg = f"ERR {e}"
        log.write(f"{datetime.datetime.now()} {name} p{p+1}/{d.page_count} {msg}\n"); log.flush()
log.write(f"{datetime.datetime.now()} done\n")
