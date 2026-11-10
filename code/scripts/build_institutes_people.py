"""E3 (round 3, 2026-11-10): national institute (NARS), division, NSB proposer, breeders and professional contacts per variety.

Runs after scripts/phase3_L1_build.py (which writes bgd_variety_people.csv and bgd_institutions.csv from the key papers and
04_working/L1/*) and before assemble.py. No network: the official pages it reads were archived by
scripts/phase3_PEOPLE_fetch.py (manifest part 02_raw/_manifest_parts/PEOPLE.csv).

Inputs   05_output/final/bgd_rice_varieties.csv      developer, developer_std, developer_type, developer_division (previous build)
         05_output/final/bgd_nsb_decisions_full.csv  developer_applicant and the verbatim passage of every approval decision
         05_output/final/bgd_variety_people.csv      as written by phase3_L1_build.py (authors of key papers)
         04_working/L1/institutions_manual.csv, 04_working/L1/directory.csv, 04_working/evidence_L1.csv
         04_working/PEOPLE/institutions_extra.csv    official name, ministry, address, phone, fax, role mailbox, head (transcribed)
         02_raw/bina/varieties/*.html                BINA variety pages (officer in charge of each page)
         04_working/PEOPLE/release_papers.csv        E5: release/description paper per variety, authors in printed order
Outputs  04_working/PEOPLE/variety_nars.csv          one row per register variety (all of them): institute, division, proposer
         04_working/evidence_PEOPLE.csv              the same as evidence rows (fields nars_institute, nars_division,
                                                     proposer_as_printed, breeder_named; developer_division where a source
                                                     states the division, which assemble.py already carries into the register)
         05_output/final/bgd_variety_people.csv      extended: rows for breeders named in NSB minutes, BINA page officers and
                                                     current heads of the developing division; new columns (see COLS);
                                                     E5: authors of the variety's release paper get role 'release-paper
                                                     author', printed author order, is_first_author/is_corresponding_author
         05_output/final/bgd_institutions.csv        extended: name (Bangla/English), ministry, address, phone, fax, role
                                                     mailbox, head, and one row for every other developer in the register

Contact rule (00_admin/rights_and_personal_data_policy.md): institutional office numbers, role mailboxes, and the work
e-mail of named heads/breeders as published on the institution's own site or printed as a corresponding-author address.
Webmail (gmail, yahoo, ...) and mobile numbers are never copied; attendance sheets are never read.
Idempotent: rows this script adds are dropped and rebuilt on every run.
"""
import csv, glob, pathlib, re, sys, datetime
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import ROOT, _manifest_rows  # noqa: E402

FIN = ROOT / "05_output/final"; W = ROOT / "04_working"; PW = W / "PEOPLE"
TODAY = datetime.date.today().isoformat()
AGENT = "PEOPLE"
WEBMAIL = re.compile(r"[\w.+\-]+@(?:gmail|yahoo|hotmail|outlook|live|ymail|rediffmail)\.\w+(?:\.\w+)?", re.I)
MOBILE = re.compile(r"(?:\+?88)?[0০][1১][3-9৩-৯](?:[\s\-]?[0-9০-৯]){8}")
BN = re.compile(r"[ঀ-৿]")
MAN = {}
for _r in _manifest_rows():
    MAN.setdefault(_r["file_path"].replace("\\", "/"), _r.get("source_url", ""))


def rd(p):
    return pd.read_csv(p, dtype=str, keep_default_na=False) if pathlib.Path(p).exists() else pd.DataFrame()


R = rd(FIN / "bgd_rice_varieties.csv")
N = rd(FIN / "bgd_nsb_decisions_full.csv")
N = N[N.variety_id != ""]
APPROVAL = ["release", "release_provisional", "registration_provisional", "registration_full", "registration_conditional"]

# ---------------------------------------------------------------- institute
INST_STD = {"BRRI": "BRRI", "BINA": "BINA", "BAU": "BAU", "BSMRAU": "BSMRAU/GAU", "University of Rajshahi": "RU", "BADC": "BADC", "BRAC": "BRAC"}
CATEGORY = {"public research institute": "NARS institute", "university": "public university", "public seed agency": "public seed corporation",
            "NGO": "NGO", "private company": "private company", "foreign public": "IRRI line (introduced)", "introduction": "introduction"}
INST_NAME = {"BRRI": "Bangladesh Rice Research Institute", "BINA": "Bangladesh Institute of Nuclear Agriculture",
             "BAU": "Bangladesh Agricultural University", "BSMRAU/GAU": "Gazipur Agricultural University (formerly BSMRAU)",
             "RU": "University of Rajshahi", "BADC": "Bangladesh Agricultural Development Corporation", "BRAC": "BRAC"}
