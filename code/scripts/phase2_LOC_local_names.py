"""Local-name rows (local_name_bn left blank unless the source itself prints Bangla) from survey and DNA-fingerprinting sources already in 02_raw (SPIA 2025)."""
import csv
H = ["variety_id", "local_name", "local_name_bn", "region", "source", "local_file", "page_or_locator",
     "source_type", "confidence", "flags", "notes"]
SP = "02_raw/spia_cgspace/SPIA_Bangladesh_Study_2025.pdf"
CB = "02_raw/spia_bd2025/SPIA_BIHS_2024_Varnames.xlsx"
rows = [
 ["", "Miniket", "", "Khulna division (largest cluster, 25 samples)", "SPIA Bangladesh Study 2025", SP, "p.49 (PDF p.61), text below Fig.19/above Fig.20",
  "DNA fingerprinting study", "high", "trade_or_processing_label;not_a_released_variety",
  "SPIA: Miniket is made by heavy milling of medium-slender varieties; self-reported Miniket samples fall in three distinct genetic clusters. No single released variety corresponds."],
 ["RICE-BRRI_DHAN57", "Miniket", "", "", "SPIA Bangladesh Study 2025", SP, "p.50 (PDF p.62), para above Fig.21",
  "DNA fingerprinting study", "medium", "trade_or_processing_label",
  "SPIA: BRRI Dhan 57 'is always misclassified. The common names given for it are Jira and Miniket.' Not one-to-one: other Miniket samples match other clusters."],
 ["RICE-BRRI_DHAN57", "Jira", "", "", "SPIA Bangladesh Study 2025", SP, "p.50 (PDF p.62), para above Fig.21",
  "DNA fingerprinting study", "medium", "",
  "Same sentence as above. 'Jira' is also used for other grain-shape groups (see SPIA Fig.20); not one-to-one."],
 ["", "Haridhan / Horidhan", "", "", "SPIA Bangladesh Study 2025", SP, "p.54 (PDF p.66), Table 18 note",
  "DNA fingerprinting study", "high", "farmer_variety;not_a_released_variety",
  "Predominantly matched Indian accession UPRH265; farmer-made variety, origin disputed."],
 ["", "Paijam", "", "", "SPIA Bangladesh Study 2025", SP, "p.54 (PDF p.66), Table 18 note",
  "DNA fingerprinting study", "medium", "local_variety",
  "20 of 32 samples named Paijam closely matched Patisail. Pajam/Paijam also appears in the SCA 2016 compendium as approved 1966 (to verify in Phase 3)."],
 ["", "Mota", "", "", "SPIA Bangladesh Study 2025", SP, "p.54 (PDF p.66), Table 18 note",
  "DNA fingerprinting study", "medium", "grain_type_label;not_a_released_variety",
  "Most self-reported 'Mota' (bold round grain) matched TK Deep Straw in the 3k genome reference set."],
 ["RICE-BR1", "Chandina", "", "", "SPIA BIHS 2024 SurveyCTO codebook, list 'paddy' code 1", CB, "choices sheet, list_name=paddy, value=1",
  "survey", "high", "", "Label 'Chandina BR-1 (Boro/Aus)'."],
 ["RICE-BR11", "Mukta", "", "", "SPIA BIHS 2024 SurveyCTO codebook, list 'paddy' code 11", CB, "choices sheet, list_name=paddy, value=11",
  "survey", "high", "", "Label 'Mukta BR-11 (Aman)'."],
 ["RICE-BRRI_DHAN89", "(mistaken for BRRI dhan29)", "", "", "SPIA Bangladesh Study 2025", SP, "p.50 (PDF p.62)",
  "DNA fingerprinting study", "high", "misreport_pattern_not_alias",
  "SPIA: many farmers mistake BRRI Dhan 89 for its parent BRRI Dhan 29. Recorded as a misreporting pattern, not an alias."],
 ["", "Jirashail / Banglajira (BADC)", "জিরাশাইল; বাংলাজিরা", "", "NSB 108th meeting minutes, agenda 12",
  "02_raw/sca/nsb_minutes_108.pdf", "p.8, agenda item 12", "official", "high", "landrace_or_market_name;approval_refused",
  "NSB 108 (2022-12-26) refused BADC's proposal to release Jirashail: a traditional/landrace variety that cannot be released in any institution's name; BADC may continue marketing it as Banglajira. Also cited in NSB 75 minutes (p.101) as a grain-type comparator alongside Miniket."],
]
with open("04_working/local_names_LOC.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(H); w.writerows(rows)
print(len(rows))
