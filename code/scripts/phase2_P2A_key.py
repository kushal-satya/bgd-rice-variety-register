"""P2A: build 04_working/nsb_meeting_key.csv (NSB meeting number -> date) from
(1) bijoy2unicode text of the NSB activities report no.5 (meetings 58-75, text layer),
(2) MoA cumulative hybrid list 2026 and 2018 editions (text layer; meeting/date pairs),
(3) OCR of NSB minutes (single files 83-115 and the early bundles),
(4) Wayback file titles, (5) manual rows (04_working/_P2A_key_manual.csv: gazettes, SCA lists, crops read by eye).
OCR rows are 'two_source' when they equal a text-layer row, 'visual_check' when listed in
04_working/_P2A_key_visual.csv (crop opened and read), else 'unvalidated'.
Columns: meeting_no, meeting_date, source_file, page, method, validation, notes, kind."""
import csv, re, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parents[1]
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
MON = {"জানুয়ারি": 1, "জানুয়ারী": 1, "ফেব্রুয়ারি": 2, "ফেব্রুয়ারী": 2, "মার্চ": 3, "এপ্রিল": 4, "মে": 5, "জুন": 6,
       "জুলাই": 7, "আগস্ট": 8, "আগষ্ট": 8, "সেপ্টেম্বর": 9, "অক্টোবর": 10, "নভেম্বর": 11, "ডিসেম্বর": 12}


def iso(d, m, y):
    y = int(y)
    if y < 100:
        y += 1900 if y > 50 else 2000
    d, m = int(d), int(m)
    if not (1 <= m <= 12 and 1 <= d <= 31) or not (1970 <= y <= 2026):
        return None
    return f"{y:04d}-{m:02d}-{d:02d}"


NUMD = r"(\d{1,2})\s*[-./]\s*(\d{1,2})\s*[-./]\s*(\d{2,4})"
WORDD = r"(\d{1,2})\s*(" + "|".join(MON) + r")[,\s]*(\d{4})"
rows = []


def add(m, d, src, page, method, validation, notes, kind):
    if d is None:
        return
    rows.append(dict(meeting_no=int(m), meeting_date=d, source_file=src, page=page, method=method,
                     validation=validation, notes=notes, kind=kind))


# (1) NSB activities report no.5 (minutes 58-75), text layer
t = (ROOT / "03_extracted/text/P2A/nsb_058-075_unicode.txt").read_text(encoding="utf-8").splitlines()
HDR = re.compile(r"^\s*জাতী\S*\s+(?:\S+\s+)?বো\S*\s*([০-৯]+)\s*তম.{0,15}সভার\s*কা\S*বরণী\s*$")
page = 0
for i, l in enumerate(t):
    mm = re.match(r"=== page (\d+)", l)
    if mm:
        page = int(mm.group(1)); continue
    h = HDR.match(l)
    if h and i > 400:
        mtg = int(h.group(1).translate(BN))
        nxt = (t[i + 1] + " " + t[i + 2]).translate(BN)
        dm = re.search(NUMD, nxt)
        if dm:
            add(mtg, iso(*dm.groups()), "02_raw/sca/nsb_minutes_058-075.pdf", page, "bijoy2unicode", "",
                "opening sentence of the minutes ('গত DATE খ্রিঃ তারিখ ... সভা ... অনুষ্ঠিত হয়'); NSB activities report no.5 (Nov 2011), SutonnyMJ text layer", "minutes_text")
        else:
            dw = re.search(r"(\d{1,2})\S*\s+(" + "|".join(MON) + r"),?\s*(\d{4})", nxt)
            if dw:
                add(mtg, iso(dw.group(1), MON[dw.group(2)], dw.group(3)), "02_raw/sca/nsb_minutes_058-075.pdf", page,
                    "bijoy2unicode", "", "opening sentence, date written in words; report no.5 text layer", "minutes_text")

