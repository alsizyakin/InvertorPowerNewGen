"""Bottleneck width of GND copper in the four passages between the key block and the drivers, per layer."""
import sys, numpy as np
sys.path.insert(0, "/home/alexey/Git/KiCad/InvertorPowerNewGen/bench_2026-10-13/tools"); sys.dont_write_bytecode = True
import kpcb
from matplotlib.path import Path
PASS = {"C (notch-J1)": (116.3, 126.75), "J1-J2": (134.75, 138.75), "J2-J3": (146.75, 150.75), "A (J3-notch)": (158.75, 169.2)}
def run(fn):
    B = kpcb.load(fn); out = {}
    for lay in ("In1.Cu", "In4.Cu"):
        P = [(Path(pts), (min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)))
             for z in B["zones"] if z["net"] == "GND" for l, pts in z["fills"] if l == lay and len(pts) > 2]
        for name, (xa, xb) in PASS.items():
            xs = np.arange(xa, xb, 0.05); worst = (1e9, None)
            for y in np.arange(91.5, 101.01, 0.25):
                cand = [p for p, bb in P if bb[2] <= y <= bb[3]]
                n = sum(1 for x in xs if any(p.contains_point((x, y)) for p in cand))
                if n*0.05 < worst[0]: worst = (n*0.05, round(y, 2))
            out[(lay, name)] = worst
    return out
res = [run(f) for f in sys.argv[1:]]
for k in res[0]:
    print(f"{k[0]:7s} {k[1]:14s} " + "  ".join(f"{r[k][0]:5.2f} mm @y{r[k][1]}" for r in res))
