import requests, time, sys, os
UA = "Mozilla/5.0 (research archive; contact via https://github.com/kushal-satya/bgd-rice-variety-register) python-requests"
doms = sys.argv[1:]
os.makedirs("02_raw/_robots", exist_ok=True)
for d in doms:
    for scheme in ("https", "http"):
        try:
            r = requests.get(f"{scheme}://{d}/robots.txt", headers={"User-Agent": UA}, timeout=30, verify=False)
            print(f"== {d} [{scheme}] status={r.status_code} ctype={r.headers.get('content-type')} len={len(r.text)}")
            print(r.text[:1500])
            if r.status_code == 200:
                open(f"02_raw/_robots/{d}.txt", "w", encoding="utf-8").write(r.text)
            else:
                open(f"02_raw/_robots/{d}.txt", "w", encoding="utf-8").write(f"# HTTP {r.status_code} at {scheme}://{d}/robots.txt\n")
            break
        except Exception as e:
            print(f"== {d} [{scheme}] ERROR {e}")
            open(f"02_raw/_robots/{d}.txt", "w", encoding="utf-8").write(f"# unreachable: {e}\n")
        time.sleep(2)
    time.sleep(2)