# proposer text (Bangla or English, as printed) -> institute; first match wins
PROP = [(r"ধান\s*গবেষ|ব্রি(?![ঀ-৿])|বি\s*,?\s*আর\s*,?\s*আর\s*,?\s*আই|^বি$|BRRI|Rice Research", "BRRI"), (r"পরমাণু|আনবিক|আণবিক|বিনা|BINA|Nuclear", "BINA"),
        (r"বঙ্গবন্ধু|শেখ মুজিব|বিএসএমআরএইউ|গাজীপুর কৃষি|জিএইউ|BSMRAU|Gazipur Agri", "BSMRAU/GAU"),
        (r"বাংলাদেশ কৃষি\s*বিশ্ববিদ্যালয়|বাকৃবি|\bBAU\b", "BAU"), (r"রাজশাহী বিশ্ববিদ্যালয়|Rajshahi", "RU"),
        (r"কৃষি উন্নয়ন কর্পোরেশন|বিএডিসি|BADC", "BADC"), (r"ব্র্যাক|বর্যাক|BRAC", "BRAC"), (r"আয়শা আবেদ|Ayesha", "Ayesha Abed Foundation")]


def inst_from_text(t):
    for rx, lab in PROP:
        if re.search(rx, t or "", re.I):
            return lab
    return ""


def nars_institute(r):
    std = r.developer_std
    if std in INST_STD:
        return INST_STD[std], "register developer_std"
    if r.developer_type in ("foreign public", "introduction"):
        lab = inst_from_text(r.developer)
        return lab, f"register developer field ('{r.developer}'); line bred abroad ({std}), {lab or 'national institute not stated'} as releasing institute"
    return std, "register developer_std (non-NARS developer: company or NGO)"


# ---------------------------------------------------------------- proposer as printed in the NSB minutes
LEAD = re.compile(r"^(?:.*?(?:ভিত্তিতে|সিদ্ধান্ত\s*[:ঃ]|আলোচ্য\s*(?:বিষয়|সূচী)[^:ঃ]*[:ঃ]))?\s*(?:[(\[]?\s*[০-৯0-9a-zA-Zক-ঙivx]{1,4}\s*[).\]]\s*)*", re.S)
CLAUSE = re.compile(r"([^।:;\n>]{3,160}?)\s*(?:কর্তৃক|কতৃক|কতৃর্ক|এর|-এর|’র|'র)\s*(?:প্রস্তাবিত|উদ্ভাবিত|উদ্বাবিত|উত্তাবিত)")


SUBJ = re.compile(r"^\s*(?:[(\[]?\s*[০-৯0-9a-zA-Zক-ঞ]{1,3}\s*[).\]]\s*)?([^()\d]{3,70}?)\s*(?:এর|-এর|’র)\s")


def clean_prop(s):
    s = re.sub(r"\[কলাম \d+\]", " ", s)
    # headings before the proposer: 'আলোচ্যসূচি-৫: X', 'বিষয় ৩: X', 'সিদ্ধান্ত ঃ X', '... বিবেচনা ঃ (i) X'
    s = re.sub(r"^.*(?:বিষয়|সূচী|সূচি|সিদ্ধান্ত|বিবেচনা)\s*[-–]?\s*[(]?[০-৯0-9]*[)]?\s*[:ঃ]\s*", "", s.strip(), flags=re.S)
    s = re.sub(r"^আলোচ্য\s*(?:বিষয়|সূচী|সূচি)\s*[-–]?\s*[০-৯0-9]+\s*", "", s)
    s = LEAD.sub("", s.strip()).strip(" ,.-ঃ:")
    # keep what follows the last connective of a long sentence ('... হওয়ায় প্রচলিত শর্ত সাপেক্ষে সাময়িকভাবে X')
    s = re.split(r"(?:হওয়ায়|সাপেক্ষে|সাময়িকভাবে|ভিত্তিতে|অনুমোদন|সুপারিশকৃত|,\s*কারিগরি কমিটি)\s+", s)[-1]
    s = re.sub(r"^(?:বোরো|আমন|আউশ)\s*মৌসুমে\s*চাষাবাদের\s*জন্য\s*", "", s)
    return s.strip(" ,.-ঃ:")


def norm(s):
    return re.sub(r"[\s\-–_.,;:()'\"]+", "", str(s)).lower()


