"""Build the website in two editions from one set of page files (site/index.html, content/text.md, assets/).

internal (default target for the research panel)
  site_internal/                                   full data, including the NSB attendance and contacts table
  05_output/final/rice_register_internal.html      the same page as one self-contained file
  05_output/final/rice_register.html               page body for the claude.ai artifact (private link)
public (safe to put on open GitHub Pages)
  site/data/                                       mobile numbers and webmail addresses removed (redact_personal.py),
                                                   no attendance table; the Board contacts section stays hidden
  05_output/final/rice_register_standalone.html    the public page as one self-contained file

site/ holds the editable page files; site_internal/ is a generated copy of them plus the internal data, so edit
site/content/text.md and rebuild, never the copy."""
import json
import pathlib
import re
import shutil
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import redact_personal as RP

R = pathlib.Path(__file__).resolve().parents[1]
SITE, INTERNAL, FINAL = R / "site", R / "site_internal", R / "05_output/final"
EXTRA = ["DATA_DICTIONARY.md", "CHANGELOG.md", "bgd_variety_archive.xlsx"]

base = json.loads((FINAL / "viz_data.json").read_text(encoding="utf-8"))
qa = (R / "06_validation/qa_checks.md").read_text(encoding="utf-8")
base["n_qa_checks"] = len(re.findall(r"^\|[^|]+\|\s*(PASS|FAIL)\s*\|", qa, re.M))
# survey codes under which each variety appears (crosswalk; matched on label, so codes differ between rounds)
cw_fp = FINAL / "bgd_variety_crosswalk.csv"
if cw_fp.exists():
    cw = pd.read_csv(cw_fp, dtype=str, keep_default_na=False)
    cw = cw[cw.variety_id.ne("")]
    SRC0 = {"BIHS2011_12": "BIHS 2011–12", "BIHS2015": "BIHS 2015", "BIHS2018_19": "BIHS 2018–19", "BIHS2024_SPIA": "BIHS 2024 (SPIA)",
            "MIXTAPE2026_draft": "MIXTAPE 2026, March and May drafts", "MIXTAPE2026_0821": "MIXTAPE 2026, 21 August draft", "MIXTAPE2026_CAPI": "MIXTAPE 2026, CAPI forms (October)", "SPIA_DNA_reference": "SPIA DNA reference sample"}
    codes = (cw.assign(t=cw.source.map(SRC0).fillna(cw.source) + " code " + cw.code)
               .groupby("variety_id").t.apply(lambda s: " | ".join(dict.fromkeys(s))))
    for row in base["rice"]:
        row["survey_codes"] = codes.get(row["variety_id"], "")
# parents, later decisions and legal status per variety, for the record view
pe_fp = FINAL / "bgd_pedigree_edges.csv"
if pe_fp.exists():
    par = {}
    for r in pd.read_csv(pe_fp, dtype=str, keep_default_na=False).itertuples():
        par.setdefault(r.child_id, []).append(dict(l=r.parent_label_as_printed, id=r.parent_id, role=r.parent_role, cg=r.parent_is_cgiar_line,
                                                  c=r.parent_cgiar_center, dose=r.backcross_dose))
    base["parents"] = par
ev_fp = FINAL / "bgd_variety_events.csv"
if ev_fp.exists():
    evs = {}
    for r in pd.read_csv(ev_fp, dtype=str, keep_default_na=False).itertuples():
        evs.setdefault(r.variety_id, []).append(dict(d=r.event_date, m=r.meeting_no, t=r.event_type, x=r.detail))
    base["events"] = evs
# how the survey code lists match the register, by source
SRC = {"BIHS2011_12": "BIHS 2011–12", "BIHS2015": "BIHS 2015", "BIHS2018_19": "BIHS 2018–19", "BIHS2024_SPIA": "BIHS 2024 (SPIA)",
       "MIXTAPE2026_draft": "MIXTAPE 2026, March and May drafts", "MIXTAPE2026_0821": "MIXTAPE 2026, 21 August draft", "MIXTAPE2026_CAPI": "MIXTAPE 2026, CAPI forms (October)", "SPIA_DNA_reference": "SPIA DNA reference sample"}
if cw_fp.exists():
    cwall = pd.read_csv(cw_fp, dtype=str, keep_default_na=False)
    grp = lambda m: "resolved" if m in ("exact_code_name", "normalised_name", "alias") else m
    cs = cwall.assign(g=cwall.match_type.map(grp)).groupby(["source", "g"]).size().unstack(fill_value=0)
    base["crosswalk_summary"] = [dict(source=s, label=SRC.get(s, s), n=int(row.sum()),
                                      **{k: int(row.get(k, 0)) for k in ["resolved", "brand_family", "not_approved_variety", "generic_label", "unmatched"]})
                                 for s, row in cs.iterrows()]
# fields on which sources disagree, with the most common kind of disagreement
cf_fp = FINAL / "bgd_conflicts_summary.csv"
if cf_fp.exists():
    cf = pd.read_csv(cf_fp, dtype=str, keep_default_na=False)
    base["conflicts_by_field"] = sorted([dict(field=f, n=int(x.variety_id.nunique()), top=x.classification.value_counts().index[0])
                                         for f, x in cf.groupby("field")], key=lambda z: -z["n"])
