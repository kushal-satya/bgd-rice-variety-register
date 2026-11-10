"""Comparison of the BAU stocktake draft (20 Sep 2026) with the register (round 3, agent E2). Validation only.

PI ruling 2026-11-10: BAU values are never written into evidence or the register; they are compared only.

    python scripts/bau_compare.py [path/to/Bangladesh_Stocktake_DRAFT_BAU_20_09_26.xlsx]

Inputs : the BAU workbook (sheet BD_innovation_latest; header rows 0-1; rice rows are those with column 1 == 'Rice'),
         05_output/final/bgd_rice_varieties.csv, the attribute columns of scripts/derive_attributes.add, and the variety_id
         of each BAU row: taken from 06_validation/bau_crosswalk.csv when it exists (the reviewed match), otherwise from the
         coordinator's automatic match (pickle given by BAU_MATCH_PKL) plus the manual matches in MANUAL below.
Outputs: 06_validation/bau_crosswalk.csv (one row per BAU rice row), 06_validation/bau_attribute_disagreements.csv
         (long), 06_validation/bau_missing_from_bau.csv (register varieties with no BAU row), and
         06_validation/bau_verification_sample.csv (random sample of 30 BAU values in fields the register cannot fill,
         for checking against the source BAU cites; the verdict columns are filled by hand).
BAU columns used (0-based): 2 name, 3 local/official name, 4 year of release, 6 type, 8 genetic line, 9 parental line,
11-13 yield potential Aus/Aman/Boro, 14-16 on-farm yield, 17-19 duration, 20-22 plant height, 28 grain type,
29 grain size (mm), 31 amylose, 32 'glycemic index', 35 NARS, 44 reference.
"""
import pathlib, re, sys, os
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
V = ROOT / "06_validation"
sys.path.insert(0, str(ROOT / "scripts"))
import derive_attributes as A

if len(sys.argv) < 2:   # the BAU draft is unpublished and is not archived; pass its path
    sys.exit("usage: python scripts/bau_compare.py <path to Bangladesh_Stocktake_DRAFT_BAU_20_09_26.xlsx>")