def proposer(r):
    """(as printed, source dict) from the first approval decision of the variety."""
    d = N[(N.variety_id == r.variety_id) & N.decision_type.isin(APPROVAL)].sort_values("meeting_date")
    toks = {norm(x) for x in [r.official_name_bn, r.official_name_en, r.breeding_line, r.popular_name] + r.aliases.split("|") if len(norm(x)) >= 4}
    for x in d.itertuples():
        src = dict(source_file=x.source_file, pages=x.pages, meeting=x.meeting_no, dec_id=x.dec_id, url=x.source_url, decision=x.decision_type)
        da = x.developer_applicant
        passage = x.variety_passage_verbatim or x.variety_segment_verbatim
        # sentences, and the numbered items of a list sentence ('(১) X এর ... (২) Y এর ...')
        sents = [s for s in re.split(r"[।>\n]|(?=\(\s*[০-৯0-9]{1,2}\s*\))|(?<=\s)(?=[০-৯]{1,2}\.\s)", passage) if s.strip()]
        hits = [s for s in sents if toks and any(t in norm(s) for t in toks)]
        # 1) the proposer clause of the sentence that names the variety (beats developer_applicant, which in multi-variety
        #    agenda items sometimes carries the previous item's proposer, e.g. Binadhan-9 in NSB 77)
        for s in sorted(hits, key=lambda s: not re.match(r"\s*\(\s*[০-৯0-9]{1,2}\s*\)", s)):   # numbered decision items first
            ns = norm(s)
            pos = min((ns.find(t) for t in toks if t in ns), default=-1)
            # the clause that ends nearest before the variety's name ('X কর্তৃক উদ্ভাবিত <name>'), not an earlier item's
            ms = [m for m in CLAUSE.finditer(s) if len(norm(s[:m.end()])) <= pos + 1]
            if ms and clean_prop(ms[-1].group(1)):
                return clean_prop(ms[-1].group(1)), "clause before কর্তৃক/এর প্রস্তাবিত in the sentence naming the variety", src
            m = SUBJ.search(s)
            if m and re.match(r"\s*\(\s*[০-৯0-9]{1,2}\s*\)", s) and not re.search(r"জাতগুলো|হলো|নিম্নরূপ|যথা", m.group(1)):
                return clean_prop(m.group(1)), "subject '<developer> এর ...' of the numbered decision naming the variety", src
        if "as printed:" in da:
            return clean_prop(da.split("as printed:", 1)[1]), "developer_applicant (as printed)", src
        if not hits and len({clean_prop(c) for c in CLAUSE.findall(passage)}) == 1:
            return clean_prop(CLAUSE.search(passage).group(1)), "the only proposer clause in the passage", src
        if da and BN.search(da):
            return clean_prop(da), "developer_applicant (Bangla, as printed)", src
        for s in hits:   # '(৩) মুক্তারপুর ভাণ্ডার এর S-2B (Krishan-12) হাইব্রিড জাতটি ...'
            m = SUBJ.search(s)
            if m and not re.search(r"জাতগুলো|হলো|নিম্নরূপ|যথা", m.group(1)):
                return clean_prop(m.group(1)), "subject '<developer> এর ...' of the sentence naming the variety", src
    if len(d):
        x = d.iloc[0]
        return "", "no proposer clause found; developer_applicant (standardised) = " + (x.developer_applicant or "blank"), \
            dict(source_file=x.source_file, pages=x.pages, meeting=x.meeting_no, dec_id=x.dec_id, url=x.source_url, decision=x.decision_type)
    return "", "no NSB approval decision in bgd_nsb_decisions_full.csv", {}


# ---------------------------------------------------------------- division
PBD_BRRI, HRD, BIO = "Plant Breeding Division, BRRI", "Hybrid Rice Division, BRRI", "Biotechnology Division, BRRI"
PBD_BINA = "Plant Breeding Division, BINA"
P_PBD, P_HRD, P_BIO = ("02_raw/brri/PEOPLE_div_plant_breeding.html", "02_raw/brri/PEOPLE_div_hybrid_rice.html", "02_raw/brri/PEOPLE_div_biotechnology.html")
P_BINA = "02_raw/bina/L1_plant_breeding_division.html"
STATED = {  # variety -> (division, basis, local_file, locator); read on the archived pages on 2026-11-10
    "RICE-BRRI_HYBRID1": (PBD_BRRI, "Hybrid Rice Division page: BRRI hybrid dhan1 was developed when hybrid research ran under the Plant Breeding Division (from 1998, ARMP project)", P_HRD, "ব্রি উদ্ভিদ প্রজনন বিভাগের তত্ত্বাবধানে ... ব্রি হাইব্রিড ধান১, উদ্ভাবিত হয়"),
    **{f"RICE-BRRI_HYBRID{i}": (HRD, "Hybrid Rice Division page names the variety among those the division developed and released", P_HRD,
                                f"ব্রি হাইব্রিড রাইস বিভাগ নতুন ... হাইব্রিড ধান উদ্ভাবন ও অবমুক্ত করে (ব্রি হাইব্রিড ধান{i})") for i in (5, 6, 7, 8)},
    **{f"RICE-BRRI_DHAN{i}": (BIO, "Biotechnology Division page: the division 'played an important role' in developing the variety (contributing division)", P_BIO,
                              "ব্রি জীবপ্রযুক্তি বিভাগ ... ব্রি ধান৮৬, ব্রি ধান৮৭, ব্রি ধান৮৯, ব্রি ধান৯২ এবং ব্রি ধান৯৬ উদ্ভাবনে গুরুত্বপূর্ণ ভূমিকা পালন করেছে") for i in (86, 87, 89, 92, 96)},
    "RICE-BU_DHAN2": ("Department of Genetics and Plant Breeding, BSMRAU", "NSB 90th meeting minutes: the breeder thanked for the variety is a professor of this department",
                      "02_raw/sca/nsb_minutes_090.pdf", "p. 4: ড. এম এ খালেক মিয়া, অধ্যাপক, জেনেটিক্স এন্ড প্লান্ট ব্রিডিং বিভাগ"),
}
INFER = {  # (institute, hybrid?) -> division by mandate; the variety is not named by the source
    ("BRRI", False): (PBD_BRRI, "inferred: the Plant Breeding Division's mandate is developing BRRI's modern varieties (division page); the variety itself is not named", P_PBD),
    ("BINA", False): (PBD_BINA, "inferred: BINA's Plant Breeding Division page says the division developed BINA's varieties of 14 crops including rice; the variety itself is not named", P_BINA),
}


