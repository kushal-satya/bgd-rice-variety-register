"""P2A: download selected MoA gazettes from dpp.gov.bd (bgpress index rows from RR) via lib_fetch."""
import csv, re, sys, pathlib
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
        print("ok", fetch(url, rel, agent="P2A", notes="Gazette Extraordinary (MoA) " + r["cells_joined"][:150]))
    except Exception as e:
        print("FAIL", url, e)
