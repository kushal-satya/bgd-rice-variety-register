"""REV2 (round-1 review, November 2026): write the reviewer corrections and the new evidence rows of version 1.2.

Outputs (both are ordinary inputs of scripts/assemble.py; this script only writes them and is not part of rebuild_all.sh):
  04_working/evidence_corrections_rev2.csv   agent REV2; drop | refield | replace (replace with empty value adds a row)
  04_working/evidence_REV2.csv               new evidence rows read by eye on the page image or the minutes text

Every value that a correction must match is looked up in the raw extraction files (04_working/evidence_*.csv) so that a
correction never silently misses; the script stops if an expected value is not found. Reasons cite file and page.
Run: python scripts/rev2_corrections.py
"""
import csv
import glob
import pathlib
import re
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
W = ROOT / "04_working"
raw = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False) for f in glob.glob(str(W / "evidence_*.csv"))
                 if not re.search(r"evidence_(corrections|attendance|REV2)", f)], ignore_index=True)
COR, EV = [], []


def values(key, field, pat=None, src=None):
    x = raw[(raw.pilot_key == key) & (raw.field == field)]
    if src:
        x = x[x.source_id.str.match(src)]
    if pat:
        x = x[x.value.str.contains(pat, regex=True)]
    return sorted(set(x.value))


def cor(key, field, value, action, reason, new_value="", new_field="", must=True):
    if must and value and not ((raw.pilot_key == key) & (raw.field == field) & (raw.value == value)).any():
        sys.exit(f"value not found: {key} {field} {value[:60]}")
    COR.append(dict(agent="REV2", pilot_key=key, field=field, value=value, action=action, new_field=new_field,
                    reason=reason, new_value=new_value))


def ev(key, field, value, source_id, title, rank, local_file, page, locator, notes, validation="visual_check", value_raw="",
       method="ocr"):
    EV.append(dict(pilot_key=key, field=field, value=value, value_raw=value_raw or value, source_id=source_id,
                   source_title=title, authority_rank=rank, local_file=local_file, page=str(page), locator=locator,
                   method=method, validation=validation, confidence="high", notes="REV2 2026-11-10: " + notes))


# ---------------------------------------------------------------- A. trait glosses
NS = "official Bangla text says অলবণাক্ত (non-saline); the English gloss dropped the negation (review A1-01/A1-02, 2026-11-10)"
cor("BRRI_DHAN27", "key_traits", "salt tolerant", "replace", NS + "; BRRI riceprofile variety page (DS-S07)",
    "suited to non-saline tidal land of Barishal and Patuakhali (aus)")
cor("BRRI_DHAN44", "key_traits", "salt tolerant", "replace", NS + "; ADC 2025 p.14 (RB-S01) and riceprofile (DS-S07)",
    "suited to non-saline coastal tidal areas")
cor("BRRI_DHAN52", "key_traits", "salt tolerant; submergence tolerant", "replace", NS + "; riceprofile (DS-S07)",
    "submergence tolerant; also suited to non-saline tidal medium-high land of Barishal, Patuakhali and Bhola")
cor("BRRI_DHAN106", "key_traits", "salt tolerant", "replace", NS + "; ADC 2025 (RB-S01) 'বরিশাল অঞ্চলের অলবণাক্ত জোয়ার-ভাটা'",
    "suited to non-saline tidal areas of Barishal (transplanted aus)")
# SPIA Table 27 flag glosses copied into key_traits duplicate cgiar_spia_flags; a stress tag must not rest on them alone
GLOSS = {"saline tolerant", "drought tolerant", "Sub1", "saline tolerant; drought tolerant", "Sub1; saline tolerant"}
g = raw[(raw.source_id == "DS-S01") & (raw.field == "key_traits") & raw.value.isin(GLOSS)]
for (k, v), _ in g.groupby(["pilot_key", "value"]):
    other = raw[(raw.pilot_key == k) & (raw.field == "key_traits") & (raw.value == v) & (raw.source_id != "DS-S01")]
    if len(other):
        continue          # the same words also come from another source: leave them
    cor(k, "key_traits", v, "refield", "gloss of the SPIA 2025 Table 27 flags (DS-S01), which are kept in cgiar_spia_flags; "
        "not a trait statement (review A1-03, 2026-11-10)", new_field="spia_trait_gloss")

