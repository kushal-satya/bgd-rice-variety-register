"""L1: build literature / publications / people / institutions outputs + evidence_L1.csv.
Inputs: 04_working/L1/pubs.json, mentions.csv (phase3_L1_parse.py), directory.csv (phase3_L1_directory.py),
manual files 04_working/L1/key_overrides.csv, people_contacts.csv, institutions_manual.csv. No network."""
import sys, json, re, csv, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import ROOT
from phase3_L1_parse import main_set
W = ROOT / "04_working/L1"; FIN = ROOT / "05_output/final"
TODAY = datetime.date.today().isoformat()
MAIN = main_set()
PUBS = {p["pub_id"]: p for p in json.load(open(W / "pubs.json", encoding="utf-8"))}
MENT = list(csv.DictReader(open(W / "mentions.csv", encoding="utf-8")))


def rd(f):
    p = W / f
    return list(csv.DictReader(open(p, encoding="utf-8-sig"))) if p.exists() else []


OVR = rd("key_overrides.csv")  # variety_id,pub_id,action(key|notkey|drop|add),publication_type,note


def disp_name(vid):
    r = MAIN[vid]; return r["official_name_en"] or r["official_name_bn"] or vid


REL = re.compile(r"(variety for|varieties for|suitable for|variety (?:in|of) Bangladesh|a new\b|new (?:high|rice|aromatic|salt|zinc|drought|submergence)|"
                 r"^\s*(?:BRRI|Bina|BR)\s*[- ]?(?:dhan|hybrid)?\s*[- ]?\d+\s*[:\-–]|development of .*variet|developing .*variet|released|release of|"
                 r"isolated through|high[- ]yielding .*variety|promising .*(?:rice|variet)|ecosystem of Bangladesh|for (?:the )?(?:boro|aman|aus) season|"
                 r"a (?:salt|zinc|drought|submergence|premium|short|cold)[- ]\w+.*variety)", re.I)
NOTREL = re.compile(r"^\s*(?:the\s+)?(?:effects?|influence|response|performance|impacts?|evaluation|determination|assessment|study|studies|comparative|growth|yield performance|amelioration|validation|optimi[sz]|weeding|callus)\b", re.I)
ADO = re.compile(r"adopt|impacts? of (?:the )?(?:adoption|BRRI|BINA|modern|stress|improved|salt|new)|diffusion|farmers'? (?:perception|preference)|welfare|returns? to|economic|profitab|yield gap|willingness|consumer", re.I)
GEN = re.compile(r"gene\b|genes\b|QTL|marker|introgress|genetic|transform|CRISPR|mutant|mutation|SNP|genom|pyramid|heterosis|parental line|"
                 r"maintainer|restorer|backcross|haplotype|allele|transcript|tissue culture|callus|regenerat|in vitro|molecular|diversity|"
                 r"combining ability|heritab|breeding", re.I)


def classify(p, vid, basis):
    t = p["title"]; ab = p.get("abstract", "")
    src = p.get("sources", []); typ = (p.get("type") or "").lower()
    if re.search(r"\breview\b", t, re.I): return "review"
    if basis.startswith("title") and REL.search(t) and not NOTREL.search(t) and not GEN.search(t.split(":")[-1] if ":" in t else t) and not ADO.search(t): return "release/description paper"
    if "cgspace" in src and not re.search(r"journal|article", typ): return "CGIAR report"
    if ADO.search(t): return "adoption/impact"
    if GEN.search(t): return "breeding/genetics"

    return "other"


def key_rank(p):
    """lower = better candidate for key paper"""
    src = p.get("sources", []); doi = p.get("doi", "")
    v = (p.get("venue") or "").lower()
    pen = 0
    if not doi: pen += 2
    if "zenodo" in doi or "zenodo" in v: pen += 3
    if "correction" in p["title"].lower(): pen += 10
    if "dataset" in p["title"].lower(): pen += 1
    return (pen, p.get("year") or "9999")


