"""E5 (round 3, 2026-11-10): the release/description paper of each public variety, with its authors in printed order.

Writes 04_working/PEOPLE/release_papers.csv (one row per variety x paper). No network: the candidate search is
scripts/phase3_PEOPLE_release_search.py (Crossref + 04_working/L1/pubs.json -> release_candidates.csv); the papers
accepted after reading the title and abstract are listed in ACCEPTED below. A paper is accepted only when its title or
abstract makes the variety the subject (its development, release or description), not a passing mention.

Author order, affiliations and the corresponding author are taken from the paper as printed where an open copy was
archived (local_file); otherwise from the API metadata in 04_working/L1/pubs.json (basis column says which).
Corresponding e-mail: copied only when it is a professional (institutional) address; every corresponding address
printed in these papers is webmail, so the column stays blank and the note says so (contact rule,
00_admin/rights_and_personal_data_policy.md).
Also appends to the L1 input 04_working/L1/key_overrides.csv (action key, publication_type release/description paper) for
an accepted paper that is already in pubs.json but is not the variety's key paper, only when the variety has no key paper,
so that phase3_L1_build.py makes it the key paper and doi_key_paper is filled (never replaced) at the next rebuild.
"""
import csv, json, re, sys, pathlib
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import ROOT  # noqa: E402

PW = ROOT / "04_working/PEOPLE"; L1 = ROOT / "04_working/L1"
RP = "02_raw/literature_pages/release_papers/"
BRRI_PBD = "Plant Breeding Division, Bangladesh Rice Research Institute, Gazipur-1701, Bangladesh"
WEBMAIL_NOTE = "the corresponding e-mail printed in the paper is a webmail address and is not copied (contact rule)"

# doi -> transcription from the archived copy (authors in printed order, affiliation per author, corresponding author)
PRINTED = {
    "10.31248/jasp2020.235": dict(
        local_file=RP + "10_31248_jasp2020_235.pdf",
        authors=["Md. Abdul Kader", "Tamal Lata Aditya", "Ratna Rani Majumder", "Tapas Kumer Hore", "A K M Shalahuddin", "Md. Ehsanul Haq"],
        affs=[BRRI_PBD, "Bangladesh Rice Research Institute, Gazipur-1701, Bangladesh"] + [BRRI_PBD] * 4,
        corresponding="Md. Ehsanul Haq", corr_note=WEBMAIL_NOTE + "; a mobile number printed with it is not copied",
        locator="p. 224, author block"),
    "10.3329/brj.v23i1.46080": dict(
        local_file=RP + "10_3329_brj_v23i1_46080.pdf",
        authors=["M A Kader", "T L Aditya", "R R Majumder", "T K Hore", "A K M Shalahuddin", "A Amin"],
        affs=["Plant Breeding Division, BRRI", "Director (Research), BRRI, Gazipur, Bangladesh"] + ["Plant Breeding Division, BRRI"] * 4,
        corresponding="M A Kader", corr_note=WEBMAIL_NOTE, locator="p. 45, author block and footnote"),
    "10.3329/brj.v23i1.46081": dict(
        local_file=RP + "10_3329_brj_v23i1_46081.pdf",
        authors=["A K M Shalahuddin", "A S M Masuduzzaman", "M M Emam Ahmed", "T L Aditya", "M S Kabir"],
        affs=["Scientific Officer, Plant Breeding Division, BRRI", "Chief Scientific Officer, Office of Director (Research), BRRI",
              "Scientific Officer, Plant Breeding Division, BRRI", "Director (Research), BRRI", "Director General, BRRI, Gazipur"],
        corresponding="A K M Shalahuddin", corr_note=WEBMAIL_NOTE, locator="p. 57, author block and footnote"),
    "10.3329/brj.v29i1.90747": dict(
        local_file=RP + "10_3329_brj_v29i1_90747.pdf",
        authors=["M R A Sarker", "R J Promee", "M A Rahman", "M S Rahman", "B Karmakar", "K M Iftekharuddaula"],
        affs=["Plant Breeding Division, BRRI"] * 3 + ["Plant Physiology Division, BRRI", "Adaptive Research Division, BRRI", "Plant Breeding Division, BRRI"],
        corresponding="M R A Sarker", corr_note=WEBMAIL_NOTE, locator="p. 18, author block and footnote"),
    "10.1371/journal.pone.0294573": dict(
        local_file="02_raw/literature_pages/10_1371_journal_pone_0294573.html", authors=None, affs=None,
        corresponding="M. Akhlasur Rahman", corr_note=WEBMAIL_NOTE, locator="landing page, author list"),
}
# variety -> doi of its release/description paper (the 21 key papers already in bgd_literature.csv, and new finds)
ACCEPTED = {
    "RICE-BR20": "10.5281/zenodo.7218534", "RICE-BR21": "10.5281/zenodo.7218534",
    "RICE-BRRI_DHAN47": "10.3860/irrn.v32i1.1093", "RICE-BRRI_DHAN63": "10.11648/j.jps.20180605.13",
    "RICE-BRRI_DHAN66": "10.3329/brj.v23i1.46080", "RICE-BRRI_DHAN67": "10.3329/brj.v29i1.90747",
    "RICE-BRRI_DHAN70": "10.17265/1934-7391/2018.05.001", "RICE-BRRI_DHAN71": "10.9734/ijpss/2020/v32i1230347",
    "RICE-BRRI_DHAN79": "10.9734/ajrcs/2024/v9i1253", "RICE-BRRI_DHAN80": "10.9734/ejnfs/2020/v12i930294",
    "RICE-BRRI_DHAN84": "10.9734/aprj/2020/v6i130117", "RICE-BRRI_DHAN91": "10.3329/brj.v23i1.46081",
    "RICE-BRRI_DHAN93": "10.31248/jasp2020.235", "RICE-BRRI_DHAN94": "10.31248/jasp2020.235", "RICE-BRRI_DHAN95": "10.31248/jasp2020.235",
    "RICE-BRRI_DHAN97": "10.1371/journal.pone.0294573", "RICE-BRRI_DHAN99": "10.1371/journal.pone.0294573",
    "RICE-BRRI_DHAN98": "10.1016/j.dib.2024.111092", "RICE-BRRI_DHAN100": "10.9734/aprj/2021/v8i130164",
    "RICE-BRRI_DHAN102": "10.9734/jeai/2023/v45i42112", "RICE-BRRI_DHAN104": "10.9734/ajaar/2023/v22i4448",
    "RICE-BRRI_DHAN107": "10.9734/ajrcs/2024/v9i2267",
}
# per-paper notes where the printed record differs from the API record
NEW_PUBS = {
    "10.3329/brj.v29i1.90747": dict(year_note="issue labelled 2025 (vol. 29 no. 1); the article page and Crossref give 2026"),
}


