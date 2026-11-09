"""F3I: compare variety key sets across institute and CGIAR lists -> 06_validation/count_sources.md"""
import csv, pathlib, re, sys
from collections import defaultdict
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_keys import make_key
ROOT = pathlib.Path(__file__).resolve().parents[1]
E = list(csv.DictReader(open(ROOT / "04_working/evidence_F3I.csv", encoding="utf-8")))
S = defaultdict(set)
for r in E:
    sid, lf, f = r["source_id"], r["local_file"], r["field"]
    if sid == "RB-S08" and f == "official_name_bn" and "variety_list" in lf: S["BRRI site lists"].add(r["pilot_key"])
    if sid == "RB-S01" and f == "breeding_line": S["ADC 2025 T1"].add(r["pilot_key"])
    if sid == "DS-S07" and f == "source_url": S["Rice Profile"].add(r["pilot_key"])
    if sid == "DS-S01" and f == "cgiar_spia_flags": S["SPIA T27"].add(r["pilot_key"])
    if sid == "DS-S04" and f == "official_name_en": S["TRIVSA"].add(r["pilot_key"])
    if sid == "RB-S12" and f == "official_name_bn": S["BINA at-a-glance"].add(r["pilot_key"])
    if sid == "DS-S06" and f == "official_name_en": S["HarvestPlus BCR"].add(r["pilot_key"])
    if sid == "RB-S22" and f == "official_name_en": S["IAEA MVD"].add(r["pilot_key"])
    if sid == "RB-S04" and f == "breeding_line": S["BRRI fact sheets (F3I gap set)"].add(r["pilot_key"])
grp = lambda k: "BRRI" if k.startswith(("BR", "BRRI")) and not k.startswith("BRAC") else "BINA" if k.startswith(("BINA", "IRATOM")) else "other"
num = lambda k: (k.rstrip("0123456789"), int(re.sub(r"\D", "", k) or 0))
srt = lambda ks: ", ".join(sorted(ks, key=num)) or "(none)"
L = ["# Variety counts by source (F3I, 2026-10-06)", "",
     "Keys are `lib_keys.make_key` on variety-name cells (see decisions_F3I.md for the two hand-keyed rows: BINA 'বিনাধান-৭ | ২০১৫' -> BINADHAN17; MVD 'BINA dham 25' -> BINADHAN25).",
     "Built by `scripts/phase3_F3I_count_sources.py` from `04_working/evidence_F3I.csv`.", "",
     "| Source | Stated total | Keys found | BRRI keys | BINA keys | other keys | Coverage |", "|---|---|---|---|---|---|---|"]
STATED = {"BRRI site lists": "127 ('সর্বমোট ১২৭', index page)", "ADC 2025 T1": "115 (BR1-dhan108, hybrid 1-8)",
          "Rice Profile": "99 pages (ids 1-107, gaps)", "SPIA T27": "139 (1970-2023, report count)", "TRIVSA": "72 (to 2010 + pre-1974 IRRI)",
          "BINA at-a-glance": "27 rice rows (BINA total 28 per NSB-115 news)", "HarvestPlus BCR": "11 rice rows", "IAEA MVD": "15 rice rows",
          "BRRI fact sheets (F3I gap set)": "12 (dhan109-118, hybrid 9-10)"}
COV = {"BRRI site lists": "BR1-BR26 (no BR13), BRRI dhan27-118, hybrid 1-10", "ADC 2025 T1": "to 2024", "Rice Profile": "BR1 to BRRI dhan100, many gaps",
       "SPIA T27": "1970-2023, BRRI+BINA+BU", "TRIVSA": "1966-2010", "BINA at-a-glance": "1975-2026", "HarvestPlus BCR": "zinc rice", "IAEA MVD": "mutant-derived only",
       "BRRI fact sheets (F3I gap set)": "2025-2026 releases"}
for s, ks in S.items():
    L.append(f"| {s} | {STATED.get(s,'')} | {len(ks)} | {sum(grp(k)=='BRRI' for k in ks)} | {sum(grp(k)=='BINA' for k in ks)} | {sum(grp(k)=='other' for k in ks)} | {COV.get(s,'')} |")
