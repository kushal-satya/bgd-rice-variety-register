"""Check release/datapackage.json against the CSV files in 05_output/final. Exit 1 on any failure.

    python scripts/validate_datapackage.py [path/to/datapackage.json] [data folder]

Checks: every public bgd_*.csv is listed and every listed file exists; the header of each file equals the schema field names
in order; byte counts and SHA-256 hashes match; integer, number and date fields hold only conforming values; primary keys
are complete and unique; foreign keys resolve. The package describes the public copies, so each file is passed through
scripts/redact_personal.public_table first; this is a no-op on files that are already public (site/data), so either folder
can be checked. Uses only pandas (the frictionless package is not required).
"""
import hashlib
import json
import pathlib
import re
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import redact_personal as RP  # noqa: E402
PAT = {"integer": re.compile(r"^-?\d+$"), "number": re.compile(r"^-?\d+(\.\d+)?$"), "date": re.compile(r"^\d{4}-\d{2}-\d{2}$")}


def main():
    pkg_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "release/datapackage.json"
    data = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "05_output/final"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    errs, frames = [], {}
    listed = {pathlib.PurePosixPath(r["path"]).name for r in pkg["resources"]}
    # REV3: build_datapackage.py packages exactly the tables the site offers (viz_data.json 'files'); a CSV the site does not
    # publish (bgd_failures.csv, an internal build log) is not expected in the package
    viz = data / "viz_data.json"
    offered = {f["file"] for f in json.loads(viz.read_text(encoding="utf-8"))["files"]} if viz.exists() else None
    for fp in sorted(data.glob("bgd_*.csv")):
        if offered is not None and fp.name not in offered:
            continue
        if fp.name != "bgd_nsb_attendance.csv" and fp.name not in listed:
            errs.append(f"{fp.name}: CSV not listed in the package")
    if "bgd_nsb_attendance.csv" in listed:
        errs.append("bgd_nsb_attendance.csv (personal data) is listed in the public package")
    for r in pkg["resources"]:
        fp = data / pathlib.PurePosixPath(r["path"]).name
        if not fp.exists():
            errs.append(f"{r['name']}: file {fp.name} missing"); continue
        d = RP.public_table(fp.name, pd.read_csv(fp, dtype=str, keep_default_na=False))
        frames[r["name"]] = d
        names = [f["name"] for f in r["schema"]["fields"]]
        if names != list(d.columns):
            errs.append(f"{r['name']}: header differs from schema (missing {sorted(set(names) - set(d.columns))}, extra {sorted(set(d.columns) - set(names))}, or order)")
        if r.get("bytes") is not None and r["bytes"] != fp.stat().st_size:
            errs.append(f"{r['name']}: bytes {r['bytes']} != {fp.stat().st_size}")
        if r.get("hash", "").startswith("sha256:") and r["hash"][7:] != hashlib.sha256(fp.read_bytes()).hexdigest():
            errs.append(f"{r['name']}: sha256 differs")
        for f in r["schema"]["fields"]:
            if f["type"] in PAT and f["name"] in d:
                v = d[f["name"]][d[f["name"]] != ""]
                bad = v[~v.str.fullmatch(PAT[f["type"]])]
                if len(bad):
                    errs.append(f"{r['name']}.{f['name']}: {len(bad)} values not {f['type']} (e.g. {bad.iloc[0]!r})")
        pk = r["schema"].get("primaryKey")
        if pk and (d[pk[0]].eq("").any() or not d[pk[0]].is_unique):
            errs.append(f"{r['name']}: primaryKey {pk} not complete and unique")
    for r in pkg["resources"]:
        for fk in r["schema"].get("foreignKeys", []):
            d, ref = frames.get(r["name"]), frames.get(fk["reference"]["resource"])
            if d is None or ref is None:
                errs.append(f"{r['name']}: foreign key target missing"); continue
            v = set(d[fk["fields"][0]][d[fk["fields"][0]] != ""]) - set(ref[fk["reference"]["fields"][0]])
            if v:
                errs.append(f"{r['name']}: {len(v)} {fk['fields'][0]} values not in {fk['reference']['resource']} (e.g. {sorted(v)[0]})")
    print(f"{pkg_path.name}: {len(pkg['resources'])} resources checked against {data}; {len(errs)} problem(s)")
    for e in errs:
        print("  FAIL", e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
