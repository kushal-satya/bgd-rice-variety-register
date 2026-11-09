"""L2: extract every table/field from the CGIAR-specific sources into 03_extracted/tables/ and write
04_working/evidence_L2.csv. Re-runnable; reads only files already in 02_raw (manifest).

Sources
  L2-S01 CGSpace 10568/164332  Biswas et al. 2021 GR2E BRRI dhan29 Golden Rice (Front. Plant Sci.)
  L2-S02 CGSpace 10568/126480  Sarkar et al. 2022 Adoption determinants of exotic rice cultivars (Front. SFS)
  L2-S03 CGSpace 10568/106031  Akhter et al. 2019 Rice diversity and the joy of Eid (UBINIG/Bioversity brief)
  L2-S04 SPIA/ISPC Brief 71 (2018) short-duration rice (BD56) Bangladesh
  L2-S05 J. Exp. Bot. erag452 (2026) Hussain et al. (IRRI) flood tolerance review: metadata only
  L2-S06 GloMIP product catalog (rice; Bangladesh rows) + L2-S07 GloMIP market segments
  L2-S08 ASTI data download, Bangladesh, all indicators
  L2-S09a-d ASTI-BARC Bangladesh publications (CB34 2006, Note 2011, Factsheet 2014, Country Brief 2019)
  L2-S10 ASTI-hosted CGIAR-TRIVSA rice dataset (Bangladesh rows)
"""
import csv, json, re, sys, html, pathlib, zipfile, io, glob, collections
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_keys import make_key
import fitz, pdfplumber, openpyxl
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "02_raw"; CS = RAW / "cgiar_specific"
TAB = ROOT / "03_extracted/tables"; TAB.mkdir(parents=True, exist_ok=True)
WK = ROOT / "04_working"
EVH = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file", "page",
       "locator", "method", "validation", "confidence", "notes"]
EV = []
COUNTS = collections.OrderedDict()


def rel(p):
    return str(pathlib.Path(p).resolve().relative_to(ROOT)).replace("\\", "/")


def wcsv(name, header, rows):
    p = TAB / name
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(header)
        for r in rows:
            w.writerow(["" if v is None else v for v in r])
    COUNTS[name] = (len(rows), len(header))
    return p


def words25(s):
    s = re.sub(r"\s+", " ", str(s)).strip()
    w = s.split(" ")
    return " ".join(w[:25])


def ev(key, field, value, value_raw, src, page="", locator="", method="pdf_text", validation="unvalidated",
       confidence="high", notes="", lf=""):
    S = SRC[src]
    EV.append({"pilot_key": key, "field": field, "value": value, "value_raw": words25(value_raw) if value_raw else "",
               "source_id": src, "source_title": S["title"], "authority_rank": S["rank"], "local_file": lf or S["file"],
               "page": page, "locator": words25(locator), "method": method, "validation": validation,
               "confidence": confidence, "notes": notes})


def url_row(key, src, raw_name, page="", locator="", method="pdf_text"):
    ev(key, "cgiar_source_url", SRC[src]["url"], raw_name, src, page, locator or raw_name, method,
       notes="variety mentioned in this CGIAR source")


def key_of(name):
    """make_key on a variety-name cell, plus the documented manual cases (decisions_L2.md)."""
    n = str(name).strip()
    k = make_key(n)
    if k:
        return k, ""
    m = re.match(r"^BRRI[-\s]?(\d+)$", n, re.I)          # 'BRRI-28', 'BRRI 34' (UBINIG brief)
    if m:
        return make_key(f"BRRI dhan{m.group(1)}"), "manual: 'BRRI-<n>' read as BRRI dhan<n>"
    if re.fullmatch(r"BD\s?(\d+)", n):                     # SPIA brief 'BD56', 'BD51'
        k2 = make_key("BRRI dhan" + re.sub(r"\D", "", n))
        return k2, "manual: SPIA brief abbreviation BD<n> = BRRI dhan<n> (brief text: 'BRRI Dhan 56' ... 'the BD56 variety')"
    manual = {"hira-2": "HYB_HIRA2", "pajam": "OLD_PAJAM", "bau 63": "OLD_BAU63", "purbachi": "OLD_PURBACHI"}
    if n.lower() in manual:
        return manual[n.lower()], "manual: crosswalk (hybrid_key_crosswalk / key_crosswalk_other)"
    return "UNMATCHED", ""


SRC = {
    "L2-S01": dict(title="Biswas et al. 2021, Development and field evaluation of near-isogenic lines of GR2-E BRRI dhan29 golden rice, Front. Plant Sci. 12:619739 (CGSpace 10568/164332)",
                   rank="4_cgiar_record", file="02_raw/cgiar_specific/cgspace_gr2e_brri_dhan29/PMC7947304_fullText.xml",
                   url="https://cgspace.cgiar.org/items/ee9e7073-e49c-4d12-a703-a3102966741e"),
    "L2-S02": dict(title="Sarkar et al. 2022, Adoption determinants of exotic rice cultivars in Bangladesh, Front. Sustain. Food Syst. 6:813933 (CGSpace 10568/126480)",
                   rank="4_cgiar_record", file="02_raw/cgiar_specific/cgspace_exotic_adoption/ORIGINAL/article.pdf",
                   url="https://cgspace.cgiar.org/items/ce70f984-8ed1-43e5-82c8-299cf2326083"),
    "L2-S02s": dict(title="Sarkar et al. 2022, Supplementary Material (Data_Sheet_1.pdf), Front. Sustain. Food Syst. 6:813933",
                    rank="4_cgiar_record", file="02_raw/cgiar_specific/cgspace_exotic_adoption/supplementary/Data_Sheet_1.pdf",
                    url="https://cgspace.cgiar.org/items/ce70f984-8ed1-43e5-82c8-299cf2326083"),
    "L2-S03": dict(title="Akhter et al. 2019, Rice diversity and the joy of Eid, Bioversity International/UBINIG brief (CGSpace 10568/106031)",
                   rank="4_cgiar_record", file="02_raw/cgiar_specific/cgspace_ubinig_brief/ORIGINAL/UBINIG_brief_FINAL_FOR_WEB.pdf",
                   url="https://cgspace.cgiar.org/server/api/core/bitstreams/96056a86-e517-4444-b07c-a79ff13f9425/content"),
    "L2-S04": dict(title="SPIA/ISPC Brief 71 (Sept 2018), From Green Revolution to Agricultural Transformation: short duration rice varieties in Bangladesh",
                   rank="4_cgiar_record", file="02_raw/cgiar_specific/ispc_brief71/ispc_brief_71_rice_bangladesh.pdf",
                   url="https://iaes.cgiar.org/sites/default/files/pdf/ispc_brief_71_rice_bangladesh.pdf"),
    "L2-S05": dict(title="Hussain, Anumalla, Zhang, Ismail 2026, Translating flood-tolerance biology into breeding: a five-dimensional framework, J. Exp. Bot. erag452",
                   rank="5_peer_reviewed", file="02_raw/cgiar_specific/jxb_erag452/europepmc_core.json",
                   url="https://doi.org/10.1093/jxb/erag452"),
    "L2-S06": dict(title="CGIAR GloMIP Product Catalog (rice), Bangladesh rows, accessed 2026-10-07",
                   rank="4_cgiar_record", file="02_raw/cgiar_specific/glomip/product-catalog_list_all.json",
                   url="https://glomip.cgiar.org/product-catalog"),
    "L2-S07": dict(title="CGIAR GloMIP Seed Product Market Segments, accessed 2026-10-07",
                   rank="4_cgiar_record", file="02_raw/cgiar_specific/glomip/market-segments_list_all.json",
                   url="https://glomip.cgiar.org/market-segments"),
    "L2-S09d": dict(title="ASTI-BARC Country Brief Bangladesh 2019 (Agricultural R&D Indicators, IFPRI/APAARI)",
                    rank="4_cgiar_record", file="02_raw/cgiar_specific/asti/pubs/bangladesh-country-note-2019__Bangladesh-CountryBrief-2019.pdf",
                    url="https://www.asti.cgiar.org/publications/bangladesh-country-note-2019"),
    "L2-S10": dict(title="CGIAR-TRIVSA rice dataset (TRIVSA-Rice-Data.xlsx) hosted by ASTI, Bangladesh rows",
                   rank="4_cgiar_record", file="02_raw/asti_trivsa/TRIVSA-Rice-Data.xlsx",
                   url="https://www.asti.cgiar.org/sites/default/files/trivsa/TRIVSA-Rice-Data.xlsx"),
}


# ------------------------------------------------------------------ generic helpers
def pdf_text_rows(pdf_path):
    rows = []
    d = fitz.open(pdf_path)
    for i, p in enumerate(d):
        for j, line in enumerate(p.get_text().splitlines()):
            if line.strip():
                rows.append([i + 1, j + 1, line])
    return rows


def pdf_layout_rows(pdf_path):
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, p in enumerate(pdf.pages):
            for j, line in enumerate((p.extract_text(layout=True) or "").splitlines()):
                if line.strip():
                    rows.append([i + 1, j + 1, line.rstrip()])
    return rows


def pdfplumber_tables(pdf_path):
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, p in enumerate(pdf.pages):
            for t, tab in enumerate(p.extract_tables()):
                for r, row in enumerate(tab):
                    for c, cell in enumerate(row):
                        rows.append([i + 1, t + 1, r + 1, c + 1, (cell or "").replace("\n", " ")])
    return rows


def dspace_metadata_rows(item_json):
    j = json.loads(pathlib.Path(item_json).read_text(encoding="utf-8"))
    rows = [["_uuid", j.get("uuid"), "", "", ""], ["_handle", j.get("handle"), "", "", ""],
            ["_name", j.get("name"), "", "", ""], ["_lastModified", j.get("lastModified"), "", "", ""],
            ["_inArchive", j.get("inArchive"), "", "", ""], ["_withdrawn", j.get("withdrawn"), "", "", ""]]
    for k, vals in j["metadata"].items():
        for v in vals:
            rows.append([k, v.get("value"), v.get("language"), v.get("authority"), v.get("place")])
    return rows


def bitstream_rows(folder):
    rows = []
    for f in sorted(glob.glob(str(folder / "bundle_*_bitstreams.json"))):
        j = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        bundle = pathlib.Path(f).name.split("_")[1]
        for s in j["_embedded"]["bitstreams"]:
            rows.append([bundle, s.get("name"), s.get("uuid"), s.get("sizeBytes"),
                         (s.get("checkSum") or {}).get("value"), s.get("sequenceId"),
                         s["_links"]["content"]["href"]])
    return rows


