"""F3I: OCR (ben+eng, psm 4) page 1 of the gap BRRI fact sheets (byte-identical duplicates skipped).
Cached by lib_ocr. Log: logs/ocr_F3I.log. Usage: python phase3_F3I_ocr_factsheets.py <pdf_rel> [...]
(dhan109-115 were OCR'd earlier with psm 4 and 6, pages 1-2; dhan118 by P2B.)"""
import pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import ocr_pages
ROOT = pathlib.Path(__file__).resolve().parents[1]
log = open(ROOT / "logs/ocr_F3I.log", "a", encoding="utf-8")
for rel in sys.argv[1:]:
    t = time.time()
    ocr_pages(rel, [0], psm=4)
    log.write(f"{time.strftime('%H:%M:%S')} {rel} psm4 page1 {time.time() - t:.0f}s\n")
    log.flush()
log.write("DONE batch\n")
log.close()
