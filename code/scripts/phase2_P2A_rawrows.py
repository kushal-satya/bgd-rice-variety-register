"""P2A: write 04_working/P2A_official_rice_rows_raw.csv: every rice row read from the SCA annual lists,
the SCA 2016 compendium (rice pages 11-33) and the MoA cumulative hybrid list (2026 and 2018 editions).
OCR rows are split on serial-number line starts (heuristic; no cleaning). validated = yes when the
(meeting, date) pair read from the row equals a validated row of 04_working/nsb_meeting_key.csv
(key_check) or the row was visually checked by P2A; else no."""
import csv, re, pathlib, glob
ROOT = pathlib.Path(__file__).resolve().parents[1]
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
OCR = ROOT / "03_extracted/text/ocr"
CONF = re.compile(r"8(?=[০-৯]|\s?তম)|(?<=[০-৯])8|¢(?=[০-৯]|\s?তম)|(?<=[০-৯])¢")
NUMD = r"(\d{1,2})\s*[-./]\s*(\d{1,2})\s*[-./]\s*(\d{2,4})"


def iso(d, m, y):
    y = int(y)
    if y < 100:
        y += 1900 if y > 50 else 2000
    if not (1 <= int(m) <= 12 and 1 <= int(d) <= 31):
        return ""
    return f"{y:04d}-{int(m):02d}-{int(d):02d}"


key_ok = set()
for r in csv.DictReader(open(ROOT / "04_working/nsb_meeting_key.csv", encoding="utf-8")):
    if r["validation"] in ("two_source", "visual_check") and r["kind"] != "title":
        key_ok.add((int(r["meeting_no"]), r["meeting_date"]))
VISUAL = {  # (file stem, page, name regex) of rows P2A cropped and read
    ("approved_varieties_notified_crops_bangladesh_2016", 11, r"আইআর|বিআর-১ "), ("approved_varieties_notified_crops_bangladesh_2016", 14, r"বিআর-১১"),
    ("approved_varieties_notified_crops_bangladesh_2016", 16, r"ধান-২৮"), ("approved_varieties_notified_crops_bangladesh_2016", 17, r"ধান-২৯"),
    ("approved_varieties_notified_crops_bangladesh_2016", 19, r"ধান-৪৭"), ("approved_varieties_notified_crops_bangladesh_2016", 20, r"ধান-৫[২৬]"),
    ("approved_varieties_notified_crops_bangladesh_2016", 21, r"ধান-৬২"), ("approved_varieties_notified_crops_bangladesh_2016", 24, r"বিনা ধান-৭"),
    ("approved_varieties_notified_crops_bangladesh_2016", 27, r"হাইব্রিড ধান-১|HS-273"),
    ("approved_crop_varieties_2018-19", 1, r"ধান- ৮৯"), ("approved_crop_varieties_2025-26", 1, r"বিনা ধান২৭"),
    ("approved_crop_varieties_2025-26", 2, r"ধান১১৮"),
}
START = re.compile(r"^\W{0,3}(?:ধান\s*)?(?:[০-৯0-9]{1,3}\s*[).।:]|[০-৯]{2,3}\s|[0-9]{1,2}\)|v[o)]|So\s)")
RICE = re.compile(r"ধান|ব্রি|বিনা|হাইব্রিড|dhan|Dhan|হীরা|আইআর|বিআর|BR|IR|ইরাটম|পাজাম|পূর্বাচী|বাউ|বিইউ")
out = []


