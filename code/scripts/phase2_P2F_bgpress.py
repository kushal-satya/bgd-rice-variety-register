"""P2F: list MoFL (ministry=55) extraordinary gazettes on dpp.gov.bd/bgpress via the
search form (POST), using the lib_fetch throttle and UA. Saves the result HTML and an index.
Usage: python phase2_P2F_bgpress.py [ministry_id] [label]"""
import sys, csv, re, pathlib, requests, datetime
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import _throttle, UA, RAW, register_existing, ROOT
from bs4 import BeautifulSoup

URL = "https://dpp.gov.bd/bgpress/index.php/document/extraordinary_gazettes/285"
mid = sys.argv[1] if len(sys.argv) > 1 else "55"
label = sys.argv[2] if len(sys.argv) > 2 else "mofl"
_throttle("dpp.gov.bd")
data = {"submited": "1", "publication_date": "", "ministry": mid, "keyword": "", "case": "",
        "subject": "", "eng_memo": "", "eng_date": "", "ben_memo": "", "ben_date": ""}
r = requests.post(URL, data=data, headers={"User-Agent": UA}, timeout=120)
print(r.status_code, len(r.content))
rel = f"bgpress/bgpress_{label}_extraordinary_search_m{mid}.html"
out = RAW / rel
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(r.content)
register_existing(rel, URL + f" [POST ministry={mid}]", "P2F", f"bgpress extraordinary gazette list, ministry={mid} ({label})")
s = BeautifulSoup(r.text, "html.parser")
rows = []
for tr in s.find_all("tr"):
    tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
    links = [a["href"] for a in tr.find_all("a", href=True) if "upload_file" in a["href"] or a["href"].endswith(".pdf")]
    if links and tds:
        rows.append((" || ".join(t for t in tds if t), links[0]))
idx = ROOT / f"04_working/P2F_bgpress_{label}_index.csv"
with open(idx, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["cells_joined", "pdf_url"]); w.writerows(rows)
print(len(rows), "rows ->", idx)
