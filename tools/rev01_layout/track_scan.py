"""Track check: corners sharper than 135 deg, width changes and 45-degree jogs < 0.3 mm that make a 90-degree turn, at
free joints (not on a pad or via of the net); segment ends are matched within 0.02 mm. Usage: track_scan.py board rev0_board
(rev0_board: git show 69d7c8c:Power.kicad_pcb, to mark which findings are in the new routing)."""
import sys, math, collections
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__))); sys.dont_write_bytecode = True
import pcbedit, geom
B = pcbedit.Board(sys.argv[1]); G = geom.Board(sys.argv[1]); R0 = pcbedit.Board(sys.argv[2])
TOL = 0.02
segs = list(B.segments()); vias = list(B.vias())
k0 = set((g["net"], g["layer"], tuple(sorted([(round(g["x1"], 2), round(g["y1"], 2)), (round(g["x2"], 2), round(g["y2"], 2))]))) for g in R0.segments())
def isnew(g): return (g["net"], g["layer"], tuple(sorted([(round(g["x1"], 2), round(g["y1"], 2)), (round(g["x2"], 2), round(g["y2"], 2))]))) not in k0
pads = [(r, p) for r, f in G.fps.items() for p in f.placed()[0]]
def at_pad(x, y, net):
    for r, p in pads:
        if p.get("net") == net and abs(x - p["x"]) <= p["aw"]/2 + 0.01 and abs(y - p["y"]) <= p["ah"]/2 + 0.01: return r + "." + p["name"]
def at_via(x, y, net): return any(v["net"] == net and math.hypot(v["x"] - x, v["y"] - y) < v["size"]/2 for v in vias)
byl = collections.defaultdict(list)
for i, g in enumerate(segs): byl[(g["net"], g["layer"])].append(i)
def joints(i, side):
    g = segs[i]; p = (g["x1"], g["y1"]) if side == 0 else (g["x2"], g["y2"]); out = []
    for j in byl[(g["net"], g["layer"])]:
        if j == i: continue
        h = segs[j]
        for sj, q in ((0, (h["x1"], h["y1"])), (1, (h["x2"], h["y2"]))):
            if math.hypot(p[0] - q[0], p[1] - q[1]) < TOL: out.append((j, sj))
    return p, out
def d(g, side):
    v = (g["x2"] - g["x1"], g["y2"] - g["y1"]) if side == 0 else (g["x1"] - g["x2"], g["y1"] - g["y2"]); L = math.hypot(*v)
    return (v[0]/L, v[1]/L, L) if L > 1e-9 else None
seen = set(); rep = []
for i, g in enumerate(segs):
    for side in (0, 1):
        p, js = joints(i, side)
        if len(js) != 1: continue
        j, sj = js[0]; pair = tuple(sorted([(i, side), (j, sj)]))
        if pair in seen: continue
        seen.add(pair); h = segs[j]
        if at_pad(*p, g["net"]) or at_via(*p, g["net"]): continue
        u, v = d(g, side), d(h, sj)
        if not u or not v: continue
        ang = math.degrees(math.acos(max(-1, min(1, u[0]*v[0] + u[1]*v[1]))))
        new = isnew(g) or isnew(h)
        if ang < 134.9: rep.append(("corner", g["net"], g["layer"], (round(p[0], 3), round(p[1], 3)), round(ang), new))
        if abs(g["w"] - h["w"]) > 1e-6: rep.append(("width", g["net"], g["layer"], (round(p[0], 3), round(p[1], 3)), (g["w"], h["w"]), new))
        if math.hypot(p[0] - (g["x1"] if side == 1 else g["x2"]), 0) >= 0 and u[2] < 0.3 and abs(ang - 135) < 1:
            # g is a short 45-degree jog: look at the joint on its other end
            p2, js2 = joints(i, 1 - side)
            if len(js2) == 1:
                k, sk = js2[0]; w = d(segs[k], sk)
                if w and abs(v[0]*w[0] + v[1]*w[1]) < 0.05 and not at_pad(*p2, g["net"]) and not at_via(*p2, g["net"]):
                    rep.append(("jog90", g["net"], g["layer"], (round(p[0], 3), round(p[1], 3)), round(u[2], 3), new))
for r in sorted(set(rep), key=lambda r: (not r[-1], r[0], r[1])): print(*r)
print("total", len(set(rep)), "| new routing:", sum(1 for r in set(rep) if r[-1]))
