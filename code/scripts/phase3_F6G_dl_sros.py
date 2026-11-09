"""F6G: download every pre-2013 MoA extraordinary SRO in the bgpress MoA index (RR index + F6G refresh)
that is not yet in 02_raw. Re-runnable (lib_fetch skips existing)."""
import sys, csv, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch, ROOT
sys.stdout.reconfigure(encoding="utf-8")
idx = [ROOT / "01_discovery/_parts/RR_bgpress_moa_extraordinary_index.csv", ROOT / "04_working/F6G/bgpress_moa_m14_index.csv"]
seen = set(); out = []
for f in idx:
    if not f.exists(): continue
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        c = [x.strip() for x in r["cells_joined"].split("||")]
        d = datetime.datetime.strptime(c[0], "%d-%b-%Y").date()
        url = r["pdf_url"].replace("http://", "https://")
        if url in seen: continue
        seen.add(url)
        if d.year >= 2013: continue
        fn = url.split("/")[-1].replace(" ", "_").replace("(", "").replace(")", "")
        rel = f"bgpress/moa_extra_{c[0]}_{fn}"
        try:
            p = fetch(url.replace(" ", "%20"), rel, "F6G", f"bgpress MoA extraordinary {c[0]} {c[1]} pp {c[-1]}")
            sz = (ROOT / p).stat().st_size
        except Exception as e:
            p, sz = f"FAIL {e}", 0
        print(c[0], c[1], p, sz)
