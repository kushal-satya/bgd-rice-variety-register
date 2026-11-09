"""Link hygiene applied to every final table (called from make_final.py).

1. Strip the polite-pool e-mail parameter (mailto=...) from any URL.
2. Replace links that do not work for readers with a working equivalent, from 04_working/link_fixes.csv
   (old_url -> new_url, with reason): Europe PMC pages that block automated access -> DOI; DOIs printed by a
   publisher but never registered -> the publisher's article page.
3. Add a status for each row's primary links, from 06_validation/link_audit_results.csv:
   ok | blocked_to_bots (403: page exists but refuses automated checks) | dead (404/410/soft error) |
   unreachable (DNS/TLS/timeout) | unchecked.
"""
import re
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAILTO = re.compile(r"([?&])mailto=[^&\s|]+&?")
FIX = ROOT / "04_working/link_fixes.csv"
AUD = ROOT / "06_validation/link_audit_results.csv"

fixes = pd.read_csv(FIX, dtype=str).fillna("") if FIX.exists() else pd.DataFrame(columns=["old_url", "new_url", "reason"])
FIXMAP = dict(zip(fixes.old_url, fixes.new_url))
aud = pd.read_csv(AUD, dtype=str).fillna("") if AUD.exists() else pd.DataFrame(columns=["url", "verdict"])
VERDICT = dict(zip(aud.url, aud.verdict))
STATUS = {"ok": "ok", "blocked_403": "blocked_to_bots", "dead_404": "dead", "dead_410": "dead", "soft_error_page": "dead",
          "unreachable": "unreachable", "doi_not_registered": "dead", "rate_limited": "unchecked"}


def clean_url(u):
    u = MAILTO.sub(lambda m: m.group(1) if m.group(0).endswith("&") else "", u).rstrip("?&")
    return FIXMAP.get(u, u)


def clean_cell(v):
    if not isinstance(v, str) or "http" not in v:
        return v
    if " | " in v:
        return " | ".join(dict.fromkeys(clean_url(x.strip()) for x in v.split(" | ")))
    if v.strip().startswith("http") and "\n" not in v:
        return clean_url(v.strip())
    return MAILTO.sub(lambda m: m.group(1) if m.group(0).endswith("&") else "", v)


def status(u):
    if not u:
        return ""
    return STATUS.get(VERDICT.get(u, ""), "unchecked")


def apply(df, primary_cols=("source_url", "archived_url")):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].map(clean_cell)
    for c in primary_cols:
        if c in df.columns:
            df[c + "_status"] = df[c].map(status)
    return df


def clean_doi(d):
    """Repair DOIs mangled by extraction: trailing '.html', a duplicated prefix ('10.x/10.x/...'), URL forms."""
    d = (d or "").strip()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    d = re.sub(r"\.html?$", "", d)
    m = re.match(r"^(10\.\d{4,9})/(10\.\d{4,9}/.+)$", d)
    if m:
        d = m.group(2)
    return d


def apply_literature(df):
    """Literature/publications: link the DOI when the publisher URL is dead; keep the dead address in its own column.
    REV2 (v1.2, review A7-24): Crossref and OpenAlex return 1970-01-01 as the issue date of many Bangladesh Journals Online
    (DOI prefix 10.3329) and other articles whose volumes appeared decades later; that year is a placeholder, so it is blanked
    and year_note says why. No other source of the year is archived locally."""
    df = df.copy()
    if "year" in df.columns:
        ph = df["year"].astype(str).eq("1970")
        if "year_note" not in df.columns:
            df["year_note"] = ""
        df.loc[ph, "year_note"] = "year unknown: the bibliographic API gives 1970-01-01, a placeholder date"
        df.loc[ph, "year"] = ""
    if "doi" in df.columns:
        df["doi"] = df["doi"].map(clean_doi)
        df["doi_status"] = df["doi"].map(lambda d: status("https://doi.org/" + d) if d else "")
    for c in ("url", "open_access_url"):
        if c not in df.columns:
            continue
        st = df[c].map(status)
        dead = st.isin(["dead", "unreachable"])
        prev = df[c + "_dead"] if c + "_dead" in df.columns else pd.Series("", index=df.index)
        df[c + "_dead"] = prev.where(prev.astype(str).ne(""), df[c].where(dead, ""))   # idempotent across re-runs
        if c == "url" and "doi" in df.columns:
            ok_doi = df["doi"].ne("") & df["doi_status"].isin(["ok", "unchecked"])
            df.loc[dead & ok_doi, c] = "https://doi.org/" + df.loc[dead & ok_doi, "doi"]
            df.loc[dead & ~ok_doi, c] = ""
        else:
            df.loc[dead, c] = ""
    return df