def docx_tables(data):
    """Return [(table_no,row,col,text)] from .docx bytes (no python-docx dependency)."""
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    z = zipfile.ZipFile(io.BytesIO(data))
    root = ET.fromstring(z.read("word/document.xml"))
    out = []
    for t, tbl in enumerate(root.iter("{%s}tbl" % ns["w"])):
        for r, tr in enumerate(tbl.findall("w:tr", ns)):
            for c, tc in enumerate(tr.findall("w:tc", ns)):
                txt = " ".join("".join(x.text or "" for x in p.iter("{%s}t" % ns["w"])) for p in tc.findall(".//w:p", ns))
                out.append([t + 1, r + 1, c + 1, re.sub(r"\s+", " ", txt).strip()])
    return out


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def html_rows(s):
    """Rows of cell texts from an HTML fragment of <tr><td>..."""
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", s or "", re.S):
        out.append([strip_tags(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)])
    return out


# ================================================================== L2-S01 GR2E BRRI dhan29 (CGSpace item, no files)
def s01():
    base = CS / "cgspace_gr2e_brri_dhan29"
    wcsv("cgspace_gr2e_brri_dhan29_metadata.csv", ["field", "value", "language", "authority", "place"],
         dspace_metadata_rows(base / "item.json"))
    root = ET.parse(base / "PMC7947304_fullText.xml").getroot()
    txt = lambda e: re.sub(r"\s+", " ", "".join(e.itertext())).strip()
    rows = []
    for tw in root.iter("table-wrap"):
        tid = tw.get("id"); cap = txt(tw.find("caption")) if tw.find("caption") is not None else ""
        for r, tr in enumerate(tw.iter("tr")):
            for c, cell in enumerate(tr):
                rows.append([tid, cap, r + 1, c + 1, cell.tag, txt(cell)])
    wcsv("cgspace_gr2e_brri_dhan29_tables.csv", ["table_id", "caption", "row", "col", "cell_tag", "text"], rows)
    # sections / paragraphs (all text)
    prow = []
    for k, sec in enumerate(root.iter("sec")):
        title = sec.find("title"); title = txt(title) if title is not None else ""
        for j, p in enumerate(sec.findall("p")):
            prow.append([k + 1, title, j + 1, txt(p)])
    ab = root.find(".//abstract")
    prow.insert(0, [0, "Abstract", 1, txt(ab)])
    wcsv("cgspace_gr2e_brri_dhan29_text.csv", ["section_no", "section_title", "para_no", "text"], prow)
    # supplementary docx tables
    z = zipfile.ZipFile(base / "PMC7947304_supplementary.zip")
    srows = []
    for n in z.namelist():
        if n.lower().endswith(".docx"):
            for t, r, c, x in docx_tables(z.read(n)):
                srows.append([n, t, r, c, x])
    wcsv("cgspace_gr2e_brri_dhan29_supp_tables.csv", ["file_in_zip", "table_no", "row", "col", "text"], srows)
    # evidence
    src = "L2-S01"; m = "api_json"
    q1 = "a widely grown rice variety, BRRI dhan29, which covers around 26.1% of the irrigated rice area (4.901 Mha) of Bangladesh in the dry season."
    ev("BRRI_DHAN29", "adoption", "26.1% of irrigated (Boro, dry-season) rice area, ca. 4.901 Mha (citing BRRI 2019; BBS 2020)", q1, src,
       "", "Abstract", "html", notes="secondary figure cited by the article; Europe PMC JATS XML of PMC7947304")
    ev("BRRI_DHAN29", "key_traits", "yields 7-8 t/ha under optimum management in Boro (Nov-May)",
       "It yields 7–8 t/ha under optimum management conditions in the Boro season (November to May).", src, "", "Introduction", "html")
    ev("BRRI_DHAN29", "cgiar_independent",
       "CGSpace/Biswas 2021: IRRI used BRRI dhan29 as recurrent parent to introgress the GR2E Golden Rice event (MABC at IRRI 2008-2014); a CGIAR use of the variety, not a claim that IRRI bred BRRI dhan29",
       "The introgression work was done at IRRI, Philippines during 2008–2014.", src, "", "Materials and Methods", "html",
       confidence="high", notes="attribution concerns the GR2E derivative, not BRRI dhan29 itself; mention only for BRRI dhan29")
    url_row("BRRI_DHAN29", src, "BRRI dhan29", locator="Abstract", method="html")
    ev("UNMATCHED", "breeding_line", "IR 112060 GR 2-E:2-7-63-2-96 (GR2E BRRI dhan29 Golden Rice, lead line)",
       "IR 112060 GR 2-E:2-7-63-2-96 was finally selected for further advancement.", src, "", "Discussion", "html",
       notes="transgenic NIL of BRRI dhan29; article says lead lines need open-field evaluation 'before deciding for commercial cultivation'; no release stated")
    ev("UNMATCHED", "cgiar_independent",
       "CGSpace/Biswas 2021: GR2E BRRI dhan29 Golden Rice NILs developed by IRRI-BRRI (crosses and backcrossing at IRRI; trials at BRRI); IRRI designations IR 112060/112062/112064",
       "BRRI dhan29 was crossed with GR2E Golden Rice (IR-∅∅GR2E-5), and the resulting F1 progenies were crossed further with BRRI dhan29", src, "", "Methods", "html",
       notes="not an approved variety in any source read by L2")
    for nm, k in [("BR11", "BR11"), ("BRRI dhan28", "BRRI_DHAN28")]:
        url_row(k, src, nm, locator="Introduction: 'some rice varieties like BR11, BRRI dhan28, and BRRI dhan29 are very popular'", method="html")


