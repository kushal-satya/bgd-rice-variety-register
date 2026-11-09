"""F3H: build the hybrid key crosswalk and the hybrid evidence file.

Inputs (all in 04_working):
  _F3H_moa2026_cells.csv   span-level parse of the MoA 2026 list (phase3_F3H_moa_spans.py)
  _F3H_moa2026_visual.csv  visual transcription of the Nikosh-font rows 162-271 (+ serial 103 developer)
  _F3H_moa2018_cells.csv   same parse of the 2018 edition
  _F3H_moa2016_list.csv    visual transcription of the 1998-2016 edition (scan)
  _F3H_compendium_hybrids.csv  visual transcription of SCA compendium hybrid table (pp.27-33)
  _F3H_sca_hybrid_lists.csv    visual transcription of SCA annual registered-hybrid lists FY2014-15..2025-26
  _F3H_slugs.csv           serial -> key (hand-assigned, see decisions_F3H.md)
  _F3H_other_match.csv     manual matches of other-source rows to keys (optional; overrides automatic)
  nsb_meeting_key.csv + nsb_meeting_key_additions_F3H.csv
Outputs:
  04_working/hybrid_key_crosswalk.csv
  04_working/evidence_F3H.csv
  04_working/_F3H_match_report.csv  (other-source rows and the key they were matched to)
"""
import csv, re, pathlib, collections, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
W = ROOT / "04_working"
sys.path.insert(0, str(ROOT / "scripts"))
from lib_keys import make_key  # noqa: E402

BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
FIELDS = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file",
          "page", "locator", "method", "validation", "confidence", "notes"]

SRC = {
    "MOA_HYB26": ("MoA Seed Wing, 'জাতীয় বীজ বোর্ড (NSB) কর্তৃক ১৯৯৮-০৫/০২/২০২৬ পর্যন্ত অনুমোদিত হাইব্রিড ধানের জাত'",
                  "2_official_list", "02_raw/moa/hybrid_rice_varieties_list_2026-02-05.pdf"),
    "MOA_HYB18": ("MoA Seed Wing, cumulative list of NSB-approved hybrid rice varieties (edition 07.08.2018)",
                  "2_official_list", "02_raw/moa_wayback/hybrid_rice_list_2018-08-07.pdf"),
    "MOA_HYB16": ("MoA Seed Wing, cumulative list of NSB-approved hybrid rice varieties 1998-2016 (file dated 22.12.16; scan)",
                  "2_official_list", "02_raw/moa_wayback/hybrid_rice_list_1998-2016.pdf"),
    "NSB_R5": ("NSB minutes 58th-75th meetings (2005-2011), activities report no.5 (Nov 2011)", "1_primary_legal",
               "02_raw/sca/nsb_minutes_058-075.pdf"),
    "NSB_115": ("NSB minutes, 115th meeting (05-02-2026)", "1_primary_legal", "02_raw/sca/nsb_minutes_115.pdf"),
    "SCA_COMP": ("SCA, 'বাংলাদেশের নোটিফাইড ফসলের অনুমোদিত জাত' (approved varieties of notified crops; imprint 2014, posted 2016)",
                 "2_official_list", "02_raw/sca/approved_varieties_notified_crops_bangladesh_2016.pdf"),
}
for fy in ["2014-15", "2015-16", "2016-17", "2017-18", "2018-19", "2019-20", "2021-22", "2022-23", "2023-24",
           "2024-25", "2025-26"]:
    SRC[f"SCA_HYB_{fy}"] = (f"SCA, list of hybrid rice varieties registered in FY{fy} (হাইব্রিড ধানের জাত নিবন্ধন)",
                            "2_official_list", f"02_raw/sca/registered_hybrid_rice_{fy}.pdf")

PUBLIC = {"BRRI", "BU"}  # developer class with institute keys (make_key)

