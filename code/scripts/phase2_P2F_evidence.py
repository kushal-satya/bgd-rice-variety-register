"""P2F: build 04_working/evidence_P2F.csv and fish_excluded.csv from hand-curated rows.
Every row points to a file in 02_raw (manifest). Page numbers for text PDFs are found
programmatically from a quoted phrase (find_page) so that the locator is checkable."""
import csv, re, pathlib, sys
import fitz

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "04_working/evidence_P2F.csv"
HDR = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank",
       "local_file", "page", "locator", "method", "validation", "confidence", "notes"]

# ---------------- sources ----------------
S = {
 "MOFL22": ("P2F-S01", "MoFL প্রজ্ঞাপন নং ৩৩.০০.০০০০.১৩০.৯৯.০২৭.১৯-২২ (04 Aug 2021): naming of 4th-generation rohu 'সুবর্ণ রুই (Subarno Rui)'", "1_primary_legal", "02_raw/mofl/mofl_prajnapan22_subarno_rui_naming_2021-08-04.pdf"),
 "MOFL17": ("P2F-S02", "MoFL প্রজ্ঞাপন নং ৩৩.০০.০০০০.১৩০.৯৯.০২৭.১৯.১৭ (11 Apr 2022): renaming to 'বিএফআরআই সুবর্ণ রুই' [BFRI Subarno Rui]", "1_primary_legal", "02_raw/mofl/mofl_prajnapan17_bfri_subarno_rui_renaming_2022-04-11.pdf"),
 "MOFLLIST": ("P2F-S03", "MoFL বিজ্ঞপ্তি ও প্রজ্ঞাপন listing, search 'রুই'", "1_primary_legal", "02_raw/mofl/mofl_notification_circulars_search_rui.html"),
 "FRIPRAJ": ("P2F-S04", "fri.gov.bd 'প্রজ্ঞাপন সর্ম্পকিত' page (BFRI copy of the two MoFL notifications)", "3_institute_page", "02_raw/bfri/pages/static-pages_6922e09b933eb65569e27cc7.html"),
 "LEAF95": ("FS009", "BFRI extension leaflet no. 95 (2022) 'উন্নত জাতের বিএফআরআই সুবর্ণ রুই উদ্ভাবন ও চাষাবাদ প্রযুক্তি' (J. Rashid, M. E. Haque)", "3_institute_page", "02_raw/bfri/bfri_subarna_rui_page_img1.jpg"),
 "LEAF95B": ("FS009", "BFRI extension leaflet no. 95 (2022), image 2 (cover/back panel)", "3_institute_page", "02_raw/bfri/bfri_subarna_rui_page_img2.jpg"),
 "LEAF95P": ("FS009", "fri.gov.bd static page hosting leaflet no. 95 (HTML)", "3_institute_page", "02_raw/bfri/pages/static-pages_6922df1b933eb65569e1fe81.html"),
 "TVC": ("FS008", "BFRI Technology Validation Committee minutes, memo 33.04.0000.000.106.24.0001.25.61 dated 18 Jun 2025, সারণি-২ (87 technologies)", "2_official_list", "02_raw/bfri/bfri_technologies_list_attachment_2026.pdf"),
 "GLANCE": ("FS011", "fri.gov.bd 'এক নজরে বিএফআরআই' (BFRI at a glance)", "3_institute_page", "02_raw/bfri/pages/static-pages_6922ded5933eb65569e1db71.html"),
 "AWARDS": ("FS010", "fri.gov.bd 'গবেষণায় স্বীকৃতি' (awards list)", "3_institute_page", "02_raw/bfri/pages/static-pages_6922e0ca933eb65569e28987.html"),
 "TECHPAGE": ("FS012", "fri.gov.bd 'বিএফআরআই উদ্ভাবিত প্রযুক্তিসমুহ' page (legacy numbered list)", "3_institute_page", "02_raw/bfri/pages/static-pages_6922e048933eb65569e2654d.html"),
 "AR1617": ("P2F-S10", "BFRI Annual Report 2016-17", "3_institute_page", "02_raw/bfri/bfri_annual_report_2016-17.pdf"),
 "AR1718": ("P2F-S11", "BFRI Annual Report 2017-18", "3_institute_page", "02_raw/bfri/bfri_annual_report_2017-18.pdf"),
 "AR1819": ("P2F-S12", "BFRI Annual Report 2018-19", "3_institute_page", "02_raw/bfri/bfri_annual_report_2018-19.pdf"),
 "AR2021": ("FS013", "BFRI Annual Report 2020-21", "3_institute_page", "02_raw/bfri/bfri_annual_report_2020-21.pdf"),
 "AR2122": ("P2F-S13", "BFRI Annual Report 2021-22, part 1 (scanned)", "3_institute_page", "02_raw/bfri/bfri_annual_report_2021-22_part1.pdf"),
 "AR2223": ("P2F-S14", "BFRI Annual Report 2022-23", "3_institute_page", "02_raw/bfri/bfri_annual_report_2022-23.pdf"),
 "AR2324": ("P2F-S15", "BFRI Annual Report 2023-24", "3_institute_page", "02_raw/bfri/bfri_annual_report_2023-24.pdf"),
 "SUPERTIL": ("P2F-S16", "BFRI publication 'বিএফআরআই সুপার তেলাপিয়ার মনোসেক্স পোনা উৎপাদন ও চাষ প্রযুক্তি' (undated booklet)", "3_institute_page", "02_raw/bfri/bfri_pub_super_tilapia_monosex_tech.pdf"),
 "GIFTLEAF": ("P2F-S17", "BFRI leaflet 'বিএফআরআই গিফট তেলাপিয়ার মনোসেক্স পোনা উৎপাদন ও চাষ প্রযুক্তি' (undated)", "3_institute_page", "02_raw/bfri/bfri_leaflet_gift_monosex_tech.pdf"),
 "RAJLEAF": ("P2F-S18", "BFRI leaflet 'পুকুরে রাজপুঁটি মাছ চাষ' (undated)", "3_institute_page", "02_raw/bfri/bfri_leaflet_rajputi_pond_culture.pdf"),
 "FAOJ": ("FS014", "BFRI slides 'Quality Fish Seed in Bangladesh: Contribution of BFRI' (FAO Annex J, c.2013, undated)", "3_institute_page", "02_raw/fao/fao_annexJ_quality_fish_seed_bangladesh_bfri.pdf"),
 "HUSSAIN": ("FS015", "Hussain, Barman, Karim, Keus (WorldFish Bangladesh), 'Tilapia farming in Bangladesh', TheFishSite printout dated June 2014", "4_cgiar_record", "02_raw/worldfish/hussain_c2014_tilapia_farming_bangladesh.pdf"),
 "WFBLOG": ("FS021", "WorldFish blog 'Fish genetics: A year in review' (14 Dec 2015)", "4_cgiar_record", "02_raw/worldfish/worldfish_blog_fish_genetics_year_review_2015.html"),
 "WFDISS": ("FS020", "WorldFish 'Genetically improved aquatic animal strains available for dissemination' (2026)", "4_cgiar_record", "02_raw/worldfish/worldfish_genetic_resources_dissemination.html"),
 "WFKHUL": ("P2F-S20", "WorldFish update: Khulna workshop on carp genetic improvement (Sep 2025)", "4_cgiar_record", "02_raw/worldfish/worldfish_khulna_workshop_2025.html"),
 "FRONT": ("FS022", "Hamilton et al. 2022, On-farm performance of genetically-improved rohu in Bangladesh, Frontiers in Aquaculture doi 10.3389/faquc.2022.1060335", "5_peer_reviewed", "02_raw/literature/frontiers_2022_g3_rohu_faquc.2022.1060335.html"),
 "FILTR": ("P2F-S21", "Fish Innovation Lab Final Technical Report, Advancing Aquaculture Systems Productivity Through Carp Genetic Improvement (WorldFish, Hamilton et al., Aug 2023)", "4_cgiar_record", "02_raw/fishinnovationlab/fil_2025_technical_report_hamilton_carp_genetic_improvement.pdf"),
 "FILMAY": ("FS023", "Fish Innovation Lab news (24 May 2023): CGIP shares G3 technology with DoF", "6_secondary", "02_raw/fishinnovationlab/fil_2023-05_cgip_shares_g3_with_dof.html"),
 "FILAUG": ("FS023", "Fish Innovation Lab news (18 Aug 2023): CGIP shares G3 technology with BFRI", "6_secondary", "02_raw/fishinnovationlab/fil_2023-08_cgip_shares_g3_with_bfri.html"),
 "TBS": ("FS024", "The Business Standard (8 Aug 2023): 'WorldFish G3 Rohu' handed over to BFRI", "6_secondary", "02_raw/news/tbs_2023-08_worldfish_g3_rohu_handed_to_bfri.html"),
 "YEASIN22": ("FS016", "Yeasin 2022, brief report on on-farm trial of G3 rohu (WorldFish hdl 20.500.12348/5428; item metadata only, PDF restricted)", "4_cgiar_record", "02_raw/worldfish/hdl_20.500.12348_5428_item_metadata.json"),
 "ALAM23": ("FS017", "Alam 2023 (READY), Wider-scale promotion of G3 rohu, project completion report (WorldFish hdl 20.500.12348/5683)", "4_cgiar_record", "02_raw/worldfish/alam_2023_wider_scale_promotion_g3_rohu_hdl5683.pdf"),
 "YH25": ("FS018", "Hamilton & Yeasin 2025, CGIDP progress and future pathways (presentation, 24 Sep 2025; hdl 20.500.12348/6598)", "4_cgiar_record", "02_raw/worldfish/yeasin_hamilton_2025_cgidp_progress_hdl6598.pdf"),
 "YH25M": ("FS018", "WorldFish digital archive item metadata hdl 20.500.12348/6598 (abstract)", "4_cgiar_record", "02_raw/worldfish/hdl_20.500.12348_6598_item_metadata.json"),
 "DV_SV": ("P2F-S22", "Harvard Dataverse doi:10.7910/DVN/SVNV6B 'Dataset on the dissemination of genetically improved carp in Bangladesh' (WorldFish, CC BY 4.0), metadata", "4_cgiar_record", "02_raw/dataverse/SVNV6B_metadata.json"),
 "DV_BF": ("P2F-S23", "Harvard Dataverse doi:10.7910/DVN/BFV5P1 'Dissemination of Genetically Improved Seed (Bangladesh, 2025)' (WorldFish, CC BY 4.0), metadata", "4_cgiar_record", "02_raw/dataverse/BFV5P1_metadata.json"),
 "HATCH": ("FS001", "Fish Hatchery Act 2010 (bdlaws act-details-1042)", "1_primary_legal", "02_raw/bdlaws/act-details-1042_fish_hatchery_act_2010.html"),
 "BGPRESS": ("P2F-S24", "dpp.gov.bd/bgpress extraordinary gazette list, ministry=55 (MoFL), 114 records 1979-2026", "1_primary_legal", "02_raw/bgpress/bgpress_mofl_extraordinary_search_m55.html"),
 "VANN": ("FS025", "DoF Vannamei culture guideline + MoFL approval letter 29 Mar 2023", "1_primary_legal", "02_raw/dof/dof_vannamei_guideline_2023.pdf"),
}

