"""§5: exhaustive search of F.Cu places for the RC snubbers (C + R in series), per phase and per type:
LS = node - C - X - R - GND, HS = VDC - C - X - R - node. A terminal pad counts as connected when its centre lies
in a filled F.Cu zone of its net; X pads must be within 1.0 mm (edge to edge) and joinable by a straight track.
Clearance 0.2 to other-net copper (pads, tracks, vias), courtyards (shrunk 0.25) incl. the bulk-cap circles,
0.3 to the board edge. Usage: snub_search.py board tools variant out.json"""
import sys, math, json, collections
sys.path.insert(0, sys.argv[2]); sys.path.insert(0, "/home/alexey/Git/KiCad/InvertorPowerNewGen/bench_2026-10-13/tools")
sys.dont_write_bytecode = True
import geom, kpcb
from matplotlib.path import Path
fn, variant, out = sys.argv[1], sys.argv[3], sys.argv[4]
G = geom.Board(fn); K = kpcb.load(fn)
PARTS = {"C0805": (1.037, 1.175, 1.45, 3.76, 1.97), "R1206": (1.55, 1.3, 1.75, 4.91, 2.25),
         "R0805": (1.0375, 1.2, 1.4, 3.7, 1.95), "C0603": (0.8625, 1.075, 0.95, 3.3, 1.46), "R0603": (0.9125, 0.975, 0.95, 3.3, 1.46)}
VAR = {"a": ("C0805", "R1206"), "b": ("C0805", "R0805"), "c": ("C0603", "R0603")}[variant]
PH = {"C": dict(x0=116.2, x1=134.2, node="/Current_Sensor_3/Phase_IN", ls=("Q8", "Q4"), hs=("Q1", "Q7"), cols=((116.2, 121.2), (121.2, 128.2), (128.2, 134.2))),
      "B": dict(x0=134.2, x1=151.2, node="/Current_Sensor_2/Phase_IN", ls=("Q9", "Q5"), hs=("Q2", "Q10"), cols=((134.2, 138.2), (138.2, 145.2), (145.2, 151.2))),
      "A": dict(x0=151.2, x1=169.2, node="/Current_Sensor_1/Phase_IN", ls=("Q11", "Q6"), hs=("Q3", "Q12"), cols=((151.2, 155.2), (155.2, 162.5), (162.5, 169.2)))}
fills = collections.defaultdict(list); ifills = collections.defaultdict(list)
for z in K["zones"]:
    for lay, pts in z["fills"]:
        if len(pts) <= 2: continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        e = (Path(pts), (min(xs), min(ys), max(xs), max(ys)))
        if lay == "F.Cu": fills[z["net"]].append(e)
        elif lay in ("In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu"): ifills[z["net"]].append(e)
def in_ifill(net, x, y):
    """the via lands on an inner-layer pour of its net (3 of 4 points 0.55 mm around the centre inside a fill)"""
    pts = [(x + dx, y + dy) for dx, dy in ((0.55, 0), (-0.55, 0), (0, 0.55), (0, -0.55))]
    return sum(any(bb[0] <= px <= bb[2] and bb[1] <= py <= bb[3] and p.contains_point((px, py)) for p, bb in ifills[net]) for px, py in pts) >= 3
def in_fill(net, x, y):
    return any(bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3] and p.contains_point((x, y)) for p, bb in fills[net])