# ---------------------------------------------------------------- B. identity
cor("BU_AROMATIC_DHAN2", "official_name_en", "BU Aromatic Dhan-2", "refield",
    "SPIA/HarvestPlus label of BU dhan2 (same institute, year and zinc content 22 mg/kg; NSB 90 approved one BSMRAU rice "
    "variety in 2016); kept as an alias (review A6-02)", new_field="aliases")
for v in values("OLD_JIRASHAIL", "decision_conditions", pat="৬৭তম"):
    cor("OLD_JIRASHAIL", "decision_conditions", v, "drop",
        "text of the NSB 75 hybrid-registration item (Sura, Agomoni, parent-line and wheat-seed imports), not a decision "
        "on Jirashail (review A6-09)")
N1 = "02_raw/sca/nsb_minutes_001-018.pdf"
T1 = "NSB minutes 1-18 (1974-1981), sca.gov.bd"
ev("BR4", "aliases", "Bri-shail", "NSB_R1", T1, "1_primary_legal", N1, 14, "NSB 4, agenda 08.8 (জ) 'রি-শাইল' (OCR); same variety as BR4",
   "popular name under which BR4 was approved; RICE-OLD_BRISHAIL merged into BR4 in v1.1", value_raw="ব্রি-শাইল")
ev("BR4", "aliases", "Brishail", "NSB_R1", T1, "1_primary_legal", N1, 14, "NSB 4, agenda 08.8 (জ)", "romanised popular name")
ev("HYB_LOKNATH505", "aliases", "Loknath-503", "NSB_29_42", "NSB minutes 29-42", "1_primary_legal",
   "02_raw/sca/nsb_minutes_029-042.pdf", 45, "NSB 40, agenda 2.30 decision", "NSB 40 prints লোকনাথ-৫০৩; the MoA lists print 505 "
   "(review A6-07)", value_raw="লোকনাথ-৫০৩")
L24 = "02_raw/sca/approved_crop_varieties_2024-25.pdf"
ev("BRRI_DHAN114", "duration_days", "143", "SCA_FY2024-25_INBRED", "২০২৪-২৫ অর্থবছরে নোটিফাইড ফসলের জাত ছাড়করণ", "2_official_list",
   L24, 2, "SCA_FY2024-25_INBRED row 6 col 6 (row printed as ব্রি ধান১১৩)",
   "row 6 is BRRI dhan114: the second Boro BRRI release of NSB 114, blast resistant, and BRRI dhan113 is row 5 (review A6-06)",
   value_raw="১৪৩")
# names with an NSB decision and no registration through NSB 115 (review A6-10)
NOTAPP = [("HYB_MALLIKABASMATI1", "মল্লিকা বাসমতি-১ (সুগন্ধী)", "Mallika Seed Company", "02_raw/sca/nsb_minutes_058-075.pdf", 66, "NSB_R5", 67,
           "2008-09-17", "may be registered after a second-year trial if its yield equals BRRI dhan28 and papers on aromaticity are supplied"),
          ("HYB_SUPREMEHYBRIDDHAN23", "সুপ্রীম হাইব্রিড ধান-২৩", "Supreme Seed Company", "02_raw/sca/nsb_minutes_101.pdf", 3, "NSB_101", 101,
           "2019-11-19", "sent back to the Technical Committee with 16 other Boro hybrids (check yields identical)"),
          ("HYB_NATIONALAGRICAREHYBRIDDHAN3", "ন্যাশনাল এগ্রিকেয়ার হাইব্রিড ধান-৩", "National Agri Care", "02_raw/sca/nsb_minutes_101.pdf", 3,
           "NSB_101", 101, "2019-11-19", "sent back to the Technical Committee with 16 other Boro hybrids (check yields identical)"),
          ("HYB_ISPAHANIHYBRIDDHAN11", "ইস্পাহানি হাইব্রিড ধান১১", "Ispahani Agro", "02_raw/sca/nsb_minutes_106.pdf", 2, "NSB_106", 106,
           "2022-01-18", "re-trial ordered under a BRRI/BADC/DAE monitoring team"),
          ("HYB_MITALIHYBRIDDHAN6", "মিতালী হাইব্রিড ধান৬", "Mitali Agro Seed Industries", "02_raw/sca/nsb_minutes_106.pdf", 2, "NSB_106", 106,
           "2022-01-18", "re-trial ordered under a BRRI/BADC/DAE monitoring team"),
          ("HYB_GIANTAGROHYBRIDDHAN3", "জায়েন্ট এগ্রো হাইব্রিড ধান৩ (রত্না)", "Giant Agro Processing", "02_raw/sca/nsb_minutes_111.pdf", 3,
           "NSB_111", 111, "2024-01-09", "amylose content to be determined by BRRI before a decision"),
          ("HYB_NATIONALAGRICAREHYBRIDDHAN9", "ন্যাশনাল এগ্রি কেয়ার হাইব্রিড ধান৯ (ARBH21092)", "National Agri Care",
           "02_raw/sca/nsb_minutes_111.pdf", 3, "NSB_111", 111, "2024-01-09", "amylose content to be determined by BRRI before a decision")]
