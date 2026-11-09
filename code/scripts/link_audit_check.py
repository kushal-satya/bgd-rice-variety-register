"""Check every URL in 06_validation/link_audit_urls.csv. One worker thread per host (each throttled by lib_fetch).
DOIs are checked against the DOI resolver's handle API (registered or not), never by scraping publishers.
Resumable: results cached in 06_validation/link_audit_results.csv."""
import sys, csv, re, json, pathlib, threading, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
sys.path.insert(0, "scripts")
from lib_fetch import get
OUT = pathlib.Path("06_validation/link_audit_results.csv")
U = pd.read_csv("06_validation/link_audit_urls.csv", dtype=str).fillna("")
done = set(pd.read_csv(OUT, dtype=str).url) if OUT.exists() else set()
lock = threading.Lock()
ERR = re.compile(r"domain is not available|page not found|404 not found|access denied|this page (?:does not|doesn't) exist|no such item", re.I)
H = ["url", "kind", "status", "final_url", "content_type", "verdict", "note"]
if not OUT.exists():
    with open(OUT, "w", newline="", encoding="utf-8") as f: csv.writer(f).writerow(H)


def doi_of(u):
    m = re.search(r"doi\.org/(10\.\d{4,9}/.+)$", u)
    return urllib.parse.unquote(m.group(1)) if m else None


def check(u):
    d = doi_of(u)
    try:
        if d:
            r = get("https://doi.org/api/handles/" + urllib.parse.quote(d, safe="/"), timeout=60)
            code = r.json().get("responseCode") if r.headers.get("content-type", "").startswith("application/json") else None
            v = "ok" if code == 1 else ("doi_not_registered" if code in (100, 200) else f"check_failed_{r.status_code}")
            return [u, "doi", r.status_code, "", "application/json", v, f"handle responseCode={code}"]
        r = get(u, timeout=90, allow_redirects=True, stream=True)
        ct = r.headers.get("content-type", "")
        body = b""
        if "html" in ct:
            body = r.raw.read(200000, decode_content=True) if hasattr(r, "raw") else r.content[:200000]
        r.close()
        txt = body.decode("utf-8", "ignore")
        if r.status_code >= 400:
            v = {403: "blocked_403", 404: "dead_404", 410: "dead_410", 429: "rate_limited"}.get(r.status_code, f"error_{r.status_code}")
        elif ERR.search(txt[:20000]):
            v = "soft_error_page"
        else:
            v = "ok"
        return [u, "web", r.status_code, r.url if r.url != u else "", ct[:60], v, ""]
    except Exception as e:  # noqa
        return [u, "doi" if d else "web", "", "", "", "unreachable", type(e).__name__ + ": " + str(e)[:120]]


def worker(urls):
    for u in urls:
        res = check(u)
        with lock:
            with open(OUT, "a", newline="", encoding="utf-8") as f: csv.writer(f).writerow(res)


todo = U[~U.url.isin(done)]
groups = [g.url.tolist() for _, g in todo.groupby(todo.url.map(lambda x: "doi.org" if doi_of(x) else (urllib.parse.urlparse(x).hostname or "")))]
print(len(todo), "to check in", len(groups), "host groups", flush=True)
with ThreadPoolExecutor(min(24, len(groups) or 1)) as ex:
    list(ex.map(worker, groups))
print("done", flush=True)
