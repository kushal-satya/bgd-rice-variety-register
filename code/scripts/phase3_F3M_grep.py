"""Reading aid: grep a regex in one F3M source text within a page range. Usage: python phase3_F3M_grep.py <src> <p0> <p1> <regex>"""
import sys, re
sys.stdout.reconfigure(encoding="utf-8")
import phase3_F3M_build as B
src, a, b, rx = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
P = B.pages_of(src)
for p in range(a, b + 1):
    for u in P.get(p, []):
        if re.search(B.norm(rx), u):
            print(p, u[:170])
