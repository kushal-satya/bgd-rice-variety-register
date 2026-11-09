"""L1: fetch official institute contact/officer/division pages (brri.gov.bd, bina.gov.bd)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch
PAGES = [
 ("https://brri.gov.bd/pages/static-pages/6922de01933eb65569e17918", "brri/L1_contact_address.html", "BRRI যোগাযোগের ঠিকানা"),
 ("https://brri.gov.bd/pages/static-pages/6922dcda933eb65569e1269a", "brri/L1_division_heads.html", "BRRI সকল বিভাগীয় ও শাখা প্রধান"),
 ("https://brri.gov.bd/pages/static-pages/6922e140933eb65569e2b1fa", "brri/L1_officers_class1.html", "BRRI কর্মকর্তা-১ম শ্রেণী"),
 ("https://brri.gov.bd/pages/static-pages/6922dcdc933eb65569e1271c", "brri/L1_research_divisions.html", "BRRI গবেষণা কার্যক্রম বিভাগসমূহ"),
 ("https://bina.gov.bd/pages/static-pages/6922dc17933eb65569e0e60a", "bina/L1_plant_breeding_division.html", "BINA উদ্ভিদ প্রজনন বিভাগ"),
]
for u, rel, n in PAGES + [tuple(a.split("|")) for a in sys.argv[1:]]:
    try: print(fetch(u, rel, "L1", n))
    except Exception as e: print("FAIL", u, e)
