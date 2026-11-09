"""F5M step 1: locate every F3M decision in the F5M page texts and cut out its full agenda item.
Inputs : 04_working/F3M_decisions_index.csv, 04_working/_F3M_decisions_manual.tsv (find regex),
         03_extracted/text/F5M/<stem>.txt (+ .lines.json), raw OCR in 03_extracted/text/ocr/<stem>/
Output : 04_working/_F5M_items.json  {dec_id: {...item boundaries, anchor, passage...}}
         03_extracted/text/F5M/review/<stem>.md  (human review dump)"""
import csv, json, re, sys, pathlib, unicodedata, difflib
sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parents[1]
W = ROOT / "04_working"; T = ROOT / "03_extracted/text/F5M"
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
SRC = {"B1": "nsb_minutes_001-018", "B2": "nsb_minutes_019-028", "B3": "nsb_minutes_029-042", "B4": "nsb_minutes_043-057",
       "B5": "nsb_minutes_058-075", "B6": "nsb_minutes_076-082"}


def stem_of(src):
    return SRC.get(src) or f"nsb_minutes_{int(src[1:]):03d}"


def norm(s):
    s = unicodedata.normalize("NFC", s or "")
    return s.replace("য়", "য়").replace("ড়", "ড়").replace("ঢ়", "ঢ়")


_P = {}


def pages(stem):
    """-> list of (page, line_text, meta) in order"""
    if stem in _P:
        return _P[stem]
    f = T / f"{stem}.txt"
    lines = f.read_text(encoding="utf-8").splitlines()
    mf = T / f"{stem}.lines.json"
    meta = json.loads(mf.read_text()) if mf.exists() else [None] * len(lines)
    out, pg = [], 0
    for i, u in enumerate(lines):
        m = re.match(r"=== page (\d+)$", u)
        if m:
            pg = int(m.group(1)); continue
        out.append((pg, norm(u), meta[i] if i < len(meta) else None))
    _P[stem] = out
    return out


AG = r"(?:আলোচ্য|আলোচ্য|আলোচন্য|আলোচ্|আলোচা|আলোচ্যা)\s*(?:সূ?ু?চী|সূ?ু?চি|সুচী|বিষয়|বিষয়)"
AGENDA = re.compile(r"^\W{0,4}" + AG + r"\s*[-–:ঃ]?\s*\(?\s*([০-৯0-9]{1,2}|[ক-ঞ]|বিবিধ)")
SECTION = re.compile(r"^\W{0,3}([০-৯0-9]{1,2}\s*[.৷:]\s*[০-৯0-9]{1,2})\s+\S")
MEET = re.compile(r"(?:জাতীয়|জাতীয়)\s*বীজ\s*(?:বোর্ড|বোর্ডে|বোড)\S*\s*(?:\(এনএসবি\)\s*)?(?:এর\s*)?[০-৯0-9]{1,3}\s*-?\s*তম\s*(?:\(বিশেষ\)\s*)?সভার\s*কার্যবিবরণী")


def is_head(src, u, nxt=""):
    if AGENDA.search(u[:40]):
        return "agenda"
    if MEET.search(u) and len(u) < 90 and not re.search(r"নিশ্চিত|অনুষ্ঠিত|পাঠানো", u + " " + nxt):
        return "meeting"
    if src in ("B1", "B2", "B3", "B4") and SECTION.match(u):
        return "section"
    if src in ("B2", "B3") and re.match(r"^\W{0,2}[০-৯]{1,2}\s*[।|]\s+\S", u) and len(u) < 200 and not re.search(r"জনাব|সদস্য$|আহ্বায়ক|আহবায়ক", u):
        return "numbered"
    if src in ("B2", "B3") and re.match(r"^\W{0,2}[\(\[]?[ক-ঞ][\)\]]\s*\S", u) and len(u) < 160:
        return "letter"
    return None


