"""§6 check: edge-to-edge distance on F.Cu from the HI/LI copper of each driver (D?-HI, D?-LI nets and the input
lines within the driver area) to node copper (Phase_IN / Phase_OUT: pads, tracks, vias, zone fills).
Usage: hidist.py board.kicad_pcb tools_dir"""
import sys, math
sys.path.insert(0, sys.argv[2]); sys.path.insert(0, "/home/alexey/Git/KiCad/InvertorPowerNewGen/bench_2026-10-13/tools")
sys.dont_write_bytecode = True
import geom, kpcb
fn = sys.argv[1]
G = geom.Board(fn); K = kpcb.load(fn)
def dps(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay; L = vx*vx + vy*vy
    t = 0 if L == 0 else max(0, min(1, ((px-ax)*vx + (py-ay)*vy)/L))
    return math.hypot(px - ax - t*vx, py - ay - t*vy)
def inter(a, b, c, d):
    def o(p, q, r): return (q[0]-p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0])
    return o(a, b, c)*o(a, b, d) < 0 and o(c, d, a)*o(c, d, b) < 0
def dss(a, b, c, d):
    if inter(a, b, c, d): return 0.0
    return min(dps(*a, *c, *d), dps(*b, *c, *d), dps(*c, *a, *b), dps(*d, *a, *b))
def rect_edges(p):
    x0, y0, x1, y1 = p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2
    return [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
# objects as (kind, geometry, half-width, label): 'seg' -> ((a,b), hw); edges of rect/polygon -> hw 0; via -> point, r
def collect(netpred, win):
    out = []
    x0, y0, x1, y1 = win
    inw = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1
    for s in G.segs:
        if s["layer"] == "F.Cu" and netpred(s["net"]) and (inw(s["x1"], s["y1"]) or inw(s["x2"], s["y2"])):
            out.append(("seg", ((s["x1"], s["y1"]), (s["x2"], s["y2"])), s["w"]/2, f'track {s["net"]}'))
    for r, f in G.fps.items():
        for p in f.placed()[0]:
            onF = p["tht"] or (f.layer == "F.Cu")
            if onF and netpred(p["net"]) and inw(p["x"], p["y"]):
                for e in rect_edges(p): out.append(("seg", e, 0.0, f'pad {r}.{p["name"]} {p["net"]}'))
    for v in G.vias:
        if netpred(v["net"]) and inw(v["x"], v["y"]):
            out.append(("pt", (v["x"], v["y"]), geom._via_r(v), f'via {v["net"]} ({v["x"]},{v["y"]})'))
    return out
def zone_edges(netpred, win):
    out = []; x0, y0, x1, y1 = win
    for z in K["zones"]:
        if not netpred(z["net"]): continue
        for lay, pts in z["fills"]:
            if lay != "F.Cu": continue
            for i in range(len(pts)):
                a, b = pts[i], pts[(i+1) % len(pts)]
                if (x0 <= a[0] <= x1 and y0 <= a[1] <= y1) or (x0 <= b[0] <= x1 and y0 <= b[1] <= y1):
                    out.append(("seg", (tuple(a), tuple(b)), 0.0, f'zone {z["net"]}'))
    return out
def dist(o1, o2):
    if o1[0] == "seg" and o2[0] == "seg": d = dss(*o1[1], *o2[1])
    elif o1[0] == "seg": d = dps(*o2[1], *o1[1][0], *o1[1][1])
    elif o2[0] == "seg": d = dps(*o1[1], *o2[1][0], *o2[1][1])
    else: d = math.hypot(o1[1][0]-o2[1][0], o1[1][1]-o2[1][1])
    return d - o1[2] - o2[2]
node = lambda n: "Phase_IN" in n or "Phase_OUT" in n
for d, k in (("D4", "3"), ("D5", "2"), ("D6", "1")):
    f = G.fps[d]; cx = f.x
    win = (cx - 8.5, 101.5, cx + 2.0, 117.0)
    sig = lambda n, d=d, k=k: n in (f"Net-({d}-HI)", f"Net-({d}-LI)", f"/TMR1_CH{k}", f"/TMR1_CH{k}N")
    S = collect(sig, win)
    N = collect(node, (win[0]-3, win[1]-3, win[2]+3, win[3]+3)) + zone_edges(node, (win[0]-4, win[1]-4, win[2]+4, win[3]+4))
    best = min(((dist(a, b), a[3], b[3]) for a in S for b in N), default=None)
    print(f"{d}: min HI/LI -> node copper on F.Cu = {best[0]:.2f} mm  ({best[1]}  <->  {best[2]})")
if len(sys.argv) > 3:
    for d, k in (("D4", "3"), ("D5", "2"), ("D6", "1")):
        f = G.fps[d]; cx = f.x; win = (cx - 8.5, 101.5, cx + 2.0, 117.0)
        sig = lambda n, d=d, k=k: n in (f"Net-({d}-HI)", f"Net-({d}-LI)", f"/TMR1_CH{k}", f"/TMR1_CH{k}N")
        S = collect(sig, win)
        N = collect(node, (win[0]-3, win[1]-3, win[2]+3, win[3]+3)) + zone_edges(node, (win[0]-4, win[1]-4, win[2]+4, win[3]+4))
        per = {}
        for a in S:
            dm = min(((dist(a, b), b[3]) for b in N), default=(99, ""))
            if a[3] not in per or dm[0] < per[a[3]][0]: per[a[3]] = dm
        print(d, "objects closer than 2 mm:")
        for lab, (dd, nb) in sorted(per.items(), key=lambda kv: kv[1][0]):
            if dd < 2.0: print(f"   {dd:5.2f}  {lab:40s} <-> {nb}")