XLSX = pathlib.Path(sys.argv[1])
PKL = os.environ.get("BAU_MATCH_PKL", "")
# BAU rows the automatic match left open (Excel row number -> variety_id, basis). Evidence: the trade/line code in BAU
# column 8 equals the code in the register (official lists), and the company name is a transliteration of the official one.
MANUAL = {
    163: ("RICE-OLD_BAU63", "alias: BAU names it 'BAU Dhan-1 (BAU-63)'; register BAU-63 (Bharosa), approved 1982"),
    166: ("RICE-BU_AROMATIC_HYBRID1", "transliteration variant (official spelling: BU Aromatic Hybrid Dhan-1)"),
    172: ("RICE-HYB_AMARSHRI1", "transliteration variant (official spelling: Amarshri-1, অমরশ্রী-১)"),
    272: ("RICE-HYB_PETROCHEMAGRODHAN14", "name variant (official spelling: Petrochem Agro dhan-14, Pioneer 27P31)"),
    304: ("RICE-HYB_EXPLOREHYBRIDDHAN1", "transliteration variant (official spelling: Explore hybrid dhan1)"),
    307: ("RICE-HYB_WINALLHITECHHYBRIDDHAN1", "transliteration variant (official spelling: Winall Hi-Tech hybrid dhan1)"),
    308: ("RICE-HYB_WINALLHITECHHYBRIDDHAN2", "transliteration variant (official spelling: Winall Hi-Tech hybrid dhan2)"),
    335: ("RICE-HYB_ACIAGROLINKHYBRIDDHAN4", "line code PAC 202337 (official name: ACI Agrolink hybrid dhan4; BAU numbers it dhan-8)"),
    338: ("RICE-HYB_ACIFORMULATIONHYBRIDDHAN4", "transliteration variant (official spelling: ACI Formulations hybrid dhan4, BH 81)"),
    342: ("RICE-HYB_ACIFORMULATIONHYBRIDDHAN5", "name and number (official: ACI Formulations hybrid dhan5; code differs, see disagreements)"),
    343: ("RICE-HYB_ACIFORMULATIONHYBRIDDHAN8", "transliteration variant (official spelling: ACI Formulations hybrid dhan8, NASH 267)"),
    345: ("RICE-HYB_ACIFORMULATIONHYBRIDDHAN7", "transliteration variant (official spelling: ACI Formulations hybrid dhan7, AP20)"),
    361: ("RICE-HYB_GBKHYBRIDDHAN2", "line code JD-013 (official name: GBK hybrid dhan2; BAU 'Jindegi')"),
    362: ("RICE-HYB_BAGROHYBRIDDHAN1", "transliteration variant (official spelling: B-Agro hybrid dhan1, SQ-01; BAU 'Byangora')"),
    367: ("RICE-HYB_BAGROHYBRIDDHAN2", "transliteration variant (official spelling: B-Agro hybrid dhan2, KPHB02; BAU 'Byangora')"),
    364: ("RICE-HYB_THREESHYBRIDDHAN1", "transliteration variant (official spelling: Three S hybrid dhan1, SAVA-23; BAU 'GS')"),
    365: ("RICE-HYB_THREESHYBRIDDHAN2", "transliteration variant (official spelling: Three S hybrid dhan2, SAVA-81; BAU 'GS')"),
    368: ("RICE-HYB_THREESAGROHYBRIDDHAN3", "transliteration variant (official spelling: Three S Agro hybrid dhan3, C UU DA HE SO 1; BAU 'GS Agro')"),
    366: ("RICE-HYB_EXPLOREHYBRIDDHAN3", "transliteration variant (official spelling: Explore hybrid dhan3, Indam 300-007; BAU 'Excelor')"),
    370: ("RICE-HYB_DUPONTHYBRIDDHAN9", "line code Pioneer 28P94 (official name: DuPont hybrid dhan9; BAU numbers it dhan-1)"),
    373: ("RICE-HYB_NILSAGARHYBRIDDHAN1", "transliteration variant (official spelling: Nilsagar hybrid dhan1, Nil-102)"),
    393: ("RICE-HYB_MITALIAGROHYBRIDDHAN5", "line code SHD-2992 (official name: Mitali Agro hybrid dhan5; BAU numbers it dhan-6)"),
    397: ("RICE-HYB_NAFCOHYBRIDDHAN3", "transliteration variant (official spelling: Nafco hybrid dhan3, CQR-2; BAU 'Namco')"),
    406: ("RICE-HYB_BLESSINGHYBRIDDHAN1", "line code FD-6 (official name: Blessing hybrid dhan1, Blessing Agrovet Industries; BAU 'Racing Agrovet')"),
    407: ("RICE-HYB_SURAVIHYBRIDDHAN1", "transliteration variant (official spelling: Suravi hybrid dhan1, RXEL-34; BAU 'Suruchi')"),
    415: ("RICE-HYB_SURAVIHYBRIDDHAN2", "transliteration variant (official spelling: Suravi hybrid dhan2, PAN-2145; BAU 'Suruchi')"),
    409: ("RICE-HYB_SUPREMEHYBRIDHIRA25", "line code MRP-5222 (official name: Supreme hybrid Hira-25; BAU calls it Heera-15)"),
    422: ("RICE-HYB_AUSBANGLAHYBRIDDHAN1", "transliteration variant (official spelling: Aus-Bangla hybrid dhan1; BAU 'US-Bangla')"),
}
UNMATCHED_NOTE = {r: "no registration of this name in the NSB minutes, gazettes, SCA or MoA lists of the archive; BAU gives no year or code"
                  for r in (199, 200, 201, 202, 203)}

SEAS = {"aus": 0, "aman": 1, "boro": 2}
NUMF = [("yield_potential", 11, "t_ha"), ("duration", 17, "days"), ("plant_height", 20, "cm")]


