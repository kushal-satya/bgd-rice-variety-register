"""F3H: hybrid-rice decisions in NSB activities report no.5 (minutes of meetings 58-75; SutonnyMJ text layer,
converted by P2A to 03_extracted/text/P2A/nsb_058-075_unicode.txt). Hand-mapped decision items -> keys.

Writes 04_working/_F3H_r5_decisions.csv (meeting, key, kind, page, line, quote, regions_en, notes).
Latin words inside the text layer are Bijoy-garbled (e.g. 'ঐঞগ' = HTM); names were matched by the readable Bangla
trade names and by the MoA list. Each item was read in the converted text by F3H.
"""
import csv, re, pathlib, unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
TXT = ROOT / "03_extracted/text/P2A/nsb_058-075_unicode.txt"

# (meeting, key, kind, unique substring of the decision line, regions in English, note)
D = [
    (58, "HYB_HIRA995", "extension", "হাইব্রিড ধান ৯৯-৫ (হীরা) জাতটিকে ঢাকা অঞ্চলে বিপণন", "Dhaka", "decision: marketing and cultivation in Dhaka region"),
    (59, "HYB_TINPATA40", "new", "সিদ্ধান্ত্ম: তিনপাতা-৪০ জাতটি ঢাকা", "Dhaka, Mymensingh, Comilla", "provisional registration (সাময়িকভাবে নিবন্ধিকরণ); MoA list gives only the 60th meeting"),
    (59, "HYB_JAGORON2", "new", "সিদ্ধান্ত্ম: তিনপাতা-৪০ জাতটি ঢাকা", "Dhaka, Mymensingh, Comilla, Jessore, Rangpur", "BRAC HB-8 (MoA row 32 'এইচবি-০৮ (জাগরণ-২)'); provisional registration; MoA list gives only the 60th meeting"),
    (59, "HYB_RAICHAR101", "extension", "সিদ্ধান্ত্ম: পুনঃস্ট্রায়ালকৃত চেন্‌স ক্রপ সায়েন্স", "all regions", "re-trialled; provisional registration for all regions"),
    (59, "HYB_LP50", "extension", "সিদ্ধান্ত্ম: পুনঃট্রায়ালকৃত আফতাব বহুমুখী ফামর্ লিঃ এর এলপি-৫০", "Rajshahi", "re-trialled; regional provisional registration; NOT in the MoA list meeting column (which gives only the 56th)"),
    (59, "HYB_HIRA2", "extension", "সিদ্ধান্ত্ম: পুনঃট্রায়ালকৃত আফতাব বহুমুখী ফামর্ লিঃ এর এলপি-৫০", "Dhaka, Mymensingh", "HS-273 re-trialled; regional provisional registration"),
]
T60 = [("HYB_TAJ1", "ময়মনসিংহ, কুমিলস্না ও রংপুর", "Mymensingh, Comilla, Rangpur"),
       ("HYB_TAJ2", "ময়মনসিংহ, কুমিলস্না\n২ (দুই)", "Mymensingh, Comilla"),
       ("HYB_SONARBANGLA6", "এইচ-০৮৯ ও এইচ-১২৫", "Dhaka, Mymensingh, Comilla, Jessore"),
       ("HYB_GOLDHTM606", "এইচ-০৯০ ও এইচ-১২৪", "Mymensingh, Comilla"),
       ("HYB_TIAHTM707", "এইচ-১০৭ ও এইচ-১৪১", "Mymensingh, Comilla"),
       ("HYB_LP108", "এইচ-০৯১ ও এইচ-১২১", "Mymensingh, Comilla, Rajshahi"),
       ("HYB_SURMA2", "এইচ-০৯২ ও এইচ-১৩৯", "Mymensingh, Comilla, Jessore, Rajshahi"),
       ("HYB_SURMA1", "এইচ-০৯৮ ও এইচ-১৩৬", "Dhaka, Mymensingh, Comilla"),
       ("HYB_TINPATA10", "এইচ-০৯৪ ও এইচ-১২৮", "Mymensingh, Comilla, Rajshahi"),
       ("HYB_TINPATA40", "এইচ-০৯৫ ও এইচ-১২২", "Dhaka, Mymensingh, Comilla, Jessore, Rajshahi"),
       ("HYB_TINPATASUPER", "এইচ-১১২ ও এইচ-১৫৩", "Mymensingh, Comilla"),
       ("HYB_DOYELHTM202", "এইচ-০৯৬ ও এইচ-১৩০", "Mymensingh, Comilla"),
       ("HYB_MAYNAHTM303", "এইচ-১১১ ও এইচ-১৩১", "Dhaka, Mymensingh, Comilla, Rajshahi"),
       ("HYB_LP70", "এইচ-০৯৭ ও এইচ-১৩৫", "Mymensingh, Comilla, Jessore"),
       ("HYB_ACI1", "এইচ-১০১ ও এইচ-১২৭", "Mymensingh, Comilla, Jessore"),
       ("HYB_ACI2", "এইচ-১০৩ ও এইচ-১২৩", "Mymensingh, Comilla, Jessore, Rajshahi"),
       ("HYB_JAGORON3", "এইচ-১০২ ও এইচ-১৪২", "Mymensingh, Comilla, Jessore"),
       ("HYB_JAGORON2", "এইচ-১০৬ ও এইচ-১২৯", "Dhaka, Mymensingh, Comilla, Jessore, Rangpur")]
