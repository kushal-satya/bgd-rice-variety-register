"""Repair and extend 02_raw/manifest.csv after the Wayback job (scripts/archive_wayback.py) has finished.

    python scripts/repair_manifest.py [--manifest PATH] [--dry-run] [--force]

What it does, every run (idempotent: a second run changes nothing):
1. Case collisions. On the case-insensitive Windows disk two OpenAlex responses whose names differ only in case
   (q_BINA_dhan_p*.json and q_Bina_dhan_p*.json) were written onto one file. For every group of rows whose file_path
   differs only in case, the spelling that exists on disk (exact, case-sensitive directory listing) is kept; rows whose
   spelling is not on disk are removed and written to 06_validation/manifest_repair_removed_rows.csv. If the kept
   row's SHA-256 no longer matches the file, it is set to the hash of the file on disk and the note records the old value.
2. Files on disk without a row (other than robots copies, manifest parts, the manifest, CATALOGUE.csv and README.md)
   get a row with the file's hash, the file date as download_date and a note; known files get a written provenance.
3. Derived columns, recomputed each run and appended after the original columns:
   bytes, mime_type, duplicate_of (path of the first-listed file with the same SHA-256), integrity_status
   (ok | truncated | missing | hash_mismatch) and archive_status (archived | not archivable: API response |
   address unstable: deposit file | no public address: deposit file | archivable, retry).
The file is written atomically (temporary file, then replace). The original columns are never reordered, so scripts
that read the manifest by column name keep working.

Run it only when archive_wayback.py has stopped: that job holds the manifest in memory and rewrites it whole, so it
would undo these changes. The script refuses to run while logs/wayback_archive.log has been written in the last
15 minutes, unless --force is given.
"""
import argparse
import csv
import datetime
import os
import pathlib
import sys
import time
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_archive as LA

DERIVED = ["bytes", "mime_type", "duplicate_of", "integrity_status", "archive_status"]
KNOWN_NEW = {   # provenance for files that reached 02_raw without a manifest row
    "02_raw/wayback_cdx/F6G_moa_portal_folder_2da640c5.json": dict(
        agent="F6G", source_url="",
        notes="Wayback CDX listing of the retired moa.portal.gov.bd gazette folder page/2da640c5_2b98_427c_ae5d_f2d301e9bb9b "
              "(exact CDX query URL not logged; see 04_working/notes_F6G.md section E); added by repair_manifest.py"),
}


# Files overwritten after their manifest row was written, so the recorded hash belongs to a capture that no longer exists.
# Each reset applies only if the manifest still holds the old hash and the disk holds the new one (nothing else is touched).
HASH_RESETS = {
    "02_raw/cgiar_specific/glomip/product-catalog.html": dict(
        old="48749102271da95ea7a1b800089794464ab2dfb3dd0dda3d8df81c99006981d2",
        new="110e4191a298bf70" ,   # prefix of the hash of the file on disk on 2026-11-09
        note="RE-CAPTURED: scripts/phase3_L2_glomip.py rewrites this page on every run (fresh session and CSRF token) but "
             "register_existing() keeps the first row, so the first capture's hash was left on a later capture of 2026-10-07 "
             "11:31; sha256 reset to the file on disk (repair_manifest.py). Not cited by the register."),
}


def exact_exists(rel):
    """Case-sensitive existence test (os.path.exists is case-insensitive on Windows)."""
    p = LA.ROOT / rel
    parent = p.parent
    try:
        return p.name in os.listdir(parent) and exact_exists_dir(parent)
    except FileNotFoundError:
        return False


def exact_exists_dir(d):
    d = pathlib.Path(d)
    if d == LA.ROOT or d == d.parent:
        return True
    try:
        return d.name in os.listdir(d.parent) and exact_exists_dir(d.parent)
    except FileNotFoundError:
        return False


