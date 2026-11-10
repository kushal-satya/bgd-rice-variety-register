"""Variety-wise rice area coverage, from the two public by-variety sources that could be archived.

Inputs  02_raw/brri/brri_db_adoption_rate_brri_varieties.pdf
            BRRI Agricultural Economics Division, 'Adoption rate (%) of BRRI released Aus/Aman/Boro rice varieties in
            Bangladesh over the years' (3 pages, one per season; PDF modified 2025-06-30). Percent of the national seasonal
            rice area under each BRRI variety, 1990-91 to 2023-24. Footnote: 'Source: Sample survey, Agricultural Economics
            Division, BRRI'. This is a BRRI survey, not a DAE census, and it gives shares, not hectares.
        02_raw/dae/bina_aed_area_coverage_2022_23_bjnag37_2.pdf   (Rahman et al. 2023, Bangladesh J. Nuclear Agric.
            37(2):89-107, Table 1, p.93): hectares under each BINA rice variety, 2022-23, from DAE district offices
            (Deputy Directors of the 64 districts); 'Source: DAE data, 2022-23 and BBS, 2022'.
        02_raw/dae/bina_aed_area_coverage_2023_24_bjnag38_2.pdf   (Rahman et al. 2024, 38(2):97-110, Table 1, p.100):
            the same for 2023-24, with the BBS seasonal totals used as denominators.
        05_output/final/bgd_rice_varieties.csv (register; every variety_id written must exist there)
Output  05_output/final/bgd_variety_area.csv: one row per (variety, season, year, source).

Run: python scripts/build_variety_area.py

Rules
- Values are copied as printed. Shares are never converted to hectares and hectares are never re-derived from shares.
  area_ha is filled only where the source prints hectares (the BINA tables); area_share_pct is the printed percent of the
  national seasonal rice area (both sources).
- The BRRI PDF is a table whose blank cells are dropped by the text layer, so each number is placed in its year column by
  its horizontal position (centre within 9 pt of a header centre), never by its order in the line.
- Boro page header: the first column is printed '2022-24' (read as 2023-24, as on the Aus and Aman pages) and no column
  is printed for 2021-22 (the third column is printed '2020-21'). Years are kept as printed apart from the first column;
  every Boro row carries a flag saying so. See 06_validation/dae_area_search.md.
- A printed number is flagged and its share left blank when it has no decimal point and is more than five times both of
  its printed neighbours (one case: BRRI dhan63, Boro, printed '70' between 1.07 and 0.16).
- Aggregate rows ('All BRRI Varieties', 'Others BRRI Varieties', BINA subtotals and totals) are not written.
"""
import pathlib
import re
import sys

import pandas as pd
import pdfplumber

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_keys import make_key  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
F = ROOT / "05_output/final"
BRRI_PDF = "02_raw/brri/brri_db_adoption_rate_brri_varieties.pdf"
BINA = [("02_raw/dae/bina_aed_area_coverage_2022_23_bjnag37_2.pdf", "2022-23", 5,
         "Rahman MH, Sarkar MMA, Haque MR, Islam S (2023). Area coverage of BINA developed rice, pulse, oilseed and "
         "horticultural crop varieties in Bangladesh. Bangladesh J. Nuclear Agric. 37(2):89-107. doi:10.3329/bjnag.v37i2.71784",
         "Table 1. Variety wise area coverage of BINA developed rice varieties in 2022-23"),
        ("02_raw/dae/bina_aed_area_coverage_2023_24_bjnag38_2.pdf", "2023-24", 4,
         "Rahman MH, Sarkar MMA, Haque MR, Islam S (2024). Area coverage of BINA developed rice, pulse, oilseed and "
         "horticultural crop varieties in Bangladesh. Bangladesh J. Nuclear Agric. 38(2):97-110. doi:10.3329/bjnag.v38i2.79581",
         "Table 1. Variety-wise area coverage of BINA developed rice varieties in 2023-24")]
BRRI_CITE = ("BRRI Agricultural Economics Division. Adoption rate (%) of BRRI released Aus, Aman and Boro rice varieties in "
             "Bangladesh over the years. BRRI 'Rice database' page, PDF dated 2025-06-30.")
