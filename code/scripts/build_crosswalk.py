"""Crosswalk from rice variety codes/labels in household surveys and the SPIA DNA reference library
to variety_id in the Bangladesh rice variety register (05_output/final/bgd_rice_varieties.csv).

Run from anywhere:  python scripts/build_crosswalk.py

Reads (read-only):
  value labels / code lists: BIHS 2011/12, 2015, 2018/19 .dta value labels; SPIA BIHS 2024 .dta value labels;
  SPIA DNA fingerprinting reference library (Barcode_reference_2024.xlsx) and the distinct
  reference names used in bangladesh_rice_assignment_results.xlsx;
  MIXTAPE 2026 questionnaire drafts (May 15 HTML, March 3 text export), the 21 August 2026 questionnaire
  (Survey/MIXTAPE Survey_08_21_2026.docx.md) and the fielded SurveyCTO choice lists as printed in the CAPI
  printables of 14 Oct 2026 (Survey/bihs_spia2026_*_printable_English.pdf; no XLSForm is on disk).
  plot counts (step 'plot coverage'): only the crop-code and variety-code columns of the BIHS H1 plot files and the
  SPIA C2 variety columns; no household identifier or other variable is read, and only aggregate counts are written.
Writes:
  05_output/final/bgd_variety_crosswalk.csv          compact, one row per (source, code, label); for reading
  05_output/final/bgd_variety_crosswalk_long.csv     one row per (source, instrument_version, variable, code); for merging
  05_output/final/bgd_non_register_names.csv         attributes of every NA_ identifier
  06_validation/crosswalk_plot_coverage.csv          plot-weighted match rates by round and season
  06_validation/crosswalk_plot_cgiar.csv             plot reports by cgiar_role, depth_to_cgiar, top varieties
  06_validation/crosswalk_report.md
Uses the hand decisions in 04_working/crosswalk_manual_overrides.csv and the attributes of non-register names in
04_working/crosswalk_non_register_attributes.csv.

Matching rule: labels are matched on their text, never on the code number. Survey codes are list
positions (BIHS code 13 = 'Gazi BR-14'), so a code never implies a variety number.
"""
import csv
import html
import re
import sys
import warnings
from collections import OrderedDict, defaultdict
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # bgd_variety_archive
BGD = ROOT.parent                       # RES/BGD_MIX
sys.path.insert(0, str(HERE))
from lib_keys import make_key  # noqa: E402

REG = ROOT / "05_output/final/bgd_rice_varieties.csv"
LOCAL = ROOT / "05_output/final/bgd_local_names.csv"
UNRES = ROOT / "05_output/final/bgd_rice_not_approved_or_unresolved.csv"
OVR = ROOT / "04_working/crosswalk_manual_overrides.csv"
OUT = ROOT / "05_output/final/bgd_variety_crosswalk.csv"
OUT_LONG = ROOT / "05_output/final/bgd_variety_crosswalk_long.csv"
OUT_NA = ROOT / "05_output/final/bgd_non_register_names.csv"
NA_ATTR = ROOT / "04_working/crosswalk_non_register_attributes.csv"
PEDSUM = ROOT / "05_output/final/bgd_pedigree_summary.csv"
COV = ROOT / "06_validation/crosswalk_plot_coverage.csv"
COV_CGIAR = ROOT / "06_validation/crosswalk_plot_cgiar.csv"
REPORT = ROOT / "06_validation/crosswalk_report.md"

W = "BIHS data, shape files and SPIA 2024 wave"
SPIA_FINAL = f"{W}/SPIA 2024 round/Data/Final"
SPIA_COPY = "hilsa_feasibility/external/SPIA-Bangladesh-Study-2025/Data/Final"   # copy of the SPIA release; only source of module b1_5
DNA = f"{W}/SPIA 2024 round/Data/DNA fingerprinting"

# (source, file, label-set filter). Variables are read from the label-set attachments in each file.
DTA_SOURCES = [
    ("BIHS2011_12", f"{W}/BIHS 2011-2012/011_mod_h1_male.dta", None),
    ("BIHS2015", f"{W}/BIHS 2015-2016/015_r2_mod_h1_male.dta", None),
    ("BIHS2015", f"{W}/BIHS 2015-2016/029_r2_mod_i4_male.dta", None),
    ("BIHS2015", f"{W}/BIHS 2015-2016/030_r2_mod_i5_male.dta", "rice_only"),
    ("BIHS2018_19", f"{W}/BIHS 2018-2019/BIHSRound3/Male/021_bihs_r3_male_mod_h1.dta", None),
    ("BIHS2018_19", f"{W}/BIHS 2018-2019/BIHSRound3/Male/035_bihs_r3_male_mod_i4.dta", None),
    ("BIHS2018_19", f"{W}/BIHS 2018-2019/BIHSRound3/Male/037_bihs_r3_male_mod_i5.dta", "rice_only"),
    ("BIHS2018_19", f"{W}/BIHS 2018-2019/BIHSRound3/Community/153_r3_com_mod_l1.dta", None),
    ("BIHS2018_19", f"{W}/BIHS 2018-2019/BIHSRound3/Community/154_r3_com_mod_l1_20.dta", None),
    ("BIHS2024_SPIA", f"{SPIA_COPY}/SPIA_BIHS_2024_module_b1_5.dta", None),
    ("BIHS2024_SPIA", f"{SPIA_FINAL}/SPIA_BIHS_2024_module_b6.dta", None),
    ("BIHS2024_SPIA", f"{SPIA_FINAL}/SPIA_BIHS_2024_module_c2_4.dta", None),
]
MIX_HTML = "MIXTAPESurvey_Draft_05_15_26.html"
MIX_TXT = "MIXTAPE Survey_Draft_03_03_26.docx.txt"
MIX_AUG = "Survey/MIXTAPE Survey_08_21_2026.docx.md"
# SurveyCTO printables (HTML printed to PDF on 14 Oct 2026); the XLSForm itself is not on disk
CAPI_PDFS = [("Survey/bihs_spia2026_male_resp_V1_printable_English.pdf", "CAPI male_resp_V1 (printed 2026-10-14)"),
             ("Survey/bihs_spia2026_hhq_training_v2_all_printable_English.pdf", "CAPI hhq_training_v2_all (printed 2026-10-14)")]

# instrument version of each (source, file); the key of the long crosswalk is (source, instrument_version, variable, code)
IV_BY_SOURCE = {"BIHS2011_12": "2011-12", "BIHS2015": "2015", "BIHS2018_19": "2018-19", "BIHS2024_SPIA": "2024",
                "SPIA_DNA_reference": "2024", "MIXTAPE2026_0821": "2026-08-21"}
IV_BY_FILE = {MIX_HTML: "2026-05-15 draft", MIX_TXT: "2026-03-03 draft"} | {f: v for f, v in CAPI_PDFS}

COLS = ["source", "source_file", "variable", "code", "label_as_printed", "variety_id", "variety_name",
        "match_type", "n_candidates", "candidate_ids", "confidence", "note", "non_register_id"]
LONG_COLS = ["source", "instrument_version", "survey_file", "variable", "code", "label_as_printed", "variety_id",
             "variety_name", "match_type", "n_candidates", "candidate_ids", "confidence", "note", "non_register_id",
             "family_rice_type", "family_cgiar_roles"]
SOURCE_ORDER = ["BIHS2011_12", "BIHS2015", "BIHS2018_19", "BIHS2024_SPIA", "MIXTAPE2026_draft", "MIXTAPE2026_0821",
                "MIXTAPE2026_CAPI", "SPIA_DNA_reference"]

# notes on single codes that depend on another variable of the survey (finding A2-04)
CROP_A_NOTE = ("combine with crop_a: the 2011-12 list has no local or landrace names, so local varieties fall here; "
               "crop_a 11, 12, 14 and 15 (aush local, aush local developed, aman local, b. aman local) mark local "
               "rice, 17 and 20 an unspecified hybrid, 13, 16, 18 and 19 an unnamed HYV")
CODE_NOTES = {("BIHS2011_12", "54"): CROP_A_NOTE, ("BIHS2011_12", "74"): CROP_A_NOTE}

# ----------------------------------------------------------------------------------------------
# normalisation helpers
BN_DIG = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
SEASON = re.compile(r"\((?:[^()]*\b(?:boro|aus|aush|aoush|aman)\b[^()]*)\)?", re.I)
TRAIT = re.compile(r"(zinc enriched|drought tolerant|saline tolerant|weed resistant|salt tolerant|flood tolerant|\(aromatic\)|\(zinc\))", re.I)


def norm(s):
    s = str(s).translate(BN_DIG).lower()
    return re.sub(r"[\s\-_.,;:()\[\]/'\"‘’?*|®]+", "", s)


