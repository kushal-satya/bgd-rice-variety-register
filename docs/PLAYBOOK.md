# Playbook: building a national variety register for adoption research
# Distilled from the Bangladesh Rice Variety Register (v1.1.1, Oct 2026). Written as a brief you can hand to an agent
# or a research assistant for another country. Lines marked [IN] are India-specific pointers to verify, not facts.

## 0. Goal and unit
- Unit of observation: one officially approved variety (release, notification or registration by the national body),
  plus pre-system introductions if they are still grown. One stable identifier per variety, never renamed.
- Deliverable: a register (one row per variety) + long-format evidence behind every cell + decision-level table +
  crosswalk to the survey codes you will actually merge on + a website that is a data publication, not a dashboard.
- Decide up front: approval date = date of the approving meeting; notification/gazette date kept as a separate column.

## 1. Folder layout (keep it; the build reads these paths)
  00_admin/        plan.md, status.md, decisions_log.md (EVERY judgement call, dated), agent briefs, this playbook
  01_discovery/    search_log.csv, sources_inventory.csv, approval_systems_memo.md, crawl_plan.md
  02_raw/          every source file, unchanged, + manifest.csv (file_path, source_url, archived_url, download_date, sha256)
  03_extracted/    OCR text per page (txt + tsv word confidences), text layers, tables
  04_working/      evidence_*.csv (long format), corrections, key maps, meeting-date key, manual TSVs (all declared)
  05_output/       assembled tables; 05_output/final/ = the release (CSV, XLSX, DATA_DICTIONARY.md, CHANGELOG.md)
  06_validation/   qa_checks.md, spot checks, count reconciliation, link audit, reviewer memos
  scripts/         one entry point: rebuild_all.sh runs everything in dependency order
  site/            index.html, content/text.md (ALL prose), assets/, data/ ; site_internal/ generated if needed

## 2. Phases, each ending in a STOP for the PI
  Phase 0 Discovery: who approves what, under which law; which lists exist; which are primary (minutes) vs secondary.
  Phase 1 Crawl plan: per source, URL pattern, robots.txt verdict, expected pages, manual-download list.
  Phase 2 Pilot: 10-20 varieties end to end (fetch -> OCR -> evidence -> assemble -> validate). Fix the pipeline here.
  Phase 3 Full build + validation + external review + revision + release.

## 3. Fetching rules (non-negotiable)
- Respect robots.txt and site terms; if blocked, add to the manual list. No alternate user agents, mirrors, proxies.
- 2-3 s between requests to one host (8 s for archive.org); one worker per host; never re-download a file in the manifest.
- Keep a local copy AND a Wayback snapshot of every source; record both URLs and the SHA-256.
- Broken TLS chains on government hosts: allowlist those hosts explicitly (NO_VERIFY set) and log it.
- API keys (OpenAlex etc.) only via environment variable, sent as a header, never in URLs, manifests or outputs.
- Government PDFs often live on object-storage URLs that rotate: archive immediately, cite the archived copy.

## 4. Reading scanned documents
- Tesseract 5 + tessdata_best for the script (ben / hin / tel / tam / kan ...), psm 6, 300 dpi, keep the TSV word confidences.
- Legacy encodings (Bijoy/SutonnyMJ in Bangla; Krutidev / Shusha / Shree-Lipi in Indian scripts [IN]) need a
  font-aware converter: convert only spans whose font is the legacy font; never convert Latin runs (codes like HG-202 break).
- Repair known script errors after conversion (e.g. reph position) and ADD A QA CHECK for each repair.
- Rule: a number or date read by OCR is admitted only if (a) it matches an independent key (meeting number -> date) or
  (b) it was confirmed on a crop of the page image, or (c) two independent sources agree. Everything else stays in
  evidence as 'unvalidated' and never reaches the register. Report how many readings were dropped.
- Say in the methods WHO read the page images (human double entry vs vision model) and report audit error rates.