# (1b) report no.5: agenda item 1 of each minutes confirms the previous meeting(s) ('বিগত DATE ... NNতম সভার')
page = 0
for i, l in enumerate(t):
    mm = re.match(r"=== page (\d+)", l)
    if mm:
        page = int(mm.group(1)); continue
    if i < 400:
        continue
    L = (l + " " + (t[i + 1] if i + 1 < len(t) else "")).translate(BN)
    m1 = re.search(r"বিগত\s*" + NUMD + r"\s*(?:খ্রিঃ)?\s*(?:তারিখে|তারিখ)\s*অনুষ্ঠিত\s*(?:বীজ বো\S*|জাতীয়\s*বীজ\s*বো\S*)\s*(\d{2})\s*তম", L)
    if m1 and l.translate(BN).find(m1.group(0)[:12]) >= 0:
        add(m1.group(4), iso(*m1.groups()[:3]), "02_raw/sca/nsb_minutes_058-075.pdf", page, "bijoy2unicode", "",
            "agenda item 1 of the next meeting's minutes confirms this meeting's date; report no.5 text layer", "minutes_text_prev")
    m2 = re.search(r"বিগত\s*" + NUMD + r"\s*এবং\s*" + NUMD + r"\s*তারিখে\s*অনুষ্ঠিত[^।]{0,40}?(\d{2})\s*তম\s*ও\s*(\d{2})\s*তম", L)
    if m2:
        g = m2.groups()
        add(g[6], iso(*g[0:3]), "02_raw/sca/nsb_minutes_058-075.pdf", page, "bijoy2unicode", "", "agenda item of a later meeting confirms this date (two meetings named); report no.5 text layer", "minutes_text_prev")
        add(g[7], iso(*g[3:6]), "02_raw/sca/nsb_minutes_058-075.pdf", page, "bijoy2unicode", "", "agenda item of a later meeting confirms this date (two meetings named); report no.5 text layer", "minutes_text_prev")

# (2) MoA hybrid list pairs
for ed, f in (("2026", "02_raw/moa/hybrid_rice_varieties_list_2026-02-05.pdf"),
              ("2018", "02_raw/moa_wayback/hybrid_rice_list_2018-08-07.pdf")):
    seen = collections.Counter(); pages = {}
    for r in csv.DictReader(open(ROOT / f"04_working/_P2A_moa_hybrid_entries_{ed}.csv", encoding="utf-8")):
        for p in filter(None, r["pairs"].split(";")):
            m, d = p.split("=")
            seen[(int(m), d)] += 1; pages.setdefault((int(m), d), r["page"])
    for (m, d), n in sorted(seen.items()):
        add(m, d, f, pages[(m, d)], "bijoy2unicode", "",
            f"MoA cumulative hybrid list ({ed} edition), column 'অনুমোদনের তারিখ ও সভা'; pair in {n} entries", "list_pair")

# (3) OCR minutes
OCR = ROOT / "03_extracted/text/ocr"
CONF = re.compile(r"8(?=[০-৯]|\s?তম)|(?<=[০-৯])8|¢(?=[০-৯]|\s?তম)|(?<=[০-৯])¢")


def repaired(raw):
    """OCR trap: Bangla ৪ read as Latin 8 and ৫ as ¢ inside Bangla numbers. Repair 1:1 (same length) and
    return (text_with_latin_digits, set_of_repaired_offsets)."""
    fixed = CONF.sub(lambda m: "৪" if m.group(0) == "8" else "৫", raw)
    offs = {i for i, (a, b) in enumerate(zip(raw, fixed)) if a != b}
    return fixed.translate(BN), offs


def flag(mm, offs, notes):
    if any(mm.start() <= o < mm.end() for o in offs):
        return notes + "; OCR confusable repaired in this span (Latin 8->৪ / ¢->৫)"
    return notes


def ocr_text(stem, p):
    f = OCR / stem / f"p{p:03d}_psm6.txt"
    return f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""


