"""L2: metadata + OA full text for the Frontiers golden-rice paper (CGSpace item without files)
and the JXB 2026 review (OUP returned a Cloudflare 403; metadata only via Crossref/OpenAlex/Europe PMC)."""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch, get
AG = "L2"
EP = "https://www.ebi.ac.uk/europepmc/webservices/rest"

def tryfetch(url, rel, notes):
    try:
        print(fetch(url, rel, AG, notes))
    except Exception as e:
        print("FAIL", url, e)

# golden rice GR2-E BRRI dhan29 (PMC7947304)
g = "cgiar_specific/cgspace_gr2e_brri_dhan29"
tryfetch(f"{EP}/PMC7947304/fullTextXML", f"{g}/PMC7947304_fullText.xml", "Europe PMC OA full text (CC-BY) of CGSpace item 10568/164332")
tryfetch(f"{EP}/PMC7947304/supplementaryFiles", f"{g}/PMC7947304_supplementary.zip", "Europe PMC supplementary files bundle")
tryfetch(f"{EP}/search?query=DOI:%2210.3389/fpls.2021.619739%22&format=json&resultType=core", f"{g}/europepmc_core.json", "Europe PMC core record")
tryfetch("https://api.crossref.org/works/10.3389/fpls.2021.619739", f"{g}/crossref.json", "Crossref record")

# exotic cultivars paper: crossref for completeness
tryfetch("https://api.crossref.org/works/10.3389/fsufs.2022.813933", "cgiar_specific/cgspace_exotic_adoption/crossref.json", "Crossref record")

# JXB erag452
j = "cgiar_specific/jxb_erag452"
tryfetch("https://api.crossref.org/works/10.1093/jxb/erag452", f"{j}/crossref.json", "Crossref record; OUP site 403 Cloudflare challenge")
tryfetch("https://api.openalex.org/works/doi:10.1093/jxb/erag452", f"{j}/openalex.json", "OpenAlex record")
tryfetch(f"{EP}/search?query=DOI:%2210.1093/jxb/erag452%22&format=json&resultType=core", f"{j}/europepmc_core.json", "Europe PMC core record (abstract)")
