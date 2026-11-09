"""F3L: render gazette pages (150 dpi) into 04_working/crops/F3L/gz_<tag>_pN.png for visual checks."""
import fitz, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
G = {"2007nsb60": "02_raw/moa/release_gazette_nsb60_2007.pdf",
     "2007nsb62": "02_raw/moa/release_gazette_nsb62_2007.pdf",
     "2009nsb68": "02_raw/moa_wayback/gazette_nsb68_2009-07-21.pdf",
     "2013-12-02": "02_raw/bgpress/moa_extra_02-Dec-2013_8154_27389.pdf",
     "2014-03-18": "02_raw/bgpress/release_notification_2014-03-18.pdf",
     "2015-01-22": "02_raw/bgpress/moa_extra_22-Jan-2015_12441_44845.pdf",
     "2016-06-02": "02_raw/sca_laws/hybrid_rice_evaluation_registration_revised_procedure_gazette.pdf",
     "2016-11-07": "02_raw/bgpress/moa_extra_07-Nov-2016_18866_13961.pdf",
     "2017-04-27": "02_raw/bgpress/moa_extra_27-Apr-2017_21223_67595.pdf",
     "2018-01-10": "02_raw/bgpress/moa_extra_10-Jan-2018_24293_98386.pdf",
     "2019-12-11": "02_raw/bgpress/moa_extra_11-Dec-2019_34659_83539.pdf",
     "2021-08-25": "02_raw/bgpress/release_notification_2021-08-25.pdf",
     "2022-06-08": "02_raw/bgpress/moa_extra_08-Jun-2022_44797_55779.pdf",
     "2025-04-17": "02_raw/bgpress/moa_extra_17-Apr-2025_57313_27596.pdf",
     "2025-07-19": "02_raw/bgpress/release_notification_2025-07-19.pdf"}
OUT = ROOT / "04_working/crops/F3L"
if __name__ == "__main__":
    for tag, f in G.items():
        d = fitz.open(ROOT / f)
        pages = range(min(d.page_count, 3)) if tag != "2016-06-02" else [1]
        for i in pages:
            o = OUT / f"gz_{tag}_p{i+1}.png"
            if not o.exists():
                d[i].get_pixmap(dpi=150).save(o)
            print(o.name, d[i].rect)
