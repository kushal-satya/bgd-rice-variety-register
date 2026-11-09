"""F3W: save CGSpace item metadata JSON (via lib_fetch) for selected handles and print text fields."""
import json, sys
from lib_fetch import fetch, get, ROOT
from phase3_F3W_lib import log
for h in sys.argv[1:]:
    url = f"https://cgspace.cgiar.org/server/api/pid/find?id=hdl:{h}"
    rel = f"cgiar_web/cgspace/item_{h.replace('/', '_')}.json"
    try:
        p = fetch(url, rel, agent="F3W", notes=f"CGSpace item metadata hdl:{h}")
        log(url, "ok", p)
    except Exception as e:
        log(url, f"ERR {e}", ""); print("ERR", h, e); continue
    d = json.loads((ROOT / p).read_text(encoding="utf-8"))
    md = d.get("metadata", {})
    print("=" * 20, h, d.get("uuid"))
    for k, vs in md.items():
        if k.startswith(("dc.title", "dcterms.abstract", "dc.description", "dcterms.issued", "dcterms.type", "cg.contributor.crp", "cg.contributor.initiative", "dcterms.description", "cg.howPublished", "dcterms.bibliographicCitation", "cg.identifier.url", "cg.contributor.affiliation", "dcterms.subject")):
            for v in vs:
                print(f"  {k}: {v['value'][:1500]}")
