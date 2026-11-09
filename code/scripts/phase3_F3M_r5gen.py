"""One-off generator (kept for re-runs): turn parsed hybrid items of NSB activities report no.5 (meetings 58-75,
Bijoy text layer) into draft rows for 04_working/_F3M_decisions_manual.tsv. Output printed; rows were then
reviewed by hand and appended. Usage: python phase3_F3M_r5gen.py > draft.tsv"""
import re, sys, unicodedata
sys.stdout.reconfigure(encoding="utf-8")
from phase3_F3M_hybparse import r5_lines, items, parse
import pathlib
R = pathlib.Path(__file__).resolve().parents[1] / "03_extracted/text/P2A/nsb_058-075_unicode.txt"
MT = {}
page = 0
for u in R.read_text(encoding="utf-8").splitlines():
    m = re.match(r"=== page (\d+)", u)
    if m: page = int(m.group(1)); continue
    m = re.match(r"^\s*জাতী\S*\s+\S+\s+বো\S+\s+([০-৯]+)\s*তম", u)
    if m: MT[page] = int(m.group(1).translate(str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")))
DATES = {64: "2007-09-24", 67: "2008-09-17", 70: "2009-11-04", 72: "2010-04-06", 73: "2010-09-15", 75: "2011-09-15"}
def mtg(p):
    k = max(x for x in MT if x <= p); return MT[k]
def norm(s):
    return s.replace("য়", "য়").replace("ড়", "ড়").replace("ঢ়", "ঢ়")
L = [(p, norm(u), lat) for p, u, lat in r5_lines(50, 101)]
n = 0
for it in items(L):
    r = parse(it)
    if not r: continue
    lat = [t for t in r["latin"].split(" ; ") if t and not re.search(r"GBP|e‡l|^\d+$|^[0-9]+[gq] |cybt|h_v", t)]
    lat = [re.sub(r"^(Gi|Z|Ki|I) ", "", t) for t in lat]
    m = mtg(r["page"]); n += 1
    typ = "registration_extension" if r["retrial"] else "registration_provisional"
    print("\t".join([f"r5h{n:03d}", str(m), DATES.get(m, ""), typ, re.sub(r"^(পূনঃ|পুনঃ|পুণঃ)\s*(ট্রায়ালকৃত|টায়ালকৃত)\s*", "", r["name_bn"]),
                     " / ".join(lat), r["h_codes"], r["company"], "", r["regions"], "", "B5", str(r["page"]),
                     re.escape(r["name_bn"][-12:]), "re-trial" if r["retrial"] else ""]))
