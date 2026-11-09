"""Download files to 02_raw/<slug>/ and append to FS_manifest.csv.
Usage: python phase0_FS_download.py items.json
items.json: list of {"url":..., "slug":..., "name":..., "notes":..., "archived_url":""}"""
import csv, json, os, sys, hashlib, time, datetime, requests, urllib3
urllib3.disable_warnings()
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[1])
MAN = os.path.join(ROOT, "01_discovery", "_parts", "FS_manifest.csv")
UA = {"User-Agent": "Mozilla/5.0 (research archive; contact via https://github.com/kushal-satya/bgd-rice-variety-register) python-requests"}
cols = ["file_path", "source_url", "archived_url", "download_date", "sha256", "file_type", "agent", "notes"]
done = set()
if os.path.exists(MAN):
    done = {r["source_url"] for r in csv.DictReader(open(MAN, encoding="utf-8"))}
items = json.load(open(sys.argv[1], encoding="utf-8"))
new = not os.path.exists(MAN)
with open(MAN, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new: w.writerow(cols)
    for it in items:
        if it["url"] in done:
            print("SKIP already", it["url"]); continue
        d = os.path.join(ROOT, "02_raw", it["slug"]); os.makedirs(d, exist_ok=True)
        try:
            r = requests.get(it["url"], headers=UA, timeout=180, verify=False)
        except Exception as e:
            print("ERR", it["url"], e); continue
        if r.status_code != 200:
            print("HTTP", r.status_code, it["url"]); continue
        p = os.path.join(d, it["name"]); open(p, "wb").write(r.content)
        h = hashlib.sha256(r.content).hexdigest()
        ft = it["name"].rsplit(".", 1)[-1].lower()
        w.writerow([os.path.relpath(p, ROOT).replace("\\", "/"), it["url"], it.get("archived_url", ""),
                    datetime.date.today().isoformat(), h, ft, "FS", it.get("notes", "")])
        f.flush(); done.add(it["url"])
        print("OK", len(r.content), p)
        time.sleep(3)
