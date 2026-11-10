"""E3 (round 3, 2026-11-10): archive the official pages that name the developing institutes, their parent ministry and
their divisions, for scripts/build_institutes_people.py. Network; run once by hand, never by rebuild_all.sh.

Every page goes through lib_fetch.fetch() (manifest row + SHA-256 in 02_raw/_manifest_parts/PEOPLE.csv). lib_fetch
throttles to one request per 2.5 s per host; this script waits another second so each host sees at most one request
every 3.5 s. robots.txt checked on 2026-11-10: brri.gov.bd, bina.gov.bd and badc.gov.bd serve no robots.txt (404, the
national-portal default page), gau.edu.bd and ru.ac.bd disallow only /wp-admin/. No forms are submitted, no e-mail is sent.
"""
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch

PAGES = [
    # (url, path under 02_raw, note)
    ("https://brri.gov.bd/pages/static-pages/6922de57933eb65569e19fb3", "brri/PEOPLE_about_brri.html", "BRRI 'about' page: status, parent ministry"),
    ("https://brri.gov.bd/pages/static-pages/6922deaf933eb65569e1c998", "brri/PEOPLE_mandate.html", "BRRI mandate page"),
    ("https://brri.gov.bd/pages/static-pages/6922dc53933eb65569e0fbbf", "brri/PEOPLE_div_plant_breeding.html", "BRRI Plant Breeding Division page"),
    ("https://brri.gov.bd/pages/static-pages/6922df83933eb65569e22772", "brri/PEOPLE_div_hybrid_rice.html", "BRRI Hybrid Rice Division page"),
    ("https://brri.gov.bd/pages/static-pages/6922e045933eb65569e2648c", "brri/PEOPLE_div_biotechnology.html", "BRRI Biotechnology Division page"),
    ("https://bina.gov.bd/pages/static-pages/6922dfeb933eb65569e24a74", "bina/PEOPLE_about_bina.html", "BINA 'about' page: status, parent ministry"),
    # the BINA Biotechnology Division menu link returned 404 on 2026-11-10; not retried
    ("https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-bina/2024/12/ea1ff99866a8465485aa6088f7a59181.pdf",
     "bina/PEOPLE_about_bina.pdf", "BINA 'about' document linked from the 'বিনা সম্পর্কে' page"),
    ("https://bina.gov.bd/pages/static-pages/6922e13c933eb65569e2b096", "bina/PEOPLE_introduction.html", "BINA introduction (ভূমিকা) page"),
    ("https://badc.gov.bd/", "institutions/PEOPLE_badc_home.html", "BADC home page"),
    ("https://badc.gov.bd/pages/static-pages/6922e0d2933eb65569e28b67", "institutions/PEOPLE_badc_contact.html", "BADC contact page"),
    ("https://www.ru.ac.bd/agronomy/", "institutions/PEOPLE_ru_agronomy_home.html", "University of Rajshahi, Dept of Agronomy and Agricultural Extension, home page"),
]

if __name__ == "__main__":
    for url, rel, note in PAGES:
        try:
            p = fetch(url, rel, agent="PEOPLE", notes=note)
            print("ok ", p)
        except Exception as e:  # keep going; a failure is reported, not hidden
            print("FAIL", url, e)
        time.sleep(1.0)
