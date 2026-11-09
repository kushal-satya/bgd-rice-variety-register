"""F6G: list extraordinary gazettes on dpp.gov.bd/bgpress for a ministry id (POST form, lib_fetch throttle/UA).
Saves the HTML under 02_raw/bgpress/ and an index CSV in 04_working/F6G/.
Usage: python phase3_F6G_bgpress_lists.py <ministry_id> <label>"""
import sys, csv, re, pathlib, requests
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import _throttle, UA, RAW, register_existing, ROOT, already
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding="utf-8")
URL = "https://dpp.gov.bd/bgpress/index.php/document/extraordinary_gazettes/285"
mid, label = sys.argv[1], sys.argv[2]
rel = f"bgpress/bgpress_{label}_extraordinary_search_m{mid}.html"
out = RAW / rel
if not out.exists():
    _throttle("dpp.gov.bd")
    data = {"submited": "1", "publication_date": "", "ministry": mid, "keyword": "", "case": "",
            "subject": "", "eng_memo": "", "eng_date": "", "ben_memo": "", "ben_date": ""}
    r = requests.post(URL, data=data, headers={"User-Agent": UA}, timeout=180)
    print(r.status_code, len(r.content))
    out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(r.content)
    register_existing(rel, URL + f" [POST ministry={mid}]", "F6G", f"bgpress extraordinary gazette list, ministry={mid} ({label})")
s = BeautifulSoup(out.read_text(encoding="utf-8", errors="replace"), "html.parser")
rows = []
for tr in s.find_all("tr"):
    tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
    links = [a["href"] for a in tr.find_all("a", href=True) if "upload_file" in a["href"] or a["href"].endswith(".pdf")]
    if links and tds:
        rows.append((" || ".join(t for t in tds if t), links[0]))
idx = ROOT / f"04_working/F6G/bgpress_{label}_m{mid}_index.csv"
with open(idx, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["cells_joined", "pdf_url"]); w.writerows(rows)
print(len(rows), "rows ->", idx)
