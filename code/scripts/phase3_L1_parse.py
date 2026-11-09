"""L1: parse cached literature API JSON -> unified publication records + variety mentions.
Writes 04_working/L1/pubs.json and 04_working/L1/mentions.csv. No network."""
import sys, json, re, csv, pathlib, glob, html, unicodedata
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import ROOT
RAWD = ROOT / "02_raw/literature_api"; OUT = ROOT / "04_working/L1"; OUT.mkdir(parents=True, exist_ok=True)


def ntitle(t): return re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKD", (t or "").lower()))[:150]
def clean(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def bare_doi(d):
    if not d: return ""
    d = d.strip().lower(); d = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", d); return d


def inv_abs(ii):
    if not ii: return ""
    pos = {}
    for w, ps in ii.items():
        for p in ps: pos[p] = w
    return " ".join(pos[i] for i in sorted(pos))


PUBS = {}
TIDX = {}


def add(rec):
    if not rec["title"]: return
    tk = ntitle(rec["title"])
    k = ("doi:" + rec["doi"]) if rec["doi"] else None
    if k is None or k not in PUBS:
        old = TIDX.get(tk)
        if old and (k is None or not PUBS[old].get("doi") or PUBS[old].get("doi") == rec["doi"]):
            if k and old != k:  # upgrade title-key record to doi key
                PUBS[k] = PUBS.pop(old); TIDX[tk] = k
            k = TIDX[tk]
    if k is None: k = "t:" + tk
    TIDX.setdefault(tk, k)
    cur = PUBS.setdefault(k, {"sources": [], "raw_files": []})
    for f, v in rec.items():
        if f in ("sources", "raw_files"):
            for x in v:
                if x not in cur[f]: cur[f].append(x)
        elif f == "abstract":
            if v and len(v) > len(cur.get(f, "")): cur[f] = v
        elif v and not cur.get(f): cur[f] = v


def oa_rec(w, fp):
    pl = w.get("primary_location") or {}; src = pl.get("source") or {}; b = w.get("biblio") or {}
    auth = []; affs = []; orc = []; corr = []; raws = []
    for a in w.get("authorships", []):
        nm = (a.get("author") or {}).get("display_name") or a.get("raw_author_name") or ""
        auth.append(nm)
        ins = "; ".join(i.get("display_name", "") for i in a.get("institutions", [])) or "; ".join(a.get("raw_affiliation_strings", []) or [])
        affs.append(f"{nm}: {ins}" if ins else "")
        raw = "; ".join(a.get("raw_affiliation_strings", []) or [])
        if raw: raws.append(f"{nm}: {raw}")
        o = (a.get("author") or {}).get("orcid")
        if o: orc.append(f"{nm}: {o.replace('https://orcid.org/', '')}")
        if a.get("is_corresponding"): corr.append(nm)
    vip = "; ".join(x for x in [b.get("volume") and f"vol {b['volume']}", b.get("issue") and f"issue {b['issue']}",
                                b.get("first_page") and f"pp {b['first_page']}-{b.get('last_page') or ''}"] if x)
    oa = w.get("open_access") or {}
    funders = {(g.get("funder_display_name") or "") for g in (w.get("grants") or [])} | {(f.get("display_name") or "") for f in (w.get("funders") or [])}
    return {"doi": bare_doi(w.get("doi")), "title": clean(w.get("title") or w.get("display_name")), "authors": "; ".join(auth),
            "affiliations": " || ".join(x for x in affs if x), "affiliations_raw": " || ".join(raws), "orcids": "; ".join(orc), "corresponding_authors": "; ".join(corr),
            "year": str(w.get("publication_year") or ""), "venue": src.get("display_name") or "", "publisher": src.get("host_organization_name") or "",
            "volume_issue_pages": vip, "type": w.get("type") or "", "cited_by_count": str(w.get("cited_by_count", "")),
            "keywords": "; ".join([k.get("display_name", "") for k in (w.get("keywords") or [])] + [c["display_name"] for c in (w.get("concepts") or [])[:6]]),
            "topics": "; ".join(t.get("display_name", "") for t in (w.get("topics") or [])[:3]),
            "countries": "; ".join(sorted({c for a in w.get("authorships", []) for c in (a.get("countries") or [])})),
            "funders": "; ".join(sorted(funders - {""})),
            "license": pl.get("license") or (w.get("best_oa_location") or {}).get("license") or "", "oa_status": oa.get("oa_status") or "",
            "open_access_url": oa.get("oa_url") or "", "url": pl.get("landing_page_url") or (w.get("doi") or ""),
            "abstract": inv_abs(w.get("abstract_inverted_index")), "openalex_id": w.get("id", ""), "language": w.get("language") or "",
            "sources": ["openalex"], "raw_files": [fp]}


def cr_rec(it, fp):
    auth = []; affs = []; orc = []
    for a in it.get("author", []):
        nm = " ".join(x for x in [a.get("given"), a.get("family")] if x) or a.get("name", "")
        auth.append(nm)
        af = "; ".join(x.get("name", "") for x in a.get("affiliation", []))
        if af: affs.append(f"{nm}: {af}")
        if a.get("ORCID"): orc.append(f"{nm}: {a['ORCID'].split('/')[-1]}")
    yr = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
    vip = "; ".join(x for x in [it.get("volume") and f"vol {it['volume']}", it.get("issue") and f"issue {it['issue']}", it.get("page") and f"pp {it['page']}"] if x)
    return {"doi": bare_doi(it.get("DOI")), "title": clean((it.get("title") or [""])[0]), "authors": "; ".join(auth), "affiliations": " || ".join(affs),
            "orcids": "; ".join(orc), "year": str(yr or ""), "venue": (it.get("container-title") or [""])[0], "publisher": it.get("publisher", ""),
            "volume_issue_pages": vip, "type": it.get("type", ""), "cited_by_count": str(it.get("is-referenced-by-count", "")),
            "keywords": "; ".join(it.get("subject", [])), "funders": "; ".join(f.get("name", "") for f in it.get("funder", [])),
            "license": "; ".join(l.get("URL", "") for l in it.get("license", [])[:1]), "url": it.get("URL", ""),
            "abstract": clean(it.get("abstract", "")), "sources": ["crossref"], "raw_files": [fp]}


def ep_rec(r, fp):
    auth = []; affs = []; orc = []
    for a in (r.get("authorList") or {}).get("author", []):
        nm = a.get("fullName", ""); auth.append(nm)
        ad = "; ".join(x.get("affiliation", "") for x in (a.get("authorAffiliationDetailsList") or {}).get("authorAffiliation", []))
        if ad: affs.append(f"{nm}: {ad}")
        oid = (a.get("authorId") or {})
        if oid.get("type") == "ORCID": orc.append(f"{nm}: {oid.get('value')}")
    ji = r.get("journalInfo") or {}
    vip = "; ".join(x for x in [ji.get("volume") and f"vol {ji['volume']}", ji.get("issue") and f"issue {ji['issue']}", r.get("pageInfo") and f"pp {r['pageInfo']}"] if x)
    ftu = [u.get("url") for u in (r.get("fullTextUrlList") or {}).get("fullTextUrl", []) if u.get("availabilityCode") in ("OA", "F")]
    return {"doi": bare_doi(r.get("doi")), "title": clean(r.get("title")), "authors": "; ".join(auth), "affiliations": " || ".join(affs),
            "orcids": "; ".join(orc), "year": str(r.get("pubYear", "")), "venue": (ji.get("journal") or {}).get("title", ""),
            "volume_issue_pages": vip, "type": "; ".join((r.get("pubTypeList") or {}).get("pubType", [])), "cited_by_count": str(r.get("citedByCount", "")),
            "keywords": "; ".join((r.get("keywordList") or {}).get("keyword", [])), "funders": "; ".join(g.get("agency", "") for g in (r.get("grantsList") or {}).get("grant", [])),
            "license": r.get("license", ""), "oa_status": "OA" if r.get("isOpenAccess") == "Y" else "", "open_access_url": ftu[0] if ftu else "",
            "url": f"https://europepmc.org/article/{r.get('source')}/{r.get('id')}", "abstract": clean(r.get("abstractText")),
            "pmid": r.get("pmid", ""), "pmcid": r.get("pmcid", ""), "sources": ["europepmc"], "raw_files": [fp]}


def cg_rec(o, fp):
    md = o.get("metadata", {})
    g = lambda k: [x["value"] for x in md.get(k, [])]
    return {"doi": bare_doi((g("cg.identifier.doi") or [""])[0]), "title": clean((g("dc.title") or [""])[0]), "authors": "; ".join(g("dc.contributor.author")),
            "affiliations": "; ".join(g("cg.contributor.affiliation")), "year": ((g("dcterms.issued") or g("dc.date.issued") or [""])[0])[:4],
            "venue": "; ".join(g("cg.journal") or g("dcterms.isPartOf") or g("dcterms.publisher")), "volume_issue_pages": "; ".join(g("cg.volume") + g("cg.issue")),
            "type": "; ".join(g("dcterms.type") or g("dc.type")), "keywords": "; ".join(g("dcterms.subject") + g("cg.subject.agrovoc"))[:500],
            "countries": "; ".join(g("cg.coverage.country")), "funders": "; ".join(g("cg.contributor.donor")), "license": "; ".join(g("dcterms.license")),
            "oa_status": "; ".join(g("dcterms.accessRights")), "url": "https://hdl.handle.net/" + (o.get("handle") or ""), "abstract": clean((g("dcterms.abstract") or [""])[0]),
            "cgspace_handle": o.get("handle", ""), "cgspace_uuid": o.get("uuid", ""), "cg_identifier_url": "; ".join(g("cg.identifier.url")),
            "sources": ["cgspace"], "raw_files": [fp]}


def bj_rec(j, fp):
    return dict(j, sources=["banglajol"], raw_files=[fp])


def load():
    for f in sorted(glob.glob(str(RAWD / "*/*.json"))):
        rel = "02_raw/" + str(pathlib.Path(f).relative_to(ROOT / "02_raw")).replace("\\", "/")
        try: j = json.load(open(f, encoding="utf-8"))
        except Exception: continue
        api = pathlib.Path(f).parent.name
        if api == "openalex":
            for w in j.get("results", []) if "results" in j else [j]: add(oa_rec(w, rel))
        elif api == "crossref":
            m = j.get("message", {})
            for it in (m.get("items", []) if "items" in m else [m]): add(cr_rec(it, rel))
        elif api == "europepmc":
            for r in j.get("resultList", {}).get("result", []): add(ep_rec(r, rel))
        elif api == "cgspace":
            if "_embedded" in j and "searchResult" in j["_embedded"]:
                for o in j["_embedded"]["searchResult"]["_embedded"]["objects"]:
                    add(cg_rec(o["_embedded"]["indexableObject"], rel))
            elif "metadata" in j: add(cg_rec(j, rel))
        elif api == "banglajol_meta":
            add(bj_rec(j, rel))


SEP = r"\s*[-–‐:]?\s*"
PATS = [
    (r"\bB\.?\s?R\.?\s?R\.?\s?I\.?" + SEP + r"hybrid" + SEP + r"(?:dhan|rice)?" + SEP + r"0?(\d{1,2})\b(?![-.]\d)", "BRRI_HYBRID"),
    (r"\bB\.?\s?R\.?\s?R\.?\s?I\.?" + SEP + r"dhan" + SEP + r"(\d{1,3})\b(?!-\d)", "BRRI_DHAN"),
    (r"\bBina" + SEP + r"hybrid" + SEP + r"(?:dhan)?" + SEP + r"(\d{1,2})\b", "BINA_HYBRID"),
    (r"\bBina" + SEP + r"dhan" + SEP + r"(\d{1,2})\b(?!-\d)", "BINADHAN"),
    (r"\bBU" + SEP + r"aromatic" + SEP + r"hybrid" + SEP + r"(?:dhan)?" + SEP + r"(\d)\b", "BU_AROMATIC_HYBRID"),
    (r"\bBU" + SEP + r"dhan" + SEP + r"(\d)\b", "BU_DHAN"),
    (r"\bGAU" + SEP + r"dhan" + SEP + r"(\d)\b", "GAU_DHAN"),
    (r"\bBAU" + SEP + r"dhan" + SEP + r"(\d)\b", "BAU_DHAN"),
    (r"\bBRAC" + SEP + r"dhan" + SEP + r"(\d)\b", "BRAC_DHAN"),
    (r"\bIratom" + SEP + r"(\d{2})\b", "IRATOM"),
    (r"(?<![A-Za-z0-9])BR" + SEP + r"(\d{1,2})\b(?![-–]\d|\s*-?\s*Sub|\.\d|\s*\()", "BR"),
    (r"(?<![A-Za-z0-9])IR" + SEP + r"(8|5|20)\b(?![-–]\d|\.\d)", "IR"),
]
NAMED = [(r"\bBina\s*-?\s*sh?ail\b", "BINASHAIL"), (r"\bPajam\b", "OLD_PAJAM"), (r"\bPurbachi\b", "OLD_PURBACHI"),
         (r"\bBrishail\b", "OLD_BRISHAIL"), (r"\bBAU\s*-?\s*63\b", "OLD_BAU63"), (r"\bACI\s*dhan\s*-?\s*(\d)\b", "PVT_ACI_DHAN"),
         (r"\bSupreme\s*dhan\s*-?\s*(\d)\b", "PVT_SUPREME_DHAN"), (r"\bRabi\s*dhan\s*-?\s*(\d)\b", "PVT_RABI_DHAN")]


ALIASES = [(r"\bBR\s*-?\s*11\s*-?\s*Sub\s*-?\s*1\b", "BRRI_DHAN52", False), (r"\bSwarna\s*-?\s*Sub\s*-?\s*1\b", "BRRI_DHAN51", True),
           (r"\bBangabandhu\s*dhan\s*-?\s*100\b", "BRRI_DHAN100", False), (r"\bIR\s*-?\s*69690\s*-?\s*H?\b", "BRRI_HYBRID1", True)]
ALIAS_HITS = set()


def find_keys(text, bd_ok):
    out = {}
    if not text: return out
    t = text.replace(" ", " ")
    for pat, k, need_bd in ALIASES:
        m = re.search(pat, t, flags=re.I)
        if m and (bd_ok or not need_bd):
            out.setdefault(k, m.group(0) + " [alias]")
    for pat, pref in PATS:
        for m in re.finditer(pat, t, flags=re.I if pref not in ("BR", "IR") else 0):
            if pref in ("BR", "IR") and not bd_ok: continue
            n = int(m.group(1))
            k = f"{pref}{n}"
            if pref == "BRRI_DHAN" and n <= 26: k = f"BR{n}"
            if pref == "BR" and n >= 27: k = f"BRRI_DHAN{n}"
            out.setdefault(k, m.group(0))
    for pat, k in NAMED:
        m = re.search(pat, t, flags=re.I)
        if m: out.setdefault(k + (m.group(1) if m.groups() else ""), m.group(0))
    return out


def main_set():
    s = {}
    for r in csv.DictReader(open(ROOT / "05_output/final/bgd_rice_varieties.csv", encoding="utf-8-sig")):
        if r["rice_type"] == "inbred" or r["variety_id"].startswith(("RICE-BRRI_HYBRID", "RICE-BINA_HYBRID", "RICE-BU_AROMATIC_HYBRID")):
            s[r["variety_id"]] = r
    return s


if __name__ == "__main__":
    load()
    main = main_set()
    pubs = []
    for k, p in PUBS.items():
        p["pub_id"] = k; pubs.append(p)
    json.dump(pubs, open(OUT / "pubs.json", "w", encoding="utf-8"), ensure_ascii=False)
    rows = []
    for p in pubs:
        txt_all = f"{p['title']} {p.get('abstract', '')} {p.get('keywords', '')}"
        bd = bool(re.search(r"Bangladesh|BRRI|BINA|Gazipur|Mymensingh|Rangpur|Rajshahi|Khulna|Boro|Aman", txt_all))
        if not re.search(r"rice|paddy|Oryza|dhan", txt_all, re.I): continue
        kt = find_keys(p["title"], bd); ka = find_keys(p.get("abstract", ""), bd)
        for k in sorted(set(kt) | set(ka)):
            vid = "RICE-" + k
            if vid not in main: continue
            mb = "title" if k in kt else "abstract"
            if "[alias]" in (kt.get(k) or ka.get(k)): mb += " (alias)"
            rows.append({"pub_id": p["pub_id"], "variety_id": vid, "match_basis": mb,
                         "mention": kt.get(k) or ka.get(k), "n_varieties_in_title": len(kt), "n_varieties_total": len(set(kt) | set(ka))})
    with open(OUT / "mentions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["pub_id", "variety_id", "match_basis", "mention", "n_varieties_in_title", "n_varieties_total"])
        w.writeheader(); w.writerows(rows)
    print(len(pubs), "pubs;", len(rows), "mentions;", len({r['variety_id'] for r in rows}), "varieties;",
          len({r['variety_id'] for r in rows if r['match_basis'] == 'title'}), "with title match")
