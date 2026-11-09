"""Fill manifest archived_url: use an existing Wayback capture if one exists, else ask
Save Page Now (anonymous) to capture the source URL. Slow by design (archive.org 8 s throttle,
plus a 20 s pause after each SPN request). Resumable: rows that already have archived_url are skipped.

    python scripts/archive_wayback.py [--only-used FILE.csv] [--max N]

--only-used: restrict to file paths listed in a CSV column 'local_file' (e.g. 05_output/sources.csv).
Results are logged in logs/wayback_archive.log; failures stay blank and are listed at the end.
"""
import csv, os, sys, time, json, pathlib, argparse, logging
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import get, ROOT

logging.basicConfig(filename=ROOT / "logs/wayback_archive.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")
ap = argparse.ArgumentParser(); ap.add_argument("--only-used"); ap.add_argument("--max", type=int, default=10**9)
a = ap.parse_args()
man = ROOT / "02_raw/manifest.csv"
rows = list(csv.DictReader(open(man, encoding="utf-8"))); h = list(rows[0].keys())
used = None
if a.only_used:
    used = [r["local_file"].replace("\\", "/") for r in csv.DictReader(open(a.only_used, encoding="utf-8"))]


BACKOFF = [120, 300, 900, 1800, 3600]   # waits on 429/503/timeouts; never switch endpoint or identity
SPN_PAUSE = 60                           # steady pace: at most one capture per minute


def call(url, timeout):
    """GET with patient retries on rate limits and transient errors. Returns a response or None."""
    for wait in BACKOFF + [None]:
        try:
            r = get(url, timeout=timeout, allow_redirects=True)
            if r.status_code not in (429, 502, 503, 504, 520, 523):
                return r
            why = r.status_code
        except Exception as e:  # noqa  (timeouts, resets)
            why = type(e).__name__
        if wait is None:
            logging.info("giving up after backoff: %s %s", why, url); return None
        logging.info("%s from archive.org, sleeping %s s", why, wait); time.sleep(wait)


def available(url):
    r = call("https://archive.org/wayback/available?url=" + url, 60)
    if r is None or r.status_code != 200:
        return None
    try:
        snap = r.json().get("archived_snapshots", {}).get("closest")
    except ValueError:
        return None
    return snap["url"] if snap and snap.get("available") else ""


def save(url):
    r = call("https://web.archive.org/save/" + url, 180)
    time.sleep(SPN_PAUSE)
    if r is None:
        return ""
    loc = r.headers.get("Content-Location") or (r.url if "/web/" in r.url else "")
    if loc and loc.startswith("/web/"):
        loc = "https://web.archive.org" + loc
    logging.info("SPN %s %s %s", r.status_code, url, loc)
    return loc if r.status_code == 200 and loc else ""


def checkpoint(path, cap):
    """Write one archived_url into the manifest as it is NOW on disk (another job, such as a rebuild, may have changed
    other rows since this run started), then replace the file atomically."""
    cur = list(csv.DictReader(open(man, encoding="utf-8"))); hh = list(cur[0].keys())
    for x in cur:
        if x["file_path"] == path and not x.get("archived_url"):
            x["archived_url"] = cap
    tmp = man.with_suffix(".csv.tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=hh); w.writeheader(); w.writerows(cur)
    os.replace(tmp, man)


if used is not None:   # work through the target list in its own order (most important files first)
    order = {k: i for i, k in enumerate(used)}
    rows.sort(key=lambda x: order.get(x["file_path"].replace("\\", "/"), 10**9))
done = fail = 0
for r in rows:
    if done >= a.max:
        break
    url = r.get("source_url", "")
    if r.get("archived_url") or not url.startswith("http") or "web.archive.org" in url:
        if "web.archive.org" in url and not r.get("archived_url"):
            r["archived_url"] = url  # the source itself is a Wayback capture
        continue
    if used is not None and r["file_path"].replace("\\", "/") not in order:
        continue
    cap = available(url)
    if cap is None:
        fail += 1; continue
    if cap == "":
        cap = save(url)
    r["archived_url"] = cap; done += 1; fail += (cap == "")
    if cap:
        checkpoint(r["file_path"], cap)
    print(time.strftime("%Y-%m-%d %H:%M"), "done", done, "unarchived", fail, "|", "OK " + cap if cap else "FAILED " + url, flush=True)
print("processed", done, "unarchived", fail)
