"""Parent -> child pedigree edges for the rice register, and distance to the nearest CGIAR line.

Reads   05_output/final/bgd_rice_varieties.csv      (pedigree, breeding_line, aliases, cgiar_* columns)
        05_output/final/bgd_nsb_decisions_full.csv  (pedigree_cross, fallback only)
        04_working/evidence_corrections.csv         (values already dropped by the coordinator are not re-used)
        03_extracted/tables/raitzer2015_bd_varieties.csv (published Raitzer et al. 2015 weights, for the check)
Writes  05_output/final/bgd_pedigree_edges.csv
        05_output/final/bgd_pedigree_summary.csv
        05_output/final/bgd_pedigree_ancestors.csv   (every ancestor path to generation 5, with nominal genetic shares)
        05_output/final/bgd_pedigree_founders.csv    (register descendants of every ancestor, by decade)
        05_output/final/bgd_lineage_graph.json       (nodes and parent -> child edges for the website)
        06_validation/cgiar_spia_concordance.csv     (register cgiar_role against SPIA 2025 Table 27 classes)

Attribution measures (added 2026-11-10 for the round-1 review, A2-05/06/07; see function attribution())
- contribution_share: nominal genetic share of an ancestor under equal parental contribution, 0.5 per generation;
  'A*n/B' gives A (1 - 0.5**n) and B 0.5**n (BC1 = A*2/B: 0.75); BCn printed as such = n+1 doses; a mutant,
  somaclone or selection source has share 1 at generation 0. A child whose parent shares add to more than 1 is rescaled.
- irri_share_nominal / cgiar_share_nominal: sum of the shares of the first IRRI (any CGIAR) line on each path, up to
  generation 3 (great-grandparents); 1 for a CGIAR line itself.
- irri_weight_raitzer: Raitzer et al. (2015, pp. 31-32, Table 2.1): last-cross rule (CGIAR line released directly, or a
  mutant/selection of one = 1) and otherwise the geometric rule for a NARS cross (breeding credit 0.5 to the NARS; the
  other 0.5 by pedigree, 0.25 / 0.125 / 0.125 for the parent / grandparent / great-grandparent generations). A CGIAR
  ancestor at generation g earns share x (sum of the generation weights from g to 3), i.e. its ancestors count as CGIAR.
- share_untraced_weight: the part of that 0.5 whose CGIAR status is unknown (above untraced lines, and the untraced line
  itself unless it is a Bangladeshi institute line). irri_weight_raitzer + share_untraced_weight is an upper bound.

Parsing rules (written for the CGIAR recode review, 06_validation/cgiar_recode_memo.md)
- Purdy notation: '/' first-order cross, '//' second, '///' third, '/n/' n-th. The highest-order separator splits the
  child's two direct parents (generation 1); a side that is itself a cross is an unnamed F1 whose parents are
  generation 2, and so on. ' x ', '×' and ' and ' are first-order separators.
- 'A*n/B': A is the recurrent parent with backcross_dose n, B the donor. A lone '*' with no number is printed but
  unexplained (GloMIP style) and is dropped with a note.
- 'mutant of X', 'somaclonal variant of X', 'selection from X', 'derived from X', 'advance line of X': X is the
  mutant / somaclone / selection source. Such an edge has generation 0: the derivative sits in the same generation as
  its source and inherits the source's ancestry.
- A parent label is resolved to a register variety (parent_id) only by identity, never by similarity:
  (a) lib_keys.make_key on a label that is a variety name (BR 4, BRRI dhan29, ব্রি ধান২৯, Iratom-24, IR 8), never on a
      line code; (b) exact match with a register name or alias; (c) the label equals a register breeding line or is a
      hyphen-bounded prefix of it (BR51-46-5 -> BR10, line BR51-46-5-HR65). A label that shares the cross number of a
      register line but is a different selection (KN1B-361-1-8-6-9 vs BR17's KN-1B-361-1-8-6-10) is a sister line: it
      gets no parent_id, but its parents are taken to be those of the documented cross. The note says so.
- CGIAR lines: IR + digits (IR8, IR 58025A, IR09F436), IRBB/IRBL lines, 'IRRI <n>' lines, IRGC accessions (IRRI),
  NERICA and WAB lines (AfricaRice); a register variety whose own evidence makes it a CGIAR line (cgiar_role 1, after
  the demotions in DEMOTE below). NSIC, PSBRc, OM, CR, BG, IET, TCCP and similar designations are not CGIAR lines
  unless a parenthetical IR designation is printed with them (NSIC Rc 106 (IR61920-3B-22-2-1)).
- depth_to_cgiar: 0 = the variety is a CGIAR line or a mutant/somaclone/selection of one; otherwise the smallest
  generation number at which a CGIAR line appears, recursing through register parents and sister-line crosses, max 5.
- implied_cgiar_role (summary, working column): 1 CGIAR line itself; 2 depth <= CODE2_MAX (5 since the PI decision of 2026-10-08) or IRRI ancestry
  stated without a named line; 3 current code 3 kept; 4 parents parsed, no CGIAR line within MAXD; 5 otherwise.
  It is a check against the register, not a value written to it.
"""
import re
import sys
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lib_keys import make_key  # noqa: E402

REG_FILE = "05_output/final/bgd_rice_varieties.csv"
DEC_FILE = "05_output/final/bgd_nsb_decisions_full.csv"
MAXD = 5               # depth is traced this far
CODE2_MAX = 5          # PI decision 2026-10-08: code 2 = documented CGIAR parent or earlier ancestor (to MAXD); was 2 (2026-10-06)
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
DERIV_ROLES = {"mutant_source", "somaclone_source", "selection_source"}

# Register code-1 rows that are not CGIAR lines on the evidence (see the memo): they are kept out of the
# 'CGIAR line itself' set. PROMOTE adds rows whose own line is an IRRI cross selected elsewhere.
DEMOTE = {
    "RICE-BRRI_DHAN92": "Rice Profile id 100: line IRGC103918 collected from IRRI, anther-cultured and crossed twice with a "
                        "BRRI line at BRRI; breeding line BR(BE)6158RWBC2-1-2-1-1 is a BRRI line",
    "RICE-BRRI_HYBRID4": "ADC 2025 Table 1 p.12: BR28H = IR58025A/BRRI10R; MoA 2026 hybrid list row 74 origin 'ব্রি'; "
                         "BRRI-made hybrid on an IRRI CMS line",
}
PROMOTE = {
    "RICE-PVT_ACI_DHAN1": "line IR102481-BK-BK-ACI 28-3-1 selected by ACI from the IRRI segregating population "
                          "IR102481-BK-BK (NSB 110 minutes); same basis as BRRI dhan97 (IRRI cross, selected in Bangladesh)",
}

