"""F6G: search NSB minutes (OCR cache + text layer converted with bijoy2unicode) for gazette/press/notification
mentions. Usage: python phase3_F6G_minutes_grep.py <bundle-glob> <regex>"""
import sys, glob, re, os, unicodedata, pathlib, fitz
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import ROOT
from bijoy2unicode import converter
sys.stdout.reconfigure(encoding="utf-8")
C = converter.Unicode(); N = lambda s: unicodedata.normalize("NFD", s)
pat = re.compile(N(sys.argv[2]))
for pdf in sorted(glob.glob(str(ROOT / f"02_raw/sca/{sys.argv[1]}.pdf"))):
    stem = pathlib.Path(pdf).stem; doc = fitz.open(pdf)
    for i, pg in enumerate(doc):
        srcs = []
        o = ROOT / f"03_extracted/text/ocr/{stem}/p{i+1:03d}_psm6.txt"
        if o.exists(): srcs.append(("ocr", o.read_text(encoding="utf-8", errors="replace")))
        t = pg.get_text()
        if len(t.strip()) > 100:
            srcs.append(("bijoy", "\n".join(C.convertBijoyToUnicode(l + "  ") for l in t.splitlines())))
            srcs.append(("text", t))
        for kind, s in srcs:
            s = N(s)
            for m in pat.finditer(s):
                ctx = s[max(0, m.start() - 220): m.end() + 220].replace("\n", " ")
                print(f"{stem} p{i+1} [{kind}] :: {unicodedata.normalize('NFC', ctx)}\n")