def s(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return ""
    if isinstance(v, float) and v.is_integer(): return str(int(v))
    return str(v).strip()


def nn(x):
    return re.sub(r"[^0-9a-z\u0980-\u09ff]", "", s(x).lower().translate(A.BN))


def toks(b):
    """Codes BAU gives for a row: parenthetical parts of the name, the name itself, and column 8 split at '/'."""
    nm = s(b[2])
    parts = re.findall(r"\(([^)]+)\)", nm) + [re.sub(r"\([^)]*\)", "", nm)] + s(b[8]).split("/")
    parts += [p for q in parts for p in re.split(r"\s+", q) if re.search(r"\d", p)]
    return [re.sub(r"[^0-9A-Z]", "", p.upper()) for p in parts if len(re.sub(r"[^0-9A-Z]", "", p.upper())) >= 3]


def num_agree(ours, bau):
    """ours '140-145' or '140'; bau '142' -> True when bau lies in ours (or equal)."""
    try:
        lo, hi = (float(p) for p in (ours.split("-") + ours.split("-"))[:2]) if "-" in ours else (float(ours), float(ours))
        b = [float(p) for p in re.findall(r"\d+(?:\.\d+)?", bau)]
        return bool(b) and all(lo - 1e-9 <= x <= hi + 1e-9 for x in b) or (len(b) == 2 and b[0] == lo and b[1] == hi)
    except ValueError:
        return ours == bau


def main():
    x = pd.read_excel(XLSX, sheet_name="BD_innovation_latest", header=None)
    bau = x[(x[1] == "Rice") & x[2].notna()].copy()
    bau["bau_row"] = bau.index + 1
    reg = pd.read_csv(ROOT / "05_output/final/bgd_rice_varieties.csv", dtype=str, keep_default_na=False)
    att = A.add(reg).set_index("variety_id")
    eva = pd.read_csv(A.EVF, dtype=str, keep_default_na=False)
    readings = eva.assign(vid="RICE-" + eva.pilot_key).groupby(["vid", "field"]).apply(
        lambda g: list(zip(g.value, g.local_file, g.page))).to_dict()
    cw_old = V / "bau_crosswalk.csv"
    if cw_old.exists():
        m = pd.read_csv(cw_old, dtype=str, keep_default_na=False).set_index("bau_row")
        vid = {int(k): v for k, v in m.variety_id.items()}
        basis_manual = {r: b for r, (_, b) in MANUAL.items()}
    else:
        p = pd.read_pickle(PKL)
        vid = {int(i) + 1: v for i, v in p["vid"].items() if isinstance(v, str) and v}
        basis_manual = {}
        for r, (v, b) in MANUAL.items():
            vid[r] = v; basis_manual[r] = b
    names = {}
    for _, r in reg.iterrows():
        ns = [r.variety_name, r.official_name_en, r.popular_name] + r.aliases.split(" | ") + re.findall(r"\(([^)]+)\)", r.variety_name) + \
             [re.sub(r"\s*\(.*\)\s*$", "", r.variety_name)]
        names[r.variety_id] = [n for n in ns if n.strip()]
    codes = {}
    for _, r in reg.iterrows():
        cs = [r.breeding_line, r.official_name_en, r.trial_codes, r.pedigree_note] + r.aliases.split(" | ") + \
             re.findall(r"\(([^)]+)\)", r.variety_name) + r.trial_codes.split(";")
        codes[r.variety_id] = {re.sub(r"[^0-9A-Z]", "", c.upper()) for c in cs if c.strip()}
    out, att_dis = [], []
    for _, b in bau.iterrows():
        row = int(b.bau_row); v = vid.get(row, "")
        rec = dict(bau_row=row, bau_sl_no=s(b[0]), bau_name=s(b[2]), bau_local_name=s(b[3]), bau_year=s(b[4]),
                   bau_type=s(b[6]), bau_genetic_line=s(b[8]), bau_reference_code=(re.match(r"^([HN]\d\d-\d\d)", s(b[44])) or [""])[0],
                   variety_id=v, variety_name="", official_name_en="", approval_date="", match_basis="",
                   disagreements_identity="", disagreements_attributes="")
        if not v:
            rec["match_basis"] = "unmatched: " + UNMATCHED_NOTE.get(row, "no register variety found")
            out.append(rec); continue
        rr = reg.set_index("variety_id").loc[v]
        rec.update(variety_name=rr.variety_name, official_name_en=rr.official_name_en, approval_date=rr.approval_date)
        if row in basis_manual and basis_manual[row]:
            rec["match_basis"] = basis_manual[row]
        elif s(b[2]) in names[v]:
            rec["match_basis"] = "exact"
        elif nn(b[2]) in {nn(n) for n in names[v]}:
            rec["match_basis"] = "normalised"
        elif nn(re.sub(r"\s+(Aman|Boro|Aus|Boro/Aman)$", "", s(b[2]))) in {nn(n) for n in names[v]}:
            rec["match_basis"] = "normalised"
        elif any(t and t in codes[v] for t in toks(b)):
            t = next(t for t in toks(b) if t and t in codes[v])
            rec["match_basis"] = f"line or trade code {t} (official spelling: {rr.variety_name}; {rr.official_name_en})"
        else:
            rec["match_basis"] = f"transliteration variant (official spelling: {rr.official_name_en or rr.variety_name})"
        # identity disagreements (listed, not adjudicated: E1 owns identity fields)
        dis = []
        if s(b[4]) and s(b[4])[:4] != rr.approval_date[:4]:
            fy = rec["bau_reference_code"]
            dis.append(f"year: BAU {s(b[4])}{' (list ' + fy + ')' if fy else ''} vs NSB approval {rr.approval_date}")
        # local name: only when the register holds a Latin-script name to compare with (Bangla vs romanised is not a disagreement)
        latin = [n for n in names[v] if re.search(r"[A-Za-z]", n)]
        if s(b[3]) and nn(b[3]) != nn(b[2]) and re.search(r"[A-Za-z]", rr.popular_name) and \
                not any(nn(b[3]) in nn(n) or nn(n) in nn(b[3]) for n in latin if len(nn(n)) > 3):
            dis.append(f"local name: BAU '{s(b[3])}' vs register '{rr.popular_name}'")
        bl = re.sub(r"[^0-9A-Z]", "", s(b[8]).upper())
        if bl and not re.search(r"\d", bl):
            dis.append(f"genetic line: BAU '{s(b[8])}' is not a line code (register breeding_line '{rr.breeding_line}')")
        elif bl and rr.breeding_line and bl not in codes[v] and not any(bl in c or c in bl for c in codes[v] if len(c) > 4):
            dis.append(f"genetic line: BAU '{s(b[8])}' vs register breeding_line '{rr.breeding_line}'")
        # parentage: compare the coded parents (letters+digits); romanisation of landrace names is not a disagreement
        pc = lambda t: set(re.findall(r"(?<![A-Z])[A-Z]+\d+", re.sub(r"([A-Z])\s+(\d)", r"\1\2", t.upper())))
        cb, cr = pc(s(b[9])), pc(rr.pedigree)
        if cb and cr and cb != cr and not re.search(r"[ঀ-৿]", rr.pedigree):
            dis.append(f"parentage: BAU '{s(b[9])}' vs register pedigree '{rr.pedigree}'")
        rec["disagreements_identity"] = " | ".join(dis)
        # attribute disagreements (our value from archived sources vs BAU value)
        ad = []
        for base, c0, unit in NUMF:
            for se, k in SEAS.items():
                bv = s(b[c0 + k]); ov = att.at[v, f"{base}_{se}_{unit}"]
                if bv and ov and not num_agree(ov, bv):
                    ad.append((f"{base}_{se}_{unit}", bv, ov))
        for col, c in [("grain_type", 28), ("amylose_pct", 31)]:
            bv = s(b[c]); ov = att.at[v, col]
            if not (bv and ov): continue
            if col == "grain_type":
                if ov.split(" (")[0] not in bv.lower() and bv.lower() not in ov:
                    ad.append((col, bv, ov))
            elif not num_agree(ov.lstrip("<>"), bv):
                ad.append((col, bv, ov))
        for f, bv, ov in ad:
            grp = f.split("_")[0] if not f.startswith(("yield", "plant")) else "_".join(f.split("_")[:2])
            src = att.at[v, {"yield": "yield_potential_source", "duration": "duration_source", "plant_height": "plant_height_source",
                             "grain": "grain_source", "amylose": "grain_quality_source"}.get(grp if grp != "yield_potential" else "yield", "grain_source")]
            sp = [p for p in src.split(" | ") if p.startswith(f + ":")]
            other = [f"{rv} ({lf}{', p. ' + pg if pg else ''})" for rv, lf, pg in readings.get((v, f), [])
                     if (num_agree(rv.lstrip("<>"), bv) if f != "grain_type" else rv.split(" (")[0] in bv.lower())]
            att_dis.append(dict(bau_row=row, variety_id=v, field=f, bau_value=bv, register_value=ov,
                                register_source=sp[0].split(": ", 1)[1] if sp else "",
                                bau_value_also_in_archive="; ".join(dict.fromkeys(other))))
        rec["disagreements_attributes"] = "; ".join(f"{f}: BAU {bv} vs ours {ov}" for f, bv, ov in ad)
        out.append(rec)
    cw = pd.DataFrame(out)
    dup = cw[cw.variety_id.ne("") & cw.variety_id.duplicated(keep=False)]
    for v, g in dup.groupby("variety_id"):
        for i in g.index:
            others = ", ".join(str(r) for r in g.bau_row if r != cw.at[i, "bau_row"])
            cw.at[i, "disagreements_identity"] = (cw.at[i, "disagreements_identity"] + f" | duplicate: BAU row(s) {others} describe the same variety").strip(" |")
    cw.to_csv(V / "bau_crosswalk.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(att_dis).to_csv(V / "bau_attribute_disagreements.csv", index=False, encoding="utf-8-sig")
    miss = reg[~reg.variety_id.isin(set(cw.variety_id))][["variety_id", "variety_name", "official_name_en", "official_name_bn",
                                                              "developer_std", "rice_type", "approval_date", "release_category"]]
    miss.to_csv(V / "bau_missing_from_bau.csv", index=False, encoding="utf-8-sig")
    # verification sample: BAU values in fields where the register (our archive) is blank for that variety
    if not (V / "bau_verification_sample.csv").exists():
        pool = []
        fields = [(f"{base}_{se}_{unit}", c0 + k) for base, c0, unit in NUMF for se, k in SEAS.items()] + \
                 [(f"on_farm_yield_{se}_t_ha", 14 + k) for se, k in SEAS.items()] + \
                 [("grain_type", 28), ("grain_size_mm (BAU col 29)", 29), ("amylose_pct", 31), ("glycemic_index (BAU col 32)", 32)]
        for _, b in bau.iterrows():
            v = vid.get(int(b.bau_row), "")
            if not v: continue
            for f, c in fields:
                ours = att.at[v, f] if f in att.columns else ""
                if s(b[c]) and not ours:
                    pool.append(dict(bau_row=int(b.bau_row), variety_id=v, bau_name=s(b[2]), field=f, bau_column=c, bau_value=s(b[c]),
                                     bau_reference=s(b[44]).replace("\n", " || "), bau_reference_col49=s(b[49])))
        pool = pd.DataFrame(pool)
        smp = pool.sample(30, random_state=20261110).sort_values(["bau_row", "bau_column"])
        for c in ["source_checked", "source_value", "verdict", "note"]:
            smp[c] = ""
        smp.to_csv(V / "bau_verification_sample.csv", index=False, encoding="utf-8-sig")
        print("verification pool", len(pool), pool.field.value_counts().to_dict())
    print(f"BAU rice rows {len(cw)}; matched {cw.variety_id.ne('').sum()} ({cw.variety_id[cw.variety_id.ne('')].nunique()} varieties); "
          f"register varieties absent from BAU {len(miss)}; identity disagreements {cw.disagreements_identity.ne('').sum()} rows; "
          f"attribute disagreements {len(att_dis)}")
    print(cw.match_basis.str.extract(r"^(exact|normalised|line or trade code|line code|transliteration variant|alias|name|unmatched)")[0].value_counts().to_string())


if __name__ == "__main__":
    main()
