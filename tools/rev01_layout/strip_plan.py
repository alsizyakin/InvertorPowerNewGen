"""+4 mm board: plan of the strip between the bulk caps and the block (y ~65.5...75), per phase:
  CER x2  : C1206 VDC-GND (05 P1), pad 1 on the VDC F.Cu fill, pad 2 with two GND vias at the pad (In1/In3 GND);
  LS chain: node - C0805 = island = R0612 - GND (05 P2: pads end to end, middle = short wide copper, no track);
  HS chain: VDC - C0805 = island = R0612 - node;
  C0603 x2: the rev0 0603s C90, C92...C96, two per phase, pad 1 on VDC, pad 2 with one GND via.
Terminal pads must lie in the F.Cu fill of their net. Exposed pads keep 0.5 mm from other-net copper (P5), vias 0.2 from
tracks/vias and 0.5 from other-net exposed pads; courtyards must not overlap (bulk caps: circle r 5.25).
Movable and therefore ignored as obstacles: the snubber parts, C90, C92...C96 and their GND stubs/vias.
Phases are planned C, B, A in turn; parts already chosen are obstacles for the next phase.
Usage: strip_plan.py board.kicad_pcb out.json"""
import sys, os, math, json, collections, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, "/home/alexey/Git/KiCad/InvertorPowerNewGen/bench_2026-10-13/tools")
sys.dont_write_bytecode = True
import geom, kpcb
from matplotlib.path import Path

fn, out = sys.argv[1], sys.argv[2]
G = geom.Board(fn); K = kpcb.load(fn)
CANY = float(os.environ.get("CANY", "65.13"))
CANS = [(x, CANY, 5.25) for x in (127.0, 137.5, 148.0, 158.5)]
CL_PAD, CL_VIA, CL_HOLE, CL_EDGE = 0.5, 0.2, 0.25, 0.3
MOVABLE = {"C90", "C92", "C93", "C94", "C95", "C96"} | {f"C{n}" for n in range(112, 118)} | {f"R{n}" for n in range(100, 106)}
MOV_VIAS = []                                            # GND vias of the movable 0603s: filled in below
# phase slices: a part (courtyard and vias) must lie inside its phase's slice, so phases do not take each other's room
PH = {"C": dict(x0=116.2, x1=float(os.environ.get("XC1", "134.3")), node="/Current_Sensor_3/Phase_IN", ls="Q8", hs="Q1"),
      "B": dict(x0=134.3, x1=float(os.environ.get("XB1", "151.3")), node="/Current_Sensor_2/Phase_IN", ls="Q9", hs="Q2"),
      "A": dict(x0=151.3, x1=169.2, node="/Current_Sensor_1/Phase_IN", ls="Q11", hs="Q3")}
inside = lambda P, r: r[0] >= P["x0"] - 1e-6 and r[2] <= P["x1"] + 1e-6
# local models at rot 0: pad offset along x, pad w, pad h, courtyard half-sizes
M = {"C1206": (1.5625, 1.325, 1.8, 2.48, 1.15), "C0805": (1.0375, 1.175, 1.45, 1.88, 0.985),
     "R0612": (0.8375, 1.175, 3.4, 1.68, 1.95), "C0603": (0.8625, 1.075, 0.95, 1.65, 0.73)}

# ---------------------------------------------------------------- board model
fills = collections.defaultdict(list)
for z in K["zones"]:
    for lay, pts in z["fills"]:
        if len(pts) > 2:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            fills[(lay, z["net"])].append((Path(pts), (min(xs), min(ys), max(xs), max(ys))))
def in_fill(lay, net, x, y):
    return any(bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3] and p.contains_point((x, y)) for p, bb in fills[(lay, net)])