def locate(stem, page, rx, alt=()):
    P = pages(stem)
    idx = {}
    for i, (pg, u, m) in enumerate(P):
        idx.setdefault(pg, []).append(i)
    order = [page] + [p for k in range(1, 9) for p in (page + k, page - k)]
    rxs = []
    if rx:
        try:
            rxs.append(re.compile(norm(rx)))
        except re.error:
            rxs.append(re.compile(re.escape(norm(rx))))
    for a in alt:
        if a:
            rxs.append(re.compile(re.escape(norm(a)), re.I))
    for r in rxs:
        for p in order:
            ids = idx.get(p, [])
            for j, i in enumerate(ids):
                u = P[i][1]
                if r.search(u):
                    return i, "regex" if r is rxs[0] and rx else "alt"
                if j + 1 < len(ids) and r.search(u + " " + P[ids[j + 1]][1]) and not r.search(P[ids[j + 1]][1]):
                    return i, "regex2" if r is rxs[0] and rx else "alt2"
    return None, "not_found"


def item_bounds(src, stem, i):
    """item = from the nearest heading at/above the anchor (max 3 pages back; else start of the anchor's page)
    to the line before the next heading (max 4 pages forward)."""
    P = pages(stem)
    s = i
    kind = None
    while s >= 0:
        if P[i][0] - P[s][0] > 3:
            s = next(j for j in range(i, -1, -1) if P[j][0] != P[i][0]) + 1
            kind = "page_start"; break
        kind = is_head(src, P[s][1], P[s + 1][1] if s + 1 < len(P) else "")
        if kind:
            break
        s -= 1
    s = max(s, 0)
    LV = {"meeting": 0, "agenda": 1, "section": 1, "numbered": 1, "page_start": 1, "letter": 2, None: 1}
    e = i + 1
    while e < len(P):
        if P[e][0] - P[i][0] > 4:
            break
        k = is_head(src, P[e][1], P[e + 1][1] if e + 1 < len(P) else "")
        if k and LV[k] <= LV[kind]:
            break
        e += 1
    return s, e, kind


ENUM = re.compile(r"^\W{0,3}(\(?[০-৯0-9]{1,2}\)|[০-৯0-9]{1,2}\s*[।|.]\s|\(?[ক-ঞ]\)\s|\[কলাম|সিদ্ধান্ত\s*[:ঃ]|আলোচনা\s*[:ঃ]|সুপারিশ\s*[:ঃ]|শর্ত)")


def paragraphs(lines):
    """split (idx, text) list into paragraphs at blank lines and enumerators"""
    paras, cur = [], []
    for i, u in lines:
        if not u.strip():
            if cur:
                paras.append(cur); cur = []
            continue
        if cur and ENUM.match(u):
            paras.append(cur); cur = []
        cur.append((i, u))
    if cur:
        paras.append(cur)
    return paras


def main():
    IX = list(csv.DictReader(open(W / "F3M_decisions_index.csv", encoding="utf-8")))
    MAN = {}
    with open(W / "_F3M_decisions_manual.tsv", encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for l in f:
            v = l.rstrip("\n").split("\t"); v += [""] * (len(hdr) - len(v))
            MAN[v[0].strip()] = dict(zip(hdr, [x.strip() for x in v]))
    res = {}
    for d in IX:
        m = MAN.get(d["dec_id"], {})
        src = m.get("src") or ""
        stem = pathlib.Path(d["local_file"]).stem
        if not src:
            src = {v: k for k, v in SRC.items()}.get(stem, "S" + stem[-3:])
        alt = []
        for f in ("breeding_line_raw", "variety_raw"):
            v = d.get(f, "")
            for part in re.split(r"[();/,]|\s-\s", v):
                part = part.strip()
                if len(part) >= 4 and re.search(r"[A-Za-z0-9০-৯]", part) and not re.search(r"proposed|hybrid|varieties|names", part):
                    alt.append(part)
        page = int(d["page"] or m.get("page") or 1)
        i, how = locate(stem, page, m.get("find", ""), alt)
        if i is None:
            res[d["dec_id"]] = {"stem": stem, "src": src, "found": how, "page": page}
            continue
        s, e, kind = item_bounds(src, stem, i)
        P = pages(stem)
        res[d["dec_id"]] = {"stem": stem, "src": src, "found": how, "anchor": i, "anchor_page": P[i][0],
                            "start": s, "end": e, "head_kind": kind, "p0": P[s][0], "p1": P[e - 1][0],
                            "heading": P[s][1]}
    json.dump(res, open(W / "_F5M_items.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    from collections import Counter
    print(Counter(v["found"] for v in res.values()))
    print(Counter(v.get("head_kind") for v in res.values()))
    for k, v in res.items():
        if v["found"] == "not_found":
            print("NOT FOUND", k, v)


if __name__ == "__main__":
    main()
