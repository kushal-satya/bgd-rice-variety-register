"""F6G: write 04_working/evidence_F6G.csv from hand-checked findings (every value read by eye from the crop
named in `locator`). Re-runnable."""
import csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
HDR = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file", "page",
       "locator", "method", "validation", "confidence", "notes"]
M19 = ("02_raw/sca/nsb_minutes_019-028.pdf", "NSB_R2", "NSB activities report no.2 (minutes summaries, NSB 19th-28th meetings, 1984-1992)")
M29 = ("02_raw/sca/nsb_minutes_029-042.pdf", "NSB_R3", "NSB activities report no.3 (minutes, NSB 29th-42nd meetings, 1993-1999)")
M43 = ("02_raw/sca/nsb_minutes_043-057.pdf", "NSB_R4", "NSB activities report no.4 (minutes, NSB 43rd-57th meetings, 2000-2005)")
rows = []

def add(key, field, value, raw, src, page, loc, conf, notes):
    f, sid, title = src
    rows.append(dict(pilot_key=key, field=field, value=value, value_raw=raw, source_id=sid, source_title=title,
                     authority_rank="1_primary_legal", local_file=f, page=page, locator=loc, method="ocr",
                     validation="visual_check", confidence=conf, notes=notes))

# 1. BR22 / BR23: approved NSB 24th (19-10-1988), decision (5) gazette; 25th meeting (31-10-1989) item 9.01 reports gazette 16-3-89
raw89 = "পূর্বের সভার সিদ্ধান্তের প্রেক্ষিতে ... অনুমোদিত জাতগুলি বাংলাদেশ সরকারের ১৬-৩-৮৯ইং তারিখের ১১ই নভেম্বর গেজেটে প্রকাশিত হয়"
for k, nm in [("BR22", "কিরণ (বি. আর-২২)"), ("BR23", "দিশারী (বি. আর-২৩)")]:
    add(k, "gazette_date", "1989-03-16", raw89, M19, 50,
        "NSB 25th meeting item 9.01 (implementation of 24th meeting decisions); crop 04_working/crops/F6G/m25_p50_gazette_1989.png; context crops m25_p49_head.png, m24_p48_BR22_23.png",
        "medium",
        f"REPORTED gazette date, gazette itself not seen (not on dpp.gov.bd: no extraordinary MoA item that day; weekly issues are listed online only from 2013; 16 Mar 1989 was a Thursday, the weekly issue day). Link to {nm}: the 24th meeting (19-10-1988) approved BR22/BR23 and decided (5) that all approved varieties be gazetted; the 25th meeting reports 'approved varieties' of the previous meeting published. The printed phrase also contains '১১ই নভেম্বর' which is unexplained; do not treat the day as certain.")
    add(k, "gazette_reference", "Bangladesh Gazette (issue type not stated), 16-3-89, notification of NSB 24th-meeting approvals (reported by NSB 25th minutes)", raw89, M19, 50,
        "NSB 25th meeting item 9.01; crop m25_p50_gazette_1989.png", "medium", "memo/SRO number not stated in the minutes")
    add(k, "approval_reference", "NSB 24th meeting (1988-10-19), item 8.02(গ), decision (5) 'উল্লিখিত সকল অনুমোদিত জাতগুলির গেজেট বিজ্ঞপ্তি কৃষি মন্ত্রণালয় কর্তৃক যথারীতি প্রকাশের ব্যবস্থা গ্রহণ করা হইবে'",
        "উল্লিখিত সকল অনুমোদিত জাতগুলির গেজেট বিজ্ঞপ্তি কৃষি মন্ত্রণালয় কর্তৃক, যথারীতি প্রকাশের ব্যবস্থা গ্রহণ করা হইবে।", M19, 48,
        "NSB 24th meeting item 8.02(গ) and decision (৫); crop m24_p48_BR22_23.png", "high", "approval cited by the gazette report above")