_pdf_cache = {}


def find_page(key, phrase):
    """1-based page of the first page whose text layer contains phrase (whitespace-normalised)."""
    f = ROOT / S[key][3]
    if f not in _pdf_cache:
        d = fitz.open(f)
        _pdf_cache[f] = [re.sub(r"\s+", " ", p.get_text()) for p in d]
    ph = re.sub(r"\s+", " ", phrase)
    for i, t in enumerate(_pdf_cache[f]):
        if ph in t:
            return i + 1
    raise SystemExit(f"phrase not found in {key}: {phrase}")


rows = []


def R(pk, field, value, raw, key, page="", locator="", method="html", validation="unvalidated", conf="high", notes="", find=None):
    sid, title, rank, lf = S[key]
    assert (ROOT / lf).exists(), lf
    if find:
        page = find_page(key, find)
        if not locator:
            locator = f'"{find[:140]}"'
    rows.append([pk, field, value, raw, sid, title, rank, lf, page, locator, method, validation, conf, notes])


# ======================= BFRI Subarna rui (G4 rohu) =======================
pk = "FISH_BFRI_SUBARNA_RUI_G4"
R(pk, "species_common_en", "Rohu", "রুই মাছের (Labeo rohita)", "MOFL22", 1, "body para 1", "visual_check", "visual_check", notes="crop 04_working/crops/P2F/mofl_prajnapan22_body.png")
R(pk, "species_scientific", "Labeo rohita", "(Labeo rohita)", "MOFL22", 1, "body para 1", "visual_check", "visual_check", notes="crop mofl_prajnapan22_body.png")
R(pk, "species_bn", "রুই", "রুই মাছের", "MOFL22", 1, "body para 1", "visual_check", "visual_check")
R(pk, "strain_name", "সুবর্ণ রুই (Subarno Rui)", "সুবর্ণ রুই (Subarno Rui) নামকরণ করা হইল", "MOFL22", 1, "para 02", "visual_check", "visual_check", notes="original official name 04 Aug 2021; superseded 11 Apr 2022")
R(pk, "strain_name", "বিএফআরআই সুবর্ণ রুই [BFRI Subarno Rui]", "“বিএফআরআই সুবর্ণ রুই” [BFRI Subarno Rui] হিসেবে পুনঃ নামকরণ করা হলো", "MOFL17", 1, "body", "pdf_text", "two_source", notes="current official name; also on MoFL listing (P2F-S03) and BFRI notifications page (P2F-S04)")
R(pk, "official_name_bn", "বিএফআরআই সুবর্ণ রুই", "“বিএফআরআই সুবর্ণ রুই”", "MOFL17", 1, "body", "pdf_text", "two_source", notes="two_source with BFRI leaflet 95 and TVC row 51")
R(pk, "official_name_en", "BFRI Subarno Rui", "[BFRI Subarno Rui]", "MOFL17", 1, "body", "pdf_text", "two_source", notes="English spelling per MoFL; WorldFish/FIL/TBS spell 'Subarna Rohu'; BFRI AR 2022-23 'Suborno Rui', AR 2023-24 'Shuborno Rui'")
R(pk, "local_name", "Subarna Rohu", "BFRI’s recently evolved and released Subarna Rohu strain", "FILAUG", "", '"Subarna Rohu strain"', "html", notes="spelling used by WorldFish/FIL and TBS")
R(pk, "local_name", "Suborno Rui", "F4 generation of BFRI Suborno Rui", "AR2223", method="pdf_text", find="F4 generation of BFRI Suborno Rui")
R(pk, "local_name", "Shuborno Rui", "BFRI Shuborno Rui 255.00", "AR2324", method="pdf_text", find="BFRI Shuborno Rui")
R(pk, "developer", "Bangladesh Fisheries Research Institute (BFRI), Freshwater Station, Mymensingh", "বাংলাদেশ মৎস্য গবেষণা ইনস্টিটিউট (BFRI) কৌলিতাত্ত্বিক গবেষণার মাধ্যমে", "MOFL22", 1, "body para 1", "visual_check", "two_source", notes="two_source with leaflet 95 (authors J. Rashid, M. E. Haque; contact Freshwater Station)")
R(pk, "generation", "G4 (4th generation)", "৪র্থ প্রজন্ম উদ্ভাবন করিয়াছে", "MOFL22", 1, "body para 1", "visual_check", "two_source", notes="two_source: leaflet 95 '৪র্থ প্রজন্মের উন্নত জাত'; FIL Aug 2023 'G4 improved generation'")
R(pk, "generation", "F1 2009 (mass selection) -> F2, F3 (family selection) -> F4 2020", "সিলেকটিভ ব্রিডিং (mass selection) এর মাধ্যমে ২০০৯ সালে ... ১ম প্রজন্মের (F1) ... অতঃপর ২০২০ সালে উন্নত জাতের ৪র্থ প্রজন্মের জাত", "LEAF95", 1, "middle panel 'জাত উন্নয়ন কৌশল', bullets 2-3", "visual_check", "visual_check", notes="crop 04_working/crops/P2F/subarna_leaflet_generations.png. Base population: di-allele crossing of Halda, Jamuna, Brahmaputra rohu, 9 groups")
R(pk, "pedigree", "Base population from di-allele crossing of Halda, Jamuna and Brahmaputra river rohu (9 groups); mass selection F1 (2009); family selection F2-F4", "হালদা, যমুনা ও ব্রহ্মপুত্র উৎসের রুই মাছের মধ্যে ডাই এ্যালিল ক্রসিং (di-allele crossing) এর মাধ্যমে ৯টি গ্রুপ থেকে প্রথমে বেইজ পপুলেশন", "LEAF95", 1, "middle panel bullet 1", "visual_check", "visual_check", "medium", notes="read from 1136x808 JPG by eye; text small but legible")
R(pk, "key_traits", "20.12% more productive than the conventional strain; fast growing; free of inbreeding problem; polymorphic loci 15, gene diversity 0.271 ± 0.190", "প্রচলিত জাতের চেয়ে ২০.১২% অধিক উৎপাদনশীল ... Polymorphic locus ও Gene diversity যথাক্রমে ১৫ এবং ০.২৭১ ± ০.১৯০", "MOFL22", 1, "body para 1", "ocr", "visual_check", notes="numbers confirmed on crop mofl_prajnapan22_body.png; 20.12% also in leaflet 95 and FIL Aug 2023 (two_source)")
R(pk, "key_traits", "Gene diversity 0.271±0.198 for BFRI Rohu (F4) (polymorphic loci 15, 71.43%)", "BFRI Rohu (F4) 15 71.43 0.271±0.198", "AR2021", method="pdf_text", find="BFRI Rohu (F4) 15 71.43", notes="CONFLICT: AR 2020-21 gives SD ±0.198; MoFL notification and leaflet 95 table give ±0.190")
R(pk, "release_date", "2021-06-10", "গত ১০ জুন ২০২১ তারিখে “বিএফআরআই সুবর্ণ রুই” এর উন্নত নতুন জাত ঘোষণা ও অবমুক্ত করা হয়েছে", "LEAF95", 1, "right panel 'প্রযুক্তি অবমুক্তকরণ ও আনুষ্ঠানিকতা'", "visual_check", "two_source", notes="crop subarna_leaflet_release_distribution.png; two_source with FIL Aug 2023 'On June 10, 2021, the G4 improved generation of rohu was named Subarna Rohu by BFRI'. NOTE: precedes the MoFL naming notification (04 Aug 2021)")
R(pk, "release_date", "2021-06-10", "On June 10, 2021, the G4 improved generation of rohu was named Subarna Rohu by BFRI, which has been released for quality seed production", "FILAUG", "", '"On June 10, 2021, the G4 improved generation of rohu was named Subarna Rohu by BFRI"', "html", "two_source", "medium", notes="secondary (author M. G. Hussain, ex-BFRI DG); says BFRI named it, whereas the MoFL notification names it on 04 Aug 2021")
R(pk, "approval_date", "2021-08-04", "২০ শ্রাবণ ১৪২৮ / ০৪ আগস্ট ২০২১", "MOFL22", 1, "header 'তারিখ:'", "visual_check", "two_source", notes="crop mofl_prajnapan22_header.png; also cited in MoFL notification 17 of 11 Apr 2022 ('০৪.০৮.২০২১ খ্রি. তারিখের ... -২২ সংখ্যক প্রজ্ঞাপনমূলে') and MoFL listing date ০৪-০৮-২০২১")
R(pk, "approval_reference", "MoFL Fisheries-5 Branch notification no. 33.00.0000.130.99.027.19-22", "নম্বর: ৩৩.০০.০০০০.১৩০.৯৯.০২৭.১৯-২২", "MOFL22", 1, "header 'নম্বর:'", "visual_check", "two_source", notes="two_source with MoFL notification 17 (2022) which cites this number; signed by A Z M Nurul Haque, Deputy Secretary, 'রাষ্ট্রপতির আদেশক্রমে'")
R(pk, "approval_date", "2022-04-11", "১১ এপ্রিল ২০২২ / ২৮ চৈত্র ১৪২৮", "MOFL17", 1, "header 'তারিখ:'", "pdf_text", "two_source", notes="renaming notification (name change only); two_source with MoFL listing date ১১-০৪-২০২২")
R(pk, "approval_reference", "MoFL Fisheries-5 Branch notification no. 33.00.0000.130.99.027.19.17 (renaming)", "নম্বর: ৩৩.০০.০০০০.১৩০.৯৯.০২৭.১৯.১৭", "MOFL17", 1, "header", "pdf_text", notes="signed Subrata Bhowmik, Joint Secretary, 'রাষ্ট্রপতির আদেশক্রমে'")
R(pk, "approving_body", "Ministry of Fisheries and Livestock (MoFL), Fisheries-5 Branch", "মৎস্য ও প্রাণিসম্পদ মন্ত্রণালয় মৎস্য-০৫ অধিশাখা", "MOFL22", 1, "letterhead", "visual_check", "visual_check")
R(pk, "approval_or_release_mechanism", "R1_statutory: MoFL naming notification (প্রজ্ঞাপন) 33.00.0000.130.99.027.19-22 of 04 Aug 2021, renamed by 33.00.0000.130.99.027.19.17 of 11 Apr 2022", "প্রজ্ঞাপন ... জাতটিকে সুবর্ণ রুই (Subarno Rui) নামকরণ করা হইল", "MOFL22", 1, "title 'প্রজ্ঞাপন' + para 02", "visual_check", "visual_check", notes="memo B2: 'an MoFL or gazette notification that names or authorises the strain' = R1. It is a naming notification, not an approval under Hatchery Act s.6(2). The copy list asks DPP to publish it in the next issue of the Bangladesh Gazette (gazette issue not located; not in bgpress extraordinary list for MoFL)")
R(pk, "approval_or_release_mechanism", "R2_institute_release: BFRI declaration and release event, 10 Jun 2021; listed as BFRI technology no. 51 (TVC 2025)", "প্রযুক্তি অবমুক্তকরণ ও আনুষ্ঠানিকতা ... ঘোষণা ও অবমুক্ত করা হয়েছে", "LEAF95", 1, "right panel", "visual_check", "visual_check")
R(pk, "releasing_body", "MoFL (naming); BFRI (declaration and release)", "মৎস্য ও প্রাণিসম্পদ মন্ত্রণালয় কর্তৃক প্রজ্ঞাপনের মাধ্যমে", "LEAF95", 1, "left panel para 1", "visual_check", "visual_check", "medium")
R(pk, "distribution_channel", "20,000 fry to 10 DoF hatcheries; 30 kg spawn to 40 farmers/entrepreneurs/hatcheries (previous season); 69 kg spawn to 47 (current season)", "২০,০০০ পোনা এ পর্যন্ত মৎস্য অধিদপ্তরের ১০টি হ্যাচারিতে বিতরণ ... ৪০ জন ... ৩০ কেজি রেণু ... ৪৭ জন ... ৬৯ কেজি রেণু", "LEAF95", 1, "right panel 'জার্মপ্লাজম বিতরণ ও সম্প্রসারণ'", "visual_check", "visual_check", "medium", notes="seasons not dated in leaflet (published 2022)")
R(pk, "distribution_channel", "255 kg spawn of BFRI Shuborno Rui produced at BFRI Freshwater Station hatchery (2023-24) and distributed to farmers, hatchery and nursery owners", "BFRI Shuborno Rui 255.00 - April-July", "AR2324", method="pdf_text", find="BFRI Shuborno Rui 255.00")
R(pk, "status", "Widely disseminated in the field (BFRI TVC 2025, technology no. 51)", "অধিক উৎপাদনশীল বিএফআরআই সুবর্ণ রুই” উদ্ভাবন | মাঠ পর্যায়ে ব্যাপক সম্প্রসারিত", "TVC", 3, "সারণি-২ row ৫১", "visual_check", "visual_check", notes="crop 04_working/crops/P2F/bfri_tvc_p3_row51.png")
R(pk, "release_category", "R1_statutory", "", "MOFL22", 1, "", "visual_check", "visual_check", notes="derived: R1 because MoFL notification found; R2 evidence also present")
R(pk, "cgiar_role", "4", "", "LEAF95", 1, "middle panel", "visual_check", "unvalidated", "medium", notes="base population from wild river stocks bred by BFRI; no CGIAR element in MoFL notification, leaflet or AR 2020-21. WorldFish G3 rohu is a separate program (FIL Aug 2023 contrasts the two)")
R(pk, "source_url", "https://mofl.gov.bd/pages/notification-circulars", "", "MOFLLIST", "", "row 2 'প্রজ্ঞাপন ২২'", "html", notes="PDF: objectstorage .../office-mofl/2024/12/6d8d5a3bc970485c9ea63316bd86e4d2.pdf")
R(pk, "approval_date", "2021-08-04", "প্রজ্ঞাপন ২২ ... (০৪/০৮/২০২১) | ০৪-০৮-২০২১", "MOFLLIST", "", "row 2 title + publish date", "html", "two_source", notes="listing confirms both notifications; search 'রুই' returns exactly 2 entries")
R(pk, "approval_date", "2021-08-04", "রুই মাছের জাত 'সুবর্ণ রুই' নামকরণ", "FRIPRAJ", "", "row ৩", "html", "two_source", "medium", notes="BFRI page lists both notifications (attachments are images/PDF); confirms BFRI holds them")

