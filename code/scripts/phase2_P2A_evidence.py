"""P2A: write 04_working/evidence_P2A.csv (long format, one row per variety x field x source).
All values were read by P2A from the files named below; crops of OCR'd cells are in 04_working/crops/P2A/.
Methods: bijoy2unicode = SutonnyMJ text layer converted (digits typed, not OCR); ocr = Tesseract, then
validated (visual_check = crop opened and read; key_check = NSB meeting/date equals 04_working/nsb_meeting_key.csv)."""
import csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]

S = {  # source_id: (title, authority_rank, local_file)
    "SCA_COMP": ("SCA, 'বাংলাদেশের নোটিফাইড ফসলের অনুমোদিত জাত' (approved varieties of notified crops; imprint 2014, posted 2016)", "2_official_list", "02_raw/sca/approved_varieties_notified_crops_bangladesh_2016.pdf"),
    "MOA_HYB26": ("MoA Seed Wing, 'জাতীয় বীজ বোর্ড (NSB) কর্তৃক ১৯৯৮-০৫/০২/২০২৬ পর্যন্ত অনুমোদিত হাইব্রিড ধানের জাত'", "2_official_list", "02_raw/moa/hybrid_rice_varieties_list_2026-02-05.pdf"),
    "MOA_HYB18": ("MoA Seed Wing, List of Hybrid Rice Variety 07.08.2018 (Wayback)", "2_official_list", "02_raw/moa_wayback/hybrid_rice_list_2018-08-07.pdf"),
    "NSB_R1": ("NSB activities report no.1 (minutes summaries, NSB 1st-18th meetings, 1974-1984)", "1_primary_legal", "02_raw/sca/nsb_minutes_001-018.pdf"),
    "NSB_29_42": ("NSB minutes 29th-42nd meetings (1993-1999), activities report no.3", "1_primary_legal", "02_raw/sca/nsb_minutes_029-042.pdf"),
    "NSB_43_57": ("NSB minutes 43rd-57th meetings (2000-2005), activities report no.4 (June 2005)", "1_primary_legal", "02_raw/sca/nsb_minutes_043-057.pdf"),
    "NSB_R5": ("NSB minutes 58th-75th meetings (2005-2011), activities report no.5 (Nov 2011)", "1_primary_legal", "02_raw/sca/nsb_minutes_058-075.pdf"),
    "NSB_76_82": ("NSB minutes 76th-82nd meetings (2012-2014)", "1_primary_legal", "02_raw/sca/nsb_minutes_076-082.pdf"),
    "NSB_115": ("NSB 115th meeting minutes (meeting 05-02-2026)", "1_primary_legal", "02_raw/sca/nsb_minutes_115.pdf"),
    "TC_001": ("NSB Technical Committee, proceedings of the 1st meeting (21 April 1980), Wayback copy", "1_primary_legal", "02_raw/sca_wayback/tc_minutes_001_1980-04-21.pdf"),
    "TC_025": ("NSB Technical Committee, 25th meeting minutes (12-6-94 and 2-7-94), Wayback copy", "1_primary_legal", "02_raw/sca_wayback/tc_minutes_025_1994-06-12.pdf"),
    "SCA_AV1819": ("SCA, 'ফসলের অনুমোদিত জাতসমূহ, ২০১৮-১৯'", "2_official_list", "02_raw/sca/approved_crop_varieties_2018-19.pdf"),
    "SCA_AV2526": ("SCA, 'ফসলের অনুমোদিত জাতসমূহ, ২০২৫-২৬'", "2_official_list", "02_raw/sca/approved_crop_varieties_2025-26.pdf"),
    "GAZ_20070416": ("Bangladesh Gazette Extraordinary 16 Apr 2007, MoA Seed Wing notification of 18 Mar 2007 (NSB 62)", "1_primary_legal", "02_raw/moa/release_gazette_nsb62_2007.pdf"),
    "GAZ_20140318": ("Bangladesh Gazette Extraordinary 18 Mar 2014, MoA Seed Wing notification of 20 Nov 2013", "1_primary_legal", "02_raw/bgpress/release_notification_2014-03-18.pdf"),
    "GAZ_20150122": ("Bangladesh Gazette Extraordinary 22 Jan 2015, MoA Seed Wing notification of 24 Dec 2014 (NSB 70-83)", "1_primary_legal", "02_raw/bgpress/moa_extra_22-Jan-2015_12441_44845.pdf"),
    "GAZ_20191211": ("Bangladesh Gazette Extraordinary 11 Dec 2019, MoA Seed Wing notification of 05 Dec 2019 (NSB 95-101)", "1_primary_legal", "02_raw/bgpress/moa_extra_11-Dec-2019_34659_83539.pdf"),
}
rows = []


def E(pk, field, value, raw, sid, page, loc, method, val, conf, notes=""):
    t, rank, f = S[sid]
    rows.append(dict(pilot_key=pk, field=field, value=value, value_raw=raw, source_id=sid, source_title=t, authority_rank=rank,
                     local_file=f, page=page, locator=loc, method=method, validation=val, confidence=conf, notes=notes))


V, K, U, T = "visual_check", "key_check", "unvalidated", "two_source"
BJ = "bijoy2unicode"

# ---------------- IR8 ----------------
c = "compendium BRRI rice table row 01; crop cmp_IR8.png"
E("IR8", "official_name_bn", "আইআর ৮", "আইআর ৮", "SCA_COMP", 11, c, "ocr", V, "high")
E("IR8", "official_name_en", "IR8", "", "SCA_COMP", 11, c, "visual_check", V, "medium", "English form inferred from the Bangla transliteration 'আইআর ৮'; the compendium row has no English text")
E("IR8", "release_category", "pre_NSB_recommended", "ছাড়করণের সময় ১৯৬৬", "SCA_COMP", 11, c, "ocr", V, "high", "release year 1966 precedes the NSB (set up 1973); listed in the official compendium of approved varieties")
E("IR8", "approval_date", "1966", "১৯৬৬", "SCA_COMP", 11, c + "; column 'ছাড়করণের সময়'", "ocr", V, "high", "year only; no NSB meeting (pre-NSB)")
E("IR8", "approving_body", "none (pre-NSB; listed by SCA as approved variety)", "", "SCA_COMP", 11, c, "ocr", V, "medium")
E("IR8", "season", "Aus; Boro", "আউশ এবং বোরো", "SCA_COMP", 11, c, "ocr", V, "high")
E("IR8", "region_scope", "nationwide", "সমগ্র বাংলাদেশ", "SCA_COMP", 11, c, "ocr", V, "high")
E("IR8", "key_traits", "first HYV ('ইরি ধান', miracle variety) that started the green revolution; short stature 90-100 cm", "খাটো আকৃতির সর্বপ্রথম উফশী জাত। 'ইরি ধান' (মিরাকল ভ্যারাইটি) হিসেবে সবুজ বিপ্লব (গ্রীন রিভোল্যুশন) শুরু", "SCA_COMP", 11, c + "; column 'বিশেষ বৈশিষ্ট্য'", "ocr", V, "medium", "special-trait text partly beyond crop; read from OCR + crop")
E("IR8", "developer", "listed under BRRI table (institute heading 'বাংলাদেশ ধান গবেষণা ইনস্টিটিউট')", "প্রতিষ্ঠান ঃ বাংলাদেশ ধান গবেষণা ইনস্টিটিউট (বিআরআরআই)", "SCA_COMP", 11, "page heading", "ocr", U, "low", "the compendium files IRRI introductions under BRRI; it does not state IRRI as breeder")
E("IR8", "status", "seed multiplication of IR8 suspended by the NSB 7th meeting (16-08-1976)", "সভায় আইআর-৮ এবং আইআর-২০ বীজ বর্ধন এখন থেকে স্হগিত রাখার সিদ্ধান্ত নেওয়া হয়", "NSB_R1", 17, "item 07.(খ) of 7th meeting summary; crops n007_open.png (p16), n007_ir8.png", "ocr", V, "medium", "not a formal denotification; a seed-programme decision")
E("IR8", "cgiar_evidence", "name/designation IR8 (IRRI line); compendium trait text 'ইরি ধান'", "আইআর ৮ ... 'ইরি ধান'", "SCA_COMP", 11, c, "ocr", V, "medium")