# ================================================================== L2-S02 exotic cultivars adoption
def s02():
    base = CS / "cgspace_exotic_adoption"
    wcsv("cgspace_exotic_adoption_metadata.csv", ["field", "value", "language", "authority", "place"], dspace_metadata_rows(base / "item.json"))
    wcsv("cgspace_exotic_adoption_bitstreams.csv", ["bundle", "name", "uuid", "sizeBytes", "md5", "sequenceId", "content_url"], bitstream_rows(base))
    art = base / "ORIGINAL/article.pdf"; sup = base / "supplementary/Data_Sheet_1.pdf"
    wcsv("cgspace_exotic_adoption_article_text.csv", ["page", "line", "text"], pdf_text_rows(art))
    wcsv("cgspace_exotic_adoption_supp_text.csv", ["page", "line", "text"], pdf_text_rows(sup))
    # curated tables (text-born; typed from the PDF text layer)
    t1 = [["Adoption intensity", "Adoption percentage of exotic varieties", 0.52, 0.69, 1, 0],
          ["Age", "Age of the rice grower (year)", 43.41, 0.21, 57, 22],
          ["Education", "Education of the household head (year)", 7.41, 0.58, 16, 0],
          ["Occupation", "Dummy: 1 = if only farming, 0 = Otherwise", 0.39, 1.24, 1, 0],
          ["Household size", "Number of household members", 4.58, 0.19, 7, 3],
          ["Family labor", "Number of family member engaged in farming", 2.21, 0.37, 4, 1],
          ["Farm size", "Dummy: 1 = small farm, 0 = Otherwise", 0.35, 1.38, 1, 0],
          ["Land type", "Dummy: 1 = if household has own land, 0 = otherwise", 0.39, 1.26, 1, 0],
          ["Training", "Dummy: 1 = Farmers received rice production training, 0 = Otherwise", 0.33, 1.43, 1, 0],
          ["Distance to extension office", "Distance from house to Upazila Agriculture Office (km)", 8.68, 0.56, 16, 0.50],
          ["Distance to market", "Distance from house to local market (km)", 0.96, 0.78, 4, 0.10],
          ["Yield difference", "Yield of exotic rice varieties over domestic (t/ha)", 0.48, 5.74, 5.91, -4.50],
          ["Price differences", "Price of exotic rice varieties over domestic varieties (US$/quintal)", 0.44, 27.88, 25.66, -22.03],
          ["Cultivated varieties", "Number of cultivated rice varieties per farm", 1.69, 0.45, 4, 1],
          ["Weather condition", "Dummy: 1 = Good weather, 0 = Otherwise", 0.47, 1.07, 1, 0],
          ["SD of yield difference", "Standard deviation of exotic and domestic rice varieties yields differences", 0.12, 2.20, 0.66, -0.11],
          ["Received market price information", "Dummy: 1 = Yes, 0 = Otherwise", 0.38, 1.26, 1, 0]]
    wcsv("cgspace_exotic_adoption_table1_descriptives.csv", ["variable", "description", "mean", "cv", "max", "min"], t1)
    t3 = [["Human labor (man-day/ha)", 67, 60, 73, 78], ["Hired", 52, 49, 58, 60], ["Family", 15, 11, 15, 18],
          ["Seed (kg/ha)", 36, 39, 36, 38], ["Fertilizer (kg/ha)", 442, 394, 517, 533], ["Urea", 179, 171, 176, 181],
          ["TSP", 82, 72, 82, 79], ["MoP", 95, 77, 124, 132], ["DAP", 33, 26, 52, 66], ["Gypsum", 49, 41, 72, 69],
          ["ZnSO4", 3, 3, 7, 3], ["Theovit", 1, 4, 2, 1], ["Boron", "-", "-", 2, 2]]
    wcsv("cgspace_exotic_adoption_table3_inputs.csv", ["input_item", "wet_domestic", "wet_exotic", "dry_domestic", "dry_exotic"], t3)
    t4 = [["Availability", "Insufficient and delay seed supply", 58.00, 1], ["Connectivity", "Inadequate information", 56.25, 2],
          ["Confidence", "Uncertainty about yield, pests and diseases, and market demand", 43.08, 3],
          ["Connectivity", "Poor communication among research, extension, and farmers", 40.17, 4],
          ["Accessibility", "Lack of farmer demonstration", 31.58, 5], ["Connectivity", "Delay in sharing feedback on demonstrated varieties", 15.50, 6]]
    wcsv("cgspace_exotic_adoption_table4_slow_adoption.csv", ["group", "reason", "responses_pct", "rank"], t4)
    t5 = [["Age", "0.006* (0.003)", "0.008** (0.004)", "0.001ns (0.003)", "0.001ns (0.003)"],
          ["Education", "−0.019** (0.007)", "−0.028*** (0.009)", "−0.039*** (0.013)", "−0.039*** (0.014)"],
          ["Occupation", "−0.285*** (0.061)", "−0.382*** (0.078)", "−0.201*** (0.057)", "−0.201*** (0.058)"],
          ["Household size", "−0.017ns (0.036)", "−0.008ns (0.045)", "−0.011ns (0.033)", "−0.011ns (0.033)"],
          ["Family labor", "−0.048ns (0.037)", "−0.092* (0.047)", "−0.028* (0.015)", "−0.028* (0.016)"],
          ["Farm size", "0.922*** (0.116)", "1.435*** (0.118)", "0.028ns (0.157)", "0.029ns (0.170)"],
          ["Land type", "0.189*** (0.046)", "−0.180*** (0.058)", "0.025ns (0.055)", "0.025ns (0.057)"],
          ["Training received", "−0.265*** (0.073)", "−0.781*** (0.087)", "−0.300*** (0.092)", "−0.300*** (0.097)"],
          ["Distance to extension office", "−0.016** (0.007)", "−0.057*** (0.009)", "0.016** (0.007)", "0.016** (0.007)"],
          ["Distance to market", "−0.088ns (0.100)", "−0.536*** (0.107)", "−0.583*** (0.103)", "−0.583*** (0.108)"],
          ["Yield difference", "0.537*** (0.039)", "–", "1.354*** (0.214)", "1.354*** (0.238)"],
          ["Price differences", "0.101*** (0.010)", "–", "0.167*** (0.013)", "0.167*** (0.013)"],
          ["Cultivated varieties", "−0.030ns (0.043)", "−0.058ns (0.050)", "0.052ns (0.042)", "0.052ns (0.043)"],
          ["Weather condition", "−0.525*** (0.061)", "1.502*** (0.075)", "−0.929*** (0.179)", "−0.929*** (0.187)"],
          ["Constant", "−0.612** (0.302)", "−1.015** (0.341)", "−1.149*** (0.403)", "−1.149*** (0.433)"],
          ["Residual of yield difference from 1st stage", "-", "-", "−0.975*** (0.220)", "−0.975*** (0.242)"],
          ["Residual of price difference from 1st stage", "-", "-", "−0.087*** (0.008)", "−0.087*** (0.008)"],
          ["Goodness of fit, Wald chi2", "2285.02***", "1414.58***", "-", "-"], ["Pseudo R2", "0.418", "0.272", "-", "-"],
          ["Log Pseudolikelihood", "−507.340", "−635.158", "−351.202", "−351.202"],
          ["Wald test for endogeneity (yield residual)", "-", "-", "19.62***", "16.23***"],
          ["Wald test for endogeneity (price residual)", "-", "-", "109.62***", "107.75***"],
          ["Wald test for endogeneity (joint)", "-", "-", "137.47***", "136.96***"],
          ["Instrument relevance F (yield difference)", "-", "-", "210.03***", "210.03***"],
          ["Instrument relevance F (price difference)", "-", "-", "19.05***", "19.05***"],
          ["AIC", "1044.680", "1296.316", "0.584", "0.584"], ["BIC", "1121.763", "1363.121", "−8772.585", "−8772.585"],
          ["Bootstrap replication", "-", "-", "-", "1,000"], ["Number of observations", "1,260", "1,260", "1,260", "1,260"]]
    wcsv("cgspace_exotic_adoption_table5_regression.csv", ["variable", "model_I", "model_II", "model_III", "model_IV"], t5)
    st5 = [["Age", "0.001*", "0.001**", "0.0002ns", "0.0002ns"], ["Education", "-0.003**", "-0.005***", "-0.005***", "-0.005***"],
           ["Occupation", "-0.039***", "-0.063***", "-0.027***", "-0.027***"], ["Household size", "-0.002ns", "-0.001ns", "-0.001ns", "-0.001ns"],
           ["Family labor", "-0.006ns", "-0.015*", "-0.004*", "-0.004*"], ["Farm size", "0.125***", "0.237***", "0.004ns", "0.004ns"],
           ["Land type", "0.026***", "-0.030***", "0.003ns", "0.003ns"], ["Training received", "-0.036***", "-0.129***", "-0.040***", "-0.040***"],
           ["Distance to extension office", "-0.002**", "-0.009***", "0.002**", "0.002**"], ["Distance to market", "-0.012ns", "-0.089***", "-0.078***", "-0.078***"],
           ["Yield difference", "0.073***", "-", "0.182***", "0.182***"], ["Price differences", "0.014***", "-", "0.022***", "0.022***"],
           ["Cultivated varieties", "-0.004ns", "-0.010ns", "0.007ns", "0.007ns"], ["Weather condition", "-0.071***", "0.249***", "-0.125***", "-0.125***"]]
    wcsv("cgspace_exotic_adoption_supp_table5_marginal_effects.csv", ["variable", "model_I", "model_II", "model_III", "model_IV"], st5)
    st1 = [["Rangpur", "Badarganj", "Ramnathpur, Madhupur"], ["Rangpur", "Gangachora", "Gangachara, Alambiditor"], ["Rangpur", "Kaunia", "Tepamadhupur, Kursha"],
           ["Rangpur", "Metropoliton", "Metropoliton, Darshana"], ["Rangpur", "Mithapukur", "Ranipukur, Balarhat"], ["Rangpur", "Pirgacha", "Annadannagar, Pirgachha"],
           ["Rangpur", "Pirganj", "Bhendabari, Mithipur"], ["Rangpur", "Sadar", "Mominpur, Haridebpur"], ["Rangpur", "Taraganj", "Alampur, Kursha"],
           ["Bogura", "Sariakandi", "Kazla, Kamalpur"], ["Bogura", "Sonatala", "Sonatala, Balua"], ["Bogura", "Adamdighi", "Adamdighi, Nasaratpur"],
           ["Bogura", "Dhunat", "Nimgachi, Kalerpara"], ["Bogura", "Nandigram", "Nandigram, Bhatgram"], ["Bogura", "Bogura Sadar", "Rajapur, Gokul"],
           ["Bogura", "Sherpur", "Khanpur, Mirzapur"], ["Bogura", "Shajahanpur", "Amrul, Arai"], ["Bogura", "Gabtali", "Gabtali, Nasipur"],
           ["Bogura", "Shibganj", "Raynagar, Shibganj"], ["Bogura", "Kahaloo", "Paikar, Kahaloo"], ["Bogura", "Dhupchanchia", "Dhupchanchia, Talora"]]
    wcsv("cgspace_exotic_adoption_supp_table1_locations.csv", ["district", "upazila", "unions"], st1)
    st2 = [("Wet", "Domestic", "Inbred", v) for v in ["BR11", "BR22", "BR23", "BRRI dhan33", "BRRI dhan34", "BRRI dhan39", "BRRI dhan41", "BRRI dhan44",
                                                      "BRRI dhan49", "BRRI dhan51", "BRRI dhan52", "BRRI dhan56", "BRRI dhan57", "BRRI dhan62", "BRRI dhan66", "BRRI dhan72"]]
    st2 += [("Wet", "Domestic", "Hybrid", v) for v in ["ACI", "Dhanigold", "Hira-2"]]
    st2 += [("Wet", "Exotic", "", v) for v in ["Guti swarna", "Mamun swarna", "Ranjit Swarna", "Parija"]]
    st2 += [("Dry", "Domestic", "", v) for v in ["BRRI dhan28", "BRRI dhan29", "BRRI dhan36", "BRRI dhan50", "BRRI dhan55", "BRRI dhan58", "BRRI dhan59", "BRRI dhan61", "BRRI dhan63"]]
    st2 += [("Dry", "Exotic", "", v) for v in ["Zira", "Khato-10", "Moazzem zira", "Parija", "Sampa katari"]]
    wcsv("cgspace_exotic_adoption_supp_table2_cultivars.csv", ["season", "origin_type", "inbred_or_hybrid", "cultivar"], [list(r) for r in st2])
    s3h = ["trait", "BR11", "BRRI dhan49", "BRRI dhan52", "Guti swarna", "Ronjit swarna", "Mamun swarna"]
    s3 = [["Yield (t/ha)", "3.85", "4.40", "4.39", "4.58", "4.25", "4.33"], ["Plant height (cm)", "115", "100", "116", "95", "98", "92"],
          ["Growth duration (days)", "150-155", "135-140", "145-150", "140-145", "140-145", "135-140"],
          ["Lodging", "Lodging problem", "No lodging", "Lodging problem", "Lodging problem in low land", "No lodging", "Lodging problem"],
          ["Shattering", "No shattering", "No shattering", "No shattering", "No shattering", "No shattering", "No shattering"],
          ["Diseases", "Highly susceptible to sheath blight and bacterial blight", "Highly susceptible to false smut", "Susceptible to sheath blight",
           "Susceptible to sheath blight; Lower infestation of sheath rot", "Less infestation of sheath blight", "Less infestation"],
          ["Insect*", "Susceptible to BPH and leaf folder", "Susceptible to BPH; Rat attack due to early ripening", "Susceptible to BPH",
           "Less infestation of ear cutting caterpillar", "Less infestation", "Less infestation"],
          ["Resistance", "Panicle cannot exert properly due to cold and drought; Plant cannot survive up to 10 days under stagnant water at low land",
           "-", "Submerged up to 2 weeks", "Quick recovery capacity from any stress; Drought escaping", "-", "More rainfall during flowering stage caused grain sterility"],
          ["Grain size and shape", "Bold", "Medium slender", "Medium bold", "Medium bold", "Medium slender", "Medium slender"],
          ["Milling outturn (%)", "65.00", "61.25", "65.00", "70.00", "62.50", "62.50"],
          ["Straw quality", "Good", "Good", "Very good", "Good", "Very good", "Good"],
          ["Price (US$/quintal)", "24.72", "25.61", "22.03", "25.16", "22.63", "24.12"],
          ["Others", "Used to make puffed rice", "Good taste to eat for its Nazirshail type grain", "High tillering ability alongside the number of grain sterility is also high",
           "Erect flag leaf", "-", "-"]]
    wcsv("cgspace_exotic_adoption_supp_table3_wet_traits.csv", s3h, s3)
    s4h = ["trait", "BRRI dhan28", "BRRI dhan50", "BRRI dhan63", "Zira", "Moazzem Zira", "Sampa Katari"]
    s4 = [["Yield (t/ha)", "6.23", "6.08", "5.98", "6.56", "6.19", "6.15"], ["Plant height (cm)", "90", "82", "86", "77", "80", "75"],
          ["Growth duration (days)", "140-145", "155-160", "150-155", "150-155", "150-155", "155-160"],
          ["Lodging", "Lodging problem", "No lodging", "No lodging", "Lodging problem due to panicle weight and weak stem", "No lodging due to strong stem", "Lodging problem"],
          ["Shattering", "No shattering", "Shattering problem", "Shattering problem", "No shattering", "No shattering", "No shattering"],
          ["Diseases", "Highly susceptible to blast", "Highly susceptible to Neck blast", "Highly susceptible to blast", "Susceptible to blast",
           "Susceptible to blast", "Susceptible to blast and bacterial blight"],
          ["Insect*", "Susceptible to BPH", "Susceptible to BPH", "Less infestation", "Susceptible to BPH", "Less infestation", "Susceptible to BPH and leaf folder"],
          ["Grain size and shape", "Medium slender", "Long slender", "Long slender", "Long slender", "Long slender", "Short slender"],
          ["Milling outturn (%)", "62.50", "52.50", "61.00", "70.00", "65.00", "63.00"],
          ["Straw quality", "Good", "Very good", "Very good", "Good", "Good", "Good"],
          ["Price (US$/quintal)", "23.88", "25.07", "26.87", "28.36", "28.06", "28.66"],
          ["Others", "Good taste to eat and non-sticky", "Aroma, lower head rice percentage", "---", "Taste reduces if rice become cold",
           "Input intensive (fertilizer and irrigation)", "Non-sticky rice"]]
    wcsv("cgspace_exotic_adoption_supp_table4_dry_traits.csv", s4h, s4)
    # variety facts quoted in the article text (Figures 4-8 values given in prose)
    vf = [  # variety, season, metric, value, page, quote
        ("Dhanigold", "wet", "yield_t_ha", "5.45", 5, "the domestic hybrid Dhanigold (5.45 t/ha) has the highest yield"),
        ("Hira-2", "wet", "yield_t_ha", "5.05", 5, "followed by Hira-2 (5.05 t/ha)"),
        ("ACI", "wet", "yield_t_ha", "4.93", 5, "ACI (4.93 t/ha)"),
        ("Guti swarna", "wet", "yield_t_ha", "4.54", 5, "Guti swarna (4.54 t/ha)"),
        ("BRRI dhan49", "wet", "yield_t_ha", "4.41", 5, "BRRI dhan49 (4.41 t/ha)"),
        ("BRRI dhan52", "wet", "yield_t_ha", "4.38", 5, "BRRI dhan52 (4.38 t/ha)"),
        ("Guti swarna", "wet", "adoption_pct", "38.91", 5, "the exotic inbred Guti Swarna (38.91%) had the highest adoption rate"),
        ("BR11", "wet", "adoption_pct", "17.59", 5, "domestic varieties BR11 (17.59%)"),
        ("BRRI dhan52", "wet", "adoption_pct", "12.90", 5, "BRRI dhan52 (12.90%)"),
        ("BRRI dhan49", "wet", "adoption_pct", "5.19", 5, "BRRI dhan49 (5.19%)"),
        ("BR11", "wet", "yield_t_ha", "3.85", 5, "despite the yield was significantly lower at only 3.85 t/ha"),
        ("BRRI dhan29", "dry", "yield_t_ha", "6.90", 5, "BRRI dhan29 (6.90 t/ha) yielded the highest"),
        ("BRRI dhan58", "dry", "yield_t_ha", "6.71", 5, "followed by BRRI dhan58 (6.71 t/ha)"),
        ("Zira", "dry", "yield_t_ha", "6.57", 5, "Zira (6.57 t/ha)"),
        ("BRRI dhan28", "dry", "yield_t_ha", "6.24", 5, "BRRI dhan28 (6.24 t/ha)"),
        ("Moazzem zira", "dry", "yield_t_ha", "6.18", 5, "Moazzem zira (6.18 t/ha)"),
        ("Zira", "dry", "adoption_pct", "70.72", 5, "the exotic variety Zira (70.72%)"),
        ("BRRI dhan28", "dry", "adoption_pct", "15.16", 6, "domestic varieties BRRI dhan28 (15.16%)"),
        ("BRRI dhan29", "dry", "adoption_pct", "4.76", 6, "BRRI dhan29 (4.76%)"),
        ("Khato-10", "dry", "adoption_pct", "1.36", 6, "Khato-10 (1.36%)"),
        ("BRRI dhan58", "dry", "adoption_pct", "0.96", 6, "BRRI dhan58 (0.96%)"),
        ("BRRI dhan34", "wet", "price_usd_quintal", "43.50", 8, "domestic BRRI dhan34 was found to be the highest (43.50 US$/quintal)"),
        ("BRRI dhan49", "wet", "price_usd_quintal", "25.59", 8, "BRRI dhan49 (25.59 US$/quintal)"),
        ("Guti swarna", "wet", "price_usd_quintal", "25.15", 8, "Guti swarna (25.15 US$/quintal)"),
        ("BR11", "wet", "price_usd_quintal", "24.71", 8, "BR11 (24.71 US$/quintal)"),
        ("Mamun swarna", "wet", "price_usd_quintal", "24.13", 8, "Mamun swarna (24.13 US$/quintal)"),
        ("Sampa katari", "dry", "price_usd_quintal", "28.67", 9, "Sampa katari (28.67 US$/quintal)"),
        ("Zira", "dry", "price_usd_quintal", "28.35", 9, "Zira (28.35 US$/quintal)"),
        ("Moazzem zira", "dry", "price_usd_quintal", "28.07", 9, "Moazzem zira (28.07 US$/quintal)"),
        ("BRRI dhan63", "dry", "price_usd_quintal", "26.83", 9, "domestic rice varieties BRRI dhan63 (26.83 US$/quintal)"),
        ("BRRI dhan50", "dry", "price_usd_quintal", "25.09", 10, "BRRI dhan50 (25.09 US$/quintal)"),
        ("BRRI dhan28", "dry", "price_usd_quintal", "23.88", 10, "BRRI dhan28 (23.88 US$/quintal)"),
    ]
    wcsv("cgspace_exotic_adoption_variety_facts_text.csv", ["variety", "season", "metric", "value", "page", "quote"], [list(v) for v in vf])
    # evidence: per-variety facts (approved varieties keyed; others UNMATCHED)
    src = "L2-S02"
    note_area = "study-area figure (Rangpur wet season / Bogura dry season, field survey 2019-20, n=1,260), not national"
    for v, season, metric, val, pg, q in vf:
        k, kn = key_of(v)
        fld = "adoption" if metric == "adoption_pct" else "key_traits"
        lab = {"adoption_pct": "adoption rate %", "yield_t_ha": "yield t/ha", "price_usd_quintal": "farm-gate price US$/quintal"}[metric]
        ev(k, fld, f"{season} season {lab}: {val} ({note_area if metric=='adoption_pct' else 'field survey 2019-20'})", q, src, pg, q,
           notes="; ".join(x for x in [kn, f"raw name '{v}'" if k == "UNMATCHED" else "",
                                        "source calls this cultivar exotic" if v in ("Guti swarna", "Zira", "Khato-10", "Moazzem zira", "Mamun swarna", "Sampa katari") else "",
                                        "domestic hybrid; trade name not resolved to an MoA key" if v in ("ACI", "Dhanigold") else ""] if x))
    # supplementary table traits per approved variety
    for hdr, tab, season, pg in [(s3h, s3, "wet (Rangpur)", 2), (s4h, s4, "dry (Bogura)", 3)]:
        for ci, v in enumerate(hdr[1:], start=1):
            k, kn = key_of(v)
            if k == "UNMATCHED":
                continue   # exotic cultivars: kept in the table only
            traits = "; ".join(f"{r[0]}: {r[ci]}" for r in tab)
            ev(k, "key_traits", f"{season} 2019-20 farmer-survey traits: {traits}", f"{v} " + " ".join(r[ci] for r in tab[:3]), "L2-S02s", pg,
               f"Supplementary Table {'3' if pg == 2 else '4'}, column {v}", notes=kn)
    # named mentions -> cgiar_source_url (all supp table 2 cultivars + text mentions)
    seen = set()
    for season, o, t, v in st2:
        k, kn = key_of(v)
        if k != "UNMATCHED" and k not in seen:
            seen.add(k); url_row(k, src, v, page=1, locator="Supplementary Table 2", method="pdf_text")
    for k in ["BRRI_DHAN28", "BRRI_DHAN29"]:
        ev(k, "key_traits", "2016 severe blast of BRRI dhan28 and BRRI dhan29 caused significant yield loss in north and northwest; farmers then shifted to exotic varieties",
           "In 2016, a severe blast of the domestic mega rice varieties BRRI dhan28 and BRRI dhan29 caused significant yield loss", src, 5, "Results: Ten Years' Adoption Status")
    ev("BRRI_DHAN49", "local_name", "BR49, Pajam, Nazir (milled-rice brand names used by processors)",
       "rice processors were keen to supply milled BRRI dhan49 by the brand name of BR49, Pajam, and Nazir after grading", src, 9, "Price Variation",
       confidence="medium", notes="market/brand names of milled rice, not variety aliases")


