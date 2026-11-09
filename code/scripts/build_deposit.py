"""Build deposit/: the package of cited source documents for a public repository (Zenodo). Nothing is uploaded.

    python scripts/build_catalogue.py     # first: the deposit is selected from 02_raw/CATALOGUE.csv
    python scripts/build_deposit.py

Output (deposit/ at the project root; keep it out of git):
  sources/government_bd.zip   cited Government of Bangladesh documents       (rights_class gov_bd_official)
  sources/cgiar.zip           cited CGIAR documents, records and pages        (cgiar_open)
  sources/other_open.zip      cited openly licensed items and API metadata    (open_licence, openalex_cc0, crossref_metadata)
  sources/_withheld.csv       cited files that are not redistributed, with title, addresses, SHA-256 and reason
  MANIFEST_cited.csv          one row per cited file: checksum, size, type, addresses (mailto removed), rights, where deposited
  CATALOGUE.csv               the catalogue of the whole archive (02_raw/CATALOGUE.csv), personal contacts removed
  SHA256SUMS                  checksums of the deposited source files, by their 02_raw/ path (verify after unzipping)
  SHA256SUMS_packages         checksums of the zip files and tables in this folder
  README.md, LICENSE, NOTICE.md, CITATION.cff
Inside the zips every file keeps its 02_raw/... path, so each local_file value in the register resolves after unzipping.
Zip entries carry a fixed timestamp (the file's download date), so the zips are reproducible byte for byte. Every file is
re-hashed while it is packed; a mismatch with the manifest stops the build.
"""
import csv
import datetime
import hashlib
import pathlib
import shutil
import sys
import zipfile

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_archive as LA
import redact_personal as RP

ROOT = LA.ROOT
OUT = ROOT / "deposit"
GROUPS = {"government_bd": "Government of Bangladesh official publications (gazettes, acts and rules, NSB and Technical Committee minutes, SCA and Ministry lists, notices, BRRI/BINA/BFRI publications and pages)",
          "cgiar": "CGIAR outputs (CGSpace items and records, IRRI, WorldFish, HarvestPlus, AfricaRice, ASTI, GloMIP and SPIA documents and pages)",
          "other_open": "Openly licensed items (CC BY articles, CC0 Dataverse metadata), OpenAlex responses (CC0) and Crossref metadata without abstracts"}


def sha(fp):
    return hashlib.sha256(fp.read_bytes()).hexdigest()


def mb(n):
    return f"{n / 1e6:,.1f} MB"


