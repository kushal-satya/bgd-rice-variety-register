"""F5L task 1 + 3: every printed cell of every official rice list, long and wide, plus evidence rows.

Inputs (all transcriptions are cell-level, verbatim Unicode Bangla):
  SCA 2016 compendium inbred tables  04_working/F5L/comp_inbred_p*.tsv        (F5L helpers, visual)
  SCA 2016 compendium hybrid table   04_working/_F3H_compendium_hybrids.csv    (F3H helper, visual)
  SCA FY inbred lists                04_working/F5L/fy_inbred_verbatim*.tsv    (F5L helpers, visual)
  SCA FY registered-hybrid lists     04_working/_F3H_sca_hybrid_lists.csv      (F3H helper, visual)
  MoA hybrid list 2026               04_working/_F3H_moa2026_cells.csv (SutonnyMJ rows, text layer checked by eye
                                     against 14 crops by F3H) + _F3H_moa2026_visual.csv (Nikosh rows, visual)
  MoA hybrid list 2018               04_working/_F3H_moa2018_cells.csv (text layer, unvalidated) + F5L visual rows
  MoA hybrid list 2020 (new)         04_working/F5L/_F5L_moa2020_cells.csv (text layer) + F5L visual rows
  MoA hybrid list 1998-2016          04_working/_F3H_moa2016_list.csv (F3H helper, visual)
  MoA season summaries               04_working/F5L/moa_editions_visual.tsv (F5L helper, visual)
  Gazette release notices            04_working/F5L/gazette_verbatim*.tsv (F5L helpers, visual)
Outputs:
  05_output/final/bgd_official_list_rows_full.csv   (long; one row per printed cell)
  03_extracted/tables/official_<list_id>_wide.csv   (one row per printed row)
  04_working/evidence_F5L.csv                       (structured attributes, Phase 2 evidence format)
"""
import csv, glob, os, pathlib, re, sys, collections
import pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "scripts"))
from lib_keys import make_key
from lib_names import variety_name

BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
LAT2BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def rd(p, sep=","):
    return pd.read_csv(p, sep=sep, dtype=str, keep_default_na=False, quoting=3 if sep == "\t" else 0)


# ---------------------------------------------------------------- reference data
MANIFEST = {r["file_path"]: r["source_url"] for r in csv.DictReader(open("02_raw/manifest.csv", encoding="utf-8"))}
REMAP = {r["old_key"]: r["new_key"] for r in csv.DictReader(open("04_working/key_remap.csv", encoding="utf-8"))}
XW = rd("04_working/hybrid_key_crosswalk.csv")
CODE = dict(zip(XW.key, XW.code))
MATCH = rd("04_working/_F3H_match_report.csv")
MKEY = {(r.source_id, r.row_id): r.key for r in MATCH.itertuples()}
SLUG = dict(zip(rd("04_working/_F3H_slugs.csv").serial, rd("04_working/_F3H_slugs.csv").key))
MEET = collections.defaultdict(set)
for f in ["04_working/nsb_meeting_key.csv", "04_working/nsb_meeting_key_additions_F3L.csv",
          "04_working/nsb_meeting_key_additions_F3H.csv"]:
    for r in csv.DictReader(open(f, encoding="utf-8")):
        if r.get("validation") in ("visual_check", "key_check", "two_source") and r["meeting_date"]:
            MEET[int(r["meeting_no"])].add(r["meeting_date"])

OTHER = {"পাজাম": "OLD_PAJAM", "পূর্বাচী": "OLD_PURBACHI", "বিএইউ-৬৩": "OLD_BAU63", "রাবি ধান-১": "OLD_RABI_DHAN1",
         "এসিআই ধান১": "OLD_ACI_DHAN1", "এসিআই ধান২": "OLD_ACI_DHAN2", "এসিআই ধান৩": "OLD_ACI_DHAN3",
         "সুপ্রীম ধান১": "OLD_SUPREME_DHAN1"}   # same table as phase3_F3L_evidence.OTHER


def nrm(s):
    return re.sub(r"[\s\-]+", "", str(s))


OTHER_N = {nrm(k): v for k, v in OTHER.items()}


def inbred_key(name):
    """F3L's key_of on the variety-name part of a name cell (never on line/pedigree text)."""
    name = re.sub(r"^\s*[০-৯0-9]+\s*[).]\s*", "", str(name))   # serial printed inside the name cell ('৮) রাবি ধান-১')
    n = nrm(name)
    for k, v in OTHER_N.items():
        if n.startswith(k):
            return v
    if n.startswith("বঙ্গবন্ধুধান১০০"):
        return "BRRI_DHAN100"
    nm = re.sub(r"ব্রি\s*-\s*ধান", "ব্রি ধান", str(name)).replace("বি ইউ ধান", "বিইউ ধান")
    nm = re.split(r"[(\[]", nm)[0]            # drop bracketed line/code/popular name
    return make_key(nm) or "UNMATCHED"


