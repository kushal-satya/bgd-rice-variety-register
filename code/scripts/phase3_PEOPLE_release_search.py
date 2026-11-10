"""E5 (round 3, 2026-11-10): search for the release/description paper of every public variety.

Scope: BRRI (inbred and hybrid), BINA (incl. Iratom), university varieties (BAU, BU/GAU, RU) in
05_output/final/bgd_rice_varieties.csv.
Step 1 (no network): titles in 04_working/L1/pubs.json that name the variety.
Step 2 (network): Crossref works?query.bibliographic=<variety name> rice variety (rows 40), via lib_fetch.get
         (throttled, User-Agent without any e-mail; no mailto parameter). Raw JSON cached in
         04_working/PEOPLE/crossref_cache/<variety_id>.json so reruns make no calls.
Output:  04_working/PEOPLE/release_candidates.csv  every title that names the variety (with a release-wording flag),
         for manual review; accepted papers are transcribed into 04_working/PEOPLE/release_papers.csv.
"""
import json, re, sys, pathlib, time, urllib.parse, html
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import ROOT, get  # noqa: E402

PW = ROOT / "04_working/PEOPLE"; CACHE = PW / "crossref_cache"
GROUPS = ["BRRI", "BINA", "University"]
REL = re.compile(r"develop|new\b|variety|released|release|suitable|high[- ]yielding|promising|description|characteri[sz]", re.I)


def name_rx(name):
    """Regex that finds the variety name in a title, tolerant of spaces/hyphens, not followed by a digit."""
    n = re.sub(r"\s*\(.*\)", "", name).strip()
    m = re.match(r"(BRRI hybrid dhan|BRRI dhan|Binadhan|BAU dhan|BU dhan|GAU dhan|RU dhan|BU Aromatic Hybrid dhan|BR|Iratom|Binashail)\s*-?\s*(\d*)$", n, re.I)
    if not m:   # e.g. 'BAU-63 (Bharosa)': flexible separators, not followed by a digit
        return re.compile(r"(?<![A-Za-z])" + r"[\s\-]*".join(re.escape(x) for x in re.split(r"[\s\-]+", n)) + r"(?!\d)", re.I) if n else None
    stem, num = m.group(1), m.group(2)
    parts = [re.escape(p) for p in re.split(r"\s+", stem)]
    if stem.lower() == "binadhan":
        parts = ["bina", "dhan"]
    s = r"[\s\-]*".join(parts)
    pre = r"(?<![A-Za-z])"
    if stem == "BR":
        pre = r"(?<![A-Za-z])"
    return re.compile(pre + s + (r"[\s\-]*" + num + r"(?!\d)" if num else r"(?![A-Za-z])"), re.I)


def query_name(name):
    return re.sub(r"\s*\(.*\)", "", name).strip()


def main(network=True):
    PW.mkdir(exist_ok=True); CACHE.mkdir(exist_ok=True)
    R = pd.read_csv(ROOT / "05_output/final/bgd_rice_varieties.csv", dtype=str, keep_default_na=False)
    S = R[R.developer_group.isin(GROUPS)]
    pubs = json.load(open(ROOT / "04_working/L1/pubs.json", encoding="utf-8"))
    rows, calls = [], 0
    lit = pd.read_csv(ROOT / "05_output/final/bgd_literature.csv", dtype=str, keep_default_na=False)
    have_key = set(lit[(lit.is_key_paper == "yes") & (lit.publication_type == "release/description paper")].variety_id)
    for r in S.itertuples():
        rx = name_rx(r.variety_name)
        if rx is None:
            print("no pattern for", r.variety_id, r.variety_name); continue
        for p in pubs:
            t = p.get("title") or ""
            if rx.search(t):
                rows.append(dict(variety_id=r.variety_id, variety_name=r.variety_name, source="L1 pubs.json", doi=p.get("doi", ""),
                                 title=t, year=p.get("year", ""), venue=p.get("venue", ""), authors=p.get("authors", ""),
                                 release_wording="yes" if REL.search(t) else "no", pub_id=p["pub_id"]))
        # query 1: '<name> rice variety'; query 2 (varieties without a key release paper only): the name with the number
        # split off ('BRRI dhan 79') plus release wording, because Crossref tokenises 'dhan79' as one word
        qs = [(CACHE / f"{r.variety_id}.json", query_name(r.variety_name) + " rice variety")]
        if r.variety_id not in have_key:
            qs.append((CACHE / f"{r.variety_id}__q2.json",
                       re.sub(r"(?<=[A-Za-z])-?(\d+)$", r" \1", query_name(r.variety_name)) + " development new high yielding rice variety Bangladesh"))
        for f, qtext in qs:
            if not f.exists() and network:
                resp = get(f"https://api.crossref.org/works?query.bibliographic={urllib.parse.quote(qtext)}&rows=40&select=DOI,title,author,container-title,issued,type")
                calls += 1
                if resp.status_code == 200:
                    f.write_text(resp.text, encoding="utf-8")
                else:
                    print("crossref", resp.status_code, r.variety_id)
                time.sleep(1.0)
            if not f.exists():
                continue
            for it in json.loads(f.read_text(encoding="utf-8"))["message"]["items"]:
                t = html.unescape(" ".join(it.get("title") or []))
                if rx.search(t):
                    au = "; ".join(" ".join(x for x in [a.get("given", ""), a.get("family", "")] if x) or a.get("name", "") for a in it.get("author", []))
                    yr = str((it.get("issued", {}).get("date-parts") or [[""]])[0][0] or "")
                    rows.append(dict(variety_id=r.variety_id, variety_name=r.variety_name, source="Crossref", doi=it["DOI"].lower(), title=t, year=yr,
                                     venue=" ".join(it.get("container-title") or []), authors=au,
                                     release_wording="yes" if REL.search(t) else "no", pub_id="doi:" + it["DOI"].lower()))
    D = pd.DataFrame(rows).drop_duplicates(["variety_id", "doi", "title"])
    D.to_csv(PW / "release_candidates.csv", index=False, encoding="utf-8-sig")
    print(f"crossref calls {calls}; candidate rows {len(D)}; varieties with any titled paper {D.variety_id.nunique()}/{len(S)}; "
          f"with release wording {D[D.release_wording == 'yes'].variety_id.nunique()}")


if __name__ == "__main__":
    main(network="--offline" not in sys.argv)
