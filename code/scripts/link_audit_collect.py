"""Collect every URL that appears in the final outputs, with where it appears.

Link columns are read whole (official file names contain spaces, commas and brackets, so a regex would cut them);
' | '-separated lists are split; URLs inside free text are found with a regex."""
import re
import pathlib
import urllib.parse
import pandas as pd

F = pathlib.Path("05_output/final")
URL = re.compile(r"https?://[^\s|;,\"'<>\]\)]+")
rows = []
for f in ["bgd_rice_varieties.csv", "bgd_sources.csv", "bgd_cgiar_sources.csv", "bgd_fish_strains.csv", "bgd_fish_events.csv",
          "bgd_fish_approvals.csv", "bgd_literature.csv", "bgd_institutions.csv", "bgd_variety_people.csv", "bgd_local_names.csv"]:
    fp = F / f
    if not fp.exists():
        continue
    d = pd.read_csv(fp, dtype=str).fillna("")
    for c in d.columns:
        for v in d[c]:
            v = v.strip()
            if "http" not in v:
                continue
            items = [x.strip() for x in v.split(" | ")]
            if all(x.startswith("http") for x in items) and c.endswith(("url", "_urls", "website", "url_as_printed")):
                parts = items                              # whole cell(s) are URLs, keep spaces/commas/brackets
            else:
                parts = URL.findall(v)                     # URL embedded in free text
            for u in parts:
                rows.append((u.rstrip("."), f, c))
    for c in ("doi_key_paper", "doi"):
        if c in d:
            for v in d[c]:
                for doi in re.findall(r"10\.\d{4,9}/[^\s|;]+", v):
                    rows.append(("https://doi.org/" + doi.rstrip(".,"), f, c))
u = pd.DataFrame(rows, columns=["url", "file", "column"])
g = u.groupby("url").agg(n_refs=("file", "size"), where=("file", lambda s: "; ".join(sorted(set(s)))),
                         columns=("column", lambda s: "; ".join(sorted(set(s))))).reset_index()
g["host"] = g.url.map(lambda x: urllib.parse.urlparse(x).hostname or "")
g.to_csv("06_validation/link_audit_urls.csv", index=False, encoding="utf-8-sig")
print(len(g), "unique URLs")
print(g.host.value_counts().head(12).to_string())