# ================================================================== L2-S03 UBINIG brief
def s03():
    base = CS / "cgspace_ubinig_brief"
    wcsv("cgspace_ubinig_brief_metadata.csv", ["field", "value", "language", "authority", "place"], dspace_metadata_rows(base / "item.json"))
    wcsv("cgspace_ubinig_brief_bitstreams.csv", ["bundle", "name", "uuid", "sizeBytes", "md5", "sequenceId", "content_url"], bitstream_rows(base))
    pdf = base / "ORIGINAL/UBINIG_brief_FINAL_FOR_WEB.pdf"
    wcsv("cgspace_ubinig_brief_text.csv", ["page", "line", "text"], pdf_text_rows(pdf))
    t1 = [["Payesh (or kheer)", "Sweet rice pudding, prepared with white and fine quality rice cooked in milk, sugar/molasses, coconut, nuts and other dry spices.",
           "Begun bichi, Chiniguri, Jamai aduri, Kalijira, Kartik jhul, Najirshail, Paijam", "Bashmoti", ""],
          ["Firni", "Sweet rice pudding, made with coarsely ground rice cooked in milk, sugar/molasses, coconut, nuts and other dry spices.",
           "Begun bichi, Chiniguri, Jamai aduri, Kalijira, Kartik jhul, Najirshail, Paijam", "Bashmoti", ""],
          ["Pulao", "Rice cooked with butter-oil and flavoured with hot spices", "Chiniguri Kalijira, Ukun modhu, Radhuni pagol", "Bashmoti", ""],
          ["Chaler-ruti", "Rice-flour bread, similar to chapatis", "Kalijira and Sadadhepa", "",
           "Ajoldigha, Bhorilota, BRRI-28, BRRI-29, Chamara, Hijoldigha, Hijoldigha, Jhuldhan, Kalobakri, Kartikjhul, Kartik shail, Laldhepa, Pakri, Shaini dhan"],
          ["Semai", "Handmade rice vermicelli", "", "", "Patjag, Laldhepa, Sadadhepa, Boro Digha, Sadadigha"],
          ["Khichuri", "Rice cooked with pulses, turmeric and spices", "Bhawailya digha, Dholdigha, Hidi, Matibhangor, Pati shail, Patjag", "Bashmoti", "Kalobakri"],
          ["Pitha", "Rice-flour cakes/dumplings", "", "", "Chamara, Hijoldigha, Kartikjhul, Patjag"],
          ["Shomser-pitha", "Pitha filled with meat", "Dhepor, Laldhepa, Sadadhepa", "", ""],
          ["Teller-pitha", "Rice-flour cakes/dumplings with molasses deep-fried in oil", "Sadadhepa", "", "Chamara, Hijol digha (in Tangail), Kartikjhul"]]
    wcsv("cgspace_ubinig_brief_table1_culinary.csv", ["dish", "description", "non_aromatic_white", "aromatic_white", "red_rice"], t1)
    t2 = [["Tangail (Delduar)", "Large area / many households", "Chamara", "flood resistant; farmers have the seeds; grown on low-lying land"],
          ["Tangail (Delduar)", "Large area / many households", "BRRI-28 and BRRI-29", "both varieties mature in 140 days; good market demand; farmers have the seeds; can be grown on all types of land"],
          ["Tangail (Delduar)", "Large area / few households", "Bhawailya Digha; Kartik jhul", "good market demand; flood resistant; can be grown in waterbodies"],
          ["Tangail (Delduar)", "Large area / few households", "Patjag", "grown in low-lying fields with water; rainfed; long-duration rice"],
          ["Tangail (Delduar)", "Large area / few households", "Lal Dhepa; Sada Dhepa", "grown in char/beel land with water; good yield; good for pitha"],
          ["Tangail (Delduar)", "Large area / few households", "Sada Digha", "drought resistant (can survive water shortages); good for fodder"],
          ["Tangail (Delduar)", "Small area", "Chiniguri; Kalijira; Najirshail", "lower yield; need to grow on medium and high land; compete with Rabi crops for harvesting"],
          ["Tangail (Delduar)", "Small area", "Bashmoti; Jamai aduri; Jhul dhan; Paijam", "seeds are disappearing; Bashmoti straws are shorter"],
          ["Tangail (Delduar)", "Small area", "Boro Digha", "has a long straw; flood resistant; good for human food and fodder for cows; seeds are disappearing"],
          ["Tangail (Delduar)", "Small area", "Dhepor", "needs land with water; seeds are disappearing"],
          ["Tangail (Delduar)", "Small area", "Jhul dhan", "good for pitha and payesh but cannot be husked in mills"],
          ["Tangail (Delduar)", "Small area", "Patishail", "flood resistant; grown on low-level land"],
          ["Tangail (Delduar)", "Small area (held/planted list)", "Bashmoti; Boro Digha; Chiniguri; Dhepor; Hijoldigha; Jamai Aduri; Kalijira; Najirshail; Paijam; Patishail", ""]]
    t3 = [["Natore and Pabna", "Large area / many households", "BRRI-28 and BRRI-29", "both grow in 140 days; good market demand; higher yield; farmers have seeds; can be grown on all types of land"],
          ["Natore and Pabna", "Large area / many households", "Ukun modhu (BRRI-34)", "a numbered rice (BRRI-34); similar to Begun bichi, Chiniguri and Kaliljira, but not as tasty; has a higher yield"],
          ["Natore and Pabna", "Large area / many households", "Bashmoti", "grown in medium- and high-level land; can be cultivated in Aman and Boro season; fetches a good price; has a higher yield"],
          ["Natore and Pabna", "Large area / many households", "Hidi", "a favourite rice for farmers; can be grown in high- and low-level land"],
          ["Natore and Pabna", "Large area / many households", "Kartik shail", "a favourite rice for farmers; can be grown as Aus-Aman mixed; early harvesting in (Kartik) October; known as poverty-saving rice; tastes good"],
          ["Natore and Pabna", "Large area / many households", "Pakri", "can be grown in high or low land; water tolerant; yield is satisfactory; can make chira, muri and pitha"],
          ["Natore and Pabna", "Small area / few households (?)", "Begun bichi", "Has lower yield but is considered essential for festivals and special occasions"],
          ["Natore and Pabna", "Small area", "Chiniguri; Kalijira", "lower yield; need medium- and high-level land; compete with rabi crops for harvesting; Kalijira replaced by Ukun modhu (BRRI-34) that has a higher yield"],
          ["Natore and Pabna", "Small area", "Kalobokri", "a drought-resistant variety that needs high level land, which is lacking. Drought situation is changing"],
          ["Natore and Pabna", "Small area", "Ajoldigha; Dholdigha", "need low land and more water, which is lacking. Lower yield"],
          ["Natore and Pabna", "Small area", "Matibhangor", "can be grown in less water; has low yield"],
          ["Natore and Pabna", "Small area", "Bhorilota; Shaini", "need deep water"]]
    wcsv("cgspace_ubinig_brief_table2_3_fourcell.csv", ["site", "four_cell_category", "varieties", "reasons_as_printed"], t2 + t3)
    f1 = [["Tangail (Figure 1)", x, c] for c, xs in [("Large area / many households", ["BR 28 & 29", "Chamara"]),
                                                    ("Large area / few households", ["Bhawalya digha", "Kartik jhul", "Lal dhepa", "Patjag", "Sada dhepa", "Sada digha"]),
                                                    ("Small area (many or few households; cell boundaries not recoverable from text layer)",
                                                     ["Bashmoti", "Kalijira", "J. Aduri", "Jhuldhan", "Dhepor", "Boro digha", "Chiniguri", "Paijam", "Hijoldigha", "Patishail", "Najirshall"])] for x in xs]
    f1 += [["Natore/Pabna (Figure 2)", x, "as printed in figure (cell placement from text layer uncertain)"] for x in
           ["BR 28 & 29", "Kartikshail", "Hidi", "Ukun modhu", "Bashmoti", "Begunbichi", "Kalijira", "Ajoldigha", "Dholdigha", "Bhorilota", "Matibhangor", "Shaini", "Chiniguri", "Kalobokri", "Pakri"]]
    wcsv("cgspace_ubinig_brief_figures_fourcell.csv", ["figure", "variety_as_printed", "cell"], f1)
    src = "L2-S03"
    for nm in ["BRRI-28", "BRRI-29"]:
        k, kn = key_of(nm)
        ev(k, "key_traits", "matures in 140 days; good market demand; farmers have seed; grown on all land types (Tangail, Natore, Pabna farmers, 2019)",
           "BRRI-28 and BRRI- 29: both varieties mature in 140 days; good market demand; farmers have the seeds; can be grown on all types of land.",
           src, 6, "Table 2", notes=kn)
        ev(k, "adoption", "grown by many households on large areas (four-cell analysis, Delduar/Tangail and Natore/Pabna, Eid-ul-Azha 2019)",
           "Of the 19 varieties, only three (Chamara, BRRI-28 and BRRI-29) are grown by many farming households and on a large amount of land.",
           src, 7, "p.7 text", confidence="medium", notes=kn + "; qualitative community-level assessment")
        url_row(k, src, nm, 3, "Table 1 / Table 2")
    k, kn = key_of("BRRI-34")
    ev(k, "local_name", "Ukun modhu", "Ukun modhu is a numbered rice (BRRI-34); similar to Begun bichi, Chiniguri and Kaliljira, but not as tasty; has a higher yield.",
       src, 8, "Table 3", confidence="medium", notes=kn + "; farmers' name in Natore/Pabna")
    ev(k, "adoption", "grown by many households on large areas in Natore/Pabna (2019); replacing Kalijira/Chiniguri",
       "special aromatic rice varieties such as Chiniguri and Kalijira needed for pulao and payesh are being replaced by a modern high-yielding variety called Ukun Modhu (BRRI-34)",
       src, 9, "p.9 text", confidence="medium", notes=kn)
    url_row(k, src, "Ukun modhu (BRRI-34)", 8, "Table 3")


