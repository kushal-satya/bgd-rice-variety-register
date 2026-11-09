"""F3W: CGSpace REST discover search (robots allows /server/api). Prints candidate items; saves raw JSON of each query."""
import json, sys, pathlib, re
from lib_fetch import get, ROOT
OUT = ROOT / "04_working/F3W_cgspace_queries"; OUT.mkdir(parents=True, exist_ok=True)
qs = sys.argv[1:]
for q in qs:
    for page in range(3):
        r = get("https://cgspace.cgiar.org/server/api/discover/search/objects", params={"query": q, "dsoType": "ITEM", "size": 100, "page": page})
        if r.status_code != 200:
            print("HTTP", r.status_code, q); break
        slug = re.sub(r"\W+", "_", q)[:60]
        (OUT / f"{slug}_p{page}.json").write_text(r.text, encoding="utf-8")
        sr = r.json()["_embedded"]["searchResult"]
        objs = sr["_embedded"]["objects"]
        for o in objs:
            it = o["_embedded"]["indexableObject"]; md = it["metadata"]
            g = lambda k: (md.get(k) or [{}])[0].get("value", "")
            print(it["handle"], "|", g("dcterms.type"), "|", g("dcterms.issued")[:10], "|", g("dc.title")[:140])
        if (page + 1) * 100 >= sr["page"]["totalElements"]: break