# ======================= BFRI improved rohu F1 (2009) =======================
pk = "FISH_BFRI_ROHU_F1_2009"
R(pk, "species_scientific", "Labeo rohita", "রুই মাছের (Labeo rohita) উন্নত জাত", "TVC", 2, "সারণি-২ row ১৮", "visual_check", "visual_check", notes="crop bfri_tvc_p2_rows18-22.png")
R(pk, "species_common_en", "Rohu", "", "TVC", 2, "row ১৮", "visual_check", "visual_check")
R(pk, "species_bn", "রুই", "রুই মাছের", "TVC", 2, "row ১৮", "visual_check", "visual_check")
R(pk, "strain_name", "রুই মাছের উন্নত জাত (বিদ্যমান জাত হতে ১৬% বেশী উৎপাদনশীল)", "রুই মাছের (Labeo rohita) উন্নত জাত (বিদ্যমান জাত হতে ১৬% বেশী উৎপাদনশীল) উদ্ভাবন", "TVC", 2, "row ১৮", "visual_check", "visual_check", notes="no proper name; BFRI ARs 2016-18 call the line 'BFRI Rohu'")
R(pk, "local_name", "BFRI Rohu", "Genetic improvement of BFRI Rohu, Labeo rohita through selection", "AR1617", method="pdf_text", find="Genetic improvement of BFRI Rohu, Labeo rohita through selection")
R(pk, "release_date", "2009", "২০০৯ সালে দেশীয় রুই মাছের নতুন উন্নত জাত উদ্ভাবন করতে সক্ষম হয়েছেন", "GLANCE", "", '"২০০৯ সালে দেশীয় রুই মাছের নতুন উন্নত জাত উদ্ভাবন"', "html", "two_source", "medium", notes="year of development (উদ্ভাবন), not a dated release statement; two_source with leaflet 95 ('২০০৯ সালে ... ১ম প্রজন্মের (F1)')")
R(pk, "release_date", "2009", "২০০৯ সালে রুই মাছের উন্নত জাতের ১ম প্রজন্মের (F1) মাছ উদ্ভাবন করা হয়েছে", "LEAF95", 1, "middle panel bullet 2", "visual_check", "visual_check", "medium")
R(pk, "generation", "F1 (first generation)", "ক্রস ব্রিডিং পদ্ধতিতে প্রথম প্রজন্মের উন্নত রুই জাত", "GLANCE", "", '"প্রথম প্রজন্মের উন্নত রুই জাত"', "html", "two_source")
R(pk, "pedigree", "Wild rohu from several rivers, cross-breeding", "দেশের বিভিন্ন নদী উৎস থেকে রুই মাছের বন্যজাত(wild) সংগ্র্রহ করে ক্রস ব্রিডিং পদ্ধতিতে", "GLANCE", "", "quoted phrase", "html", conf="medium", notes="leaflet 95 instead says mass selection from a di-allele-cross base population")
R(pk, "key_traits", "16% more productive than existing strain", "বিদ্যমান জাত হতে ১৬ ভাগ অধিক উৎপাদনশীল", "GLANCE", "", "quoted phrase", "html", "two_source", notes="two_source with TVC row 18 ('১৬% বেশী'). CONFLICT: leaflet 95 gives F1 = +7.5% over base population; FAO Annex J slide gives 'BFRI Rohu: 15-20%'")
R(pk, "key_traits", "7.5% more productive than the base population (F1)", "বেইজ পপুলেশন থেকে ৭.৫% অধিক উৎপাদনশীল", "LEAF95", 1, "middle panel bullet 2", "visual_check", "visual_check", "medium", notes="conflicts with 16% (GLANCE, TVC); 16.83% is the leaflet's 3rd-generation figure")
R(pk, "key_traits", "BFRI Rohu: 15-20% higher growth rate than normal breed", "BFRI Rohu: 15-20% higher growth rate than normal breed", "FAOJ", method="pdf_text", find="BFRI Rohu: 15-20% higher growth rate")
R(pk, "approval_or_release_mechanism", "R2_institute_release: BFRI statement of development (2009) + National Fisheries Week 2010 gold medal + TVC list row 18", "এ জাত উদ্ভাবনের জন্য ইনস্টিটিউটকে জাতীয় মৎস্য সপ্তাহ ২০১০ স্বর্ণপদক প্রদান করা হয়", "GLANCE", "", "quoted phrase", "html", conf="medium", notes="no dated release/declaration statement found; award is recognition, not approval")
R(pk, "key_traits", "Award: gold medal 2010 for 'রুই মাছের উন্নত জাত উদ্ভাবন'", "রুই মাছের উন্নত জাত উদ্ভাবন ২০১০ স্বর্ণপদক", "AWARDS", "", "awards table row", "html", "two_source", notes="two_source with GLANCE (National Fisheries Week 2010)")
R(pk, "releasing_body", "BFRI", "", "TVC", 2, "row ১৮", "visual_check", "visual_check")
R(pk, "distribution_channel", "BFRI Rohu spawn among species produced at BFRI-FS hatchery 2009-2013 (275-345 kg spawn/yr all species combined)", "BFRI Rohu, BFRI Rajpunti, Catla (Halda, Jamuna) ... 2009 275", "FAOJ", method="pdf_text", find="BFRI Rohu, BFRI Rajpunti, Catla (Halda, Jamuna)", conf="medium", notes="quantities are for all listed species together")
R(pk, "status", "Widely disseminated in the field (TVC 2025, row 18)", "মাঠ পর্যায়ে ব্যাপক সম্প্রসারিত", "TVC", 2, "row ১৮", "visual_check", "visual_check", notes="the 2009 F1 line is the ancestor of Subarna rui (G4); TVC lists both separately")
R(pk, "release_category", "R2_institute_release", "", "TVC", 2, "row ১৮", "visual_check", "visual_check", "medium")
R(pk, "cgiar_role", "4", "", "GLANCE", "", "", "html", conf="medium", notes="wild river stocks, BFRI; no CGIAR element found")

