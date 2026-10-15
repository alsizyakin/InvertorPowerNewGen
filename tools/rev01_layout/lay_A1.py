"""Phase A, block: as phase C shifted +34 mm (R_gs R36/R38 moved right 0.25). The pair goes straight down
passage A (right of J3): HO on In4 in the block -> In3 below it; SW on In1 all the way (In1 in passage A is node
pour, no GND bridge there; In4 bridge A untouched). TH3 lines on In2 in the block and in the passage (In2 is node
pour there): +3.3 straight into the In2 +3.3 plane under the drivers, NTC -> In3 at the bottom of the passage.
LO A in the block on In4 (R6 via stays, In3 below it)."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1])
I1, I2, I3, I4, F = "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "F.Cu"
HO, SW, LO = "/Driver_1/HO", "/Driver_1/SW", "/Driver_1/LO"
G1, G7 = "Net-(C108-Pad1)", "Net-(C109-Pad1)"
TH33, NTC = "+3.3V", "Net-(U3-+)"
near = lambda a, b, t=0.03: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t
on = lambda g, a, b: (near((g["x1"], g["y1"]), a) and near((g["x2"], g["y2"]), b)) or (near((g["x1"], g["y1"]), b) and near((g["x2"], g["y2"]), a))
# --- removals
B.del_segs(lambda g: g["net"] == HO)
B.del_vias(lambda v: v["net"] == HO)
B.del_vias(lambda v: v["net"] in (TH33, NTC) and (near((v["x"], v["y"]), (158.91, 80.84)) or near((v["x"], v["y"]), (158.91, 82.66))))
B.del_segs(lambda g: g["net"] in (TH33, NTC) and g["layer"] == F and 158 < g["x1"] < 159.5 and 80 < g["y1"] < 83.5)
B.del_segs(lambda g: g["net"] == TH33 and g["layer"] == I3 and min(g["x1"], g["x2"]) >= 151.5 and 80 < min(g["y1"], g["y2"]) and max(g["y1"], g["y2"]) < 108)
B.del_vias(lambda v: v["net"] == TH33 and near((v["x"], v["y"]), (154.0, 107.25)))
B.del_segs(lambda g: g["net"] == NTC and g["layer"] == I3 and min(g["x1"], g["x2"]) >= 159.0 and max(g["y1"], g["y2"]) <= 102.01 and min(g["y1"], g["y2"]) < 101.9)
B.del_segs(lambda g: g["net"] == G1 and on(g, (164.75, 81.5), (163.16, 81.5)))
# --- placements
B.move_fp("R36", 162.5, 81.5, 0)
B.move_fp("R38", 162.5, 90.25, 0)
B.move_fp("TH3", 157.75, 81.75, 90)
B.move_fp("R34", 159.55, 81.5, 90)
B.move_fp("NT3", 161.09, 81.5, 0)
B.move_fp("C108", 162.5, 82.55, 180)
B.move_fp("C109", 162.5, 91.3, 180)
# --- F.Cu
B.track([(161.6, 79.6875), (159.95, 80.588)], 0.5, F, G1)
B.track([(163.39, 81.5), (163.39, 82.55)], 0.3, F, G1)
B.track([(163.39, 90.25), (163.39, 91.3)], 0.3, F, G7)
B.track([(159.55, 82.412), (159.55, 83.25)], 0.4, F, HO); B.add_via((159.55, 83.25), HO)
B.track([(160.59, 81.5), (160.59, 82.4)], 0.3, F, SW); B.add_via((160.59, 82.4), SW)
B.track([(166.66, 90.25), (166.66, 91.3), (165.56, 92.4), (162.6, 92.4), (162.1, 92.9)], 0.4, F, HO)   # R3.1 -> HO via
B.add_via((162.1, 92.9), HO)
B.track([(157.75, 80.838), (158.55, 80.838)], 0.4, F, NTC); B.add_via((158.55, 80.84), NTC)
B.track([(157.75, 82.662), (158.55, 82.662)], 0.4, F, TH33); B.add_via((158.55, 82.66), TH33)
# --- pair: HO In4 in the block -> In3 down passage A; SW In1 all the way (stacked over HO)
# HO crosses y 91.5 on In4 inside the node pour, clear of the GND gap between the node and VDC pours (bridge A)
B.track([(159.55, 83.25), (161.6, 85.3), (161.6, 92.4), (162.1, 92.9)], 0.3, I4, HO)
B.track([(162.1, 92.9), (161.75, 93.25), (161.75, 102.35), (160.1, 104.0)], 0.3, I3, HO)
B.track([(160.59, 82.4), (162.4, 84.21), (162.4, 92.2), (162.85, 92.65), (162.85, 93.35), (161.75, 94.45), (161.75, 103.25),
         (162.25, 103.75)], 0.3, I1, SW)
# --- TH3 lines on In2
B.track([(158.55, 80.84), (162.0, 80.84), (162.0, 91.6), (162.8, 92.4), (162.8, 93.4), (162.0, 94.2), (162.0, 99.5), (159.5, 102.0)], 0.3, I2, NTC); B.add_via((159.5, 102.0), NTC)
B.track([(158.55, 82.66), (158.55, 83.95), (161.25, 83.95), (161.25, 99.26), (159.26, 101.25), (157.5, 101.25), (157.5, 104.8)], 0.3, I2, TH33)
# --- LO A: in-block part of the In3 path -> In4; the diagonal is split at the R6 via (151.25,92.5)
for a, b in [((156.75, 81.5), (156.75, 82.0)), ((156.75, 82.0), (154.5, 84.25)), ((154.5, 84.25), (154.5, 89.25))]:
    B.set_layer(LO, I3, a, b, I4)
B.split(LO, I3, (150.0, 93.75), (154.5, 89.25), (151.25, 92.5), I3, I4)
B.save()
print("lay_A1 applied")
