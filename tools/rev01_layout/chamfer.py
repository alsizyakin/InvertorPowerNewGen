"""Chamfer the 90-degree corners of the new routing at 45 degrees. For every degree-2 joint of two tracks (same
net, layer, width) not sitting on a pad or via, the corner is cut with legs c = 0.8 ... 0.2 mm (largest that keeps
0.2 mm to other-net copper on that layer: pads, vias, tracks). Usage: chamfer.py board rev0_board tools"""
import sys, math, collections, re
sys.path.insert(0, sys.argv[3]); sys.dont_write_bytecode = True
from pcbedit import Board, seg_text, SEG_RE
import geom
fn = sys.argv[1]
G = geom.Board(fn); B = Board(fn); old = Board(sys.argv[2])
key = lambda g: (g["net"], g["layer"], tuple(sorted([(round(g["x1"], 2), round(g["y1"], 2)), (round(g["x2"], 2), round(g["y2"], 2))])))
oldk = set(key(g) for g in old.segments())
segs = list(B.segments()); newids = set(g["uuid"] for g in segs if key(g) not in oldk)
ends = collections.defaultdict(list)
for g in segs:
    for e in ((g["x1"], g["y1"]), (g["x2"], g["y2"])): ends[(g["net"], g["layer"], round(e[0], 3), round(e[1], 3))].append(g)
pads = [(p, f.layer) for r, f in G.fps.items() for p in f.placed()[0]]
def on_pad_or_via(net, layer, x, y):
    for v in G.vias:
        if v["net"] == net and math.hypot(v["x"]-x, v["y"]-y) < geom._via_r(v): return True
    for p, fl in pads:
        if p["net"] != net: continue
        if not (p["tht"] or fl == layer): continue
        if abs(p["x"]-x) <= p["aw"]/2 and abs(p["y"]-y) <= p["ah"]/2: return True
    return False
def ok_seg(net, layer, a, b, w, skip):
    for p, fl in pads:
        if p["net"] == net or not (p["tht"] or fl == layer): continue
        r = (p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2)
        if geom.d_seg_rect(a[0], a[1], b[0], b[1], r) - w/2 < 0.2: return False
    for v in G.vias:
        if v["net"] == net: continue
        if geom.d_seg_rect(a[0], a[1], b[0], b[1], (v["x"], v["y"], v["x"], v["y"])) - w/2 - geom._via_r(v) < 0.2: return False
    for s in segs:
        if s["net"] == net or s["layer"] != layer or s["uuid"] in skip: continue
        d = min(geom.d_seg_rect(a[0], a[1], b[0], b[1], (s["x1"], s["y1"], s["x1"], s["y1"])),
                geom.d_seg_rect(a[0], a[1], b[0], b[1], (s["x2"], s["y2"], s["x2"], s["y2"])),
                geom.d_seg_rect(s["x1"], s["y1"], s["x2"], s["y2"], (a[0], a[1], a[0], a[1])),
                geom.d_seg_rect(s["x1"], s["y1"], s["x2"], s["y2"], (b[0], b[1], b[0], b[1])))
        if d - w/2 - s["w"]/2 < 0.2: return False
    for e in G.edge:
        if geom.d_seg_rect(*e, (a[0], a[1], a[0], a[1])) < 0.3: return False
    return True
done = 0; skipped = []; touched = set(); newtext = {}
for k, gs in ends.items():
    if len(gs) != 2: continue
    g1, g2 = gs
    if g1["uuid"] in touched or g2["uuid"] in touched: continue
    if not (g1["uuid"] in newids or g2["uuid"] in newids): continue
    if abs(g1["w"] - g2["w"]) > 1e-6: continue
    net, layer, cx, cy = k
    def far(g):
        return (g["x2"], g["y2"]) if abs(g["x1"]-cx) < 1e-3 and abs(g["y1"]-cy) < 1e-3 else (g["x1"], g["y1"])
    p1, p2 = far(g1), far(g2)
    L1, L2 = math.hypot(p1[0]-cx, p1[1]-cy), math.hypot(p2[0]-cx, p2[1]-cy)
    if L1 < 1e-6 or L2 < 1e-6: continue
    u = ((p1[0]-cx)/L1, (p1[1]-cy)/L1); v = ((p2[0]-cx)/L2, (p2[1]-cy)/L2)
    if abs(u[0]*v[0] + u[1]*v[1]) > 0.05: continue
    if on_pad_or_via(net, layer, cx, cy): skipped.append((net, layer, cx, cy, "pad/via at corner")); continue
    w = g1["w"]; res = None
    for c in (0.8, 0.6, 0.5, 0.4, 0.3, 0.2, 0.15, 0.1):
        c = min(c, 0.45 * L1, 0.45 * L2)
        a = (round(cx + u[0]*c, 4), round(cy + u[1]*c, 4)); b = (round(cx + v[0]*c, 4), round(cy + v[1]*c, 4))
        if ok_seg(net, layer, a, b, w, {g1["uuid"], g2["uuid"]}): res = (a, b, c); break
    if not res: skipped.append((net, layer, cx, cy, "no clearance")); continue
    a, b, c = res
    newtext[g1["uuid"]] = seg_text(p1[0], p1[1], a[0], a[1], w, layer, net, g1["uuid"])
    newtext[g2["uuid"]] = seg_text(p2[0], p2[1], b[0], b[1], w, layer, net, g2["uuid"])
    B.add_seg(a, b, w, layer, net)
    touched |= {g1["uuid"], g2["uuid"]}; done += 1
B.s = SEG_RE.sub(lambda m: newtext.get(m.group(8), m.group(0)), B.s)
B.save()
print("chamfered", done, "skipped", len(skipped))
for s in skipped: print("   skipped", s)