for k, sub, reg in T60:
    note = "60th meeting agenda 9 table: 18 hybrids of 10 companies registered region-wise, provisionally and with conditions (TC 53rd special); trial codes in table row"
    if k == "HYB_TAJ2":
        note += "; table prints the name garbled as 'ঞঅঔ-১ (এজঅ-৩)' (TAJ-1 (GRA-3)); matched to Taj-2 (GRA-3) by code and position"
    if k == "HYB_JAGORON3":
        note += "; footnote: BW001 (Jagoron-3) developed in Bangladesh by BRAC, so 'provisional' does not apply"
    D.append((60, k, "new", sub, reg, note))
D += [
    (64, "HYB_JAGORON2", "extension", "সিদ্ধান্ত্ম: রাজশাহী অঞ্চলসহ সারা দেশে বর্যাকের এইচবি-৮", "nationwide incl. Rajshahi", "provisional registration extended to the whole country"),
]
T64 = [("HYB_LP106", "খ.চ ১০৬ হাইব্রিড জাতটি", "Mymensingh, Comilla, Rajshahi", ""),
       ("HYB_SURMA4", "ঐ.জ-৪২২ (ঝঁৎসধ-৪)", "Mymensingh, Comilla, Jessore", ""),
       ("HYB_KRISHAN2", "ঝ-২ই (কৎরংযধহ-১২)", "Mymensingh, Comilla, Rajshahi", "minutes print the trade name as 'Krishan-12' (Bijoy-garbled Latin 'কৎরংযধহ-১২'); MoA list 'এস-২বি(কৃষাণ-২)'"),
       ("HYB_AGRONI7", "ঐজগ-০১ (অমৎহর-৭)", "Mymensingh, Comilla", ""),
       ("HYB_SWARATHI14", "ঐজগ-০২ (ঝযধৎধঃযর-১৪) হাইব্রিড জাতটি ময়মনসিংহ ও কুমিলস্না অঞ্চলে চাষাবাদের", "Mymensingh, Comilla", ""),
       ("HYB_RUPSHIBANGLA1", "কামাল সীড কোং লিঃ", "Mymensingh, Comilla", "minutes name the applicant 'কামাল সীড কোং লিঃ'; MoA list developer is গেটকো এগ্রোভিশন লিঃ"),
       ("HYB_ALORON2", "ঐই-০৯ (অষষড়ৎধহ-২)", "Mymensingh, Comilla, Rajshahi", ""),
       ("HYB_SUPREMEHYBRID5", "ঝঁঢ়বৎবসব ঐুনৎরফ-৫ (ঐববৎধ-৫) হাইব্রিড জাতটি ময়মনসিংহ ও কুমিলস্না", "Mymensingh, Comilla", ""),
       ("HYB_MADHUMATI2", "ডইজ-২ (গড়ফযড়সড়ঃর-২) হাইব্রিড জাতটি ময়মনসিংহ ও কুমিলস্না", "Mymensingh, Comilla", ""),
       ("HYB_MANIK2", "ঐএ-২০২ (গধহরশ-২)", "Mymensingh, Comilla, Rajshahi", ""),
       ("HYB_MADHUMATI5", "ডইজ-৫ (গড়ফযড়সড়ঃর-৫)", "Mymensingh, Comilla, Jessore", ""),
       ("HYB_LP05", "খ.চ.০৫ হাইব্রিড জাতটি ময়মনসিংহ ও কুমিলস্না", "Mymensingh, Comilla", "")]