def fin(key):
    """key may hold several keys joined by ';' (a gazette row naming two varieties)."""
    ids, names = [], []
    for k in str(key).split(";"):
        k = REMAP.get(k, k)
        if not k or k == "UNMATCHED":
            continue
        ids.append("RICE-" + k)
        names.append(variety_name(k, CODE.get(k, "") or ""))
    return ";".join(ids), ";".join(names)


# ---------------------------------------------------------------- header glosses / column kinds
def kind_of(h):
    h = h or ""
    if h.startswith("("):
        return "meta"
    if "প্রতিষ্ঠান (page banner)" in h:
        return "institute_banner"
    if re.search(r"ক্র|^ক্রম", h) and len(h) < 12:
        return "serial"
    if "ফসল" in h:
        return "crop"
    if "জাতের নাম" in h or "জাতসমূহ" in h or h.strip() == "জাত":
        return "name"
    if "সনাক্তকারী" in h:
        return "identifying_traits"
    if "বিশেষ" in h or "বৈশিষ্ট্য" in h:
        return "special_traits"
    if "জীবন" in h:
        return "duration"
    if "ফলন" in h:
        return "yield"
    if "মৌসুম" in h or "মৌসু ম" in h:
        return "season"
    if "উৎস" in h:
        return "origin"
    if "উদ্ভাবন" in h or "আমদান" in h or "উৎপাদনকারী" in h or "প্রতিষ্ঠান" in h:
        return "developer"
    if "অঞ্চল" in h:
        return "region"
    if "ছাড়করণের সময়" in h:
        return "release_year"
    if "সভা" in h or "তারিখ" in h or "নিবন্ধনের সময়" in h or "ছাড়করণের" in h:
        return "meeting_date"
    if "মন্তব্য" in h:
        return "remarks"
    return "other"


GLOSS = {"serial": "serial number", "crop": "crop name", "name": "variety name (as printed, incl. code/line)",
         "identifying_traits": "identifying (diagnostic) characteristics", "special_traits": "special characteristics",
         "duration": "growth duration / life span (days)", "yield": "yield", "season": "production season",
         "origin": "origin (source country / breeder)", "developer": "developer / importer (institute or company)",
         "region": "recommended / registered / approved region", "release_year": "time (year) of release",
         "meeting_date": "NSB meeting number and date (approval / registration / release)",
         "remarks": "remarks (season and area of cultivation)", "institute_banner": "institute (table banner above the rows)"}
META_GLOSS = {"(list title)": "list title", "(footer text)": "footer text", "(gazette masthead)": "gazette masthead",
              "(gazette page numbers)": "gazette page numbers", "(issuing office)": "issuing office",
              "(memo number)": "memo (notification) number", "(memo date)": "memo date", "(preamble)": "preamble",
              "(text after table)": "text after the table", "(signatory)": "signatory",
              "(season heading)": "season heading", "(variety names listed)": "variety names listed under the heading",
              "(summary title)": "season-summary title"}


def gloss(h):
    k = kind_of(h)
    if k == "meta":
        return META_GLOSS.get(h, h.strip("()"))
    g = GLOSS.get(k, "")
    if k == "yield":
        if "একর" in h:
            g += " (t/acre)"
        elif re.search(r"হে|হঃ", h):
            g += " (t/ha)"
        if "গড়" in h:
            g = "average " + g
    if k == "duration" and "গড়" in h:
        g = "average " + g
    if k == "special_traits" and "সনাক্ত" not in h and h.strip() and "বিশেষ" not in h:
        g = "characteristics"
    if k == "meeting_date" and "ছাড়করণের তারিখ" in h:
        g = "date of release (NSB meeting and date)"
    if k == "region" and "নিবন্ধন" in h:
        g = "region of registration"
    if k == "region" and "অনুমোদিত" in h:
        g = "approved region"
    if k == "region" and "সুপারিশ" in h:
        g = "recommended region"
    if k == "name" and "অনুমোদিত" in h:
        g = "approved variety name (as printed)"
    if k == "developer" and "উদ্ভাবনকারী প্রতিষ্ঠান" in h:
        g = "developing institute"
    if k == "developer" and h.startswith("প্রতিষ্ঠানের নাম"):
        g = "institute name"
    return g or "(unglossed)"


# ---------------------------------------------------------------- normalisers
MONTHS = {"জানুয়ারি": 1, "জানুয়ারী": 1, "ফেব্রুয়ারি": 2, "ফেব্রুয়ারী": 2, "মার্চ": 3, "এপ্রিল": 4, "মে": 5, "জুন": 6,
          "জুলাই": 7, "আগস্ট": 8, "আগষ্ট": 8, "সেপ্টেম্বর": 9, "অক্টোবর": 10, "নভেম্বর": 11, "ডিসেম্বর": 12}