## 5. Evidence first, register second
  evidence_<AGENT>.csv columns:
  pilot_key, field, value, value_raw, source_id, source_title, authority_rank, local_file, page, locator,
  method (html|pdf_text|ocr|bijoy2unicode|api_json|xlsx|visual_check), validation (key_check|visual_check|two_source|''),
  confidence, notes
- One row per (variety, field, source). Quote the source text in value_raw. Never overwrite evidence; correct it with
  evidence_corrections*.csv (agent, pilot_key, field, value, action=drop|refield|replace, new_field, reason, new_value).
- Reviewer corrections use agent REV*; the assembler applies them to the matching value whoever recorded it.
- assemble.py picks one value per field by explicit precedence:
    authority rank: 1 primary legal (minutes, gazette) > 2 official list > 3 institute > 4 CGIAR/international > 5 papers
    dates: earliest validated within the best rank; approval_reference must name the meeting whose date was chosen
    codes vs labels: a breeding-line CODE beats a prose label; prose goes to a note column, never to the pedigree
    every losing value -> conflicts.csv with file and page; register gets conflict_fields + conflict_note
- Pedigree hygiene: origin statements, trial codes and vague notes are NOT pedigrees; route them to their own columns.
- One resolved date per meeting (meeting_key_resolved.csv) with the basis; never a set of candidate dates.
- Merged identities go through key_remap.csv (old_key, new_key, reason) so every table follows.

## 6. CGIAR (or any donor-lineage) coding
  1 CGIAR line released directly | 2 CGIAR parent or ANY documented earlier ancestor | 3 collaboration/funding only
  4 traceable pedigree with no CGIAR element | 5 unknown.  Strongest documented link wins. Never from name similarity.
- Build a parent->child edge table from the pedigree strings ('/', '//', '*n' backcross, 'mutant of', 'somaclone of').
- Parents that are register varieties pass on their ancestry; mutants/somaclones inherit the source variety's ancestry.
- Publish depth_to_cgiar so narrower definitions (parent/grandparent only, as SPIA) can be recovered.
- Keep the CGIAR centre's own statements (SPIA, Villanueva-style genebank shares, Raitzer weights) in a separate
  'independent' column: cross-check, never source of the code.
- Unit tests for the coding rules; a QA check that no breeding line is shared by two ids without a stated reason.

## 7. Trait tags (only if you need them)
- Keyword rules in both scripts, documented in code. A stress tag needs a tolerance word NEXT TO the stress term;
  a disease tag needs a resistance word; negations ('not tolerant', 'non-saline') never tag; 'medium slender' is not
  'fine'; 'short duration' is dropped above a season-specific day limit; donor flags count only when 'Y';
  screening codes (HR/R/MR vs S) by their own rule.
- Record the column that produced each tag, and a 'trait_text_available' flag so 'no tag' != 'no trait'.
- Say that tags follow documentation, which grows over time.

## 8. Analysis-ready columns (what a regression needs)
  season dummies; numeric duration min/max; numeric yield; ecosystem_std; establishment; photoperiod; grain_class;
  breeding_method; recommended region mapped to admin units (district -> state/division); developer_std + developer_type;
  status_as_of_<date> with basis; events table (extension, rename, suspension, withdrawal proposed/decided, renewal).
- Blank means 'not stated', never zero. Document this in every table's intro.

## 9. Crosswalk to surveys (the part researchers actually merge on)
- Collect every variety code list: each survey round's value labels/choice lists, DNA reference libraries.
- Match on the printed LABEL, never on the code number (code numbers change between rounds and between questionnaire drafts).
- match_type: exact_code_name | normalised_name | alias | brand_family (list all members, no single id) |
  not_approved_variety (give a stable NA_ pseudo-id: Swarna, Miniket...) | generic_label | unmatched.
- Manual overrides in their own file with reasons; a report listing every unmatched label.

