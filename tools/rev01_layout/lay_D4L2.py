"""D4 left, part 2: free the input channel (GND vias moved), cut inputs for R118/R121 (series) placement."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1])
F, BC = "F.Cu", "B.Cu"
near = lambda a, b, t=0.03: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t
on = lambda g, a, b: (near((g["x1"], g["y1"]), a) and near((g["x2"], g["y2"]), b)) or (near((g["x1"], g["y1"]), b) and near((g["x2"], g["y2"]), a))
# D4 pin-3 GND via: from the channel (126.75,108.0) to under the driver body (130.3,107.4)
B.del_segs(lambda g: g["net"] == "GND" and g["layer"] == F and (on(g, (128.28, 107.89), (126.86, 107.89)) or on(g, (126.86, 107.89), (126.75, 108.0))))
B.del_vias(lambda v: v["net"] == "GND" and near((v["x"], v["y"]), (126.75, 108.0)))
B.track([(129.385, 107.885), (129.7, 107.55), (129.7, 107.15)], 0.5, F, "GND"); B.add_via((129.7, 107.15), "GND")
# R67/C74 GND via: (126.75,112.75) -> (125.4,113.4)
B.del_segs(lambda g: g["net"] == "GND" and g["layer"] == F and (on(g, (124.41, 112.5), (126.5, 112.5)) or on(g, (126.5, 112.5), (126.75, 112.75))))
B.del_segs(lambda g: g["net"] == "GND" and g["layer"] == BC and on(g, (126.25, 112.25), (126.75, 112.75)))
B.del_vias(lambda v: v["net"] == "GND" and near((v["x"], v["y"]), (126.75, 112.75)))
B.del_segs(lambda g: g["net"] == "GND" and g["layer"] == F and on(g, (124.41, 112.5), (124.41, 114.2)))
B.move_fp("R67", 123.25, 112.5, 0); B.move_fp("C74", 123.25, 114.25, 0)
B.track([(124.16, 112.5), (124.16, 114.25)], 0.5, F, "GND")
B.track([(124.16, 113.3), (125.15, 113.15)], 0.5, F, "GND"); B.add_via((125.15, 113.15), "GND")
# inputs: remove the parts near the driver (already cut in the work copy) -- idempotent
B.del_segs(lambda g: g["net"] == "/TMR1_CH3" and g["layer"] == F and max(g["y1"], g["y2"]) <= 115.01 and min(g["x1"], g["x2"]) < 131)
B.del_segs(lambda g: g["net"] == "/TMR1_CH3N" and g["layer"] == F and max(g["y1"], g["y2"]) <= 114.76 and min(g["x1"], g["x2"]) < 131.5)
B.move_fp("R118", 125.45, 111.1, 90)
B.move_fp("R121", 126.75, 111.1, 90)
B.save()
print("lay_D4L2 base applied")