def clean_label(lab):
    s = str(lab).strip()
    s = re.sub(r"^\s*hybrid:\s*", "", s, flags=re.I)
    s = SEASON.sub(" ", s)
    s = TRAIT.sub(" ", s)
    s = re.sub(r"\(\s*\)", " ", s)
    s = re.sub(r"[.*?]+\s*$", "", s.strip())
    return re.sub(r"\s+", " ", s).strip()


# ----------------------------------------------------------------------------------------------
# register index
reg = pd.read_csv(REG, dtype=str).fillna("")
REG_IDS = set(reg.variety_id)
REG_NAME = dict(zip(reg.variety_id, reg.variety_name))
unres = pd.read_csv(UNRES, dtype=str).fillna("")
UNRES_IDS = dict(zip(unres.variety_id, unres.status))


def split_alias(a):
    return [p.strip() for p in re.split(r"[|;]", a) if p.strip()]


name_index = defaultdict(set)     # norm(name) -> {variety_id}
name_kind = {}                    # (norm, id) -> 'normalised_name' | 'alias'
for r in reg.itertuples():
    vn = r.variety_name
    for nm, kind in [(vn, "normalised_name"), (re.sub(r"\s*\(.*$", "", vn), "normalised_name"),
                     (r.official_name_en, "normalised_name"), (r.popular_name, "alias")] + \
                    [(a, "alias") for a in split_alias(r.aliases)]:
        if nm and len(norm(nm)) >= 3:
            k = norm(nm)
            name_index[k].add(r.variety_id)
            name_kind.setdefault((k, r.variety_id), kind)
loc = pd.read_csv(LOCAL, dtype=str).fillna("")
for r in loc.itertuples():
    # DNA-study misclassification patterns and milled-rice brand names are not aliases
    if not r.variety_id.startswith("RICE-") or r.source_type == "DNA fingerprinting study":
        continue
    if re.search(r"not variety aliases|brand names|misreport", r.notes + r.flags, re.I):
        continue
    for nm in (r.local_name, r.local_name_bn):
        if nm and len(norm(nm)) >= 3:
            name_index[norm(nm)].add(r.variety_id)
            name_kind.setdefault((norm(nm), r.variety_id), "alias")

# ----------------------------------------------------------------------------------------------
# vocabularies (classification rules, not per-code decisions)
GENERIC = re.compile(r"^(others?|others? ?\d? ?\(?specify\)?|others? \(traditional\)|other hybrid.*|skip|not assigned|"
                     r"do not know|don'?t know|n/?a|\|?|nan|\(blank\)|miscellaneous.*|chinese|mota.*|bhojon.*)$", re.I)
GENERIC_NOTE = {"mota": "grain-type description (bold round grain), not a variety; SPIA DNA: most self-reported 'Mota' matched TK Deep Straw",
                "bhojon": "grain-type description (white/coarse), not a variety name",
                "chinese": "origin description (Chinese hybrid seed), not a variety name",
                "miscellaneous": "residual hybrid category"}

# label-norm prefix -> (non_register_id, note, confidence)
NOT_APPROVED = [
    # attributes of every NA_ id (type, origin, cgiar_role, SPIA DNA findings) are in bgd_non_register_names.csv
    ("nerica", "NA_NERICA", "NERICA (New Rice for Africa) lines, AfricaRice; label names no Bangladesh release (BRRI dhan82, Binadhan-19 and -21 derive from NERICA-10)", "medium"),
    ("haridhan", "NA_HARIDHAN", "farmer-selected variety; SPIA DNA: mostly matched Indian accession UPRH265 (bgd_local_names)", "high"),
    ("horidhan", "NA_HARIDHAN", "farmer-selected variety; SPIA DNA: mostly matched Indian accession UPRH265 (bgd_local_names)", "high"),
    ("asiruddin", "NA_ASIRUDDIN", "local/traditional variety; no register entry", "high"),
    ("kajallata", "NA_KAJALLATA", "farmer/local name; no register entry or alias; origin not documented in the archive", "medium"),
    ("khudekajal", "NA_KHUDE_KAJAL", "local/traditional variety; no register entry", "high"),
    ("miniket", "NA_MINIKET", "trade/processing label; SPIA DNA: self-reported Miniket falls in three genetic clusters, one of them BRRI dhan57 (bgd_local_names); never one-to-one", "high"),
    ("bashmati", "NA_BASMATI", "Basmati-type aromatic rice; no Bangladesh release of this name", "high"),
    ("basmati", "NA_BASMATI", "Basmati-type aromatic rice; no Bangladesh release of this name", "high"),
    ("jamaibabu", "NA_JAMAI_BABU", "farmer/local name; no register entry or alias; origin not documented in the archive", "medium"),
    ("gutirajshahi", "NA_GUTI_SWARNA", "Swarna group (Guti Swarna / 'Rajshahi' / Lal Swarna), Indian-origin; one code bundles several Swarna-type names", "high"),
    ("gutiswarna", "NA_GUTI_SWARNA", "Swarna group, Indian-origin", "high"),
    ("swarna", "NA_SWARNA", "Swarna (MTU 7029), Indian release; BRRI dhan51 is Swarna-Sub1, a different variety", "high"),
    ("binnidhan", "NA_BINNI_DHAN", "local name (binni); no register entry", "high"),
    ("tepidhan", "NA_TEPI_DHAN", "local/traditional variety; no register entry", "high"),
    ("jirashail", "NA_JIRASHAIL", "Jirashail: not in register (listed in bgd_rice_not_approved_or_unresolved.csv as RICE-OLD_JIRASHAIL)", "high"),
    ("jira", "NA_JIRA", "Jira/Jirashail-type name; SPIA DNA: 'Jira' samples include BRRI dhan57 and other clusters (bgd_local_names); not one-to-one", "medium"),
    ("katari", "NA_KATARIBHOG", "Katari(bhog), local name; no register entry", "medium"),
    ("ronjit", "NA_RANJIT", "Ranjit, probably the Indian variety of that name (GloMIP lists an Indian Ranjit Sub-1); no Bangladesh register entry", "medium"),
    ("ranjit", "NA_RANJIT", "Ranjit, probably the Indian variety of that name (GloMIP lists an Indian Ranjit Sub-1); no Bangladesh register entry", "medium"),
]

# brand token (normalised label) -> (family label, regex over names, regex over developer)
NAMEFIELDS = ["variety_name", "official_name_en", "official_name_bn", "aliases", "popular_name"]
BRANDS = OrderedDict([
    ("hira", ("Hira (Supreme Seed)", r"hira|heera|হীরা|হীর-", None)),
    ("hs", ("HS (Supreme Seed HS- codes)", r"\bHS-?\s?\d|এইচ এস-", None)),
    ("lalteer", ("Lal Teer", r"lal ?teer|লাল ?তীর|লালতীর", r"lal ?teer|লাল ?তীর|লালতীর")),
    ("sonarbangla", ("Sonar Bangla", r"sonar ?bangla|সোনার বাংলা", None)),
    ("aloron", ("Aloron", r"aloron|আলোড়ন", None)),
    ("jagoron", ("Jagoron", r"jagoron|জাগরণ", None)),
    ("shakti", ("Shakti (BRAC)", r"shakti|শক্তি", None)),
    ("alok", ("Alok (ACI)", r"\ba+lok\b|আলোক", None)),
    ("taj", ("Taj", r"\btaj\b|তাজ", None)),
    ("surma", ("Surma (Syngenta)", r"surma|সুরমা", None)),
    ("tia", ("Tia", r"\btia\b|টিয়া", None)),
    ("janakraj", ("Janakraj", r"janak ?raj|জনক ?রাজ|জনকরাজ", None)),
    ("aftabhybrids", ("Aftab hybrids", None, r"aftab|আফতাব")),
    ("syngentahybrids", ("Syngenta hybrids", None, r"syngenta|সিনজেন")),
    ("az", ("Arize AZ- (Bayer)", r"\bAZ\s?\d|এজেড|এ জেড", None)),
    ("aci", ("ACI (all ACI brands)", None, r"\bACI\b|এসিআই|এ সি আই")),
    ("babylon", ("Babylon", r"babylon", r"babylon")),
    ("brac", ("BRAC", None, r"brac|ব্র্যাক|বর্যাক|ব্রাক")),
    ("ispahanihybrids", ("Ispahani hybrids", r"ispahani|ইস্পাহান", r"ispahani|ইস্পাহান")),
    ("krishibid", ("Krishibid", r"krishibid|কৃষিবিদ", r"krishibid|কৃষিবিদ")),
])
BRAND_SYNONYM = [("laltir", "lalteer"), ("sokti", "shakti"), ("aloran", "aloron"), ("jagoran", "jagoron"),
                 ("jonokraj", "janakraj"), ("aftabhyrbrids", "aftabhybrids"), ("heera", "hira")]


