"""L2: GloMIP product catalog. The page's 'Excel'/'CSV' buttons are DataTables client-side exports of
the JSON returned by POST /product-catalog/list. We replicate the page's own calls (same session,
CSRF token from the page), sequentially, with lib_fetch's per-host throttle and UA, and save the raw
JSON responses untouched (register_existing). Then we build the same table the Excel button exports
(all columns) plus the per-variety detail records for Bangladesh rows."""
import sys, pathlib, json, re, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import requests
from lib_fetch import _throttle, UA, RAW, register_existing, already

AG = "L2"; H = "glomip.cgiar.org"; B = "https://glomip.cgiar.org"
OUT = "cgiar_specific/glomip"
(RAW / OUT).mkdir(parents=True, exist_ok=True)
s = requests.Session(); s.headers["User-Agent"] = UA

def call(method, url, rel=None, **kw):
    if rel and (RAW / rel).exists():
        return (RAW / rel).read_bytes()
    _throttle(H)
    r = s.request(method, url, timeout=90, **kw)
    print(method, r.status_code, len(r.content), url)
    r.raise_for_status()
    if rel:
        (RAW / rel).write_bytes(r.content)
        register_existing(rel, url, AG, f"GloMIP {method} (page's own XHR); session+CSRF as in browser")
    return r.content

page = call("GET", f"{B}/product-catalog")
(RAW / OUT / "product-catalog.html").write_bytes(page)
register_existing(f"{OUT}/product-catalog.html", f"{B}/product-catalog", AG, "GloMIP product catalog page HTML")
tok = re.search(rb'name="csrf-token" content="([^"]+)"', page).group(1).decode()
hdr = {"X-CSRF-TOKEN": tok, "X-Requested-With": "XMLHttpRequest"}
call("GET", f"{B}/pc-filters", f"{OUT}/pc-filters.json", headers=hdr)
call("POST", f"{B}/pc-search", None, headers=hdr, data={})
lst = call("POST", f"{B}/product-catalog/list", f"{OUT}/product-catalog_list_all.json", headers=hdr, data={})
data = json.loads(lst)["result"]["data"]
print("rows", len(data))
want = [d for d in data if "bangladesh" in str(d.get("countries", "")).lower()]
print("BD rows", len(want))
(RAW / OUT / "details").mkdir(exist_ok=True)
for d in want:
    pid = d["pc_id"]
    call("GET", f"{B}/product-catalog/details/{pid}", f"{OUT}/details/pc_{pid}.json", headers=hdr)

# --- Market segments referenced by the Bangladesh product-catalog rows (context for 'market segment') ---
msp = call("GET", f"{B}/market-segments")
(RAW / OUT / "market-segments.html").write_bytes(msp)
register_existing(f"{OUT}/market-segments.html", f"{B}/market-segments", AG, "GloMIP market segments page HTML")
tok = re.search(rb'name="csrf-token" content="([^"]+)"', msp).group(1).decode()
hdr = {"X-CSRF-TOKEN": tok, "X-Requested-With": "XMLHttpRequest"}
call("GET", f"{B}/ms-filters", f"{OUT}/ms-filters.json", headers=hdr)
call("POST", f"{B}/ms-search", None, headers=hdr, data={})
ml = json.loads(call("POST", f"{B}/market-segments/list", f"{OUT}/market-segments_list_all.json", headers=hdr, data={}))
mrows = ml["result"]["data"]
print("MS rows", len(mrows), list(mrows[0].keys()) if mrows else None)
need = {d.get("ms_shortname") for d in want if d.get("ms_shortname")}
(RAW / OUT / "ms_details").mkdir(exist_ok=True)
for m in mrows:
    txt = json.dumps(m)
    if any(n in txt for n in need):
        mid = m.get("ms_id") or m.get("id")
        call("GET", f"{B}/market-segments/details/{mid}", f"{OUT}/ms_details/ms_{mid}.json", headers=hdr)
