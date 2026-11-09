"""P2B: download BRRI Rice Profile listing pages and every per-variety page (sequential, lib_fetch).
Saves to 02_raw/brri_riceprofile/. Writes 04_working/P2B_scratch/riceprofile_index.csv (id, name)."""
import re, html, csv, pathlib
from lib_fetch import fetch, ROOT

BASE = "https://riceprofile.brri.gov.bd/varieties"
idx = {}
for pg in range(1, 10):
    url = BASE if pg == 1 else f"{BASE}?page={pg}"
    rel = f"brri_riceprofile/varieties_list_p{pg}.html"
    p = fetch(url, rel, agent="P2B", notes=f"BRRI Rice Profile variety listing page {pg}")
    t = (ROOT / p).read_text(encoding="utf-8", errors="replace")
    # each card: name ... link varieties/<id>
    for m in re.finditer(r'href="https://riceprofile\.brri\.gov\.bd/varieties/(\d+)"', t):
        vid = m.group(1)
        # name = nearest preceding heading text
        seg = t[max(0, m.start() - 3000):m.start()]
        hs = re.findall(r"<h\d[^>]*>(.*?)</h\d>", seg, re.S)
        name = html.unescape(re.sub(r"<[^>]+>|\s+", " ", hs[-1]).strip()) if hs else ""
        idx.setdefault(vid, name)
print(len(idx), "variety ids")
out = ROOT / "04_working/P2B_scratch"; out.mkdir(parents=True, exist_ok=True)
with open(out / "riceprofile_index.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["id", "name_listing"])
    for k in sorted(idx, key=int):
        w.writerow([k, idx[k]])
for k in sorted(idx, key=int):
    fetch(f"{BASE}/{k}", f"brri_riceprofile/variety_{int(k):03d}.html", agent="P2B",
          notes=f"BRRI Rice Profile variety page id {k}: {idx[k]}")
print("done")