# ======================= BFRI GIFT / Super tilapia =======================
pk = "FISH_BFRI_GIFT"
R(pk, "species_scientific", "Oreochromis niloticus", "বিএফআরআই সুপার তেলাপিয়ার (Oreochromis niloticus)", "TVC", 2, "সারণি-২ row ৭", "visual_check", "visual_check", notes="crop bfri_tvc_p2_rows7-8.png")
R(pk, "species_common_en", "Nile tilapia", "", "TVC", 2, "row ৭", "visual_check", "visual_check")
R(pk, "species_bn", "তেলাপিয়া", "তেলাপিয়া", "TVC", 2, "row ৭", "visual_check", "visual_check")
R(pk, "strain_name", "বিএফআরআই সুপার তেলাপিয়া", "বিএফআরআই সুপার তেলাপিয়ার (Oreochromis niloticus) পোনা উৎপাদন ও চাষ: বিভিন্ন উৎসের তেলাপিয়া জাত থেকে নির্বাচিত পদ্ধতিতে (family selection) উন্নত জাতের তেলাপিয়া উৎপাদন", "TVC", 2, "row ৭", "visual_check", "visual_check")
R(pk, "strain_name", "বিএফআরআই গিফট জাত (BFRI GIFT Strain) = সুপার তেলাপিয়া", "গিফট তেলাপিয়ার জাত উন্নয়ন করা হয়েছে, যা সুপার তেলাপিয়া হিসেবে নামকরণ করা হয় ... বিএফআরআই গিফট জাত (BFRI GIFT Strain) হিসাবে অভিহিত", "SUPERTIL", 2, "p2 intro para", "ocr", "visual_check", notes="crop 04_working/crops/P2F/bfri_super_tilapia_p2_top.png; booklet undated; naming date not stated")
R(pk, "strain_name", "BFRI Super GIFT strain", "the newly improved strain has been renamed BFRI Super GIFT strain", "HUSSAIN", method="pdf_text", find="renamed BFRI Super GIFT strain", notes="WorldFish authors incl. M. G. Hussain (ex-BFRI DG); no naming date")
R(pk, "local_name", "BFRI GIFT; BFRI GIF tilapia; Super tilapia", "BFRI GIF tilapia and 8.0 kg of spawn", "AR2021", method="pdf_text", find="BFRI GIF tilapia", conf="medium")
R(pk, "developer", "BFRI (Freshwater Station, Mymensingh) in collaboration with WorldFish, Penang", "this work has been conducted in collaboration with the WorldFish, Penang, Malaysia", "AR1617", method="pdf_text", find="conducted in collaboration with the WorldFish, Penang, Malaysia")
R(pk, "pedigree", "GIFT founder stock of 30 families (300 individuals) introduced from Malaysia through WorldFish in March 2005; family selection thereafter", "The founder stock comprised of 30 families having 300 individuals of the GIFT strain was introduced from Malaysia through WorldFish in March 2005", "AR1617", method="pdf_text", find="introduced from Malaysia through WorldFish in March 2005", notes="AR also says BFRI family selection program 'since 1995' (sic) - conflicts with 2005 founder date and with Hussain (family selection from 2005)")
R(pk, "pedigree", "GIFT received 1994 (first batch) and 1996 (116 families) from WorldFish; mass selection 1998-2004 (F6 +32.66%); family selection from 2005; six generations 2008-2012", "BFRI received the first batch of GIFT strain tilapia in 1994, and 116 families of the same strain in 1996", "HUSSAIN", method="pdf_text", find="BFRI received the first batch of GIFT strain tilapia in 1994")
R(pk, "generation", "14th generation of GIFT strain (by 2012)", "Six generations were developed from 2008–2012 through family selection (14th generation of GIFT strain)", "HUSSAIN", method="pdf_text", find="Six generations were developed from 2008", notes="CONFLICT (generation numbering): counts generations differently from BFRI ARs (which number BFRI family-selection generations from the 2005 founders: F-10 in 2016-17/2017, F-14 in 2020-21). Do not reconcile.")
R(pk, "generation", "F1-F10 of family selection reported (gains 7.17%...56.25% over founder population)", "7.17, 13.60, 23.21, 30.30, 35.38, 39.25, 43.19, 49.03, 52.82 and 56.25% greater harvest weight than that of the founder population in F1 ... F10", "AR1617", method="pdf_text", find="greater harvest weight than that of the founder population in F1")
R(pk, "generation", "F-10 breeders mated July 2017 (towards F-11/F-12)", "On the basis of breeding values of F-10 generation, the best 50 males have been crossed with 50 females", "AR1819", method="pdf_text", find="On the basis of breeding values of F-10 generation")
R(pk, "generation", "F-14 (2020-21)", "F-14 generation of BFRI GIFT was developed", "AR2021", method="pdf_text", find="F-14 generation of BFRI GIFT was developed")
R(pk, "generation", "F-13 (cohort breeding, stocked Sept 2022)", "The F-13 generations of GIFT fingerlings ... stocked in September 2022", "AR2223", method="pdf_text", find="The F-13 generations of GIFT fingerlings", notes="CONFLICT: AR 2022-23 cohort-breeding line is F-13 after AR 2020-21 reported F-14; may be a separate line or numbering slip")
R(pk, "key_traits", "BFRI GIFT 50-60% more productive than local or other tilapia strains", "স্থানীয় জাত বা অন্যান্য তেলাপিয়ার চেয়ে শতকরা ৫০-৬০ ভাগ বেশি উৎপাদনশীল", "SUPERTIL", 2, "p2 intro para", "ocr", "visual_check", notes="crop bfri_super_tilapia_p2_top.png")
R(pk, "key_traits", "BFRI GIFT 32-66% more productive than ordinary local GIFT", "সাধারণ স্থানীয় গিফট জাতের তেলাপিয়ার তুলনায় ... বিএফআরআই গিফট জাত ৩২-৬৬% অধিক উৎপাদনশীল", "GIFTLEAF", 1, "intro para", "pdf_text", conf="medium", notes="legacy-font text layer read as Unicode with glyph noise; numbers as extracted ('৩২-৬৬%') not visually checked -> unvalidated")
R(pk, "key_traits", "BFRI GIFT Tilapia: 35-40% higher growth rate than normal breed", "BFRI GIFT Tilapia: 35-40% higher growth rate than normal breed", "FAOJ", method="pdf_text", find="BFRI GIFT Tilapia: 35-40% higher growth")
R(pk, "approval_or_release_mechanism", "R2_institute_release: listed as BFRI technology no. 7 (TVC 2025); renamed 'BFRI Super GIFT' (no date)", "বিএফআরআই সুপার তেলাপিয়ার ... পোনা উৎপাদন ও চাষ | মাঠ পর্যায়ে ব্যাপক সম্প্রসারিত", "TVC", 2, "row ৭", "visual_check", "visual_check", "medium", notes="no dated release or naming statement found; no MoFL notification (MoFL search 'তেলাপিয়া', 'গিফট' = 0 hits)")
R(pk, "releasing_body", "BFRI", "", "TVC", 2, "row ৭", "visual_check", "visual_check")
R(pk, "distribution_channel", "Improved germplasm to >200 tilapia hatcheries per year", "supply improved germplasm every year to over 200 tilapia hatcheries", "AR1617", method="pdf_text", find="supply improved germplasm every year to over 200 tilapia hatcheries", notes="Hussain c.2014: >1.0 million broodstock/yr to 200 hatcheries")
R(pk, "distribution_channel", "BFRI GIFT germplasm to DoF hatcheries Raipur (Lakshmipur) and Nimgachi (Sirajganj), 2020-21; 1.50 lakh fry + 8.0 kg spawn distributed in 2020-21", "The improved germplasm of BFRI GIFT and BFRI Vietnamies Koi were distributed among the selected hatchery of Department of Fisheries", "AR2021", method="pdf_text", find="The improved germplasm of BFRI GIFT and BFRI Vietnamies Koi were distributed")
R(pk, "distribution_channel", "BFRI GIFT fry from BFRI-FS hatchery: 0.5 M (2009) rising to 2.50 M (2013); ~150 hatcheries maintain BFRI GIFT", "BFRI GIFT 2009 0.5 ... 2013 2.50 Note: About 150 Tilapia hatcheries maintained BFRI GIFT", "FAOJ", method="pdf_text", find="About 150 Tilapia hatcheries maintained BFRI GIFT", conf="medium", notes="2013 value is a target in the slide")
R(pk, "status", "Widely disseminated in the field (TVC 2025, row 7)", "মাঠ পর্যায়ে ব্যাপক সম্প্রসারিত", "TVC", 2, "row ৭", "visual_check", "visual_check")
R(pk, "release_category", "R2_institute_release", "", "TVC", 2, "row ৭", "visual_check", "visual_check", "medium")
R(pk, "cgiar_role", "2", "", "AR1617", method="pdf_text", find="introduced from Malaysia through WorldFish in March 2005", notes="derived from WorldFish GIFT germplasm (1994/1996 batches; 2005 Jitra founders) by BFRI selection")
R(pk, "cgiar_center", "WorldFish (formerly ICLARM)", "provided in 1994 by WorldFish (formerly ICLARM) under the Dissemination and Evaluation of Genetically Improved Tilapia in Asia (DEGITA) project", "HUSSAIN", method="pdf_text", find="provided in 1994 by WorldFish (formerly ICLARM)")
R(pk, "cgiar_evidence", "AR 2016-17 p58: GIFT founders (30 families) introduced from Malaysia through WorldFish, March 2005; Hussain c.2014 p2: GIFT batches 1994 and 1996 (116 families)", "", "AR1617", method="pdf_text", find="introduced from Malaysia through WorldFish in March 2005")

