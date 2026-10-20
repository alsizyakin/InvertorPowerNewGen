"""Owner 2026-10-20: lines in passage B (In2) re-laid tighter, fewer vias; track corners and widths cleaned up.
Usage: lay_P4h.py board
F28 passage B on In2: the order was +3.3V (x 147.2) | U2+ (148.25, 0.5 mm) | HO (149.25); +3.3V crossed U2+ at the
    bottom by a hop to In4 (vias (147.2, 100.85) / (147.2, 103.6)). Now U2+ | +3.3V | HO at x 148.15 / 148.7 / 149.25
    (gaps 0.25), all 0.3 mm:
    - top: the two vias swap nets - U2+ drops at (146.55, 92.4), +3.3V runs on In1 under that via and drops at
      (147.6, 92.3) (C105 / R32 / R2 on F.Cu leave no other spots); HO via (148.5, 92.0) stays (SW on In4 x 149.25);
    - bottom: U2+ turns left above +3.3V and runs along the top edge of the +3.3V plane (y 104.25) instead of across the
      Phase_OUT B polygon (y 102.25, 90-degree corner at (141.85, 102.25), 0.5 -> 0.3 mm); +3.3V goes down into its
      plane at x 147.75; the HO via moves (148.1, 104.0) -> (148.45, 103.95), clear of SW on In4, of +3.3V and of C8.
    Vias 6 -> 4. The Phase_OUT B copper on In2 right of J2 gets ~1 mm along the passage and the strip under the old U2+
    line (y 102.5-104) joins it; In4 loses the +3.3V hop.
F29 corners and widths (scan with joints matched within 0.02 mm): 45-degree jogs shorter than 0.3 mm that made a
    90-degree turn, and width changes at free joints:
    /TMR1_CH1 F.Cu (148.1, 114.44); /Driver_3/LO In4 at the T (122.0, 91.0), 0.3 -> 0.5; GND F.Cu (154.5, 108.0) 0.3 -> 0.5;
    /CAN1_TXD_MCU F.Cu (129.75, 133.5) (rev0)."""
import sys, os, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import pcbedit
fn = sys.argv[1]
B = pcbedit.Board(fn)
if any(abs(v["x"] - 148.45) < 1e-3 and abs(v["y"] - 103.95) < 1e-3 for v in B.vias("/Driver_2/HO")): sys.exit("lay_P4h: already applied")

def near(p, q, t=0.02): return abs(p[0] - q[0]) < t and abs(p[1] - q[1]) < t
def drop(net, layer, pts):
    """delete the segments of `net` on `layer` whose both ends are in `pts` (within 0.02)"""
    n = B.del_segs(lambda g: g["net"] == net and g["layer"] == layer and any(near((g["x1"], g["y1"]), p) for p in pts)
                   and any(near((g["x2"], g["y2"]), p) for p in pts))
    return n
def drop_via(net, p):
    assert B.del_vias(lambda v: v["net"] == net and near((v["x"], v["y"]), p)) == 1, (net, p)

# ---------------------------------------------------------------- F28
U, P3, HO = "Net-(U2-+)", "+3.3V", "/Driver_2/HO"
assert drop(P3, "In1.Cu", [(146.0, 92.4), (146.55, 92.4)]) == 1
assert drop(P3, "In1.Cu", [(144.2, 90.6), (146.0, 92.4)]) == 1
B.track([(144.2, 90.6), (145.6, 92.0)], 0.3, "In1.Cu", P3)
assert drop(P3, "In2.Cu", [(146.55, 92.4), (147.2, 93.05), (147.2, 100.85), (147.2, 103.6), (147.2, 105.0)]) == 3
assert drop(P3, "In4.Cu", [(147.2, 100.85), (147.2, 103.6)]) == 1
for p in ((146.55, 92.4), (147.2, 100.85), (147.2, 103.6)): drop_via(P3, p)
assert drop(U, "In1.Cu", [(146.35, 91.6), (146.9, 91.6), (147.6, 92.3)]) == 2
assert drop(U, "In2.Cu", [(147.6, 92.3), (148.25, 92.95), (148.25, 93.25), (148.25, 101.0), (147.0, 102.25),
                          (141.925, 102.25), (141.93, 102.25), (141.85, 102.33), (141.85, 109.3)]) == 7
