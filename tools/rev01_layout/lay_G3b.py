"""Review round 1 on rev0.1-gnd (docs/reviews/01, 03, 05): layout fixes.
F1 (S2/E9) Temp_PCB_3 back to In2 (In3 between it and the OCP nets on B.Cu); SWD on In2 from y ~118 down along U6,
   the part at J6 stays on In4 (on In2 it would cut off the FB7 via (121.25, 113.75)) - two new transition vias.
F2 (S4/E5) GND on In1 under the HI inputs of D4/D6: small GND zones above Phase_OUT in priority.
F3 (E6) HO A off the screw cutout: the F.Cu detour (162.6..166.66, 92.4..90.25) and its via go; a branch on In4 along
   y 89.4 under the HS A drain column and a via at R3.1 (as HO C runs on In4 along y 90.65).
Usage: lay_G3b.py board.kicad_pcb"""
import re, sys, os, math, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0]))); sys.dont_write_bytecode = True
import pcbedit
from pcbedit import fmt
fn = sys.argv[1]
B = pcbedit.Board(fn)
def seg_is(g, a, b, tol=2e-3):
    p, q = (g["x1"], g["y1"]), (g["x2"], g["y2"])
    return any(math.hypot(u[0]-a[0], u[1]-a[1]) < tol and math.hypot(v[0]-b[0], v[1]-b[1]) < tol for u, v in ((p, q), (q, p)))
def relayer(net, la, lb, keep=lambda g: False):
    n = 0
    for g in sorted(B.segments(net=net, layer=la), key=lambda g: -g["span"][0]):
        if keep(g): continue
        B.replace_seg(g, pcbedit.seg_text(g["x1"], g["y1"], g["x2"], g["y2"], g["w"], lb, net, g["uuid"])); n += 1
    return n
log = []
# ---- F1
log.append(("Temp_PCB_3 -> In2", relayer("/Temp_PCB_3_MCU", "In4.Cu", "In2.Cu")))
SWC, SWD = "/SWCLK_IN", "/SWDIO_IN"
B.split(SWC, "In4.Cu", (121.25, 118.0), (120.25, 119.0), (120.75, 118.5), "In4.Cu", "In4.Cu")
B.split(SWD, "In4.Cu", (122.0, 113.439339), (122.0, 124.25), (122.0, 117.75), "In4.Cu", "In4.Cu")
top_c = [((119.573503, 113.14), (121.25, 114.816497)), ((121.25, 114.816497), (121.25, 118.0)), ((121.25, 118.0), (120.75, 118.5))]
top_d = [((119.5, 111.87), (120.430661, 111.87)), ((120.430661, 111.87), (122.0, 113.439339)), ((122.0, 113.439339), (122.0, 117.75))]
log.append(("SWCLK -> In2 below y 118.5", relayer(SWC, "In4.Cu", "In2.Cu", keep=lambda g: any(seg_is(g, a, b) for a, b in top_c))))
log.append(("SWDIO -> In2 below y 117.75", relayer(SWD, "In4.Cu", "In2.Cu", keep=lambda g: any(seg_is(g, a, b) for a, b in top_d))))
B.add_via((120.75, 118.5), SWC); B.add_via((122.0, 117.75), SWD)
# ---- F3
HO = "/Driver_1/HO"
gone = [((162.1, 92.9), (162.6, 92.4)), ((162.6, 92.4), (165.56, 92.4)), ((165.56, 92.4), (166.66, 91.3)), ((166.66, 91.3), (166.66, 90.25)),
        ((161.6, 92.4), (162.1, 92.9)), ((162.1, 92.9), (161.75, 93.25))]