def main():
    P = {p["pub_id"]: p for p in json.load(open(L1 / "pubs.json", encoding="utf-8"))}
    lit = pd.read_csv(ROOT / "05_output/final/bgd_literature.csv", dtype=str, keep_default_na=False)
    rows = []
    for vid, doi in ACCEPTED.items():
        p = P.get("doi:" + doi, {}); pr = PRINTED.get(doi, {}); nw = NEW_PUBS.get(doi, {})
        if pr.get("authors"):
            authors, affs, basis = pr["authors"], pr["affs"], "as printed in the archived copy (" + pr["locator"] + ")"
        else:
            authors = [a.strip() for a in (p.get("authors") or "").split(";") if a.strip() and not re.search(r"Institute|Division|Bangladesh", a)]
            amap = {}
            for ch in (p.get("affiliations") or "").split(" || "):
                if ": " in ch:
                    nm, af = ch.split(": ", 1); amap.setdefault(nm.strip(), af.strip())
            # exact name, else the unique affiliation entry with the same surname ('Debsharma SK', 'Khandakar Md. Iftekharuddaula')
            sur = lambda n: (n.split(",")[0] if "," in n else (n.split()[-1] if n.split() else "")).strip(" .*").lower()
            affs = []
            for a in authors:
                hit = amap.get(a) or ""
                if not hit:
                    c = [f for nm, f in amap.items() if sur(nm) == sur(a) or nm.split()[0].lower() == sur(a)]
                    hit = c[0] if len(set(c)) == 1 and sum(sur(x) == sur(a) for x in authors) == 1 else ""
                affs.append(hit)
            basis = "API metadata (04_working/L1/pubs.json: " + ", ".join(p.get("sources", [])) + "); order as deposited"
        old = lit[(lit.variety_id == vid) & (lit.doi == doi)]
        status = "key paper in bgd_literature.csv before round 3" if len(old) and old.is_key_paper.iloc[0] == "yes" else "new (E5, round 3)"
        corr = pr.get("corresponding", "")
        if not corr:
            star = [a for a in (p.get("corresponding_authors") or "").split(";") if a.strip()]
            corr = star[0].strip() if star else ""
        rows.append(dict(
            variety_id=vid, doi=doi, title=nw.get("title") or p.get("title", ""), year=nw.get("year") or p.get("year", ""),
            journal=nw.get("venue") or p.get("venue", ""), authors="; ".join(authors),
            affiliations=" || ".join(f"{a}: {f}" for a, f in zip(authors, affs) if f),
            corresponding_author=corr, corresponding_email="",
            match_basis="title names the variety; the paper describes its development/release (title and abstract read)",
            url="https://doi.org/" + doi, local_file=pr.get("local_file", ""), author_basis=basis, status=status,
            notes="; ".join(x for x in [pr.get("corr_note", "") if corr else "corresponding author not identified (no open copy archived; publisher page refused automated access or was not read)",
                                         nw.get("year_note", "")] if x)))
    D = pd.DataFrame(rows)
    D.to_csv(PW / "release_papers.csv", index=False, encoding="utf-8-sig")
    # ---------- L1 input: make an accepted paper the variety's key paper when the variety has none (doi_key_paper only if blank)
    ovr_f = L1 / "key_overrides.csv"
    ovr = list(csv.DictReader(open(ovr_f, encoding="utf-8-sig")))
    have_key = set(lit[lit.is_key_paper == "yes"].variety_id)
    seen = {(o["variety_id"], o["pub_id"], o["action"]) for o in ovr}
    add = []
    for vid, doi in ACCEPTED.items():
        if vid in have_key or ("doi:" + doi) not in P:
            continue
        for action in ("key",):
            if (vid, "doi:" + doi, action) not in seen:
                add.append({"variety_id": vid, "pub_id": "doi:" + doi, "action": action, "publication_type": "release/description paper",
                            "note": "E5 round 3: release/description paper of the variety (title and abstract read; archived PDF)"})
    if add:
        with open(ovr_f, "a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(ovr[0].keys()), extrasaction="ignore"); w.writerows(add)
    print(f"release papers {len(D)} rows, {D.doi.nunique()} papers, {D.variety_id.nunique()} varieties "
          f"({(D.status.str.startswith('new')).sum()} new); with corresponding author {(D.corresponding_author != '').sum()}; "
          f"key_overrides rows added {len(add)}")


if __name__ == "__main__":
    main()