for k, sub, reg, n in T64:
    D.append((64, k, "new", sub, reg, "agenda 8: 14 Boro hybrids, provisional registration on TC 57th recommendation" + ("; " + n if n else "")))
D += [
    (64, "HYB_SONARBANGLA6", "extension", "ঐঞগ-৪ (সোনার বাংলা-৬) হাইব্রিড জাতটি রাজশাহী", "Rajshahi", "re-trialled; previously Dhaka, Mymensingh, Comilla, Jessore; NOT in the MoA list meeting column"),
    (64, "HYB_HIRA2", "extension", "ঐঝ-২৭৩ (ঝঁঢ়ৎবসব ঐুনৎরফ-২) হাইব্রিড জাতটি যশোর", "Jessore", "re-trialled; previously Dhaka, Mymensingh, Comilla, Rajshahi; NOT in the MoA list meeting column (see P2A)"),
    (67, "HYB_ARIZETEJ", "new", "এ্যারাইজঞগ তেজ (৯৬১১০)", "Jessore, Rajshahi", ""),
    (67, "HYB_JAMUNAQRD3", "new", "যমুনা (ছউজ ৩)", "Mymensingh, Comilla, Jessore, Rajshahi", ""),
    (67, "HYB_HIRA6", "new", "হীরা-৬ (ঐঝ ৪৮)", "Dhaka, Mymensingh, Rangpur", "MoA list region 'পুনঃ ট্রায়ালের মাধ্যমে সকল অঞ্চল'"),
    (67, "HYB_HIRA4", "new", "হীরা -৪ (ঐঝছ ১)", "Comilla, Jessore, Rajshahi", ""),
    (67, "HYB_LILY1", "new", "লিলি-১ (ঈঘজ ৫১০৪) হাইব্রিড জাতটি ময়মনসিংহ", "Mymensingh, Comilla, Jessore, Rajshahi", ""),
    (67, "HYB_RAJKUMARGH14", "new", "রাজকুমার (এঐ-১৪)", "Mymensingh, Comilla, Jessore, Rajshahi", "applicant printed as এসিআই ফরমোলেশন লিঃ"),
    (67, "HYB_SAMPAD93024", "new", "সম্পদ (৯৩০২৪)", "Mymensingh, Jessore", "applicant printed as এসিআই ফরমোলেশন লিঃ"),
    (67, "HYB_FALONGH12", "new", "ফলন (এঐ-১২)", "Comilla, Jessore, Rajshahi", "applicant printed as এসিআই এগ্রো কেমিক্যালস লিঃ"),
    (67, "HYB_BUMPER3", "new", "নিপা ট্রেডিং ইন্টারন্যাশনাল লিঃ এর হাইব্রিড জাতটির সংশোধিত নাম", "Rajshahi, Jessore", "conditional: registration to be given once a revised name is received (name not printed); matched to MoA row 53 'টিকে-৬ (বাম্পার-৩)' (Nipa Trading, 67th, Jessore & Rajshahi)"),
    (67, "HYB_SERABRS696", "new", "এফেক্স ক্রাপ্ট লিঃ এর সেরা", "Mymensingh, Comilla, Rajshahi, Rangpur", ""),
    (67, "HYB_JHALOKAGROG1", "new", "এগ্রো জি-১ (ঊঅখ-৯২০১) হাইব্রিড জাতটি ময়মনসিংহ ও কুমিলস্না", "Mymensingh, Comilla", "code printed EAL-9201 (Bijoy-garbled)"),
    (67, "HYB_BIJLIAGROG2", "new", "এগ্রো জি-২ (ঊঅখ-৯২০২) হাইব্রিড জাতটি ময়মনসিংহ ও যশোর", "Mymensingh, Jessore", "wording 'নিবন্ধনের জন্য সুপারিশ করা' (recommended for registration); code EAL-9202"),
    (67, "HYB_PANNA1", "new", "পান্না-১ (ঈএঝঈ-১)", "Mymensingh, Jessore, Rangpur", ""),
    (67, "HYB_MADHUMATI2", "extension", "পূনঃ ট্রায়ালকৃত ডইজ-২ (গড়ফযঁসড়ঃর-২) হাইব্রিড জাতটি যশোর", "Jessore", "re-trialled; previously Mymensingh, Comilla; NOT in the MoA list meeting column"),
    (67, "HYB_MADHUMATI5", "extension", "পূনঃ ট্রায়ালকৃত ডইজ-২ (গড়ফযঁসড়ঃর-৫)", "Rajshahi", "code printed WBR-2 but trade name Modhumoti-5 and prior regions (Mymensingh, Comilla, Jessore) match Madhumati-5; NOT in the MoA list meeting column"),
    (67, "HYB_AGRONI7", "extension", "ঐজগ-০১ (অমৎধহর-৭) হাইব্রিড জাতটি যশোর", "Jessore", "re-trialled; wording 'ছাড়করণের অনুমোদন'; NOT in the MoA list meeting column"),
    (67, "HYB_SWARATHI14", "extension", "পূনঃ ট্রায়ালকৃত ঐজগ-০২ (ঝযধৎধঃযর-১৪) হাইব্রিড জাতটি যশোর", "Jessore", "re-trialled; NOT in the MoA list meeting column"),
    (67, "HYB_CHAMAK1", "new", "ঞণ ১০২ (ঈযধসধশ-১)", "Comilla, Jessore", "re-trialled entry; wording 'ছাড়করণের অনুমোদন'"),
    (67, "HYB_SUPREMEHYBRID5", "extension", "পূনঃ ট্রায়ালকৃত ঝঁঢ়ৎবসব ঐুনৎরফ-৫ (ঐববৎধ-৫) হাইব্রিড জাতটি যশোর", "Jessore", "re-trialled; NOT in the MoA list meeting column"),
    (67, "HYB_ACI1", "extension", "অঈও-১(ঞঝঝ-৬৪)", "Rajshahi", "re-trialled; code TSS-64 (garbled); NOT in the MoA list meeting column"),
    (67, "HYB_LP05", "extension", "পূনঃ ট্রায়ালকৃত খ.চ.০৫", "Rajshahi", "re-trialled; NOT in the MoA list meeting column"),
    (67, "BRRI_HYBRID2", "new", "ব্রি হাইব্রিড ধান-২ জাতটিকে ঢাকা", "Dhaka, Comilla, Jessore, Rajshahi", "'উদ্ভাবিত' by BRRI; wording 'নিবন্ধিকরণের অনুমোদন দেয়া হলো' (registration)"),
    (67, "HYB_SL8H", "new", "এসএল ৮-এইচ হাইব্রিড জাতটিকে", "Comilla, Jessore, Mymensingh", "BADC-produced; registration"),
    (70, "BRRI_HYBRID3", "new", "ব্রি হাইব্রিড ধান-৩ জাতটি কুমিলস্না", "Comilla, Rajshahi", "wording 'নিবন্ধনের জন্য ছাড়করণ করা হলো'; CONFLICT: MoA list region 'ঢাকা ও রাজশাহী'"),
    (70, "HYB_MALOTI8", "new", "মালতি-৮ (ডইজ-৮)", "Comilla, Jessore, Rajshahi", ""),
    (70, "HYB_CHINAKING2", "new", "চায়না কিং-২", "Comilla, Jessore, Rajshahi", ""),
    (70, "HYB_BRAC5", "new", "বর্যাক এর বর্যাক-৫ (শক্তি-২)", "Comilla, Jessore", ""),
    (70, "HYB_HRM604", "new", "ঐজগ-৬০৪(গঝ-০১)", "Comilla, Jessore, Rajshahi", ""),
    (70, "HYB_GOLDEN1", "new", "গোল্ডেন-১ হাইব্রিড জাতটি", "Mymensingh, Comilla, Jessore", ""),
    (70, "HYB_BRAC6", "new", "বর্যাক এর বর্যাক-৬ (শক্তি-৩)", "Comilla, Jessore", ""),
    (70, "HYB_SACHCHALRN001", "new", "সচ্চল (জঘ-০০১)", "Comilla, Jessore", ""),
    (70, "HYB_SHANKAR3", "new", "শংকর-৩ (ঐবলরধ-৩০৩)", "Comilla, Jessore, Rajshahi", ""),
    (70, "HYB_MANGALHEJIA909", "new", "মঙ্গল (ঐবলরধ-৯০৯)", "Comilla, Rangpur", ""),
    (70, "HYB_LILY10", "new", "লিলি-১০ (ঈঘ-৮১০১)", "Mymensingh, Comilla, Jessore", ""),
    (70, "HYB_LILY1", "extension", "পুনঃ ট্রায়ালকৃত লিলি-১ (ঈঘজ-৫১০৪)", "Dhaka, Rangpur", "re-trialled; NOT in the MoA list meeting column"),
    (70, "HYB_MANIK2", "extension", "পুনঃ ট্রায়ালকৃত মানিক-২", "Dhaka, Jessore", "re-trialled; NOT in the MoA list meeting column"),
    (70, "HYB_HIRA6", "extension", "পুনঃ ট্রায়ালকৃত হাইব্রিড হীরা-৬", "Comilla, Jessore, Rajshahi", "re-trialled; NOT in the MoA list meeting column"),
    (70, "HYB_ROPABRS694", "new", "পুনঃ ট্রায়ালকৃত ফলন-২ (ইজঝ-৬৯৪)", "Mymensingh, Comilla, Jessore, Rajshahi, Rangpur", "printed as 'ফলন-২ (BRS-694)' (MoA row 61 'রোপা(ফলন-২)বিআরএস-৬৯৪'); wording says re-trialled but no earlier registration found"),
    (70, "HYB_SERABRS696", "extension", "পুনঃ ট্রায়ালকৃত সেরা", "Dhaka, Jessore", "re-trialled; applicant printed এপেক্স লেদার ক্রাপ্ট লিঃ; NOT in the MoA list meeting column"),
    (70, "HYB_JHALOKAGROG1", "extension", "পুনঃ ট্রায়ালকৃত এগ্রোজি-১", "Dhaka, Jessore", "re-trialled; NOT in the MoA list meeting column"),
    (70, "HYB_BIJLIAGROG2", "extension", "পুনঃ ট্রায়ালকৃত এগ্রোজি-২", "Dhaka, Comilla, Rangpur", "re-trialled; NOT in the MoA list meeting column"),
    (70, "HYB_ARIZETEJ", "extension", "পুনঃ ট্রায়ালকৃত অৎরল ঞধল", "Mymensingh, Rangpur", "re-trialled; NOT in the MoA list meeting column"),
    (70, "HYB_ACI2", "extension", "পুনঃ ট্রায়ালকৃত অঈও-২", "Rangpur", "re-trialled; NOT in the MoA list meeting column"),
    (70, "HYB_ARIZEDHANIH07002", "new", "পুনঃ ট্রায়ালকৃত অৎরল উযধহর", "Mymensingh, Comilla, Rajshahi, Rangpur", "printed 'Arij Dhani (H-07002)' (garbled Latin)"),
    (70, "HYB_MADHUMATI2", "extension", "ডইজ-২ (গড়ফযঁসড়ঃর ২) হাইব্রিড জাতটি রাজশাহী ও রংপুর", "Rajshahi, Rangpur", "re-trialled; NOT in the MoA list meeting column"),
    (70, "HYB_HIRA4", "extension", "ঐুনৎরফ-৪ (ঐববৎধ-৪)", "Mymensingh", "re-trialled; NOT in the MoA list meeting column"),
    (72, "BRRI_HYBRID4", "new", "(১) বাংলাদেশ ধান গবেষণা ইনস্টিটিউট কতৃর্ক উদ্ভাবিত ব্রি হাইব্রিড ধান-৪", "Comilla, Mymensingh", "wording 'নিবন্ধনের জন্য ছাড়করণ করা হলো' (Aman trials 2008-09, 2009-10)"),
    (72, "HYB_HIRA10", "new", "হীরা-১০ (ঝঐউ ৪১) হাইব্রিড জাতটি ময়মনসিংহ", "Mymensingh, Rajshahi", ""),
]
T73 = [("HYB_AGOMONIJBS174", "আগমনী (ঔইঝ-১৭-৪) হাইব্রিড জাতটি ময়মনসিংহ", "Mymensingh, Chittagong", ""),
       ("HYB_RADARNK5017", "রাডার (ঘক ৫০১৭)", "Mymensingh, Chittagong", ""),
       ("HYB_MONIHAR5", "মনিহার-৫ (খঊ-০০৮)", "Mymensingh, Chittagong, Jessore", ""),
       ("HYB_MONIHAR6", "মনিহার-৬ (খঊ-০২১)", "Mymensingh, Chittagong, Jessore, Rajshahi, Rangpur", ""),
       ("HYB_BALIA1", "বালিয়া-১ (ঔইঝ-১৭-৩)", "Dhaka, Mymensingh, Chittagong, Jessore, Rangpur", "applicant নদার্ন এগ্রিকালচারাল এন্ড ইন্ডাষ্ট্রিয়াল কোং লিঃ; MoA list developer পারটেক্স এগ্রো লিঃ; CONFLICT region: MoA list has Rajshahi, minutes Rangpur"),
       ("HYB_BALIA2", "বালিয়া-২ (ঔইঝ-১৭-১)", "Mymensingh, Chittagong, Jessore, Rangpur", "applicant নদার্ন এগ্রিকালচারাল এন্ড ইন্ডাষ্ট্রিয়াল কোং লিঃ; MoA list developer পারটেক্স এগ্রো লিঃ"),
       ("HYB_NAFCO108", "নাফকো-১০৮ (ছ ১০৮)", "Mymensingh, Chittagong, Rajshahi", ""),
       ("HYB_SAFALYA1", "সাফল্য-১ (ঔকজঐ-৪০১)", "Mymensingh, Chittagong", ""),
       ("HYB_MITALI12", "মিতালী-১২ (ঐঝঘ-২)", "Mymensingh, Jessore", ""),
       ("HYB_RUPALIHE88", "(ঞ) আয়শা আবেদ ফাউন্ডেশন এর রূপালী (ঐঊ-৮৮)", "Dhaka, Chittagong, Jessore", "")]
