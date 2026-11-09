"""F3I: IAEA/FAO Mutant Variety Database (nucleus.iaea.org/sites/mvd), Bangladesh entries, via the site's public
SharePoint REST endpoint (robots.txt disallows only /_layouts/, /_vti_bin/, /_catalogs/). Sequential, lib_fetch.
Note: lib_fetch.fetch uses its default headers; SharePoint returns Atom XML without an Accept header, so we pass
nothing special and save what the server returns untouched."""
import pathlib, sys, json
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch
B = "https://nucleus.iaea.org/sites/mvd/_api/web/lists/getbytitle('{}')/items?$top=5000"
jobs = [
    ("MutantVariety", "&$filter=CountryIDId eq 100", "iaea/mvd_MutantVariety_BGD.xml"),
    ("CommonName", "&$select=Id,Title", "iaea/mvd_CommonName.xml"),
    ("BreedingPhysical", "", "iaea/mvd_BreedingPhysical_all.xml"),
    ("MutantDevelopmentType", "", "iaea/mvd_MutantDevelopmentType.xml"),
    ("Physical Mutagen", "", "iaea/mvd_PhysicalMutagen.xml"),
    ("MutantVarietyPublication", "", "iaea/mvd_MutantVarietyPublication_all.xml"),
    ("MutantVarietyImprovedCharacter", "", "iaea/mvd_MutantVarietyImprovedCharacter_all.xml"),
]
for lst, extra, rel in jobs:
    url = B.format(lst) + extra
    try:
        print(lst, fetch(url, rel, "F3I", notes=f"IAEA MVD SharePoint REST list '{lst}' {extra}"))
    except Exception as e:
        print(lst, "FAILED", e)
