"""Append rows to FS search log. Usage: python phase0_DS_log.py rows.json
rows.json: list of [engine_site, query, language, n_results, useful_hits, notes]"""
import csv, json, os, sys, datetime
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[1])
P = os.path.join(ROOT, "01_discovery", "_parts", "FS_search_log.csv")
cols = ["date", "agent", "engine_site", "query", "language", "n_results", "useful_hits", "notes"]
new = not os.path.exists(P)
rows = json.load(open(sys.argv[1], encoding="utf-8"))
with open(P, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new:
        w.writerow(cols)
    for r in rows:
        w.writerow([datetime.date.today().isoformat(), "FS"] + r)
print(sum(1 for _ in open(P, encoding="utf-8")) - 1, "rows")