def yy(y):
    y = int(y)
    return y + (1900 if y >= 70 else 2000) if y < 100 else y


def meeting_pairs(t):
    """Extract (meeting_no, iso_date|None) pairs from a meeting/date cell."""
    s = t.translate(BN)
    nums = [(m.start(), int(m.group(1))) for m in re.finditer(r"(\d{2,3})\s*(?:-?\s*তম|তি|তম|ম|তম\b|সভা)", s)]
    dates = []
    for m in re.finditer(r"(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{2,4})", s):
        d, mo, y = int(m.group(1)), int(m.group(2)), yy(m.group(3))
        if 1 <= d <= 31 and 1 <= mo <= 12:
            dates.append((m.start(), f"{y:04d}-{mo:02d}-{d:02d}"))
    for m in re.finditer(r"(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s*,?\s*(\d{4})", s):
        dates.append((m.start(), f"{int(m.group(3)):04d}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"))
    nums = [n for n in nums if 30 <= n[1] <= 130]
    if not nums:
        return [(None, d) for _, d in dates]
    out = []
    for i, (pos, n) in enumerate(nums):
        # nearest date not yet used
        best = min(dates, key=lambda d: abs(d[0] - pos)) if dates else None
        out.append((n, best[1] if best else None))
    return out


def norm_value(kind, text):
    t = text.translate(BN).strip()
    if not t or t in ("-", "–"):
        return ""
    if kind in ("duration", "yield", "release_year", "serial"):
        return re.sub(r"\s+", " ", t)
    if kind == "meeting_date":
        pr = meeting_pairs(text)
        return "; ".join((f"NSB {n}" if n else "NSB ?") + (f" = {d}" if d else "") for n, d in pr)
    return ""


def validate(kind, text, base):
    """base: validation of the transcription (visual_check / unvalidated). Meeting cells upgrade to key_check."""
    if kind == "meeting_date" and text.strip():
        pr = meeting_pairs(text)
        if pr and all(n and d and d in MEET.get(n, set()) for n, d in pr):
            return "key_check"
    return base


def join_lines(s):
    parts = [p.strip() for p in str(s).split(" | ")]
    out = ""
    for p in parts:
        if not p:
            continue
        if out and (out.endswith("-") or out.endswith("/")) and not out.endswith(" -"):
            out += p
        else:
            out += (" " if out else "") + p
    return out


# ---------------------------------------------------------------- collectors
ROWS = []   # long cells


def add(list_id, title, ed, src, page, row_no, key, header, text, base_val, method, locator, col_index,
        serial="", note="", uncertain="", key_basis=""):
    vid, vname = fin(key) if key else ("", "")
    k = kind_of(header)
    val = "unvalidated" if uncertain else validate(k, text, base_val)
    ROWS.append(dict(list_id=list_id, list_title=title, fy_or_edition=ed, source_file=src, page=page, row_no=row_no,
                     variety_id=vid, variety_name=vname, column_header_as_printed=header,
                     column_header_en=gloss(header), cell_text_verbatim=text,
                     cell_value_normalised=norm_value(k, text) if k != "meta" else "",
                     validation=val, source_url=MANIFEST.get(src, ""), col_index=col_index,
                     serial_as_printed=serial, column_kind=k, method=method, locator=locator,
                     uncertain=uncertain, key_basis=key_basis, notes=note))


def helper_list(files, ed_of, title_of, key_fn, method="visual_check (transcribed by eye from 300-dpi page crops)"):
    frames = [rd(f, "\t") for f in files if os.path.exists(f)]
    if not frames:
        return
    d = pd.concat(frames, ignore_index=True)
    d["pg"] = d.page.astype(int)
    d["rp"] = d.row_in_page.astype(int)
    d["ci"] = d.col_index.astype(int)
    for lid, g in d.groupby("list_id", sort=False):
        g = g.sort_values(["pg", "rp", "ci"])
        meta = g[g.rp == 0]
        title = title_of(lid, meta)
        ed = ed_of(lid)
        for r in meta.itertuples():
            add(lid, title, ed, r.source_file, r.pg, 0, "", r.column_header_as_printed, r.cell_text_verbatim,
                "visual_check", "visual_check", r.crop_file, r.ci, r.serial_as_printed, r.note, r.uncertain)
        body = g[g.rp > 0]
        n, key, basis = 0, "", ""
        for (pg, rp), rr in body.groupby(["pg", "rp"], sort=True):
            cont = rr.note.str.contains("continues row").any() and rp == 1
            if cont:   # a printed row broken across a page: same row_no and key, empty spill-over cells dropped
                rr = rr[rr.cell_text_verbatim.str.strip() != ""]
            else:
                n += 1
                names = rr[rr.column_header_as_printed.map(kind_of) == "name"].cell_text_verbatim.tolist()
                names = sorted([x for x in names if x.strip() != "ধান"], key=len, reverse=True) or names  # FY2020-21 heads the crop column 'জাতের নাম' too
                key, basis = key_fn(lid, names[0] if names else "", rr)
            for r in rr.itertuples():
                add(lid, title, ed, r.source_file, r.pg, n, key, r.column_header_as_printed, r.cell_text_verbatim,
                    "visual_check", method, r.crop_file, r.ci, r.serial_as_printed, r.note, r.uncertain, basis)


