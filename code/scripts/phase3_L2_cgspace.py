"""L2: CGSpace items (REST API, DSpace 7). Saves item/bundle/bitstream JSON and ORIGINAL files."""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import get, fetch, register_existing, RAW, already

API = "https://cgspace.cgiar.org/server/api/core"
AG = "L2"

def save_json(url, rel, notes):
    if already(url=url) or already(rel=rel):
        return json.loads((RAW / rel).read_text(encoding="utf-8"))
    r = get(url); r.raise_for_status()
    p = RAW / rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(r.content)
    register_existing(rel, url, AG, notes)
    return r.json()

def do_item(uuid, slug):
    base = f"cgiar_specific/{slug}"
    it = save_json(f"{API}/items/{uuid}", f"{base}/item.json", "CGSpace item metadata (REST)")
    # owning collection
    try:
        save_json(f"{API}/items/{uuid}/owningCollection", f"{base}/owningCollection.json", "owning collection")
    except Exception as e:
        print("owningCollection", e)
    b = save_json(f"{API}/items/{uuid}/bundles", f"{base}/bundles.json", "item bundles")
    for bun in b["_embedded"]["bundles"]:
        bs = save_json(f"{API}/bundles/{bun['uuid']}/bitstreams?size=100",
                       f"{base}/bundle_{bun['name']}_bitstreams.json", f"bitstreams of bundle {bun['name']}")
        for s in bs["_embedded"]["bitstreams"]:
            if bun["name"] in ("ORIGINAL", "TEXT", "LICENSE"):
                name = s["name"].replace(" ", "_")
                try:
                    print(fetch(f"{API}/bitstreams/{s['uuid']}/content", f"{base}/{bun['name']}/{name}", AG,
                                f"CGSpace bitstream {s['uuid']} bundle {bun['name']}"))
                except Exception as e:
                    print("FAIL", s["name"], e)
    return it

if __name__ == "__main__":
    do_item("ee9e7073-e49c-4d12-a703-a3102966741e", "cgspace_gr2e_brri_dhan29")
    do_item("ce70f984-8ed1-43e5-82c8-299cf2326083", "cgspace_exotic_adoption")
    # bitstream 96056a86 -> its bundle -> item
    bsid = "96056a86-e517-4444-b07c-a79ff13f9425"
    meta = save_json(f"{API}/bitstreams/{bsid}", "cgiar_specific/cgspace_ubinig_brief/bitstream.json", "bitstream metadata")
    bun = get(f"{API}/bitstreams/{bsid}/bundle").json()
    item = get(f"{API}/bundles/{bun['uuid']}/item").json()
    print("UBINIG parent item", item["uuid"], item["name"], item.get("handle"))
    do_item(item["uuid"], "cgspace_ubinig_brief")
    print(fetch(f"{API}/bitstreams/{bsid}/content", "cgiar_specific/cgspace_ubinig_brief/UBINIG_brief_FINAL_FOR_WEB.pdf", AG,
                "the bitstream URL given by the PI"))
