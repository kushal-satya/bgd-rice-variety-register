"""L1: harvest literature API JSON (OpenAlex, Crossref, Europe PMC, CGSpace) into 02_raw/literature_api.
Sequential, via lib_fetch.fetch (cached; manifest rows under agent L1). Re-runnable."""
import os
import sys, json, re, csv, pathlib, urllib.parse as U
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch, ROOT
A = "L1"; MAIL = os.environ.get("POLITE_POOL_EMAIL", "")   # set to use the OpenAlex/Crossref polite pool; never committed
def slug(s): return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:80]
def F(url, rel, notes=""):
    try:
        p = fetch(url, "literature_api/" + rel, A, notes)
        return json.loads((ROOT / p).read_text(encoding="utf-8"))
    except Exception as e:
        print("FAIL", url, e, flush=True); return None

def openalex_all(q, tag, maxpages=15):
    cur = "*"
    for i in range(maxpages):
        url = f"https://api.openalex.org/works?search={U.quote(q)}&per-page=200&cursor={U.quote(cur)}{"&mailto=" + MAIL if MAIL else ""}"
        j = F(url, f"openalex/q_{slug(tag)}_p{i}.json", f"OpenAlex search {q}")
        if not j or not j.get("results"): break
        cur = j["meta"].get("next_cursor")
        if not cur: break

def crossref_journal(issn, tag):
    cur = "*"
    for i in range(20):
        url = f"https://api.crossref.org/journals/{issn}/works?rows=200&cursor={U.quote(cur)}{"&mailto=" + MAIL if MAIL else ""}"
        j = F(url, f"crossref/journal_{tag}_p{i}.json", f"Crossref journal {issn}")
        if not j or not j["message"]["items"]: break
        cur = j["message"].get("next-cursor")

def epmc(q, tag):
    cur = "*"
    for i in range(10):
        url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={U.quote(q)}&format=json&resultType=core&pageSize=500&cursorMark={U.quote(cur)}"
        j = F(url, f"europepmc/q_{slug(tag)}_p{i}.json", f"Europe PMC {q}")
        if not j or not j.get("resultList", {}).get("result"): break
        nxt = j.get("nextCursorMark")
        if not nxt or nxt == cur: break
        cur = nxt

def cgspace(q, tag, maxpages=10):
    for i in range(maxpages):
        url = f"https://cgspace.cgiar.org/server/api/discover/search/objects?query={U.quote(q)}&size=100&page={i}&dsoType=ITEM"
        j = F(url, f"cgspace/q_{slug(tag)}_p{i}.json", f"CGSpace discover {q}")
        if not j: break
        sr = j["_embedded"]["searchResult"]; pg = sr["page"]
        if i + 1 >= pg.get("totalPages", 0): break

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "broad"
    if step == "broad":
        for q in ['"BRRI dhan"', 'Binadhan', '"BINA dhan"', '"BRRI hybrid"', '"Bina dhan"', 'Binasail',
                  '"Iratom 24"', '"BU dhan"', '"BRAC dhan"', '"BAU dhan"', '"GAU dhan"', '"BR11" rice', '"BR 11" rice Bangladesh',
                  '"BRRI dhan-"', '"BRRI Dhan" variety release', 'rice variety Bangladesh release BRRI',
                  '"BRRI hybrid dhan"', 'hybrid rice Bangladesh variety']:
            openalex_all(q, q)
        crossref_journal("1025-7330", "BRJ")
        for q in ['"BRRI dhan" OR "BRRI dhan*" OR Binadhan OR "BINA dhan" OR "Bina dhan" OR "BRRI hybrid"']:
            epmc(q, "brri_bina_all")
        for q in ['BRRI dhan', 'Binadhan', 'BINA dhan', 'Bangladesh rice variety release', 'Bangladesh rice variety', 'BRRI hybrid']:
            cgspace(q, q)