def multi_key(name):
    """A gazette row may name two varieties ('ব্রিধান-৫১ এবং ব্রিধান-৫২'): key each part, join with ';'."""
    parts = [p for p in re.split(r"\s+এবং\s+|,\s*|\s+ও\s+", name) if p.strip()]
    ks = [inbred_key(p) for p in parts]
    ks = [k for k in ks if k != "UNMATCHED"] or ["UNMATCHED"]
    return ks


# ---- SCA compendium inbred
def comp_key(lid, name, rr):
    if lid == "SCA_FY2024-25_INBRED" and rr.pg.iloc[0] == 2 and nrm(name) == nrm("ব্রি ধান১১৩"):
        return "UNMATCHED", "F3L decision: second printed 'ব্রি ধান১১৩' (p.2 serial 6), probably dhan114 but yield differs from gazette; not keyed"
    return inbred_key(name), "lib_keys.make_key / F3L key_of on the name cell"


helper_list(sorted(glob.glob("04_working/F5L/comp_inbred_p*.tsv")), lambda l: "2016 (imprint 2014)",
            lambda l, m: "বাংলাদেশের নোটিফাইড ফসলের অনুমোদিত জাত (SCA compendium of approved varieties of notified crops; "
                         "imprint 2014, posted 2016) — ফসল ঃ ধান (Oryza sativa), inbred tables", comp_key)


# ---- SCA FY inbred lists
def fy_title(lid, meta):
    t = meta[meta.column_header_as_printed == "(list title)"].cell_text_verbatim.tolist()
    return t[0] if t else lid


helper_list(sorted(glob.glob("04_working/F5L/fy_inbred_verbatim*.tsv")),
            lambda l: "FY" + l.split("_FY")[1].split("_")[0], fy_title, comp_key)

# ---- gazettes
GZ_SRC_TITLE = "Bangladesh Gazette, Ministry of Agriculture (Seed Wing) variety release notification"


def gz_title(lid, meta):
    memo = meta[meta.column_header_as_printed == "(memo number)"].cell_text_verbatim.tolist()
    date = meta[meta.column_header_as_printed == "(memo date)"].cell_text_verbatim.tolist()
    return f"{GZ_SRC_TITLE}, gazette {lid[3:]}" + (f"; memo {memo[0]}" if memo else "") + (f" ({date[0]})" if date else "")


def gz_key(lid, name, rr):
    ks = multi_key(name)
    return ";".join(ks), "F3L key_of on each variety named in the printed row"


GZ_FILES = sorted(glob.glob("04_working/F5L/gazette_verbatim*.tsv"))
helper_list(GZ_FILES, lambda l: l[3:], gz_title, gz_key)



# ---- SCA compendium hybrid table (F3H)
COMP_H = ["ক্রম", "জাতের নাম", "উৎস", "উদ্ভাবনকারী/ আমদানীকারক", "নিবন্ধনের অঞ্চল", "মৌসুম", "জীবনকাল (দিন)",
          "ফলন (টন/হেঃ)", "নিবন্ধনের সময় (সভা ও তারিখ)"]
ch = rd("04_working/_F3H_compendium_hybrids.csv")
for n, r in enumerate(ch.itertuples(), 1):
    key = MKEY.get(("SCA_COMP", r.serial), "UNMATCHED")
    vals = [r.serial, r.name_as_printed, r.origin_as_printed, r.developer_as_printed, r.region_as_printed,
            r.season_as_printed, r.duration_days_as_printed, r.yield_t_ha_as_printed, r.meeting_cell_as_printed]
    for i, (h, v) in enumerate(zip(COMP_H, vals), 1):
        add("SCA2016_COMP_HYBRID", "বাংলাদেশের নোটিফাইড ফসলের অনুমোদিত জাত (SCA compendium; imprint 2014, posted 2016) — "
            "হাইব্রিড ধানের নিবন্ধিত জাত (registered hybrid rice varieties)", "2016 (imprint 2014)",
            "02_raw/sca/approved_varieties_notified_crops_bangladesh_2016.pdf", r.pdf_page, n, key, h, join_lines(v),
            "visual_check", "visual_check (F3H helper, page crops)", r.crop_file, i, r.serial,
            r.notes if i == 2 else "", r.uncertain if i == 2 else "", "F3H match report (SCA_COMP)")

