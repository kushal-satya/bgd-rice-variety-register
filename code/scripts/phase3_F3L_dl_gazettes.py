"""F3L: download missing MoA release-notice gazettes (bgpress MoA extraordinary index, RR) via lib_fetch.
Usage: python scripts/phase3_F3L_dl_gazettes.py 8154_27389,44797_55779,57313_27596"""
import csv, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch
ROOT = pathlib.Path(__file__).resolve().parents[1]
WANT = sys.argv[1].split(",")
for r in csv.DictReader(open(ROOT / "01_discovery/_parts/RR_bgpress_moa_extraordinary_index.csv", encoding="utf-8-sig")):
    url = r["pdf_url"]; fn = url.rsplit("/", 1)[1]
    if fn.replace(".pdf", "") not in WANT: continue
    d = r["cells_joined"].split("||")[0].strip()
    rel = f"bgpress/moa_extra_{d}_{fn}"
    try:
        print("ok", fetch(url, rel, agent="F3L", notes="Gazette Extraordinary (MoA) " + r["cells_joined"][:150]))
    except Exception as e:
        print("FAIL", url, e)
