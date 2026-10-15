"""D6 right side (phase A): HO-D6 off-branch R108/D32 on B.Cu right of U12 (as lay_D4R shifted +24 mm),
X via at the bottom of the HO In3 lane; the old SW path C9.2 -> via (162.25,103.75) is kept as the SW feed of
the In1 SW lane."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1])
F, BC = "F.Cu", "B.Cu"
HO, HD = "/Driver_1/HO", "/Driver_1/HO_DRV"
B.flip_fp("R108"); B.flip_fp("D32")
B.move_fp("R108", 159.55, 106.55, 90)
B.move_fp("D32", 160.75, 106.5, 90)
B.save()
B = Board(sys.argv[1])
B.track([(157.22, 106.615), (158.75, 106.6)], 0.4, F, HD); B.add_via((158.75, 106.6), HD)
B.track([(158.75, 106.6), (159.15, 107.0), (159.55, 107.46)], 0.4, BC, HD)
B.track([(159.55, 107.46), (160.75, 107.55)], 0.4, BC, HD)
B.add_via((160.1, 104.0), HO)
B.track([(159.55, 105.638), (160.1, 105.09), (160.1, 104.0)], 0.4, BC, HO)
B.track([(160.75, 105.45), (160.1, 105.09)], 0.4, BC, HO)
B.save()
print("lay_D6R applied")
