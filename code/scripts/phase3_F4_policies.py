"""F4: download MoFL/DoF policy and rule PDFs relevant to fish genetic/species control; extract text (+bijoy)."""
import sys, pathlib, fitz
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch, ROOT
from bijoy2unicode import converter
C = converter.Unicode()
OS = "https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/"
ITEMS = [
 ("office-fisheries/2024/12/0706f80e886f4a8b89633a10c93cac65.pdf", "dof/national_fisheries_policy_1998_en.pdf", "National Fisheries Policy 1998 (English), DoF policies page"),
 ("office-fisheries/2024/12/eef9cdf536fa4236a7fa6ce7cbed2fb6.PDF", "dof/national_fisheries_policy_1998_bn.pdf", "জাতীয় মৎস্য নীতি 1998 (Bangla), DoF policies page"),
 ("office-fisheries/2024/12/b797c858f4ac4b5bbdb3c0656f0ebede.pdf", "dof/fish_protection_conservation_rules_2024-02-07.pdf", "মৎস্য সুরক্ষা ও সংরক্ষণ বিধিমালা, 7 Feb 2024 (DoF laws page)"),
 ("office-fisheries/2024/12/4a8ffb5f321a4411af69502bf6022cdf.pdf", "dof/pcf_rules_prepublication_2020-05-04.pdf", "PCF Rules 1985 proposed amendment pre-publication (posted 2020-05-04)"),
 ("office-mofl/2024/12/3b248ff097104e84b7c07a38506373de.pdf", "mofl/pcf_rules_rule19_2021-09-13.pdf", "PCF Rules rule 19 insertion notification (13/09/2021)"),
 ("office-mofl/2024/12/74d972eeabc342438960b0f61baf174d.pdf", "mofl/govt_fish_seed_farm_policy.pdf", "সরকারি মৎস্যবীজ উৎপাদন খামার ও বাঁওড়ে মৎস্যবীজ ... নীতিমালা (MoFL copy)"),
 ("office-mofl/2024/12/660dc3453c0a43ca9766fa7826ef1fa9.pdf", "mofl/national_fish_award_policy_rev2019.pdf", "জাতীয় মৎস্য পুরষ্কার নীতি (revised 2019)"),
]
for path, rel, note in ITEMS:
    try:
        p = fetch(OS + path, "fish_governance/" + rel, "F4", note)
    except Exception as e:
        print("FAIL", rel, e); continue
    d = fitz.open(ROOT / p); txt = "\n".join(f"=== page {i+1}\n" + pg.get_text() for i, pg in enumerate(d))
    stem = pathlib.Path(p).stem
    (ROOT / "03_extracted/text/F4" / (stem + ".txt")).write_text(txt, encoding="utf-8")
    uni = []
    for line in txt.splitlines():
        try: uni.append(C.convertBijoyToUnicode(line + "  ").rstrip())
        except Exception: uni.append(line)
    (ROOT / "03_extracted/text/F4/uni" / (stem + ".txt")).write_text("\n".join(uni), encoding="utf-8")
    print(rel, d.page_count, len(txt))