BIN = 2.0; bins = collections.defaultdict(list)
def add(o, x0, y0, x1, y1):
    for i in range(int(x0 // BIN), int(x1 // BIN) + 1):
        for j in range(int(y0 // BIN), int(y1 // BIN) + 1): bins[(i, j)].append(o)
def near(x0, y0, x1, y1):
    seen = set(); res = []
    for i in range(int(x0 // BIN), int(x1 // BIN) + 1):
        for j in range(int(y0 // BIN), int(y1 // BIN) + 1):
            for o in bins[(i, j)]:
                if id(o) not in seen: seen.add(id(o)); res.append(o)
    return res
for r in ("C92", "C95", "C96"):
    p2 = [p for p in G.fps[r].placed()[0] if p["net"] == "GND"][0]
    MOV_VIAS += [(v["x"], v["y"]) for v in G.vias if v["net"] == "GND" and math.hypot(v["x"]-p2["x"], v["y"]-p2["y"]) < 1.6]
for r in ("C92", "C95", "C96"):                       # GND vias reached through a short F.Cu stub from pad 2
    p2 = [p for p in G.fps[r].placed()[0] if p["net"] == "GND"][0]
    pr = (p2["x"]-p2["aw"]/2-0.05, p2["y"]-p2["ah"]/2-0.05, p2["x"]+p2["aw"]/2+0.05, p2["y"]+p2["ah"]/2+0.05)
    for sg in G.segs:
        if sg["net"] != "GND" or sg["layer"] != "F.Cu": continue
        for (ax, ay), (bx, by) in (((sg["x1"], sg["y1"]), (sg["x2"], sg["y2"])), ((sg["x2"], sg["y2"]), (sg["x1"], sg["y1"]))):
            if geom.d_pt_rect(ax, ay, pr) == 0:
                MOV_VIAS += [(v["x"], v["y"]) for v in G.vias if v["net"] == "GND" and math.hypot(v["x"]-bx, v["y"]-by) < 0.05]
print("movable vias:", MOV_VIAS)
mov_stub = lambda s: s["net"] == "GND" and s["layer"] == "F.Cu" and any(
    math.hypot(s[k1] - a, s[k2] - b) < 0.05 for k1, k2 in (("x1", "y1"), ("x2", "y2")) for a, b in MOV_VIAS)
for r, f in G.fps.items():
    if r in MOVABLE: continue
    pads, crt = f.placed()
    for p in pads:
        rr = (p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2)
        top = p["tht"] or f.layer == "F.Cu"
        add(("pad", rr, p["net"], top), *rr)
    if f.layer == "F.Cu" and crt and crt[2] - crt[0] > 0.01 and not f.lib.startswith("Capacitor_THT"):
        add(("crt", crt, r), *crt)                       # bulk caps: circles CANS
for v in G.vias:
    if any(math.hypot(v["x"] - a, v["y"] - b) < 0.05 for a, b in MOV_VIAS): continue
    r0 = geom._via_r(v); add(("via", (v["x"], v["y"], r0, v.get("d", 0.3)), v["net"]), v["x"]-r0, v["y"]-r0, v["x"]+r0, v["y"]+r0)
for s in G.segs:
    if mov_stub(s): continue
    add(("seg", s, s["net"]), min(s["x1"], s["x2"]) - s["w"], min(s["y1"], s["y2"]) - s["w"], max(s["x1"], s["x2"]) + s["w"], max(s["y1"], s["y2"]) + s["w"])

U4 = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}
def rect(c, w, h): return (c[0]-w/2, c[1]-h/2, c[0]+w/2, c[1]+h/2)
def part(kind, x, y, rot):
    """rot 0: pad 1 at -x; 90: pad 1 at +y (KiCad y down: rot 90 turns local +x to -y); returns pads [p1, p2] rects, crt."""
    off, w, h, cx, cy = M[kind]
    ux, uy = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}[rot]
    if rot in (90, 270): w, h, cx, cy = h, w, cy, cx
    p1 = (x - ux*off, y - uy*off); p2 = (x + ux*off, y + uy*off)
    return [rect(p1, w, h), rect(p2, w, h)], (x - cx, y - cy, x + cx, y + cy)
def ctr(r): return ((r[0]+r[2])/2, (r[1]+r[3])/2)
def ov(a, b): return min(a[2], b[2]) - max(a[0], b[0]) > 1e-6 and min(a[3], b[3]) - max(a[1], b[1]) > 1e-6

CL_MID = float(os.environ.get("CL_MID", "0.5"))
def pad_ok(pr, net, cl=None):
    """exposed new pad `pr` of `net` (None = new net) against the board"""
    cl = (CL_PAD if net is not None else CL_MID) if cl is None else cl
    for e in G.edge:
        if geom.d_seg_rect(*e, pr) < CL_EDGE: return False
    for o in near(pr[0]-1, pr[1]-1, pr[2]+1, pr[3]+1):
        if o[0] == "pad":
            if not o[3]: continue
            if net is not None and o[2] == net: continue
            if geom.d_rect_rect(pr, o[1]) < cl: return False
        elif o[0] == "via":
            if net is not None and o[2] == net: continue
            if geom.d_pt_rect(o[1][0], o[1][1], pr) - o[1][2] < cl: return False
        elif o[0] == "seg":
            s = o[1]
            if s["layer"] != "F.Cu" or (net is not None and o[2] == net): continue
            if geom.d_seg_rect(s["x1"], s["y1"], s["x2"], s["y2"], pr) - s["w"]/2 < cl: return False
    return True
def crt_ok(crt):
    for cx, cy, r in CANS:
        if geom.d_pt_rect(cx, cy, crt) < r: return False
    for o in near(*crt):
        if o[0] == "crt" and ov(o[1], crt): return False
    return True
def via_ok(x, y, net="GND", r=0.3):
    if not (in_fill("In1.Cu", net, x, y) and in_fill("In3.Cu", net, x, y)): return False
    for e in G.edge:
        if geom.d_seg_rect(*e, (x, y, x, y)) - r < CL_EDGE: return False
    for o in near(x-1.5, y-1.5, x+1.5, y+1.5):
        if o[0] == "pad":
            if o[2] == net: continue
            if geom.d_pt_rect(x, y, o[1]) - r < (CL_PAD if o[3] else CL_VIA): return False
        elif o[0] == "via":
            d = math.hypot(o[1][0]-x, o[1][1]-y)
            if o[2] != net and d - r - o[1][2] < CL_VIA: return False
            if d - 0.15 - o[1][3]/2 < CL_HOLE: return False
        elif o[0] == "seg":
            s = o[1]
            if o[2] == net: continue
            if geom.d_pt_seg(x, y, s["x1"], s["y1"], s["x2"], s["y2"]) - r - s["w"]/2 < CL_VIA: return False
    return True
def term_in(pr, net, lay="F.Cu", need=3):
    """terminal pad on the fill of its net: centre and pad ends (0.25 in) inside; need=2 lets one end stick out of the
    fill (into the VDC ribbon above a raised column top: the fill keeps the pad clearance around that end)"""
    c = ctr(pr); w, h = pr[2]-pr[0], pr[3]-pr[1]
    ends = [(c[0]-w/2+0.25, c[1]), (c[0]+w/2-0.25, c[1])] if w >= h else [(c[0], c[1]-h/2+0.25), (c[0], c[1]+h/2-0.25)]
    return in_fill(lay, net, *c) and sum(in_fill(lay, net, *e) for e in ends) >= need - 1

# ---------------------------------------------------------------- candidates
def pads_of(fp, net):
    return [(p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2) for p in G.fps[fp].placed()[0] if p["net"] == net]
def dmin(r, rs): return min(geom.d_rect_rect(r, q) for q in rs)
STEP = float(os.environ.get("STEP", "0.1"))
def grid(x0, x1, y0=65.5, y1=75.2):
    y = y0
    while y <= y1 + 1e-9:
        x = x0
        while x <= x1 + 1e-9: yield round(x, 3), round(y, 3); x += STEP
        y += STEP

def cer_cands(kind, P, nvias, free=False):
    hd = pads_of(P["hs"], "VDC"); top = min(r[1] for r in hd)
    tgt = ((min(r[0] for r in hd) + max(r[2] for r in hd))/2, top)
    if free: P = dict(P, x0=116.2, x1=169.2)
    res = []
    for x, y in grid(P["x0"] + 0.6, P["x1"] - 0.6):
        for rot in (0, 90, 180, 270):
            pads, crt = part(kind, x, y, rot)
            if not inside(P, crt) or not crt_ok(crt): continue
            if not term_in(pads[0], "VDC"): continue
            if not (pad_ok(pads[0], "VDC") and pad_ok(pads[1], "GND")): continue
            # GND vias at pad 2: outer end (2, side by side) / flanks / one outer
            p2 = ctr(pads[1]); p1 = ctr(pads[0]); ux, uy = p2[0]-p1[0], p2[1]-p1[1]; n = math.hypot(ux, uy); ux, uy = ux/n, uy/n
            w2 = (pads[1][2]-pads[1][0]) if abs(ux) > 0.5 else (pads[1][3]-pads[1][1])      # pad size along the axis
            l2 = (pads[1][3]-pads[1][1]) if abs(ux) > 0.5 else (pads[1][2]-pads[1][0])      # across
            e = w2/2 + 0.32; vx, vy = -uy, ux
            opts = []
            if nvias == 2:
                s = min(0.45, l2/2 - 0.05)
                opts.append([(p2[0]+ux*e+vx*s, p2[1]+uy*e+vy*s), (p2[0]+ux*e-vx*s, p2[1]+uy*e-vy*s)])
                f_ = l2/2 + 0.32
                opts.append([(p2[0]+vx*f_, p2[1]+vy*f_), (p2[0]-vx*f_, p2[1]-vy*f_)])
                opts.append([(p2[0]+ux*e, p2[1]+uy*e), (p2[0]+vx*f_, p2[1]+vy*f_)])
                opts.append([(p2[0]+ux*e, p2[1]+uy*e), (p2[0]-vx*f_, p2[1]-vy*f_)])
            else:
                opts.append([(p2[0]+ux*e, p2[1]+uy*e)])
                f_ = l2/2 + 0.32
                opts += [[(p2[0]+vx*f_, p2[1]+vy*f_)], [(p2[0]-vx*f_, p2[1]-vy*f_)]]
            for vs in opts:
                if all(via_ok(*v) and P["x0"] + 0.3 <= v[0] <= P["x1"] - 0.3 for v in vs):
                    sc = math.hypot(x - tgt[0], y - tgt[1])
                    res.append(dict(kind=kind, x=x, y=y, rot=rot, vias=[(round(a, 3), round(b, 3)) for a, b in vs],
                                    pads=pads, crt=crt, nets=["VDC", "GND"], score=round(sc, 2)))
                    break
    return res

def chain_cands(P, typ):
    """straight chains (C on the R axis) and L chains (C turned 90 deg next to the R middle pad, its terminal pad
    pointing away): the L is 1.8 mm shorter along the strip"""
    # schematic order (§5): LS node - C - X - R - GND, HS VDC - C - X - R - node: R terminal nA, C terminal nB
    if typ == "LS": nA, nB, tA, tB = "GND", P["node"], pads_of(P["ls"], "GND"), pads_of(P["ls"], P["node"])
    else: nA, nB, tA, tB = P["node"], "VDC", pads_of(P["hs"], P["node"]), pads_of(P["hs"], "VDC")
    D = M["R0612"][3] + M["C0805"][3] + 0.02; DL = M["R0612"][3] + M["C0805"][4] + 0.02
    res = []
    for x, y in grid(P["x0"] - 4, P["x1"] + 4):
        for d in (0, 90, 180, 270):
            ux, uy = U4[d]
            rp, rc = part("R0612", x, y, d)                      # R pad 2 (towards C) = middle
            if not (inside(P, rc) and crt_ok(rc)): continue
            if not (term_in(rp[0], nA, need=2) and pad_ok(rp[0], nA) and pad_ok(rp[1], None)): continue
            rm = ctr(rp[1])
            shapes = [("I", d, 0.0)] + [("L", (d + t) % 360, k) for t in (90, 270) for k in (-1.0, -0.5, 0.0, 0.5, 1.0)]
            for shp, cr, k in shapes:
                wx, wy = U4[cr]
                if shp == "I": cx, cy = x + ux*D, y + uy*D
                else: cx, cy = x + ux*DL + wx*(M["C0805"][0] + k), y + uy*DL + wy*(M["C0805"][0] + k)
                cp, cc = part("C0805", cx, cy, cr)               # C pad 1 = middle, pad 2 = terminal
                if not (inside(P, cc) and crt_ok(cc) and not ov(cc, rc)): continue
                if not (term_in(cp[1], nB, need=2) and pad_ok(cp[1], nB) and pad_ok(cp[0], None)): continue
                if geom.d_rect_rect(cp[1], rp[0]) < CL_PAD or geom.d_rect_rect(cp[1], rp[1]) < CL_MID: continue
                cm = ctr(cp[0]); a = (rm[0] + wx*k, rm[1] + wy*k) if shp == "L" else rm
                sc = dmin(rp[0], tA) + dmin(cp[1], tB)
                res.append(dict(kind="chain", shape=shp, x=x, y=y, rot=d, cx=round(cx, 3), cy=round(cy, 3), crot=cr,
                                bridge=[(round(a[0], 3), round(a[1], 3)), (round(cm[0], 3), round(cm[1], 3))],
                                rnet=nA, cnet=nB, pads=[rp[0], rp[1], cp[0], cp[1]], nets=[nA, "X", "X", nB], crt=rc, crt2=cc,
                                score=round(sc, 2), dR=round(dmin(rp[0], tA), 2), dC=round(dmin(cp[1], tB), 2), vias=[]))
    return res

def diverse(c, n, cell=0.8):
    c = sorted(c, key=lambda r: r["score"]); seen = set(); top = []
    for r in c:
        k = (int(r["x"] // cell), int(r["y"] // cell), r["rot"], r.get("shape"), r.get("crot"))
        if k in seen: continue
        seen.add(k); top.append(r)
        if len(top) >= n: break
    return top

def compat(a, b):
    ca = [a["crt"]] + ([a["crt2"]] if "crt2" in a else []); cb = [b["crt"]] + ([b["crt2"]] if "crt2" in b else [])
    if any(ov(x, y) for x in ca for y in cb): return False
    for pa, na in zip(a["pads"], a["nets"]):
        for pb, nb in zip(b["pads"], b["nets"]):
            if na == nb and na != "X": continue
            if geom.d_rect_rect(pa, pb) < CL_PAD: return False
        for v in b["vias"]:
            if na != "GND" and geom.d_pt_rect(v[0], v[1], pa) - 0.3 < CL_PAD: return False
    for pb, nb in zip(b["pads"], b["nets"]):
        for v in a["vias"]:
            if nb != "GND" and geom.d_pt_rect(v[0], v[1], pb) - 0.3 < CL_PAD: return False
    for v in a["vias"]:
        for w in b["vias"]:
            if math.hypot(v[0]-w[0], v[1]-w[1]) < 0.3 + CL_HOLE: return False
    return True

def as_obstacle(it):
    for pr, n in zip(it["pads"], it["nets"]): add(("pad", pr, n if n != "X" else f"X{id(it)}", True), *pr)
    for c in [it["crt"]] + ([it["crt2"]] if "crt2" in it else []): add(("crt", c, "new"), *c)
    for v in it["vias"]: add(("via", (v[0], v[1], 0.3, 0.3), "GND"), v[0]-0.3, v[1]-0.3, v[0]+0.3, v[1]+0.3)

K = int(os.environ.get("KTRY", "6"))           # compatible alternatives tried per level (ceramics, 0603)
NCH = int(os.environ.get("NCH", "25"))         # snubber chains: best NCH positions, spread out
plan = {ph: {} for ph in PH}
srt = lambda c: sorted(c, key=lambda r: r["score"])
def search(pools, wts, miss, kmax):
    best = [None, None]
    n = len(pools)
    lb = [sum(w*(pl[0]["score"] if pl else m) for pl, w, m in zip(pools[k:], wts[k:], miss[k:])) for k in range(n)] + [0]
    def dfs(i, chosen, sc):
        if best[0] is not None and sc + lb[i] >= best[0]: return
        if i == n:
            best[0], best[1] = sc, list(chosen); return
        tried = 0
        for c in pools[i]:
            if best[0] is not None and sc + wts[i]*c["score"] + lb[i+1] >= best[0]: break
            if all(o is None or compat(c, o) for o in chosen):
                dfs(i + 1, chosen + [c], sc + wts[i]*c["score"]); tried += 1
                if tried >= kmax[i]: break
        dfs(i + 1, chosen + [None], sc + wts[i]*miss[i])
    dfs(0, [], 0.0)
    return best[1]
def keep(ph, names, items):
    for nm, it in zip(names, items):
        if it is None: print(f"  {ph} {nm}: none"); continue
        as_obstacle(it)
        plan[ph][nm] = {k: v for k, v in it.items() if k not in ("pads", "crt", "crt2")}
        print(f"  {ph} {nm}: " + ", ".join(f"{k}={v}" for k, v in plan[ph][nm].items() if k not in ("nets", "kind", "rnet", "cnet", "bridge")), flush=True)
# pass 1, per phase inside its slice: LS and HS snubber chains and the first 1206 at the HS drain
for ph, P in PH.items():
    LS = diverse(chain_cands(P, "LS"), NCH); HS = diverse(chain_cands(P, "HS"), NCH); C12 = srt(cer_cands("C1206", P, 2))
    print(f"{ph}: LS {len(LS)} {[c['score'] for c in LS[:3]]}; HS {len(HS)} {[c['score'] for c in HS[:3]]}; 1206 {len(C12)}", flush=True)
    keep(ph, ["LS", "HS", "CER1"], search([LS, HS, C12], [1.0, 1.0, float(os.environ.get("WCER", "1.5"))], [50, 30, 50], [999, 999, K]))
# pass 2, inside the phase slice: the second 1206 of each phase, nearest to that phase's HS drain (on the VDC
# ribbon over In1 GND in 0.1 mm any place of the slice is a low-inductance branch, 05 P1)
for ph, P in (() if os.environ.get("NOCER2") == "1" else PH.items()):
    keep(ph, ["CER2"], search([srt(cer_cands("C1206", P, 2, free=os.environ.get("CER2FREE") == "1"))], [1.0], [99], [1]))
# pass 3: the rev0 0603s, two per phase, nearest to the phase's HS drain
for ph, P in PH.items():
    C06 = srt(cer_cands("C0603", P, 1, free=True))
    keep(ph, ["C06a", "C06b"], search([C06, C06], [1.0, 1.0], [99, 99], [K, K]))
json.dump(plan, open(out, "w"), indent=1)