# obstacles on F.Cu, binned
B = 2.0; bins = collections.defaultdict(list)
def add(o, x0, y0, x1, y1):
    for i in range(int(x0 // B), int(x1 // B) + 1):
        for j in range(int(y0 // B), int(y1 // B) + 1): bins[(i, j)].append(o)
for r, f in G.fps.items():
    pads, crt = f.placed()
    for p in pads:
        if p["tht"] or f.layer == "F.Cu":
            rr = (p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2)
            add(("pad", rr, p["net"]), *rr)
    if f.layer == "F.Cu" and crt and crt[2] - crt[0] > 0.01:
        add(("crt", (crt[0]+0.25, crt[1]+0.25, crt[2]-0.25, crt[3]-0.25), r), *crt)
for v in G.vias:
    r0 = geom._via_r(v); add(("via", (v["x"], v["y"], r0), v["net"]), v["x"]-r0, v["y"]-r0, v["x"]+r0, v["y"]+r0)
for s in G.segs:
    if s["layer"] == "F.Cu":
        add(("seg", s, s["net"]), min(s["x1"], s["x2"]) - s["w"], min(s["y1"], s["y2"]) - s["w"], max(s["x1"], s["x2"]) + s["w"], max(s["y1"], s["y2"]) + s["w"])
CANS = [(x, 69.13, 5.25) for x in (127.0, 137.5, 148.0, 158.5)]
def near_objs(x0, y0, x1, y1):
    seen = set(); res = []
    for i in range(int(x0 // B), int(x1 // B) + 1):
        for j in range(int(y0 // B), int(y1 // B) + 1):
            for o in bins[(i, j)]:
                if id(o) not in seen: seen.add(id(o)); res.append(o)
    return res
def part_geom(kind, x, y, rot):
    off, aw, ah, cw, ch = PARTS[kind]
    if rot in (90, 270): aw, ah, cw, ch = ah, aw, ch, cw
    dx, dy = (off, 0) if rot in (0, 180) else (0, off)
    pads = [(x - dx, y - dy, aw, ah), (x + dx, y + dy, aw, ah)]
    return pads, (x - cw/2 + 0.25, y - ch/2 + 0.25, x + cw/2 - 0.25, y + ch/2 - 0.25)
def rect(p): return (p[0]-p[2]/2, p[1]-p[3]/2, p[0]+p[2]/2, p[1]+p[3]/2)
def ov(a, b): return min(a[2], b[2]) - max(a[0], b[0]) > 1e-6 and min(a[3], b[3]) - max(a[1], b[1]) > 1e-6
def clear(kind, x, y, rot, nets):
    """nets: net of each pad (None = new net X). True if no conflict with the board."""
    pads, crt = part_geom(kind, x, y, rot)
    for cx, cy, r in CANS:
        if geom.d_pt_rect(cx, cy, crt) < r - 0.25: return False
    for e in G.edge:
        for p in pads:
            if geom.d_seg_rect(*e, rect(p)) < 0.3: return False
    for o in near_objs(crt[0]-1, crt[1]-1, crt[2]+1, crt[3]+1):
        if o[0] == "crt":
            if ov(o[1], crt): return False
            continue
        for p, net in zip(pads, nets):
            pr = rect(p)
            if o[0] == "pad":
                if net is not None and o[2] == net: continue
                if geom.d_rect_rect(pr, o[1]) < 0.2: return False
            elif o[0] == "via":
                if net is not None and o[2] == net: continue
                if geom.d_pt_rect(o[1][0], o[1][1], pr) - o[1][2] < 0.2: return False
            else:
                s = o[1]
                if net is not None and o[2] == net: continue
                if geom.d_seg_rect(s["x1"], s["y1"], s["x2"], s["y2"], pr) - s["w"]/2 < 0.2: return False
    return True
def via_spot(net, pad, xr, otherpads):
    """A free via spot (0.6/0.3) of `net` next to `pad`, x within xr; None if none."""
    hx, hy = pad[2]/2, pad[3]/2
    for d in (0.45, 0.6, 0.8):
        for ux, uy in ((1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)):
            x = pad[0] + ux*(hx + d); y = pad[1] + uy*(hy + d)
            if not (xr[0] + 0.4 <= x <= xr[1] - 0.4): continue
            ok = True
            for o in near_objs(x-1.5, y-1.5, x+1.5, y+1.5):
                if o[0] == "pad":
                    if geom.d_pt_rect(x, y, o[1]) - 0.3 < (0.05 if o[2] == net else 0.2): ok = False; break
                elif o[0] == "via":
                    if math.hypot(o[1][0]-x, o[1][1]-y) < (0.5 if o[2] == net else 0.8): ok = False; break
                elif o[0] == "seg":
                    s_ = o[1]
                    if o[2] != net and geom.d_seg_rect(s_["x1"], s_["y1"], s_["x2"], s_["y2"], (x, y, x, y)) - s_["w"]/2 - 0.3 < 0.2: ok = False; break
            if ok:
                for p in otherpads:
                    if geom.d_pt_rect(x, y, rect(p)) - 0.3 < 0.2: ok = False; break
            if ok:
                for cx, cy, r in CANS:
                    if math.hypot(cx-x, cy-y) < r: ok = False; break
            if ok and in_ifill(net, x, y): return (round(x, 3), round(y, 3))
    return None
def seg_clear(a, b, w=0.3):
    x0, y0, x1, y1 = min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])
    for o in near_objs(x0-1, y0-1, x1+1, y1+1):
        if o[0] == "pad":
            if geom.d_seg_rect(a[0], a[1], b[0], b[1], o[1]) - w/2 < 0.2: return False
        elif o[0] == "via":
            if geom.d_seg_rect(a[0], a[1], b[0], b[1], (o[1][0], o[1][1], o[1][0], o[1][1])) - w/2 - o[1][2] < 0.2: return False
        elif o[0] == "seg":
            s = o[1]
            # segment-segment distance via endpoints (good enough for short stubs)
            d = min(geom.d_seg_rect(a[0], a[1], b[0], b[1], (s["x1"], s["y1"], s["x1"], s["y1"])),
                    geom.d_seg_rect(a[0], a[1], b[0], b[1], (s["x2"], s["y2"], s["x2"], s["y2"])),
                    geom.d_seg_rect(s["x1"], s["y1"], s["x2"], s["y2"], (a[0], a[1], a[0], a[1])),
                    geom.d_seg_rect(s["x1"], s["y1"], s["x2"], s["y2"], (b[0], b[1], b[0], b[1])))
            if d - w/2 - s["w"]/2 < 0.2: return False
    return True
res = {}
step = 0.2
ONLY = __import__("os").environ.get("ONLY", "")
for ph, P in PH.items():
    for typ in ("LS", "HS"):
        if ONLY and f"{ph}-{typ}" not in ONLY.split(","): continue
        tC, tR = ("node", "GND") if typ == "LS" else ("VDC", "node")
        netC = P["node"] if tC == "node" else "VDC"; netR = "GND" if tR == "GND" else P["node"]
        x0, x1 = P["x0"] - 2, P["x1"] + 2
        # target pins for ranking: LS D/S or HS D/S
        qp = [p for qn in (P["ls"] if typ == "LS" else P["hs"]) for p in G.fps[qn].placed()[0] if not p["tht"]]
        tgtC = [(p["x"], p["y"]) for p in qp if p["net"] == netC]; tgtR = [(p["x"], p["y"]) for p in qp if p["net"] == netR]
        colof = {"GND": P["cols"][0], P["node"]: P["cols"][1], "VDC": P["cols"][2]}
        Cs, Rs = [], []
        y = 70.0
        while y <= 100.0:
            x = x0
            while x <= x1:
                for rot in (0, 90):
                    for side in (0, 1):     # which pad is the terminal
                        pads, _ = part_geom(VAR[0], x, y, rot)
                        t, xp = pads[side], pads[1 - side]
                        nets = [None, None]; nets[side] = netC
                        if clear(VAR[0], x, y, rot, nets):
                            v = None if in_fill(netC, t[0], t[1]) else via_spot(netC, t, colof[netC], [xp])
                            if in_fill(netC, t[0], t[1]) or v: Cs.append((x, y, rot, side, xp, v))
                        pads, _ = part_geom(VAR[1], x, y, rot)
                        t, xp = pads[side], pads[1 - side]
                        nets = [None, None]; nets[side] = netR
                        if clear(VAR[1], x, y, rot, nets):
                            v = None if in_fill(netR, t[0], t[1]) else via_spot(netR, t, colof[netR], [xp])
                            if in_fill(netR, t[0], t[1]) or v: Rs.append((x, y, rot, side, xp, v))
                x += step
            y += step
        best = []
        grid = collections.defaultdict(list)
        for r in Rs: grid[(int(r[4][0] // 3), int(r[4][1] // 3))].append(r)
        for c in Cs:
            cx = c[4]
            for i in (-1, 0, 1):
                for j in (-1, 0, 1):
                    for r in grid[(int(cx[0] // 3) + i, int(cx[1] // 3) + j)]:
                        rx = r[4]
                        dpad = geom.d_rect_rect(rect(cx), rect(rx))
                        if dpad > 1.0: continue
                        cp, cc = part_geom(VAR[0], c[0], c[1], c[2]); rp, rc = part_geom(VAR[1], r[0], r[1], r[2])
                        if ov(cc, rc): continue
                        # pads of different nets between the two parts: C terminal vs R pads, R terminal vs C pads
                        ctp, rtp = cp[c[3]], rp[r[3]]
                        if geom.d_rect_rect(rect(ctp), rect(rx)) < 0.2 or geom.d_rect_rect(rect(rtp), rect(cx)) < 0.2 \
                           or geom.d_rect_rect(rect(ctp), rect(rtp)) < 0.2: continue
                        if dpad > 0.0 and not seg_clear((cx[0], cx[1]), (rx[0], rx[1])): continue
                        bad = False
                        for vv, others in ((c[5], rp), (r[5], cp)):
                            if vv and any(geom.d_pt_rect(vv[0], vv[1], rect(p)) - 0.3 < 0.2 for p in others): bad = True
                        if c[5] and r[5] and math.hypot(c[5][0]-r[5][0], c[5][1]-r[5][1]) < 0.8: bad = True
                        if bad: continue
                        dC = min(math.hypot(ctp[0]-a, ctp[1]-b) for a, b in tgtC) if tgtC else 99
                        dR = min(math.hypot(rtp[0]-a, rtp[1]-b) for a, b in tgtR) if tgtR else 99
                        best.append((round(dC + dR + (0.5 if c[5] else 0) + (0.5 if r[5] else 0), 2), c[:4], r[:4], round(dC, 1), round(dR, 1), c[5], r[5]))
        best.sort()
        # keep diverse: one per 1.5 mm cell of the C position
        seen = set(); top = []
        for b in best:
            k = (int(b[1][0] // 1.5), int(b[1][1] // 1.5))
            if k in seen: continue
            seen.add(k); top.append(b)
            if len(top) >= 5: break
        res[f"{ph}-{typ}"] = top
        print(f"{variant} {ph}-{typ}: C cand {len(Cs)}, R cand {len(Rs)}, pairs {len(best)}; best {top[:3]}", flush=True)
json.dump(res, open(out, "w"))