def family_members(token):
    _, rx_name, rx_dev = BRANDS[token]
    out = []
    for r in reg.itertuples():
        txt = " ".join(getattr(r, f) for f in NAMEFIELDS)
        if (rx_name and re.search(rx_name, txt, re.I)) or (rx_dev and re.search(rx_dev, r.developer, re.I)):
            out.append(r.variety_id)
    return sorted(out)


FAMILY = {t: family_members(t) for t in BRANDS}

# ----------------------------------------------------------------------------------------------
# extraction


def read_dta_labels(path, rice_only):
    it = pd.read_stata(path, iterator=True)
    vl = it.value_labels()
    varlist, lbllist = list(it._varlist), list(it._lbllist)
    it.close()
    rows = []
    for var, lname in zip(varlist, lbllist):
        if not lname or lname not in vl:
            continue
        d = vl[lname]
        lab_text = " ".join(map(str, d.values()))
        if len(re.findall(r"(?i)\bbr\b|bri |brri|binadhan|\bbina\b|hira|miniket|chandina", lab_text)) < 10:
            continue          # not a rice-variety list (crop lists, admin units ...)
        for code, lab in d.items():
            if rice_only and not (make_key(lab) or re.search(r"(?i)\bbina\b", str(lab))):
                continue      # i5_01 mixes varieties with machinery
            rows.append((var, str(int(code)), str(lab)))
    return rows


def parse_code_list(text):
    """'label...12 | label...13' -> [(code, label)]"""
    out = []
    for part in text.split(" | "):
        m = re.match(r"\s*(.*?)\.{3}\s*(-?\d+)\s*$", part.strip())
        if m:
            out.append((m.group(2), m.group(1).strip()))
    return out


