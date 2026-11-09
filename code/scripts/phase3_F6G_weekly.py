"""F6G: sweep Bangladesh Gazette WEEKLY issues on dpp.gov.bd/bgpress (listed only from 2013) for MoA
variety-release notices. Downloads the chosen Parts via lib_fetch into 02_raw/gazette_weekly/, text-searches
each page (raw text + bijoy2unicode conversion, NFD-normalised), logs every issue to 04_working/F6G/weekly_scan_log.csv.
Usage: python phase3_F6G_weekly.py <date_from> <date_to> [parts, default "Part I,Part VI,Part VII"]"""
import sys, re, html, csv, pathlib, unicodedata, requests, fitz
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import _throttle, UA, get, fetch, ROOT
from bijoy2unicode import converter
sys.stdout.reconfigure(encoding="utf-8")
C = converter.Unicode()
N = lambda s: unicodedata.normalize("NFD", s)
TERMS = ["ছাড়করণ", "ছাড়করন", "ছাড়কৃত", "জাতীয় বীজ বোর্ড", "বীজ বোর্ড", "চাষাবাদের নিমিত্ত", "ধানের জাত",
         "ব্রি ধান", "বিনা ধান", "বীজ অনুবিভাগ", "বীজ উইং", "এনএসবি", "National Seed Board"]
df, dt = sys.argv[1], sys.argv[2]
parts = sys.argv[3].split(",") if len(sys.argv) > 3 else ["Part I", "Part VI", "Part VII"]
LOG = ROOT / "04_working/F6G/weekly_scan_log.csv"
new = not LOG.exists()
logf = open(LOG, "a", newline="", encoding="utf-8"); lw = csv.writer(logf)
if new: lw.writerow(["issue_date", "vol", "part", "pages_printed", "pdf_pages", "text_pages", "local_file", "hits"])
_throttle("www.dpp.gov.bd")
r = requests.post("https://www.dpp.gov.bd/bgpress/index.php/document/search_gazette",
                  data={"keyword": "", "date_from": df, "date_to": dt, "gazette_type": "weekly"}, headers={"User-Agent": UA}, timeout=120)
issues = sorted(set(re.findall(r'get_gazette_part/(\d+)/(\d{4}-\d\d-\d\d)', r.text)), key=lambda x: x[1])
print(len(issues), "issues", df, dt)
for vol, d in issues:
    lr = get(f"https://www.dpp.gov.bd/bgpress/index.php/document/get_gazette_part/{vol}/{d}")
    for tr in re.findall(r'<tr.*?</tr>', lr.text, re.S):
        cells = [re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', c))).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
        if not cells or cells[0] not in parts: continue
        pdfs = re.findall(r'href="([^"]+\.pdf)"', tr)
        if not pdfs:
            lw.writerow([d, vol, cells[0], cells[2] if len(cells) > 2 else "", 0, 0, "", "no file (N/A)"]); continue
        url = pdfs[0].replace("http://", "https://")
        tag = cells[0].replace(" ", "")
        try:
            p = fetch(url, f"gazette_weekly/weekly_{d}_{tag}_{url.split('/')[-1]}", "F6G", f"Bangladesh Gazette weekly {d} vol {vol} {cells[0]} pp {cells[2] if len(cells)>2 else ''}")
            doc = fitz.open(ROOT / p)
        except Exception as e:
            lw.writerow([d, vol, cells[0], cells[2] if len(cells) > 2 else "", 0, 0, "", f"FAIL {e}"]); print(d, cells[0], "FAIL", e); continue
        hits = []; tp = 0
        for i, pg in enumerate(doc):
            t = pg.get_text()
            if len(t.strip()) > 50: tp += 1
            def cv(l):
                try: return C.convertBijoyToUnicode(l + "  ")
                except Exception: return ""
            u = "\n".join(cv(l) for l in t.splitlines())
            nt, nu = N(t), N(u)
            for term in TERMS:
                if N(term) in nt or N(term) in nu:
                    hits.append(f"p{i+1}:{term}")
        lw.writerow([d, vol, cells[0], cells[2] if len(cells) > 2 else "", doc.page_count, tp, p, ";".join(hits)]); logf.flush()
        print(d, cells[0], doc.page_count, tp, hits[:8])
