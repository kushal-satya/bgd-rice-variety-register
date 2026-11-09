"""L1: parse official BRRI / BINA officer directory pages (saved by phase3_L1_inst_fetch.py) into
04_working/L1/directory.csv. Only institutional fields are kept for downstream use (see decisions_L1.md):
name (Bangla, as printed), designation, office/division, office phone (land line / extension), e-mail(s).
Mobile numbers and home phones are NOT copied."""
import sys, re, csv, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import ROOT
from phase3_L1_txt import txt

SRC = {
    "02_raw/brri/L1_division_heads.html": "https://brri.gov.bd/pages/static-pages/6922dcda933eb65569e1269a",
    "02_raw/brri/L1_division_heads_more.html": "https://brri.gov.bd/pages/static-pages/6922dd34933eb65569e13eca",
    "02_raw/brri/L1_dg_directors.html": "https://brri.gov.bd/pages/static-pages/6922dccf933eb65569e122e3",
    "02_raw/brri/L1_officers_cso.html": "https://brri.gov.bd/pages/static-pages/6922df4a933eb65569e2115b",
    "02_raw/brri/L1_officers_pso.html": "https://brri.gov.bd/pages/static-pages/6922e11d933eb65569e2a4b1",
    "02_raw/brri/L1_officers_sso.html": "https://brri.gov.bd/pages/static-pages/6922dea5933eb65569e1c4b9",
    "02_raw/brri/L1_officers_so.html": "https://brri.gov.bd/pages/static-pages/6922e115933eb65569e2a181",
    "02_raw/bina/L1_officers.html": "https://bina.gov.bd/pages/officers",
}
FIELDS = {"নাম": "name_bn", "পদবি": "designation", "অফিস": "office", "ফোন(অফিস)": "phone_office", "ফোন (অফিস)": "phone_office",
          "ইন্টারকম": "intercom", "ই-মেইল": "email", "ইমেইল": "email", "ফ্যাক্স": "fax"}


def parse(f):
    s = txt(ROOT / f)
    i = s.find("কন্টেন্ট:")
    if i < 0: i = 0
    s = s[i:]
    # cut each record at 'নাম |'
    parts = re.split(r"\n?\s*নাম\s*\n?\s*\|", s)[1:]
    out = []
    for p in parts:
        flat = re.sub(r"\s*\n\s*", " ", "নাম |" + p)
        rec = {}
        for lab, key in FIELDS.items():
            m = re.search(r"(?:^|\|)\s*" + re.escape(lab) + r"\s*\|\s*([^|]*)\|", flat)
            if m and key not in rec: rec[key] = m.group(1).strip()
        if not rec.get("name_bn"): continue
        em = re.sub(r"\s+@", "@", rec.get("email", ""))
        em = re.sub(r"(brri\.gov\.b)\s+d", r"\1d", em)
        rec["email"] = "; ".join(sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", em.replace("bdj", "bd j")))))
        rec["source_file"] = f; rec["source_url"] = SRC[f]
        out.append(rec)
    return out


if __name__ == "__main__":
    rows = []
    for f in SRC:
        if (ROOT / f).exists(): rows += parse(f)
    cols = ["name_bn", "designation", "office", "phone_office", "intercom", "email", "source_file", "source_url"]
    with open(ROOT / "04_working/L1/directory.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(len(rows), "directory rows")