for key, bn, dev, lf, pg, sid, mtg, date, why in NOTAPP:
    t = f"NSB {mtg}th meeting minutes"
    ev(key, "official_name_bn", bn, sid, t, "1_primary_legal", lf, pg, f"NSB {mtg} ({date})", "name as printed in the deferral (F3M decision register)", validation="key_check")
    ev(key, "developer", dev, sid, t, "1_primary_legal", lf, pg, f"NSB {mtg} ({date})", "applicant named in the minutes (F3M decision register)", validation="key_check")
    ev(key, "decision_conditions", f"NSB {mtg} ({date}): {why}", sid, t, "1_primary_legal", lf, pg, f"NSB {mtg}", "summary of the decision (F3M decision register notes)",
       validation="key_check")
    ev(key, "status", "not approved: deferred or conditional; no later registration through NSB 115 (2026-02-05)", sid, t,
       "1_primary_legal", lf, pg, f"NSB {mtg}", "no later decision names this variety (bgd_nsb_decisions_full.csv searched by name)",
       validation="key_check")

# ---------------------------------------------------------------- C. Iratom-38 and Iratom-24 approval
IR = ("NSB 4 (1975-06-18), agenda 08.8 (ছ): 'ইরাটমের বীজ বিতরণ করা যাইতে পারে' (generic Iratom; varieties not numbered); NSB 7 "
      "(1976-08-16, minutes p.17) records that the BAEC 'Iratom' had NSB approval; NSB 12-14 discuss Iratom-24 and Iratom-38 as the "
      "approved Iratom varieties and NSB 14 (1981-03-30, p.29) continues Iratom-24 and suspends the cultivation of Iratom-38 (review A1-07, A6-04)")
REF = "NSB 4th meeting, agenda 08.8 (ছ) (generic 'Iratom'; varieties not numbered)"
for k in ("IRATOM24", "IRATOM38"):
    ev(k, "approval_date", "1975-06-18", "NSB_R1", T1, "1_primary_legal", N1, 14, "NSB 4, agenda 08.8 (ছ)", IR)
    ev(k, "approval_reference", REF, "NSB_R1", T1, "1_primary_legal", N1, 14, "NSB 4, agenda 08.8 (ছ)", IR)
ev("IRATOM38", "release_category", "NSB_release", "NSB_R1", T1, "1_primary_legal", N1, 14, "NSB 4, agenda 08.8 (ছ)", IR)
for v in values("IRATOM38", "status", pat="withdrawn"):
    cor("IRATOM38", "status", v, "replace", "the NSB suspended its cultivation at the 14th meeting (1981-03-30); no withdrawal "
        "is recorded (review A1-07)", "suspended (NSB 14, 1981-03-30)")

# ---------------------------------------------------------------- E. origin_country
for k, v, nv in [("BRRI_HYBRID1", "IRRI", "Philippines (IRRI)"), ("PVT_ACI_DHAN1", "Philippines (IRRI segregating population)", "Philippines (IRRI)"),
                 ("HYB_GETCOAGROVISIONHYBRIDDHAN5", "China/Bangladesh", "China; Bangladesh")]:
    cor(k, "origin_country", v, "replace", "origin_country normalised to country names; IRRI recorded as 'Philippines (IRRI)' "
        f"(printed '{v}'; review A1-10)", nv)
for k, nv in [("HYB_PARTEXHYBRIDDHAN5", "China"), ("HYB_PETROCHEMHYBRIDDHAN4", "India")]:
    for v in values(k, "origin_country", pat="corrected"):
        cor(k, "origin_country", v, "replace", f"normalised; the correction text '{v}' is kept in the row notes (review A1-10)", nv)

