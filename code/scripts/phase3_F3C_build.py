"""F3C: independent CGIAR-original attribution sources for Bangladesh rice varieties.

Reads the downloaded CGIAR sources (02_raw/cgiar_lit/), writes
  03_extracted/tables/<source>_bd_varieties.csv
  04_working/evidence_F3C.csv
  06_validation/cgiar_attribution_crosscheck.md
Re-runnable; no network access (downloads are done by phase3_F3C_fetch.py / cgspace_list).
"""
import csv, io, pathlib, re, sys, zipfile, collections
import docx, openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lib_keys import make_key

RAW = ROOT / "02_raw/cgiar_lit"
TAB = ROOT / "03_extracted/tables"
EVH = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank",
       "local_file", "page", "locator", "method", "validation", "confidence", "notes"]
RANK = "4_cgiar_record"
EV = []

# Names that make_key cannot key safely (decided per row; see decisions_F3C.md)
MANUAL = {
    "ACI-2": "HYB_ACI2",            # MoA row 30 'এসিআই-২' (ACI Ltd); exact name
}
FORCE_UNMATCHED = {"BR11_Sub1", "Swarna_Sub1", "Swarna *", "Sahbhagidhan", "Sahbhagi dhan", "BRRI HV4",
                   "BRRI HV6", "RU dhan 1"}


def key_of(name):
    n = name.strip()
    if n in FORCE_UNMATCHED:
        return "UNMATCHED"
    if n in MANUAL:
        return MANUAL[n]
    if n == "BRRI dhan52/BR11_Sub1":          # source's own label equates the two
        return "BRRI_DHAN52"
    return make_key(n) or "UNMATCHED"


def ev(**k):
    row = {h: "" for h in EVH}
    row.update(k)
    EV.append(row)


