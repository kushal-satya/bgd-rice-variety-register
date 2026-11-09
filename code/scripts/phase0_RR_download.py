"""Download a file untouched, write sha256 + manifest row to 01_discovery/_parts/RR_manifest.csv.
usage: python phase0_RR_download.py <url> <relative_dest_path> <file_type> "<notes>" [archived_url]"""
import requests, hashlib, csv, os, sys, datetime, time
UA = {"User-Agent": "Mozilla/5.0 (research archive; contact via https://github.com/kushal-satya/bgd-rice-variety-register) python-requests"}
MAN = "01_discovery/_parts/RR_manifest.csv"
COLS = ["file_path","source_url","archived_url","download_date","sha256","file_type","agent","notes"]
url, dest, ftype, notes = sys.argv[1:5]
arch = sys.argv[5] if len(sys.argv) > 5 else ""
if os.path.exists(MAN):
    for r in csv.DictReader(open(MAN, encoding="utf-8")):
        if r["source_url"] == url:
            print("already downloaded:", r["file_path"]); sys.exit(0)
fetch = arch if (arch and os.environ.get("FETCH_ARCHIVED")) else url
r = requests.get(fetch, headers=UA, verify=False, timeout=300)
r.raise_for_status()
os.makedirs(os.path.dirname(dest), exist_ok=True)
open(dest, "wb").write(r.content)
h = hashlib.sha256(r.content).hexdigest()
new = not os.path.exists(MAN)
with open(MAN, "a", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    if new: w.writerow(COLS)
    w.writerow([dest.replace("\\","/"), url, arch, datetime.date.today().isoformat(), h, ftype, "RR", notes])
print("saved", dest, len(r.content), h[:12], r.headers.get("content-type"))
time.sleep(2.5)