# Pedigrees the generic parser cannot read. Each tuple: (label as printed, role, generation, backcross_dose, note).
# The source column / file named here is the one the edge is read from.
M_REG = ("pedigree", REG_FILE)
M_SPIA = ("cgiar_spia_flags (SPIA 2025 Table 27 'IRRI/INGER entry used as parents')", REG_FILE)
MANUAL = {
    "RICE-BRRI_DHAN92": (("pedigree; Rice Profile id 100 intro", "05_output/final/bgd_rice_varieties.csv; "
                          "03_extracted/tables/brri_riceprofile.csv"), [
        ("IRGC103918 (rice x wheat derived line 'Rice/Wheat (RI)', collected from IRRI)", "female", 2, "",
         "Rice Profile id 100: 'IRGC103918' collected from IRRI Philippines, anther-cultured, then crossed twice "
         "with a BRRI line; generation 2 or deeper"),
        ("BR319-1-HR2", "male", 2, "", "BRRI line in the full pedigree Rice/Wheat(RI)/BR319-1-HR2//DH(Mingolo/Suweon290)/Panbira"),
        ("DH (Mingolo/Suweon290)", "unknown", 2, "", "doubled-haploid line; position in the cross not clear from the printed formula"),
        ("Panbira", "unknown", 2, "", "position in the cross not clear from the printed formula")]),
    "RICE-PVT_ACI_DHAN1": (M_REG, [("IR102481-BK-BK (IRRI segregating population)", "selection_source", 0, "",
                                    "pedigree selection by ACI from an IRRI cross population")]),
    "RICE-BINADHAN13": (M_REG, [("Kalizira (local aromatic cultivar)", "mutant_source", 0, "", "gamma ray 150 Gy + Datura extract")]),
    "RICE-BINADHAN14": (M_REG, [("Ashfal", "mutant_source", 0, "", "carbon-ion beam mutagenesis")]),
    "RICE-BINADHAN18": (M_REG, [("ব্রি ধান২৯ (BRRI dhan29)", "mutant_source", 0, "", "carbon-ion irradiation of BRRI dhan29 seed")]),
    "RICE-BINADHAN25": (M_REG, [("ব্রি ধান২৯ (BRRI dhan29)", "mutant_source", 0, "", "carbon-ion irradiation mutant of BRRI dhan29")]),
    "RICE-BINADHAN19": (M_REG, [("NERICA-10", "mutant_source", 0, "", "carbon-ion irradiation 40 Gy")]),
    "RICE-BINADHAN21": (M_REG, [("NERICA-10", "mutant_source", 0, "", "gamma irradiation 350 Gy")]),
    "RICE-BINADHAN24": (M_REG, [("Tap Hanh (Vietnam)", "mutant_source", 0, "", "gamma irradiation 250 Gy")]),
    "RICE-BINADHAN9": (M_REG, [("কালজিরা (Kalizira, local aromatic)", "female", 1, "", ""),
                               ("Y-1281 (high-yielding mutant line)", "male", 1, "", "")]),
    "RICE-BINADHAN20": (M_REG, [("বিনা ধান ৭ (Binadhan-7)", "female", 1, "", ""),
                                ("iron-rich breeding line from Vietnam (unnamed)", "male", 1, "", "")]),
    "RICE-BRRI_DHAN95": (M_REG, [("লাল স্বর্ণা (Lal Swarna)", "female", 1, "", ""),
                                 ("Barisail", "female", 2, "", "parent of the F1 used as male"),
                                 ("PSBRC2", "male", 2, "", "Philippine Seed Board release; no source in the archive states its breeding origin")]),
    "RICE-BRRI_DHAN100": (M_REG, [("BR7166-5B-5", "female", 2, "", "parent of the 2006 F1 used as female"),
                                  ("BG305", "male", 2, "", "parent of the 2006 F1 used as female"),
                                  ("ব্রি ধান২৯ (BRRI dhan29)", "male", 1, "", "crossed 2007")]),
    "RICE-BRRI_DHAN90": (M_REG, [("BR7166-5B-1-RAN-1", "recurrent", 1, "2", "F1 backcrossed once to BR7166-5B-1-RAN-1"),
                                 ("ব্রি ধান-৩৪ (BRRI dhan34)", "donor", 1, "", "")]),
    "RICE-BRRI_DHAN57": (M_REG, [("BR11", "recurrent", 1, "BC5", "NIL, BC5F1 (NSB 75 minutes)"),
                                 ("INGER line CR146-7027-224", "donor", 1, "", "Indian (CRRI) line received through INGER")]),
    "RICE-BRRI_DHAN87": (M_SPIA, [("BRRI dhan29*3", "recurrent", 1, "3", ""),
                                  ("Oryza rufipogon (IRGC103404)", "donor", 1, "", "IRRI genebank accession")]),
    "RICE-BRRI_DHAN89": (M_SPIA, [("BRRI dhan29*3", "recurrent", 1, "3", ""),
                                  ("Oryza rufipogon (IRGC103404)", "donor", 1, "", "IRRI genebank accession")]),
    "RICE-BRRI_DHAN96": (M_SPIA, [("BRRI dhan28*3", "recurrent", 1, "3", ""),
                                  ("Oryza rufipogon (IRGC103404)", "donor", 1, "", "IRRI genebank accession")]),
    "RICE-BRRI_DHAN82": (M_REG, [("NERICA10", "selection_source", 0, "", "pure-line selection (Rice Profile); line NERICA10-7-PL2-B")]),
    "RICE-BRRI_DHAN107": (M_REG, [("local collection (unnamed)", "selection_source", 0, "", "pure-line selection")]),
    "RICE-BRRI_DHAN93": (M_REG, [("local germplasm (unnamed)", "selection_source", 0, "", "pure-line selection; line BR-SF (Rang)-PL1-B")]),
    "RICE-BRRI_DHAN94": (M_REG, [("local germplasm (unnamed)", "selection_source", 0, "", "pure-line selection; line BR-RS (Raj)-PL4-B")]),
    "RICE-BRRI_DHAN34": (("breeding_line", REG_FILE), [("Khaskani (Acc. No. 4341)", "selection_source", 0, "",
                                                         "selection from a genebank accession of the landrace Khaskani")]),
    "RICE-BINADHAN7": (("TRIVSA Releases row 65 col Parents; IAEA MVD item 3150 (via 04_working/evidence_F3I.csv)",
                        "02_raw/asti_trivsa/TRIVSA-Rice-Data.xlsx; 03_extracted/tables/iaea_mvd_bgd.csv"),
                       [("Tainguyen (Tai Nguyen, Vietnam; line TNDB-100)", "mutant_source", 0, "",
                         "gamma-ray M3 lines from IAEA project RAS/5/037, selected at BINA; the register pedigree "
                         "cell holds only the line TNDB100")]),
    "RICE-OLD_PAJAM": (("pedigree (= TRIVSA 'Original breeding line name')", REG_FILE),
                       [("Mahsuri", "unknown", 1, "", "TRIVSA: developing institution 'Malaysia'; relation to Mahsuri not stated")]),
    "RICE-OLD_PURBACHI": (("pedigree (= TRIVSA 'Original breeding line name')", REG_FILE),
                          [("Chin-chu-ai", "unknown", 1, "", "TRIVSA: developing institution 'China'; SCA compendium p.11 '(উৎসঃ গণচীন)'")]),
    "RICE-BR5": (M_REG, [("Badshabhog", "unknown", 1, "", "pedigree cell reads 'Badshabhog rice'; relation not stated")]),
    "RICE-BINADHAN15": (M_REG, [("IR 2153-14-1-6-2", "female", 1, "", "printed 'IR 2153-14-1-6-2/IR 2061-214-38 2/IR 2071-625-1-252'; order of crosses unclear"),
                                ("IR 2061-214-38", "unknown", 1, "", ""),
                                ("IR 2071-625-1-252", "male", 1, "", "")]),
}

