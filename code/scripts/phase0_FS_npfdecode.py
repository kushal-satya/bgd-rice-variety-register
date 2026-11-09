"""Decode base64 <rt-renderer encoded-content> body from bangladesh.gov.bd (NPF v2) pages.
Usage: python phase0_FS_npfdecode.py page.html [...]  -> prints decoded text + links"""
import re, sys, base64, html
for fn in sys.argv[1:]:
    t = open(fn, encoding="utf-8").read()
    for enc in re.findall(r'encoded-content="([^"]+)"', t):
        h = base64.b64decode(enc + "=" * (-len(enc) % 4)).decode("utf-8", "replace")
        links = re.findall(r'(?:href|src)="([^"]+)"', h)
        txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()
        print("=====", fn); print(txt); print("LINKS:", links)
