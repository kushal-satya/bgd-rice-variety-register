"""L2: ASTI. Saves the /data, /bangladesh and /trivsa pages, the TRIVSA xlsx files, and the Bangladesh
'full dataset' that the /data page's 'Download data' button produces (a form POST to the www host's
excelexport script, exactly as the button sends it). dataportal.asti.cgiar.org (the JSON API) is
robots-disallowed and is NOT called directly."""
import sys, pathlib, re, time, datetime, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import requests
from lib_fetch import fetch, _throttle, UA, RAW, register_existing, already

AG = "L2"; W = "https://www.asti.cgiar.org"; OUT = "cgiar_specific/asti"
for u, rel in [(f"{W}/data", f"{OUT}/data.html"), (f"{W}/bangladesh?country=BGD", f"{OUT}/bangladesh.html"),
               (f"{W}/trivsa", f"{OUT}/trivsa.html"),
               (f"{W}/sites/default/files/trivsa/TRIVSA-Data.xlsx", f"{OUT}/TRIVSA-Data.xlsx"),
               (f"{W}/sites/default/files/trivsa/TRIVSA-Rice-Data.xlsx", f"{OUT}/TRIVSA-Rice-Data.xlsx")]:  # rice file already in manifest as 02_raw/asti_trivsa/]:
    try:
        print(fetch(u, rel, AG, "ASTI"))
    except Exception as e:
        print("FAIL", u, e)

page = (RAW / OUT / "data.html").read_text(encoding="utf-8")
inds = re.search(r'"FULL\.INDICATORS":"([^"]+)"', page).group(1)
url = f"{W}/sites/all/libraries/mw//excelexport/"
for fmt, rel in [("xls", f"{OUT}/ASTI_full_BGD_country.xls"), ("csv", f"{OUT}/ASTI_full_BGD_country.csv")]:
    if (RAW / rel).exists() or (RAW / rel.replace(".xls", ".xlsx")).exists():
        continue
    data = {"lang": "en", "format": fmt, "indicators": inds, "type": "country", "countries": "BGD",
            "mw-export-monitor": str(int(time.time() * 1000))}
    _throttle("www.asti.cgiar.org")
    r = requests.post(url, data=data, headers={"User-Agent": UA}, timeout=180)
    print(fmt, r.status_code, r.headers.get("content-type"), r.headers.get("content-disposition"), len(r.content))
    if r.status_code == 200 and len(r.content) > 500:
        cd = r.headers.get("content-disposition", "")
        m = re.search(r'filename="?([^";]+)', cd)
        if m and m.group(1).endswith(".xlsx"):
            rel = rel.replace(".xls", ".xlsx")
        (RAW / rel).write_bytes(r.content)
        register_existing(rel, url + f"?countries=BGD&format={fmt}&type=country&indicators=FULL.INDICATORS",
                          AG, "ASTI /data 'Download data' button: form POST, all FULL.INDICATORS, Bangladesh")
    else:
        print(r.text[:500])

# --- ASTI-BARC Bangladesh publications (country note / factsheet / briefs): agency-level tables ---
from lib_fetch import get
for slug in ["bangladesh-country-note-2019", "bangladesh-factsheet", "bangladesh-note", "bangladesh-brief"]:
    rel = f"{OUT}/pubs/{slug}.html"
    p = fetch(f"{W}/publications/{slug}", rel, AG, "ASTI publication page")
    t = (RAW / rel).read_text(encoding="utf-8", errors="replace")
    for h in sorted(set(re.findall(r'href="([^"]+\.pdf)"', t, re.I))):
        u = h if h.startswith("http") else W + h
        name = u.rsplit("/", 1)[-1].split("?")[0]
        try:
            print(fetch(u, f"{OUT}/pubs/{slug}__{name}", AG, f"PDF linked from ASTI page {slug}"))
        except Exception as e:
            print("FAIL", u, e)
