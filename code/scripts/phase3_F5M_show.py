"""F5M reading aid: auto-extracted values for the decisions of one meeting (compare with the page image)."""
import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
m = sys.argv[1]
F = ["yield_t_ha", "yield_advantage_pct", "duration_days", "origin_country", "check_variety", "grain_type", "amylose_pct",
     "grain_wt_1000_g", "protein_pct", "zinc_mg_kg", "dus_distinct_traits_n", "vcu_regions_n", "vcu_sites_n", "breeding_line", "pedigree_cross"]
for x in csv.DictReader(open("05_output/final/bgd_nsb_decisions_full.csv", encoding="utf-8-sig")):
    if x["meeting_no"] == m:
        print(x["dec_id"], x["pages"], x["decision_type"], x["variety_name_as_printed"][:45], x["pilot_key"])
        print("    " + " | ".join(f"{f[:6]}={x[f][:40]}" for f in F if x[f]))
