"""Survey popular names from the SPIA BIHS 2024 'paddy' choice list (e.g. 'Biplob BR-3 (Aus/Aman)').
Only labels with a recognisable official series + a leading popular name are used; market names
(Miniket, Jira...) are handled in phase2_LOC_local_names.py with explicit evidence."""
import re, sys, pandas as pd
sys.path.insert(0, "scripts")
from lib_keys import make_key
p = pd.read_csv("03_extracted/tables/spia_bihs2024_paddy_choices.csv", dtype=str).fillna("")
rows = []
for _, r in p.iterrows():
    lab = r["label::English"].strip()
    m = re.match(r"^([A-Za-z][A-Za-z ]+?)\s+(BR-?\s*\d+)", lab)
    if not m or m.group(1).lower().startswith("bri dhan"):
        continue
    key = make_key(m.group(2))
    rows.append(["RICE-" + key, m.group(1).strip(), "", "", "SPIA BIHS 2024 SurveyCTO codebook, list 'paddy'",
                 "02_raw/spia_bd2025/SPIA_BIHS_2024_Varnames.xlsx", f"choices sheet, list_name=paddy, value={r['value']}",
                 "survey", "high", "", f"Label '{lab}'."])
cols = ["variety_id", "local_name", "local_name_bn", "region", "source", "local_file", "page_or_locator",
        "source_type", "confidence", "flags", "notes"]
loc = pd.read_csv("04_working/local_names_LOC.csv", dtype=str).fillna("")
out = pd.concat([loc, pd.DataFrame(rows, columns=cols)]).drop_duplicates(["variety_id", "local_name", "source"])
out.to_csv("04_working/local_names_LOC.csv", index=False, encoding="utf-8")
print(len(rows), "codebook names;", len(out), "LOC rows")