def variety_queries(vid):
    """Name-spelling variants per main variety id (without 'RICE-')."""
    k = vid.replace("RICE-", ""); m = re.match(r"([A-Z_]+?)(\d+)$", k); q = []
    if not m:
        return {"BINASHAIL": ['Binasail rice', 'Binashail'], "OLD_PAJAM": ['Pajam rice Bangladesh'],
                "OLD_PURBACHI": ['Purbachi rice'], "OLD_BRISHAIL": ['Brishail rice'], "OLD_BAU63": ['"BAU 63" rice']}.get(k, [])
    p, n = m.group(1), m.group(2)
    if p == "BRRI_DHAN": q = [f"BRRI dhan{n}", f'"BRRI dhan {n}"', f'"BRRI dhan-{n}"', f'"BR{n}" rice Bangladesh']
    elif p == "BRRI_HYBRID": q = [f'"BRRI hybrid dhan{n}"', f'"BRRI hybrid dhan {n}"', f'"BRRI hybrid {n}"']
    elif p == "BINADHAN": q = [f'"Binadhan-{n}"', f"Binadhan{n}", f'"Bina dhan {n}"', f"Bina dhan{n}"]
    elif p == "BINA_HYBRID": q = [f'"Bina hybrid dhan {n}"', f'"Binahybrid dhan {n}"']
    elif p == "BR": q = [f'"BR{n}" rice Bangladesh', f'"BR {n}" rice Bangladesh', f'"BR-{n}" rice Bangladesh']
    elif p == "IR": q = [f'"IR{n}" Bangladesh rice', f'"IR {n}" Bangladesh rice']
    elif p == "IRATOM": q = [f'"Iratom {n}"', f'Iratom{n}']
    elif p in ("BU_DHAN", "GAU_DHAN", "BAU_DHAN", "BRAC_DHAN"):
        a = p.split("_")[0]; q = [f'"{a} dhan {n}"', f'"{a} dhan{n}"', f'"{a} dhan-{n}"']
    elif p == "BU_AROMATIC_HYBRID": q = [f'"BU Aromatic Hybrid Dhan {n}"', f'"BU aromatic hybrid"']
    elif p.startswith("OLD_BAU"): q = [f'"BAU {n}" rice']
    elif p.startswith("PVT_"):
        a = p.split("_")[1]; q = [f'"{a} dhan {n}"', f'"{a} dhan{n}"']
    return q

def main_ids():
    rows = list(csv.DictReader(open(ROOT / "05_output/final/bgd_rice_varieties.csv", encoding="utf-8-sig")))
    return [r["variety_id"] for r in rows if r["rice_type"] == "inbred" or r["variety_id"].startswith(
        ("RICE-BRRI_HYBRID", "RICE-BINA_HYBRID", "RICE-BU_AROMATIC_HYBRID"))]

def pervariety():
    import os
    no_oa = os.environ.get("NO_OPENALEX")  # OpenAlex free daily budget exhausted 2026-10-07 (HTTP 429): skip
    for vid in main_ids():
        for q in ([] if no_oa else variety_queries(vid)):
            url = f"https://api.openalex.org/works?search={U.quote(q)}&per-page=200{"&mailto=" + MAIL if MAIL else ""}"
            F(url, f"openalex/v_{slug(q)}.json", f"OpenAlex per-variety {vid}")
        for q in variety_queries(vid)[:1]:
            url = f"https://cgspace.cgiar.org/server/api/discover/search/objects?query={U.quote(q)}&size=100&page=0&dsoType=ITEM"
            F(url, f"cgspace/v_{slug(q)}.json", f"CGSpace per-variety {vid}")
        q0 = variety_queries(vid)[:2]
        for q in q0:
            url = f"https://api.crossref.org/works?query.bibliographic={U.quote(q.strip(chr(34)) + ' rice variety')}&rows=40{"&mailto=" + MAIL if MAIL else ""}"
            F(url, f"crossref/v_{slug(q)}.json", f"Crossref per-variety {vid}")

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "pervariety":
    pervariety()

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "epmc2":
    for q in ['BRRI dhan*', 'binadhan*', '"BINA dhan*"', '"BRRI hybrid"', 'Bangladesh AND "rice variety"']:
        epmc(q, "v2_" + q)

def crossref_query(q, pages=5):
    cur = "*"
    for i in range(pages):
        url = f"https://api.crossref.org/works?query.bibliographic={U.quote(q)}&rows=200&cursor={U.quote(cur)}&select=DOI,title,author,issued,container-title,volume,issue,page,type,is-referenced-by-count,subject,funder,license,URL,abstract,publisher{"&mailto=" + MAIL if MAIL else ""}"
        j = F(url, f"crossref/q_{slug(q)}_p{i}.json", f"Crossref query {q}")
        if not j or not j["message"]["items"]: break
        cur = j["message"].get("next-cursor")

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "crossref_generic":
    for q in ["development rice variety Bangladesh BRRI dhan", "rice variety ecosystem of Bangladesh", "high yielding rice variety Bangladesh",
              "Binadhan mutant rice variety Bangladesh", "BRRI hybrid dhan variety", "zinc enriched rice variety Bangladesh",
              "salt tolerant rice variety Bangladesh", "premium quality aromatic rice variety Bangladesh", "Bangladesh Journal of Nuclear Agriculture rice Binadhan"]:
        crossref_query(q)

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "journals":
    for issn, tag in [("0258-7130", "BJNAg"), ("1026-3071", "BJPBG"), ("1682-8348", "SAARCJA"), ("0258-7122", "BJAR"),
                      ("1013-1922", "BAJ"), ("1810-3030", "JBAU"), ("1025-482X", "ABA"), ("0117-4185", "IRRN")]:
        crossref_journal(issn, tag)