# ---- SCA FY hybrid lists (F3H)
sh = rd("04_working/_F3H_sca_hybrid_lists.csv")
FIELD = {"serial": "list_serial", "name": "name_as_printed", "origin": "origin_as_printed", "developer": "developer_as_printed",
         "region": "region_as_printed", "season": "season_as_printed", "duration": "duration_days_as_printed",
         "yield": "yield_t_ha_as_printed", "identifying_traits": "traits_as_printed", "special_traits": "traits_as_printed"}
for fy, g in sh.groupby("fy", sort=True):
    note0 = next(n for n in g.notes if "HEADER:" in n)
    title = re.search(r"TITLE:\s*(.*?)\s*(?:\(|\|\|)", note0).group(1).strip()
    hdr = [h.strip() for h in re.search(r"HEADER:\s*(.*?)\s*\|\|", note0).group(1).split(" | ")]
    lid = f"SCA_FY{fy}_HYBRID"
    src = g.source_file.iloc[0]
    add(lid, title, "FY" + fy, src, 1, 0, "", "(list title)", title, "visual_check", "visual_check (F3H helper)",
        g.crop_file.iloc[0], 0)
    for n, r in enumerate(g.itertuples(), 1):
        key = MKEY.get((f"SCA_HYB_{fy}", f"{fy}#p{r.page}#{r.list_serial}"), MKEY.get((f"SCA_HYB_{fy}", r.list_serial), "UNMATCHED"))
        for i, h in enumerate(hdr, 1):
            k = kind_of(h)
            if k == "meeting_date":
                v = " ".join(x for x in [r.meeting_no_as_printed, r.meeting_date_as_printed] if x)
            else:
                v = getattr(r, FIELD.get(k, "notes"), "") if k in FIELD else ""
            note = ""
            if i == 2:
                note = (r.notes if "HEADER:" not in r.notes else r.notes.split("||")[-1]).strip()
                if r.latin_code_as_printed:
                    note = (note + "; " if note else "") + f"code part of the name cell: {r.latin_code_as_printed}"
            if k == "meeting_date":
                note = "cell = meeting number + date as printed (two transcription fields joined)"
            add(lid, title, "FY" + fy, src, r.page, n, key, h, join_lines(v), "visual_check",
                "visual_check (F3H helper, page crops)", r.crop_file, i, r.list_serial, note,
                r.uncertain if i == 2 else "", "F3H match report")

# ---- MoA cumulative hybrid lists
MOA_H26 = ["ক্রম", "অনুমোদিত জাতের নাম", "উৎস", "উদ্ভাবনকারী/ আমদানীকারক", "অনুমোদিত অঞ্চল", "অনুমোদনের তারিখ ও সভা"]
MOA_H18 = ["ক্রঃ নং", "অনুমোদিত জাতের নাম", "উৎস", "উদ্ভাবনকারী/আমদানীকারক", "অনুমোদিত অঞ্চল", "অনুমোদনের তারিখ ও সভা"]
VIS = rd("04_working/F5L/moa_editions_visual.tsv", "\t") if os.path.exists("04_working/F5L/moa_editions_visual.tsv") else None


def ser_bn(s):
    s = int(s)
    return f"{s:02d}".translate(LAT2BN)


def moa_edition(lid, ed, src, title, cells, hdr, key_of_row, nikosh_visual=None, base="unvalidated", meth=""):
    add(lid, title, ed, src, 1, 0, "", "(list title)", title, "visual_check" if base == "visual_check" else "unvalidated",
        meth, "", 0)
    for n, r in enumerate(cells.itertuples(), 1):
        key, basis = key_of_row(r)
        vis = nikosh_visual.get(str(r.serial)) if nikosh_visual else None
        vals = [r.name, r.origin, r.developer, r.region, r.date]
        bval = base
        m = meth
        note = r.serial_note
        if vis is not None:
            vals, bval, m = vis["vals"], "visual_check", "visual_check (Nikosh row read from the page image)"
            note = (note + "; " if note else "") + vis.get("note", "")
        pg = int(str(r.pages).split(";")[0])
        add(lid, title, ed, src, pg, n, key, hdr[0], "" if "blank" in r.serial_note else ser_bn(r.serial), bval, m,
            f"serial {r.serial}; bands {r.bands}", 1, str(r.serial), note, "", basis)
        for i, (h, v) in enumerate(zip(hdr[1:], vals), 2):
            add(lid, title, ed, src, pg, n, key, h, join_lines(v), bval, m, f"serial {r.serial}", i, str(r.serial),
                "", "", basis)


