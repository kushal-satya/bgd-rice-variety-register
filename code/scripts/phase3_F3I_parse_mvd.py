"""F3I: parse the saved IAEA MVD Atom XML (02_raw/iaea/mvd_*.xml) into 03_extracted/tables/iaea_mvd_bgd_rice.csv."""
import pathlib, re, csv
import xml.etree.ElementTree as ET
ROOT = pathlib.Path(__file__).resolve().parents[1]
NS = {"a": "http://www.w3.org/2005/Atom", "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
      "d": "http://schemas.microsoft.com/ado/2007/08/dataservices"}


def items(f):
    root = ET.parse(ROOT / "02_raw/iaea" / f).getroot()
    for e in root.findall("a:entry", NS):
        p = e.find("a:content/m:properties", NS)
        d = {}
        for c in p:
            tag = c.tag.split("}")[1]
            if len(c):  # collection
                d[tag] = [x.text for x in c]
            else:
                d[tag] = c.text
        yield d


common = {d["Id"]: d["Title"] for d in items("mvd_CommonName.xml")}
dev = {d["Id"]: d.get("Title") for d in items("mvd_MutantDevelopmentType.xml")}
pm = {d["Id"]: d.get("Title") for d in items("mvd_PhysicalMutagen.xml")}
mv = list(items("mvd_MutantVariety_BGD.xml"))
ids = {d["Id"] for d in mv}
bp = {}
for d in items("mvd_BreedingPhysical_all.xml"):
    k = d.get("MutantVarietyIDId")
    if k in ids:
        bp.setdefault(k, []).append(d)
pub = {}
for d in items("mvd_MutantVarietyPublication_all.xml"):
    k = d.get("MutantVarietyIDId")
    if k in ids:
        pub.setdefault(k, []).append(d.get("Title") or d.get("Publication") or "")
rows = []
for d in mv:
    cn = common.get(d.get("CommonNameIDId"))
    b = bp.get(d["Id"], [])
    rows.append({"list_id": d["Id"], "mvid": d.get("MutantVarietyID"), "variety_name": d.get("VarietyName"),
                 "local_name": d.get("LocalName"), "common_name": cn, "original_name": d.get("OriginalName"),
                 "national_reg_year": d.get("NationalRegistrationYear"), "local_reg_year": d.get("LocalRegistrationYear"),
                 "registration": d.get("Registration"), "national_agency": d.get("NationalRegistrationAgency"),
                 "development_type": dev.get(d.get("DevelopmentIDId")),
                 "short_description": (d.get("ShortDescription") or "").strip(),
                 "character_improvement": d.get("CharacterImprovementDetails"),
                 "breeding_physical": " || ".join("; ".join(f"{k}={v}" for k, v in x.items() if v and k not in ("__metadata",) and not k.startswith(("Content", "OData", "Author", "Editor", "GUID", "Created", "Modified", "FileSystem", "ServerRedirected", "Compliance", "Attachments"))) for x in b),
                 "publications": " || ".join(p for p in pub.get(d["Id"], []) if p)[:1500],
                 "form_url": "https://nucleus.iaea.org" + (d.get("FormUrl") or "")})
out = ROOT / "03_extracted/tables/iaea_mvd_bgd.csv"
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "Bangladesh entries;", sum(1 for r in rows if (r["common_name"] or "").lower().startswith("rice")), "rice")
