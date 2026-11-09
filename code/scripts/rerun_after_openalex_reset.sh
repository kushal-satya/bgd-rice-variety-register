#!/bin/bash
# Wait for the OpenAlex daily budget to reset (00:00 UTC), then fill the per-variety literature gap and rebuild.
cd "$(dirname "$0")/.."
now=$(date -u +%s); target=$(date -u -d "tomorrow 00:15" +%s); sleep $(( target - now ))
export PYTHONIOENCODING=utf-8
python scripts/phase3_L1_harvest.py pervariety && python scripts/phase3_L1_parse.py && python scripts/phase3_L1_build.py \
 && python scripts/merge_manifest.py && python scripts/assemble.py --stage full && python scripts/phase2_LOC_local_names.py \
 && python scripts/phase3_LOC_codebook_names.py && python scripts/phase2_local_names.py full && python scripts/cgiar_tables.py && python scripts/make_final.py \
 && python scripts/build_viz.py
