"""Polite, manifest-aware downloader shared by all phases.

    from lib_fetch import fetch
    path = fetch(url, "sca/nsb_minutes_040.pdf", agent="P2A", notes="...")

- One request per THROTTLE_S seconds per host, enforced across processes
  (a lock file and a timestamp file per host under logs/.throttle/).
- Never downloads a URL or path that already appears in 02_raw/manifest.csv or any
  02_raw/_manifest_parts/*.csv; it returns the existing local path instead.
- Writes the file untouched and appends a manifest row (sha256, date) to
  02_raw/_manifest_parts/<agent>.csv. Merge with scripts/merge_manifest.py.
- TLS verification is off only for hosts in NO_VERIFY (incomplete certificate chains,
  logged in decisions_log 2026-10-06).
Wayback archiving is done centrally afterwards (scripts/archive_wayback.py).
"""
import csv, datetime, hashlib, os, pathlib, time, glob, urllib.parse, logging
import requests, urllib3

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "02_raw"
PARTS = RAW / "_manifest_parts"
THR = ROOT / "logs/.throttle"
THROTTLE_S = 2.5
HOST_THROTTLE = {"web.archive.org": 8.0, "archive.org": 8.0}  # Wayback rate-limits hard
NO_VERIFY = {"sca.gov.bd", "www.sca.gov.bd", "brri.gov.bd", "www.brri.gov.bd", "bina.gov.bd", "www.bina.gov.bd", "fri.gov.bd", "www.fri.gov.bd", "fisheries.gov.bd", "www.fisheries.gov.bd",
             "riceprofile.brri.gov.bd"}
UA = "bgd-variety-archive/0.1 (academic research; contact via https://github.com/kushal-satya/bgd-rice-variety-register)"
HEADER = ["file_path", "source_url", "archived_url", "download_date", "sha256",
          "file_type", "agent", "notes"]
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
PARTS.mkdir(parents=True, exist_ok=True); THR.mkdir(parents=True, exist_ok=True)
(ROOT / "logs").mkdir(exist_ok=True)
logging.basicConfig(filename=ROOT / "logs/fetch.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")


def _manifest_rows():
    files = [RAW / "manifest.csv"] + [pathlib.Path(p) for p in glob.glob(str(PARTS / "*.csv"))]
    for f in files:
        if f.exists():
            with open(f, encoding="utf-8-sig", newline="") as fh:
                yield from csv.DictReader(fh)


def already(url=None, rel=None):
    """Return the existing manifest row for this URL or relative path, else None."""
    relp = ("02_raw/" + rel).replace("\\", "/") if rel else None
    for r in _manifest_rows():
        if (url and r.get("source_url") == url) or (relp and r.get("file_path", "").replace("\\", "/") == relp):
            return r
    return None


def _throttle(host):
    lock = THR / f"{host}.lock"; stamp = THR / f"{host}.t"
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL); os.close(fd); break
        except FileExistsError:
            if time.time() - lock.stat().st_mtime > 120:  # stale lock
                lock.unlink(missing_ok=True)
            time.sleep(0.3)
    try:
        last = float(stamp.read_text()) if stamp.exists() else 0
        wait = HOST_THROTTLE.get(host, THROTTLE_S) - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        stamp.write_text(str(time.time()))
    finally:
        lock.unlink(missing_ok=True)


def get(url, **kw):
    """Throttled GET (no manifest entry): use for HTML listing pages, APIs, CDX."""
    host = urllib.parse.urlparse(url).hostname or ""
    _throttle(host)
    kw.setdefault("timeout", 90)
    kw.setdefault("headers", {"User-Agent": UA})
    # Optional free OpenAlex key, read from the environment and sent as a header: it never enters URLs,
    # the manifest or any output file. Set it yourself: OPENALEX_API_KEY=<key>.
    if host == "api.openalex.org" and os.environ.get("OPENALEX_API_KEY"):
        kw["headers"] = {**kw["headers"], "Authorization": "Bearer " + os.environ["OPENALEX_API_KEY"]}
    kw.setdefault("verify", host not in NO_VERIFY)
    r = requests.get(url, **kw)
    logging.info("GET %s %s %s", r.status_code, len(r.content), url)
    return r


def fetch(url, rel, agent, notes="", archived_url=""):
    """Download url to 02_raw/<rel> once; return the local path relative to ROOT."""
    hit = already(url=url) or already(rel=rel)
    if hit:
        return hit["file_path"]
    r = get(url)
    r.raise_for_status()
    out = RAW / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(r.content)
    row = {"file_path": ("02_raw/" + rel).replace("\\", "/"), "source_url": url,
           "archived_url": archived_url, "download_date": datetime.date.today().isoformat(),
           "sha256": hashlib.sha256(r.content).hexdigest(),
           "file_type": out.suffix.lstrip(".").lower() or r.headers.get("content-type", ""),
           "agent": agent, "notes": notes}
    part = PARTS / f"{agent}.csv"
    new = not part.exists()
    with open(part, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER)
        if new:
            w.writeheader()
        w.writerow(row)
    return row["file_path"]


def register_existing(rel, url, agent, notes=""):
    """Add a manifest row for a file saved by other means (e.g. an HTML page you saved yourself)."""
    if already(rel=rel):
        return
    p = RAW / rel
    row = {"file_path": ("02_raw/" + rel).replace("\\", "/"), "source_url": url, "archived_url": "",
           "download_date": datetime.date.today().isoformat(),
           "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
           "file_type": p.suffix.lstrip(".").lower(), "agent": agent, "notes": notes}
    part = PARTS / f"{agent}.csv"
    new = not part.exists()
    with open(part, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER)
        if new:
            w.writeheader()
        w.writerow(row)