STATEMENT = re.compile(r"collected from irri|obtained under|contains irri|own development|irri line, collected|"
                       r"bacterial leaf blight resistant genes|^nationwide$", re.I)
DERIV = re.compile(r"^\s*(mutant of|somaclonal variant of|somaclone of|selection from|pure-?line selection from|"
                   r"derived from|advance line of)\s+(.+)$", re.I)
DERIV_ROLE = {"mutant of": "mutant_source", "somaclonal variant of": "somaclone_source", "somaclone of": "somaclone_source",
              "selection from": "selection_source", "pure-line selection from": "selection_source",
              "pureline selection from": "selection_source", "derived from": "selection_source",
              "advance line of": "selection_source"}
DROP_PAREN = re.compile(r"\((?=[^()]*(?:cross|tissue|BRAC|Supreme|research|(?:19|20|১৯|২০)[0-9০-৯]{2}))[^()]*\)"
                        r"|\([\s0-9০-৯\-]+\)", re.I)
BN_PAREN = re.compile(r"\((?=[^()]*[ঀ-৿])(?![^()]*[A-Za-z])[^()]*\)")   # Bengali-only gloss in parentheses
BENGALI = re.compile(r"[ঀ-৿]")
CG_IRRI = re.compile(r"^(IR-?\d|IR\d+[A-Z]|IRBB\d|IRBL|IRRI\d|IRGC)", re.I)
CG_AFR = re.compile(r"^(NERICA|WAB\d)", re.I)
NAMELIKE = re.compile(r"^(BR|BRRI\s*DHAN|BRRI\s*HYBRID\s*DHAN|BINA\s*DHAN|BINADHAN|IRATOM|IR|BU\s*DHAN|BAU\s*DHAN|BRAC\s*DHAN)"
                      r"[\s\-]*\d+$", re.I)
NAMELIKE_BN = re.compile(r"^(ব্রি|বিআর|বিনা|ইরাটম|আইআর)\s*(ধান|হাইব্রিড\s*ধান)?\s*[-–]?\s*\d+$")
LINECODE = re.compile(r"\d+[A-Z]*-[\w()]+-|^BRR?I?\d+[ABR]$|^BR\d+-", re.I)


def norm_name(s):
    return re.sub(r"[\s\-_.]", "", str(s).translate(BN).lower())


def norm_line(s):
    s = str(s).translate(BN).upper().replace(" ", "").replace("–", "-")
    s = re.sub(r"^([A-Z]+)-(?=\d)", r"\1", s)          # KN-1B-... -> KN1B-..., BR-7528 -> BR7528
    return s.strip("-*")


def segs(s):
    return [x for x in norm_line(s).split("-") if x]


def is_cgiar_label(label, alias=""):
    for t in (label, alias):
        t = str(t).translate(BN).strip()
        if not t:
            continue
        if CG_IRRI.match(t.replace(" ", "")):
            return "IRRI"
        if re.search(r"IRGC", t, re.I):
            return "IRRI"
        if CG_AFR.match(t.replace(" ", "")):
            return "AfricaRice"
    return ""