k = B.del_segs(lambda g: g["net"] == HO and any(seg_is(g, a, b) for a, b in gone)); assert k == 6, k
k = B.del_vias(lambda v: v["net"] == HO and abs(v["x"] - 162.1) < 1e-3 and abs(v["y"] - 92.9) < 1e-3); assert k == 1, k
B.split(HO, "In4.Cu", (161.6, 85.3), (161.6, 92.4), (161.6, 89.4), "In4.Cu", "In4.Cu")
B.track([(161.6, 92.4), (161.6, 93.1), (161.75, 93.25)], 0.3, "In4.Cu", HO)
B.track([(161.6, 89.4), (166.66, 89.4)], 0.3, "In4.Cu", HO)
B.add_via((166.66, 89.4), HO)
B.track([(166.66, 89.4), (166.66, 90.25)], 0.4, "F.Cu", HO)
log.append(("HO A rerouted", 1))
# ---- F7 (E7/S6): Kelvin pairs of the shunts get the same surroundings in all phases. NTC lines B/A below the block
# go to In2 (In3 between them and the Kelvin lines on B.Cu); the +3.3V NTC lines they used to cross hop to In4 and
# drop into the +3.3V plane with a via; the +12V drop of phase A runs on the shunt axis x 154.7 as in C (130.7) and
# B (142.75); the GND via (154.8, 108.0) under U12 moves to (155.7, 108.0).
log.append(("U2+ -> In2", relayer("Net-(U2-+)", "In4.Cu", "In2.Cu")))
log.append(("U3+ -> In2", relayer("Net-(U3-+)", "In4.Cu", "In2.Cu")))
k = B.del_vias(lambda v: v["net"] == "Net-(U3-+)" and abs(v["x"] - 159.5) < 1e-3 and abs(v["y"] - 102.0) < 1e-3); assert k == 1
# +3.3V NTC B: on In2, dips to In4 between (147.2, 100.85) and (147.2, 103.6) where U2+ crosses on In2 (the driver
# side below has no free spot for a plane via); +3.3V NTC A: from (159.26, 101.25) on In4 into the plane at (156.4, 104.5)
B.split("+3.3V", "In2.Cu", (147.2, 93.05), (147.2, 105.0), (147.2, 100.85), "In2.Cu", "In2.Cu")
B.split("+3.3V", "In2.Cu", (147.2, 100.85), (147.2, 105.0), (147.2, 103.6), "In4.Cu", "In2.Cu")
P33 = [((159.26, 101.25), (158.292, 101.25)), ((158.292, 101.25), (157.5, 102.042))]
n = 0
for g in sorted(B.segments(net="+3.3V", layer="In2.Cu"), key=lambda g: -g["span"][0]):
    if any(seg_is(g, a, b) for a, b in P33):
        B.replace_seg(g, pcbedit.seg_text(g["x1"], g["y1"], g["x2"], g["y2"], g["w"], "In4.Cu", "+3.3V", g["uuid"])); n += 1
assert n == 2, n
k = B.del_segs(lambda g: g["net"] == "+3.3V" and g["layer"] == "In2.Cu" and seg_is(g, (157.5, 102.042), (157.5, 104.8))); assert k == 1, k
B.track([(157.5, 102.042), (157.5, 103.4), (156.4, 104.5)], 0.3, "In4.Cu", "+3.3V")
for xy in ((147.2, 100.85), (147.2, 103.6), (159.26, 101.25), (156.4, 104.5)): B.add_via(xy, "+3.3V")
log.append(("+3.3V NTC B/A crossings -> In4, vias", n))
gone12 = [((154.7, 103.25), (156.0, 104.55)), ((156.0, 104.55), (156.0, 109.5)), ((156.0, 109.5), (155.28, 110.22))]
k = B.del_segs(lambda g: g["net"] == "+12V" and g["layer"] == "In4.Cu" and any(seg_is(g, a, b) for a, b in gone12)); assert k == 3, k
B.track([(154.7, 103.25), (154.7, 109.64), (155.28, 110.22)], 1.0, "In4.Cu", "+12V")
k = B.del_vias(lambda v: v["net"] == "GND" and abs(v["x"] - 154.8) < 1e-3 and abs(v["y"] - 108.0) < 1e-3); assert k == 1
k = B.del_segs(lambda g: g["net"] == "GND" and g["layer"] == "F.Cu" and seg_is(g, (154.5, 108.0), (154.8, 108.0))); assert k == 1
B.track([(154.5, 108.0), (155.7, 108.0)], 0.3, "F.Cu", "GND"); B.add_via((155.7, 108.0), "GND")
log.append(("+12V A drop on the shunt axis", 1))
B.save()
# ---- F2: GND zones on In1 under HI of D4 and D6 (Phase_OUT C prio 5, A prio 14 on In1/In2/In4)
s = open(fn, encoding="utf-8").read()
tpl = re.search(r'\n\t\(zone\n\t\t\(net "GND"\)\n\t\t\(layers "In1.Cu" "In3.Cu" "In4.Cu"\).*?\n\t\)', s, re.S).group(0)
tpl = re.sub(r'\n\t\t\(filled_polygon.*?\n\t\t\)', '', tpl, flags=re.S)
def zone(pts, name):
    z = tpl.replace('(layers "In1.Cu" "In3.Cu" "In4.Cu")', '(layer "In1.Cu")').replace("(priority 3)", "(priority 40)")
    z = re.sub(r'\(uuid "[^"]+"\)', f'(uuid "{uuid.uuid4()}")', z, count=1)
    z = z.replace('(hatch none 0.5)', f'(name "{name}")\n\t\t(hatch none 0.5)')
    return re.sub(r'\(pts\n.*?\n\t\t\t\)', "(pts\n\t\t\t\t" + " ".join(f"(xy {fmt(x)} {fmt(y)})" for x, y in pts) + "\n\t\t\t)", z, flags=re.S)