def rows_from(stem, page, src, rice_only):
    f = OCR / stem / f"p{page:03d}_psm6.txt"
    if not f.exists():
        return
    lines = [l.strip() for l in f.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    cur = []
    groups = []
    for l in lines:
        has_date = bool(re.search(NUMD, " ".join(cur).translate(BN)))
        if cur and (START.match(l) or (has_date and re.match(r"^\W{0,3}\S*\s*\S*\s*(হাইব্রিড|ধান|ব্রি|বিনা)", l))):
            groups.append(cur); cur = []
        cur.append(l)
    if cur:
        groups.append(cur)
    for g in groups:
        txt = " / ".join(g)
        if rice_only and not RICE.search(txt):
            continue
        fx = CONF.sub(lambda m: "৪" if m.group(0) == "8" else "৫", txt).translate(BN)
        mt = re.findall(r"(\d{2,3})\s*-?\s*তম", fx)
        dt = [iso(*d) for d in re.findall(NUMD, fx)]
        dt = [d for d in dt if d]
        nm = re.search(r"((?:ব্রি|বিনা|বি|বাউ|বিইউ|জিএইউ|ব্র্যাক|রাবি)\s*(?:হাইব্রিড\s*)?ধান[-\s]*[০-৯]+|বিআর[-\s]*[০-৯]+|আইআর\s*\S+|[^\s|/]+\s*হাইব্রিড\s*ধান[-\s]*[০-৯]*|HS-\d+|হীরা[-\s]*[০-৯]+)", txt)
        m0 = int(mt[0]) if mt else None
        d0 = dt[0] if dt else ""
        vis = any(s == stem and p == page and re.search(rx, txt) for s, p, rx in VISUAL)
        ok = vis or (m0 is not None and (m0, d0) in key_ok)
        out.append(dict(source_file=src, page=page, row_text_ocr=txt, name_guess=nm.group(1) if nm else "",
                        meeting_no_guess=";".join(mt), date_guess=";".join(dt), validated="yes" if ok else "no",
                        method="ocr", validation_basis=("visual_check" if vis else "key_check" if ok else "")))


comp = "approved_varieties_notified_crops_bangladesh_2016"
for p in range(11, 34):
    rows_from(comp, p, f"02_raw/sca/{comp}.pdf", rice_only=False)
for f in sorted(glob.glob(str(ROOT / "02_raw/sca/approved_crop_varieties_*.pdf"))):
    stem = pathlib.Path(f).stem
    for p in range(1, 4):
        rows_from(stem, p, f"02_raw/sca/{stem}.pdf", rice_only=True)
for f in sorted(glob.glob(str(ROOT / "02_raw/sca/registered_hybrid_rice_*.pdf"))):
    stem = pathlib.Path(f).stem
    for p in range(1, 4):
        rows_from(stem, p, f"02_raw/sca/{stem}.pdf", rice_only=False)
# MoA cumulative hybrid list (text layer, bijoy2unicode)
for ed, src in (("2026", "02_raw/moa/hybrid_rice_varieties_list_2026-02-05.pdf"), ("2018", "02_raw/moa_wayback/hybrid_rice_list_2018-08-07.pdf")):
    for r in csv.DictReader(open(ROOT / f"04_working/_P2A_moa_hybrid_entries_{ed}.csv", encoding="utf-8")):
        pairs = [p.split("=") for p in r["pairs"].split(";") if p]
        ok = bool(pairs) and all((int(m), d) in key_ok for m, d in pairs)
        out.append(dict(source_file=src, page=r["page"], row_text_ocr=f"[{r['serial']}] " + r["row_text"], name_guess=r["name_guess"],
                        meeting_no_guess=r["meetings"], date_guess=r["dates"], validated="yes" if ok else "no",
                        method="bijoy2unicode (text layer, not OCR)", validation_basis="key_check" if ok else ""))
with open(ROOT / "04_working/P2A_official_rice_rows_raw.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["source_file", "page", "row_text_ocr", "name_guess", "meeting_no_guess", "date_guess",
                                       "validated", "method", "validation_basis"])
    w.writeheader(); w.writerows(out)
import collections
c = collections.Counter((r["source_file"].split("/")[-1][:30], r["validated"]) for r in out)
for k, v in sorted(c.items()):
    print(k, v)
print(len(out))
