"""Download a document into 02_raw/<slug>/ and append a manifest row (RB).
Usage: python phase0_RB_dl.py URL slug filename "notes" """
import requests, sys, time, os, hashlib, csv, datetime
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[1])
UA = "Mozilla/5.0 (research archive; contact via https://github.com/kushal-satya/bgd-rice-variety-register) python-requests"
url, slug, fn, notes = sys.argv[1:5]
MAN = os.path.join(ROOT, "01_discovery", "_parts", "RB_manifest.csv")
cols = ["file_path","source_url","archived_url","download_date","sha256","file_type","agent","notes"]
if os.path.exists(MAN):
    for row in csv.DictReader(open(MAN, encoding="utf-8")):
        if row["source_url"] == url:
            print("ALREADY", row["file_path"]); sys.exit(0)
time.sleep(2.5)
r = requests.get(url, headers={"User-Agent": UA}, timeout=180, verify=False)
r.raise_for_status()
d = os.path.join(ROOT, "02_raw", slug); os.makedirs(d, exist_ok=True)
p = os.path.join(d, fn)
open(p, "wb").write(r.content)
sha = hashlib.sha256(r.content).hexdigest()
ft = fn.rsplit(".", 1)[-1].lower()
new = not os.path.exists(MAN)
with open(MAN, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new: w.writerow(cols)
    w.writerow([f"02_raw/{slug}/{fn}", url, "", datetime.date.today().isoformat(), sha, ft, "RB", notes])
print("SAVED", p, len(r.content), r.headers.get("content-type"))
