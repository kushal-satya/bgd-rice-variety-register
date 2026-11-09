"""P2A: download SCA annual approved/hybrid lists (all) and NSB minutes listed in RR_sca_listing_inventory.csv
via lib_fetch (throttled, manifest-aware). Args: 'lists' | 'nsb' [meeting filter list e.g. 19-28,83,95]"""
import csv, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_fetch import fetch
ROOT = pathlib.Path(__file__).resolve().parents[1]
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
inv = list(csv.DictReader(open(ROOT / "01_discovery/_parts/RR_sca_listing_inventory.csv", encoding="utf-8-sig")))
mode = sys.argv[1]
want = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
for r in inv:
    url = r["files"].strip()
    if not url:
        print("NO FILE:", r["title"]); continue
    t = r["title"].translate(BN)
    if mode == "lists" and r["list"] in ("approved_crop_varieties", "registered_hybrid_rice"):
        fy = re.search(r"(\d{4}-\d{2})", t).group(1)
        stem = "approved_crop_varieties" if r["list"] == "approved_crop_varieties" else "registered_hybrid_rice"
        rel = f"sca/{stem}_{fy}.pdf"
    elif mode == "nsb" and r["list"] == "nsb_minutes":
        nums = [int(x) for x in re.findall(r"(\d+)", t)]
        key = f"{nums[0]}-{nums[1]}" if len(nums) == 2 else str(nums[0])
        if want and key not in want: continue
        rel = f"sca/nsb_minutes_{nums[0]:03d}-{nums[1]:03d}.pdf" if len(nums) == 2 else f"sca/nsb_minutes_{nums[0]:03d}.pdf"
    elif mode == "tc" and r["list"] == "tcnsb_minutes":
        n = int(re.findall(r"(\d+)", t)[0])
        if want and str(n) not in want: continue
        rel = f"sca/tc_minutes_{n:03d}.pdf"
    else:
        continue
    try:
        p = fetch(url, rel, agent="P2A", notes=f"SCA listing '{r['title']}' (upload date {r['publish_date_bn']})")
        print("ok", p)
    except Exception as e:
        print("FAIL", rel, e)
