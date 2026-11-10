# Changes between versions

## Version 1.3 (10 November 2026)

Version 1.3 follows a third audit of the identity fields and adds attribute, institute and people columns. A stocktake compiled by a team at Bangladesh Agricultural University (draft of 20 September 2026) was compared row by row with the register; it was used only to point to values worth checking, and no value in the register comes from it (`06_validation/bau_comparison.md`). Decisions are in `00_admin/decisions_log.md` under 10 November 2026.

### Errors corrected

Thirty identity values were wrong and are corrected (`04_working/evidence_corrections_rev4.csv`, `06_validation/error_sweep_r3.md`): ten breeding lines, nine Bangla names, five developers, two pedigrees, two seasons and two English names. Among them, the breeding lines of BRRI dhan51 and dhan52 had been OCR-garbled names and are now IR81213-246-237 and IR85260-66-654-Gaz2; BRRI dhan45 is BR5877-21-2-3 and BRRI dhan40 BR5331-93-2-8-3, as the NSB minutes print them; the pedigree of BRRI dhan47 reads IR51511 (the handbook's IR515111 is kept as a recorded disagreement). Breeding lines and pedigree readings are now chosen by the number of independent sources that agree, with the NSB minutes deciding ties (`06_validation/precedence_support_log.csv`). The proposer of a variety at a Board meeting is now read only from the clause next to the variety's own name, which corrects Binadhan-9 and Hira-10. Of 735 source disagreements across ten fields, 7 remain unresolved and are listed in the sweep report.

### Pedigree parents that are not one variety

Parents outside the register now carry a type (`parent_type` in `bgd_pedigree_edges.csv`; `04_working/pedigree_parent_types.csv`). A group name such as 'Basmati (D)', unnamed germplasm and a wild species without an accession are kept as printed and marked as not identifiable; twenty landraces are marked as such; four spelling pairs of one landrace now share one node, and the Binadhan-17 cross is read as C418, Zhong 413 and SH109.

### New columns

The register gains 41 attribute columns read from the official lists, NSB decisions, the BRRI handbook and Rice Profile and BINA's pages: yield potential, duration and plant height by season, grain type and size as printed, aleurone colour, amylose, protein, zinc, iron, glycemic index, germplasm origin and target ecosystem, each group with the file and page it is printed on. Columns that no archived source states (on-farm yield, grain length and breadth in mm, first year of adoption, CGIAR projects) are present and empty. It also gains the national research institute, the breeding division (marked stated or inferred), the proposer as printed in the minutes, and the year the institute released the variety where its own sources state it (`institute_release_year`, 153 varieties; `approval_year` remains the NSB year). Release papers name breeders for 24 varieties (`bgd_variety_people.csv`).

## Version 1.2 (November 2026)

Version 1.2 follows a second review by seven reviewers (an agricultural economist, a development economist, an archivist, a data auditor, a designer, a completeness reviewer and an editor of data publications). Every judgement is recorded, with its evidence, in `00_admin/decisions_log.md` under 10 November 2026; the reviewer corrections are in `04_working/evidence_corrections_rev2.csv` and `04_working/evidence_REV2.csv`, written by `scripts/rev2_corrections.py`.

### Coverage and identity

- **Iratom-38 is now in the register.** The 4th meeting of the Board (18 June 1975, agenda 08.8) allowed seed of the Atomic Energy Commission's 'Iratom' rice to be distributed, the 7th meeting records that Iratom had the Board's approval, and the 14th meeting (30 March 1981) continued Iratom-24 and suspended the cultivation of Iratom-38. Iratom-38 is therefore recorded as approved in 1975 and suspended in 1981, and Iratom-24 now carries the same approval date and reference. The register has 444 varieties again (158 releases, 278 registrations, 8 recommendations before the Board; 279 hybrids and 165 inbreds), and BINA's count of 28 varieties is matched inside the register. Version 1.1 had 443 rows because Bri-shail had been merged into BR4 (see version 1.1 below).
- **BU Aromatic dhan2 is BU dhan2.** The name used by SPIA and HarvestPlus for a 2016 BSMRAU variety with 22 mg/kg zinc is BU dhan2, approved at the 90th meeting; it is kept as an alias, the SPIA flags are attached to BU dhan2, and the unresolved row is gone.
- **Board decisions linked to their varieties.** The decision on 'Loknath-503' (40th meeting) is the hybrid Loknath-505; the unnamed Nipa Trading hybrid of the 67th meeting is Bumper-3; the 'NERICA mutant' that BRRI proposed at the 89th meeting, and the 92nd meeting's instruction to proceed with it as a NERICA pure line, belong to BRRI dhan82, released at the 94th meeting. The generic Iratom approval of the 4th meeting is now one decision row for each of the two Iratom varieties, so the decision table has 579 rows.
- **Names that were never approved.** Mallika Basmati-1 (conditional decision, 67th meeting) and six hybrids deferred at the 101st, 106th and 111th meetings and never registered (Supreme hybrid dhan23, National Agricare hybrid dhan3 and dhan9, Ispahani hybrid dhan11, Mitali hybrid dhan6, Giant Agro hybrid dhan3) are listed in `bgd_rice_not_approved_or_unresolved.csv` with the decision that left them there. The Jirashail row no longer carries the text of an unrelated hybrid decision.
- **Aliases.** BR4 carries Bri-shail and Brishail, the names under which it was approved; Loknath-505 carries Loknath-503.
- **BRRI dhan114.** Its duration (143 days) is taken from the 2024-25 SCA inbred list, whose sixth row prints the name as BRRI dhan113.

### Traits

- **False salt-tolerance tags removed.** BRRI dhan27, 44, 52 and 106 are described by BRRI and the Board as varieties for non-saline (অলবণাক্ত) tidal land; an English gloss had dropped the negation. The glosses are corrected and the tag is gone. For BRRI dhan106 the 2022-23 SCA list prints 'saline tidal areas', which the minutes, the gazette and BRRI contradict; the disagreement is recorded rather than tagged.
- **No stress tag on a SPIA flag alone.** A salt, submergence or drought tag now needs a statement by an official or institute source. Where the SPIA Table 27 flag is the only evidence (Binadhan-7 and BRRI dhan44 for salinity, among others), `feature_evidence` says 'SPIA only' and no tag is given.
- **Stricter resistance tags.** TRIVSA screening codes count only when they are R or HR; a resistance described as moderate or partial gives no tag; and a resistance tag is withheld when any source says the variety is susceptible to the same disease. BRRI dhan28 is no longer tagged blast resistant and BR11 no longer carries a blast tag. In all, 19 varieties lost one or more tags. A defect in the rule for English grain descriptions (a control character where a word boundary was meant) had kept 'slender' and 'fine' in English text from counting; with it repaired, five varieties gain the fine-grain tag (Binadhan-10, BRRI dhan28, 48, 80 and 84).

### Status and seed

- **legal_status_2026.** A new column states the legal position in words: active; active, withdrawal proposed 2021 and deferred (19 register varieties); time-limited registration, renewal not recorded; provisional, re-evaluation outcome not recorded; seed multiplication suspended (IR8, IR20); suspended (Iratom-38); recommended before the Board, no later decision. `status_as_of_2026` is kept for compatibility, and the old `status` column, which contradicted it, is no longer published in the register. Legal status says nothing about whether seed is produced or the variety grown.
- **hybrid_seed_source.** Whether a hybrid's commercial seed is imported or produced in Bangladesh is recorded, with the Board meeting that says so, for the 11 hybrids where a decision states it; every other hybrid is 'unknown'. The value is never inferred from the country of origin or the company.

### Coding

- **CGIAR code 1 includes mutants and selections of a CGIAR line.** Iratom-24 (a mutant of IR8) and Binadhan-19 and -21 (mutants of NERICA-10) are now code 1, so that code 1 always has a CGIAR line at depth 0 and code 2 a CGIAR parent or earlier ancestor. BRRI dhan33, coded 3 on one sentence in an IRRI news item, is code 4: its pedigree (BG388/BG367-4) has no CGIAR element. A new column, `cgiar_derivation`, says whether the link is a direct line, a selection, a mutant, a cross with a CGIAR parent, an earlier ancestor or a collaboration.
- **Trial numbers come from the Board's decision.** For yield, duration and the yield criterion the order of sources is now the Board's decision, then the SCA annual list, then the gazette. BRRI dhan107's yield is 8.19 t/ha, as in the 111th meeting and the SCA list, not the 7.00 t/ha printed in the gazette, which is the yield of the check variety; ACI dhan2's is 6.82 t/ha. A new column, `yield_basis`, says whether a yield is a Board trial mean, a list or gazette figure, or an institute's advertised figure, and `yield_source_id` names the source.
- **yield_advantage_pct is renamed yield_criterion_pct.** The figure is the yield advantage over the check that the decision says was met, usually the registration criterion, not a measured gain.
- **Regions.** `region_scope` is now an English summary in every row. A nationwide approval with a named exception is no longer flagged nationwide: BRRI dhan37 and 38 were approved at the 41st meeting for all regions except Khulna and Barishal. Region now follows the approving decision when it names one; Syngenta SJ 201 is recorded for Mymensingh and Jessore, as the four Ministry lists print it. Gazette sentences that cover several varieties are cut to the clause about the variety.
- **Developers and sector.** IR5, IR8 and IR20 are coded to IRRI and Pajam and Purbachi as introductions from Malaysia and China, so BRRI's count by developer is 127, as on its website. Sector now follows the developer's type: BADC hybrid dhan1 (SL-8H) and RU dhan1 are public.
- **Origin country.** IRRI is recorded as 'Philippines (IRRI)' and the correction notes of the 91st meeting are moved to the row notes.
- **Smaller corrections.** Breeding lines of Binadhan-14 (RM(1)-200(C)-1-10) and Binadhan-21 (N10/350/P-5-4); Binadhan-14's pedigree (a carbon-ion mutant of Ashfal); approval references of Binashail (23rd meeting, agenda 5.03) and BR22 and BR23 (24th meeting, agenda 8.02 (গ), decision (1)); a season inferred from a duration printed for another season no longer sets a season flag (GAU dhan3); unit words removed from yields; the compendium's '135.140' days for IAHS 100001 read as 135-140; every published table in Unicode NFC.

### Fish and literature

- **Fish.** Improved rajputi (silver barb) is Barbonymus gonionotus; the BFRI list misprints Systomus sarana, the olive barb. Subarno Rui is recorded under the name the Ministry gave it on 11 April 2022, BFRI Subarno Rui, with the earlier naming of 4 August 2021; the strain is released, not superseded. Fish code 4 means documented parent stocks with no WorldFish germplasm, whether native stock or earlier imports.
- **Publication years.** Thirty-five publications, mostly in Bangladesh Journals Online, carried the year 1970, a placeholder in the bibliographic databases; the year is now blank with a note, in both the publications and the literature tables.

### Checks

- **New integrity checks.** `scripts/qa_checks.py` now also tests the register count, the CGIAR code against pedigree depth, the vocabulary of legal status and region, the agreement of region flags with exceptions, season flags against the season column, unit text in numeric columns, Unicode normalisation, and that no salt tag rests on a non-saline text or a stress tag on a SPIA flag alone. `06_validation/count_reconciliation.md` is now generated by `scripts/phase3_count_reconciliation.py` on every rebuild.

### Corrections after the second review round

A second round of review read the page text, the records and the data against the sources. The corrections it led to are in `04_working/evidence_corrections_rev3.csv` and in the scripts named below; each is logged under 10 November 2026.

- **Approval route of two BRRI hybrids.** BRRI hybrid dhan3 (70th meeting) and dhan4 (72nd meeting) were registered, not released: the minutes release them 'for registration' under agenda items on hybrid registration, as the Ministry's hybrid lists and the SCA compendium record. The gazettes of 2013 to 2015 print both in a table of released varieties, and that reading is kept in the conflicts table. For a hybrid, the route now follows the Board's decision. Releases fall from 160 to 158 and registrations rise from 276 to 278; BRRI hybrid dhan1 (2001) remains the one public hybrid that was released.
- **CGIAR code of BRRI hybrid dhan2 and dhan3.** Both are now code 5. Their parents are BRRI's own male-sterile and restorer lines, whose pedigrees are not published, and SPIA codes both as having an IRRI parent; code 4 requires parents known to contain no CGIAR line.
- **Decision text.** The decision shown for a variety now comes only from its own part of the agenda item. An agenda item can hold several sub-items, and a variety whose own clause carried no 'decision' heading had been shown the decision of another sub-item: BRRI hybrid dhan3, for instance, showed the approval of seed standards for 74 non-notified crops. Bare 'decision:' labels are gone, a hybrid's name must match with its brand word (BADC hybrid dhan3 had been shown Babylon hybrid dhan3's decision), and a decision that runs on into the next agenda heading is cut there. In a check of 30 randomly drawn decisions against the minutes, none came from another sub-item.
- **Kretzschmar et al. (2018).** The supplementary sheet prints, in the rows for BRRI dhan28 and dhan29, the pedigree and year of other varieties; the error is in the source, which prints the same rows in both of its tables. The two rows no longer count as evidence, so the records of the two most widely grown varieties no longer show a spurious disagreement on pedigree and year. The sheet's other years are release years and are kept.
- **Records.** BR4's official Bangla name is বিআর-৪, with Bri-shail as its popular name; Binadhan-17's pedigree is its cross, C418(ZHONG413)2//SH109/(ZHONG413)2, with the Green Super Rice line SAGC-7 as a note; repeated lineage clauses (BR4, BRRI dhan28, IR8) are removed; Iratom-38's suspension is recorded as a suspension of cultivation, and that of IR8 and IR20 as a suspension of seed multiplication; BRRI hybrid dhan6's recommended region follows the 92nd meeting; the legacy status field no longer appears among the disagreements of a record.
- **Coding.** Binadhan-12 is tagged submergence tolerant, as the SCA compendium and BINA state that it survives up to 25 days of full submergence. BRRI dhan44 is no longer flagged nationwide: the 58th meeting released it for the tidal areas of the south. Binadhan-16 stays code 2, on SPIA and Dikitanan et al. (2022), with a note that the depth to the CGIAR line is unknown.
- **Columns.** In `bgd_pedigree_summary.csv` the column `cgiar_derivation` is renamed `breeding_route`, because the register's column of that name has a different vocabulary; for a mutant or selection of a CGIAR line, `nearest_cgiar_ancestor` now names the source line (NERICA-10 for Binadhan-19, IR8 for Iratom-24) rather than the variety itself. The register has a new column, `quality_notes`, which writes the quality flags out as sentences. `bgd_evidence.csv` is now in Unicode NFC like the other tables.
- **References.** The reference list gives full author lists and adds the three BIHS datasets, the SCA annual lists, the Technical Committee minutes, GloMIP, the 2022 renaming of BFRI Subarno Rui, and four studies of modern and hybrid rice in Bangladesh (Hossain, Bose and Mustafi 2006; Kabir et al. 2015; Yamano et al. 2016; Spielman et al. 2017). Every DOI was resolved at doi.org on 9 November 2026.

### Known gaps

Four additions proposed in the first review round are deferred to version 1.3, because each needs new extraction from sources the archive has not yet read, and this version corrects errors only. The register does not yet provide variety-year or region-by-season spell files for merging with household surveys; it has no companion table of seed supply by variety from BADC and SCA reports; it records the registrant of a variety but not, as a separate field, the breeder of record; and it gives the yield stated in a decision or list rather than the measured yields of the variety and its check in the Board's trials.

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

- **Duplicate identity.** Bri-shail (RICE-OLD_BRISHAIL), approved at the 4th meeting of the Board in 1975, is the variety BR4, whose popular name is Brishail; the two rows were merged under RICE-BR4. The register therefore had 443 varieties (159 releases, 276 registrations, 8 recommendations before the Board) instead of 444. RICE-OLD_BRISHAIL is retired, and Bri-shail and Brishail are aliases of BR4. (Recorded here in version 1.2; version 1.1 did not list the merge.)
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
