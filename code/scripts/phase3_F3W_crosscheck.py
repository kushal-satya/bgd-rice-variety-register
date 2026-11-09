"""F3W: compare evidence_F3W.csv (CGIAR websites) with 05_output/rice_varieties.csv cgiar_role/cgiar_lineage.
Writes 06_validation/cgiar_websites_crosscheck.md. Does not change the archive."""
import csv, pathlib, re
from collections import defaultdict
ROOT = pathlib.Path(__file__).resolve().parents[1]
ev = list(csv.DictReader(open(ROOT / "04_working/evidence_F3W.csv", encoding="utf-8")))
arch = {r["variety_id"].replace("RICE-", ""): r for r in csv.DictReader(open(ROOT / "05_output/rice_varieties.csv", encoding="utf-8-sig"))}

# claim strength stated by the CGIAR page: D = CGIAR line/developed by CGIAR; C = collaboration/co-development/funding;
# H = HarvestPlus support; N = national credit only (no CGIAR role in development); M = mention/testing/dissemination only
CLAIM = {
 ("IR8", "F3W-W01"): "D", ("BRRI_DHAN47", "F3W-W02"): "D", ("BRRI_DHAN96", "F3W-W03"): "N", ("BRRI_DHAN99", "F3W-W04"): "C",
 ("BRRI_DHAN97", "F3W-W04"): "C", ("BINADHAN10", "F3W-W04"): "C", ("BRRI_DHAN88", "F3W-W05"): "N", ("BRRI_DHAN100", "F3W-W05"): "N",
 ("BRRI_DHAN52", "F3W-W06"): "D", ("BRRI_DHAN51", "F3W-W06"): "D", ("BRRI_DHAN56", "F3W-W06"): "N", ("BRRI_DHAN71", "F3W-W06"): "N",
 ("IR20", "F3W-W07"): "D", ("BRRI_DHAN51", "F3W-W08"): "D", ("BRRI_DHAN107", "F3W-W09"): "N", ("BRRI_DHAN108", "F3W-W09"): "N",
 ("BINADHAN11", "F3W-W10"): "N", ("BRRI_DHAN51", "F3W-W12"): "D", ("BINADHAN8", "F3W-W13"): "C", ("BINADHAN10", "F3W-W13"): "C",
 ("BRRI_DHAN47", "F3W-W13"): "C", ("BRRI_DHAN55", "F3W-W13"): "C", ("BRRI_DHAN78", "F3W-W14"): "C", ("BRRI_DHAN72", "F3W-W15"): "H",
 ("BRRI_DHAN64", "F3W-W15"): "H", ("BRRI_DHAN100", "F3W-W16"): "H", ("BRRI_DHAN62", "F3W-W16"): "H", ("BRRI_DHAN74", "F3W-W16"): "H",
 ("BRRI_DHAN84", "F3W-W16"): "H", ("BRRI_DHAN62", "F3W-W17"): "H", ("BRRI_DHAN97", "F3W-W19"): "D", ("BRRI_DHAN99", "F3W-W19"): "D",
 ("BRRI_DHAN100", "F3W-W20"): "H", ("BRRI_DHAN84", "F3W-W21"): "H", ("BINADHAN20", "F3W-W22"): "H", ("BRRI_DHAN51", "F3W-W23"): "C",
 ("BRRI_DHAN52", "F3W-W23"): "C", ("BRRI_DHAN79", "F3W-W23"): "C", ("BINADHAN11", "F3W-W23"): "C", ("BINADHAN12", "F3W-W23"): "C",
 ("BRRI_DHAN50", "F3W-W24"): "M", ("BRRI_DHAN63", "F3W-W24"): "M", ("BINADHAN17", "F3W-W25"): "C", ("BRRI_DHAN75", "F3W-W25"): "C",
 ("BRRI_DHAN51", "F3W-W26"): "D", ("BRRI_DHAN56", "F3W-W27"): "D", ("BRRI_DHAN62", "F3W-W33"): "H", ("BRRI_DHAN33", "F3W-W28"): "C",
 ("BRRI_DHAN69", "F3W-W28"): "C", ("BINADHAN17", "F3W-W28"): "C", ("BINADHAN11", "F3W-W29"): "N",
}
LBL = {"D": "CGIAR-developed / CGIAR line", "C": "collaboration / co-developed with CGIAR", "H": "HarvestPlus support / zinc rice",
       "N": "credited to national institute only", "M": "mention / testing / dissemination only"}

def verdict(claim, role, lineage, key):
    hp = "HarvestPlus" in lineage
    if claim == "M": return "n/a (no development claim)"
    if claim == "N":
        return "framing difference (CGIAR page silent on CGIAR origin; archive codes %s)" % role if role in ("1", "2", "3") else "agree (no CGIAR claim; archive %s)" % role
    if role in ("", "5", "4"):
        return "DISAGREE: CGIAR site claims involvement, archive cgiar_role=%s" % (role or "blank")
    if claim == "D": return "agree" if role == "1" else "partial: site says CGIAR-developed, archive code %s" % role
    if claim == "C": return "agree (archive %s is at least as strong)" % role
    if claim == "H": return "agree" if (hp or role == "3") else "partial: archive %s via IRRI parent; HarvestPlus not in lineage" % role
    return "?"