drop_via(U, (147.6, 92.3))
assert drop(HO, "In2.Cu", [(149.25, 92.75), (149.25, 102.85), (148.1, 104.0)]) == 2
assert drop(HO, "B.Cu", [(148.1, 104.0), (148.1, 105.09), (147.5512, 105.6388), (148.625, 105.615)]) == 3
drop_via(HO, (148.1, 104.0))

W = 0.3
# In1: +3.3V passes under the U2+ via and climbs to its own via (the old U2+ via spot); U2+ drops at the old +3.3V spot
B.track([(145.6, 92.0), (145.6, 92.6), (146.15, 93.15), (147.0, 93.15), (147.6, 92.55), (147.6, 92.3)], W, "In1.Cu", P3)
B.add_via((147.6, 92.3), P3)
B.track([(146.35, 91.6), (146.55, 91.8), (146.55, 92.4)], W, "In1.Cu", U); B.add_via((146.55, 92.4), U)
# In2: U2+ | +3.3V | HO
B.track([(146.55, 92.4), (148.15, 94.0), (148.15, 101.95), (145.85, 104.25), (142.35, 104.25), (141.85, 104.75),
         (141.85, 109.3)], W, "In2.Cu", U)
B.track([(147.6, 92.3), (148.7, 93.4), (148.7, 102.7), (147.75, 103.65), (147.75, 105.0)], W, "In2.Cu", P3)
B.track([(149.25, 92.75), (149.25, 103.15), (148.45, 103.95)], W, "In2.Cu", HO); B.add_via((148.45, 103.95), HO)
B.track([(148.45, 103.95), (148.45, 104.9), (148.75, 105.2)], 0.4, "B.Cu", HO)
B.track([(148.45, 104.9), (147.7, 105.65)], 0.4, "B.Cu", HO)

# ---------------------------------------------------------------- F29
def swap(net, layer, old_pts, new_pts, w, n_old):
    assert drop(net, layer, old_pts) == n_old, (net, old_pts)
    B.track(new_pts, w, layer, net)
swap("/TMR1_CH1", "F.Cu", [(140.814626, 114.5), (148.042894, 114.5), (148.04, 114.5), (148.1, 114.44), (148.1, 113.3125)],
     [(140.814626, 114.5), (147.75, 114.5), (148.1, 114.15), (148.1, 113.3125)], 0.3, 3)
swap("/CAN1_TXD_MCU", "F.Cu", [(129.25, 134.0), (129.75, 133.5), (129.725, 133.475), (129.725, 132.405)],
     [(129.25, 134.0), (129.725, 133.525), (129.725, 132.405)], 0.5, 3)
# LO of phase C on In4: the T at (122.0, 91.0) made a zigzag (down-right, down, up-right to the via) and the east branch
# was 0.3 between the node C vias; now the west line runs into the via (122.75, 90.25) and the east branch leaves the
# via straight, 0.5 mm like the rest of the net (0.21 mm to the node via (123.25, 91.75))
swap("/Driver_3/LO", "In4.Cu", [(120.5, 89.25), (122.0, 90.75), (122.0, 91.0), (122.75, 90.25), (122.05, 91.05), (123.5, 91.05),
     (124.0, 91.55), (124.0, 95.85)], [(120.5, 89.25), (121.5, 90.25), (122.75, 90.25), (124.0, 91.5), (124.0, 95.85)], 0.5, 7)
swap("GND", "F.Cu", [(154.5, 108.0), (155.7, 108.0)], [(154.5, 108.0), (155.7, 108.0)], 0.5, 1)
B.save()
print("F28: passage B re-laid (vias 6 -> 4)")
