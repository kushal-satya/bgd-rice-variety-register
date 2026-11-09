"""NSB attendance and contacts table (internal edition only).

Input: 04_working/attendance/attendance_*.csv, transcribed by eye from the attendance sheets (হাজিরা) appended to the NSB
minutes (page images in 04_working/attendance_png/). Names, posts, phone numbers and e-mails are as handwritten; an
illegible digit is '?'. Output: 05_output/final/bgd_nsb_attendance.csv, one row per signed or listed entry, with the
original and archived address of the minutes."""
import glob
import pathlib

import pandas as pd

R = pathlib.Path(__file__).resolve().parents[1]
parts = [pd.read_csv(f, dtype=str, keep_default_na=False).assign(transcribed_by=pathlib.Path(f).stem.split("_")[-1])
         for f in sorted(glob.glob(str(R / "04_working/attendance/attendance_*.csv")))]
out = R / "05_output/final/bgd_nsb_attendance.csv"
if not parts:
    print("no attendance evidence yet")
    raise SystemExit
a = pd.concat(parts, ignore_index=True)
for c in a.columns:
    a[c] = a[c].str.strip()
a["meeting_no"] = a.meeting_no.str.extract(r"(\d+)", expand=False)
src = pd.read_csv(R / "05_output/final/bgd_sources.csv", dtype=str, keep_default_na=False)[["local_file", "source_url", "archived_url"]]
man = pd.read_csv(R / "02_raw/manifest.csv", dtype=str, keep_default_na=False)
man = man.assign(local_file=man.file_path.str.replace(chr(92), "/", regex=False).str.extract(r"(02_raw/.*)$", expand=False))
src = pd.concat([src, man[~man.local_file.isin(src.local_file)][["local_file", "source_url"]]]).drop_duplicates("local_file")
a = a.merge(src.rename(columns={"local_file": "source_file"}), on="source_file", how="left").fillna("")
a = a.sort_values(["meeting_no", "page", "serial"], key=lambda s: pd.to_numeric(s, errors="coerce"), kind="stable")
a.insert(0, "entry_id", ["NSB%03d-%02d" % (int(m), i + 1) for m, g in a.groupby("meeting_no", sort=False) for i in range(len(g))])
a.to_csv(out, index=False, encoding="utf-8-sig")
print(out.relative_to(R), len(a), "rows;", a.meeting_no.nunique(), "meetings;", (a.read_confidence == "low").sum(), "low-confidence rows")
