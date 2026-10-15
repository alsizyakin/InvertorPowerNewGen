"""D4 right side (phase C): old SW-to-node path removed, HO-D4 off-branch on B.Cu, pair tail HO(In3)/SW(In4) from the
driver up passage J1-J2 to the block-side ends of lay_C1."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1])
F, I3, I4, BC = "F.Cu", "In3.Cu", "In4.Cu", "B.Cu"
HO, SW, HD = "/Driver_3/HO", "/Driver_3/SW", "/Driver_3/HO_DRV"
near = lambda a, b, t=0.02: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t
# old SW path from pin 6 under the driver to the node near the shunt: keep only pin6 -> C7.2
keep = [((133.22, 107.89), (135.32, 107.89)), ((135.32, 107.89), (135.75, 108.31))]
B.del_segs(lambda g: g["net"] == SW and g["layer"] == F and min(g["y1"], g["y2"]) > 95 and not any(
    (near((g["x1"], g["y1"]), a) and near((g["x2"], g["y2"]), b)) or (near((g["x1"], g["y1"]), b) and near((g["x2"], g["y2"]), a)) for a, b in keep))
B.del_vias(lambda v: v["net"] == SW and near((v["x"], v["y"]), (126.25, 102.25)))
# HO-D4 off-branch on B.Cu: R_on R106 and D_off D30 side by side, X on top, HO_DRV at the bottom
B.flip_fp("R106"); B.flip_fp("D30")
B.move_fp("R106", 135.55, 106.55, 90)
B.move_fp("D30", 136.75, 106.5, 90)
B.save()
B = Board(sys.argv[1])
# vias: HO_DRV (from pin 7), X of the branch, SW (from C7.2)
B.track([(133.22, 106.615), (134.75, 106.6)], 0.4, F, HD); B.add_via((134.75, 106.6), HD)
B.track([(134.75, 106.6), (135.15, 107.0), (135.55, 107.46)], 0.4, BC, HD)
B.track([(135.55, 107.46), (136.75, 107.55)], 0.4, BC, HD)
B.add_via((136.1, 104.0), HO)
B.track([(135.55, 105.638), (136.1, 105.09), (136.1, 104.0)], 0.4, BC, HO)
B.track([(136.75, 105.45), (136.1, 105.09)], 0.4, BC, HO)
B.track([(135.75, 108.31), (135.25, 108.81), (135.25, 109.45)], 0.4, F, SW); B.add_via((135.25, 109.45), SW)
# pair up passage J1-J2: HO on In3, SW on In4 under it
B.track([(136.1, 104.0), (135.25, 103.15), (135.25, 93.45), (134.4, 92.6)], 0.3, I3, HO)
B.add_via((134.4, 92.6), HO)
B.track([(133.75, 90.65), (133.75, 91.95), (134.4, 92.6)], 0.3, I4, HO)
B.track([(134.5, 89.85), (135.25, 90.6), (135.25, 105.6), (135.5, 105.85), (135.5, 107.35), (135.25, 107.6), (135.25, 109.45)], 0.3, I4, SW)
B.save()
print("lay_D4R applied")