# ================================================================== L2-S04 ISPC brief 71
def s04():
    pdf = CS / "ispc_brief71/ispc_brief_71_rice_bangladesh.pdf"
    wcsv("ispc_brief71_text.csv", ["page", "line", "text"], pdf_text_rows(pdf))
    facts = [[1, "design", "villages selected (Rajshahi region)", "256", "The study selected 256 villages in the Rajshahi region"],
             [1, "design", "treated villages (BD56 mini-kits)", "192", "192 were ‘treated’ with BD56 mini-kits"],
             [1, "design", "control villages (BD51 mini-kits)", "64", "64 formed the control where seed mini-kits of an analogous long duration rice variety (BD51) were distributed"],
             [1, "variety", "BD51 expected duration (days)", "145", "BD51 was expected to require 145 days of cultivation"],
             [1, "variety", "BD56 expected duration (days)", "115", "compared to 115 days for BD56"],
             [1, "design", "mini-kit recipients per village (treatment arms)", "5", "five mini-kit recipients were randomly drawn"],
             [1, "design", "BD51 recipients per control village", "up to 15", "BD51 was distributed in the same manner to up to 15 equivalent farmers"],
             [1, "design", "farmers surveyed", "1,795", "covering a total of 1,795 farmers"],
             [1, "design", "survey period", "14 months", "three subsequent surveys over a 14-month period"],
             [2, "result", "BD56 harvest advance vs BD51 (days, Aman)", "25", "BD56 was on average harvested 25 days earlier than BD51"],
             [2, "result", "increase in probability of Rabi crop on BD56 plots (pp)", "28", "BD56 plots were 28 percentage points more likely than BD51 plots to be planted with a Rabi crop"],
             [2, "result", "BD56 plots in mustard (%)", "20", "mustard (20 percent of plots)"],
             [2, "result", "BD56 plots in potatoes (%)", "15", "potatoes (15 percent)"],
             [2, "result", "BD56 plots in pulses (%)", "8", "pulses (8 percent)"],
             [2, "result", "BD56 rice yield penalty (%)", "43", "The cost of shorter duration is a 43 percent lower rice yield"],
             [2, "result", "BD56 farmers who cultivated a Rabi crop (%)", "52", "the 52 percent of farmers who chose to cultivate a Rabi crop"],
             [2, "result", "annual profit gain for those farmers vs control (%)", "16", "had a 16 percent higher annual profit than control farmers"],
             [2, "result", "Rabi uptake: largest farmers (%)", "35", "Thirty-five percent of the largest farmers planted a Rabi crop"],
             [2, "result", "Rabi uptake: SAO-selected farmers (%)", "29", "29 percent among SAO-selected farmers"],
             [2, "result", "Rabi uptake: randomly drawn farmers (%)", "18", "18 percent of randomly drawn farmers"],
             [2, "result", "BD56 recipients without Rabi crop (%)", "48", "Forty-eight percent of BD56 mini-kit recipients did not cultivate a Rabi crop"],
             [2, "design", "mini-kit seed quantity (kg)", "5", "Mini-kits provided only 5 kg of seeds (sufficient for 0.1-0.2 hectare of rice)"],
             [2, "funding", "BD56 development funding", "partially funded by STRASA (Gates Foundation)", "Development of BD56 was partially funded by Stress Tolerant Rice for Africa and South Asia (STRASA) project"],
             [2, "funding", "study funding", "USAID Feed the Future Innovation Lab for Assets and Market Access (AID-OAA-L-12-00001)", "Financial support for this project came from USAID"],
             [2, "source", "underlying paper", "Manzoor, de Janvry, Emerick, Kelley, Sadoulet (2018), Tufts Economics working paper", "The Modest Gains from Augmenting Social Learning in Agriculture"]]
    wcsv("ispc_brief71_facts.csv", ["page", "type", "item", "value", "quote"], facts)
    wcsv("ispc_brief71_figure1_series.csv", ["series", "line_style", "note"],
         [[s, "dotted=BD51 (control), solid=BD56 (treatment)", "Figure 1 'Land use over one year' (share of plots, Jul 2016-Jul 2017); values only graphical, not extractable from text layer"]
          for s in ["Rice", "Pulses", "Wheat", "Mustard", "Potato", "Fallow"]])
    src = "L2-S04"
    k56, n56 = key_of("BD56"); k51, n51 = key_of("BD51")
    ev(k56, "cgiar_independent", "SPIA/ISPC 2018: development of BD56 partially funded by the STRASA project (IRRI-led, Gates Foundation); brief is headed IRRI",
       "Development of BD56 was partially funded by Stress Tolerant Rice for Africa and South Asia (STRASA) project, which was funded by the Gates Foundation.",
       src, 2, "Funding acknowledgements", notes=n56)
    ev(k56, "key_traits", "short duration: ~115 days (vs 145 for BRRI dhan51); harvested on average 25 days earlier than BD51 in Aman; 43% lower rice yield than BD51 in the RCT",
       "BD51 was expected to require 145 days of cultivation compared to 115 days for BD56.", src, 1, "Data and methodology", notes=n56)
    ev(k56, "adoption", "RCT seed mini-kits in 192 of 256 Rajshahi villages (2016-17); 52% of BD56 recipients planted a Rabi crop",
       "192 were ‘treated’ with BD56 mini-kits", src, 1, "Data and methodology", confidence="medium", notes=n56 + "; experimental distribution, not population adoption")
    ev(k56, "season", "Aman", "In the Aman season, BD56 was on average harvested 25 days earlier than BD51.", src, 2, "p.2", notes=n56)
    ev(k51, "key_traits", "long duration analogous variety, ~145 days (used as control in SPIA RCT)", "BD51 was expected to require 145 days of cultivation",
       src, 1, "Data and methodology", notes=n51)
    url_row(k56, src, "BRRI Dhan 56 / BD56", 1, "Researchers introduced a shorter duration rice variety, BRRI Dhan 56")
    url_row(k51, src, "BD51", 1, "analogous long duration rice variety (BD51)")