# ======================= BFRI improved tilapia (~50%) TVC row 19 =======================
pk = "FISH_BFRI_TILAPIA_IMPROVED_50PCT"
R(pk, "strain_name", "তেলাপিয়ার উন্নত জাত (প্রায় ৫০% বেশী উৎপাদনশীল)", "তেলাপিয়ার (Oreochromis niloticus) উন্নত জাত (প্রায় ৫০% বেশী উৎপাদনশীল) উদ্ভাবন", "TVC", 2, "সারণি-২ row ১৯", "visual_check", "visual_check", notes="crop bfri_tvc_p2_rows18-22.png")
R(pk, "species_scientific", "Oreochromis niloticus", "(Oreochromis niloticus)", "TVC", 2, "row ১৯", "visual_check", "visual_check")
R(pk, "key_traits", "about 50% more productive", "প্রায় ৫০% বেশী উৎপাদনশীল", "TVC", 2, "row ১৯", "visual_check", "visual_check", notes="probably the same BFRI GIFT/Super tilapia line (Super tilapia booklet: 50-60%) but the TVC lists it separately from row 7; identity not documented")
R(pk, "status", "Widely disseminated in the field", "মাঠ পর্যায়ে ব্যাপক সম্প্রসারিত", "TVC", 2, "row ১৯", "visual_check", "visual_check")
R(pk, "approval_or_release_mechanism", "R2_institute_release: TVC list row 19 (no date)", "", "TVC", 2, "row ১৯", "visual_check", "visual_check", "medium")
R(pk, "cgiar_role", "5", "", "TVC", 2, "row ১৯", "visual_check", "unvalidated", "low", notes="if identical to BFRI GIFT it would be 2; not documented")

# ======================= GIFT introduction (WorldFish/ICLARM, 1994/1996) =======================
pk = "FISH_WF_GIFT_INTRO_1994"
R(pk, "strain_name", "GIFT (Genetically Improved Farmed Tilapia)", "Genetically Improved Farmed Tilapia (GIFT) strain, provided in 1994 by WorldFish (formerly ICLARM)", "HUSSAIN", method="pdf_text", find="provided in 1994 by WorldFish (formerly ICLARM)")
R(pk, "species_scientific", "Oreochromis niloticus", "improved Oreochromis niloticus i.e. Genetically Improved Farmed Tilapia (GIFT)", "HUSSAIN", method="pdf_text", find="improved Oreochromis niloticus i.e. Genetically Improved Farmed Tilapia")
R(pk, "developer", "WorldFish (ICLARM), DEGITA project", "under the Dissemination and Evaluation of Genetically Improved Tilapia in Asia (DEGITA) project", "HUSSAIN", method="pdf_text", find="Dissemination and Evaluation of Genetically Improved Tilapia in Asia (DEGITA)")
R(pk, "release_date", "1994", "BFRI received the first batch of GIFT strain tilapia in 1994", "HUSSAIN", method="pdf_text", find="BFRI received the first batch of GIFT strain tilapia in 1994", notes="received by BFRI (research institute), not by hatcheries")
R(pk, "release_date", "1996", "and 116 families of the same strain in 1996", "HUSSAIN", method="pdf_text", find="116 families of the same strain in 1996")
R(pk, "release_date", "2005-03", "introduced from Malaysia through WorldFish in March 2005", "AR1617", method="pdf_text", find="introduced from Malaysia through WorldFish in March 2005", notes="third introduction (30 families, Jitra/Malaysia); founders of current BFRI GIFT")
R(pk, "key_traits", "35-57% better growth than existing local strains in BFRI trials", "resulted in a 35-57% improvement in growth performance for the GIFT strain compared to existing local strains", "HUSSAIN", method="pdf_text", find="35-57% improvement in growth performance")
R(pk, "approval_or_release_mechanism", "R3_cgiar_release (flag): WorldFish-documented transfer of GIFT to BFRI 1994/1996; no DoF import approval found", "", "HUSSAIN", method="pdf_text", find="BFRI received the first batch of GIFT strain tilapia in 1994", conf="medium", notes="transfer to a research institute rather than to hatcheries; R3 vs R4 is a judgement call (decisions_P2F)")
R(pk, "releasing_body", "WorldFish (ICLARM)", "", "HUSSAIN", method="pdf_text", find="provided in 1994 by WorldFish (formerly ICLARM)")
R(pk, "distribution_channel", "To BFRI, which selected and disseminated it (BFRI GIFT)", "", "HUSSAIN", method="pdf_text", find="BFRI received the first batch of GIFT strain tilapia in 1994")
R(pk, "cgiar_role", "1", "", "HUSSAIN", method="pdf_text", find="provided in 1994 by WorldFish (formerly ICLARM)")
R(pk, "cgiar_center", "WorldFish (ICLARM)", "", "HUSSAIN", method="pdf_text", find="provided in 1994 by WorldFish (formerly ICLARM)")
R(pk, "status", "Superseded by BFRI GIFT (selected line)", "", "HUSSAIN", method="pdf_text", find="renamed BFRI Super GIFT strain", conf="medium")

# ======================= WorldFish GIFT breeding nuclei (AIN, 2013/2015) =======================
pk = "FISH_WF_GIFT_AIN_NUCLEI"
R(pk, "strain_name", "GIFT, 11th generation (WorldFish, from Malaysia)", "four tilapia breeding nucleuses (TBNs) were established by AIN in Jessore, Laxmipur and Mymensingh districts using broodstock of the 11th generation of GIFT brought to Bangladesh from Malaysia", "WFBLOG", "", '"broodstock of the 11th generation of GIFT brought to Bangladesh from Malaysia"', "html")
R(pk, "species_scientific", "Oreochromis niloticus", "", "WFBLOG", "", "", "html")
R(pk, "generation", "G11", "11th generation of GIFT", "WFBLOG", "", "quoted phrase", "html", notes="CONFLICT: Hussain c.2014 says five TBNs used the '14th generation improved base population of GIFT ... from BFRI, Bangladesh, and Jitra Station, Malaysia'")
R(pk, "generation", "14th generation (base population from BFRI and Jitra)", "using 14th generation improved base population of GIFT strains collected both from BFRI, Bangladesh, and Jitra Station, Malaysia", "HUSSAIN", method="pdf_text", find="using 14th generation improved base population of GIFT")
R(pk, "release_date", "2013", "In 2013, four tilapia breeding nucleuses (TBNs) were established by AIN", "WFBLOG", "", "quoted phrase", "html")
R(pk, "release_date", "2015", "During 2015, the project established three new TBNs, which have provided 2.1 million GIFT fry of the same generation to 59 hatcheries", "WFBLOG", "", "quoted phrase", "html")
R(pk, "distribution_channel", "Tilapia breeding nuclei in public/private hatcheries (Jessore, Laxmipur, Mymensingh, Barguna); 2.1 M fry to 59 hatcheries (2015)", "Green Field Hatchery, Laxmipur ... Sonar Bangla Hatchery, Bamna, Barguna ... Nova Tilapia Hatchery ... Govt. Fish Farm, Base Para, Jessore ... Genetic Hatchery, Noapara, Jessore", "HUSSAIN", method="pdf_text", find="Green Field Hatchery, Laxmipur")
R(pk, "developer", "WorldFish (projects RFLDC/DANIDA, CSISA-BD, USAID AIN)", "", "HUSSAIN", method="pdf_text", find="RFLDC-DANIDA project, CSISA-BD project")
R(pk, "approval_or_release_mechanism", "R3_cgiar_release: WorldFish-documented establishment of GIFT nuclei with dated fry distribution (2013, 2015); no government approval found", "", "WFBLOG", "", "", "html")
R(pk, "releasing_body", "WorldFish (AIN project)", "", "WFBLOG", "", "", "html")
R(pk, "cgiar_role", "1", "", "WFBLOG", "", "", "html")
R(pk, "cgiar_center", "WorldFish", "", "WFBLOG", "", "", "html")

# ======================= WorldFish GIFT G19 to EON (2025) =======================
pk = "FISH_WF_GIFT_G19_EON_2025"
R(pk, "strain_name", "G19 GIFT (WorldFish Penang)", "the dataset includes basic data on the genetic management of G19 GIFT by the EON Group, which received the improved GIFT germplasm from WorldFish Penang in 2025", "DV_BF", "", "dsDescription", "api_json", notes="new candidate not in memo B3")
R(pk, "generation", "G19", "G19 GIFT", "DV_BF", "", "dsDescription", "api_json")
R(pk, "release_date", "2025", "received the improved GIFT germplasm from WorldFish Penang in 2025", "DV_BF", "", "dsDescription", "api_json")
R(pk, "distribution_channel", "To EON Group (private) for cohort-based broodstock multiplication and seed production", "application of cohort-based mating schemes used by EON for broodstock multiplication", "DV_BF", "", "dsDescription", "api_json")
R(pk, "approval_or_release_mechanism", "R3_cgiar_release: WorldFish dataset documents transfer of G19 GIFT to a Bangladeshi company in 2025; no import approval found", "", "DV_BF", "", "dsDescription", "api_json", conf="medium", notes="data files behind a Dataverse guestbook; not downloaded")
R(pk, "releasing_body", "WorldFish (Penang)", "", "DV_BF", "", "dsDescription", "api_json")
R(pk, "cgiar_role", "1", "", "DV_BF", "", "", "api_json")
R(pk, "cgiar_center", "WorldFish", "", "DV_BF", "", "", "api_json")
R(pk, "species_scientific", "Oreochromis niloticus", "", "WFDISS", "", "GIFT Tilapia (Rapid Growth Strain)", "html", notes="WorldFish page: GIFT generation available G20 (2026), 'subject to national approvals and laws'")

