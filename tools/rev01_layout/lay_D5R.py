"""D5 right side (phase B): as lay_D4R shifted +12 mm. Old SW path to the node removed (pin6 -> C8.2 kept),
HO-D5 off-branch R107/D31 on B.Cu in the B|A gap, pair tail: HO In3 lane x 149.25, SW In4 under it."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1])
F, I3, I4, BC = "F.Cu", "In3.Cu", "In4.Cu", "B.Cu"
HO, SW, HD = "/Driver_2/HO", "/Driver_2/SW", "/Driver_2/HO_DRV"
near = lambda a, b, t=0.03: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t
keep = [((145.22, 107.89), (147.32, 107.89)), ((147.32, 107.89), (147.75, 108.31))]
B.del_segs(lambda g: g["net"] == SW and g["layer"] == F and min(g["y1"], g["y2"]) > 95 and not any(
    (near((g["x1"], g["y1"]), a) and near((g["x2"], g["y2"]), b)) or (near((g["x1"], g["y1"]), b) and near((g["x2"], g["y2"]), a)) for a, b in keep))
B.del_vias(lambda v: v["net"] == SW and near((v["x"], v["y"]), (138.25, 103.75)))
B.flip_fp("R107"); B.flip_fp("D31")
B.move_fp("R107", 147.55, 106.55, 90)
B.move_fp("D31", 148.75, 106.5, 90)
B.save()
B = Board(sys.argv[1])
B.track([(145.22, 106.615), (146.75, 106.6)], 0.4, F, HD); B.add_via((146.75, 106.6), HD)
B.track([(146.75, 106.6), (147.15, 107.0), (147.55, 107.46)], 0.4, BC, HD)
B.track([(147.55, 107.46), (148.75, 107.55)], 0.4, BC, HD)
B.add_via((148.1, 104.0), HO)
B.track([(147.55, 105.638), (148.1, 105.09), (148.1, 104.0)], 0.4, BC, HO)
B.track([(148.75, 105.45), (148.1, 105.09)], 0.4, BC, HO)
B.track([(147.75, 108.31), (147.25, 108.81), (147.25, 109.45)], 0.4, F, SW); B.add_via((147.25, 109.45), SW)
B.track([(149.25, 92.75), (149.25, 102.85), (148.1, 104.0)], 0.3, I3, HO)
B.track([(149.25, 92.75), (149.25, 104.6), (148.0, 105.85), (147.5, 105.85), (147.5, 107.35), (147.25, 107.6), (147.25, 109.45)], 0.3, I4, SW)
B.save()
print("lay_D5R applied")
