"""Р8: restore the GND vias near the LS sources lost by the C_gs via shifts (CHANGELOG §1.2 metric: via centre
within 2.5 mm of an S pin centre; rev0 29 / 31 / 29) — two in strip C, two in strip A, plus one spare in C."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1])
for p in ((116.85, 87.5), (120.65, 77.5), (119.75, 74.85), (154.65, 77.5), (153.75, 74.85)):
    B.add_via(p, "GND")
B.save(); print("lay_NEARS applied")