# ======================= BFRI rajputi (silver barb) =======================
pk = "FISH_BFRI_RAJPUTI"
R(pk, "strain_name", "রাজপুঁটির উন্নত জাত (প্রায় ৩৫% বেশী উৎপাদনশীল)", "রাজপুঁটির (Systomus sarana) উন্নত জাত (প্রায় ৩৫% বেশী উৎপাদনশীল) উদ্ভাবন", "TVC", 2, "সারণি-২ row ২০", "visual_check", "visual_check", notes="crop bfri_tvc_p2_rows18-22.png")
R(pk, "species_scientific", "Systomus sarana (as printed by BFRI TVC)", "রাজপুঁটির (Systomus sarana)", "TVC", 2, "row ২০", "visual_check", "visual_check", "low", notes="CONFLICT: Systomus sarana is the native sarpunti; BFRI ARs 2016-18 name BFRI Rajpunti 'Puntius gonionotus' (= Barbonymus gonionotus, silver barb), and TVC row 4 uses Barbonymus gonionotus for স্বরপুঁটি. Do not reconcile")
R(pk, "species_scientific", "Puntius gonionotus (= Barbonymus gonionotus)", "Genetic management of BFRI Rajpunti, Puntius gonionotus", "AR1617", method="pdf_text", find="Genetic management of BFRI Rajpunti, Puntius gonionotus")
R(pk, "species_common_en", "Silver barb (Java barb)", "Silver Barbs (Rajpunti)", "AR2324", method="pdf_text", find="Silver Barbs (Rajpunti)")
R(pk, "species_bn", "রাজপুঁটি", "রাজপুঁটির", "TVC", 2, "row ২০", "visual_check", "visual_check")
R(pk, "local_name", "Thai sarpunti (থাই সরপুঁটি); BFRI named it রাজপুঁটি", "আমাদের দেশে এ মাছটি থাই সরপুঁটি নামে পরিচিত ... ১৯৭৭ সালে থাইল্যান্ড হতে এদেশে আনা হয় ... বিএফআরআই এ মাছের নামকরণ করেছে রাজপুঁটি", "RAJLEAF", 1, "intro para", "pdf_text", conf="medium", notes="species introduced 1977 (species introduction -> excluded list); the improved strain is BFRI's later selection")
R(pk, "local_name", "BFRI Rajpunti", "BFRI Rajpunti: 32-36% higher growth rate than normal breed", "FAOJ", method="pdf_text", find="BFRI Rajpunti: 32-36% higher growth rate")
R(pk, "key_traits", "about 35% more productive", "প্রায় ৩৫% বেশী উৎপাদনশীল", "TVC", 2, "row ২০", "visual_check", "visual_check", notes="FAO Annex J: 32-36%")
R(pk, "key_traits", "Award: gold medal 2004 for 'রাজপুঁটির জাত উন্নয়ন'", "রাজপুঁটির জাত উন্নয়ন ২০০৪ স্বর্ণপদক", "AWARDS", "", "awards table row", "html", conf="medium", notes="awarding body not named on the page for this row")
R(pk, "generation", "F4 broodstock used to produce F5 (2017); F6 planned 2018", "The improved F4 generation of rajpunti broodstock (4 groups as A B C D) were used for the production of next generation (F5 progeny)", "AR1617", method="pdf_text", find="The improved F4 generation of rajpunti broodstock")
R(pk, "release_date", "", "", "TVC", 2, "row ২০", "visual_check", "unvalidated", "low", notes="no release or declaration date found; earliest dated recognition = 2004 medal")
R(pk, "approval_or_release_mechanism", "R2_institute_release: TVC list row 20 + 2004 medal (no release date)", "", "TVC", 2, "row ২০", "visual_check", "visual_check", "medium")
R(pk, "releasing_body", "BFRI", "", "TVC", 2, "row ২০", "visual_check", "visual_check")
R(pk, "distribution_channel", "123.1 kg silver barb (Rajpunti) spawn produced at BFRI-FS hatchery 2023-24 and distributed", "Silver barb (Rajpunti) 123.100", "AR2324", method="pdf_text", find="Silver barb (Rajpunti) 123.100")
R(pk, "status", "Less widely disseminated (TVC 2025, row 20)", "মাঠ পর্যায়ে অপেক্ষাকৃত কম সম্প্রসারিত", "TVC", 2, "row ২০", "visual_check", "visual_check")
R(pk, "release_category", "R2_institute_release", "", "TVC", 2, "row ২০", "visual_check", "visual_check", "medium")
R(pk, "cgiar_role", "4", "", "RAJLEAF", 1, "", "pdf_text", conf="low", notes="species from Thailand 1977; origin of the improved base population not documented; no CGIAR element found")

# ======================= BFRI Vietnamese / Thai koi =======================
pk = "FISH_BFRI_VIETNAMESE_KOI"
R(pk, "strain_name", "থাই কৈ মাছের জাত উন্নয়ন (TVC wording)", "থাই কৈ (Anabas testudineus) মাছের জাত উন্নয়ন", "TVC", 2, "সারণি-২ row ২১", "visual_check", "visual_check", notes="crop bfri_tvc_p2_rows18-22.png. CONFLICT: TVC says 'Thai koi', BFRI ARs describe stock improvement of 'Vietnamese koi' from Vietnam broodstock")
R(pk, "strain_name", "BFRI Vietnamese Koi", "BFRI Vietnamies Koi", "AR2021", method="pdf_text", find="BFRI GIFT and BFRI Vietnamies Koi")
R(pk, "species_scientific", "Anabas testudineus", "(Anabas testudineus)", "TVC", 2, "row ২১", "visual_check", "visual_check")
R(pk, "species_common_en", "Climbing perch", "Climbing Perch Koi", "AR2021", method="pdf_text", find="Stock Improvement and Dissemination of Tilapia and Climbing Perch Koi")
R(pk, "species_bn", "কৈ", "কৈ", "TVC", 2, "row ২১", "visual_check", "visual_check")
R(pk, "pedigree", "1000 broodstock obtained from Vietnam; broodstock replacement technique", "The breeding program was initiated involving 1000 brood stock obtained from Vietnam to produce the F-1 generation", "AR1617", method="pdf_text", find="1000 brood stock obtained from Vietnam")
R(pk, "generation", "F-1 (2016-17; +4.79%)", "The F-1 generation of Vietnamese Koi showed 4.79% higher growth than non selected group", "AR1617", method="pdf_text", find="The F-1 generation of Vietnamese Koi showed 4.79% higher growth")
R(pk, "generation", "F-5 (produced April-May 2021)", "For the production of F-5 generation, the following protocols were followed during April- May 2021", "AR2021", method="pdf_text", find="For the production of F-5 generation")
R(pk, "distribution_channel", "Germplasm to DoF hatcheries: Raipur (Lakshmipur) 1500, Nimgachi (Sirajganj) 2000, Faridpur 5000 (2020-21); 0.20 lakh BFRI Vietnamese koi distributed 2020-21", "The improved germplasm of BFRI GIFT and BFRI Vietnamies Koi were distributed among the selected hatchery of Department of Fisheries", "AR2021", method="pdf_text", find="The improved germplasm of BFRI GIFT and BFRI Vietnamies Koi were distributed")
R(pk, "approval_or_release_mechanism", "R2_institute_release: TVC list row 21 (no date); otherwise R4 dissemination to DoF hatcheries 2020-21", "", "TVC", 2, "row ২১", "visual_check", "visual_check", "medium", notes="flag: TVC row names 'Thai koi', not Vietnamese koi")
R(pk, "releasing_body", "BFRI", "", "TVC", 2, "row ২১", "visual_check", "visual_check")
R(pk, "status", "Less widely disseminated (TVC 2025, row 21)", "মাঠ পর্যায়ে অপেক্ষাকৃত কম সম্প্রসারিত", "TVC", 2, "row ২১", "visual_check", "visual_check")
R(pk, "release_category", "R2_institute_release", "", "TVC", 2, "row ২১", "visual_check", "visual_check", "low", notes="R2 only via TVC inclusion; strain identity Thai vs Vietnamese unresolved")
R(pk, "cgiar_role", "4", "", "AR1617", method="pdf_text", find="1000 brood stock obtained from Vietnam", conf="medium")

# ======================= BFRI red tilapia =======================
pk = "FISH_BFRI_RED_TILAPIA"
R(pk, "strain_name", "লাল তেলাপিয়ার জাত উন্নয়ন (Red tilapia)", "লাল তেলাপিয়ার (Red tilapia, Oreochromis niloticus) জাত উন্নয়ন", "TVC", 2, "সারণি-২ row ২২", "visual_check", "visual_check", notes="crop bfri_tvc_p2_rows18-22.png")
R(pk, "species_scientific", "Oreochromis sp. (red tilapia; TVC prints Oreochromis niloticus)", "(Red tilapia, Oreochromis niloticus)", "TVC", 2, "row ২২", "visual_check", "visual_check", "medium", notes="Hussain c.2014 describes the 1988 Thai red strain as O. mossambicus x O. niloticus hybrid; the 2005 Malaysian red batch parentage not stated")
R(pk, "species_bn", "লাল তেলাপিয়া", "লাল তেলাপিয়ার", "TVC", 2, "row ২২", "visual_check", "visual_check")
R(pk, "pedigree", "Malaysian red strain brought by WorldFish in 2005, progeny-tested (100% red), improved by cohort/rotational breeding", "The World Fish Center brought a new batch of red tilapia strain to Bangladesh in 2005 ... Malaysian red strain produced 100% all red progeny", "HUSSAIN", method="pdf_text", find="brought a new batch of red tilapia strain to Bangladesh in 2005")
R(pk, "approval_or_release_mechanism", "R2_institute_release: TVC list row 22 (no date)", "", "TVC", 2, "row ২২", "visual_check", "visual_check", "medium")
R(pk, "releasing_body", "BFRI", "", "TVC", 2, "row ২২", "visual_check", "visual_check")
R(pk, "status", "Less widely disseminated (TVC 2025, row 22)", "মাঠ পর্যায়ে অপেক্ষাকৃত কম সম্প্রসারিত", "TVC", 2, "row ২২", "visual_check", "visual_check")
R(pk, "release_category", "R2_institute_release", "", "TVC", 2, "row ২২", "visual_check", "visual_check", "medium")
R(pk, "cgiar_role", "2", "", "HUSSAIN", method="pdf_text", find="brought a new batch of red tilapia strain to Bangladesh in 2005", conf="medium", notes="germplasm brought by WorldFish (2005); BFRI improved it")
R(pk, "cgiar_center", "WorldFish", "", "HUSSAIN", method="pdf_text", find="brought a new batch of red tilapia strain to Bangladesh in 2005", conf="medium")

