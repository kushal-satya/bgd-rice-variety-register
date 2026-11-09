"""P2F: keyword search of NPF v2 datatable listing pages (mofl.gov.bd, fisheries.gov.bd, fri.gov.bd).
Usage: python phase2_P2F_npfsearch.py <base_listing_url> <term> [<term> ...]
Prints each hit (title, date, attachment links). Saves listing pages that have hits via lib_fetch."""
import sys, re, html, urllib.parse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_fetch
from lib_fetch import get, fetch
# fri.gov.bd / fisheries.gov.bd serve an incomplete TLS chain (same defect as sca.gov.bd); see decisions_P2F.md
lib_fetch.NO_VERIFY.update({"fri.gov.bd", "fisheries.gov.bd", "www.fisheries.gov.bd"})

base = sys.argv[1]
host = urllib.parse.urlparse(base).hostname.split(".")[0]
slug = base.rstrip("/").split("/")[-1]
for term in sys.argv[2:]:
    url = base + "?search=" + urllib.parse.quote(term) + "&page_size=100"
    r = get(url)
    tot = re.findall(r"মোট ([০-৯0-9]+) এন্ট্রি", r.text)
    rows = []
    for tr in re.findall(r"<tr.*?</tr>", r.text, re.S):
        cells = [html.unescape(re.sub(r"<[^>]+>", " ", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        links = [l for l in re.findall(r'href="([^"]+)"', tr) if "objectstorage" in l or "/pages/" in l]
        if cells:
            rows.append((cells, links))
    print(f"### {host}/{slug} '{term}': status {r.status_code}, total {tot}")
    for c, l in rows:
        print("  -", " | ".join(x for x in c[1:3] if x)[:260]); print("    ", l[:2])
    if rows:
        tl = urllib.parse.quote(term, safe="")[:40].replace("%", "")
        fetch(url, f"fish_governance/{host}/{host}_{slug}_search_{tl}.html", "F4", f"{host} {slug} listing search='{term}'")
