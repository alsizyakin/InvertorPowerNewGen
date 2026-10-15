"""§6 for D4-D6: HI/LI copper >= 2 mm from node copper on F.Cu.
D4, D6: the HI cap stays above pin 1; F.Cu pour keepouts above the pins reach y 101.6, so the node pour (D4) and
the J3 Phase_OUT pour (D6) stay >= 2 mm from it. D5: above pin 1 sit the node-B via columns of passage J1-J2;
C119 moves next to R119, HI enters pin 1 straight from the lane, the three lowest node vias of the column
(58 -> 55) are removed, F.Cu keepout above the pins."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1]); F = "F.Cu"
near = lambda a, b, t=0.03: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t
on = lambda g, a, b: (near((g["x1"], g["y1"]), a) and near((g["x2"], g["y2"]), b)) or (near((g["x1"], g["y1"]), b) and near((g["x2"], g["y2"]), a))
# D4: enlarge the existing keepout
old = "(xy 122.6 103.2) (xy 129.9 103.2) (xy 129.9 110.2) (xy 122.6 110.2)"
assert old in B.s
B.s = B.s.replace(old, "(xy 122.6 103.2) (xy 125.7 103.2) (xy 125.7 101.6) (xy 130.9 101.6) (xy 130.9 110.2) (xy 122.6 110.2)")
# D5
NB = "/Current_Sensor_2/Phase_IN"
B.del_vias(lambda v: v["net"] == NB and any(near((v["x"], v["y"]), p) for p in ((136.25, 103.0), (136.75, 103.25), (138.25, 103.0))))
B.del_segs(lambda g: g["net"] in ("Net-(D5-HI)", "Net-(D5-LI)", "/TMR1_CH2", "/TMR1_CH2N") and g["layer"] == F and min(g["y1"], g["y2"]) > 103.5
           and min(g["x1"], g["x2"]) > 135.0 and max(g["y1"], g["y2"]) < 114.6)
B.del_segs(lambda g: g["net"] == "GND" and g["layer"] == F and on(g, (140.2625, 104.1), (140.9, 104.0)))
B.del_vias(lambda v: v["net"] == "GND" and near((v["x"], v["y"]), (140.9, 104.0)))
B.move_fp("C119", 135.15, 111.95, 90)     # pad2 HI top, pad1 GND bottom
B.move_fp("R119", 136.35, 112.7, 90)
B.move_fp("R122", 137.5, 113.2, 90)
B.keepout(F, [(134.9, 103.0), (143.3, 103.0), (143.3, 110.2), (134.9, 110.2)], name="HI/LI D5: node pour >= 2 mm")
# D6
B.keepout(F, [(146.9, 101.6), (153.4, 101.6), (153.4, 110.2), (146.9, 110.2)], name="HI/LI D6: Phase_OUT pour >= 2 mm")
B.save()
B = Board(sys.argv[1])
HI, LI = "Net-(D5-HI)", "Net-(D5-LI)"
B.track([(136.35, 111.7875), (136.35, 111.0875), (137.03, 110.41), (137.03, 105.34), (140.28, 105.34)], 0.3, F, HI)
B.track([(135.15, 111.0875), (136.35, 111.0875)], 0.3, F, HI)
B.track([(135.15, 112.8125), (134.5, 113.75)], 0.4, F, "GND")
B.track([(137.5, 112.2875), (137.72, 112.07), (137.72, 106.61), (140.28, 106.61)], 0.3, F, LI)
B.track([(135.9, 113.6), (136.35, 113.6125)], 0.3, F, "/TMR1_CH2")
B.track([(135.8, 114.492893), (137.5, 114.49)], 0.3, F, "/TMR1_CH2N")
B.save()
print("lay_HI applied")
