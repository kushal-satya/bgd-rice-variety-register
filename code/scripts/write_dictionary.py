"""Render the data dictionary of the final release as 05_output/final/DATA_DICTIONARY.md.

Inputs   04_working/data_dictionary.csv         one row per (table, column): label, type, meaning, values,
                                                 source_and_derivation, share_nonblank
         04_working/data_dictionary_tables.csv  one row per table: unit of observation and description
         05_output/final/<table>                the released CSV files themselves
Output   05_output/final/DATA_DICTIONARY.md

Coverage (the share of rows in which a column is not blank) and row counts are recomputed from the current files every
time the script runs, so the dictionary stays correct after a rebuild. The script prints a warning for every documented
column that is missing from its CSV and for every CSV column that the dictionary does not document; it never edits the
dictionary CSVs. Tables holding personal data (bgd_nsb_attendance.csv) are opened for their header line only.

Run after scripts/make_final.py, which writes an older, shorter DATA_DICTIONARY.md:
    python scripts/write_dictionary.py
"""
import csv
import datetime
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
F = ROOT / "05_output/final"
DD_PATH = ROOT / "04_working/data_dictionary.csv"
TAB_PATH = ROOT / "04_working/data_dictionary_tables.csv"
OUT = F / "DATA_DICTIONARY.md"
PRIVATE = {"bgd_nsb_attendance.csv"}     # personal data: header only, never the rows

PREFACE = """\
This dictionary describes every column of every table in the Bangladesh Rice Variety Register and its companion tables on
fish strains, sources and literature. Each table section gives the unit of observation, the number of rows, and for each
column its meaning, its allowed values or units, and its coverage, the share of rows in which the column is not blank.
Coverage and row counts are computed from the released files when this document is built. How each column was derived, and
from which source, is recorded in `04_working/data_dictionary.csv` (column `source_and_derivation`), which also gives a
short label and a data type for every column.

## Conventions

**Identifiers.** Every rice variety has a stable identifier, `variety_id`, of the form `RICE-<key>`, where the key is built
from the official name (for example `RICE-BRRI_DHAN29`, `RICE-BINADHAN7`, `RICE-HYB_ACI1`). The number in the key is the
official series number, not a running count. The identifier is the join key across all tables; display names
(`variety_name`) are generated from it and are not official spellings. Fish strains use `FISH-<key>`. Publications use
`pub_id` (`doi:<DOI>`, or `t:<normalised title>` when there is no DOI). Survey codes in the crosswalk are list positions that
change between survey rounds and must never be used as a join key on their own.

**Lists inside a cell.** A cell that holds several values separates them with a space, a vertical bar and a space (` | `).
Lists of field names, derived multi-valued categories (for example `season_std`, `breeding_method`, `region_divisions`) and
the quality flags use a semicolon (`; ` or `;`). In `bgd_nsb_decisions_full.csv`, sentences matched in the minutes are
separated by ` ‖ `, and in `bgd_publications.csv` per-author affiliations are separated by ` || `. No other structure is
packed into a cell; long-format detail is in the conflicts and evidence tables.

**Blank cells.** A blank cell means that no eligible source states the value. It never means zero, "no" or "none". A blank
`pedigree` means no pedigree has been published, not that the variety has no parents; a blank `feature_tags` together with
`trait_text_available = no` means there is no trait information, not that the variety lacks the traits; and a `cgiar_role`
of 5 means no CGIAR link is documented, not that there was none. Where a column is filled for only some kinds of varieties
(for example ecosystem and grain class, which the hybrid registration records rarely state), its coverage should be read
together with `rice_type` before any comparison between groups.

**Bangla text.** Names, trait statements, decision texts and list cells are kept as printed, in Unicode Bangla, including
Bangla digits, the source's spelling, spacing and hyphenation, and ditto marks (ঐ). Text from legacy Bijoy (SutonnyMJ) text
layers was converted to Unicode, and a misplaced reph introduced by the converter was repaired; nothing else was edited.
English columns ending in `_std`, `_en` or `_class`, the season flags and the numeric minimum and maximum columns are the
analysis-ready versions of these texts.

**Dates and numbers.** Dates are ISO dates (`YYYY-MM-DD`). When only the year is documented the cell holds the year alone
(`YYYY`) and the row is flagged `year_only`; a year must not be read as 1 January. `approval_date` is the date of the National
Seed Board decision, not the gazette date or the date of first cultivation. Columns that copy printed numbers (`duration_days`,
`yield_t_ha`, `yield_advantage_pct`) are text, because a cell may hold a range or several season-specific values; the derived
`_min_` and `_max_` columns hold the numbers. Units are given in the column descriptions: days for duration, tonnes per hectare
for yield, percent for shares, milligrams per kilogram for zinc and iron.

**Choice between sources.** The register is assembled from long-format evidence. A value is eligible only if it came from a
machine-readable text layer or was validated (`key_check`, `visual_check` or `two_source`); unvalidated OCR never enters the
register. Among eligible values the most authoritative source wins, by authority rank (`1_primary_legal` NSB minutes, Gazette,
acts; `2_official_list` SCA and MoA lists; `3_institute_page`; `4_cgiar_record`; `5_peer_reviewed`; `6_secondary`), then by
validation strength and confidence. Some descriptive fields use their own order: English names, popular names and pedigree
detail prefer the developing institute; season, ecosystem and key traits prefer the official lists; for approval dates a full
date beats a year and the earlier date wins a tie; for gazette dates the earliest notification is kept. Every competing version
is kept in `bgd_conflicts.csv`.

**Files.** All tables are UTF-8 CSV files with a byte-order mark, so that spreadsheet programs display Bangla correctly. Read
every column as text (for example `pandas.read_csv(path, dtype=str, keep_default_na=False)`) and convert the numeric columns
explicitly; otherwise codes such as `0` flags and years are silently retyped and blank cells become missing values.
"""