for k, sub, reg, n in T73:
    D.append((73, k, "new", sub, reg, "decision wording 'নিবন্ধনের জন্য সুপারিশ করা হলো'; 10 varieties may each import 15 t seed this year" + ("; " + n if n else "")))
D += [
    (75, "HYB_ARIZEDHANIH07002", "extension", "অ্যারাইজ ধানী (এইচ ০৭০০২) জাতটি", "Mymensingh, Chittagong, Jessore, Rajshahi", "Aman-season registration (provisional, conditional) on TC 66th recommendation"),
    (75, "HYB_MUKTI1", "new", "মুক্তি-১ (ঐই ১২) জাতটি", "Mymensingh, Jessore, Rajshahi", "Aman-season registration (provisional, conditional) on TC 66th recommendation"),
]
T75 = [("HYB_SURAFLHR014", "সুরা (ঋখঐজঙ১৪)", "Mymensingh, Chittagong, Jessore"),
       ("HYB_MALIK1", "মালিক-১ (ঋখ-২০০০-৬)", "Mymensingh, Chittagong, Jessore"),
       ("HYB_BELI1", "বেলী-১ (ইঅ-১)", "Mymensingh, Chittagong"),
       ("HYB_CJY527", "সিজেওয়াই-৫২৭ (ঈঔণ-৫২৭)", "Mymensingh, Chittagong"),
       ("HYB_RUPALI7", "রূপালী-৭ (এই-০১০২)", "Mymensingh, Chittagong, Jessore, Rangpur"),
       ("HYB_JANAKRAJSQR6", "জনকরাজ (ঝছজ-৬)", "Mymensingh, Chittagong"),
       ("HYB_NABINIS1", "নবীন (ওঝ-১)", "Mymensingh, Chittagong, Rajshahi"),
       ("HYB_DURBARIS2", "দূবার্র (ওঝ-২)", "Mymensingh, Chittagong"),
       ("HYB_PARTEXHYBRID4", "পারটেক্স হাইব্রিড-৪ (ঔকজঐ-১২২০)", "Mymensingh, Chittagong, Jessore"),
       ("HYB_ALPHA2", "হাইব্রিড আলফা-২", "Mymensingh, Chittagong")]
