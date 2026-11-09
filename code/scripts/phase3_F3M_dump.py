"""F3M: concatenate cached OCR text of an NSB minutes PDF into 03_extracted/text/F3M/<stem>.txt
with '=== page N' markers, and print per-page rice keyword hit counts.
Usage: python phase3_F3M_dump.py <stem> [<stem> ...]"""
import sys, pathlib, re
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import OCR, ROOT
KW = re.compile(r"ধান|ধাণ|rice|Rice|RICE|paddy|ইরি|বিআর|ব্রি|বিনা|হাইব্রিড|হাইব্রীড|হাইৱিড|IR\s*\d|BR\s*\d|উফশী|উফসী")
out = ROOT / "03_extracted/text/F3M"; out.mkdir(parents=True, exist_ok=True)
for stem in sys.argv[1:]:
    d = OCR / stem
    pages = sorted(d.glob("p*_psm6.txt"))
    buf, hits = [], []
    for f in pages:
        n = int(f.name[1:4]); t = f.read_text(encoding="utf-8", errors="replace")
        buf.append(f"=== page {n}\n{t}")
        hits.append((n, len(KW.findall(t))))
    (out / f"{stem}.txt").write_text("\n".join(buf), encoding="utf-8")
    print(stem, len(pages), " ".join(f"{n}:{h}" for n, h in hits))
