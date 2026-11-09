"""P2A helper: map each line of a converted/OCR text file (with '=== page N' markers) to page and
current NSB meeting (from minute headers). grep(pattern) -> list of (line_no, page, meeting, text)."""
import re, pathlib
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
HDR = re.compile(r"^\s*জাতী\S*\s+(?:\S+\s+)?বো\S*\s*([০-৯0-9]+)\s*তম.{0,15}সভার\s*কা\S*বরণী\s*$")
def load(path, header_from=0):
    lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    out, page, mtg = [], 0, None
    for i, l in enumerate(lines, 1):
        m = re.match(r"=== page (\d+)", l)
        if m: page = int(m.group(1)); continue
        h = HDR.search(l)
        if h and i >= header_from:
            mtg = int(h.group(1).translate(BN))
        out.append((i, page, mtg, l))
    return out
def grep(rows, pat):
    r = re.compile(pat)
    return [x for x in rows if r.search(x[3])]
if __name__ == "__main__":
    import sys
    rows = load(sys.argv[1], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
    for x in grep(rows, sys.argv[2]): print(*x, sep=" | ")