for n in range(83, 116):
    stem = f"nsb_minutes_{n:03d}"
    for p in (1, 2):
        tx, offs = repaired(ocr_text(stem, p))
        for mm in re.finditer(r"সভার তারিখ\s*\S?\s*:?\s*" + WORDD, tx):
            add(n, iso(mm.group(1), MON[mm.group(2)], mm.group(3)), f"02_raw/sca/{stem}.pdf", p, "ocr", "",
                flag(mm, offs, "minutes heading 'সভার তারিখ'"), "minutes_ocr")
        for mm in re.finditer(r"সভার তারিখ\s*\S?\s*:?\s*" + NUMD, tx):
            add(n, iso(*mm.groups()), f"02_raw/sca/{stem}.pdf", p, "ocr", "", flag(mm, offs, "minutes heading 'সভার তারিখ'"), "minutes_ocr")
        for mm in re.finditer(r"গত\s*" + NUMD + r"[^।]{0,200}?(\d{2,3})\s*-?\s*তম\s*সভা", tx):
            if int(mm.group(4)) == n:
                add(n, iso(*mm.groups()[:3]), f"02_raw/sca/{stem}.pdf", p, "ocr", "",
                    flag(mm, offs, "cover letter or opening: 'গত DATE তারিখে ... অনুষ্ঠিত ... NNতম সভা'"), "minutes_ocr")
        for mm in re.finditer(NUMD + r"\s*তারিখে[^।]{0,40}?অনুষ্ঠিত[^।]{0,80}?(\d{2,3})\s*-?\s*তম", tx):
            if int(mm.group(4)) == n:
                add(n, iso(*mm.groups()[:3]), f"02_raw/sca/{stem}.pdf", p, "ocr", "",
                    flag(mm, offs, "cover letter: 'DATE তারিখে অনুষ্ঠিত ... NNতম সভার কার্যবিবরণী'"), "minutes_ocr")
        for mm in re.finditer(r"(\d{2,3})\s*-?\s*তম\s*সভা\s*(?:বিগত\s*)?" + NUMD, tx):
            if int(mm.group(1)) == n - 1:
                add(n - 1, iso(*mm.groups()[1:4]), f"02_raw/sca/{stem}.pdf", p, "ocr", "",
                    flag(mm, offs, f"agenda item 1 of NSB {n} states the previous meeting's date"), "minutes_ocr_prev")
        for mm in re.finditer(r"(\d{2,3})\s*-?\s*তম\s*সভা\s*(?:বিগত\s*)?" + WORDD, tx):
            if int(mm.group(1)) == n - 1:
                add(n - 1, iso(mm.group(2), MON[mm.group(3)], mm.group(4)), f"02_raw/sca/{stem}.pdf", p, "ocr", "",
                    flag(mm, offs, f"agenda item 1 of NSB {n} states the previous meeting's date"), "minutes_ocr_prev")
        for mm in re.finditer(r"বিগত\s*" + NUMD + r"[^।]{0,80}?(\d{2,3})\s*-?\s*তম\s*সভার", tx):
            if int(mm.group(4)) == n - 1:
                add(n - 1, iso(*mm.groups()[:3]), f"02_raw/sca/{stem}.pdf", p, "ocr", "",
                    flag(mm, offs, f"agenda item 1 of NSB {n} states the previous meeting's date"), "minutes_ocr_prev")
for stem in ("nsb_minutes_001-018", "nsb_minutes_019-028", "nsb_minutes_029-042", "nsb_minutes_043-057", "nsb_minutes_076-082"):
    d = OCR / stem
    if not d.exists():
        continue
    for f in sorted(d.glob("p*_psm6.txt")):
        p = int(f.name[1:4]); tx, offs = repaired(f.read_text(encoding="utf-8", errors="replace"))
        for mm in re.finditer(NUMD + r"\s*(?:ইং|খ্রিঃ|খ্রি:|খ্রি)?\s*তারিখ[^।]{0,90}?বোর্ডের\s*(\d{1,3})\s*-?\s*তম\s*(?:\(বিশেষ\)\s*)?সভা", tx):
            add(int(mm.group(4)), iso(*mm.groups()[:3]), f"02_raw/sca/{stem}.pdf", p, "ocr", "",
                flag(mm, offs, "opening sentence or agenda item in bundle ('DATE তারিখ ... বোর্ডের NNতম সভা')"), "minutes_ocr")
        for mm in re.finditer(r"বোর্ডের\s*(\d{1,3})\s*-?\s*তম\s*(?:\(বিশেষ\)\s*)?সভা\s*(?:বিগত\s*)?" + NUMD, tx):
            add(int(mm.group(1)), iso(*mm.groups()[1:4]), f"02_raw/sca/{stem}.pdf", p, "ocr", "",
                flag(mm, offs, "opening sentence in bundle ('বোর্ডের NNতম সভা DATE')"), "minutes_ocr")

