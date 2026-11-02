# Changes between versions

## Version 1.1.1 (22 October 2026)

A further pass over the web register after the reviews of version 1.1.

- **Decision texts.** Where one agenda item disposed of several crops, the decision shown for a rice variety is now cut to the sentences about that variety. The decision shown for BRRI dhan74 (87th meeting) had been the paragraph about potato varieties in the same item.
- **Fish strains.** The three strains without a CGIAR code now carry one. Subarna rui is coded 4 (national stock only) on the strength of BFRI's published pedigree, which traces the line to Halda, Jamuna and Brahmaputra river rohu; the improved hybrid magur and the improved tilapia are coded 5, because no archived source states their parent stocks.
- **Reference links.** The seven links that had not been checked on the build date (seed legislation on the Seed Certification Agency's server, the BRRI Rice Profile and Raitzer et al. 2015) were checked on 22 October 2026 and are live.
- **Record view.** Each variety's record now shows its parents (linked to their own records where they are register varieties), its breeding method, the number of generations to its nearest CGIAR ancestor, its legal status at February 2026 with the basis for it, every Board decision about it after approval, its other names, and the standardised developer name and type.
- **Methods.** A table of the completeness of each field, by seed type, and a table of the fields on which sources disagree.
- **Surveys.** A section explaining how survey codes are linked to the register, with the match rates for each BIHS round, the MIXTAPE drafts and the SPIA DNA reference sample.

## Version 1.1 (8 October 2026)

Version 1.1 follows an external review of version 1.0 by three reviewers: an applied economist working on technology adoption, a data editor who audited accuracy and reproducibility, and an editor of data publications. The memos are in `06_validation/`. Variety identifiers are unchanged except where noted below.

### Corrections to the register

- **Swapped hybrid records.** The records of Syngenta hybrid dhan 4, 5 and 6 had names, line codes and dates exchanged between rows. They now follow the 86th and 90th NSB meetings: Syngenta hybrid dhan 6 (line CE0915) was registered at the 90th meeting on 9 October 2016, not at the 86th.
- **Name corrected by the Board.** Supreme hybrid dhan14 is now recorded as Heera14, the name the 109th meeting substituted for Heera29. The earlier name is kept as an alias.
- **Line codes.**
  - BADC hybrid dhan6 carries its own line code, MJ0032; one Ministry list misprints it as MJ0031.
  - The two North South hybrids carry NSSL-1 and NSSL-2 rather than the NSSL-3 printed against both in the 2026 Ministry list.
  - BRRI dhan69 no longer carries BRRI dhan67's breeding line (BR7100-R-6-6), which entered from a misaligned row of the 2014-15 SCA list.
  - ACI hybrid dhan12 is recorded under its registered line GA 1702; the 111th minutes printed ACI2019 by mistake, as the 114th minutes record.
- **HIRA hybrid dhan2.**
  - Its line (HS-273) is restored.
  - Its region is recorded cumulatively, as registered at the 53rd meeting and extended at the 59th and 64th.
  - Conditions copied from other varieties in the same agenda item have been removed.
- **Bayer hybrid dhan5.** Its Aman (82nd meeting) and Boro (83rd meeting) registrations are both reflected in its season and region.
- **Meeting references.** These were added for BR26 (29th meeting) and BRRI dhan33 and dhan34 (38th meeting). The meeting at which BR4–BR7 and Iratom-24 were approved is not recorded in the surviving summary of meetings 1–18, and the reference is left blank.
- **Meeting dates.** Each NSB meeting now has one resolved date (`04_working/nsb_meeting_key_resolved.csv`). Eight meetings previously had two competing readings; the basis for each choice is given in `06_validation/identity_fixes_memo.md`.
- **Decision text.** Twenty-four records showed a decision about potato varieties taken in the same agenda item as their own approval. The decision text is now taken only from paragraphs about rice.

### CGIAR coding

- **Ancestry depth.** Code 2 now covers a documented CGIAR parent or any earlier documented ancestor, not only parents and grandparents. The number of generations to the nearest CGIAR ancestor is published as `depth_to_cgiar`, so the earlier, narrower definition can be recovered.
- **Mutant and somaclonal derivatives** take the ancestry of their source variety. BRRI dhan58 and dhan88 and Binadhan-18 and -25, all derived from BRRI dhan29, therefore move from code 4 to code 2.
- **Other recodes** follow documented pedigrees and are listed with their evidence in `06_validation/cgiar_recode_memo.md`.

### Traits

The trait rules were tightened:
- A negative statement is no longer recorded as the trait.
- Non-saline land is not read as salinity tolerance, and waterlogging is not read as submergence tolerance.
- Grains described as medium slender are no longer recorded as fine grain.
- "Short duration" is not recorded where the stated duration exceeds 145 days (Boro), 120 days (Aman) or 110 days (Aus).
- Zinc enrichment requires an official statement, a stated zinc content of at least 19 mg/kg, or a HarvestPlus flag.

A new field, `trait_text_available`, records whether any trait description was found.

### New tables and columns

- `bgd_variety_crosswalk.csv`: survey and DNA reference codes matched to register identifiers.
- `bgd_pedigree_edges.csv` and `bgd_pedigree_summary.csv`: parent–child links and depth to the nearest CGIAR ancestor.
- `bgd_variety_events.csv` and `bgd_variety_status.csv`: post-approval decisions and legal status at February 2026.
- Analysis-ready columns in the register: season indicators, numeric duration and yield, ecosystem, establishment method, photoperiod sensitivity, grain class, breeding method, administrative divisions of the recommended region, and a standardised developer name and type.

### Build

- Software versions are pinned in `requirements.txt`.
- An OCR failure now stops the build instead of passing silently.
- The register is rebuilt from a single entry point, `scripts/rebuild_all.sh`.

## Version 1.0 (7 October 2026)

First complete release: 444 rice varieties and 9 improved fish strains.