# ======================= BFRI improved hybrid magur =======================
pk = "FISH_BFRI_HYBRID_MAGUR"
R(pk, "strain_name", "উন্নত জাতের হাইব্রিড মাগুর", "উন্নত জাতের হাইব্রিড মাগুরের চাষ", "TVC", 3, "সারণি-২ row ৪১", "visual_check", "visual_check", notes="crop bfri_tvc_p3_row41.png; cross not stated")
R(pk, "strain_name", "শংকর জাতের মাগুর", "৩১. শংকর জাতের মাগুরের পোনা উৎপাদন ও চাষ", "TECHPAGE", "", "legacy list item ৩১", "html", conf="medium")
R(pk, "species_bn", "মাগুর (hybrid)", "হাইব্রিড মাগুরের", "TVC", 3, "row ৪১", "visual_check", "visual_check")
R(pk, "species_scientific", "", "", "TVC", 3, "row ৪১", "visual_check", "unvalidated", "low", notes="parent species not stated in any source read; C. batrachus x C. gariepinus is an assumption NOT recorded")
R(pk, "status", "Not functional at present (TVC 2025)", "বর্তমান সময়ে কার্যকরী নয়", "TVC", 3, "row ৪১", "visual_check", "visual_check")
R(pk, "approval_or_release_mechanism", "R2_institute_release (TVC list row 41, no date); Hatchery Act 2010 s.6(2) DG DoF approval for hybrid release not found", "অনুমোদন ব্যতীত ... উদ্ভাবিত সংকরায়ন জাতের মাছ উৎপাদন বা চাষের জন্য অবমুক্ত করা যাইবে না", "HATCH", "", "s.6(2)", "html", conf="low", notes="legal requirement exists since 2010; no approval document located")
R(pk, "releasing_body", "BFRI", "", "TVC", 3, "row ৪১", "visual_check", "visual_check")
R(pk, "release_category", "R2_institute_release", "", "TVC", 3, "row ৪১", "visual_check", "visual_check", "low")
R(pk, "cgiar_role", "5", "", "TVC", 3, "row ৪১", "visual_check", "unvalidated", "low")

# ======================= WorldFish G3 rohu =======================
pk = "FISH_WF_G3_ROHU"
R(pk, "strain_name", "WorldFish G3 rohu (G3-multiplier)", "a multiplier population comprised of highly-ranked WorldFish G3 rohu families was released to hatcheries in Bangladesh", "FRONT", "", '"In 2020, a multiplier population comprised of highly-ranked WorldFish G3 rohu families"', "html")
R(pk, "local_name", "জি-থ্রি রুই / G3 Rohu", "'WorldFish G3 Rohu'", "TBS", "", "headline", "html")
R(pk, "species_scientific", "Labeo rohita", "", "FRONT", "", "title", "html")
R(pk, "species_common_en", "Rohu", "", "FRONT", "", "title", "html")
R(pk, "species_bn", "রুই", "", "WFDISS", "", "", "html", conf="medium", notes="Bangla name from common usage; WorldFish page is English")
R(pk, "developer", "WorldFish Carp Genetic Improvement Program (Jashore), funded by USAID AIN, Bangladesh Aquaculture and Nutrition Activity, Feed the Future Fish Innovation Lab, CGIAR", "From 2018 to 2020, the program was financially supported by the USAID-funded Bangladesh Aquaculture and Nutrition Activity", "FILMAY", "", "quoted phrase", "html")
R(pk, "pedigree", "Founders collected as spawn from Halda, Jamuna and Padma rivers (2012); base population 2014 (210 families); G1 2016, G2 2018, G3 2020/21", "At the start of the program in 2012, seed of three wild rohu stocks were collected from the Halda, Jamuna and Padma rivers", "WFBLOG", "", "quoted phrase", "html", "two_source", notes="two_source with Frontiers 2022 and FIL technical report")
R(pk, "generation", "G3", "generation one (G1) was spawned in 2016, G2 in 2018 and G3 in 2020/21", "FRONT", "", "quoted phrase", "html", "two_source", notes="two_source with FIL technical report and FIL May 2023 news")
R(pk, "release_date", "2020", "In 2020, a multiplier population ... was released to hatcheries in Bangladesh for development into broodstock", "FRONT", "", "Introduction", "html", "two_source", notes="two_source with FIL technical report: 7 partner hatcheries given 2.2 kg G3 multiplier spawn in 2020")
R(pk, "release_date", "2020", "This was in addition to the seven partner hatcheries supplied with 2.2 kg of G3 rohu multiplier spawn in 2020", "FILTR", method="pdf_text", find="seven partner hatcheries supplied with 2.2 kg of G3 rohu multiplier spawn in 2020", validation="two_source")
R(pk, "release_date", "2021-05", "in May 2021, Worldfish supplied four ‘partner’ hatcheries with 2.5 kg of G3 rohu multiplier spawn to be grown into broodstock", "FILTR", method="pdf_text", find="supplied four ‘partner’ hatcheries with 2.5 kg of G3 rohu multiplier spawn", notes="second release")
R(pk, "release_date", "2020-2021", "WorldFish released genetically improved ‘generation 3’ or ‘G3’ rohu hatchlings to several hatcheries in Bangladesh in 2020-21", "YEASIN22", "", "dc.description.abstract", "api_json", "two_source", notes="also Alam 2023 p5/p7: 'released ... in 2020 and 2021'")
R(pk, "release_date", "2022", "Generation 3 rohu has been disseminated to private and public hatcheries for multiplication and was made commercially available to rohu growers in 2022", "FILMAY", "", "quoted phrase", "html", "two_source", notes="first commercial seed sales by hatcheries in 2022 (FIL technical report; Frontiers 'spawned in commercial hatcheries for the first time in mid-2022')")
R(pk, "key_traits", "Realised genetic gain 38.6% (Jashore) and 34.9% (Natore-Rajshahi) in harvest weight over control; ~37% faster growth", "realised genetic gains of 38.6% (Jashore) and 34.9% (Natore–Rajshahi) for the G3-multiplier over the control strain", "FRONT", "", "Abstract", "html", "two_source")
R(pk, "approval_or_release_mechanism", "R3_cgiar_release: WorldFish release of G3 multiplier spawn to partner hatcheries (2020, May 2021); no DoF approval or MoFL notification found", "", "FILTR", method="pdf_text", find="seven partner hatcheries supplied with 2.2 kg of G3 rohu multiplier spawn in 2020", notes="MoFL notification search ('রুই', 'WorldFish', 'ওয়ার্ল্ডফিশ', 'প্রজন্ম') returned only the Subarna notices; DoF notification search 'রুই' = 0")
R(pk, "approval_or_release_mechanism", "Handover ('technology sharing') to DoF on 2023-05-09", "officially received the rapid-growing WorldFish Generation 3 (G3) rohu on behalf of DoF during a day-long international workshop held on May 9, 2023", "FILMAY", "", "quoted phrase", "html", conf="medium", notes="ceremony, not an approval instrument")
R(pk, "approval_or_release_mechanism", "Handover to BFRI on 2023-08-08", "During the day-long workshop held on August 8, 2023, Mahmud thanked the team", "FILAUG", "", "quoted phrase", "html", "two_source", "medium", notes="two_source with TBS 2023-08-08; BFRI DG speaks of 'necessary validation and comparative evaluation' with Subarna")
R(pk, "releasing_body", "WorldFish", "", "FRONT", "", "", "html")
R(pk, "distribution_channel", "Partner hatcheries -> commercial spawn sales; by Aug 2023: 38 private, 18 DoF, 1 BFRI, 2 educational hatcheries held G3 broodstock; spawn sold 245 kg (2022), 2826 kg (2023)", "At the conclusion of The Project 38 geographically-disparate private, 18 DoF, one BFRI and two educational institution hatcheries were known to maintain G3 rohu broodstock", "FILTR", method="pdf_text", find="38 geographically-disparate private, 18 DoF, one BFRI and two educational institution hatcheries")
R(pk, "distribution_channel", "61 hatcheries adopted broodstock, 31 producing seed; >200,000 farmers reached (2024); spawn sold 246 kg (2022), 4,135 kg (2023), 6,938 kg (2024)", "61 hatcheries adopted broodstock, while currently 31 hatcheries are producing seed", "YH25", method="pdf_text", find="61 hatcheries adopted broodstock", notes="CONFLICT: 2023 spawn sales 2826 kg in FIL report (to Aug 2023) vs 4,135 kg in 2025 presentation (full year?)")
R(pk, "status", "Widely adopted; current WorldFish rohu release in Bangladesh until G5 (2026)", "WorldFish’s genetically improved G3 rohu exhibits rapid growth under farm conditions and is widely adopted in Bangladesh", "WFDISS", "", "Rohu Carp entry", "html")
R(pk, "release_category", "R3_cgiar_release", "", "FRONT", "", "", "html")
R(pk, "cgiar_role", "1", "", "FRONT", "", "", "html")
R(pk, "cgiar_center", "WorldFish", "", "FRONT", "", "", "html")
R(pk, "source_url", "https://doi.org/10.7910/DVN/SVNV6B", "Dataset on the dissemination of genetically improved carp in Bangladesh", "DV_SV", "", "title; timePeriodCovered 2022-05-01 to 2022-12-31", "api_json", notes="CC BY 4.0; data file behind guestbook, not downloaded")