def division(r, inst, l1):
    if r.variety_id in STATED:
        d, b, f, loc = STATED[r.variety_id]; return d, "stated", b, f, loc
    if r.developer_division:
        ev = l1.get(r.variety_id.replace("RICE-", ""), {})
        b = ("variety named on the BINA Plant Breeding Division page" if "BINA" in r.developer_division
             else "author affiliation of the key release paper")
        return r.developer_division, "stated", b, ev.get("local_file", ""), ev.get("locator", "") or ev.get("source_id", "")
    if r.variety_id == "RICE-PVT_RABI_DHAN1":
        x = N[(N.variety_id == r.variety_id) & (N.decision_type == "release")]
        f, pg = (x.source_file.iloc[0], x.pages.iloc[0]) if len(x) else ("", "")
        return ("Department of Agronomy and Agricultural Extension, University of Rajshahi (trials run jointly with ACI Limited)", "stated",
                "NSB minutes: the department and ACI Limited jointly ran the research on the line", f, f"pp. {pg}: রাজশাহী বিশ্ববিদ্যালয়ের এগ্রোনমী এন্ড এগ্রিকালচার এক্সটেনশন বিভাগ এবং এসিআই লিমিটেড যৌথভাবে")
    hyb = "HYBRID" in r.variety_id
    if inst == "BRRI" and hyb:
        n = int(re.sub(r"\D", "", r.variety_id) or 0)
        if n in (2, 3, 4):
            return (PBD_BRRI, "inferred", "inferred: released 2008-2010, before the Hybrid Rice Division was created (August 2012), while hybrid research sat in the Plant Breeding Division (Hybrid Rice Division page)", P_HRD, "")
        return (HRD, "inferred", "inferred: released after August 2012 by the division responsible for BRRI hybrids; the division page predates the release and does not name it", P_HRD, "")
    if (inst, hyb) in INFER and r.developer_type in ("public research institute",):
        d, b, f = INFER[(inst, hyb)]; return d, "inferred", b, f, ""
    if r.developer_type in ("private company", "NGO", "public seed agency"):
        return "", "not applicable", "no breeding division is published by this developer", "", ""
    return "", "not stated", "no source consulted names the division or department", "", ""


# ---------------------------------------------------------------- people
def keep_work_mail(s):
    """Drop webmail; keep institutional addresses. Returns (kept, dropped_any)."""
    parts = [p.strip() for p in re.split(r";", s or "") if p.strip()]
    kept = [p for p in parts if not WEBMAIL.search(p)]
    return "; ".join(kept), len(kept) < len(parts)


def bina_officers():
    from bs4 import BeautifulSoup
    out = []
    for f in sorted(glob.glob(str(ROOT / "02_raw/bina/varieties/*.html"))):
        t = BeautifulSoup(open(f, encoding="utf-8").read(), "html.parser").get_text(" ", strip=True)
        m = re.search(r"নাম ও পদবী\s+(.{3,60}?)\s+((?:প্রধান|মুখ্য|ঊর্ধ্বতন)\s*বৈজ্ঞানিক কর্মকর্তা)\s+(.{3,60}?বিভাগ)", t)
        if not m:
            continue
        stem = pathlib.Path(f).stem
        rel = "02_raw/bina/varieties/" + pathlib.Path(f).name
        out.append({"variety_id": "RICE-" + stem, "person_name": m.group(1).strip(), "role": "variety page officer (BINA)",
                    "role_as_stated": "দায়িত্বপ্রাপ্ত কর্মকর্তা (officer in charge) named on the BINA web page of the variety",
                    "affiliation_as_stated": f"{m.group(2).strip()}, {m.group(3).strip()}, বিনা, ময়মনসিংহ-২২০২",
                    "source": MAN.get(rel, ""), "source_locator": rel,
                    "notes": "officer responsible for the variety page, not a statement that this person bred the variety; the page's webmail address and mobile number are not copied"})
    return out