add = zone([(148.9, 103.1), (152.7, 103.1), (152.7, 105.4), (148.9, 105.4)], "GND_under_HI_D6") + \
      zone([(127.6, 103.1), (129.4, 103.1), (129.4, 105.4), (127.6, 105.4)], "GND_under_HI_D4")
k = s.find("\n\t(zone\n"); s = s[:k] + add + s[k:]
open(fn, "w", encoding="utf-8").write(s)
log.append(("In1 GND zones under HI D4/D6", 2))
for l in log: print(*l)
# ---- F6 (E8): GND stitching vias along the edge of the control part (y >= 104) and at the GND pins of J6/J7.
# Candidates on a 0.25 mm grid 0.9-1.5 mm from the outline (and 1.0-1.8 mm from the J6/J7 GND pins); a via is kept
# when In3 and In1 or In4 are GND under it, it clears everything by 0.2 mm, is off every courtyard, and no GND via
# or GND THT pad is within 3 mm (edge) / 1.2 mm (connector).
sys.path.insert(0, "/home/alexey/Git/KiCad/InvertorPowerNewGen/bench_2026-10-13/tools")
import geom, kpcb
from matplotlib.path import Path
G = geom.Board(fn); K = kpcb.load(fn)
gf = {l: [Path(p) for z in K["zones"] if z["net"] == "GND" for ll, p in z["fills"] if ll == l and len(p) > 2] for l in ("In1.Cu", "In3.Cu", "In4.Cu")}
def gnd_on(l, x, y): return all(any(p.contains_point((x + dx, y + dy)) for p in gf[l]) for dx, dy in ((0.45, 0), (-0.45, 0), (0, 0.45), (0, -0.45)))
crts = [c for f in G.fps.values() for c in [f.placed()[1]] if c and c[2] - c[0] > 0.01]
gnd_pts = [(v["x"], v["y"]) for v in G.vias if v["net"] == "GND"] + \
          [(p["x"], p["y"]) for f in G.fps.values() for p in f.placed()[0] if p["net"] == "GND" and p["tht"]]
def edge_d(x, y): return min(geom.d_pt_seg(x, y, *e) for e in G.edge)
def ok(x, y, near):
    if any(c[0] - 0.3 <= x <= c[2] + 0.3 and c[1] - 0.3 <= y <= c[3] + 0.3 for c in crts): return False
    if any(math.hypot(px - x, py - y) < near for px, py in gnd_pts): return False
    if not gnd_on("In3.Cu", x, y) or not (gnd_on("In1.Cu", x, y) or gnd_on("In4.Cu", x, y)): return False
    return not G.check_items(vias=[dict(x=x, y=y, net="GND", size=0.6, d=0.3)])
new = []
cand = []
y = 104.0
while y <= 144.5:
    x = 116.25
    while x <= 169.25:
        d = edge_d(x, y)
        if 0.9 <= d <= 1.5: cand.append((abs(d - 1.1), x, y))
        x += 0.25
    y += 0.25
