#!/bin/bash
# Full rebuild from archived sources and agent evidence, in dependency order. Logs to logs/rebuild_all.log.
set -e
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
run(){ echo "== $*"; python "$@"; }
run scripts/merge_manifest.py
run scripts/phase2_COORD_cgiar.py
run scripts/phase3_COORD_cgiar_web.py
run scripts/phase3_fix_bijoy_latin.py
run scripts/phase3_fix_provisional.py
run scripts/phase3_F5L_corpus.py        # OCR page corpus (from cached OCR; no network)
run scripts/phase3_F5M_build.py         # NSB decisions table and evidence_F5M.csv
run scripts/phase3_L1_build.py          # literature, people, institutions (from harvested files; no network)
run scripts/assemble.py --stage full
run scripts/phase2_LOC_local_names.py
run scripts/phase3_LOC_codebook_names.py
run scripts/phase2_local_names.py full
run scripts/phase3_count_reconciliation.py
run scripts/export_xlsx.py full
run scripts/cgiar_tables.py
run scripts/make_final.py
run scripts/build_pedigree.py
run scripts/build_status_events.py
run scripts/build_crosswalk.py
run scripts/conflicts_report.py
run scripts/build_evidence_public.py
run scripts/make_final.py
run scripts/write_dictionary.py
run scripts/build_datapackage.py
run scripts/validate_datapackage.py
run scripts/build_attendance.py
run scripts/build_site.py
run scripts/check_figures.py          # every figure recomputed independently from the data
echo "REBUILD OK"
