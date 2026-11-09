"""P2F: polite crawl of fri.gov.bd static/publication pages (BFS from home, max N pages),
saves each page untouched under 02_raw/bfri/pages/ via lib_fetch.fetch, decodes the
base64 rt-renderer body to 03_extracted/text/P2F_fri/<id>.txt and writes an index CSV."""
import sys, re, base64, html, csv, pathlib, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_fetch
lib_fetch.NO_VERIFY.update({"fri.gov.bd"})  # incomplete TLS chain; decisions_P2F.md
from lib_fetch import fetch, ROOT

MAXN = int(sys.argv[1]) if len(sys.argv) > 1 else 400
OUT = ROOT / "03_extracted/text/P2F_fri"; OUT.mkdir(parents=True, exist_ok=True)
KINDS = ("static-pages", "publications", "files")
start = ["https://fri.gov.bd/"]
seen, queue, rows = set(), list(start), []


def decode(t):
    parts, links = [], []
    for enc in re.findall(r'encoded-content="([^"]+)"', t):
        try:
            h = base64.b64decode(enc + "=" * (-len(enc) % 4)).decode("utf-8", "replace")
        except Exception:
            continue
        links += re.findall(r'(?:href|src)="([^"]+)"', h)
        parts.append(re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip())
    return " ".join(parts), links


while queue and len(seen) < MAXN:
    u = queue.pop(0)
    if u in seen:
        continue
    seen.add(u)
    path = urllib.parse.urlparse(u).path
    pid = path.rstrip("/").split("/")[-1][-24:] or "home"
    kind = path.split("/")[2] if path.count("/") >= 3 else "home"
    rel = f"bfri/pages/{kind}_{pid}.html"
    try:
        p = fetch(u, rel, "P2F", "fri.gov.bd page (P2F crawl)")
    except Exception as e:
        print("ERR", u, e); continue
    t = (ROOT / p).read_text(encoding="utf-8", errors="replace")
    title = (re.findall(r"<title>(.*?)</title>", t, re.S) or [""])[0].strip()
    body, blinks = decode(t)
    (OUT / f"{kind}_{pid}.txt").write_text(title + "\n" + body + "\nLINKS: " + " ".join(blinks), encoding="utf-8")
    rows.append([u, p, title, len(body), " ".join(l for l in blinks if "objectstorage" in l)])
    for h in re.findall(r'href="(/pages/[^"#]+)"', t) + [l for l in blinks if l.startswith("/pages/") or "fri.gov.bd/pages/" in l]:
        h = html.unescape(h)
        full = urllib.parse.urljoin("https://fri.gov.bd/", h)
        parts = urllib.parse.urlparse(full).path.split("/")
        if len(parts) > 3 and parts[2] in KINDS and full not in seen and "?" not in full:
            queue.append(full)
    print(len(seen), title[:70], len(body))

with open(ROOT / "04_working/P2F_fri_crawl_index.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["url", "local_file", "title", "body_chars", "objectstorage_links"]); w.writerows(rows)