def write_table(name, header, rows):
    TAB.mkdir(parents=True, exist_ok=True)
    with open(TAB / f"{name}_bd_varieties.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(header); w.writerows(rows)


# ---------------------------------------------------------------- 1. Raitzer et al. 2015
RZ = dict(source_id="DS-S12", source_title="Raitzer et al. 2015, Is Rice Improvement Still Making a Difference? (CGIAR ISPC/SPIA), CGSpace 10568/128929",
          authority_rank=RANK, local_file="02_raw/cgiar_lit/raitzer2015_spia_rice_1989-2009.pdf", method="pdf_text",
          validation="unvalidated", confidence="high")
rz_rows = [["BRRI dhan 28", "25%", "IRRI attribution weight (last-cross + geometric rule)", 92, "3.5.1.2"],
           ["BRRI dhan 29", "37.5%", "IRRI attribution weight (last-cross + geometric rule)", 92, "3.5.1.2"]]
write_table("raitzer2015", ["variety_as_printed", "irri_contribution", "measure", "pdf_page", "section"], rz_rows)
for name, w, meas, pg, sec in rz_rows:
    ev(pilot_key=key_of(name), field="cgiar_independent",
       value=f"Raitzer 2015: NARS cross with IRRI germplasm, IRRI attribution weight {w} (not an IRRI cross; an IRRI cross would be 100%)",
       value_raw=f"the {w} IRRI contribution to {name}", page=pg,
       locator=f"section {sec} 'Multiplying the respective shifts from each variety by the 25% IRRI contribution to BRRI dhan 28 and the 37.5% contribution to BRRI dhan 29'",
       notes="Only variety-level figures in the report. Table 3.2 (p.65) is aggregated by period (12 IRRI crosses, 34 NARES crosses with IRRI parents, 1 with IRRI ancestors, 2 with none, of 49 releases 1970-2009) and names no varieties. Weighting rule p.41 (last cross rule + geometric rule, Table 2.1 p.42).",
       **RZ)

# ---------------------------------------------------------------- 2. Villanueva et al. 2022
VL = dict(source_id="DS-S09", source_title="Villanueva, Enriquez & Capilit 2022, The impact of the international rice genebank (IRG) on rice farming in Bangladesh, CABI Agric Biosci, Additional file 1 Table S1/S2",
          authority_rank=RANK, local_file="02_raw/cgiar_lit/villanueva2022_additional_file1.docx", method="xlsx",
          validation="unvalidated", confidence="high")
d = docx.Document(RAW / "villanueva2022_additional_file1.docx")
s1 = [[c.text.strip() for c in r.cells] for r in d.tables[0].rows][2:]
s2 = {r.cells[0].text.strip(): [c.text.strip() for c in r.cells] for r in d.tables[1].rows[1:]}
vl_out = []
VL_CLASS = {}
for i, r in enumerate(s1, start=3):
    name, yr, typ, area, pct, de, po, no, un = r
    s2r = s2.get(name, ["", "", "", ""])
    vl_out.append([name, yr, typ, area, pct, de, po, no, un, s2r[1], s2r[2], s2r[3]])
    k = key_of(name)
    de_f, po_f, un_f = float(de), float(po), float(un)
    if un_f >= 1:
        cls, txt = "unknown", "IRG progenitor contribution unknown (hybrid, confidential pedigree)"
    elif de_f > 0:
        cls, txt = "definite", f"IRRI genebank (IRG) accession in pedigree, definite contribution {de} (possible {po}; IRGC-numbered progenitor in IRIS pedigree)"
    elif po_f > 0:
        cls, txt = "possible", f"no IRGC-numbered progenitor; possible IRG contribution {po} (progenitor name matches an IRG accession)"
    else:
        cls, txt = "none", "no IRG progenitor in IRIS pedigree (definite 0, possible 0)"
    VL_CLASS[(k, name)] = (cls, de, po, yr)
    raw = f"{name} | {yr} | {typ} | definite {de} | possible {po} | no {no} | unknown {un}"
    common = dict(page="Table S1", locator=f"Additional file 1 Table S1 row {i} '{name}'", **VL)
    note = ("IRG = IRRI's International Rice Genebank. Measures genebank-accession content in the IRIS pedigree, not IRRI breeding; "
            f"Table S2 counts definite/possible ancestors: {s2r[1]}/{s2r[2]}.")
    if k == "UNMATCHED":
        note += f" Raw name '{name}' not keyed."
    ev(pilot_key=k, field="cgiar_independent", value=f"Villanueva 2022: {txt}", value_raw=raw, notes=note, **common)
    if yr and yr != "-":
        ev(pilot_key=k, field="approval_date", value=yr, value_raw=f"{name} | Released year {yr}",
           notes="'Released year' as printed in Villanueva 2022 Table S1 (year only).", **common)
write_table("villanueva2022", ["variety_as_printed", "released_year", "variety_type", "area_000ha_ws2015", "pct_area",
                               "irg_definite", "irg_possible", "irg_no", "irg_unknown", "s2_n_definite_ancestors",
                               "s2_n_possible_ancestors", "s2_total"], vl_out)

# ---------------------------------------------------------------- 3. Dikitanan et al. 2022
DK = dict(source_id="DS-S13", source_title="Dikitanan et al. 2022, Assessing returns to research investments in rice varietal development (Global Food Security 33:100646), Appendix Table A2",
          authority_rank=RANK, local_file="02_raw/cgiar_lit/dikitanan2022_PMC9231557_supp.zip", method="xlsx",
          validation="unvalidated", confidence="high")
z = zipfile.ZipFile(ROOT / DK["local_file"])
dd = docx.Document(io.BytesIO(z.read("mmc1.docx")))
ORIGIN = {"1": "two IRRI lines as parents", "2": "1 IRRI line as parent", "3": "with other IRRI ancestry",
          "4": "without IRRI connection", "": "origin cell blank"}
dk_out = []
DK_CLASS = collections.OrderedDict()
for i, r in enumerate(dd.tables[1].rows[1:], start=2):
    inst, season, name, gen, yld, yr, org, traits = [c.text.strip() for c in r.cells]
    dk_out.append([inst, season, name, gen, yld, yr, org, traits])
    k = key_of(name)
    DK_CLASS.setdefault((k, name), []).append((i, inst, season, yr, org))
write_table("dikitanan2022", ["institution", "season", "variety_as_printed", "generation", "ave_yield_t_ha",
                              "release_year", "origin_code", "main_traits"], dk_out)
for (k, name), occ in DK_CLASS.items():
    rows_txt = ", ".join(str(o[0]) for o in occ)
    orgs = sorted({o[4] for o in occ}); yrs = sorted({o[3] for o in occ})
    for org in orgs:
        ev(pilot_key=k, field="cgiar_independent",
           value=f"Dikitanan 2022: origin code {org or 'blank'} = {ORIGIN[org]}",
           value_raw=" || ".join(f"{o[1]} | {o[2]} | {name} | {o[3]} | {o[4]}" for o in occ if o[4] == org),
           page="Appendix Table A2", locator=f"Appendix Table A2 row(s) {rows_txt} '{name}'",
           notes=("Origin codes from the table footnote: 1 two IRRI lines as parents; 2 one IRRI line as parent; 3 other IRRI ancestry; "
                  "4 without IRRI connection. Parentage from IRIS, BRRI and BINA (main text p.5)."
                  + (f" Raw name '{name}' not keyed." if k == "UNMATCHED" else "")), **DK)
    for y in yrs:
        ev(pilot_key=k, field="approval_date", value=y, value_raw=f"{name} | Release year {y}",
           page="Appendix Table A2", locator=f"Appendix Table A2 row(s) {rows_txt} '{name}'",
           notes="'Release year' as printed (year only).", **DK)

# ---------------------------------------------------------------- 4. Kretzschmar et al. 2018
KZ = dict(source_id="DS-S10", source_title="Kretzschmar et al. 2018, DNA fingerprinting at farm level maps rice biodiversity across Bangladesh (Sci Rep 8:14920), Supplementary 1 Sheet A",
          authority_rank=RANK, local_file="02_raw/cgiar_lit/kretzschmar2018_PMC6175857_supp.zip", method="xlsx",
          validation="unvalidated", confidence="medium")
z = zipfile.ZipFile(ROOT / KZ["local_file"])
wb = openpyxl.load_workbook(io.BytesIO(z.read("41598_2018_33080_MOESM1_ESM.xlsx")), read_only=True)
kz_out = []
KZ_CLASS = {}
IRPAT = re.compile(r"\bIR\s?\d[\w\-]*|\bIRRI\s?\d+")
for i, r in enumerate(wb["Sheet A"].iter_rows(values_only=True), start=1):
    if i < 3:
        continue
    L = [("" if v is None else str(v).strip()) for v in r[:4]]
    R = [("" if v is None else str(v).strip()) for v in r[4:12]]
    kz_out.append(L + R)
    name, yr, origin, chars = L
    if not name:
        continue
    k = key_of(name)
    loc = f"MOESM1_ESM.xlsx Sheet A row {i}, left block '{name}'"
    irs = IRPAT.findall(origin)
    # Varieties whose own name contains an IR line in the pedigree string count only if the IR token is a direct parent token
    if origin:
        txt = ("IR designation(s) in printed pedigree: " + ", ".join(irs)) if irs else "no IR designation in printed pedigree"
    else:
        txt = "no pedigree printed"
    KZ_CLASS[(k, name)] = ("ir" if irs else ("none" if origin else "blank"), origin, yr)
    note = "Source makes no attribution statement; the cgiar_independent value is derived by F3C from the 'Origin' (pedigree) cell. Data from 'BRRI personal communication'."
    if k == "UNMATCHED":
        note += f" Raw name '{name}' not keyed."
    if name in ("BRRI dhan28", "BRRI dhan29"):
        note += " Year and pedigree for this row look misassigned in the source (dhan28/dhan29 released 1994; 'BR6(IR8)/Purbaci' is the dhan28 pedigree with BR6 mislabelled IR8)."
    ev(pilot_key=k, field="cgiar_independent", value=f"Kretzschmar 2018 (derived): {txt}",
       value_raw=f"{name} | {yr} | {origin}", page="Sheet A", locator=loc, notes=note,
       **{**KZ, "confidence": "low"})
    if origin:
        ev(pilot_key=k, field="pedigree", value=origin, value_raw=origin, page="Sheet A", locator=loc,
           notes="Column 'Origin' (pedigree) as printed." + (" " + note.split(". ", 2)[-1] if "misassigned" in note else ""), **KZ)
    if yr:
        ev(pilot_key=k, field="approval_date", value=yr, value_raw=f"{name} | Year of release {yr}", page="Sheet A", locator=loc,
           notes="'Year of release' as printed (year only)." + (" Suspect: see cgiar_independent row note." if name in ("BRRI dhan28", "BRRI dhan29") else ""),
           **{**KZ, "confidence": "low" if name in ("BRRI dhan28", "BRRI dhan29") else "medium"})
write_table("kretzschmar2018", ["L_variety", "L_year", "L_origin_pedigree", "L_characteristics", "R_variety", "R_year",
                                "R_origin_pedigree", "R_characteristics", "R_potential_yield_kg_ha", "R_season",
                                "R_used_as_primary_reference", "R_comment"], kz_out)

# ---------------------------------------------------------------- 5. CGIAR innovation records (CGSpace)
CR = dict(source_id="F3C-CGS-122323", source_title="CGIAR Research Program on Rice, innovation #1945 'Promising lines were released for irrigated lowland conditions in Bangladesh' (CGSpace 10568/122323)",
          authority_rank=RANK, local_file="02_raw/cgiar_lit/crp_rice_innovation_IN1945.pdf", method="pdf_text",
          validation="unvalidated", confidence="medium", page="1")
raw97 = "Two promising lines BRRI Dhan 97 (IR83484-3-B-7-1-1-1) and BRRI Dhan99 (HHZ5-DT20-DT2-DT1) were released"
for name, line in (("BRRI Dhan 97", "IR83484-3-B-7-1-1-1"), ("BRRI Dhan99", "HHZ5-DT20-DT2-DT1")):
    k = key_of(name)
    ev(pilot_key=k, field="cgiar_independent",
       value=f"CRP Rice 2020 innovation #1945: IRRI-reported release of line {line}; lead organisation IRRI, contributing BRRI"
             + ("; IR-designated line" if line.startswith("IR") else "; not IR-designated (HHZ = Huanghuazhan-derived line)"),
       value_raw=raw97, locator="'Description of the innovation' / 'Name of lead organization: IRRI'",
       notes="CGIAR results-reporting record (sub-IDO 'Adoption of CGIAR materials with enhanced genetic gains').", **CR)
    ev(pilot_key=k, field="breeding_line", value=line, value_raw=raw97, locator="'Description of the innovation'", notes="", **CR)
A4 = dict(source_id="F3C-CGS-122813", source_title="CGIAR Research Program A4NH, innovation #2629 'BRRI dhan 100: A new zinc biofortified rice variety released in Bangladesh' (CGSpace 10568/122813)",
          authority_rank=RANK, local_file="02_raw/cgiar_lit/a4nh_innovation_IN2629_brri_dhan100.pdf", method="pdf_text",
          validation="unvalidated", confidence="medium", page="1")
ev(pilot_key="BRRI_DHAN100", field="cgiar_independent",
   value="A4NH 2021 innovation #2629: BRRI-led release; contributing organisations IRRI and HarvestPlus (collaboration)",
   value_raw="Name of lead organization: BRRI ... Names of top five contributing organizations: IRRI; HarvestPlus",
   locator="'Name of lead organization' / 'Names of top five contributing organizations'",
   notes="Generic stage text: 'Collaboration between HarvestPlus, CGIAR breeding centers, and National Agricultural Research Systems resulted in the release of 21 new varieties'.", **A4)

# ---------------------------------------------------------------- write evidence
with open(ROOT / "04_working/evidence_F3C.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=EVH); w.writeheader(); w.writerows(EV)

# ---------------------------------------------------------------- cross-check
arch = {r["variety_id"].replace("RICE-", "", 1): r for r in csv.DictReader(open(ROOT / "05_output/rice_varieties.csv", encoding="utf-8-sig"))}


def arch_of(k):
    r = arch.get(k)
    if not r:
        return None
    return r


def cmp(expected, k):
    """expected: set of acceptable archive codes. Returns (status, role, lineage)."""
    r = arch_of(k)
    if r is None:
        return "not_in_archive", "", ""
    role = (r.get("cgiar_role") or "").strip()
    lin = (r.get("cgiar_lineage") or "").strip()
    if role in ("", "5"):
        return "archive_unknown", role or "blank", lin
    return ("agree" if role in expected else "disagree"), role, lin


report = []
stats = {}


def tally(src, items):
    c = collections.Counter(s for s, *_ in items)
    stats[src] = c
    return c


# Raitzer
rz_items = []
for name, w_, *_ in rz_rows:
    k = key_of(name); st, role, lin = cmp({"2"}, k)
    rz_items.append((st, k, name, f"IRRI weight {w_} (NARS cross with IRRI germplasm)", role, lin))
# Villanueva: definite -> {1,2}; none/possible -> {3,4}
vl_items = []
for (k, name), (cls, de, po, yr) in VL_CLASS.items():
    if k == "UNMATCHED" or cls == "unknown":
        vl_items.append(("not_compared", k, name, f"{cls} (definite {de}, possible {po})", "", ""))
        continue
    exp = {"1", "2"} if cls == "definite" else {"3", "4"}
    st, role, lin = cmp(exp, k)
    vl_items.append((st, k, name, f"{cls} (definite {de}, possible {po})", role, lin))
# Dikitanan: 1/2 -> {1,2}; 3 -> {2,4} (ancestry, archive codes grandparent 2 or beyond-grandparent 4); 4 -> {3,4}
dk_items = []
for (k, name), occ in DK_CLASS.items():
    for org in sorted({o[4] for o in occ}):
        if k == "UNMATCHED" or org == "":
            dk_items.append(("not_compared", k, name, f"origin {org or 'blank'} = {ORIGIN[org]}", "", ""))
            continue
        exp = {"1": {"1", "2"}, "2": {"1", "2"}, "3": {"2", "4"}, "4": {"3", "4"}}[org]
        st, role, lin = cmp(exp, k)
        dk_items.append((st, k, name, f"origin {org} = {ORIGIN[org]}", role, lin))
# Kretzschmar (derived): IR token in pedigree -> {1,2}; no IR token -> {2,3,4} (grandparent possible)
kz_items = []
for (k, name), (cls, origin, yr) in KZ_CLASS.items():
    if k == "UNMATCHED" or cls == "blank":
        kz_items.append(("not_compared", k, name, f"pedigree '{origin}'", "", ""))
        continue
    exp = {"1", "2"} if cls == "ir" else {"2", "3", "4"}
    st, role, lin = cmp(exp, k)
    kz_items.append((st, k, name, f"pedigree '{origin}' ({'IR parent token' if cls == 'ir' else 'no IR token'})", role, lin))
# CRP records
cr_items = []
for k, desc, exp in (("BRRI_DHAN97", "IRRI-led release of IR83484-3-B-7-1-1-1", {"1"}),
                     ("BRRI_DHAN99", "IRRI-led release of HHZ5-DT20-DT2-DT1", {"1", "2", "3"}),
                     ("BRRI_DHAN100", "BRRI-led; IRRI + HarvestPlus contributing", {"1", "2", "3"})):
    st, role, lin = cmp(exp, k); cr_items.append((st, k, k, desc, role, lin))

SRC = [("Raitzer et al. 2015 (SPIA)", rz_items), ("Villanueva et al. 2022 (IRRI, IRG/IRIS)", vl_items),
       ("Dikitanan et al. 2022 (IRRI, Appendix A2)", dk_items), ("Kretzschmar et al. 2018 (IRRI; derived from printed pedigree)", kz_items),
       ("CGIAR innovation records (CRP Rice #1945, A4NH #2629)", cr_items)]

L = []
L.append("# CGIAR attribution cross-check (agent F3C, 2026-10-07)\n")
L.append("Compares the archive's `cgiar_role` / `cgiar_lineage` (05_output/rice_varieties.csv, as assembled before F3C) with CGIAR-original, variety-level attribution published outside SPIA 2025 T27, HarvestPlus BCR and TRIVSA. Archive codes: 1 = CGIAR line released directly; 2 = CGIAR parent or grandparent; 3 = collaboration/funding only; 4 = pedigree known, no CGIAR element; 5 = unknown. **No archive value was changed.** Evidence rows: `04_working/evidence_F3C.csv` (field `cgiar_independent`). Generated by `scripts/phase3_F3C_build.py`.\n")
L.append("## Each source's own definition of IRRI contribution\n")
L.append("- **Raitzer et al. 2015** (SPIA/ISPC). Last-cross rule plus geometric rule: \"direct releases of international crosses are given an absolute IRRI attributable weight of 100%\"; NARS crosses using IRRI germplasm are 50% NARS for the cross, the rest by pedigree share to great-grandparents (PDF p.41, Table 2.1 p.42). Table 3.2 (p.65) classes releases as IRRI cross / NARES cross with IRRI parent(s) / with IRRI ancestor(s) / no IRRI, but **only as period counts**; no variety rows. Only two varieties get numbers (p.92): BRRI dhan28 25%, dhan29 37.5%.")
L.append("- **Villanueva et al. 2022** (IRRI). Contribution of the International Rice **Genebank** (IRG), not of IRRI breeding: \"Definite contribution refers to a progenitor whose name is tagged with an International Rice Germplasm Collection (IRGC) number in the IRIS records\" (p.3-4); \"possible\" = name matches an IRG accession without an IRGC number. Values are pedigree probabilities 0-1 (Table S1).")
L.append("- **Dikitanan et al. 2022** (IRRI). Appendix Table A2 'Origin of variety' footnote: 1 = two IRRI lines as parents; 2 = 1 IRRI line as parent; 3 = with other IRRI ancestry; 4 = without IRRI connection. Parentage from IRIS, BRRI and BINA (p.5). Main text: IRRI \"directly or indirectly\" contributed to 87 of 89 leading varieties (p.2).")
L.append("- **Kretzschmar et al. 2018** (IRRI). No attribution statement. Supplementary Sheet A gives 'Year of release' and 'Origin' (pedigree) for 40 BRRI/BINA reference varieties from BRRI personal communication. F3C derived an 'IR token in pedigree' flag; treat as weak.")
L.append("- **CGIAR innovation records** (CGSpace OICR/innovation summaries). State lead and contributing organisations; no pedigree rule.\n")
L.append("## Comparison rules used\n")
L.append("| source verdict | counts as agreement when archive cgiar_role is |\n|---|---|")
L.append("| Raitzer: NARS cross with IRRI germplasm (25%/37.5%) | 2 |")
L.append("| Villanueva: definite IRG contribution > 0 | 1 or 2 |")
L.append("| Villanueva: definite = 0 (possible only, or none) | 3 or 4 |")
L.append("| Dikitanan: origin 1 or 2 (IRRI line(s) as parent) | 1 or 2 |")
L.append("| Dikitanan: origin 3 (other IRRI ancestry) | 2 (grandparent) or 4 (ancestry beyond grandparent) |")
L.append("| Dikitanan: origin 4 (no IRRI connection) | 3 or 4 |")
L.append("| Kretzschmar: IR designation in printed pedigree | 1 or 2 |")
L.append("| Kretzschmar: pedigree printed, no IR designation | 2, 3 or 4 |")
L.append("| CRP #1945 dhan97 (IR line, IRRI lead) | 1 |; dhan99, dhan100 (IRRI lead/contributing) | 1, 2 or 3 |\n")
L.append("Archive role 5/blank is reported as `archive_unknown`, not as a disagreement. Hybrids with 'unknown' pedigree and unkeyed names are `not_compared`.\n")
L.append("## Agreement rate per source\n")
L.append("| source | rows | compared | agree | disagree | archive unknown (5) | not in archive | not compared | agreement rate |\n|---|---|---|---|---|---|---|---|---|")
for src, items in SRC:
    c = tally(src, items)
    comp = c["agree"] + c["disagree"]
    rate = f"{c['agree']}/{comp} = {100 * c['agree'] / comp:.0f}%" if comp else "n/a"
    L.append(f"| {src} | {len(items)} | {comp} | {c['agree']} | {c['disagree']} | {c['archive_unknown']} | {c['not_in_archive']} | {c['not_compared']} | {rate} |")
L.append("")
L.append("## Every disagreement (and archive-unknown cases)\n")
for src, items in SRC:
    bad = [x for x in items if x[0] in ("disagree", "archive_unknown", "not_in_archive")]
    if not bad:
        continue
    L.append(f"### {src}\n")
    L.append("| status | key | name as printed | source says | archive cgiar_role | archive cgiar_lineage (abridged) | archive pedigree |\n|---|---|---|---|---|---|---|")
    for st, k, name, says, role, lin in bad:
        ped = (arch.get(k) or {}).get("pedigree", "")
        L.append(f"| {st} | {k} | {name} | {says} | {role} | {lin[:160].replace('|', '/')} | {ped[:90].replace('|', '/')} |")
    L.append("")
L.append("## Definitional notes on the disagreements\n")
L.append("- Dikitanan's origin codes describe **parents and ancestry only**; there is no 'IRRI cross released directly' class. An IRRI cross whose parents are not IR lines (BR2 = IR272 line from CP-SLO/Sigadis; BRRI dhan69 crossed at IRRI from WuShanYouZhan/PI312777) is coded 3 there but 1 in the archive. These are scheme differences, not factual conflicts.")
L.append("- Villanueva counts IRRI **genebank** accessions (IRGC numbers in IRIS), which include landraces and other countries' lines held at IRRI (e.g. via IET/BG/C-series ancestors). A 'definite' IRG share is therefore compatible with archive code 4 under the coordinator rule that CR/IET/BG designations are not CGIAR. The six Villanueva disagreements (BR21, dhan33, 39, 41, 54, 62) are all of this kind; for dhan39/41/54 the IRG content sits behind BR line codes the archive could not resolve.")
L.append("- Real factual conflicts worth a coordinator look: **BR21** (Dikitanan: 1 IRRI line as parent; Villanueva: definite 0.875; archive 4, pedigree C22/IET1444), **BRRI dhan27** (Dikitanan: 1 IRRI line as parent; archive 4, pedigree KN1B-361-1-8-6-9/C168), **BRRI dhan59** (Dikitanan: 1 IRRI line as parent; archive 3 INGER, pedigree blank), **BINA dhan16** (Dikitanan: other IRRI ancestry; archive 5 although its own pedigree cell says 'Contains IRRI genetic material').\n")
# release-year comparison
L.append("## Release years stated by these sources vs archive approval_date\n")
L.append("| source | key | name as printed | source year | archive approval_date |\n|---|---|---|---|---|")
nyr = collections.Counter()
for r in EV:
    if r["field"] != "approval_date" or r["pilot_key"] == "UNMATCHED":
        continue
    a = (arch.get(r["pilot_key"]) or {}).get("approval_date", "")
    src = r["source_id"]
    if not a:
        nyr[(src, "no_archive_date")] += 1; continue
    if a[:4] == r["value"]:
        nyr[(src, "same")] += 1
    else:
        nyr[(src, "differs")] += 1
        L.append(f"| {src} | {r['pilot_key']} | {r['value_raw'].split(' | ')[0]} | {r['value']} | {a} |")
L.append("")
L.append("Counts: " + "; ".join(f"{s} {k}={v}" for (s, k), v in sorted(nyr.items())) + "\n")
L.append("Year differences of 1 are expected (BRRI release year vs NSB meeting date). Kretzschmar's dhan28 = 2013 and dhan29 = 2014 are source errors (row note).\n")
(ROOT / "06_validation/cgiar_attribution_crosscheck.md").write_text("\n".join(L) + "\n", encoding="utf-8")

keys = {r["pilot_key"] for r in EV if r["pilot_key"] != "UNMATCHED"}
print("evidence rows", len(EV), "distinct keys", len(keys), "UNMATCHED rows", sum(r["pilot_key"] == "UNMATCHED" for r in EV))
print(collections.Counter(r["field"] for r in EV))
for s, c in stats.items():
    print(s, dict(c))