# ======================= WorldFish G5 rohu (pending) =======================
pk = "FISH_WF_G5_ROHU"
R(pk, "strain_name", "WorldFish G5 rohu", "G5 rohu is to be disseminated to hatcheries in 2026", "WFDISS", "", "Rohu Carp entry", "html")
R(pk, "species_scientific", "Labeo rohita", "", "WFDISS", "", "", "html")
R(pk, "generation", "G5", "Generation available: G5", "WFDISS", "", "Rohu Carp entry", "html", "two_source", notes="Hamilton & Yeasin 2025 slide 9: rohu G4 and G5 produced by 2024/2025")
R(pk, "release_date", "2026", "G5 rohu is to be disseminated to hatcheries in 2026", "WFDISS", "", "Rohu Carp entry", "html", "two_source", "medium", notes="planned date; two_source with Hamilton & Yeasin 2025 abstract ('planned release of G5 rohu in 2026'). Not confirmed as done")
R(pk, "key_traits", "expected >50% faster growth than unimproved strains (on-farm trials 2025)", "G5 rohu, currently under on-farm trials, is expected to grow over 50% faster than unimproved strains", "WFKHUL", "", "quoted phrase", "html", conf="medium")
R(pk, "status", "Planned / in on-farm trial (2025)", "G5 rohu ... is currently under field trials", "WFKHUL", "", "quoted phrase", "html")
R(pk, "approval_or_release_mechanism", "R3_cgiar_release (pending): WorldFish dissemination planned 2026", "", "WFDISS", "", "", "html", conf="medium")
R(pk, "cgiar_role", "1", "", "WFDISS", "", "", "html")
R(pk, "cgiar_center", "WorldFish", "", "WFDISS", "", "", "html")

# ======================= WorldFish G4 silver carp (pending) =======================
pk = "FISH_WF_G4_SILVER_CARP"
R(pk, "strain_name", "WorldFish improved silver carp G4", "Silver Carp ( Hypophthalmichthys molitrix ) WorldFish’s improved silver carp strain shows favourable growth relative to other available strains in Bangladesh", "WFDISS", "", "Silver Carp entry", "html")
R(pk, "species_scientific", "Hypophthalmichthys molitrix", "", "WFDISS", "", "", "html")
R(pk, "generation", "G4", "Generation available: G4", "WFDISS", "", "Silver Carp entry", "html", notes="Hamilton & Yeasin 2025 slide 2: 'three [generations] for silver carp'")
R(pk, "pedigree", "Founders collected as adults from 17 Bangladeshi hatcheries in 2014; base population 2017; G1 2019", "silver carp founders were collected, as adults, from 17 Bangladeshi hatcheries in 2014", "FILTR", method="pdf_text", find="silver carp founders were collected, as adults, from 17 Bangladeshi hatcheries in 2014")
R(pk, "release_date", "", "G4 silver carp and G3 catla expected in the coming years", "WFKHUL", "", "quoted phrase", "html", conf="medium", notes="no year given on WorldFish page; Phase 0 note '2026-27' not found in sources saved here")
R(pk, "status", "Pending (not yet disseminated as of Sep 2025)", "Work on other species continues, with G4 silver carp and G3 catla expected in the coming years", "WFKHUL", "", "quoted phrase", "html")
R(pk, "approval_or_release_mechanism", "none yet (R3 pending)", "", "WFKHUL", "", "", "html")
R(pk, "cgiar_role", "1", "", "WFDISS", "", "", "html")
R(pk, "cgiar_center", "WorldFish", "", "WFDISS", "", "", "html")

# ======================= WorldFish G3 catla (pending) =======================
pk = "FISH_WF_G3_CATLA"
R(pk, "strain_name", "WorldFish catla G3", "G3 calta is to be disseminated to hatcheries from 2027", "WFDISS", "", "Catla Carp entry", "html", notes="'calta' sic on WorldFish page")
R(pk, "species_scientific", "Labeo catla (syn. Catla catla)", "Catla Carp ( Labeo catla syn. Catla catla )", "WFDISS", "", "Catla entry", "html")
R(pk, "generation", "G3 (from 2027)", "Generation available: G3 (from 2027)", "WFDISS", "", "Catla entry", "html")
R(pk, "release_date", "2027", "G3 calta is to be disseminated to hatcheries from 2027", "WFDISS", "", "Catla entry", "html", conf="medium", notes="planned date")
R(pk, "pedigree", "Founders collected as spawn from rivers in 2012; base population 2016-2017; G1 2021", "Base populations were then generated by mating between founders (2014 for rohu, 2016-2017 for catla and 2017 for silver carp)", "FILTR", method="pdf_text", find="2016-2017 for catla")
R(pk, "status", "Pending", "", "WFDISS", "", "", "html")
R(pk, "approval_or_release_mechanism", "none yet (R3 pending, 2027)", "", "WFDISS", "", "", "html")
R(pk, "cgiar_role", "1", "", "WFDISS", "", "", "html")
R(pk, "cgiar_center", "WorldFish", "", "WFDISS", "", "", "html")

# ---------------- write ----------------
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(HDR); w.writerows(rows)
print(len(rows), "rows ->", OUT)
from collections import Counter
for k, v in Counter(r[0] for r in rows).items():
    print(f"  {k}: {v}")

# ---------------- excluded ----------------
EXC = ROOT / "04_working/fish_excluded.csv"
exc = [
 ("Vannamei shrimp (Litopenaeus/Penaeus vannamei)", "species introduction", "MoFL approval letter 29 Mar 2023 for a DoF guideline; species not strain", "FS025", "02_raw/dof/dof_vannamei_guideline_2023.pdf"),
 ("Thai pangas (Pangasianodon hypophthalmus)", "species introduction / breeding technique", "BFRI first bred Thai pangas 1993; TVC rows 5-6 are breeding and culture techniques", "FS014", "02_raw/fao/fao_annexJ_quality_fish_seed_bangladesh_bfri.pdf"),
 ("Thai and Vietnamese pangas/tra pure lines (2010, 2011)", "germplasm introduction", "Wild Mekong stocks collected Oct 2010 / Oct 2011; stock improvement 'in progress', no named release", "FS014", "02_raw/fao/fao_annexJ_quality_fish_seed_bangladesh_bfri.pdf"),
 ("Exotic carp pure lines at BFRI (grass, black, silver, bighead, crucian carp; 2010-2011)", "germplasm introduction", "Pure-line introductions from China for seed production and research", "FS014", "02_raw/fao/fao_annexJ_quality_fish_seed_bangladesh_bfri.pdf"),
 ("Rajputi / Thai sarpunti species introduction (1977)", "species introduction", "Species brought from Thailand in 1977 and named রাজপুঁটি by BFRI; the later BFRI improved rajputi strain is kept in the main evidence (FISH_BFRI_RAJPUTI)", "P2F-S18", "02_raw/bfri/bfri_leaflet_rajputi_pond_culture.pdf"),
 ("Super tilapia monosex fry (TVC row 8) / BFRI GIFT monosex", "monosex technology", "Hormonal sex reversal technique applied to BFRI GIFT; not a separate strain", "FS008", "02_raw/bfri/bfri_technologies_list_attachment_2026.pdf"),
 ("Chitralada Nile tilapia (1974, UNICEF; re-introduced later)", "species/strain introduction (non-CGIAR, public)", "Introduced from Thailand via UNICEF; no improvement/release by a public breeder documented", "FS015", "02_raw/worldfish/hussain_c2014_tilapia_farming_bangladesh.pdf"),
 ("Mozambique tilapia O. mossambicus (1954)", "species introduction", "First tilapia introduced from Thailand 1954; became a pest", "FS015", "02_raw/worldfish/hussain_c2014_tilapia_farming_bangladesh.pdf"),
 ("Thai red tilapia (1988) / red mutant hybrid", "strain introduction", "1988 Thai red stocks 'not true breeding'; BFRI red tilapia strain built on the 2005 WorldFish Malaysian red batch instead (FISH_BFRI_RED_TILAPIA)", "FS015", "02_raw/worldfish/hussain_c2014_tilapia_farming_bangladesh.pdf"),
 ("Genomar, GIFO, FaST, Swansea YY-male/GMT (Fishgen) tilapia", "private commercial imports", "Introduced by private hatcheries; no public release of a derived line found", "FS015", "02_raw/worldfish/hussain_c2014_tilapia_farming_bangladesh.pdf"),
 ("YY GIFT super-males (marker-assisted selection, BFRI, from Mar 2021)", "not released (in development)", "AR 2020-21 and AR 2023-24 report pseudo-female/YY production work; no release found", "FS013", "02_raw/bfri/bfri_annual_report_2020-21.pdf"),
 ("BFRI catla stock improvement (Halda, Jamuna wild stocks)", "not released (in development)", "AR 2020-21 reports grow-out of wild-origin catla for stock improvement; no named strain or release", "FS013", "02_raw/bfri/bfri_annual_report_2020-21.pdf"),
 ("BFRI kalibaus (Labeo calbasu) pure-line breeding", "not released (germplasm/brood management)", "AR 2022-23 'Improved Germplasm Production of Carps, White Pangas and Pure-line Breeding of Kalibaus'", "P2F-S14", "02_raw/bfri/bfri_annual_report_2022-23.pdf"),
 ("WorldFish G4 rohu (intermediate generation)", "not disseminated", "Produced in the breeding nucleus (Hamilton & Yeasin 2025 slide 9) but WorldFish went from G3 to planned G5 dissemination", "FS018", "02_raw/worldfish/yeasin_hamilton_2025_cgidp_progress_hdl6598.pdf"),
 ("Native-species breeding techniques (pabda, gulsha, shing, magur, koi, tengra, mahashol, chital, kuchia, etc.)", "breeding/culture technique", "TVC rows 4, 10-14, 23, 32, 35, 38, 43-50, 52-55 are induced-breeding or culture techniques, not strains", "FS008", "02_raw/bfri/bfri_technologies_list_attachment_2026.pdf"),
 ("Golda prawn early brood / hatchery model", "technique", "TVC row 15 (mini hatchery model) and coastal rows are techniques", "FS008", "02_raw/bfri/bfri_technologies_list_attachment_2026.pdf"),
 ("African magur (Clarias gariepinus)", "species (banned)", "Species banned by gazette per press reports; gazette not retrieved in this pilot; not a strain", "", ""),
 ("SPF black tiger shrimp PL", "health-status class", "Specific-pathogen-free status, not a strain; no primary document read", "", ""),
 ("Mola (Amblypharyngodon mola) carp-mola polyculture", "species/technology promotion", "WorldFish nutrition-sensitive technology, not a strain", "", ""),
]
with open(EXC, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["item", "exclusion_reason", "detail", "source_id", "local_file"]); w.writerows(exc)
print(len(exc), "excluded ->", EXC)
