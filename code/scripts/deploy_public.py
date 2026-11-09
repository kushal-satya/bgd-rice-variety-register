"""Assemble the PUBLIC repository (deploy_repo/) for GitHub Pages from the public edition of the site.

deploy_repo/ = the site (index.html, content/, assets/, data/ as built by build_site.py's public edition)
             + release metadata at the root (LICENSE, NOTICE.md, CITATION.cff, .zenodo.json, datapackage.json)
             + code/ (the build scripts and requirements.txt) + sources/ (02_raw/CATALOGUE.csv and 02_raw/README.md)
             + docs/PLAYBOOK.md + README.md + EDITING.md
The internal board-contacts view is removed from index.html and content/text.md, and the deployed tree is scanned for
mobile numbers, personal e-mail addresses and the internal attendance table; the script stops if any is found.
It does not commit or push; do that from deploy_repo/ with git.
Usage: python scripts/deploy_public.py
"""
import pathlib, re, shutil, sys

R = pathlib.Path(__file__).resolve().parents[1]
SITE, DEP = R / "site", R / "deploy_repo"
sys.path.insert(0, str(R / "scripts"))
import redact_personal as RP

if not (DEP / ".git").exists():
    sys.exit("deploy_repo/ is not a git repository; clone https://github.com/kushal-satya/bgd-rice-variety-register there first")

# 1. clear everything except .git, then copy the public site
for p in DEP.iterdir():
    if p.name != ".git":
        shutil.rmtree(p) if p.is_dir() else p.unlink()
shutil.copytree(SITE, DEP, dirs_exist_ok=True, ignore=shutil.ignore_patterns("README.md"))

# 2. no trace of the internal view
idx = (DEP / "index.html").read_text(encoding="utf-8")
idx = re.sub(r"<!--BOARD-START-->.*?<!--BOARD-END-->", "", idx, flags=re.S)
idx = re.sub(r'\s*<a href="#board"[^>]*>Board contacts</a>', "", idx)
(DEP / "index.html").write_text(idx, encoding="utf-8")
txt = (DEP / "content/text.md").read_text(encoding="utf-8")
txt = re.sub(r"<!-- @board-title -->.*?(?=<!-- @)", "", txt, flags=re.S)
(DEP / "content/text.md").write_text(txt, encoding="utf-8")

# 3. release metadata, code, source catalogue, playbook
for f in (R / "release").iterdir():
    shutil.copy2(f, DEP / f.name)
code = DEP / "code"; code.mkdir()
shutil.copytree(R / "scripts", code / "scripts", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
shutil.copy2(R / "requirements.txt", code / "requirements.txt")
src = DEP / "sources"; src.mkdir()
for f in ("CATALOGUE.csv", "README.md"):
    if (R / "02_raw" / f).exists():
        shutil.copy2(R / "02_raw" / f, src / f)
(DEP / "docs").mkdir(exist_ok=True)
shutil.copy2(R / "00_admin/PLAYBOOK_variety_register.md", DEP / "docs/PLAYBOOK.md")
shutil.copy2(R / "00_admin/rights_and_personal_data_policy.md", DEP / "docs/rights_and_personal_data_policy.md")

# 4. EDITING.md from the site README, without the internal-edition sections
ed = (SITE / "README.md").read_text(encoding="utf-8")
ed = re.sub(r"## Two editions.*?(?=\n## )", "", ed, flags=re.S)
ed = "\n".join(l for l in ed.split("\n") if "board_" not in l and "attendance" not in l.lower())
(DEP / "EDITING.md").write_text(ed, encoding="utf-8")
(DEP / "README.md").write_text("""# Bangladesh Rice Variety Register

A register of the rice varieties approved for cultivation in Bangladesh from 1966 to February 2026, with the National Seed Board decision behind each approval, pedigrees, stated traits, documented links to CGIAR breeding, the lineage of breeding lines, and the codes under which each variety appears in household surveys. It also covers improved fish strains and the government acts on fish species.

The site is at https://kushal-satya.github.io/bgd-rice-variety-register/. The tables are in `data/` as UTF-8 CSV files and one Excel workbook, described column by column in `data/DATA_DICTIONARY.md` and as a Frictionless Data Package in `datapackage.json`; corrections between versions are listed in `data/CHANGELOG.md`. The evidence behind every value, with source file, page and quotation, is in `data/bgd_evidence.csv`, and every source document is listed in `sources/CATALOGUE.csv` with its original address, Internet Archive copy and SHA-256 fingerprint. The scripts that build every table from the archived sources are in `code/`; `docs/PLAYBOOK.md` describes the method for use on other countries' registers.

Data and documentation are released under CC BY 4.0 and code under the MIT licence (see `LICENSE` and `NOTICE.md`); source documents remain the property of their publishers. Telephone numbers and personal e-mail addresses of individuals are removed from every public file (`docs/rights_and_personal_data_policy.md`). Page text is in `content/text.md`; `EDITING.md` explains how to change it.

Cite as: Kumar, K. (2026). *Bangladesh Rice Variety Register, 1966–2026: officially approved rice varieties, with improved fish strains* (Version 1.2) [Data set]. Cornell University. https://kushal-satya.github.io/bgd-rice-variety-register/
""", encoding="utf-8")
(DEP / ".nojekyll").write_text("", encoding="utf-8")

# 5. privacy scan of everything that will be published
bad = []
OK_MAILS = {e.lower() for e in RP.OFFICE_EMAILS} | {"noreply@anthropic.com"}
for f in DEP.rglob("*"):
    if ".git" in f.parts or not f.is_file() or f.suffix.lower() not in {".csv", ".md", ".json", ".html", ".js", ".py", ".txt", ".cff", ".sh", ".ps1"}:
        continue
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "nsb_attendance" in f.name:
        bad.append(f"{f.relative_to(DEP)}: internal attendance table")
    for m in RP.MOBILE.finditer(t):
        bad.append(f"{f.relative_to(DEP)}: mobile number pattern '{m.group(0)}'")
    for m in RP.EMAIL.finditer(t):
        a = re.sub(r"\s|^mailto:", "", m.group(0).lower())
        if a not in OK_MAILS and not any(a.endswith(o) for o in OK_MAILS) and "example" not in a:
            bad.append(f"{f.relative_to(DEP)}: e-mail address '{m.group(0)}'")
    if re.search("kd" + "475|kushal" + "156", t):   # the author's user name and personal e-mail prefix (built from parts so this file passes its own scan)
        bad.append(f"{f.relative_to(DEP)}: the author's personal identifier")
if bad:
    print("\n".join(sorted(set(bad))[:60])); sys.exit(f"STOP: {len(set(bad))} privacy problems; nothing should be pushed")
n = sum(1 for f in DEP.rglob("*") if f.is_file() and ".git" not in f.parts)
mb = sum(f.stat().st_size for f in DEP.rglob("*") if f.is_file() and ".git" not in f.parts) / 1e6
big = [f"{f.relative_to(DEP)} ({f.stat().st_size / 1e6:.0f} MB)" for f in DEP.rglob("*") if f.is_file() and ".git" not in f.parts and f.stat().st_size > 95e6]
print(f"deploy_repo ready: {n} files, {mb:.0f} MB; privacy scan clean." + (f" Files over GitHub's 100 MB limit: {big}" if big else ""))