# ---------------- BR1 ----------------
c = "compendium BRRI rice table row 06; crop cmp_BR1.png"
E("BR1", "official_name_bn", "বিআর-১ (চান্দিনা)", "বিআর-১ (চান্দিনা)", "SCA_COMP", 11, c, "ocr", V, "high")
E("BR1", "popular_name", "Chandina", "চান্দিনা", "SCA_COMP", 11, c, "ocr", V, "high")
E("BR1", "release_category", "pre_NSB_recommended", "১৯৭০", "SCA_COMP", 11, c, "ocr", V, "high", "release year 1970 precedes NSB (1973); no NSB/gazette record found")
E("BR1", "approval_date", "1970", "১৯৭০", "SCA_COMP", 11, c + "; column 'ছাড়করণের সময়'", "ocr", V, "high", "year only")
E("BR1", "developer", "BRRI", "প্রতিষ্ঠান ঃ বাংলাদেশ ধান গবেষণা ইনস্টিটিউট (বিআরআরআই)", "SCA_COMP", 11, "page heading", "ocr", V, "high")
E("BR1", "season", "Aus; Boro", "আউশ এবং বোরো", "SCA_COMP", 11, c, "ocr", V, "high")
E("BR1", "region_scope", "nationwide", "সমগ্র বাংলাদেশ", "SCA_COMP", 11, c, "ocr", V, "high")
E("BR1", "key_traits", "protein 9%; short erect leaves", "প্রোটিনের পরিমাণ শতকরা ৯ ভাগ; পাতা ছোট ও খাড়া", "SCA_COMP", 11, c, "ocr", V, "high")

# ---------------- BR11 ----------------
c = "compendium BRRI rice table row 16; crop cmp_BR11.png, cmp_BR11_full.png"
E("BR11", "official_name_bn", "বিআর-১১ (মুক্তা)", "বিআর-১১ (মুক্তা)", "SCA_COMP", 14, c, "ocr", V, "high")
E("BR11", "popular_name", "Mukta", "মুক্তা", "SCA_COMP", 14, c, "ocr", V, "high")
E("BR11", "official_name_bn", "মুক্তা (বি, আর--১১)", "মুক্তা (বি, আর--১১)", "NSB_R1", 28, "item 4.15 (14th meeting) list (ঘ) 'ধান জাত'; crop n014_br11b.png", "ocr", V, "high")
E("BR11", "release_category", "NSB_release", "কারিগরী কমিটির সুপারিশ ... অন্যমোদন লাভ করে", "NSB_R1", 28, "item 15.2 of 14th meeting; crops n014_open.png, n014_br11b.png", "ocr", V, "high", "pre-2005 regime (Seeds Ordinance 1977); NSB approval on TC recommendation; no gazette SRO for rice found in screened SROs")
E("BR11", "approving_body", "NSB (on recommendation of NSB Technical Committee 1st meeting)", "", "NSB_R1", 28, "item 15.2", "ocr", V, "high")
E("BR11", "approval_date", "1981-03-30", "৩০-৩-৮১", "NSB_R1", 28, "item 4.15 opening: '৩০-৩-৮১ তারিখে অনুষ্ঠিত জাতীয় বীজ বোর্ডের ১৪তম সভা'; crop n014_open.png", "ocr", V, "high", "matches key row 14 (visual); compendium year 1981 agrees")
E("BR11", "approval_reference", "NSB 14th meeting", "জাতীয় বীজ বোর্ডের ১৪তম সভা", "NSB_R1", 28, "item 4.15", "ocr", V, "high")
E("BR11", "approval_date", "1981", "১৯৮১", "SCA_COMP", 14, c + "; column 'ছাড়করণের সময়'", "ocr", V, "high", "year only; agrees with NSB 14th meeting 1981-03-30")
E("BR11", "approval_reference", "NSB TC 1st meeting recommendation (21 Apr 1980)", "Agendum- V : Release of new variety of paddy BR-10 (Progoti) and BR-11 (Mukta) by Bangladesh Rice Research Institute", "TC_001", 2, "Agendum V; crops tc001_date.png (p1), tc001_br11.png", "ocr", V, "high", "TC 'recommended the above two varieties for release'; TC date is not the approval date")
E("BR11", "official_name_en", "BR-11 (Mukta)", "BR-11 (Mukta)", "TC_001", 2, "Agendum V", "ocr", V, "high")
E("BR11", "developer", "BRRI", "Bangladesh Rice Research Institute", "TC_001", 2, "Agendum V", "ocr", V, "high")
E("BR11", "season", "Aman", "আমন", "SCA_COMP", 14, c, "ocr", V, "high")
E("BR11", "region_scope", "nationwide", "সমগ্র বাংলাদেশ", "SCA_COMP", 14, c, "ocr", V, "high")
E("BR11", "key_traits", "weakly photoperiod-sensitive; 2nd place in a 1976 international trial; 14.3 t/ha in Mexico in the same trial", "স্বল্প আলোক সংবেদনশীল। ১৯৭৬ সালে আন্তর্জাতিক পরীক্ষায় ২য় স্থান অধিকার করে। একই পরীক্ষায় মেক্সিকোতে হেক্টর প্রতি ১৪.৩ টন ফলন দিয়ে", "SCA_COMP", 14, "column 'বিশেষ বৈশিষ্ট্য'; crop cmp_BR11_full.png", "ocr", V, "high")
E("BR11", "key_traits", "late transplanting variety for flood-affected land, similar to BR-10 but matures one week earlier", "The character of the variety, BR-11 is stated to be similar to that of BR-10 but matures one week earlier than BR-10", "TC_001", 2, "Agendum V", "ocr", V, "high")

# ---------------- BRRI dhan28 / dhan29 ----------------
for pk, num, row, pg, region_raw, region, trait_raw, trait, crop in (
        ("BRRI_DHAN28", "২৮", 32, 16, "সমগ্র বাংলাদেশ (কৃষি পরিবেশ অঞ্চল ২৪ ব্যতীত)", "nationwide except AEZ 24", "ডিগ পাতা হেলে যায় এবং শিষ উপরে থাকে ফলে সহজেই দৃষ্টি আকর্ষণ করে; চাল মাঝারী চিকন ও সাদা", "flag leaf bends, panicle stays above; medium-slender white grain", "cmp_DHAN28.png"),
        ("BRRI_DHAN29", "২৯", 33, 17, "সমগ্র বাংলাদেশ (কৃষি পরিবেশ অঞ্চল ১, ১১, ১৪, ২৪, ২৯ ব্যতীত)", "nationwide except AEZ 1, 11, 14, 24, 29", "সার গ্রহণ করার ক্ষমতা বেশী, কান্ড মজবুত এবং অত্যন্ত জনপ্রিয় ফলনশীল জাত", "high fertiliser response, strong stem, very popular high-yielding variety", "cmp_DHAN29.png, cmp_DHAN29_reg.png")):
    c = f"compendium BRRI table row {row}; crop {crop}"
    E(pk, "official_name_bn", f"ব্রি ধান-{num}", f"ব্রি ধান-{num}", "SCA_COMP", pg, c, "ocr", V, "high")
    E(pk, "official_name_bn", f"ব্রি ধান-{num}", f"ব্রি ধান-{num}", "NSB_29_42", 18, "32nd meeting, item 3 list of 19 approved varieties; crop n032_rice.png", "ocr", V, "high")
    E(pk, "release_category", "NSB_release", "নিম্নবর্ণিত বিভিন্ন ফসলের মোট ১৯টি জাতের অনুমোদন দেয়া হলো", "NSB_29_42", 18, "32nd meeting item 3 decision", "ocr", V, "high", "pre-2005 regime; NSB approval on TC 25th meeting recommendation")
    E(pk, "approving_body", "NSB (on recommendation of NSB Technical Committee 25th meeting)", "", "NSB_29_42", 18, "item 3", "ocr", V, "high")
    E(pk, "approval_date", "1994-07-25", "২৫/৭/৯৪", "NSB_29_42", 18, "32nd meeting opening '২৫/৭/৯৪ ইং তারিখ ... জাতীয় বীজ বোর্ডের ৩২তম সভা অনুষ্ঠিত হয়'; crop n032_open.png", "ocr", V, "high", "compendium year 1994 agrees")
    E(pk, "approval_reference", "NSB 32nd meeting", "জাতীয় বীজ বোর্ডের ৩২তম সভায় অনুমোদন প্রাপ্ত জাতের নাম", "NSB_29_42", 18, "item 3 table heading", "ocr", V, "high")
    E(pk, "approval_reference", "NSB TC 25th meeting (12-6-94 and 2-7-94) recommendation", "ব্রি ধান-২৮, ব্রি ধান-২৯, ব্রি ধান-৩০ এবং ব্রি ধান-৩১ নামে জাত চারটি অনুমোদনের জন্য জাতীয় বীজ বোর্ডকে সুপারিশ করা হলো", "TC_025", 1, "item 3.1 decision; crops tc025_head.png, tc025_dhan2829.png", "ocr", V, "high")
    E(pk, "approval_date", "1994", "১৯৯৪", "SCA_COMP", pg, c + "; column 'ছাড়করণের সময়'", "ocr", V, "high", "year only; agrees with NSB 32nd meeting")
    E(pk, "developer", "BRRI", "বাংলাদেশ ধান গবেষণা ইনস্টিটিউট কর্তৃক উদ্ভাবিত", "TC_025", 1, "item 3.1", "ocr", V, "high")
    E(pk, "season", "Boro", "বোরো", "SCA_COMP", pg, c, "ocr", V, "high")
    E(pk, "region_scope", region, region_raw, "SCA_COMP", pg, c + "; column 'সুপারিশকৃত অঞ্চল'", "ocr", V, "high")
    E(pk, "key_traits", trait, trait_raw, "SCA_COMP", pg, c, "ocr", V, "high")