def nsb_breeders():
    """Breeders thanked by name in the NSB minutes (visually checked against the page image on 2026-11-10)."""
    f = "02_raw/sca/nsb_minutes_090.pdf"
    u = MAN.get(f, "")
    base = dict(role="breeder", source=u, source_locator=f + ", p. 4 (minutes of the 90th NSB meeting, 9 Oct 2016)", record_source="PEOPLE: NSB minutes")
    return [
        dict(base, variety_id="RICE-BRRI_DHAN78", person_name="ড. এ এস এম মাসুদুজ্জামান (Dr. A. S. M. Masuduzzaman)",
             role_as_stated="thanked by the NSB chair 'for developing the variety' (জাতটি উদ্ভাবনের জন্য), with his research team and BRRI",
             affiliation_as_stated="মুখ্য বৈজ্ঞানিক কর্মকর্তা, বাংলাদেশ ধান গবেষণা ইনস্টিটিউট (Chief Scientific Officer, BRRI; as printed in 2016)",
             notes="English spelling as in the author list of the BRRI dhan91 key paper (doi:10.3329/brj.v23i1.46081); not found in the 2026 BRRI directory, so no contact"),
        dict(base, variety_id="RICE-BU_DHAN2", person_name="ড. এম এ খালেক মিয়া (Dr. M. A. Khaleque Mian)",
             role_as_stated="thanked by the NSB chair 'for developing the variety' (জাতটি উদ্ভাবনের জন্য), with his research team and BSMRAU",
             affiliation_as_stated="অধ্যাপক, জেনেটিক্স এন্ড প্লান্ট ব্রিডিং বিভাগ, বঙ্গবন্ধু শেখ মুজিবুর রহমান কৃষি বিশ্ববিদ্যালয়, গাজীপুর (Professor, Dept of Genetics and Plant Breeding, BSMRAU)",
             notes="the OCR text reads '©.' for 'ড.'; read from the page image. English transliteration is ours. No departmental contact page exists on gau.edu.bd"),
    ]


def _pkey(n):
    """(surname, initials) of an author name in any of the printed forms ('Md. Abdul Kader', 'M A Kader', 'Salam, M.A.')."""
    n = re.sub(r"[*†]", "", n).strip()
    if "," in n:
        sur, given = n.split(",", 1)
    else:
        t = n.split(); sur, given = (t[-1] if t else ""), " ".join(t[:-1])
    ini = "".join(w[0] for w in re.split(r"[\s.\-]+", given) if w and w[0].isalpha()).lower()
    return re.sub(r"[^a-z]", "", sur.lower()), ini


def release_paper_authors():
    """E5 (round 3): the release/description paper of each variety (04_working/PEOPLE/release_papers.csv, written by
    scripts/phase3_PEOPLE_release_papers.py from the archived copy or the API record): {(variety_id, 'doi:'+doi): row}."""
    f = PW / "release_papers.csv"
    return {(r["variety_id"], "doi:" + r["doi"]): r for r in rd(f).to_dict("records")} if f.exists() else {}


def mark_release_authors(people, rp):
    """Rows from the key-paper author list (L1) whose paper is the variety's release paper become 'release-paper author',
    with author_position in printed order and the corresponding author flagged; papers without L1 rows (not yet in
    the literature table) get one row per author from release_papers.csv."""
    done = set()
    for x in people:
        r = rp.get((x["variety_id"], x.get("source", "")))
        if not r:
            continue
        auth = [a.strip() for a in r["authors"].split(";") if a.strip()]
        keys = [_pkey(a) for a in auth]
        k = _pkey(x["person_name"])
        pos = [i for i, kk in enumerate(keys) if kk == k] or [i for i, kk in enumerate(keys) if kk[0] == k[0] and sum(q[0] == k[0] for q in keys) == 1]
        if len(pos) == 1:
            x["author_position"] = pos[0] + 1
        corr = r["corresponding_author"] and _pkey(r["corresponding_author"]) in (k,) or \
            (r["corresponding_author"] and _pkey(r["corresponding_author"])[0] == k[0] and sum(q[0] == k[0] for q in keys) == 1)
        x["role"] = "release-paper author"
        x["is_corresponding_author"] = "yes" if corr or x.get("is_corresponding_author") == "yes" else "no"
        x["is_first_author"] = "yes" if str(x.get("author_position")) == "1" else "no"
        if not x.get("affiliation_as_stated") and len(pos) == 1:
            af = dict(a.split(": ", 1) for a in r["affiliations"].split(" || ") if ": " in a)
            x["affiliation_as_stated"] = af.get(auth[pos[0]], "")
        x["notes"] = "; ".join(y for y in [x.get("notes", ""), "author order as printed (" + r["author_basis"] + ")" if len(pos) == 1 else "position not matched to the printed list"] if y)
        done.add((x["variety_id"], x["source"]))
    out = []
    for key, r in rp.items():
        if key in done:
            continue
        auth = [a.strip() for a in r["authors"].split(";") if a.strip()]
        af = dict(a.split(": ", 1) for a in r["affiliations"].split(" || ") if ": " in a)
        for i, a in enumerate(auth):
            corr = bool(r["corresponding_author"]) and _pkey(r["corresponding_author"]) == _pkey(a)
            out.append({"variety_id": r["variety_id"], "person_name": a, "author_position": i + 1,
                        "role_as_stated": "author of the release/description paper" + (" - corresponding author" if corr else ""),
                        "affiliation_as_stated": af.get(a, ""), "source": key[1], "role": "release-paper author",
                        "is_corresponding_author": "yes" if corr else "no", "is_first_author": "yes" if i == 0 else "no",
                        "source_locator": r["local_file"] or r["url"], "record_source": "PEOPLE: release paper (04_working/PEOPLE/release_papers.csv)",
                        "notes": "; ".join(y for y in ["author order as printed (" + r["author_basis"] + ")", r["notes"] if corr else ""] if y)})
    return out


