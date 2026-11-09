"""Write DS existing_datasets, sources_inventory and manifest CSVs (Phase 0)."""
import csv, os, hashlib

ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[1])
P = os.path.join(ROOT, "01_discovery", "_parts")


def w(name, cols, rows):
    with open(os.path.join(P, name), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(cols)
        for r in rows:
            assert len(r) == len(cols), (name, r[0], len(r))
            wr.writerow(r)
    print(name, len(rows))


DS_COLS = ["dataset_id", "title", "publisher_or_author", "url", "covers_rice", "covers_fish",
           "coverage_description", "years_covered", "n_records", "format", "license", "last_updated",
           "backbone_potential", "backbone_rationale", "cgiar_fields_present", "accessed", "notes"]
ds = [
 ["DS-D01", "SPIA Bangladesh Study 2025 - Appendix B Table 27 'Rice varietal releases'",
  "CGIAR SPIA (Singla, Ul Islam, Hassan, Monteiro, Stevenson, Emerick)",
  "https://iaes.cgiar.org/sites/default/files/pdf/SPIA_Bangladesh_Study_2025.pdf ; https://hdl.handle.net/10568/178983",
  "yes", "no",
  "Public rice releases BRRI (BR1..BRRI dhan106), BINA (Binadhan-4..26, Iratom 24), BRRI hybrid dhan; per variety: release year, IRRI direct contribution, indirect contribution (IR line as one parent), INGER entry, in SPIA DNA reference library, Sub1, saline, drought, HarvestPlus flags, IRRI/INGER entry used as parent(s). Report Table 4 gives 139 releases 1970-2023 (115 IRRI/HarvestPlus germplasm origin, 24 BRRI/BINA pure-line).",
  "1970-2023", "139 (per Table 4; table rows not yet counted)", "PDF text (table spans PDF pp.106-114, printed pp.94-102)",
  "CC BY 4.0 per repo LICENSE (osf.io/v9jtu); report itself not separately checked", "2025-12-17",
  "high",
  "Only source found that gives a full public-release list with explicit, documented CGIAR (IRRI/INGER/HarvestPlus) attribution and parent designations; 2023 cut-off, no private hybrids, no gazette/NSB citation, data source of pedigrees not stated in table; must be extracted from PDF and cross-checked against BRRI/BINA/SCA.",
  "IRRI direct; IRRI indirect (IR parent); INGER entry; IRRI/INGER parent designation; HarvestPlus; Sub1; reference-library flag",
  "yes", "Downloaded to 02_raw/spia_cgspace/. Definition (p.46 printed): lower bound = IRRI parents or grandparents; upper bound adds INGER entries. Also Appendix D-J give wheat, maize, potato, sweetpotato, lentil, groundnut, chickpea releases. Fish strains discussed in text only (GIFT, G3 rohu), no strain table."],
 ["DS-D02", "SPIA Bangladesh Study Stocktake Dataset (SPIA_BIHS_BD_Stocktake_2024_Final.xlsx)",
  "CGIAR SPIA", "https://hdl.handle.net/10568/185563", "yes", "yes",
  "Stocktake of CGIAR-related innovations: sheets Definitions, BD_innovation, BD_Policies, Not in BIHS. Rice section lists varieties by trait cluster as free text (e.g. 'BR-28---1994', 'BRRI dhan 72 (2015)'); fish section: genetically improved carp (G2 silver carp, G1 catla, G3 rohu 2020), GIFT dissemination years 1994,1996,1997,2005,2008,2009,2012.",
  "1970-2020 (rice entries)", "~60 innovation IDs; rice ~100 free-text variety lines", "XLSX",
  "dcterms.license 'Other'; Open Access", "issued 2025-12-17; sheet says 'Last update: 01/12/2023'; CGSpace item modified 2026-09-23",
  "low", "Public origin of the coordinator's local BAN_Stocktake file (final version). Useful as a CGIAR-attribution cross-check and for fish strain dissemination years, but rice entries are inconsistent free text (BR-28 for BRRI dhan28, duplicates across traits) with no pedigree.",
  "CGIAR-related efforts description per innovation; centre names", "yes", "Downloaded to 02_raw/spia_cgspace/. Bitstream CGSpace uuid ae197934-81b8-4497-8010-e6dfb55b0b92 (800,908 bytes)."],
 ["DS-D03", "SPIA-Bangladesh-Study-2025 replication package (GitHub)",
  "CGIAR-SPIA", "https://github.com/CGIAR-SPIA/SPIA-Bangladesh-Study-2025", "yes", "yes",
  "Stata replication: Data/DNA fingerprinting/{Barcode_reference_2024.xlsx, bangladesh_rice_assignment_results.xlsx, ref_clusters_no_hybrids_with_HH_Ids.csv, missing_barcode_list_replated.xlsx}; SurveyCTO codebooks with 'paddy' choice list (185 codes: BR1-BR36 with names, BRRI dhan up to 106, BINA 1-25, BRRI hybrid 1-8, private hybrids, local names), strain_tilapia (Chitralada, GIFT, GST, GIFT-World Fish, GIFU, FaST), strain_rohu (G0-G4); BIHS questionnaires 2024.",
  "survey 2024; codes to BRRI dhan106", "214 files", "XLSX/CSV/DTA/PDF on GitHub",
  "BSD-3 (code) + CC BY 4.0 (data) per osf.io/v9jtu", "pushed 2026-10-06 (repo created 2025-11-13)",
  "low", "Public origin of the coordinator's local SPIA replication files. Code lists are survey vocabularies (useful for name-matching and fish strain categories), not a release register; DNA reference library covers ~106 reference seed samples only.",
  "none explicit in code lists (CGIAR flags are in report Table 27)", "yes",
  "Repo README; tree listed via GitHub API; only README, License and Codebook/SPIA_BIHS_2024_Varnames.xlsx read (scratch copy, not archived)."],
 ["DS-D04", "TRIVSA rice data (Tracking Improved Varieties in South Asia) - Releases sheet",
  "IRRI (Yamano, Pandey) via ASTI/IFPRI", "https://www.asti.cgiar.org/sites/default/files/trivsa/TRIVSA-Rice-Data.xlsx ; https://www.asti.cgiar.org/trivsa", "yes", "no",
  "Rice releases for BD, Bhutan, India states, Nepal, Sri Lanka; 86 fields incl. breeding line name, release name, alternative name, year, method (hybridization/introduction/mutation), parents, female/male parent, institution, country of origin (IRRI etc.), ecosystem, season, traits, INGER designation/IET. Bangladesh: 72 rows 1966-2010; institution BRRI 43, IRRI 16, BINA 7, BAU 2, BSMRAU 1; parents filled 69/72.",
  "1966-2010 (BD)", "1510 releases total; 72 Bangladesh", "XLSX",
  "not stated on ASTI page; Dataverse copy CC BY-NC-SA 4.0", "file Last-Modified 2020-04-06 (data compiled c.2010-2013)",
  "medium", "Best structured historical backbone with pedigree and IRRI origin fields; ends 2010 and lists IR8/IR20/IR5 introductions as releases; must be extended with SPIA Table 27 and BRRI/BINA/NSB sources for 2011+.",
  "Country of origin = IRRI; Institution = IRRI; parents; INGER designation", "yes", "Downloaded to 02_raw/asti_trivsa/ (445,810 bytes)."],
 ["DS-D05", "TRIVSA dataset on Harvard Dataverse (IRRI Dataverse)",
  "Yamano, Takashi and Pandey, Sushil (IRRI)", "https://doi.org/10.7910/DVN/26301", "yes", "no",
  "8 files incl. 'Varietal releases-Data.xlsx' (312 KB), CodingManualTRIVSA.xlsx, expert estimates, HH and community surveys; metadata note: 1510 released varieties compiled.",
  "collection from 2010", "1510", "XLSX", "CC BY-NC-SA 4.0", "version released 2025-02-18 (deposited 2014-05-29)",
  "medium", "Same content family as DS-D04; Dataverse copy is gated by a guestbook form, so use the ASTI copy or have a person fill the guestbook manually.",
  "as DS-D04", "blocked", "Download returned 'required Guestbook response for guestbookID 40'; not submitted (form with personal data)."],
 ["DS-D06", "HarvestPlus Database of Biofortified Crops Released (BCR)",
  "HarvestPlus", "https://bcr.harvestplus.org/ (JSON: /api/v1/details_varieties_released)", "yes", "no",
  "All biofortified releases by country with variety, release year, breeder organisation, status, fields for pedigree (NA for BD). Bangladesh 21 rows: zinc rice BRRI dhan62 (2013), 64 (2014), 72 (2015), 74 (2015), 84 (2017), 100 (2021), 101 (2021), 102 (2022), Binadhan-20 (2017), BU Aromatic Dhan-2 (2016), BU Aromatic Hybrid Dhan-1 (2016); plus lentil, wheat, OFSP.",
  "2010-2022 (BD)", "498 total; 21 BD; 11 BD zinc rice", "API (JSON) / HTML",
  "not stated (c) HarvestPlus 2004-2022", "updated_at null; site footer 2022",
  "low", "Authoritative only for the HarvestPlus-supported subset; useful to set the HarvestPlus attribution flag. Discrepancies to check: BRRI dhan100 2021 here vs approval 2020 on BRRI Rice Profile; BRRI dhan101 listed as zinc rice.",
  "breeder_organization (HARVESTPLUS/BRII/BINA/BSMRAU)", "yes", "robots allows all; JSON read into scratch only, not archived."],
 ["DS-D07", "BRRI Rice Profile portal (ব্রি - রাইস প্রোফাইল)",
  "Bangladesh Rice Research Institute", "https://riceprofile.brri.gov.bd/varieties", "yes", "no",
  "Bangla variety profile pages /varieties/{id} (ids up to 107; ~9 list pages x 12): season, cropping pattern, land type, area, introduction text with breeding line (কৌলিক সারি), cross, year approved for cultivation, traits, yield, duration; archive PDFs.",
  "BRRI varieties to at least BRRI dhan100+", "~107 pages (not counted)", "HTML (Bangla)",
  "not stated", "unknown",
  "medium", "Official institute source with pedigree text per variety for BRRI only; free text in Bangla, needs scraping and parsing; no BINA/private/hybrid coverage seen; probably better handled by the BRRI-focused agent.",
  "none (cross text sometimes names IR lines)", "yes", "robots allows all; old URL /list.php is 404."],
 ["DS-D08", "50 years of rice breeding in Bangladesh: genetic yield trends - Table 1 and Suppl. Table S1",
  "Rahman, Malik, Kabir et al. (Theor Appl Genet 136:18, 2023)", "https://doi.org/10.1007/s00122-023-04260-x ; PMC9867671", "yes", "no",
  "BRRI inbred releases 1970-2020 by season used in trials (41 Boro/winter, 45 Aman/monsoon) with release year.",
  "1970-2020", "86 varieties", "PDF table + ESM", "CC BY 4.0", "2023-01",
  "low", "Release-year cross-check for BRRI only; no pedigree, no BINA, trial data on request only.", "none", "yes", ""],
 ["DS-D09", "Villanueva, Enriquez & Capilit 2022 - IRG impact on rice farming in Bangladesh, Additional file 1 Tables S1-S2",
  "IRRI (CABI Agric Biosci 3:71)", "https://doi.org/10.1186/s43170-022-00113-7 ; https://hdl.handle.net/10568/126982", "yes", "no",
  "53 varieties adopted in 2015 wet season (43 inbred, 10 hybrid) with IRG progenitor contributions computed from IRIS pedigrees; 38/43 inbreds have a definite IRG progenitor.",
  "varieties in use 2015", "53", "PDF + supplementary file", "CC BY 4.0", "2022-12",
  "low", "Shows IRIS holds pedigrees for BD inbreds (not hybrids) and gives a method for genetic attribution; not a release list.",
  "IRG progenitor contribution (definite/possible)", "yes", "Main PDF read via CGSpace bitstream; supplementary file not opened."],
 ["DS-D10", "Kretzschmar et al. 2018 Sci Rep 8:14920 - DNA fingerprinting at farm level, Supplementary spreadsheets A-D",
  "IRRI", "https://doi.org/10.1038/s41598-018-33080-z", "yes", "no",
  "Breeders' reference set of BRRI/BINA varieties (Aman 2015), released 1980 (BR10, BR11) to 2011; farmer samples.",
  "reference varieties 1980-2011", "small reference set", "XLSX supplements", "CC BY 4.0", "2018",
  "none", "Reference panel, not a release register.", "none", "metadata_only", "Full text via Europe PMC API; PMC direct served reCAPTCHA."],
 ["DS-D11", "WorldFish: Dataset on the dissemination of genetically improved carp in Bangladesh",
  "Benzie, Yeasin, Ali, Fakhruddin, Dam Lam, Hamilton (WorldFish)", "https://doi.org/10.7910/DVN/SVNV6B", "no", "yes",
  "G3 rohu dissemination from hatcheries and nurseries to farmers 2022-2023.", "2022-2023", "1 xlsx (393,781 bytes)", "XLSX", "CC BY 4.0", "2025-05-19",
  "none", "Adoption/dissemination data for one strain, not a strain register; useful for G3 rohu release/dissemination dates.", "WorldFish strain (G3 rohu)", "metadata_only", ""],
 ["DS-D12", "WorldFish: Dissemination of Genetically Improved Seed (Bangladesh, 2025)",
  "Yeasin, Fakhruddin, Hamilton (WorldFish)", "https://doi.org/10.7910/DVN/BFV5P1", "no", "yes",
  "2025 G3 rohu seed sales by hatcheries; G19 GIFT cohort mating data at EON Group (received from WorldFish Penang 2025).", "2025", "3 xlsx", "XLSX", "CC BY 4.0", "2025-12-11",
  "none", "Documents G19 GIFT import in 2025 and G3 rohu dissemination; not a register.", "WorldFish strain/generation", "metadata_only", ""],
 ["DS-D13", "BIHS 2018-2019 (and 2011-12, 2015) questionnaires and codebooks",
  "IFPRI", "https://doi.org/10.7910/DVN/NXKLZJ ; https://doi.org/10.7910/DVN/BXSYEL ; https://doi.org/10.7910/DVN/OR6MHT", "yes", "yes",
  "Household questionnaires (EN and BN PDF) and codebooks; crop module carries a rice variety code list and fish species codes.", "2011-2019", "n/a", "PDF/XLS/TAB", "IFPRI Terms of Use (Dec 2025)", "2021-02-04",
  "none", "Survey vocabulary only; coordinator already has BIHS locally.", "none", "metadata_only", "Variety code list not opened in this phase."],
 ["DS-D14", "CGIAR varietal release and adoption database (11 CGIAR crops x 15 countries, 2009-2015)",
  "CGIAR Big Data platform post (publisher unclear)", "https://bigdata.cgiar.org/newly-released-database-on-varietal-release-and-adoption-estimates-for-eleven-cgiar-mandated-crops-across-15-countries/", "unknown", "unknown",
  "Announced database of varietal release and adoption estimates; country list not confirmed.", "2009-2015", "unknown", "unknown", "unknown", "unknown",
  "none", "Could not open (two 60 s timeouts); BD coverage unconfirmed; probably the SPIA/DIIVA-style Asia follow-up.", "unknown", "blocked", "Retry manually."],
 ["DS-D15", "Rice image classification datasets (Mendeley 2fgv99854n, tx277syzhm, khdg28v5d7, 3mn9843tz2; Kaggle RiceNet-62; HuggingFace AgML)",
  "various university groups", "https://data.mendeley.com/datasets/2fgv99854n", "yes", "no",
  "Images of 8-62 named BD rice varieties; no release, pedigree or CGIAR metadata.", "2024-2026", "n/a", "JPG", "various (CC BY)", "2024-2026",
  "none", "No release metadata.", "none", "metadata_only", "Found via WebSearch and Google Dataset Search (41 hits, all image sets)."],
]
w("DS_existing_datasets.csv", DS_COLS, ds)

SRC_COLS = ["source_id", "title", "publisher", "url", "language", "date", "format", "coverage",
            "authority_rank", "robots_txt_status", "wayback_available", "access_notes", "notes"]
src = [
 ["DS-S01", "SPIA Bangladesh Study 2025: Updating the Green Revolution", "CGIAR SPIA", "https://iaes.cgiar.org/sites/default/files/pdf/SPIA_Bangladesh_Study_2025.pdf", "en", "2025-12-17", "PDF text", "Appendix B Table 27: 139 rice releases 1970-2023 with IRRI/INGER/HarvestPlus flags and parents; Appendices D-J other crops; GIFT and G3 rohu text", "4_cgiar_record", "not_checked", "yes:2026-2026", "14.7 MB; WebFetch size limit exceeded, downloaded directly", "Also at hdl 10568/178983"],
 ["DS-S02", "SPIA Bangladesh Study Stocktake Dataset", "CGIAR SPIA", "https://hdl.handle.net/10568/185563", "en", "2025-12-17", "XLSX", "CGIAR-related innovations stocktake (crops, fish, policies)", "4_cgiar_record", "allowed", "not_checked", "CGSpace REST API (/server/api not disallowed; /search disallowed)", "Public origin of local BAN_Stocktake_July_2023.xlsx (final version, 'Last update 01/12/2023')"],
 ["DS-S03", "CGIAR-SPIA/SPIA-Bangladesh-Study-2025 (GitHub)", "CGIAR SPIA", "https://github.com/CGIAR-SPIA/SPIA-Bangladesh-Study-2025", "en", "2025-11-13 to 2026-10-06", "other", "Replication package incl. DNA fingerprinting reference and assignment files, SurveyCTO codebooks", "4_cgiar_record", "not_checked", "not_checked", "GitHub API, unauthenticated", "Public origin of local SPIA replication package; LICENSE at https://osf.io/v9jtu"],
 ["DS-S04", "TRIVSA rice data (ASTI tool)", "IRRI / ASTI-IFPRI", "https://www.asti.cgiar.org/sites/default/files/trivsa/TRIVSA-Rice-Data.xlsx", "en", "2020-04-06 (file); data c.2010-2013", "XLSX", "72 BD rice releases 1966-2010 with parents and institution", "4_cgiar_record", "allowed", "yes:2016-2023", "direct download", ""],
 ["DS-S05", "Tracking Improved Varieties in South Asia (TRIVSA) - Harvard Dataverse", "IRRI", "https://doi.org/10.7910/DVN/26301", "en", "2014-05-29 / v2025-02-18", "XLSX", "releases, expert estimates, surveys for 5 South Asian countries", "4_cgiar_record", "no_robots", "not_checked", "Guestbook required for file download (blocked, manual)", "Harvard Dataverse robots.txt returned HTTP 202 with empty body"],
 ["DS-S06", "HarvestPlus Database of Biofortified Crops Released", "HarvestPlus", "https://bcr.harvestplus.org/", "en", "c.2022", "API", "11 BD zinc rice + lentil/wheat/OFSP", "4_cgiar_record", "allowed", "yes:2022-2026", "JSON at /api/v1/details_varieties_released", ""],
 ["DS-S07", "BRRI Rice Profile (ব্রি - রাইস প্রোফাইল)", "BRRI", "https://riceprofile.brri.gov.bd/varieties", "bn", "unknown", "HTML", "BRRI variety profiles with breeding line, cross, approval year", "3_institute_page", "allowed", "no", "public pages; login only for comparison/chat tools", "Bangla terms seen: জাত, কৌলিক সারি, সংকরায়ণ, চাষাবাদের জন্য অনুমোদিত হয়"],
 ["DS-S08", "Rahman et al. 2023 50 years of rice breeding in Bangladesh: genetic yield trends", "Theor Appl Genet", "https://doi.org/10.1007/s00122-023-04260-x", "en", "2023-01", "PDF text", "BRRI releases 1970-2020 (Table 1)", "5_peer_reviewed", "not_checked", "not_checked", "open access (PMC9867671; CGSpace 10568/132723)", ""],
 ["DS-S09", "Villanueva, Enriquez & Capilit 2022 The impact of the international rice genebank (IRG) on rice farming in Bangladesh", "CABI Agriculture and Bioscience", "https://doi.org/10.1186/s43170-022-00113-7", "en", "2022-12", "PDF text", "53 adopted varieties, IRIS pedigrees, IRG progenitor shares", "5_peer_reviewed", "not_checked", "not_checked", "publisher site redirects to Springer IdP; CGSpace copy 10568/126982 works", ""],
 ["DS-S10", "Kretzschmar et al. 2018 DNA fingerprinting at farm level maps rice biodiversity across Bangladesh", "Scientific Reports", "https://doi.org/10.1038/s41598-018-33080-z", "en", "2018", "PDF text", "Aman 2015 DNA fingerprinting; breeders' reference set", "5_peer_reviewed", "not_checked", "not_checked", "PMC served reCAPTCHA; Europe PMC API works", ""],
 ["DS-S11", "Yamano et al. 2017 DNA fingerprinting for variety identification ... submergence-tolerant rice in Bangladesh (AgEcon 284813) and companion 284814", "IRRI / AgEcon Search", "https://doi.org/10.22004/ag.econ.284813", "en", "2017", "PDF text", "1302 seed samples, 544 farmers 2014-15", "6_secondary", "allowed", "not_checked", "WebFetch got HTTP 403; robots allows /record with crawl-delay 5", "conference paper"],
 ["DS-S12", "Raitzer et al. 2015 Is Rice Improvement Still Making a Difference? ... varieties released 1989-2009 in Bangladesh, Indonesia and the Philippines", "CGIAR ISPC/SPIA", "https://hdl.handle.net/10568/128929", "en", "2015-06", "PDF text", "BD releases 1989-2009 with IRRI contribution (not opened)", "4_cgiar_record", "allowed", "not_checked", "not opened in Phase 0", "Likely contains a release-level IRRI ancestry table; check in Phase 1"],
 ["DS-S13", "Dikitanan et al. 2022 Assessing returns to research investments in rice varietal development: Philippines and Bangladesh", "Global Food Security", "https://doi.org/10.1016/j.gfs.2022.100646", "en", "2022-06", "PDF text", "BD rice varietal development returns; likely uses an IRRI-related release classification", "5_peer_reviewed", "not_checked", "not_checked", "CC BY 4.0, CGSpace 10568/119865; not opened", ""],
 ["DS-S14", "Pandey et al. (eds) 2012 Patterns of adoption of improved rice varieties and farm-level impacts in stress-prone rainfed areas in South Asia", "IRRI", "https://ageconsearch.umn.edu/record/164467/files/Patternsofadoption.pdf", "en", "2012", "PDF text", "includes Bangladesh chapter; variety lists not verified", "4_cgiar_record", "allowed", "not_checked", "not opened", ""],
 ["DS-S15", "Hossain, Bose & Mustafi 2006 Adoption and productivity impact of modern rice varieties in Bangladesh", "The Developing Economies 44(2)", "https://ideas.repec.org/a/bla/deveco/v44y2006i2p149-166.html", "en", "2006", "PDF text", "MV adoption, variety replacement", "5_peer_reviewed", "disallowed:/cgi-bin/", "not_checked", "IDEAS search CGI disallowed; item page fine", ""],
 ["DS-S16", "WorldFish G3 rohu and GIFT documents (brief 20.500.12348/4186; CGIP progress report 2025 6883; G3 rohu adoption 2025 6976; GIFT M&E reports 6031, 6032; Hossain 2014 tilapia BD 177)", "WorldFish", "https://digitalarchive.worldfishcenter.org/", "en/bn", "2014-2026", "PDF text", "GIFT and G3 rohu introduction/dissemination history in BD", "4_cgiar_record", "disallowed:/search", "not_checked", "DSpace REST /server/api used (not disallowed)", "Bangla G3 rohu brief 20.500.12348/4366"],
 ["DS-S17", "WorldFish G3 rohu dissemination datasets", "WorldFish", "https://doi.org/10.7910/DVN/SVNV6B ; https://doi.org/10.7910/DVN/BFV5P1", "en", "2025", "XLSX", "G3 rohu dissemination 2022-23 and 2025; G19 GIFT at EON 2025", "4_cgiar_record", "no_robots", "not_checked", "metadata only", ""],
 ["DS-S18", "Genesys PGR / IRRI GRIN-Global accession records (e.g. 10.18730/4X8KK)", "Crop Trust / IRRI", "https://www.genesys-pgr.org/", "en", "live", "database", "IRG accessions of BD origin; pedigree field sometimes present; no release name/year field", "6_secondary", "allowed", "not_checked", "gringlobal.irri.org did not respond; snp-seek.irri.org robots 404 (GitHub Pages)", "Not a release register"],
 ["DS-S19", "USDA GRIN (npgsweb.ars-grin.gov)", "USDA ARS", "https://npgsweb.ars-grin.gov/", "en", "live", "database", "not checked", "6_secondary", "disallowed:/ for ClaudeBot and AI crawlers; /search/ for all", "not_checked", "not accessed (robots)", ""],
 ["DS-S20", "BIHS 2018-19 questionnaires and codebooks", "IFPRI", "https://doi.org/10.7910/DVN/NXKLZJ", "en/bn", "2021-02-04", "PDF text", "rice variety code list in crop module", "6_secondary", "no_robots", "not_checked", "IFPRI terms of use; not downloaded", ""],
 ["DS-S21", "HarvestPlus Bangladesh country profile PDFs (2022, 2024)", "HarvestPlus", "https://harvestplus.org/wp-content/uploads/2024/09/Bangladesh.pdf", "en", "2020-2024", "PDF text", "counts of zinc rice/wheat/lentil releases", "4_cgiar_record", "not_checked", "not_checked", "Illustrator PDF; fetch tool could not extract text", ""],
]
w("DS_sources_inventory.csv", SRC_COLS, src)

MAN_COLS = ["file_path", "source_url", "archived_url", "download_date", "sha256", "file_type", "agent", "notes"]
files = [
 ("02_raw/spia_cgspace/SPIA_BIHS_BD_Stocktake_2024_Final.xlsx", "https://cgspace.cgiar.org/server/api/core/bitstreams/ae197934-81b8-4497-8010-e6dfb55b0b92/content", "", "xlsx", "SPIA BD stocktake final; hdl 10568/185563"),
 ("02_raw/spia_cgspace/SPIA_Bangladesh_Study_2025.pdf", "https://iaes.cgiar.org/sites/default/files/pdf/SPIA_Bangladesh_Study_2025.pdf", "ARCH_PDF", "pdf", "SPIA report; Appendix B Table 27 rice releases"),
 ("02_raw/asti_trivsa/TRIVSA-Rice-Data.xlsx", "https://www.asti.cgiar.org/sites/default/files/trivsa/TRIVSA-Rice-Data.xlsx", "ARCH_TRIVSA", "xlsx", "TRIVSA rice releases; 72 BD rows"),
]
arch = {}
if os.path.exists(os.path.join(P, "_DS_wayback.txt")):
    for line in open(os.path.join(P, "_DS_wayback.txt"), encoding="utf-8"):
        k, v = line.rstrip("\n").split("\t")
        arch[k] = v
rows = []
for fp, url, a, ft, note in files:
    h = hashlib.sha256(open(os.path.join(ROOT, fp), "rb").read()).hexdigest()
    rows.append([fp, url, arch.get(a, ""), "2026-10-06", h, ft, "DS", note])
w("DS_manifest.csv", MAN_COLS, rows)