# pedigree graph for the lineage view (build_pedigree.py)
lg_fp = FINAL / "bgd_lineage_graph.json"
if lg_fp.exists():
    g = json.loads(lg_fp.read_text(encoding="utf-8"))
    base["lineage"] = {"nodes": [{k: n.get(k, "") for k in ("id", "label", "kind", "year", "cgiar_center", "parent_type")} for n in g["nodes"]],
                       "edges": [{k: e.get(k, "") for k in ("source", "target", "role", "basis")} for e in g["edges"]]}
# rice plot reports in household surveys: matching coverage and CGIAR categories (built by build_crosswalk.py)
VAL = R / "06_validation"
fp = VAL / "crosswalk_plot_coverage.csv"
if fp.exists():
    pc = pd.read_csv(fp, dtype=str, keep_default_na=False)
    base["plot_coverage"] = pc[pc.season.eq("all")].to_dict("records") if "season" in pc else pc.to_dict("records")
fp = VAL / "crosswalk_plot_cgiar.csv"
if fp.exists():
    pg = pd.read_csv(fp, dtype=str, keep_default_na=False)
    pg = pg[pg.season.eq("all")]
    # one set of categories per round, matching the generations figure: depth for CGIAR-linked varieties,
    # the CGIAR code for the rest, then brand families, never-approved names and residual codes
    pick = {("depth_to_cgiar", "register depth_to_cgiar 0"): "d0", ("depth_to_cgiar", "register depth_to_cgiar 1"): "d1",
            ("depth_to_cgiar", "register depth_to_cgiar 2"): "d2", ("depth_to_cgiar", "register depth_to_cgiar 3+"): "d3",
            ("cgiar_role", "register cgiar_role 3"): "collab", ("cgiar_role", "register cgiar_role 4"): "none",
            ("cgiar_role", "register cgiar_role 5"): "unknown", ("cgiar_role", "brand_family"): "brand_family",
            ("cgiar_role", "other_unknown"): "other"}
    rows = []
    for rd, g in pg.groupby("round", sort=False):
        for (dim, cat), key in pick.items():
            x = g[(g.dimension == dim) & (g.category == cat)]
            if len(x):
                rows.append(dict(round=rd, cat=key, n=x.n_plots.iloc[0], share=x.share.iloc[0], denom=x.denominator.iloc[0]))
        na = g[(g.dimension == "cgiar_role") & g.category.str.startswith("not_approved_name")]
        if len(na):
            rows.append(dict(round=rd, cat="not_approved", n=str(na.n_plots.astype(int).sum()), share=str(na.share.astype(float).sum()), denom=na.denominator.iloc[0]))
    for x in rows:
        x["round"] = {"SPIA 2024": "BIHS 2024 (SPIA)"}.get(x["round"], x["round"])
    base["plot_cgiar"] = rows
    top = pg[pg.dimension == "top10_register_variety"]
    base["plot_top"] = top[["round", "variety_id", "variety_name", "cgiar_role", "share"]].to_dict("records")
att_fp = FINAL / "bgd_nsb_attendance.csv"
attendance = pd.read_csv(att_fp, dtype=str, keep_default_na=False).to_dict("records") if att_fp.exists() else []

css = (SITE / "assets/style.css").read_text(encoding="utf-8")
js = (SITE / "assets/app.js").read_text(encoding="utf-8").replace("</", "<\\/")
text = (SITE / "content/text.md").read_text(encoding="utf-8")
page = (SITE / "index.html").read_text(encoding="utf-8")
safe = lambda s: s.replace("<", "\\u003c")   # JSON strings cannot then close the script element


def public_page(html):
    """The public edition carries no trace of the internal board-contacts view: markup and nav link are removed."""
    html = re.sub(r"<!--BOARD-START-->.*?<!--BOARD-END-->", "", html, flags=re.S)
    return re.sub(r'\s*<a href="#board"[^>]*>Board contacts</a>', "", html)


def single_file(d, page=page):
    d = dict(d, download_base=None)          # no data folder beside a single file: file names without links
    body = page[page.index("<body>") + len("<body>"):page.index("</body>")]
    body = body.replace('<script src="assets/app.js"></script>',
                        "<script>window.__SITE_TEXT__=" + safe(json.dumps(text, ensure_ascii=False)) + ";\n"
                        "window.__SITE_DATA__=" + safe(json.dumps(d, ensure_ascii=False, separators=(",", ":"))) + ";</script>\n"
                        "<script>\n" + js + "</script>")
    head = page[:page.index("</head>")].replace('<link rel="stylesheet" href="assets/style.css">', "<style>\n" + css + "</style>")
    return head + "</head>\n<body>" + body + "</body>\n</html>\n", "<style>\n" + css + "</style>\n" + body