SEASONS = ["Aus", "Aman", "Boro"]           # page order of the BRRI PDF
BINA_SEASONS = ["Boro", "Aus", "Aman"]      # block order of the BINA tables (closed by 'Subtotal' lines)
COLS = ["variety_id", "variety_name_source", "season", "year", "area_ha", "area_share_pct", "season_total_ha",
        "geography", "measure", "data_origin", "value_printed", "flag", "source_file", "source_page", "source_table",
        "source_citation"]
NUM = re.compile(r"^\d+(?:\.\d+)?$")


def vid(name):
    k = make_key(name)
    return f"RICE-{k}" if k else ""


def _rows(words, tol=2.5):
    rows = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if rows and abs(w["top"] - rows[-1][0]["top"]) <= tol:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w["x0"]) for r in rows]


def _header(page, ncut=74):
    """Year labels and column centres from the header band (two text lines: 'YYYY-' over 'YY').
    Aus and Aman pages: whole words. Boro page: the text layer splits the header into single characters, which are
    grouped by horizontal gaps instead."""
    ws = [w for w in page.extract_words(x_tolerance=1) if 60 < w["top"] < 90 and w["x0"] > 90]
    first = [w for w in ws if re.match(r"^\d{4}-$", w["text"])]
    if len(first) >= 25:
        t0 = max(w["top"] for w in first)
        second = [w for w in ws if re.match(r"^\d{2}$", w["text"]) and t0 < w["top"] < t0 + 10]
        out = []
        for w in first:
            s = min(second, key=lambda z: abs(z["x0"] - w["x0"]))
            out.append((w["text"] + s["text"], (w["x0"] + w["x1"]) / 2))
        return out
    cs = sorted((c for c in page.chars if 60 < c["top"] < ncut and c["x0"] > 90), key=lambda c: c["x0"])
    groups, cur = [], []
    for c in cs:
        if cur and c["x0"] - cur[-1]["x0"] > 6:
            groups.append(cur); cur = []
        cur.append(c)
    groups.append(cur)
    top0 = min(c["top"] for c in cs)
    out = []
    for g in groups:
        a = "".join(c["text"] for c in g if c["top"] < top0 + 2).rstrip("-")
        b = "".join(c["text"] for c in g if c["top"] >= top0 + 2)
        out.append((f"{a}-{b}", (min(c["x0"] for c in g) + max(c["x1"] for c in g)) / 2))
    return out


def brri_rows():
    out = []
    pdf = pdfplumber.open(ROOT / BRRI_PDF)
    for pno, (page, season) in enumerate(zip(pdf.pages, SEASONS), start=1):
        hdr = _header(page)
        words = page.extract_words(x_tolerance=1)
        hdr_bottom = max(w["bottom"] for w in words if w["top"] < 80 and w["x0"] > 90 and "-" in w["text"]) + 1
        flag_page = ""
        if season == "Boro":
            flag_page = ("Boro header prints the first column as '2022-24' (read as 2023-24) and has no 2021-22 column; "
                         "years after 2022-23 are as printed and may be shifted by one year")
        for row in _rows([w for w in words if w["top"] > hdr_bottom]):
            label = " ".join(w["text"] for w in row if w["x1"] < hdr[0][1] - 9)
            if not label or label.startswith(("Source", "NB", "All ", "Others")):
                continue
            vals = []
            for w in row:
                if w["x1"] < hdr[0][1] - 9:
                    continue
                t = w["text"]
                if not NUM.match(t):
                    raise SystemExit(f"p{pno} {label}: unparsed token {t!r}")
                cx = (w["x0"] + w["x1"]) / 2
                j = min(range(len(hdr)), key=lambda i: abs(hdr[i][1] - cx))
                if abs(hdr[j][1] - cx) > 9:
                    raise SystemExit(f"p{pno} {label}: {t} at x={cx:.0f} matches no column")
                vals.append((j, t))
            if len(set(j for j, _ in vals)) != len(vals):
                raise SystemExit(f"p{pno} {label}: two numbers in one column")
            v = vid(label)
            if not v:
                raise SystemExit(f"p{pno}: no key for {label!r}")
            nums = {j: float(t) for j, t in vals}
            for j, t in vals:
                year = hdr[j][0]
                if season == "Boro" and j == 0 and year == "2022-24":
                    year = "2023-24"
                flag = flag_page
                share = nums[j]
                nb = [nums[i] for i in (j - 1, j + 1) if i in nums]
                if "." not in t and share > 1 and nb and all(share > 5 * max(n, 0.01) for n in nb):
                    flag = "; ".join(x for x in [flag, f"printed '{t}' is out of line with neighbours {nb}; share left blank"] if x)
                    share = None
                out.append({"variety_id": v, "variety_name_source": label, "season": season, "year": year,
                            "area_ha": None, "area_share_pct": share, "season_total_ha": None, "geography": "Bangladesh",
                            "measure": "percent of national seasonal rice area",
                            "data_origin": "BRRI Agricultural Economics Division sample survey",
                            "value_printed": t, "flag": flag, "source_file": BRRI_PDF, "source_page": pno,
                            "source_table": f"Adoption rate (%) of BRRI released {season} rice varieties in Bangladesh over the years",
                            "source_citation": BRRI_CITE})
    return out


