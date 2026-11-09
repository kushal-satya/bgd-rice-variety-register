"""Show report-5 (meetings 58-75) unicode lines with the original ASCII (Latin-font) tokens from the raw
Bijoy layer, so Latin names/codes can be read as typed. Usage: python phase3_F3M_bijoyview.py <page_from> <page_to> [regex]"""
import re, sys, pathlib
R = pathlib.Path(__file__).resolve().parents[1] / "03_extracted/text/P2A"
uni = (R / "nsb_058-075_unicode.txt").read_text(encoding="utf-8").splitlines()
raw = (R / "nsb_058-075_raw.txt").read_text(encoding="utf-8", errors="replace").splitlines()
a, b = int(sys.argv[1]), int(sys.argv[2]); rx = re.compile(sys.argv[3]) if len(sys.argv) > 3 else None
page = 0
LAT = re.compile(r"\(([^()]*[0-9][^()]*)\)|\b([A-Z][A-Za-z]*[ .-]?[A-Za-z]*[ .-]?\d+[A-Za-z0-9.-]*)")
for u, r in zip(uni, raw):
    m = re.match(r"=== page (\d+)", u)
    if m:
        page = int(m.group(1)); continue
    if a <= page <= b and (rx is None or rx.search(u)):
        toks = [x[0] or x[1] for x in LAT.findall(r)]
        print(f"p{page}| {u.strip()[:230]}" + (f"  <<{' ; '.join(toks)}>>" if toks else ""))
