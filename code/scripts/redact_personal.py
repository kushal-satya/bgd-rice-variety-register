"""Remove personal contact details for the PUBLIC edition of the website (scripts/build_site.py) and of any public deposit.

The research tables in 05_output/final keep everything; this is applied only to copies meant for open publication.
The rule is set out in 00_admin/rights_and_personal_data_policy.md; change the two together.

The OCR corpus includes the attendance sheets (হাজিরা) of NSB and Technical Committee meetings, on which officials write
their mobile numbers and personal e-mail addresses. The internal edition keeps them (bgd_nsb_attendance.csv is built from
these sheets for the research panel). In the public edition:
- Bangladeshi mobile numbers (Latin or Bangla digits, with or without +88) are replaced with a marker;
- every e-mail address is replaced with a marker, except the institutional office addresses printed on letterheads and
  official contact pages that are listed in OFFICE_EMAILS (role mailboxes such as dg@brri.gov.bd, not named people);
- OpenAlex/Crossref polite-pool parameters (mailto=...) are removed from addresses;
- public_table() also drops the columns that hold individuals' contact details (professional_email and
  professional_phone in bgd_variety_people.csv); institution switchboards and role mailboxes in bgd_institutions.csv stay.
Office landlines printed on letterheads are institutional numbers and are kept. Names and posts of officials as printed
in public records are kept.

Functions used by the build: text(s), redact(df), redact_xlsx(src, dst), public_table(name, df).
"""
import pathlib
import re
import sys

import pandas as pd

MOBILE = re.compile(r"(?<![\d০-৯])(?:\+?(?:88|৮৮)[\s\-]?)?[0০][1১][3-9৩-৯](?:[\s\-.]?[0-9০-৯]){8}(?![\d০-৯])")
WEBMAIL = re.compile(r"[\w.+\-]+\s?@\s?(?:gmail|yahoo|hotmail|outlook|live|ymail)\s?\.\s?\w+(?:\.\w+)?", re.I)
# any e-mail address: ASCII local part, optional OCR space around '@', a domain ending in a letter-only top-level label
EMAIL = re.compile(r"(?:mailto:)?(?<![A-Za-z0-9._%+\-])[A-Za-z0-9._%+\-]+\s?@\s?[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}(?![A-Za-z0-9\-])", re.I)
MAILTO_Q1 = re.compile(r"\?mailto=[^&\s\"'<>]*&")       # ?mailto=x&rest  -> ?rest
MAILTO_Q2 = re.compile(r"[?&]mailto=[^&\s\"'<>]*")      # &mailto=x or ?mailto=x at the end -> ''
MARK_EMAIL, MARK_MOBILE = "[e-mail removed]", "[mobile removed]"

# Institutional office (role) addresses as printed on letterheads and official contact pages. They name an office, not a
# person, and are kept in the public edition. Keep this list identical to the table in
# 00_admin/rights_and_personal_data_policy.md.
OFFICE_EMAILS = {
    "dg@brri.gov.bd", "dr@brri.gov.bd", "head.breeding@brri.gov.bd", "head.hybrid@brri.gov.bd", "head.biotech@brri.gov.bd",
    "head.grs@brri.gov.bd", "head.gqn@brri.gov.bd", "head.ard@brri.gov.bd", "head.rfs@brri.gov.bd",
    "dg@bina.gov.bd",
    "dir@sca.gov.bd",
    "acsl@moa.gov.bd", "cst@moa.gov.bd",
    "dg@fisheries.gov.bd", "cfeo@fisheries.gov.bd", "adaqua@fisheries.gov.bd", "ddaqua@fisheries.gov.bd",
    "ddchingri@fisheries.gov.bd", "ddext@fisheries.gov.bd",
    "fisheries-5@mofl.gov.bd", "fisheries-x@mofl.gov.bd",
    "registrar@gau.edu.bd", "info@badc.gov.bd", "registrar@ru.ac.bd", "info@brac.net", "info@aci-bd.com",
}
# columns that hold individuals' contact details, dropped from the public copy of each table
DROP_COLUMNS = {"bgd_variety_people.csv": ["professional_email", "professional_phone"], "bgd_institutions.csv": ["head_work_email"]}