def split_top(expr):
    """Split a Purdy expression at its highest-order separator, ignoring text in parentheses."""
    depth, marks, i = 0, [], 0
    while i < len(expr):
        c = expr[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth = max(0, depth - 1)
        elif depth == 0 and c == "/":
            m = re.match(r"/(\d+)/", expr[i:])
            if m:
                marks.append((int(m.group(1)), i, i + len(m.group(0))))
                i += len(m.group(0))
                continue
            j = i
            while j < len(expr) and expr[j] == "/":
                j += 1
            marks.append((j - i, i, j))
            i = j
            continue
        elif depth == 0:
            m = re.match(r"\s+(?:x|X|×|and)\s+", expr[i:])
            if m and i > 0:
                marks.append((1, i, i + len(m.group(0))))
                i += len(m.group(0))
                continue
        i += 1
    if not marks:
        return None
    top = max(m[0] for m in marks)
    cut = [m for m in marks if m[0] == top][-1]   # crosses read left to right: the last top-order mark splits
    return expr[:cut[1]].strip(), expr[cut[2]:].strip()


def parse_cross(expr, gen=1, out=None):
    """Leaves of a cross whose direct parents are generation `gen`: [(label, role, generation)]."""
    out = [] if out is None else out
    parts = split_top(expr)
    if parts is None:
        out.append((expr.strip(), "unknown", gen))
        return out
    left, right = parts
    lb, rb = re.search(r"\*\s*(\d+)\s*$", left), re.match(r"^\s*(\d+)\s*\*", right)
    roles = ("recurrent", "donor") if lb else (("donor", "recurrent") if rb else ("female", "male"))
    for side, role in zip((left, right), roles):
        if split_top(side) is None:
            out.append((side.strip(), role, gen))
        else:
            parse_cross(side, gen + 1, out)
    return out


def clean_formula(s):
    s = str(s).strip()
    for _ in range(3):
        s = BN_PAREN.sub("", s)
        s = DROP_PAREN.sub("", s)
    s = s.split(";")[0]
    s = re.split(r"\s*->\s*", s)[0]
    if "," in s:
        head, tail = s.split(",", 1)
        if re.search(r"/| x |×", head):
            s = head
    s = re.sub(r"\+\s*gamma irradiation.*$", "", s, flags=re.I)
    s = re.sub(r"\s+BC\d+F\d+\s*$", "", s)
    s = re.sub(r"^\(+|\)+$", "", s.strip()) if s.strip().startswith("(") and s.strip().endswith(")") \
        and s.count("(") == s.count(")") and split_top(s.strip()[1:-1]) is not None else s
    return s.strip()


def parse_string(s):
    """Return (status, [(label, role, gen, dose, note)])."""
    if not isinstance(s, str) or not s.strip():
        return "none", []
    raw = s.strip()
    if STATEMENT.search(raw):
        return "statement_only", []
    f = clean_formula(raw)
    m = DERIV.match(f)
    if m:
        key = m.group(1).lower()
        return "parsed", [(m.group(2).strip(), DERIV_ROLE.get(key, "selection_source"), 0, "", "")]
    if split_top(f) is None:
        return "line_only", [(f, "unknown", 1, "", "")]
    out = []
    for label, role, gen in parse_cross(f):
        dose, note = "", ""
        m2 = re.search(r"\*\s*(\d+)\s*$", label) or re.match(r"^\s*(\d+)\s*\*", label)
        if m2:
            dose = m2.group(1)
        elif "*" in label:
            note = "unexplained '*' in printed formula dropped"
        out.append((label, role, gen, dose, note))
    return "parsed", out


def main():
    reg = pd.read_csv(ROOT / REG_FILE, dtype=str).fillna("")
    dec = pd.read_csv(ROOT / DEC_FILE, dtype=str).fillna("")
    corr = pd.read_csv(ROOT / "04_working/evidence_corrections.csv", dtype=str).fillna("")
    dropped = {(r.pilot_key, r.value) for r in corr.itertuples() if r.action == "drop" and r.field == "pedigree"}
    dropped |= {(r.pilot_key, r.value) for r in corr.itertuples() if r.action == "refield" and r.field == "pedigree"}
    R = reg.set_index("variety_id")
    ids = set(R.index)

    # ---- identity indexes
    name_ix = {}
    for vid, r in R.iterrows():
        for c in ("variety_name", "official_name_en", "official_name_bn"):
            if r[c]:
                name_ix.setdefault(norm_name(r[c]), set()).add(vid)
        for a in r.aliases.split("|"):
            if a.strip() and not LINECODE.search(norm_line(a)):
                name_ix.setdefault(norm_name(a), set()).add(vid)
    line_ix = []                                  # (normalised line, variety_id)
    for vid, r in R.iterrows():
        vals = r.breeding_line.split("|") + [a for a in r.aliases.split("|") if LINECODE.search(norm_line(a))]
        for v in vals:
            v = re.sub(r"\(.*?\)", "", v).strip()
            if v and re.search(r"\d", v) and not BENGALI.search(v):
                line_ix.append((norm_line(v), vid))

    def cgiar_line(vid):
        if vid in DEMOTE:
            return False
        return vid in PROMOTE or R.at[vid, "cgiar_role"] == "1"

    def resolve(label):
        """-> (parent_id, how, sibling_of)"""
        lab = label.translate(BN).strip()
        alias = ""
        m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", lab)
        main_lab = lab
        if m and m.group(1).strip():
            main_lab, alias = m.group(1).strip(), m.group(2).strip()
        main_lab = re.sub(r"\*\s*\d*\s*$|^\s*\d+\s*\*", "", main_lab).strip()
        main_lab = re.sub(r"^INGER line\s+", "", main_lab, flags=re.I)
        for cand in (main_lab, alias):
            if not cand:
                continue
            if NAMELIKE.match(cand) or NAMELIKE_BN.match(cand):
                k = make_key(cand)
                if k and "RICE-" + k in ids:
                    return "RICE-" + k, "name (lib_keys.make_key)", ""
            hit = name_ix.get(norm_name(cand))
            if hit and len(hit) == 1:
                return next(iter(hit)), "exact register name/alias", ""
        if is_cgiar_label(main_lab, alias):
            return "", "", ""
        for cand in (main_lab, alias):
            if not cand or not re.search(r"\d", cand) or BENGALI.search(cand):
                continue
            nl = norm_line(cand)
            hits = {vid for l, vid in line_ix if l == nl or (len(segs(cand)) >= 3 and l.startswith(nl + "-"))}
            if len(hits) == 1:
                return next(iter(hits)), "breeding line (exact or hyphen-bounded prefix)", ""
            s = segs(cand)
            sib = set()
            for l, vid in line_ix:
                t = l.split("-")
                if len(s) >= 2 and len(t) >= 2:
                    cross_no = re.match(r"^(BR|IR)\d+$", s[0]) and s[0] == t[0]
                    common = 0
                    for a, b in zip(s, t):
                        if a != b:
                            break
                        common += 1
                    deep = len(s) >= 4 and len(t) >= 4 and common >= min(len(s), len(t)) - 1 and common >= 3
                    if cross_no or deep:
                        sib.add(vid)
            if sib:
                return "", "sister line", "|".join(sorted(sib))
        return "", "", ""

    # ---- edges
    edges = []
    for vid, r in R.iterrows():
        recs, status, scol, sfile = [], "none", "", ""
        if vid in MANUAL:
            (scol, sfile), lst = MANUAL[vid]
            recs, status = list(lst), "parsed"
        else:
            tries = [("pedigree", REG_FILE, r.pedigree if (vid[5:], r.pedigree) not in dropped else "")]
            if r.hybrid_parent_female or r.hybrid_parent_male:
                tries.append(("hybrid_parent_female/hybrid_parent_male", REG_FILE,
                              f"{r.hybrid_parent_female}/{r.hybrid_parent_male}"))
            m = re.search(r"parents '([^']*)'", r.cgiar_spia_flags)
            if m and m.group(1).strip():
                tries.append((M_SPIA[0], REG_FILE, m.group(1)))
            for pc in dec.loc[dec.variety_id == vid, "pedigree_cross"]:
                if pc and (vid[5:], pc) not in dropped and pc != "nationwide":
                    tries.append(("pedigree_cross", DEC_FILE, pc))
            seen = []
            for col, fil, txt in tries:
                st, rr = parse_string(txt)
                seen.append(st)
                if st == "parsed":
                    recs, status, scol, sfile = rr, st, col, fil
                    break
            if status != "parsed":
                status = "statement_only" if "statement_only" in seen else ("line_only" if "line_only" in seen else "none")
        for label, role, gen, dose, note in recs:
            pid, how, sib = resolve(label)
            if pid == vid:                      # the variety's own line printed as its source is not a parent
                pid, how = "", ""
            alias = re.search(r"\(([^()]*)\)\s*$", label)
            centre = is_cgiar_label(re.sub(r"\(.*$", "", label), alias.group(1) if alias else "")
            if not centre and "IRGC" in label:
                centre = "IRRI"
            if pid and cgiar_line(pid):
                centre = R.at[pid, "cgiar_center"].split("|")[0].strip() or "IRRI"
            is_cg = "Y" if centre else "N"
            n = [note] if note else []
            if pid:
                n.append(f"resolved by {how}")
            if sib:
                n.append("sister line of " + ", ".join(R.at[s, 'variety_name'] for s in sib.split("|")) +
                         " (same cross designation); parents taken from that documented cross")
            if not pid and not sib and not centre and LINECODE.search(norm_line(re.sub(r"\(.*$", "", label))):
                n.append("breeding line not traced in the register")
            edges.append(dict(child_id=vid, child_name=r.variety_name, parent_label_as_printed=label, parent_id=pid,
                              parent_role=role, backcross_dose=dose, parent_is_cgiar_line=is_cg,
                              parent_cgiar_center=centre, source_column=scol, source_file=sfile, note="; ".join(n),
                              generation=gen, sibof=sib, _status=status))
        if not recs:
            edges.append(dict(child_id=vid, _status=status, _empty=True))

    E = pd.DataFrame([e for e in edges if not e.get("_empty")])
    status_of = {}
    for e in edges:
        status_of.setdefault(e["child_id"], e["_status"])

    # ---- depth
    by_child = {k: g for k, g in E.groupby("child_id")}
    memo = {}

    def depth_var(vid, stack, cross_only=False):
        if not cross_only and cgiar_line(vid):
            return 0, R.at[vid, "variety_name"], R.at[vid, "variety_name"]
        key = (vid, cross_only)
        if key in memo:
            return memo[key]
        if vid in stack:
            return None, "", ""
        best = (None, "", "")
        for e in (by_child[vid].itertuples() if vid in by_child else []):
            if cross_only and e.parent_role in DERIV_ROLES:
                continue
            step = 0 if e.parent_role in DERIV_ROLES else int(e.generation)
            d, anc, path = depth_label(e, stack | {vid})
            if d is None:
                continue
            tot = d + step
            if tot <= MAXD and (best[0] is None or tot < best[0]):
                rel = e.parent_role if e.parent_role in DERIV_ROLES else f"g{e.generation}"
                best = (tot, anc, f"{R.at[vid, 'variety_name']} <-{rel}- {path}")
        memo[key] = best
        return best

    def depth_label(e, stack):
        if e.parent_is_cgiar_line == "Y" and not e.parent_id:
            return 0, e.parent_label_as_printed, e.parent_label_as_printed
        if e.parent_id:
            return depth_var(e.parent_id, stack)
        if e.sibof:
            best = (None, "", "")
            for s in e.sibof.split("|"):
                if is_cgiar_label(R.at[s, "breeding_line"]) and cgiar_line(s):
                    cand = (0, R.at[s, "variety_name"], f"{e.parent_label_as_printed} [sister of {R.at[s, 'variety_name']}]")
                else:
                    d, anc, path = depth_var(s, stack, cross_only=True)
                    if d is None:
                        continue
                    d = d - 0  # the sister line has the same parents as the documented sibling
                    cand = (d, anc, f"{e.parent_label_as_printed} [sister of {path}]")
                if best[0] is None or cand[0] < best[0]:
                    best = cand
            return best
        return None, "", ""

    rows = []
    for vid, r in R.iterrows():
        d, anc, path = depth_var(vid, frozenset())
        g = by_child.get(vid)
        npar = 0 if g is None else int((g.generation.astype(int) <= 1).sum())
        st = status_of.get(vid, "none")
        if st == "parsed" and g is not None:
            untraced = g.note.str.contains("not traced").any()
            st = "parsed_untraced_lines" if untraced else "parsed"
        stated = re.search(r"contains irri genetic material", r.pedigree + " " + r.cgiar_spia_flags, re.I)
        if d is None and stated:              # IRRI ancestry stated by a CGIAR source without a named line
            anc, path = "IRRI (line not named)", "statement: 'Contains IRRI genetic material' (SPIA 2025 Table 27)"
        if cgiar_line(vid):
            implied = "1"
        elif (d is not None and d <= CODE2_MAX) or (d is None and stated):
            implied = "2"
        elif r.cgiar_role == "3":
            implied = "3"
        elif st.startswith("parsed"):
            implied = "4"
        else:
            implied = "5" if r.cgiar_role not in ("3",) else "3"
        rows.append(dict(variety_id=vid, n_parents_parsed=npar, depth_to_cgiar="" if d is None else d,
                         nearest_cgiar_ancestor=anc, pedigree_parse_status=st, cgiar_path=path,
                         current_cgiar_role=r.cgiar_role, implied_cgiar_role=implied))
    S = pd.DataFrame(rows)
    # sister lines keep the register variety they share a cross with (round-1 review A2-07; I3 2026-11-10)
    E = E.rename(columns={"sibof": "sister_of_id"}).drop(columns=["_status"])
    E = E[[c for c in E.columns if c != "sister_of_id"][:4] + ["sister_of_id"] + [c for c in E.columns if c != "sister_of_id"][4:]]
    S = attribution(R, E, S, cgiar_line)
    E.to_csv(ROOT / "05_output/final/bgd_pedigree_edges.csv", index=False, encoding="utf-8-sig")
    S.to_csv(ROOT / "05_output/final/bgd_pedigree_summary.csv", index=False, encoding="utf-8-sig")
    print(f"edges: {len(E)} rows for {E.child_id.nunique()} varieties; summary: {len(S)} rows")
    print(S.pedigree_parse_status.value_counts().to_string())
    print(pd.crosstab(S.current_cgiar_role, S.implied_cgiar_role).to_string())


# =====================================================================================================================
# Attribution measures, ancestor table and lineage graph (round-1 review A2-05/06/07; I3, 2026-11-10)
# =====================================================================================================================
MAXA = 5                                   # ancestors are listed to this generation
# Raitzer et al. (2015) Table 2.1, column D (NARS cross using IRRI material: breeding 0.5, material 0.5): the pedigree
# weight of a whole generation. Per ancestor it is 0.125 (parent), 0.03125 (grandparent), 0.015625 (great-grandparent).
RAITZER_T = {1: 0.25, 2: 0.125, 3: 0.125}
RAITZER_FILE = "03_extracted/tables/raitzer2015_bd_varieties.csv"
NARS_LINE = re.compile(r"^(BR|BRRI|BRR|BINA|BU|BAU|BRAC|ACI|SL)\s*[-\d(]", re.I)   # Bangladeshi institute line codes
DECADES = ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]

