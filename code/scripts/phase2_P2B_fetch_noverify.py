"""P2B helper: lib_fetch.get with verify=False for bina.gov.bd (same incomplete TLS chain as brri.gov.bd/sca.gov.bd,
the NPF platform; certificate defect, not access control), then save untouched and register in the manifest
via lib_fetch.register_existing. Throttle and User-Agent come from lib_fetch unchanged."""
from lib_fetch import get, register_existing, already, RAW

def fetch_nv(url, rel, notes=""):
    hit = already(url=url) or already(rel=rel)
    if hit:
        return hit["file_path"]
    r = get(url, verify=False)
    r.raise_for_status()
    p = RAW / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(r.content)
    register_existing(rel, url, "P2B", notes + " [fetched with verify=False: incomplete TLS chain]")
    return "02_raw/" + rel
