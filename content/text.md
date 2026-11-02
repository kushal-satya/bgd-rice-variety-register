<!--
All text on the page lives in this file. Edit freely.

Blocks: each block starts with a marker line  <!-- @block-id -->  and runs to the next marker.
Formatting: **bold**, *italic*, `code`, [link text](https://...), lists starting with "- " or "1. ", headings "### ".
Numbers: write {{placeholder}} and the page fills in the value computed from the data when it loads, so the text stays
correct when the data are rebuilt. The full list of placeholders is in README.md (section "Placeholders").
-->

<!-- @title -->
Bangladesh Rice Variety Register

<!-- @tagline -->
Every rice variety approved for cultivation in Bangladesh since {{year_min}}: the approving decision, the pedigree, the stated traits, the link to CGIAR breeding and the survey codes, each traced to its source document.

<!-- @guide-title -->
How to use this site

<!-- @guide -->
**Figures** shows approvals over time, the CGIAR link of inbred varieties by period, and the traits stated for them. **Register** is the table of all {{n_rice}} varieties: filter it, search it in English or Bangla, open a variety to read its full record, and download the selection as a CSV file. **Surveys** explains how the codes used in household surveys are matched to the register. **Fish** covers improved fish strains and the government acts on fish species. **Methods** describes how the register was built and verified and how complete each field is. **Data and references** gives the citation, the files and the source documents.

Each variety has a permanent address: the page address followed by `#` and the variety identifier, for example `#RICE-BRRI_DHAN29`.

<!-- @lede -->
This register lists the {{n_rice}} rice varieties that the Government of Bangladesh approved for cultivation between {{year_min}} and February {{year_max}}. For each variety it gives the National Seed Board decision that approved it, the developer, the breeding line and pedigree where these were published, the traits stated in the official description, the strength of any documented link to CGIAR breeding, and the survey codes under which the variety appears in the Bangladesh Integrated Household Survey. Every value can be traced to a page of an archived source document.

The record is not equally complete for all varieties. Public institutes publish the pedigree and a trait description for almost every inbred variety they release, whereas private companies registering hybrids rarely publish either, so most statements about hybrids are limited to who registered them, when, and for which season and region. A second part of the register covers improved fish strains and the government acts that regulate fish species.

<!-- @meta-coverage -->
{{n_rice}} rice varieties, of which {{n_inbred}} are inbred and {{n_hybrid}} hybrid, and {{n_public}} were developed by public bodies and {{n_private}} by companies or NGOs; {{n_fish}} improved fish strains.

<!-- @meta-completeness -->
A pedigree is recorded for {{n_pedigree}} of the {{n_rice}} varieties, the exact date of the approving meeting for {{n_dated}}, a gazette notification date for {{n_gazette}}, and a determinate CGIAR link (codes 1 to 4) for {{n_cgiar_known}}.

<!-- @meta-asof -->
The 115th meeting of the National Seed Board, 5 February 2026.

<!-- @meta-version -->
1.1.1, built {{built_long}}. Variety identifiers do not change between versions.

<!-- @meta-unit -->
One officially approved rice variety: a release or registration by the National Seed Board, or one of the 8 varieties recommended for cultivation in 1966–1973, before the Board's first meeting.

<!-- @brief-title -->
Methodology in brief

<!-- @brief -->
1. **Enumerating approvals.** We assembled every release and registration of rice from the National Seed Board's own minutes (meetings 1 to 115), and checked the list against the Seed Certification Agency's annual lists and its 2016 compendium, the Ministry of Agriculture's cumulative hybrid lists, and the release notices printed in the Bangladesh Gazette. A variety enters the register only if one of these documents records its approval.
2. **Archiving and reading the sources.** All {{n_source_files}} source documents were downloaded, stored unchanged and fingerprinted (SHA-256), so that any value can be checked against the exact file it came from. Most minutes are scanned Bangla documents, which we read with optical character recognition. Because OCR misreads digits, no number or date read from a scan was accepted on its own: it entered the register only if it agreed with an independent list of meeting numbers and dates or was confirmed on an image of the page. {{n_ocr_unconfirmed}} OCR readings failed both tests and were discarded.
3. **Recording evidence before assembling the register.** Every reading was stored as a separate evidence row with its file, page and quotation ({{n_evidence}} rows in all). The register is then assembled from these rows by fixed rules. Where sources disagree, the more authoritative source prevails, in the order NSB minutes, gazette, official lists, institute records and CGIAR records, and the competing values are kept in the conflicts table rather than discarded.
4. **Coding the CGIAR link.** Each variety's link to CGIAR breeding is coded from its documented pedigree and from explicit statements in the minutes and institute records, never from resemblance between names. The coding was then cross-checked against CGIAR's own accounts of Bangladeshi varieties (SPIA 2025; Dikitanan et al. 2022; Villanueva et al. 2022; IRRI and HarvestPlus records).
5. **Validating the result.** {{n_qa_checks}} automated integrity checks pass. In two independent audits, randomly drawn values were re-read on the page images: the first found no errors in 205 values and 5 partial matches, the second no errors in 218 values, 4 partial matches and 14 values about which the source says nothing. The partial matches have been corrected. The totals agree with three external counts: SPIA's (2025) list of 139 public and NGO varieties released to 2023, once the 13 register entries outside SPIA’s scope are set aside; BRRI's own count of 127 varieties (117 inbred, 10 hybrid); and the Ministry of Agriculture's list of 270 distinct hybrids to February 2026, to which the register adds 9 hybrids registered at or just before the 115th meeting.

<!-- @fig1-title -->
Approvals by year, {{year_min}}–{{year_max}}

<!-- @fig1-sub -->
Number of rice varieties approved for cultivation in each year, by the sector of the developer and by seed type. Years are those of the approving National Seed Board meeting; varieties recommended before 1974 are dated by the Seed Certification Agency's 2016 compendium.

<!-- @fig1-caption -->
Colour shows whether the developer is a public body (BRRI, BINA, the agricultural universities and BADC) or a seed company or NGO such as BRAC. Hatching marks hybrids, which may come from either sector. The bar for {{year_max}} is drawn lighter because it represents a single meeting, held on 5 February.

<!-- @fig2-title -->
Inbred approvals by CGIAR link

<!-- @fig2-sub -->
Number of inbred varieties approved in each five-year period, divided by the strongest documented link to CGIAR breeding. The last period, marked with an asterisk, runs only to February {{year_max}}.

<!-- @fig2-caption -->
Codes are assigned from documented pedigrees, NSB minutes and institute records, never from similarity of names. Hybrids are left out because most private hybrids have no published pedigree, which would leave their link unknown.

<!-- @fig3-title -->
Stated traits of inbred varieties, by period of approval

<!-- @fig3-sub -->
Number of inbred varieties approved in each decade whose official or institute description states each trait. The figure beneath each decade is the number of inbred varieties approved in it.

<!-- @fig3-caption -->
A trait is recorded when the official or institute description of the variety states it; the register does not test varieties itself. The rules are strict. A tolerance is recorded only when a word such as "tolerant" appears next to the stress it refers to, and a disease resistance only when a word such as "resistant" does. Negative statements ("not tolerant of heat at flowering") are never recorded as the trait. "Fine grain" requires the description to call the grain fine or slender, so grains described as medium slender are excluded. Descriptions became fuller over time, so these counts understate the traits of early varieties. {{n_inbred_untagged}} of the {{n_inbred}} inbred varieties have no recorded trait.

<!-- @register-title -->
Register

<!-- @register-sub -->
Each row is one approved variety. The list can be filtered by sector, developer, seed type, stated trait or CGIAR link, and searched by name, breeding line or pedigree in English or Bangla. Selecting a row opens the full record: the variety's traits, pedigree, gazette notification, CGIAR evidence, related literature, the text of each National Seed Board decision about it, and its source documents. While a record is open, the address bar holds a permanent link to it.

<!-- @surveys-title -->
Linking the register to household surveys

<!-- @surveys-intro -->
Household surveys record the rice variety a farmer grew as a numeric code from a printed list, and the lists differ between surveys. In the Bangladesh Integrated Household Survey (BIHS) code 13 is BR14 in most rounds, and BIHS 2024 inserted the varieties released after 2015 into the middle of the list, so a code that meant one variety in 2015 means another in 2024. The two 2026 drafts of the MIXTAPE questionnaire number their lists differently again. The crosswalk (`bgd_variety_crosswalk.csv`) therefore matches every code on its printed label, never on its number, and gives the register identifier it resolves to. A label that names a brand under which several hybrids are registered (Hira, ACI, Lal Teer) cannot be resolved to one variety; the crosswalk lists every registered member instead. Labels that denote widely grown but never approved varieties (Swarna, Haridhan, Miniket) are kept with their own stable identifiers so that they can still be analysed. Each variety's record on this page lists the codes under which it appears.

<!-- @surveys-note -->
"One register variety" counts codes whose label matches exactly one approved variety by name, normalised spelling or recorded alias. "Residual category" is a code such as "Other" or "Do not know". Matches that rest on a single judgement are marked low confidence in the file and are listed in `06_validation/crosswalk_report.md`.

<!-- @compl-title -->
Completeness of the record

<!-- @compl-sub -->
Share of varieties for which each field holds a value, by seed type. A blank field means the sources do not state the value; it never means zero or no. The right-hand table shows the fields on which the sources disagree and the usual form the disagreement takes; the register keeps the value from the most authoritative source and every alternative in `bgd_conflicts.csv`.

<!-- @fish-title -->
Fish: improved strains and government control

<!-- @fish-intro -->
Bangladesh regulates fish and shrimp at the level of the **species**, not the **strain**. The Ministry of Fisheries and Livestock (MoFL) and the Department of Fisheries (DoF) decide which species hatcheries may produce (Fish Hatchery Rules 2011) and which may be imported (Fish Quarantine Rules 2024), and they ban species by gazette notification. Only one new species has been approved in this way: whiteleg shrimp (vannamei), piloted from 2019 and approved for commercial farming on 29 March 2023.

Nothing comparable to the National Seed Board exists for improved strains. There is no statutory register of strains, no mandatory trial and no formal release decision. The Bangladesh Fisheries Research Institute (BFRI) lists technologies approved by its own Technology Validation Committee, and one strain, Subarna rui, has been named by ministry notification (2021). The Fish Hatchery Act 2010 (s. 6(2)) requires the approval of the Director General of Fisheries before a hybrid is released, but we found no record of such an approval.

<!-- @fish-strains-sub -->
The release basis records how a strain came into use: by ministerial naming in an MoFL notification (R1), by an announcement of release from BFRI (R2), by a documented WorldFish release of a named generation (R3), or by dissemination alone, without any release act (R4). The CGIAR column records whether the strain was bred by WorldFish (1), was derived from WorldFish germplasm (2), comes from national or wild stock only (4), or has an undocumented origin (5).

<!-- @fish-events-sub -->
Introductions of improved germplasm into Bangladesh and announced future generations. These are kept apart from released strains because they are not releases.

<!-- @fish-acts-sub -->
The register records {{n_fish_acts}} acts of MoFL, DoF and BFRI concerning fish species and strains, grouped here by type. {{n_fish_ornamental}} of them are ornamental species listed in a single schedule of the Fish Quarantine Rules 2024. The full list, with the quoted text and source of each act, is in `bgd_fish_approvals.csv`.

<!-- @methods-title -->
Methods

<!-- @methods -->
**Scope.** The unit of observation is an officially approved rice variety. Approval takes one of three forms: a release (ছাড়করণ) or a registration (নিবন্ধন) by the National Seed Board under the Seeds Ordinance 1977, as amended in 2005, and the Seed Act 2018; or, for 8 varieties, a recommendation for cultivation made between 1966 and 1973, before the Board existed. Coverage runs to the 115th meeting of the Board (5 February 2026). Names that circulate as rice varieties but have no documented approval, such as Jirashail, whose release the Board refused in 2022, are listed in a separate file.

**Definitions.** A *release* is the Board's approval of an inbred variety of a notified crop after multi-location trials of its value for cultivation and use (VCU). A *registration* is its approval of a hybrid on the strength of tests of distinctness, uniformity and stability (DUS) together with the registrant's yield data. For a hybrid, the developer shown is the registrant, which is often the importer of a hybrid bred abroad. The approval date is the date of the approving meeting. Where sources give different dates ({{n_date_conflicts}} varieties), the minutes prevail and the other dates are kept in `bgd_conflicts.csv`. No rice variety has ever been formally withdrawn. The Board suspended seed multiplication of IR8 and IR20 in 1976, and in 2021 it deferred a proposal to withdraw 20 varieties pending further trials; both are recorded in the status history (`bgd_variety_events.csv`). The register is therefore cumulative.

**Sources.** The primary sources are the minutes of the National Seed Board (meetings 1 to 115) and of its Technical Committee. The secondary official sources are the Seed Certification Agency's annual lists (fiscal years 2014-15 to 2025-26) and its 2016 compendium, the Ministry of Agriculture's hybrid lists (editions from 1998 to 2026), and Bangladesh Gazette release notices. These are supplemented by records of BRRI and BINA and by CGIAR publications and databases (SPIA, IRRI, HarvestPlus, WorldFish, ASTI/TRIVSA, GloMIP).

**Extraction and verification.** Scanned Bangla documents were read with Tesseract 5.4 using its Bangla and English models, and text in the legacy SutonnyMJ encoding was converted to Unicode. A number or date read from a scan was admitted only if it agreed with the list of meeting numbers and dates or was confirmed on an image of the page. The page images were read by a vision-language model (Claude, Anthropic) rather than by double entry by human coders; the two audits described above were separate re-readings of random samples. {{n_dated}} varieties carry the exact date of the approving meeting and {{n_gazette}} a gazette notification date.

**Traits.** Traits are recorded from the official and institute descriptions of each variety by keyword rules written in both Bangla and English; the rules are given in the caption to the third figure and in `scripts/feature_tags.py`. Flags from SPIA (2025) count only when marked "yes", and disease and stress ratings from the TRIVSA database only when rated tolerant or resistant. For every trait the register names the column whose text produced it. A separate field, `trait_text_available`, distinguishes a variety whose description states no trait from one for which no description was found.

**CGIAR coding.** Each variety receives the code of its strongest documented link to CGIAR breeding. Code 1 is a CGIAR-bred line released directly in Bangladesh. Code 2 is a variety with a CGIAR line among its documented parents or earlier ancestors. Code 3 is a variety whose only documented CGIAR involvement is collaboration or funding. Code 4 is a variety whose traceable pedigree contains no CGIAR line. Code 5 is a variety whose pedigree is unknown. A parent that is itself a registered variety passes on its own documented CGIAR ancestry, and a mutant or somaclonal derivative takes the ancestry of the variety it was derived from. The number of generations between a variety and its nearest CGIAR ancestor is recorded in `depth_to_cgiar`, so the narrower definition used by SPIA, which counts parents and grandparents only, can be recovered by restricting to a depth of two or less. The parent–child links behind every code are in `bgd_pedigree_edges.csv`.

**Linking to household surveys.** Household surveys record rice varieties by numeric codes whose meaning changes from one survey round to the next. In most BIHS rounds code 13 is BR14, for example, and the two 2026 drafts of the MIXTAPE questionnaire number their lists differently. The crosswalk (`bgd_variety_crosswalk.csv`) therefore matches each code on its printed label, never on its number, and it identifies labels that denote a brand family covering several registered hybrids rather than a single variety.

**Limitations.** Most private hybrids have no published pedigree and little trait description, so their CGIAR link is unknown and their traits largely unrecorded. Weekly issues of the Bangladesh Gazette before 2013 are not available online, so many earlier releases lack a gazette date. Because descriptions became fuller over time, the recorded traits of older varieties are incomplete. The register records what was approved, not what farmers grow; adoption figures are reported only where a source gives them.

**Versions.** Variety identifiers (`variety_id`) are stable across versions. Corrections made between versions are listed in `CHANGELOG.md`.

<!-- @verify-title -->
Verification of values read from scanned documents

<!-- @references-title -->
References

<!-- @references-sub -->
The primary documents and datasets on which the register rests. Links were checked on the build date unless marked otherwise; "archived copy" points to the Internet Archive where the original host is no longer available.

<!-- @data-title -->
Data and citation

<!-- @citation -->
Kumar, K. (2026). *Bangladesh Rice Variety Register, {{year_min}}–{{year_max}}: officially approved rice varieties, with improved fish strains* (Version 1.1.1) [Data set]. Cornell University. Data as of the 115th meeting of the National Seed Board, 5 February 2026.

<!-- @cite-variety -->
To cite a single variety, cite the register and give the variety's identifier, for example `RICE-BRRI_DHAN29`.

<!-- @availability -->
The register and its supporting tables are distributed as UTF-8 CSV files and as a single Excel workbook (`bgd_variety_archive.xlsx`), and every column is documented in `DATA_DICTIONARY.md`. Each file listed below can be downloaded from this page. Every source document is identified in `bgd_sources.csv` by its original address, by an Internet Archive copy where one exists, and by its SHA-256 fingerprint. The archived source documents, and the scripts that rebuild every table from them, are held by the author and are available on request.

<!-- @footer -->
Bangladesh Rice Variety Register, version 1.1.1, built {{built_long}}.
