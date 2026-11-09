"""F3I: download BINA per-variety rice pages linked from the saved BINA menu (sequential, lib_fetch)."""
import pathlib, re, sys
from bs4 import BeautifulSoup
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch
from lib_keys import make_key
ROOT = pathlib.Path(__file__).resolve().parents[1]
s = BeautifulSoup((ROOT / "02_raw/bina/bina_at_a_glance_varieties.html").read_text(encoding="utf-8"), "html.parser")
seen = set()
for a in s.find_all("a"):
    t = a.get_text(" ", strip=True); h = a.get("href", "")
    if h.startswith("/pages/static-pages/") and re.search(r"বিনা\s*ধান|বিনাধান|ইরাটম|বিনাশাইল", t) and h not in seen:
        seen.add(h)
        key = make_key(t) or "UNMATCHED"
        url = "https://bina.gov.bd" + h
        try:
            p = fetch(url, f"bina/varieties/{key}.html", "F3I", notes=f"BINA per-variety page {t} [verify=False: incomplete TLS chain]")
        except Exception as e:
            p = f"FAILED {e}"
        print(key, t, p)