# ---------------- BRRI dhan47 ----------------
E("BRRI_DHAN47", "official_name_bn", "ব্রি ধান-৪৭", "ব্রি ধান-৪৭", "GAZ_20070416", 1, "table row (২); crop gaz2007_nsb62_bottom.png", "ocr", V, "high")
E("BRRI_DHAN47", "breeding_line", "IR63307-4B-4-3", "আইআর ৬৩৩০৭-৪বি-৪-৩", "NSB_R5", 40, "62nd meeting, agenda 3 (খ) and decision (ক); crop r5_dhan47.png", BJ, V, "high", "IRRI designation; minutes say 'ব্রি কর্তৃক উদ্ভাবিত' (developed by BRRI). Candidate for IRRI_DIRECT")
E("BRRI_DHAN47", "release_category", "NSB_release", "সারিটি ব্রি ধান-৪৭ হিসেবে ছাড়করণ করা হলো", "NSB_R5", 40, "62nd meeting decision (ক)", BJ, V, "high")
E("BRRI_DHAN47", "approving_body", "NSB (on recommendation of TC 54th meeting)", "জাতীয় বীজ বোর্ডের কারিগরী কমিটি ৫৪তম সভায় ... সুপারিশ করেছে", "NSB_R5", 40, "agenda 3", BJ, V, "high")
E("BRRI_DHAN47", "approval_date", "2007-01-18", "১৮.০১.০৭", "NSB_R5", 38, "62nd minutes opening 'গত ১৮.০১.০৭ খ্রিঃ তারিখ ... ৬২তম সভা'", BJ, K, "high", "key: 62 = 2007-01-18 (minutes + 64th minutes confirmation)")
E("BRRI_DHAN47", "approval_reference", "NSB 62nd meeting", "জাতীয় বীজ বোর্ডের ৬২তম সভায় অনুমোদনের প্রেক্ষিতে", "GAZ_20070416", 1, "notification text; crop gaz2007_nsb62_top.png", "ocr", V, "high", "two_source with NSB report no.5 (62nd minutes)")
E("BRRI_DHAN47", "gazette_date", "2007-04-16", "রবিবার, এপ্রিল ১৬, ২০০৭", "GAZ_20070416", 1, "masthead; crop gaz2007_nsb62_top.png", "ocr", V, "high", "notification itself dated 18 Mar 2007 ('তারিখ, ১৮ মার্চ ২০০৭')")
E("BRRI_DHAN47", "gazette_reference", "MoA Seed Wing notification নং কৃষি/বীজ উইং/বীজ প্র-৭(২)/৯৩/৪৮ dated 2007-03-18; Gazette Extraordinary 16 Apr 2007, p.5491", "নং কৃষি/বীজ উইং/বীজ প্র-৭(২)/৯৩/৪৮", "GAZ_20070416", 1, "memo line; crop gaz2007_nsb62_top.png", "ocr", V, "high", "gazette page number 5491 read by OCR only ('(৫৪৯১)'), not visually checked")
E("BRRI_DHAN47", "season", "Boro", "বোরো মৌসুমে সারা দেশে চাষাবাদযোগ্য", "GAZ_20070416", 1, "remark column", "ocr", V, "high")
E("BRRI_DHAN47", "region_scope", "nationwide", "বোরো মৌসুমে সারা দেশে চাষাবাদযোগ্য", "GAZ_20070416", 1, "remark column", "ocr", V, "high")
E("BRRI_DHAN47", "region_scope", "saline areas", "লবনাক্ত এলাকা", "SCA_COMP", 19, "compendium row 51; crop cmp_DHAN47.png", "ocr", V, "high", "conflicts with gazette 'সারা দেশে'")
E("BRRI_DHAN47", "approval_date", "2007", "২০০৭", "SCA_COMP", 19, "row 51 'ছাড়করণের সময়'", "ocr", V, "high", "year only")
E("BRRI_DHAN47", "key_traits", "salinity tolerant; suited to saline areas of Satkhira; medium-bold grain", "লবণাক্ততা সহিষ্ণু। সাতক্ষীরার লবণাক্ত এলাকার জন্য উপযোগী।", "SCA_COMP", 19, "row 51; crop cmp_DHAN47.png", "ocr", V, "high")
E("BRRI_DHAN47", "developer", "BRRI", "ব্রি কর্তৃক উদ্ভাবিত", "NSB_R5", 40, "agenda 3 (খ)", BJ, V, "high")
E("BRRI_DHAN47", "cgiar_evidence", "breeding line is an IRRI designation (IR63307-4B-4-3) in NSB 62nd minutes", "আইআর ৬৩৩০৭-৪বি-৪-৩ সারিটি ব্রি ধান-৪৭ হিসেবে ছাড়করণ", "NSB_R5", 40, "62nd meeting decision", BJ, V, "high")