# (4) Wayback titles
for r in csv.DictReader(open(ROOT / "01_discovery/_parts/RR_wayback_variety_files.csv", encoding="utf-8-sig")):
    if r["category"] != "nsb_minutes_or_reports":
        continue
    fn = r["filename"]
    m2 = re.match(r"NSB\s*(\d{1,3})\s*[-_]\s*(\d{1,3})\s*\(" + NUMD + r"\s*-\s*" + NUMD + r"\)", fn)
    m = re.match(r"(?:NSB\s*|NSB Minutes-?\s*|\d+\.\s*NSB Minutes-?)?(\d{2,3})\s*(?:th|nd|rd|st)?\s*(?:NSB)?\s*[,(]\s*" + NUMD, fn)
    m3 = re.search(r"NSB Minutes-?\s*(\d{3})\s*\(" + NUMD, fn)
    loc = f"Wayback file title '{fn}' (first capture {r['first_capture'][:8]})"
    if m2:
        add(m2.group(1), iso(*m2.groups()[2:5]), "01_discovery/_parts/RR_wayback_variety_files.csv", "", "html", "", loc + ": first meeting of bundle", "title")
        add(m2.group(2), iso(*m2.groups()[5:8]), "01_discovery/_parts/RR_wayback_variety_files.csv", "", "html", "", loc + ": last meeting of bundle", "title")
    elif m3:
        add(m3.group(1), iso(*m3.groups()[1:4]), "01_discovery/_parts/RR_wayback_variety_files.csv", "", "html", "", loc, "title")
    elif m:
        add(m.group(1), iso(*m.groups()[1:4]), "01_discovery/_parts/RR_wayback_variety_files.csv", "", "html", "", loc, "title")

# (5) manual rows
EXTRA = ROOT / "04_working/_P2A_key_manual.csv"
if EXTRA.exists():
    for r in csv.DictReader(open(EXTRA, encoding="utf-8")):
        add(r["meeting_no"], r["meeting_date"], r["source_file"], r["page"], r["method"], r["validation"], r["notes"], r["kind"])

# validation
txt = collections.defaultdict(set)
for r in rows:
    if r["method"] == "bijoy2unicode" or r["validation"] in ("visual_check",):
        txt[r["meeting_no"]].add(r["meeting_date"])
VISUAL = set()
VF = ROOT / "04_working/_P2A_key_visual.csv"
if VF.exists():
    VISUAL = {(int(r["meeting_no"]), r["meeting_date"], r["source_file"], str(r["page"])) for r in csv.DictReader(open(VF, encoding="utf-8"))}
for r in rows:
    if r["validation"]:
        continue
    m, d = r["meeting_no"], r["meeting_date"]
    if r["method"] == "ocr":
        if (m, d, r["source_file"], str(r["page"])) in VISUAL:
            r["validation"] = "visual_check"
        elif d in txt[m]:
            r["validation"] = "two_source"; r["notes"] += "; equals a text-layer source (MoA hybrid list / NSB report no.5) or a visually checked row"
        else:
            r["validation"] = "unvalidated"
    elif r["method"] == "bijoy2unicode":
        others = sorted({x["source_file"].split("/")[-1] for x in rows if x["meeting_no"] == m and x["meeting_date"] == d
                         and x["source_file"] != r["source_file"] and x["kind"] != "title" and x["source_file"].split("/")[-1][:12] != r["source_file"].split("/")[-1][:12]})
        if not others and r["kind"] in ("minutes_text", "minutes_text_prev"):
            same = {x["kind"] for x in rows if x["meeting_no"] == m and x["meeting_date"] == d and x["source_file"] == r["source_file"]}
            if {"minutes_text", "minutes_text_prev"} <= same:
                others = ["own minutes + next meeting's confirmation (same report, text layer)"]
        r["validation"] = "two_source" if others else "unvalidated"
        if others:
            r["notes"] += "; agrees with " + ", ".join(others)[:200]
    else:
        alld = {x["meeting_date"] for x in rows if x["meeting_no"] == m and x["kind"] != "title"}
        r["validation"] = "unvalidated"
        r["notes"] += "; title date " + ("EQUALS" if d in alld else "DIFFERS FROM") + " the meeting date found in minutes/lists"
seen = set(); out = []
for r in sorted(rows, key=lambda r: (r["meeting_no"], r["meeting_date"], r["source_file"], str(r["page"]))):
    k = (r["meeting_no"], r["meeting_date"], r["source_file"], str(r["page"]), r["kind"])
    if k in seen:
        continue
    seen.add(k); out.append(r)
with open(ROOT / "04_working/nsb_meeting_key.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["meeting_no", "meeting_date", "source_file", "page", "method", "validation", "notes", "kind"])
    w.writeheader(); w.writerows(out)
best = collections.defaultdict(collections.Counter)
for r in out:
    if r["kind"] == "title":
        continue
    best[r["meeting_no"]][(r["meeting_date"], r["validation"][:3])] += 1
print(len(out), "rows;", len(best), "meetings")
for m in sorted(best):
    print(m, dict(best[m]))
