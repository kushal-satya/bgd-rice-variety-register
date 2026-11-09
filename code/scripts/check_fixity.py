"""Fixity check of the source archive: re-hash every file in 02_raw/manifest.csv and compare with the recorded SHA-256.

    python scripts/check_fixity.py [--manifest PATH] [--report-dir DIR]

Writes 06_validation/fixity_report.md (summary and every failure) and 06_validation/fixity_events.csv (one PREMIS-style
fixity event per file: file_path, algorithm, recorded, computed, date, outcome). Also checks:
- case collisions: manifest paths that differ only in letter case (on a case-insensitive disk they are one file);
- files on disk without a manifest row, and manifest rows without a file (case-sensitive comparison).
Exit status 1 if any file is missing, any hash differs, or any case collision exists; 0 otherwise. Truncated captures that the
manifest already marks (integrity_status = truncated, or a 'TRUNCATED' note) are reported but do not fail the check.
"""
import collections
import csv
import datetime
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_archive as LA

ROOT = LA.ROOT
REPORT = ROOT / "06_validation/fixity_report.md"
EVENTS = ROOT / "06_validation/fixity_events.csv"


def disk_files():
    out = []
    for dp, dn, fn in os.walk(LA.RAW):
        for f in fn:
            rel = (pathlib.Path(dp) / f).relative_to(ROOT).as_posix()
            if rel in LA.NOT_SOURCES or rel.startswith(LA.NOT_SOURCE_DIRS) or rel.endswith(".csv.tmp"):
                continue
            out.append(rel)
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--manifest", default=str(LA.MANIFEST)); ap.add_argument("--report-dir", default=str(ROOT / "06_validation"))
    a = ap.parse_args()
    global REPORT, EVENTS
    REPORT, EVENTS = pathlib.Path(a.report_dir) / REPORT.name, pathlib.Path(a.report_dir) / EVENTS.name
    today = datetime.date.today().isoformat()
    rows = LA.read_manifest(a.manifest)
    disk = disk_files()
    disk_set = set(disk)                      # exact spelling from the directory listing
    events, missing, mismatch, truncated = [], [], [], []
    for r in rows:
        p = r["file_path"]
        if p not in disk_set:
            missing.append(p); outcome, comp = "missing", ""
        else:
            comp = LA.sha256(ROOT / p)
            outcome = "pass" if comp == r["sha256"] else "fail"
            if outcome == "fail":
                mismatch.append((p, r["sha256"], comp))
        if r.get("integrity_status") == "truncated" or "TRUNCATED" in r.get("notes", ""):
            truncated.append(p)
        events.append(dict(file_path=p, algorithm="SHA-256", recorded=r["sha256"], computed=comp, date=today, outcome=outcome))
    lower = collections.defaultdict(list)
    for r in rows:
        lower[r["file_path"].lower()].append(r["file_path"])
    collisions = {k: v for k, v in lower.items() if len(v) > 1}
    listed = {r["file_path"] for r in rows}
    unlisted = sorted(set(disk) - listed)

    with open(EVENTS, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file_path", "algorithm", "recorded", "computed", "date", "outcome"])
        w.writeheader(); w.writerows(events)
    ok = not (missing or mismatch or collisions)
    n_pass = sum(e["outcome"] == "pass" for e in events)
    L = ["# Fixity report for 02_raw", "",
         f"Run {today} by `scripts/check_fixity.py`. Every file listed in `02_raw/manifest.csv` was read in full and its SHA-256 "
         f"compared with the value recorded at download. One fixity event per file is in `06_validation/fixity_events.csv`.", "",
         f"**Result: {'PASS' if ok else 'FAIL'}.** {len(rows):,} manifest rows; {n_pass:,} files match their recorded checksum, "
         f"{len(mismatch)} differ, {len(missing)} are missing from disk; {len(collisions)} case collision(s); "
         f"{len(unlisted)} file(s) on disk without a manifest row; {len(truncated)} known truncated capture(s).", ""]
    if mismatch:
        L += ["## Checksum differs", "", "| file | recorded | computed |", "|---|---|---|"]
        L += [f"| `{p}` | `{a[:16]}...` | `{b[:16]}...` |" for p, a, b in mismatch] + [""]
    if missing:
        L += ["## Listed but not on disk (case-sensitive)", ""] + [f"- `{p}`" for p in missing] + [""]
    if collisions:
        L += ["## Case collisions", "",
              "These manifest paths differ only in letter case. On a case-insensitive disk (Windows, macOS default) they are one "
              "file, so one response overwrote the other. Run `scripts/repair_manifest.py`.", ""]
        L += [f"- {', '.join(f'`{x}`' for x in v)}" for v in collisions.values()] + [""]
    if unlisted:
        L += ["## On disk without a manifest row", ""] + [f"- `{p}`" for p in unlisted] + [""]
    if truncated:
        L += ["## Known truncated captures (reported, not a failure)", "",
              "These files are complete copies of what the Internet Archive served, but the capture itself was cut short; they "
              "do not open and the register does not cite them.", ""] + [f"- `{p}`" for p in truncated] + [""]
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"fixity {'PASS' if ok else 'FAIL'}: {n_pass}/{len(rows)} match, {len(mismatch)} differ, {len(missing)} missing, "
          f"{len(collisions)} case collisions, {len(unlisted)} unlisted, {len(truncated)} known truncated -> {REPORT}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
