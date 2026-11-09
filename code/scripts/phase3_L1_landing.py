"""L1: for key papers, resolve the DOI landing page, obey robots.txt, save the page (lib_fetch) and extract
corresponding-author e-mail(s) printed on the page plus citation_author / citation_author_institution meta tags.
Output: 04_working/L1/landing_extract.csv. Sequential; one request per host per 2.5 s (lib_fetch)."""
import sys, re, csv, json, pathlib, html, urllib.parse as U, urllib.robotparser as RP
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import get, fetch, ROOT, UA

W = ROOT / "04_working/L1"
ROBOTS = {}


def robots_ok(url):
    host = U.urlparse(url).netloc
    if host not in ROBOTS:
        rp = RP.RobotFileParser()
        try:
            r = get(f"https://{host}/robots.txt", timeout=30)
            txt = r.text if r.status_code == 200 else ""
            (ROOT / "02_raw/_robots" / f"{host}.txt").write_text(f"# HTTP {r.status_code}\n" + txt[:50000], encoding="utf-8")
            rp.parse(txt.splitlines())
        except Exception as e:
            rp.parse([])
        ROBOTS[host] = rp
    return ROBOTS[host].can_fetch(UA, url) and ROBOTS[host].can_fetch("*", url)


def main(dois):
    out = []
    for doi in dois:
        rec = {"doi": doi, "landing_url": "", "status": "", "local_file": "", "corresponding_emails": "", "meta_authors": "", "meta_institutions": "", "notes": ""}
        try:
            r = get("https://doi.org/" + doi, allow_redirects=False, timeout=30)
            loc = r.headers.get("Location", "")
            hops = 0
            while loc and hops < 4 and r.status_code in (301, 302, 303, 307, 308):
                if not robots_ok(loc): break
                r = get(loc, allow_redirects=False, timeout=60); hops += 1
                nloc = r.headers.get("Location", "")
                if nloc: loc = U.urljoin(loc, nloc)
                else: break
            rec["landing_url"] = loc
            if not loc or not robots_ok(loc):
                rec["status"] = "robots_disallow_or_no_redirect"; out.append(rec); continue
            if r.status_code != 200:
                rec["status"] = f"HTTP {r.status_code}"; out.append(rec); continue
            rel = "literature_pages/" + re.sub(r"[^A-Za-z0-9]+", "_", doi)[:100] + ".html"
            lf = fetch(loc, rel, "L1", f"landing page for doi {doi}")
            rec["local_file"] = lf; rec["status"] = "ok"
            t = (ROOT / lf).read_text(encoding="utf-8", errors="replace")
            metas = re.findall(r'<meta[^>]+name=["\'](citation_author(?:_institution|_email)?)["\'][^>]+content=["\']([^"\']*)["\']', t, flags=re.I)
            rec["meta_authors"] = "; ".join(html.unescape(v) for k, v in metas if k.lower() == "citation_author")
            rec["meta_institutions"] = " || ".join(html.unescape(v) for k, v in metas if k.lower() == "citation_author_institution")[:2000]
            em = [v for k, v in metas if k.lower() == "citation_author_email"]
            plain = html.unescape(re.sub(r"<[^>]+>", " ", t))
            for m in re.finditer(r"(?:Corresponding|correspondence|\*\s*E-?mail)", plain, flags=re.I):
                em += re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", plain[m.start(): m.start() + 300])
            em += re.findall(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', t)
            bad = re.compile(r"(info|support|editor|editorial|office|contact|journal|submission|admin|help|permissions|plos|elsevier|webmaster|banglajol|sciencedomain|journalajrcs|journalaprj|noreply|press)@|@(?:example)", re.I)
            rec["corresponding_emails"] = "; ".join(sorted({e.strip(".") for e in em if not bad.search(e)}))
        except Exception as e:
            rec["status"] = "error: " + str(e)[:120]
        out.append(rec)
        print(rec["doi"], rec["status"], rec["corresponding_emails"], flush=True)
    f = W / "landing_extract.csv"
    old = list(csv.DictReader(open(f, encoding="utf-8"))) if f.exists() else []
    done = {o["doi"] for o in out}
    rows = [o for o in old if o["doi"] not in done] + out
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    lit = list(csv.DictReader(open(ROOT / "05_output/final/bgd_literature.csv", encoding="utf-8")))
    dois = sorted({r["doi"] for r in lit if r["is_key_paper"] == "yes" and r["doi"] and "zenodo" not in r["doi"]})
    main(dois)