def main():
    cat_path = ROOT / "02_raw/CATALOGUE.csv"
    if not cat_path.exists():
        sys.exit("02_raw/CATALOGUE.csv not found: run scripts/build_catalogue.py first")
    cat = pd.read_csv(cat_path, dtype=str, keep_default_na=False)
    man = {r["file_path"]: r for r in LA.read_manifest()}
    cited = cat[cat.cited_in_register == "Y"].copy()
    cited["group"] = cited.rights_class.map(lambda c: LA.deposit_group(c) if LA.rights_includable(c) else "")
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "sources").mkdir(parents=True)

    sums, sizes, problems = [], {}, []
    for g in GROUPS:
        sel = cited[cited.group == g].sort_values("file_path")
        zp = OUT / "sources" / f"{g}.zip"
        raw_bytes = 0
        with zipfile.ZipFile(zp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for r in sel.itertuples():
                fp = ROOT / r.file_path
                if not fp.exists():
                    problems.append(f"missing on disk: {r.file_path}"); continue
                h = sha(fp)
                if h != r.sha256:
                    problems.append(f"hash differs from manifest: {r.file_path} ({h} vs {r.sha256})")
                d = (man.get(r.file_path, {}).get("download_date") or "2026-10-06")[:10]
                y, m, dd = (int(x) for x in d.split("-"))
                zi = zipfile.ZipInfo(r.file_path, date_time=(y, m, dd, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = 0o644 << 16
                z.writestr(zi, fp.read_bytes())
                sums.append((h, r.file_path)); raw_bytes += fp.stat().st_size
        sizes[g] = (len(sel), raw_bytes, zp.stat().st_size)
    if problems:
        print("\n".join(problems)); sys.exit("deposit stopped: fix the manifest (scripts/repair_manifest.py) or the files first")

    wh = cited[cited.group == ""][["file_path", "title", "issuing_body", "document_type", "source_url", "archived_url", "sha256",
                                   "bytes", "rights_basis"]].rename(columns={"rights_basis": "reason_withheld"})
    wh.to_csv(OUT / "sources/_withheld.csv", index=False, encoding="utf-8-sig")

    cols = ["file_path", "title", "issuing_body", "document_date", "document_type", "sha256", "bytes", "mime_type", "source_url",
            "archived_url", "archive_status", "download_date", "agent", "rights_class", "deposited_in", "duplicate_of",
            "integrity_status", "fields_supported", "n_evidence_rows", "notes"]
    mc = cited.assign(deposited_in=cited.group.map(lambda g: f"sources/{g}.zip" if g else "not deposited (see sources/_withheld.csv)"),
                      notes=cited.file_path.map(lambda p: man.get(p, {}).get("notes", "")))
    mc = RP.redact(mc[cols].copy())
    mc["source_url"] = mc.source_url.map(LA.strip_mailto)
    mc.to_csv(OUT / "MANIFEST_cited.csv", index=False, encoding="utf-8-sig")
    RP.redact(cat.copy()).to_csv(OUT / "CATALOGUE.csv", index=False, encoding="utf-8-sig")
    for f in ["LICENSE", "NOTICE.md", "CITATION.cff"]:
        if (ROOT / "release" / f).exists():
            shutil.copy2(ROOT / "release" / f, OUT / f)
    with open(OUT / "SHA256SUMS", "w", encoding="utf-8", newline="\n") as fh:
        fh.writelines(f"{h}  {p}\n" for h, p in sorted(sums, key=lambda x: x[1]))

    n_dep = sum(v[0] for v in sizes.values()); raw = sum(v[1] for v in sizes.values()); zipped = sum(v[2] for v in sizes.values())
    rows = "\n".join(f"| `sources/{g}.zip` | {GROUPS[g]} | {sizes[g][0]} | {mb(sizes[g][1])} | {mb(sizes[g][2])} |" for g in GROUPS)
    readme = f"""# Bangladesh Rice Variety Register: source archive (cited documents)

This deposit holds the source documents cited by the Bangladesh Rice Variety Register (Kumar 2026; version 1.2.0,
https://kushal-satya.github.io/bgd-rice-variety-register/; code and data at
https://github.com/kushal-satya/bgd-rice-variety-register). The register gives, for every value, the file and page it was
read from; the `local_file` column of each register table is a path such as `02_raw/sca/nsb_minutes_058-075.pdf`. Unzip the
three archives in `sources/` into one folder and every such path resolves to the document it names.

Of the {len(cited)} files the register cites, {n_dep} are deposited here ({mb(raw)} uncompressed, {mb(zipped)} as zip files).
The other {len(wh)} are publisher documents, news reports, web pages and survey-linked files that may not be redistributed;
`sources/_withheld.csv` lists each with its title, original address, Internet Archive copy where one exists, SHA-256 and the
reason, so that a reader can obtain the same file and check that it is identical. The rule for each class of document is set
out in `NOTICE.md`; the deposited documents keep their own rights and are not covered by the licence of the register.

| file | contents | files | uncompressed | zip |
|---|---|---:|---:|---:|
{rows}

`MANIFEST_cited.csv` describes every cited file (title, issuing body, document date and type, SHA-256, size, media type,
original and archived address, download date, collecting workstream, rights class, the zip it is in, and the register fields
it supports). `CATALOGUE.csv` describes all {len(cat)} files collected for the project, most of which are discovery material
and literature-search responses that the register does not cite and that are not deposited. In both tables the polite-pool
e-mail parameter of OpenAlex and Crossref addresses has been removed (the query result does not depend on it), and e-mail
addresses and mobile numbers of individuals have been removed from the notes.

## Verifying the files

`SHA256SUMS` lists the SHA-256 checksum of every deposited document under its `02_raw/` path; the same values are in the
register's `bgd_sources.csv` and were computed when each file was downloaded (6 and 7 October 2026). After unzipping the three
archives in this folder, run

    sha256sum -c SHA256SUMS

(on macOS `shasum -a 256 -c SHA256SUMS`). Every line should end in `OK`. `SHA256SUMS_packages` gives the checksums of the
zip files and tables in this folder as deposited.

## Citation

Kumar, K. (2026). *Bangladesh Rice Variety Register: officially approved rice varieties, with improved fish strains*
(Version 1.2.0) [Data set]. Cornell University. https://kushal-satya.github.io/bgd-rice-variety-register/

Built {datetime.date.today().isoformat()} by `scripts/build_deposit.py`.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    pk = [p for p in sorted(OUT.rglob("*")) if p.is_file() and p.name != "SHA256SUMS_packages"]
    with open(OUT / "SHA256SUMS_packages", "w", encoding="utf-8", newline="\n") as fh:
        fh.writelines(f"{sha(p)}  {p.relative_to(OUT).as_posix()}\n" for p in pk)
    total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    for g, (n, rb, zb) in sizes.items():
        print(f"sources/{g}.zip: {n} files, {mb(rb)} uncompressed, {mb(zb)} zipped")
    print(f"withheld: {len(wh)} cited files; deposited {n_dep} of {len(cited)} cited files")
    print(f"deposit/ total size: {mb(total)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