def data_folder(folder, d, files, redact):
    data = folder / "data"
    if data.exists():
        shutil.rmtree(data)
    data.mkdir(parents=True)
    for f in files:
        src = FINAL / f
        if not src.exists():
            continue
        if redact and f.endswith(".csv"):
            RP.public_table(f, pd.read_csv(src, dtype=str, keep_default_na=False)).to_csv(data / f, index=False, encoding="utf-8-sig")
        elif redact and f.endswith(".xlsx"):
            RP.redact_xlsx(src, data / f)
        else:
            shutil.copy2(src, data / f)
    (data / "site_data.json").write_text(json.dumps(dict(d, download_base="data/"), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def report(*paths):
    for p in paths:
        print(p.relative_to(R), round(p.stat().st_size / 1024), "KB")


listed = [x["file"] for x in base["files"]]
# the documentation and metadata files offered beside the tables (rows in the files table, with their own paths)
DOCS = [("bgd_variety_archive.xlsx", "data/", "All tables in one Excel workbook, with a README sheet and the data dictionary", "Workbook"),
        ("DATA_DICTIONARY.md", "data/", "Every column of every table: meaning, values, source and coverage", "Column"),
        ("CHANGELOG.md", "data/", "Corrections and additions between versions", "Version"),
        ("datapackage.json", "", "Machine-readable description of every table (Frictionless Data Package)", "Table"),
        ("sources/CATALOGUE.csv", "", "Every source document: title, issuer, date, type, original address, Internet Archive copy, SHA-256", "Source document"),
        ("LICENSE", "", "Licence: CC BY 4.0 for data and documentation, MIT for code", ""),
        ("CITATION.cff", "", "Citation metadata", "")]
for name, folder, desc, unit in DOCS:
    src = {"datapackage.json": R / "release/datapackage.json", "sources/CATALOGUE.csv": R / "02_raw/CATALOGUE.csv",
           "LICENSE": R / "release/LICENSE", "CITATION.cff": R / "release/CITATION.cff"}.get(name, FINAL / name)
    if src.exists():
        base["files"].append(dict(file=name, path=folder + name, desc=desc, unit=unit, rows="", cols="", mb=round(src.stat().st_size / 1e6, 1)))
# local copies so the links also work when site/ is served on its own
for name, src in [("datapackage.json", R / "release/datapackage.json"), ("LICENSE", R / "release/LICENSE"), ("CITATION.cff", R / "release/CITATION.cff"),
                  ("NOTICE.md", R / "release/NOTICE.md"), ("sources/CATALOGUE.csv", R / "02_raw/CATALOGUE.csv")]:
    if src.exists():
        (SITE / name).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, SITE / name)

# ---- internal edition ----
internal = dict(base, attendance=attendance)
if attendance:
    internal["files"] = base["files"] + [dict(file=att_fp.name, desc="Attendance at National Seed Board meetings, with posts and contact details as written on the sheets (internal)",
                                              unit="Attendee-meeting", rows=len(attendance), cols=len(attendance[0]), mb=round(att_fp.stat().st_size / 1e6, 1))]
if INTERNAL.exists():
    shutil.rmtree(INTERNAL)
shutil.copytree(SITE, INTERNAL, ignore=shutil.ignore_patterns("data"))
data_folder(INTERNAL, internal, listed + ["bgd_nsb_attendance.csv"] + EXTRA, redact=False)
full, body = single_file(internal)
(FINAL / "rice_register_internal.html").write_text(full, encoding="utf-8")
(FINAL / "rice_register.html").write_text(body, encoding="utf-8")

# ---- public edition: scrub personal contacts everywhere, including the verbatim NSB text shown in the register ----
public = json.loads(RP.text(json.dumps(base, ensure_ascii=False)))
for decs in public.get("decisions", {}).values():      # verbatim minutes text: the stricter free-text rule
    for x in decs:
        for k in ("h", "p", "dec"):
            if isinstance(x.get(k), str):
                x[k] = RP.free_text(x[k])
for r in public.get("rice", []):   # every free-text field (v1.3: the *_source columns of derive_attributes quote OCR text)
    for k in list(r):
        if isinstance(r.get(k), str) and not RP.NOT_TEXT_COLUMN.search(k):
            r[k] = RP.free_text(r[k])
public["attendance"] = []
data_folder(SITE, public, listed + EXTRA, redact=True)
_dd = (SITE / "data/DATA_DICTIONARY.md").read_text(encoding="utf-8")   # the public dictionary does not describe the internal attendance table
_dd = re.sub(r"\n## bgd_nsb_attendance\.csv\n.*?(?=\n## |\Z)", "\n", _dd, flags=re.S)
_dd = "\n".join(l for l in _dd.split("\n") if "bgd_nsb_attendance" not in l)
(SITE / "data/DATA_DICTIONARY.md").write_text(_dd, encoding="utf-8")
full_pub, body_pub = single_file(public, public_page(page))
(FINAL / "rice_register_public_body.html").write_text(body_pub, encoding="utf-8")   # public page body for a hosted preview
(FINAL / "rice_register_standalone.html").write_text(full_pub, encoding="utf-8")

report(INTERNAL / "data/site_data.json", FINAL / "rice_register_internal.html", FINAL / "rice_register.html",
       SITE / "data/site_data.json", FINAL / "rice_register_standalone.html")
print("attendance rows (internal only):", len(attendance))