VAR = re.compile(r"(Binadhan-\d+|BINA dhan\d+|Iratom-\d+|Binashail)\s+([\d,]+)\s+([\d.]+)\s+([\d.]+)")
TOT = re.compile(r"^(Boro|Aus|Aman)\s+(\d{6,})")


def bina_rows():
    out = []
    for rel, year, pno, cite, table in BINA:
        text = pdfplumber.open(ROOT / rel).pages[pno - 1].extract_text()
        start = text.index("Table 1.")
        block = text[start:text.index("Source:", start)]
        season_i, totals, rows = 0, {}, []
        for line in block.splitlines():
            m = TOT.match(line.strip())
            if m:
                totals[m.group(1)] = int(m.group(2))
            if re.match(r"^(Subtotal|Sub-total)\b", line.strip()):
                season_i += 1
                continue
            m = VAR.search(line)
            if m:
                rows.append((BINA_SEASONS[season_i], m))
        # 2023-24 prints the BBS seasonal totals in a column of their own (Boro, Aus, Aman, then the grand total and the BINA total);
        # the Aman figure sits on its own line, so the totals are read in order rather than from the season label.
        big = re.findall(r"(?<![\d,.])(\d{7,8})(?![\d.])", block)
        if len(big) >= 4:
            totals = dict(zip(BINA_SEASONS, map(int, big[:3])))
        if season_i != 3:
            raise SystemExit(f"{rel}: expected 3 season subtotals, found {season_i}")
        for season, m in rows:
            name, ha, adopt, cov = m.groups()
            v = vid(name)
            if not v:
                raise SystemExit(f"{rel}: no key for {name!r}")
            flag = ""
            if year == "2022-23" and name == "Binadhan-24":
                flag = ("printed shares (0.34, 0.07) repeat the Binadhan-18 line and do not match 2,740 ha; "
                        "area_ha is as printed")
            out.append({"variety_id": v, "variety_name_source": name, "season": season, "year": year,
                        "area_ha": int(ha.replace(",", "")), "area_share_pct": float(cov),
                        "season_total_ha": totals.get(season), "geography": "Bangladesh",
                        "measure": "hectares, and percent of national seasonal rice area",
                        "data_origin": "DAE district offices (64 districts), compiled by BINA Agricultural Economics Division",
                        "value_printed": f"{ha} ha; {adopt}% of BINA rice area; {cov}% of seasonal rice area",
                        "flag": flag, "source_file": rel, "source_page": pno,
                        "source_table": f"{table} (printed page {pno + (88 if year == '2022-23' else 96)})", "source_citation": cite})
    return out


def main():
    df = pd.DataFrame(brri_rows() + bina_rows(), columns=COLS)
    reg = set(pd.read_csv(F / "bgd_rice_varieties.csv", dtype=str, keep_default_na=False).variety_id)
    missing = sorted(set(df.variety_id) - reg)
    if missing:
        raise SystemExit(f"variety_id not in register: {missing}")
    key = ["variety_id", "season", "year", "source_file"]
    if df.duplicated(key).any():
        raise SystemExit(f"duplicate rows: {df[df.duplicated(key, keep=False)][key].values.tolist()}")
    for c in ["area_ha", "season_total_ha", "source_page"]:
        df[c] = df[c].astype("Int64")
    df = df.sort_values(["variety_id", "season", "year", "source_file"]).reset_index(drop=True)
    df.to_csv(F / "bgd_variety_area.csv", index=False, encoding="utf-8-sig")
    print(f"bgd_variety_area.csv: {len(df)} rows, {df.variety_id.nunique()} varieties; "
          f"by source: {df.groupby('data_origin').size().to_dict()}")


if __name__ == "__main__":
    main()