# ---------------- BRRI dhan52 ----------------
E("BRRI_DHAN52", "official_name_bn", "ব্রি ধান-৫২", "ব্রি ধান -৫২", "NSB_R5", 86, "72nd meeting agenda 3 decision; crop r5_dhan52.png", BJ, V, "high")
E("BRRI_DHAN52", "official_name_bn", "ব্রিধান-৫২", "ব্রিধান-৫১ এবং ব্রিধান-৫২", "GAZ_20150122", 1, "table row 'ধান ব্রিধান-৫১ এবং ব্রিধান-৫২ ব্রি ৭২তম সভা'", BJ, T, "high", "two_source: also GAZ_20140318 p.1")
E("BRRI_DHAN52", "breeding_line", "BR11-Sub1", "বিআর-১১ সাব-১ কৌলিক সারিটিকে ব্রি ধান -৫২ হিসেবে ছাড়করণ করা হলো", "NSB_R5", 86, "72nd meeting agenda 3 decision; crop r5_dhan52.png", BJ, V, "high", "line name written in Bangla in the minutes")
E("BRRI_DHAN52", "release_category", "NSB_release", "ছাড়করণ করা হলো", "NSB_R5", 86, "agenda 3 decision; crop r5_dhan52.png", BJ, V, "high")
E("BRRI_DHAN52", "approving_body", "NSB (on TC recommendation)", "কারিগরী কমিটি কতৃর্ক প্রস্তাবকৃত", "NSB_R5", 85, "agenda 3 discussion", BJ, V, "high")
E("BRRI_DHAN52", "approval_date", "2010-04-06", "০৬/০৪/২০১০", "NSB_R5", 85, "72nd minutes opening 'গত ০৬/০৪/২০১০ খ্রিঃ তারিখ ... ৭২তম সভা'", BJ, K, "high", "key: 72 = 2010-04-06 two_source (MoA hybrid list)")
E("BRRI_DHAN52", "approval_reference", "NSB 72nd meeting", "৭২তম সভা", "NSB_R5", 85, "72nd minutes", BJ, K, "high")
E("BRRI_DHAN52", "approval_date", "2010", "২০১০", "SCA_COMP", 20, "row 56; crop cmp_DHAN52.png", "ocr", V, "high", "year only")
E("BRRI_DHAN52", "gazette_date", "2014-03-18", "মঙ্গলবার, মাচর্ ১৮, ২০১৮ (masthead) / বাংলাদেশ গেজেট, অতিরিক্ত, মাচর্ ১৮, ২০১৪ (p.2 header)", "GAZ_20140318", 1, "masthead", BJ, U, "medium", "the p.1 masthead text layer reads 2018 while p.2 running header and the bgpress index say 18 Mar 2014; notification dated 20 Nov 2013; not visually checked")
E("BRRI_DHAN52", "gazette_reference", "MoA Seed Wing notification নং ১২.০৯৭.০২২.০২.০০.০৩২.২০০৮-১২৬ dated 2013-11-20; Gazette Extraordinary 18 Mar 2014, p.10577", "নং ১২.০৯৭.০২২.০২.০০.০৩২.২০০৮-১২৬", "GAZ_20140318", 1, "memo line; '(১০৫৭৭)'", BJ, U, "high", "text layer")
E("BRRI_DHAN52", "gazette_date", "2015-01-22", "বৃহস্পতিবার, জানুয়ারি ২২, ২০১৫", "GAZ_20150122", 1, "masthead", BJ, U, "high", "second gazetting of the same varieties (NSB 70-83 batch); notification dated 24 Dec 2014")
E("BRRI_DHAN52", "gazette_reference", "MoA Seed Wing notification নং ১২.০৯৭.০২২.০২.০০.০৩২.২০০৮-৪৮৬ dated 2014-12-24; Gazette Extraordinary 22 Jan 2015, p.493", "নং ১২.০৯৭.০২২.০২.০০.০৩২.২০০৮-৪৮৬", "GAZ_20150122", 1, "memo line; '(৪৯৩)'", BJ, U, "high")
E("BRRI_DHAN52", "season", "Transplanted Aman", "রোপা আমন মৌসুমে সারা দেশে চাষাবাদযোগ্য", "GAZ_20150122", 1, "remark column", BJ, T, "high", "same remark in GAZ_20140318")
E("BRRI_DHAN52", "region_scope", "nationwide (flash-flood-prone areas per minutes)", "রোপা আমন মৌসুমে সারা দেশে চাষাবাদযোগ্য", "GAZ_20150122", 1, "remark column", BJ, T, "high")
E("BRRI_DHAN52", "ecosystem", "flash-flood (submergence) prone areas", "আকস্মিক বন্যাপ্রবণ (Flash flood submergence) এলাকায় চাষাবাদের নিমিত্তে", "NSB_R5", 86, "agenda 3 decision; crop r5_dhan52.png", BJ, V, "high", "Latin words garbled in text layer; read from the page")
E("BRRI_DHAN52", "key_traits", "submergence tolerant; weakly photoperiod-sensitive; 145 d (155 d after 14 d submergence)", "জলমগ্নতা সহিষ্ণু জাত; স্বল্প আলোক সংবেদনশীল", "SCA_COMP", 20, "row 56; crop cmp_DHAN52.png", "ocr", V, "high")
E("BRRI_DHAN52", "cgiar_evidence", "minutes describe the line as developed by BRRI in IRRI-BRRI collaboration", "ইরি-ব্রি সহযোগিতায় বাংলাদেশ ধান গবেষণা ইনস্টিটিউট কতৃর্ক উদ্ভাবিত", "NSB_R5", 85, "72nd meeting agenda 3 discussion", BJ, U, "high", "text layer; not cropped")
E("BRRI_DHAN52", "developer", "BRRI", "বাংলাদেশ ধান গবেষণা ইনস্টিটিউট কতৃর্ক উদ্ভাবিত", "NSB_R5", 86, "agenda 3 decision; crop r5_dhan52.png", BJ, V, "high")

# ---------------- BRRI dhan56 ----------------
E("BRRI_DHAN56", "official_name_bn", "ব্রি ধান-৫৬", "ব্রি ধান-৫৬", "NSB_R5", 101, "75th meeting item (৩) heading; crop r5_dhan56.png", BJ, V, "high")
E("BRRI_DHAN56", "breeding_line", "IR74371-70-1-1", "আইআর ৭৪৩৭১-৭০-১-১", "NSB_R5", 101, "75th meeting item (৩) heading and decision; crop r5_dhan56.png", BJ, V, "high", "IRRI designation. Candidate for IRRI_DIRECT")
E("BRRI_DHAN56", "pedigree", "IR 55419-4 / WAY RAREM, backcrossed twice (BC2F1), pedigree selection", "আন্তর্জাতিক ধান গবেষণা ইনস্টিটিউট, ফিলিপাইন এর IR 55419-4 এবং WAY RAREM নামক স্থানীয় খরাসহিষ্ণু জাতের সাথে দুইবার পশ্চাৎ সংকরায়ন (BC2F1)", "NSB_R5", 101, "75th meeting discussion; crop r5_dhan56.png", "visual_check", V, "high", "Latin words garbled in the bijoy conversion; read from the page image")
E("BRRI_DHAN56", "cgiar_evidence", "minutes state the line derives from IRRI Philippines line IR 55419-4", "আন্তর্জাতিক ধান গবেষণা ইনস্টিটিউট, ফিলিপাইন এর IR 55419-4", "NSB_R5", 101, "75th meeting discussion", "visual_check", V, "high")
E("BRRI_DHAN56", "release_category", "NSB_release", "সারা দেশে চাষাবাদের জন্য ছাড়করণ করা হলো", "NSB_R5", 101, "decision", BJ, T, "high", "two_source: gazette 22 Jan 2015 lists it as released at NSB 75")
E("BRRI_DHAN56", "approving_body", "NSB (on TC recommendation)", "জাতীয় বীজ বোর্ডের নিকট সুপারিশ করা হয়েছে", "NSB_R5", 101, "discussion", BJ, U, "high")
E("BRRI_DHAN56", "approval_date", "2011-09-15", "১৫-০৯-২০১১", "NSB_R5", 97, "75th minutes opening 'গত ১৫-০৯-২০১১ খ্রিঃ তারিখ ... ৭৫ তম সভা'", BJ, K, "high", "key: 75 = 2011-09-15 two_source (MoA hybrid list)")
E("BRRI_DHAN56", "approval_reference", "NSB 75th meeting", "৭৫তম সভা", "GAZ_20150122", 2, "table row 'ব্রিধান-৫৫, ব্রি ধান-৫৬ এবং ব্রিধান-৫৭ ব্রি ৭৫তম সভা'", BJ, T, "high", "two_source with 75th minutes")
E("BRRI_DHAN56", "approval_date", "2011", "২০১১", "SCA_COMP", 20, "row 60; crop cmp_DHAN56.png", "ocr", V, "high", "year only")
E("BRRI_DHAN56", "gazette_date", "2014-03-18", "মাচর্ ১৮, ২০১৪ (p.2 header)", "GAZ_20140318", 2, "page 10578", BJ, U, "medium", "masthead p.1 reads 2018 (see BRRI_DHAN52 note)")
E("BRRI_DHAN56", "gazette_reference", "notification নং ১২.০৯৭.০২২.০২.০০.০৩২.২০০৮-১২৬ (20 Nov 2013); Gazette Extraordinary 18 Mar 2014, p.10578", "(১০৫৭৮)", "GAZ_20140318", 2, "row 'ব্রিধান-৫৫, ব্রি ধান-৫৬ এবং ব্রিধান-৫৭ ব্রি ৭৫তম সভা'", BJ, U, "high")
E("BRRI_DHAN56", "gazette_date", "2015-01-22", "জানুয়ারি ২২, ২০১৫", "GAZ_20150122", 2, "page 494 header", BJ, U, "high")
E("BRRI_DHAN56", "gazette_reference", "notification নং ১২.০৯৭.০২২.০২.০০.০৩২.২০০৮-৪৮৬ (24 Dec 2014); Gazette Extraordinary 22 Jan 2015, p.494", "৪৯৪", "GAZ_20150122", 2, "row ব্রিধান-৫৫/৫৬/৫৭", BJ, U, "high")
E("BRRI_DHAN56", "season", "Aman", "ব্রিধান-৫৬ ও ব্রিধান-৫৭ আমন মৌসুমে সারা দেশে চাষাবাদযোগ্য", "GAZ_20150122", 2, "remark column", BJ, T, "high")
E("BRRI_DHAN56", "region_scope", "nationwide", "আমন মৌসুমে সারা দেশে চাষাবাদযোগ্য", "GAZ_20150122", 2, "remark column", BJ, T, "high")
E("BRRI_DHAN56", "key_traits", "drought tolerant (no yield loss with 10-12 rainless days at reproductive stage); 105-110 d; up to 3.5 t/ha under drought", "এ জাতটি খড়া সহনশীল। প্রজনন পর্যায়ে ১০-১২ দিন বৃষ্টি না হলেও ফলনের তেমন কোন ক্ষতি হয় না", "NSB_R5", 101, "discussion; crop r5_dhan56.png", "visual_check", V, "high")
E("BRRI_DHAN56", "developer", "BRRI", "বাংলাদেশ ধান গবেষণা ইনস্টিটিউট কতৃর্ক উদ্ভাবিত", "NSB_R5", 101, "item (৩) heading; crop r5_dhan56.png", BJ, V, "high")