site, adc, rp, spia, triv, bina = (S[x] for x in ("BRRI site lists", "ADC 2025 T1", "Rice Profile", "SPIA T27", "TRIVSA", "BINA at-a-glance"))
brri = lambda ks: {k for k in ks if grp(k) == "BRRI"}
binak = lambda ks: {k for k in ks if grp(k) == "BINA"}
L += ["", "## BRRI: 127 (site) vs 115 (ADC) vs Rice Profile vs SPIA vs TRIVSA", "",
      f"- Site total check: site lists give {len(site)} distinct keys (125 with a fact-sheet link; BR4 and BR5 rows link 'not_found.jpg'); index page says 127. Breakdown: {len([k for k in site if 'HYBRID' not in k])} inbred + {len([k for k in site if 'HYBRID' in k])} hybrid.",
      f"- On site, not in ADC 2025 ({len(site-adc)}): {srt(site-adc)}. All are 2025-2026 releases after the June 2025 ADC edition.",
      f"- In ADC, not on site: {srt(adc-site)}.",
      f"- On site, no Rice Profile page ({len(site-rp)}): {srt(site-rp)}.",
      f"- Rice Profile pages not on site: {srt(rp-site)}.",
      f"- BRRI keys in SPIA T27: {len(brri(spia))}. On site but not in SPIA ({len(site-spia)}): {srt(site-spia)}. (SPIA cut-off 2023: BRRI dhan107-118 and hybrid 8-10 are expected to be missing; any older key here is a SPIA gap.)",
      f"- BRRI keys in SPIA not on site: {srt(brri(spia)-site)}.",
      f"- BRRI keys in TRIVSA: {len(brri(triv))} (TRIVSA BD set ends 2010). BRRI keys in TRIVSA not on site: {srt(brri(triv)-site)}. Site keys released to 2010 (ADC year <= 2010) missing from TRIVSA: "
      + srt({k for k in site & adc if any(r['pilot_key']==k and r['source_id']=='RB-S01' and r['field']=='approval_date' and r['value'][:4].isdigit() and int(r['value'][:4])<=2010 for r in E)} - triv) + ".",
      "", "## BINA: 28", "",
      f"- BINA at-a-glance rice keys ({len(bina)}): {srt(bina)}.",
      "- Missing from the BINA table: BINADHAN27 (approved at NSB 115, 2026-02-05, per news and NSB sources outside F3I scope). The table's second 'বিনাধান-৭ | ২০১৫' row is keyed to BINADHAN17, which gives 27 rows = 27 distinct keys; 27 + Binadhan-27 = 28. No Binadhan-1/2/3 exist under that name.",
      f"- BINA keys in SPIA T27 ({len(binak(spia))}): {srt(binak(spia))}. In BINA table but not SPIA: {srt(bina-spia)} (post-2023 or Iratom-38). In SPIA but not BINA table: {srt(binak(spia)-bina)}.",
      f"- BINA keys in TRIVSA: {srt(binak(triv))}. Not on BINA table: {srt(binak(triv)-bina)}.",
      f"- BINA keys in IAEA MVD: {srt(binak(S['IAEA MVD']))}.",
      "", "## Other breeders seen in these lists", "",
      f"- SPIA T27 non-BRRI/BINA keys: {srt({k for k in spia if grp(k)=='other'})}.",
      f"- TRIVSA non-BRRI/BINA keys: {srt({k for k in triv if grp(k)=='other'})}.",
      "- Not in any F3I list: GAU dhan3 (Banglajol ABA 84826 only), GAU dhan4, BU dhan2, BAU dhan1, BAU dhan3 (ACI page only), the BRAC inbred registered at NSB 106 (name not found), Rabi dhan1 (ACI page).",
      "", "## Key in exactly one F3I list", ""]
allk = set().union(*S.values())
for k in sorted(allk, key=num):
    ins = [s for s, ks in S.items() if k in ks]
    if len(ins) == 1:
        L.append(f"- {k}: only in {ins[0]}")
(ROOT / "06_validation/count_sources.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