HEADS = {}  # division label -> head row from institutions_extra.csv


def head_rows(vrows):
    out = []
    for v in vrows:
        h = next((h for lab, h in HEADS.items() if v["nars_division"].startswith(lab)), None)
        if not h or not h["head_name_as_listed"]:
            continue
        mail = "; ".join(x for x in [h["head_work_email"], h["role_email"] and (h["role_email"] + " (division mailbox)")] if x)
        out.append({"variety_id": v["variety_id"], "person_name": h["head_name_as_listed"].split(",")[0].strip(), "role": "division head (current)",
                    "role_as_stated": "current head of the " + ("developing" if v["nars_division_basis"] == "stated" else "probable developing (inferred)")
                                      + " division, as listed on the institution's site",
                    "affiliation_as_stated": h["head_name_as_listed"].split(",", 1)[-1].strip() + ", " + v["nars_division"],
                    "source": h["head_source_url"], "source_locator": "institution directory / division page",
                    "current_position_as_stated": h["head_name_as_listed"].split(",", 1)[-1].strip(),
                    "professional_email": mail, "professional_phone": h["office_phone"],
                    "contact_source_url": h["head_source_url"], "contact_source_type": "official institutional site",
                    "notes": "head in 2026, not necessarily head when the variety was bred; contact for enquiries about the division's varieties"})
    return out


COLS = ["variety_id", "person_name", "author_position", "role_as_stated", "affiliation_as_stated", "orcid", "source",
        "current_position_as_stated", "professional_email", "professional_phone", "contact_source_url", "contact_source_type", "notes",
        # added by this script
        "role", "is_corresponding_author", "nars_institute", "nars_division", "source_locator", "record_source",
        # added by E5 (round 3): first author of the variety's release paper (blank on rows that are not release-paper authors)
        "is_first_author"]
ICOLS = ["institution", "division", "official_website", "official_public_contact", "contact_person_as_listed", "source_url", "local_file",
         "retrieved_at", "notes",
         "institution_short", "institution_name_en", "institution_name_bn", "division_name_en", "division_name_bn", "developer_category",
         "parent_ministry", "parent_ministry_source", "address", "office_phone", "fax", "role_email", "head_name_as_listed",
         "head_work_email", "head_source_url", "n_varieties", "contact_status"]
ECOLS = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file", "page", "locator",
         "method", "validation", "confidence", "notes"]


RP_DOI = {}


