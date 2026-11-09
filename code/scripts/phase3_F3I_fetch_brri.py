"""F3I: download BRRI fact sheets for varieties missing from ADC 2025 Table 1 (BRRI dhan109-118, hybrid dhan9-10)
and, for reference, every fact sheet linked from the four season list pages (cache-aware via lib_fetch).
Links are read from the saved list pages in 02_raw/brri/."""
import pathlib, re, sys
from bs4 import BeautifulSoup
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch
from lib_keys import make_key
ROOT = pathlib.Path(__file__).resolve().parents[1]
B = ROOT / "02_raw/brri"
PAGES = {"aus": "brri_gov_variety_list_aus.html", "aman": "brri_gov_variety_list_aman.html",
         "boro": "brri_gov_variety_list_boro.html", "hybrid": "brri_gov_variety_list_hybrid.html",
         "new2026": "brri_gov_new_varieties_2026_page.html"}
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def links():
    out = []
    for season, f in PAGES.items():
        s = BeautifulSoup((B / f).read_text(encoding="utf-8", errors="replace"), "html.parser")
        for t in s.find_all("table"):
            for r in t.find_all("tr"):
                cells = [c.get_text(" ", strip=True) for c in r.find_all(["td", "th"])]
                a = r.find("a")
                if not a or not a.get("href", "").endswith(".pdf"):
                    continue
                name = cells[1] if season == "new2026" else cells[0]
                name = re.sub(r"(?<=[০-৯])\s+(?=[০-৯])", "", name)  # 'ব্রি ধান১ ০ ৩' -> 'ব্রি ধান১০৩'
                name = re.sub(r"^ব্রি উদ্ভাবিত নতুন ধানের জাত\s*", "", name)
                out.append((season, name, make_key(name), a["href"]))
    return out


if __name__ == "__main__":
    want = set(sys.argv[1:])  # keys to download; empty = gap set only
    gap = {f"BRRI_DHAN{n}" for n in range(109, 119)} | {"BRRI_HYBRID9", "BRRI_HYBRID10"}
    for season, name, key, url in links():
        if (want and key in want) or (not want and key in gap):
            rel = f"brri/factsheets/{key}_{season}_{url.rsplit('/', 1)[-1]}"
            p = fetch(url, rel, "F3I", notes=f"BRRI fact sheet {name} (list page: {season})")
            print(key, season, p)