def vis_rows(lid):
    out = {}
    if VIS is None:
        return out
    g = VIS[VIS.list_id == lid]
    for (pg, rp), rr in g[g.row_in_page.astype(int) > 0].groupby(["page", "row_in_page"]):
        rr = rr.sort_values("col_index", key=lambda s: s.astype(int))
        ser = rr[rr.col_index == "1"].cell_text_verbatim.tolist()
        if not ser:
            continue
        s = re.sub(r"\D", "", ser[0].translate(BN))
        vals = rr[rr.col_index.astype(int) >= 2].cell_text_verbatim.tolist()
        if s:
            out[str(int(s))] = {"vals": (vals + [""] * 5)[:5], "note": "; ".join(x for x in rr.note if x),
                                "unc": "; ".join(x for x in rr.uncertain if x)}
    return out


c26 = rd("04_working/_F3H_moa2026_cells.csv")
v26 = rd("04_working/_F3H_moa2026_visual.csv")
vis26 = {}
for r in v26.itertuples():
    if r.name_bn_as_printed:
        vis26[r.serial] = {"vals": [r.name_bn_as_printed, r.origin_as_printed, r.developer_as_printed,
                                    r.region_as_printed, r.date_cell_as_printed], "note": r.notes}
    else:   # row 103: developer cell only
        base = c26[c26.serial == r.serial].iloc[0]
        vis26[r.serial] = {"vals": [base["name"], base.origin, r.developer_as_printed, base.region, base.date],
                           "note": "developer cell read by eye (Nikosh); " + r.notes}
T26 = "জাতীয় বীজ বোর্ড (NSB) কর্তৃক ১৯৯৮-০৫/০২/২০২৬ পর্যন্ত অনুমোদিত হাইব্রিড ধানের জাত"
moa_edition("MOA_HYBRID_2026", "2026-02-05", "02_raw/moa/hybrid_rice_varieties_list_2026-02-05.pdf", T26, c26, MOA_H26,
            lambda r: (SLUG.get(str(r.serial), "UNMATCHED"), "F3H slugs (MoA 2026 serial)"), vis26, "visual_check",
            "bijoy2unicode (span-level, F3H repairs) checked by eye against page crops by F3H")

c18 = rd("04_working/_F3H_moa2018_cells.csv")
T18 = "জাতীয় বীজ বোর্ড (NSB) কর্তৃক ১৯৯৮-২০১৮ পর্যন্ত অনুমোদিত হাইব্রিড ধানের জাতের তথ্য :"
moa_edition("MOA_HYBRID_2018", "2018-08-07", "02_raw/moa_wayback/hybrid_rice_list_2018-08-07.pdf", T18, c18, MOA_H18,
            lambda r: (MKEY.get(("MOA_HYB18", str(r.serial)), "UNMATCHED"), "F3H match report (MOA_HYB18)"),
            vis_rows("MOA_HYBRID_2018"), "unvalidated", "bijoy2unicode text layer (span-level parse, F3H)")

# 2020 edition: drop the summary paragraphs mis-parsed as rows; key by exact name match to 2026/2018
c20 = rd("04_working/F5L/_F5L_moa2020_cells.csv")
c20 = c20[~c20.name.str.contains("মৌসুম")]
c20 = c20[c20.serial.astype(int) <= 191] if len(c20) and c20.serial.astype(int).max() > 191 else c20
NAME26 = {nrm(join_lines(r.name)): SLUG.get(r.serial) for r in c26.itertuples()}
NAME26.update({nrm(v["vals"][0]): SLUG.get(s) for s, v in vis26.items()})
NAME18 = {nrm(join_lines(r.name)): MKEY.get(("MOA_HYB18", r.serial)) for r in c18.itertuples()}
vis20 = vis_rows("MOA_HYBRID_2020")


def lat(s):
    return re.sub(r"[^0-9a-zঀ-৿]", "", str(s).translate(BN).lower())


LAT26 = {lat(join_lines(r.name)): SLUG.get(r.serial) for r in c26.itertuples()}
LAT26.update({lat(v["vals"][0]): SLUG.get(s) for s, v in vis26.items()})


def key20(r):
    raw = vis20[str(r.serial)]["vals"][0] if str(r.serial) in vis20 else join_lines(r.name)
    if LAT26.get(lat(raw)) and nrm(raw) not in NAME26:
        return LAT26[lat(raw)], "name match to MoA 2026 row ignoring punctuation and digit script"
    nm = nrm(vis20[str(r.serial)]["vals"][0]) if str(r.serial) in vis20 else nrm(join_lines(r.name))
    if nm in NAME26 and NAME26[nm]:
        return NAME26[nm], "exact name match to MoA 2026 row"
    if nm in NAME18 and NAME18[nm]:
        return NAME18[nm], "exact name match to MoA 2018 row"
    k = make_key(join_lines(r.name))
    return (k, "lib_keys.make_key") if k else ("UNMATCHED", "no exact name match")


T20 = "জাতীয় বীজ বোর্ড (NSB) কর্তৃক ১৯৯৮-১৬/০৩/২০২০ পর্যন্ত অনুমোদিত হাইব্রিড ধানের জাতের তথ্য:"
moa_edition("MOA_HYBRID_2020", "2020-03-16", "02_raw/moa/item4_crop_varieties_page.pdf", T20, c20, MOA_H26, key20,
            vis20, "unvalidated", "bijoy2unicode text layer (span-level parse with F3H's parser)")

