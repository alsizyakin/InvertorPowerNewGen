"""Raster overlap (0.05 mm) of copper of different nets on two adjacent layers, e.g. In4 over B.Cu, F.Cu over In1.
Usage: ovl.py board layA layB x0 y0 x1 y1 [net-substring,...]"""
import sys, collections, numpy as np
sys.path.insert(0, "/home/alexey/Git/KiCad/InvertorPowerNewGen/bench_2026-10-13/tools"); sys.dont_write_bytecode = True
import kpcb
from matplotlib.path import Path
fn, LA, LB = sys.argv[1:4]; x0, y0, x1, y1 = map(float, sys.argv[4:8]); h = 0.05
B = kpcb.load(fn)
xs = np.arange(x0, x1, h); ys = np.arange(y0, y1, h); X, Y = np.meshgrid(xs, ys); P = np.c_[X.ravel(), Y.ravel()]
def raster(lay):
    M = np.full(X.shape, "", dtype=object)
    for z in B["zones"]:
        for l, pts in z["fills"]:
            if l == lay and len(pts) > 2:
                xs_ = [p[0] for p in pts]; ys_ = [p[1] for p in pts]
                if max(xs_) < x0 or min(xs_) > x1 or max(ys_) < y0 or min(ys_) > y1: continue
                M[Path(pts).contains_points(P).reshape(X.shape)] = z["net"]
    for s in B["segs"]:
        if s["layer"] != lay: continue
        vx, vy = s["x2"]-s["x1"], s["y2"]-s["y1"]; L = vx*vx+vy*vy
        t = np.clip(((X-s["x1"])*vx+(Y-s["y1"])*vy)/L, 0, 1) if L > 0 else 0
        M[np.hypot(X-s["x1"]-t*vx, Y-s["y1"]-t*vy) <= s["w"]/2] = s["net"]
    for f in B["fps"]:
        for p in f["pads"]:
            if not (p["type"] == "thru_hole" or f["layer"] == lay): continue
            w, hh = (p["w"], p["h"]) if abs(f["rot"]) % 180 == 0 else (p["h"], p["w"])
            M[(abs(X-p["x"]) <= w/2) & (abs(Y-p["y"]) <= hh/2)] = p["net"]
    return M
A, Bm = raster(LA), raster(LB)
c = collections.Counter()
for a, b in zip(A.ravel(), Bm.ravel()):
    if a and b and a != b: c[(a, b)] += 1
want = sys.argv[8].split(",") if len(sys.argv) > 8 else None
for (a, b), n in c.most_common(400):
    if want and not any(w in a or w in b for w in want): continue
    if n*h*h >= 0.3: print(f"  {a[:24]:24s} over {b[:26]:26s} {n*h*h:6.2f} mm2")