def _office(addr):
    a = re.sub(r"\s", "", addr).lower()
    if a.startswith("mailto:"):
        a = a[7:]
    return any(a == o or (a.endswith(o) and not a[-len(o) - 1].isalnum()) for o in OFFICE_EMAILS)


def _email(m):
    s = m.group(0)
    return s if _office(s) else MARK_EMAIL


def text(s):
    s = MAILTO_Q2.sub("", MAILTO_Q1.sub("?", s))
    s = WEBMAIL.sub(MARK_EMAIL, MOBILE.sub(MARK_MOBILE, s))
    return EMAIL.sub(_email, s)


def redact(df):
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].map(lambda v: text(v) if isinstance(v, str) else v)
    return df


# OCR and verbatim text can write a mobile number with separators inside it, run it into neighbouring digits, or misread
# its leading 0. In free-text columns any run of 10 or more digits (Latin or Bangla, with single spaces, hyphens or dots
# between groups) that contains a Bangladeshi mobile pattern is removed whole. Hash and identifier columns are never
# touched, because they are not free text.
# A phone number is written in at most three groups of three or more digits (for example 01XXX-XXXXXX, written in Latin or Bangla digits);
# breeding lines (BR1674-15-4-1-3-1) and memo numbers (33.00.0000.130.99.027) have short groups or follow letters.
DIGIT_RUN = re.compile(r"(?<![A-Za-z0-9০-৯\-.])[0-9০-৯]{3,}(?:[\s\-.][0-9০-৯]{3,}){0,2}(?![0-9০-৯]|[\-.][0-9০-৯])")
NOT_TEXT_COLUMN = re.compile(r"(^|_)(id|ids|sha256|sha|hash|url|urls|doi|file|path|date|page|pages|key|code|line|no|year)$|_id_|^variety_id|^source_id", re.I)
_BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def _run(m):
    digits = re.sub(r"[\s\-.]", "", m.group(0)).translate(_BN)
    return MARK_MOBILE if len(digits) >= 10 and re.search(r"1[3-9]\d{8}", digits) else m.group(0)


def free_text(s):
    return DIGIT_RUN.sub(_run, text(s))


def public_table(name, df):
    """Public copy of a released table: personal contact columns dropped (DROP_COLUMNS), text() on every cell, and the
    stricter free_text() on free-text columns. name is the file name (e.g. 'bgd_variety_people.csv'); a path is accepted too."""
    drop = [c for c in DROP_COLUMNS.get(pathlib.Path(str(name)).name, []) if c in df.columns]
    df = redact(df.drop(columns=drop))
    for c in df.columns:   # every column that is not an identifier, hash, address, date, page or file path
        if not NOT_TEXT_COLUMN.search(c) and df[c].dtype == object:
            df[c] = df[c].map(lambda v: free_text(v) if isinstance(v, str) else v)
    return df


def redact_xlsx(src, dst):
    import openpyxl
    wb = openpyxl.load_workbook(src)
    drop_names = {c for cols in DROP_COLUMNS.values() for c in cols}
    for ws in wb.worksheets:
        header = [c.value for c in ws[1]] if ws.max_row else []
        for idx in sorted((i + 1 for i, h in enumerate(header) if h in drop_names), reverse=True):
            ws.delete_cols(idx)
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str):
                    c.value = text(c.value)
    wb.save(dst)


def redact_files(folder):
    n = 0
    for fp in sorted(pathlib.Path(folder).glob("bgd_*.csv")):
        d = pd.read_csv(fp, dtype=str, keep_default_na=False)
        red = public_table(fp.name, d.copy())
        if not red.equals(d):
            red.to_csv(fp, index=False, encoding="utf-8-sig"); n += 1
    return n


if __name__ == "__main__":
    print(redact_files(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[1] / "05_output/final"), "files rewritten")
