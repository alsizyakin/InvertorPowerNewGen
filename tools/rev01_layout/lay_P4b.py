"""Review round 2 of rev0.1-plus4 (docs/reviews/07, 09). Usage: lay_P4b.py board.kicad_pcb
F12 (07 P9): the snubber middle points X sit 0.30-0.44 mm from node/VDC copper (84 V): X pads get a 0.5 mm local
     clearance. Two places then still come closer: R102.1 (X, LS chain A) to the D tab of Q11 - the chain A goes up by
     0.06 mm (shifting it in x hits C129 or Q11); R100.1 to the GND via (119.75, 74.85) - the via moves to (119.35, 75.05).
F13 (07 P14): VDC on B.Cu over the node columns in the strip comes back (the +4 mm cut was needed on F.Cu only):
     B.Cu-only VDC zones (priority 9: same-net zones of one priority must not overlap), 0.6 mm off the GND strips and
     the B.Cu node zones.
F14 (09 E14, 07 P12): the slot screws are on chassis potential: B.Mask openings kept >= 1.5 mm off the screw slots
     (119.0, 95.5) and (166.5, 95.5), r 2.75 - a circle r 4.25 is cut out of each B.Mask zone it touches."""
import sys, os, re, math, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import pcbedit, fplib, geom
fn = sys.argv[1]
G = geom.Board(fn); B = pcbedit.Board(fn)

def fmt(v):
    t = f"{v:.4f}".rstrip("0").rstrip("."); return t if t not in ("-0", "") else "0"

# ---------------------------------------------------------------- F12
S3 = os.environ.get("STRIP_S3") == "1"     # rev0.1-shift3: the two +4 mm specific shifts below do not apply; VDC zones from y 72.0
DY_A = -0.06
for ref in (() if S3 else ("R102", "C114")):
    f = G.fps[ref]; B.move_fp(ref, f.x, f.y + DY_A, f.rot)
if not S3:
    g = [g for g in B.segments("Net-(C114-Pad2)", "F.Cu")]; assert len(g) == 1; g = g[0]
    B.replace_seg(g, pcbedit.seg_text(g["x1"], g["y1"] + DY_A, g["x2"], g["y2"] + DY_A, g["w"], "F.Cu", g["net"], g["uuid"]))
    nv = B.del_vias(lambda v: v["net"] == "GND" and abs(v["x"] - 119.75) < 0.01 and abs(v["y"] - 74.85) < 0.01)
    assert nv == 1
    B.add_via((119.35, 75.05), "GND")
for c in ("C112", "C113", "C114", "C115", "C116", "C117"): B.s = fplib.set_pad_clearance(B.s, c, {"2": 0.5})
for r in ("R100", "R101", "R102", "R103", "R104", "R105"): B.s = fplib.set_pad_clearance(B.s, r, {"1": 0.5})

# ---------------------------------------------------------------- F13
def zone_text(net, layer, prio, pts):
    xy = " ".join(f"(xy {fmt(x)} {fmt(y)})" for x, y in pts)
    return (f'\t(zone\n\t\t(net "{net}")\n\t\t(layer "{layer}")\n\t\t(uuid "{uuid.uuid4()}")\n\t\t(hatch none 0.5)\n'
            f'\t\t(priority {prio})\n\t\t(connect_pads yes\n\t\t\t(clearance 0.6)\n\t\t)\n\t\t(min_thickness 0.25)\n'
            f'\t\t(fill yes\n\t\t\t(thermal_gap 0.5)\n\t\t\t(thermal_bridge_width 0.5)\n\t\t\t(smoothing fillet)\n\t\t\t(radius 1)\n'
            f'\t\t\t(island_removal_mode 0)\n\t\t)\n\t\t(polygon\n\t\t\t(pts\n\t\t\t\t{xy}\n\t\t\t)\n\t\t)\n\t)\n')
new_z = ""
for x0, x1 in ((121.85, 129.5), (138.85, 146.5), (155.85, 163.5)):     # GND strips end at 121.25 / 138.25 / 155.25
    yt = 72.0 if S3 else 71.0
    new_z += zone_text("VDC", "B.Cu", 9, [(x0, yt), (x1, yt), (x1, 73.65), (x0, 73.65)])   # node zones start at 74.25
