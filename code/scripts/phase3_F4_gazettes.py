"""F4: download selected MoFL extraordinary gazettes (from 04_working/P2F_bgpress_mofl_index.csv)
and extract text. Re-runnable (lib_fetch skips existing)."""
import sys, csv, re, pathlib, fitz
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch, ROOT
SKIP = re.compile(r"নিয়োগ|চাকুরী|গ্রেডেশন|ডেইরি|পোল্ট্রি|পশু জবাই|ভেটেরিনারি|সামুদ্রিক মৎস্য বিধিমালা, ২০২৩।|Marine Fisheries Act|নিঝুম|পশুরোগ")
out = []
for r in csv.DictReader(open(ROOT/"04_working/P2F_bgpress_mofl_index.csv", encoding="utf-8")):
    c, u = r["cells_joined"], r["pdf_url"]
    d = c.split("||")[0].strip()
    yr = int(d[-4:])
    if yr < 2008 and "384-L" not in c and "442-L" not in c and "343-L" not in c: continue
    if SKIP.search(c): continue
    url = "https://dpp.gov.bd" + u.replace(" ", "%20")
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", u.split("/")[-1])
    rel = f"fish_governance/bgpress/mofl_{d}_{name}"
    try:
        p = fetch(url, rel, "F4", f"MoFL extraordinary gazette: {c[:150]}")
    except Exception as e:
        print("FAIL", url, e); continue
    try:
        doc = fitz.open(ROOT/p); txt = "\n".join(pg.get_text() for pg in doc)
    except Exception as e:
        txt = ""; print("open fail", p, e)
    tp = ROOT/"03_extracted/text/F4"/(pathlib.Path(p).stem+".txt"); tp.parent.mkdir(parents=True, exist_ok=True); tp.write_text(txt, encoding="utf-8")
    print(d, len(txt), p)
