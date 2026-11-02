# Bangladesh Rice Variety Register: data dictionary

Kushal Kumar, Cornell University. Generated 2026-10-22 by `scripts/write_dictionary.py`.

This dictionary describes every column of every table in the Bangladesh Rice Variety Register and its companion tables on
fish strains, sources and literature. Each table section gives the unit of observation, the number of rows, and for each
column its meaning, its allowed values or units, and its coverage, the share of rows in which the column is not blank.
Coverage and row counts are computed from the released files when this document is built. How each column was derived, and
from which source, is recorded in `04_working/data_dictionary.csv` (column `source_and_derivation`), which also gives a
short label and a data type for every column.

## Conventions

**Identifiers.** Every rice variety has a stable identifier, `variety_id`, of the form `RICE-<key>`, where the key is built
from the official name (for example `RICE-BRRI_DHAN29`, `RICE-BINADHAN7`, `RICE-HYB_ACI1`). The number in the key is the
official series number, not a running count. The identifier is the join key across all tables; display names
(`variety_name`) are generated from it and are not official spellings. Fish strains use `FISH-<key>`. Publications use
`pub_id` (`doi:<DOI>`, or `t:<normalised title>` when there is no DOI). Survey codes in the crosswalk are list positions that
change between survey rounds and must never be used as a join key on their own.

**Lists inside a cell.** A cell that holds several values separates them with a space, a vertical bar and a space (` | `).
Lists of field names, derived multi-valued categories (for example `season_std`, `breeding_method`, `region_divisions`) and
the quality flags use a semicolon (`; ` or `;`). In `bgd_nsb_decisions_full.csv`, sentences matched in the minutes are
separated by ` ‖ `, and in `bgd_publications.csv` per-author affiliations are separated by ` || `. No other structure is
packed into a cell; long-format detail is in the conflicts and evidence tables.

**Blank cells.** A blank cell means that no eligible source states the value. It never means zero, "no" or "none". A blank
`pedigree` means no pedigree has been published, not that the variety has no parents; a blank `feature_tags` together with
`trait_text_available = no` means there is no trait information, not that the variety lacks the traits; and a `cgiar_role`
of 5 means no CGIAR link is documented, not that there was none. Where a column is filled for only some kinds of varieties
(for example ecosystem and grain class, which the hybrid registration records rarely state), its coverage should be read
together with `rice_type` before any comparison between groups.

**Bangla text.** Names, trait statements, decision texts and list cells are kept as printed, in Unicode Bangla, including
Bangla digits, the source's spelling, spacing and hyphenation, and ditto marks (ঐ). Text from legacy Bijoy (SutonnyMJ) text
layers was converted to Unicode, and a misplaced reph introduced by the converter was repaired; nothing else was edited.
English columns ending in `_std`, `_en` or `_class`, the season flags and the numeric minimum and maximum columns are the
analysis-ready versions of these texts.

**Dates and numbers.** Dates are ISO dates (`YYYY-MM-DD`). When only the year is documented the cell holds the year alone
(`YYYY`) and the row is flagged `year_only`; a year must not be read as 1 January. `approval_date` is the date of the National
Seed Board decision, not the gazette date or the date of first cultivation. Columns that copy printed numbers (`duration_days`,
`yield_t_ha`, `yield_advantage_pct`) are text, because a cell may hold a range or several season-specific values; the derived
`_min_` and `_max_` columns hold the numbers. Units are given in the column descriptions: days for duration, tonnes per hectare
for yield, percent for shares, milligrams per kilogram for zinc and iron.

**Choice between sources.** The register is assembled from long-format evidence. A value is eligible only if it came from a
machine-readable text layer or was validated (`key_check`, `visual_check` or `two_source`); unvalidated OCR never enters the
register. Among eligible values the most authoritative source wins, by authority rank (`1_primary_legal` NSB minutes, Gazette,
acts; `2_official_list` SCA and MoA lists; `3_institute_page`; `4_cgiar_record`; `5_peer_reviewed`; `6_secondary`), then by
validation strength and confidence. Some descriptive fields use their own order: English names, popular names and pedigree
detail prefer the developing institute; season, ecosystem and key traits prefer the official lists; for approval dates a full
date beats a year and the earlier date wins a tie; for gazette dates the earliest notification is kept. Every competing version
is kept in `bgd_conflicts.csv`.

**Files.** All tables are UTF-8 CSV files with a byte-order mark, so that spreadsheet programs display Bangla correctly. Read
every column as text (for example `pandas.read_csv(path, dtype=str, keep_default_na=False)`) and convert the numeric columns
explicitly; otherwise codes such as `0` flags and years are silently retyped and blank cells become missing values.

## Tables

