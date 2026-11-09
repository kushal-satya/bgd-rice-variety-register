"""F3W: fetch CGIAR web pages listed in URLS (sequential via lib_fetch), dump text to scratch dir."""
import sys, pathlib, re
from phase3_F3W_lib import page, hits
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
lst = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
for line in lst:
    if not line.strip() or line.startswith("#"): continue
    url, rel = line.split()[:2]
    p, t = page(url, rel, "F3W CGIAR website statement")
    name = rel.replace("/", "__")
    if not p:
        print("FAIL", url, t); continue
    (OUT / (name + ".txt")).write_text(t, encoding="utf-8")
    h = hits(t)
    print(f"OK {rel} chars={len(t)} hits={len(h)}")
