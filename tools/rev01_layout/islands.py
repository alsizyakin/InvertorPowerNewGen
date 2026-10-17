"""Fill pieces of GND on a layer with the number of GND vias / THT pads inside each. Usage: islands.py board [layer]"""
import sys
sys.path.insert(0, "/home/alexey/Git/KiCad/InvertorPowerNewGen/bench_2026-10-13/tools"); sys.dont_write_bytecode = True
import kpcb
from matplotlib.path import Path
B = kpcb.load(sys.argv[1]); lay = sys.argv[2] if len(sys.argv) > 2 else "In4.Cu"
def area(p): return abs(sum(p[i][0]*p[i-1][1] - p[i-1][0]*p[i][1] for i in range(len(p)))) / 2
pts = [(v["x"], v["y"]) for v in B["vias"] if v["net"] == "GND"] + [(p["x"], p["y"]) for f in B["fps"] for p in f["pads"] if p["net"] == "GND" and p["type"] == "thru_hole"]
for z in B["zones"]:
    if z["net"] != "GND": continue
    for l, poly in z["fills"]:
        if l != lay or len(poly) < 3: continue
        P = Path(poly); n = sum(P.contains_point(q) for q in pts)
        xs = [q[0] for q in poly]; ys = [q[1] for q in poly]
        print(f"  {area(poly):7.1f} mm2  vias {n:3d}  x {min(xs):.1f}..{max(xs):.1f} y {min(ys):.1f}..{max(ys):.1f}")