c16 = rd("04_working/_F3H_moa2016_list.csv")
T16 = "জাতীয় বীজ বোর্ড (NSB) কর্তৃক ১৯৯৮-২০১৬ পর্যন্ত অনুমোদিত হাইব্রিড ধানের জাতের  তথ্য :"
add("MOA_HYBRID_1998_2016", T16, "1998-2016", "02_raw/moa_wayback/hybrid_rice_list_1998-2016.pdf", 1, 0, "",
    "(list title)", T16, "visual_check", "visual_check", "04_working/crops/F5L/moa16_p1_header.png", 0)
for n, r in enumerate(c16.itertuples(), 1):
    key = MKEY.get(("MOA_HYB16", r.serial), "UNMATCHED")
    for i, (h, v) in enumerate(zip(MOA_H18, [r.serial, r.name_as_printed, r.origin_as_printed, r.developer_as_printed,
                                              r.region_as_printed, r.meeting_cell_as_printed]), 1):
        add("MOA_HYBRID_1998_2016", T16, "1998-2016", "02_raw/moa_wayback/hybrid_rice_list_1998-2016.pdf", r.pdf_page,
            n, key, h, join_lines(v), "visual_check", "visual_check (F3H helper; scan with junk text layer)", r.crop_file,
            i, r.serial, r.notes if i == 2 else "", r.uncertain if i == 2 else "", "F3H match report (MOA_HYB16)")

# season summaries + any other MoA visual list rows not used above
if VIS is not None:
    sumv = VIS[VIS.list_id.str.endswith("_SEASON_SUMMARY")]
    srcmap = {"2018": "02_raw/moa_wayback/hybrid_rice_list_2018-08-07.pdf", "2020": "02_raw/moa/item4_crop_varieties_page.pdf",
              "2026": "02_raw/moa/hybrid_rice_varieties_list_2026-02-05.pdf"}
    for lid, g in sumv.groupby("list_id"):
        ed = re.search(r"(\d{4})", lid).group(1)
        g = g.assign(rp=g.row_in_page.astype(int), ci=g.col_index.astype(int)).sort_values(["page", "rp", "ci"])
        for r in g.itertuples():
            add(lid, f"MoA hybrid list {ed} edition — seasonal summary (মৌসুম ভিত্তিক)", ed, srcmap.get(ed, r.source_file),
                int(r.page), r.rp, "", r.column_header_as_printed, r.cell_text_verbatim, "visual_check", "visual_check",
                r.crop_file, r.ci, r.serial_as_printed, r.note, r.uncertain,
                "season summary; names not keyed here (F3H maps the 2026 summary in evidence_F3H season rows)")

long = pd.DataFrame(ROWS)
long["fy_or_edition"] = long.fy_or_edition.astype(str)
cols = ["list_id", "list_title", "fy_or_edition", "source_file", "page", "row_no", "variety_id", "variety_name",
        "column_header_as_printed", "column_header_en", "cell_text_verbatim", "cell_value_normalised", "validation",
        "source_url", "col_index", "serial_as_printed", "column_kind", "method", "locator", "uncertain", "key_basis", "notes"]
