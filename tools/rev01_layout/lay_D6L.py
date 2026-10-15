"""D6 left side (phase A): as lay_D5L shifted +12 mm (same surroundings: C8, D5 branch, U3-+ via).
Differences: the inputs come from the left along y 114.5/115.25, R120/R123 a little higher (ADC lines below),
C3 keeps no own via (the F.Cu diagonal to (150.75,112.75) would hit D35); instead a GND via under the D6 body
next to pin 3. NTC A In3 moved under the driver body, LO A lane jogs to x 149.5 and ends at the LO via."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1])
F, I3 = "F.Cu", "In3.Cu"
LO, LD = "/Driver_1/LO", "/Driver_1/LO_DRV"
HI, LI, CH, CHN = "Net-(D6-HI)", "Net-(D6-LI)", "/TMR1_CH1", "/TMR1_CH1N"
NTC = "Net-(U3-+)"
near = lambda a, b, t=0.03: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t
on = lambda g, a, b: (near((g["x1"], g["y1"]), a) and near((g["x2"], g["y2"]), b)) or (near((g["x1"], g["y1"]), b) and near((g["x2"], g["y2"]), a))
# --- removals
B.del_segs(lambda g: g["net"] == LO and g["layer"] == F and on(g, (150.8, 109.16), (152.28, 109.16)))
B.del_vias(lambda v: v["net"] == LO and near((v["x"], v["y"]), (150.8, 109.16)))
B.del_segs(lambda g: g["net"] == LO and g["layer"] == I3 and (on(g, (150.8, 109.16), (150.0, 108.36)) or on(g, (150.0, 108.36), (150.0, 93.75))))
B.del_segs(lambda g: g["net"] == "GND" and g["layer"] == F and (on(g, (152.28, 107.89), (150.91, 107.89)) or on(g, (150.91, 107.89), (150.85, 107.95))
                                                                 or on(g, (150.75, 112.75), (151.96, 112.75)) or on(g, (151.96, 112.75), (153.71, 111.0))))
B.del_vias(lambda v: v["net"] == "GND" and near((v["x"], v["y"]), (150.85, 107.95)))
B.del_segs(lambda g: g["net"] == NTC and g["layer"] == I3 and min(g["x1"], g["x2"]) > 148.3 and max(g["x1"], g["x2"]) < 155 and 101.9 < min(g["y1"], g["y2"]) and max(g["y1"], g["y2"]) < 110.3)
B.del_segs(lambda g: g["net"] == CH and g["layer"] == F and min(g["x1"], g["x2"]) >= 148.0 and min(g["y1"], g["y2"]) > 105)
B.del_segs(lambda g: g["net"] == CHN and g["layer"] == F and min(g["x1"], g["x2"]) >= 148.0 and min(g["y1"], g["y2"]) > 106)
# --- placements
B.move_fp("C120", 151.4, 104.1, 180)
B.move_fp("C123", 150.55, 107.15, 270)
B.move_fp("R114", 151.5, 110.6, 180)
B.move_fp("D35", 151.55, 112.0, 180)
B.move_fp("R120", 148.1, 112.4, 90)
B.move_fp("R123", 149.4, 112.9, 90)
B.save()
B = Board(sys.argv[1])
# --- In3: NTC A under the D6 body, LO A lane to the new LO via
B.track([(154.25, 102.0), (153.85, 102.4), (153.85, 109.3), (152.65, 110.5), (149.0, 110.5), (148.34, 109.84)], 0.3, I3, NTC)
B.track([(150.0, 93.75), (150.0, 104.0), (149.5, 104.5), (149.5, 108.9), (150.3, 109.7), (150.6, 109.7)], 0.5, I3, LO)
B.add_via((150.6, 109.7), LO)
# --- LO branch
B.track([(152.28, 109.16), (152.41, 109.5), (152.41, 110.6), (152.6, 110.95), (152.6, 112.0)], 0.4, F, LD)
B.track([(150.6, 109.7), (150.59, 110.6), (150.5, 112.0)], 0.4, F, LO)
# --- GND: C123 to pin 3 + via, pin 3 via under the body, C120 via
B.track([(150.55, 108.0125), (151.0, 107.89), (152.28, 107.89)], 0.4, F, "GND")
B.track([(150.55, 108.0125), (150.8, 108.85)], 0.4, F, "GND"); B.add_via((150.8, 108.85), "GND")
B.track([(154.0, 108.5), (154.5, 108.0), (154.8, 108.0)], 0.5, F, "GND"); B.add_via((154.8, 108.0), "GND")
B.track([(152.2625, 104.1), (152.9, 104.0)], 0.4, F, "GND"); B.add_via((152.9, 104.0), "GND")
# --- HI (outer) / LI lanes
B.track([(148.1, 111.4875), (149.03, 110.56), (149.03, 104.6), (149.53, 104.1), (150.5375, 104.1),
         (151.78, 105.34), (152.28, 105.34)], 0.3, F, HI)
B.track([(149.4, 111.9875), (149.72, 111.67), (149.72, 106.61), (152.28, 106.61)], 0.3, F, LI)
# --- inputs
B.track([(148.04, 114.5), (148.1, 114.44), (148.1, 113.3125)], 0.3, F, CH)
B.track([(148.0, 115.25), (149.4, 113.85)], 0.3, F, CHN)
B.save()
print("lay_D6L applied")