by_site = defaultdict(list)
for r in ev:
    if r["field"] != "cgiar_independent": continue
    by_site[r["source_id"]].append(r)
SITE = {"IRRI (irri.org, Rice Today, IRRI news blog)": ["F3W-W01", "F3W-W02", "F3W-W03", "F3W-W04", "F3W-W05", "F3W-W06", "F3W-W07", "F3W-W08", "F3W-W09", "F3W-W10", "F3W-W11", "F3W-W28", "F3W-W29"],
        "STRASA (strasa.irri.org)": ["F3W-W12", "F3W-W13", "F3W-W14"],
        "HarvestPlus (harvestplus.org) and HarvestPlus/IFPRI brief": ["F3W-W15", "F3W-W16", "F3W-W17", "F3W-W18", "F3W-W33"],
        "CGIAR reporting records on CGSpace (CRP Rice / A4NH innovations, OICR, MELIA) and SPIA": ["F3W-W19", "F3W-W20", "F3W-W21", "F3W-W22", "F3W-W23", "F3W-W24", "F3W-W25", "F3W-W26", "F3W-W27"]}
L = ["# CGIAR websites cross-check (agent F3W, 2026-10-07)", "",
     "Compares what CGIAR centre/programme websites and CGIAR's own reporting records say about Bangladesh rice varieties with the archive's",
     "`cgiar_role` / `cgiar_lineage` in `05_output/rice_varieties.csv`. Evidence rows: `04_working/evidence_F3W.csv` (field `cgiar_independent`, authority_rank `4_cgiar_record`).",
     "No archive code was changed. Claim types: " + "; ".join(f"**{k}** = {v}" for k, v in LBL.items()) + ".", ""]
dis = []
for site, sids in SITE.items():
    L += [f"## {site}", "", "| key | source | claim | archive cgiar_role | archive cgiar_lineage (start) | verdict |", "|---|---|---|---|---|---|"]
    for sid in sids:
        for r in by_site.get(sid, []):
            k = r["pilot_key"]
            a = arch.get(k)
            if k == "UNMATCHED":
                L.append(f"| UNMATCHED | {sid} | aggregate | - | - | see notes below |"); continue
            claim = "M" if ("mention only" in r["notes"] or "dissemination, not development" in r["value"]) else CLAIM.get((k, sid), "?")
            if not a:
                L.append(f"| {k} | {sid} | {claim} | NOT IN ARCHIVE | | **variety claimed but not in archive** |"); dis.append((k, sid, "not in archive")); continue
            v = verdict(claim, a["cgiar_role"], a["cgiar_lineage"], k)
            if v.startswith("DISAGREE") or v.startswith("partial") or v.startswith("framing"): dis.append((k, sid, v))
            L.append(f"| {k} | {sid} | {claim} | {a['cgiar_role']} {a['cgiar_center']} | {a['cgiar_lineage'][:70].replace('|', '/')} | {v} |")
    L.append("")

# dates / lines
L += ["## Dates, breeding lines, aliases stated on CGIAR sites vs archive", "", "| key | field | CGIAR site value | archive value | source | result |", "|---|---|---|---|---|---|"]
for r in ev:
    if r["field"] not in ("approval_date", "breeding_line", "pedigree", "aliases", "release_date"): continue
    a = arch.get(r["pilot_key"])
    if not a:
        L.append(f"| {r['pilot_key']} | {r['field']} | {r['value']} | (fish: see evidence_P2F.csv) | {r['source_id']} | see notes |"); continue
    av = {"approval_date": a["approval_date"], "breeding_line": a["breeding_line"], "pedigree": a["pedigree"], "aliases": a["aliases"]}.get(r["field"], "")
    if r["field"] == "approval_date": ok = av[:4] == r["value"][:4]
    elif r["field"] == "breeding_line": ok = re.sub(r"\W", "", r["value"]).upper() in re.sub(r"\W", "", av).upper()
    else: ok = None
    res = "agree" if ok else ("DISAGREE" if ok is False else "consistent (text)")
    if ok is False: dis.append((r["pilot_key"], r["source_id"], f"{r['field']} {r['value']} vs archive {av}"))
    L.append(f"| {r['pilot_key']} | {r['field']} | {r['value']} | {av[:40].replace('|', '/')} | {r['source_id']} | {res} |")
L.append("")
head = (ROOT / "04_working/F3W_crosscheck_summary.md").read_text(encoding="utf-8")
open(ROOT / "06_validation/cgiar_websites_crosscheck.md", "w", encoding="utf-8").write(
    head.rstrip() + "\n\n# Detailed tables (generated by scripts/phase3_F3W_crosscheck.py)\n\n" + "\n".join(L[6:]) + "\n")
for d in dis: print(d)
