"""F3W: list ORIGINAL bitstreams of CGSpace items and download them once via lib_fetch."""
import json, sys, re
from lib_fetch import fetch, get, ROOT
from phase3_F3W_lib import log
for h in sys.argv[1:]:
    p = ROOT / f"02_raw/cgiar_web/cgspace/item_{h.replace('/', '_')}.json"
    d = json.loads(p.read_text(encoding="utf-8")); u = d["uuid"]
    r = get(f"https://cgspace.cgiar.org/server/api/core/items/{u}/bundles")
    for b in r.json()["_embedded"]["bundles"]:
        if b["name"] != "ORIGINAL": continue
        rb = get(b["_links"]["bitstreams"]["href"])
        for bs in rb.json()["_embedded"]["bitstreams"]:
            name = re.sub(r"[^\w.-]+", "_", bs["name"])[:80]
            url = f"https://cgspace.cgiar.org/server/api/core/bitstreams/{bs['uuid']}/content"
            rel = f"cgiar_web/cgspace/{h.replace('/', '_')}__{name}"
            try:
                lp = fetch(url, rel, agent="F3W", notes=f"CGSpace hdl:{h} bitstream {bs['name']}")
                log(url, "ok", lp); print(h, lp, bs.get("sizeBytes"))
            except Exception as e:
                log(url, f"ERR {e}", ""); print("ERR", h, e)
