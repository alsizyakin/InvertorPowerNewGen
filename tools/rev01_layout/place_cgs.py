"""Find places for the LS C_gs (gate pad routed to the gate net on F.Cu, GND pad on the GND strip pour, no via
under any pad, no via removed). Usage: place_cgs.py board tools out.json"""
import sys, json, math
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
import geom, router
G = geom.Board(sys.argv[1])
STRIP = {"C": (116.2, 121.2), "B": (134.2, 138.2), "A": (151.2, 155.2)}
JOBS = [("C102", "C", "Net-(C102-Pad1)", [(120.09, 81.5), (118.25, 79.16)], (116.3, 79.6, 123.0, 84.2)),
        ("C103", "C", "Net-(C103-Pad1)", [(120.09, 90.25), (118.25, 87.91)], (116.3, 88.4, 123.0, 93.0)),
        ("C106", "B", "Net-(C106-Pad1)", [(137.09, 81.5), (135.25, 79.16)], (134.0, 79.6, 140.0, 84.2)),
        ("C107", "B", "Net-(C107-Pad1)", [(135.72, 90.09), (135.25, 87.91)], (134.0, 88.4, 140.0, 93.0)),
        ("C110", "A", "Net-(C110-Pad1)", [(154.09, 81.5), (152.25, 79.16)], (151.0, 79.6, 157.0, 84.2)),
        ("C111", "A", "Net-(C111-Pad1)", [(152.25, 89.59), (152.25, 87.91)], (151.0, 88.4, 157.0, 93.0))]
def via_in_pad(pads):
    for p in pads:
        r = (p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2)
        for v in G.vias:
            if geom.d_pt_rect(v["x"], v["y"], r) < geom._via_r(v) - 1e-6: return True
    return False
res = {}
for ref, ph, gnet, anchors, win in JOBS:
    f = G.fps[ref]; best = None
    for rot in (0, 90, 180, 270):
        x = win[0]
        while x <= win[2] + 1e-9:
            y = win[1]
            while y <= win[3] + 1e-9:
                if not G.check_fast(ref, x, y, rot):
                    pads, _ = f.placed(x, y, rot)
                    gp = [p for p in pads if p["net"] == gnet][0]; gn = [p for p in pads if p["net"] == "GND"][0]
                    if STRIP[ph][0] + 0.3 <= gn["x"] <= STRIP[ph][1] - 0.3 and not via_in_pad(pads):
                        d = min(math.hypot(gp["x"]-a[0], gp["y"]-a[1]) for a in anchors)
                        if d < 3.2 and (best is None or d < best[0]): best = (d, (round(x, 2), round(y, 2), rot))
                y += 0.1
            x += 0.1
    print(ref, best, flush=True)
    if best:
        x, y, rot = best[1]; pads, _ = f.placed(x, y, rot)
        gp = [p for p in pads if p["net"] == gnet][0]
        a = min(anchors, key=lambda a: math.hypot(gp["x"]-a[0], gp["y"]-a[1]))
        rw = (min(a[0], gp["x"]) - 1.5, min(a[1], gp["y"]) - 1.5, max(a[0], gp["x"]) + 1.5, max(a[1], gp["y"]) + 1.5)
        p = router.Router(G, "F.Cu", rw).route((gp["x"], gp["y"]), a, gnet, 0.3, moved={ref: (x, y, rot)})
        print("   route", p, flush=True)
        res[ref] = [best[1], p, gnet]
json.dump(res, open(sys.argv[3], "w"))
