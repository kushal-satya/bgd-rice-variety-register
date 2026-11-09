"""P2F: download WorldFish / CGIAR / secondary sources for fish strains via lib_fetch.
Dataverse: metadata JSON for both datasets; data files only if < 2 MB."""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch, get, ROOT

A = "P2F"
items = [
    ("https://digitalarchive.worldfishcenter.org/bitstream/handle/20.500.12348/177/3743_2014_Hossain.pdf",
     "worldfish/hussain_c2014_tilapia_farming_bangladesh.pdf", "Hussain, Barman, Karim, Keus (WorldFish BD) c.2014: GIFT history, BFRI Super GIFT (FS015)"),
    ("https://worldfishcenter.org/worldfish-genetic-resources-dissemination",
     "worldfish/worldfish_genetic_resources_dissemination.html", "WorldFish strains available for dissemination (FS020)"),
    ("https://worldfishcenter.org/blog/fish-genetics-year-review",
     "worldfish/worldfish_blog_fish_genetics_year_review_2015.html", "WorldFish blog 14 Dec 2015 (FS021)"),
    ("https://worldfishcenter.org/updates/faster-growing-carp-food-secure-future-reflections-workshop-khulna",
     "worldfish/worldfish_khulna_workshop_2025.html", "WorldFish Khulna workshop Sep 2025: G5 rohu on-farm trial"),
    ("https://www.frontiersin.org/journals/aquaculture/articles/10.3389/faquc.2022.1060335/full",
     "literature/frontiers_2022_g3_rohu_faquc.2022.1060335.html", "Frontiers in Aquaculture 2022 G3 rohu growth (FS022)"),
    ("https://www.fishinnovationlab.msstate.edu/newsroom/2023/08/carp-genetic-improvement-program-bangladesh-shares-g3-technology-bangladesh",
     "fishinnovationlab/fil_2023-08_cgip_shares_g3_with_bfri.html", "Fish Innovation Lab news Aug 2023: G3 to BFRI; Subarna note (FS023)"),
    ("https://www.tbsnews.net/node/679266", "news/tbs_2023-08_worldfish_g3_rohu_handed_to_bfri.html", "TBS: WorldFish G3 rohu handed over to BFRI (FS024)"),
    ("http://www.fao.org/fileadmin/user_upload/affris/docs/news/pres2/Annex_J_Quality_fish_seed_in_Bangladesh.pdf",
     "fao/fao_annexJ_quality_fish_seed_bangladesh_bfri.pdf", "BFRI slides Quality Fish Seed in Bangladesh (FS014)"),
]
for u, rel, note in items:
    try:
        print("OK", fetch(u, rel, A, note))
    except Exception as e:
        print("ERR", u, e)

for doi in ["doi:10.7910/DVN/SVNV6B", "doi:10.7910/DVN/BFV5P1"]:
    u = f"https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId={doi}"
    rel = f"dataverse/{doi.split('/')[-1]}_metadata.json"
    try:
        p = fetch(u, rel, A, f"Harvard Dataverse dataset metadata {doi} (CC BY 4.0)")
        md = json.loads((ROOT / p).read_text(encoding="utf-8"))
        files = md["data"]["latestVersion"]["files"]
        for f in files:
            df = f["dataFile"]; size = df.get("filesize", 0)
            print(doi, df["id"], df.get("filename"), size, df.get("contentType"))
            if size and size < 2_000_000:
                fu = f"https://dataverse.harvard.edu/api/access/datafile/{df['id']}?format=original"
                try:
                    print("  ->", fetch(fu, f"dataverse/{doi.split('/')[-1]}_{df.get('originalFileName', df['filename'])}", A, f"data file of {doi}"))
                except Exception as e:
                    print("  ERR", e)
    except Exception as e:
        print("ERR", doi, e)
