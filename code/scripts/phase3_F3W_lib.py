"""F3W helpers: fetch a page via lib_fetch (logged, once) and return plain text."""
import re, sys, pathlib, html, csv, datetime
from lib_fetch import fetch, get, ROOT
LOG = ROOT / "04_working/F3W_fetchlog.csv"

def log(url, status, rel, note=""):
    new = not LOG.exists()
    with open(LOG, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new: w.writerow(["date", "url", "status", "local_file", "note"])
        w.writerow([datetime.date.today().isoformat(), url, status, rel, note])

def page(url, rel, notes=""):
    """Fetch url into 02_raw/cgiar_web/<rel>; return (local_path, text) or (None, status)."""
    try:
        p = fetch(url, "cgiar_web/" + rel, agent="F3W", notes=notes)
    except Exception as e:
        log(url, f"ERR {str(e)[:120]}", "", notes); return None, str(e)[:200]
    log(url, "ok", p, notes)
    return p, text_of(p)

def text_of(p):
    fp = ROOT / p
    if fp.suffix.lower() == ".pdf":
        import fitz
        d = fitz.open(fp); return "\n".join(f"[[p{i+1}]] " + pg.get_text() for i, pg in enumerate(d))
    b = fp.read_bytes().decode("utf-8", "replace")
    b = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", b)
    b = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h\d>|</tr>|</div>", "\n", b)
    t = html.unescape(re.sub(r"<[^>]+>", " ", b))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t)

VAR = re.compile(r"(BRRI\s*dhan\s*-?\s*\d+|BRRI\s*hybrid\s*dhan\s*-?\s*\d+|Bina\s*dhan\s*-?\s*\d+|Binadhan\s*-?\s*\d+|\bBR\s?-?\d{1,2}\b|IR\s?\d{2,6}[-\w]*|Swarna[- ]Sub1|BR11[- ]Sub1|NERICA\s*-?\s*\d+|BU\s+(?:Aromatic\s+)?(?:Hybrid\s+)?Dhan\s*-?\s*\d+|GIFT|rohu|G3)", re.I)

def hits(t, width=220):
    out = []
    for m in VAR.finditer(t):
        out.append(t[max(0, m.start()-width): m.end()+width].replace("\n", " "))
    return out

if __name__ == "__main__":
    url, rel = sys.argv[1], sys.argv[2]
    p, t = page(url, rel, sys.argv[3] if len(sys.argv) > 3 else "")
    print(p)
    if p:
        out = pathlib.Path(sys.argv[4]) if len(sys.argv) > 4 else None
        if out: out.write_text(t, encoding="utf-8")
        print(len(t)); print(t[:int(sys.argv[5]) if len(sys.argv)>5 else 6000])