# ---------------- BRRI dhan62 ----------------
c = "80th meeting agenda 12 decision; crops n080_dhan62_a.png, n080_dhan62_dec.png"
E("BRRI_DHAN62", "official_name_bn", "ব্রি ধান-৬২", "ব্রি ধান-৬২", "NSB_76_82", 32, c, "ocr", V, "high")
E("BRRI_DHAN62", "breeding_line", "BR7517-2R-27-3", "BR7517-2R-27-3", "NSB_76_82", 32, c, "ocr", V, "high")
E("BRRI_DHAN62", "release_category", "NSB_release", "আমন মৌসুমে সারা দেশে চাষাবাদের নিমিত্তে ছাড়করণ করা হলো", "NSB_76_82", 32, c, "ocr", V, "high")
E("BRRI_DHAN62", "approving_body", "NSB (on recommendation of TC 72nd meeting)", "জাতীয় বীজ বোর্ডের কারিগরী কমিটির ৭২ তম সভার সুপারিশের ভিত্তিতে", "NSB_76_82", 32, c, "ocr", V, "high")
E("BRRI_DHAN62", "approval_date", "2013-08-26", "২৬/০৮/২০১৩", "NSB_76_82", 28, "80th minutes opening; crop n080_open.png", "ocr", V, "high", "MoA hybrid list 2018 ed. also gives 26/08/13; BUT 81st minutes agenda 1 (p36, crop n081_item1.png) say 28/08/2013 - conflict kept in key")
E("BRRI_DHAN62", "approval_date", "2013-08-28", "২৮/০৮/২০১৩", "NSB_76_82", 36, "81st minutes agenda 1 'বিগত ২৮/০৮/২০১৩ খ্রিঃ তারিখে অনুষ্ঠিত জাতীয় বীজ বোর্ডের ৮০তম সভার'", "ocr", V, "low", "conflicting statement of the 80th meeting date, in the next meeting's minutes")
E("BRRI_DHAN62", "approval_reference", "NSB 80th meeting", "এনএসবি এর ৮০তম সভা", "NSB_76_82", 28, "80th minutes", "ocr", V, "high", "two_source with GAZ_20150122 ('৮০ তম সভা')")
E("BRRI_DHAN62", "approval_date", "2013", "২০১৩", "SCA_COMP", 21, "row 66; crop cmp_DHAN62.png", "ocr", V, "high", "year only")
E("BRRI_DHAN62", "gazette_date", "2015-01-22", "জানুয়ারি ২২, ২০১৫", "GAZ_20150122", 2, "row ব্রিধান-৫৯/৬০/৬১/৬২ '৮০ তম সভা'", BJ, U, "high")
E("BRRI_DHAN62", "gazette_reference", "notification নং ১২.০৯৭.০২২.০২.০০.০৩২.২০০৮-৪৮৬ (24 Dec 2014); Gazette Extraordinary 22 Jan 2015, p.494", "ব্রিধান-৫৯, ব্রিধান-৬০ ব্রিধান-৬১ এবং ব্রিধান-৬২ ব্রি ৮০ তম সভা", "GAZ_20150122", 2, "table row", BJ, U, "high")
E("BRRI_DHAN62", "gazette_date", "2014-03-18", "মাচর্ ১৮, ২০১৪", "GAZ_20140318", 2, "row 'ব্রিধান-৫৯, ব্রিধান-৫৯, ব্রিধান-৬০ ও ব্রিধান-৬২ ব্রি ৮০তম সভা'", BJ, U, "medium", "this earlier gazette row lists ব্রিধান-৫৯ twice and omits ৬১ (typo in gazette); masthead p.1 reads 2018")
E("BRRI_DHAN62", "season", "Aman", "ব্রিধান-৬২ আমন মৌসুমে সারা দেশে চাষাবাদযোগ্য", "GAZ_20150122", 2, "remark", BJ, T, "high")
E("BRRI_DHAN62", "region_scope", "nationwide", "আমন মৌসুমে সারা দেশে চাষাবাদযোগ্য", "GAZ_20150122", 2, "remark", BJ, T, "high")
E("BRRI_DHAN62", "key_traits", "shortest-duration Aman variety, high zinc", "সবচেয়ে স্বল্প জীবনকাল ও উচ্চ মাত্রার জিংক সম্পন্ন এবং আমন মৌসুমে আবাদযোগ্য উচ্চফলনশীল ধানের জাত", "NSB_76_82", 32, c, "ocr", V, "high")
E("BRRI_DHAN62", "key_traits", "earliest Aman variety; long slender white grain; 100 d; 3.5 t/ha", "আমন মৌসুমে সবচেয়ে আগাম জাত", "SCA_COMP", 21, "row 66; crop cmp_DHAN62.png", "ocr", V, "high")
E("BRRI_DHAN62", "developer", "BRRI", "বাংলাদেশ ধান গবেষণা ইনস্টিটিউট (ব্রি), জয়দেবপুর, গাজীপুর কর্তৃক উদ্ভাবিত", "NSB_76_82", 32, c, "ocr", V, "high")