# ---------------------------------------------------------------- G. CGIAR codes
for k, src, why in [("BINADHAN19", "02_raw/sca/nsb_minutes_092.pdf p.4", "NERICA-10 seed irradiated with carbon ions (40 Gy)"),
                    ("BINADHAN21", "02_raw/sca/nsb_minutes_097.pdf p.4", "NERICA-10 seed irradiated with gamma rays (350 Gy)"),
                    ("IRATOM24", "SCA 2016 compendium; ASTI-TRIVSA", "gamma-ray mutant of IR8")]:
    cor(k, "cgiar_role", "", "replace", f"a mutant of a CGIAR line is code 1 (CGIAR line released directly, or a mutant or selection "
        f"within one; depth_to_cgiar 0): {why} ({src}); review A2-06 / A4-02, 2026-11-10", "1", must=False)
cor("BRRI_DHAN33", "cgiar_role", "3", "drop", "code 3 rested on an IRRI News sentence alone (F3W-W28, unvalidated); the documented "
    "pedigree BG388/BG367-4 (ADC 2025 p.9; NSB 38 minutes p.36) has no CGIAR element, so code 4 (review A4-07)")
cor("BRRI_DHAN33", "cgiar_center", "IRRI", "drop", "follows the cgiar_role correction above (review A4-07)")
for v in values("BRRI_DHAN33", "cgiar_lineage", src="F3W-W28"):
    cor("BRRI_DHAN33", "cgiar_lineage", v, "refield", "a CGIAR self-report is a cross-check, not a coded link (review A4-07)",
        new_field="cgiar_independent")

# ---------------------------------------------------------------- H. fish
for v in values("FISH_BFRI_RAJPUTI", "species_scientific", pat="Systomus"):
    cor("FISH_BFRI_RAJPUTI", "species_scientific", v, "replace", "rajputi (silver barb) is Barbonymus gonionotus; Systomus sarana is "
        "the olive barb (sarpunti). The TVC list misprints the name (review A7-09)",
        "Barbonymus gonionotus (the BFRI TVC list prints Systomus sarana)")
for v in values("FISH_BFRI_SUBARNA_RUI_G4", "strain_name", pat=r"^সুবর্ণ রুই \(Subarno Rui\)$"):
    cor("FISH_BFRI_SUBARNA_RUI_G4", "strain_name", v, "replace", "named সুবর্ণ রুই by MoFL notification of 04 Aug 2021 and renamed "
        "'বিএফআরআই সুবর্ণ রুই' by MoFL notification of 11 Apr 2022; the current name is used (review A7-10)",
        "বিএফআরআই সুবর্ণ রুই (BFRI Subarno Rui)")
for v in values("FISH_BFRI_SUBARNA_RUI_G4", "status", pat="superseded"):
    cor("FISH_BFRI_SUBARNA_RUI_G4", "status", v, "replace", "the strain is not superseded; only its name changed (review A7-10)",
        "released; named Subarno Rui 2021-08-04, renamed BFRI Subarno Rui 2022-04-11 (current name)")
for v in values("FISH_BFRI_SUBARNA_RUI_G4", "approval_or_release_mechanism", pat="R1_statutory"):
    cor("FISH_BFRI_SUBARNA_RUI_G4", "approval_or_release_mechanism", v, "replace", "release code R1 renamed R1_ministerial_naming in "
        "v1.1.1 (review A7-07)", v.replace("R1_statutory", "R1_ministerial_naming"))

# ---------------------------------------------------------------- A4 data audit
for v in values("HYB_SYNGENTASJ201", "region_scope", pat=r"^Jessore region\(s\)$"):
    cor("HYB_SYNGENTASJ201", "region_scope", v, "replace", "MoA 2026 list p.4 row 97 prints 'ময়মনসিংহ ও যশোর', as do the 2016, 2018 and "
        "2020 lists (review A4-04)", "Mymensingh, Jessore region(s)")
SEASON_ONLY = "a season statement from the 2015-01-22 gazette sentence, not a region; the region is the compendium's 'nationwide'"
for k, why in [("BINADHAN14", SEASON_ONLY + " (NSB 80 p.32: 'বোরো মৌসুমে সারা দেশে')")] + \
              [(k, SEASON_ONLY) for k in ("BRRI_DHAN65", "BRRI_DHAN66", "BRRI_DHAN67", "BRRI_DHAN68", "BRRI_DHAN69")]:
    for v in values(k, "region_scope", pat="[ঀ-৿]"):
        cor(k, "region_scope", v, "drop", why + " (review A4-03)")
