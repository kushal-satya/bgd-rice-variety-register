"""Collect everything CGIAR-produced into two tables in 05_output/final/:
- bgd_cgiar_sources.csv: one row per CGIAR source document (centre, title, URL/DOI, local copy, SHA-256, archive copy,
  how many varieties it mentions, which fields were taken from it).
- bgd_cgiar_statements.csv: one row per (variety, CGIAR source, field) with the value and the exact quote."""
import re, pathlib, sys
import pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lib_names import variety_name
ev = pd.read_csv(ROOT / "05_output/evidence_all.csv", dtype=str).fillna("")
man = pd.read_csv(ROOT / "02_raw/manifest.csv", dtype=str).fillna("")
man["file_path"] = man.file_path.str.replace("\\", "/", regex=False)
M = man.drop_duplicates("file_path").set_index("file_path")
c = ev[ev.authority_rank.str.startswith("4") & ev.eligible.astype(str).eq("True")].copy()
c["local_file"] = c.local_file.str.replace("\\", "/", regex=False)


def centre(row):
    t = " ".join([row.source_title, row.local_file, row.source_id]).lower()
    for k, v in [("spia", "SPIA (CGIAR)"), ("harvestplus", "HarvestPlus"), ("worldfish", "WorldFish"), ("africarice", "AfricaRice"),
                 ("glomip", "CGIAR GloMIP"), ("asti", "IFPRI ASTI"), ("trivsa", "IRRI / ASTI (TRIVSA)"), ("strasa", "IRRI STRASA"),
                 ("cgspace", "CGIAR (CGSpace)"), ("irri", "IRRI"), ("villanueva", "IRRI (Villanueva et al. 2022)"),
                 ("dikitanan", "IRRI (Dikitanan et al. 2022)"), ("kretzschmar", "IRRI (Kretzschmar et al. 2018)"),
                 ("raitzer", "SPIA (Raitzer et al. 2015)"), ("ispc", "ISPC/SPIA")]:
        if k in t:
            return v
    return "CGIAR (other)"


c["centre"] = c.apply(centre, axis=1)
c["source_url"] = c.local_file.map(lambda f: M.source_url.get(f, ""))
c["archived_url"] = c.local_file.map(lambda f: M.archived_url.get(f, ""))
c["sha256"] = c.local_file.map(lambda f: M.sha256.get(f, ""))
c["variety_id"] = "RICE-" + c.pilot_key
c.loc[c.pilot_key.str.startswith("FISH_"), "variety_id"] = "FISH-" + c.pilot_key.str[5:]
c["variety_name"] = c.pilot_key.map(lambda k: variety_name(k) if not k.startswith("FISH_") else k[5:])
st = c[["variety_id", "variety_name", "centre", "source_title", "field", "value", "value_raw", "page", "locator",
        "method", "validation", "source_url", "archived_url", "local_file"]].rename(columns={"value_raw": "quote_or_cell"})
st = st.drop_duplicates().sort_values(["variety_id", "centre", "field"])
st.to_csv(ROOT / "05_output/final/bgd_cgiar_statements.csv", index=False, encoding="utf-8-sig")
src = c.groupby("local_file").agg(centre=("centre", "first"), source_title=("source_title", "first"),
                                  source_url=("source_url", "first"), archived_url=("archived_url", "first"),
                                  sha256=("sha256", "first"), n_varieties=("pilot_key", "nunique"),
                                  n_statements=("value", "size"),
                                  fields=("field", lambda s: "; ".join(sorted(set(s))))).reset_index()
src["doi"] = src.source_url.str.extract(r"(10\.\d{4,9}/[^\s?#]+)")[0].fillna("")
src = src[["centre", "source_title", "doi", "source_url", "archived_url", "local_file", "sha256", "n_varieties", "n_statements", "fields"]]
src.sort_values(["centre", "source_title"]).to_csv(ROOT / "05_output/final/bgd_cgiar_sources.csv", index=False, encoding="utf-8-sig")
print(len(src), "CGIAR source files;", len(st), "statements;", st.variety_id.nunique(), "varieties/strains")
print(src.groupby("centre").agg(files=("local_file", "size"), varieties=("n_varieties", "sum")).to_string())