for k, sub, reg in T75:
    D.append((75, k, "new", sub, reg, "agenda 4: Boro hybrids registered on TC 67th recommendation"))
D += [
    (75, "HYB_SUBARNA3RH664", "new", "সুবণর্-৩ (জঐ-৬৬৪)", "Mymensingh, Jessore",
     "Supreme Seed 'সুবর্ণ-৩ (RH-664)' registered at the 75th meeting; NO matching row in the MoA 2026 list (minutes-only hybrid)"),
    (75, "HYB_AGOMONIJBS174", "extension", "পুনঃ ট্রায়ালকৃত আগমনী", "Jessore", "re-trialled; NOT in the MoA list meeting column"),
    (75, "HYB_BRAC5", "extension", "পুনঃ ট্রায়ালকৃত শক্তি-২ (বর্যাক-৫)", "Dhaka, Mymensingh, Rangpur", "re-trialled; NOT in the MoA list meeting column"),
    (75, "HYB_BRAC6", "extension", "পুনঃ ট্রায়ালকৃত শক্তি-৩ (বর্যাক-৬)", "Rangpur", "re-trialled; NOT in the MoA list meeting column"),
    (75, "HYB_ALORON2", "extension", "পুনঃ ট্রায়ালকৃত আলোড়ন-২", "Jessore, Rangpur", "re-trialled; NOT in the MoA list meeting column"),
    (75, "HYB_RUPALIHE88", "extension", "পুনঃ ট্রায়ালকৃত রূপালী (ঐঊ-৮৮)", "Rangpur", "re-trialled; NOT in the MoA list meeting column"),
    (75, "HYB_MEGHNAHE25", "new", "পুনঃ ট্রায়ালকৃত মেঘনা (ঐঊ-২৫)", "Dhaka, Chittagong, Jessore, Rangpur", "printed as re-trialled; no earlier registration found"),
    (75, "HYB_RUPSHIBANGLA1", "extension", "পুনঃ ট্রায়ালকৃত রূপসী বাংলা-১", "Dhaka", "re-trialled; applicant গেটকো এগ্রোভিশন লিঃ"),
]