def read_mixtape():
    rows = []
    t = (BGD / MIX_HTML).read_text(encoding="utf-8", errors="replace")
    txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    for m in re.finditer(r"(Code \d+): Paddy Rice - (.*?)(?= Code \d+: )", txt):
        for code, lab in parse_code_list(m.group(2)):
            rows.append((MIX_HTML, f"{m.group(1)}: Paddy Rice (Module H1, H1_01)", code, lab))
    for i, line in enumerate((BGD / MIX_TXT).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        m = re.match(r"\s*(Code \d+): Paddy Rice Varieties:\s*(.*)$", line)
        if m:
            for code, lab in parse_code_list(m.group(2)):
                rows.append((MIX_TXT, f"{m.group(1)}: Paddy Rice Varieties (line {i})", code, lab))
    return rows


def parse_code_list_loose(text):
    """Like parse_code_list, but accepts '..', '...' or '…' before the code and a trailing ';'."""
    out = []
    for part in re.split(r"\s*\|\s*", text):
        m = re.match(r"\s*(.*?)\s*(?:\.{2,}|…)\s*(-?\d+)\s*;?\s*$", part.strip())
        if m and m.group(1):
            out.append((m.group(2), m.group(1).strip()))
    return out


def md_plain(s):
    """strip Markdown bold markers and backslash escapes from a pandoc export line"""
    return re.sub(r"\\(.)", r"\1", s.replace("**", "")).strip()


AUG_CODE2 = re.compile(r"^(Code 2: Paddy Rice(?: Varieties)?(?: \(Updated\))?(?: HYV)?\s*[-:]\s*|Hybrid\s*:\s*)")


def read_mixtape_aug():
    """21 Aug 2026 questionnaire: the two Code 2 rice lists of module G1 and the rice rows of the I5 technology table.
    Returns (rows, rice_label_norms, nonrice_label_norms); the label sets are used to pick the rice rows out of the
    merged CAPI choice list."""
    rows, rice, nonrice = [], set(), set()
    lines = (BGD / MIX_AUG).read_text(encoding="utf-8", errors="replace").splitlines()
    var, in_g, in_i5 = None, False, False
    for line in lines:
        s = md_plain(line)
        if s.startswith("Code 2: Paddy Rice"):
            in_g = True
            var = ("G1 variety: Code 2 Paddy Rice Varieties (Updated)" if "(Updated)" in s
                   else "G1 variety: Code 2 Paddy Rice (original list)")
        elif in_g and s.startswith("Hybrid") and var and "(Updated)" in var:
            pass                                    # the Updated list continues on the 'Hybrid:' line
        elif in_g and re.match(r"^Code 9\b", s):
            in_g, var = False, None
        elif in_g and s:
            for code, lab in parse_code_list_loose(s):
                nonrice.add(norm(clean_label(lab)))
            var = None
            continue
        if in_g and var:
            for code, lab in parse_code_list_loose(AUG_CODE2.sub("", s)):
                rows.append((MIX_AUG, var, code, lab))
                rice.add(norm(clean_label(lab)))
            continue
        if re.match(r"^#+\s*Module I5\b", s):
            in_i5 = True
            continue
        if in_i5 and re.match(r"^#+\s", s):
            in_i5 = False
        if in_i5:
            m = re.match(r"^\|\s*(\w+)\s*\|\s*([^|]*?)\s*\|", s)
            if m and re.search(r"(?i)dhan|\bbina\b", m.group(2)):
                rows.append((MIX_AUG, "I5 technology list (rice rows)", m.group(1), m.group(2)))
    return rows, rice, nonrice


CAPI_FIELD = re.compile(r"^([a-z][a-z0-9_]*[a-z0-9])(?: \(required\))?$")


def read_capi(rice_norms, nonrice_norms):
    """Choice lists of the SurveyCTO forms as printed in the English printables (code and label on one line, or code
    on one line and label on the next; long labels wrap). A field is kept when its list holds at least five rice
    variety labels. The G1 paddy list is a merged crop list (CAPI review issue MX-123): only its rice rows are kept,
    i.e. labels that occur in the 21 Aug rice lists and in none of its other crop lists, plus residual codes."""
    import fitz          # PyMuPDF
    rows = []
    for f, _iv in CAPI_PDFS:
        p = BGD / f
        if not p.exists():
            print("missing", f)
            continue
        lines = []
        with fitz.open(p) as doc:
            for page in doc:
                lines += [ln.rstrip() for ln in page.get_text().splitlines()
                          if not re.match(r"^bihs_spia2026_\S+\.html\[", ln)]
        blocks, cur = [], None
        for ln in lines:
            m = CAPI_FIELD.match(ln.strip())
            if m and "_" in m.group(1):
                cur = (m.group(1), [])
                blocks.append(cur)
            elif cur:
                cur[1].append(ln)
        for field, body in blocks:
            items, i = [], 0
            while i < len(body):
                t = body[i].strip()
                m = re.match(r"^(-?\d+)\s+(\S.*)$", t)
                if m:
                    items.append([m.group(1), m.group(2)])
                elif re.fullmatch(r"-?\d+", t) and i + 1 < len(body) and body[i + 1].strip() \
                        and not re.fullmatch(r"-?\d+", body[i + 1].strip()):
                    items.append([t, body[i + 1].strip()])
                    i += 1
                elif items and t:
                    items[-1][1] += body[i] if body[i].startswith(" ") else body[i].strip()
                i += 1
            items = [(c, re.sub(r"\s+", " ", lab).strip()) for c, lab in items]
            if sum(1 for _, lab in items if make_key(lab) or re.search(r"(?i)\bbina\b", lab)) < 5:
                continue
            merged = any(re.search(r"(?i)lentil|masur", lab) for _, lab in items)
            for c, lab in items:
                if merged:
                    n = norm(clean_label(lab))
                    if not (GENERIC.match(lab.strip()) or (n in rice_norms and n not in nonrice_norms)):
                        continue
                elif not re.search(r"(?i)dhan|\bbina\b", lab):
                    continue                   # technology lists mix varieties with machinery
                rows.append((f, field, c, lab))
    return rows


# ----------------------------------------------------------------------------------------------
# matching

def res(vid="", mt="unmatched", conf="low", note="", cands=(), nrid=""):
    cands = list(cands)
    return dict(variety_id=vid, variety_name=REG_NAME.get(vid, ""), match_type=mt,
                n_candidates=len(cands) if cands else (1 if vid else 0),
                candidate_ids=" | ".join(cands), confidence=conf, note=note, non_register_id=nrid)


def key_from_label(lab):
    """official-series key from the label text, with how it was obtained."""
    c = clean_label(lab)
    m = re.match(r"^BD-(\d+)$", c.strip())
    if m:
        return make_key(f"BRRI dhan {m.group(1)}"), "bd"
    k = make_key(c)
    if k:
        return k, "make_key"
    m = re.match(r"(?i)^bina\s*[-–]?\s*(\d+)\b", c)
    if m:
        return f"BINADHAN{int(m.group(1))}", "bina"
    return None, None


def match(lab):
    c = clean_label(lab)
    n = norm(c)
    if GENERIC.match(c.strip()) or GENERIC.match(str(lab).strip()):
        note = next((v for k, v in GENERIC_NOTE.items() if n.startswith(k)), "residual / non-variety category")
        return res(mt="generic_label", conf="high", note=note)
    key, how = key_from_label(lab)
    if key:
        vid = f"RICE-{key}"
        if vid in REG_IDS:
            if how == "make_key":
                return res(vid, "exact_code_name", "high", "official series designation read from label")
            if how == "bina":
                return res(vid, "normalised_name", "medium", f"'{c}' read as Binadhan-{key[8:]} (BINA <n> shorthand)")
            return res(vid, "normalised_name", "high", "SPIA reference name BD-<n> read as BR<n> / BRRI dhan<n>")
        if vid in UNRES_IDS:
            st = UNRES_IDS[vid] or "approval not confirmed"
            return res(mt="unmatched", conf="medium",
                       note=f"{vid} is not in the register; listed in bgd_rice_not_approved_or_unresolved.csv ({st})")
        if key in ("BINADHAN1", "BINADHAN2", "BINADHAN3"):
            return res(mt="unmatched", conf="low",
                       note="the register has no Binadhan-1, -2 or -3 (BINA's earlier releases in the register are Iratom-24 and Binashail; Iratom-38 is listed as withdrawn); label cannot be resolved")
        return res(mt="unmatched", conf="low", note=f"label reads as {key} but no such register entry")
    for pre, nrid, note, conf in NOT_APPROVED:
        if n.startswith(pre):
            return res(mt="not_approved_variety", conf=conf, note=note, nrid=nrid)
    nb = n
    for a, b in BRAND_SYNONYM:
        nb = nb.replace(a, b)
    m = re.match(r"^([a-z]+?)(\d+)$", nb)
    if nb in BRANDS:
        fam = FAMILY[nb]
        return res(mt="brand_family", conf="high" if fam else "low", cands=fam,
                   note=f"brand family {BRANDS[nb][0]}: label names no specific product; all registered members listed")
    if m and m.group(1) in BRANDS:
        fam = FAMILY[m.group(1)]
        hit = [v for v in fam if norm(re.sub(r"\s*\(.*$", "", REG_NAME[v])) == nb]
        if len(hit) == 1:
            return res(hit[0], "normalised_name", "medium", f"brand + number matched to register name {REG_NAME[hit[0]]}")
        return res(mt="unmatched", conf="medium", cands=fam,
                   note=f"'{c}' is not a registered product; candidate_ids lists the registered {BRANDS[m.group(1)][0]} family for reference only")
    ids = sorted(name_index.get(n, ()))
    if len(ids) == 1:
        kind = name_kind[(n, ids[0])]
        conf = "medium" if re.fullmatch(r"[a-z]+", n) else "high"
        return res(ids[0], kind, conf, f"label equals register {'alias' if kind == 'alias' else 'name'} of {REG_NAME[ids[0]]}")
    if len(ids) > 1:
        return res(mt="alias", conf="low", cands=ids, note="label equals a name shared by several register entries")
    return res(mt="unmatched", conf="low", note="no register name, alias or local name matches this label")


# ----------------------------------------------------------------------------------------------
def load_overrides():
    ov = {}
    if not OVR.exists():
        return ov
    with open(OVR, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            ov[(r["source"], r["code"])] = r
    return ov


def apply_override(o, lab):
    m = re.search(r"label '([^']*)'", o["note"])
    if not m or norm(clean_label(m.group(1))) != norm(clean_label(lab)):
        print(f"WARNING override {o['source']}/{o['code']} label check failed: note={o['note'][:60]!r} label={lab!r}")
        return None
    cm = re.search(r"confidence:\s*(high|medium|low)", o["note"])
    conf = cm.group(1) if cm else "medium"
    v = o["variety_id"].strip()
    note = "manual override: " + o["note"]
    if " | " in v:
        return res(mt="alias", conf=conf, cands=[x.strip() for x in v.split("|")], note=note)
    if v.startswith("NA_"):
        cands = re.findall(r"candidate (RICE-[A-Z0-9_]+)", o["note"])
        return res(mt="not_approved_variety", conf=conf, note=note, nrid=v, cands=cands)
    if v in ("", "NONE"):
        return res(mt="unmatched", conf=conf, note=note)
    if v not in REG_IDS:
        print(f"WARNING override {o['source']}/{o['code']} points to unknown id {v}")
        return None
    mt = "alias" if re.search(r"\balias\b", o["note"]) else "normalised_name"
    return res(v, mt, conf, note)


def main():
    raw = []                       # (source, file, variable, code, label)
    for src, f, flt in DTA_SOURCES:
        p = BGD / f
        if not p.exists():
            print("missing", f)
            continue
        for var, code, lab in read_dta_labels(p, flt == "rice_only"):
            raw.append((src, f, var, code, lab))
    for f, var, code, lab in read_mixtape():
        raw.append(("MIXTAPE2026_draft", f, var, code, lab))
    aug_rows, aug_rice, aug_nonrice = read_mixtape_aug()
    for f, var, code, lab in aug_rows:
        raw.append(("MIXTAPE2026_0821", f, var, code, lab))
    for f, var, code, lab in read_capi(aug_rice, aug_nonrice):
        raw.append(("MIXTAPE2026_CAPI", f, var, code, lab))

    # SPIA DNA reference library; survey code -> label lookup used to verify the BD-<n> convention
    c2 = {k: v for s, f, var, k, v in raw if s == "BIHS2024_SPIA" and var == "c2paddy_mainvariety"}
    bref = pd.read_excel(BGD / DNA / "Barcode_reference_2024.xlsx", dtype=str).fillna("")
    dna_rows, dna_notes = [], {}
    for r in bref.itertuples():
        sc = r.c2paddy_sample.split(".")[0] if r.c2paddy_sample else ""
        note = f"reference sample; survey code c2paddy_sample={sc or 'none'}"
        if sc:
            sk = key_from_label(c2.get(sc, ""))[0]
            rk = key_from_label(r.variety_name)[0]
            note += f" = '{c2.get(sc, '?')}'" + ("; BD-<n> convention verified against survey label" if sk and sk == rk
                                                   else "; WARNING survey label does not match reference name")
        if r.comment:
            note += f"; SPIA comment: {r.comment}"
        dna_rows.append(("SPIA_DNA_reference", f"{DNA}/Barcode_reference_2024.xlsx", "variety_name", r.scan_barcode, r.variety_name))
        dna_notes[(r.scan_barcode, r.variety_name)] = note
    ares = pd.read_excel(BGD / DNA / "bangladesh_rice_assignment_results.xlsx", usecols=["Variety"], dtype=str)
    for v in sorted(ares.Variety.fillna("(blank)").unique(), key=lambda s: (not s.startswith("BD"), len(s), s)):
        dna_rows.append(("SPIA_DNA_reference", f"{DNA}/bangladesh_rice_assignment_results.xlsx", "Variety (assigned reference)", v, v))
    raw += dna_rows

    # one row per (source, code, label); variables and files pooled
    grp = OrderedDict()
    for src, f, var, code, lab in raw:
        k = (src, code, lab)
        g = grp.setdefault(k, {"files": [], "vars": []})
        if f not in g["files"]:
            g["files"].append(f)
        if var not in g["vars"]:
            g["vars"].append(var)

    ov = load_overrides()
    used_ov = set()
    out = []
    result = {}                      # (src, code, lab) -> match result, reused by the long file
    for (src, code, lab), g in grp.items():
        r = None
        o = ov.get((src, code))
        if o:
            r = apply_override(o, lab)
            if r:
                used_ov.add((src, code))
        if r is None:
            r = match(lab)
        if src == "SPIA_DNA_reference" and (code, lab) in dna_notes:
            r["note"] = (r["note"] + "; " if r["note"] else "") + dna_notes[(code, lab)]
        if src == "BIHS2024_SPIA" and g["vars"] == ["c2variety_num"]:
            r["note"] += "; c2variety_num holds SPIA's DNA-assigned variety, not the farmer report"
        m = re.search(r"(\d+)$", r["variety_name"])
        if (r["match_type"] == "exact_code_name" and src != "SPIA_DNA_reference" and m and code.isdigit()
                and int(m.group(1)) != int(code)):
            r["note"] += f"; code {code} is a list position, not the variety number"
        if (src, code) in CODE_NOTES:
            r["note"] += "; " + CODE_NOTES[(src, code)]
        if src == "MIXTAPE2026_CAPI" and any(v.startswith(("g1_paddyvariety", "hb_r3_05")) for v in g["vars"]):
            r["note"] += ("; g1_paddyvariety_* and hb_r3_05_1 use a merged crop list in which most rice codes were "
                          "overwritten by lentil, maize and potato varieties (CAPI review MX-123); only the rice rows "
                          "are listed, and their codes differ from the 21 Aug questionnaire")
        result[(src, code, lab)] = r
        out.append(dict(source=src, source_file="; ".join(g["files"]), variable="; ".join(g["vars"]),
                        code=code, label_as_printed=lab, **r))
    for k in ov:
        if k not in used_ov:
            print("WARNING override not applied:", k)

    df = pd.DataFrame(out)[COLS]
    df["_o"] = df.source.map({s: i for i, s in enumerate(SOURCE_ORDER)})
    df["_c"] = pd.to_numeric(df.code, errors="coerce")
    df = df.sort_values(["_o", "variable", "_c", "code"], kind="stable").drop(columns=["_o", "_c"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"wrote {OUT} ({len(df)} rows)")

    long = build_long(raw, result)
    long.to_csv(OUT_LONG, index=False, encoding="utf-8-sig")
    print(f"wrote {OUT_LONG} ({len(long)} rows; unique on source, instrument_version, variable, code)")
    na = build_non_register(long)
    cov, cg, extra = plot_tables(long, na)
    na = add_na_plot_counts(na, extra)
    na.to_csv(OUT_NA, index=False, encoding="utf-8-sig")
    print(f"wrote {OUT_NA} ({len(na)} rows)")
    write_report(df, long, cov, cg, extra)


# ----------------------------------------------------------------------------------------------
# long crosswalk, non-register names, plot-weighted coverage

KEY = ["source", "instrument_version", "variable", "code"]
REG_TYPE = dict(zip(reg.variety_id, reg.rice_type))
REG_CGIAR = dict(zip(reg.variety_id, reg.cgiar_role))


def sort_rows(d):
    d = d.copy()
    d["_o"] = d.source.map({s: i for i, s in enumerate(SOURCE_ORDER)})
    d["_c"] = pd.to_numeric(d.code, errors="coerce")
    return d.sort_values(["_o", "instrument_version", "variable", "_c", "code"], kind="stable").drop(columns=["_o", "_c"])


def build_long(raw, result):
    """one row per (source, instrument_version, variable, code); the compact file pools variables and drafts"""
    rows = OrderedDict()
    for src, f, var, code, lab in raw:
        iv = IV_BY_FILE.get(f) or IV_BY_SOURCE[src]
        k = (src, iv, var, code)
        if k in rows:
            if rows[k]["label_as_printed"] != lab:
                raise SystemExit(f"long crosswalk key {k} has two labels: {rows[k]['label_as_printed']!r} / {lab!r}")
            if f not in rows[k]["survey_file"].split("; "):
                rows[k]["survey_file"] += "; " + f
            continue
        r = result[(src, code, lab)]
        fam_type = fam_cg = ""
        if r["match_type"] == "brand_family" and r["candidate_ids"]:
            mem = r["candidate_ids"].split(" | ")
            types = {REG_TYPE.get(v, "") for v in mem}
            fam_type = "all_hybrid" if types == {"hybrid"} else "all_inbred" if types == {"inbred"} else "mixed"
            fam_cg = " | ".join(sorted({REG_CGIAR.get(v, "") for v in mem} - {""}))
        rows[k] = dict(source=src, instrument_version=iv, survey_file=f, variable=var, code=code, label_as_printed=lab,
                       **r, family_rice_type=fam_type, family_cgiar_roles=fam_cg)
    d = sort_rows(pd.DataFrame(list(rows.values()))[LONG_COLS])
    assert not d.duplicated(KEY).any(), "long crosswalk is not unique on its key"
    return d


def na_ids_defined():
    ids = {x[1] for x in NOT_APPROVED}
    ids |= {o["variety_id"].strip() for o in load_overrides().values() if o["variety_id"].strip().startswith("NA_")}
    return ids


def build_non_register(long):
    attr = pd.read_csv(NA_ATTR, dtype=str, encoding="utf-8-sig").fillna("")
    used = long[long.non_register_id != ""]
    ids = na_ids_defined() | set(used.non_register_id)
    missing = sorted(ids - set(attr.non_register_id))
    if missing:
        print("WARNING non-register ids without attributes in", NA_ATTR.name, missing)
    out = []
    for r in attr.itertuples():
        u = used[used.non_register_id == r.non_register_id]
        variants = sorted({re.sub(r"\.$", "", x).strip() for x in u.label_as_printed}, key=str.lower)
        occ = []
        for (s, iv), g in u.groupby(["source", "instrument_version"], sort=False):
            codes = sorted(set(g.code), key=lambda c: (len(c), c))
            occ.append(f"{s} {iv}: code {', '.join(codes)}")
        out.append(dict(non_register_id=r.non_register_id, name_std=r.name_std, name_variants=" | ".join(variants),
                        rice_type=r.rice_type, rice_type_basis=r.rice_type_basis, name_class=r.name_class,
                        likely_origin=r.likely_origin, origin_basis=r.origin_basis, cgiar_role=r.cgiar_role,
                        cgiar_center=r.cgiar_center, cgiar_basis=r.cgiar_basis, spia_dna_note=r.spia_dna_note,
                        spia_self_report_note=r.spia_self_report_note, in_crosswalk="Y" if len(u) else "N",
                        crosswalk_occurrences="; ".join(occ)))
    return pd.DataFrame(out)


# plot files: (source, round label, file, crop-code column or None, variety-code column)
PLOT_FILES = [
    ("BIHS2011_12", "BIHS 2011-12", f"{W}/BIHS 2011-2012/011_mod_h1_male.dta", "crop_a", "h1_01"),
    ("BIHS2015", "BIHS 2015", f"{W}/BIHS 2015-2016/015_r2_mod_h1_male.dta", "crop_a", "h1_01"),
    ("BIHS2018_19", "BIHS 2018-19", f"{W}/BIHS 2018-2019/BIHSRound3/Male/021_bihs_r3_male_mod_h1.dta", "crop_a_h1", "h1_01"),
    ("BIHS2024_SPIA", "SPIA 2024", f"{SPIA_FINAL}/SPIA_BIHS_2024_module_c2_4.dta", None, "c2paddy_mainvariety"),
]
CATS = ["register_variety", "brand_family", "not_approved_name", "other_unknown"]


def crop_class(label):
    """season and seed type of a BIHS crop-code label; None when the crop is not field rice"""
    s = str(label).lower()
    season = "aus" if re.search(r"aus|aush", s) else "aman" if "aman" in s else "boro" if "boro" in s else None
    if season is None:
        return None
    kind = "hybrid" if "hybrid" in s else "local" if re.search(r"local|\(l\)", s) else "hyv" if "hyv" in s else "unspecified"
    return season, kind


def read_plot_codes(path, crop_col, var):
    """only two columns: crop code and variety code (no household identifier); returns frame and crop labels"""
    it = pd.read_stata(path, iterator=True)
    vl = it.value_labels()
    lbl = dict(zip(it._varlist, it._lbllist))
    d = it.read(columns=[c for c in (crop_col, var) if c], convert_categoricals=False)
    it.close()
    return d, vl.get(lbl.get(crop_col, ""), {}) if crop_col else {}


def plot_tables(long, na):
    paths = [BGD / p[2] for p in PLOT_FILES]
    if not all(p.exists() for p in paths):
        print("plot coverage: survey .dta files not found; keeping the existing", COV.name, "and", COV_CGIAR.name)
        cov = pd.read_csv(COV, dtype={"share": float}) if COV.exists() else pd.DataFrame()
        cg = pd.read_csv(COV_CGIAR) if COV_CGIAR.exists() else pd.DataFrame()
        return cov, cg, {}
    ped = pd.read_csv(PEDSUM, dtype=str, encoding="utf-8-sig").fillna("")
    depth = dict(zip(ped.variety_id, ped.depth_to_cgiar))
    na_cg = dict(zip(na.non_register_id, na.cgiar_role))
    cov_rows, cg_rows, extra = [], [], {}
    for src, rnd, f, crop_col, var in PLOT_FILES:
        d, crop_lab = read_plot_codes(BGD / f, crop_col, var)
        d = d[d[var].notna()].copy()
        d["code"] = d[var].astype(int).astype(str)
        excluded = {}
        if crop_col:
            cls = d[crop_col].map(lambda c: crop_class(crop_lab.get(c, "")) if pd.notna(c) else None)
            for c, n in d.loc[cls.isna(), crop_col].value_counts().items():
                excluded[f"{int(c)} {crop_lab.get(c, '')}".strip()] = int(n)
            d["season"] = cls.map(lambda x: x[0] if x else None)
            d["seed_type"] = cls.map(lambda x: x[1] if x else None)
            d = d[cls.notna()]
        else:
            d["season"], d["seed_type"] = None, None
        lk = long[(long.source == src) & (long.variable == var)].drop_duplicates("code").set_index("code")
        d["match_type"] = d.code.map(lk.match_type).fillna("code_not_in_label_list")
        d["variety_id"] = d.code.map(lk.variety_id).fillna("")
        d["nrid"] = d.code.map(lk.non_register_id).fillna("")
        d["cat"] = "other_unknown"
        d.loc[d.match_type == "brand_family", "cat"] = "brand_family"
        d.loc[d.match_type == "not_approved_variety", "cat"] = "not_approved_name"
        d.loc[d.variety_id != "", "cat"] = "register_variety"
        d["cg"] = d.variety_id.map(REG_CGIAR).fillna("")
        d["dp"] = d.variety_id.map(lambda v: "" if not v else ("none" if depth.get(v, "") == "" else
                                                              "3+" if int(depth[v]) >= 3 else depth[v]))
        d["cg_cat"] = d.cat
        reg_m = d.cat == "register_variety"
        d.loc[reg_m, "cg_cat"] = "register cgiar_role " + d.loc[reg_m, "cg"]
        na_m = d.cat == "not_approved_name"
        d.loc[na_m, "cg_cat"] = "not_approved_name cgiar_role " + d.loc[na_m, "nrid"].map(na_cg).fillna("unassigned")
        d["dp_cat"] = d.cat
        d.loc[reg_m, "dp_cat"] = "register depth_to_cgiar " + d.loc[reg_m, "dp"]
        seasons = ["all"] + ([s for s in ("aus", "aman", "boro") if (d.season == s).any()] if crop_col else [])
        for s in seasons:
            sub = d if s == "all" else d[d.season == s]
            n = len(sub)
            for c in CATS:
                k = int((sub.cat == c).sum())
                cov_rows.append(dict(round=rnd, season=s, category=c, n_plots=k, denominator=n, share=round(k / n, 4)))
            for dim, col in [("cgiar_role", "cg_cat"), ("depth_to_cgiar", "dp_cat")]:
                vc = sub[col].value_counts()
                for c in sorted(vc.index, key=lambda x: (not x.startswith("register"), x)):
                    cg_rows.append(dict(round=rnd, season=s, dimension=dim, category=c, variety_id="", variety_name="",
                                        cgiar_role="", n_plots=int(vc[c]), denominator=n, share=round(vc[c] / n, 4)))
            top = sub[sub.cat == "register_variety"].variety_id.value_counts().head(10)
            for i, (v, k) in enumerate(top.items(), 1):
                cg_rows.append(dict(round=rnd, season=s, dimension="top10_register_variety", category=f"rank {i}",
                                    variety_id=v, variety_name=REG_NAME.get(v, ""), cgiar_role=REG_CGIAR.get(v, ""),
                                    n_plots=int(k), denominator=n, share=round(k / n, 4)))
        oth = d[d.cat == "other_unknown"]
        extra[rnd] = dict(
            n=len(d), excluded=excluded, no_row=int((d.match_type == "code_not_in_label_list").sum()),
            other_by_type=(oth.seed_type.value_counts(normalize=True).round(3).to_dict() if crop_col else {}),
            other_top=[(c, lk.label_as_printed.get(c, "?"), int(k)) for c, k in oth.code.value_counts().head(4).items()],
            na_counts=d[d.nrid != ""].nrid.value_counts().to_dict())
    cov, cg = pd.DataFrame(cov_rows), pd.DataFrame(cg_rows)
    COV.parent.mkdir(parents=True, exist_ok=True)
    cov.to_csv(COV, index=False, encoding="utf-8")
    cg.to_csv(COV_CGIAR, index=False, encoding="utf-8")
    print(f"wrote {COV} ({len(cov)} rows) and {COV_CGIAR} ({len(cg)} rows)")
    return cov, cg, extra


def add_na_plot_counts(na, extra):
    def fmt(nrid):
        parts = []
        for rnd, e in extra.items():
            k = e["na_counts"].get(nrid, 0)
            if k:
                parts.append(f"{rnd}: {k} ({100 * k / e['n']:.1f}%)")
        return "; ".join(parts)
    na = na.copy()
    if extra:
        na["rice_plot_reports"] = na.non_register_id.map(fmt)
    elif OUT_NA.exists():          # survey files absent: keep the counts of the last full build
        old = pd.read_csv(OUT_NA, dtype=str, encoding="utf-8-sig").fillna("")
        na["rice_plot_reports"] = na.non_register_id.map(dict(zip(old.non_register_id, old.get("rice_plot_reports", ""))))
    else:
        na["rice_plot_reports"] = ""
    return na


# ----------------------------------------------------------------------------------------------
def md(s):
    return str(s).replace("|", "/")


def code_meaning(df, src, var):
    sub = df[(df.source == src) & df.variable.str.split("; ").apply(lambda v: var in v)]
    return {int(c): (vid or nrid or norm(lab)) for c, vid, nrid, lab in
            zip(sub.code, sub.variety_id, sub.non_register_id, sub.label_as_printed) if c.lstrip("-").isdigit()}


def coverage_section(cov, cg, extra):
    """plot-weighted match rates (A2-03), the crop_a rule for 2011-12 (A2-04) and CGIAR content of plot reports"""
    if cov is None or not len(cov):
        return ["## Plot-weighted coverage", "", "The survey .dta files were not available when this report was built.", ""]
    pct = lambda x: f"{100 * x:.1f}"
    lab = {"register_variety": "one register variety", "brand_family": "brand family",
           "not_approved_name": "non-approved name", "other_unknown": "other or unknown"}
    a = cov[cov.season == "all"]
    rounds = list(dict.fromkeys(a["round"]))
    L = ["## Plot-weighted coverage", "",
         "Code counts overstate what the crosswalk resolves, because the codes that stay unresolved are among the most "
         "often reported. The table below weights each code by the number of rice plot reports that carry it. The "
         "denominator is every rice plot report with a variety code: in the BIHS rounds, rows of the H1 plot module "
         "whose crop code is a field-rice crop (Aus, Aman or Boro, local, HYV or hybrid) and whose `h1_01` is not "
         "missing; in SPIA 2024, every row of module C2 with `c2paddy_mainvariety` (the plots sampled for DNA "
         "fingerprinting). Only the crop-code and variety-code columns were read, and only counts are kept. 'One "
         "register variety' covers exact_code_name, normalised_name and single-candidate alias rows; 'other or unknown' "
         "covers residual categories, unmatched labels, ambiguous aliases and codes absent from the label list. Counts by "
         "season, and the CGIAR breakdown below, are in `06_validation/crosswalk_plot_coverage.csv` and "
         "`06_validation/crosswalk_plot_cgiar.csv`.", "",
         "| round | rice plot reports | " + " | ".join(lab[c] for c in CATS) + " |", "|---|---:|" + "---:|" * len(CATS)]
    for r in rounds:
        g = a[a["round"] == r].set_index("category")
        L.append(f"| {r} | {int(g.denominator.iloc[0]):,} | " + " | ".join(pct(g.share[c]) + "%" for c in CATS) + " |")
    L.append("")
    reg = {r: a[(a["round"] == r) & (a.category == "register_variety")].share.iloc[0] for r in rounds}
    bihs = [r for r in rounds if r.startswith("BIHS")]
    L.append(f"In the three BIHS rounds between {pct(min(reg[r] for r in bihs))} and {pct(max(reg[r] for r in bihs))} "
             f"percent of rice plot reports resolve to a single approved variety, against {pct(reg['SPIA 2024'])} percent in "
             "the SPIA 2024 DNA plots. Non-approved names alone take "
             + ", ".join(f"{pct(a[(a['round'] == r) & (a.category == 'not_approved_name')].share.iloc[0])} percent in {r}"
                         for r in rounds) + ". " +
             " ".join(f"In {r}, {sum(e['excluded'].values()):,} report{'s' if sum(e['excluded'].values()) > 1 else ''} "
                      f"with a variety code {'sit' if sum(e['excluded'].values()) > 1 else 'sits'} on a crop code that is "
                      f"not field rice ({'; '.join(f'{k}: {v}' for k, v in e['excluded'].items())}) and "
                      f"{'are' if sum(e['excluded'].values()) > 1 else 'is'} left out of the denominator."
                      for r, e in extra.items() if e.get("excluded")) +
             " A researcher should expect between half and three fifths of BIHS rice plot reports, not the code-level "
             "share, to merge to a register variety; the rest need the brand, non-approved and residual categories "
             "handled explicitly.")
    L.append("")
    e = extra.get("BIHS 2011-12")
    if e:
        t = e["other_by_type"]
        top = "; ".join(f"code {c} '{lb}': {k:,}" for c, lb, k in e["other_top"])
        L.append("**BIHS 2011-12 and the crop code.** The 2011-12 variety list has no local or landrace names, so local "
                 "varieties are recorded as 'other' (codes 54 and 74). The crop code `crop_a` separates local, HYV and "
                 "hybrid rice and has to be read with `h1_01`. Among 2011-12 rice plot reports that end in 'other or "
                 f"unknown' ({top}), {pct(t.get('local', 0))} percent carry a local crop code (crop_a 11, 12, 14, 15), "
                 f"{pct(t.get('hyv', 0))} percent an HYV code (13, 16, 18, 19) and {pct(t.get('hybrid', 0))} percent a "
                 "hybrid code (17, 20). The crosswalk rows for codes 54 and 74 carry this rule in their note. Crop code "
                 "701 (paddy seedling) is a seedbed, not a plot, and is excluded.")
        L.append("")
    if cg is not None and len(cg):
        c = cg[(cg.season == "all") & (cg.dimension == "cgiar_role")]
        cols = [f"register cgiar_role {k}" for k in "12345"]
        L += ["## CGIAR content of rice plot reports", "",
              "Shares of all rice plot reports with a variety code, by the register's `cgiar_role` of the resolved "
              "variety. Non-approved names are coded with the `cgiar_role` assigned in `bgd_non_register_names.csv` "
              "(NERICA 1, every other name 5). Brand families and residual codes have no code. The same counts by "
              "`depth_to_cgiar`, by season, and the ten most reported varieties per round are in "
              "`06_validation/crosswalk_plot_cgiar.csv`.", "",
              "| round | code 1 | code 2 | code 3 | code 4 | code 5 | non-approved (all codes) | brand family | other or unknown |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for r in dict.fromkeys(c["round"]):
            g = c[c["round"] == r].set_index("category").share
            na_s = g[[i for i in g.index if i.startswith("not_approved")]].sum()
            L.append(f"| {r} | " + " | ".join(pct(g.get(k, 0)) + "%" for k in cols) +
                     f" | {pct(na_s)}% | {pct(g.get('brand_family', 0))}% | {pct(g.get('other_unknown', 0))}% |")
        L.append("")
        t = cg[(cg.season == "all") & (cg.dimension == "top10_register_variety") & (cg.category == "rank 1")]
        L.append("The most reported register variety is " + "; ".join(
            f"{x.variety_name} in {x['round']} ({pct(x.share)} percent, code {x.cgiar_role})" for _, x in t.iterrows()) +
            ". Self-reports are not grain identity: SPIA's DNA study finds BRRI dhan28 and dhan29 over-reported and BRRI "
            "dhan57 and dhan89 under-reported (SPIA 2025, p.50).")
        L.append("")
    return L


def write_report(df, long=None, cov=None, cg=None, extra=None):
    n_aug_i5 = int(((long.source == "MIXTAPE2026_0821") & long.variable.str.startswith("I5")).sum()) if long is not None else 0
    MT = ["exact_code_name", "normalised_name", "alias", "brand_family", "not_approved_variety", "generic_label", "unmatched"]
    tab = df.pivot_table(index="source", columns="match_type", values="code", aggfunc="count", fill_value=0)
    tab = tab.reindex(index=[s for s in SOURCE_ORDER if s in tab.index], columns=MT, fill_value=0)
    # how often the same code means different things across the main farmer-report lists
    lists = {"BIHS 2011-12": code_meaning(df, "BIHS2011_12", "h1_01"), "BIHS 2015": code_meaning(df, "BIHS2015", "h1_01"),
             "BIHS 2018-19": code_meaning(df, "BIHS2018_19", "h1_01"), "SPIA 2024": code_meaning(df, "BIHS2024_SPIA", "b2paddy_variety")}
    names = list(lists)
    diffs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = lists[names[i]], lists[names[j]]
            shared = sorted(set(a) & set(b))
            nd = sum(a[c] != b[c] for c in shared)
            diffs.append(f"{names[i]} and {names[j]} share {len(shared)} code numbers, of which {nd} mean something different")
    L = ["# Crosswalk from survey and DNA variety codes to the rice register", "",
         f"Built by `scripts/build_crosswalk.py`. Outputs: `05_output/final/bgd_variety_crosswalk.csv` ({len(df)} rows, "
         "compact, for reading), `05_output/final/bgd_variety_crosswalk_long.csv` "
         f"({len(long) if long is not None else 'n.a.'} rows, the file to merge on), "
         "`05_output/final/bgd_non_register_names.csv` (attributes of the `NA_` identifiers), "
         "`06_validation/crosswalk_plot_coverage.csv` and `06_validation/crosswalk_plot_cgiar.csv`. Hand decisions: "
         "`04_working/crosswalk_manual_overrides.csv` and `04_working/crosswalk_non_register_attributes.csv`.", "",
         "## Which file to merge on", "",
         "Merge survey data on `bgd_variety_crosswalk_long.csv`. It has one row per source, instrument version, variable "
         "and code, and the build asserts that this key is unique, so a left join of a survey variable on (source, "
         "instrument_version, variable, code) can never duplicate a plot. The compact `bgd_variety_crosswalk.csv` is "
         "kept unchanged in layout for existing users: it pools the variables that share a code and label into one "
         "semicolon-joined `variable` cell and pools the MIXTAPE drafts under one source, so it has to be exploded and "
         "filtered before any merge. In the long file the March and May 2026 drafts are separate instrument versions "
         "(they number codes 104 and up differently), as are the 21 August 2026 questionnaire and the two CAPI "
         "printables. Brand-family rows in the long file also carry `family_rice_type` (all_hybrid, all_inbred or "
         "mixed) and `family_cgiar_roles` (the distinct cgiar_role codes of the members), which bound what a brand "
         "report can mean.", "",
         "## What was matched and how", "",
         "Each row of the crosswalk is one code in one code list, keyed on source, code and the label exactly as printed. "
         "When the same code and label recur across several variables or files of one survey round (for example `h1_01`, `i4_02` "
         "and the community module in BIHS 2018-19), they share one row and the variables are listed together. Matching uses the "
         "label text only and never the code number. The numbering differs between rounds in ways that make code-based merging "
         "unsafe. In BIHS 2011-12, BIHS 2015, SPIA 2024 and the May 2026 MIXTAPE draft code 13 is 'Gazi BR-14' and the BR and "
         "BRRI dhan numbers then run one ahead of the code, so code 28 is BRRI dhan29. BIHS 2018-19 skips code 13 instead, so "
         "there code 28 is BRRI dhan28. SPIA 2024 then inserts BRRI dhan70-106 at codes 69-105, which moves every local and "
         "hybrid name: code 74 is Miniket in BIHS 2015 and BRRI dhan75 in SPIA 2024. Across the farmer-report lists, " +
         "; ".join(diffs) + ". Rows where the code differs from the variety number carry a note.", "",
         "Labels that name an official series designation (BR, BRRI dhan, BRRI hybrid dhan, Binadhan, Iratom, Binashail, BU) are read "
         "with the archive's `make_key` and coded `exact_code_name`. The shorthand 'BINA <n>' is read as Binadhan-n with medium "
         "confidence (`normalised_name`). The SPIA reference names 'BD-<n>' are read as BR n or BRRI dhan n (`normalised_name`, "
         "high confidence), and this reading was checked row by row: the reference library records the survey code of each "
         "reference sample (`c2paddy_sample`), and for every reference sample the survey label behind that code names the same "
         "variety. Labels equal to a register alias or a vetted local name are coded `alias`. Hybrid trade names that cover "
         "several registered products (Hira, Lal Teer, HS, Sonar Bangla, Jagoron, Alok, Taj, Surma, Janakraj and the company "
         "residuals added by SPIA such as 'Aftab hybrids' or 'BRAC') are coded `brand_family`, with every registered member in "
         "`candidate_ids` and no `variety_id`. Widely grown names without a Bangladesh approval (Miniket, the Swarna group, "
         "Haridhan, Kajallata, Jira, Katari, Ranjit and local landraces) are coded `not_approved_variety` with a stable `NA_` "
         "identifier in `non_register_id`. Residual categories such as 'Others', 'Do not know', 'Mota' and 'Bhojon "
         "(white/coarse)' are `generic_label`. An unmatched row may still list candidates when the label names an unregistered "
         "member of a known brand (for example 'Shakti 1'); those candidates are for reference and are not a match.", "",
         "## Counts by source", "",
         "| source | rows | " + " | ".join(MT) + " |", "|---|---:|" + "---:|" * len(MT)]
    for s, r in tab.iterrows():
        L.append(f"| {s} | {int(r.sum())} | " + " | ".join(str(int(r[m])) for m in MT) + " |")
    L.append("")
    for s in tab.index:
        r = tab.loc[s]
        sub = df[df.source == s]
        reg_n = int(r["exact_code_name"] + r["normalised_name"] + r["alias"])
        hand = int(sub.note.str.startswith("manual override").sum())
        L.append(f"**{s}.** Of {len(sub)} code rows, {reg_n} resolve to a single register variety, "
                 f"{int(r['brand_family'])} are brand families, {int(r['not_approved_variety'])} are non-approved names, "
                 f"{int(r['generic_label'])} are residual categories and {int(r['unmatched'])} stay unmatched; {hand} row{"" if hand == 1 else "s"} rest{"s" if hand == 1 else ""} on "
                 "a manual override. Files read: " +
                 ", ".join(f"`{f}`" for f in sorted({x for v in sub.source_file for x in v.split('; ')})) + ".")
        L.append("")
    L += coverage_section(cov, cg, extra or {})
    L += ["## Source notes", "",
          "BIHS 2011-12 has a single 74-code list (`h1_01`) in which the BRRI dhan series is written 'br 27' or 'bri rice br-40'; "
          "all of these resolve. BIHS 2015 (128 codes, used in `h1_01` and `i4_02`) and BIHS 2018-19 (154 codes, used in `h1_01`, "
          "`i4_02` and community module L1) add local names and hybrid trade names. The technology lists `i5_01` in 2015 and "
          "2018-19 mix machinery with a few varieties; only their rice rows are included, and their codes (2 = BRRI dhan41) are a "
          "numbering of their own.", "",
          "SPIA BIHS 2024 keeps the BIHS 2015 codes 1-68 and renumbers from 69 on, as described above. The field list "
          "(`b2paddy_variety`, the seedbed variables and the intercrop variable) runs to code 192, where codes 180-192 were added "
          "after fieldwork from 'other, specify' answers; `c2paddy_mainvariety` adds codes 193-214, mostly company residuals. Code "
          "128 reads 'ACI 5' in the field list but 'ACI' in `c2paddy_mainvariety`, so it appears twice. `c2variety_num` is a "
          "separate 27-code list holding SPIA's DNA-assigned variety (code 1 = BRRI dhan100) and must not be read with the "
          "farmer-report list. Module b1_5 is read from the copy of the SPIA release under `hilsa_feasibility/external`, because "
          "the SPIA folder under `BIHS data, shape files and SPIA 2024 wave` does not contain it.", "",
          "The two MIXTAPE drafts disagree with each other. The 15 May 2026 draft (H1_01, Code 2; identical in the 12 May HTML) "
          "reuses the BIHS 2015 list, ending at Robi = 128. The 3 March 2026 draft agrees on codes 1-103 and then renumbers: "
          "BINA 6-15 sit at 104-113 (May skips BINA 9, as BIHS 2015 did), BRRI dhan70-108 at 114-152, BRRI hybrid 5-8 at 153-156, "
          "Binadhan-17 to -26 at 157-166, BINA 16 at 167, Binashail at 168, Iratom-24 at 169 and Iratom-38 at 170. Code 107 is "
          "therefore Binadhan-10 in May and Binadhan-9 in March, and code 114 is Binashail in May and BRRI dhan70 in March. The "
          "May list also omits every release after BRRI dhan69 and Binadhan-16, so newer varieties would fall into 'Other'. The "
          "range summary in `Survey_20260427/MODULE I.md` (code list I.XX-1) is not a usable code list (it gives '26-70' for BRRI "
          "dhan27-69 and assigns 116 to both BINA 16 and Taj) and was not ingested.", "",
          "The 21 August 2026 questionnaire (`Survey/MIXTAPE Survey_08_21_2026.docx.md`, source `MIXTAPE2026_0821`) "
          "prints two Code 2 lists for the G1 variety question. The first repeats the May list (1-128) label for label. "
          "The second, headed 'Updated', is the 3 March numbering (codes 1-82 and 85-170, the same labels) extended by "
          "BRRI dhan109-118 (171-180), BRRI hybrid dhan9 and 10 (181-182), Binadhan-27 and -28 (183-184), the "
          "university varieties BU, GAU and BAU (185-191), Mini Shail/Rabi dhan-1 (192), ACI dhan1, Lal Teer hybrid "
          "dhan3 and Ispahani hybrid dhan9 (193-195). The two lists are kept as separate variables of one instrument "
          "version, because code 104 and up mean different things in them. Its I5 technology table lists "
          f"{n_aug_i5} rice varieties numbered 1-25 and then '25a' to '25bf', a numbering of its own. 'BAU dhan-1 "
          "(BAU-63)' is read as the registered BAU-63, as the label itself says; 'Mini Shail/Rabi dhan-1' pairs RU "
          "dhan1 (Rabi dhan1, an inbred) with ACI hybrid dhan16 (Minishail 1) and is left ambiguous; Ispahani hybrid "
          "dhan9 is not in the register (meetings to 115).", "",
          "No XLSForm of the MIXTAPE CAPI is on disk (the SurveyCTO folder is empty). The fielded choice lists were "
          "therefore read from the SurveyCTO printables of 14 October 2026 (`Survey/bihs_spia2026_male_resp_V1_printable_"
          "English.pdf` and `..._hhq_training_v2_all_printable_English.pdf`, source `MIXTAPE2026_CAPI`, one instrument "
          "version per form). They differ from the questionnaire in a way that matters for any merge. The G1 variety "
          "fields (`g1_paddyvariety_1` to `_3`, and `hb_r3_05_1`) use a 196-code list in which most rice codes were "
          "overwritten by lentil, maize and potato varieties, as the October CAPI review recorded (issue MX-123): only "
          "BR9 and BR10 (codes 9, 10), Shapla, Bashmati, Jamaibabu, Guti/Rajshahi/Lalshorna and Bhojon (76-80) and the "
          "varieties from Binadhan-17 on (155-193, two below the questionnaire's 157-195) survive. Only those rice rows "
          "are in the crosswalk; 'Lal Teer' (code 43) sits in the maize block and is left out. BRRI dhan28, dhan29 and "
          "every other mainstream BRRI variety cannot be recorded in these fields as printed. The I5 technology fields "
          "(`i5_sel_grp1`, `i5_sel_grp2` and the `hbr*_code_lookup` fields) number 48 rice varieties 1-48, which again "
          "differs from the questionnaire's I5 table.", "",
          "The SPIA DNA reference library (`Barcode_reference_2024.xlsx`) has 110 reference samples: BD-1 to BD-106 for BR and "
          "BRRI dhan varieties, with gaps, and ten Binadhan varieties, including Binadhan-26, which SPIA notes was not on the "
          "survey option list. Reference rows are keyed on the sample barcode. The crosswalk also lists every distinct reference "
          "name used in the assignment results file, keyed on the name itself, so assignments can be joined directly. The "
          "farmer-reported names in `ref_clusters_no_hybrids_with_HH_Ids.csv` repeat survey labels already covered and were not "
          "added. The 6830_Replication_Group folder holds a psychology replication unrelated to rice and has no variety material; "
          "the CG_Stocktake workbooks list CGIAR innovations rather than survey codes.", "",
          "## Main ambiguities", "",
          "Brand families cannot be resolved without seed-packet or DNA evidence: 'Hira' alone has "
          f"{len(FAMILY['hira'])} registered members and 'ACI' {len(FAMILY['aci'])}. Numbered trade names were resolved only when "
          "the number identifies one registered product (Hira 2, Hira 6, Aloron 2, and Shakti 2 through the Bangla alias of "
          "Brac-5). 'Hira 19' matches Bangla aliases on two Supreme Seed registrations and is left ambiguous. 'Shakti 1', "
          "'Aloron 1' and 'ACI 5' name products that are not in the register. 'Paijam' is kept outside the register although "
          "Pajam (RICE-OLD_PAJAM) is registered, because SPIA found most self-reported Paijam samples to be Patisail; the "
          "registered Pajam appears only as a candidate. 'BINA 1' to 'BINA 3' match no release. Several SPIA additions rest on "
          "a single judgement recorded in the override file (Bongobondhu as BRRI dhan100, Tej Gold and Dhani Gold as the Bayer "
          "registrations carrying those Bangla names, Aftab LP 108, Aftab 70 and NAFCO 2). Finally, SPIA's DNA study shows that "
          "farmer reports of BRRI dhan29 are often BRRI dhan89 and that 'Miniket' and 'Jira' include BRRI dhan57; the crosswalk "
          "records what the label says, not what the grain is.", "",
          "## Unmatched labels", "",
          "The following labels have no register id. Most are short trade or local names (Shapla, Shonali, Padma, Bijoy, Borkot, "
          "Raja, Chitra, Shobujmoti, Kajol, Robi) that appear in every list since BIHS 2015 and match no registered name, alias "
          "or local name; they are left open rather than guessed. Each row in the crosswalk carries its own note.", "",
          "| label | where (source: code) | note |", "|---|---|---|"]
    un = df[df.match_type == "unmatched"].copy()
    un["k"] = un.label_as_printed.map(lambda x: norm(clean_label(x)))
    for k, g in un.groupby("k", sort=False):
        where = "; ".join(f"{s}: {c}" for s, c in zip(g.source, g.code))
        L.append(f"| {md(g.label_as_printed.iloc[0])} | {md(where)} | {md(g.note.iloc[0])} |")
    L.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
