"""GND connectivity over filled zones, vias, THT pads and GND tracks; reports components."""
import sys, math
sys.path.insert(0, "/home/alexey/Git/KiCad/InvertorPowerNewGen/bench_2026-10-13/tools"); sys.dont_write_bytecode = True
import kpcb
from matplotlib.path import Path
B = kpcb.load(sys.argv[1]); NET = sys.argv[2] if len(sys.argv) > 2 else "GND"
polys = []
for z in B["zones"]:
    if z["net"] != NET: continue
    for lay, pts in z["fills"]:
        if len(pts) > 2:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            area = 0.5*abs(sum(xs[i]*ys[i-1]-xs[i-1]*ys[i] for i in range(len(pts))))
            polys.append(dict(layer=lay, path=Path(pts), bb=(min(xs), min(ys), max(xs), max(ys)), area=area))
parent = list(range(len(polys)))
def find(a):
    while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b): parent[find(a)] = find(b)
def hits(x, y, layers=None):
    return [i for i, p in enumerate(polys) if (layers is None or p["layer"] in layers)
            and p["bb"][0] <= x <= p["bb"][2] and p["bb"][1] <= y <= p["bb"][3] and p["path"].contains_point((x, y))]
anchors = []
for v in B["vias"]:
    if v["net"] == NET:
        h = hits(v["x"], v["y"]); anchors.append((("via", v["x"], v["y"]), h))
for f in B["fps"]:
    for p in f["pads"]:
        if p["net"] != NET: continue
        lays = None if p["type"] == "thru_hole" else [f["layer"]]
        h = hits(p["x"], p["y"], lays); anchors.append(((f["ref"]+"."+p["name"], p["x"], p["y"]), h))
for s in B["segs"]:
    if s["net"] == NET:
        h = hits(s["x1"], s["y1"], [s["layer"]]) + hits(s["x2"], s["y2"], [s["layer"]]); anchors.append((("seg", s["x1"], s["y1"]), h))
for a, h in anchors:
    for i in h[1:]: union(h[0], i)
comps = {}
for i in range(len(polys)): comps.setdefault(find(i), []).append(i)
big = sorted(comps.values(), key=lambda c: -sum(polys[i]["area"] for i in c))
print("components:", len(big))
for c in big[:8]:
    A = sum(polys[i]["area"] for i in c)
    xs = [polys[i]["bb"] for i in c]
    bb = (min(b[0] for b in xs), min(b[1] for b in xs), max(b[2] for b in xs), max(b[3] for b in xs))
    lay = sorted({polys[i]["layer"] for i in c})
    print(f"  area {A:8.1f} mm2  polys {len(c):3d}  layers {lay}  bbox x {bb[0]:.1f}..{bb[2]:.1f} y {bb[1]:.1f}..{bb[3]:.1f}")
if len(sys.argv) > 4:
    x, y = float(sys.argv[3]), float(sys.argv[4])
    for i in hits(x, y):
        root = find(i); c = comps[root]
        print(f"point ({x},{y}) on {polys[i]['layer']}: component area {sum(polys[j]['area'] for j in c):.1f}")
