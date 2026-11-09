"""Classify Wayback CDX rows (saved JSON in 02_raw/wayback_cdx) into variety-relevant categories.
Writes 01_discovery/_parts/RR_wayback_variety_files.csv (one row per unique archived document)."""
import json, re, csv, urllib.parse, collections, glob, os
DOC = re.compile(r"\.(pdf|xlsx?|docx?)$", re.I)
def classify(u, fn):
    f = fn
    if "1502f478" in u: return "committee_minutes_unidentified(likely Seed Promotion Committee)"
    if re.search(r"\bTC\b|TC Meeting|TC of NSB|NSB TC|কারিগরি কমিটি|কারিগরী কমিটি", f, re.I): return "tcnsb_minutes_or_docs"
    if "78cad328" in u and re.search(r"Meeting", f, re.I): return "tcnsb_minutes_or_docs"
    if re.search(r"Gazette|গেজেট|release_|NSB-\d+.*\d\d\.\d\d|ছাড়করণ", f, re.I) and not re.search(r"পদ্ধতি|নির্দেশিকা|Evaluation", f): return "release_gazette_or_notification"
    if re.search(r"hybrid|হাইব্রিড", f, re.I) and re.search(r"list|List|Regis|Hybrid\.pdf|Hybrid \(1\)|Hybrid 17|hybrid_1998|জাত--", f): return "hybrid_rice_registered_list"
    if re.search(r"Approved var|Variety\.pdf|notified_crops_released|অনুমোদিত জাত", f, re.I): return "approved_variety_list"
    if re.search(r"পদ্ধতি|নির্দেশিকা|Evaluation|Procedure|Evolution|Manual", f, re.I) and re.search(r"জাত|Variet|hybrid|হাইব্রিড|Rice|Wheat", f, re.I): return "release_registration_procedure"
    if re.search(r"NSB|বীজ বোর্ড|Seed Board", f, re.I) or ("a10922ac" in u or "4f5ba92d" in u): return "nsb_minutes_or_reports"
    if re.search(r"(?<![a-z])\d{1,3}\s?(st|nd|rd|th)?\s?Meeting", f, re.I) and "sca.portal" in u: return "nsb_minutes_or_reports"
    if re.search(r"\bDUS\b", f): return "dus_reports"
    return None
out = {}
for fpath in sorted(glob.glob("02_raw/wayback_cdx/*.json")):
    try: data = json.load(open(fpath, encoding="utf-8"))
    except Exception: continue
    for r in data[1:]:
        urlkey, ts, orig, mime, status, digest, length = r
        u = urllib.parse.unquote(orig)
        if not (DOC.search(u) or mime == "application/pdf"): continue
        if status not in ("200", "-"): continue
        fn = u.rsplit("/", 1)[-1]
        cat = classify(u, fn)
        if not cat: continue
        key = re.sub(r"^https?://(www\.)?", "", u).replace(":80/", "/")
        key = key.replace("sca.gov.bd/", "sca.portal.gov.bd/", 1) if "/sites/default/files/files/sca.portal.gov.bd/" in key else key
        if key in out and out[key]["first_capture"] <= ts: continue
        out[key] = dict(source_cdx=os.path.basename(fpath), category=cat, first_capture=ts, mimetype=mime, length=length,
                        filename=fn, original_url=orig, wayback_url=f"https://web.archive.org/web/{ts}id_/{orig}")
rows = sorted(out.values(), key=lambda r: (r["category"], r["original_url"]))
with open("01_discovery/_parts/RR_wayback_variety_files.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
c = collections.defaultdict(list)
for r in rows:
    dom = "sca" if "sca" in r["original_url"] else "moa"
    c[(dom, r["category"])].append(r["first_capture"][:4])
for k, v in sorted(c.items()): print(k, len(v), min(v), "-", max(v))
print("total", len(rows))
