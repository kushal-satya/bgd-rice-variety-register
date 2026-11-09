"""Check that every file in 02_raw (except robots.txt copies and the archive's own catalogue files) has a manifest row,
and vice versa, and that no two manifest paths differ only by letter case (on Windows they would be the same file)."""
import collections, csv, os, glob
norm = lambda p: os.path.normpath(p).replace(os.sep, "/")
OWN = {"02_raw/manifest.csv", "02_raw/CATALOGUE.csv", "02_raw/README.md"}
m = {norm(r["file_path"]) for r in csv.DictReader(open("02_raw/manifest.csv", encoding="utf-8"))}
fs = [norm(f) for f in glob.glob("02_raw/**/*", recursive=True)
      if os.path.isfile(f) and "_robots" not in f and "_manifest_parts" not in f and norm(f) not in OWN and not f.endswith(".csv.tmp")]
miss = [f for f in fs if f not in m]
print(len(fs), "files;", len(miss), "not in manifest"); print("\n".join(miss))
print("manifest rows without file:", [x for x in m if not os.path.exists(x)])
case = [p for p, n in collections.Counter(x.lower() for x in m).items() if n > 1]
print("manifest paths that differ only by case:", case)
