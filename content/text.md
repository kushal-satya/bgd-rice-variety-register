<!--
All text on the page lives in this file. Edit freely.

Blocks: each block starts with a marker line  <!-- @block-id -->  and runs to the next marker.
Formatting: **bold**, *italic*, `code`, [link text](https://...) or [link text](#view), lists starting with "- " or "1. ",
headings "### ". Numbers: write {{placeholder}} and the page fills in the value computed from the data when it loads, so
the text stays correct when the data are rebuilt. The full list of placeholders is in EDITING.md (section "Placeholders").
-->

<!-- @title -->
Bangladesh Rice Variety Register

<!-- @tagline -->
Every rice variety approved for cultivation in Bangladesh since {{year_min}}: the approving decision, the pedigree, the stated traits, the link to CGIAR breeding and the survey codes, each traced to its source document.

<!-- @guide-title -->
How to use this site

<!-- @guide -->
The [Register](#register) lists all {{n_rice}} varieties, newest first. Filter it, search it in English or Bangla, and select a variety's name to open its full record: identity and approval, pedigree and CGIAR link, traits, the text of every Board decision about it, and its sources. [CGIAR and lineage](#cgiar) shows how CGIAR breeding reached Bangladeshi varieties and lets you trace any variety's ancestors and descendants. [Figures](#figures) shows approvals over time and the traits stated for inbred varieties. [Surveys](#surveys) explains how the variety codes in household surveys are matched to the register. [Fish](#fish) covers improved fish strains and the government acts on fish species. [Methods](#methods) describes how the register was built and verified and how complete each field is, and [Data and citation](#data) gives the files, the citation and the sources.

Each variety has a permanent address: the page address followed by `#` and the variety identifier, for example `#RICE-BRRI_DHAN29`. Its family tree is at `#L-RICE-BRRI_DHAN29`.

<!-- @lede -->
This register lists the {{n_rice}} rice varieties that the Government of Bangladesh approved for cultivation between {{year_min}} and February {{year_max}}. For each variety it gives the National Seed Board decision that approved it, the developer, the breeding line and pedigree where these were published, the traits stated in the official description, the strength of any documented link to CGIAR breeding, and the codes under which the variety appears in household surveys. Every value read from a document can be traced to a page of an archived source; values derived by rule, such as the CGIAR code, are traced to the documents they rest on.

The record is not equally complete for all varieties. Public institutes publish the pedigree and a trait description for almost every inbred variety they release ({{n_pedigree_inbred}} of {{n_inbred}} inbred varieties have a recorded pedigree), whereas companies registering hybrids rarely publish either, so most statements about hybrids are limited to who registered them, when, and for which season and region. A second part of the register covers improved fish strains and the government acts that regulate fish species.

<!-- @meta-coverage -->
{{n_rice}} rice varieties, of which {{n_inbred}} are inbred and {{n_hybrid}} hybrid, and {{n_public}} were developed by public bodies and {{n_private}} by companies or NGOs; {{n_fish}} improved fish strains.

<!-- @meta-completeness -->
A pedigree is recorded for {{n_pedigree}} of the {{n_rice}} varieties, the exact date of the approving meeting for {{n_dated}}, a gazette notification date for {{n_gazette}}, and a known CGIAR link (codes 1 to 4; code 5 means the pedigree is unknown) for {{n_cgiar_known}}.

<!-- @meta-asof -->
The 115th meeting of the National Seed Board, 5 February 2026. Later meetings of the Board are outside this version.

<!-- @meta-version -->
1.2, built {{built_long}}. Variety identifiers do not change between versions.

<!-- @meta-unit -->
One officially approved rice variety: a release or registration by the National Seed Board, or one of the 8 varieties recommended for cultivation in 1966–1973, before the Board's first meeting.

<!-- @brief-title -->
Methodology in brief

<!-- @brief -->
1. **Enumerating approvals.** We assembled every release and registration of rice from the National Seed Board's own minutes (meetings 1 to 115), and checked the list against the Seed Certification Agency's annual lists and its 2016 compendium, the Ministry of Agriculture's cumulative hybrid lists, and the release notices printed in the Bangladesh Gazette. A variety enters the register only if one of these documents records its approval.
2. **Archiving and reading the sources.** All {{n_source_files}} source documents were downloaded, stored unchanged and fingerprinted (SHA-256), so that any value can be checked against the exact file it came from. Most minutes are scanned Bangla documents, which we read with optical character recognition. Because OCR misreads digits, no number or date read from a scan was accepted on its own: it entered the register only if it agreed with an independent list of meeting numbers and dates or was confirmed on an image of the page. {{n_ocr_unconfirmed}} OCR readings failed both tests and were kept out of the register; they remain in the evidence file, marked as unconfirmed.
3. **Recording evidence before assembling the register.** Every reading was stored as a separate evidence row with its file, page and quotation ({{n_evidence}} rows in all). The register is then assembled from these rows by fixed rules. Where sources disagree, the more authoritative source prevails: for dates and decisions the order is NSB minutes, gazette, official lists, institute records and CGIAR records, and for trial figures (yield, duration) the NSB decision comes before the Seed Certification Agency's list and the gazette. The competing values are kept in the conflicts table rather than discarded.
4. **Coding the CGIAR link.** Each variety's link to CGIAR breeding is coded from its documented pedigree and from explicit statements in the minutes and institute records, never from resemblance between names, and the parent–child links behind every code are published. The coding was then cross-checked against CGIAR's own accounts of Bangladeshi varieties (SPIA 2025; Dikitanan et al. 2022; Villanueva et al. 2022; IRRI and HarvestPlus records).
5. **Validating the result.** {{n_qa_checks}} automated integrity checks pass, with a handful of warnings that are documented as accepted exceptions. Three independent audits re-read randomly drawn values on the page images. The first found no value that contradicted its source among 205 checked, and 5 partial matches, all minor spellings of Bangla names. The second found none among 218, 4 partial matches, and 14 default CGIAR codes that no document can confirm. The third, in November 2026, checked 474 values for 42 varieties across every developer group and found 8 outright errors (1.7 per cent; 95 per cent interval 0.7 to 3.3) and 16 further partial matches (5.1 per cent counting both), none of them in approval dates, developers, seasons or durations. The errors were corrected in this version. The totals agree with three external counts: SPIA's (2025) list of 139 public and NGO varieties released to 2023, once the register entries outside SPIA's scope are set aside; BRRI's own count of 127 varieties (117 inbred, 10 hybrid); and the Ministry of Agriculture's list of 270 distinct hybrids to February 2026, to which the register adds 9 hybrids the list omits (7 registered at the 115th meeting itself, one at the 112th and one at the 75th).

<!-- @register-title -->
Register

<!-- @register-sub -->
Each row is one approved variety, newest first. Filter by sector, developer, seed type, stated trait or CGIAR link, or search by name, breeding line or pedigree in English or Bangla. Select a variety's name to open its full record; select it again to close it. While a record is open, the address bar holds a permanent link to it.

<!-- @cgiar-title -->
CGIAR breeding and the lineage of Bangladeshi varieties

<!-- @cgiar-intro -->
Since IR8 was introduced in 1966, much of Bangladesh's rice breeding has built on lines bred at CGIAR centres, above all the International Rice Research Institute (IRRI). The register traces that contribution through the documented pedigree of every approved variety. A variety can be a CGIAR line released directly, it can descend from one through one or more generations of crossing in Bangladesh, its only link can be collaboration or funding, or its traceable pedigree can contain no CGIAR line at all. The figures below show how these links changed over time, which breeding lines have had the most influence, and how often the varieties farmers actually grow carry CGIAR ancestry. The family tree at the bottom traces any variety's ancestors and descendants.

These figures concern inbred varieties unless stated otherwise. Most hybrids are registered by companies that do not publish parent lines, so their CGIAR link is unknown, and counting them would show the growth of hybrid registration rather than any change in breeding.

<!-- @fig4-title -->
How far back the CGIAR line sits, by period of approval

<!-- @fig4-sub -->
Inbred varieties approved in each five-year period, by the number of generations between the variety and its nearest documented CGIAR ancestor. The last period, marked with an asterisk, runs only to February {{year_max}}.

<!-- @fig4-caption -->
Until the end of the 1970s about half of the approved inbred varieties were IRRI lines released directly. In the 1980s and 1990s most were bred in Bangladesh from crosses with an IRRI parent or grandparent, and varieties three or more generations removed from a CGIAR line appear from the 1990s, usually through earlier Bangladeshi varieties. Direct releases of CGIAR lines never stopped: they were again the largest single group in the 2010s. Generations are counted along the documented parent–child links; a mutant or somaclone is counted in the same generation as the variety it was derived from. Binadhan-16, whose CGIAR ancestry is stated without a published pedigree, is shown as having a CGIAR parent. The data table gives the counts.

<!-- @fig6-title -->
CGIAR ancestry of the varieties farmers grow

<!-- @fig6-sub -->
Share of rice plots sown to varieties in each CGIAR category, in the three BIHS rounds and the 2024 round conducted by SPIA, among plots whose variety code was recorded. The number of plots is given under each round.

<!-- @fig6-caption -->
Survey codes are matched to the register through the crosswalk described under [Surveys](#surveys). The 2011–12 round (*) is not comparable with later rounds: its code list had no codes for Swarna, Miniket or local varieties, so those plots fall under the residual code. A brand family is a label such as "Hira" that covers several registered hybrids, so no single CGIAR code applies. "Never approved" covers widely grown names with no approval record, such as Swarna, an Indian release, and Miniket, a trade name. Plot shares weight each reported plot equally; they are not area-weighted and are not national estimates.

<!-- @fig5-title -->
Lines and varieties with the most approved descendants

<!-- @fig5-sub -->
Number of approved varieties descending from each line, split by generation. Select a line to see its family tree.

<!-- @fig5-caption -->
A descendant is counted once, at the shortest number of generations through which it descends. Unlike the generations figure above, a mutant or somaclone counts here as a child of the variety it was derived from. Lines bred at a CGIAR centre are shown in bold with a dot; the list includes approved varieties such as BR10 and BRRI dhan29 that became parents in their turn. Counts include only documented links; varieties whose parents are not published, which include most hybrids, cannot be counted as descendants of anything.

<!-- @lin-title -->
Family tree of a variety

<!-- @lin-sub -->
Choose a variety or breeding line. Its documented ancestors are drawn to the left, generation by generation, and its descendants to the right: approved varieties, and the unapproved breeding lines through which some of them descend. Select any box to move the tree to that variety.

<!-- @lin-caption -->
The tree shows only links documented in a published pedigree, the NSB minutes or an institute record. A breeding line that was never approved in Bangladesh appears with a dashed outline. A dotted link was inferred from a shared cross number (a sister line) or from an extended line designation rather than printed as a parent. Where a generation has more than 18 members, the remainder are counted rather than drawn.

<!-- @fig1-title -->
Approvals by year, {{year_min}}–{{year_max}}

<!-- @fig1-sub -->
Number of rice varieties approved in each year, for public developers (above) and seed companies and NGOs (below), on the same scale. Solid bars are inbred varieties and hatched bars hybrids. Years are those of the approving National Seed Board meeting; varieties recommended before 1974 are dated by the Seed Certification Agency's 2016 compendium.

<!-- @fig1-caption -->
Public developers are BRRI, BINA, the agricultural universities and BADC, together with the five IRRI and foreign varieties introduced before BRRI's first release; the private panel includes seed companies and NGOs such as BRAC. The bar for {{year_max}}, outlined with a dashed line, represents a single meeting, held on 5 February.

<!-- @fig2-title -->
Cumulative number of approved varieties

<!-- @fig2-sub -->
Varieties approved up to the end of each year, by sector and seed type. No rice variety has been formally withdrawn, so the totals only grow; the Board's few suspensions of seed multiplication or cultivation are recorded in each variety's record.

<!-- @fig2-caption -->
The first hybrids were registered in 1998. By 2009 the cumulative number of private hybrids registered had overtaken the number of public inbred varieties released since 1966, and it has stayed ahead since. A count of approved varieties says nothing about the area each is grown on; see [CGIAR and lineage](#cgiar) for shares of farmers' plots.

<!-- @fig3-title -->
Stated traits of inbred varieties, by decade of approval

<!-- @fig3-sub -->
Share of inbred varieties approved in each decade whose official or institute description states each trait. The figure beneath each decade is the number of inbred varieties approved in it; the right-hand column gives the share across all inbred varieties.

<!-- @fig3-caption -->
A trait is recorded when the official or institute description of the variety states it; the register does not test varieties itself. A tolerance is recorded only when a word such as "tolerant" appears next to the stress it refers to, and a disease resistance only when the variety is called resistant (a rating of "moderately resistant" is not enough, and any source calling it susceptible overrules the tag). Negative statements ("not tolerant of heat at flowering", "suited to non-saline land") are never recorded as the trait, and a SPIA flag alone does not create a stress tag. "Fine grain" requires the description to call the grain fine or slender. Descriptions became fuller over time, so most traits of early varieties are understated. The two disease rows behave differently: most bacterial blight and blast tags before 2010 come from TRIVSA screening ratings, which cover varieties only up to 2008, so the fall in those rows after the 2000s reflects the sources, not breeding. Decades marked * are incomplete (1966 onwards; to February 2026). {{n_inbred_untagged}} of the {{n_inbred}} inbred varieties have no recorded trait.

<!-- @surveys-title -->
Linking the register to household surveys

<!-- @surveys-intro -->
Household surveys record the rice variety a farmer grew as a numeric code from a printed list, and the lists differ between surveys. In the Bangladesh Integrated Household Survey (BIHS) code 13 is BR14 in most rounds, and BIHS 2024 inserted the varieties released after 2015 into the middle of the list, so a code that meant one variety in 2015 means another in 2024. The successive drafts of the MIXTAPE questionnaire number their lists differently again. The crosswalk therefore matches every code on its printed label, never on its number, and gives the register identifier it resolves to. Merge on `bgd_variety_crosswalk_long.csv`, which has one row per survey, instrument version, variable and code.

A label that names a brand under which several hybrids are registered (Hira, ACI, Lal Teer) cannot be resolved to one variety; the crosswalk lists every registered member instead. Labels that denote widely grown but never approved varieties (Swarna, Haridhan, Miniket) are kept with their own stable identifiers and described in `bgd_non_register_names.csv`, so that they can still be analysed. Each variety's record lists the codes under which it appears.

<!-- @surveys-note -->
"One register variety" counts codes whose label matches exactly one approved variety by name, normalised spelling or recorded alias. "Residual category" is a code such as "Other" or "Do not know". Matches that rest on a single judgement are marked low confidence in the file.

<!-- @plots-title -->
How many reported plots can be matched

<!-- @plots-sub -->
Counting codes overstates coverage, because a few residual codes such as "Other" account for many plots. This table weights each rice plot report equally. In the earlier BIHS rounds only about half of the plots resolve to a single approved variety; the rest are brand families, never-approved names such as Swarna, or residual codes. Analyses that join survey plots to the register should report the share they could match.

<!-- @compl-title -->
Completeness of the record

<!-- @compl-sub -->
Share of varieties for which each field holds a value, by seed type. A blank field means the sources do not state the value; it never means zero or no. The right-hand table shows the fields on which the sources disagree and the usual form the disagreement takes; the register keeps the value from the most authoritative source and every alternative in `bgd_conflicts.csv`.

<!-- @board-sub -->
This table lists the officials and members who signed the attendance sheets appended to the minutes of NSB meetings {{board_first}} to {{board_last}}: {{n_board_rows}} entries for {{n_board_people}} distinct names. Names, posts and telephone numbers were transcribed from handwriting as written; a digit that could not be read is shown as "?". The table is for internal use and is not included in the public edition of the site.

<!-- @fish-title -->
Fish: improved strains and government control

<!-- @fish-intro -->
Bangladesh regulates fish and shrimp at the level of the **species**, not the **strain**. The Ministry of Fisheries and Livestock (MoFL) and the Department of Fisheries (DoF) decide which species hatcheries may produce (Fish Hatchery Rules 2011) and which may be imported (Fish Quarantine Rules 2024), and they ban species by gazette notification. Only one new species has been approved in this way: whiteleg shrimp (vannamei), whose pilot culture was approved in 2019, first stocked in 2021, and approved for commercial farming on 29 March 2023.

Nothing comparable to the National Seed Board exists for improved strains. There is no statutory register of strains, no mandatory trial and no formal release decision. The Bangladesh Fisheries Research Institute (BFRI) lists technologies approved by its own Technology Validation Committee, and one strain has been named by ministry notification: Subarna rui (4 August 2021), renamed BFRI Subarno Rui by a further notification of 11 April 2022. The Fish Hatchery Act 2010 (s. 6(2)) requires the approval of the Director General of Fisheries before a hybrid is released, but we found no record of such an approval.

<!-- @fish-strains-sub -->
The release basis records how a strain came into use: by ministerial naming in an MoFL notification (R1), by an announcement of release from BFRI (R2), by a documented WorldFish release of a named generation (R3), or by dissemination alone, without any release act (R4). The CGIAR column records whether the strain was bred by WorldFish (1), was derived from WorldFish germplasm (2), comes from documented parent stocks that include no WorldFish germplasm (4), or has parent stocks that no source states (5).

<!-- @fish-events-sub -->
Introductions of improved germplasm into Bangladesh and announced future generations. These are kept apart from released strains because they are not releases.

<!-- @fish-acts-sub -->
The register records {{n_fish_acts}} acts of MoFL, DoF and BFRI concerning fish species and strains, grouped here by type. {{n_fish_ornamental}} of them are ornamental species listed in a single schedule of the Fish Quarantine Rules 2024. The full list, with the quoted text and source of each act, is in `bgd_fish_approvals.csv`.

<!-- @methods-title -->
Methods

<!-- @methods -->
**Scope.** The unit of observation is an officially approved rice variety. Approval takes one of three forms: a release (ছাড়করণ) or a registration (নিবন্ধন) by the National Seed Board under the Seeds Ordinance 1977, as amended in 2005, and the Seed Act 2018; or, for 8 varieties, a recommendation for cultivation made between 1966 and 1973, before the Board existed. Coverage runs to the 115th meeting of the Board (5 February 2026). Names that circulate as rice varieties but have no documented approval, such as Jirashail, whose release the Board refused in 2022, are listed in a separate file with the reason.

**Definitions.** A *release* is the Board's approval of a variety after multi-location trials of its value for cultivation and use (VCU); almost all inbred varieties, and the early public hybrids BRRI hybrid dhan1, 3 and 4, were released. A *registration* is the Board's approval of a hybrid after trials conducted by the Seed Certification Agency against a check variety; the minutes record the yield advantage the hybrid had to show over the check, which is kept as `yield_criterion_pct`. Registrations were often provisional at first, and the Board at times made continued registration of an imported hybrid conditional on producing its seed in Bangladesh from the fourth year. For a hybrid, the developer shown is the registrant, which is often the importer of a hybrid bred abroad. The approval date is the date of the approving meeting. Where sources give different dates ({{n_date_conflicts}} varieties), the minutes prevail and the other dates are kept in `bgd_conflicts.csv`.

**Legal status.** No rice variety has been formally denotified. The Board suspended seed multiplication of IR8 and IR20 in 1976 and the cultivation of Iratom-38 in 1981, and in 2021 it deferred a proposal to withdraw 20 low-yielding varieties pending re-evaluation. These decisions are recorded in `bgd_variety_events.csv`, and each variety's legal status at February 2026 is in `legal_status_2026`. Legal status says nothing about whether seed of a variety is still produced or whether farmers still grow it.

**Sources.** The primary sources are the minutes of the National Seed Board (meetings 1 to 115) and of its Technical Committee. The secondary official sources are the Seed Certification Agency's annual lists (fiscal years 2014-15 to 2025-26) and its 2016 compendium, the Ministry of Agriculture's cumulative hybrid lists (editions of 2016, 2018 and 2026, which together cover registrations from 1998), and Bangladesh Gazette release notices. These are supplemented by records of BRRI and BINA and by CGIAR publications and databases (SPIA, IRRI, HarvestPlus, WorldFish, ASTI/TRIVSA, GloMIP).

**Extraction and verification.** Scanned Bangla documents were read with Tesseract 5.4 using its Bangla and English models, and text in the legacy SutonnyMJ encoding was converted to Unicode. A number or date read from a scan was admitted only if it agreed with the list of meeting numbers and dates or was confirmed on an image of the page. The page images were read by a vision-language model (Claude, Anthropic) rather than by double entry by human coders; the audits described above were separate re-readings of random samples. {{n_dated}} varieties carry the exact date of the approving meeting and {{n_gazette}} a gazette notification date.

**Traits.** Traits are recorded from the official and institute descriptions of each variety by keyword rules written in both Bangla and English; the rules are given in the caption to the trait figure and in `code/scripts/feature_tags.py`. For every trait the register names the source whose text produced it. A separate field, `trait_text_available`, distinguishes a variety whose description states no trait from one for which no description was found.

**CGIAR coding.** Each variety receives the code of its strongest documented link to CGIAR breeding. Code 1 is a CGIAR-bred line released directly in Bangladesh, including a mutant or selection made directly from such a line. Code 2 is a variety with a CGIAR line among its documented parents or earlier ancestors. Code 3 is a variety whose only documented CGIAR involvement is collaboration or funding. Code 4 is a variety whose traceable pedigree contains no CGIAR line. Code 5 is a variety whose pedigree is unknown. A parent that is itself a registered variety passes on its own documented CGIAR ancestry. The number of generations to the nearest CGIAR ancestor is recorded in `depth_to_cgiar`, every ancestor with its nominal genetic share in `bgd_pedigree_ancestors.csv`, and SPIA's own classification of each variety alongside the register's code. Restricting to a depth of two or less approximates SPIA's definition, which counts parents and grandparents, but the two classifications do not agree for every variety: of the 139 varieties SPIA lists, 113 agree, 8 more agree once deeper ancestors are allowed, and the remaining 18 differ for documented reasons, listed in the concordance table. Attribution weights following Raitzer et al. (2015) are computed in `bgd_pedigree_summary.csv`; they reproduce the published weight for BRRI dhan28 (0.25) but give 0.125 for BRRI dhan29 against a published 0.375, because the archive does not document the origin of its parent BG90-2.

**Linking to household surveys.** See [Surveys](#surveys). The crosswalk matches each code on its printed label, never on its number.

**Limitations.** Most private hybrids have no published pedigree and little trait description, so their CGIAR link is unknown and their traits largely unrecorded. Because hybrids are registered in large numbers, shares of CGIAR-linked varieties computed over all approved varieties fall over time for that reason alone; use inbred-only or plot-weighted shares. Weekly issues of the Bangladesh Gazette before 2013 are not available online, so many earlier releases lack a gazette date. Because descriptions became fuller over time, the recorded traits of older varieties are incomplete. The register records what was approved, not what farmers grow; in the earlier BIHS rounds only about half of reported rice plots can be matched to a single approved variety.

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
Kumar, K. (2026). *Bangladesh Rice Variety Register, {{year_min}}–{{year_max}}: officially approved rice varieties, with improved fish strains* (Version 1.2) [Data set]. Cornell University. https://kushal-satya.github.io/bgd-rice-variety-register/. Data as of the 115th meeting of the National Seed Board, 5 February 2026.

<!-- @cite-variety -->
To cite a single variety, cite the register and give the variety's identifier, for example `RICE-BRRI_DHAN29`.

<!-- @availability -->
The register and its supporting tables are distributed as UTF-8 CSV files and as a single Excel workbook (`bgd_variety_archive.xlsx`). Every column is documented in `DATA_DICTIONARY.md`, a machine-readable description of all tables is in `datapackage.json`, and changes between versions are in `CHANGELOG.md`. Each file listed below can be downloaded from this page. The evidence behind every value (`bgd_evidence.csv`) gives the source file, page and quotation for each reading. Every source document is identified in `bgd_sources.csv` and in the source catalogue (`sources/CATALOGUE.csv`), which give its original address, an Internet Archive copy where one exists, and its SHA-256 fingerprint. The scripts that rebuild every table from the archived sources are published in the [code repository](https://github.com/kushal-satya/bgd-rice-variety-register). The archived source documents themselves are being prepared for deposit in a public repository with a persistent identifier; until then they are available from the author.

<!-- @about -->
The data and documentation are released under the Creative Commons Attribution 4.0 International licence (CC BY 4.0), and the code under the MIT licence. Source documents remain the property of their publishers and are listed, not relicensed. Names and posts of officials appear as printed in public government records; telephone numbers and personal e-mail addresses of individuals are removed from every public file.

<!-- @footer -->
Bangladesh Rice Variety Register, version 1.2, built {{built_long}}.