def snippet(s, n=300):
    s = (s or "").strip(); return s if len(s) <= n else s[:n - 3].rsplit(" ", 1)[0] + "..."


def build():
    # ---------- literature rows
    rows = {}
    for m in MENT:
        p = PUBS[m["pub_id"]]; vid = m["variety_id"]
        rows[(vid, m["pub_id"])] = {"variety_id": vid, "pub": p, "match_basis": m["match_basis"], "mention": m["mention"],
                                     "publication_type": classify(p, vid, m["match_basis"]), "is_key_paper": "no", "note": ""}
    for o in OVR:
        k = (o["variety_id"], o["pub_id"])
        if o["action"] == "drop": rows.pop(k, None); continue
        if o["action"] == "add" and k not in rows and o["pub_id"] in PUBS:
            rows[k] = {"variety_id": o["variety_id"], "pub": PUBS[o["pub_id"]], "match_basis": o.get("match_basis") or "full text",
                       "mention": "", "publication_type": o.get("publication_type") or "other", "is_key_paper": "no", "note": o.get("note", "")}
        if k in rows:
            if o.get("publication_type"): rows[k]["publication_type"] = o["publication_type"]
            if o.get("note"): rows[k]["note"] = o["note"]
    # auto key paper: best release/description paper per variety, title-matched, <=2 varieties in title
    forced = {(o["variety_id"], o["pub_id"]): o["action"] for o in OVR if o["action"] in ("key", "notkey")}
    byv = {}
    for k, r in rows.items():
        byv.setdefault(r["variety_id"], []).append(r)
    for vid, rs in byv.items():
        fk = [r for r in rs if forced.get((vid, r["pub"]["pub_id"])) == "key"]
        if fk:
            for r in fk: r["is_key_paper"] = "yes"
            continue
        cand = [r for r in rs if r["publication_type"] == "release/description paper" and r["match_basis"].startswith("title")
                and forced.get((vid, r["pub"]["pub_id"])) != "notkey"]
        if cand:
            cand.sort(key=lambda r: key_rank(r["pub"])); cand[0]["is_key_paper"] = "yes"
    lit = []
    for (vid, pid), r in sorted(rows.items(), key=lambda kv: (kv[0][0], kv[1]["is_key_paper"] != "yes", kv[1]["pub"].get("year") or "")):
        p = r["pub"]
        lit.append({"variety_id": vid, "publication_type": r["publication_type"], "is_key_paper": r["is_key_paper"], "title": p["title"],
                    "authors": p.get("authors", ""), "year": p.get("year", ""), "venue": p.get("venue", ""),
                    "volume_issue_pages": p.get("volume_issue_pages", ""), "doi": p.get("doi", ""),
                    "url": p.get("url") or (("https://doi.org/" + p["doi"]) if p.get("doi") else ""),
                    "open_access_url": p.get("open_access_url", ""), "source_api": "; ".join(p.get("sources", [])),
                    "match_basis": r["match_basis"], "abstract_snippet": snippet(p.get("abstract", "")), "retrieved_at": TODAY,
                    "pub_id": pid, "mention_as_written": r["mention"], "notes": r["note"]})
    cols = ["variety_id", "publication_type", "is_key_paper", "title", "authors", "year", "venue", "volume_issue_pages", "doi", "url",
            "open_access_url", "source_api", "match_basis", "abstract_snippet", "retrieved_at", "pub_id", "mention_as_written", "notes"]
    with open(FIN / "bgd_literature.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(lit)
    # ---------- publications
    used = {}
    for r in lit:
        used.setdefault(r["pub_id"], set()).add(r["variety_id"])
    pcols = ["pub_id", "doi", "title", "authors", "affiliations", "orcids", "corresponding_authors", "year", "venue", "publisher",
             "volume_issue_pages", "type", "cited_by_count", "keywords", "topics", "countries", "funders", "license", "oa_status", "affiliations_raw",
             "open_access_url", "url", "abstract", "openalex_id", "pmid", "pmcid", "cgspace_handle", "cgspace_uuid", "cg_identifier_url",
             "language", "sources", "raw_files", "varieties_linked", "retrieved_at"]
    with open(FIN / "bgd_publications.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=pcols, extrasaction="ignore"); w.writeheader()
        for pid in sorted(used, key=lambda x: (PUBS[x].get("year") or "", x)):
            p = dict(PUBS[pid]); p["sources"] = "; ".join(p.get("sources", [])); p["raw_files"] = "; ".join(p.get("raw_files", []))
            p["varieties_linked"] = "; ".join(sorted(used[pid])); p["retrieved_at"] = TODAY
            w.writerow(p)
    return lit


CORP = re.compile(r"Institute|Division|Program|Programme|University|Bangladesh|Department|Centre|Center|CGIAR", re.I)


def _surname(n):
    n = re.sub(r"[^A-Za-z ,]", " ", n).strip()
    if "," in n: return n.split(",")[0].strip().lower()
    toks = [t for t in n.split() if len(t) > 1]
    return toks[-1].lower() if toks else ""


def people(lit):
    contacts = {(c["person_name"].lower()): c for c in rd("people_contacts.csv")}
    land = {r["doi"]: r for r in rd("landing_extract.csv")}
    out = []
    for r in lit:
        if r["is_key_paper"] != "yes": continue
        p = PUBS[r["pub_id"]]
        affs = {}
        for chunk in (p.get("affiliations") or "").split(" || "):
            if ": " in chunk:
                nm, af = chunk.split(": ", 1); affs.setdefault(nm.strip(), af.strip())
        orc = dict(x.split(": ", 1) for x in (p.get("orcids") or "").split("; ") if ": " in x)
        corr = set(x.strip() for x in (p.get("corresponding_authors") or "").split(";") if x.strip())
        authors = [x.strip() for x in (p.get("authors") or "").split(";") if x.strip()]
        lr = land.get(p.get("doi", ""), {})
        src_note = ""
        if (not authors or any(CORP.search(a) for a in authors)) and lr.get("meta_authors"):
            authors = [x.strip() for x in lr["meta_authors"].split(";") if x.strip()]
            src_note = "author list from citation_author meta tags of the landing page (API list contained institution names)"
        authors = [a for a in authors if not CORP.search(a)]
        for i, a in enumerate(authors):
            a_clean = a.rstrip("*").strip()
            af = affs.get(a, "")
            sn = _surname(a_clean)
            same = [x for x in authors if _surname(x.rstrip("*")) == sn]
            if not af and sn and len(same) == 1:  # surname fallback only when unambiguous within the paper
                hits = [v for nm, v in affs.items() if _surname(nm) == sn]
                if len(hits) == 1: af = hits[0]
            oc = orc.get(a, "")
            if not oc and sn and len(same) == 1:
                hits = [v for nm, v in orc.items() if _surname(nm) == sn]
                if len(hits) == 1: oc = hits[0]
            is_corr = a in corr or a_clean in corr or a.endswith("*")
            c = contacts.get(a_clean.lower(), {})
            out.append({"variety_id": r["variety_id"], "person_name": a_clean, "author_position": i + 1,
                        "role_as_stated": ("author of key paper (" + r["publication_type"] + ")") + (" - corresponding author" if is_corr else ""),
                        "affiliation_as_stated": af, "orcid": oc,
                        "source": ("doi:" + p["doi"]) if p.get("doi") else p.get("url", ""),
                        "current_position_as_stated": c.get("current_position_as_stated", ""),
                        "professional_email": c.get("professional_email", ""), "professional_phone": c.get("professional_phone", ""),
                        "contact_source_url": c.get("contact_source_url", ""), "contact_source_type": c.get("contact_source_type", ""),
                        "notes": "; ".join(x for x in [src_note, c.get("notes", "")] if x)})
    for e in rd("people_extra.csv"):  # breeders named explicitly in official/publication sources; paper-printed corresponding e-mails
        out.append(e)
    cols = ["variety_id", "person_name", "author_position", "role_as_stated", "affiliation_as_stated", "orcid", "source",
            "current_position_as_stated", "professional_email", "professional_phone", "contact_source_url", "contact_source_type", "notes"]
    with open(FIN / "bgd_variety_people.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(out)
    return out


DIV = re.compile(r"((?:Plant Breeding|Hybrid Rice|Biotechnology|Genetic Resources? (?:and|&) Seed|Grain Quality (?:and|&) Nutrition|Plant Physiology|"
                 r"Genetics and Plant Breeding|Department of Genetics and Plant Breeding)[^,;]*(?:Division|Department|Dept\.?)?)", re.I)


def rank_of(p, r):
    d = p.get("doi", ""); v = (p.get("venue") or "").lower()
    if d.startswith("10.32942") or "rxiv" in v or "research square" in v: return "6_secondary"
    if "zenodo" in d or "irrn" in d or "International Rice Research" in (p.get("venue") or "") or r["publication_type"] == "CGIAR report": return "4_cgiar_record"
    return "5_peer_reviewed"


def evidence(lit):
    rows = []
    for r in lit:
        if r["is_key_paper"] != "yes": continue
        p = PUBS[r["pub_id"]]; key = r["variety_id"].replace("RICE-", "")
        rf = (p.get("raw_files") or [""])[0]
        base = {"pilot_key": key, "source_id": "L1-" + (p.get("doi") or r["pub_id"])[:60], "source_title": f"{p.get('authors','').split(';')[0]} et al. ({p.get('year')}) {p['title']}"[:300],
                "authority_rank": rank_of(p, r), "local_file": rf, "page": "", "method": "api_json", "validation": "unvalidated",
                "confidence": "high" if r["match_basis"] == "title" else "medium"}
        if p.get("doi"):
            rows.append(dict(base, field="doi_key_paper", value=p["doi"], value_raw=p["doi"], locator=f"title: {p['title'][:120]}",
                             notes=f"publication_type={r['publication_type']}; match_basis={r['match_basis']}; venue={p.get('venue','')}"))
        # developer division from first-author / any affiliation strings
        land = {x["doi"]: x for x in rd("landing_extract.csv")}
        affs = " || ".join(x for x in [p.get("affiliations_raw") or "", land.get(p.get("doi", ""), {}).get("meta_institutions", ""), p.get("affiliations") or ""] if x)
        m = DIV.search(affs) if r["publication_type"] in ("release/description paper", "breeding/genetics") else None
        if m and re.search(r"BRRI|Bangladesh Rice|BINA|Nuclear Agriculture|Agricultural University|Bangabandhu|Gazipur", affs, re.I):
            inst = "BRRI" if re.search(r"BRRI|Bangladesh Rice Research", affs, re.I) else ("BINA" if re.search(r"BINA|Nuclear Agriculture", affs, re.I) else "")
            val = (m.group(1).strip() + (", " + inst if inst else ""))
            rows.append(dict(base, field="developer_division", value=val, value_raw=m.group(0), locator="author affiliation in API metadata",
                             confidence="medium", notes="division of authors of the key paper; not an official statement of the developing division"))
    for e in rd("evidence_extra.csv"):
        rows.append(e)
    cols = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file", "page", "locator",
            "method", "validation", "confidence", "notes"]
    with open(ROOT / "04_working/evidence_L1.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    return rows


def institutions():
    rows = rd("institutions_manual.csv")
    cols = ["institution", "division", "official_website", "official_public_contact", "contact_person_as_listed", "source_url", "local_file", "retrieved_at", "notes"]
    with open(FIN / "bgd_institutions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    return rows


if __name__ == "__main__":
    lit = build(); ppl = people(lit); ev = evidence(lit); ins = institutions()
    kv = {r["variety_id"] for r in lit if r["is_key_paper"] == "yes"}; anyv = {r["variety_id"] for r in lit}
    print(f"literature rows {len(lit)}; varieties with >=1 paper {len(anyv)}/{len(MAIN)}; with key paper {len(kv)}; people rows {len(ppl)}; evidence {len(ev)}; institutions {len(ins)}")
