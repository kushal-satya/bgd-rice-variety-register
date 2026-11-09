"""Convert SutonnyMJ/Bijoy-encoded text extracted from PDFs to Unicode Bangla (line by line).
Lines that are pure ASCII English (e.g. Times New Roman runs) will also be mangled, so keep originals."""
import sys
from bijoy2unicode import converter
c = converter.Unicode()
src, dst = sys.argv[1], sys.argv[2]
out = []
for line in open(src, encoding="utf-8"):
    line = line.rstrip("\n")
    if line.startswith("=== page"):
        out.append(line); continue
    try:
        out.append(c.convertBijoyToUnicode(line + "  ").rstrip())
    except Exception:
        out.append("[[UNCONVERTED]] " + line)
open(dst, "w", encoding="utf-8").write("\n".join(out))
