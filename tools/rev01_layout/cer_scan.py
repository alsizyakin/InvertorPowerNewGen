"""Spots for a 0603 VDC-GND cap (template C92: pad1 VDC, pad2 GND) in the strip above the block: pad1 centre in the
VDC F.Cu fill, pad2 gets a GND via (0.6/0.3) 0.45-0.8 mm off the pad, landing on inner GND; clear of everything,
of the bulk-cap circles and of each other. Usage: cer_scan.py board"""
import sys, os, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0]))); sys.path.insert(0, "/home/alexey/Git/KiCad/InvertorPowerNewGen/bench_2026-10-13/tools")
sys.dont_write_bytecode = True
import geom, kpcb
from matplotlib.path import Path
fn = sys.argv[1]; G = geom.Board(fn); K = kpcb.load(fn)
CANS = [(x, 65.13, 5.25) for x in (127.0, 137.5, 148.0, 158.5)]
fF, fI = [], []
for z in K["zones"]:
    for lay, pts in z["fills"]:
        if len(pts) < 3: continue
        e = Path(pts)
        if lay == "F.Cu" and z["net"] == "VDC": fF.append(e)
        if lay in ("In1.Cu", "In3.Cu") and z["net"] == "GND": fI.append(e)
inF = lambda x, y: any(p.contains_point((x, y)) for p in fF)
inI = lambda x, y: sum(any(p.contains_point((x+dx, y+dy)) for p in fI) for dx, dy in ((.55, 0), (-.55, 0), (0, .55), (0, -.55))) >= 3
ref = sys.argv[2] if len(sys.argv) > 2 else "C92"; orig = (G.fps[ref].x, G.fps[ref].y)
res = []
y = 66.0
while y <= 75.0:
    x = 116.5
    while x <= 169.0:
        if abs(x - orig[0]) < 2.2 and abs(y - orig[1]) < 1.6: x += 0.25; continue    # C92 itself stays
        for rot in (0, 90, 180, 270):
            pads, crt = G.fps[ref].placed(x, y, rot)
            if any(geom.d_pt_rect(cx, cy, crt) < r - 0.25 for cx, cy, r in CANS): continue
            p1 = [p for p in pads if p["name"] == "1"][0]; p2 = [p for p in pads if p["name"] == "2"][0]
            if not inF(p1["x"], p1["y"]): continue
            if G.check_fast(ref, x, y, rot): continue
            # via for pad 2, pointing away from pad 1
            ux, uy = (p2["x"] - p1["x"]), (p2["y"] - p1["y"]); n = math.hypot(ux, uy); ux, uy = ux/n, uy/n
            for d in (0.75, 0.9, 1.05):
                vx, vy = p2["x"] + ux*d, p2["y"] + uy*d
                v = dict(x=vx, y=vy, net="GND", d=0.3, size=0.6)
                if not inI(vx, vy): continue
                if any(math.hypot(cx-vx, cy-vy) < r for cx, cy, r in CANS): continue
                bad = any(o["net"] != "GND" and math.hypot(o["x"]-vx, o["y"]-vy) < 0.8 for o in G.vias)
                bad = bad or any(q["net"] != "GND" and geom.d_pt_rect(vx, vy, (q["x"]-q["aw"]/2, q["y"]-q["ah"]/2, q["x"]+q["aw"]/2, q["y"]+q["ah"]/2)) - 0.3 < 0.2
                                 for f in G.fps.values() for q in f.placed()[0] if abs(q["x"]-vx) < 4 and abs(q["y"]-vy) < 4)
                bad = bad or any(s["net"] != "GND" and geom.d_seg_rect(s["x1"], s["y1"], s["x2"], s["y2"], (vx, vy, vx, vy)) - s["w"]/2 - 0.3 < 0.2
                                 for s in G.segs if abs(s["x1"]-vx) < 6 and abs(s["y1"]-vy) < 6)
                if not bad: res.append((round(x, 2), round(y, 2), rot, (round(vx, 2), round(vy, 2)))); break
        x += 0.25
    y += 0.25
print("spots:", len(res))
for name, ox in (("C94", 119.75), ("C93", 142.75), ("C90", 153.0)):
    near = sorted(res, key=lambda r: (abs(r[0]-ox) + abs(r[1]-73.75)))[:3]
    print(name, "orig", ox, 73.75, "->", near)
xs = collections.Counter(int(r[0]) for r in res); print("by x:", sorted(xs.items()))
# greedy: mutually compatible set per phase, nearest to the HS drain top first
pads0, crt0 = G.fps[ref].placed(0, 0, 0)
def boxes(r):
    pads, crt = G.fps[ref].placed(r[0], r[1], r[2])
    vx, vy = r[3]
    return (crt[0]+.25, crt[1]+.25, crt[2]-.25, crt[3]-.25), [(p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2) for p in pads] + [(vx-.3, vy-.3, vx+.3, vy+.3)]
def ok(a, b):
    ca, pa = boxes(a); cb, pb = boxes(b)
    if min(ca[2], cb[2]) - max(ca[0], cb[0]) > 0 and min(ca[3], cb[3]) - max(ca[1], cb[1]) > 0: return False
    return all(geom.d_rect_rect(x, y) >= 0.2 for x in pa for y in pb)
for ph, (x0, x1, top) in {"C": (126.0, 136.5, (131.6, 75.0)), "B": (143.0, 153.5, (148.6, 75.0)), "A": (160.0, 169.0, (165.9, 75.0))}.items():
    cand = sorted([r for r in res if x0 <= r[0] <= x1], key=lambda r: math.hypot(r[0]-top[0], r[1]-top[1]))
    pick = []
    for r in cand:
        if all(ok(r, p) for p in pick): pick.append(r)
    print(ph, len(pick), [(p[0], p[1], p[2], round(math.hypot(p[0]-top[0], p[1]-top[1]), 1)) for p in pick[:6]])