long = long[cols]
long.to_csv("05_output/final/bgd_official_list_rows_full.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- wide per list
os.makedirs("03_extracted/tables", exist_ok=True)
for f in glob.glob("03_extracted/tables/official_*_wide.csv"):
    os.remove(f)
for lid, g in long.groupby("list_id", sort=False):
    body = g[g.row_no.astype(int) > 0].copy()
    meta = g[g.row_no.astype(int) == 0]
    body["colname"] = body.col_index.astype(str).str.zfill(2) + " " + body.column_header_as_printed + " [" + body.column_header_en + "]"
    idx = ["row_no", "page", "serial_as_printed_row", "variety_id", "variety_name"]
    ser = body.groupby("row_no").serial_as_printed.first()
    body["serial_as_printed_row"] = body.row_no.map(ser)
    w = body.pivot_table(index=idx, columns="colname", values="cell_text_verbatim", aggfunc=lambda x: " ‖ ".join(x)).reset_index()
    v = body.groupby("row_no").validation.agg(lambda s: ";".join(f"{k}={n}" for k, n in s.value_counts().items()))
    w["validation_counts"] = w.row_no.map(v)
    w.insert(0, "list_id", lid)
    w = w.sort_values("row_no", key=lambda s: s.astype(int))
    w.columns.name = None
    out = pathlib.Path(f"03_extracted/tables/official_{lid}_wide.csv")
    w.to_csv(out, index=False, encoding="utf-8-sig")
    if len(meta):
        meta[["list_id", "page", "column_header_as_printed", "column_header_en", "cell_text_verbatim", "validation", "locator"]] \
            .to_csv(out.with_name(f"official_{lid}_meta.csv"), index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- evidence (task 3)
SEASON = [("বোনা আউশ", "B. Aus"), ("রোপা আউশ", "T. Aus"), ("রোপা আমন", "T. Aman"), ("বোনা আমন", "B. Aman"),
          ("বোরো", "Boro"), ("আউশ", "Aus"), ("আমন", "Aman"), ("খরিফ-১", "Kharif-1"), ("খরিফ-২", "Kharif-2"), ("রবি", "Rabi")]


def season_en(t):
    out, s = [], t
    for b, e in SEASON:
        if b in s:
            out.append(e)
            s = s.replace(b, "")
    return "; ".join(dict.fromkeys(out))


ORIGIN = {"ভারত": "India", "চীন": "China", "বাংলাদেশ": "Bangladesh", "ফিলিপাইন": "Philippines", "ইরি": "IRRI",
          "পাকিস্তান": "Pakistan", "থাইল্যান্ড": "Thailand", "ভিয়েতনাম": "Vietnam", "যুক্তরাষ্ট্র": "USA",
          "India": "India", "China": "China", "Philippines": "Philippines", "নিজস্ব": "Bangladesh (own)"}
EVF = {"special_traits": "special_traits_official", "identifying_traits": "identifying_traits_official",
       "region": "recommended_region", "duration": "duration_days", "yield": "yield_t_ha", "season": "season",
       "origin": "origin_country", "release_year": "release_year_official", "remarks": "recommended_region"}
ev = []
for r in long.itertuples():
    if int(r.row_no) == 0 or r.column_kind not in EVF and not (r.column_kind == "meeting_date" and r.list_id.startswith("SCA_FY") and r.list_id.endswith("INBRED")):
        continue
    t = r.cell_text_verbatim.strip()
    if not t or t in ("-", "–"):
        continue
    keys = [v.replace("RICE-", "") for v in r.variety_id.split(";")] if r.variety_id else ["UNMATCHED"]
    field = EVF.get(r.column_kind, "release_year_official")
    tt = t.translate(BN)
    if field == "duration_days":
        value = re.sub(r"\s*দিন", "", tt)
    elif field == "yield_t_ha":
        value = tt + (" (per acre as printed)" if "একর" in tt or "একর" in r.column_header_as_printed else "")
    elif field == "season":
        value = season_en(t) or t
    elif field == "origin_country":
        value = "ditto (ঐ = as the row above; see evidence_F3H for the resolved country)" if t == "ঐ" else             next((v for k, v in ORIGIN.items() if k in t), t)
    elif field == "release_year_official":
        if r.column_kind == "meeting_date":
            ds = [d for _, d in meeting_pairs(t) if d]
            if not ds:
                continue
            value = ds[0][:4]
        else:
            value = tt
    else:
        value = t
    is_gz = r.list_id.startswith("GZ_")
    for k in keys:
        ev.append(dict(pilot_key=REMAP.get(k, k), field=field, value=value, value_raw=t, source_id=r.list_id,
                       source_title=r.list_title, authority_rank="1_primary_legal" if is_gz else "2_official_list",
                       local_file=r.source_file, page=r.page,
                       locator=f"{r.list_id} row {r.row_no} col {r.col_index} '{r.column_header_as_printed}'"[:200],
                       method="visual_check" if r.validation != "unvalidated" and "visual" in r.method else
                       ("bijoy2unicode" if "bijoy" in r.method else "visual_check"),
                       validation=r.validation,
                       confidence="low" if t == "ঐ" else ("medium" if r.validation == "unvalidated" or len(keys) > 1 else "high"),
                       notes=("printed row names several varieties; the cell applies to them jointly as worded; " if len(keys) > 1 else "") + ("season/region remark; " if r.column_kind == "remarks" else "") +
                             ("release year = year of the printed release date (NSB meeting); " if r.column_kind == "meeting_date" else "") +
                             (r.notes or "")[:300]))
        if r.column_kind == "remarks" and season_en(t):
            ev.append(dict(ev[-1], field="season", value=season_en(t)))
evd = pd.DataFrame(ev)
evd.to_csv("04_working/evidence_F5L.csv", index=False, encoding="utf-8")

# ---------------------------------------------------------------- summary
print("cells", len(long), "lists", long.list_id.nunique())
s = long[long.row_no.astype(int) > 0].groupby("list_id").agg(rows=("row_no", "nunique"), cells=("row_no", "size"),
                                                            keyed=("variety_id", lambda x: (x != "").sum()))
print(s.to_string())
print(long.validation.value_counts().to_string())
print("no source_url:", sorted(set(long[long.source_url == ""].source_file)))
print("evidence rows", len(evd), evd.field.value_counts().to_string(), evd.validation.value_counts().to_string())