def esc(v):
    v = "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)
    v = v.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")      # '<key>' would otherwise vanish as an HTML tag
    return v.replace("\r", " ").replace("\n", " ").replace("|", "\\|").strip()


def coverage(series):
    return float(series.astype(str).str.strip().ne("").mean()) if len(series) else 0.0


def main():
    dd = pd.read_csv(DD_PATH, dtype=str, keep_default_na=False)
    tabs = pd.read_csv(TAB_PATH, dtype=str, keep_default_na=False)
    warnings = []
    md = ["# Bangladesh Rice Variety Register: data dictionary", "",
          f"Kushal Kumar, Cornell University. Generated {datetime.date.today().isoformat()} by `scripts/write_dictionary.py`.", "",
          PREFACE, "## Tables", "",
          "| table | unit of observation | rows |", "|---|---|---:|"]
    sections, updated = [], []
    for t in tabs.itertuples():
        fp = F / t.table
        cols = dd[dd.table == t.table]
        if not fp.exists():
            warnings.append(f"{t.table}: file not found; table skipped")
            continue
        private = t.table in PRIVATE
        if private:
            with open(fp, encoding="utf-8-sig", newline="") as fh:
                header = next(csv.reader(fh))
            data, nrows = None, None
        else:
            data = pd.read_csv(fp, dtype=str, keep_default_na=False)
            header, nrows = list(data.columns), len(data)
        documented = list(cols.column)
        for c in documented:
            if c not in header:
                warnings.append(f"{t.table}: documented column '{c}' is missing from the CSV")
        for c in header:
            if c not in documented:
                warnings.append(f"{t.table}: column '{c}' is in the CSV but not documented")
        rows_txt = "header only (personal data)" if private else f"{nrows:,}"
        md.append(f"| [{t.table}](#{t.table.replace('.', '').lower()}) | {esc(t.unit)} | {rows_txt} |")
        sec = [f"## {t.table}", "", f"*Unit of observation:* {esc(t.unit)}.", "", esc(t.description), ""]
        if private:
            sec += ["The rows of this table are not read when this dictionary is built, so coverage is not reported. "
                    "The columns are documented from scripts/build_attendance.py and the header line.", ""]
        else:
            sec += [f"The file has {nrows:,} rows and {len(header)} columns.", ""]
        sec += ["| column | meaning | values | coverage |", "|---|---|---|---:|"]
        by_col = cols.set_index("column")
        for c in header:
            if c not in by_col.index:
                sec.append(f"| `{c}` | *(not documented)* |  | {'' if private else f'{coverage(data[c]):.2f}'} |")
                continue
            r = by_col.loc[c]
            cov = "n/a" if private else f"{coverage(data[c]):.2f}"
            if not private:
                updated.append((t.table, c, f"{coverage(data[c]):.2f}"))
            sec.append(f"| `{c}` | {esc(r['meaning'])} | {esc(r['values'])} | {cov} |")
        sections += sec + [""]
    md += [""] + sections
    OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
    changed = sum(1 for tb, c, v in updated if dd.loc[(dd.table == tb) & (dd.column == c), "share_nonblank"].iloc[0] != v
                  if ((dd.table == tb) & (dd.column == c)).any())
    print(f"wrote {OUT}: {len(tabs)} tables, {len(dd)} documented columns; "
          f"{changed} coverage values differ from data_dictionary.csv (the Markdown uses the current files)")
    for w in warnings:
        print("WARNING:", w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