B.save()
s = open(fn, encoding="utf-8").read()
k = s.find("\n\t(zone\n") + 1
s = s[:k] + new_z + s[k:]

# ---------------------------------------------------------------- F14
SLOTS = [(119.0, 95.5), (166.5, 95.5)]; R = 2.75 + 1.5; NSEG = 24
def inside(poly, x, y):
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
    return c
def seg_circle(p, q, cx, cy, r):
    """parameters t in (0,1) where segment p-q crosses the circle"""
    dx, dy = q[0]-p[0], q[1]-p[1]; fx, fy = p[0]-cx, p[1]-cy
    a = dx*dx + dy*dy; b = 2*(fx*dx + fy*dy); c = fx*fx + fy*fy - r*r
    D = b*b - 4*a*c
    if a == 0 or D <= 0: return []
    sq = math.sqrt(D); return sorted(t for t in ((-b - sq)/(2*a), (-b + sq)/(2*a)) if 1e-9 < t < 1 - 1e-9)
def minus_circle(poly, cx, cy, r):
    """polygon minus a circle that cuts its boundary in exactly two points"""
    pts = []
    for p, q in zip(poly, poly[1:] + poly[:1]):
        pts.append((p, False))
        for t in seg_circle(p, q, cx, cy, r): pts.append(((p[0] + t*(q[0]-p[0]), p[1] + t*(q[1]-p[1])), True))
    ks = [i for i, (p, f) in enumerate(pts) if f]
    if len(ks) != 2: return None
    n = len(pts); i0, i1 = ks
    a_, b_ = pts[i0][0], pts[(i0 + 1) % n][0]; mid = ((a_[0] + b_[0])/2, (a_[1] + b_[1])/2)
    if math.hypot(mid[0]-cx, mid[1]-cy) < r: i0, i1 = i1, i0          # i0 -> i1 must run outside
    out = []; i = i0
    while True:
        out.append(pts[i][0])
        if i == i1: break
        i = (i + 1) % n
    # close along the arc from the entry point back to the exit point, through the polygon interior
    a1 = math.atan2(out[-1][1]-cy, out[-1][0]-cx); a0 = math.atan2(out[0][1]-cy, out[0][0]-cx)
    for sgn in (1, -1):
        span = (a0 - a1) % (2*math.pi) if sgn > 0 else -((a1 - a0) % (2*math.pi))
        am = a1 + span/2
        if inside(poly, cx + r*math.cos(am), cy + r*math.sin(am)): break
    return out + [(cx + r*math.cos(a1 + span*k/NSEG), cy + r*math.sin(a1 + span*k/NSEG)) for k in range(1, NSEG)]
n = 0; res = []; last = 0
for m in re.finditer(r'\n\t\(zone\n.*?\n\t\)', s, re.S):
    t = m.group(0)
    if '(layer "B.Mask")' not in t: continue
    pm = re.search(r'\n\t\t\(polygon\n\t\t\t\(pts\n(.*?)\n\t\t\t\)\n\t\t\)', t, re.S)
    poly = [(float(a), float(b)) for a, b in re.findall(r'\(xy ([\d.\-]+) ([\d.\-]+)\)', pm.group(1))]
    changed = False
    for cx, cy in SLOTS:
        if all(math.hypot(x-cx, y-cy) > R for x, y in poly) and not any(seg_circle(p, q, cx, cy, R) for p, q in zip(poly, poly[1:] + poly[:1])):
            continue
        new = minus_circle(poly, cx, cy, R); assert new, ("slot", cx, cy)
        poly = new; changed = True
    if not changed: continue
    body = "\t\t\t\t" + " ".join(f"(xy {fmt(x)} {fmt(y)})" for x, y in poly)
    t2 = t[:pm.start(1)] + body + t[pm.end(1):]
    t2 = re.sub(r'\n\t\t\(filled_polygon.*?\n\t\t\)', '', t2, flags=re.S)
    res.append(s[last:m.start()]); res.append(t2); last = m.end(); n += 1
res.append(s[last:]); s = "".join(res)
open(fn, "w", encoding="utf-8").write(s)
print("B.Cu VDC zones added: 3; B.Mask zones cut at the slots:", n)