| table | unit of observation | rows |
|---|---|---:|
| [bgd_rice_varieties.csv](#bgd_rice_varietiescsv) | One officially approved rice variety | 443 |
| [bgd_nsb_decisions_full.csv](#bgd_nsb_decisions_fullcsv) | One NSB decision on one variety | 578 |
| [bgd_official_list_rows_full.csv](#bgd_official_list_rows_fullcsv) | One printed cell of an official list | 9,539 |
| [bgd_cgiar_sources.csv](#bgd_cgiar_sourcescsv) | One CGIAR-produced source document | 94 |
| [bgd_cgiar_statements.csv](#bgd_cgiar_statementscsv) | One statement by one CGIAR source about one variety and field | 2,637 |
| [bgd_literature.csv](#bgd_literaturecsv) | One variety-publication pair | 3,105 |
| [bgd_publications.csv](#bgd_publicationscsv) | One publication | 1,468 |
| [bgd_variety_people.csv](#bgd_variety_peoplecsv) | One person named for one variety | 150 |
| [bgd_institutions.csv](#bgd_institutionscsv) | One developing institution or division | 14 |
| [bgd_local_names.csv](#bgd_local_namescsv) | One name linked (or explicitly not linked) to a variety | 151 |
| [bgd_fish_strains.csv](#bgd_fish_strainscsv) | One released improved fish strain | 9 |
| [bgd_fish_events.csv](#bgd_fish_eventscsv) | One germplasm transfer, dissemination or planned release | 6 |
| [bgd_fish_approvals.csv](#bgd_fish_approvalscsv) | One government act on a fish or shrimp species, strain or framework | 183 |
| [bgd_conflicts.csv](#bgd_conflictscsv) | One version of one field for one variety from one source | 9,995 |
| [bgd_conflicts_summary.csv](#bgd_conflicts_summarycsv) | One variety and field with more than one version | 562 |
| [bgd_sources.csv](#bgd_sourcescsv) | One archived source file | 354 |
| [bgd_ocr_pages.csv](#bgd_ocr_pagescsv) | One page of an official document | 1,925 |
| [bgd_ocr_audit.csv](#bgd_ocr_auditcsv) | One OCR'd page that supplied values | 166 |
| [bgd_rice_not_approved_or_unresolved.csv](#bgd_rice_not_approved_or_unresolvedcsv) | One rice name with no documented approval | 3 |
| [bgd_variety_crosswalk.csv](#bgd_variety_crosswalkcsv) | One variety code or label in one survey or library | 1,053 |
| [bgd_pedigree_edges.csv](#bgd_pedigree_edgescsv) | One parent-child link | 326 |
| [bgd_pedigree_summary.csv](#bgd_pedigree_summarycsv) | One register variety | 443 |
| [bgd_variety_events.csv](#bgd_variety_eventscsv) | One NSB decision event for one variety | 532 |
| [bgd_variety_status.csv](#bgd_variety_statuscsv) | One variety | 445 |

## bgd_rice_varieties.csv

*Unit of observation:* One officially approved rice variety.

The register of rice varieties approved in Bangladesh: every variety released or registered by the National Seed Board (NSB) from its first meeting in 1974 to meeting 115 (5 February 2026), and the few varieties recommended before the Board existed. Each row gives the variety's names, developer, approval route and NSB decision, gazette notification, pedigree, agronomic traits, documented CGIAR link with its evidence, legal status in 2026, and the main source with quality flags. Values are chosen from long-format evidence by field-specific precedence rules; every competing value is kept in bgd_conflicts.csv. Columns after the source columns are derived in English for analysis (scripts/derive_covariates.py, feature_tags.py) or copied from the pedigree and status tables.

The file has 443 rows and 107 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `variety_id` | Stable identifier of a rice variety in the register and the key for joining every table in the archive. The number inside the identifier is the official series number of the variety, not a running count. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 1.00 |
| `variety_name` | Uniform English display name of the variety, generated from the identifier so that every variety is written the same way (for example 'BRRI dhan29', 'Binadhan-7', 'BRRI hybrid dhan1'). It is intended for display and labelling; the spellings used by the official documents are kept in official_name_en and official_name_bn. | Free text; for private hybrids the registration or trial code is added in parentheses where one is known, e.g. 'Partex hybrid dhan6 (HR-30)'. Unique within the register. | 1.00 |
| `developer_group` | Broad group of the developer, derived from the identifier. It separates the two public institutes from universities, the public seed corporation, private companies and the varieties introduced before BRRI existed. | BRRI; BINA; University; Private or NGO inbred; Private company; BADC (public corporation); Introduction (pre-BRRI); Other. | 1.00 |
| `sector` | Whether the developer is a public body or a private firm or NGO. The sector is independent of rice_type: BRRI and BADC hybrids are public hybrids, and BRAC's inbreds are private inbreds. | public; private. | 1.00 |
| `rice_type` | Whether the variety is an F1 hybrid or an inbred (open-pollinated) variety. Use this column rather than type for analysis. | hybrid; inbred. Never blank. | 1.00 |
| `approval_year` | Calendar year of approval_date, the year of the National Seed Board decision that released or registered the variety (or the year of recommendation for the pre-NSB varieties). It is not the year of gazette notification or of first cultivation. | Four-digit year, 1966-2026. | 1.00 |
| `official_name_en` | English name of the variety as printed by the developing institute or another official source, with the source's own spacing and hyphenation (for example 'BAU dhan 2'). Blank means no English spelling was printed; most such rows are private hybrids registered under a Bangla name. | Free text as printed. | 0.90 |
| `official_name_bn` | Bangla name of the variety as printed in the official record, kept exactly as printed, including Bangla digits and the source's own spacing and hyphens (for example 'বিনা ধান-১০'). | Bangla text (Unicode, NFC as extracted). Never blank in the register. | 1.00 |
| `popular_name` | Popular or farmer name given by an official or institute source (for example চান্দিনা for BR1). Blank means no source states one; other names reported by surveys and markets are in bgd_local_names.csv. | Free text, usually Bangla. | 0.06 |
| `aliases` | Other labels under which the variety appears in the sources: breeding-line labels that are not line codes (such as 'BR11-Sub1'), names used before renaming, trade names and codes printed by other sources. It is a record of labels seen in the sources, not a vetted list of local names. | Labels separated by ' \| ', in order of first appearance. | 0.64 |
| `breeding_line` | Pre-release designation of the line that became the variety (for example 'BR7671-37-2-2-3-7-3', 'IR91820-25BAY2-3-1'); for private hybrids, the company's trial or product code (for example 'Win301'). Blank means no line code was published. | Designation as printed. Where a source prints the code in both Bangla and Latin script the two forms are joined by '\|' without spaces (for example 'বাউ-১৬\|BAU-16'). | 0.70 |
| `pedigree` | Parentage of the variety as printed, usually in Purdy notation ('/' a first-order cross, '//' a second-order cross, 'A*n/B' a backcross), or a statement of derivation such as 'mutant of BRRI dhan29' or 'line collected from IRRI, Philippines'. Blank means no pedigree has been published, which is the case for most private hybrids; it does not mean the variety has no known parents. | Free text as printed. Parsed parent-child links are in bgd_pedigree_edges.csv. | 0.38 |
| `hybrid_parent_female` | Reserved for the female (cytoplasmic male-sterile A) parent of a hybrid. It is empty in the current release: registration records do not publish hybrid parent lines, and where a source prints them they are kept in pedigree. | Empty in every row. | 0.00 |
| `hybrid_parent_male` | Reserved for the male (restorer) parent of a hybrid. It is empty in the current release for the reason given under hybrid_parent_female. | Empty in every row. | 0.00 |
| `type` | Variety type as written by the winning source. Capitalisation is not harmonised and a few rows are blank; rice_type is the cleaned version. | hybrid; inbred; Inbred; inbred (mutant). | 0.98 |
| `developer` | Name of the developing institute or the applicant company as printed by the winning source, in Bangla or English. The same developer is written in many ways (148 spellings); use developer_std for grouping. | Free text as printed. | 1.00 |
| `developer_std` | Canonical English name of the developer or applicant. Bangla names and spelling variants map to one name; legally separate firms of one business group stay separate (ACI Limited, ACI Formulations, ACI Agrolink), and Gazipur Agricultural University is coded under its former name BSMRAU. | Names from the DEVELOPERS table in derive_covariates.py (e.g. BRRI, BINA, BAU, BSMRAU, BADC, BRAC, Supreme Seed Company); a name not in the table falls back to the cleaned original with legal suffixes removed. | 1.00 |
| `developer_type` | Institutional type of the standardised developer. | public research institute (BRRI, BINA); university; public seed agency (BADC); NGO (BRAC and its seed enterprise); foreign public (IRRI); private company. | 1.00 |
| `developer_country_of_origin` | Country from which the seed or germplasm came, as recorded in the register (mostly the import origin of hybrids stated in the NSB minutes). It is never inferred from the nationality of the company. Blank means not stated, which is the usual case for public inbreds. | China; India; Bangladesh; Philippines (IRRI); Vietnam; 'Bangladesh; China'. | 0.65 |
| `developer_division` | Breeding division of the developing institute, where an institute page or the author affiliation of the key paper names it. It is a medium-confidence attribution, not an official statement of which division bred the variety. | Plant Breeding Division, BRRI; Plant Breeding Division, BINA. | 0.06 |
| `origin_country` | Country of origin of the variety or its seed as recorded by the winning source, with any correction the source itself records. developer_country_of_origin is the cleaned version. | Mostly China, India, Bangladesh, Philippines (IRRI); a few cells carry the correction text, e.g. 'China (as corrected by NSB 91; NSB 90 printed ...)'. | 0.65 |
| `origin_statement` | Statements of origin found in the pedigree slot of a source (for example 'origin India', 'imported from China'), kept separately because they describe where seed came from, not parentage. | Statements separated by ' \| '. | 0.19 |
| `trial_codes` | Seed Certification Agency trial entry numbers of a hybrid (for example 'H-101/127'), found in the pedigree or breeding-line slot of a source. They identify the entry in the SCA's VCU trials and are not pedigrees. | Codes separated by ' \| ' (several trial years may be listed). | 0.18 |
| `pedigree_note` | Text found in the pedigree slot that is not a pedigree: 'own development', a trade name, a supplier, or a trait. Kept so that nothing printed is lost. | Notes separated by ' \| '. | 0.04 |
| `breeding_method` | How the variety was developed, read from the pedigree text. Several methods can apply (for example a cross followed by marker-assisted backcrossing). Blank means the pedigree is empty or names a single parent without saying how it was used. | introduction; selection; cross; mutation; somaclonal; biotech; hybrid (CMS 3-line); hybrid (2-line); hybrid (system not stated); joined by '; '. 'introduction' and the hybrid values are exclusive. | 0.96 |
| `release_category` | Legal route by which the variety was approved. Release (ছাড়করণ) applies to inbred varieties and some public hybrids; registration (নিবন্ধন) is the route for hybrids, which since 1998 are registered after VCU trials rather than released. A row is in the register only if this field is filled. | NSB_release; NSB_registration; pre_NSB_recommended (recommended 1966-1973, before the National Seed Board was constituted). | 1.00 |
| `approving_body` | Body that approved the variety, as the sources describe it. For varieties released after 1977 the NSB approves and the Ministry of Agriculture notifies the release in the Gazette. | Mostly 'NSB' or 'NSB (approval); Government/MoA (notification)'; some rows name the Technical Committee meeting that recommended the variety; 'none: recommended before the NSB was constituted (1974)' for pre-NSB varieties. | 1.00 |
| `approval_date` | Date of the National Seed Board meeting that released or registered the variety. For the pre-NSB varieties it is the date or year of the recommendation. An earlier provisional release is in provisional_release_date, and later decisions (extensions, renamings, suspensions) are in bgd_variety_events.csv. This is a decision date, not the gazette date, the date of first sale or the date of first cultivation. | ISO date YYYY-MM-DD; year only (YYYY) when only the year is documented, which affects 12 rows (flag year_only). | 1.00 |
| `approval_reference` | Meeting number and agenda item of the National Seed Board decision behind approval_date. | 'NSB &lt;n&gt;th meeting, agenda &lt;k&gt;' (agenda omitted where the source does not give it). | 0.97 |
| `provisional_release_date` | Date of an earlier provisional release by the NSB, for varieties whose full release came later (BRRI dhan40 and BRRI dhan41). Blank for all other varieties. | ISO date YYYY-MM-DD. | 0.00 |
| `provisional_release_reference` | NSB meeting and agenda item of the provisional release. | 'NSB &lt;n&gt;th meeting, agenda &lt;k&gt;'. | 0.00 |
| `gazette_date` | Date of the earliest Bangladesh Gazette notification of the release that was found in an archived copy of the Gazette. Later notifications of the same variety are listed in conflict_note. Blank means no archived gazette copy was found; see gazette_status for the reason. | ISO date YYYY-MM-DD. | 0.22 |
| `gazette_date_reported` | Gazette notification date as reported in later NSB minutes when no copy of that Gazette issue was found. It is a report of a notification, not a copy of one. | ISO date YYYY-MM-DD. | 0.01 |
| `gazette_status_note` | What the NSB minutes or Seed Wing memos say about the gazetting of the variety when no gazette copy was found (sent for gazetting, not yet published at the next meeting, reported issued between two dates). | Free text, partly Bangla, with memo numbers as printed. | 0.02 |
| `gazette_reference` | Issue, date and pages of the Gazette notification in gazette_date, with the Seed Wing notification number. | Free text, e.g. 'Bangladesh Gazette Extraordinary 2013-12-02, p.10261-10262; MoA Seed Wing ...'. | 0.22 |
| `season` | Growing season or seasons for which the variety was approved, in English labels as given by the winning source. Bangladesh has three rice seasons: Aus (pre-monsoon), Aman (monsoon) and Boro (dry, irrigated). For analysis use season_std or the three season flags, which also read season statements in other columns. | Aus; Aman; T. Aman; Boro; combinations joined by '; '; qualifiers such as '(direct-seeded)'. | 1.00 |
| `season_aus` | 1 when any source in the register names Aus as a season for the variety. When at least one season is known, the seasons not named are 0. Blank only when no season is stated anywhere. | 1; 0; blank (not stated). | 1.00 |
| `season_aman` | As season_aus, for the Aman (monsoon) season, including transplanted Aman (T. Aman). | 1; 0; blank (not stated). | 1.00 |
| `season_boro` | As season_aus, for the Boro (dry, irrigated) season. | 1; 0; blank (not stated). | 1.00 |
| `season_std` | The seasons flagged 1, written in a fixed order. | Lower-case season names joined by '; ' in the order aus; aman; boro. | 1.00 |
| `ecosystem` | Land type or rice ecosystem for which the variety is recommended, as printed. Most entries are Bangla land-elevation classes (উঁচু, মধ্যম উঁচু, নিচু জমি: high, medium-high, low land) rather than rice ecosystems. | Free text, mostly Bangla. | 0.27 |
| `ecosystem_std` | Rice ecosystem stated for the variety. A category is assigned only when a source states it; no ecosystem is inferred from the season (Boro is irrigated in practice, but that inference is left to the analyst). Bangla 'উঁচু জমি' (high land) is a land-elevation class and is not coded as upland. Blank means not stated, which is the usual case for hybrids. | irrigated; rainfed lowland; upland; tidal; deepwater/haor; saline coastal; favourable; joined by '; '. | 0.20 |
| `ecosystem_text_en` | Short English gloss of the ecosystem column, keeping the land-elevation classes, with ecosystem phrases from the region text appended (tidal areas, haor areas, saline areas, flood-prone areas). | Free text, e.g. 'irrigated; high, medium-high and medium-low land'. | 0.28 |
| `establishment` | Crop establishment method stated for the variety: transplanting or direct seeding. Blank means not stated. | transplanted; direct-seeded; both. | 0.13 |
| `photoperiod` | Whether a source states that the variety is photoperiod-sensitive or insensitive. Only explicit statements count; weakly or somewhat sensitive varieties are coded sensitive. Blank when not stated or when sources contradict each other. | sensitive; insensitive. | 0.08 |
| `region_scope` | Region for which the variety was approved, as summarised in English by the extracting agent from the NSB decision or official list. Hybrid registrations name SCA trial regions after their headquarters towns, in the source's spelling (Comilla, Jessore, Rajshahi). | 'nationwide', 'Whole country', or a comma-separated list of regions. | 1.00 |
| `duration_days` | Growth duration from seeding to maturity, in days, as printed. A cell may hold a range, several season-specific values or condition-specific values, so it is text; use duration_min_days and duration_max_days for numbers. | Days; free text such as '140-145', '130-135 (আউশ); 150-155 (বোরো)'. | 0.99 |
| `duration_min_days` | Smallest duration in days among all values in duration_days, including season- and condition-specific values. | Days, 60-220. Blank when duration_days is blank or unreadable. | 0.99 |
| `duration_max_days` | Largest duration in days among all values in duration_days. | Days, 60-220. | 0.99 |
| `duration_by_season` | Season-specific durations, filled only when a value in duration_days carries a season label. | 'season=min-max' pairs joined by '; ', e.g. 'aus=130-135; boro=150-155'. Days. | 0.04 |
| `yield_t_ha` | Yield in tonnes per hectare as printed by the winning source (usually the average yield in trials or the yield the institute advertises). The cell may hold a range or season-specific values, so it is text. | t/ha; free text. | 0.99 |
| `yield_min_t_ha` | Smallest yield among all values in yield_t_ha. | Tonnes per hectare, 1.5-15. | 0.99 |
| `yield_max_t_ha` | Largest yield among all values in yield_t_ha. | Tonnes per hectare, 1.5-15. | 0.99 |
| `yield_by_season` | Season-specific yields, filled only when a value in yield_t_ha carries a season label. | 'season=min-max' pairs joined by '; ', in t/ha. | 0.03 |
| `yield_advantage_pct` | Yield advantage over the check variety, in percent, as stated in the NSB decision. For most hybrid registrations the figure is the registration criterion that the decision says the variety met (for example at least 20 percent over the check), not a measured gain, so it should not be read as an estimate of the yield gain. | Percent; a number, sometimes with a qualifier such as '10 (at 6 of 10 sites)' or '20 (vs BRRI dhan28)'. | 0.40 |
| `check_variety` | Variety used as the check (control) in the VCU trials named in the NSB decision, as printed. | Free text, mostly Bangla, sometimes with the check's yield. | 0.45 |
| `recommended_region` | Region or area for which the variety is recommended, as printed (mostly Bangla). Use region_divisions and region_nationwide for analysis. | Free text, mostly Bangla. | 0.96 |
| `region_divisions` | Administrative divisions (BBS, eight divisions with Mymensingh separate since 2015) covered by the approved or recommended region. For hybrid registrations the regions are SCA trial regions named after towns and are mapped through the town's district, so they should be read as trial-region approvals, not administrative boundaries. Blank when no place is named. | Division names joined by '; ' from Barishal; Chattogram; Dhaka; Khulna; Mymensingh; Rajshahi; Rangpur; Sylhet. | 0.97 |
| `region_nationwide` | 1 when the approval or recommendation covers the whole country; 0 when specific divisions, districts or target areas are named; blank when neither field names a place. | 1; 0; blank (not stated). | 0.99 |
| `release_year_official` | Release year printed in an official variety list (SCA compendium or annual list). It can differ from approval_year by a year because lists sometimes record the season of first cultivation or the year of printing. | Four-digit year. | 0.37 |
| `special_traits_official` | Special characteristics of the variety as printed in official lists and NSB minutes, verbatim (mostly Bangla). | Free text; several sources separated by ' \| '. | 0.37 |
| `identifying_traits_official` | Identifying (distinguishing) characteristics as printed in the official lists, verbatim (mostly Bangla), for example grain shape and colour. | Free text; several sources separated by ' \| '. | 0.42 |
| `quality_traits` | Grain quality values stated in the NSB minutes or institute sources, written as key=value pairs. | Keys: grain_type (as printed, Bangla), amylose_pct (percent), grain_wt_1000_g (grams per 1000 grains), protein_pct (percent), zinc_mg_kg and iron_mg_kg (mg/kg), lb_ratio (length-breadth ratio); pairs joined by '; ', sources by ' \| '. | 0.16 |
| `grain_class` | Grain length and shape class read from grain phrases only, so that plant height ('গাছ লম্বা', tall plant) never counts. A partial value is given when a source states only one dimension. Blank means not stated, which is the usual case for hybrids. | long slender; medium slender; short slender; long bold; medium bold; short bold; slender (length not stated); bold (length not stated); long (shape not stated); medium (shape not stated); short (shape not stated). | 0.42 |
| `stress_tolerance` | Statements of tolerance to abiotic stress or resistance to disease and pests, verbatim (mostly Bangla). | Free text; several sources separated by ' \| '. | 0.11 |
| `dus_result` | Result of the Distinctness, Uniformity and Stability test as described in the NSB minutes (number of years, traits on which the variety differs from the check). | Free text, Bangla and English. | 0.04 |
| `vcu_sites` | Number of sites in the Value for Cultivation and Use trials reported in the NSB decision. | Integer count, occasionally with a qualifier such as '10 (2023-24 re-trial); 6 (2022-23)'. | 0.11 |
| `decision_conditions` | Conditions attached to the NSB decision, verbatim in Bangla: provisional periods, seed import limits, labelling requirements, re-trial requirements. | Free text; several decisions separated by ' \| '. | 0.34 |
| `feature_tags` | Standardised English tags for the main traits of the variety, read from the trait text. The rules are strict: a stress tag needs a tolerance word next to the stress term, a resistance tag a resistance word, a negated clause never produces a tag, and 'short duration' is dropped when the stated duration exceeds 145 (Boro), 120 (Aman) or 110 (Aus) days. A blank cell means no tag was found in the available text; read it together with trait_text_available. | salt tolerant; submergence tolerant; drought tolerant; cold tolerant; heat tolerant; tidal / deepwater / haor; zinc enriched; high protein; aromatic; fine grain; short duration; blast resistant; bacterial blight resistant; lodging resistant; low glycemic index; joined by ' \| '. | 0.38 |
| `feature_evidence` | For each tag in feature_tags, the column or columns whose text produced it, so that every tag can be traced back. | '&lt;tag&gt;: &lt;column&gt;, &lt;column&gt;' entries joined by ' \| '; '(TRIVSA screening)' marks a TRIVSA code and 'stated zinc content &lt;n&gt; mg/kg' a numeric zinc statement. | 0.38 |
| `trait_text_available` | Whether the register holds any trait text for the variety (official trait columns, quality, stress tolerance or key_traits). A blank feature_tags together with 'no' means there is no information, not that the variety lacks the traits. | yes; no. | 1.00 |
| `key_traits` | Summary of the variety's key traits from all sources, in English or Bangla, typically duration, yield and notable tolerances, together with CGIAR screening codes where TRIVSA reports them. | Free text; one entry per source separated by ' \| '. | 0.93 |
| `adoption` | Adoption figures as reported by TRIVSA/ASTI, SPIA or study-area papers, each with its scope, reference period and method stated in the text. Figures from different sources measure different things (national area share by expert opinion, household survey shares in a sample) and are not comparable without reading the scope. | Free text; one entry per source separated by ' \| '. | 0.07 |
| `market_segment` | CGIAR Global Market Intelligence Platform (GloMIP) market segment to which the variety is assigned. A segment groups many varieties and can contradict the variety's own season or ecosystem, so it is not used to derive covariates. | '&lt;segment id&gt; \| &lt;crop&gt; \| &lt;hybrid status&gt; \| &lt;region&gt; \| &lt;use; grain&gt; \| ...' as printed by GloMIP. | 0.03 |
| `product_profile` | GloMIP product profile of the individual variety: recommended planting methods and ecosystems (PTR, DSR, irrigated lowland, rainfed lowland, upland), the varieties it is meant to replace or accompany, and its key strengths. | Free text as printed by GloMIP, ';'-separated attributes. | 0.08 |
| `status` | Cultivation status stated by an institute or official source (for example 'active' on an institute page). It is filled for few varieties; use status_as_of_2026 for the legal status derived from the NSB decisions. | active; unknown; withdrawn (only in bgd_rice_not_approved_or_unresolved.csv). | 0.07 |
| `doi_key_paper` | DOI of the release or description paper, or the main reference, for the variety. Blank means no such paper was found; it does not mean the variety is unpublished. | DOI without the https://doi.org/ prefix; several DOIs separated by ' \| '. | 0.06 |
| `cgiar_role` | Strongest documented link between the variety and CGIAR research, coded 1 to 5. The code describes documented links only: code 5 means no parentage or link is documented, which is the case for nearly all private hybrids, and it must not be read as 'no CGIAR involvement'. | 1 = CGIAR line released directly (or a mutant or selection within one); 2 = CGIAR line as parent or earlier ancestor, traced up to five generations (use depth_to_cgiar &lt;= 2 for the SPIA parent-or-grandparent definition); 3 = CGIAR collaboration or funding only; 4 = pedigree known, no CGIAR element; 5 = unknown. | 1.00 |
| `cgiar_center` | CGIAR centre named in the documented link. Blank for codes 4 and 5. | IRRI; AfricaRice; HarvestPlus. | 0.31 |
| `cgiar_lineage` | Every documented CGIAR link written out, including weaker links than the one coded in cgiar_role (for example 'IRRI grandparent: IR20 via BR10' or 'pedigree known: Iratom-24 x Dular'). | Free text; links separated by ' \| '. | 0.33 |
| `cgiar_evidence` | The quotation or table cell, as condensed by the extracting agent, that supports the CGIAR link coded in cgiar_role. | Free text, often Bangla. | 0.12 |
| `cgiar_evidence_quote` | Exact text of the source behind cgiar_evidence, in the original language, cut to 200 characters. | Free text, up to 200 characters. | 0.12 |
| `cgiar_evidence_source` | Archived file and page from which cgiar_evidence was taken. | '02_raw/&lt;path&gt;, p. &lt;n&gt;'. | 0.12 |
| `cgiar_evidence_url` | Original public address of the document behind cgiar_evidence. Blank when cgiar_evidence is blank. | Absolute URL. | 0.12 |
| `cgiar_spia_flags` | Flags from SPIA's Bangladesh Study 2025, Appendix B Table 27, kept separate from cgiar_role because SPIA's definition (IRRI parents or grandparents) differs from the register's code. | 'spia_direct', 'spia_indirect' or 'spia_none', then ' \| SPIA T27 flags: ' and Y/N values for irri_direct, indirect_ir_parent, inger_entry, in_reference_library, sub1, saline_tolerance, drought_tolerance, harvestplus, followed by the IRRI/INGER designation text as printed. | 0.31 |
| `cgiar_independent` | What CGIAR's own publications and websites say about the variety's origin (Dikitanan et al. 2022, Villanueva et al. 2022, Raitzer et al. 2015, Kretzschmar et al. 2018, CGSpace records, IRRI, HarvestPlus, STRASA, TRIVSA). It is a cross-check and is not used to set cgiar_role on its own. | Free text, '&lt;source&gt;: &lt;statement&gt;' entries separated by ' \| '. | 0.28 |
| `cgiar_source_urls` | Links to every CGIAR-produced source that mentions the row (SPIA, IRRI, TRIVSA/ASTI, GloMIP, HarvestPlus, CGSpace, WorldFish, CGIAR papers). These sources are a cross-check and are not the basis of the approval record. | URLs separated by ' \| '. Europe PMC and Springer supplement addresses are replaced by the article's DOI or landing page. | 0.34 |
| `source_url` | Web address from which the main source file of the row was downloaded. For the rice register this is the file that supplied the approval record (approval_date); for other tables it is the file that supplied the row. | Absolute http(s) URL. Many Government of Bangladesh files are served from an Oracle object-storage address rather than a portal page; that is the address the portal links to. | 1.00 |
| `archived_url` | Address of a copy of the same file in the Internet Archive's Wayback Machine, so that the source can be consulted if the original address changes. Blank means no archived copy was made or found; it does not mean the original is unavailable. | https://web.archive.org/web/&lt;timestamp&gt;/&lt;original URL&gt;. | 0.06 |
| `local_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `source_type` | Authority rank of the source that supplied the row's main date. The rank decides which value wins when sources disagree. | 1_primary_legal (NSB minutes, Bangladesh Gazette notifications, acts and rules); 2_official_list (SCA and MoA variety lists); 3_institute_page (BRRI, BINA, BFRI and university web pages, handbooks and fact sheets); 4_cgiar_record (CGIAR, IRRI, SPIA, HarvestPlus, WorldFish, ASTI/TRIVSA, GloMIP records); 5_peer_reviewed; 6_secondary (preprints, news, grey literature); 7_reviewer_synthesis (a value added by a reviewer with the file and page cited in the notes). | 1.00 |
| `retrieved_at` | Date on which the main source file was downloaded or the bibliographic record was retrieved. | ISO date YYYY-MM-DD. | 1.00 |
| `n_sources` | Number of distinct source documents that supplied at least one usable (eligible) value for the row. It measures how well documented a row is, not how many sources agree. | Count, 1 or more. | 1.00 |
| `validation_summary` | Summary of how the key values of the row were checked, written as field=check (extraction method) and separated by '; '. The fields reported are approval_date, breeding_line, gazette_date and cgiar_role when present. | Checks: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). 'text' means the value came from a machine-readable text layer and needed no check. Methods: html; pdf_text (the PDF's own Unicode text layer); bijoy2unicode (a legacy SutonnyMJ/Bijoy text layer converted to Unicode); api_json; xlsx; ocr (Tesseract 5 OCR of a 300-dpi render); visual_check (transcribed by eye from the page image). | 1.00 |
| `flags` | Machine-readable quality flags for the row, separated by ';'. A flag marks something an analyst should know before using the row; the absence of flags does not certify a value. | year_only (only the year of the date is documented); date_single_source (one source, not cross-checked); has_conflicts:&lt;fields&gt; (sources disagree on a substantive field); &lt;field&gt;_unvalidated_only (the field had only unvalidated OCR values, which never enter the register, so it is blank); unvalidated_values=&lt;n&gt; (number of such values set aside); breeding_line_not_a_code_moved (descriptive text moved out of breeding_line); institute_claim_only (no official evidence); cgiar_role_default_unknown_no_pedigree, cgiar_role_5_pedigree_needs_review, cgiar_role_4_pedigree_documented_no_cgiar_element, cgiar_role_2_via_parent_variety, cgiar_center_missing (how cgiar_role was set); planned_not_released (fish). | 0.99 |
| `conflict_fields` | Substantive fields on which the sources for this row disagree, separated by '; '. Only approval_date, gazette_date, breeding_line, pedigree, release_category, origin_country, release_date, generation and approval_or_release_mechanism are considered substantive. Blank means no substantive disagreement was found among eligible values. | Field names separated by '; '. | 0.59 |
| `conflict_note` | One short note per field on which sources disagree, of the form '&lt;field&gt;: chose &lt;value&gt;; also &lt;other value&gt; (&lt;source_id&gt;)', with notes for different fields separated by ' \| '. It covers every field, including formatting differences, and is a pointer to bgd_conflicts.csv, which holds every version with its file and page. | Free text; notes separated by ' \| '. Later gazette notifications are listed as 'later gazette(s): &lt;dates&gt;'. | 1.00 |
| `notes` | Free-text notes added by the coordinator or reviewers about the row, such as a CGIAR record that was checked and not used. | Free text; blank for most rows. | 0.04 |
| `gazette_status` | Gazette situation of every variety, stated explicitly so that a blank gazette_date can be interpreted. Hybrid registrations are not gazetted, and no weekly Gazette issues before 2013 are online, so a missing gazette date before 2013 is usually a gap in the archive, not evidence that no notification was made. | notified (gazette in archive); notified per NSB minutes (gazette copy not found); notified per NSB minutes (date not stated); sent to Government Press, publication not confirmed; not gazetted (hybrid registrations are not gazetted); not applicable (before the Seeds Ordinance 1977); not yet published (gazettes checked to 1 Oct 2026); not found (dpp.gov.bd holds no weekly gazettes before 2013). | 1.00 |
| `status_as_of_2026` | Legal status of the variety after the last NSB meeting in the archive (meeting 115, 5 February 2026). 'Active' is a legal status under the Seeds Ordinance and says nothing about whether seed is produced or sold. Status is never inferred from elapsed time; no registration is coded as expired. | active; suspended; unknown (no NSB approval on record, a time-limited approval with no recorded renewal, or an approval made conditional with no recorded outcome); cancelled (defined, but no case found). | 1.00 |
| `status_basis` | Plain-English statement of the decision or absence of decisions behind status_as_of_2026, naming the meeting and date. | Free text. | 1.00 |
| `depth_to_cgiar` | Number of generations between the variety and the nearest CGIAR line in its documented pedigree: 0 when the variety is a CGIAR line or a mutant, somaclone or selection of one, 1 when a parent is a CGIAR line, 2 for a grandparent, and so on. Blank means no CGIAR line was found within five generations of the documented pedigree, including the many varieties with no pedigree at all. | Integer 0-5; blank. | 0.30 |
| `nearest_cgiar_ancestor` | Name or designation of the CGIAR line found at depth_to_cgiar (for example 'IR20', 'IR8', 'Oryza rufipogon (IRGC103404)'). A register variety (such as BR6) appears when it is itself a CGIAR line. | Free text as printed in the pedigree. | 0.30 |
| `source_url_status` | Result of the most recent automated check of the address in source_url. A status other than ok does not mean the archived copy is missing: the file itself is kept under 02_raw/. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 1.00 |
| `archived_url_status` | Result of the most recent automated check of the address in archived_url. A status other than ok does not mean the archived copy is missing: the file itself is kept under 02_raw/. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 0.06 |
| `cgiar_evidence_url_status` | Result of the most recent automated check of the address in cgiar_evidence_url. A status other than ok does not mean the archived copy is missing: the file itself is kept under 02_raw/. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 0.12 |
| `doi_key_paper_status` | Result of the automated check of https://doi.org/&lt;DOI&gt; for each DOI in doi_key_paper, in the same order. | ok; blocked_to_bots; dead; unreachable; unchecked; joined by '; '. | 0.06 |

## bgd_nsb_decisions_full.csv

*Unit of observation:* One NSB decision on one variety.

Every decision of the National Seed Board on a rice variety found in the minutes of meetings 1 to 115, with the full verbatim text of the agenda item, the passage and segment that concern the variety, the raw OCR or text layer, and each attribute the decision states (breeding line, origin, DUS and VCU results, yield, duration, quality, conditions, CGIAR mentions) in its own column with a validation code for every number. Verbatim columns are in Bangla as printed. A decision on several varieties appears once per variety.

The file has 578 rows and 90 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `dec_id` | Identifier of one NSB decision on one variety. An agenda item that decides on several varieties produces one row per variety. | Short code assigned during extraction (e.g. 'd001', 'b83r2', 'f5m_061a'); unique, but carries no meaning beyond identity. | 1.00 |
| `variety_id` | Register identifier of the variety the decision concerns. Blank when the decision names a variety that could not be matched to the register (pilot_key 'UNMATCHED'), for example a rejected or non-rice entry. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 0.92 |
| `variety_name` | Uniform display name of the matched variety (see bgd_rice_varieties.csv). Blank when variety_id is blank. | Free text; for private hybrids the registration or trial code is added in parentheses where one is known, e.g. 'Partex hybrid dhan6 (HR-30)'. Unique within the register. | 0.92 |
| `pilot_key` | Key used to match the decision to the register, before the 'RICE-' prefix is added. 'UNMATCHED' marks decisions on names that are not in the register. | Register key, or UNMATCHED, or blank. | 0.99 |
| `variety_name_as_printed` | Name of the variety as written in the minutes, with any breeding line or trade name printed beside it. | Bangla or English as printed. | 1.00 |
| `meeting_no` | Serial number of the National Seed Board meeting. | Integer 1-115. | 1.00 |
| `meeting_date` | Date on which the National Seed Board meeting was held. | ISO date YYYY-MM-DD. | 1.00 |
| `meeting_date_validation` | How the meeting date was checked. | key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). | 1.00 |
| `agenda_item` | Number of the agenda item (আলোচ্যসূচী) under which the decision was taken, as printed. Blank when the minutes do not number the item. | Usually an integer; a few Bangla digits or letters as printed. | 0.98 |
| `agenda_heading_verbatim` | Heading of the agenda item, verbatim, up to 400 characters. | Bangla text as printed (OCR or converted text layer). | 1.00 |
| `decision_type` | Type of decision the Board took on the variety, as classified when the minutes were read. | release; release_provisional; registration_provisional; registration_conditional; registration_full; registration_extension; rename; suspension; condition_change; status_change; denotification_proposed; approval_deferred; re_trial; approval_denied; gazette. | 1.00 |
| `source_id` | Identifier of the minutes document, shared with bgd_sources.csv and bgd_conflicts.csv. | NSB_&lt;meeting range or number&gt; or NSB_R&lt;n&gt; (SCA activity reports that compile minutes). | 1.00 |
| `source_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `pages` | PDF page or pages of source_file on which the agenda item is printed. | Integer or range 'a-b'. | 1.00 |
| `source_url` | Web address from which the main source file of the row was downloaded. For the rice register this is the file that supplied the approval record (approval_date); for other tables it is the file that supplied the row. | Absolute http(s) URL. Many Government of Bangladesh files are served from an Oracle object-storage address rather than a portal page; that is the address the portal links to. | 1.00 |
| `text_source` | Which text the verbatim columns were taken from. | text_layer (Bijoy text layer converted to Unicode; meetings 58-75); ocr (Tesseract OCR of the page image); ocr_columns (OCR words re-assigned to the columns of a ruled two-column table). | 1.00 |
| `anchor_status` | How the decision was located in the minutes text. A '; passage=anchor_paragraph' suffix means the variety passage could not be isolated by name and the paragraph holding the anchor line is given instead. | regex, regex2 (hand-written pattern); alt, alt2 (breeding-line or name variant); token (number token near the expected page); with optional suffixes '; passage=anchor_paragraph' or '; passage_not_isolated'. | 1.00 |
| `n_decisions_in_item` | Number of variety decisions taken under the same agenda item. Values above 1 mean the item text is shared and the variety-specific columns were cut from a multi-variety passage. | Count, 1 or more. | 1.00 |
| `breeding_line` | Breeding line or trial code printed with the variety in the minutes. | As printed. | 0.67 |
| `pedigree_cross` | Pedigree or derivation of the variety as printed in the minutes (for example 'Basmati(D) x BR5'). Origin statements are moved to germplasm_source. A few cells hold a misplaced value (for example 'nationwide') carried over from the reading sheet. | As printed. | 0.10 |
| `pedigree_statements` | Sentences in the variety passage that mention parentage or crossing. | Verbatim sentences matched by keyword, joined by ' ‖ '. Keyword matching can pick up sentences about other matters in the same agenda item, so read them against variety_passage_verbatim. | 0.08 |
| `hybrid_parent_female_A_line` | Female (CMS) parent line of a hybrid where the minutes print it. | As printed. | 0.00 |
| `hybrid_maintainer_B_line` | Maintainer line of a hybrid where the minutes print it; empty in the current release. | As printed. | 0.00 |
| `hybrid_parent_male_R_line` | Restorer (male) parent line of a hybrid where the minutes print it. | As printed. | 0.00 |
| `hybrid_parent_statements` | Sentences that mention hybrid parent lines, their import or local production. | Verbatim sentences matched by keyword, joined by ' ‖ '. Keyword matching can pick up sentences about other matters in the same agenda item, so read them against variety_passage_verbatim. | 0.02 |
| `germplasm_source` | Statement of where the seed or germplasm came from, as printed. | Free text, Bangla or English; equals origin_statements in the current build. | 0.26 |
| `origin_country` | Country of origin of the seed or germplasm read from the minutes, with any correction noted. | Country names in English, sometimes with a correction note. | 0.25 |
| `origin_statements` | Sentences that state the origin of the variety or its seed. | Verbatim sentences matched by keyword, joined by ' ‖ '. Keyword matching can pick up sentences about other matters in the same agenda item, so read them against variety_passage_verbatim. | 0.13 |
| `developer_applicant` | Institute or company that proposed or imported the variety, as listed in the index and, where found, as printed in the passage ('as printed: ...'). | Free text; ' \| as printed: ' separates the index value from the printed one. | 0.90 |
| `season` | Season for which the decision approves the variety, in English. | Aus; Aman; Boro; Rope (transplanted) Aman or Aus; qualifiers as written. | 0.66 |
| `region_scope` | Region for which the decision approves the variety, summarised in English. | 'nationwide' or a list of regions or towns. | 0.73 |
| `region_text` | Sentences of the decision that name the approved area. | Verbatim sentences matched by keyword, joined by ' ‖ '. Keyword matching can pick up sentences about other matters in the same agenda item, so read them against variety_passage_verbatim. | 0.46 |
| `dus_result` | Result of the Distinctness, Uniformity and Stability test as described in the minutes. | Verbatim text. | 0.06 |
| `dus_statements` | Sentences about the DUS test. | Verbatim sentences matched by keyword, joined by ' ‖ '. Keyword matching can pick up sentences about other matters in the same agenda item, so read them against variety_passage_verbatim. | 0.04 |
| `dus_years` | Number of years or seasons of DUS testing. | Integer, sometimes with years in parentheses. | 0.06 |
| `dus_distinct_traits_n` | Number of traits on which the variety was found distinct from the check. | Count. | 0.07 |
| `dus_check_variety` | Variety against which distinctness was tested. | As printed (Bangla). | 0.07 |
| `vcu_statements` | Sentences about the Value for Cultivation and Use trials. | Verbatim sentences matched by keyword, joined by ' ‖ '. Keyword matching can pick up sentences about other matters in the same agenda item, so read them against variety_passage_verbatim. | 0.24 |
| `vcu_regions_n` | Number of regions in which VCU trials were held. | Count. | 0.08 |
| `vcu_sites_n` | Number of VCU trial sites. | Count, occasionally with a qualifier. | 0.08 |
| `vcu_trial_type` | Whether the VCU trials were on research stations, on farms or both. | on-station; on-farm; 'on-station; on-farm'. | 0.19 |
| `check_variety` | Check variety of the VCU trials as printed. | Bangla text as printed. | 0.37 |
| `yield_t_ha` | Yield reported for the variety in the trials described in the decision. | Tonnes per hectare. | 0.30 |
| `yield_advantage_pct` | Yield advantage over the check as stated. For most hybrid registrations this is the registration criterion that the decision says was met (at least 20 or 10 percent over the check), not a measured gain. | Percent, sometimes with a qualifier such as '(at 6 of 10 sites)'. | 0.33 |
| `yield_statements` | Sentences that report yields. | Verbatim sentences matched by keyword, joined by ' ‖ '. Keyword matching can pick up sentences about other matters in the same agenda item, so read them against variety_passage_verbatim. | 0.07 |
| `duration_days` | Growth duration reported in the decision. | Days. | 0.29 |
| `duration_statements` | Sentences that report growth duration. | Verbatim sentences matched by keyword, joined by ' ‖ '. Keyword matching can pick up sentences about other matters in the same agenda item, so read them against variety_passage_verbatim. | 0.07 |
| `special_traits_official` | Special characteristics stated in the decision. | Verbatim text. | 0.10 |
| `identifying_traits_official` | Identifying characteristics stated in the decision; empty in the current release. | Verbatim text. | 0.00 |
| `grain_type` | Grain shape and size as printed (for example চিকন, মাঝারি মোটা). | Bangla as printed. | 0.26 |
| `grain_quality_statements` | Sentences that describe grain quality. | Verbatim sentences matched by keyword, joined by ' ‖ '. Keyword matching can pick up sentences about other matters in the same agenda item, so read them against variety_passage_verbatim. | 0.05 |
| `amylose_pct` | Amylose content of the grain. | Percent; a few values carry '&gt;' as printed. | 0.08 |
| `lb_ratio` | Grain length to breadth ratio. | Ratio. | 0.00 |
| `grain_wt_1000_g` | Weight of 1000 grains. | Grams. | 0.09 |
| `protein_pct` | Protein content of the grain. | Percent. | 0.05 |
| `zinc_mg_kg` | Zinc content of the grain. | Milligrams per kilogram. | 0.02 |
| `iron_mg_kg` | Iron content of the grain, with the Board's comment where it made one. | Milligrams per kilogram; text where brown and polished values or a comment are given. | 0.01 |
| `stress_tolerance` | Tolerance and resistance statements in the decision. | Verbatim text. | 0.09 |
| `tc_recommendation_text` | Text of the NSB Technical Committee recommendation on which the decision rests, verbatim. | Bangla text. | 0.86 |
| `decision_text` | Decision paragraph or paragraphs (সিদ্ধান্ত) of the agenda item that name the variety, verbatim. When no decision paragraph names it, decision paragraphs that are not about another crop are given. | Bangla text; paragraphs separated by blank lines. | 0.70 |
| `decision_conditions` | Conditions attached to the decision, verbatim. | Bangla text. | 0.67 |
| `import_period` | Sentences of the conditions that concern seed import (আমদানি). | Sentences joined by ' ‖ '. | 0.26 |
| `provisional_years` | Length in years of a provisional or time-limited approval. | Years. | 0.01 |
| `label_requirements` | Sentences that set packet or label requirements (প্যাকেট, লেবেল). | Sentences joined by ' ‖ '. | 0.16 |
| `cgiar_mentions` | Sentences that mention IRRI, IR lines, INGER or other CGIAR elements. | Verbatim sentences matched by keyword, joined by ' ‖ '. Keyword matching can pick up sentences about other matters in the same agenda item, so read them against variety_passage_verbatim. | 0.04 |
| `cgiar_lineage` | CGIAR link documented by this decision, written out. | Free text. | 0.09 |
| `cgiar_role` | CGIAR involvement code supported by this decision alone; the register's cgiar_role combines all sources. | 1-5 as in bgd_rice_varieties.csv. | 0.09 |
| `cgiar_center` | CGIAR centre named in the decision. | IRRI; AfricaRice. | 0.07 |
| `cgiar_quote` | Exact words of the minutes that support cgiar_lineage. | Verbatim, mostly Bangla. | 0.09 |
| `val_yield_t_ha` | How the value in yield_t_ha was checked. | Validation of the numeric value in yield_t_ha: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when yield_t_ha is blank. | 0.30 |
| `val_yield_advantage_pct` | How the value in yield_advantage_pct was checked. | Validation of the numeric value in yield_advantage_pct: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when yield_advantage_pct is blank. | 0.33 |
| `val_duration_days` | How the value in duration_days was checked. | Validation of the numeric value in duration_days: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when duration_days is blank. | 0.29 |
| `val_dus_distinct_traits_n` | How the value in dus_distinct_traits_n was checked. | Validation of the numeric value in dus_distinct_traits_n: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when dus_distinct_traits_n is blank. | 0.07 |
| `val_dus_years` | How the value in dus_years was checked. | Validation of the numeric value in dus_years: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when dus_years is blank. | 0.06 |
| `val_vcu_regions_n` | How the value in vcu_regions_n was checked. | Validation of the numeric value in vcu_regions_n: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when vcu_regions_n is blank. | 0.08 |
| `val_vcu_sites_n` | How the value in vcu_sites_n was checked. | Validation of the numeric value in vcu_sites_n: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when vcu_sites_n is blank. | 0.08 |
| `val_amylose_pct` | How the value in amylose_pct was checked. | Validation of the numeric value in amylose_pct: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when amylose_pct is blank. | 0.08 |
| `val_lb_ratio` | How the value in lb_ratio was checked. | Validation of the numeric value in lb_ratio: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when lb_ratio is blank. | 0.00 |
| `val_grain_wt_1000_g` | How the value in grain_wt_1000_g was checked. | Validation of the numeric value in grain_wt_1000_g: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when grain_wt_1000_g is blank. | 0.09 |
| `val_protein_pct` | How the value in protein_pct was checked. | Validation of the numeric value in protein_pct: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when protein_pct is blank. | 0.05 |
| `val_zinc_mg_kg` | How the value in zinc_mg_kg was checked. | Validation of the numeric value in zinc_mg_kg: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when zinc_mg_kg is blank. | 0.02 |
| `val_iron_mg_kg` | How the value in iron_mg_kg was checked. | Validation of the numeric value in iron_mg_kg: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when iron_mg_kg is blank. | 0.01 |
| `val_provisional_years` | How the value in provisional_years was checked. | Validation of the numeric value in provisional_years: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). Blank when provisional_years is blank. | 0.01 |
| `breeding_line_validation` | How the breeding line was checked. | key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). | 0.66 |
| `manual_field_sources` | Fields whose values were entered or corrected by hand, each with the page crop or note that supports it. | '&lt;field&gt;: &lt;note&gt;' entries joined by ' \| '; 'visual:pg_&lt;meeting&gt;_p&lt;page&gt;' names the crop read by eye. | 0.55 |
| `f3m_notes` | Notes written by the reader of the minutes (agent F3M or F5M), in English. | Free text. | 0.54 |
| `variety_passage_verbatim` | The paragraphs of the agenda item that name the variety, verbatim. For a single-variety item of moderate length it is the whole item. | Bangla text; paragraphs separated by blank lines. | 1.00 |
| `variety_segment_verbatim` | In a multi-variety passage, the sentences from the first mention of this variety up to the next sentence that names another variety of the same item. Blank when the segment equals the passage. | Bangla text. | 0.50 |
| `item_text_verbatim` | Full text of the agenda item, cleaned only of line-break noise, page numbers and file-path footers. | Bangla text; paragraphs separated by blank lines. | 1.00 |
| `raw_text` | Unmodified text of the agenda item as it came from the OCR or the unconverted Bijoy text layer, with page markers. Bijoy text appears as Latin-character garble (for example 'Av‡jvP¨m~Px') and is kept so that conversions can be checked. | Text with '[p.&lt;n&gt;]' page markers. | 1.00 |

## bgd_official_list_rows_full.csv

*Unit of observation:* One printed cell of an official list.

Every printed cell of every official rice variety list in the archive (the SCA compendium of 2016, the SCA annual inbred and hybrid lists, the Ministry of Agriculture hybrid lists of 1998-2016, 2018, 2020 and 2026, and the Bangladesh Gazette release notices), one row per cell, with the cell text verbatim, a normalised value where a rule exists, the matched variety and how the cell was read. Wide versions (one row per printed row) are in 03_extracted/tables/.

The file has 9,539 rows and 22 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `list_id` | Identifier of the official list or gazette notice the cell belongs to. | SCA2016_COMP_INBRED, SCA2016_COMP_HYBRID (SCA compendium, imprint 2014, issued 2016); SCA_FY&lt;yyyy-yy&gt;_INBRED and SCA_FY&lt;yyyy-yy&gt;_HYBRID (SCA annual lists); MOA_HYBRID_1998_2016, MOA_HYBRID_2018, MOA_HYBRID_2020, MOA_HYBRID_2026 (Ministry of Agriculture cumulative hybrid lists) and their _SEASON_SUMMARY tables; GZ_&lt;yyyy-mm-dd&gt; (Bangladesh Gazette release notices). | 1.00 |
| `list_title` | Title of the list as printed, with an English note on the edition where needed. | Bangla text as printed. | 1.00 |
| `fy_or_edition` | Edition of the list: the fiscal year, the date to which the list is complete, or the gazette date. | 'FY2025-26', an ISO date, a year range, or '2016 (imprint 2014)'. | 1.00 |
| `source_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `page` | Page of the source file on which the value is printed, counted as the PDF page (1 = first page of the file), not the number printed on the page. | Integer page number, or a range 'a-b' when the item spans pages. Blank for web pages, spreadsheets and API records. | 1.00 |
| `row_no` | Position of the printed row within the list (or within the page for some lists). Row 0 holds title, banner and other metadata cells that belong to no variety. | Integer, 0 or more. | 1.00 |
| `variety_id` | Register identifier of the variety in this printed row. Blank for metadata cells (row 0) and for the rare row whose name could not be matched. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 0.98 |
| `variety_name` | Display name of the matched variety. | Free text; for private hybrids the registration or trial code is added in parentheses where one is known, e.g. 'Partex hybrid dhan6 (HR-30)'. Unique within the register. | 0.98 |
| `column_header_as_printed` | Header of the column the cell belongs to, as printed. | Bangla text as printed. | 1.00 |
| `column_header_en` | English translation of the column header. | Free text. | 1.00 |
| `cell_text_verbatim` | Text of the printed cell, verbatim, including ditto marks (ঐ, 'as above'), Bangla digits and printing errors. | Unicode text as printed. | 1.00 |
| `cell_value_normalised` | Machine-readable form of the cell where a rule exists (meeting number and date, years, numbers). Blank for cells that have no normalised form, such as names and remarks. | For meeting cells 'NSB &lt;n&gt; = YYYY-MM-DD'; otherwise ASCII numbers or ISO dates. | 0.36 |
| `validation` | How the value was checked after extraction. Unvalidated OCR values are kept in the evidence but never enter the register. | key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). | 1.00 |
| `source_url` | Web address from which the main source file of the row was downloaded. For the rice register this is the file that supplied the approval record (approval_date); for other tables it is the file that supplied the row. | Absolute http(s) URL. Many Government of Bangladesh files are served from an Oracle object-storage address rather than a portal page; that is the address the portal links to. | 1.00 |
| `col_index` | Position of the column in the printed table, counted from the left (0 for metadata). | Integer 0-10. | 1.00 |
| `serial_as_printed` | Serial number (ক্রমিক নং) printed at the start of the row. | As printed, often Bangla digits. | 0.92 |
| `column_kind` | Standard meaning of the column, used to map list cells to register fields. | name; serial; crop; developer; origin; season; region; meeting_date; release_year; duration; yield; identifying_traits; special_traits; remarks; institute_banner; meta. | 1.00 |
| `method` | How the cell was read, in words. | visual_check variants (transcribed by eye from page crops) or bijoy2unicode text-layer variants (some checked by eye against crops). | 1.00 |
| `locator` | Path of the page crop used to read the cell, or another locator. | Relative path under 04_working/crops/. | 1.00 |
| `uncertain` | Note on a reading the transcriber could not settle (handwritten digits, stamps, stray marks). A cell with a note here is marked unvalidated. | Free text; blank for nearly all cells. | 0.00 |
| `key_basis` | How the printed row was matched to a register variety. | For example 'lib_keys.make_key / F3L key_of on the name cell', 'exact name match to MoA 2026 row', 'F3H match report'. | 0.98 |
| `notes` | Transcriber's notes on the cell (merged cells, banners carried from an earlier page). | Free text. | 0.12 |

## bgd_cgiar_sources.csv

*Unit of observation:* One CGIAR-produced source document.

The CGIAR-produced documents, datasets and web pages used in the archive (SPIA, IRRI, HarvestPlus, WorldFish, GloMIP, ASTI/TRIVSA, CGSpace records and CGIAR papers), with their centre, addresses, archived file, checksum and the fields they supplied.

The file has 94 rows and 10 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `centre` | CGIAR centre or programme that produced the source. | SPIA (CGIAR); HarvestPlus; WorldFish; AfricaRice; CGIAR GloMIP; IFPRI ASTI; IRRI / ASTI (TRIVSA); IRRI STRASA; CGIAR (CGSpace); IRRI; IRRI (Villanueva et al. 2022); IRRI (Dikitanan et al. 2022); IRRI (Kretzschmar et al. 2018); SPIA (Raitzer et al. 2015); ISPC/SPIA; CGIAR (other). | 1.00 |
| `source_title` | Title of the source document. | Free text. | 1.00 |
| `doi` | DOI of the source when its address contains one. Blank for most sources, which are web pages, spreadsheets and reports without DOIs; it does not mean the source has none. | DOI without prefix. | 0.02 |
| `source_url` | Web address from which the main source file of the row was downloaded. For the rice register this is the file that supplied the approval record (approval_date); for other tables it is the file that supplied the row. | Absolute http(s) URL. Many Government of Bangladesh files are served from an Oracle object-storage address rather than a portal page; that is the address the portal links to. | 1.00 |
| `archived_url` | Address of a copy of the same file in the Internet Archive's Wayback Machine, so that the source can be consulted if the original address changes. Blank means no archived copy was made or found; it does not mean the original is unavailable. | https://web.archive.org/web/&lt;timestamp&gt;/&lt;original URL&gt;. | 0.07 |
| `local_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `sha256` | SHA-256 hash of the archived file, which lets a user verify that the copy in 02_raw/ is the file that was downloaded. | 64 lowercase hexadecimal characters. | 1.00 |
| `n_varieties` | Number of varieties or strains for which the source supplied at least one statement. | Count. | 1.00 |
| `n_statements` | Number of statements (rows of bgd_cgiar_statements.csv) taken from the source. | Count. | 1.00 |
| `fields` | Register fields for which the source supplied values. | Field names joined by '; '. | 1.00 |

## bgd_cgiar_statements.csv

*Unit of observation:* One statement by one CGIAR source about one variety and field.

Each statement that a CGIAR source makes about a rice variety or fish strain: the field, the value, the exact quote or table cell, its location, and how it was read and checked. Only eligible evidence (text methods or validated readings) is included.

The file has 2,637 rows and 14 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `variety_id` | Register identifier of the rice variety, or the fish strain identifier. | RICE-&lt;key&gt; or FISH-&lt;key&gt;. | 1.00 |
| `variety_name` | Display name of the variety (or strain key for fish). | Free text. | 1.00 |
| `centre` | CGIAR centre or programme that produced the source. | SPIA (CGIAR); HarvestPlus; WorldFish; AfricaRice; CGIAR GloMIP; IFPRI ASTI; IRRI / ASTI (TRIVSA); IRRI STRASA; CGIAR (CGSpace); IRRI; IRRI (Villanueva et al. 2022); IRRI (Dikitanan et al. 2022); IRRI (Kretzschmar et al. 2018); SPIA (Raitzer et al. 2015); ISPC/SPIA; CGIAR (other). | 1.00 |
| `source_title` | Title of the source document. | Free text. | 1.00 |
| `field` | Register field to which the statement supplies a value. | A column name of bgd_rice_varieties.csv or bgd_fish_strains.csv, or cgiar_source_url. | 1.00 |
| `value` | Value of the field according to the source, as recorded in the evidence. | Free text. | 1.00 |
| `quote_or_cell` | Exact words or table cell from the source behind the value. | Verbatim text. | 0.96 |
| `page` | Page of the source file on which the value is printed, counted as the PDF page (1 = first page of the file), not the number printed on the page. | Integer page number, or a range 'a-b' when the item spans pages. Blank for web pages, spreadsheets and API records. | 0.43 |
| `locator` | Where on the page or in the file the value was found: a table and row, a sheet and cell, a quoted phrase, or the path of the image crop that was read by eye. | Free text. | 0.99 |
| `method` | How the value was read from the source file. | html; pdf_text (the PDF's own Unicode text layer); bijoy2unicode (a legacy SutonnyMJ/Bijoy text layer converted to Unicode); api_json; xlsx; ocr (Tesseract 5 OCR of a 300-dpi render); visual_check (transcribed by eye from the page image). | 1.00 |
| `validation` | How the value was checked after extraction. Unvalidated OCR values are kept in the evidence but never enter the register. | key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). | 1.00 |
| `source_url` | Web address from which the main source file of the row was downloaded. For the rice register this is the file that supplied the approval record (approval_date); for other tables it is the file that supplied the row. | Absolute http(s) URL. Many Government of Bangladesh files are served from an Oracle object-storage address rather than a portal page; that is the address the portal links to. | 1.00 |
| `archived_url` | Address of a copy of the same file in the Internet Archive's Wayback Machine, so that the source can be consulted if the original address changes. Blank means no archived copy was made or found; it does not mean the original is unavailable. | https://web.archive.org/web/&lt;timestamp&gt;/&lt;original URL&gt;. | 0.67 |
| `local_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |

## bgd_literature.csv

*Unit of observation:* One variety-publication pair.

Publications that name each variety in their title or abstract, found through OpenAlex, Crossref, Europe PMC and CGSpace, with a classification of the publication's type and a flag for the variety's key (release or description) paper. A publication that names several varieties appears once per variety.

The file has 3,105 rows and 21 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `variety_id` | Stable identifier of a rice variety in the register and the key for joining every table in the archive. The number inside the identifier is the official series number of the variety, not a running count. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 1.00 |
| `publication_type` | Type of the publication with respect to the variety, assigned by title rules and then checked by hand for candidate key papers. | release/description paper; breeding/genetics; adoption/impact; CGIAR report; review; other. | 1.00 |
| `is_key_paper` | Whether this publication is the key paper for the variety: the best release or description paper whose title names it, or one chosen by hand. At most a few varieties have one. | yes; no. | 1.00 |
| `title` | Title of the publication. | Free text. | 1.00 |
| `authors` | Authors in publication order. | Names joined by '; '. | 0.99 |
| `year` | Year of publication. | Four-digit year. | 1.00 |
| `venue` | Journal, repository or series. | Free text. | 0.96 |
| `volume_issue_pages` | Volume, issue and page range. | 'vol &lt;v&gt;; issue &lt;i&gt;; pp &lt;a-b&gt;' with parts omitted when absent. | 0.88 |
| `doi` | DOI of the publication, cleaned of URL prefixes and extraction errors. Blank when the work has no DOI in the APIs used. | DOI without the https://doi.org/ prefix. | 0.90 |
| `url` | Landing page of the publication: the publisher page, or https://doi.org/&lt;DOI&gt; when no other address is given or the publisher address is dead. | Absolute URL. | 0.96 |
| `open_access_url` | Address of a free full-text copy, where the APIs report one. | Absolute URL. | 0.77 |
| `source_api` | Bibliographic services that returned the record. | openalex; crossref; europepmc; cgspace; joined by '; '. | 1.00 |
| `match_basis` | Where the variety's name was found in the record. A title match is much more specific than an abstract match; an abstract match often means the variety was only one of several in an experiment. | title; abstract; title (alias); abstract (alias) (matched on an alias rather than the official name). | 1.00 |
| `abstract_snippet` | First 300 characters of the abstract. | Free text. | 0.98 |
| `retrieved_at` | Date on which the main source file was downloaded or the bibliographic record was retrieved. | ISO date YYYY-MM-DD. | 1.00 |
| `pub_id` | Identifier of the publication, the key for joining bgd_publications.csv. | 'doi:&lt;DOI&gt;' when the work has a DOI, otherwise 't:&lt;normalised title&gt;'. | 1.00 |
| `mention_as_written` | The variety name exactly as it appears in the title or abstract. | Free text. | 1.00 |
| `notes` | Reviewer's note on the classification (for example why a candidate is not a release paper). | Free text. | 0.00 |
| `doi_status` | Result of the automated check of https://doi.org/&lt;DOI&gt;. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 0.90 |
| `url_dead` | The original URL when the automated link check found it dead; the url column then holds a working replacement (usually the DOI link) or is blank. Blank when the original link works. | Absolute URL. | 0.04 |
| `open_access_url_dead` | The original open-access URL when the automated link check found it dead; the open_access_url column then holds a working replacement (usually the DOI link) or is blank. Blank when the original link works. | Absolute URL. | 0.05 |

## bgd_publications.csv

*Unit of observation:* One publication.

Full bibliographic records of the publications in bgd_literature.csv, as returned by the APIs (authors, affiliations, ORCID iDs, citations, keywords, funders, licence, open-access status, abstract and repository identifiers).

The file has 1,468 rows and 37 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `pub_id` | Identifier of the publication, the key for joining bgd_publications.csv. | 'doi:&lt;DOI&gt;' when the work has a DOI, otherwise 't:&lt;normalised title&gt;'. | 1.00 |
| `doi` | DOI of the publication, cleaned of URL prefixes and extraction errors. Blank when the work has no DOI in the APIs used. | DOI without the https://doi.org/ prefix. | 0.90 |
| `title` | Title of the publication. | Free text. | 1.00 |
| `authors` | Authors in publication order. | Names joined by '; '. | 0.99 |
| `affiliations` | Institutional affiliation of each author, as returned by the APIs. | '&lt;author&gt;: &lt;institution&gt;' entries joined by ' \|\| '. | 0.74 |
| `orcids` | ORCID iDs of authors, where registered. | '&lt;author&gt;: &lt;ORCID&gt;' entries joined by '; '. | 0.76 |
| `corresponding_authors` | Corresponding authors where the API identifies them. | Names joined by '; '. | 0.19 |
| `year` | Year of publication. | Four-digit year. | 1.00 |
| `venue` | Journal, repository or series. | Free text. | 0.96 |
| `publisher` | Publisher of the venue. | Free text. | 0.70 |
| `volume_issue_pages` | Volume, issue and page range. | 'vol &lt;v&gt;; issue &lt;i&gt;; pp &lt;a-b&gt;' with parts omitted when absent. | 0.89 |
| `type` | Work type as reported by the API that supplied the record; vocabularies differ between APIs and are not harmonised. | e.g. article, journal-article, Journal Article, Preprint, dissertation. | 1.00 |
| `cited_by_count` | Number of citing works reported by OpenAlex on the retrieval date. | Count. | 0.99 |
| `keywords` | Author or indexer keywords. | Terms joined by '; '. | 0.88 |
| `topics` | OpenAlex topic labels. | Labels joined by '; '. | 0.86 |
| `countries` | Countries of the authors' institutions. | ISO 3166 two-letter codes (some full names) joined by '; '. | 0.69 |
| `funders` | Funding bodies named in the record. | Names joined by '; '. | 0.19 |
| `license` | Licence of the work as reported; spellings are not harmonised. | e.g. cc-by, cc-by-nc, a licence URL. | 0.55 |
| `oa_status` | Open-access status as reported by OpenAlex, or the repository's wording for CGSpace. | diamond; gold; hybrid; green; bronze; closed; OA; Open Access; Limited Access. | 0.88 |
| `affiliations_raw` | Full affiliation strings as printed in the record. | '&lt;author&gt;: &lt;string&gt;' entries joined by ' \|\| '. | 0.71 |
| `open_access_url` | Address of a free full-text copy, where the APIs report one. | Absolute URL. | 0.74 |
| `url` | Landing page of the publication: the publisher page, or https://doi.org/&lt;DOI&gt; when no other address is given or the publisher address is dead. | Absolute URL. | 0.97 |
| `abstract` | Full abstract as returned by the API. | Free text. | 0.96 |
| `openalex_id` | OpenAlex work identifier. | https://openalex.org/W&lt;n&gt;. | 0.86 |
| `pmid` | PubMed identifier. | Integer. | 0.07 |
| `pmcid` | PubMed Central identifier. | PMC&lt;n&gt;. | 0.05 |
| `cgspace_handle` | Handle of the record in CGSpace, CGIAR's repository. | 10568/&lt;n&gt;. | 0.03 |
| `cgspace_uuid` | Internal identifier of the CGSpace item. | UUID. | 0.03 |
| `cg_identifier_url` | Alternative address recorded by CGSpace for the item. | Absolute URL. | 0.00 |
| `language` | Language of the work. | ISO 639-1 code (en, de, id, tr). | 0.81 |
| `sources` | Bibliographic services that returned the record. | openalex; crossref; europepmc; cgspace; joined by '; '. | 1.00 |
| `raw_files` | Archived API responses that contain the record. | Paths under 02_raw/literature_api/ joined by '; '. | 1.00 |
| `varieties_linked` | Register varieties linked to the publication in bgd_literature.csv. | variety_id values joined by '; '. | 1.00 |
| `retrieved_at` | Date on which the main source file was downloaded or the bibliographic record was retrieved. | ISO date YYYY-MM-DD. | 1.00 |
| `doi_status` | Result of the automated check of https://doi.org/&lt;DOI&gt;. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 0.90 |
| `url_dead` | The original URL when the automated link check found it dead; the url column then holds a working replacement (usually the DOI link) or is blank. Blank when the original link works. | Absolute URL. | 0.03 |
| `open_access_url_dead` | The original open-access URL when the automated link check found it dead; the open_access_url column then holds a working replacement (usually the DOI link) or is blank. Blank when the original link works. | Absolute URL. | 0.04 |

## bgd_variety_people.csv

*Unit of observation:* One person named for one variety.

Authors of the key papers and breeders named in official or publication sources, with role, affiliation and ORCID as stated, and professional contact details only where the institution's official directory or the paper itself publishes them.

The file has 150 rows and 13 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `variety_id` | Stable identifier of a rice variety in the register and the key for joining every table in the archive. The number inside the identifier is the official series number of the variety, not a running count. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 1.00 |
| `person_name` | Name of the author or breeder as printed in the source. | Free text. | 1.00 |
| `author_position` | Position of the person in the author list of the key paper. | 1 = first author. | 1.00 |
| `role_as_stated` | Role of the person with respect to the variety. | 'author of key paper (&lt;publication type&gt;)', with ' - corresponding author' where applicable; breeder roles from official sources. | 1.00 |
| `affiliation_as_stated` | Affiliation printed for the person in the key paper. | Free text. | 0.64 |
| `orcid` | ORCID iD of the person, where registered. | 0000-0000-0000-0000 form. | 0.24 |
| `source` | Publication or document that names the person. | 'doi:&lt;DOI&gt;' or a URL. | 1.00 |
| `current_position_as_stated` | Current post of the person according to the institution's official staff directory, as printed (often Bangla). | Free text. | 0.24 |
| `professional_email` | Institutional work e-mail from the official directory, or a corresponding-author e-mail printed in a paper. Only professional contacts are recorded. | E-mail address or addresses with their origin in parentheses. | 0.24 |
| `professional_phone` | Office telephone and extension as printed in the official directory. | Free text. | 0.22 |
| `contact_source_url` | Page from which the contact details were taken. | Absolute URL(s) joined by ' \| '. | 0.24 |
| `contact_source_type` | Kind of page that supplied the contact. | 'official institutional directory (brri.gov.bd)', optionally with '; corresponding author ...'. | 0.24 |
| `notes` | How the person was matched to the directory and how the author list was obtained. | Free text. | 0.34 |

## bgd_institutions.csv

*Unit of observation:* One developing institution or division.

Developing institutes and their breeding divisions, with the official website and the public office contact taken from the institution's own contact page.

The file has 14 rows and 9 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `institution` | Name of the developing institution. | Free text with abbreviation. | 1.00 |
| `division` | Division or department, with the Bangla name where printed. | Free text. | 1.00 |
| `official_website` | Official website of the institution. | Absolute URL. | 0.93 |
| `official_public_contact` | Public office contact (division mailbox, office phone) from the institution's own contact page. | Free text. | 0.93 |
| `contact_person_as_listed` | Office holder listed on the contact page (post, and name where printed). | Free text. | 0.93 |
| `source_url` | Web address from which the main source file of the row was downloaded. For the rice register this is the file that supplied the approval record (approval_date); for other tables it is the file that supplied the row. | Absolute http(s) URL. Many Government of Bangladesh files are served from an Oracle object-storage address rather than a portal page; that is the address the portal links to. | 0.93 |
| `local_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 0.93 |
| `retrieved_at` | Date on which the main source file was downloaded or the bibliographic record was retrieved. | ISO date YYYY-MM-DD. | 1.00 |
| `notes` | What the division develops or why it is listed. | Free text. | 0.71 |

## bgd_local_names.csv

*Unit of observation:* One name linked (or explicitly not linked) to a variety.

Popular, survey and market names of rice varieties, each with its source and the kind of source. Market labels such as Miniket and grain-type labels are recorded with flags and are never assigned to a variety without evidence.

The file has 151 rows and 11 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `variety_id` | Register variety the name refers to. Blank when the name belongs to no register variety (for example the market label Miniket); such names are flagged and never forced onto a variety. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 0.97 |
| `local_name` | Popular, survey or market name, in the script used by the source. | Free text. | 1.00 |
| `local_name_bn` | Bangla form of the name when the source prints one; left blank rather than transliterated otherwise. | Bangla text. | 0.54 |
| `region` | Region where the name is used, when the source restricts it. | Free text. | 0.01 |
| `source` | Title of the source that reports the name. | Free text. | 1.00 |
| `local_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `page_or_locator` | Page, table, sheet or choice-list entry in the source. | Free text. | 1.00 |
| `source_type` | Kind of source reporting the name. | official; survey; DNA fingerprinting study; news; other. | 1.00 |
| `confidence` | Confidence that the name refers to the linked variety. | high; medium. | 1.00 |
| `flags` | Warnings about the name. | trade_or_processing_label; not_a_released_variety; farmer_variety; local_variety; grain_type_label; landrace_or_market_name; approval_refused; misreport_pattern_not_alias; joined by ';'. | 0.05 |
| `notes` | How the name was verified (crop read by eye, agreement with another source). | Free text. | 0.58 |

## bgd_fish_strains.csv

*Unit of observation:* One released improved fish strain.

Improved fish strains released in Bangladesh by BFRI or WorldFish, with a uniform name, the basis of release, the government act found (if any), species, generation, CGIAR involvement and sources. Bangladesh has no statutory release system for fish strains, so release_basis records what kind of act stands behind each strain.

The file has 9 rows and 33 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `strain_id` | Stable identifier of the fish strain. | 'FISH-' followed by a key (developer and strain). | 1.00 |
| `strain_name_std` | Uniform English name of the strain. | Free text. | 1.00 |
| `release_basis` | Kind of act behind the release, in words. Bangladesh has no statutory release system for fish strains (06_validation/fish_governance_memo.md), so most strains rest on an institute announcement. | R1 ministerial naming; R2 institute release; R3 CGIAR release; R4 dissemination only. | 1.00 |
| `government_act` | Government instrument found for the strain, or 'none found'. | Free text. | 1.00 |
| `species_common_en` | English common name of the species. | Free text. | 1.00 |
| `species_scientific` | Scientific name, as printed by the source where noted. | Latin binomial. | 0.89 |
| `species_bn` | Bangla name of the species. | Bangla text. | 1.00 |
| `strain_name` | Name of the strain as printed by the main source, often Bangla. | Free text. | 1.00 |
| `developer` | Organisation that developed the strain, as stated. Blank when the source names none. | Free text. | 0.33 |
| `cgiar_role` | Documented CGIAR (WorldFish) involvement in the strain, on the same 1-5 scale as rice. | 1 WorldFish line released directly; 2 CGIAR germplasm as parent stock; 3 collaboration or funding only; 4 no CGIAR element documented; 5 unknown. Blank when no source states it. | 1.00 |
| `cgiar_center` | CGIAR centre named. | WorldFish; WorldFish (formerly ICLARM). | 0.33 |
| `approval_or_release_mechanism` | How the strain was released or made available, beginning with a release-ladder code and followed by the evidence. | R1_ministerial_naming (MoFL notification); R2_institute_release (BFRI announcement or Technology Validation Committee list); R3_cgiar_release (WorldFish-documented release of a named generation); R4_dissemination_only; or 'none yet (R3 pending)'. | 1.00 |
| `releasing_body` | Body that released or declared the strain. | Free text. | 0.89 |
| `release_date` | Date of release, naming or transfer. Blank when no source dates it. | ISO date YYYY-MM-DD, or year only. | 0.33 |
| `generation` | Selection generation of the strain as described by the source. | Free text such as 'G3', 'F4 broodstock used to produce F5 (2017)'. | 0.67 |
| `key_traits` | Performance claims and awards as stated, e.g. percent higher growth than the existing strain. | Free text; entries joined by ' \| '. | 0.67 |
| `distribution_channel` | How seed (spawn, fry, broodstock) reached hatcheries or farmers. | Free text. | 0.67 |
| `status` | Current status as stated by the source (for example BFRI's dissemination categories). | Free text; 'planned_not_yet_released' for announced generations. | 1.00 |
| `source_url` | Web address from which the main source file of the row was downloaded. For the rice register this is the file that supplied the approval record (approval_date); for other tables it is the file that supplied the row. | Absolute http(s) URL. Many Government of Bangladesh files are served from an Oracle object-storage address rather than a portal page; that is the address the portal links to. | 1.00 |
| `archived_url` | Address of a copy of the same file in the Internet Archive's Wayback Machine, so that the source can be consulted if the original address changes. Blank means no archived copy was made or found; it does not mean the original is unavailable. | https://web.archive.org/web/&lt;timestamp&gt;/&lt;original URL&gt;. | 0.89 |
| `local_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `source_type` | Authority rank of the source that supplied the row's main date. The rank decides which value wins when sources disagree. | 1_primary_legal (NSB minutes, Bangladesh Gazette notifications, acts and rules); 2_official_list (SCA and MoA variety lists); 3_institute_page (BRRI, BINA, BFRI and university web pages, handbooks and fact sheets); 4_cgiar_record (CGIAR, IRRI, SPIA, HarvestPlus, WorldFish, ASTI/TRIVSA, GloMIP records); 5_peer_reviewed; 6_secondary (preprints, news, grey literature); 7_reviewer_synthesis (a value added by a reviewer with the file and page cited in the notes). | 1.00 |
| `retrieved_at` | Date on which the main source file was downloaded or the bibliographic record was retrieved. | ISO date YYYY-MM-DD. | 1.00 |
| `n_sources` | Number of distinct source documents that supplied at least one usable (eligible) value for the row. It measures how well documented a row is, not how many sources agree. | Count, 1 or more. | 1.00 |
| `cgiar_source_urls` | Links to every CGIAR-produced source that mentions the row (SPIA, IRRI, TRIVSA/ASTI, GloMIP, HarvestPlus, CGSpace, WorldFish, CGIAR papers). These sources are a cross-check and are not the basis of the approval record. | URLs separated by ' \| '. Europe PMC and Springer supplement addresses are replaced by the article's DOI or landing page. | 0.22 |
| `cgiar_evidence_url` | Original public address of the document behind cgiar_evidence. Blank when cgiar_evidence is blank. | Absolute URL. | 0.11 |
| `validation_summary` | Summary of how the key values of the row were checked, written as field=check (extraction method) and separated by '; '. The fields reported are approval_date, breeding_line, gazette_date and cgiar_role when present. | Checks: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). 'text' means the value came from a machine-readable text layer and needed no check. Methods: html; pdf_text (the PDF's own Unicode text layer); bijoy2unicode (a legacy SutonnyMJ/Bijoy text layer converted to Unicode); api_json; xlsx; ocr (Tesseract 5 OCR of a 300-dpi render); visual_check (transcribed by eye from the page image). | 1.00 |
| `flags` | Machine-readable quality flags for the row, separated by ';'. A flag marks something an analyst should know before using the row; the absence of flags does not certify a value. | year_only (only the year of the date is documented); date_single_source (one source, not cross-checked); has_conflicts:&lt;fields&gt; (sources disagree on a substantive field); &lt;field&gt;_unvalidated_only (the field had only unvalidated OCR values, which never enter the register, so it is blank); unvalidated_values=&lt;n&gt; (number of such values set aside); breeding_line_not_a_code_moved (descriptive text moved out of breeding_line); institute_claim_only (no official evidence); cgiar_role_default_unknown_no_pedigree, cgiar_role_5_pedigree_needs_review, cgiar_role_4_pedigree_documented_no_cgiar_element, cgiar_role_2_via_parent_variety, cgiar_center_missing (how cgiar_role was set); planned_not_released (fish). | 0.89 |
| `conflict_fields` | Substantive fields on which the sources for this row disagree, separated by '; '. Only approval_date, gazette_date, breeding_line, pedigree, release_category, origin_country, release_date, generation and approval_or_release_mechanism are considered substantive. Blank means no substantive disagreement was found among eligible values. | Field names separated by '; '. | 0.44 |
| `conflict_note` | One short note per field on which sources disagree, of the form '&lt;field&gt;: chose &lt;value&gt;; also &lt;other value&gt; (&lt;source_id&gt;)', with notes for different fields separated by ' \| '. It covers every field, including formatting differences, and is a pointer to bgd_conflicts.csv, which holds every version with its file and page. | Free text; notes separated by ' \| '. Later gazette notifications are listed as 'later gazette(s): &lt;dates&gt;'. | 1.00 |
| `notes` | Free-text notes added by the coordinator or reviewers about the row, such as a CGIAR record that was checked and not used. | Free text; blank for most rows. | 0.22 |
| `source_url_status` | Result of the most recent automated check of the address in source_url. A status other than ok does not mean the archived copy is missing: the file itself is kept under 02_raw/. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 1.00 |
| `archived_url_status` | Result of the most recent automated check of the address in archived_url. A status other than ok does not mean the archived copy is missing: the file itself is kept under 02_raw/. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 0.89 |

## bgd_fish_events.csv

*Unit of observation:* One germplasm transfer, dissemination or planned release.

WorldFish germplasm transfers to BFRI and private companies, breeding-nucleus disseminations and announced future generations. These are kept apart from bgd_fish_strains.csv because none of them is a release of a named strain.

The file has 6 rows and 31 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `event_id` | Identifier of the germplasm transfer, dissemination or planned release. | 'FISH-' followed by a key. | 1.00 |
| `event_type` | Kind of event. These are not releases of named strains and are kept apart from bgd_fish_strains.csv. | germplasm transfer (WorldFish -&gt; BFRI); germplasm transfer (WorldFish -&gt; private company); germplasm dissemination (WorldFish breeding nuclei); planned generation release. | 1.00 |
| `species_common_en` | English common name of the species. | Free text. | 0.00 |
| `species_scientific` | Scientific name, as printed by the source where noted. | Latin binomial. | 1.00 |
| `species_bn` | Bangla name of the species. | Bangla text. | 0.00 |
| `strain_name` | Name of the strain as printed by the main source, often Bangla. | Free text. | 1.00 |
| `developer` | Organisation that developed the strain, as stated. Blank when the source names none. | Free text. | 0.33 |
| `cgiar_role` | Documented CGIAR (WorldFish) involvement in the strain, on the same 1-5 scale as rice. | 1 WorldFish line released directly; 2 CGIAR germplasm as parent stock; 3 collaboration or funding only; 4 no CGIAR element documented; 5 unknown. Blank when no source states it. | 1.00 |
| `cgiar_center` | CGIAR centre named. | WorldFish; WorldFish (formerly ICLARM). | 1.00 |
| `approval_or_release_mechanism` | How the strain was released or made available, beginning with a release-ladder code and followed by the evidence. | R1_ministerial_naming (MoFL notification); R2_institute_release (BFRI announcement or Technology Validation Committee list); R3_cgiar_release (WorldFish-documented release of a named generation); R4_dissemination_only; or 'none yet (R3 pending)'. | 1.00 |
| `releasing_body` | Body that released or declared the strain. | Free text. | 0.50 |
| `release_date` | Date of release, naming or transfer. Blank when no source dates it. | ISO date YYYY-MM-DD, or year only. | 0.50 |
| `generation` | Selection generation of the strain as described by the source. | Free text such as 'G3', 'F4 broodstock used to produce F5 (2017)'. | 0.83 |
| `key_traits` | Performance claims and awards as stated, e.g. percent higher growth than the existing strain. | Free text; entries joined by ' \| '. | 0.33 |
| `distribution_channel` | How seed (spawn, fry, broodstock) reached hatcheries or farmers. | Free text. | 0.50 |
| `status` | Current status as stated by the source (for example BFRI's dissemination categories). | Free text; 'planned_not_yet_released' for announced generations. | 0.67 |
| `source_url` | Web address from which the main source file of the row was downloaded. For the rice register this is the file that supplied the approval record (approval_date); for other tables it is the file that supplied the row. | Absolute http(s) URL. Many Government of Bangladesh files are served from an Oracle object-storage address rather than a portal page; that is the address the portal links to. | 1.00 |
| `archived_url` | Address of a copy of the same file in the Internet Archive's Wayback Machine, so that the source can be consulted if the original address changes. Blank means no archived copy was made or found; it does not mean the original is unavailable. | https://web.archive.org/web/&lt;timestamp&gt;/&lt;original URL&gt;. | 0.83 |
| `local_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `source_type` | Authority rank of the source that supplied the row's main date. The rank decides which value wins when sources disagree. | 1_primary_legal (NSB minutes, Bangladesh Gazette notifications, acts and rules); 2_official_list (SCA and MoA variety lists); 3_institute_page (BRRI, BINA, BFRI and university web pages, handbooks and fact sheets); 4_cgiar_record (CGIAR, IRRI, SPIA, HarvestPlus, WorldFish, ASTI/TRIVSA, GloMIP records); 5_peer_reviewed; 6_secondary (preprints, news, grey literature); 7_reviewer_synthesis (a value added by a reviewer with the file and page cited in the notes). | 1.00 |
| `retrieved_at` | Date on which the main source file was downloaded or the bibliographic record was retrieved. | ISO date YYYY-MM-DD. | 1.00 |
| `n_sources` | Number of distinct source documents that supplied at least one usable (eligible) value for the row. It measures how well documented a row is, not how many sources agree. | Count, 1 or more. | 1.00 |
| `cgiar_source_urls` | Links to every CGIAR-produced source that mentions the row (SPIA, IRRI, TRIVSA/ASTI, GloMIP, HarvestPlus, CGSpace, WorldFish, CGIAR papers). These sources are a cross-check and are not the basis of the approval record. | URLs separated by ' \| '. Europe PMC and Springer supplement addresses are replaced by the article's DOI or landing page. | 1.00 |
| `cgiar_evidence_url` | Original public address of the document behind cgiar_evidence. Blank when cgiar_evidence is blank. | Absolute URL. | 0.00 |
| `validation_summary` | Summary of how the key values of the row were checked, written as field=check (extraction method) and separated by '; '. The fields reported are approval_date, breeding_line, gazette_date and cgiar_role when present. | Checks: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). 'text' means the value came from a machine-readable text layer and needed no check. Methods: html; pdf_text (the PDF's own Unicode text layer); bijoy2unicode (a legacy SutonnyMJ/Bijoy text layer converted to Unicode); api_json; xlsx; ocr (Tesseract 5 OCR of a 300-dpi render); visual_check (transcribed by eye from the page image). | 1.00 |
| `flags` | Machine-readable quality flags for the row, separated by ';'. A flag marks something an analyst should know before using the row; the absence of flags does not certify a value. | year_only (only the year of the date is documented); date_single_source (one source, not cross-checked); has_conflicts:&lt;fields&gt; (sources disagree on a substantive field); &lt;field&gt;_unvalidated_only (the field had only unvalidated OCR values, which never enter the register, so it is blank); unvalidated_values=&lt;n&gt; (number of such values set aside); breeding_line_not_a_code_moved (descriptive text moved out of breeding_line); institute_claim_only (no official evidence); cgiar_role_default_unknown_no_pedigree, cgiar_role_5_pedigree_needs_review, cgiar_role_4_pedigree_documented_no_cgiar_element, cgiar_role_2_via_parent_variety, cgiar_center_missing (how cgiar_role was set); planned_not_released (fish). | 1.00 |
| `conflict_fields` | Substantive fields on which the sources for this row disagree, separated by '; '. Only approval_date, gazette_date, breeding_line, pedigree, release_category, origin_country, release_date, generation and approval_or_release_mechanism are considered substantive. Blank means no substantive disagreement was found among eligible values. | Field names separated by '; '. | 0.33 |
| `conflict_note` | One short note per field on which sources disagree, of the form '&lt;field&gt;: chose &lt;value&gt;; also &lt;other value&gt; (&lt;source_id&gt;)', with notes for different fields separated by ' \| '. It covers every field, including formatting differences, and is a pointer to bgd_conflicts.csv, which holds every version with its file and page. | Free text; notes separated by ' \| '. Later gazette notifications are listed as 'later gazette(s): &lt;dates&gt;'. | 0.33 |
| `notes` | Free-text notes added by the coordinator or reviewers about the row, such as a CGIAR record that was checked and not used. | Free text; blank for most rows. | 0.50 |
| `source_url_status` | Result of the most recent automated check of the address in source_url. A status other than ok does not mean the archived copy is missing: the file itself is kept under 02_raw/. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 1.00 |
| `archived_url_status` | Result of the most recent automated check of the address in archived_url. A status other than ok does not mean the archived copy is missing: the file itself is kept under 02_raw/. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 0.83 |

## bgd_fish_approvals.csv

*Unit of observation:* One government act on a fish or shrimp species, strain or framework.

Register of government acts on fish and shrimp: species that hatcheries may produce, species allowed for import (including ornamentals), bans, the vannamei introduction, strain naming, BFRI technology listings, brood-bank supply, policies and legal powers, each with the issuing body, date, reference, legal basis, quote and source.

The file has 183 rows and 26 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `act_id` | Identifier of the government act or listing. | 'F4-A&lt;nnn&gt;'. | 1.00 |
| `key` | Key of the species, strain or legal framework the act concerns; several acts can share one key. | SPECIES_&lt;name&gt;, FISH_&lt;strain key&gt; or FRAMEWORK_&lt;instrument&gt;. | 1.00 |
| `level` | Whether the act concerns a species, a named strain or the legal framework as a whole. | species; strain; framework. | 1.00 |
| `species_common_en` | English common name of the species; for lists printed only in Bangla this is the archive's gloss. | Free text. | 0.96 |
| `species_scientific` | Scientific name as printed, spacing errors kept. | Latin binomial. | 0.77 |
| `species_bn` | Bangla name as printed. | Bangla text. | 0.36 |
| `strain_name` | Strain named by the act, as printed. | Free text. | 0.08 |
| `approval_type` | Kind of government act or listing. | import_approval_ornamental; import_approval; hatchery_permitted_species; hatchery_permitted_input; introduction_recorded; introduction_approval; technology_validation_listing; technology_transfer; strain_naming; strain_release; brood_bank_supply; ban; ban_proposal; framework_instrument; policy; enforcement_directive; genetic_resource_protection; farm_permit_procedure; implementation_circular; health_certification_requirement. | 1.00 |
| `approving_body` | Ministry, department or committee that issued the act, with the instrument. | Free text; 'not stated' where the source names none. | 1.00 |
| `approval_date` | Date the act was issued or signed. | ISO date YYYY-MM-DD, or year only. | 0.96 |
| `gazette_date` | Date of publication in the Bangladesh Gazette, where published. | ISO date YYYY-MM-DD. | 0.74 |
| `approval_reference` | Number and date of the instrument or the citation of the listing. | Free text, Bangla numbers as printed. | 1.00 |
| `gazette_reference` | Gazette issue and pages, or the result of a search that found none. | Free text. | 0.74 |
| `legal_basis` | Act, section or rule under which the instrument was issued. | Free text; 'none stated'. | 1.00 |
| `scope_conditions` | What the act covers and the conditions attached. | Free text. | 1.00 |
| `status` | Whether the act is in force, superseded or a proposal, as far as the archive shows. | Free text (e.g. 'in force', 'introduced', 'trial'). | 1.00 |
| `release_ladder` | For strain-level acts, the step of the release ladder the act represents. | R1_statutory (ministerial naming; renamed R1_ministerial_naming in bgd_fish_strains.csv); R2_institute_release; R3_cgiar_release; R4_dissemination_only. | 0.08 |
| `source_url` | Web address from which the main source file of the row was downloaded. For the rice register this is the file that supplied the approval record (approval_date); for other tables it is the file that supplied the row. | Absolute http(s) URL. Many Government of Bangladesh files are served from an Oracle object-storage address rather than a portal page; that is the address the portal links to. | 1.00 |
| `local_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `page` | Page of the source file on which the value is printed, counted as the PDF page (1 = first page of the file), not the number printed on the page. | Integer page number, or a range 'a-b' when the item spans pages. Blank for web pages, spreadsheets and API records. | 0.85 |
| `locator` | Where on the page or in the file the value was found: a table and row, a sheet and cell, a quoted phrase, or the path of the image crop that was read by eye. | Free text. | 0.09 |
| `quote` | Exact words of the source that establish the act. | Verbatim, Bangla or English. | 1.00 |
| `method` | How the value was read from the source file. | html; pdf_text (the PDF's own Unicode text layer); bijoy2unicode (a legacy SutonnyMJ/Bijoy text layer converted to Unicode); api_json; xlsx; ocr (Tesseract 5 OCR of a 300-dpi render); visual_check (transcribed by eye from the page image). | 1.00 |
| `validation` | How the value was checked after extraction. Unvalidated OCR values are kept in the evidence but never enter the register. | key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). | 1.00 |
| `confidence` | The extracting agent's judgement of how secure the reading or the match is. | high; medium; low. | 1.00 |
| `notes` | Notes on reading the act (names as printed, glosses, why a row is not an approval). | Free text. | 0.98 |

## bgd_conflicts.csv

*Unit of observation:* One version of one field for one variety from one source.

Every value on which eligible sources disagree, in long format: one row per version, with its source, file, page, extraction method and validation, and a flag for the version used in the register. Formatting differences are included; bgd_conflicts_summary.csv separates them from substantive disagreements.

The file has 9,995 rows and 13 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `key` | Register key of the variety (without 'RICE-') or the fish key. | Register key; FISH_&lt;key&gt;. | 1.00 |
| `field` | Register field on which sources disagree. | Column name of the rice register or fish tables. | 1.00 |
| `value` | One version of the value, as normalised for the register. | Free text. | 1.00 |
| `value_raw` | The same version as printed in the source (Bangla, ditto marks and all). | Verbatim text. | 1.00 |
| `source_id` | Identifier of the source document. | Short code (e.g. MOA_HYB26, SCA_COMP, NSB_R5, RB-S01). | 1.00 |
| `source_title` | Title of the source document. | Free text. | 1.00 |
| `authority_rank` | Authority rank of the source, used to choose between disagreeing values. Lower numbers are more authoritative for legal facts such as approval dates; for descriptive fields (names, traits) assemble.py uses field-specific orders documented in the preface. | 1_primary_legal (NSB minutes, Bangladesh Gazette notifications, acts and rules); 2_official_list (SCA and MoA variety lists); 3_institute_page (BRRI, BINA, BFRI and university web pages, handbooks and fact sheets); 4_cgiar_record (CGIAR, IRRI, SPIA, HarvestPlus, WorldFish, ASTI/TRIVSA, GloMIP records); 5_peer_reviewed; 6_secondary (preprints, news, grey literature); 7_reviewer_synthesis (a value added by a reviewer with the file and page cited in the notes). | 1.00 |
| `local_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `page` | Page of the source file on which the value is printed, counted as the PDF page (1 = first page of the file), not the number printed on the page. | Integer page number, or a range 'a-b' when the item spans pages. Blank for web pages, spreadsheets and API records. | 0.91 |
| `locator` | Where on the page or in the file the value was found: a table and row, a sheet and cell, a quoted phrase, or the path of the image crop that was read by eye. | Free text. | 1.00 |
| `method` | How the value was read from the source file. | html; pdf_text (the PDF's own Unicode text layer); bijoy2unicode (a legacy SutonnyMJ/Bijoy text layer converted to Unicode); api_json; xlsx; ocr (Tesseract 5 OCR of a 300-dpi render); visual_check (transcribed by eye from the page image). | 1.00 |
| `validation` | How the value was checked after extraction. Unvalidated OCR values are kept in the evidence but never enter the register. | key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). | 1.00 |
| `chosen` | Whether this version is the one used in the register. | yes; no. | 1.00 |

## bgd_conflicts_summary.csv

*Unit of observation:* One variety and field with more than one version.

Disagreements between sources on the analytically important fields, one row per variety and field, classified as formatting only, compatible, a later decision or notification, a date difference, or substantive, with the value used and every alternative.

The file has 562 rows and 10 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `variety_id` | Register identifier of the variety or strain. | RICE-&lt;key&gt; or FISH-&lt;key&gt;. | 1.00 |
| `field` | Field on which the sources disagree. Only analytically important fields are summarised. | approval_date; gazette_date; breeding_line; pedigree; release_category; origin_country; season; duration_days; yield_t_ha; release_date; generation. | 1.00 |
| `classification` | Classification of the disagreement. Only 'substantive' and the date differences are real disagreements; the others are differences of form or later events. | formatting_only (same value written differently); compatible (translation, subset, overlapping numeric range, code with or without suffix); later_decision (a later NSB decision such as an extension or full release); later_notification (a later gazette); date_same_year; date_1_year; date_2plus_years; substantive. | 1.00 |
| `chosen_value` | Value used in the register. | Free text. | 1.00 |
| `chosen_source` | Kind of source that supplied the value used. | NSB minutes; SCA annual list; SCA compendium 2016; MoA hybrid list; Bangladesh Gazette; BRRI handbook (ADC); BRRI Rice Profile; BRRI other; BINA / IAEA; SPIA 2025; TRIVSA; HarvestPlus; GloMIP; CGIAR papers; Literature; CGIAR websites; Fish sources; Other. | 1.00 |
| `chosen_file` | Archived file of the value used. | Path under 02_raw/. | 1.00 |
| `chosen_page` | Page of the value used. | Integer page. | 0.98 |
| `n_versions` | Number of distinct values recorded for the field. | Count, 2 or more. | 1.00 |
| `alternatives` | Every version that is not compatible with the value used, with its source, file and page. | '&lt;value&gt; (&lt;source&gt;, &lt;file&gt; p.&lt;page&gt;)' entries joined by ' \| '. | 0.99 |
| `dissenting_sources` | Kinds of source that disagree with the value used. | Labels as in chosen_source joined by '; '. | 0.99 |

## bgd_sources.csv

*Unit of observation:* One archived source file.

Every source file that supplied at least one eligible value: its identifier, title, authority rank, original and archived addresses, download date and SHA-256 checksum.

The file has 354 rows and 10 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `source_id` | Identifier of the source document or source group. A group identifier (such as one for all BRRI Rice Profile pages) can cover many files, so it is not unique; local_file is. | Short code. | 1.00 |
| `source_title` | Title of the source. | Free text. | 1.00 |
| `authority_rank` | Authority rank of the source, used to choose between disagreeing values. Lower numbers are more authoritative for legal facts such as approval dates; for descriptive fields (names, traits) assemble.py uses field-specific orders documented in the preface. | 1_primary_legal (NSB minutes, Bangladesh Gazette notifications, acts and rules); 2_official_list (SCA and MoA variety lists); 3_institute_page (BRRI, BINA, BFRI and university web pages, handbooks and fact sheets); 4_cgiar_record (CGIAR, IRRI, SPIA, HarvestPlus, WorldFish, ASTI/TRIVSA, GloMIP records); 5_peer_reviewed; 6_secondary (preprints, news, grey literature); 7_reviewer_synthesis (a value added by a reviewer with the file and page cited in the notes). | 1.00 |
| `local_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `source_url` | Web address from which the main source file of the row was downloaded. For the rice register this is the file that supplied the approval record (approval_date); for other tables it is the file that supplied the row. | Absolute http(s) URL. Many Government of Bangladesh files are served from an Oracle object-storage address rather than a portal page; that is the address the portal links to. | 1.00 |
| `archived_url` | Address of a copy of the same file in the Internet Archive's Wayback Machine, so that the source can be consulted if the original address changes. Blank means no archived copy was made or found; it does not mean the original is unavailable. | https://web.archive.org/web/&lt;timestamp&gt;/&lt;original URL&gt;. | 0.20 |
| `download_date` | Date the file was downloaded. | ISO date YYYY-MM-DD. | 1.00 |
| `sha256` | SHA-256 hash of the archived file, which lets a user verify that the copy in 02_raw/ is the file that was downloaded. | 64 lowercase hexadecimal characters. | 1.00 |
| `source_url_status` | Result of the most recent automated check of the address in source_url. A status other than ok does not mean the archived copy is missing: the file itself is kept under 02_raw/. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 1.00 |
| `archived_url_status` | Result of the most recent automated check of the address in archived_url. A status other than ok does not mean the archived copy is missing: the file itself is kept under 02_raw/. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 0.20 |

## bgd_ocr_pages.csv

*Unit of observation:* One page of an official document.

The text corpus of the official documents (minutes, gazettes, lists, laws, notices, leaflets): for every page, the full OCR text with word confidence and, where the PDF has a usable one, its own text layer. It allows full-text search and re-checking of any value against the page.

The file has 1,925 rows and 17 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `source_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `page` | Page of the source file on which the value is printed, counted as the PDF page (1 = first page of the file), not the number printed on the page. | Integer page number, or a range 'a-b' when the item spans pages. Blank for web pages, spreadsheets and API records. | 1.00 |
| `source_url` | Web address from which the main source file of the row was downloaded. For the rice register this is the file that supplied the approval record (approval_date); for other tables it is the file that supplied the row. | Absolute http(s) URL. Many Government of Bangladesh files are served from an Oracle object-storage address rather than a portal page; that is the address the portal links to. | 1.00 |
| `ocr_engine` | OCR engine and settings. Blank when the page was not OCR'd. | e.g. 'Tesseract 5.4 ben+eng tessdata_best, psm 6, 300 dpi'. | 0.80 |
| `full_ocr_text` | Complete, untruncated OCR text of the page. OCR of Bangla print is imperfect; use it for search, not as a transcription. | Text with line breaks. | 0.79 |
| `mean_word_conf` | Mean Tesseract confidence of the recognised words on the page. | 0-100. | 0.79 |
| `median_word_conf` | Median Tesseract word confidence. | 0-100. | 0.79 |
| `pct_words_conf_below_60` | Percentage of words with confidence below 60. | Percent, 0-100. | 0.79 |
| `n_words` | Number of words recognised on the page. | Count. | 0.80 |
| `text_layer_text` | The PDF's own text layer when usable: Bijoy (SutonnyMJ) spans converted to Unicode, other fonts kept raw. Characters of fonts with no Unicode map are replaced by '[?]'. Blank when the file has no usable text layer. | Text. | 0.22 |
| `n_pages` | Number of pages in the source file. | Count. | 1.00 |
| `doc_class` | Kind of document. | minutes; gazette; official_list; law_rule_procedure; notice; leaflet; other_official. | 1.00 |
| `coverage_status` | Which texts exist for the page. | ocr only; ocr + text layer; text layer only; not OCR'd, no usable text layer; OCR'd: no text recognised (blank or image-only page). | 1.00 |
| `text_layer_note` | Fonts of the text layer and why it was used or judged unusable. | Free text. | 1.00 |
| `ocr_note` | Note on the OCR of the page; empty in the current release. | Free text. | 0.00 |
| `png_path` | Path of the 300-dpi page image that was OCR'd. | Path under 03_extracted/text/ocr/. | 0.80 |
| `ocr_txt_path` | Path of the cached OCR text file. | Path under 03_extracted/text/ocr/. | 0.80 |

## bgd_ocr_audit.csv

*Unit of observation:* One OCR'd page that supplied values.

OCR quality for each page from which OCR'd values were taken: Tesseract word confidence and how many of the page's values were validated against the meeting-date key, read by eye, or left unvalidated.

The file has 166 rows and 10 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `local_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `page` | Page of the source file on which the value is printed, counted as the PDF page (1 = first page of the file), not the number printed on the page. | Integer page number, or a range 'a-b' when the item spans pages. Blank for web pages, spreadsheets and API records. | 1.00 |
| `n_words` | Number of words with a confidence score on the page. | Count. | 1.00 |
| `mean_word_conf` | Mean Tesseract word confidence. | 0-100, one decimal. | 1.00 |
| `median_word_conf` | Median Tesseract word confidence. | 0-100, one decimal. | 1.00 |
| `pct_words_conf_below_60` | Percentage of words with confidence below 60. | Percent, one decimal. | 1.00 |
| `n_values` | Number of OCR'd evidence values taken from the page. | Count. | 1.00 |
| `n_key_check` | Of these, values validated against the NSB meeting-date key. | Count. | 1.00 |
| `n_visual_check` | Of these, values checked by eye on the page image. | Count. | 1.00 |
| `n_unvalidated` | Of these, values not checked. Unvalidated OCR never enters the register. | Count. | 1.00 |

## bgd_rice_not_approved_or_unresolved.csv

*Unit of observation:* One rice name with no documented approval.

Names that appear in the sources as rice varieties but for which no eligible evidence records an approval event (for example Jirashail, refused in 2022, Iratom-38 and BU Aromatic dhan2). The columns are those of the register before the derived columns are added.

The file has 3 rows and 73 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `variety_id` | Identifier of the name, built in the same way as register identifiers so that it can be joined to bgd_nsb_decisions_full.csv and bgd_variety_status.csv. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 1.00 |
| `variety_name` | Uniform English display name of the variety, generated from the identifier so that every variety is written the same way (for example 'BRRI dhan29', 'Binadhan-7', 'BRRI hybrid dhan1'). It is intended for display and labelling; the spellings used by the official documents are kept in official_name_en and official_name_bn. | Free text; for private hybrids the registration or trial code is added in parentheses where one is known, e.g. 'Partex hybrid dhan6 (HR-30)'. Unique within the register. | 1.00 |
| `official_name_en` | English name of the variety as printed by the developing institute or another official source, with the source's own spacing and hyphenation (for example 'BAU dhan 2'). Blank means no English spelling was printed; most such rows are private hybrids registered under a Bangla name. | Free text as printed. | 0.33 |
| `official_name_bn` | Bangla name of the variety as printed in the official record, kept exactly as printed, including Bangla digits and the source's own spacing and hyphens (for example 'বিনা ধান-১০'). | Bangla text (Unicode, NFC as extracted). Never blank in the register. | 0.67 |
| `popular_name` | Popular or farmer name given by an official or institute source (for example চান্দিনা for BR1). Blank means no source states one; other names reported by surveys and markets are in bgd_local_names.csv. | Free text, usually Bangla. | 0.00 |
| `aliases` | Other labels under which the variety appears in the sources: breeding-line labels that are not line codes (such as 'BR11-Sub1'), names used before renaming, trade names and codes printed by other sources. It is a record of labels seen in the sources, not a vetted list of local names. | Labels separated by ' \| ', in order of first appearance. | 0.00 |
| `breeding_line` | Pre-release designation of the line that became the variety (for example 'BR7671-37-2-2-3-7-3', 'IR91820-25BAY2-3-1'); for private hybrids, the company's trial or product code (for example 'Win301'). Blank means no line code was published. | Designation as printed. Where a source prints the code in both Bangla and Latin script the two forms are joined by '\|' without spaces (for example 'বাউ-১৬\|BAU-16'). | 0.00 |
| `pedigree` | Parentage of the variety as printed, usually in Purdy notation ('/' a first-order cross, '//' a second-order cross, 'A*n/B' a backcross), or a statement of derivation such as 'mutant of BRRI dhan29' or 'line collected from IRRI, Philippines'. Blank means no pedigree has been published, which is the case for most private hybrids; it does not mean the variety has no known parents. | Free text as printed. Parsed parent-child links are in bgd_pedigree_edges.csv. | 0.33 |
| `hybrid_parent_female` | Reserved for the female (cytoplasmic male-sterile A) parent of a hybrid. It is empty in the current release: registration records do not publish hybrid parent lines, and where a source prints them they are kept in pedigree. | Empty in every row. | 0.00 |
| `hybrid_parent_male` | Reserved for the male (restorer) parent of a hybrid. It is empty in the current release for the reason given under hybrid_parent_female. | Empty in every row. | 0.00 |
| `type` | Variety type as written by the winning source. Capitalisation is not harmonised and a few rows are blank; rice_type is the cleaned version. | hybrid; inbred; Inbred; inbred (mutant). | 0.00 |
| `developer` | Name of the developing institute or the applicant company as printed by the winning source, in Bangla or English. The same developer is written in many ways (148 spellings); use developer_std for grouping. | Free text as printed. | 0.67 |
| `developer_division` | Breeding division of the developing institute, where an institute page or the author affiliation of the key paper names it. It is a medium-confidence attribution, not an official statement of which division bred the variety. | Plant Breeding Division, BRRI; Plant Breeding Division, BINA. | 0.00 |
| `origin_country` | Country of origin of the variety or its seed as recorded by the winning source, with any correction the source itself records. developer_country_of_origin is the cleaned version. | Mostly China, India, Bangladesh, Philippines (IRRI); a few cells carry the correction text, e.g. 'China (as corrected by NSB 91; NSB 90 printed ...)'. | 0.33 |
| `origin_statement` | Statements of origin found in the pedigree slot of a source (for example 'origin India', 'imported from China'), kept separately because they describe where seed came from, not parentage. | Statements separated by ' \| '. | 0.00 |
| `trial_codes` | Seed Certification Agency trial entry numbers of a hybrid (for example 'H-101/127'), found in the pedigree or breeding-line slot of a source. They identify the entry in the SCA's VCU trials and are not pedigrees. | Codes separated by ' \| ' (several trial years may be listed). | 0.00 |
| `pedigree_note` | Text found in the pedigree slot that is not a pedigree: 'own development', a trade name, a supplier, or a trait. Kept so that nothing printed is lost. | Notes separated by ' \| '. | 0.00 |
| `release_category` | Approval route. It is blank for every row of this table by construction: a name is placed here precisely because no eligible evidence records an approval event. | Blank. | 0.00 |
| `approving_body` | Body that approved the variety, as the sources describe it. For varieties released after 1977 the NSB approves and the Ministry of Agriculture notifies the release in the Gazette. | Mostly 'NSB' or 'NSB (approval); Government/MoA (notification)'; some rows name the Technical Committee meeting that recommended the variety; 'none: recommended before the NSB was constituted (1974)' for pre-NSB varieties. | 0.00 |
| `approval_date` | Date or year of the event that the sources do record for the name (for example the year an institute lists it, or the NSB meeting that refused it). It is not an approval date. | ISO date YYYY-MM-DD, or year only. | 0.67 |
| `approval_reference` | Meeting number and agenda item of the National Seed Board decision behind approval_date. | 'NSB &lt;n&gt;th meeting, agenda &lt;k&gt;' (agenda omitted where the source does not give it). | 0.00 |
| `provisional_release_date` | Date of an earlier provisional release by the NSB, for varieties whose full release came later (BRRI dhan40 and BRRI dhan41). Blank for all other varieties. | ISO date YYYY-MM-DD. | 0.00 |
| `provisional_release_reference` | NSB meeting and agenda item of the provisional release. | 'NSB &lt;n&gt;th meeting, agenda &lt;k&gt;'. | 0.00 |
| `gazette_date` | Date of the earliest Bangladesh Gazette notification of the release that was found in an archived copy of the Gazette. Later notifications of the same variety are listed in conflict_note. Blank means no archived gazette copy was found; see gazette_status for the reason. | ISO date YYYY-MM-DD. | 0.00 |
| `gazette_date_reported` | Gazette notification date as reported in later NSB minutes when no copy of that Gazette issue was found. It is a report of a notification, not a copy of one. | ISO date YYYY-MM-DD. | 0.00 |
| `gazette_status_note` | What the NSB minutes or Seed Wing memos say about the gazetting of the variety when no gazette copy was found (sent for gazetting, not yet published at the next meeting, reported issued between two dates). | Free text, partly Bangla, with memo numbers as printed. | 0.00 |
| `gazette_reference` | Issue, date and pages of the Gazette notification in gazette_date, with the Seed Wing notification number. | Free text, e.g. 'Bangladesh Gazette Extraordinary 2013-12-02, p.10261-10262; MoA Seed Wing ...'. | 0.00 |
| `season` | Growing season or seasons for which the variety was approved, in English labels as given by the winning source. Bangladesh has three rice seasons: Aus (pre-monsoon), Aman (monsoon) and Boro (dry, irrigated). For analysis use season_std or the three season flags, which also read season statements in other columns. | Aus; Aman; T. Aman; Boro; combinations joined by '; '; qualifiers such as '(direct-seeded)'. | 0.67 |
| `ecosystem` | Land type or rice ecosystem for which the variety is recommended, as printed. Most entries are Bangla land-elevation classes (উঁচু, মধ্যম উঁচু, নিচু জমি: high, medium-high, low land) rather than rice ecosystems. | Free text, mostly Bangla. | 0.00 |
| `region_scope` | Region for which the variety was approved, as summarised in English by the extracting agent from the NSB decision or official list. Hybrid registrations name SCA trial regions after their headquarters towns, in the source's spelling (Comilla, Jessore, Rajshahi). | 'nationwide', 'Whole country', or a comma-separated list of regions. | 0.00 |
| `duration_days` | Growth duration from seeding to maturity, in days, as printed. A cell may hold a range, several season-specific values or condition-specific values, so it is text; use duration_min_days and duration_max_days for numbers. | Days; free text such as '140-145', '130-135 (আউশ); 150-155 (বোরো)'. | 0.33 |
| `yield_t_ha` | Yield in tonnes per hectare as printed by the winning source (usually the average yield in trials or the yield the institute advertises). The cell may hold a range or season-specific values, so it is text. | t/ha; free text. | 0.33 |
| `yield_advantage_pct` | Yield advantage over the check variety, in percent, as stated in the NSB decision. For most hybrid registrations the figure is the registration criterion that the decision says the variety met (for example at least 20 percent over the check), not a measured gain, so it should not be read as an estimate of the yield gain. | Percent; a number, sometimes with a qualifier such as '10 (at 6 of 10 sites)' or '20 (vs BRRI dhan28)'. | 0.00 |
| `check_variety` | Variety used as the check (control) in the VCU trials named in the NSB decision, as printed. | Free text, mostly Bangla, sometimes with the check's yield. | 0.00 |
| `recommended_region` | Region or area for which the variety is recommended, as printed (mostly Bangla). Use region_divisions and region_nationwide for analysis. | Free text, mostly Bangla. | 0.00 |
| `release_year_official` | Release year printed in an official variety list (SCA compendium or annual list). It can differ from approval_year by a year because lists sometimes record the season of first cultivation or the year of printing. | Four-digit year. | 0.00 |
| `special_traits_official` | Special characteristics of the variety as printed in official lists and NSB minutes, verbatim (mostly Bangla). | Free text; several sources separated by ' \| '. | 0.00 |
| `identifying_traits_official` | Identifying (distinguishing) characteristics as printed in the official lists, verbatim (mostly Bangla), for example grain shape and colour. | Free text; several sources separated by ' \| '. | 0.00 |
| `quality_traits` | Grain quality values stated in the NSB minutes or institute sources, written as key=value pairs. | Keys: grain_type (as printed, Bangla), amylose_pct (percent), grain_wt_1000_g (grams per 1000 grains), protein_pct (percent), zinc_mg_kg and iron_mg_kg (mg/kg), lb_ratio (length-breadth ratio); pairs joined by '; ', sources by ' \| '. | 0.00 |
| `stress_tolerance` | Statements of tolerance to abiotic stress or resistance to disease and pests, verbatim (mostly Bangla). | Free text; several sources separated by ' \| '. | 0.00 |
| `dus_result` | Result of the Distinctness, Uniformity and Stability test as described in the NSB minutes (number of years, traits on which the variety differs from the check). | Free text, Bangla and English. | 0.00 |
| `vcu_sites` | Number of sites in the Value for Cultivation and Use trials reported in the NSB decision. | Integer count, occasionally with a qualifier such as '10 (2023-24 re-trial); 6 (2022-23)'. | 0.00 |
| `decision_conditions` | Conditions attached to the NSB decision, verbatim in Bangla: provisional periods, seed import limits, labelling requirements, re-trial requirements. | Free text; several decisions separated by ' \| '. | 0.33 |
| `key_traits` | Summary of the variety's key traits from all sources, in English or Bangla, typically duration, yield and notable tolerances, together with CGIAR screening codes where TRIVSA reports them. | Free text; one entry per source separated by ' \| '. | 0.67 |
| `adoption` | Adoption figures as reported by TRIVSA/ASTI, SPIA or study-area papers, each with its scope, reference period and method stated in the text. Figures from different sources measure different things (national area share by expert opinion, household survey shares in a sample) and are not comparable without reading the scope. | Free text; one entry per source separated by ' \| '. | 0.00 |
| `market_segment` | CGIAR Global Market Intelligence Platform (GloMIP) market segment to which the variety is assigned. A segment groups many varieties and can contradict the variety's own season or ecosystem, so it is not used to derive covariates. | '&lt;segment id&gt; \| &lt;crop&gt; \| &lt;hybrid status&gt; \| &lt;region&gt; \| &lt;use; grain&gt; \| ...' as printed by GloMIP. | 0.00 |
| `product_profile` | GloMIP product profile of the individual variety: recommended planting methods and ecosystems (PTR, DSR, irrigated lowland, rainfed lowland, upland), the varieties it is meant to replace or accompany, and its key strengths. | Free text as printed by GloMIP, ';'-separated attributes. | 0.00 |
| `status` | Status stated by a source (for example 'withdrawn'). | Free text code. | 0.33 |
| `doi_key_paper` | DOI of the release or description paper, or the main reference, for the variety. Blank means no such paper was found; it does not mean the variety is unpublished. | DOI without the https://doi.org/ prefix; several DOIs separated by ' \| '. | 0.00 |
| `cgiar_role` | Strongest documented link between the variety and CGIAR research, coded 1 to 5. The code describes documented links only: code 5 means no parentage or link is documented, which is the case for nearly all private hybrids, and it must not be read as 'no CGIAR involvement'. | 1 = CGIAR line released directly (or a mutant or selection within one); 2 = CGIAR line as parent or earlier ancestor, traced up to five generations (use depth_to_cgiar &lt;= 2 for the SPIA parent-or-grandparent definition); 3 = CGIAR collaboration or funding only; 4 = pedigree known, no CGIAR element; 5 = unknown. | 1.00 |
| `cgiar_center` | CGIAR centre named in the documented link. Blank for codes 4 and 5. | IRRI; AfricaRice; HarvestPlus. | 0.00 |
| `cgiar_lineage` | Every documented CGIAR link written out, including weaker links than the one coded in cgiar_role (for example 'IRRI grandparent: IR20 via BR10' or 'pedigree known: Iratom-24 x Dular'). | Free text; links separated by ' \| '. | 0.00 |
| `cgiar_evidence` | The quotation or table cell, as condensed by the extracting agent, that supports the CGIAR link coded in cgiar_role. | Free text, often Bangla. | 0.33 |
| `cgiar_evidence_quote` | Exact text of the source behind cgiar_evidence, in the original language, cut to 200 characters. | Free text, up to 200 characters. | 0.33 |
| `cgiar_evidence_source` | Archived file and page from which cgiar_evidence was taken. | '02_raw/&lt;path&gt;, p. &lt;n&gt;'. | 0.33 |
| `cgiar_evidence_url` | Original public address of the document behind cgiar_evidence. Blank when cgiar_evidence is blank. | Absolute URL. | 0.33 |
| `cgiar_spia_flags` | Flags from SPIA's Bangladesh Study 2025, Appendix B Table 27, kept separate from cgiar_role because SPIA's definition (IRRI parents or grandparents) differs from the register's code. | 'spia_direct', 'spia_indirect' or 'spia_none', then ' \| SPIA T27 flags: ' and Y/N values for irri_direct, indirect_ir_parent, inger_entry, in_reference_library, sub1, saline_tolerance, drought_tolerance, harvestplus, followed by the IRRI/INGER designation text as printed. | 0.33 |
| `cgiar_independent` | What CGIAR's own publications and websites say about the variety's origin (Dikitanan et al. 2022, Villanueva et al. 2022, Raitzer et al. 2015, Kretzschmar et al. 2018, CGSpace records, IRRI, HarvestPlus, STRASA, TRIVSA). It is a cross-check and is not used to set cgiar_role on its own. | Free text, '&lt;source&gt;: &lt;statement&gt;' entries separated by ' \| '. | 0.00 |
| `cgiar_source_urls` | Links to every CGIAR-produced source that mentions the row (SPIA, IRRI, TRIVSA/ASTI, GloMIP, HarvestPlus, CGSpace, WorldFish, CGIAR papers). These sources are a cross-check and are not the basis of the approval record. | URLs separated by ' \| '. Europe PMC and Springer supplement addresses are replaced by the article's DOI or landing page. | 0.33 |
| `source_url` | Web address from which the main source file of the row was downloaded. For the rice register this is the file that supplied the approval record (approval_date); for other tables it is the file that supplied the row. | Absolute http(s) URL. Many Government of Bangladesh files are served from an Oracle object-storage address rather than a portal page; that is the address the portal links to. | 1.00 |
| `archived_url` | Address of a copy of the same file in the Internet Archive's Wayback Machine, so that the source can be consulted if the original address changes. Blank means no archived copy was made or found; it does not mean the original is unavailable. | https://web.archive.org/web/&lt;timestamp&gt;/&lt;original URL&gt;. | 0.67 |
| `local_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `source_type` | Authority rank of the source that supplied the row's main date. The rank decides which value wins when sources disagree. | 1_primary_legal (NSB minutes, Bangladesh Gazette notifications, acts and rules); 2_official_list (SCA and MoA variety lists); 3_institute_page (BRRI, BINA, BFRI and university web pages, handbooks and fact sheets); 4_cgiar_record (CGIAR, IRRI, SPIA, HarvestPlus, WorldFish, ASTI/TRIVSA, GloMIP records); 5_peer_reviewed; 6_secondary (preprints, news, grey literature); 7_reviewer_synthesis (a value added by a reviewer with the file and page cited in the notes). | 1.00 |
| `retrieved_at` | Date on which the main source file was downloaded or the bibliographic record was retrieved. | ISO date YYYY-MM-DD. | 1.00 |
| `n_sources` | Number of distinct source documents that supplied at least one usable (eligible) value for the row. It measures how well documented a row is, not how many sources agree. | Count, 1 or more. | 1.00 |
| `validation_summary` | Summary of how the key values of the row were checked, written as field=check (extraction method) and separated by '; '. The fields reported are approval_date, breeding_line, gazette_date and cgiar_role when present. | Checks: key_check (a date or number matched the validated NSB meeting-date key); visual_check (read by eye on the page image or a crop of it); two_source (two independent sources give the same value); unvalidated (machine-readable text or OCR not checked by eye). 'text' means the value came from a machine-readable text layer and needed no check. Methods: html; pdf_text (the PDF's own Unicode text layer); bijoy2unicode (a legacy SutonnyMJ/Bijoy text layer converted to Unicode); api_json; xlsx; ocr (Tesseract 5 OCR of a 300-dpi render); visual_check (transcribed by eye from the page image). | 0.67 |
| `flags` | Machine-readable quality flags for the row, separated by ';'. A flag marks something an analyst should know before using the row; the absence of flags does not certify a value. | year_only (only the year of the date is documented); date_single_source (one source, not cross-checked); has_conflicts:&lt;fields&gt; (sources disagree on a substantive field); &lt;field&gt;_unvalidated_only (the field had only unvalidated OCR values, which never enter the register, so it is blank); unvalidated_values=&lt;n&gt; (number of such values set aside); breeding_line_not_a_code_moved (descriptive text moved out of breeding_line); institute_claim_only (no official evidence); cgiar_role_default_unknown_no_pedigree, cgiar_role_5_pedigree_needs_review, cgiar_role_4_pedigree_documented_no_cgiar_element, cgiar_role_2_via_parent_variety, cgiar_center_missing (how cgiar_role was set); planned_not_released (fish). | 1.00 |
| `conflict_fields` | Substantive fields on which the sources for this row disagree, separated by '; '. Only approval_date, gazette_date, breeding_line, pedigree, release_category, origin_country, release_date, generation and approval_or_release_mechanism are considered substantive. Blank means no substantive disagreement was found among eligible values. | Field names separated by '; '. | 0.00 |
| `conflict_note` | One short note per field on which sources disagree, of the form '&lt;field&gt;: chose &lt;value&gt;; also &lt;other value&gt; (&lt;source_id&gt;)', with notes for different fields separated by ' \| '. It covers every field, including formatting differences, and is a pointer to bgd_conflicts.csv, which holds every version with its file and page. | Free text; notes separated by ' \| '. Later gazette notifications are listed as 'later gazette(s): &lt;dates&gt;'. | 0.33 |
| `notes` | Free-text notes added by the coordinator or reviewers about the row, such as a CGIAR record that was checked and not used. | Free text; blank for most rows. | 0.00 |
| `gazette_status` | Gazette situation of every variety, stated explicitly so that a blank gazette_date can be interpreted. Hybrid registrations are not gazetted, and no weekly Gazette issues before 2013 are online, so a missing gazette date before 2013 is usually a gap in the archive, not evidence that no notification was made. | notified (gazette in archive); notified per NSB minutes (gazette copy not found); notified per NSB minutes (date not stated); sent to Government Press, publication not confirmed; not gazetted (hybrid registrations are not gazetted); not applicable (before the Seeds Ordinance 1977); not yet published (gazettes checked to 1 Oct 2026); not found (dpp.gov.bd holds no weekly gazettes before 2013). | 1.00 |
| `source_url_status` | Result of the most recent automated check of the address in source_url. A status other than ok does not mean the archived copy is missing: the file itself is kept under 02_raw/. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 1.00 |
| `archived_url_status` | Result of the most recent automated check of the address in archived_url. A status other than ok does not mean the archived copy is missing: the file itself is kept under 02_raw/. | ok; blocked_to_bots (HTTP 403: the page exists but refuses automated checks); dead (404, 410 or a soft error page); unreachable (DNS, TLS or timeout failure); unchecked. Blank when the link column is blank. | 0.67 |

## bgd_variety_crosswalk.csv

*Unit of observation:* One variety code or label in one survey or library.

Rice variety codes in household surveys (BIHS 2011-12, 2015, 2018-19 and the SPIA 2024 round; MIXTAPE 2026 questionnaire drafts) and reference names in the SPIA DNA fingerprinting library, matched to register identifiers by their label text. Codes are list positions that shift between rounds, so they must never be merged on the code number.

The file has 1,053 rows and 13 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `source` | Survey round or reference library that uses the code. | BIHS2011_12; BIHS2015; BIHS2018_19; BIHS2024_SPIA; MIXTAPE2026_draft; SPIA_DNA_reference. | 1.00 |
| `source_file` | File from which the value labels or code list were read (value labels only, never household records). | Path relative to the BGD_MIX project folder. | 1.00 |
| `variable` | Variables (or questionnaire code lists) that carry this code and label. | Names joined by '; '. | 1.00 |
| `code` | Numeric code of the variety in the survey, or the reference name in the DNA library. Codes are list positions that differ between rounds; never merge on the code alone. | Integer, or text for the DNA library. | 1.00 |
| `label_as_printed` | Value label of the code as printed in the survey file. | Free text. | 1.00 |
| `variety_id` | Register variety matched to the label. Blank for brand families, non-approved names, residual categories and unmatched labels. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 0.81 |
| `variety_name` | Display name of the matched variety. | Free text. | 0.81 |
| `match_type` | How the label was matched; matching uses the label text only, never the code number. | exact_code_name (official series designation read from the label); normalised_name; alias; brand_family (trade name covering several registered products; members in candidate_ids); not_approved_variety (widely grown name without approval; see non_register_id); generic_label (residual categories such as 'Others'); unmatched. | 1.00 |
| `n_candidates` | Number of register varieties the label could refer to. | Count. | 1.00 |
| `candidate_ids` | Register varieties the label could refer to, for brand families and unmatched brand members; listed for reference, not as a match. | variety_id values joined by ' \| '. | 0.06 |
| `confidence` | The extracting agent's judgement of how secure the reading or the match is. | high; medium; low. | 1.00 |
| `note` | Reason for the match, or why there is none. | Free text. | 1.00 |
| `non_register_id` | Stable identifier for widely grown names that have no Bangladesh approval. | 'NA_&lt;NAME&gt;' (e.g. NA_MINIKET, NA_HARIDHAN). | 0.05 |

## bgd_pedigree_edges.csv

*Unit of observation:* One parent-child link.

Parent-child links parsed from the published pedigrees in the register, with the parent's role, backcross dose, generation, whether the parent is a CGIAR line, and the register variety it resolves to where it does.

The file has 326 rows and 12 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `child_id` | Register variety whose pedigree is described. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 1.00 |
| `child_name` | Display name of the child variety. | Free text. | 1.00 |
| `parent_label_as_printed` | Parent or source line as written in the pedigree. | Free text. | 1.00 |
| `parent_id` | Register variety the parent label resolves to by identity (name key, exact name or alias, or breeding line). Never by similarity. Blank when the parent is not a register variety. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 0.26 |
| `parent_role` | Role of the parent in the cross or derivation. | female; male (first and second parent of a cross); recurrent; donor (backcross); mutant_source; somaclone_source; selection_source; unknown. | 1.00 |
| `backcross_dose` | Number of doses of the recurrent parent in 'A*n/B' notation. | Integer, or BC&lt;n&gt; as printed. | 0.02 |
| `parent_is_cgiar_line` | Whether the parent is a CGIAR line (IR, IRBB/IRBL, IRRI, IRGC, NERICA, WAB designations, or a register variety that is itself a CGIAR line). | Y; N. | 1.00 |
| `parent_cgiar_center` | CGIAR centre of the parent line. | IRRI; AfricaRice. | 0.35 |
| `source_column` | Register column (or other source) the edge was read from. | Free text. | 1.00 |
| `source_file` | File the edge was read from. | Paths joined by '; '. | 1.00 |
| `note` | How the parent was resolved, or why not. | Free text. | 0.47 |
| `generation` | Generation of the parent relative to the child: 1 for direct parents, 2 for parents of an unnamed F1 inside a composite cross, and so on; 0 for mutant, somaclone and selection sources, which share the child's generation. | Integer 0-4. | 1.00 |

## bgd_pedigree_summary.csv

*Unit of observation:* One register variety.

For each register variety, the number of parents parsed, the number of generations to the nearest documented CGIAR ancestor, that ancestor, the chain that leads to it and the parse status, with two working columns used to check cgiar_role.

The file has 443 rows and 8 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `variety_id` | Stable identifier of a rice variety in the register and the key for joining every table in the archive. The number inside the identifier is the official series number of the variety, not a running count. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 1.00 |
| `n_parents_parsed` | Number of direct parents (generation 0 or 1) parsed from the pedigree. | Count. | 1.00 |
| `depth_to_cgiar` | Number of generations between the variety and the nearest CGIAR line in its documented pedigree: 0 when the variety is a CGIAR line or a mutant, somaclone or selection of one, 1 when a parent is a CGIAR line, 2 for a grandparent, and so on. Blank means no CGIAR line was found within five generations of the documented pedigree, including the many varieties with no pedigree at all. | Integer 0-5; blank. | 0.30 |
| `nearest_cgiar_ancestor` | Name or designation of the CGIAR line found at depth_to_cgiar (for example 'IR20', 'IR8', 'Oryza rufipogon (IRGC103404)'). A register variety (such as BR6) appears when it is itself a CGIAR line. | Free text as printed in the pedigree. | 0.30 |
| `pedigree_parse_status` | What the pedigree parser could do with the variety's pedigree. | parsed; parsed_untraced_lines (parents include institute lines that cannot be traced in the register); statement_only (only a statement such as 'line collected from IRRI'); none (no pedigree). | 1.00 |
| `cgiar_path` | Chain from the variety to its nearest CGIAR ancestor. | '&lt;variety&gt; &lt;-g&lt;n&gt;- &lt;ancestor&gt;' links, with mutant_source, selection_source or somaclone_source for derivations and '[sister of ...]' for sister lines. | 0.30 |
| `current_cgiar_role` | cgiar_role of the variety in the register when the pedigree was built (working column). | 1-5. | 1.00 |
| `implied_cgiar_role` | cgiar_role that the parsed pedigree alone implies; a check against the register, not a value written to it (working column). | 1-5, rules in scripts/build_pedigree.py. | 1.00 |

## bgd_variety_events.csv

*Unit of observation:* One NSB decision event for one variety.

Every NSB decision linked to a variety, coded as an event (release, registration, extension, renaming, suspension, deferred denotification and others), with an English summary and a Bangla excerpt of the decision.

The file has 532 rows and 9 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `variety_id` | Stable identifier of a rice variety in the register and the key for joining every table in the archive. The number inside the identifier is the official series number of the variety, not a running count. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 1.00 |
| `variety_name` | Display name of the variety. | Free text. | 1.00 |
| `event_date` | Date of the NSB meeting at which the decision was taken. | ISO date YYYY-MM-DD. | 1.00 |
| `meeting_no` | NSB meeting number. | Integer. | 1.00 |
| `event_type` | Kind of decision on the variety, refined from decision_type by keyword rules on the variety's own text. | release; provisional_release; full_release_after_provisional; registration; extension_season_or_region; registration_renewal_or_extension; rename; suspension; import_permission; rejection; recommendation_pending/deferred; denotification_proposed_deferred; condition_change; status_change_other; gazette_notification (defined); cancellation/denotification and transfer_of_registration are defined but do not occur. | 1.00 |
| `detail` | English summary of the event, the meeting, and the season or region where given. | Free text. | 1.00 |
| `decision_text_excerpt` | Bangla source text of the decision, verbatim, cut to 400 characters. | Bangla text. | 1.00 |
| `source_file` | Path of the source file inside the archive, relative to the archive root. Every value in the archive can be traced to a page of a file under 02_raw/. | Relative path beginning '02_raw/'; the SHA-256 of each file is in bgd_sources.csv. | 1.00 |
| `page` | Page of the source file on which the value is printed, counted as the PDF page (1 = first page of the file), not the number printed on the page. | Integer page number, or a range 'a-b' when the item spans pages. Blank for web pages, spreadsheets and API records. | 1.00 |

## bgd_variety_status.csv

*Unit of observation:* One variety.

Legal status of each variety at February 2026 (after NSB meeting 115), with a plain-English basis and the date of the last event. It covers the register and the non-register names that have NSB decisions.

The file has 445 rows and 4 columns.

| column | meaning | values | coverage |
|---|---|---|---:|
| `variety_id` | Identifier of the variety: every register variety, plus names outside the register that have NSB decisions (for example Iratom-38, Jirashail and BRRI-shail); the basis column says 'not in the rice register' for these. | 'RICE-' followed by a key built from the official name by lib_keys.make_key: BR&lt;n&gt; (BR series, 1970-1993), BRRI_DHAN&lt;n&gt;, BRRI_HYBRID&lt;n&gt;, BINADHAN&lt;n&gt;, IRATOM&lt;n&gt;, BINASHAIL, BU_, BAU_ and GAU_ (universities), BRAC_DHAN&lt;n&gt;, PVT_ (other private inbreds), HYB_&lt;trade name&gt; (private and BADC hybrids), IR&lt;n&gt; and OLD_ (pre-BRRI introductions and old names). | 1.00 |
| `status_as_of_2026` | Legal status of the variety after the last NSB meeting in the archive (meeting 115, 5 February 2026). 'Active' is a legal status under the Seeds Ordinance and says nothing about whether seed is produced or sold. Status is never inferred from elapsed time; no registration is coded as expired. | active; suspended; unknown (no NSB approval on record, a time-limited approval with no recorded renewal, or an approval made conditional with no recorded outcome); cancelled (defined, but no case found). | 1.00 |
| `basis` | Plain-English statement of the decision or absence of decisions behind status_as_of_2026, naming the meeting and date. | Free text. | 1.00 |
| `last_event_date` | Date of the last NSB decision on the variety, or its register approval date when no decision is linked. | ISO date YYYY-MM-DD, or year only. | 1.00 |

