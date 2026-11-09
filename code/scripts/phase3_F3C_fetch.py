"""F3C: download CGIAR-original attribution sources once (lib_fetch, sequential)."""
from lib_fetch import fetch
B = "https://cgspace.cgiar.org/server/api/core/bitstreams/{}/content"
ITEMS = [
    ("4c4881c0-62cc-4439-8c93-10b5b096d3f8", "cgiar_lit/raitzer2015_spia_rice_1989-2009.pdf", "Raitzer et al. 2015 SPIA, CGSpace 10568/128929"),
    ("7726a055-ac07-45cd-9c0a-9b5f538c4992", "cgiar_lit/villanueva2022_irg_bangladesh.pdf", "Villanueva et al. 2022 CABI A&B 3:71, CGSpace 10568/126982"),
    ("b41442a1-2c79-4be0-90a3-f9478e8bc16a", "cgiar_lit/dikitanan2022_gfs_returns.pdf", "Dikitanan et al. 2022 GFS, CGSpace 10568/119865"),
]
for u, rel, n in ITEMS:
    print(fetch(B.format(u), rel, agent="F3C", notes=n))
