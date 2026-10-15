"""D4 left, part 4: node pour pulled back from the inputs (§6, >= 2 mm), C118 above pin 1, C121 next to R121."""
import sys, json
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1]); F = "F.Cu"
near = lambda a, b, t=0.03: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t
N = "/Current_Sensor_3/Phase_IN"
B.del_vias(lambda v: v["net"] == N and any(near((v["x"], v["y"]), (125.5, y)) for y in (103.0, 103.5, 104.0)))
B.keepout(F, [(122.6, 103.2), (129.9, 103.2), (129.9, 110.2), (122.6, 110.2)], name="HI/LI D4: node pour >= 2 mm")
B.move_fp("C118", 127.4, 104.1, 0)          # pad1 GND left (126.54), pad2 HI right (128.26)
B.track([(128.2625, 104.1), (128.2625, 105.345)], 0.3, F, "Net-(D4-HI)")
B.track([(126.5375, 104.1), (125.6, 104.1)], 0.4, F, "GND"); B.add_via((125.6, 104.1), "GND")
c = json.load(open(sys.argv[3]))
pl, rt = c["C121"]
B.move_fp("C121", pl[0], pl[1], pl[2])
for k, path in rt.items():
    B.track([tuple(p) for p in path], 0.3, F, "Net-(D4-LI)" if k == "1" else "GND")
B.save()
print("lay_D4L4 applied")