# 2. BR26: approved NSB 29th (08-04-1993); 30th meeting (26-10-1993) reports gazette issued, no date
rawbr26 = "ব্রি কর্তৃক উদ্ভাবিত ধানের জাত বি আর-২৬, (শ্রাবনী) ... বোর্ডের ২৯ তম সভায় অনুমোদিত হয়েছিল। জাত গুলোর গেজেট বিজ্ঞপ্তি জারী করা হয়েছে।"
add("BR26", "gazette_reference", "gazette notification reported issued between 1993-04-08 and 1993-10-26 (date and number not stated)", rawbr26, M29, 12,
    "NSB 30th meeting item 2(iii) (implementation of 29th meeting decisions); crop 04_working/crops/F6G/m30_p12_BR26.png",
    "medium", "No gazette_date can be given: the minutes only say the notification was issued. Gazette not found online (pre-2013 non-SRO notices and all pre-2013 weekly issues are absent from dpp.gov.bd).")

# 3. BAU dhan2: approved NSB 36th (22-08-1996); 37th meeting (03-04-1997) reports release gazette published 14/11/96
rawbau = "বাংলাদেশ কৃষি বিশ্ববিদ্যালয় কর্তৃক উদ্ভাবিত 'বাউ ধান-২' নামক ধানের জাতটি বিগত বোর্ড সভায় অনুমোদিত হয়। ইং ১৪/১১/৯৬ তারিখে জাতটির ছাড়করণ বিষয়ক গেজেট বিজ্ঞপ্তি প্রকাশিত হয়েছে।"
add("BAU_DHAN2", "gazette_date", "1996-11-14", rawbau, M29, 32,
    "NSB 37th meeting, review of previous meeting decisions, item (ii); crop 04_working/crops/F6G/m37_p32_BAU2.png", "medium",
    "REPORTED date of the release (ছাড়করণ) gazette notification; gazette itself not seen. 14 Nov 1996 was a Thursday (weekly issue day); no MoA extraordinary item on bgpress that day.")
add("BAU_DHAN2", "gazette_reference", "release (ছাড়করণ) gazette notification of 14/11/96 (issue type, page and memo not stated; reported by NSB 37th minutes)", rawbau, M29, 32,
    "crop m37_p32_BAU2.png", "medium", "")

# 4. BRRI dhan34 (and 'ব্রি ধান-৩০' as printed, probably dhan33): NSB 39th meeting reports press request memo 130 of 09/09/97
rawd34 = "বিআরআরআই কর্তৃক উদ্ভাবিত ব্রি ধান-৩০ ও ব্রি ধান -৩৪ অনুমোদিত হয়েছিল। জাতগুলো ছাড়করনের বিষয়ে গেজেট বিজ্ঞপ্তি জারীর জন্য সরকারী মূদ্রনালয়কে অনুরোধ জানানো হয়েছে। স্মারক নং- ১৩০ তারিখ ইং ০৯/০৯/৯৭ মাধ্যমে ) এ সংক্রান্ত গেজেট বিজ্ঞপ্তি প্রকাশিত না হয়ে থাকলে সরকারী মুদ্রনালয়কে তাগিদ দিতে হবে।"
add("BRRI_DHAN34", "gazette_reference", "NOT CONFIRMED PUBLISHED: release gazette requested from Government Press by Seed Wing memo no. 130 of 1997-09-09; publication not confirmed as of NSB 39th meeting (1998-02-05)", rawd34, M29, 38,
    "NSB 39th meeting, review of 38th meeting decisions, item (v); crop 04_working/crops/F6G/m39_p38_dhan33_34.png", "high", "no gazette date")
add("UNMATCHED", "gazette_reference", "NOT CONFIRMED PUBLISHED: release gazette requested by memo no. 130 of 1997-09-09 for 'ব্রি ধান-৩০' (as printed)", rawd34, M29, 38,
    "crop m39_p38_dhan33_34.png", "low",
    "Printed 'ব্রি ধান-৩০' among varieties approved at the 38th meeting (1997-07-16). BRRI dhan30 was approved at the 32nd meeting (1994); the 38th approved BRRI dhan33 and dhan34, so this is probably BRRI dhan33. Not keyed (provenance rule).")

