"""F3I: parse BRRI Adhunik Dhaner Chash 2025 Table 2 (সারণী ২: season, height, duration, traits, yield),
PDF pp.13-17. Columns are fixed x-bands taken from the header words; a row starts at a word in the name band.
SutonnyMJ text converted with bijoy2unicode. Output: 03_extracted/tables/adc2025_table2.csv"""
import pdfplumber, csv, pathlib, re, sys
from bijoy2unicode import converter
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_keys import make_key
ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF = ROOT / "02_raw/brri/brri_adhunik_dhaner_chash_2025_adc2025.pdf"
C = converter.Unicode()
BANDS = [("name", 0, 110), ("season", 110, 145), ("height", 145, 180), ("duration", 180, 222), ("traits", 222, 320), ("yield", 320, 999)]
band = lambda x: next(b for b, a, z in BANDS if a <= x < z)
rows = []
with pdfplumber.open(PDF) as pdf:
    for pn in range(12, 17):
        p = pdf.pages[pn]
        ws = [w for w in p.extract_words(keep_blank_chars=True) if w["text"].strip() and 60 < w["top"] < 560]
        ws = [w for w in ws if not (w["top"] < 80 and pn == 12) and "(†mwg)" not in w["text"]]
        starts = sorted({round(w["top"]) for w in ws if band(w["x0"]) == "name" and re.match(r"weAvi|weª", w["text"].strip())})
        for i, t0 in enumerate(starts):
            t1 = starts[i + 1] if i + 1 < len(starts) else 560
            cell = {b: [] for b, _, _ in BANDS}
            for w in sorted(ws, key=lambda w: (w["top"], w["x0"])):
                if t0 - 2 <= w["top"] < t1 - 2:
                    cell[band(w["x0"])].append(w["text"].strip())
            raw = {b: " ".join(v) for b, v in cell.items()}
            uni = {b: C.convertBijoyToUnicode(raw[b] + "  ").strip() for b in ("name", "season", "traits")}
            name, foot = uni["name"], ""
            if "*" in name:  # footnote text that sits in the name band (hybrid dhan8)
                name, foot = name.split("*", 1)[0].strip(), "*" + name.split("*", 1)[1].strip()
            season_bn = "; ".join(C.convertBijoyToUnicode(s + "  ").strip() for s in cell["season"])
            m = re.match(r"^(.*?)\s+((?:রোপা|বোনা)\s+(?:আমন|আউশ))$", name)
            if m:  # season word that starts left of the season band
                name, season_bn = m.group(1).strip(), "; ".join(x for x in (m.group(2), season_bn) if x)
            rows.append({"pdf_page": pn + 1, "row_top_pt": t0, "variety_bn": name, "key": make_key(name),
                         "season_bn": season_bn, "footnote_bn": foot,
                         "height_cm": "; ".join(cell["height"]), "duration_days": "; ".join(cell["duration"]),
                         "traits_bn": uni["traits"], "yield_t_ha": "; ".join(cell["yield"]),
                         "bijoy_ascii_name": raw["name"], "bijoy_ascii_traits": raw["traits"]})
out = ROOT / "03_extracted/tables/adc2025_table2.csv"
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "rows;", len({r["key"] for r in rows}), "keys; unmatched:", [r["variety_bn"] for r in rows if not r["key"]])