if __name__ == "__main__":
    nfd = lambda x: unicodedata.normalize("NFD", x)
    lines = [nfd(l) for l in TXT.read_text(encoding="utf-8").splitlines()]
    page_of, p = [], 0
    for l in lines:
        m = re.match(r"=== page (\d+)", l)
        if m:
            p = int(m.group(1))
        page_of.append(p)
    # meeting sections
    heads = [(i, int(m.group(1).translate(str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789"))))
             for i, l in enumerate(lines) for m in [re.search(nfd(r"বীজ বোডের্র ([০-৯]+)তম সভার কাযির্ববরণী\s*$"), l)] if m and not l.startswith(nfd("আলোচ্যসূচী"))]
    def mtg_of(i):
        return max([m for j, m in heads if j <= i], default=None)
    out, used = [], set()
    for mt, key, kind, sub, reg, note in D:
        sub = nfd(sub)
        own = [i for i in range(len(lines)) if sub in lines[i] and mtg_of(i) == mt]
        span = [i for i in range(len(lines) - 1) if sub in lines[i] + chr(10) + lines[i + 1] and mtg_of(i) == mt]
        hits = own or span
        if not hits:
            raise SystemExit(f"not found: {mt} {key} {sub}")
        i = hits[-1]  # decisions follow the discussion text
        used.add((mt, sub))
        q = " ".join(x.strip() for x in lines[i:i + 3])[:300]
        out.append(dict(meeting=mt, key=key, kind=kind, page=page_of[i], line=i + 1, quote=q, regions_en=reg, notes=note))
    with open(ROOT / "04_working/_F3H_r5_decisions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(len(out), "decisions;", sum(1 for o in out if o["kind"] == "extension"), "extensions")