for _, x, y in sorted(cand):
    if ok(x, y, 3.0): new.append((x, y)); gnd_pts.append((x, y))
n_edge = len(new)
for r in ("J6", "J7"):
    pins = [p for p in G.fps[r].placed()[0] if p["net"] == "GND"]
    got = 0
    for p in pins:
        for a in range(0, 360, 15):
            for rr in (1.0, 1.4, 1.8):
                x, y = round(p["x"] + rr*math.cos(math.radians(a)), 3), round(p["y"] + rr*math.sin(math.radians(a)), 3)
                if got < 4 and ok(x, y, 1.2): new.append((x, y)); gnd_pts.append((x, y)); got += 1
B = pcbedit.Board(fn)
for x, y in new:   # free via: no tracks, KiCad must keep its net
    B.added.append(pcbedit.via_text(x, y, "GND").replace('(layers "F.Cu" "B.Cu")\n', '(layers "F.Cu" "B.Cu")\n\t\t(free yes)\n'))
B.save()
print("F6 stitching vias: edge", n_edge, "connectors", len(new) - n_edge, [(round(x, 2), round(y, 2)) for x, y in new])
# ---- F8 (S5/E9): second GND via for the In4 GND island under U4/U9 (55 mm2, one via after F7); found by a search over
# the filled board (clear of all copper, off the F.Cu courtyards). The other islands have 2 vias or no free spot.
B = pcbedit.Board(fn)
B.added.append(pcbedit.via_text(138.45, 103.38, "GND").replace('(layers "F.Cu" "B.Cu")\n', '(layers "F.Cu" "B.Cu")\n\t\t(free yes)\n'))
B.save(); print("F8 island via (138.45, 103.38)")
# ---- F9 (P5): clearances of exposed pads for the 72-84 V variant.
# C124/C128 (with the VDC via and both stubs) +0.3 mm in x: the VDC pad clears R19.2/C100.1 and R30.2/C104.1 by 0.53 mm,
# the GND pad goes deeper into the GND strip of the next phase. The bootstrap caps C7/C8/C9 -0.3 mm in x: the HI tracks
# of the next driver clear them by 0.53 mm (all track ends stay inside the pads; C9 for the symmetry of the phases).
B = pcbedit.Board(fn)
for ref, x0, vv, vg in (("C124", 132.35, 131.787, 132.912), ("C128", 149.35, 148.787, 149.912)):
    B.move_fp(ref, x0 + 0.3, 82.15)
    k = B.del_segs(lambda g: g["layer"] == "F.Cu" and (seg_is(g, (x0 - 1.1, 82.15), (vv, 81.15)) or seg_is(g, (x0 + 1.1, 82.15), (vg, 81.15)))); assert k == 2, (ref, k)
    k = B.del_vias(lambda v: abs(v["y"] - 81.15) < 1e-3 and abs(v["x"] - vv) < 2e-3); assert k == 1, (ref, k)
    B.track([(x0 - 0.8, 82.15), (vv + 0.3, 81.15)], 0.5, "F.Cu", "VDC"); B.add_via((vv + 0.3, 81.15), "VDC")
    B.track([(x0 + 1.4, 82.15), (vg, 81.15)], 0.5, "F.Cu", "GND")      # GND via stays (C106.1 / C110.1 next to it)
for ref, x0 in (("C7", 135.75), ("C8", 147.75), ("C9", 159.75)):
    B.move_fp(ref, x0 - 0.3, 106.75)
B.save(); print("F9 C124/C128 +0.3, C7/C8/C9 -0.3")
# ---- F10 (P1): C132 (phase A, no GND strip next to its GND pad) gets a second GND via at the inner edge of the pad,
# next to the existing one at (167.21, 81.15); outside the pad there is no other free spot (edge, Q3/Q12, C108).
B = pcbedit.Board(fn)
B.track([(167.75, 82.15), (167.313, 82.15)], 0.5, "F.Cu", "GND"); B.add_via((167.313, 82.15), "GND")
B.save(); print("F10 C132 second GND via (167.313, 82.15)")
