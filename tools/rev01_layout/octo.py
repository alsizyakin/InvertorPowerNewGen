"""Make every track segment run at 0, 45 or 90 degrees (owner's rule, 2026-10-19). For each segment off these angles:
- a segment lying wholly inside one pad of its net is deleted;
- otherwise its ends that sit in a pad of the net may move inside that pad (preferably to the pad centre lines), an end
  at a via may shift up to 0.05 mm, a T-joint end may slide along its straight track; other track joints stay. Candidates: one octilinear segment, or two (45 degrees + straight) in either order.
- a candidate must keep 0.2 mm to other-net pads, vias, tracks and 0.25 mm to the board edge, and make no corner sharper
  than 135 degrees with the track at a joint (90 degrees at a branch point); the cheapest (length + bends + distance of pad ends from the centre) wins.
Usage: octo.py board.kicad_pcb [tools_dir]  (edits the board in place, prints what changed and what was left)"""
import sys, math, collections
sys.path.insert(0, sys.argv[2] if len(sys.argv) > 2 else "/home/alexey/Git/KiCad/InvertorPowerNewGen/tools/rev01_layout")
sys.dont_write_bytecode = True
from pcbedit import Board, seg_text
import geom

TOL = 0.01                       # degrees off 0/45/90 still accepted
fn = sys.argv[1]
B = Board(fn); G = geom.Board(fn)
pads = [(f, p, (p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2))
        for f in G.fps.values() for p in f.placed()[0]]
vias = list(B.vias())
segs = [dict(g) for g in B.segments()]

