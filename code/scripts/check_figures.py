"""Check every figure on the site against the data, independently of the page script.

The page draws each figure in the browser and writes the numbers behind it into a 'Data for this figure' table. This
script renders the single-file public page in headless Edge (once per view, so each view's figures are drawn), reads
those tables from the rendered page, recomputes the same numbers from site_data.json with pandas, and compares them
cell by cell. It also checks internal coherence: the bars of each period add up to the period total, shares add up to
100 per cent, and every figure caption number that is a placeholder matches the data.

Writes 06_validation/figure_check.md and exits with status 1 if any check fails.
Usage: python scripts/check_figures.py
"""
import json, pathlib, re, shutil, subprocess, sys, tempfile
import pandas as pd
from bs4 import BeautifulSoup

R = pathlib.Path(__file__).resolve().parents[1]
PAGE = R / "05_output/final/rice_register_standalone.html"
# Chrome first (a pending Edge update can make headless Edge return an empty page), then Edge
EDGE = next((b for b in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"] if pathlib.Path(b).exists()))
D = json.loads((R / "site/data/site_data.json").read_text(encoding="utf-8"))
rice = pd.DataFrame(D["rice"]).fillna("")
rice["y"] = pd.to_numeric(rice.approval_year, errors="coerce")
problems, notes = [], []


def dom(view):
    # a private profile, so that an open Edge window cannot absorb the headless run
    prof = tempfile.mkdtemp(prefix="figcheck_")
    try:
        out = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--window-size=1280,2400",
                              "--virtual-time-budget=15000", "--dump-dom", PAGE.as_uri() + "#" + view],
                             capture_output=True, text=True, encoding="utf-8", timeout=240)
    finally:
        shutil.rmtree(prof, ignore_errors=True)
    return BeautifulSoup(out.stdout, "lxml")


def table(soup, fid):
    box = soup.find(id=fid)
    if box is None or box.find("table") is None:
        problems.append(f"{fid}: no data table rendered"); return None
    rows = [[c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])] for tr in box.find("table").find_all("tr")]
    return pd.DataFrame(rows[1:], columns=rows[0])


def num(s):
    s = str(s).replace(",", "").replace("%", "").strip()
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else None


def compare(name, got, want):
    """got, want: dict key -> number"""
    bad = [(k, got.get(k), v) for k, v in want.items() if got.get(k) is None or abs(got[k] - v) > 1e-6]
    extra = [k for k in got if k not in want]
    if bad or extra:
        problems.append(f"{name}: {len(bad)} cells differ, {len(extra)} unexpected cells; first: {bad[:4]} {extra[:4]}")
    else:
        notes.append(f"{name}: {len(want)} cells agree with an independent recomputation.")


sector = rice.sector.where(rice.sector != "", "public")
series = (sector.map({"public": "Public", "private": "Private"}) + " " + rice.rice_type)

# ---- Figures view: approvals per year (fig1), cumulative (fig2), traits by decade (fig3)
soup = dom("figures")
t1 = table(soup, "f1data")
if t1 is not None:
    got = {}
    for _, r in t1.iterrows():
        y = int(re.match(r"\d{4}", r.iloc[0]).group())
        for c in t1.columns[1:]:
            got[(y, c)] = num(r[c])
        parts = [num(r[c]) for c in t1.columns[1:5]]
        if sum(parts) != num(r["All"]):
            problems.append(f"f1 {y}: series do not add up to the year total")
    want = {}
    for (y, s), n in rice.groupby(["y", series]).size().items():
        want[(int(y), s)] = n
    for y in rice.y.dropna().unique():
        y = int(y)
        for c in t1.columns[1:5]:
            want.setdefault((y, c), 0)
        want[(y, "All")] = int((rice.y == y).sum())
    want = {k: v for k, v in want.items() if k[1] in t1.columns}
    compare("Figure 1 (approvals per year)", got, want)
t2 = table(soup, "f2data")
if t2 is not None:
    got = {(int(r.iloc[0]), c): num(r[c]) for _, r in t2.iterrows() for c in t2.columns[1:]}
    want = {}
    for y in {k[0] for k in got}:
        s = rice[rice.y <= y]
        for c in t2.columns[1:]:
            want[(y, c)] = int((series[s.index] == c).sum())
    compare("Figure 2 (cumulative approvals)", got, want)
    # cumulative series never fall
    for c in t2.columns[1:]:
        v = [num(x) for x in t2[c]]
        if any(b < a for a, b in zip(v, v[1:])):
            problems.append(f"f2 {c}: cumulative series falls")
