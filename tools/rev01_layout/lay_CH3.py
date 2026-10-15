"""D4 HI input (/TMR1_CH3): drop the loop (128.25,115) -> (130.5,115) -> (130.5,116.5) -> (128.5,118.5); go straight
down x 128.5 into the old line (128.5,118.5) -> (128.5,124.75)."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1]); N = "/TMR1_CH3"
near = lambda a, b, t=0.03: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t
on = lambda g, a, b: (near((g["x1"], g["y1"]), a) and near((g["x2"], g["y2"]), b)) or (near((g["x1"], g["y1"]), b) and near((g["x2"], g["y2"]), a))
B.del_segs(lambda g: g["net"] == N and (on(g, (128.25, 115.0), (130.5, 115.0)) or on(g, (130.5, 115.0), (130.5, 116.5)) or on(g, (130.5, 116.5), (128.5, 118.5))))
B.track([(128.25, 115.0), (128.5, 115.25), (128.5, 118.5)], 0.3, "F.Cu", N)
B.save(); print("lay_CH3 applied")