# ---------------- BRRI dhan89 ----------------
c = "FY2018-19 list row 2; crop sca1819_DHAN89.png"
E("BRRI_DHAN89", "official_name_bn", "ব্রি ধান-৮৯", "ব্রি ধান- ৮৯", "SCA_AV1819", 1, c, "ocr", V, "high")
E("BRRI_DHAN89", "breeding_line", "BR-(Bio)-9786-BC2-59-1-2", "(BR-(Bio)-9786-BC2-59-1-2)", "SCA_AV1819", 1, c, "ocr", V, "high")
E("BRRI_DHAN89", "release_category", "NSB_release", "২০১৮-২০১৯ সালে জাতীয় বীজ বোর্ড কর্তৃক ছাড়কৃত নোটিফাইড ফসলের ইনব্রিড জাতের তালিকা", "SCA_AV1819", 1, "title; crop sca1819_header.png", "ocr", V, "high")
E("BRRI_DHAN89", "approval_date", "2018-10-09", "৯.১০.২০১৮", "SCA_AV1819", 1, c + "; column 'ছাড়করণের তারিখ'", "ocr", K, "high", "visual_check also done; key 97 = 2018-10-09 (two_source)")
E("BRRI_DHAN89", "approval_reference", "NSB 97th meeting", "NSB (৯৭তম সভা)", "SCA_AV1819", 1, c, "ocr", V, "high", "two_source with GAZ_20191211")
E("BRRI_DHAN89", "approval_reference", "NSB 97th meeting", "৯৭তম সভা", "GAZ_20191211", 1, "table row 'ব্রি ধান-৮৯ ৯৭তম সভা'; crop gaz2019_p1_table.png", "ocr", V, "high")
E("BRRI_DHAN89", "gazette_date", "2019-12-11", "বুধবার, ডিসেম্বর ১১, ২০১৯", "GAZ_20191211", 1, "masthead; crop gaz2019_p1_table.png", "ocr", V, "high", "notification dated 05 Dec 2019 ('২০ অগ্রহায়ণ ১৪২৬/০৫ ডিসেম্বর ২০১৯')")
E("BRRI_DHAN89", "gazette_reference", "MoA Seed Wing notification নং ১২.০০.০০০০.০৯৮.১৭.০০১.০৪.১২০০ dated 2019-12-05 under Seed Act 2018 s.7(3); Gazette Extraordinary 11 Dec 2019, p.25625", "নং ১২.০০.০০০০.০৯৮.১৭.০০১.০৪.১২০০", "GAZ_20191211", 1, "memo line; crop gaz2019_p1_table.png", "ocr", V, "high", "page 25625 from bgpress index and OCR '( ২৫৬২৫ )'")
E("BRRI_DHAN89", "season", "Boro", "বোরো মৌসুমে সারাদেশে চাষযোগ্য", "GAZ_20191211", 1, "remark", "ocr", V, "high", "SCA list also 'বোরো'")
E("BRRI_DHAN89", "region_scope", "nationwide", "বোরো মৌসুমে সারাদেশে চাষযোগ্য", "GAZ_20191211", 1, "remark", "ocr", V, "high")
E("BRRI_DHAN89", "key_traits", "3-5 days earlier than BRRI dhan29; 154-158 d; 8.15 t/ha; light green leaves, broad flag leaf, panicle above flag leaf at maturity", "ব্রি ধান ২৯ এর চাইতে ৩-৫ দিন আগাম", "SCA_AV1819", 1, c, "ocr", V, "high")
E("BRRI_DHAN89", "developer", "BRRI", "ব্রি", "SCA_AV1819", 1, c, "ocr", V, "high")

# ---------------- BRRI dhan118 ----------------
E("BRRI_DHAN118", "official_name_bn", "ব্রি ধান১১৮", "ব্রি ধান১১৮", "NSB_115", 7, "agenda 9 decision; crop n115_dhan118_dec2.png", "ocr", V, "high", "SCA FY2025-26 list row 6 agrees (crop sca2526_DHAN118.png)")
E("BRRI_DHAN118", "breeding_line", "BR11894-R-R-R-R-169", "BR11894-R-R-R-R-169", "NSB_115", 7, "agenda 9 text and decision; crops n115_dhan118_a.png, n115_dhan118_dec2.png", "ocr", V, "high", "OCR read a trailing '1' ('-1691') that is the danda; corrected by eye")
E("BRRI_DHAN118", "release_category", "NSB_release", "ব্রি ধান১১৮ হিসেবে সারাদেশের জন্য ছাড়করণের অনুমোদন দেয়া হলো", "NSB_115", 7, "agenda 9 decision", "ocr", V, "high")
E("BRRI_DHAN118", "approving_body", "NSB (on TC recommendation)", "কারিগরি কমিটির সুপারিশকৃত", "NSB_115", 7, "agenda 9 decision", "ocr", V, "high")
E("BRRI_DHAN118", "approval_date", "2026-02-05", "০৫/০২/ ২০২৬", "SCA_AV2526", 2, "row 6 'এনএসবি এর ১১৫তম সভা তারিখঃ ০৫/০২/ ২০২৬'; crop sca2526_DHAN118.png", "ocr", K, "high", "visual_check also; key 115 = 2026-02-05")
E("BRRI_DHAN118", "approval_reference", "NSB 115th meeting", "এনএসবি এর ১১৫তম সভা", "SCA_AV2526", 2, "row 6", "ocr", V, "high", "two_source with NSB_115 minutes")
E("BRRI_DHAN118", "season", "Boro", "বোরো", "SCA_AV2526", 2, "row 6", "ocr", V, "high")
E("BRRI_DHAN118", "region_scope", "nationwide", "সারাদেশের জন্য ছাড়করণের অনুমোদন", "NSB_115", 7, "agenda 9 decision", "ocr", V, "high", "trait text says suited to haor areas")
E("BRRI_DHAN118", "key_traits", "cold tolerant at reproductive stage, suited to haor; 137 d; 6.77 t/ha; DUS vs BRRI dhan28 (5 traits); VCU check BRRI dhan67", "হাওর অঞ্চলের উপযোগী প্রজনন পর্যায়ে ঠান্ডা সহনশীল", "SCA_AV2526", 2, "row 6; crop sca2526_DHAN118.png", "ocr", V, "high", "DUS/VCU details from NSB_115 p7 OCR text, not cropped")
E("BRRI_DHAN118", "developer", "BRRI", "বাংলাদেশ ধান গবেষণা ইনস্টিটিউট (ব্রি)", "SCA_AV2526", 2, "row 6", "ocr", V, "high")
E("BRRI_DHAN118", "gazette_date", "", "", "SCA_AV2526", 2, "", "ocr", U, "low", "no gazette notification found; latest MoA release gazette in the bgpress index is 19 Jul 2025 (NSB 108-114)")

# ---------------- Binadhan-7 ----------------
E("BINADHAN7", "official_name_bn", "বিনা ধান-৭", "বিনা ধান-৭", "NSB_R5", 52, "64th meeting agenda 7 decision 1; crop r5_bina7.png", BJ, V, "high")
E("BINADHAN7", "breeding_line", "TNDB-100", "টিএনডিবি-১০০ লাইনটি বিনা ধান-৭ হিসেবে", "NSB_R5", 52, "agenda 7 decision 1", BJ, V, "high", "line written in Bangla; Latin form 'TNDB-100' is a transliteration")
E("BINADHAN7", "release_category", "NSB_release", "দেশের সকল অঞ্চলের জন্য চাষাবাদের নিমিত্তে ছাড়করণের অনুমোদন দেয়া হলো", "NSB_R5", 52, "agenda 7 decision 1", BJ, V, "high")
E("BINADHAN7", "approving_body", "NSB (on recommendation of TC 56th meeting)", "জাতীয় বীজ বোর্ডের কারিগরী কমিটির ৫৬তম সভায় ধান, পাট ও আখের একটি করে মোট তিনটি জাত ছাড়করণের অনুমোদন", "NSB_R5", 52, "agenda 7 heading", BJ, U, "high")
E("BINADHAN7", "approval_date", "2007-09-24", "২৪.০৯.২০০৭", "NSB_R5", 48, "64th minutes opening 'গত ২৪.০৯.২০০৭ খ্রিঃ তারিখ ... ৬৪তম সভা'", BJ, K, "high", "key 64 = 2007-09-24 two_source (MoA hybrid list)")
E("BINADHAN7", "approval_reference", "NSB 64th meeting", "৬৪তম সভা", "NSB_R5", 48, "64th minutes", BJ, K, "high")
E("BINADHAN7", "approval_date", "2007", "২০০৭", "SCA_COMP", 24, "BINA table row 06; crop cmp_BINA7.png", "ocr", V, "high", "year only")
E("BINADHAN7", "region_scope", "nationwide", "দেশের সকল অঞ্চলের জন্য", "NSB_R5", 52, "decision", BJ, V, "high", "compendium also 'সমগ্র বাংলাদেশ'")
E("BINADHAN7", "season", "Aman", "আমন", "SCA_COMP", 24, "row 06", "ocr", V, "high")
E("BINADHAN7", "key_traits", "early maturing, suited to monga areas; 115-120 d; 5.5 t/ha; long slender grain; partially resistant to stem borer and leafhopper(?)", "আগাম পাকে বিধায় মঙ্গা এলাকার উপযোগী। গলমাছি ও পামরি পোকা আংশিক প্রতিরোধী", "SCA_COMP", 24, "row 06; crop cmp_BINA7.png", "ocr", V, "high", "pest names translated loosely: গলমাছি = gall midge, পামরি পোকা = rice hispa")
E("BINADHAN7", "developer", "BINA", "বাংলাদেশ পরমাণু কৃষি গবেষণা ইনস্টিটিউট কতৃর্ক উদ্ভাবিত", "NSB_R5", 52, "decision", BJ, V, "high")
E("BINADHAN7", "gazette_date", "", "", "NSB_R5", 52, "", BJ, U, "low", "no gazette notice for NSB 64 found (MoA copies exist for NSB 60, 62, 68 only)")

