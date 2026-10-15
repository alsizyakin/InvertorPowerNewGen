"""C_gs of the LS (C102/C103, C106/C107, C110/C111) in the GND strips next to R_g / R_gs. For the upper ones
2-3 strip GND vias are moved inside the same strip (count and near-S count unchanged). Positions and via moves
come from place_cgs.py / place_cgs2.py (L/cgs.json, L/cgs2.json); gate stubs are routed here."""
import sys, json, math
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
import geom, router
fn = sys.argv[1]; low = json.load(open(sys.argv[3])); up = json.load(open(sys.argv[4]))
near = lambda a, b, t=0.03: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t
B = Board(fn)
for ref, d in up.items():
    for (a, b) in d["moves"]:
        B.del_vias(lambda v, a=a: v["net"] == "GND" and near((v["x"], v["y"]), tuple(a)))
        B.add_via(tuple(b), "GND")
    B.move_fp(ref, *d["pos"])
for ref, (pos, route, gnet) in low.items():
    B.move_fp(ref, *pos)
    B.track([tuple(p) for p in route], 0.3, "F.Cu", gnet)
B.save()
G = geom.Board(fn); B = Board(fn)
for ref, d in up.items():
    f = G.fps[ref]; gp = [p for p in f.placed()[0] if p["net"] == d["gnet"]][0]
    best = None
    for a in d["anchors"]:
        rw = (min(a[0], gp["x"]) - 1.5, min(a[1], gp["y"]) - 1.5, max(a[0], gp["x"]) + 1.5, max(a[1], gp["y"]) + 1.5)
        p = router.Router(G, "F.Cu", rw).route((gp["x"], gp["y"]), tuple(a), d["gnet"], 0.3)
        if p:
            L = sum(math.hypot(p[i+1][0]-p[i][0], p[i+1][1]-p[i][1]) for i in range(len(p)-1))
            if best is None or L < best[0]: best = (L, p)
    print(ref, "gate route", best)
    if best: B.track(best[1], 0.3, "F.Cu", d["gnet"])
B.save()
print("lay_CGS applied")
# GND pads of C107 / C111 sit below the end of the strip pour: own GND via each (viaspot.py)
B = Board(fn)
B.track([(136.9, 91.0625), (136.9, 92.0)], 0.4, "F.Cu", "GND"); B.add_via((136.9, 92.0), "GND")
B.track([(153.4, 91.3625), (154.25, 91.0)], 0.4, "F.Cu", "GND"); B.add_via((154.25, 91.0), "GND")
B.save()
print("C_gs GND vias added")
