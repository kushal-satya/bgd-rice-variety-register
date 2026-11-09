"""Combine local names from institute/official evidence and survey/DNA rows into the local_names schema."""
import sys, pandas as pd
SUF = "_pilot" if (len(sys.argv) < 2 or sys.argv[1] == "pilot") else ""
src = pd.read_csv(f"05_output/local_names_from_sources{SUF}.csv", dtype=str).fillna("")
ev = pd.read_csv(f"05_output/evidence_all{SUF}.csv", dtype=str).fillna("")
pop = ev[(ev.field == "popular_name") & ev.eligible.astype(str).eq("True")][src.columns.intersection(ev.columns)]
src = pd.concat([src, pop], ignore_index=True).drop_duplicates(["pilot_key", "value", "source_id"])
vid = src.pilot_key.map(lambda k: ("FISH-" + k[5:]) if k.startswith("FISH_") else "RICE-" + k)
src = src[src.get("eligible", pd.Series("True", index=src.index)).astype(str).ne("False")]
vid = vid[src.index]
src = src.assign(variety_id=vid,
                 local_name=src.value, local_name_bn=src.value_raw.where(src.value_raw.str.contains("[ঀ-৿]")),
                 region="", source=src.source_title, page_or_locator="p" + src.page + " " + src.locator,
                 source_type=src.authority_rank.map(lambda r: "official" if r[:1] in "123" else ("news" if r[:1] == "6" else "other")),
                 flags="", notes=src.notes)
loc = pd.read_csv("04_working/local_names_LOC.csv", dtype=str).fillna("")
cols = ["variety_id", "local_name", "local_name_bn", "region", "source", "local_file", "page_or_locator",
        "source_type", "confidence", "flags", "notes"]
out = pd.concat([src[cols], loc[cols]], ignore_index=True).fillna("")
out.to_csv(f"05_output/local_names{SUF}.csv", index=False, encoding="utf-8-sig")
out = out.drop_duplicates(["variety_id", "local_name", "source"])
out.to_csv(f"05_output/local_names{SUF}.csv", index=False, encoding="utf-8-sig")
print(len(out))