# ---------------- Binadhan-27 ----------------
E("BINADHAN27", "official_name_bn", "বিনা ধান২৭", "বিনা ধান২৭", "NSB_115", 4, "agenda 3 decision; crop n115_bina27_dec2.png", "ocr", V, "high", "SCA FY2025-26 list row 1 agrees (crop sca2526_BINA27.png)")
E("BINADHAN27", "breeding_line", "BN-P-318", "BN-P-318", "NSB_115", 4, "agenda 3; crops n115_bina27_a.png, n115_bina27_dec2.png", "ocr", V, "high")
E("BINADHAN27", "cgiar_evidence", "line collected from IRRI Philippines through IRRI-BINA collaboration", "কৌলিক সারিটি ইরি-বিনার সহযোগিতায় ইরি-ফিলিপাইন হতে সংগ্রহ করা হয়", "NSB_115", 4, "agenda 3 text; crop n115_bina27_a.png", "ocr", V, "high")
E("BINADHAN27", "release_category", "NSB_release", "বিনা ধান২৭ হিসেবে সারাদেশের জন্য ছাড়করণের অনুমোদন দেয়া হলো", "NSB_115", 4, "agenda 3 decision", "ocr", V, "high")
E("BINADHAN27", "approving_body", "NSB (on TC recommendation)", "কারিগরি কমিটির সুপারিশকৃত", "NSB_115", 4, "decision", "ocr", V, "high")
E("BINADHAN27", "approval_date", "2026-02-05", "০৫/০২/ ২০২৬", "SCA_AV2526", 1, "row 1 'এনএসবি এর ১১৫তম সভা তারিখঃ ০৫/০২/ ২০২৬'; crop sca2526_BINA27.png", "ocr", K, "high", "visual_check also; key 115")
E("BINADHAN27", "approval_reference", "NSB 115th meeting", "এনএসবি এর ১১৫তম সভা", "SCA_AV2526", 1, "row 1", "ocr", V, "high", "two_source with NSB_115")
E("BINADHAN27", "season", "Aman", "আমন", "SCA_AV2526", 1, "row 1", "ocr", V, "high")
E("BINADHAN27", "region_scope", "nationwide", "সারাদেশের জন্য", "NSB_115", 4, "decision", "ocr", V, "high")
E("BINADHAN27", "key_traits", "blast resistant; photoperiod-insensitive; 120-125 d; 6.30 t/ha; long slender grain, amylose 25.70%", "ব্লাস্ট রোগ প্রতিরোধী", "SCA_AV2526", 1, "row 1; crop sca2526_BINA27.png", "ocr", V, "high")
E("BINADHAN27", "developer", "BINA", "বাংলাদেশ পরমাণু কৃষি গবেষণা ইনস্টিটিউট (বিনা)", "SCA_AV2526", 1, "row 1", "ocr", V, "high")
E("BINADHAN27", "gazette_date", "", "", "NSB_115", 4, "", "ocr", U, "low", "no gazette found (see BRRI_DHAN118)")

# ---------------- HIRA2 (HS-273) ----------------
c = "MoA list row 11; crop moa26_p1_row11.png"
E("HIRA2", "official_name_bn", "এইচ এস-২৭৩ (হীরা-২)", "এইচ এস-২৭৩ (হীরা-২)", "MOA_HYB26", 1, c, BJ, V, "high")
E("HIRA2", "official_name_en", "HS-273 (Supreme Hybrid-2)", "HS-273 (Supreme Hybrid-2)", "NSB_R5", 53, "64th meeting agenda 8 item 14; crop r5_hira2_64.png", "visual_check", V, "high")
E("HIRA2", "official_name_bn", "HS-273 (হীরা-২)", "HS-273 (হীরা-২)", "SCA_COMP", 27, "hybrid table row 11; crop cmp_HIRA2.png", "ocr", V, "high")
E("HIRA2", "type", "hybrid", "হাইব্রিড", "MOA_HYB26", 1, c, BJ, V, "high")
E("HIRA2", "release_category", "NSB_registration", "সাময়িকভাবে নিবন্ধন অনুমোদন করা হল", "NSB_43_57", 100, "53rd meeting decision (ক); crop n053_hira2.png", "ocr", V, "high", "provisional registration")
E("HIRA2", "approving_body", "NSB (on recommendation of TC 46th meeting)", "কারিগরী কমিটির ৪৬তম সভার সুপারিশের আলোকে নিম্নলিখিত শর্তাধীনে", "NSB_43_57", 100, "53rd meeting decision; crop n053_hira2.png", "ocr", V, "high")
E("HIRA2", "approval_date", "2003-10-13", "১৩/১০/২০০৩", "NSB_43_57", 96, "53rd minutes opening '১৩/১০/২০০৩খ্রিঃ তারিখ ... ৫৩তম সভা'", "ocr", K, "high", "key 53 = 2003-10-13 two_source (MoA list '১৩.১০.০৩,৫৩ সভা')")
E("HIRA2", "approval_reference", "NSB 53rd meeting: provisional registration for Comilla and Rajshahi regions", "সুপ্রীম সীড কোম্পানীর এইচএস-২৭৩ হাইব্রিড জাতটিকে কুমিল্লা ও রাজশাহী অঞ্চলের জন্য", "NSB_43_57", 100, "decision (ক)", "ocr", V, "high")
E("HIRA2", "approval_date", "2005-10-27", "২৭-১০-২০০৫", "NSB_R5", 18, "59th minutes opening", BJ, K, "high", "key 59 two_source")
E("HIRA2", "approval_reference", "NSB 59th meeting: re-trialled, provisional registration extended to Dhaka and Mymensingh", "এইচএস-২৭৩ জাতটি ঢাকা ও ময়মনসিংহ অঞ্চলে ... অঞ্চলভিত্তিক সাময়িকভাবে নিবন্ধিকরণের অনুমোদন দেয়া হ'ল", "NSB_R5", 21, "59th meeting agenda 3 (গ)", BJ, U, "high", "text layer, not cropped")
E("HIRA2", "approval_date", "2007-09-24", "২৪.০৯.২০০৭", "NSB_R5", 48, "64th minutes opening", BJ, K, "high", "key 64 two_source")
E("HIRA2", "approval_reference", "NSB 64th meeting: re-trialled, provisional registration extended to Jessore (previously Dhaka, Mymensingh, Comilla, Rajshahi)", "HS-273 (Supreme Hybrid-2) হাইব্রিড জাতটি যশোর অঞ্চলে চাষাবাদের নিমিত্তে সাময়িকভাবে নিবন্ধিকরণের জন্য অনুমোদন দেয়া হলো", "NSB_R5", 53, "64th meeting agenda 8 item 14; crop r5_hira2_64.png", "visual_check", V, "high", "not in the MoA cumulative list's meeting column")
E("HIRA2", "approval_reference", "NSB 53rd (13.10.03) and 59th (27.10.05) meetings", "১৩.১০.০৩,৫৩ সভা ও ২৭.১০.০৫, ৫৯তম সভা", "MOA_HYB26", 1, c, BJ, K, "high")
E("HIRA2", "approval_reference", "NSB 53rd, 59th and 68th meetings", "৫৩, ৫৯ ও ৬৮ তম সভা", "SCA_COMP", 27, "hybrid row 11; crop cmp_HIRA2.png", "ocr", V, "medium", "68th not supported by the 68th minutes text (no HS-273 item found in report no.5); the Jessore extension is in the 64th minutes")
E("HIRA2", "region_scope", "Dhaka, Mymensingh, Rajshahi, Comilla and Jessore regions", "ঢাকা, ময়মনসিংহ, রাজশাহী, কুমিল্লা ও যশোর", "MOA_HYB26", 1, c, BJ, V, "high", "compendium lists the same five regions")
E("HIRA2", "origin", "China", "চীন", "MOA_HYB26", 1, c + "; column 'উৎস'", BJ, V, "high", "compendium also 'চীন'")
E("HIRA2", "developer", "Supreme Seed Co. Ltd (importer/developer)", "সুপ্রিম সীড কোং লিঃ", "MOA_HYB26", 1, c + "; column 'উদ্ভাবনকারী/আমদানীকারক'", BJ, V, "high")
E("HIRA2", "season", "Boro", "বোরো", "SCA_COMP", 27, "hybrid row 11", "ocr", V, "high")
E("HIRA2", "key_traits", "142-162 d; 7.40 t/ha", "১৪২-১৬২; ৭.৪০", "SCA_COMP", 27, "hybrid row 11; crop cmp_HIRA2.png", "ocr", V, "high")
E("HIRA2", "status", "provisional registration with conditions: F1 seed to be produced locally from year 6, otherwise approval withdrawn", "জাতগুলোর জন্য ... ৬ষ্ঠ বছর থেকে এ জাতগুলো দেশে উৎপাদন করে বাজারজাত করতে হবে। অন্যথায় জাতগুলোর অনুমোদন প্রত্যাহার করা হবে", "NSB_43_57", 100, "53rd meeting conditions 4", "ocr", U, "medium", "condition text from OCR, not cropped; no withdrawal record found")

