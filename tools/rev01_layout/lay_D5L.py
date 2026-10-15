"""D5 left side (phase B). The channel between C7 and the D5 pins carries HI (outer) and LI; C119 above pin 1,
C122 between the LI lane and pin 2 (GND to pin 3 + via), R119/R122 below-left on the input lines.
LO-D5 branch R113 || D34 horizontal under the left pins, LO via at the channel bottom, In3 LO lane extended to it.
TH2 +3.3 moved from In3 to In2 (In2 below the bushings is the +3.3 plane); NTC In3 shifted under the driver body."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1])
F, I2, I3 = "F.Cu", "In2.Cu", "In3.Cu"
LO, LD = "/Driver_2/LO", "/Driver_2/LO_DRV"
HI, LI, CH, CHN = "Net-(D5-HI)", "Net-(D5-LI)", "/TMR1_CH2", "/TMR1_CH2N"
TH33, NTC = "+3.3V", "Net-(U2-+)"
near = lambda a, b, t=0.03: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t
on = lambda g, a, b: (near((g["x1"], g["y1"]), a) and near((g["x2"], g["y2"]), b)) or (near((g["x1"], g["y1"]), b) and near((g["x2"], g["y2"]), a))
# --- removals
B.del_segs(lambda g: g["net"] == LO and g["layer"] == F and min(g["x1"], g["x2"]) > 138.5 and min(g["y1"], g["y2"]) > 108.5)
B.del_vias(lambda v: v["net"] == LO and near((v["x"], v["y"]), (138.8, 109.15)))
B.del_segs(lambda g: g["net"] == LO and g["layer"] == I3 and on(g, (138.8, 109.15), (137.5, 107.85)))
B.del_segs(lambda g: g["net"] == "GND" and g["layer"] == F and (on(g, (140.28, 107.89), (139.98, 108.18)) or on(g, (139.98, 108.18), (138.82, 108.18))))
B.del_vias(lambda v: v["net"] == "GND" and near((v["x"], v["y"]), (138.82, 108.18)))
B.del_segs(lambda g: g["net"] == TH33 and g["layer"] == I3 and 139 < min(g["x1"], g["x2"]) and max(g["x1"], g["x2"]) < 148 and 92 < min(g["y1"], g["y2"]) and max(g["y1"], g["y2"]) < 107.5)
B.del_vias(lambda v: v["net"] == TH33 and near((v["x"], v["y"]), (139.0, 107.27)))
B.del_segs(lambda g: g["net"] == NTC and g["layer"] == I3 and 136 < min(g["x1"], g["x2"]) and max(g["x1"], g["x2"]) < 142 and min(g["y1"], g["y2"]) > 102.2 and max(g["y1"], g["y2"]) < 111)
B.del_segs(lambda g: g["net"] == CH and g["layer"] == F and min(g["x1"], g["x2"]) >= 132.0 and max(g["y1"], g["y2"]) <= 117.5 and min(g["y1"], g["y2"]) >= 105)
B.del_segs(lambda g: g["net"] == CHN and g["layer"] == F and min(g["x1"], g["x2"]) >= 131.4 and max(g["y1"], g["y2"]) <= 118.8 and min(g["y1"], g["y2"]) >= 106)
# --- placements
B.move_fp("C119", 139.4, 104.1, 180)     # pad2 HI left (138.54), pad1 GND right (140.26)
B.move_fp("C122", 138.55, 107.15, 270)   # pad1 LI top, pad2 GND bottom
B.move_fp("R113", 139.5, 110.6, 180)     # pad1 LO_DRV right, pad2 LO left
B.move_fp("D34", 139.55, 112.0, 180)     # K (LO_DRV) right, A (LO) left
B.move_fp("R119", 136.1, 112.7, 90)
B.move_fp("R122", 137.4, 113.2, 90)
B.save()
B = Board(sys.argv[1])
# --- In2: TH2 +3.3 from the via under the block straight down passage J2-J3 into the +3.3 plane
B.track([(146.55, 92.4), (147.2, 93.05), (147.2, 105.0)], 0.3, I2, TH33)
# --- In3: NTC under the driver body, LO lane extended to the new LO via
B.track([(141.93, 102.25), (141.85, 102.33), (141.85, 109.3), (140.65, 110.5), (137.0, 110.5), (136.34, 109.84)], 0.3, I3, NTC)
B.track([(137.5, 107.85), (137.5, 108.9), (138.3, 109.7), (138.6, 109.7)], 0.5, I3, LO)
B.add_via((138.6, 109.7), LO)
# --- LO branch
B.track([(140.28, 109.16), (140.41, 109.5), (140.41, 110.6), (140.6, 110.95), (140.6, 112.0)], 0.4, F, LD)
B.track([(138.6, 109.7), (138.59, 110.6), (138.5, 112.0)], 0.4, F, LO)
# --- C122 (LI) and C119 (HI), GND
B.track([(138.55, 108.0125), (139.0, 107.89), (140.28, 107.89)], 0.4, F, "GND")
B.track([(138.55, 108.0125), (138.8, 108.85)], 0.4, F, "GND"); B.add_via((138.8, 108.85), "GND")
B.track([(140.2625, 104.1), (140.9, 104.0)], 0.4, F, "GND"); B.add_via((140.9, 104.0), "GND")
# --- lanes HI (outer) / LI from the series resistors to the pins
B.track([(136.1, 111.7875), (136.1, 111.3), (137.03, 110.37), (137.03, 104.6), (137.53, 104.1), (138.5375, 104.1),
         (139.78, 105.34), (140.28, 105.34)], 0.3, F, HI)
B.track([(137.4, 112.2875), (137.72, 111.97), (137.72, 106.61), (140.28, 106.61)], 0.3, F, LI)
# --- input stubs kept from the old lines
B.track([(132.063173, 117.436827), (135.9, 113.6), (136.1, 113.6125)], 0.3, F, CH)
B.track([(131.5, 118.792893), (135.8, 114.492893), (137.4, 114.49)], 0.3, F, CHN)
B.save()
print("lay_D5L applied")
