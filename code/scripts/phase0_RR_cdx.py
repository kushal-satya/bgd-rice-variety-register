"""Query Wayback CDX API for SCA / MoA / NSB domains; save raw JSON; print summary."""
import requests, json, time, sys, collections, datetime
UA = {"User-Agent": "research archive (contact via https://github.com/kushal-satya/bgd-rice-variety-register) python-requests"}
QUERIES = {
 "sca.portal.gov.bd_pdf": dict(url="sca.portal.gov.bd/*", filter="mimetype:application/pdf"),
 "sca.portal.gov.bd_all": dict(url="sca.portal.gov.bd/*"),
 "sca.gov.bd_all": dict(url="sca.gov.bd/*"),
 "www.sca.gov.bd_all": dict(url="www.sca.gov.bd/*"),
 "moa.portal.gov.bd_pdf": dict(url="moa.portal.gov.bd/*", filter="mimetype:application/pdf"),
 "moa.gov.bd_all": dict(url="moa.gov.bd/*"),
 "www.moa.gov.bd_all": dict(url="www.moa.gov.bd/*"),
 "seedwing_moa_portal": dict(url="seedwing.portal.gov.bd/*"),
 "nsb_portal": dict(url="nsb.portal.gov.bd/*"),
}
which = sys.argv[1:] or list(QUERIES)
for name in which:
    q = QUERIES[name]
    params = {"url": q["url"], "output": "json", "collapse": "urlkey", "limit": "50000",
              "fl": "urlkey,timestamp,original,mimetype,statuscode,digest,length"}
    if "filter" in q: params["filter"] = q["filter"]
    for attempt in range(3):
        try:
            r = requests.get("http://web.archive.org/cdx/search/cdx", params=params, headers=UA, timeout=300)
            break
        except Exception as e:
            print(name, "error", e); time.sleep(10)
    else:
        continue
    fn = f"02_raw/wayback_cdx/{name}.json"
    open(fn, "w", encoding="utf-8").write(r.text)
    try:
        rows = json.loads(r.text) if r.text.strip() else []
    except Exception:
        print(name, "non-json", r.status_code, r.text[:200]); continue
    rows = rows[1:] if rows else []
    years = [x[1][:4] for x in rows]
    mimes = collections.Counter(x[3] for x in rows)
    print(f"{name}: status {r.status_code}, {len(rows)} unique urls, years {min(years) if years else '-'}-{max(years) if years else '-'}, mimes {mimes.most_common(6)}", flush=True)
    time.sleep(5)
