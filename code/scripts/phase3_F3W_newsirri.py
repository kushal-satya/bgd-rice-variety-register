"""F3W: IRRI news blog (news.irri.org, Blogger) label feeds; robots allows /feeds. Saves each feed; extracts Bangladesh variety sentences."""
import json, re, html, urllib.parse, pathlib, sys
from lib_fetch import fetch, ROOT
from phase3_F3W_lib import log
LABELS = ["BRRI", "Bangladesh Rice Research Institute", "BINA", "Bangladesh Institute of Nuclear Agriculture", "strasa", "GSR",
          "Green Super Rice", "Binadhan-17", "BRRI dhan75", "HarvestPlus", "IRRI Bangladesh Office", "stress-tolerant rice",
          "Media release", "CSISA", "Bangladesh", "Seeds without Borders", "biofortified high-zinc rice", "Salinity Rice Breeding", "hybrid rice", "drought", "flood"]
VR = re.compile(r"(BRRI\s*dhan\s*-?\s*\d+|BRRIdhan\s*\d+|BR\s?11|BINA\s*dhan\s*-?\s*\d+|Binadhan\s*-?\s*\d+|BINA-\d+|Swarna-Sub1|BR11-Sub1|BU\s+dhan|BRRI hybrid)", re.I)
posts = {}
for lab in LABELS:
    url = "https://news.irri.org/feeds/posts/default/-/" + urllib.parse.quote(lab) + "?alt=json&max-results=500"
    rel = "cgiar_web/irri/newsirri_feed_label_" + re.sub(r"\W+", "_", lab) + ".json"
    try:
        p = fetch(url, rel, "F3W", f"IRRI news blog label feed {lab}"); log(url, "ok", p)
    except Exception as e:
        log(url, f"ERR {e}", ""); print("ERR", lab, e); continue
    d = json.loads((ROOT / p).read_text(encoding="utf-8"))
    for e in d["feed"].get("entry", []):
        link = [l["href"] for l in e["link"] if l["rel"] == "alternate"][0]
        posts.setdefault(link, (e, p))
print("posts", len(posts))
out = []
for link, (e, p) in sorted(posts.items(), key=lambda x: x[1][0]["published"]["$t"]):
    body = html.unescape(re.sub(r"<[^>]+>", " ", e["content"]["$t"])); body = re.sub(r"\s+", " ", body)
    if "bangladesh" not in body.lower(): continue
    if not VR.search(body): continue
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if VR.search(s)]
    out.append({"link": link, "feed": p, "published": e["published"]["$t"][:10], "title": e["title"]["$t"], "sents": sents})
pathlib.Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("bd variety posts", len(out))
