"""Repair Latin runs that bijoy2unicode wrongly converted to Bangla (e.g. 'HG-202' -> 'ঐএ-২০২').

Font-aware: in SutonnyMJ PDFs the Latin codes are printed in Latin fonts (Times, Arial). For every
Latin-font token on every page of each cited PDF we compute what bijoy2unicode turns it into, and
replace that garbled string with the original Latin wherever it occurs in a bijoy2unicode evidence
value from the same file. Ambiguous garbles (two different Latin sources) are skipped and listed.
Writes 04_working/evidence_corrections_bijoy.csv (action=replace), applied by assemble.py."""
import re, fitz, pandas as pd
from bijoy2unicode import converter
C = converter.Unicode()
ev = pd.concat([pd.read_csv(p, dtype=str, keep_default_na=False).assign(agent=p.split("evidence_")[1][:-4])
                for p in __import__("glob").glob("04_working/evidence_*.csv")])
b = ev[ev.method == "bijoy2unicode"]
fixes, ambiguous = [], set()
for f, g in b.groupby("local_file"):
    try:
        d = fitz.open(f)
    except Exception:
        continue
    gmap = {}
    for page in d:
        for blk in page.get_text("dict")["blocks"]:
            for ln in blk.get("lines", []):
                for sp in ln["spans"]:
                    if "Sutonny" in sp["font"] or not re.search(r"[A-Za-z]", sp["text"]):
                        continue
                    for tok in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-/.]*[A-Za-z0-9]|[A-Za-z]", sp["text"]):
                        # code-like tokens only: >=2 capitals, or letters+digits (e.g. HG-202, Hejia-303)
                        if not (re.search(r"[A-Z].*[A-Z]", tok) or (re.search(r"[A-Za-z]", tok) and re.search(r"\d", tok))):
                            continue
                        try:
                            gar = C.convertBijoyToUnicode(tok).strip()
                        except Exception:
                            continue
                        if gar and gar != tok and len(gar) >= 2:
                            if gar in gmap and gmap[gar] != tok:
                                ambiguous.add((f, gar, gmap[gar], tok))
                            gmap.setdefault(gar, tok)
    for a in ambiguous:
        gmap.pop(a[1], None)
    keys = sorted(gmap, key=len, reverse=True)
    for _, r in g.iterrows():
        def fix_paren(m):
            t = m.group(0)
            for gar in keys:
                if gar in t:
                    t = t.replace(gar, gmap[gar])
            return t
        new = re.sub(r"\([^()]*\)", fix_paren, r.value)   # only inside parentheses
        if new != r.value:
            fixes.append(dict(agent=r.agent, pilot_key=r.pilot_key, field=r.field, value=r.value, action="replace",
                              new_field="", new_value=new, reason="bijoy2unicode garbled a Latin-font run; restored from the PDF's Latin span (font-aware)"))
out = pd.DataFrame(fixes).drop_duplicates()
out.to_csv("04_working/evidence_corrections_bijoy.csv", index=False, encoding="utf-8")
print(len(out), "replacements;", len(ambiguous), "ambiguous garbles skipped")
print(out[out.field == "official_name_bn"][["pilot_key", "value", "new_value"]].head(25).to_string())
