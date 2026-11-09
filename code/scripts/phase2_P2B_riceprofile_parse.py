"""P2B: parse saved BRRI Rice Profile variety pages (02_raw/brri_riceprofile/variety_NNN.html).
Extracts the page title name, season (মৌসুম), land type (জমির ধরন), suitable area, the introduction
paragraph (জাত পরিচিতি; holds breeding line, cross and the NSB approval sentence), traits and special
needs, plus regex hits for NSB year and breeding line. Output: 03_extracted/tables/brri_riceprofile.csv"""
import re, html, csv, pathlib, glob
ROOT = pathlib.Path(__file__).resolve().parents[1]
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
LABELS = ["মৌসুম", "শস্য বিন্যাস", "জমির ধরন", "উপযুক্ত এলাকা", "তুলনা করতে লগইন করুন", "জাত পরিচিতি",
          "জাতের বৈশিষ্ট্য", "বিশেষ প্রয়োজনীয়তা", "জীবনকাল", "ফলন", "অ্যামিলোজ", "চাষাবাদ পদ্ধতি"]


def text_lines(t):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    s = re.sub(r"</(tr|p|div|li|h\d|td|th)>", "\n", s)
    x = html.unescape(re.sub(r"<[^>]+>", " ", s))
    x = re.sub(r"[ \t\xa0]+", " ", x)
    return [l.strip() for l in x.split("\n") if l.strip()]


def section(lines, label):
    if label not in lines:
        return ""
    i = lines.index(label)
    out = []
    for l in lines[i + 1:]:
        if l in LABELS:
            break
        out.append(l)
    return " ".join(out)


rows = []
for f in sorted(glob.glob(str(ROOT / "02_raw/brri_riceprofile/variety_*.html"))):
    t = open(f, encoding="utf-8", errors="replace").read()
    m = re.search(r"<title>(.*?)\|", t, re.S)
    name = html.unescape(m.group(1)).strip() if m else ""
    L = text_lines(t)
    intro = section(L, "জাত পরিচিতি")
    years = re.findall(r"([১২][৯০][০-৯]{2})\s*সাল", intro)
    lines_ = re.findall(r"[A-Z]{1,4}\s?\(?[A-Za-z]*\)?\s?\d{2,6}(?:[-–][A-Za-z0-9*()]+)+", intro)
    rows.append({"rp_id": int(re.search(r"variety_(\d+)", f).group(1)), "name_bn": name,
                 "season": section(L, "মৌসুম"), "land_type": section(L, "জমির ধরন"),
                 "suitable_area": section(L, "উপযুক্ত এলাকা"), "intro": intro,
                 "intro_years": ";".join(y.translate(BN) for y in years),
                 "intro_codes": ";".join(lines_),
                 "traits": section(L, "জাতের বৈশিষ্ট্য"), "special": section(L, "বিশেষ প্রয়োজনীয়তা"),
                 "duration": section(L, "জীবনকাল"), "yield": section(L, "ফলন"),
                 "local_file": "02_raw/brri_riceprofile/" + pathlib.Path(f).name,
                 "source_url": "https://riceprofile.brri.gov.bd/varieties/%d" % int(re.search(r"variety_(\d+)", f).group(1))})
out = ROOT / "03_extracted/tables/brri_riceprofile.csv"
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "pages parsed")