# Why a variety's register code and its SPIA 2025 Table 27 class differ (06_validation/cgiar_spia_concordance.csv).
SPIA_REASONS = {
    "RICE-BINADHAN17": "Register 3: Green Super Rice line SAGC-7 from Chinese parents C418(ZHONG413)2//SH109/(ZHONG413)2; no "
                       "source places the cross at IRRI, so GSR membership is coded as collaboration (memo, Green Super "
                       "Rice). SPIA counts the GSR line as an IRRI direct contribution.",
    "RICE-BINADHAN18": "Register 2 (depth 2): carbon-ion mutant of BRRI dhan29, whose grandparents IR20 and IR5-114-3-1 are "
                       "IRRI lines. SPIA sets every flag to N, although it codes Binadhan-25, another BRRI dhan29 mutant, "
                       "indirect_ir_parent=Y.",
    "RICE-BINADHAN19": "Register 2 (depth 0): mutant of NERICA-10, an AfricaRice line. SPIA's classes record IRRI and INGER "
                       "contributions only, so an AfricaRice source falls outside them.",
    "RICE-BINADHAN21": "Register 2 (depth 0): mutant of NERICA-10, an AfricaRice line. SPIA's classes record IRRI and INGER "
                       "contributions only, so an AfricaRice source falls outside them.",
    "RICE-BRRI_DHAN82": "Register 1: pure-line selection from NERICA10, an AfricaRice line. SPIA's classes record IRRI and "
                        "INGER contributions only.",
    "RICE-BINADHAN20": "Register 4: Binadhan-7 (a mutant of Tai Nguyen) crossed with an unnamed Vietnamese iron-rich line, "
                       "with no CGIAR element documented (memo, HarvestPlus). SPIA sets irri_direct=Y and harvestplus=Y but "
                       "prints no IRRI line, so its basis cannot be checked.",
    "RICE-BU_AROMATIC_HYBRID1": "Register 5: no parents documented (NSB 89, 'own development'). SPIA sets irri_direct=Y and "
                                "harvestplus=Y but prints no IRRI line, so its basis cannot be checked.",
    "RICE-BINADHAN26": "Register 1: a line collected from IRRI and released directly. SPIA codes it indirect (IR line as one "
                       "parent) and prints only its Xa4/Xa5 resistance genes.",
    "RICE-BR15": "Register 1: the IRRI cross IR1561-228-1-2/IR1737//CR94-13 introduced and released (TRIVSA: institution "
                 "IRRI, method Introduction). SPIA codes it indirect, presumably because the third parent, CR94-13, is an "
                 "Indian line.",
    "RICE-BRRI_HYBRID1": "Register 1: released under the IRRI hybrid number IR69690 (NSB 48). SPIA codes it indirect, "
                         "reading the IRRI CMS line IR58025A as one parent.",
    "RICE-BRRI_DHAN27": "Register 2 (depth 2): the female parent KN1B-361-1-8-6-9 is a sister line of BR17 (Zerak/IR8). SPIA "
                        "codes it as an INGER entry with no IRRI parent; it does not follow the sister-line link.",
    "RICE-BRRI_DHAN39": "Register 2 (depth 4): IRRI ancestry is reached only through BR1674-28-3-1-1, a sister line of BRRI "
                        "dhan35 (BR4//BR26-7-4-1/ARC14529), which puts IR20 at generation 4, beyond SPIA's grandparent limit.",
    "RICE-BRRI_DHAN60": "Register 2 (depth 1): the male parent BR26 is the IRRI line IR44595-70-2-2-3 released directly. "
                        "SPIA sets every flag to N, so it does not treat BR26 as an IR line.",
    "RICE-BRRI_DHAN83": "Register 2 (depth 2): the parent BR24 is C22/IR9752-136-2, so IR9752-136-2 is a grandparent. SPIA "
                        "sets every flag to N although it codes BR24 itself irri_direct=Y.",
    "RICE-BRRI_DHAN86": "Register 2 (depth 3): the male parent BR802-78-2-1-1 is a sister line of BRRI dhan29 "
                        "(BG90-2/BR51-46-5), whose grandparents are IR20 and IR5-114-3-1. SPIA does not follow sister "
                        "lines, and the IRRI lines sit beyond its grandparent limit.",
    "RICE-BRRI_HYBRID2": "Register 4: BRRI CMS and restorer lines (BRR10A/BRRI10R) whose own pedigrees are not published, "
                         "so no CGIAR line can be traced. SPIA codes indirect (IR line as one parent); no source in the "
                         "archive documents IRRI material in these lines.",
    "RICE-BRRI_HYBRID3": "Register 4: BRRI CMS and restorer lines (BRR11A/BRRI15R) whose own pedigrees are not published, "
                         "so no CGIAR line can be traced. SPIA codes indirect (IR line as one parent); no source in the "
                         "archive documents IRRI material in these lines.",
}


