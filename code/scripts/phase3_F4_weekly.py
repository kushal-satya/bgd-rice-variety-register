"""F4: search Bangladesh Gazette weekly Part I issues in a date window for fish-strain naming notices.
Usage: python phase3_F4_weekly.py <date_from> <date_to> <term1,term2,...>"""
import sys, re, html, pathlib, requests, fitz
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import _throttle, UA, get, fetch, ROOT
from bijoy2unicode import converter
C = converter.Unicode()
df, dt, terms = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
_throttle("www.dpp.gov.bd")
r = requests.post("https://www.dpp.gov.bd/bgpress/index.php/document/search_gazette",
                  data={"keyword": "", "date_from": df, "date_to": dt, "gazette_type": "weekly"}, headers={"User-Agent": UA}, timeout=120)
issues = sorted(set(re.findall(r'get_gazette_part/(\d+)/(\d{4}-\d\d-\d\d)', r.text)), key=lambda x: x[1])
print(len(issues), "issues")
for vol, d in issues:
    lr = get(f"https://www.dpp.gov.bd/bgpress/index.php/document/get_gazette_part/{vol}/{d}")
    for tr in re.findall(r'<tr.*?</tr>', lr.text, re.S):
        cells = [re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', c))).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
        if not cells or cells[0] != "Part I": continue
        url = re.findall(r'href="([^"]+\.pdf)"', tr)[0].replace("http://", "https://")
        try:
            p = fetch(url, f"fish_governance/bgpress_weekly/weekly_{d}_partI_{url.split('/')[-1]}", "F4", f"Bangladesh Gazette weekly {d} vol {vol} Part I pp {cells[2] if len(cells)>2 else ''}")
        except Exception as e:
            print(d, "FAIL", e); continue
        try:
            doc = fitz.open(ROOT / p)
        except Exception as e:
            print(d, "open fail", e); continue
        hits = []
        for i, pg in enumerate(doc):
            t = pg.get_text()
            u = "\n".join(C.convertBijoyToUnicode(l + "  ") for l in t.splitlines())
            for term in terms:
                if term in t or term in u:
                    hits.append((i + 1, term))
        print(d, vol, cells[2] if len(cells) > 2 else "", doc.page_count, "HITS:", hits)