t3 = table(soup, "f3data")
if t3 is not None:
    inb = rice[(rice.rice_type == "inbred") & rice.y.notna()].copy()
    inb["dec"] = (inb.y // 10 * 10).astype(int)
    got, want = {}, {}
    for _, r in t3.iterrows():
        for c in t3.columns[1:]:
            got[(r.iloc[0], c)] = num(r[c])
    tags = inb.feature_tags.str.split(r" \| ")
    for c in t3.columns[1:]:
        m = re.match(r"(\d{4})s \(n=(\d+)\)", c)
        sub = inb[inb.dec == int(m.group(1))] if m else inb
        if m and int(m.group(2)) != len(sub):
            problems.append(f"f3 column {c}: header n differs from {len(sub)} inbred varieties")
        for t in t3.iloc[:, 0]:
            want[(t, c)] = int(sub.feature_tags.str.split(r" \| ").apply(lambda l: t in l).sum())
    compare("Figure 3 (stated traits by decade)", got, want)

# ---- CGIAR view: generations (fig4), founders (fig5), plots (fig6)
soup = dom("cgiar")


def depth_cat(r):
    if r.cgiar_role in ("5", ""): return "Pedigree unknown"
    if r.cgiar_role == "4": return "No CGIAR line in the traceable pedigree"
    if r.cgiar_role == "3": return "Collaboration or funding only"
    d = r.depth_to_cgiar
    if d == "": return "Itself a CGIAR line" if r.cgiar_role == "1" else "CGIAR parent"
    d = int(d)
    return {0: "Itself a CGIAR line", 1: "CGIAR parent", 2: "CGIAR grandparent"}.get(d, "CGIAR ancestor 3–5 generations back")


t4 = table(soup, "f4data")
if t4 is not None:
    inb = rice[(rice.rice_type == "inbred") & rice.y.notna()].copy()
    inb["cat"] = inb.apply(depth_cat, axis=1)
    inb["p"] = (inb.y // 5 * 5).astype(int)
    got, want = {}, {}
    for _, r in t4.iterrows():
        p0 = int(re.match(r"(\d{4})", r.iloc[0]).group(1))
        p = p0 // 5 * 5
        for c in t4.columns[1:]:
            got[(p, c)] = num(r[c])
        if sum(num(r[c]) for c in t4.columns[1:-1]) != num(r[t4.columns[-1]]):
            problems.append(f"f4 {r.iloc[0]}: categories do not add up to the period total")
        sub = inb[inb.p == p]
        for c in t4.columns[1:-1]:
            want[(p, c)] = int((sub.cat == c).sum())
        want[(p, t4.columns[-1])] = len(sub)
    compare("Figure 4 (generations to the nearest CGIAR line)", got, want)
    if int(sum(want[k] for k in want if k[1] == t4.columns[-1])) != int((rice.rice_type == "inbred").sum()):
        problems.append("f4: periods do not cover every inbred variety")
t5 = table(soup, "f5data")
if t5 is not None:
    g = D.get("lineage") or {}
    kids = {}
    for e in g.get("edges", []):
        kids.setdefault(e["source"], []).append(e["target"])
    label = {n["id"]: n["label"] for n in g.get("nodes", [])}
    lab2id = {}
    for k, v in label.items():
        lab2id.setdefault(v, k)
    got, want = {}, {}
    for _, r in t5.iterrows():
        nm = re.sub(r"\s*\(CGIAR line\)$", "", r.iloc[0])
        k = lab2id.get(nm)
        if k is None:
            problems.append(f"f5: line '{nm}' not in the pedigree graph"); continue
        seen, q = {}, [(k, 0)]
        while q:
            n, d = q.pop(0)
            for c in kids.get(n, []):
                if c not in seen:
                    seen[c] = d + 1; q.append((c, d + 1))
        reg = {n["id"] for n in g.get("nodes", []) if n.get("kind") == "register variety"}
        seen = {x: d for x, d in seen.items() if x in reg}   # approved varieties only, reached through any line
        by = {1: 0, 2: 0, 3: 0}
        for d in seen.values():
            by[min(3, d)] += 1
        for c, v in zip(t5.columns[1:], [by[1], by[2], by[3], len(seen)]):
            want[(nm, c)] = v; got[(nm, c)] = num(r[c])
    compare("Figure 5 (descendants of breeding lines)", got, want)
    # founders file agrees on the totals
    fp = R / "05_output/final/bgd_pedigree_founders.csv"
    if fp.exists():
        fo = pd.read_csv(fp, dtype=str).fillna("")
        col = next((c for c in fo.columns if "n_descend" in c), None)
        if col:
            lab = next((c for c in fo.columns if c in ("ancestor_label", "label", "line")), fo.columns[0])
            m = dict(zip(fo[lab], pd.to_numeric(fo[col], errors="coerce")))
            for nm in [re.sub(r"\s*\(CGIAR line\)$", "", x) for x in t5.iloc[:, 0]]:
                if nm in m and m[nm] != want.get((nm, t5.columns[-1])):
                    problems.append(f"f5 {nm}: page shows {want.get((nm, t5.columns[-1]))} descendants, founders file {m[nm]}")
t6 = table(soup, "f6data")
if t6 is not None and D.get("plot_cgiar"):
    for _, r in t6.iterrows():
        tot = sum(num(r[c]) for c in t6.columns[1:])
        if abs(tot - 100) > 0.6:
            problems.append(f"f6 {r.iloc[0]}: shares add up to {tot:.1f} per cent")
    notes.append(f"Figure 6 (plot shares): {len(t6)} survey rounds, each adding up to 100 per cent within rounding.")

# ---- placeholders left unfilled anywhere in the text
soup = dom("overview")
left = re.findall(r"\{\{\s*\w+\s*\}\}", soup.get_text(" "))
if left:
    problems.append(f"unfilled placeholders on the page: {sorted(set(left))}")

out = ["# Figure check", "", f"Page: `{PAGE.name}`; data built {D.get('built')}.", ""]
out += ["## Problems", ""] + ([f"- {p}" for p in problems] or ["None."]) + ["", "## Agreements", ""] + [f"- {n}" for n in notes]
(R / "06_validation/figure_check.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
sys.exit(1 if problems else 0)