# ---------------- BRRI hybrid dhan1 ----------------
E("BRRI_HYBRID1", "official_name_bn", "ব্রি হাইব্রিড ধান-১", "ব্রি হাইব্রিড ধান-১", "NSB_43_57", 56, "48th (special) meeting agenda 1 decision (ক); crop n048_decision.png", "ocr", V, "high")
E("BRRI_HYBRID1", "official_name_en", "BRRI Hybrid dhan-1", "BRRI Hybrid dhan-1 (IR-69690)", "SCA_COMP", 27, "hybrid row 06; crop cmp_BRRIHYB1.png", "ocr", V, "high")
E("BRRI_HYBRID1", "breeding_line", "IR69690", "আইআর-৬৯৬৯০", "NSB_43_57", 55, "48th meeting agenda 1 heading; crop n048_item1.png", "ocr", V, "high", "compendium gives '(IR-69690)'")
E("BRRI_HYBRID1", "type", "hybrid", "হাইব্রিড", "NSB_43_57", 55, "agenda 1", "ocr", V, "high")
E("BRRI_HYBRID1", "release_category", "NSB_release", "ব্রি হাইব্রিড ধান-১ নামে প্রাথমিক পর্যায়ে দেশের বরিশাল ও যশোর অঞ্চলের জন্য ৩ বছরের জন্য ছাড় করা হলো", "NSB_43_57", 56, "decision (ক); crop n048_decision.png", "ocr", V, "high", "public hybrid released (ছাড়), regionally and initially for 3 years; MoA hybrid list also includes it")
E("BRRI_HYBRID1", "approving_body", "NSB (on recommendation of TC 40th (special) meeting)", "কারিগরী কমিটির ৪০তম (বিশেষ) সভার সুপারিশ", "NSB_43_57", 55, "agenda 1 heading; crop n048_item1.png", "ocr", V, "high")
E("BRRI_HYBRID1", "approval_date", "2001-07-08", "০৮-০৭-২০০১", "NSB_43_57", 55, "48th (special) minutes opening 'বিগত ০৮-০৭-২০০১ তারিখ'; header crop n048_header.png", "ocr", K, "high", "key 48 = 2001-07-08 two_source (MoA list '৪৮ তম সভা-৮/৭/০১'; compendium '০৮/৭/০১')")
E("BRRI_HYBRID1", "approval_reference", "NSB 48th (special) meeting", "জাতীয় বীজ বোর্ডের ৪৮তম (বিশেষ) সভার কার্যবিবরণী", "NSB_43_57", 55, "header; crop n048_header.png", "ocr", V, "high")
E("BRRI_HYBRID1", "approval_reference", "NSB 48th meeting, 8/7/01", "৪৮ তম সভা-৮/৭/০১", "MOA_HYB26", 1, "row 06; crop moa26_p1_row06.png", BJ, K, "high")
E("BRRI_HYBRID1", "region_scope", "Barisal and Jessore regions (initially, for 3 years)", "দেশের বরিশাল ও যশোর অঞ্চলের জন্য ৩ বছরের জন্য", "NSB_43_57", 56, "decision (ক)", "ocr", V, "high", "MoA list: 'যশোর ও বরিশাল'")
E("BRRI_HYBRID1", "origin", "ইরি (IRRI)", "ইরি", "MOA_HYB26", 1, "row 06 column 'উৎস'; crop moa26_p1_row06.png", BJ, V, "high", "cgiar_evidence candidate; conflicts with compendium origin 'বাংলাদেশ'")
E("BRRI_HYBRID1", "cgiar_evidence", "MoA cumulative hybrid list records origin 'ইরি' (IRRI)", "ব্রি হাইব্রিড ধান-১ | ইরি | ব্রি, গাজীপুর", "MOA_HYB26", 1, "row 06; crop moa26_p1_row06.png", BJ, V, "high", "the 2018 MoA edition has the same entry")
E("BRRI_HYBRID1", "origin", "বাংলাদেশ (Bangladesh)", "বাংলাদেশ", "SCA_COMP", 27, "hybrid row 06 column 'উৎস'; crop cmp_BRRIHYB1.png", "ocr", V, "high", "conflicts with MoA list 'ইরি'")
E("BRRI_HYBRID1", "developer", "BRRI, Gazipur", "ব্রি, গাজীপুর", "MOA_HYB26", 1, "row 06", BJ, V, "high", "48th minutes: 'বাংলাদেশ ধান গবেষণা ইনস্টিটিউট (ব্রি) কর্তৃক উদ্ভাবিত'")
E("BRRI_HYBRID1", "season", "Boro", "বোরো", "SCA_COMP", 27, "hybrid row 06", "ocr", V, "high")
E("BRRI_HYBRID1", "key_traits", "145-150 d; 7.00 t/ha; pilot production tests in 25 locations, yields 5.32-9.56 t/ha", "১৪৫-১৫০; ৭.০০", "SCA_COMP", 27, "hybrid row 06; crop cmp_BRRIHYB1.png", "ocr", V, "high", "yield range from 48th minutes OCR text, not cropped")
E("BRRI_HYBRID1", "status", "released initially for 3 years", "৩ বছরের জন্য ছাড় করা হলো", "NSB_43_57", 56, "decision (ক)", "ocr", V, "medium", "later extension/withdrawal not traced")

# ---------------- IRRI_DIRECT (no choice made by P2A) ----------------
E("IRRI_DIRECT", "breeding_line", "candidates from official minutes: BRRI dhan47 = IR63307-4B-4-3 (NSB 62); BRRI dhan56 = IR74371-70-1-1 (NSB 75); BRRI hybrid dhan1 = IR69690 (NSB 48)", "আইআর ৬৩৩০৭-৪বি-৪-৩ / আইআর ৭৪৩৭১-৭০-১-১ / আইআর-৬৯৬৯০", "NSB_R5", 40, "see BRRI_DHAN47, BRRI_DHAN56, BRRI_HYBRID1 rows", BJ, V, "medium", "the institute agent chooses the IRRI_DIRECT variety; these are the IR-designated lines released under BD names that appear in P2A's sources")

# convenience: source_url from manifest
man = {}
for f in [ROOT / "02_raw/manifest.csv"] + list((ROOT / "02_raw/_manifest_parts").glob("*.csv")):
    if f.exists():
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            man[r["file_path"].replace("\\", "/")] = r["source_url"]
for r in rows:
    if r["local_file"] not in man:
        r["notes"] = (r["notes"] + "; " if r["notes"] else "") + "WARNING local_file not in manifest"
cols = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file", "page", "locator",
        "method", "validation", "confidence", "notes"]
with open(ROOT / "04_working/evidence_P2A.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
import collections
print(len(rows)); print(collections.Counter(r["pilot_key"] for r in rows))
print(collections.Counter((r["method"], r["validation"]) for r in rows))
print([r["local_file"] for r in rows if "WARNING" in r["notes"]][:5])