def dev(a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    if math.hypot(dx, dy) < 1e-4: return 0.0
    r = math.degrees(math.atan2(dy, dx)) % 45
    return min(r, 45 - r)

def on_layer(f, p, layer):
    return p["tht"] or (layer in p["cu"]) or ("*.Cu" in p["cu"] and f.layer == layer)

def pad_at(net, layer, pt):
    for f, p, r in pads:
        if p["net"] == net and on_layer(f, p, layer) and r[0]-1e-6 <= pt[0] <= r[2]+1e-6 and r[1]-1e-6 <= pt[1] <= r[3]+1e-6:
            return f, p, r
    return None

def via_at(net, pt):
    return any(v["net"] == net and math.hypot(v["x"]-pt[0], v["y"]-pt[1]) < v["size"]/2 for v in vias)

def others_at(net, layer, pt, skip):
    """Directions (unit vectors from pt) of the other segments of the net ending at pt or passing through it."""
    out = []
    for s in segs:
        if s is skip or s["net"] != net or s["layer"] != layer: continue
        a, b = (s["x1"], s["y1"]), (s["x2"], s["y2"])
        for p, q in ((a, b), (b, a)):
            if math.hypot(p[0]-pt[0], p[1]-pt[1]) < 1e-3:
                L = math.hypot(q[0]-p[0], q[1]-p[1]); out.append(((q[0]-p[0])/L, (q[1]-p[1])/L))
        if geom.d_pt_seg(pt[0], pt[1], *a, *b) < 1e-3 and min(math.hypot(a[0]-pt[0], a[1]-pt[1]), math.hypot(b[0]-pt[0], b[1]-pt[1])) > 1e-3:
            out.append(None)                                   # T-joint on a straight run: any angle is fine
    return out

def end_moves(net, layer, pt, other):
    hit = pad_at(net, layer, pt)
    if not hit:
        if not via_at(net, pt):
            # a T-joint on the middle of a straight track may slide along that track
            out = [pt]
            for s in segs:
                if s["net"] != net or s["layer"] != layer: continue
                a, b = (s["x1"], s["y1"]), (s["x2"], s["y2"])
                if geom.d_pt_seg(pt[0], pt[1], *a, *b) > 1e-3 or min(math.hypot(a[0]-pt[0], a[1]-pt[1]), math.hypot(b[0]-pt[0], b[1]-pt[1])) < 1e-3: continue
                if dev(a, b) > TOL: continue
                L = math.hypot(b[0]-a[0], b[1]-a[1]); u = ((b[0]-a[0])/L, (b[1]-a[1])/L)
                for k in range(8):
                    d = (math.cos(math.radians(45*k)), math.sin(math.radians(45*k)))
                    det = u[0]*(-d[1]) - u[1]*(-d[0])
                    if abs(det) < 1e-9: continue
                    rx, ry = other[0]-a[0], other[1]-a[1]
                    t = (rx*(-d[1]) - ry*(-d[0])) / det
                    if 0.05 < t < L - 0.05: out.append((round(a[0]+u[0]*t, 4), round(a[1]+u[1]*t, 4)))
            return out, None
        # a track may end up to 0.05 mm off a via centre: line it up with the other end
        cand = [pt, (other[0], pt[1]), (pt[0], other[1])]
        for sx in (-1, 1):
            for sy in (-1, 1):
                t = ((pt[0]-other[0])*sx + (pt[1]-other[1])*sy) / 2
                cand.append((other[0]+sx*t, other[1]+sy*t))
        return [q for q in cand if math.hypot(q[0]-pt[0], q[1]-pt[1]) <= 0.05], None
    f, p, r = hit
    c = (p["x"], p["y"])
    cand = [pt, c, (c[0], pt[1]), (pt[0], c[1])]
    return [q for i, q in enumerate(cand) if all(math.hypot(q[0]-o[0], q[1]-o[1]) > 1e-4 for o in cand[:i])], (f, p, r)

def snaps(fixed, rect, centre):
    """For each of the 8 octilinear rays from `fixed`: the point of the ray inside the pad rect (shrunk by 0.1) that is
    nearest to the pad centre."""
    sh = (rect[0]+0.1, rect[1]+0.1, rect[2]-0.1, rect[3]-0.1); out = []
    for k in range(8):
        a = math.radians(45*k); d = (round(math.cos(a), 12), round(math.sin(a), 12))
        lo, hi = 0.0, 1e9
        for c, dc, l, h in ((fixed[0], d[0], sh[0], sh[2]), (fixed[1], d[1], sh[1], sh[3])):
            if abs(dc) < 1e-9:
                if not l <= c <= h: lo, hi = 1, 0
            else:
                t1, t2 = sorted(((l - c)/dc, (h - c)/dc)); lo, hi = max(lo, t1), min(hi, t2)
        if lo > hi: continue
        t = min(max((centre[0]-fixed[0])*d[0] + (centre[1]-fixed[1])*d[1], lo), hi)
        out.append((round(fixed[0]+d[0]*t, 4), round(fixed[1]+d[1]*t, 4)))
    return out

def doglegs(a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]; ax, ay = abs(dx), abs(dy); sx, sy = math.copysign(1, dx), math.copysign(1, dy)
    if dev(a, b) <= TOL: return [[a, b]]
    m = min(ax, ay)
    p1 = (a[0]+sx*m, a[1]+sy*m)                                # 45 degrees first
    p2 = (b[0]-sx*m, b[1]-sy*m)                                # straight first
    return [[a, (round(p1[0], 4), round(p1[1], 4)), b], [a, (round(p2[0], 4), round(p2[1], 4)), b]]

def clear(poly, w, layer, net, skip):
    for a, b in zip(poly, poly[1:]):
        for f, p, r in pads:
            if p["net"] == net or not on_layer(f, p, layer): continue
            if geom.d_seg_rect(a[0], a[1], b[0], b[1], r) - w/2 < 0.2 - 1e-6: return False
        for v in vias:
            if v["net"] == net: continue
            if geom.d_pt_seg(v["x"], v["y"], a[0], a[1], b[0], b[1]) - w/2 - v["size"]/2 < 0.2 - 1e-6: return False
        for s in segs:
            if s is skip or s["layer"] != layer or s["net"] == net: continue
            if geom.d_seg_seg((a[0], a[1], b[0], b[1]), (s["x1"], s["y1"], s["x2"], s["y2"])) - w/2 - s["w"]/2 < 0.2 - 1e-6: return False
        for e in G.edge:
            if geom.d_seg_seg((a[0], a[1], b[0], b[1]), e) - w/2 < 0.25: return False
    return True

def corner_ok(poly, net, layer, skip, ends_free):
    """No corner sharper than 135 degrees inside the polyline or against other tracks at a joint end."""
    def u(p, q):
        L = math.hypot(q[0]-p[0], q[1]-p[1]); return ((q[0]-p[0])/L, (q[1]-p[1])/L)
    for i in range(1, len(poly)-1):
        a, b = u(poly[i], poly[i-1]), u(poly[i], poly[i+1])
        if a[0]*b[0] + a[1]*b[1] > -0.5: return False
    for k, (pt, nxt) in enumerate(((poly[0], poly[1]), (poly[-1], poly[-2]))):
        if ends_free[k]: continue
        d = u(pt, nxt); oth = others_at(net, layer, pt, skip)
        lim = -0.5 if len(oth) == 1 else 0.05                  # a branch of a Y or T joint may stand at 90 degrees
        for o in oth:
            if o is not None and d[0]*o[0] + d[1]*o[1] > lim: return False
    return True

changed, left = [], []
for g in [s for s in segs if dev((s["x1"], s["y1"]), (s["x2"], s["y2"])) > TOL]:
    net, layer, w = g["net"], g["layer"], g["w"]
    A, Bp = (g["x1"], g["y1"]), (g["x2"], g["y2"])
    ma, pa = end_moves(net, layer, A, Bp); mb, pb = end_moves(net, layer, Bp, A)
    ends_free = (pa is not None or via_at(net, A), pb is not None or via_at(net, Bp))
    if pa and pb and pa[0] is pb[0] and pa[1] is pb[1]:
        segs.remove(g)
        changed.append((g, "deleted (inside %s.%s)" % (pa[0].ref, pa[1]["name"]), None)); continue
    cands = []
    for a in ma:
        for b in mb:
            for poly in doglegs(a, b): cands.append(poly)
    if pa: cands += [[q, Bp] for q in snaps(Bp, pa[2], (pa[1]["x"], pa[1]["y"]))]
    if pb: cands += [[A, q] for q in snaps(A, pb[2], (pb[1]["x"], pb[1]["y"]))]
    best = None
    for poly in cands:
        if any(math.hypot(q[0]-p[0], q[1]-p[1]) < 0.05 for p, q in zip(poly, poly[1:])): continue
        if any(dev(p, q) > TOL for p, q in zip(poly, poly[1:])): continue
        if not clear(poly, w, layer, net, g): continue
        if not corner_ok(poly, net, layer, g, ends_free): continue
        L = sum(math.hypot(q[0]-p[0], q[1]-p[1]) for p, q in zip(poly, poly[1:]))
        off = (math.hypot(poly[0][0]-pa[1]["x"], poly[0][1]-pa[1]["y"]) if pa else 0) + \
              (math.hypot(poly[-1][0]-pb[1]["x"], poly[-1][1]-pb[1]["y"]) if pb else 0)
        cost = L + 0.4*(len(poly)-2) + 0.5*off
        if best is None or cost < best[0]: best = (cost, poly)
    if not best:
        # last resort: slide a track joint of degree 2 along its other (straight) track until this one is octilinear
        for J, K, free in ((A, Bp, ends_free[0]), (Bp, A, ends_free[1])):
            if free: continue
            oth = [s for s in segs if s is not g and s["net"] == net and s["layer"] == layer and
                   any(math.hypot(e[0]-J[0], e[1]-J[1]) < 1e-3 for e in ((s["x1"], s["y1"]), (s["x2"], s["y2"])))]
            if len(oth) != 1: continue
            o = oth[0]; F = (o["x2"], o["y2"]) if math.hypot(o["x1"]-J[0], o["y1"]-J[1]) < 1e-3 else (o["x1"], o["y1"])
            if dev(J, F) > TOL: continue
            Lo = math.hypot(F[0]-J[0], F[1]-J[1]); u = ((F[0]-J[0])/Lo, (F[1]-J[1])/Lo)
            for k in range(8):
                a = math.radians(45*k); d = (math.cos(a), math.sin(a))
                det = u[0]*(-d[1]) - u[1]*(-d[0])
                if abs(det) < 1e-9: continue
                rx, ry = K[0]-J[0], K[1]-J[1]                  # J + s*u = K - t*d
                sl = (rx*(-d[1]) - ry*(-d[0])) / det; t = (u[0]*ry - u[1]*rx) / det
                if t <= 0.05 or abs(sl) > 0.3 or sl > Lo - 0.05: continue
                J2 = (round(J[0]+u[0]*sl, 4), round(J[1]+u[1]*sl, 4))
                if dev(J2, K) > TOL or dev(J2, F) > TOL: continue
                if not (clear([J2, K], w, layer, net, g) and clear([J2, F], o["w"], layer, net, o)): continue
                if best is None or abs(sl) < best[0]: best = (abs(sl), [J2, K], o, [J2, F])
        if not best: left.append(g); continue
        _, poly, o, opoly = best; segs.remove(g); segs.remove(o)
        segs += [dict(x1=p[0], y1=p[1], x2=q[0], y2=q[1], w=x["w"], layer=layer, net=net, uuid=None, span=None)
                 for x, pl in ((g, poly), (o, opoly)) for p, q in zip(pl, pl[1:])]
        changed += [(g, "replaced (joint slid)", poly), (o, "replaced (joint slid)", opoly)]; continue
    poly = best[1]; segs.remove(g)
    new = [dict(x1=p[0], y1=p[1], x2=q[0], y2=q[1], w=w, layer=layer, net=net, uuid=None, span=None) for p, q in zip(poly, poly[1:])]
    segs += new; changed.append((g, "replaced", poly))

# write: drop changed segments by uuid, add the new ones
drop = set(g["uuid"] for g, _, _ in changed)
from pcbedit import SEG_RE
B.s = SEG_RE.sub(lambda m: "" if m.group(8) in drop else m.group(0), B.s)
for g, how, poly in changed:
    if poly:
        for p, q in zip(poly, poly[1:]): B.add_seg(p, q, g["w"], g["layer"], g["net"])
B.save()
f2 = lambda p: "(%.3f,%.3f)" % p
for g, how, poly in changed:
    print(f'{g["layer"]:5s} {g["net"][-18:]:18s} {f2((g["x1"], g["y1"]))}->{f2((g["x2"], g["y2"]))}  {how}' +
          (" -> " + "".join(f2(p) for p in poly) if poly else ""))
print("fixed", len(changed), "left", len(left))
for g in left: print("   LEFT", g["layer"], g["net"], f2((g["x1"], g["y1"])), f2((g["x2"], g["y2"])))