## 10. Validation (report RESULTS, not procedures)
- 25-30 automated integrity checks (unique ids, required fields, date <= today, gazette >= approval, codes in range,
  no control chars, no script-repair artefacts, counts reconcile to external lists, no shared codes across ids...).
- Two independent spot checks of random values against page images (stratified; report match/partial/mismatch and
  the 95% bound implied by zero errors). Fix partials, re-run.
- Count reconciliation against every external list (national institute count, CGIAR list, ministry hybrid list) with the
  named exceptions explained one by one.
- Link audit: DOIs via doi.org handle API; all URLs HEAD/GET politely; map dead links to archived copies.
- External review by 3 personas (applied economist / data editor / data-journal editor) BEFORE release; revise; CHANGELOG.

## 11. Reproducibility
- requirements.txt with pinned versions; Tesseract version + language files; tool paths from env vars, not hard-coded.
- Any failure (OCR, fetch, parse) stops the run; no silent passes.
- Every manual input declared (file, author, date, basis). rebuild_all.sh is the only entry point.
- Data dictionary generated from a CSV (table, column, label, type, meaning, values, source_and_derivation, coverage)
  and re-rendered on every build with a header check against the real files.
- Personal data (attendance sheets, contact numbers) never in evidence_*; separate folder, separate build, internal
  edition only; public edition redacts mobiles/webmail and omits the table.

## 12. Website (data publication, not dashboard)
- Static: index.html + content/text.md (every sentence editable; {{placeholders}} computed from the data) + data/ CSVs.
- Views with a sticky nav (Overview, Figures, Register, Surveys, Fish/other, Methods, Data & references); never one scroll.
- Register: filters, bilingual search ranking name matches first, permalink per variety (#ID), record view with
  traits, parents (linked), generations to donor line, status + later decisions, survey codes, how verified, disagreements.
- Figures: counts not shares; mark partial periods; hatch = seed type, colour = sector; negated/absent documented.
- Methods page: definitions, completeness table by seed type, disagreements by field, who read the scans, limitations,
  versioning. Citation + availability statement + files table with unit of observation, rows, columns, MB.
- No KPI tiles, pills, gradients; system font; hairline tables; one accent; both light and dark themes.
- Test: render every record in a headless browser (no errors, no 'undefined'); phone width with no horizontal scroll.

## 13. Writing rules
- Full sentences, researcher's voice. Report numbers with their denominators. Claim only what the data hold
  (coverage is uneven: say so in the first paragraph). No README bullet lists on the public page.

## 14. India: where to start [IN - verify each]
- Approval: Central Sub-Committee on Crop Standards, Notification and Release of Varieties (CVRC) for central releases;
  State Variety Release Committees (SVRC) for state releases; notification under s.5 of the Seeds Act 1966 by Gazette of
  India S.O. numbers (egazette.gov.in). Hybrids from private firms: 'truthfully labelled' seed needs no release;
  registration under PPV&FR Act 2001 is a separate register (plantauthority.gov.in) - keep the two apart.
- Lists: Seednet (seednet.gov.in) notified-variety lists; ICAR-IIRR (rice) and crop-specific AICRP annual reports;
  ICAR 'Varieties notified' compendia; state agricultural university release lists. Expect name/code mismatches
  (IET numbers vs release names vs local names) - IET number is the key.
- Surveys to crosswalk: NSSO/SAS variety fields, ICRISAT VDSA, CCAFS/SPIA DNA-fingerprinting studies (Bihar, Odisha),
  state crop-cutting lists, your own questionnaire drafts.
- Scripts: Hindi/Devanagari gazettes often in legacy fonts (Krutidev) -> font-aware conversion; English S.O. notices
  are machine-readable; regional-language SVRC minutes are the scanned problem.
- Dates: approval = CVRC meeting date; notification = S.O. date; both columns, earliest gazette wins for 'notified'.
