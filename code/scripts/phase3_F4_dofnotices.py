"""F4: download selected DoF notice PDFs (fisheries.gov.bd/pages/notices hits) and extract text."""
import sys, pathlib, fitz
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_fetch
from lib_fetch import fetch, ROOT
OS = "https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-fisheries/"
ITEMS = [
 ("2024/12/8ffa17e24ef64c4f9236b49047d7f521.pdf", "dof_notice_2023-04-05_vannamei_commercial_approval_letter.pdf", "MoFL approval of commercial vannamei culture + guideline (DoF notice dated 2023-04-05)"),
 ("2026/5/2515451e-b769-4baa-8b33-8c37a8da2951.pdf", "dof_notice_2026-06-22_shrimp_pl_demand.pdf", "Golda/bagda/harina/chaka/vannamei PL annual demand"),
 ("2024/12/250e0b4939bf4cc88ecddc1165e1f92e.PDF", "dof_notice_2024-11-26_china_carp_wf_g3_rohu_brood_info.pdf", "Govt farms: China-imported silver/grass/bighead carp and WorldFish G3 rohu brood info"),
 ("2024/12/4a348cbe602b40b481273e8a6268805a.pdf", "dof_notice_2020-01-13_broodbank_china_carp_restocking.pdf", "Completed brood bank project: China-imported Chinese carp fingerlings redistribution"),
 ("2024/12/d73ee7170b204f37aa9125a65692e794.pdf", "dof_notice_2020-01-29_china_carp_supervision_committee.pdf", "Committee for rearing China-imported Chinese carp"),
 ("2024/12/9d6b25d01dba4aeeaf8558c5d88bac9a.pdf", "dof_notice_2023-11-12_brood_management_workshop.pdf", "Quality brood management workshop"),
 ("2024/12/ed92efdfdf0947ad9a9527d8f122f459.pdf", "dof_notice_2025-05-08_piranha_banned_action.pdf", "Action on Prothom Alo report 'piranha farmed though banned'"),
 ("2024/12/8830e6a85d7b462b977b5b4b19f2cd98.pdf", "dof_notice_2021-12-12_sucker_fish_action.pdf", "Action on sucker fish"),
 ("2024/12/27ded698acc248618354d6cccb17f59a.pdf", "dof_notice_2022-07-04_sucker_fish_campaign.pdf", "Sucker fish campaign"),
 ("2024/12/e688fdcb55f141f79539d04c93ed2c9b.pdf", "dof_notice_2025-06-24_suckermouth_research.pdf", "Suckermouth catfish research cooperation"),
 ("2024/12/9ad022508f3e4f5292ba6e627acf9775.pdf", "dof_notice_2025-12-01_import_species_identification_quarantine.pdf", "Species identification + quarantine report for imported live fish/seed"),
 ("2026/3/d64a20f0-04fc-4544-9f0c-ca5edb72e17c.pdf", "dof_notice_2026-04-08_live_fish_import_noc.pdf", "NOC for import of live fish, feed, aqua inputs"),
]
for path, name, note in ITEMS:
    try:
        p = fetch(OS + path, "fish_governance/dof/" + name, "F4", note)
    except Exception as e:
        print("FAIL", name, e); continue
    try:
        doc = fitz.open(ROOT / p); txt = "\n".join(f"=== page {i+1}\n" + pg.get_text() for i, pg in enumerate(doc))
    except Exception as e:
        txt = ""; print("open fail", e)
    tp = ROOT / "03_extracted/text/F4" / (pathlib.Path(p).stem + ".txt"); tp.write_text(txt, encoding="utf-8")
    print(name, len(txt), doc.page_count if txt else "")