def _dose_n(d):
    d = str(d).strip()
    m = re.match(r"^BC\s*(\d+)$", d, re.I)          # BCn = n backcrosses = n+1 doses of the recurrent parent
    if m:
        return int(m.group(1)) + 1
    return int(d) if d.isdigit() else None


def _edge_shares(rows):
    """Nominal genetic share of each parent edge of one child, under equal parental contribution.
    A parent at generation g has 0.5**g; 'A*n/B' gives the recurrent parent (1 - 0.5**n) and the donor 0.5**n of the
    side they sit on; a mutant/somaclone/selection source has 1. Shares of a child that add up to more than 1 (a formula
    whose order of crosses is unclear, e.g. three parents at generation 1) are rescaled to 1."""
    rec = {}
    for e in rows:
        if e.parent_role == "recurrent" and _dose_n(e.backcross_dose):
            rec[int(e.generation)] = _dose_n(e.backcross_dose)
    out = []
    for e in rows:
        g = int(e.generation)
        if e.parent_role in DERIV_ROLES:
            s = 1.0
        elif e.parent_role == "recurrent" and g in rec:
            s = 0.5 ** (g - 1) * (1 - 0.5 ** rec[g])
        elif e.parent_role == "donor" and g in rec:
            s = 0.5 ** (g - 1) * 0.5 ** rec[g]
        else:
            s = 0.5 ** g
        out.append([e, s])
    tot = sum(s for e, s in out if e.parent_role not in DERIV_ROLES)
    if tot > 1 + 1e-9:
        for x in out:
            if x[0].parent_role not in DERIV_ROLES:
                x[1] /= tot
    return out


def _main_label(label):
    return re.sub(r"\s*\([^()]*\)\s*$", "", str(label)).strip() or str(label).strip()


def _line_key(label):
    lab = re.sub(r"^INGER line\s+", "", str(label), flags=re.I)
    lab = re.sub(r"\*\s*\d*\s*$", "", lab).strip()
    main = _main_label(lab)
    base = main if re.search(r"\d", main) else lab
    return "L:" + re.sub(r"\s+", " ", norm_line(base) if re.search(r"\d", base) else base.strip())


def _cross_family(line):
    m = re.match(r"^([A-Z]+\d+)", norm_line(_main_label(line)))
    return m.group(1) if m else ""


def _tail_weight(g):
    """Raitzer pedigree weight of one generation-g position and everything above it, per unit of nominal share."""
    return sum(RAITZER_T[k] for k in range(max(g, 1), 4))


