"""Write release/datapackage.json, a Frictionless Data Package describing every public CSV in 05_output/final.

    python scripts/build_datapackage.py          # then: python scripts/validate_datapackage.py

One resource per bgd_*.csv in 05_output/final except the internal attendance table (bgd_nsb_attendance.csv). Resource
paths are 'data/<file>', the layout of the public repository and site, so the descriptor is meant to sit at the root of
the public repository next to data/. Field descriptions, titles and types come from 04_working/data_dictionary.csv. A
dictionary type is declared as integer, number or date only if every non-blank value of the column conforms; otherwise
the field is a string, so the descriptor never claims more than the file delivers. Blank cells are declared missing
values. A primaryKey is declared on the first identifier column (variety_id, strain_id, event_id, act_id, pub_id) that is
complete and unique; a foreignKey to bgd_rice_varieties.csv is declared on variety_id where every value is a register
identifier. The descriptor describes the PUBLIC copies (scripts/redact_personal.public_table applied: contact columns of
bgd_variety_people.csv dropped), which is what the site and repository publish. Byte counts and hashes are not recorded,
because the public copies are rewritten by every site build; rerun this script after every rebuild.
"""
import json
import pathlib
import re
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import redact_personal as RP  # noqa: E402
F = ROOT / "05_output/final"
OUT = ROOT / "release/datapackage.json"
PRIVATE = {"bgd_nsb_attendance.csv"}
ID_COLS = ["variety_id", "strain_id", "event_id", "act_id", "pub_id"]
REGISTER = "bgd_rice_varieties.csv"
INT = re.compile(r"^-?\d+$")
NUM = re.compile(r"^-?\d+(\.\d+)?$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def public_files():
    """Exactly the tables offered for download on the site (the files list make_final.py writes into viz_data.json)."""
    import json
    listed = {f["file"] for f in json.loads((F / "viz_data.json").read_text(encoding="utf-8"))["files"]}
    return sorted(p for p in F.glob("bgd_*.csv") if p.name in listed and p.name not in PRIVATE)


def field_type(dtype, s):
    v = s[s.str.strip() != ""]
    if dtype == "integer" and v.str.fullmatch(INT).all():
        return "integer"
    if dtype in ("decimal", "number", "integer") and v.str.fullmatch(NUM).all():
        return "number"
    if dtype == "date" and v.str.fullmatch(DATE).all():
        return "date"
    return "string"


def main():
    dd = pd.read_csv(ROOT / "04_working/data_dictionary.csv", dtype=str, keep_default_na=False)
    tabs = pd.read_csv(ROOT / "04_working/data_dictionary_tables.csv", dtype=str, keep_default_na=False).set_index("table")
    reg_ids = set(pd.read_csv(F / REGISTER, dtype=str, keep_default_na=False).variety_id)
    resources, undocumented = [], []
    for fp in public_files():
        d = RP.public_table(fp.name, pd.read_csv(fp, dtype=str, keep_default_na=False))
        cols = dd[dd.table == fp.name].drop_duplicates("column").set_index("column")
        fields = []
        for c in d.columns:
            f = {"name": c}
            if c in cols.index:
                r = cols.loc[c]
                f["title"] = r["label"]
                desc = r["meaning"] + (f" Values: {r['values']}" if r["values"] else "")
                f["description"] = desc
                f["type"] = field_type(r["type"], d[c])
                if r["type"] == "URL":
                    f["format"] = "uri" if d[c][d[c] != ""].str.match(r"^https?://").all() else "default"
            else:
                f["type"] = "string"; undocumented.append(f"{fp.name}:{c}")
            fields.append(f)
        schema = {"fields": fields, "missingValues": [""]}
        for k in ID_COLS:
            if k in d.columns and (d[k] != "").all() and d[k].is_unique:
                schema["primaryKey"] = [k]
                break
        if fp.name != REGISTER and "variety_id" in d.columns:
            v = set(d.variety_id[d.variety_id != ""])
            if v and v <= reg_ids:
                schema["foreignKeys"] = [{"fields": ["variety_id"], "reference": {"resource": "bgd_rice_varieties", "fields": ["variety_id"]}}]
        res = {"name": fp.stem.lower(), "path": f"data/{fp.name}", "profile": "tabular-data-resource", "format": "csv",
               "mediatype": "text/csv", "encoding": "utf-8-sig"}
        if fp.name in tabs.index:
            res["title"] = tabs.loc[fp.name, "unit"]
            res["description"] = tabs.loc[fp.name, "description"]
        res["schema"] = schema
        resources.append(res)
    pkg = {
        "profile": "tabular-data-package",
        "name": "bgd-rice-variety-register",
        "title": "Bangladesh Rice Variety Register: officially approved rice varieties, with improved fish strains",
        "version": "1.3.0",
        "homepage": "https://kushal-satya.github.io/bgd-rice-variety-register/",
        "description": "Every rice variety officially approved in Bangladesh (National Seed Board meetings 1 to 115, 1974 to 5 February "
                       "2026, and the varieties recommended before the Board existed), with the evidence for every value, the Board's "
                       "decisions, official lists, CGIAR links, pedigrees, improved fish strains and government acts on fish. All files are "
                       "UTF-8 CSV with a byte-order mark; read every column as text and convert numeric columns explicitly.",
        "keywords": ["Bangladesh", "rice", "crop varieties", "variety release", "National Seed Board", "CGIAR", "pedigree", "fish strains"],
        "contributors": [{"title": "Kushal Kumar", "role": "author", "organization": "Cornell University"}],
        "licenses": [{"name": "CC-BY-4.0", "path": "https://creativecommons.org/licenses/by/4.0/",
                      "title": "Creative Commons Attribution 4.0 International"}],
        "sources": [{"title": "Source documents listed in bgd_sources.csv and 02_raw/CATALOGUE.csv (third-party rights, see NOTICE.md)"}],
        "resources": resources,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(pkg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(resources)} resources, "
          f"{sum('primaryKey' in r['schema'] for r in resources)} with primaryKey, "
          f"{sum('foreignKeys' in r['schema'] for r in resources)} with foreignKeys; {len(undocumented)} undocumented columns")
    for u in undocumented:
        print("  undocumented:", u)
    return 0


if __name__ == "__main__":
    sys.exit(main())