def integrity(rel, path_on_disk):
    if not path_on_disk.exists():
        return "missing"
    if rel.lower().endswith(".pdf"):
        try:
            import fitz
            with fitz.open(path_on_disk) as doc:
                if doc.page_count == 0:
                    return "truncated"
        except Exception:  # noqa
            return "truncated"
        if path_on_disk.stat().st_size == 1048576:
            return "truncated"
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(LA.MANIFEST))
    ap.add_argument("--removed-log", default=str(LA.ROOT / "06_validation/manifest_repair_removed_rows.csv"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    man = pathlib.Path(a.manifest)
    log = LA.ROOT / "logs/wayback_archive.log"
    if not a.force and man.resolve() == LA.MANIFEST.resolve() and log.exists() and time.time() - log.stat().st_mtime < 900:
        sys.exit("logs/wayback_archive.log was written in the last 15 minutes: archive_wayback.py may still be running. "
                 "Wait for it to finish, or pass --force.")

    rows = LA.read_manifest(man)
    with open(man, encoding="utf-8-sig", newline="") as fh:
        header = next(csv.reader(fh))
    base = [c for c in header if c not in DERIVED]
    report = []

    # 1. case collisions
    groups = defaultdict(list)
    for r in rows:
        groups[r["file_path"].lower()].append(r)
    removed = []
    for k, g in groups.items():
        if len(g) < 2:
            continue
        on_disk = [r for r in g if exact_exists(r["file_path"])]
        if len(on_disk) != 1:
            report.append(f"case group {k}: {len(on_disk)} spellings on disk, left unchanged")
            continue
        keep = on_disk[0]
        for r in g:
            if r is not keep:
                removed.append(dict(r, removed_on=datetime.date.today().isoformat(),
                                    removed_reason=f"case collision with {keep['file_path']}; file overwritten on a case-insensitive disk"))
        disk_sha = LA.sha256(LA.ROOT / keep["file_path"])
        if disk_sha != keep["sha256"]:
            keep["notes"] = (keep["notes"] + f" | CASE COLLISION: file on disk is the response saved for "
                             f"{', '.join(r['file_path'].rsplit('/', 1)[-1] for r in g if r is not keep)}; "
                             f"sha256 reset from {keep['sha256']} (repair_manifest.py)").strip(" |")
            keep["sha256"] = disk_sha
    drop_paths = {(r["file_path"], r["sha256"]) for r in removed}
    rows = [r for r in rows if (r["file_path"], r["sha256"]) not in drop_paths or exact_exists(r["file_path"])]
    report.append(f"case collisions: {len(removed)} row(s) removed")

    # 1b. known re-captures
    for r in rows:
        fix = HASH_RESETS.get(r["file_path"])
        if fix and r["sha256"] == fix["old"] and (LA.ROOT / r["file_path"]).exists():
            disk_sha = LA.sha256(LA.ROOT / r["file_path"])
            if disk_sha.startswith(fix["new"]):
                r["notes"] = (r["notes"] + f" | {fix['note']} Old sha256 {fix['old']}.").strip(" |")
                r["sha256"] = disk_sha
                report.append(f"hash reset: {r['file_path']}")

    # 2. files on disk without a row
    listed = {r["file_path"] for r in rows}
    listed_ci = {p.lower() for p in listed}
    added = 0
    for fp in sorted(LA.RAW.rglob("*")):
        if not fp.is_file():
            continue
        rel = fp.relative_to(LA.ROOT).as_posix()
        if rel in LA.NOT_SOURCES or rel.startswith(LA.NOT_SOURCE_DIRS) or rel.lower() in listed_ci:
            continue
        info = KNOWN_NEW.get(rel, dict(agent="", source_url="", notes="file found in 02_raw without a manifest row; added by repair_manifest.py, provenance to be completed"))
        rows.append({c: "" for c in base} | dict(file_path=rel, source_url=info["source_url"], archived_url="",
                    download_date=datetime.date.fromtimestamp(fp.stat().st_mtime).isoformat(), sha256=LA.sha256(fp),
                    file_type=fp.suffix.lstrip("."), agent=info["agent"], notes=info["notes"]))
        added += 1
    report.append(f"rows added for unlisted files: {added}")

    # 3. derived columns
    first = {}
    for r in rows:
        first.setdefault(r["sha256"], r["file_path"])
    for r in rows:
        p = LA.ROOT / r["file_path"]
        r["bytes"] = str(p.stat().st_size) if p.exists() else ""
        r["mime_type"] = LA.mime_type(r["file_path"])
        r["duplicate_of"] = "" if first[r["sha256"]] == r["file_path"] else first[r["sha256"]]
        r["integrity_status"] = integrity(r["file_path"], p)
        if r["integrity_status"] == "ok" and LA.sha256(p) != r["sha256"]:
            r["integrity_status"] = "hash_mismatch"
        r["archive_status"] = LA.archive_status(r)
    out_cols = base + DERIVED

    from collections import Counter
    report.append("integrity_status: " + str(dict(Counter(r["integrity_status"] for r in rows))))
    report.append("archive_status: " + str(dict(Counter(r["archive_status"] for r in rows))))
    report.append(f"duplicates (rows with duplicate_of): {sum(1 for r in rows if r['duplicate_of'])}")
    print("\n".join(report))
    if a.dry_run:
        print("dry run: nothing written"); return 0
    if removed:
        rl = pathlib.Path(a.removed_log); rl.parent.mkdir(parents=True, exist_ok=True)
        old = list(csv.DictReader(open(rl, encoding="utf-8-sig"))) if rl.exists() else []
        seen = {(r["file_path"], r["sha256"]) for r in old}
        allr = old + [r for r in removed if (r["file_path"], r["sha256"]) not in seen]
        cols = list(dict.fromkeys([c for r in allr for c in r.keys() if c not in DERIVED]))
        with open(rl, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(allr)
    tmp = man.with_suffix(".csv.tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=out_cols, extrasaction="ignore")   # CRLF, as archive_wayback.py writes
        w.writeheader(); w.writerows(rows)
    os.replace(tmp, man)
    print(f"wrote {man}: {len(rows)} rows, columns {out_cols}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