TR = {"BRRI_DHAN106": "Chattogram, Barishal (non-saline tidal areas)", "BRRI_DHAN109": "tidal areas",
      "BRRI_DHAN110": "flash-flood-prone areas", "BRRI_DHAN111": "flood-prone areas", "BRRI_DHAN27": "AEZ 12, 13 and 18",
      "BRRI_DHAN32": "Comilla, Brahmanbaria (except AEZ 1, 5, 14, 15 and 16)", "BRRI_DHAN85": "Comilla region and the east",
      "BRRI_DHAN91": "Manikganj, Faridpur, Comilla region(s)", "BRRI_DHAN92": "Rajshahi, Rangpur, Khulna region(s)",
      "BRRI_DHAN94": "Rangpur, Dinajpur, Rajshahi region(s)", "BRRI_HYBRID3": "Comilla, Rajshahi region(s)",
      "BRRI_HYBRID4": "Comilla, Mymensingh region(s)"}
for k, nv in TR.items():
    for v in values(k, "region_scope", pat="[ঀ-৿]"):
        cor(k, "region_scope", v, "replace", f"region_scope is the English controlled summary; Bangla text '{v}' translated (review A4-03)", nv)
SPLIT = {"BINADHAN14": "বিনা ধান-১৪ বোরো মৌসুমে চাষাবাদযোগ্য", "BRRI_DHAN65": "ব্রিধান ৬৫ বোনা আউশ মৌসুমে চাষাবাদযোগ্য",
         "BRRI_DHAN66": "ব্রিধান ৬৬ রোপা আমন মৌসুমে চাষাবাদযোগ্য", "BRRI_DHAN67": "ব্রিধান ৬৭ বোরো মৌসুমে চাষাবাদযোগ্য",
         "BRRI_DHAN68": "ব্রিধান ৬৮ বোরো মৌসুমে চাষাবাদযোগ্য", "BRRI_DHAN69": "ব্রিধান ৬৯ বোরো মৌসুমে চাষাবাদযোগ্য",
         "BRRI_DHAN63": "ব্রি ধান-৬৩ বোরো মৌসুমে সারা দেশে চাষাবাদযোগ্য", "BRRI_DHAN64": "ব্রি ধান-৬৪ বোরো মৌসুমে সারা দেশে চাষাবাদযোগ্য"}
for k, nv in SPLIT.items():
    for v in values(k, "recommended_region", src=r"G[A]?Z_"):
        if re.search(r"(ধান[\s-]*[০-৯]+).*(ধান[\s-]*[০-৯]+)", v):
            cor(k, "recommended_region", v, "replace", f"the gazette cell covers several varieties ('{v}'); only the clause about this "
                "variety is kept (review A4-11)", nv)
ev("BINADHAN14", "breeding_line", "RM(1)-200(C)-1-10", "NSB_76_82", "NSB minutes 76-82", "1_primary_legal",
   "02_raw/sca/nsb_minutes_076-082.pdf", 32, "NSB 80, agenda 13, decision", "read on the page image (review A4-05 crop "
   "nsb_minutes_076-082_p32.png)")
for v in values("BINADHAN14", "pedigree", pat="carbon ion"):
    cor("BINADHAN14", "pedigree", v, "replace", "the IAEA record is a sentence with trait claims; the pedigree it states is kept "
        "(review A4-16)", "Ashfal, carbon-ion beam mutant")
cor("BINASHAIL", "approval_reference", "NSB 23th meeting, agenda 5.02", "replace", "the margin of NSB 23 minutes p.30 prints ৫০৩: item "
    "5.03 (ক) (review A4-10, checked on the page image)", "NSB 23rd meeting, agenda 5.03 (ক)")
for k in ("BR22", "BR23"):
    cor(k, "approval_reference", "NSB 24th meeting, agenda 8.02", "replace", "NSB 24 minutes p.48: decision (1) of item 8.02 (গ) approves "
        "the variety; decision (5) is the general gazette instruction (review A4-10)", "NSB 24th meeting, agenda 8.02 (গ), decision (1)")
    for v in values(k, "approval_reference", pat="decision \\(5\\)"):
        cor(k, "approval_reference", v, "drop", "quotes decision (5), the general gazette instruction, not the approval (review A4-10)")
cor("HYB_IAHS100001", "duration_days", "135.140", "replace", "SCA 2016 compendium p.27 prints ১৩৫.১৪০, a typo for 135-140 (review A4-13)",
    "135-140 (printed 135.140)")

pd.DataFrame(COR).to_csv(W / "evidence_corrections_rev2.csv", index=False, encoding="utf-8")
pd.DataFrame(EV).to_csv(W / "evidence_REV2.csv", index=False, encoding="utf-8")
print(f"corrections {len(COR)}, evidence rows {len(EV)}")
