"""rev0.1-ina-ref, step I1 (owner 2026-10-21: «делаем»). Usage: lay_I1.py board
Applies to the board of e2db9a1 (the owner's hand reroute of the MCU zone is not in shift3.sh).
I1 +12V off In4 under the INA240s U4 / U9 / U12 (B.Cu), so that In4 under the shunt amplifiers is GND:
   - the trunk from J6 and the D1 riser go to In2, between the In1 and In3 grounds;
   - the D2 / D3 risers go to In1 (on In2 they would cross the thermistor lines B / C) and step down to the In2 trunk
     through a via under the U9 / U12 body (tented, between the pin rows).
I2 +3.3V: the trunk on In2 cuts the +3.3V pour; the two parts above it feed TH1 and TH2 / TH3. One jumper through
   In1 per part (fixed paths, checked with geom.check_items):
   - TH1: from its via (123.6, 104.7) on In1 down x 123.2, half way between VDC_MCU (F.Cu x 122.0) and U1+ (F.Cu
     x 124.34), so that neither loses In1 ground; across VDC_MCU at 45 degrees to the +3.3V via (121.1, 111.13) of the
     pour below the trunk (no new via);
   - TH2 / TH3: the part above the trunk reaches the end of the TH3 line (162.7, 104.7) along the edge of the phase
     copper; a via there, In1 straight down past the U3+ line, a via in the right part of the pour. Kept away from the
     HO / SW vias of phase B (a jumper from the TH2 line would sit 0.2 mm from them). Between the SW track of phase A
     (F.Cu x 161.8) and the U3+ line (x 163.3) a via fits at x 162.45-162.65 only: the TH3 line moves from x 162.7 to
     162.65 (its vertical run on In2 and the 45-degree piece above it)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import pcbedit, geom
fn = sys.argv[1]
B = pcbedit.Board(fn)
P12 = "+12V"; P33 = "+3.3V"
if any(True for _ in B.segments(P12, "In2.Cu")):
    sys.exit("lay_I1: already applied")

# ---------------------------------------------------------------- I1
D2_RISER = ((142.75, 110.25), (142.75, 103.30)); D2_VIA = (142.75, 109.6)
D3_RISER = ((154.70, 103.25), (154.70, 109.64)); D3_VIA = (154.70, 109.64)
segs = list(B.segments(P12, "In4.Cu"))
assert len(segs) == 33, len(segs)
for g in sorted(segs, key=lambda g: -g["span"][0]):        # from the end of the file: spans stay valid
    ends = {(round(g["x1"], 2), round(g["y1"], 2)), (round(g["x2"], 2), round(g["y2"], 2))}
    if ends == set(D2_RISER):                               # In1 from the anode via down to the via, In2 stub to the trunk
        B.replace_seg(g, pcbedit.seg_text(*D2_RISER[1], *D2_VIA, g["w"], "In1.Cu", P12, g["uuid"])
                         + pcbedit.seg_text(*D2_VIA, *D2_RISER[0], g["w"], "In2.Cu", P12))
    elif ends == set(D3_RISER):
        B.replace_seg(g, pcbedit.seg_text(g["x1"], g["y1"], g["x2"], g["y2"], g["w"], "In1.Cu", P12, g["uuid"]))
    else:
        B.replace_seg(g, pcbedit.seg_text(g["x1"], g["y1"], g["x2"], g["y2"], g["w"], "In2.Cu", P12, g["uuid"]))
B.add_via(D2_VIA, P12); B.add_via(D3_VIA, P12)
B.save()

# ---------------------------------------------------------------- I2
B = pcbedit.Board(fn)
g = B.find_seg(P33, "In2.Cu", (161.25, 91.60), (162.70, 93.05))
B.replace_seg(g, pcbedit.seg_text(161.25, 91.60, 162.65, 93.00, g["w"], "In2.Cu", P33, g["uuid"]))
g = B.find_seg(P33, "In2.Cu", (162.70, 93.05), (162.70, 104.70))
B.replace_seg(g, pcbedit.seg_text(162.65, 93.00, 162.65, 104.70, g["w"], "In2.Cu", P33, g["uuid"]))
B.save()
B = pcbedit.Board(fn); G = geom.Board(fn)
JUMPERS = [([(123.6, 104.7), (123.2, 105.1), (123.2, 109.9), (121.97, 111.13), (121.1, 111.13)], []),  # TH1
           ([(162.65, 104.7), (162.65, 106.9)], [(162.65, 104.7), (162.65, 106.9)])]              # TH2 / TH3
for pts, vias in JUMPERS:
    bad = G.check_items(vias=[geom.V(x, y, P33) for x, y in vias], segs=geom.P(pts, 0.3, "In1.Cu", P33))
    assert not bad, bad
    B.track(pts, 0.3, "In1.Cu", P33)
    for v in vias: B.add_via(v, P33)
B.save()
