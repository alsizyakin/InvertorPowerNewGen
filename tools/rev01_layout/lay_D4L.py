"""D4 left side (phase C): NTC lead moved to F.Cu, LO-D4 off-branch on B.Cu left of U4, LO_DRV via, X to the LO In3 path."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1])
F, I3, BC = "F.Cu", "In3.Cu", "B.Cu"
LO, LD, NTC = "/Driver_3/LO", "/Driver_3/LO_DRV", "Net-(U1-+)"
near = lambda a, b, t=0.02: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t
on = lambda g, a, b: (near((g["x1"], g["y1"]), a) and near((g["x2"], g["y2"]), b)) or (near((g["x1"], g["y1"]), b) and near((g["x2"], g["y2"]), a))
# NTC lead: B.Cu (124.34,107.25)-(124.34,110.75) -> F.Cu down to a new via, B.Cu stub to R20.2
B.del_segs(lambda g: g["net"] == NTC and g["layer"] == BC and on(g, (124.34, 107.25), (124.34, 110.75)))
B.track([(124.3375, 107.25), (124.34, 109.7)], 0.4, F, NTC); B.add_via((124.34, 109.7), NTC)
B.track([(124.34, 109.7), (124.34, 110.75)], 0.4, BC, NTC)
# old LO stub / via at pin 4 and the In3 tail towards it
B.del_segs(lambda g: g["net"] == LO and g["layer"] == F and min(g["y1"], g["y2"]) > 108 and min(g["x1"], g["x2"]) > 126)
B.del_vias(lambda v: v["net"] == LO and near((v["x"], v["y"]), (126.8, 109.138), 0.05))
B.del_segs(lambda g: g["net"] == LO and g["layer"] == I3 and (on(g, (126.8, 109.14), (124.39, 109.14)) or on(g, (124.39, 109.14), (122.0, 106.75))
                                                            or on(g, (122.0, 106.75), (122.0, 98.75))))
B.track([(122.0, 103.9), (122.0, 98.75)], 0.5, I3, LO)
# LO_DRV: pin 4 -> via -> B.Cu to the branch
B.track([(128.28, 109.155), (126.8, 109.14)], 0.4, F, LD); B.add_via((126.8, 109.14), LD)
B.flip_fp("R112"); B.flip_fp("D33")
B.move_fp("R112", 121.0, 106.6, 90)
B.move_fp("D33", 122.25, 106.55, 90)
B.save()
B = Board(sys.argv[1])
# B.Cu: LO_DRV via -> bottom pads; X (top pads) -> via -> In3 LO path
B.track([(126.8, 109.14), (126.56, 108.9), (123.0, 108.9), (122.25, 108.15), (122.25, 107.6)], 0.4, BC, LD)
B.track([(122.25, 107.6), (121.0, 107.512)], 0.4, BC, LD)
B.track([(121.0, 105.688), (122.25, 105.5)], 0.4, BC, LO)
B.track([(121.0, 105.688), (121.1, 104.8)], 0.4, BC, LO); B.add_via((121.1, 104.8), LO)
B.track([(121.1, 104.8), (122.0, 103.9)], 0.5, I3, LO)
B.save()
print("lay_D4L applied")
