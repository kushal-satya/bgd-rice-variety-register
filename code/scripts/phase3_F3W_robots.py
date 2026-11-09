"""F3W: fetch robots.txt for CGIAR web hosts (sequential, lib_fetch.get)."""
import pathlib
from lib_fetch import get, ROOT
HOSTS = ["www.irri.org", "irri.org", "knowledgebank.irri.org", "www.cgiar.org", "results.cgiar.org",
         "www.harvestplus.org", "www.africarice.org", "csisa.org", "www.cimmyt.org", "ricebreedinginnovations.irri.org",
         "strasa.irri.org", "cgspace.cgiar.org", "worldfishcenter.org", "reporting.cgiar.org", "mel.cgiar.org", "ricepedia.org",
         "seed.irri.org", "www.rice.org"]
out = ROOT / "02_raw/_robots"
for h in HOSTS:
    try:
        r = get(f"https://{h}/robots.txt")
        print(h, r.status_code, len(r.text))
        if r.status_code == 200:
            (out / f"{h}.txt").write_text(r.text, encoding="utf-8")
    except Exception as e:
        print(h, "ERR", e)
