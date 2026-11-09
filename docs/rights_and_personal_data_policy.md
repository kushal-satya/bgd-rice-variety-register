# Rights and personal-data policy for the public release

Kushal Kumar, Cornell University. Draft of 10 November 2026, for confirmation by the principal investigator and the Cornell
University Library copyright office before any source document is redistributed. This policy governs the public website,
the public data tables, and the deposit of source documents (`deposit/`, built by `scripts/build_deposit.py`). The internal
edition (`site_internal/`, `05_output/final/`) is a research copy held by the author and is not covered by the public
release rules below.

## 1. What is being released, and under which licence

The register's own content, that is the tables in `05_output/final/`, the data dictionary, the changelog, the source
catalogue (`02_raw/CATALOGUE.csv`), the manifest of checksums and the documentation text of the website, is the author's
work and is released under the Creative Commons Attribution 4.0 International licence (CC BY 4.0). The scripts in
`scripts/` and the website code (`site/assets/`) are released under the MIT licence. The licence texts and the citation
metadata are in `release/`. Neither licence extends to the third-party source documents in `02_raw/`, which keep their own
rights; `release/NOTICE.md` says so in the form a downstream user will read.

Facts extracted from the sources (a variety's name, approval date, approving meeting, pedigree, yield) are not themselves
protected by copyright, and quoting short passages with page references for verification is ordinary scholarly practice.
The question this policy settles is narrower: which source files may be copied in full into a public deposit.

## 2. Rights classes of source files

Every file in `02_raw/` is assigned one class, mechanically from its folder and original web address
(`scripts/lib_archive.py`, function `rights_class`), and the class is recorded in the catalogue column `rights_class` with a
one-line `rights_basis`. Only files cited by the register are deposited.

| rights_class | which files | treatment in the public deposit |
|---|---|---|
| `gov_bd_official` | Official publications of the Government of Bangladesh and its statutory bodies: Bangladesh Gazette issues, acts, ordinances and rules, National Seed Board and Technical Committee minutes, SCA and Ministry variety lists, Department of Fisheries and Ministry notices, and the pages and publications of BRRI, BINA and BFRI (hosts ending in `gov.bd`, the national portal's object storage, `dpp.gov.bd`, and Internet Archive copies of these). | Redistributed in full, with the statement "Official publication of the Government of Bangladesh, reproduced unaltered for research and verification; no rights are claimed by the depositor." Pending confirmation (section 4). |
| `cgiar_open` | CGIAR outputs: CGSpace items and records, IRRI, WorldFish, HarvestPlus, AfricaRice, ASTI, GloMIP and SPIA (IAES) documents and pages. CGIAR's Open and FAIR Data Assets Policy makes most of these available under CC BY 4.0 or CC BY-NC-SA. | Redistributed in full, with the item's own licence where the item states one. Web pages of the centres (IRRI news, *Rice Today*, STRASA) carry site terms rather than an item licence and are to be checked (section 4). |
| `open_licence` | Items under an explicit open licence: Frontiers and PLOS articles (CC BY 4.0), Harvard Dataverse metadata records (CC0), Internet Archive CDX listings. | Redistributed in full, with the licence named. |
| `openalex_cc0` | OpenAlex API responses. OpenAlex releases its data under CC0. | Redistributed in full. |
| `crossref_metadata` | Crossref API responses that contain bibliographic metadata only. Crossref states that its metadata are facts free to reuse. | Redistributed in full. |
| `withhold` | Everything else: publisher PDFs and pages without an open licence, Crossref responses that contain abstracts (abstracts remain the publishers' copyright), news reports, company and university web pages, FAO, IAEA and Europe PMC documents whose licence was not verified, the SPIA Bangladesh Study 2025 replication files (public GitHub repository whose licence has not been verified; some files carry household identifiers) and the SPIA stocktake workbook copied from a local disk. | Not redistributed. The deposit lists each withheld file with its original address, Internet Archive address where one exists, SHA-256 and the reason (`deposit/sources/_withheld.csv`), so that a reader can obtain the same document and verify it is identical. |

A file moves from `withhold` to an open class only when its licence has been checked and recorded; the rule in
`lib_archive.rights_class` and this table are then changed together and the deposit is rebuilt.

## 3. Personal data

The register names people in two ways: officials acting in an official capacity, as printed in public records (members of
the National Seed Board, signatories of gazette notices and circulars, heads of research divisions), and authors and
breeders named in publications. The rule for the public edition is:

1. **Names and posts of officials, as printed in public records, are kept.** They are part of the public record of who
   decided what, and the register's account of each decision depends on them.
2. **Phone numbers and e-mail addresses of individuals are removed from every public file.** This covers mobile numbers in
   any script (Latin or Bangla digits, with or without +88), personal and professional e-mail addresses of named people
   (including corresponding-author addresses in article affiliations and directory addresses of named staff), and the
   project's own polite-pool address in API query URLs (`mailto=`). The columns `professional_email` and
   `professional_phone` are dropped from the public copy of `bgd_variety_people.csv`; the `contact_source_url` column stays,
   so a reader can reach the person through the official directory that published the contact.
3. **Institutional contacts stay.** Switchboard and office landline numbers printed on letterheads and contact pages, and the
   role mailboxes listed below, identify an office rather than a person and are kept, including in `bgd_institutions.csv`.
4. **The attendance sheets stay internal.** The NSB attendance table (`bgd_nsb_attendance.csv`), built from the signed
   attendance sheets with the contact details officials wrote on them, is published only in the internal edition, and its
   rows are never read by the public build.
5. **The internal edition is separate.** `05_output/final/` and `site_internal/` keep the full data for the research
   team; only the copies made by `scripts/build_site.py` (public site), `scripts/build_evidence_public.py` and
   `scripts/build_deposit.py` are public, and all three pass every text cell through `scripts/redact_personal.py`.

**Allow-list of institutional office e-mail addresses** (kept in public files; `OFFICE_EMAILS` in
`scripts/redact_personal.py` must match this list):

| address | office |
|---|---|
| dg@brri.gov.bd | Director General, BRRI |
| dr@brri.gov.bd | Director (Research), BRRI |
| head.breeding@brri.gov.bd, head.hybrid@brri.gov.bd, head.biotech@brri.gov.bd, head.grs@brri.gov.bd, head.gqn@brri.gov.bd, head.ard@brri.gov.bd, head.rfs@brri.gov.bd | Division heads' mailboxes, BRRI (Plant Breeding, Hybrid Rice, Biotechnology, Genetic Resources and Seed, Grain Quality and Nutrition, Adaptive Research, Rice Farming Systems; as printed in the BRRI directory) |
| dg@bina.gov.bd | Director General, BINA |
| dir@sca.gov.bd | Director, Seed Certification Agency |
| acsl@moa.gov.bd, cst@moa.gov.bd | Offices of the Ministry of Agriculture, as printed on NSB letterheads |
| dg@fisheries.gov.bd, cfeo@fisheries.gov.bd, adaqua@fisheries.gov.bd, ddaqua@fisheries.gov.bd, ddchingri@fisheries.gov.bd, ddext@fisheries.gov.bd | Director General and wing offices, Department of Fisheries |
| fisheries-5@mofl.gov.bd, fisheries-x@mofl.gov.bd | Fisheries sections, Ministry of Fisheries and Livestock |
| registrar@gau.edu.bd, registrar@ru.ac.bd | Registrars, Gazipur Agricultural University and University of Rajshahi |
| info@brac.net, info@aci-bd.com | General enquiry mailboxes, BRAC and ACI Limited |

Any other address, including OCR fragments of addresses, is replaced by `[e-mail removed]`; mobile numbers by
`[mobile removed]`. Adding an address to the list requires that it be printed as an office address on an official
letterhead or contact page, and that it name an office, not a person.

## 4. To be confirmed before the deposit is made public

These points are decisions or confirmations for the principal investigator and, where marked, the Cornell University Library
copyright services. Nothing has been uploaded anywhere.

1. **Licences** (PI): CC BY 4.0 for data and documentation, MIT for code, as drafted in `release/LICENSE`.
2. **Bangladesh government documents** (PI with Cornell copyright services): whether official Bangladesh publications may be
   redistributed in full from a United States repository. Bangladesh's Copyright Act 2023 replaced the Copyright Act 2000;
   the text of its provisions on official documents, gazettes and acts has not been checked for this project, and neither
   has the position of government research institutes' own publications (BRRI, BINA and BFRI factsheets, annual reports
   and web pages). If the answer is no for any group, that group is moved to `withhold` and only metadata, addresses and
   checksums are deposited.
3. **CGIAR web pages** (PI): whether IRRI, WorldFish and HarvestPlus web pages (as distinct from CGSpace items with a
   stated licence) may be redistributed, or should be withheld and represented by their Internet Archive copies.
4. **SPIA files** (PI with SPIA): the replication package is public on GitHub, but its licence has not been checked and some files carry household identifiers; they are withheld and the repository is cited instead. Confirm, or record the licence and move `SPIA_BIHS_2024_Varnames.xlsx` (the only cited file) to an open class.
5. **Literature harvest** (PI): whether the 512 MB of uncited literature API responses go into an optional separate
   deposit or are left out as reproducible from the harvest scripts.
6. **Personal-data rule** (PI): the rule in section 3, in particular dropping the BRRI directory contacts of named staff
   from the public tables and removing corresponding-author e-mail addresses from the public publications table.
