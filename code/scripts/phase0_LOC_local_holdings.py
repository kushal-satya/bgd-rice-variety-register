"""Phase 0: register datasets already on disk (SPIA BD 2025 replication package,
SPIA BD stocktake) as discovery hits. Copies untouched files into 02_raw and writes
_parts/LOC_* rows. Re-runnable: skips files already in the manifest."""
import csv, hashlib, shutil, datetime, pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
BGD = ROOT.parent
SPIA = BGD / "hilsa_feasibility/external/SPIA-Bangladesh-Study-2025"
GH = "https://github.com/CGIAR-SPIA/SPIA-Bangladesh-Study-2025/blob/main/"
TODAY = datetime.date.today().isoformat()

files = [  # (local source, 02_raw dest, source_url, note)
    (SPIA / "Data/DNA fingerprinting/Barcode_reference_2024.xlsx", "spia_bd2025/Barcode_reference_2024.xlsx",
     GH + "Data/DNA%20fingerprinting/Barcode_reference_2024.xlsx", "SPIA DNA reference library: 110 reference varieties (BD-n, Binadhan-n)"),
    (SPIA / "Data/DNA fingerprinting/bangladesh_rice_assignment_results.xlsx", "spia_bd2025/bangladesh_rice_assignment_results.xlsx",
     GH + "Data/DNA%20fingerprinting/bangladesh_rice_assignment_results.xlsx", "2,202 field samples assigned to reference varieties"),
    (SPIA / "Data/DNA fingerprinting/ref_clusters_no_hybrids_with_HH_Ids.csv", "spia_bd2025/ref_clusters_no_hybrids_with_HH_Ids.csv",
     GH + "Data/DNA%20fingerprinting/ref_clusters_no_hybrids_with_HH_Ids.csv", "370 rows: farmer-reported names (Miniket, Jira, Katari, Hira...) vs DNA cluster group"),
    (SPIA / "Data/DNA fingerprinting/missing_barcode_list_replated.xlsx", "spia_bd2025/missing_barcode_list_replated.xlsx",
     GH + "Data/DNA%20fingerprinting/missing_barcode_list_replated.xlsx", ""),
    (SPIA / "Data/Codebook/SPIA_BIHS_2024_Varnames.xlsx", "spia_bd2025/SPIA_BIHS_2024_Varnames.xlsx",
     GH + "Data/Codebook/SPIA_BIHS_2024_Varnames.xlsx", "SurveyCTO codebook; choice list 'paddy' = 185 rice variety codes with popular names"),
    (BGD / "CG_Stocktake/BAN_Stocktake_July_2023.xlsx", "spia_stocktake/BAN_Stocktake_July_2023.xlsx",
     "", "CGIAR-related innovations - Bangladesh stocktake (SPIA), last update 01/12/2023; received file, public URL not yet confirmed"),
]

man_path = ROOT / "02_raw/manifest.csv"
parts = ROOT / "01_discovery/_parts"
done = {r["file_path"] for r in csv.DictReader(open(man_path, encoding="utf-8"))}
loc_man = parts / "LOC_manifest.csv"
rows = []
for src, dest, url, note in files:
    rel = "02_raw/" + dest
    if rel in done:
        continue
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, out)
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    rows.append([rel, url, "", TODAY, sha, out.suffix.lstrip("."), "LOC",
                 f"copied from local disk {src.relative_to(BGD)}; {note}"])
with open(loc_man, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow("file_path,source_url,archived_url,download_date,sha256,file_type,agent,notes".split(","))
    w.writerows(rows)

# export the 'paddy' choice list for later local-name work
ch = pd.read_excel(SPIA / "Data/Codebook/SPIA_BIHS_2024_Varnames.xlsx", "choices")
p = ch[ch.list_name == "paddy"][["list_name", "value", "label::English"] +
                                 [c for c in ch.columns if "Bangla" in c or "Bengali" in c]]
(ROOT / "03_extracted/tables").mkdir(parents=True, exist_ok=True)
p.to_csv(ROOT / "03_extracted/tables/spia_bihs2024_paddy_choices.csv", index=False, encoding="utf-8")
print("paddy codes:", len(p), "manifest rows:", len(rows))