# 5. BRRI dhan39: NSB 43rd (28-03-2000) reports press request for the 42nd meeting's approved varieties
raw39 = "ঐ সভায় গৃহীত ২নং সিদ্ধান্তের বিষয়ে অনুমোদিত জাতসমূহের গেজেট বিজ্ঞপ্তি জারির জন্য মন্ত্রণালয়ের সংশ্লিষ্ট শাখার মাধ্যমে সরকারি মুদ্রণালয়কে অনুরোধ জানানো হয়েছে।"
add("BRRI_DHAN39", "gazette_reference", "NOT CONFIRMED PUBLISHED: gazette for varieties approved under NSB 42nd meeting decision 2 requested from Government Press (no memo/date given), as of NSB 43rd meeting (2000-03-28)", raw39, M43, 11,
    "NSB 43rd meeting agenda 2; crop 04_working/crops/F6G/m43_p11_dhan39.png", "medium",
    "Link to BRRI dhan39 rests on the targets file (BRRI dhan39 approved at NSB 42nd, agenda 4); the minutes say 'decision 2' and do not name the varieties in this passage.")

# 6. BRRI dhan40/41: NSB 53rd-meeting implementation table: sent to press, not yet published
raw40 = "লবণাক্ত এলাকায় চাষোপযোগী ব্রিধান-৪০ ও ব্রি ধান-৪১ জাত দুটি অবমুক্ত করা হলো ... প্রজ্ঞাপন আকারে জারী করার জন্য সরকারী মুদ্রণালয়ে প্রেরণ করা হয়েছে। গেজেট এখনও প্রকাশ হয়নি। খুব শীঘ্রই হবে বলে আমাদেরকে জানানো হয়েছে।"
for k in ["BRRI_DHAN40", "BRRI_DHAN41"]:
    add(k, "gazette_reference", "NOT YET PUBLISHED at the next NSB meeting: notification sent to Government Press for gazetting; 'গেজেট এখনও প্রকাশ হয়নি'", raw40, M43, 97,
        "implementation table of the NSB 52nd meeting decisions (in the 53rd meeting minutes); crop 04_working/crops/F6G/m53_p97_dhan40_41.png", "high",
        "no gazette date; same table mentions a 02/10/2003 memo, so the status is as of late 2003")

# 7. BRRI dhan42/43: Seed Wing memo কৃষি/বীজ/উইং/ বীজ প্র-৭(২)/৯৩/২৫০ of 28/7/2004 asked the Press to publish in the Extraordinary
raw42 = "অত্র উইং এর কৃষি/বীজ/উইং/ বীজ প্র-৭(২)/৯৩/ ২৫০, তারিখঃ ২৮/৭/২০০৪ খ্রিঃ সংখ্যক স্মারকের মাধ্যমে বাংলাদেশ গেজেটের অতিরিক্ত সংখ্যায় প্রকাশের জন্য বাংলাদেশ সরকারী মুদ্রণালয়, ঢাকাকে অনুরোধ করা হয়েছে।"
for k in ["BRRI_DHAN42", "BRRI_DHAN43"]:
    add(k, "gazette_reference", "SENT FOR GAZETTING: Seed Wing memo কৃষি/বীজ/উইং/বীজ প্র-৭(২)/৯৩/২৫০ dated 2004-07-28 asked the Government Press to publish in the Gazette Extraordinary; publication date not stated", raw42, M43, 117,
        "implementation table of NSB 54th meeting decisions, item 7 (in the NSB 56th meeting minutes, 30/12/2004); crop 04_working/crops/F6G/m55_p117_dhan42_43.png", "high",
        "Same file series (বীজ প্র-৭(২)/৯৩) as the 2007 release gazettes (/৪৬, /৪৮). The 2004 Extraordinary is not on dpp.gov.bd (pre-2013 non-SRO notices are not indexed). Breeding lines printed: বিআর-৬০৫৮-৬-৩-৩ (dhan42), বিআর-৫৫৪৩-৫-১-২-৪ (dhan43).")

with open(ROOT / "04_working/evidence_F6G.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=HDR); w.writeheader(); w.writerows(rows)
print(len(rows), "rows")