def attribution(R, E, S, cgiar_line):
    """Ancestor table, attribution measures, SPIA split, concordance, lineage graph and founders."""
    import json
    by_child = {}
    for e in E.itertuples():
        by_child.setdefault(e.child_id, []).append(e)
    shares = {vid: _edge_shares(rows) for vid, rows in by_child.items()}
    vname = R["variety_name"].to_dict()

    # ---- ancestor table: every path from a variety back to generation MAXA
    anc = []

    def walk(root, vid, offset, mult, path, stack, below_cg, cross_only=False):
        for e, s in shares.get(vid, []):
            if cross_only and e.parent_role in DERIV_ROLES:
                continue
            g = offset + int(e.generation)
            if g > MAXA:
                continue
            sh = mult * s
            pid = e.parent_id
            label = vname[pid] if pid else e.parent_label_as_printed
            is_cg = e.parent_is_cgiar_line == "Y"
            sis = e.sister_of_id.split("|")[0] if e.sister_of_id else ""
            step = label + (f" [sister of {vname[sis]}]" if sis and not pid else "")
            p = path + ["(unnamed F1)"] * max(0, int(e.generation) - 1) + [step]
            traced_further = (pid and pid in shares) or (not pid and sis)
            untraced = (not is_cg) and (not traced_further) and bool(re.search(r"\d", _main_label(label)))
            anc.append(dict(variety_id=root, variety_name=vname[root], ancestor_label=label, ancestor_id=pid,
                            ancestor_kind="register variety" if pid else ("CGIAR line" if is_cg else "other line"),
                            generation=g, path=" > ".join(p), parent_role=e.parent_role, contribution_share=sh,
                            ancestor_is_cgiar_line="Y" if is_cg else "N", ancestor_cgiar_center=e.parent_cgiar_center,
                            first_cgiar_on_path="Y" if is_cg and not below_cg else "N",
                            ancestry_untraced="Y" if untraced else "N",
                            sister_of_id=e.sister_of_id if not pid else ""))
            if pid and pid not in stack:
                walk(root, pid, g, sh, p, stack | {pid}, below_cg or is_cg)
            elif not pid and sis and sis not in stack:
                walk(root, sis, g, sh, p, stack | {sis}, below_cg or is_cg, cross_only=True)

    for vid in R.index:
        walk(vid, vid, 0, 1.0, [vname[vid]], frozenset({vid}), False)
    A = pd.DataFrame(anc)
    keys = ["variety_id", "variety_name", "ancestor_label", "ancestor_id", "ancestor_kind", "generation", "path",
            "parent_role", "ancestor_is_cgiar_line", "ancestor_cgiar_center", "first_cgiar_on_path", "ancestry_untraced",
            "sister_of_id"]
    A = A.groupby(keys, as_index=False, sort=False)["contribution_share"].sum()
    A = A[keys[:6] + ["path", "parent_role", "contribution_share"] + keys[8:]]
    A.assign(contribution_share=A.contribution_share.round(6)).to_csv(
        ROOT / "05_output/final/bgd_pedigree_ancestors.csv", index=False, encoding="utf-8-sig")

    # ---- attribution measures per variety
    rz = pd.read_csv(ROOT / RAITZER_FILE, dtype=str).fillna("")
    rz_pub = {}
    for r in rz.itertuples():
        k = make_key(re.sub(r"dhan\s+(\d+)", r"dhan\1", r.variety_as_printed))
        if k and "RICE-" + k in R.index:
            rz_pub["RICE-" + k] = f"{float(r.irri_contribution.rstrip('%')) / 100:g}"
    out = {}
    byv = {k: g for k, g in A.groupby("variety_id")}
    for vid in R.index:
        a = byv.get(vid)
        centre = R.at[vid, "cgiar_center"].split("|")[0].strip() or "IRRI"
        o = dict(irri_share_nominal="", cgiar_share_nominal="", irri_weight_raitzer="", cgiar_weight_raitzer="",
                 raitzer_basis="", share_untraced_weight="", irri_weight_raitzer_published=rz_pub.get(vid, ""))
        if cgiar_line(vid):
            irri = 1.0 if centre == "IRRI" else 0.0
            o.update(irri_share_nominal=irri, cgiar_share_nominal=1.0, irri_weight_raitzer=irri, cgiar_weight_raitzer=1.0,
                     share_untraced_weight=0.0,
                     raitzer_basis=f"last-cross rule: {centre} line released directly")
        elif a is None:
            o["raitzer_basis"] = ("not computed: IRRI ancestry stated, line not named"
                                  if S.set_index("variety_id").at[vid, "nearest_cgiar_ancestor"].startswith("IRRI (")
                                  else "not computed: no parents parsed")
        else:
            first = a[(a.first_cgiar_on_path == "Y") & (a.generation <= 3)]
            irri_f = first[first.ancestor_cgiar_center == "IRRI"]
            o["irri_share_nominal"] = min(1.0, irri_f.contribution_share.sum())
            o["cgiar_share_nominal"] = min(1.0, first.contribution_share.sum())
            d0 = first[first.generation == 0]
            if len(d0):
                irri0 = 1.0 if (d0.ancestor_cgiar_center == "IRRI").any() else 0.0
                o.update(irri_weight_raitzer=irri0, cgiar_weight_raitzer=1.0, share_untraced_weight=0.0,
                         raitzer_basis="last-cross rule: mutant or selection of a CGIAR line")
            else:
                w = lambda f: float((f.contribution_share * f.generation.map(_tail_weight)).sum())
                wi, wc = w(irri_f), w(first)
                op = a[(a.ancestry_untraced == "Y") & (a.generation <= 3) & (a.first_cgiar_on_path == "N")]
                unk = 0.0            # weight of positions whose CGIAR status is unknown: above an untraced line,
                for r in op.itertuples():   # and the line itself unless it is a Bangladeshi institute line
                    own = 0.0 if NARS_LINE.match(_main_label(r.ancestor_label)) else RAITZER_T.get(r.generation, 0.0)
                    unk += r.contribution_share * (own + _tail_weight(r.generation + 1) * (r.generation < 3))
                o.update(irri_weight_raitzer=round(wi, 6), cgiar_weight_raitzer=round(wc, 6),
                         share_untraced_weight=round(unk, 6),
                         raitzer_basis="geometric rule: NARS cross with CGIAR material within three generations"
                         if wc > 0 else "geometric rule: NARS cross, no CGIAR line traced within three generations")
        out[vid] = o
    X = pd.DataFrame.from_dict(out, orient="index")
    for c in ("irri_share_nominal", "cgiar_share_nominal", "irri_weight_raitzer", "cgiar_weight_raitzer",
              "share_untraced_weight"):
        X[c] = X[c].map(lambda v: "" if v == "" else f"{round(float(v), 6):g}")

    # ---- cgiar_derivation (A2-06) and SPIA flags split out of cgiar_spia_flags (A2-07)
    deriv = {}
    for vid in R.index:
        roles = {e.parent_role for e in by_child.get(vid, [])}
        d = ""
        for rr, lab in (("mutant_source", "mutant"), ("somaclone_source", "somaclone"), ("selection_source", "selection")):
            if rr in roles:
                d = lab
        if not d and cgiar_line(vid):
            d = "introduction"
        elif not d and roles & {"female", "male", "recurrent", "donor"}:
            d = "cross"
        deriv[vid] = d
    X["cgiar_derivation"] = pd.Series(deriv)
    fl = R["cgiar_spia_flags"]
    cat = fl.str.extract(r"^spia_(direct|indirect|none)")[0].fillna("")
    X["spia_in_t27"] = cat.map(lambda c: "Y" if c else "N")
    X["spia_category"] = cat
    for col, key in (("spia_irri_direct", "irri_direct"), ("spia_indirect_ir_parent", "indirect_ir_parent"),
                     ("spia_inger_entry", "inger_entry"), ("spia_in_reference_library", "in_reference_library"),
                     ("spia_harvestplus", "harvestplus")):
        X[col] = fl.str.extract(key + r"=([YN])")[0].fillna("")
    X["spia_none"] = cat.map(lambda c: "" if not c else ("Y" if c == "none" else "N"))
    S = S.merge(X, left_on="variety_id", right_index=True, how="left")

    # ---- concordance of the register code with SPIA's classes
    rows = []
    T = S.merge(R[["variety_name", "cgiar_spia_flags"]], left_on="variety_id", right_index=True)

    def status(code, c, depth):
        if not c:
            return "not compared (not in SPIA Table 27)"
        if code == "1":
            return "concordant" if c == "direct" else "discordant"
        if code == "2":
            if c == "none":
                return "discordant"
            return "concordant" if depth == "" or int(depth) <= 2 else "concordant in class, IRRI line beyond grandparents"
        return "concordant" if c == "none" else "discordant"
    T["concordance"] = [status(a, b, d) for a, b, d in zip(T.current_cgiar_role, T.spia_category, T.depth_to_cgiar)]
    ct = T.groupby(["current_cgiar_role", "spia_category", "concordance"]).size().reset_index(name="n_varieties")
    for r in ct.itertuples():
        rows.append(dict(section="count", cgiar_role=r.current_cgiar_role, spia_category=r.spia_category or "not in T27",
                         concordance=r.concordance, n_varieties=r.n_varieties))
    for r in T[T.concordance.str.startswith(("discordant", "concordant in class"))].sort_values(
            ["concordance", "current_cgiar_role", "variety_id"]).itertuples():
        par = re.search(r"parents '([^']*)'", r.cgiar_spia_flags)
        reason = SPIA_REASONS.get(r.variety_id, "")
        if not reason and r.concordance.startswith("concordant in class"):
            reason = (f"Both sources link the variety to IRRI, but the register reaches the nearest CGIAR line at "
                      f"generation {r.depth_to_cgiar} ({r.cgiar_path}); SPIA's class is defined on parents or grandparents.")
        rows.append(dict(section="variety", cgiar_role=r.current_cgiar_role, spia_category=r.spia_category,
                         concordance=r.concordance, n_varieties=1, variety_id=r.variety_id, variety_name=r.variety_name,
                         depth_to_cgiar=r.depth_to_cgiar, nearest_cgiar_ancestor=r.nearest_cgiar_ancestor,
                         spia_parents_text=par.group(1) if par else "", reason=reason or "no explanation recorded"))
    C = pd.DataFrame(rows)
    C.to_csv(ROOT / "06_validation/cgiar_spia_concordance.csv", index=False, encoding="utf-8-sig")

    # ---- lineage graph: register varieties, CGIAR lines and other lines; parent -> child
    nodes, edges = {}, []

    def reg_node(vid):
        if vid not in nodes:
            r = R.loc[vid]
            nodes[vid] = dict(id=vid, label=r.variety_name, kind="register variety", year=r.approval_year,
                              developer_group=r.developer_group, cgiar_role=r.cgiar_role,
                              cgiar_center=r.cgiar_center.split("|")[0].strip() if r.cgiar_role in ("1", "2") else "",
                              cross_family=_cross_family(r.breeding_line.split("|")[0]) if r.breeding_line else "",
                              sister_of_id="")
        return vid

    def line_node(e):
        k = _line_key(e.parent_label_as_printed)
        if k not in nodes:
            nodes[k] = dict(id=k, label=_main_label(re.sub(r"^INGER line\s+", "", e.parent_label_as_printed, flags=re.I)),
                            kind="CGIAR line" if e.parent_is_cgiar_line == "Y" else "other line", year="",
                            developer_group="", cgiar_role="", cgiar_center=e.parent_cgiar_center,
                            cross_family=_cross_family(e.parent_label_as_printed), sister_of_id=e.sister_of_id)
        return k

    for e in E.itertuples():
        tgt = reg_node(e.child_id)
        src = reg_node(e.parent_id) if e.parent_id else line_node(e)
        edges.append(dict(source=src, target=tgt, role=e.parent_role, generation=int(e.generation), basis="printed pedigree"))
        if not e.parent_id and e.sister_of_id:
            sib = e.sister_of_id.split("|")[0]
            for f in by_child.get(sib, []):
                if f.parent_role in DERIV_ROLES:
                    continue
                s2 = reg_node(f.parent_id) if f.parent_id else line_node(f)
                edges.append(dict(source=s2, target=src, role=f.parent_role, generation=int(f.generation),
                                  basis=f"inferred: sister line of {vname[sib]} (same cross)"))
    lines = [k for k in nodes if k.startswith("L:")]
    for a_ in lines:                                   # a line whose designation extends another's is selected from it
        for b_ in lines:
            if a_ != b_ and b_.startswith(a_ + "-") and len(a_[2:].split("-")) >= 3:
                edges.append(dict(source=a_, target=b_, role="selection_source", generation=0,
                                  basis="inferred: line designation extends the parent line's"))
    seen, ded = set(), []
    for e in edges:
        k = (e["source"], e["target"], e["role"], e["basis"])
        if k not in seen and e["source"] != e["target"]:
            seen.add(k)
            ded.append(e)
    edges = ded

    # ---- founders: register descendants of every ancestor node (any generation), by decade
    import heapq
    kids = {}
    for e in edges:
        kids.setdefault(e["source"], []).append((e["target"], e["generation"]))
    yr = R["approval_year"].to_dict()
    frows = []
    for n in nodes:
        if n not in kids:
            continue
        dist, pq = {n: 0}, [(0, n)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, 1e9):
                continue
            for v, w in kids.get(u, []):
                if d + w < dist.get(v, 1e9):
                    dist[v] = d + w
                    heapq.heappush(pq, (d + w, v))
        desc = {v: d for v, d in dist.items() if v != n and v in R.index}
        if not desc:
            continue
        nd = nodes[n]
        row = dict(ancestor_id=n if n in R.index else "", ancestor_node=n, ancestor_label=nd["label"], ancestor_kind=nd["kind"],
                   ancestor_is_cgiar_line="Y" if (nd["kind"] == "CGIAR line" or (n in R.index and cgiar_line(n))) else "N",
                   ancestor_cgiar_center=nd["cgiar_center"] if nd["kind"] == "CGIAR line" or (n in R.index and cgiar_line(n)) else "",
                   ancestor_year=nd["year"], cross_family=nd["cross_family"], n_descendants=len(desc),
                   n_children=len({t for t, _ in kids[n] if t in R.index}))
        for dc in DECADES:
            row["n_" + dc] = 0
        for v in desc:
            y = yr.get(v, "")
            if str(y).isdigit():
                dc = f"{max(1960, int(y) // 10 * 10)}s"
                row["n_" + dc] = row.get("n_" + dc, 0) + 1
        gens = sorted(set(desc.values()))
        row["generations"] = "|".join(str(x) for x in gens)
        row["max_generation"] = max(gens)
        row["first_descendant_year"] = min((int(yr[v]) for v in desc if str(yr.get(v, "")).isdigit()), default="")
        row["descendant_ids"] = "|".join(sorted(desc, key=lambda v: (str(yr.get(v, "")), v)))
        frows.append(row)
    Fd = pd.DataFrame(frows).sort_values(["n_descendants", "ancestor_year"], ascending=[False, True])
    Fd.insert(0, "founder_rank", range(1, len(Fd) + 1))
    Fd["top12"] = (Fd.founder_rank <= 12).map({True: "Y", False: "N"})
    Fd.to_csv(ROOT / "05_output/final/bgd_pedigree_founders.csv", index=False, encoding="utf-8-sig")
    ndesc = dict(zip(Fd.ancestor_node, Fd.n_descendants))
    for k, nd in nodes.items():
        nd["n_descendants"] = int(ndesc.get(k, 0))
    graph = dict(
        meta=dict(title="Bangladesh rice register: pedigree lineage graph", version="1.1.1",
                  built_by="scripts/build_pedigree.py", source="05_output/final/bgd_pedigree_edges.csv",
                  note="Nodes are register varieties (id = variety_id), CGIAR lines and other breeding lines or "
                       "landraces (id 'L:' + normalised designation) that appear in a parsed pedigree. Edges run parent -> "
                       "child; generation 1 = direct parent, 2 = parent of an unnamed F1 inside a composite cross, 0 = "
                       "mutant, somaclone or selection source. Edges with basis 'inferred: ...' come from sister-line or "
                       "line-designation rules, not from a printed pedigree. Register varieties with no parsed pedigree "
                       "and no descendants (most private hybrids) are not nodes.",
                  n_nodes=len(nodes), n_edges=len(edges)),
        founders=list(Fd.ancestor_node[:12]),
        nodes=list(nodes.values()), edges=edges)
    (ROOT / "05_output/final/bgd_lineage_graph.json").write_text(json.dumps(graph, ensure_ascii=False, separators=(",", ":")),
                                                                  encoding="utf-8")

    # ---- checks printed for the log
    for vid in ("RICE-BRRI_DHAN28", "RICE-BRRI_DHAN29"):
        x = S.set_index("variety_id").loc[vid]
        print(f"Raitzer check {vid}: computed {x.irri_weight_raitzer}, untraced weight {x.share_untraced_weight}, "
              f"published {x.irri_weight_raitzer_published}")
    print(f"ancestors: {len(A)} rows for {A.variety_id.nunique()} varieties; lineage graph {len(nodes)} nodes, "
          f"{len(edges)} edges; founders {len(Fd)}")
    print(Fd.head(12)[["founder_rank", "ancestor_label", "n_descendants", "generations"]].to_string(index=False))
    print(C[C.section == "count"].to_string(index=False))
    return S


if __name__ == "__main__":
    main()
