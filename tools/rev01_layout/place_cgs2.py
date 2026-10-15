"""Upper-LS C_gs: place the cap in the GND strip next to R_g / R_gs, relocating the strip GND vias that would sit
under or too close to its pads to free spots of the same strip (count and the near-S count preserved).
Usage: place_cgs2.py board tools out.json"""
import sys, json, math, copy
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
import geom, router
G = geom.Board(sys.argv[1])
STRIP = {"C": (116.2, 121.2), "B": (134.2, 138.2), "A": (151.2, 155.2)}
SPADS = {"C": "Q8", "B": "Q9", "A": "Q11"}
JOBS = [("C102", "C", "Net-(C102-Pad1)", [(120.09, 81.5), (118.25, 79.16), (119.85, 79.41)], (116.4, 79.4, 122.4, 84.6)),
        ("C106", "B", "Net-(C106-Pad1)", [(137.09, 81.5), (135.25, 79.16), (136.85, 79.41)], (134.3, 79.4, 139.4, 84.6)),
        ("C110", "A", "Net-(C110-Pad1)", [(154.09, 81.5), (152.25, 79.16), (153.85, 79.41)], (151.3, 79.4, 156.4, 84.6))]
VR = 0.3
def rect(p): return (p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2)
allpads = [(r, p, f.layer) for r, f in G.fps.items() for p in f.placed()[0]]
def spot_ok(x, y, strip, keep_vias, newpads):
    if not (strip[0] + 0.45 <= x <= strip[1] - 0.45): return False
    for r, p, lay in allpads:
        if abs(p["x"] - x) > 3 or abs(p["y"] - y) > 3: continue
        d = geom.d_pt_rect(x, y, rect(p)) - VR
        if d < (0.0 if p["net"] == "GND" else 0.2): return False
        if p["net"] == "GND" and not p["tht"] and d < 0.05: return False     # no via in/at a GND SMD pad
    for p in newpads:
        d = geom.d_pt_rect(x, y, rect(p)) - VR
        if d < (0.05 if p["net"] == "GND" else 0.2): return False
    for v in keep_vias:
        if math.hypot(v["x"] - x, v["y"] - y) < 0.5 - 1e-6: return False
    for s in G.segs:
        if s["net"] == "GND": continue
        if max(s["x1"], s["x2"]) < x - 2 or min(s["x1"], s["x2"]) > x + 2 or max(s["y1"], s["y2"]) < y - 2 or min(s["y1"], s["y2"]) > y + 2: continue
        if geom.d_seg_rect(s["x1"], s["y1"], s["x2"], s["y2"], (x, y, x, y)) - s["w"]/2 - VR < 0.2: return False
    return True
res = {}
for ref, ph, gnet, anchors, win in JOBS:
    strip = STRIP[ph]
    spads = [p for p in G.fps[SPADS[ph]].placed()[0] if p["net"] == "GND" and not p["tht"]]
    nearS = lambda x, y: min(geom.d_pt_rect(x, y, rect(p)) for p in spads) <= 2.5
    svias = [v for v in G.vias if v["net"] == "GND" and strip[0] - 0.3 < v["x"] < strip[1] + 0.3 and 72 < v["y"] < 93.5]
    G2 = copy.copy(G); G2.vias = [v for v in G.vias if v not in svias]; G2._pc = None
    f = G.fps[ref]; best = None
    for rot in (0, 90, 180, 270):
        x = win[0]
        while x <= win[2] + 1e-9:
            y = win[1]
            while y <= win[3] + 1e-9:
                if not geom.Board.check_fast(G2, ref, x, y, rot):
                    pads, _ = f.placed(x, y, rot)
                    gp = [p for p in pads if p["net"] == gnet][0]; gn = [p for p in pads if p["net"] == "GND"][0]
                    if strip[0] + 0.3 <= gn["x"] <= strip[1] - 0.3:
                        d = min(math.hypot(gp["x"]-a[0], gp["y"]-a[1]) for a in anchors)
                        bad = [v for v in svias if any(geom.d_pt_rect(v["x"], v["y"], rect(p)) - VR < (0.05 if p["net"] == "GND" else 0.2) for p in pads)]
                        if d < 2.6 and len(bad) <= 4:
                            key = (len(bad), d)
                            if best is None or key < best[0]: best = (key, (round(x, 2), round(y, 2), rot), bad, pads)
                y += 0.05
            x += 0.05
    if not best: print(ref, "no candidate"); continue
    (nbad, d), pos, bad, pads = best
    keep = [v for v in svias if v not in bad]; moves = []
    for v in bad:
        ns = nearS(v["x"], v["y"]); cand = None
        for dy in [i * 0.25 for i in range(-24, 25)]:
            for dx in [i * 0.25 for i in range(-12, 13)]:
                x, y = v["x"] + dx, v["y"] + dy
                if ns and not nearS(x, y): continue
                if spot_ok(x, y, strip, keep + [{"x": m[1][0], "y": m[1][1]} for m in moves], pads):
                    dd = math.hypot(dx, dy)
                    if cand is None or dd < cand[0]: cand = (dd, (round(x, 3), round(y, 3)))
        if cand is None: break
        moves.append(((v["x"], v["y"]), cand[1]))
    print(ref, pos, "gate dist", round(d, 2), "moved vias", moves, "of", len(bad), flush=True)
    res[ref] = {"pos": pos, "moves": moves, "nbad": len(bad), "gnet": gnet, "anchors": anchors}
json.dump(res, open(sys.argv[3], "w"))