REGION_WORDS = {
    "ঢাকা": "Dhaka", "ময়মনসিংহ": "Mymensingh", "রাজশাহী": "Rajshahi", "রংপুর": "Rangpur", "কুমিল্লা": "Comilla",
    "যশোর": "Jessore", "চট্টগ্রাম": "Chittagong", "চট্রগ্রাম": "Chittagong", "খুলনা": "Khulna", "বরিশাল": "Barisal",
    "দিনাজপুর": "Dinajpur",
}
ORIGIN = {"ভারত": "India", "চীন": "China", "চায়না": "China", "বাংলাদেশ": "Bangladesh", "ফিলিপাইন": "Philippines",
          "ইরি": "IRRI", "ব্রি": "Bangladesh", "নিজস্ব": "Bangladesh", "উদ্ভাবিত": "Bangladesh",
          "নিজস্ব উদ্ভাবিত": "Bangladesh", "চীন/ বাংলাদেশ": "China/Bangladesh", "India": "India", "China": "China"}


LAT2BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def ordn(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


REGION_SPECIAL = {
    118: "Aman (NSB 82nd): Mymensingh, Chittagong, Rajshahi; Boro (NSB 83rd): Dhaka, Mymensingh, Chittagong, Rajshahi, Jessore",
    164: "Boro (NSB 95th): Chittagong, Khulna, Rangpur; Aus (NSB 102nd): Chittagong, Rangpur, Khulna",
}


def iso(s):
    d, m, y = re.split(r"\s*[./]\s*", s.strip())
    y = int(y)
    y = y + (1900 if y > 50 else 2000) if y < 100 else y
    return f"{y:04d}-{int(m):02d}-{int(d):02d}"


TOK = re.compile(r"(\d{1,2}\s*[./]\s*\d{1,2}\s*[./]\s*\d{2,4})|(\d{2,3})(?=\s*-?\s*(?:তম|তি|সভা|সিো))")


def pairs_of(cell):
    """(meeting, iso_date, raw_date) pairs in printed order; the list prints 'NN তম সভা-DATE' or 'DATE, NNতম সভা'."""
    t = cell.translate(BN).replace(" | ", " ")
    toks = [("D", m.group(1)) if m.group(1) else ("M", int(m.group(2))) for m in TOK.finditer(t)]
    out = []
    for i in range(0, len(toks) - 1, 2):
        a, b = toks[i], toks[i + 1]
        if a[0] == b[0]:
            raise ValueError(cell)
        mt, dt = (a[1], b[1]) if a[0] == "M" else (b[1], a[1])
        out.append((mt, iso(dt), dt))
    return out


def load_key():
    k = collections.defaultdict(set)
    for f in ["nsb_meeting_key.csv", "nsb_meeting_key_additions_F3H.csv"]:
        p = W / f
        if p.exists():
            for r in csv.DictReader(open(p, encoding="utf-8")):
                if r["validation"] in ("two_source", "visual_check"):
                    k[int(r["meeting_no"])].add(r["meeting_date"])
    return k


KEY = load_key()


def region_en(raw):
    s = raw.replace(" | ", " ")
    parts = []
    if re.search(r"সকল\s*অঞ্চল", s):
        parts.append("all regions")
    if re.search(r"সারা\s*দেশ|সারাদেশ|সারদেশ|সারা\s*বাংলাদেশ", s):
        parts.append("nationwide")
    names = []
    for w in re.findall(r"[ঀ-৿]+", s):
        w2 = w[:-1] if w.endswith("ও") and w[:-1] in REGION_WORDS else w
        if w2 in REGION_WORDS and REGION_WORDS[w2] not in names:
            names.append(REGION_WORDS[w2])
    if names:
        parts.append(", ".join(names) + " region(s)")
    q = []
    if "পুনঃ ট্রায়াল" in s:
        q.append("after re-trial")
    if "সুগন্ধি" in s:
        q.append("as an aromatic variety")
    return "; ".join(parts) + (f" ({'; '.join(q)})" if q else "")


def seasons_in(text):
    s = text.replace(" | ", " ")
    out = []
    for bn, en in [("বোরো", "Boro"), ("আমন", "Aman"), ("আউশ", "Aus")]:
        if bn in s:
            out.append(en)
    return out


def latin_parts(name):
    return [m.group(0).strip(" ,;") for m in re.finditer(r"[A-Za-z][A-Za-z0-9 .\-®/]*[A-Za-z0-9]|[A-Za-z]", name)
            if m.group(0).strip()]


def strip_transfer(dev):
    m = re.search(r"হস্তান্তর|হস্তা:", dev)
    if not m:
        return dev.strip(), ""
    return dev[:m.start()].strip(), dev[m.start():].strip()


class Ev:
    def __init__(self):
        self.rows = []

    def add(self, key, field, value, raw, sid, page, locator, method, validation, conf="high", notes=""):
        t, rank, lf = SRC[sid]
        self.rows.append(dict(pilot_key=key, field=field, value=value, value_raw=raw, source_id=sid, source_title=t,
                              authority_rank=rank, local_file=lf, page=page, locator=locator, method=method,
                              validation=validation, confidence=conf, notes=notes))


def j(s):
    return re.sub(r"\s+", " ", s.replace(" | ", " ")).strip()


def moa2026(ev):
    cells = {int(r["serial"]): r for r in csv.DictReader(open(W / "_F3H_moa2026_cells.csv", encoding="utf-8"))}
    vis = {int(r["serial"]): r for r in csv.DictReader(open(W / "_F3H_moa2026_visual.csv", encoding="utf-8"))}
    slugs = {int(r["serial"]): r for r in csv.DictReader(open(W / "_F3H_slugs.csv", encoding="utf-8"))}
    recs = []
    prev_origin = None
    for s in sorted(cells):
        c = cells[s]
        v = vis.get(s)
        nik = s >= 162
        name = j(v["name_bn_as_printed"]) if nik else j(c["name"])
        origin = j(v["origin_as_printed"]) if nik else j(c["origin"])
        dev_full = j(v["developer_as_printed"]) if (v and v["developer_as_printed"]) else j(c["developer"])
        region = j(v["region_as_printed"]) if nik else j(c["region"])
        datecell = c["date"]
        page = c["pages"].split(";")[0]
        crop = v["crop_file"] if nik else f"04_working/crops/F3H/moa26_sutonny/moa26_p{page}_{'a' if s_in_top(c) else 'b'}.png"
        loc = f"MoA 2026 list row {s}; crop {crop}"
        meth = "visual_check" if nik else "bijoy2unicode"
        sl = slugs[s]
        key = sl["key"]
        rec = dict(serial=s, key=key, name=name, origin=origin, dev=dev_full, region=region, datecell=j(datecell),
                   page=page, loc=loc, crop=crop, cls=sl["class"], code=sl["code"], slug_note=sl["notes"])
        recs.append(rec)
        sernote = c["serial_note"]
        # names
        ev.add(key, "official_name_bn", name, name, "MOA_HYB26", page, loc, meth, "visual_check", "high",
               ("serial cell blank in the list; serial 125 inferred from position. " if sernote else "") +
               ("Bangla letters read from the page image (Nikosh text layer garbled)" if nik else "SutonnyMJ text layer converted; checked against page image"))
        lat = latin_parts(name)
        if lat:
            ev.add(key, "official_name_en", "; ".join(lat), "; ".join(lat), "MOA_HYB26", page, loc,
                   "pdf_text", "visual_check", "high", "Latin code/name printed inside the name cell")
        comps = [x.strip(" ,;”“’") for x in re.split(r"[()]", name) if x.strip(" ,;”“’")]
        if len(comps) > 1:
            for comp in comps:
                if re.search(r"[ঀ-৿]", comp):
                    ev.add(key, "aliases", comp, name, "MOA_HYB26", page, loc, meth, "visual_check", "high",
                           "component of the printed name (main name or bracketed trade name/code)")
        # developer
        dev, transfer = strip_transfer(dev_full)
        ev.add(key, "developer", dev, dev_full, "MOA_HYB26", page, loc, meth, "visual_check", "high",
               "column 'উদ্ভাবনকারী/আমদানীকারক' (developer/importer)")
        if transfer:
            ev.add(key, "aliases", f"registration transfer note: {transfer}", transfer, "MOA_HYB26", page, loc, meth,
                   "visual_check", "high", "transfer of the registration to another company (হস্তান্তর) printed in the developer cell")
            to = re.sub(r"^(হস্তান্তর|হস্তা)\s*:\s*", "", transfer)
            ev.add(key, "developer", f"transferee: {to}", transfer, "MOA_HYB26", page, loc, meth, "visual_check",
                   "high", "registration holder after transfer")
        # origin
        o = origin
        oval = None
        if o == "ঐ":
            oval = prev_origin
            onote = "ditto mark 'ঐ' (= same as the row above); resolved to the last explicit value above"
        elif re.search(r"[A-Za-z]", o):
            m = re.search(r"(India|China|চায়না|ভারত)", o)
            oval = {"India": "India", "China": "China", "চায়না": "China", "ভারত": "India"}.get(m.group(1)) if m else None
            onote = "the উৎস column names the foreign breeder/licensor and its country"
            breeder = re.sub(r",?\s*(India|China|চায়না|ভারত)\s*$", "", o).strip(" ,")
            ev.add(key, "developer", f"breeder/licensor: {breeder}", o, "MOA_HYB26", page, loc, "pdf_text",
                   "visual_check", "high", "foreign breeder printed in the উৎস (origin) column")
        else:
            m = re.search(r"(India|China|চায়না|ভারত)", o)
            oval = ORIGIN.get(o) or ({"India": "India", "China": "China", "চায়না": "China", "ভারত": "India"}.get(m.group(1)) if m else None)
            onote = {"নিজস্ব": "printed 'নিজস্ব' (own/in-house); country = registrant's (Bangladesh) by inference",
                     "নিজস্ব উদ্ভাবিত": "printed 'নিজস্ব উদ্ভাবিত' (own development); Bangladesh by inference",
                     "উদ্ভাবিত": "printed 'উদ্ভাবিত' (developed [by BRRI]); Bangladesh by inference",
                     "ব্রি": "printed 'ব্রি' (BRRI) in the origin column",
                     "ইরি": "printed 'ইরি' (IRRI) in the origin column; IRRI is a CGIAR centre, not a country"}.get(o, "")
        if o != "ঐ":
            prev_origin = oval
        if oval:
            conf = "medium" if o in ("নিজস্ব", "নিজস্ব উদ্ভাবিত", "উদ্ভাবিত", "ঐ") else "high"
            ev.add(key, "origin_country", oval, o, "MOA_HYB26", page, loc, "pdf_text" if re.search("[A-Za-z]", o) else meth,
                   "visual_check", conf, onote)
        if o == "ইরি":
            ev.add(key, "cgiar_evidence", "MoA hybrid list gives origin 'ইরি' (IRRI)", o, "MOA_HYB26", page, loc, meth, "visual_check", "high", "")
            ev.add(key, "cgiar_center", "IRRI", o, "MOA_HYB26", page, loc, meth, "visual_check", "high", "")
            ev.add(key, "cgiar_lineage", "MoA list origin IRRI", o, "MOA_HYB26", page, loc, meth, "visual_check", "high", "")
            ev.add(key, "cgiar_role", "1", o, "MOA_HYB26", page, loc, meth, "visual_check", "medium",
                   "origin IRRI read as an IRRI line released directly (cf. pilot: NSB 48th minutes line IR-69690); compendium says origin Bangladesh (conflict kept by P2A)")
        # type / category / body
        ev.add(key, "type", "hybrid", "অনুমোদিত হাইব্রিড ধানের জাত", "MOA_HYB26", page, loc, meth, "visual_check", "high", "list title")
        if rec["cls"] in ("private", "public_importer"):
            ev.add(key, "release_category", "NSB_registration", "অনুমোদিত হাইব্রিড ধানের জাত", "MOA_HYB26", page, loc,
                   meth, "visual_check", "high",
                   "private/importer hybrid in the MoA cumulative list of NSB-approved hybrids (registration route, memo A1)")
        ev.add(key, "approving_body", "NSB", "জাতীয় বীজ বোর্ড (NSB)", "MOA_HYB26", page, loc, meth, "visual_check", "high", "list title")
        # meetings
        prs = pairs_of(datecell)
        rec["pairs"] = prs
        for i, (mt, dt, raw) in enumerate(prs):
            okk = dt in KEY.get(mt, set())
            note = []
            if mt == 56 and dt == "2005-12-30":
                note.append("MoA list typo: 56th meeting was 30-12-2004 (58th minutes); see decisions_P2A")
            if mt == 49 and dt == "2001-09-11":
                note.append("list prints 11.09.01 here but 12/9/01 for the other 49th-meeting entries; key 49 = 2001-09-12")
            if i > 0:
                note.append("extension: later meeting printed in the same cell (region/season added after re-trial)")
            if s == 108 and i == 1:
                note.append("row 108 duplicates row 112 (both Bayer hybrid-4 Arize Dhani Gold); 2018 edition row 108 gives the 80th meeting 26/08/13 instead")
            meth_d = "visual_check" if nik else "bijoy2unicode"
            val = "key_check" if okk else "unvalidated"
            ev.add(key, "approval_date", dt, raw.translate(LAT2BN), "MOA_HYB26", page, loc + "; column 'অনুমোদনের তারিখ ও সভা'", meth_d, val,
                   "high" if okk else "medium", "; ".join(note) + (f"; NSB {mt} = {dt} in meeting key" if okk else f"; NOT in validated meeting key (key has {sorted(KEY.get(mt, []))})"))
            ev.add(key, "approval_reference", f"NSB {ordn(mt)} meeting ({dt})", j(datecell), "MOA_HYB26", page, loc, meth_d, val,
                   "high" if okk else "medium", "; ".join(note))
        # region and season
        if region:
            ev.add(key, "region_scope", REGION_SPECIAL.get(s, region_en(region)), region, "MOA_HYB26", page, loc, meth, "visual_check", "high",
                   "column 'অনুমোদিত অঞ্চল'" + ("; region added by the later meeting printed in the same row" if len(prs) > 1 and s in (10, 118) else ""))
        else:
            ev.add(key, "region_scope", "", "", "MOA_HYB26", page, loc, meth, "visual_check", "high", "region cell blank on the page")
        ss = seasons_in(region + " " + name)
        if ss:
            ev.add(key, "season", "; ".join(ss), region if seasons_in(region) else name, "MOA_HYB26", page, loc, meth,
                   "visual_check", "high", "season word printed in the region or name cell")
        rec["seasons_cell"] = ss
    return recs


def s_in_top(c):
    b = c["bands"].split(";")[0]
    y = float(b.split(":")[1].split("-")[0])
    return y < 420


def season_summary(ev, recs):
    """MoA 2026 p.12 'মৌসুম ভিত্তিক' summary (read from crops moa26_p12_summary_a/b.png)."""
    lists = {
        "Aman only (শুধুমাত্র আমন মৌসুম (৩২টি))": [125, 144, 145, 74, 161, None, 146, 117, 86, 99, 100, 116, 147, 191, 246,
                                                193, 194, 195, 196, 197, 198, 199, 200, 201, 221, 225, 226, 227, 228, 252, 253, 254],
        "Aus only (শুধুমাত্র আউশ মৌসুম (৮টি))": [173, 187, 188, 189, 190, 222, 223, 224],
        "Boro and Aman (বোরো ও আমন উভয় মৌসুম (৩টি))": [127, 108, 118],
        "Boro and Aus (বোরো ও আউশ উভয় মৌসুম (১টি))": [164],
    }
    raw_names = {
        "Aman only (শুধুমাত্র আমন মৌসুম (৩২টি))": "বিএডিসি হাইব্রিড ধান-২ (Win-207), বিএডিসি হাইব্রিড ধান-৬ (MJ0032), বিইউ সুগন্ধি হাইব্রিড ধান-১, ব্রি হাইব্রিড ধান-৪, ব্রি হাইব্রিড ধান-৬, বায়ার হাইব্রিড ধান-২, বায়ার হাইব্রিড ধান-৬, ব্র্যাক হাইব্রিড ধান-১০, ব্র্যাক হাইব্রিড ধান-মুক্তি-১, সিনজেনটা-সুবর্ণা-৮, পেট্টোকেম এগ্রো ধান-১২, পেট্টোকেম এগ্রো ধান-১৬ ও সুপ্রিম হাইব্রিড ধান-১৬, উইন অল হাইটেক হাইব্রিড ধান৯, ব্র্যাক হাইব্রিড ধান১৯, সুপ্রীম হাইব্রিড হীরা২৫, মাহিকো হাইব্রিড ধান৪, নর্থ সাউথ হাইব্রিড ধান৫, লাল তীর হাইব্রিড ধান১, এ সি আই হাইব্রিড ধান১১, লাল তীর হাইব্রিড ধান২ (টিয়া), ব্র্যাক হাইব্রিড ধান১৮, বায়ার হাইব্রিড ধান-৮, তিনপাতা সুপার হাইব্রিড ধান৫, তিনপাতা হাইব্রিড ধান৪, ব্র্যাক হাইব্রিড ধান২০, এসিআই হাইব্রিড ধান১৬, মাহিকো হাইব্রিড ধান৮, সুপ্রীম হাইব্রিড ধান১৪, ভিএনআর হাইব্রিড ধান৩, ভিএনআর হাইব্রিড ধান৪, মিতালী এগ্রো হাইব্রিড ধান৭",
    }
    names_aman = [x.strip() for x in re.split(r",\s*| ও ", raw_names["Aman only (শুধুমাত্র আমন মৌসুম (৩২টি))"])]
    bys = {r["serial"]: r for r in recs}
    named = set()
    loc0 = "MoA 2026 list p.12 seasonal summary 'মৌসুম ভিত্তিক'; crops 04_working/crops/F3H/moa26_p12_summary_a.png, _b.png"
    for lab, sers in lists.items():
        season = {"Aman only": "Aman", "Aus only": "Aus", "Boro and Aman": "Boro; Aman", "Boro and Aus": "Boro; Aus"}[lab.split(" (")[0]]
        for i, s in enumerate(sers):
            if s is None:
                ev.add("UNMATCHED", "season", season, names_aman[i], "MOA_HYB26", 12, loc0, "visual_check", "visual_check",
                       "high", "name in the seasonal summary with no matching row in the MoA 2026 table")
                continue
            named.add(s)
            r = bys[s]
            raw = names_aman[i] if lab.startswith("Aman only") else ""
            note = f"named in the summary list '{lab}'"
            if s == 144:
                note += "; summary prints code MJ0032 while row 144 prints MJ0031 (row 127 BADC hybrid dhan-4 is also MJ0031)"
            if s == 99:
                note += "; summary calls it 'সিনজেনটা-সুবর্ণা-৮' while row 99 is 'সুবর্ণ-৮ (২০০৭)' of Supreme Seed: match by name only, medium confidence"
            if s == 86:
                note += "; summary 'ব্র্যাক হাইব্রিড ধান-মুক্তি-১' matched to row 86 'মুক্তি-১ (HB 12)' (BRAC)"
            if s in (100, 116):
                note += "; summary 'পেট্টোকেম এগ্রো ধান-NN' matched by number to the Petrochem row"
            if s == 147:
                note += "; summary name 'সুপ্রিম হাইব্রিড ধান-১৬' matched to row 147 (printed 'সুপ্রিম হাইব্রিড ধান-১১ (হীরা-১৯)') via SCA FY2015-16 row 21 (Supreme hybrid dhan-16, 89th, Aman, Rajshahi & Khulna)"
            if s == 246:
                note += "; CONFLICT: row 246 region cell says 'বোরো মৌসুমে' (Boro); the summary lists ব্র্যাক হাইব্রিড ধান১৯ as Aman-only"
            if s == 125:
                note += "; summary gives code Win-207 (row prints win-207)"
            ev.add(r["key"], "season", season, raw or lab, "MOA_HYB26", 12, loc0, "visual_check", "visual_check",
                   "medium" if s in (99, 86, 100, 116, 147) else "high", note)
    for r in recs:
        if r["serial"] not in named:
            ev.add(r["key"], "season", "Boro", "শুধুমাত্র বোরো মৌসুম (২২৭টি) : ২২৭টি হাইব্রিড ধানের জাত বোরো মৌসুমের জন্য জাতীয় বীজ বোর্ড কর্তৃক অনুমোদিত।",
                   "MOA_HYB26", 12, loc0, "visual_check", "visual_check", "medium",
                   "by exclusion: not named in the Aman-only, Aus-only or two-season lists; the summary says the remaining 227 are Boro-only"
                   + ("; row 112 duplicates row 108, which the summary lists under Boro and Aman" if r["serial"] == 112 else "")
                   + ("; row 160 prints the same name as row 147" if r["serial"] == 160 else ""))
    return named


if __name__ == "__main__":
    ev = Ev()
    recs = moa2026(ev)
    season_summary(ev, recs)
    import phase3_F3H_other as other  # noqa: E402
    extra = other.run(ev, recs)
    # crosswalk
    cw = []
    seen = collections.defaultdict(list)
    for r in recs:
        seen[r["key"]].append(r["serial"])
    for r in recs:
        al = sorted({x["value"] for x in ev.rows if x["pilot_key"] == r["key"] and x["field"] == "aliases"})
        notes = [r["slug_note"]] if r["slug_note"] else []
        if len(seen[r["key"]]) > 1:
            notes.append("same variety listed more than once in MoA 2026: serials " + ";".join(map(str, seen[r["key"]])))
        cw.append(dict(key=r["key"], moa2026_serial=r["serial"], name_bn_as_printed=r["name"],
                       name_latin_as_printed="; ".join(latin_parts(r["name"])), code=r["code"], company=r["dev"],
                       aliases_seen=" | ".join(al), notes=" ".join(notes)))
    for x in extra:
        x["aliases_seen"] = " | ".join(sorted({e["value"] for e in ev.rows if e["pilot_key"] == x["key"] and e["field"] in ("aliases", "official_name_bn")} - {x["name_bn_as_printed"]}))
        if not x["company"]:
            x["company"] = next((e["value"] for e in ev.rows if e["pilot_key"] == x["key"] and e["field"] == "developer"), "")
    cw += extra
    with open(W / "hybrid_key_crosswalk.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["key", "moa2026_serial", "name_bn_as_printed", "name_latin_as_printed", "code",
                                           "company", "aliases_seen", "notes"])
        w.writeheader()
        w.writerows(cw)
    with open(W / "evidence_F3H.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(ev.rows)
    c = collections.Counter(r["validation"] for r in ev.rows)
    print("rows", len(ev.rows), "keys", len({r["pilot_key"] for r in ev.rows}), dict(c), "crosswalk", len(cw))