# ================================================================== L2-S05 JXB (metadata only)
def s05():
    j = CS / "jxb_erag452"
    rows = []
    cr = json.loads((j / "crossref.json").read_text(encoding="utf-8"))["message"]
    for k, v in cr.items():
        rows.append(["crossref", k, json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v])
    oa = json.loads((j / "openalex.json").read_text(encoding="utf-8"))
    for k in ["id", "doi", "title", "publication_date", "type", "open_access", "best_oa_location", "primary_location", "cited_by_count",
              "authorships", "topics", "keywords", "concepts", "referenced_works_count", "biblio", "is_retracted", "language", "ids"]:
        if k in oa:
            v = oa[k]; rows.append(["openalex", k, json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v])
    ep = json.loads((j / "europepmc_core.json").read_text(encoding="utf-8"))["resultList"]["result"][0]
    for k, v in ep.items():
        rows.append(["europepmc", k, json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v])
    wcsv("jxb_erag452_metadata.csv", ["source", "field", "value"], rows)


# ================================================================== L2-S06/07 GloMIP
def s06():
    g = CS / "glomip"
    lst = json.loads((g / "product-catalog_list_all.json").read_text(encoding="utf-8"))["result"]["data"]
    cols = ["pc_id", "crop", "variety", "parent", "type", "countries", "ms_shortname", "ms_longname", "OtherMSName", "style"]
    allrows = [[html.unescape(str(d.get(c))) if d.get(c) is not None else "" for c in cols] for d in lst]
    wcsv("glomip_product_catalog_all.csv", cols, allrows)
    bd = [d for d in lst if "bangladesh" in str(d.get("countries", "")).lower()]
    wcsv("glomip_product_catalog_bangladesh.csv", cols, [[html.unescape(str(d.get(c))) if d.get(c) is not None else "" for c in cols] for d in bd])
    # details (all fields), plus long tables
    dcols = None; drows = []; ks = []; gy = []; ba = []
    for d in bd:
        det = json.loads((g / f"details/pc_{d['pc_id']}.json").read_text(encoding="utf-8"))
        flat = {"pc_id": d["pc_id"]}
        for k, v in det.items():
            if k.endswith("_btn"):
                v = json.dumps(v)
            if k in ("key_strengths", "considerations", "gyat", "gyat_head", "bas", "bas_head"):
                v = " || ".join(" | ".join(r) for r in html_rows(v)) if k not in ("bas_head",) else " | ".join(strip_tags(x) for x in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", v or ""))
            flat[k] = "" if v is None else str(v).strip()
        if dcols is None:
            dcols = list(flat.keys())
        drows.append([flat.get(c, "") for c in dcols])
        for kind in ("key_strengths", "considerations"):
            for r in html_rows(det.get(kind)):
                ks.append([d["pc_id"], det["variety"], kind] + (r + ["", "", ""])[:3])
        gh = ["variety", "grain_yield_kg_ha", "grain_yield_pct_adv", "maturity_days", "plant_height_cm", "lodging", "shattering",
              "1000_grain_weight_g", "panicle_threshability", "HRR_pct", "amylose_pct", "special_trait", "tillering"]
        for r in html_rows(det.get("gyat")):
            gy.append([d["pc_id"], det["variety"]] + (r + [""] * 13)[:13])
        bh = [strip_tags(x) for x in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", det.get("bas_head") or "")]
        for r in html_rows(det.get("bas")):
            for i, val in enumerate(r[1:], start=1):
                ba.append([d["pc_id"], det["variety"], r[0], bh[i] if i < len(bh) else f"col{i}", val])
    wcsv("glomip_product_catalog_bangladesh_details.csv", dcols, drows)
    wcsv("glomip_bd_key_strengths_considerations.csv", ["pc_id", "variety", "kind", "main_trait", "sub_trait", "description"], ks)
    wcsv("glomip_bd_relative_performance_yield_agronomy.csv", ["pc_id", "catalog_variety"] + gh, gy)
    wcsv("glomip_bd_relative_performance_stress.csv", ["pc_id", "catalog_variety", "row_variety", "stress", "rating"], ba)
    # market segments
    ms = json.loads((g / "market-segments_list_all.json").read_text(encoding="utf-8"))["result"]["data"]
    mcols = list(ms[0].keys())
    msbd = [m for m in ms if "Bangladesh" in str(m.get("countries"))]
    wcsv("glomip_market_segments_bangladesh.csv", mcols, [[strip_tags(str(m.get(c))) if m.get(c) is not None else "" for c in mcols] for m in msbd])
    mrows = []
    for f in sorted((g / "ms_details").glob("ms_*.json")):
        m = json.loads(f.read_text(encoding="utf-8"))
        for k, v in m.items():
            mrows.append([m.get("ms_MSID"), k, strip_tags(v) if isinstance(v, str) else json.dumps(v, ensure_ascii=False)])
    wcsv("glomip_market_segment_details_referenced_by_bd_varieties.csv", ["ms_id", "field", "value"], mrows)
    ms_countries = {}
    for f in (g / "ms_details").glob("ms_*.json"):
        m = json.loads(f.read_text(encoding="utf-8"))
        ms_countries[m["ms_MSShortName"]] = ", ".join(x["name"] for x in m.get("ms_chart_countries", []))
    # evidence
    src = "L2-S06"; loc = "02_raw/cgiar_specific/glomip/details/pc_{}.json"
    for d in bd:
        det = json.loads((g / f"details/pc_{d['pc_id']}.json").read_text(encoding="utf-8"))
        name = det["variety"].strip()
        k, kn = key_of(name)
        lf = loc.format(d["pc_id"])
        def e(field, value, raw, locator, conf="high", notes=""):
            ev(k, field, value, raw, src, "", f"pc_id {d['pc_id']}: {locator}", "api_json", confidence=conf,
               notes="; ".join(x for x in [kn, notes] if x), lf=lf)
        e("cgiar_source_url", SRC[src]["url"], name, "product catalog row", notes="no per-variety public URL; detail served by /product-catalog/details/<pc_id> XHR")
        if det.get("parent_variety"):
            e("pedigree", html.unescape(det["parent_variety"]).strip(), html.unescape(det["parent_variety"]), "Parent",
              notes="GloMIP 'Parent' field; '*' marks are unexplained on the page")
        e("type", det.get("variety_type") or "", det.get("variety_type") or "", "Type")
        desc = (det.get("variety_description") or "").strip()
        if desc:
            e("key_traits", desc, desc, "Description")
            m = re.search(r"Developed by ([A-Z][A-Za-z]+) and released in (\d{4})", desc)
            if m:
                e("developer", m.group(1), m.group(0), "Description")
                e("approval_date", m.group(2), m.group(0), "Description", notes="'released in' year from GloMIP description")
        msn = d.get("ms_shortname") or det.get("ms_shortname")
        if msn or (det.get("ms_othername") not in (None, "", "-")):
            val = f"{msn or ''} | {d.get('ms_longname') or ''} | other name: {det.get('ms_othername') or d.get('OtherMSName') or ''}"
            nt = ""
            if msn and msn in ms_countries and "Bangladesh" not in ms_countries[msn]:
                nt = f"GloMIP's segment record {msn} lists target countries {ms_countries[msn]} (not Bangladesh)"
            e("market_segment", val, val, "Market Segment Information", notes=nt)
        pos = {"PTR": det.get("ptr"), "DSR": det.get("dsr"), "Irrigated lowland": det.get("il"), "Rainfed lowland": det.get("rl"), "Upland": det.get("upland")}
        posv = "; ".join(f"{a}: {b}" for a, b in pos.items() if b)
        rep = {"replace IL": det.get("ril"), "replace RL": det.get("rrl"), "replace UP": det.get("rup"),
               "companion IL": det.get("cil"), "companion RL": det.get("crl"), "companion UP": det.get("cup")}
        repv = "; ".join(f"{a}: {b}" for a, b in rep.items() if b and b != "None")
        ksl = [" / ".join(r) for r in html_rows(det.get("key_strengths"))]
        col = [" / ".join(r) for r in html_rows(det.get("considerations"))]
        prof = f"planting/ecosystem: {posv}" + (f"; positioning: {repv}" if repv else "") + \
               (f"; key strengths: {' ; '.join(ksl)}" if ksl else "") + (f"; considerations: {' ; '.join(col)}" if col else "") + \
               (f"; producibility kg/acre: {det.get('variety_kg')}" if det.get("variety_kg") else "") + \
               (f"; recommendation: {det.get('recommendation')}" if det.get("recommendation") else "") + \
               (f"; remarks: {re.sub(r'\s+', ' ', det.get('remarks') or '').strip()}" if det.get("remarks") else "")
        e("product_profile", prof, posv or prof, "Planting method/ecosystem, Positioning, Key Strengths, Considerations, Producibility, Recommendation")
        if "PTR: Recommended" in posv or "Irrigated" in posv:
            pass
        for r in html_rows(det.get("gyat")):
            if r and r[0].strip() == name:
                e("key_traits", f"GloMIP relative performance: yield {r[1]} kg/ha (adv {r[2]}%), maturity {r[3]} d, height {r[4]} cm, lodging {r[5]}, 1000-grain wt {r[7]} g, amylose {r[10]}%",
                  " ".join(r[:8]), "Relative Variety Performance - Grain Yield and Agronomic Traits")
    for m in msbd:
        if m["crop"] == "Rice":
            pass


# ================================================================== L2-S08/S09 ASTI
def s08():
    a = CS / "asti"
    rows = []; long = []
    with open(a / "ASTI_full_BGD_country.csv", encoding="utf-8-sig") as fh:
        lines = fh.read().splitlines()
    lines = [l for l in lines if not l.startswith("sep=")]
    rd = list(csv.reader(lines, delimiter=";"))
    hdr = [h.lstrip("﻿") for h in rd[0]]
    for r in rd[1:]:
        if not r:
            continue
        rows.append(r)
        for i, y in enumerate(hdr):
            if re.fullmatch(r"\d{4}", y) and i < len(r) and r[i] not in ("", None):
                long.append([r[0], r[1], y, r[i], r[-1] if hdr[-1] == "Note" else ""])
    wcsv("asti_bgd_indicators_wide.csv", hdr, rows)
    wcsv("asti_bgd_indicators_long.csv", ["country", "indicator", "year", "value", "note"], long)
    # xlsx sheets as delivered (all cells)
    wb = openpyxl.load_workbook(a / "ASTI_full_BGD_country.xlsx", data_only=True)
    cells = []
    for ws in wb.worksheets:
        for r in ws.iter_rows():
            for c in r:
                if c.value not in (None, ""):
                    cells.append([ws.title, c.row, c.column, c.value])
    wcsv("asti_bgd_indicators_xlsx_cells.csv", ["sheet", "row", "col", "value"], cells)
    # publications: all text (layout), pdfplumber tables, curated tables
    pubs = {"CB34_2006": "bangladesh-brief__Bangladesh_CB34.pdf", "Note_2011": "bangladesh-note__Bangladesh-Note.pdf",
            "Factsheet_2014": "bangladesh-factsheet__Bangladesh-Factsheet.pdf", "CountryBrief_2019": "bangladesh-country-note-2019__Bangladesh-CountryBrief-2019.pdf"}
    lay = []; tabs = []; mentions = []
    for tag, fn in pubs.items():
        p = a / "pubs" / fn
        for pg, ln, t in pdf_layout_rows(p):
            lay.append([tag, pg, ln, t])
        for r in pdfplumber_tables(p):
            tabs.append([tag] + r)
        for pg, ln, t in pdf_text_rows(p):
            pass
        full = "\n".join("=== %d\n" % (i + 1) + pp.get_text() for i, pp in enumerate(fitz.open(p)))
        cur = 0
        for part in re.split(r"(=== \d+\n)", full):
            m = re.match(r"=== (\d+)\n", part)
            if m:
                cur = int(m.group(1)); continue
            flat = re.sub(r"\s+", " ", part)
            for mm in re.finditer(r"([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*)[^.;()]{0,60}?\((\d[\d,.]*) (?:FTEs?|fte)[^)]*\)", flat):
                mentions.append([tag, cur, mm.group(1), mm.group(2), mm.group(0)[:200]])
            for mm in re.finditer(r"(BRRI|BINA|BFRI|FRI|BARI)[^.]{0,120}?(\d+) (?:fte|FTE) researchers", flat):
                mentions.append([tag, cur, mm.group(1), mm.group(2), mm.group(0)[:200]])
    wcsv("asti_pubs_layout_text.csv", ["publication", "page", "line", "text"], lay)
    wcsv("asti_pubs_pdfplumber_tables.csv", ["publication", "page", "table", "row", "col", "text"], tabs)
    wcsv("asti_pubs_agency_fte_mentions.csv", ["publication", "page", "agency_or_phrase_head", "fte", "phrase"], mentions)
    cur_tabs = []
    T = lambda pub, page, table, *vals: cur_tabs.append([pub, page, table] + list(vals))
    for row in [("BARI", "221.0", "313.0", "167.0", "701.0"), ("Other BARC-affiliated (12)", "310.2", "591.8", "37.5", "939.5"), ("NIB", "7.0", "25.0", "—", "32.0"),
                ("BAU (6)", "114.3", "59.1", "—", "173.4"), ("Other higher education (42)", "182.9", "216.6", "3.0", "402.5"), ("Nonprofit (2)", "4.6", "14.8", "0.8", "20.2"),
                ("Total (64)", "840.0", "1,220.2", "208.3", "2,268.6")]:
        T("CountryBrief_2019", 2, "Agricultural researchers by qualification level, 2016 (FTEs): PhD|MSc|BSc|TOTAL", *row)
    for row in [("BARI", "1,722.2", "1,865.2", "2,264.9"), ("BRRI", "372.0", "537.8", "565.7"), ("BLRI", "122.0", "183.8", "323.8"), ("BINA", "94.5", "302.3", "259.2"),
                ("SRDI", "160.8", "436.2", "212.4"), ("BFRI", "143.7", "162.6", "207.5"), ("BJRI", "219.2", "208.7", "197.2"), ("FRI", "120.5", "113.8", "193.5"),
                ("BARC", "412.0", "521.2", "160.4"), ("BSRI", "143.5", "138.1", "140.2"), ("CDB", "43.1", "47.2", "73.1"), ("BSRTI", "9.6", "41.0", "43.4"),
                ("BTRI", "45.4", "48.8", "41.4"), ("Total", "3,608.3", "4,606.6", "4,682.7")]:
        T("CountryBrief_2019", 4, "Total expenditure by BARC-affiliated agencies, million taka constant 2011 prices: 2006|2011|2016", *row)
    for row in [("2016", "2,675", "1,277", "730"), ("2015", "2,006", "1,629", "628"), ("2014", "1,979", "1,756", "757"), ("2013", "1,876", "1,697", "687"),
                ("2012", "1,922", "1,938", "552"), ("2011", "1,995", "2,002", "609"), ("2010", "2,002", "1,805", "549"), ("2009", "1,787", "1,286", "645"),
                ("2008", "1,198", "1,297", "895"), ("2007", "1,231", "1,230", "1,257"), ("2006", "1,183", "1,207", "1,218")]:
        T("CountryBrief_2019", 4, "Total expenditures by cost category, BARC-affiliated institutes, million taka 2011 prices: Salaries|Operating and program costs|Capital investments", *row)
    for row in [("Barley", "1", "", "", "", "", ""), ("Beans", "2", "1", "", "", "", ""), ("Fiber crops", "", "", "2", "", "", ""), ("Flowers", "6", "", "", "", "", ""),
                ("Fruit", "9", "", "", "", "", ""), ("Garlic", "2", "1", "", "", "", ""), ("Groundnuts", "", "1", "", "", "", ""), ("Herbs and spices", "12", "1", "", "", "", ""),
                ("Maize", "3", "", "", "", "", ""), ("Olives", "1", "", "", "", "", ""), ("Onions", "1", "", "", "", "", ""), ("Potatoes", "26", "", "", "", "", ""),
                ("Pulses", "6", "4", "", "", "", ""), ("Rice", "", "6", "", "21", "", ""), ("Sesame seed", "", "1", "", "", "", ""), ("Soybeans", "", "1", "", "", "", ""),
                ("Sugarcane", "", "", "", "", "4", ""), ("Sweet potatoes", "4", "", "", "", "", ""), ("Tea", "", "", "", "", "", "2"),
                ("Vegetables", "14", "4", "1", "", "", ""), ("Wheat", "2", "1", "", "", "", ""), ("TOTAL", "89", "21", "3", "21", "4", "2")]:
        T("CountryBrief_2019", 6, "New varieties released or registered by BARC-affiliated institutes, 2013-2016: BARI|BINA|BJRI|BRRI|BSRI|BTRI (note: data for BSRI were not available)", *row)
    for row in [("BARI", "12", "16", "33", "12", "20", "18", "111"), ("BINA", "1", "1", "3", "5", "9", "1", "20"), ("BJRI", "–", "2", "–", "3", "–", "1", "6"),
                ("BRRI", "2", "3", "–", "4", "3", "1", "13"), ("BSRI", "1", "–", "2", "–", "–", "1", "4"), ("BSRTI", "–", "1", "1", "–", "–", "–", "2"),
                ("BTRI", "–", "–", "–", "–", "1", "–", "1"), ("CDB", "–", "–", "–", "1", "1", "–", "2"), ("TOTAL", "16", "23", "39", "25", "34", "22", "159")]:
        T("Factsheet_2014", 3, "Number of new crop varieties released by BARC-affiliated institutes: 2007|2008|2009|2010|2011|2012|TOTAL", *row)
    for row in [("BARI", "1,827.6", "52", "36", "12"), ("BRRI", "535.1", "40", "48", "12"), ("BARC", "449.2", "16", "84", ""), ("BINA", "355.8", "27", "22", "51"),
                ("SRDI", "321.1", "39", "60", "1"), ("BJRI", "196.8", "50", "47", "3"), ("BLRI", "188.8", "20", "42", "38"), ("BFRI", "140.3", "72", "27", "1"),
                ("BSRI", "131.6", "71", "29", ""), ("FRI", "114.7", "58", "42", ""), ("BTRI", "48.7", "43", "55", "1")]:
        T("Factsheet_2014", 3, "BARC-affiliated institutes' spending 2012 (million taka 2011 prices) and cost-category shares %: spending|salaries|operating and program|capital", *row)
    for row in [("BARI", "2000", "485.0", "22", "59", "19"), ("BARI", "2009", "600.0", "27", "59", "15"), ("BARI", "2012", "738.0", "36", "62", "2"),
                ("Other BARC-affiliated", "2000", "872.0", "22", "60", "19"), ("Other BARC-affiliated", "2009", "841.0", "29", "64", "8"), ("Other BARC-affiliated", "2012", "884.0", "30", "61", "9"),
                ("Higher education", "2000", "201.4", "53", "40", "7"), ("Higher education", "2009", "376.2", "44", "52", "4"), ("Higher education", "2012", "456.8", "47", "53", "0.4")]:
        T("Factsheet_2014", 2, "Distribution of agricultural researchers by degree (FTEs; shares %): year|FTE|PhD%|MSc%|BSc%", *row)
    for row in [("BARI", "845.1", "37.3", "29.6", "600.0", "28.8"), ("Other BARC-affiliated (10)", "1,100.7", "48.6", "38.6", "841.0", "40.4"),
                ("Non-BARC government (10)", "387.1", "17.1", "13.6", "338.5", "16.6"), ("BRAC", "141.6", "6.3", "5.0", "7.5", "0.4"),
                ("Higher education (32)", "376.0", "16.6", "13.2", "286.8", "13.8"), ("Total (54)", "2,850.5", "125.9", "100", "2,073.8", "100")]:
        T("Note_2011", 2, "Table 1 public agricultural R&D spending and staffing 2009: takas m (2005)|PPP$ m (2005)|spend share %|FTEs|FTE share %", *row)
    for row in [("BARI", "547.6", "46.9", "511.0", "26.4", "28.4", "1"), ("BARC-affiliated", "1,105.6", "94.7", "806.0", "53.4", "44.9", "10"),
                ("Other government", "182.6", "15.6", "273.0", "8.8", "15.2", "10"), ("Higher education", "227.9", "19.5", "197.4", "11.0", "11.0", "17"),
                ("Subtotal", "2,063.7", "176.8", "1,787.4", "99.4", "99.5", "38"), ("Private enterprises", "11.7", "1.0", "9.0", "0.6", "0.5", "2"),
                ("Total", "2,075.4", "177.8", "1,796.4", "100", "100", "40")]:
        T("CB34_2006", 1, "Table 1 composition of ag research expenditures and researchers 2002: takas m (2000)|intl $ m (2000)|researchers fte|spend %|researchers %|agencies", *row)
    mx = max(len(r) for r in cur_tabs)
    wcsv("asti_pubs_curated_tables.csv", ["publication", "page", "table"] + [f"c{i}" for i in range(1, mx - 2)], [r + [""] * (mx - len(r)) for r in cur_tabs])
    src = "L2-S09d"
    q = "BRRI released a large number of rice varieties in recent years, but so far none have been sufficiently promising to replace BRRI Dhan 28 and 29, which were released in 1994"
    for k in ["BRRI_DHAN28", "BRRI_DHAN29"]:
        ev(k, "approval_date", "1994", q, src, 6, "p.6 text beside variety-release table", notes="'released in 1994' (ASTI-BARC 2019)")
        ev(k, "adoption", "primary drivers of increased rice productivity since 1994; no newer BRRI variety promising enough to replace them (ASTI-BARC 2019)",
           q, src, 6, "p.6 text", confidence="medium", notes="qualitative")
        url_row(k, src, "BRRI Dhan 28 and 29", 6, "p.6 text")


# ================================================================== L2-S10 TRIVSA rice (Bangladesh rows)
def s10():
    f = RAW / "asti_trivsa/TRIVSA-Rice-Data.xlsx"
    wbv = openpyxl.load_workbook(f, data_only=True); wbf = openpyxl.load_workbook(f, data_only=False)
    out = {}
    for sh in ["Releases", "Adoption", "Overview"]:
        vrows = list(wbv[sh].iter_rows(values_only=True)); frows = list(wbf[sh].iter_rows(values_only=True))
        out[sh] = (vrows, frows)
    vr, fr = out["Releases"]
    hdr = list(vr[0]); code = list(vr[1])
    keep = [i for i, r in enumerate(vr) if i > 1 and r[1] == "Bangladesh"]
    def cell(i, j):
        v = vr[i][j]
        if v is None and isinstance(fr[i][j], str) and fr[i][j].startswith("="):
            return fr[i][j] + " [formula; no cached value]"
        return v
    rel_rows = [[i + 1] + [cell(i, j) for j in range(len(hdr))] for i in keep]
    wcsv("trivsa_rice_bangladesh_releases.csv", ["xlsx_row"] + [f"{h} [{c}]" if c and c != h else str(h) for h, c in zip(hdr, code)], rel_rows)
    ar, af = out["Adoption"]
    ah = [str(x) if x is not None else f"col{j+1}" for j, x in enumerate(ar[0])]
    nonempty = [j for j in range(len(ah)) if any(r[j] not in (None, "") for r in ar[1:] if r[1] and "Bangladesh" in str(r[1]))]
    adr = [[i + 1] + [ar[i][j] for j in nonempty] for i in range(1, len(ar)) if ar[i][1] and "Bangladesh" in str(ar[i][1])]
    wcsv("trivsa_rice_bangladesh_adoption.csv", ["xlsx_row"] + [ah[j] for j in nonempty], adr)
    orow, _ = out["Overview"]
    ov = [[i + 1] + list(r[:7]) for i, r in enumerate(orow) if i < 4 or (r[1] and "Bangladesh" in str(r[1]))]
    wcsv("trivsa_rice_overview_header_and_bangladesh.csv", ["xlsx_row", "c1", "c2", "c3", "c4", "c5", "c6", "c7"], ov)
    # evidence
    src = "L2-S10"
    H = {h: j for j, h in enumerate(hdr)}
    trait_cols = [h for h in hdr if h and (h.startswith("Resistance") or h in ("Grain Yield (t/ha)", "Days to maturity from 50% flowering", "Days from seeding to harvesting",
                  "Plant Height (cm)", "Photoperiod Sensitivity", "Cold Tolerance", "Drought Sensitivity", "Submergence tolerance", "Salt injury resistance",
                  "Days from seeding to harvesting by season: Boro", "Days from seeding to harvesting by season: Aus", "Days from seeding to harvesting by season: Aman",
                  "Grain type", "Special features/traits", "Comments", "Amylose content", "1000 grain weight"))]
    for i in keep:
        r = vr[i]; name = r[H["Release Name"]]
        k, kn = key_of(name)
        if k == "UNMATCHED" and r[H["Alternative Name"]]:
            k2, kn2 = key_of(r[H["Alternative Name"]])
            if k2 != "UNMATCHED":
                k, kn = k2, kn2 + "; keyed on Alternative Name"
        loc = f"Releases sheet row {i+1} (Ref ID {r[0]}), {name}"
        origin = r[H["Country of origin "]]; inst = r[H["Institution that developed the variety"]]; meth = r[H["Method"]]
        ev(k, "cgiar_independent", f"ASTI-TRIVSA 2015: country of origin '{origin}'; developing institution '{inst}'; method '{meth}'",
           f"{name} | {origin} | {inst} | {meth} | {r[H['Original breeding line name ']]}", src, "", loc, "xlsx",
           notes="; ".join(x for x in [kn, "mention only (no CGIAR origin stated)" if not any("IRRI" in str(x) or "CGIAR" in str(x) for x in (origin, inst)) else "", f"raw name '{name}'" if k == "UNMATCHED" else ""] if x))
        tv = "; ".join(f"{h}: {cell(i, H[h])}" for h in trait_cols if cell(i, H[h]) not in (None, ""))
        if tv:
            ev(k, "key_traits", "TRIVSA: " + tv, f"{name} " + tv, src, "", loc, "xlsx", notes=kn + ("; 'Days to maturity from 50% flowering' cells are formulas (=T-30)" if "formula" in tv else ""))
        url_row(k, src, name, "", loc, "xlsx")
    for i in range(1, len(ar)):
        r = ar[i]
        if not (r[1] and "Bangladesh" in str(r[1])):
            continue
        name = str(r[2]).strip()
        k, kn = key_of(name)
        parts = []
        for j, lab in [(5, "expert opinion (national)"), (6, "expert opinion (aggregated district)"), (7, "household survey"), (8, "community survey")]:
            if r[j] not in (None, ""):
                parts.append(f"{lab} {round(float(r[j]), 3)}%")
        if not parts:
            continue
        ev(k, "adoption", "TRIVSA % of national rice area, 2008-10 reference period: " + "; ".join(parts),
           f"{name} | " + " | ".join(str(r[j]) for j in range(3, 9)), src, "", f"Adoption sheet row {i+1}: {name}", "xlsx",
           notes="; ".join(x for x in [kn, f"raw name '{name}'" if k == "UNMATCHED" else "", "aggregate row" if name in ("Hybrids", "Other MVs", "Minikit") else "",
                                        "Overview: Bangladesh rice area 11,553 thousand ha (2008-10); % area to improved varieties 80 expert / 90 household / 86 community"] if x))


def mark_two_source():
    """approval_date rows: two_source when another agent's evidence gives the same year for the key."""
    other = collections.defaultdict(set)
    for f in glob.glob(str(WK / "evidence_*.csv")):
        if f.endswith("evidence_L2.csv"):
            continue
        with open(f, encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                if r.get("field") == "approval_date" and r.get("value"):
                    other[r["pilot_key"]].add((r["value"][:4], r.get("source_id", "")))
    for e in EV:
        if e["field"] == "approval_date" and e["pilot_key"] != "UNMATCHED":
            hits = sorted({s for y, s in other.get(e["pilot_key"], set()) if y == e["value"][:4]})
            if hits:
                e["validation"] = "two_source"
                e["notes"] = (e["notes"] + "; " if e["notes"] else "") + "same year in " + ", ".join(hits[:4])
            else:
                yrs = sorted({y for y, s in other.get(e["pilot_key"], set())})
                if yrs:
                    e["notes"] = (e["notes"] + "; " if e["notes"] else "") + "CONFLICT: other sources give " + ", ".join(yrs)


if __name__ == "__main__":
    for fn in (s01, s02, s03, s04, s05, s06, s08, s10):
        fn()
    mark_two_source()
    with open(WK / "evidence_L2.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=EVH); w.writeheader(); w.writerows(EV)
    print("evidence rows", len(EV), "keys", len({e['pilot_key'] for e in EV}))
    print(collections.Counter(e["field"] for e in EV))
    print(collections.Counter(e["source_id"] for e in EV))
    for k, v in COUNTS.items():
        print(f"{k}: {v[0]} rows x {v[1]} cols")
