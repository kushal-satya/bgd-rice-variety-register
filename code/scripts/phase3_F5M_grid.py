"""F5M: detect ruled tables on a 300-dpi page PNG (numpy only).
tables(png) -> list of dict(x=[column rule x], y=[row rule y], box=(x0,y0,x1,y1))"""
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None


def _longest_runs(a, axis):
    """for each column (axis=0) / row (axis=1) of bool array a: (longest run length, start, end)"""
    if axis == 1:
        a = a.T
    H, W = a.shape
    best = np.zeros(W, int); bs = np.zeros(W, int); be = np.zeros(W, int)
    cur = np.zeros(W, int); cs = np.zeros(W, int)
    for y in range(H):
        row = a[y]
        cs = np.where(row & (cur == 0), y, cs)
        cur = np.where(row, cur + 1, 0)
        upd = cur > best
        best = np.where(upd, cur, best); bs = np.where(upd, cs, bs); be = np.where(upd, y, be)
    return best, bs, be


def _extent(col, s, e, minrun=40, maxgap=120):
    """grow the run [s,e] up/down across short breaks: accept further runs >= minrun separated by gaps <= maxgap"""
    d = np.diff(np.concatenate(([0], col.astype(np.int8), [0])))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    runs = [(a, b) for a, b in zip(st, en) if b - a >= minrun]
    lo, hi = s, e
    changed = True
    while changed:
        changed = False
        for a, b in runs:
            if a <= hi and b >= lo and (a < lo or b > hi):
                lo, hi = min(lo, a), max(hi, b); changed = True
            if b < lo and lo - b <= maxgap:
                lo = a; changed = True
            if a > hi and a - hi <= maxgap:
                hi = b; changed = True
    return int(lo), int(hi)


def _group(xs, gap):
    gs, cur = [], []
    for x in xs:
        if cur and x - cur[-1] > gap:
            gs.append(cur); cur = []
        cur.append(x)
    if cur:
        gs.append(cur)
    return gs


def tables(png, dark=150, vmin=0.12, hmin=0.30):
    im = Image.open(png).convert("L")
    a = np.asarray(im) < dark
    H, W = a.shape
    v = a.copy()
    for k in range(1, 9):                              # bridge gaps up to ~16 px in rules
        v[k:] |= a[:-k]; v[:-k] |= a[k:]
    v &= np.roll(a, 0, 0) | np.roll(a, 1, 1) | np.roll(a, -1, 1) | v   # keep
    h = a.copy()
    for k in range(1, 9):
        h[:, k:] |= a[:, :-k]; h[:, :-k] |= a[:, k:]
    vb, vs, ve = _longest_runs(v, 0)
    hb, hs, he = _longest_runs(h, 1)
    vcols = [x for x in range(W) if vb[x] >= vmin * H and 20 < x < W - 20]
    vl = []
    for g in _group(vcols, 8):
        i = g[int(np.argmax(vb[g]))]
        col = a[:, max(0, i - 6):i + 7].any(axis=1)
        y0, y1 = _extent(col, int(vs[i]), int(ve[i]))
        vl.append((int(np.mean(g)), y0, y1))
    hrows = [y for y in range(H) if hb[y] >= hmin * W and 20 < y < H - 20]
    hl = []
    for g in _group(hrows, 8):
        i = g[int(np.argmax(hb[g]))]
        hl.append((int(np.mean(g)), int(hs[i]), int(he[i])))
    # cluster vertical rules overlapping in y into tables
    vl.sort(key=lambda t: t[1])
    tabs = []
    for x, y0, y1 in vl:
        for t in tabs:
            if y0 < t["box"][3] - 30 and y1 > t["box"][1] + 30:
                t["x"].append(x); t["box"] = (min(t["box"][0], x), min(t["box"][1], y0), max(t["box"][2], x), max(t["box"][3], y1))
                break
        else:
            tabs.append({"x": [x], "box": (x, y0, x, y1)})
    out = []
    for t in tabs:
        if len(t["x"]) < 2:
            continue
        x0, y0, x1, y1 = t["box"]
        ys = [y for y, a0, a1 in hl if y0 - 15 <= y <= y1 + 15 and a0 <= x0 + 60 and a1 >= x1 - 60]
        ys = sorted(set([y0] + ys + [y1]))
        ys = [y for i, y in enumerate(ys) if i == 0 or y - ys[i - 1] > 25]
        out.append({"x": sorted(t["x"]), "y": ys, "box": (x0, y0, x1, y1)})
    return out


if __name__ == "__main__":
    import sys, time
    for p in sys.argv[1:]:
        t = time.time(); print(p, tables(p), round(time.time() - t, 1))
