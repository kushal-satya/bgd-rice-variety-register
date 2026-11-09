"""P2B: extract Bangladesh rows from the saved HarvestPlus BCR JSON -> 03_extracted/tables/harvestplus_bd.csv"""
import json, csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
d = json.load(open(ROOT / "02_raw/harvestplus/bcr_details_varieties_released.json", encoding="utf-8"))
rows = [r for r in d["result"]["data"] if r.get("country_name") == "Bangladesh"]
keep = ["id_variety", "crop_name", "display_name", "primary_target", "variety_name", "local_name",
        "variety_release_status", "realease_year", "breeder_organization", "funded_by", "pedigree",
        "adaptation", "nutrition_content", "average_yield", "days_to_maturity", "growing_season", "variety_breeder"]
with open(ROOT / "03_extracted/tables/harvestplus_bd.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=keep + ["json_index"]); w.writeheader()
    for r in rows:
        w.writerow({**{k: r.get(k) for k in keep}, "json_index": d["result"]["data"].index(r)})
print(len(d["result"]["data"]), "records;", len(rows), "Bangladesh")
