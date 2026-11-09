"""F3C: list CGSpace bitstreams for target handles (throttled via lib_fetch.get)."""
import json, sys
from lib_fetch import get
HANDLES = sys.argv[1:] or ["10568/128929", "10568/126982", "10568/119865"]
for h in HANDLES:
    r = get(f"https://cgspace.cgiar.org/server/api/pid/find?id=hdl:{h}", allow_redirects=True)
    print("==", h, r.status_code, r.url)
    if r.status_code != 200:
        continue
    it = r.json(); uuid = it.get("uuid")
    print("  item", uuid, it.get("name"))
    b = get(f"https://cgspace.cgiar.org/server/api/core/items/{uuid}/bundles").json()
    for bd in b.get("_embedded", {}).get("bundles", []):
        if bd["name"] not in ("ORIGINAL",):
            continue
        bs = get(bd["_links"]["bitstreams"]["href"]).json()
        for s in bs.get("_embedded", {}).get("bitstreams", []):
            print("   ", bd["name"], s["uuid"], s["name"], s.get("sizeBytes"))
