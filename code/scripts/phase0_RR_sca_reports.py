"""Inventory SCA (sca.gov.bd) report listings: approved crop varieties, registered hybrid rice,
NSB minutes, TCNSB minutes. Lists rows (title, date, file url); does not download."""
import requests, re, time, json, csv, urllib.parse
from bs4 import BeautifulSoup
UA = {"User-Agent": "Mozilla/5.0 (research archive; contact via https://github.com/kushal-satya/bgd-rice-variety-register) python-requests"}
TYPES = {
 "approved_crop_varieties": "6a6f170926a072a44edf3848",
 "registered_hybrid_rice": "6a6f169dde9e97d4fd9ffd3b",
 "nsb_minutes": "6a3265509bb7fc5523e7cefd",
 "tcnsb_minutes": "6a3265c0dacdb576b0a0fbc7",
}
out = []
for name, tid in TYPES.items():
    page = 1
    while True:
        f = urllib.parse.quote(json.dumps({"reports_type": tid}, separators=(",", ":")))
        u = f"https://sca.gov.bd/pages/reports?filters={f}&page={page}"
        r = requests.get(u, headers=UA, verify=False, timeout=60)
        s = BeautifulSoup(r.text, "html.parser")
        cnt = s.find("span", class_="pagination-counts")
        rows = s.select("table.notice-table tbody tr.table-tr")
        n = 0
        for tr in rows:
            t = tr.find("td", attrs={"data-column": "title"})
            if not t: continue
            files = [a["href"] for a in tr.select('td[data-column="files"] a[href]')]
            d = tr.find("td", attrs={"data-column": "publish_date"})
            v = tr.select_one("td.print-none a[href]")
            out.append({"list": name, "page": page, "title": t.get_text(" ", strip=True),
                        "publish_date_bn": d.get_text(strip=True) if d else "",
                        "files": " | ".join(files), "detail": ("https://sca.gov.bd" + v["href"]) if v else ""})
            n += 1
        print(name, page, n, cnt.get_text(strip=True) if cnt else "", flush=True)
        nxt = s.find("a", class_="next-btn")
        time.sleep(2.5)
        if n == 0 or not nxt or page > 30: break
        page += 1
# dedupe (in case page param ignored)
seen=set(); ded=[]
for o in out:
    k=(o["list"],o["title"],o["files"])
    if k in seen: continue
    seen.add(k); ded.append(o)
with open("01_discovery/_parts/RR_sca_listing_inventory.csv","w",newline="",encoding="utf-8") as fh:
    w=csv.DictWriter(fh,fieldnames=list(ded[0].keys())); w.writeheader(); w.writerows(ded)
print("total unique", len(ded))