def main():
    PW.mkdir(exist_ok=True)
    RP_DOI.update({k[0]: k[1][4:] for k in release_paper_authors()})
    l1ev = rd(W / "evidence_L1.csv")
    l1 = {r.pilot_key: r._asdict() for r in l1ev[l1ev.field == "developer_division"].itertuples()} if len(l1ev) else {}
    extra = rd(PW / "institutions_extra.csv")
    for h in extra.to_dict("records"):
        if h["division_name_en"]:
            lab = h["division_name_en"] + ", " + {"BSMRAU/GAU": "BSMRAU", "RU": "University of Rajshahi"}.get(h["institution_short"], h["institution_short"])
            HEADS[lab] = h
    # ---------- per variety
    vrows, ev = [], []
    for r in R.itertuples():
        inst, ib = nars_institute(r)
        prop, pbasis, psrc = proposer(r)
        pinst = inst_from_text(prop) if prop else ""
        # 'NO' when the printed proposer names a public institute/BRAC/BADC other than the register's developer
        if not prop:
            match = ""
        elif pinst:
            match = "yes" if pinst == inst or (inst == "Ayesha Abed Foundation" and pinst == "BRAC") else "NO"
        else:
            match = "NO" if inst in INST_STD.values() else "not checked (company name)"
        div, dstat, dbasis, dfile, dloc = division(r, inst, l1)
        v = {"variety_id": r.variety_id, "variety_name": r.variety_name, "developer_category": CATEGORY.get(r.developer_type, r.developer_type),
             "nars_institute": inst, "nars_institute_name_en": INST_NAME.get(inst, inst), "nars_institute_basis": ib,
             "nars_division": div, "nars_division_basis": dstat, "nars_division_note": dbasis, "nars_division_source": dfile, "nars_division_locator": dloc,
             "proposer_as_printed": prop, "proposer_institute": pinst, "proposer_matches_institute": match, "proposer_basis": pbasis,
             "proposer_source": (f"{psrc.get('source_file','')}, pp. {psrc.get('pages','')} (NSB {psrc.get('meeting','')}, {psrc.get('dec_id','')}, {psrc.get('decision','')})" if psrc else ""),
             "n_named_breeders": 0, "n_people_rows": 0,
             "release_paper_doi": RP_DOI.get(r.variety_id, "")}
        vrows.append(v)
        key = r.variety_id.replace("RICE-", "")
        if psrc:
            ev.append(dict(pilot_key=key, field="proposer_as_printed", value=prop, value_raw=prop, source_id=f"NSB_{psrc['meeting']}",
                           source_title=f"NSB {psrc['meeting']} minutes", authority_rank="1_primary_legal", local_file=psrc["source_file"],
                           page=psrc["pages"].split("-")[0], locator=f"{psrc['dec_id']}, pp. {psrc['pages']}", method="ocr", validation="unvalidated",
                           confidence="medium" if prop else "low", notes=f"PEOPLE: {pbasis}; proposer institute {pinst or '?'}; matches register developer: {match or 'n/a'}"))
        ev.append(dict(pilot_key=key, field="nars_institute", value=inst, value_raw=r.developer, source_id="REGISTER_developer_std",
                       source_title="register developer / developer_std", authority_rank="7_reviewer_synthesis", local_file=r.local_file,
                       locator="developer_std", method="derived", validation="unvalidated", confidence="high" if inst in INST_STD.values() else "medium",
                       notes="PEOPLE: " + ib))
        if div:
            ev.append(dict(pilot_key=key, field="nars_division", value=div, value_raw=dloc[:200], source_id="PEOPLE-" + pathlib.Path(dfile).stem if dfile else "PEOPLE",
                           source_title=dfile, authority_rank="1_primary_legal" if "nsb_minutes" in dfile else "3_institute_page", local_file=dfile,
                           locator=dloc[:200], method="ocr" if dfile.endswith(".pdf") else "html", validation="visual_check" if r.variety_id == "RICE-BU_DHAN2" else "unvalidated",
                           confidence="high" if dstat == "stated" else "low", notes=f"PEOPLE: {dstat}; {dbasis}"))
            if dstat == "stated" and r.variety_id in STATED or r.variety_id == "RICE-PVT_RABI_DHAN1":
                # a source names the division: offer it to the register's developer_division (assemble.py RICE_FIELDS)
                ev.append(dict(ev[-1], field="developer_division", confidence="medium" if "contributing" in dbasis else "high",
                               validation="visual_check" if dfile.endswith(".pdf") else "unvalidated"))
    # ---------- people
    P = rd(FIN / "bgd_variety_people.csv")
    if "record_source" in P:
        P = P[P.record_source.str.startswith("L1") | (P.record_source == "")]
    vmap = {v["variety_id"]: v for v in vrows}
    lit = rd(FIN / "bgd_literature.csv")
    ptype = {(x.variety_id, "doi:" + x.doi): x.publication_type for x in lit[lit.is_key_paper == "yes"].itertuples()} if len(lit) else {}
    people = []
    for x in P.to_dict("records"):
        corr = "corresponding author" in x["role_as_stated"]
        rel = "release/description paper" in x["role_as_stated"]
        x["role"] = "corresponding author" if corr else ("developer (release-paper author)" if rel else "key-paper author")
        x["is_corresponding_author"] = "yes" if corr else "no"
        x["source_locator"] = x["source"]
        x["record_source"] = "L1: author list of the key paper (API metadata)"
        kept, dropped = keep_work_mail(x["professional_email"])
        if dropped:
            x["professional_email"] = kept
            x["notes"] = "; ".join(y for y in [x["notes"], "a webmail address printed for this person was not copied (contact rule)"] if y)
        if MOBILE.search(x.get("professional_phone", "")):
            x["professional_phone"] = MOBILE.sub("", x["professional_phone"]).strip(" ;,")
        people.append(x)
    rp = release_paper_authors()
    people += mark_release_authors(people, rp)
    for x in nsb_breeders():
        people.append(x)
    for x in bina_officers():
        if x["variety_id"] in vmap:
            x["record_source"] = "PEOPLE: BINA variety page"; people.append(x)
    for x in head_rows(vrows):
        x["record_source"] = "PEOPLE: institution directory"; people.append(x)
    for x in people:
        v = vmap.get(x["variety_id"], {})
        x["nars_institute"] = v.get("nars_institute", ""); x["nars_division"] = v.get("nars_division", "")
        x.setdefault("is_corresponding_author", "no"); x.setdefault("is_first_author", "")
        if v:
            v["n_people_rows"] += 1
            if x["role"] in ("breeder", "release-paper author", "developer (release-paper author)", "corresponding author") and \
                    (x["role"] in ("breeder", "release-paper author") or ptype.get((x["variety_id"], x["source"]), "") == "release/description paper"):
                v["n_named_breeders"] += 1
        if x["role"] == "breeder":
            ev.append(dict(pilot_key=x["variety_id"].replace("RICE-", ""), field="breeder_named", value=x["person_name"], value_raw=x["role_as_stated"],
                           source_id="NSB_90", source_title="NSB 90 minutes", authority_rank="1_primary_legal", local_file=x["source_locator"].split(",")[0],
                           page="4", locator=x["source_locator"], method="ocr", validation="visual_check", confidence="high", notes="PEOPLE: " + x["affiliation_as_stated"]))
    with open(FIN / "bgd_variety_people.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore"); w.writeheader()
        for x in sorted(people, key=lambda x: (x["variety_id"], x["role"] != "breeder", x["record_source"], int(x.get("author_position") or 0))):
            w.writerow({c: x.get(c, "") for c in COLS})
    # ---------- institutions
    man = rd(W / "L1/institutions_manual.csv")
    ex = {(h["institution"], h["division"]): h for h in extra.to_dict("records")}
    counts_i = pd.Series([v["nars_institute"] for v in vrows]).value_counts().to_dict()
    counts_d = pd.Series([v["nars_division"] for v in vrows if v["nars_division"]]).value_counts().to_dict()
    inst_rows, seen_short = [], set()
    for m in man.to_dict("records") + [h for k, h in ex.items() if k not in {(m["institution"], m["division"]) for m in man.to_dict("records")}]:
        h = ex.get((m["institution"], m["division"]), {})
        row = {c: (m.get(c) or h.get(c, "")) for c in ICOLS}
        for c in ICOLS[9:]:
            row[c] = h.get(c, row.get(c, ""))
        short = row["institution_short"] or {"BRAC": "BRAC", "ACI Limited": "ACI Limited", "Supreme Seed Company Ltd.": "Supreme Seed Company"}.get(m["institution"], "")
        row["institution_short"] = short
        seen_short.add(short)
        lab = (row["division_name_en"] + ", " + {"BSMRAU/GAU": "BSMRAU", "RU": "University of Rajshahi"}.get(short, short)) if row["division_name_en"] else ""
        row["n_varieties"] = str(sum(n for d, n in counts_d.items() if d.startswith(lab)) if lab else counts_i.get(short, 0))
        row["role_email"], _ = keep_work_mail(row["role_email"])
        if re.search(r"no department contact|lists no telephone", row["official_public_contact"]):
            row["contact_status"] = "the unit publishes no contact; use the institution row"
        elif row["official_public_contact"] or row["role_email"] or row["office_phone"]:
            row["contact_status"] = "collected from the institution's own site"
        else:
            row["contact_status"] = "no contact published or collected"
        if not row["retrieved_at"]:
            row["retrieved_at"] = TODAY
        inst_rows.append(row)
    cat = R.groupby("developer_std").developer_type.first().to_dict()
    for name, n in sorted(counts_i.items()):
        if name in seen_short or not name or name in ("BRRI", "BINA", "BAU", "BSMRAU/GAU", "RU", "BADC", "BRAC"):
            continue
        inst_rows.append({c: "" for c in ICOLS} | {"institution": name, "division": "", "institution_short": name, "institution_name_en": name,
                          "developer_category": CATEGORY.get(cat.get(name, ""), cat.get(name, "")), "n_varieties": str(n),
                          "contact_status": "not collected (round 3 covered public institutes, universities, BADC and BRAC)",
                          "retrieved_at": TODAY, "notes": "developer of record in the register (developer_std)"})
    with open(FIN / "bgd_institutions.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=ICOLS); w.writeheader(); w.writerows(inst_rows)
    # ---------- working table and evidence
    pd.DataFrame(vrows).to_csv(PW / "variety_nars.csv", index=False, encoding="utf-8-sig")
    with open(W / "evidence_PEOPLE.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ECOLS, extrasaction="ignore"); w.writeheader(); w.writerows(ev)
    # ---------- coverage
    V = pd.DataFrame(vrows)
    nars = V.developer_category.isin(["NARS institute", "public university"])
    print(f"varieties {len(V)}; with nars_institute {(V.nars_institute != '').sum()}; with division {(V.nars_division != '').sum()} "
          f"(stated {(V.nars_division_basis == 'stated').sum()}, inferred {(V.nars_division_basis == 'inferred').sum()}); "
          f"public-sector varieties {nars.sum()}, of which with division {(nars & (V.nars_division != '')).sum()}")
    print(f"proposer as printed {(V.proposer_as_printed != '').sum()}; proposer institute differs from register: {(V.proposer_matches_institute == 'NO').sum()}")
    print(f"varieties with >=1 named breeder/release-paper author {(V.n_named_breeders > 0).sum()}; people rows {len(people)} "
          f"({pd.Series([p['role'] for p in people]).value_counts().to_dict()})")
    I = pd.DataFrame(inst_rows)
    print(f"institution rows {len(I)}; with contact {(I.contact_status.str.startswith('collected')).sum()}; evidence rows {len(ev)}")


REGISTER_COLS = ["nars_institute", "nars_division", "nars_division_basis", "proposer_as_printed"]


def add(df):
    """For make_final.py (same pattern as derive_attributes.add): append the per-variety institute, division, division
    basis (stated / inferred / not stated / not applicable) and the NSB proposer as printed to the register. Pure function:
    never changes an existing column; a blank cell means no source consulted states the value."""
    df = df.copy()
    f = PW / "variety_nars.csv"
    v = pd.read_csv(f, dtype=str, keep_default_na=False).set_index("variety_id") if f.exists() else pd.DataFrame(columns=REGISTER_COLS)
    for c in REGISTER_COLS:
        df[c] = df.variety_id.map(v[c]).fillna("") if c in v else ""
    return df


if __name__ == "__main__":
    main()
